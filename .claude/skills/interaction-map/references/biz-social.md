<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
<!-- cheatsheet-version: 2025-03-31 -->
# 业务组件库 · Feed / 社区组件（示例）

> 此文件存放 Feed 流、社区帖子等社交类 UI 组件。
> 交互大图 / 原型生成时，会从这里复制组件 HTML，确保跨场景视觉一致。
> 可以修改占位符内容（如用户名、帖子内容），但不要改 HTML 结构和 CSS。
>
> **如何使用**：将你的真实业务组件 HTML 粘贴到下方，按「编号 + 标题 + 代码块」格式组织。

---

### 二、Feed / 社区组件

#### 9. Feed 条形卡（示例）
```html
  <div class="flow-col"><span class="phone-label">C-1a · Feed 条形卡</span><div class="phone" style="height:280px;"><div style="padding:14px 16px;"><div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;"><div style="width:36px;height:36px;border-radius:18px;background:linear-gradient(135deg,#667eea,#764ba2);"></div><div><div style="color:#EAECEF;font-size:14px;font-weight:600;">UserName</div><div style="color:#5E6673;font-size:11px;">2 分钟前</div></div></div><div style="color:#EAECEF;font-size:14px;line-height:1.5;margin-bottom:10px;">这是一条示例动态内容</div><div style="display:flex;align-items:center;justify-content:space-between;background:#1B1D22;border:1.5px solid #2B2F36;border-radius:8px;padding:10px 12px;"><span style="color:#EAECEF;font-size:13px;font-weight:700;">附件标题</span><span style="color:#0ECB81;font-size:13px;font-weight:700;font-family:'IBM Plex Mono',monospace;">+1,234</span></div></div></div><div class="flow-note">点击整条进详情</div></div>
```

<!-- 
  在此追加更多社区/Feed 组件：
  #### 10. 你的组件名称
  ```html
  你的组件 HTML
  ```
-->
