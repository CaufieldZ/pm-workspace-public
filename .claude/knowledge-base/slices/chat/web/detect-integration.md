---
id: chat/detect-integration
name: 集成信号探测
product: chat
platform: web
description: 集成信号探测口径（仅看是否依赖 tuikit-atomicx-vue3）
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: []
trigger-keywords: []
prerequisites: []
tags: [chat, vue3]
---

# 集成信号探测口径

> dispatcher Step 1 探测时硬编码 `read_file`，不通过 trigger-keywords 命中。
> 与 `chat/references/01-detect-project.md` § 2 互为参照。

## 探测策略

最小跑通：**只看 `package.json` 是否依赖 `tuikit-atomicx-vue3`**，不区分 UIKit，不单独识别 `tuikit-atomicx-vue3`。

## 规则

- ❗ 必须实际 `read_file package.json`，不准凭训练数据猜
  - ❌ 没读就直接判定"已集成"
- ❗ 唯一判定信号：`tuikit-atomicx-vue3` 在 `dependencies` 或 `devDependencies`

## 判定结果

| 命中 | 判定 | 走向 |
|---|---|---|
| deps 含 `tuikit-atomicx-vue3` | 已集成 | 路径 B |
| 不含，但目录非空 | 未集成 | 路径 A |
| 空目录 / 新项目 | 未集成 | 路径 A（先经新建引导） |
