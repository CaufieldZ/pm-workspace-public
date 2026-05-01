<!-- cheatsheet-version: 2025-03-31 -->
# 交互大图 · 组件速查手册

## 1. Phone Mockup 常用内部组件

### 1.1 表单页面（带输入框）
```html
<div style="padding:16px 18px;flex:1;overflow:hidden;">
  <!-- 标题图标 -->
  <div style="text-align:center;margin-bottom:16px;">
    <div style="font-size:32px;margin-bottom:4px;">🎤</div>
    <div style="font-size:12px;color:var(--dark-text2);">表单说明文字</div>
  </div>
  <!-- 输入框 -->
  <div style="margin-bottom:10px;">
    <div style="font-size:11px;color:var(--dark-text2);margin-bottom:4px;">字段名 *</div>
    <div style="background:var(--dark2);border:1.5px solid var(--dark3);border-radius:8px;padding:10px 12px;font-size:13px;color:var(--dark-text);">
      字段值
    </div>
  </div>
  <!-- 下拉选择 -->
  <div style="margin-bottom:10px;">
    <div style="font-size:11px;color:var(--dark-text2);margin-bottom:4px;">选择字段 *</div>
    <div style="background:var(--dark2);border:1.5px solid var(--dark3);border-radius:8px;padding:10px 12px;font-size:13px;display:flex;align-items:center;">
      <span style="color:var(--dark-text);">选项值</span>
      <span style="margin-left:auto;color:var(--dark-text3);">▾</span>
    </div>
  </div>
  <!-- 多行文本 -->
  <div style="margin-bottom:10px;">
    <div style="font-size:11px;color:var(--dark-text2);margin-bottom:4px;">多行输入 *</div>
    <div style="background:var(--dark2);border:1.5px solid var(--dark3);border-radius:8px;padding:10px 12px;font-size:13px;color:var(--dark-text);min-height:60px;">
      文本内容…
    </div>
  </div>
  <!-- 头像上传 -->
  <div style="margin-bottom:14px;">
    <div style="font-size:11px;color:var(--dark-text2);margin-bottom:4px;">头像</div>
    <div style="width:60px;height:60px;border-radius:30px;background:var(--dark2);border:2px dashed var(--dark3);display:flex;align-items:center;justify-content:center;font-size:20px;color:var(--dark-text3);">+</div>
  </div>
  <!-- 勾选协议 -->
  <div style="display:flex;align-items:flex-start;gap:6px;margin-bottom:14px;">
    <div style="width:16px;height:16px;border-radius:4px;border:2px solid var(--blue);display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px;">
      <span style="font-size:8px;color:var(--blue);">✓</span>
    </div>
    <div style="font-size:10px;color:var(--dark-text2);line-height:1.4;">协议文字说明</div>
  </div>
  <!-- 提交按钮 -->
  <div style="background:var(--blue);border-radius:10px;padding:12px;text-align:center;font-size:14px;font-weight:800;color:#fff;">
    提交
  </div>
</div>
```

### 1.2 结果成功页
```html
<div style="padding:24px 18px;flex:1;text-align:center;">
  <div style="width:80px;height:80px;border-radius:40px;background:rgba(14,203,129,.1);border:3px solid var(--green);margin:20px auto;display:flex;align-items:center;justify-content:center;font-size:36px;">✅</div>
  <div style="font-size:18px;font-weight:900;color:var(--green);margin-bottom:4px;">操作成功！</div>
  <div style="font-size:13px;color:var(--dark-text2);margin-bottom:20px;">描述文字</div>
  <!-- 信息面板 -->
  <div style="background:var(--dark2);border-radius:10px;padding:14px;margin-bottom:12px;text-align:left;">
    <div style="font-size:10px;color:var(--dark-text2);margin-bottom:6px;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;">DETAILS</div>
    <div style="font-size:12px;color:var(--dark-text);line-height:2;">
      <div>✓ 项目 A</div>
      <div>✓ 项目 B</div>
    </div>
  </div>
  <div style="background:var(--blue);border-radius:10px;padding:12px;text-align:center;font-size:14px;font-weight:800;color:#fff;">下一步 →</div>
</div>
```

### 1.3 列表页（Tab + 空态）
```html
<div style="padding:0 14px;flex:1;">
  <!-- Tab 栏 -->
  <div style="display:flex;border-bottom:1.5px solid var(--dark3);margin-bottom:12px;">
    <div style="flex:1;text-align:center;padding:10px;font-size:13px;font-weight:700;color:var(--dark-text);border-bottom:2.5px solid var(--blue);">Tab 1</div>
    <div style="flex:1;text-align:center;padding:10px;font-size:13px;color:var(--dark-text3);">Tab 2</div>
  </div>
  <!-- 空态 -->
  <div style="text-align:center;padding:40px 0;">
    <div style="font-size:48px;margin-bottom:8px;opacity:.3;">📺</div>
    <div style="font-size:13px;color:var(--dark-text3);">暂无记录</div>
  </div>
</div>
```

### 1.4 直播卡片网格
```html
<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
  <div style="background:var(--dark2);border-radius:10px;overflow:hidden;">
    <div style="height:90px;background:var(--dark2);display:flex;align-items:center;justify-content:center;position:relative;">
      <span style="font-size:24px;">📺</span>
      <span style="position:absolute;top:4px;left:4px;background:var(--red);color:#fff;font-size:7px;font-weight:700;padding:2px 4px;border-radius:2px;">🔴 直播</span>
      <span style="position:absolute;bottom:4px;right:4px;font-size:8px;color:var(--dark-text2);background:rgba(0,0,0,.6);padding:1px 4px;border-radius:2px;">👤 1,247</span>
    </div>
    <div style="padding:6px 8px;">
      <div style="font-size:11px;font-weight:700;color:var(--dark-text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">标题</div>
      <div style="font-size:9px;color:var(--dark-text2);">副标题</div>
    </div>
  </div>
</div>
```

### 1.5 底部 Tab 栏
```html
<div style="border-top:1px solid var(--dark2);padding:8px 14px;display:flex;justify-content:space-around;">
  <div style="text-align:center;"><div style="font-size:16px;">🏠</div><div style="font-size:9px;color:var(--dark-text2);">首页</div></div>
  <div style="text-align:center;"><div style="font-size:16px;">📊</div><div style="font-size:9px;color:var(--blue);font-weight:700;">当前</div></div>
  <div style="text-align:center;"><div style="font-size:16px;">💰</div><div style="font-size:9px;color:var(--dark-text2);">交易</div></div>
  <div style="text-align:center;"><div style="font-size:16px;">👤</div><div style="font-size:9px;color:var(--dark-text2);">我的</div></div>
</div>
```

### 1.6 底部弹层 (Bottom Sheet)
```html
<!-- 弹层在 phone 内部，position:relative 的容器中 -->
<div class="ph-overlay" style="height:380px;padding:14px 18px;">
  <!-- 拖拽指示器 -->
  <div style="width:36px;height:4px;background:var(--dark-text3);border-radius:2px;margin:0 auto 12px;"></div>
  <!-- 弹层内容 Tab -->
  <div style="display:flex;border-bottom:1.5px solid var(--dark3);margin-bottom:14px;">
    <div style="flex:1;text-align:center;padding:8px;font-size:14px;font-weight:700;color:var(--dark-text);border-bottom:2.5px solid var(--blue);">Tab A</div>
    <div style="flex:1;text-align:center;padding:8px;font-size:14px;color:var(--dark-text3);">Tab B</div>
  </div>
  <!-- 弹层列表内容 -->
  <div style="overflow:hidden;">
    <!-- ... 列表项 ... -->
  </div>
</div>
```

## 2. Web Frame 常用内部组件

### 2.1 CMS 数据表格
```html
<div style="border:1.5px solid var(--border);border-radius:10px;overflow:hidden;">
  <!-- 表头 -->
  <div style="display:grid;grid-template-columns:2.2fr 1fr 0.8fr 0.8fr 1.4fr;background:#f8f9fb;border-bottom:1.5px solid var(--border);padding:8px 12px;font-size:10px;font-weight:700;color:var(--text3);letter-spacing:.5px;">
    <span>列 A</span><span>列 B</span><span>列 C</span><span>状态</span><span>操作</span>
  </div>
  <!-- 数据行 -->
  <div style="display:grid;grid-template-columns:2.2fr 1fr 0.8fr 0.8fr 1.4fr;padding:10px 12px;align-items:center;border-bottom:1px solid #f1f5f9;">
    <div>
      <div style="font-size:12px;font-weight:600;color:var(--text);">主要信息</div>
      <div style="font-size:10px;color:var(--text3);">次要信息</div>
    </div>
    <span style="font-size:11px;color:var(--text2);">内容</span>
    <span style="font-size:11px;font-weight:700;color:var(--green);font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;">1,247</span>
    <span style="font-size:10px;padding:2px 6px;border-radius:3px;background:#fef2f2;color:var(--red);font-weight:700;">🔴 状态</span>
    <div style="display:flex;gap:6px;">
      <span style="font-size:10px;color:var(--blue);font-weight:600;">操作A</span>
      <span style="font-size:10px;color:var(--text3);">|</span>
      <span style="font-size:10px;color:#dc2626;">操作B</span>
    </div>
  </div>
</div>
```

### 2.2 数据统计面板
```html
<div style="background:#f8f9fb;border:1.5px solid var(--border);border-radius:8px;padding:10px;">
  <div style="font-size:10px;font-weight:700;color:var(--text);margin-bottom:6px;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;letter-spacing:.06em;">数据标题</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;">
    <div>
      <div style="font-size:10px;color:var(--text3);">指标 A</div>
      <div style="font-size:16px;font-weight:900;color:var(--text);font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;">1,247</div>
    </div>
    <div>
      <div style="font-size:10px;color:var(--text3);">指标 B</div>
      <div style="font-size:16px;font-weight:900;color:var(--green);font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;">+23%</div>
    </div>
  </div>
</div>
```

### 2.3 组件开关卡片
```html
<div style="background:#fff;border:1.5px solid var(--border);border-radius:10px;padding:14px 16px;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
    <div style="width:36px;height:36px;border-radius:10px;background:#ecfdf5;display:flex;align-items:center;justify-content:center;font-size:18px;">🎤</div>
    <div style="flex:1;">
      <div style="font-size:14px;font-weight:800;color:var(--text);">组件名称</div>
      <div style="font-size:10px;color:var(--text3);">组件描述</div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;">
      <span style="font-size:10px;padding:3px 10px;border-radius:4px;background:#dcfce7;color:#15803d;font-weight:700;">已启用</span>
      <span style="font-size:11px;color:var(--text3);padding:4px 10px;background:#f1f5f9;border-radius:4px;">设置</span>
    </div>
  </div>
  <!-- 白名单 -->
  <div style="background:#f8f9fb;border:1px solid var(--border);border-radius:8px;padding:10px 12px;">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
      <span style="font-size:11px;font-weight:700;color:var(--text);">白名单</span>
      <span style="font-size:10px;color:var(--blue);font-weight:600;">+ 添加</span>
    </div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;">
      <span style="font-size:10px;padding:3px 8px;border-radius:4px;background:#fff;border:1px solid var(--border);color:var(--text);">用户名 <span style="color:var(--text3);">✕</span></span>
    </div>
  </div>
</div>
```

### 2.4 OBS 推流配置块
```html
<div style="background:#f8f9fb;border:1.5px solid var(--border);border-radius:10px;padding:16px;margin-bottom:12px;">
  <div style="font-size:13px;font-weight:800;color:var(--text);margin-bottom:10px;">🔧 推流配置</div>
  <div style="margin-bottom:10px;">
    <div style="font-size:10px;color:var(--text3);margin-bottom:3px;font-weight:600;">推流地址</div>
    <div style="display:flex;align-items:center;gap:6px;">
      <div style="flex:1;background:#fff;border:1.5px solid var(--border);border-radius:6px;padding:8px 10px;font-size:11px;color:var(--text);font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;word-break:break-all;">rtmp://example.com/stream/</div>
      <div style="padding:6px 10px;border-radius:6px;background:var(--blue);color:#fff;font-size:10px;font-weight:700;flex-shrink:0;">复制</div>
    </div>
  </div>
</div>
```

## 3. 连接组件

### 3.1 屏幕间间距（无箭头）
```html
<div style="width:20px;"></div>
```

### 3.2 文字间距（大间距）
```html
<div style="width:32px;flex-shrink:0;"></div>
```

### 3.3 多行注释卡片（横排）
```html
<div style="display:flex;gap:20px;margin-top:8px;margin-bottom:20px;">
  <div class="ann-card" style="flex:1;">
    <div class="card-title">卡片 A <span class="ann-tag new">NEW</span></div>
    <div style="font-size:13px;line-height:1.8;">内容...</div>
  </div>
  <div class="ann-card" style="flex:1;">
    <div class="card-title">卡片 B</div>
    <div style="font-size:13px;line-height:1.8;">内容...</div>
  </div>
</div>
```

## 4. 颜色速查

| 用途 | 箭头线class | 箭头文字class | 标注框class | 编号class |
|------|------------|-------------|-----------|----------|
| 蓝·布局 | `.al.b` | `.tx.b` | `.anno.blue` | `.anno-n.blue` / `.ann-num.blue` |
| 绿·新增 | `.al.g` | `.tx.g` | `.anno.green` | `.anno-n.green` / `.ann-num.green` |
| 红·重要 | `.al.r` | `.tx.r` | `.anno.red` | `.anno-n.red` / `.ann-num.red` |
| 紫·Web | `.al.p` | `.tx.p` | `.anno.purple` | `.anno-n.purple` / `.ann-num.purple` |
| 琥珀·流程 | `.al.a` | `.tx.a` | `.anno.amber` | `.anno-n.amber` / `.ann-num.amber` |

## 5. 常用状态标签

```html
<!-- 状态 Badge -->
<span style="font-size:10px;padding:2px 6px;border-radius:3px;background:#fef2f2;color:var(--red);font-weight:700;">🔴 直播中</span>
<span style="font-size:10px;padding:2px 6px;border-radius:3px;background:#dcfce7;color:#15803d;font-weight:600;">预约中</span>
<span style="font-size:10px;padding:2px 6px;border-radius:3px;background:#f1f5f9;color:var(--text3);">已结束</span>

<!-- 筛选 Tab -->
<span style="font-size:11px;padding:3px 10px;border-radius:4px;background:var(--red);color:#fff;font-weight:600;">直播中 3</span>
<span style="font-size:11px;padding:3px 10px;border-radius:4px;background:#f1f5f9;color:var(--text3);">预约 5</span>

<!-- 搜索框 -->
<div style="margin-left:auto;background:#f1f5f9;border:1px solid var(--border);border-radius:6px;padding:3px 10px;font-size:11px;color:var(--text3);">🔍 搜索</div>

<!-- 提示条 -->
<div style="display:flex;align-items:center;gap:8px;padding:10px 14px;background:#fffbeb;border:1.5px solid #fcd34d;border-radius:8px;">
  <div style="width:10px;height:10px;border-radius:5px;background:var(--amber);flex-shrink:0;"></div>
  <div style="font-size:12px;color:#92400e;font-weight:600;">等待中…</div>
</div>

<!-- 提示框 -->
<div style="background:rgba(41,121,255,.05);border:1.5px solid rgba(41,121,255,.15);border-radius:8px;padding:10px 14px;">
  <div style="font-size:11px;color:var(--blue);line-height:1.6;">
    💡 <b>提示：</b>提示内容
  </div>
</div>
```

