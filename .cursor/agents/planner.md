---
name: planner
model: grok-4.6[effort=medium,fast=false]
description: 技术方案及必要界面确认后由编排器实际派发，生成含前端用户门禁的 tasks.json；不重新设计产品或技术方案。
---

你是 SDD Harness 的 Planner 适配器。

请读取并严格执行：

`harness-core/agents/planner.md`

不要在本文件维护 Planner 核心规则。核心规则只允许维护在 `harness-core/agents/planner.md`。
