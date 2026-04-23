<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
# 架构图集 · 组件速查手册

> 本文档是 CSS Grid 卡片布局的组件模板速查。
> 如需 SVG 拓扑图（绝对定位节点 + 箭头连线），参考 svg-topology-extension.md。

## 1. 步骤式资金/账户流转卡片

### 1.1 初始状态行（多账户并排）
```html
<div style="display:flex;gap:6px;">
  <!-- 托管资金 -->
  <div style="flex:0.8;padding:10px 12px;border-radius:6px;background:#f0fdfa;border:1px solid #99f6e4;font-size:11px;">
    <strong style="color:#0d9488;display:block;margin-bottom:4px;">托管资金账户</strong>
    <span style="font-size:20px;font-weight:700;color:#0d9488;">500万</span>
  </div>
  <!-- 交易账户（含可用+冻结两栏） -->
  <div style="flex:2;padding:10px 12px;border-radius:6px;background:#fffbeb;border:1px solid #fde68a;font-size:11px;">
    <strong style="color:#b45309;display:block;margin-bottom:4px;">交易账户</strong>
    <div style="display:flex;gap:8px;margin-top:2px;">
      <div style="flex:1;padding:4px 8px;background:rgba(255,255,255,0.7);border-radius:4px;border:1px solid rgba(217,119,6,0.15);">
        <span style="font-size:10px;color:#b45309;font-weight:600;">可用</span><br>
        <span style="font-size:18px;font-weight:700;color:#b45309;">300万</span>
      </div>
      <div style="flex:1;padding:4px 8px;background:rgba(255,255,255,0.7);border-radius:4px;border:1px dashed rgba(217,119,6,0.2);">
        <span style="font-size:10px;color:#a16207;font-weight:600;">冻结</span><br>
        <span style="font-size:18px;font-weight:700;color:#a16207;">0</span>
      </div>
    </div>
  </div>
  <!-- 锁仓 -->
  <div style="flex:1;padding:10px 12px;border-radius:6px;background:#fef2f2;border:1px solid #fecaca;font-size:11px;">
    <strong style="color:#dc2626;display:block;margin-bottom:4px;">🔒 锁仓</strong>
    <span style="font-size:20px;font-weight:700;color:#dc2626;">200万</span>
  </div>
  <!-- 应还 -->
  <div style="flex:1;padding:10px 12px;border-radius:6px;background:#eef2ff;border:1px solid #c7d2fe;font-size:11px;">
    <strong style="color:#4338ca;display:block;margin-bottom:4px;">应还</strong>
    <span style="font-size:20px;font-weight:700;color:#4338ca;">−500万</span>
  </div>
</div>
```

### 1.2 变动行（高亮变化的账户，其余灰色）
```html
<div style="display:flex;gap:6px;">
  <!-- 不变的账户 → 灰色 -->
  <div style="flex:0.8;padding:8px 10px;border-radius:6px;background:#f8fafc;border:1px solid #e2e8f0;font-size:11px;">
    <strong style="color:#94a3b8;">托管资金</strong><br>
    <span style="font-size:15px;font-weight:700;color:#94a3b8;">0</span>
    <span style="color:#94a3b8;font-size:10px;">不变</span>
  </div>
  <!-- 变动的账户 → 高亮边框 + 变动箭头 -->
  <div style="flex:2;padding:8px 10px;border-radius:6px;background:#fffbeb;border:2px solid #f59e0b;font-size:11px;">
    <strong style="color:#b45309;">交易账户</strong>
    <div style="display:flex;gap:6px;margin-top:2px;">
      <div style="flex:1;padding:3px 6px;background:rgba(255,255,255,0.7);border-radius:3px;border:1px solid rgba(217,119,6,0.15);">
        <span style="font-size:9px;color:#b45309;font-weight:600;">可用</span><br>
        <span style="font-size:15px;font-weight:700;color:#b45309;">290万</span>
        <span style="color:#dc2626;font-size:9px;font-weight:700;">▼−10万</span>
      </div>
      <div style="flex:1;padding:3px 6px;background:rgba(255,255,255,0.7);border-radius:3px;border:1px dashed rgba(217,119,6,0.2);">
        <span style="font-size:9px;color:#a16207;font-weight:600;">冻结</span><br>
        <span style="font-size:15px;font-weight:700;color:#a16207;">10万</span>
        <span style="color:#15803d;font-size:9px;font-weight:700;">▲+10万</span>
      </div>
    </div>
  </div>
</div>
```

### 1.3 步骤编号圆
```html
<!-- 颜色：蓝#1e40af 琥珀#d97706 紫#7c3aed 红#dc2626 绿#15803d -->
<span style="display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;background:#d97706;color:#fff;font-size:13px;font-weight:700;">1</span>
```

### 1.4 底部验证/说明条
```html
<!-- 中性灰 -->
<div style="margin-top:6px;padding:6px 12px;border-radius:4px;background:#f1f5f9;font-size:10px;color:#475569;">
  验证：交易(300+0) + 锁仓200 + 应还(−500) = <strong>0 ✓</strong>
</div>
<!-- 琥珀警告 -->
<div style="margin-top:6px;padding:6px 12px;border-radius:4px;background:#fefce8;border-left:3px solid #eab308;font-size:10px;color:#854d0e;">
  说明文字
</div>
<!-- 红色风险 -->
<div style="margin-top:6px;padding:6px 12px;border-radius:4px;background:#fef2f2;border-left:3px solid #f87171;font-size:10px;color:#991b1b;">
  风险说明
</div>
<!-- 绿色成功 -->
<div style="margin-top:6px;padding:6px 12px;border-radius:4px;background:#ecfdf5;border-left:3px solid #34d399;font-size:10px;color:#065f46;">
  成功说明
</div>
```

## 2. 数据可视化

### 2.1 竞品对比表（inline style table）
```html
<table style="width:100%;border-collapse:collapse;font-size:11px;">
  <thead>
    <tr style="background:#f1f5f9;">
      <th style="padding:8px 10px;text-align:left;border-bottom:2px solid #cbd5e1;font-weight:700;color:#334155;">维度</th>
      <th style="padding:8px 10px;text-align:center;border-bottom:2px solid #cbd5e1;font-weight:700;color:#15803d;">方案 A</th>
      <th style="padding:8px 10px;text-align:center;border-bottom:2px solid #cbd5e1;font-weight:700;color:#b45309;">方案 B</th>
    </tr>
  </thead>
  <tbody>
    <tr style="border-bottom:1px solid #e2e8f0;">
      <td style="padding:6px 10px;">指标名</td>
      <td style="padding:6px 10px;text-align:center;color:#15803d;font-weight:600;">✅ 优势</td>
      <td style="padding:6px 10px;text-align:center;color:#94a3b8;">—</td>
    </tr>
  </tbody>
</table>
```

### 2.2 成本分析卡
```html
<div style="flex:1;padding:20px;border-radius:8px;background:#f0fdf4;border:1.5px solid #86efac;">
  <div style="font-size:13px;font-weight:700;color:#15803d;margin-bottom:12px;">✅ 成本分析</div>
  <div style="display:flex;flex-direction:column;gap:8px;">
    <div style="display:flex;justify-content:space-between;font-size:12px;padding:6px 10px;background:rgba(21,128,61,0.05);border-radius:4px;">
      <span style="color:#334155;">费用项</span>
      <strong style="color:#15803d;">0 USDT</strong>
    </div>
  </div>
</div>
```

### 2.3 五级防护/阶梯条
```html
<div style="display:flex;gap:6px;width:100%;">
  <div style="flex:1;padding:8px 10px;border-radius:5px;background:#f0fdf4;border:1px solid #bbf7d0;font-size:10px;">
    <strong style="color:#15803d;">① < 50%</strong><br><span style="color:#64748b">正常</span>
  </div>
  <div style="color:#cbd5e1;display:flex;align-items:center;">→</div>
  <div style="flex:1;padding:8px 10px;border-radius:5px;background:#fefce8;border:1px solid #fef08a;font-size:10px;">
    <strong style="color:#a16207;">② 50-70%</strong><br><span style="color:#64748b">预警</span>
  </div>
  <div style="color:#cbd5e1;display:flex;align-items:center;">→</div>
  <div style="flex:1;padding:8px 10px;border-radius:5px;background:#fef2f2;border:1.5px solid #f87171;font-size:10px;">
    <strong style="color:#991b1b;">③ > 90%</strong><br><span style="color:#64748b">红色警报</span>
  </div>
</div>
```

### 2.4 分工对比双栏
```html
<div style="display:flex;gap:16px;margin-top:24px;">
  <div style="flex:1;padding:16px;border-radius:8px;background:#fffbeb;border:1.5px solid #fcd34d;">
    <div style="font-size:12px;font-weight:700;color:#b45309;margin-bottom:10px;">A 侧</div>
    <div style="font-size:11px;color:#334155;line-height:2;">
      <div>🔸 任务 1</div>
      <div>🔸 任务 2</div>
    </div>
  </div>
  <div style="flex:1;padding:16px;border-radius:8px;background:#ecfeff;border:1.5px solid #22d3ee;">
    <div style="font-size:12px;font-weight:700;color:#0e7490;margin-bottom:10px;">B 侧</div>
    <div style="font-size:11px;color:#334155;line-height:2;">
      <div>🔹 任务 1</div>
      <div>🔹 任务 2</div>
    </div>
  </div>
</div>
```

### 2.5 双栏横条（对比说明）
```html
<div style="display:flex;border-radius:6px;overflow:hidden;border:1.5px solid #e2e8f0;">
  <div style="flex:1;padding:8px 16px;background:#eff6ff;display:flex;align-items:center;gap:8px;">
    <span style="font-size:16px;">🔒</span>
    <div>
      <div style="font-size:11px;font-weight:700;color:#1e40af;">标题</div>
      <div style="font-size:10px;color:#3b82f6;">说明</div>
    </div>
  </div>
  <div style="width:1.5px;background:#e2e8f0;"></div>
  <div style="flex:1;padding:8px 16px;background:#fff7ed;display:flex;align-items:center;gap:8px;">
    <span style="font-size:16px;">📒</span>
    <div>
      <div style="font-size:11px;font-weight:700;color:#c2410c;">标题</div>
      <div style="font-size:10px;color:#9a3412;">说明</div>
    </div>
  </div>
</div>
```

## 3. SVG 箭头速查

### 3.1 Marker 颜色定义
```html
<defs>
  <!-- 蓝·数据流 -->
  <marker id="ab" markerWidth="7" markerHeight="5" refX="7" refY="2.5" orient="auto">
    <polygon points="0 0,7 2.5,0 5" fill="#3b82f6"/>
  </marker>
  <!-- 琥珀·内部联动 -->
  <marker id="aa" ... fill="#d97706"/>
  <!-- 紫·真实资金 -->
  <marker id="ap" ... fill="#7c3aed"/>
  <!-- 青·链上余额 -->
  <marker id="at" ... fill="#0d9488"/>
  <!-- 灰·监控 -->
  <marker id="ag" ... fill="#94a3b8"/>
  <!-- 红·拒绝/风险 -->
  <marker id="ar" ... fill="#dc2626"/>
  <!-- 绿·成功 -->
  <marker id="agg" ... fill="#15803d"/>
</defs>
```

### 3.2 箭头类型
```html
<!-- 实线（主路径） -->
<line x1="A" y1="B" x2="C" y2="D" stroke="#3b82f6" stroke-width="1.5" marker-end="url(#ab)"/>

<!-- 虚线（间接/监控） -->
<line x1="A" y1="B" x2="C" y2="D" stroke="#d97706" stroke-width="1.2" stroke-dasharray="4 3" marker-end="url(#aa)"/>

<!-- 粗线（强调，如资金流） -->
<line x1="A" y1="B" x2="C" y2="D" stroke="#7c3aed" stroke-width="1.8" marker-end="url(#ap)"/>

<!-- 折线（转向） -->
<path d="M350,52 L350,68 L115,68 L115,94" fill="none" stroke="#3b82f6" stroke-width="1.5" marker-end="url(#ab)"/>

<!-- 曲线（跨区域） -->
<path d="M215,210 Q502,196 790,210" fill="none" stroke="#d97706" stroke-width="1.2" stroke-dasharray="4 3" marker-end="url(#aa)"/>

<!-- 文字标注（放在箭头旁） -->
<text x="248" y="148" fill="#3b82f6" font-size="9" font-family="JetBrains Mono" text-anchor="middle">标注</text>
```

### 3.3 坐标计算技巧

- 节点右边缘 x = left + width
- 节点左边缘 x = left
- 节点顶边缘 y = top
- 节点底边缘 y = top + height
- 节点中心 y = top + height/2
- 箭头起点 = 源节点边缘，终点 = 目标节点边缘
- 横向箭头：y 相同，x 从源右边到目标左边
- 纵向箭头：x 相同，y 从源底边到目标顶边

## 4. 产品图标库（SVG 圆标）

> 用于架构拓扑图中快速识别技术组件。圆形背景 + 品牌色 + 缩写文字，无需外部图片。
> 统一尺寸：r=16（直径 32px），字号 10px，font-weight 700。

### 4.1 SVG 模板

```html
<!-- 通用模板：cx/cy 按节点位置调整 -->
<circle cx="CX" cy="CY" r="16" fill="BRAND_COLOR"/>
<text x="CX" y="CY+3.5" text-anchor="middle" fill="#fff" font-size="10" font-weight="700" font-family="'Noto Sans SC','Inter',sans-serif">ABBR</text>
```

### 4.2 AI / LLM

| 产品 | 缩写 | 品牌色 | 示例 |
|------|------|--------|------|
| OpenAI / GPT | OAI | `#10A37F` | `<circle ... fill="#10A37F"/><text ...>OAI</text>` |
| Claude | CL | `#D97757` | `<circle ... fill="#D97757"/><text ...>CL</text>` |
| Gemini | GE | `#4285F4` | `<circle ... fill="#4285F4"/><text ...>GE</text>` |
| LLaMA | LL | `#0467DF` | `<circle ... fill="#0467DF"/><text ...>LL</text>` |
| DeepSeek | DS | `#4D6BFE` | `<circle ... fill="#4D6BFE"/><text ...>DS</text>` |
| Qwen | QW | `#6236FF` | `<circle ... fill="#6236FF"/><text ...>QW</text>` |

### 4.3 AI 框架 / Agent

| 产品 | 缩写 | 品牌色 |
|------|------|--------|
| LangChain | LC | `#1C3C3C` |
| LlamaIndex | LI | `#8B5CF6` |
| Mem0 | M0 | `#6366F1` |
| CrewAI | CR | `#FF4F00` |
| AutoGen | AG | `#0078D4` |
| Dify | DF | `#1677FF` |

### 4.4 向量数据库

| 产品 | 缩写 | 品牌色 |
|------|------|--------|
| Pinecone | PC | `#000000` |
| Weaviate | WV | `#FA0050` |
| Qdrant | QD | `#DC244C` |
| Milvus | MV | `#00A1EA` |
| ChromaDB | CH | `#FF6446` |
| pgvector | PG | `#336791` |

### 4.5 数据库 / 存储

| 产品 | 缩写 | 品牌色 |
|------|------|--------|
| PostgreSQL | PG | `#336791` |
| MySQL | MY | `#4479A1` |
| MongoDB | MG | `#47A248` |
| Redis | RD | `#DC382D` |
| Elasticsearch | ES | `#FEC514` |
| ClickHouse | CK | `#FFCC00` |
| Neo4j | N4 | `#008CC1` |

### 4.6 云 / 基础设施

| 产品 | 缩写 | 品牌色 |
|------|------|--------|
| AWS | AW | `#FF9900` |
| GCP | GC | `#4285F4` |
| Azure | AZ | `#0078D4` |
| Docker | DK | `#2496ED` |
| Kubernetes | K8 | `#326CE5` |
| Nginx | NX | `#009639` |
| Kafka | KF | `#231F20` |
| RabbitMQ | RQ | `#FF6600` |

### 4.7 区块链 / 交易所（PM-WORKSPACE 常用）

| 产品 | 缩写 | 品牌色 |
|------|------|--------|
| Binance | BN | `#F0B90B` |
| OKX | OK | `#000000` |
| Platform C | PC | `#2B3139` |
| Gate.io | GT | `#2354E6` |
| Bybit | BB | `#F7A600` |
| Ethereum | ET | `#627EEA` |
| Solana | SO | `#9945FF` |
| TRON | TR | `#FF0013` |

### 4.8 组合用法示例

```html
<!-- 在拓扑图节点内嵌品牌标 -->
<g transform="translate(180, 95)">
  <!-- 节点背景 -->
  <rect x="0" y="0" width="160" height="52" rx="8" fill="#f5f3ff" stroke="#c4b5fd" stroke-width="1.5"/>
  <!-- 品牌圆标（左侧） -->
  <circle cx="24" cy="26" r="14" fill="#D97757"/>
  <text x="24" y="30" text-anchor="middle" fill="#fff" font-size="9" font-weight="700">CL</text>
  <!-- 节点文字（右侧） -->
  <text x="48" y="22" fill="#6d28d9" font-size="11" font-weight="700">Claude Opus</text>
  <text x="48" y="36" fill="#8b5cf6" font-size="9">主推理引擎</text>
</g>
```

## 5. Section 分隔线在 Dashboard 中的用法

架构图中 `.sec` 是绝对定位的（用于 `.dia` 内），但在 Dashboard 页面中需要改为相对定位：
```html
<!-- Dashboard 中用 position:relative -->
<div class="sec" style="position:relative;width:1000px;margin-top:24px;">
  <span class="st st-a">区域标题</span><span class="sl"></span><span class="sn2">说明</span>
</div>
```
