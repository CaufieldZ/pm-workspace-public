<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# PDF Commands 速查表

> 每个操作的最小可运行 Python 代码片段，执行时直接复制修改参数即可。

## 1. 合并 PDF

```python
import pymupdf
result = pymupdf.open()
for path in ["a.pdf", "b.pdf"]:
    result.insert_pdf(pymupdf.open(path))
result.save("merged.pdf")
```

## 2. 拆分 PDF

```python
import pymupdf
doc = pymupdf.open("input.pdf")
# 按页码范围拆分
for i, (start, end) in enumerate([(0,2), (3,5)]):
    new = pymupdf.open()
    new.insert_pdf(doc, from_page=start, to_page=end)
    new.save(f"part{i+1}.pdf")
```

```python
# 每 N 页拆分
import pymupdf, math
doc = pymupdf.open("input.pdf")
n = 10
for i in range(math.ceil(len(doc)/n)):
    new = pymupdf.open()
    new.insert_pdf(doc, from_page=i*n, to_page=min((i+1)*n-1, len(doc)-1))
    new.save(f"part{i+1}.pdf")
```

## 3. 添加页码

```python
import pymupdf
doc = pymupdf.open("input.pdf")
total = len(doc)
for i, page in enumerate(doc):
    text = f"{i+1} / {total}"
    rect = pymupdf.Rect(0, page.rect.height - 40, page.rect.width, page.rect.height)
    page.insert_textbox(rect, text, fontsize=10, align=pymupdf.TEXT_ALIGN_CENTER,
                        color=(0.4, 0.4, 0.4))
doc.save("output_paged.pdf")
```

## 4. 添加水印

```python
import pymupdf
doc = pymupdf.open("input.pdf")
for page in doc:
    # 文字水印：45度倾斜 半透明
    tw = pymupdf.TextWriter(page.rect)
    font = pymupdf.Font("helv")
    text = "CONFIDENTIAL"
    fontsize = 60
    # 计算居中位置
    text_length = font.text_length(text, fontsize=fontsize)
    x = (page.rect.width - text_length) / 2
    y = page.rect.height / 2
    tw.append((x, y), text, font=font, fontsize=fontsize)
    tw.write_text(page, opacity=0.3, color=(0.8, 0.8, 0.8), morph=(pymupdf.Point(x + text_length/2, y), pymupdf.Matrix(45)))
doc.save("output_watermarked.pdf")
```

**简易版（逐页插入半透明文本，不旋转）：**

```python
import pymupdf
doc = pymupdf.open("input.pdf")
for page in doc:
    page.insert_text(
        pymupdf.Point(page.rect.width/2 - 100, page.rect.height/2),
        "CONFIDENTIAL", fontsize=50, color=(0.8, 0.8, 0.8),
        rotate=45, overlay=True
    )
doc.save("output_watermarked.pdf")
```

## 5. 旋转 PDF

```python
import pymupdf
doc = pymupdf.open("input.pdf")
for page in doc:
    page.set_rotation(90)  # 90, 180, 270
doc.save("output_rotated.pdf")
```

指定页码范围：

```python
for i in range(2, 5):  # 第3-5页（0-indexed）
    doc[i].set_rotation(90)
```

## 6. PDF 加密

```python
import pymupdf
doc = pymupdf.open("input.pdf")
# owner_pass=权限密码 user_pass=打开密码
# permissions: pymupdf.PDF_PERM_PRINT | pymupdf.PDF_PERM_COPY 等
doc.save("output_encrypted.pdf",
         encryption=pymupdf.PDF_ENCRYPT_AES_256,
         owner_pw="owner123",
         user_pw="user123",
         permissions=pymupdf.PDF_PERM_PRINT)
```

## 7. 整理页面（删除/重排/提取）

```python
import pymupdf
doc = pymupdf.open("input.pdf")

# 删除页面（0-indexed）
doc.delete_pages([1, 3])  # 删除第2、4页

# 重新排序
doc.select([2, 0, 1, 3])  # 新顺序

# 提取页面
new = pymupdf.open()
new.insert_pdf(doc, from_page=2, to_page=4)
new.save("extracted.pdf")

doc.save("output_reordered.pdf")
```

## 8. PDF 签名（叠加图片）

```python
import pymupdf
doc = pymupdf.open("input.pdf")
page = doc[0]  # 签名放在第1页
img_rect = pymupdf.Rect(350, 700, 550, 780)  # 右下角区域
page.insert_image(img_rect, filename="signature.png", overlay=True)
doc.save("output_signed.pdf")
```

## 9. PDF 转 JPG

```python
import pymupdf
doc = pymupdf.open("input.pdf")
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=150)
    pix.save(f"output_p{i+1}.jpg")
```

指定页码范围和 DPI：

```python
for i in range(2, 5):  # 第3-5页
    pix = doc[i].get_pixmap(dpi=300)
    pix.save(f"output_p{i+1}.jpg")
```

## 10. PDF 转 PDF/A

```python
import pikepdf
pdf = pikepdf.open("input.pdf")
# 设置 PDF/A 元数据
with pdf.open_metadata() as meta:
    meta["pdfaid:part"] = "2"
    meta["pdfaid:conformance"] = "B"
    meta["dc:title"] = "Converted Document"
pdf.save("output_pdfa.pdf", linearize=True)
```

> 注意：这是简化版 PDF/A 标记，严格合规需要嵌入字体和色彩配置文件。

## 11. PDF 转 Word

```python
from pdf2docx import Converter
cv = Converter("input.pdf")
cv.convert("output.docx")
cv.close()
```

指定页码范围：

```python
cv.convert("output.docx", start=0, end=5)  # 前5页
```

## 12. PDF 转 Excel

```python
import pymupdf
from openpyxl import Workbook

doc = pymupdf.open("input.pdf")
wb = Workbook()

for i, page in enumerate(doc):
    tables = page.find_tables()
    if tables.tables:
        ws = wb.active if i == 0 else wb.create_sheet(title=f"Page{i+1}")
        for table in tables:
            data = table.extract()
            for row_idx, row in enumerate(data):
                for col_idx, cell in enumerate(row):
                    ws.cell(row=row_idx+1, column=col_idx+1, value=cell)

wb.save("output.xlsx")
```

## 13. PDF 转 PPT

**模式 A：每页作为背景图片**

```python
import pymupdf
from pptx import Presentation
from pptx.util import Inches

doc = pymupdf.open("input.pdf")
prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)

for page in doc:
    pix = page.get_pixmap(dpi=200)
    img_path = "/tmp/_pdf_page_temp.png"
    pix.save(img_path)
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
    slide.shapes.add_picture(img_path, Inches(0), Inches(0),
                             prs.slide_width, prs.slide_height)

prs.save("output.pptx")
```

**模式 B：提取文字填入文本框**

```python
import pymupdf
from pptx import Presentation
from pptx.util import Inches, Pt

doc = pymupdf.open("input.pdf")
prs = Presentation()

for page in doc:
    text = page.get_text()
    slide = prs.slides.add_slide(prs.slide_layouts[1])  # title+content
    slide.shapes[1].text_frame.text = text

prs.save("output.pptx")
```

## 14. PDF 压缩

```python
import pymupdf
doc = pymupdf.open("input.pdf")
doc.save("output_compressed.pdf",
         garbage=4,      # 最大垃圾回收级别
         deflate=True,   # 压缩流
         clean=True)     # 清理冗余
```

带图片压缩（更小体积）：

```python
import pymupdf
doc = pymupdf.open("input.pdf")
for page in doc:
    for img in page.get_images(full=True):
        xref = img[0]
        pix = pymupdf.Pixmap(doc, xref)
        if pix.width > 1000 or pix.height > 1000:
            # 缩小到原来一半
            new_pix = pymupdf.Pixmap(pix, pix.width//2, pix.height//2)
            doc.update_stream(xref, new_pix.tobytes())
doc.save("output_compressed.pdf", garbage=4, deflate=True, clean=True)
```
