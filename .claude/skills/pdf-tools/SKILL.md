<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
---
name: pdf-tools
description: >
  当用户提到 PDF 操作(合并 / 拆分 / 加页码 / 水印 / 加密 / 签名 / 转 Word / Excel / PPT / 图片 / 压缩等)时触发。
argument-hint: ["<输入文件路径> [子命令/参数]"]
type: tool
output_format: 原文件同目录
depends_on: []
consumed_by: []
---

# PDF Tools

## 定位

工具型 skill——在 Claude Code 中直接处理 PDF 文件，覆盖合并/拆分/页码/水印/旋转/加密/整理页面/签名/格式转换等日常操作。纯本地 Python 处理，文件不出机器。

## 核心原则

1. **不破坏原文件**：所有操作输出新文件，原文件不动
2. **输出到同目录**：处理结果存在输入文件旁边，文件名加后缀区分
3. **先确认再执行**：涉及多文件合并或批量操作时，先列出文件清单让用户确认
4. **报告结果**：执行后告知输出路径和文件大小

## 命名规则

输出文件名 = 原文件名（去 .pdf）+ 后缀 + 扩展名：

| 操作 | 后缀示例 | 输出 |
|------|---------|------|
| 合并 | `_merged.pdf` | 合并后的单文件 |
| 拆分 | `_part1.pdf`, `_part2.pdf` ... | 多个文件 |
| 加页码 | `_paged.pdf` | |
| 加水印 | `_watermarked.pdf` | |
| 旋转 | `_rotated.pdf` | |
| 加密 | `_encrypted.pdf` | |
| 整理页面 | `_reordered.pdf` | |
| 签名 | `_signed.pdf` | |
| 转 JPG | `_p1.jpg`, `_p2.jpg` ... | 每页一张 |
| 转 PDF/A | `_pdfa.pdf` | |
| 转 Word | `.docx` | |
| 转 Excel | `.xlsx` | |
| 转 PPT | `.pptx` | |
| 压缩 | `_compressed.pdf` | |

## 执行步骤

### Step 1: 识别操作和文件

从用户消息中识别：
- 操作类型（合并/拆分/转换等）
- 输入文件路径（支持绝对路径、相对路径、glob 模式）
- 附加参数（密码、水印文字、页码范围等）

如果用户只说了操作没给文件，问一句要处理哪个文件。

### Step 2: 验证文件

```bash
ls -la <文件路径>       # 确认文件存在
file <文件路径>         # 确认是 PDF
```

### Step 3: 执行操作

根据操作类型，调用对应的 Python 代码。详见 `references/pdf-commands.md` 速查表。

所有 Python 代码统一用 `python3` 执行，import 路径：
- `import pymupdf` (PyMuPDF)
- `import pikepdf`
- `from pdf2docx import Converter`
- `from docx import Document` (python-docx)
- `from openpyxl import Workbook`
- `from pptx import Presentation` (python-pptx)

### Step 4: 验证输出

```bash
ls -la <输出文件>       # 确认生成、查看大小
```

告知用户：输出路径 + 文件大小。

## 各操作详细说明

### 合并 PDF
- 输入：多个 PDF 文件路径
- 用户可指定顺序，默认按给出顺序
- 输出：`{第一个文件名}_merged.pdf`

### 拆分 PDF
- 按页码范围拆分（如「拆出第 3-5 页」）
- 按每 N 页拆分（如「每 10 页拆一个」）
- 按书签拆分

### 添加页码
- 默认：底部居中，字号 10，格式 "1 / N"
- 用户可指定位置（顶部/底部 + 左/中/右）、字号、起始页码

### 添加水印
- 文字水印：用户指定文字，默认 45 度倾斜、半透明灰色
- 图片水印：用户提供图片路径
- 可指定透明度、位置、角度

### 旋转 PDF
- 指定旋转角度（90/180/270）
- 可指定页码范围，默认全部页面

### PDF 加密
- 用户提供密码
- 可分别设置打开密码和权限密码
- 可设置权限（禁止打印/复制/编辑）

### 整理 PDF 页面
- 删除指定页面
- 重新排序（用户给出新顺序）
- 提取指定页面为新文件

### PDF 签名
- 用户提供签名图片路径
- 指定签名位置（页码 + 坐标或区域描述）
- 叠加到指定位置，透明底

### PDF 转 JPG
- 默认 DPI 150，用户可指定
- 每页输出一张，命名 `{原名}_p{N}.jpg`
- 可指定页码范围

### PDF 转 PDF/A
- 使用 pikepdf 转换为 PDF/A 兼容格式

### PDF 转 Word
- 使用 pdf2docx，尽量还原排版和表格
- 复杂排版可能有偏差，转换后提醒用户检查

### PDF 转 Excel
- 先用 PyMuPDF 提取表格数据
- 写入 openpyxl Workbook
- 多页表格分 sheet

### PDF 转 PPT
- 每页 PDF 转为 PPT 的一页（作为背景图片）
- 或提取文字内容填入 PPT 文本框（用户指定模式）

### PDF 压缩
- 使用 PyMuPDF 的 `doc.save(garbage=4, deflate=True, clean=True)`
- 压缩图片质量（可选）

## 自检清单

- [ ] 原文件未被修改
- [ ] 输出文件存在且大小合理（>0 bytes）
- [ ] 输出路径在原文件同目录
- [ ] 执行后告知了用户输出路径和文件大小
