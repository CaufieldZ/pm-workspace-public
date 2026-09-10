# PPT Step 6 · 生成口播稿 docx（可选）

> 触发：SKILL.md Step 6 引用本文档。HTML 产出物交付后按需生成 docx 提词器。

## 触发规则

默认不生成。HTML 产出物交付后 Claude **主动问一次**：

> 「这是最终版吗？需要生成 docx 口播稿吗？（微信发手机当提词器）」

用户说「要」才执行；用户明示「最终版了」或「出口播稿」也直接触发；迭代版本说「不要」则跳过。

## 产物

`ppt-{主题}-notes-v{N}.docx`（放 deliverables 同目录）

## 技术选型

python-docx（参考模板 `.claude/skills/ppt/scripts/gen-notes-docx.py`）

项目使用时复制到 `projects/{项目}/scripts/gen_notes_v{N}.py`，填入 NOTES 数据：

```python
NOTES = [
  { 'eyebrow': '开场 · 01',
    'title': '总览 & 选路',
    'paragraphs': [
      '纯正文段（开门见山一句话核心论点）。',
      [('讲解段 1 · ', False), ('关键词', True), (' 后面跟描述。', False)],
      [('讲解段 2 · 用', False), ('内联加粗', True), (' 代替 bullet 列表。', False)],
    ],
    'transition': '→ 下一页讲 XXX，承接关系是 YYY' },
  # ... 每页一个对象
]
OUTPUT_PATH = '../deliverables/ppt-{主题}-notes-v1.docx'
```

运行 `python3 gen_notes_v1.py` 生成 docx。

## 排版规格

对齐参考样本 PM-AI-SOP-script-v3.docx · 手机阅读优化：

- 字体：PingFang SC（中英文统一）
- 调色板：标题 #1E293B slate-800 · 正文 #475569 slate-600 · 分隔线 #E5E7EB · eyebrow #2D81FF 蓝 · 过渡 #94A3B8 灰
- Eyebrow 9pt 蓝色加粗 + 大标题 18pt 加粗 + 标题下薄横线 + 正文 12pt 行距 1.6 + 过渡句 11pt 斜体浅灰
- **流动段落**（不是 bullet 列表）——强调词内联加粗 + slate-800 深色，朗读不卡顿
- 每页之间分页符——微信打开翻一页看一页

## 写作要求

- 每页 4-8 段，每段 30-80 字
- 是演讲提纲不是逐字稿——看着能讲，不是照念
- 引用的数据 / 术语必须和 HTML 内容一致
- 过渡句帮演讲者自然衔接到下一页
- 内联加粗用于强调名词 / 关键数字 / 核心论点，不滥用
