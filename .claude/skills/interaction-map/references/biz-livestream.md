<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
<!-- cheatsheet-version: 2025-03-31 -->
# 业务组件库 · 直播组件（示例）

> 此文件存放直播间、主播工作台等直播类 UI 组件。
> 交互大图 / 原型生成时，会从这里复制组件 HTML，确保跨场景视觉一致。
> 可以修改占位符内容（如主播名、聊天内容），但不要改 HTML 结构和 CSS。
>
> **如何使用**：将你的真实业务组件 HTML 粘贴到下方，按「编号 + 标题 + 代码块」格式组织。

---

### 三、直播组件

#### 17. 直播频道浏览页（示例）
```html
    <span class="phone-label">E-1a · 频道浏览</span>
    <div class="phone" style="min-height:400px;display:flex;flex-direction:column;">
      <div class="ph-status"><span>9:41</span><span>🔋</span></div>
      <div class="ph-top" style="border-bottom:1px solid var(--dark2);">
        <span style="font-size:16px;font-weight:900;color:var(--dark-text);">直播</span>
        <div style="margin-left:auto;display:flex;gap:8px;">
          <span style="font-size:11px;color:var(--dark-text2);padding:4px 10px;background:var(--dark2);border-radius:12px;">推荐</span>
          <span style="font-size:11px;color:var(--blue);padding:4px 10px;background:rgba(41,121,255,.1);border-radius:12px;font-weight:700;">热门</span>
        </div>
      </div>
      <div style="padding:10px 14px;flex:1;">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
          <div style="background:var(--dark2);border-radius:10px;overflow:hidden;">
            <div style="height:90px;background:linear-gradient(135deg,#1a1a2e,#16213e);display:flex;align-items:center;justify-content:center;position:relative;"><span style="font-size:24px;">📺</span><span style="position:absolute;top:4px;left:4px;background:var(--red);color:#fff;font-size:7px;font-weight:700;padding:2px 4px;border-radius:2px;">LIVE</span></div>
            <div style="padding:6px 8px;"><div style="font-size:11px;font-weight:700;color:var(--dark-text);">主播昵称 · 直播标题</div></div>
          </div>
        </div>
      </div>
    </div>
    <div class="flow-note">直播频道页 · 卡片网格布局</div>
  </div>
```

<!-- 
  在此追加更多直播组件：
  #### 18. 直播间全貌
  ```html
  你的组件 HTML
  ```
-->
