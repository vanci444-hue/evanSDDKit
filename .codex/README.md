# SDD V7 Codex Adapter

本目录是 Codex 适配层，只做入口和 subagent 配置，不维护核心规则。

## 入口

- 根入口：`AGENTS.md`
- Codex 配置：`.codex/config.toml`
- 子智能体：`.codex/agents/*.toml`
- 开发循环协议：`harness-core/protocols/development-loop.md`

## 使用方式

在 Codex 中打开 Harness 根目录后：

1. 先读取 `AGENTS.md`
2. 按语义路由进入对应流程（Router 见 `harness-core/router.md`），所有核心规则都在 `harness-core/`

## 子智能体

当前提供四个薄适配器：

- `planner` → `harness-core/agents/planner.md`
- `developer` → `harness-core/agents/developer.md`
- `tester` → `harness-core/agents/tester.md`
- `solution-designer` → `harness-core/agents/solution-designer.md`（由设计主 Agent 按需派出，协助 PRD 对应的七层技术方案）

如果当前 Codex 环境不支持自定义 subagent TOML，按 `harness-core/protocols/codex-subagents.md` 在主会话中模拟三角色边界。
