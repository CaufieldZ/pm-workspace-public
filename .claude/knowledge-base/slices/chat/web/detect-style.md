---
id: chat/detect-style
name: CSS 与 UI 库检测
product: chat
platform: web
description: 项目 CSS 方案与 UI 库检测（识别已有体系 + 可复用组件）
applies-to: [tuikit-atomicx-vue3]
sdk-version: "tuikit-atomicx-vue3 >=6.0.0"
depends-on-stores: []
trigger-keywords: []
prerequisites: []
tags: [chat, vue3]
---

# 项目 CSS 方案检测

> dispatcher Step 1 探测时硬编码 `read_file`，不通过 trigger-keywords 命中。

## 目标

识别项目已有的 CSS 体系和 UI 组件库，确保生成代码遵循项目现有方案，不引入冲突。

## 1. CSS 方案识别

| 探测信号 | 判定 | 后续行为 |
|---|---|---|
| `tailwindcss` / `@tailwindcss/*` 在 deps | Tailwind | 用 Tailwind utility class 写样式 |
| `unocss` 在 deps | UnoCSS | 按 UnoCSS 语法写 |
| `element-plus` 在 deps | Element Plus | 用其组件 + 遵循其变量体系 |
| `naive-ui` 在 deps | Naive UI | 用其组件 |
| `vant` 在 deps | Vant | 用其组件 |
| `ant-design-vue` 在 deps | Ant Design Vue | 用其组件 |
| `vuetify` 在 deps | Vuetify | 用其组件 |
| `*.module.css` / `*.module.scss` 存在 | CSS Modules | 用 CSS Modules 写 |
| `<style scoped>` 为主 | Vue Scoped | 用 scoped style |
| 都没识别到 | 无 CSS 方案 | 空项目默认装 Tailwind |

- ❗ 探测到已有 CSS 方案 → 生成代码直接使用该方案
  - ❌ 项目用 Element Plus，AI 手写 `<button>` 不用 `<el-button>`
- ❗ 已有方案不可叠加另一套
  - ❌ 项目用 UnoCSS，路径 A 还装 Tailwind（冲突）
  - ❌ 项目用 Vuetify，还引入 Tailwind（冲突）
- ❗ 空项目（无任何 CSS 方案）→ 路径 A 默认装 Tailwind

## 2. UI 组件库识别

探测 `package.json` deps 中的 UI 库：

- 有 UI 库 → 优先使用其提供的组件（Button / Dialog / Card 等）
- 无 UI 库 → AI 自由实现组件

## 3. 可复用组件扫描

- ❗ 扫描 `src/components/ui/*` 或项目约定组件目录
- ❗ 能复用必须复用
  - ❌ 项目有 `BaseAvatar.vue`，聊天里另写 `ChatAvatar.vue`
  - ❌ 项目有 `AppDialog.vue`，自己用 `<div class="modal">`
- ❗ 复用时遵循该组件 API 约定（props / slot / emit）
- ❗ 结果列入 `config.json.reusable_components`

## 4. 命名约定识别

- 扫 `src/components/*` 的命名（kebab-case / PascalCase）
- 扫 `<script setup>` vs Options API
- TypeScript / JavaScript

## 5. 探测输出

写入 `config.json`：

```jsonc
{
  "css_scheme": "tailwind",          // tailwind | unocss | css-modules | scoped | plain
  "ui_library": "element-plus",     // element-plus | naive-ui | vant | ant-design-vue | vuetify | null
  "naming": "PascalCase",
  "script_style": "setup-script",
  "reusable_components": [
    "src/components/ui/card.vue",
    "src/components/ui/dialog.vue"
  ]
}
```

## 6. 反例（跨规则复合错误）

- ❌ 识别到项目用 Element Plus，但不用 `<el-card>` 自己手写 card 组件 → 违反 § 1 + § 2
- ❌ 项目有 Tailwind，路径 A 又装了一遍 Tailwind → 违反 § 1 "不可叠加"
- ❌ 项目有可复用的 `BaseDialog.vue`，聊天模块另起 `ChatDialog.vue` → 违反 § 3
