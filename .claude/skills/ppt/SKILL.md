---
name: ppt
description: >
  当用户提到「PPT」「演示文档」「方案文档」「信息文档」「宣讲材料」「SOP 手册」
  「方法论文档」「团队分享」「对外宣讲」「pptx」「多Tab文档」时触发。
  也适用于：把方案/SOP/方法论类内容生成 HTML 多Tab信息文档（等同PPT给人讲方案）。
  即使用户只说「做个PPT」或「把这个做成可点击的文档」也应触发。
  不触发：architecture-diagrams 是项目内链路型（依赖 scene-list），ppt 是独立的，不依赖任何链路。
argument-hint: [内容大纲文件 或 口述大纲]
type: standalone
output_format: .html
output_prefix: ppt-
depends_on: []
optional_inputs: [context.md]
consumed_by: []
---

# PPT 信息文档

## 定位

独立产出型 Skill。把方案/SOP/方法论类内容生成 HTML 多Tab信息文档（等同 PPT 给人讲方案）。

和 architecture-diagrams 的区别：
- **architecture-diagrams**：项目内链路型，依赖 scene-list + context.md，按 13 种页面类型输出架构图集
- **ppt**：独立产出型，不依赖任何链路。用户提供内容大纲，按模板输出多Tab信息文档

用途：团队分享、对外宣讲、方法论沉淀、SOP 手册。

## 核心原则

1. **数据驱动侧边栏**：NAV 数组驱动 sidebar 导航，不硬编码
2. **PAGE_RENDERERS 分页渲染**：每个 Tab 一个渲染函数，不堆砌 HTML
3. **组件复用**：card / grid / tag / note / table / ck-item 等组件统一使用，视觉一致
4. **内容与骨架分离**：骨架脚本负责结构，填充脚本负责内容
5. **Prompt 展示用 modal**：如需展示 prompt 文本，用 modal 弹窗 + 复制按钮

### 校验标准

- Tab 能切换，侧边栏高亮跟随 = 通过
- 所有组件 class 名在 cheatsheet 中有定义 = 通过
- 产出物 > 200 行 → 必须用 Node.js 脚本生成（见 Step 3）

## 执行步骤

### Step 1：读取参考文件

并行读取：
- `references/ppt-template.html` — 骨架模板（CSS + JS + 空壳结构）
- `references/components-cheatsheet.md` — 组件速查表
- `references/gold-snippets.md` — 满分产物片段库（叙事模式 + 结构骨架参考）
- 用户提供的内容大纲（文件或口述）

### Step 2：确认大纲

用户提供内容大纲（几个 Tab、每页什么内容）。模型整理为 NAV 结构：

```
NAV = [
  { group:'分组名', dot:'green', items:[
    { id:'tab-id', icon:'📍', label:'Tab 标题' },
    ...
  ]},
];
```

确认要点：
- Tab 数量（建议 5-15 个，超过 15 考虑合并）
- 每页类型（总览 / 对比 / 清单 / 表格 / 详解 / Prompt 展示）
- 是否需要 modal 弹窗

等用户确认大纲后再进入 Step 3。

### 叙事编排规则（从满分产物 SOP-final.html 提炼）

填充每页内容时遵守以下 4 条叙事规则：

1. **先冲击后解释** — 每页先放最有视觉冲击力的元素（全景图/数据/对比图），再用卡片/表格解释细节。不要先铺定义再亮图。
2. **结论前置** — 速查表/推荐方案放在详情展开之前。听众先知道"用哪个"，再看"为什么"。
3. **参考细节折叠** — 目录列表/评测原理/技术参数等参考内容用 accordion 折叠，不抢主视觉空间。
4. **时间线顺序** — sidebar 页面顺序应匹配内容的时间线或逻辑依赖。不要把"事后"内容放在"事前"位置。

违反这些规则是满分产物迭代中最常犯的错误。每页填充完后回读检查叙事顺序。

### Step 3：生成 Node.js 骨架脚本

遵守 HTML > 200 行铁律，用 **Node.js** 脚本生成（优于 Python，避免三层转义地狱）。

**使用 Skill 内置填充脚本**：

```javascript
#!/usr/bin/env node
/**
 * gen_ppt_{主题}_v1.js — PPT 信息文档生成脚本
 * 使用 Skill 内置的 fill-template.js 模块
 */
const { fillTemplate } = require('../../../../.claude/skills/ppt/references/fill-template.js');

// 定义 NAV 数据
const NAV = [
  { group: '分组名', dot: 'green', items: [
    { id: 'tab-id', icon: '📍', label: 'Tab 标题' }
  ]}
];

// 定义 PAGE_RENDERERS（每个 Tab 的渲染函数）
// 使用 JavaScript 模板字符串（反引号），HTML 属性用双引号，无需转义换行
const renderers = {
  'tab-id': `
    <div class="page active">
      <div class="page-title">标题</div>
      <div class="page-subtitle">副标题</div>
      <!-- 页面内容 -->
    </div>
  `
};

// 生成文件
fillTemplate({
  title: '文档标题',
  nav: NAV,
  renderers: renderers,
  outputPath: 'projects/{项目名}/deliverables/ppt-{主题}-v1.html'
});
```

脚本保存到项目 `scripts/` 目录。

**脚本拆分规则（Tab ≥ 8 时强制）**：

- 主脚本 `gen_ppt_{主题}_v1.js`：≤ 80 行，只做 require + NAV 定义 + 调用 fillTemplate
- 渲染函数按 NAV group 拆分为 `pages_group0.js` / `pages_group1.js`，每文件 ≤ 150 行
- 每个渲染函数返回 HTML 字符串，用 JS 模板字符串（反引号 `` `...` ``）包裹，HTML 属性用双引号

**为什么用 Node.js 而不是 Python**：

Python 处理「Python → JS 字符串 → HTML」三层嵌套时转义极易出错：
- `"` 在 Python 字符串里需要转义为 `\"`，但 `"` 在 Python 中不是合法转义 → `SyntaxError`
- 用 raw string `r'''...'''` 写入文件变成 `\n`（字面两个字符）→ JS 报错
- Node.js 的模板字符串天然支持多行 HTML，无需手动处理换行转义

### Step 4：填充内容

按确认的大纲逐 Tab 填充内容。每个 Tab 对应一个 PAGE_RENDERERS 函数。

**页面类型 → 组件映射**：

| 页面类型 | 推荐组件 | 示例 |
|---------|---------|------|
| 总览页 | hero-num + grid3 + note | 首页/概览 |
| 对比页 | grid2 双栏 + card | 优劣势对比、方案对比 |
| 清单页 | ck-item 列表 | 步骤、检查项 |
| 表格页 | cmp-table | 规格对比、价格表 |
| 详解页 | card + note 混排 | 概念解释、功能说明 |
| Prompt 展示页 | prompt-block + modal | 可复制的 Prompt/模板 |
| 流程页 | pipe + pipe-node + pipe-arrow | 步骤流程、链路 |
| 嵌套图页 | nest-outer/mid/inner | 层级关系、架构嵌套 |

填充过程中：
- 先填充前 2-3 个 Tab → 用户确认方向
- 确认后批量填充剩余 Tab
- **每个 Tab 填充后立即用 `node -e "new Function(script)"` 验证 JS 语法**，不通过立即修正

**HTML 内容书写规范（Node.js 模板字符串模式）**：

```javascript
const renderers = {
  'overview': `
    <div class="page active">
      <div class="page-title">标题</div>
      <div class="page-subtitle">副标题</div>
      <div class="card">
        <!-- 卡片内容 -->
      </div>
    </div>
  `
};
```

注意：
- 使用 **模板字符串**（反引号 `` `...` ``），不是普通引号
- HTML 属性用 **双引号** `"class="page"`
- 内容中如果包含 `${}` 需要转义为 `\${}`（很少见）
- 内容中如果包含反引号 `` ` `` 需要转义为 `\``（很少见）
- 如需展示可复制文本，用 prompt-block 组件

### Step 5：自检

产出物声称完成前必须执行：

```bash
# 1. Tab 完整性：NAV items 数量 = PAGE_RENDERERS 函数数量
grep -c "PAGE_RENDERERS\[" {产出物}
grep -c "{ id:" {产出物}  # 或从脚本 NAV 数

# 2. 组件 class 名合法
# 对照 components-cheatsheet.md 检查

# 3. 浏览器可打开（至少检查 HTML 结构闭合）
grep -c '</html>' {产出物}

# 4. Sidebar 可导航
grep "renderNav\|goPage" {产出物} | head -5

# 5. 每个 page 有 active class（数量应 = PAGE_RENDERERS 函数数量）
grep -c 'class="page active"' {产出物}

# 6. 行数统计
wc -l {产出物}
```

全部通过后交付 HTML 产出物，然后进入 Step 6。

### Step 6：生成口播稿

HTML 产出物交付后，生成配套的口播稿 Markdown 文件。

**规格**：
- 格式：单独 Markdown 文件
- 命名：`ppt-{主题}-notes-v{N}.md`
- 存放：与 HTML 产出物同目录

**结构**：按 sidebar 页面顺序，每页一个二级标题章节。参考 `references/notes-template.md` 模板。

```markdown
# {文档标题} — 口播稿

## Tab 名称

**核心论点**：这一页要传递的 1 个关键信息

**讲解要点**：
- 要点 1（引用页面中的具体数据/图表）
- 要点 2
- 要点 3

**过渡**：→ 下一页讲 XXX，承接关系是 YYY
```

**写作要求**：
- 每页 100-200 字，整份 ≤ 3000 字
- 是演讲提纲不是逐字稿——看着能讲，不是照念
- 引用的数据/术语必须和 HTML 内容一致
- 过渡句帮演讲者自然衔接到下一页

**口播稿自检**：
- Tab 数量与 HTML 产出物的 NAV items 一致
- 每个 Tab 都有内容（无空章节）
- 数据/术语与 HTML 内容一致
- 过渡句覆盖每个页面切换点

## 输出格式

- 格式：单文件 `.html`
- 命名：`ppt-{主题}-v{N}.html`
- 存放：`projects/{项目}/deliverables/`（如有项目关联）或 `deliverables/`（独立产出）
- 版本管理：遵循 pm-workflow 8.2 版本管理规则

### 设备规范

继承 pm-workflow 第三章暗色主题：
- 侧边栏 240px，深色 `--bg2`
- 主内容区 max-width 1200px
- 字体：DM Sans + Noto Sans SC + JetBrains Mono
- 配色变量：以 `--bg: #0a0c10` 系为准

### 组件规范

详见 `references/components-cheatsheet.md`，核心组件：
- **card** — 通用卡片容器
- **grid2/3/4** — 响应式网格
- **tag-\*** — 彩色标签（blue/green/orange/purple/red）
- **note** — 左边框提示框（蓝/绿/橙）
- **cmp-table** — 对比表格
- **ck-item + ck-num** — 编号清单
- **prompt-block** — 代码/文本展示块（含复制按钮）
- **pipe/pipe-node** — 纵向流程链
- **hero-num** — 大数字展示
- **track-card** — 路径/方案选择卡片
- **accordion** — 折叠展开
- **gallery-card** — 图片/案例展示
- **modal-overlay** — 全屏弹窗
- **score** — 分数/评级徽章

## 自检

- [ ] NAV items 数量 = PAGE_RENDERERS 函数数量
- [ ] 所有组件 class 名在 cheatsheet 中有定义
- [ ] sidebar 导航正常高亮
- [ ] Tab 切换正常，页面渲染正确
- [ ] HTML 结构闭合（`</html>` 存在）
- [ ] > 200 行的产出物通过 Node.js 脚本生成
- [ ] 产出物命名符合 `ppt-{主题}-v{N}.html` 规范
- [ ] 如有 prompt 展示，复制按钮功能正常
