<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# PRD · docx 样式定义

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

```javascript
styles: {
  default: {
    document: {
      run: {
        font: "Arial",
        size: 22,                   // 11pt 正文（参照实际产出物）
        color: "333333"
      },
      paragraph: {
        spacing: { line: 360 }      // 1.5 倍行距
      }
    }
  },
  paragraphStyles: [
    // ── 标题（封面用） ──
    {
      id: "Title", name: "Title",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 48, bold: true, font: "Arial", color: "1A1A2E" },
      paragraph: { spacing: { before: 480, after: 120 }, alignment: AlignmentType.CENTER }
    },
    // ── 副标题 ──
    {
      id: "Subtitle", name: "Subtitle",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 28, font: "Arial", color: "666666" },
      paragraph: { spacing: { before: 0, after: 360 }, alignment: AlignmentType.CENTER }
    },
    // ── H1 · 章标题 ──
    {
      id: "Heading1", name: "Heading 1",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 32, bold: true, font: "Arial", color: "1A1A2E" },
      paragraph: {
        spacing: { before: 480, after: 240 },
        outlineLevel: 0,
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "2E75B6", space: 1 } }
      }
    },
    // ── H2 · 节标题 ──
    {
      id: "Heading2", name: "Heading 2",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 26, bold: true, font: "Arial", color: "2E75B6" },
      paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 1 }
    },
    // ── H3 · 子节标题 ──
    {
      id: "Heading3", name: "Heading 3",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 22, bold: true, font: "Arial", color: "333333" },
      paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 2 }
    }
  ]
}
```

## 文本样式速查

| 用途 | 字体 | 字号(half-pt) | 实际pt | 颜色 | 粗体 |
|------|------|--------------|--------|------|------|
| 封面标题 | Arial | 48 | 24pt | #1A1A2E | ✓ |
| 封面副标题 | Arial | 28 | 14pt | #666666 | — |
| H1 章标题 | Arial | 32 | 16pt | #1A1A2E | ✓ |
| H2 节标题 | Arial | 26 | 13pt | #2E75B6 | ✓ |
| H3 子节 | Arial | 22 | 11pt | #333333 | ✓ |
| 正文 | Arial | 22 | 11pt | #333333 | — |
| 表头文字 | Arial | 18 | 9pt | #FFFFFF | ✓ |
| 表格正文 | Arial | 18 | 9pt | #333333 | — |
| 代码/字段名 | IBM Plex Mono | 18 | 9pt | #C7254E | — |
| 斜体说明 | Arial | 22 | 11pt | #888888 | — |
| 标注(变更) | Arial | 20 | 10pt | #D97706 | ✓ |

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
// 表头文字 color: "FFFFFF"（白字）
// 正文行无底色
```

### 场景地图表

```javascript
// 4 列：编号 / 场景 / 模块 / 优先级
width: { size: 12960, type: WidthType.DXA },
columnWidths: [1100, 6240, 2770, 2850],

// 表头行
shading: { fill: "2D81FF", type: ShadingType.CLEAR },  // 蓝底白字
```

### Scene 详细需求表（核心两列表格）

```javascript
// 2 列：左截图(35%) / 右说明(65%)
width: { size: 12960, type: WidthType.DXA },
columnWidths: [4536, 8424],

// 左列
shading: { fill: "F8FAFB", type: ShadingType.CLEAR },  // 极浅灰底
verticalAlign: VerticalAlign.CENTER,
// 左列文字：居中，斜体，color: "888888"

// 右列
shading: null,  // 白底
// 右列文字：正常正文样式
```

### 业务规则表

```javascript
// 2 列：规则 / 详情
width: { size: 12960, type: WidthType.DXA },
columnWidths: [3880, 9080],
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

// 事件名用等宽字体
new TextRun({ text: "ac_page_view", font: "IBM Plex Mono", size: 20, color: "C7254E" })
```

### 组件复用矩阵

```javascript
// N+1 列：组件名 + 各 View
// 用 ✓ 和 — 标记
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

// 路由列用等宽字体
new TextRun({ text: "/activity-center", font: "IBM Plex Mono", size: 20 })
```

## 列表样式

```javascript
numbering: {
  config: [
    {
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "\u2022",
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

## Header / Footer

```javascript
// Header：左侧产品名 + 右侧文档版本
headers: {
  default: new Header({
    children: [
      new Paragraph({
        children: [
          new TextRun({ text: "[产品名称] PRD", font: "Arial", size: 16, color: "AAAAAA" }),
          new PositionalTab({
            alignment: PositionalTabAlignment.RIGHT,
            relativeTo: PositionalTabRelativeTo.MARGIN,
            leader: PositionalTabLeader.NONE
          }),
          new TextRun({ text: "V1.0", font: "Arial", size: 16, color: "AAAAAA" })
        ],
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "DDDDDD", space: 1 } }
      })
    ]
  })
}

// Footer：左侧「机密」+ 右侧页码
footers: {
  default: new Footer({
    children: [
      new Paragraph({
        children: [
          new TextRun({ text: "机密 · 仅限内部使用", font: "Arial", size: 16, color: "AAAAAA" }),
          new PositionalTab({
            alignment: PositionalTabAlignment.RIGHT,
            relativeTo: PositionalTabRelativeTo.MARGIN,
            leader: PositionalTabLeader.NONE
          }),
          new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "AAAAAA" }),
          new TextRun({ text: " / ", font: "Arial", size: 16, color: "AAAAAA" }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], font: "Arial", size: 16, color: "AAAAAA" })
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
    // 产品名称（Title 样式）
    new Paragraph({ style: "Title", children: [new TextRun("[产品名称]")] }),
    // 副标题
    new Paragraph({ style: "Subtitle", children: [new TextRun("产品需求文档（PRD）")] }),
    // 模块说明
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
