<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# Skill Creator 参考：PM-WORKSPACE 约定速查

> skill-creator 生成新 skill 时必须遵守的现有约定。
> 每次生成前回读此文件，确保新 skill 不破坏现有规范。

## 1. 目录约定

```
PM-WORKSPACE/
├── .claude/
│   ├── rules/
│   │   └── pm-workflow.md          ← 全局规范，优先级最高
│   ├── skills/
│   │   ├── {skill-name}/
│   │   │   ├── SKILL.md            ← 必须有
│   │   │   └── references/         ← 可选，放参考文件
│   │   └── ...
│   └── settings.json
├── projects/{项目名}/              ← 每个项目独立目录
│   ├── context.md
│   ├── scene-list.md
│   ├── screenshots/
│   ├── inputs/
│   └── deliverables/
│       └── archive/
├── references/competitors/{平台}/  ← 跨项目竞品素材
├── profile.md                      ← 全局团队约束
├── README.md
└── CLAUDE.md
```

## 2. 配色 Token（新 skill 必须继承）

### 深色板（前台产品 / 深色 PPT）
| Token | 色值 | 用途 |
|-------|------|------|
| --bg | #0B0E11 | 背景 |
| --card | #161A1E | 卡片底 |
| --input | #1E2329 | 输入区 |
| --border | #2B3139 | 边框 |
| --text | #EAECEF | 主文字 |
| --text2 | #848E9C | 副文字 |
| --text3 | #5E6673 | 三级文字 |
| --accent | #2D81FF | 强调蓝 |
| --green | #0ECB81 | 正向/成功 |
| --red | #F6465D | 负向/错误 |
| --gold | #FFD740 | 高亮 |

### 浅色板（后台）
| Token | 色值 | 用途 |
|-------|------|------|
| --bg | #F5F6FA | 背景 |
| --white | #FFF | 白底 |
| --border | #E4E7ED | 边框 |
| --sidebar | #001529 | 侧边栏 |
| --sidebar-a | #1890FF | 侧边栏选中 |
| --text | #1D2129 | 主文字 |
| --text2 | #4E5969 | 副文字 |
| --text3 | #86909C | 三级文字 |
| --blue | #2D81FF | 蓝 |
| --green | #00B42A | 绿 |
| --red | #F53F3F | 红 |
| --orange | #FF7D00 | 橙 |

## 3. 设备规范

| 设备 | 尺寸 | 说明 |
|------|------|------|
| App 壳 | 375×812px, radius 44px | 深色底，Flex 布局 |
| 交互大图 Web | 580px 宽 | 白底 + 三色圆点 |
| 原型 Web | 960px 宽 | 白底 + 三色圆点 + URL 联动 |
| 后台 | 深色侧边栏 + 浅灰内容区 | Arco 风格 |

## 4. 字体

- 正文：`Noto Sans SC` + `Inter` + `JetBrains Mono`
- 等宽：`JetBrains Mono, monospace`（PPT 例外用 `JetBrains Mono`，见 pm-workflow §三白名单）
- PPT 标题：Arial Black
- PPT 正文：Arial
- PRD：Arial 11pt

## 5. 编号规范

| 类型 | 规则 | 示例 |
|------|------|------|
| 前台主场景 | 大写字母 | A / B / C |
| 子场景 | 主场景-数字 | B-1 / B-2 |
| 后台场景 | M-数字 | M-1 / M-2 |
| 功能前缀 | 前缀-数字 | F-0 / E-1 |

编号在 scene-list.md 确定后不可改动，所有产出物复用同一套。

## 6. 文件命名规范

格式：`{类型前缀}-{项目简称}-v{版本号}.{扩展名}`

| 已有前缀 | 类型 |
|----------|------|
| rf- | 需求框架 |
| arch- | 架构图集 |
| imap- | 交互大图 |
| proto- | 原型 |
| prd- | PRD |
| bspec- | 行为规格 |
| pspec- | 页面结构 |
| tc- | 测试用例集 |

新 skill 如果有产出物文件，需要新增命名前缀，且不能和以上冲突。

## 7. 已有 Skills 清单（防触发词冲突）

| Skill | 触发词关键字 | 类型 |
|-------|-------------|------|
| scene-list | 场景清单、场景梳理 | 链路型 |
| requirement-framework | 需求框架、需求拆解 | 链路型 |
| architecture-diagrams | 架构图、系统设计 | 链路型 |
| interaction-map | 交互大图、交互地图 | 链路型 |
| prototype | 原型、可交互原型 | 链路型 |
| prd | PRD、需求文档 | 链路型 |
| cross-check | 拉通自检、交叉检查 | 工具型 |
| competitor-analysis | 竞品分析、竞品调研 | 独立产出型 |
| workspace-audit | 检查 skills、skill 审计 | 工具型 |
| skill-creator | 新建 skill、创建 skill | 工具型 |
| behavior-spec | 行为规格、切分 PRD、bspec | 链路型（可选） |
| page-structure | 页面结构、给设计师出文档、pspec | 链路型（可选） |
| test-cases | 测试用例、出 QA 文档、出测试集、tc | 链路型（可选，依赖 behavior-spec） |

新 skill 的触发词不能和以上高度重叠。

## 8. pm-workflow.md 需要更新的位置

新建 skill 后，以下位置**可能**需要更新（skill-creator 负责生成建议）：

1. **第〇章【Skill 读取规则】表格** — 新增读取路径
2. **第一章 链路步骤** — 仅链路型需要
3. **第七章 产出物格式速查表** — 有产出物文件的 skill
4. **第八章 文件命名规范** — 有新命名前缀的 skill
5. **CLAUDE.md** — 目录结构有变化时
