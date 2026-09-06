# 共享资产目录（_shared）

本目录存放跨 skill 复用的资产，**不是独立 skill**，不直接产出交付物，不会被 harness 注册触发（文件名 README.md 而非 SKILL.md）。

## 消费方

claude-design/ 被以下 9 个 skill 引用：
ppt · flowchart · architecture-diagrams · interaction-map · prototype · prd · data-report · competitor-analysis · cross-check

## 内容

- `claude-design/` — claude-design 美学 token + 工具类 + 内容规范 + 对标 demo
  - `tokens.css` — 深色 token + Platform C 蓝 accent + 四字体
  - `utilities.css` — 视觉质感工具类（film grain / eyebrow / hairline / 带色阴影 / 低调水印）
  - `anti-ai-slop.md` — HTML 产出物通用反 AI slop 规范（六禁 / 字号 / 颜色 / 印刷文档字号 + 行高 + 页边距 / 决策速查）
  - `asset-quality-rubric.md` — 5-10-2-8 素材门槛
  - `review-rubric.md` — PM 5 维度评审（场景覆盖 / 信息层级 / 规则完备 / 端能力 / 风险）
  - `content-slop-ban.md` — PRD / 数据报告内容纪律操作手册（placeholder 写法 + 业务规则完备性 + 数值来源标注，与 anti-ai-slop 配套：HTML 通用规范在那边，PRD/数据报告操作细节在这边）
  - `demos/` — 3 个对标 HTML
- `workspace.json` — 工作区元数据（当前仅 `author` 字段），被 [scripts/lib/html_builder.py](../../../scripts/lib/html_builder.py) `get_author()` 读取并注入 scene-list 视觉版 HTML 页脚。新增字段先确认有 caller。

## 引用方式

**CSS**（HTML 产出物 skill）:
```css
@import url('../../_shared/claude-design/tokens.css');
@import url('../../_shared/claude-design/utilities.css');
```

**Markdown**（SKILL.md 里声明）:
```
Step 1 读取:
- `.claude/skills/_shared/claude-design/anti-ai-slop.md`（按需 grep「决策速查」段）
```

## 维护规则

- 修改 _shared/ 下任何文件前，先 grep 哪些 skill 引用，避免级联破坏
- 新增共享资产应更新本文件「消费方」和「内容」两段
- 命令前缀留空（不参与 skill 计数，审计脚本已白名单）
