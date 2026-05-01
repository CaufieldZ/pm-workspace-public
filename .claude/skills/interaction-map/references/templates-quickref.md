# 交互大图组件速查表

fill 函数写 HTML 时查此表确认 class 和结构。首次使用某组件如不确定完整结构，Read `interaction-map-templates.html` 对应行号。

## 布局组件

| 组件 | 外层 class / 标签 | 必填子元素 | 模板行号 |
|------|-------------------|-----------|----------|
| PART 分组（App 深色） | `div.gd.viewer.fade-section#partN` | `.gd-num` + `h2` + `.gd-desc` | 51-61 |
| PART 分组（Web 蓝色） | `div.gd.host.fade-section#partN` | 同上 | 169-178 |
| PART 分组（跨端绿色） | `div.gd.cross.fade-section#part-cross` | 同上 | 242-250 |
| 场景容器 | `div.fade-section#scene-{id}` | `.st` > `h2` + `span.note`，然后 `.flow` | 76-77 |

## 屏幕组件

| 组件 | class | 关键属性 | 模板行号 |
|------|-------|---------|----------|
| Phone Mockup | `div.phone` | min-height:660px; 含 `.ph-status` + `.ph-top` + 内容区 + `.home-ind` | 84-119 |
| Web Frame | `div.webframe` | width:720px; min-height:480px; 含 `.webframe-bar` + `.webframe-body` | 191-220 |
| 屏幕标签 | `span.phone-label` | flow-col 首子元素 | 83 |
| 屏幕说明 | `div.flow-note` | flow-col 末子元素 | 120 |

## Flow 组件

| 组件 | class | 说明 | 模板行号 |
|------|-------|------|----------|
| 横向容器 | `div.flow` | 包裹多个 flow-col + 箭头 | 79 |
| 列 | `div.flow-col` | 包裹一个屏幕 | 82 |
| 箭头 | `div.aw` > `div.al.{色}` + `div.tx.{色}` | 色：b=蓝 g=绿 r=红 p=紫 a=琥珀 | 124-127 |

## 标注组件

| 组件 | class | 说明 | 模板行号 |
|------|-------|------|----------|
| 标注框 | `div.anno.{色}` | 虚线边框包裹目标元素，position:relative 父元素 | 108-110 |
| 标注编号 | `div.anno-n.{色}` | ①②③... 圆点 | 109 |
| 注释卡片 | `div.ann-card` | 右侧说明卡，含 `.card-title` + `.ann-item`* + `.info-box` | 151-162 |
| 注释条目 | `div.ann-item` > `.ann-num.{色}` + `.ann-text` | 编号圆 + 说明文字 | 153-156 |
| 标签 | `span.ann-tag.{type}` | type: new/chg/del/p0/p1/p2 | 152 |
| 信息框 | `div.info-box.{色}` | 色：blue/green/amber | 161 |

## 跨端数据流表格

| 组件 | 说明 | 模板行号 |
|------|------|----------|
| 表格容器 | 960px 白底圆角卡片，grid 6 列 | 259-287 |
| 表头 | grid: # / 起点 / → / 终点 / 数据 / 触发方式 | 262-263 |
| 数据流行 | 按需复制，每行 grid 6 列 | 266-284 |
| 技术说明 | `.info-box.green`，含同步机制/延迟分级/容错 | 290-294 |

## 底部提示框

| 组件 | class | 说明 | 模板行号 |
|------|-------|------|----------|
| 阅读指引 | `div.co.bl` | 蓝色底部提示 | 303-305 |
| 优先级说明 | `div.co.am` | 琥珀色，含 P0/P1/P2 标签 | 307-312 |
