<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
<!-- cheatsheet-version: 2025-03-31 -->
# 业务组件库 · 交易组件（示例）

> 此文件存放你的业务领域专属 UI 组件。
> 交互大图 / 原型生成时，会从这里复制组件 HTML，确保跨场景视觉一致。
> 可以修改占位符内容（如商品名、金额），但不要改 HTML 结构和 CSS。
>
> **如何使用**：将你的真实业务组件 HTML 粘贴到下方，按「编号 + 标题 + 代码块」格式组织。
> 下面是一个示例组件，展示期望的格式。

---

### 一、交易组件

#### 1. 订单卡片 · 选中态（示例）
```html
  <div class="flow-col"><span class="phone-label">B-1a · 订单选中</span><div class="phone" style="height:320px;"><div style="background:#1B1D22;padding:10px 16px;border-bottom:1.5px solid #2B2F36;"><span style="color:#EAECEF;font-size:15px;font-weight:700;border-bottom:2px solid #1A6CFF;padding-bottom:8px;">待处理</span><span style="color:#5E6673;font-size:15px;margin-left:20px;">已完成</span></div><div style="padding:12px 16px;background:rgba(14,203,129,.08);border:2px solid rgba(14,203,129,.4);border-radius:8px;margin:4px 12px;display:flex;align-items:center;justify-content:space-between;"><div style="display:flex;align-items:center;gap:8px;"><div style="width:20px;height:20px;border-radius:4px;background:#0ECB81;display:flex;align-items:center;justify-content:center;color:#fff;font-size:10px;font-weight:700;">+</div><div><div style="display:flex;gap:6px;"><span style="color:#EAECEF;font-size:15px;font-weight:700;">订单 #10234</span><span style="color:#848E9C;font-size:11px;">进行中</span></div><div style="color:#0ECB81;font-size:12px;">处理中</div></div></div><span style="color:#0ECB81;font-size:15px;font-weight:700;font-family:'IBM Plex Mono',monospace;">$1,234.56</span></div></div></div>
```

#### 2. 订单卡片 · 预览块（示例）
```html
  <div class="flow-col"><span class="phone-label">B-1b · 预览块</span><div class="phone" style="height:280px;"><div style="padding:14px 16px;"><div style="background:#1B1D22;border:1.5px solid #2B2F36;border-radius:10px;padding:14px;position:relative;"><span style="position:absolute;top:8px;right:10px;color:#5E6673;font-size:14px;">x</span><div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;"><span style="color:#EAECEF;font-size:14px;font-weight:700;">订单 #10234</span><span style="color:#848E9C;font-size:11px;">进行中</span></div><div style="color:#848E9C;font-size:11px;">订单金额</div><div style="color:#0ECB81;font-size:20px;font-weight:700;font-family:'IBM Plex Mono',monospace;">$1,234.56</div></div></div></div></div>
```

<!-- 
  在此追加更多组件：
  #### 3. 你的组件名称
  ```html
  你的组件 HTML
  ```
-->
