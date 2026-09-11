# SDD 多智能体协作

主会话负责项目定位、流程推进和状态记录；子智能体按当前任务读取必要输入。

| 角色 | 输入 | 输出 |
| --- | --- | --- |
| Solution Designer | 已确认需求、项目配置、可选原型 | `docs/tech-spec.md`；有重要体验取舍时维护 `docs/decisions.md`，由主会话与用户讨论 |
| Planner | 已确认 PRD、技术方案与相关取舍、已有任务 | 首次写入 `.sdd/tasks.json` 的 Feature / 需求映射及任务；后续提出变更交编排器应用 |
| Developer | 当前任务、相关需求与接口章节、必要规范 | 代码、执行结果和变更文件 |
| Tester | 验收要求、实现文件、相关技术约定 | 独立测试结论与报告 |
| 编排器 | 子智能体结果与用户确认 | 唯一维护任务状态并选择下一步 |

```text
A 需求对齐 → 七层技术方案 → B 界面设计（有界面时）
                      ↓
              Plan 划分 Feature 与任务
                      ↓
                  Developer
                      ↓
                    Tester
             PASS / FAIL / BLOCKED
                      ↓
                编排器更新状态
```

重要体验取舍先解释选项与后果，由主会话取得用户选择或复用已有决定；普通实现由 Agent 处理。PASS 后继续已授权任务；FAIL 按开发循环有限修复；BLOCKED 明确缺失条件。存在未完成任务或关键验收缺失时，不能宣布项目完成。

每次交接包含项目绝对路径、当前目标或任务 ID、需要读取的章节与文件、允许修改的范围。并发策略和重试规则只在 [开发循环](../harness-core/protocols/development-loop.md) 维护，各角色执行细节在 [角色目录](../harness-core/agents/)。

`.sdd/project.json` 中的规范选择决定是否加载规范集；`null` 时传入空 `rules_files`。任务仍须满足 PRD 与技术方案。只有命中当前任务的规范才进入上下文。

平台调用使用当前环境实际提供的工具，不将某个平台的固定工具语法当作所有平台通用接口。缺少子智能体能力时，按 [Codex 角色协议](../harness-core/protocols/codex-subagents.md) 保持角色边界，并说明验证是否独立执行。
