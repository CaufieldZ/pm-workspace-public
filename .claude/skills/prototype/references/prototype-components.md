<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# 可交互原型 · 通用组件库

> 所有组件不绑定具体业务，`<!-- [FILL] -->` 处按实际产品填充。
> 前台组件用深色 Token，后台组件用浅色 Token。
> 遇到本库没有的业务组件（直播间、K线图、聊天室等），按对应 Token 自行构建。

---

## A. 前台深色组件

### A1. 标准卡片（三态）
```html
<!-- 正常态 -->
<div style="background:#161A1E;border:1px solid #2B3139;border-radius:10px;padding:14px;cursor:pointer;transition:.15s;display:flex;flex-direction:column;min-height:120px;" onmouseover="this.style.borderColor='#2D81FF'" onmouseout="this.style.borderColor='#2B3139'">
  <div style="font-size:9px;padding:2px 6px;border-radius:3px;display:inline-block;width:fit-content;font-weight:600;color:#0ECB81;background:rgba(14,203,129,.1);"><!-- [FILL] 状态文字 --></div>
  <div style="font-size:13px;font-weight:700;margin-top:6px;line-height:1.4;"><!-- [FILL] 标题 --></div>
  <div style="font-size:11px;color:#848E9C;margin-top:4px;"><!-- [FILL] 描述 --></div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:auto;padding-top:10px;">
    <span style="font-size:11px;color:#5E6673;"><!-- [FILL] 时间/标签 --></span>
    <button style="background:#2D81FF;color:#fff;padding:4px 12px;border-radius:5px;font-size:11px;font-weight:600;border:none;cursor:pointer;"><!-- [FILL] CTA --></button>
  </div>
</div>

<!-- 待处理态（橙色标记） -->
<!-- 把状态色改为 color:#FF8C00;background:rgba(255,140,0,.1) -->

<!-- 禁用/结束态（半透明） -->
<!-- 加 opacity:.55; 且 hover 不变色 -->
```

### A2. 封面图卡片
```html
<div style="background:#161A1E;border:1px solid #2B3139;border-radius:10px;overflow:hidden;cursor:pointer;transition:border-color .2s;" onmouseover="this.style.borderColor='#2D81FF'" onmouseout="this.style.borderColor='#2B3139'">
  <!-- 封面图区域 -->
  <div style="height:100px;background:linear-gradient(135deg,#0a1a3a,#162040);display:flex;align-items:center;justify-content:center;position:relative;">
    <div style="font-size:32px;"><!-- [FILL] icon/图 --></div>
    <div style="position:absolute;top:8px;left:8px;font-size:8px;color:#0ECB81;background:rgba(14,203,129,.15);padding:2px 6px;border-radius:3px;font-weight:700;"><!-- [FILL] 状态 --></div>
    <div style="position:absolute;top:8px;right:8px;font-size:9px;color:#F6465D;font-weight:800;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;"><!-- [FILL] 倒计时 --></div>
  </div>
  <!-- 信息区域 -->
  <div style="padding:10px 14px;">
    <div style="font-size:13px;font-weight:700;color:#EAECEF;"><!-- [FILL] --></div>
    <div style="font-size:11px;color:#848E9C;margin-top:4px;"><!-- [FILL] --></div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;">
      <span style="font-size:10px;color:#5E6673;"><!-- [FILL] --></span>
      <button style="background:#2D81FF;color:#fff;padding:4px 12px;border-radius:5px;font-size:11px;font-weight:600;border:none;cursor:pointer;"><!-- [FILL] --></button>
    </div>
  </div>
</div>
```

### A3. Wide Card（跨栏大卡）
```html
<div style="grid-column:1/-1;background:linear-gradient(135deg,#091626,#0e1b2e);border:1px solid rgba(45,129,255,.3);border-radius:10px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;cursor:pointer;transition:.15s;" onmouseover="this.style.borderColor='#2D81FF'" onmouseout="this.style.borderColor='rgba(45,129,255,.3)'">
  <div>
    <div style="font-size:9px;color:#FFD740;background:rgba(255,215,64,.12);padding:2px 8px;border-radius:4px;font-weight:700;display:inline-block;margin-bottom:4px;"><!-- [FILL] 标签 --></div>
    <h3 style="font-size:16px;font-weight:800;color:#EAECEF;"><!-- [FILL] 标题 --></h3>
    <div style="font-size:12px;color:#848E9C;margin-top:4px;"><!-- [FILL] 描述 --></div>
  </div>
  <div style="display:flex;align-items:center;gap:16px;flex-shrink:0;">
    <div style="font-size:18px;font-weight:800;color:#F6465D;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;"><!-- [FILL] 数据 --></div>
    <button style="background:#2D81FF;color:#fff;padding:6px 18px;border-radius:5px;font-size:12px;font-weight:600;border:none;cursor:pointer;"><!-- [FILL] CTA --></button>
  </div>
</div>
```

### A4. 列表项（Feed 流/帖子/通知）
```html
<div style="background:#161A1E;border-bottom:1px solid #2B3139;padding:14px 16px;display:flex;gap:12px;cursor:pointer;transition:.15s;" onmouseover="this.style.background='#1E2329'" onmouseout="this.style.background='#161A1E'">
  <!-- 头像 -->
  <div style="width:40px;height:40px;border-radius:20px;background:#222730;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;"><!-- [FILL] avatar --></div>
  <!-- 内容 -->
  <div style="flex:1;min-width:0;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <span style="font-size:13px;font-weight:600;color:#EAECEF;"><!-- [FILL] 用户名 --></span>
      <span style="font-size:10px;color:#5E6673;"><!-- [FILL] 时间 --></span>
    </div>
    <div style="font-size:12px;color:#848E9C;margin-top:4px;line-height:1.5;"><!-- [FILL] 内容摘要 --></div>
    <!-- 操作栏（可选） -->
    <div style="display:flex;gap:16px;margin-top:8px;font-size:11px;color:#5E6673;">
      <span style="cursor:pointer;">💬 <!-- [FILL] 数 --></span>
      <span style="cursor:pointer;">❤️ <!-- [FILL] --></span>
      <span style="cursor:pointer;">🔄 <!-- [FILL] --></span>
    </div>
  </div>
</div>
```

### A5. 图文卡片（社区/资讯）
```html
<div style="background:#161A1E;border:1px solid #2B3139;border-radius:10px;overflow:hidden;cursor:pointer;transition:border-color .2s;" onmouseover="this.style.borderColor='#2D81FF'" onmouseout="this.style.borderColor='#2B3139'">
  <div style="display:flex;gap:12px;padding:14px;">
    <div style="flex:1;min-width:0;">
      <div style="font-size:13px;font-weight:700;color:#EAECEF;line-height:1.4;"><!-- [FILL] 标题 --></div>
      <div style="font-size:11px;color:#848E9C;margin-top:6px;line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;"><!-- [FILL] 摘要 --></div>
      <div style="display:flex;gap:12px;margin-top:8px;font-size:10px;color:#5E6673;">
        <span><!-- [FILL] 作者 --></span><span><!-- [FILL] 时间 --></span><span>👁 <!-- [FILL] --></span>
      </div>
    </div>
    <div style="width:80px;height:80px;border-radius:6px;background:#222730;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:24px;"><!-- [FILL] 封面 --></div>
  </div>
</div>
```

### A6. 专题/分组容器
```html
<div style="padding:0 24px;">
  <div style="display:flex;justify-content:space-between;align-items:center;padding:16px 0 10px;">
    <div style="display:flex;align-items:center;gap:8px;">
      <div style="width:24px;height:24px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:13px;background:rgba(45,129,255,.1);"><!-- [FILL] icon --></div>
      <h3 style="font-size:14px;font-weight:700;color:#EAECEF;"><!-- [FILL] 分组名 --></h3>
      <span style="font-size:11px;color:#5E6673;margin-left:4px;"><!-- [FILL] 计数 --></span>
    </div>
    <div style="font-size:12px;color:#2D81FF;font-weight:600;cursor:pointer;">查看全部 ›</div><!-- 不需要则删除 -->
  </div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding-bottom:8px;">
    <!-- [FILL] 内部放卡片组件 -->
  </div>
</div>
```

### A7. Hero / Banner 区
```html
<div style="background:linear-gradient(135deg,#060e1f,#0a1428);border-bottom:1px solid rgba(45,129,255,.18);padding:24px;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <div>
      <div style="font-size:20px;font-weight:800;color:#EAECEF;display:flex;align-items:center;gap:8px;">
        <!-- [FILL] ⚡ 标题 -->
        <span style="font-size:10px;background:#2D81FF;color:#fff;padding:2px 8px;border-radius:4px;font-weight:700;"><!-- [FILL] 标签 --></span>
      </div>
      <div style="font-size:12px;color:#848E9C;margin-top:4px;"><!-- [FILL] 副标题 --></div>
    </div>
    <div style="display:flex;gap:10px;">
      <!-- [FILL] 右侧内容（广告位/操作按钮/数据等） -->
    </div>
  </div>
</div>
```

### A8. 轮播卡片
```html
<div style="width:280px;flex-shrink:0;background:#161A1E;border:1px solid #2B3139;border-radius:10px;padding:14px;cursor:pointer;transition:.15s;" onmouseover="this.style.borderColor='#2D81FF'" onmouseout="this.style.borderColor='#2B3139'">
  <div style="font-size:9px;color:#2D81FF;background:rgba(45,129,255,.1);padding:2px 8px;border-radius:4px;display:inline-block;font-weight:700;margin-bottom:6px;"><!-- [FILL] 标签 --></div>
  <h3 style="font-size:14px;font-weight:700;color:#EAECEF;"><!-- [FILL] --></h3>
  <div style="font-size:11px;color:#848E9C;margin-top:4px;"><!-- [FILL] --></div>
  <div style="display:flex;gap:4px;margin-top:8px;">
    <div style="width:14px;height:5px;border-radius:3px;background:#2D81FF;"></div>
    <div style="width:5px;height:5px;border-radius:3px;background:#363C45;"></div>
    <div style="width:5px;height:5px;border-radius:3px;background:#363C45;"></div>
  </div>
</div>
```

### A9. App 手机 Mockup
```html
<div style="width:375px;background:#0B0E11;border-radius:28px;border:3px solid #2B2F36;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,.3);">
  <!-- 状态栏 -->
  <div style="display:flex;justify-content:space-between;padding:6px 20px 4px;font-size:11px;color:#848E9C;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;"><span>9:41</span><span>5G ▁▂▃▅ 🔋</span></div>
  <!-- 顶栏 -->
  <div style="background:#0D1117;padding:0 12px;height:36px;display:flex;align-items:center;gap:4px;border-bottom:1px solid #2B3139;">
    <span style="font-size:14px;color:#848E9C;">←</span>
    <b style="font-size:12px;color:#EAECEF;"><!-- [FILL] 页面标题 --></b>
  </div>
  <!-- 内容区 -->
  <div style="padding:10px 12px;min-height:400px;">
    <!-- [FILL] 页面内容 -->
  </div>
  <!-- 底部 Tab -->
  <div style="display:flex;background:#0D1117;border-top:1px solid #2B3139;height:42px;">
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;font-size:7px;color:#5E6673;"><span style="font-size:14px;">🏠</span><!-- [FILL] --></div>
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;font-size:7px;color:#2D81FF;"><span style="font-size:14px;">🎯</span><!-- [FILL] 当前 --></div>
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px;font-size:7px;color:#5E6673;"><span style="font-size:14px;">👤</span><!-- [FILL] --></div>
  </div>
</div>
```

### A10. 设备切换器
```html
<div style="display:flex;background:#1E2329;border-radius:6px;overflow:hidden;">
  <div onclick="switchDevice('webView','appView',[this,this.nextElementSibling],0)" style="padding:6px 16px;font-size:11px;font-weight:600;cursor:pointer;color:#EAECEF;background:#2D81FF;border-radius:6px;">🖥 Web</div>
  <div onclick="switchDevice('webView','appView',[this.previousElementSibling,this],1)" style="padding:6px 16px;font-size:11px;font-weight:600;cursor:pointer;color:#5E6673;">📱 App</div>
</div>
```

### A11. 空态
```html
<div style="text-align:center;padding:60px 0;">
  <div style="font-size:48px;margin-bottom:12px;opacity:.3;">📭</div>
  <div style="font-size:14px;color:#5E6673;"><!-- [FILL] 空态文案 --></div>
  <button style="margin-top:16px;background:#2D81FF;color:#fff;padding:8px 24px;border-radius:6px;font-size:13px;font-weight:600;border:none;cursor:pointer;"><!-- [FILL] CTA（可选） --></button>
</div>
```

---

## B. 管理台浅色组件

### B1. 筛选栏
```html
<div style="background:#FFF;border-radius:8px;border:1px solid #E4E7ED;padding:16px 20px;margin-bottom:16px;">
  <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;">
    <div style="display:flex;align-items:center;gap:4px;">
      <span style="font-size:12px;color:#4E5969;white-space:nowrap;"><!-- [FILL] 字段名 -->：</span>
      <select style="padding:5px 28px 5px 8px;border:1px solid #E4E7ED;border-radius:4px;font-size:12px;"><option>全部</option><option><!-- [FILL] --></option></select>
    </div>
    <button style="padding:6px 16px;border-radius:4px;font-size:12px;font-weight:500;background:#2D81FF;color:#fff;border:1px solid #2D81FF;cursor:pointer;">🔍 查询</button>
    <button style="padding:6px 16px;border-radius:4px;font-size:12px;font-weight:500;background:transparent;color:#4E5969;border:1px solid #E4E7ED;cursor:pointer;">重置</button>
  </div>
</div>
```

### B2. 数据表格
```html
<div style="background:#FFF;border-radius:8px;border:1px solid #E4E7ED;overflow:hidden;">
  <table style="width:100%;border-collapse:collapse;font-size:12px;">
    <thead><tr>
      <th style="background:#FAFBFC;padding:10px 8px;text-align:left;font-weight:600;color:#4E5969;border-bottom:1px solid #E4E7ED;"><!-- [FILL] --></th>
      <th style="background:#FAFBFC;padding:10px 8px;text-align:left;font-weight:600;color:#4E5969;border-bottom:1px solid #E4E7ED;">状态</th>
      <th style="background:#FAFBFC;padding:10px 8px;text-align:left;font-weight:600;color:#4E5969;border-bottom:1px solid #E4E7ED;">操作</th>
    </tr></thead>
    <tbody>
      <tr style="border-bottom:1px solid #E4E7ED;">
        <td style="padding:10px 8px;"><b><!-- [FILL] --></b></td>
        <td style="padding:10px 8px;"><span style="color:#00B42A;font-weight:600;">● 已上线</span></td>
        <td style="padding:10px 8px;">
          <div style="display:flex;gap:4px;">
            <span style="font-size:11px;cursor:pointer;padding:2px 8px;border-radius:3px;color:#FF7D00;background:#FFF3E0;">下线</span>
            <span style="font-size:11px;cursor:pointer;padding:2px 8px;border-radius:3px;color:#2D81FF;background:#EEF2FF;">编辑</span>
            <span style="font-size:11px;cursor:pointer;padding:2px 8px;border-radius:3px;color:#F53F3F;background:#FFEBEE;">删除</span>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

### B3. 表单区块
```html
<div style="margin-bottom:24px;">
  <div style="font-size:14px;font-weight:700;margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid #E4E7ED;display:flex;align-items:center;gap:6px;">📝 <!-- [FILL] 区块标题 --></div>
  <!-- 文本输入 -->
  <div style="display:flex;align-items:flex-start;margin-bottom:14px;">
    <div style="width:110px;text-align:right;padding-right:12px;padding-top:7px;font-size:12px;color:#4E5969;flex-shrink:0;"><span style="color:#F53F3F;">*</span> <!-- [FILL] --></div>
    <div style="flex:1;"><input style="width:100%;max-width:400px;padding:7px 10px;border:1px solid #E4E7ED;border-radius:4px;font-size:13px;" value="<!-- [FILL] -->"></div>
  </div>
  <!-- 下拉选择 -->
  <div style="display:flex;align-items:flex-start;margin-bottom:14px;">
    <div style="width:110px;text-align:right;padding-right:12px;padding-top:7px;font-size:12px;color:#4E5969;flex-shrink:0;"><!-- [FILL] --></div>
    <div style="flex:1;"><select style="padding:7px 10px;border:1px solid #E4E7ED;border-radius:4px;font-size:13px;min-width:200px;"><option><!-- [FILL] --></option></select></div>
  </div>
  <!-- 图片上传 -->
  <div style="display:flex;align-items:flex-start;margin-bottom:14px;">
    <div style="width:110px;text-align:right;padding-right:12px;padding-top:7px;font-size:12px;color:#4E5969;flex-shrink:0;"><!-- [FILL] --></div>
    <div style="flex:1;"><div style="width:120px;height:80px;background:#F5F6FA;border:1px dashed #E4E7ED;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:11px;color:#86909C;cursor:pointer;">📷 上传</div></div>
  </div>
</div>
```

### B4. 配置卡片（拖拽排序 + 开关）
```html
<div style="background:#FFF;border:1px solid #E4E7ED;border-radius:8px;padding:16px;display:flex;align-items:center;gap:16px;transition:.15s;margin-bottom:12px;" onmouseover="this.style.borderColor='#2D81FF'" onmouseout="this.style.borderColor='#E4E7ED'">
  <div style="cursor:grab;color:#C9CDD4;font-size:18px;">⠿</div>
  <div style="width:28px;height:28px;background:#EEF2FF;color:#2D81FF;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex-shrink:0;"><!-- [FILL] 序号 --></div>
  <div style="flex:1;min-width:0;">
    <div style="font-size:15px;font-weight:700;color:#1D2129;"><!-- [FILL] 名称 --></div>
    <div style="font-size:12px;color:#86909C;margin-top:3px;"><!-- [FILL] 规则描述 --></div>
  </div>
  <div style="width:40px;height:22px;border-radius:11px;background:#2D81FF;position:relative;cursor:pointer;flex-shrink:0;" onclick="this.classList.toggle('off');this.style.background=this.classList.contains('off')?'#C9CDD4':'#2D81FF';this.querySelector('i').style.left=this.classList.contains('off')?'2px':'20px';">
    <i style="position:absolute;width:18px;height:18px;border-radius:50%;background:#fff;top:2px;left:20px;transition:.3s;box-shadow:0 1px 3px rgba(0,0,0,.15);"></i>
  </div>
  <div style="display:flex;gap:6px;">
    <button style="padding:4px 10px;font-size:11px;border-radius:4px;background:transparent;color:#4E5969;border:1px solid #E4E7ED;cursor:pointer;">编辑</button>
    <button style="padding:4px 10px;font-size:11px;border-radius:4px;background:transparent;color:#F53F3F;border:1px solid #F53F3F;cursor:pointer;">删除</button>
  </div>
</div>
```

### B5. 弹窗
```html
<!-- 遮罩 + 弹窗 -->
<div id="myModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:95;align-items:center;justify-content:center;" onclick="if(event.target===this)this.style.display='none'">
  <div style="background:#FFF;border-radius:10px;width:600px;max-width:92vw;max-height:85vh;overflow-y:auto;box-shadow:0 12px 40px rgba(0,0,0,.15);">
    <!-- 头部 -->
    <div style="padding:16px 20px;border-bottom:1px solid #E4E7ED;font-size:15px;font-weight:700;display:flex;justify-content:space-between;align-items:center;">
      <span><!-- [FILL] 标题 --></span>
      <span style="cursor:pointer;font-size:18px;color:#86909C;" onclick="this.closest('[id]').style.display='none'">✕</span>
    </div>
    <!-- 内容 -->
    <div style="padding:20px;">
      <!-- [FILL] 表单/内容 -->
    </div>
    <!-- 底部 -->
    <div style="padding:12px 20px;border-top:1px solid #E4E7ED;display:flex;justify-content:flex-end;gap:8px;">
      <button style="padding:6px 16px;border-radius:4px;font-size:12px;background:transparent;color:#4E5969;border:1px solid #E4E7ED;cursor:pointer;" onclick="this.closest('[id]').style.display='none'">取消</button>
      <button style="padding:6px 16px;border-radius:4px;font-size:12px;background:#2D81FF;color:#fff;border:1px solid #2D81FF;cursor:pointer;">保存</button>
    </div>
  </div>
</div>
<!-- 触发：document.getElementById('myModal').style.display='flex' -->
```

### B6. Banner/媒体管理卡片
```html
<div style="background:#FFF;border:1px solid #E4E7ED;border-radius:8px;overflow:hidden;">
  <div style="height:140px;background:linear-gradient(135deg,#0a1a3a,#162040);display:flex;align-items:center;justify-content:center;position:relative;">
    <div style="position:absolute;top:8px;left:8px;background:#2D81FF;color:#fff;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;"><!-- [FILL] 序号 --></div>
    <div style="position:absolute;top:8px;right:8px;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;background:#E8F5E9;color:#2E7D32;"><!-- [FILL] 状态 --></div>
    <div style="font-size:32px;">🖼</div>
  </div>
  <div style="padding:10px 12px;">
    <div style="font-size:13px;font-weight:600;margin-bottom:4px;"><!-- [FILL] 标题 --></div>
    <div style="font-size:11px;color:#86909C;"><!-- [FILL] 描述 --></div>
  </div>
  <div style="padding:8px 12px;border-top:1px solid #E4E7ED;display:flex;gap:6px;justify-content:flex-end;">
    <button style="padding:4px 10px;font-size:11px;border-radius:4px;background:transparent;color:#4E5969;border:1px solid #E4E7ED;cursor:pointer;">编辑</button>
    <button style="padding:4px 10px;font-size:11px;border-radius:4px;background:transparent;color:#F53F3F;border:1px solid #F53F3F;cursor:pointer;">删除</button>
  </div>
</div>
```

### B7. 信息提示框
```html
<div style="font-size:11px;color:#86909C;padding:10px 14px;background:#FAFBFC;border-radius:6px;margin-top:12px;line-height:1.8;border:1px solid #E4E7ED;">
  <b style="color:#4E5969;"><!-- [FILL] 标题：--></b><!-- [FILL] 说明内容 -->
</div>
```

---

## C. 通用交互组件

### C1. 抽屉（深色，前台用）
```html
<!-- 遮罩 -->
<div id="overlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:500;" onclick="closeDrawer()"></div>
<!-- 抽屉面板 -->
<div id="drawer" style="position:fixed;top:52px;right:-440px;width:440px;bottom:0;background:#0B0E11;border-left:1px solid #2B3139;z-index:501;transition:right .3s ease;overflow-y:auto;">
  <div style="background:#161A1E;border-bottom:1px solid #2B3139;padding:14px 20px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:2;">
    <h3 style="font-size:15px;font-weight:700;color:#EAECEF;"><!-- [FILL] 标题 --></h3>
    <span style="color:#5E6673;font-size:20px;cursor:pointer;" onclick="closeDrawer()">✕</span>
  </div>
  <div style="padding:16px 20px;">
    <!-- [FILL] 内容 -->
  </div>
</div>
```

### C2. 段落分隔标题
```html
<!-- 带颜色圆点的段落分隔 -->
<div style="font-size:11px;font-weight:700;color:#0ECB81;margin-bottom:8px;display:flex;align-items:center;gap:5px;">
  <span style="width:6px;height:6px;border-radius:50%;background:#0ECB81;"></span> <!-- [FILL] 段落标题（N） -->
</div>
<!-- 带分隔线的段落分隔 -->
<div style="font-size:11px;font-weight:700;color:#5E6673;margin:14px 0 8px;display:flex;align-items:center;gap:5px;border-top:1px solid #2B3139;padding-top:12px;">
  <span style="width:6px;height:6px;border-radius:50%;background:#5E6673;"></span> <!-- [FILL] -->
</div>
```

### C3. 语种/多标签 Tab
```html
<div style="display:flex;gap:0;border-bottom:1px solid #E4E7ED;margin-bottom:16px;overflow-x:auto;">
  <div style="padding:6px 14px;font-size:12px;color:#2D81FF;cursor:pointer;border-bottom:2px solid #2D81FF;white-space:nowrap;font-weight:600;"><!-- [FILL] 选中 --></div>
  <div style="padding:6px 14px;font-size:12px;color:#86909C;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;"><!-- [FILL] --></div>
  <div style="padding:6px 14px;font-size:12px;color:#86909C;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;"><!-- [FILL] --></div>
</div>
```

---

## D. 数据驱动 CRUD 模式（后台管理必用）

> **硬规则**：后台涉及列表+编辑的页面，必须用此模式。禁止列表写死 HTML 而弹窗另一套数据。

### D1. 完整 CRUD 骨架

```html
<!-- ── 列表区域 ── -->
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
  <span id="itemCount" style="font-size:11px;color:#86909C;">共 0 条</span>
  <button onclick="openAdd()" style="padding:6px 16px;border-radius:4px;font-size:12px;background:#00B42A;color:#fff;border:1px solid #00B42A;cursor:pointer;">＋ 新增</button>
</div>
<div style="background:#FFF;border-radius:8px;border:1px solid #E4E7ED;overflow:hidden;">
  <table style="width:100%;border-collapse:collapse;font-size:12px;">
    <thead><tr>
      <th style="background:#FAFBFC;padding:10px 8px;text-align:left;font-weight:600;color:#4E5969;border-bottom:1px solid #E4E7ED;">名称</th>
      <th style="background:#FAFBFC;padding:10px 8px;text-align:left;font-weight:600;color:#4E5969;border-bottom:1px solid #E4E7ED;">状态</th>
      <th style="background:#FAFBFC;padding:10px 8px;text-align:left;font-weight:600;color:#4E5969;border-bottom:1px solid #E4E7ED;">操作</th>
    </tr></thead>
    <tbody id="listContainer"><!-- JS render --></tbody>
  </table>
</div>

<!-- ── 编辑弹窗（新增/编辑共用） ── -->
<div id="editModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:95;align-items:center;justify-content:center;" onclick="if(event.target===this)this.style.display='none'">
  <div style="background:#FFF;border-radius:10px;width:600px;max-width:92vw;max-height:85vh;overflow-y:auto;box-shadow:0 12px 40px rgba(0,0,0,.15);">
    <div style="padding:16px 20px;border-bottom:1px solid #E4E7ED;font-size:15px;font-weight:700;display:flex;justify-content:space-between;align-items:center;">
      <span id="modalTitle">新增</span>
      <span style="cursor:pointer;font-size:18px;color:#86909C;" onclick="document.getElementById('editModal').style.display='none'">✕</span>
    </div>
    <div style="padding:20px;">
      <div style="display:flex;align-items:flex-start;margin-bottom:14px;">
        <div style="width:80px;text-align:right;padding-right:12px;padding-top:7px;font-size:12px;color:#4E5969;"><span style="color:#F53F3F;">*</span> 名称</div>
        <div style="flex:1;"><input id="f-name" style="width:100%;max-width:400px;padding:7px 10px;border:1px solid #E4E7ED;border-radius:4px;font-size:13px;"></div>
      </div>
      <!-- [FILL] 更多字段 -->
    </div>
    <div style="padding:12px 20px;border-top:1px solid #E4E7ED;display:flex;justify-content:flex-end;gap:8px;">
      <button onclick="document.getElementById('editModal').style.display='none'" style="padding:6px 16px;border-radius:4px;font-size:12px;background:transparent;color:#4E5969;border:1px solid #E4E7ED;cursor:pointer;">取消</button>
      <button onclick="saveItem()" style="padding:6px 16px;border-radius:4px;font-size:12px;background:#2D81FF;color:#fff;border:1px solid #2D81FF;cursor:pointer;">保存</button>
    </div>
  </div>
</div>

<script>
// ── 数据源 ──
var items = [
  { name: '项目A', status: '已上线' },
  { name: '项目B', status: '未上线' },
];
var currentIdx = -1; // -1=新增, >=0=编辑

// ── 渲染（列表+统计全部从数组生成） ──
function renderList() {
  var html = '';
  items.forEach(function(d, i) {
    html += '<tr style="border-bottom:1px solid #E4E7ED;">'
      + '<td style="padding:10px 8px;"><b>' + d.name + '</b></td>'
      + '<td style="padding:10px 8px;">' + d.status + '</td>'
      + '<td style="padding:10px 8px;">'
      +   '<span onclick="openEdit(' + i + ')" style="cursor:pointer;padding:2px 8px;border-radius:3px;font-size:11px;color:#2D81FF;background:#EEF2FF;">编辑</span> '
      +   '<span onclick="deleteItem(' + i + ')" style="cursor:pointer;padding:2px 8px;border-radius:3px;font-size:11px;color:#F53F3F;background:#FFEBEE;">删除</span>'
      + '</td></tr>';
  });
  document.getElementById('listContainer').innerHTML = html;
  document.getElementById('itemCount').textContent = '共 ' + items.length + ' 条';
}

// ── 新增（空表单+默认值） ──
function openAdd() {
  currentIdx = -1;
  document.getElementById('modalTitle').textContent = '新增';
  document.getElementById('f-name').value = '';
  document.getElementById('editModal').style.display = 'flex';
}

// ── 编辑（按索引读数据） ──
function openEdit(idx) {
  currentIdx = idx;
  document.getElementById('modalTitle').textContent = '编辑';
  document.getElementById('f-name').value = items[idx].name;
  document.getElementById('editModal').style.display = 'flex';
}

// ── 保存 = 写数据 + render + 关弹窗 ──
function saveItem() {
  var name = document.getElementById('f-name').value.trim();
  if (!name) { alert('请填写名称'); return; }
  if (currentIdx >= 0) {
    items[currentIdx].name = name;
  } else {
    items.push({ name: name, status: '未上线' });
  }
  renderList();
  document.getElementById('editModal').style.display = 'none';
}

// ── 删除（二次确认） ──
function deleteItem(idx) {
  if (!confirm('确定删除「' + items[idx].name + '」？')) return;
  items.splice(idx, 1);
  renderList();
}

renderList();
</script>
```

### D2. 自检清单

用此模式后交付前检查：
- [ ] 列表 HTML 全部由 `renderList()` 生成，无手写静态行
- [ ] 新增和编辑共用同一个弹窗，靠 `currentIdx` 区分
- [ ] `saveItem()` 内三步：写数组 → `renderList()` → 关弹窗
- [ ] 列表摘要 = 弹窗内数据（因为都从 `items[i]` 读）
- [ ] 统计数字（`itemCount`）在 `renderList()` 内更新
- [ ] 删除有 `confirm()` 二次确认
- [ ] 多个编辑按钮都传了 `i` 索引参数
