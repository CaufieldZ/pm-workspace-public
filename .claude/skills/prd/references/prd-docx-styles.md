<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# PRD · docx 样式定义

## 字体策略（与 gen_prd_base.py FONT 字典对齐）

字体三分工原则：

| role | ascii（英文/数字）| eastAsia（中文）| 用途 |
|------|------------------|----------------|------|
| **title** | Source Serif 4 | Noto Serif SC | 封面 Title / Subtitle、H1 / H2 / H3、Scene 模块标题（触发方式 / 关键交互 / 校验逻辑等） |
| **body** | Plus Jakarta Sans | HarmonyOS Sans SC | 默认正文、表格内容、bullet、cell_text |
| **mono** | JetBrains Mono | JetBrains Mono | 代码、路由、事件名、状态标签（NEW / 变更 / P0）、Header / Footer |

Word 渲染时按字符自动选（中文走 eastAsia，英文 / 数字走 ascii）。用户系统没装相应字体时 Word 自动 fallback：

- HarmonyOS Sans SC 没装 → PingFang SC（Mac）/ 微软雅黑（Windows）
- Noto Serif SC 没装 → 系统默认中文衬线
- 不需要强制用户装字体

**调用方式**（在 gen_prd_base.py 内）：

```python
para_run(p, text, font='title', size_pt=24, bold=True)  # 标题 / 章节
para_run(p, text, size_pt=11)                            # 正文（默认 body 可省略）
para_run(p, text, font='mono', size_pt=9)                # 代码 / meta / 状态标签
```

旧脚本兼容：`font="Arial"` 自动映射到 body 配置（不需重写）。

---

## 页面设置

```javascript
page: {
  size: {
    width: 12240,     // docx-js: 传 SHORT 边作 width
    height: 15840,    // docx-js: 传 LONG 边作 height
    orientation: PageOrientation.LANDSCAPE  // docx-js 内部交换
  },
  margin: {
    top: 1080,        // 0.75"（横版上下稍窄）
    right: 1440,      // 1"
    bottom: 1080,     // 0.75"
    left: 1440        // 1"
  }
}
// Landscape 实际页面：15840 × 12240 DXA (11" × 8.5")
// 内容区宽度 = 15840 - 1440*2 = 12960 DXA
```

## 字体 & 段落样式

gen_prd_base.py 的 FONT 字典（实际生效配置）：

```python
FONT = {
  'title': {'ascii': 'Source Serif 4',    'eastAsia': 'Noto Serif SC'},
  'body':  {'ascii': 'Plus Jakarta Sans', 'eastAsia': 'HarmonyOS Sans SC'},
  'mono':  {'ascii': 'JetBrains Mono',    'eastAsia': 'JetBrains Mono'},
  # 兼容旧脚本：font="Arial" 自动映射到 body
  'Arial': {'ascii': 'Plus Jakarta Sans', 'eastAsia': 'HarmonyOS Sans SC'},
}
```

```javascript
// docx-js 风格的样式定义（参考；实际由 gen_prd_base.py para_run 注入字体）
styles: {
  default: {
    document: {
      run: {
        // 默认走 body role：Plus Jakarta Sans (英文) + HarmonyOS Sans SC (中文)
        size: 22,                   // 11pt 正文
        color: "333333"
      },
      paragraph: {
        spacing: { line: 360 }      // 1.5 倍行距
      }
    }
  },
  paragraphStyles: [
    // ── 标题（封面用，title role 衬线）──
    {
      id: "Title", name: "Title",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 48, bold: true, font: "title", color: "1A1A2E" },
      paragraph: { spacing: { before: 480, after: 120 }, alignment: AlignmentType.CENTER }
    },
    // ── 副标题（title role）──
    {
      id: "Subtitle", name: "Subtitle",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 28, font: "title", color: "666666" },
      paragraph: { spacing: { before: 0, after: 360 }, alignment: AlignmentType.CENTER }
    },
    // ── H1 · 章标题（title role）──
    {
      id: "Heading1", name: "Heading 1",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 32, bold: true, font: "title", color: "1A1A2E" },
      paragraph: {
        spacing: { before: 480, after: 240 },
        outlineLevel: 0,
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2E75B6", space: 1 } }
      }
    },
    // ── H2 · 节标题（title role）──
    {
      id: "Heading2", name: "Heading 2",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 26, bold: true, font: "title", color: "2E75B6" },
      paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 1 }
    },
    // ── H3 · 子节标题（title role）──
    {
      id: "Heading3", name: "Heading 3",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 22, bold: true, font: "title", color: "333333" },
      paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 2 }
    }
  ]
}
```

## 文本样式速查（含 font role）

| 用途 | font role | 字号(half-pt) | 实际pt | 颜色 | 粗体 |
|------|-----------|--------------|--------|------|------|
| 封面标题 | **title** | 48 | 24pt | #1A1A2E | ✓ |
| 封面副标题 | **title** | 28 | 14pt | #666666 | — |
| H1 章标题 | **title** | 32 | 16pt | #1A1A2E | ✓ |
| H2 节标题 | **title** | 26 | 13pt | #2E75B6 | ✓ |
| H3 子节 | **title** | 22 | 11pt | #333333 | ✓ |
| Scene 模块标题（触发方式 / 关键交互）| **title** | 20 | 10pt | #1A1A2E | ✓ |
| 正文 | **body** | 22 | 11pt | #333333 | — |
| 表头文字 | **body** | 18 | 9pt | #FFFFFF | ✓ |
| 表格正文 | **body** | 18 | 9pt | #333333 | — |
| 代码 / 路由 / 事件名 | **mono** | 18 | 9pt | #C7254E | — |
| 斜体说明 | **body** italic | 22 | 11pt | #888888 | — |
| 标注（变更）/ NEW / P0 tag | **mono** | 20 | 10pt | #D97706 | ✓ |
| Header / Footer | **mono** | 16 | 8pt | #AAAAAA | — |

## 颜色定义

```javascript
const COLORS = {
  // 文字
  textPrimary:   "333333",   // 正文
  textSecondary: "666666",   // 副标题/次要
  textMuted:     "888888",   // 斜体说明
  textHeading:   "1A1A2E",   // 标题/表头
  textLink:      "2E75B6",   // H2 / 链接蓝

  // 表格
  tableHeaderBg: "2D81FF",   // 表头底色（蓝色）
  tableHeaderText: "FFFFFF", // 表头文字（白色）
  tableAltRowBg: "F8FAFB",   // 交替行底色（极浅灰）
  tableBorder:   "CCCCCC",   // 边框灰
  tableBorderDk: "AAAAAA",   // 表头边框（稍深）

  // 状态标注
  tagNew:        "15803D",   // NEW 绿
  tagNewBg:      "DCFCE7",
  tagChange:     "D97706",   // 变更 琥珀
  tagChangeBg:   "FEF3C7",
  tagP0:         "15803D",   // P0 绿
  tagP0Bg:       "DCFCE7",
  tagP1:         "2563EB",   // P1 蓝
  tagP1Bg:       "DBEAFE",
  tagP2:         "92400E",   // P2 琥珀
  tagP2Bg:       "FEF3C7",

  // 强调
  codeBg:        "F5F5F5",   // 代码背景
  codeText:      "C7254E",   // 代码文字
  accentBlue:    "2E75B6",   // H1 底线 / H2 文字
  accentDark:    "1A1A2E",   // 深色强调
};
```

## 表格样式

### 通用表格边框

```javascript
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };
```

### 元信息表（封面下方）

```javascript
// 2 列，左窄右宽
width: { size: 12960, type: WidthType.DXA },
columnWidths: [3320, 9640],

// 表头行
shading: { fill: "2D81FF", type: ShadingType.CLEAR },  // 蓝底
// 表头文字 color: "FFFFFF"（白字），font: body
// 正文行无底色，font: body
```

### 场景地图表

```javascript
// 4 列：编号 / 场景 / 模块 / 优先级
width: { size: 12960, type: WidthType.DXA },
columnWidths: [1100, 6240, 2770, 2850],

// 表头行
shading: { fill: "2D81FF", type: ShadingType.CLEAR },  // 蓝底白字
// 编号列内容走 mono（A / B-1 / M-1 等编号有节奏感），其他列 body
```

### Scene 详细需求表（核心两列表格）

```javascript
// 2 列：左截图(35%) / 右说明(65%)
width: { size: 12960, type: WidthType.DXA },
columnWidths: [4536, 8424],

// 左列
shading: { fill: "F8FAFB", type: ShadingType.CLEAR },  // 极浅灰底
verticalAlign: VerticalAlign.CENTER,
// 左列文字：居中，斜体，color: "888888"，font: body italic

// 右列
shading: null,  // 白底
// 右列内容：
//   - 模块标题（**触发方式** / **关键交互** 等）走 title role 粗体
//   - numbered list 条目走 body
//   - 内嵌代码 / 路由走 mono
//   - 状态标签（变更）/ P0 走 mono
```

### 业务规则表

```javascript
// 2 列：规则 / 详情
width: { size: 12960, type: WidthType.DXA },
columnWidths: [3880, 9080],
// 规则列短文本（body），详情列含路由 / 接口路径走 mono inline
```

### 非功能性需求表

```javascript
// 2 列：指标 / 要求
width: { size: 12960, type: WidthType.DXA },
columnWidths: [4990, 7970],
```

### 埋点表

```javascript
// 3 列：事件 / 触发 / 参数
width: { size: 12960, type: WidthType.DXA },
columnWidths: [3880, 3880, 5200],

// 事件名走 mono role
new TextRun({ text: "ac_page_view", font: "mono", size: 20, color: "C7254E" })
// 参数列同样走 mono
```

### 组件复用矩阵

```javascript
// N+1 列：组件名 + 各 View
// ✓ 和 — 走 mono（让矩阵 ✓/— 视觉对齐有节奏）
// ✓ 用 color: "15803D"（绿）, — 用 color: "CCCCCC"（灰）
```

### 里程碑表

```javascript
// 3 列：阶段 / 时间 / 交付物
width: { size: 12960, type: WidthType.DXA },
columnWidths: [2490, 3330, 7140],
```

## 用户角色表

```javascript
// 4 列：角色 / 端 / 描述 / 核心操作
width: { size: 12960, type: WidthType.DXA },
columnWidths: [2220, 2220, 3880, 4640],
```

## 页面层级表

```javascript
// 3 列：层级 / 页面 / 路由
width: { size: 12960, type: WidthType.DXA },
columnWidths: [1660, 4990, 6310],

// 路由列走 mono role
new TextRun({ text: "/activity-center", font: "mono", size: 20 })
```

## 列表样式

```javascript
numbering: {
  config: [
    {
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•",
        alignment: AlignmentType.LEFT,
        style: {
          paragraph: { indent: { left: 720, hanging: 360 } },
          run: { font: "Symbol" }
        }
      }]
    },
    {
      reference: "numbers",
      levels: [{
        level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.LEFT,
        style: {
          paragraph: { indent: { left: 720, hanging: 360 } }
        }
      }]
    }
  ]
}
```

注：当前 Scene 右列的「numbered list」由 `fill_cell_blocks(numbered=True)` 用字符前缀（`1./2./3.`）实现，视觉等同 numbered list 但 docx 层无 `<w:numId>`（设计选择，避免编号配置复杂度，prd-template L186-191 强制规范由字符前缀满足）。

## Header / Footer

```javascript
// Header：左侧产品名 + 右侧文档版本（走 mono role 做 meta 节奏感）
headers: {
  default: new Header({
    children: [
      new Paragraph({
        children: [
          new TextRun({ text: "[产品名称] PRD", font: "mono", size: 16, color: "AAAAAA" }),
          new PositionalTab({
            alignment: PositionalTabAlignment.RIGHT,
            relativeTo: PositionalTabRelativeTo.MARGIN,
            leader: PositionalTabLeader.NONE
          }),
          new TextRun({ text: "V1.0", font: "mono", size: 16, color: "AAAAAA" })
        ],
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "DDDDDD", space: 1 } }
      })
    ]
  })
}

// Footer：左侧「机密」+ 右侧页码（走 mono role）
footers: {
  default: new Footer({
    children: [
      new Paragraph({
        children: [
          new TextRun({ text: "机密 · 仅限内部使用", font: "mono", size: 16, color: "AAAAAA" }),
          new PositionalTab({
            alignment: PositionalTabAlignment.RIGHT,
            relativeTo: PositionalTabRelativeTo.MARGIN,
            leader: PositionalTabLeader.NONE
          }),
          new TextRun({ children: [PageNumber.CURRENT], font: "mono", size: 16, color: "AAAAAA" }),
          new TextRun({ text: " / ", font: "mono", size: 16, color: "AAAAAA" }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], font: "mono", size: 16, color: "AAAAAA" })
        ]
      })
    ]
  })
}
```

## 封面页结构

```javascript
// Section 1：封面（无 header/footer）
{
  properties: {
    page: { size, margin },
    titlePage: true  // 首页不同
  },
  children: [
    // 上方留白
    ...Array(6).fill(new Paragraph({ spacing: { after: 200 } })),
    // 产品名称（Title 样式 = title role 衬线）
    new Paragraph({ style: "Title", children: [new TextRun("[产品名称]")] }),
    // 副标题（title role）
    new Paragraph({ style: "Subtitle", children: [new TextRun("产品需求文档（PRD）")] }),
    // 模块说明（body italic）
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: "[模块概要]", size: 22, color: "888888" })]
    }),
    // 留白
    ...Array(4).fill(new Paragraph({ spacing: { after: 200 } })),
    // 元信息表
    metaTable,
    // 分页
    new Paragraph({ children: [new PageBreak()] })
  ]
}

// Section 2：正文（有 header/footer + TOC）
{
  properties: { page: { size, margin }, headers, footers },
  children: [
    new TableOfContents("目录", { ... }),
    new Paragraph({ children: [new PageBreak()] }),
    // 正文内容...
  ]
}
```
