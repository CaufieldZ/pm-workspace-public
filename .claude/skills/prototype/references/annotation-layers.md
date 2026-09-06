---
name: annotation-layers
description: 原型两套标注层的用法——Anno 边缘 Pin 说明面板 与 spot_annot 演示点位光圈
type: reference
---

# 原型标注层

两套互不冲突的标注机制，都不往渲染壳内写文字（`ui-annotation-gate` 红线：屏内只放真实产品文案）。

- **Anno**：给页面元素挂说明卡，Pin 出壳的上/下边缘 + 折线 + Popover。用于评审时解释「这块是什么」。
- **spot_annot**：高亮「本轮改动落点」，屏内只有呼吸光圈与序号，文字走壳外图例。用于演示时说明「这轮改了哪儿」。

## Anno：说明面板

page_fns 的 value 返回 dict 替代纯 str（纯 str 向后兼容，骨架静默忽略 anno）：

```python
def page_app_feed():
    return {
        'page': '<div>...</div>',   # 渲染壳内容（不变）
        'anno': [
            {'n': 1, 'p': 'p0', 'title': '直播卡片布局', 'text': '...', 'tx': 187, 'ty': 148},
        ]
    }
```

**坐标系**：`tx/ty` 为元素在渲染壳内的像素坐标（phone 375×812；web-front 相对 `.web-front` 顶左角）。上半区（`ty < FH/2`）Pin 出顶边缘，下半区出底边缘；同边多 Pin 自动间距排开（≥ 34px），折线只走纵向不横穿内容区。

**坐标不确定时**：orchestrator 里临时给 project 加 `'anno_debug': True`，骨架会在渲染壳上叠网格 + 坐标提示层。这是调试层不是产品 UI，**交付前必须删掉该字段**。

**内容禁止**：`ann-text` / `title` 内禁裸场景编号（`A-1`）/ 决策号（`见决策 3`）/ 开发注解（`（此处占位）`）——规则同正文讲人话，`plain-language-gate` 拦。字段表 / 池策略参数 / 埋点事件名同样禁写进 anno（归 PRD）。

## spot_annot：演示点位

语义固定：**金 = 线上已有、本轮改接（relink）；蓝 = 本轮新增（new）**。

```python
from spot_annot import SPOT_CSS, SPOT_JS   # 拼进 extra_css / extra_js 尾部

EXTRA_CSS = r'''...''' + SPOT_CSS
EXTRA_JS = r'''
  const SPOT_LEGEND = {                     // 图例数据：项目侧定义
    trade: [[1, 'relink', '持仓卡分享入口 —— 线上已有，本轮改接']],
    feed:  [],                              // 无点位场景给空数组
  };
  // 壳外说明元素建好后挂图例 + 开关；切场景时同步图例
  spotLegendMount(noteEl); renderSpotLegend(sceneId);
''' + SPOT_JS
```

屏内挂法：目标元素加 `class="spot ring spot-relink|spot-new [wide]" data-spot="N"`（N 为徽标序号）。

「标注 开/关」按钮一键隐藏整套标注。**PRD 截图前先 `document.body.classList.add('noannot')` 关掉标注，截产品原貌。**
