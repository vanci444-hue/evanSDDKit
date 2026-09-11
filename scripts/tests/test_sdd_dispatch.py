"""Gate behavior across parallel completion, user review, configuration and rework."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sdd_dispatch import evaluate, validate


class DispatchTests(unittest.TestCase):
    def setUp(self):
        def task(i, kind, deps=(), status="pending"):
            return {"id": i, "type": kind, "dependencies": list(deps), "status": status}
        self.plan = {
            "external_services": [{"name": "model", "required": True, "status": "missing"}],
            "tasks": [task("UI1", "frontend"), task("UI2", "frontend", ["UI1"]),
                      task("API", "backend"), task("API2", "backend", ["API"]),
                      task("JOIN", "integration", ["API"]), task("DOC", "delivery", ["JOIN"])],
        }
        self.gate = {"kind": "frontend_mock_review", "frontend_task_ids": ["UI1", "UI2"],
                     "required_services": ["model"], "status": "pending", "user_confirmation": None,
                     "configuration_confirmation": None, "rework_task_ids": []}
        self.plan["tasks"][1]["user_gate"] = self.gate

    def finish_frontend(self):
        for t in self.plan["tasks"][:2]:
            t["status"] = "passed"

    def approve(self):
        self.finish_frontend()
        self.gate.update(status="passed", user_confirmation="User explicitly approved current Mock",
                         configuration_confirmation="Required fields present; no values logged")
        self.plan["external_services"][0]["status"] = "confirmed"

    def test_frontend_and_backend_can_start_together(self):
        result = evaluate(self.plan)
        self.assertEqual(result["developer_ready"], ["UI1", "API"])

    def test_integration_waits_even_when_its_dependencies_pass_before_gate(self):
        self.plan["tasks"][2]["status"] = "passed"
        result = evaluate(self.plan)
        self.assertIn("API2", result["developer_ready"])
        self.assertNotIn("JOIN", result["developer_ready"])

    def test_frontend_completion_closes_dispatch_before_status_writeback(self):
        self.finish_frontend()  # gate still pending: completion event must still close dispatch.
        self.plan["tasks"][2]["status"] = "testing"
        result = evaluate(self.plan)
        self.assertEqual(result["gate_phase"], "awaiting_user")
        self.assertEqual(result["developer_ready"], [])
        self.assertEqual(result["tester_ready"], [])

    def test_background_result_or_failure_does_not_bypass_gate(self):
        self.finish_frontend()
        for status in ("in_progress", "testing", "passed", "fixing", "blocked"):
            with self.subTest(status=status):
                self.plan["tasks"][2]["status"] = status
                result = evaluate(self.plan)
                self.assertEqual(result["developer_ready"], [])
                self.assertEqual(result["tester_ready"], [])

    def test_one_confirmation_cannot_open_gate(self):
        for key in ("user_confirmation", "configuration_confirmation"):
            with self.subTest(key=key):
                plan = deepcopy(self.plan)
                for t in plan["tasks"][:2]:
                    t["status"] = "passed"
                gate = plan["tasks"][1]["user_gate"]
                gate.update(status="passed")
                gate[key] = "confirmed"
                result = evaluate(plan)
                self.assertTrue(result["errors"])
                self.assertEqual(result["developer_ready"], [])

    def test_missing_or_mock_service_cannot_be_declared_ready(self):
        self.approve()
        for status in ("missing", "fallback"):
            self.plan["external_services"][0]["status"] = status
            self.assertTrue(evaluate(self.plan)["errors"])

    def test_release_unlocks_work_without_restarting_passed_tasks(self):
        self.approve()
        self.plan["tasks"][2]["status"] = "passed"
        result = evaluate(self.plan)
        self.assertEqual(result["developer_ready"], ["API2", "JOIN"])
        self.assertEqual(result["gate_phase"], "passed")

    def test_rework_only_dispatches_selected_frontend(self):
        self.finish_frontend()
        self.gate.update(status="changes_requested", rework_task_ids=["UI2"])
        self.plan["tasks"][1]["status"] = "fixing"
        self.assertEqual(evaluate(self.plan)["developer_ready"], ["UI2"])
        self.plan["tasks"][1]["status"] = "testing"
        self.assertEqual(evaluate(self.plan)["tester_ready"], ["UI2"])
        self.plan["tasks"][1]["status"] = "passed"
        self.assertEqual(evaluate(self.plan)["gate_phase"], "awaiting_user")

    def test_gate_needs_all_frontend_and_final_join_dependency(self):
        for change in ("coverage", "dependency", "missing", "duplicate", "post_gate_dependency"):
            with self.subTest(change=change):
                p = deepcopy(self.plan)
                if change == "coverage": p["tasks"][1]["user_gate"]["frontend_task_ids"] = ["UI2"]
                elif change == "dependency": p["tasks"][1]["dependencies"] = []
                elif change == "missing": del p["tasks"][1]["user_gate"]
                elif change == "duplicate": p["tasks"][0]["user_gate"] = deepcopy(self.gate)
                else: p["tasks"][0]["dependencies"] = ["JOIN"]
                self.assertTrue(validate(p))

    def test_backend_only_project_needs_no_gate(self):
        p = {"tasks": [{"id": "API", "type": "backend", "status": "pending", "dependencies": []}]}
        self.assertEqual(evaluate(p)["developer_ready"], ["API"])

    def test_no_services_still_requires_explicit_not_applicable_record(self):
        self.approve()
        self.plan["external_services"] = []
        self.gate["required_services"] = []
        self.gate["configuration_confirmation"] = "No external services; not applicable"
        self.assertEqual(evaluate(self.plan)["gate_phase"], "passed")

    def test_cli_is_read_only_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "tasks.json"
            p.write_text(json.dumps(self.plan))
            before = p.read_bytes()
            script = Path(__file__).resolve().parents[1] / "sdd_dispatch.py"
            r = subprocess.run([sys.executable, str(script), "--tasks", str(p)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(p.read_bytes(), before)
            p.write_text('{"tasks": [null]}')
            r = subprocess.run([sys.executable, str(script), "--tasks", str(p)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, r.stderr)
            self.assertEqual(json.loads(r.stdout)["developer_ready"], [])


if __name__ == "__main__":
    unittest.main()
