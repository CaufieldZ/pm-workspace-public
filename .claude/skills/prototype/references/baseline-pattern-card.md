# Prototype 标杆范式卡 · 3 个标杆 × 5 场景类型

> Step A 必读。本文件解决「下次产出一次到标杆水平」要求 — 把 3 个 PM 已认可的标杆 HTML 抽成可对照的范式骨架，下次直接照写不再凭印象。
>
> 检验：跑 `audit_against_baseline.py <候选 HTML> --baseline <本表对应标杆>`，关键组件全到才允许声明完成。

## 标杆速查

| 标杆 | 路径 | 范式 | 端构成 | 场景数 |
|------|------|------|--------|-------|
| V8 直播 | [HTX_观众端可交互原型_V8.html](../../../../projects/livestream/q2-update/deliverables/HTX_观众端可交互原型_V8.html) | 单 phone + scene chips | 纯 App | 17 |
| Community v3 | [proto-htx-community-v3.html](../../../../projects/community/base/deliverables/proto-htx-community-v3.html) | 单 phone + scene chips | 纯 App | 7 |
| Activity v5.1 | [活动中心_可交互原型_v5.1.html](../../../../projects/growth/activity-center/deliverables/活动中心_可交互原型_v5.1.html) | 多 view 切换 (gnav) | Web 前台 + Web 后台 | 12 |

## 3 标杆 × 5 场景对照矩阵

### 1. Feed 推荐 / 内容流

| 维度 | V8 | Community v3 | Activity v5.1 | 必备组件清单 |
|------|------|----|----|------|
| 容器 class | `.phone` + `.scr` | `.phone` + `.scr` | `.app-shell` + `.app-hero` | App: `.phone .scr` / Web: `.app-hero` |
| 顶部 nav | 单 phone 内 `.bbar` 横滑 chips | 单 phone 内 `.nav` chips | `.app-navbar` 全宽 | tabs1 金线 / 一级 nav |
| 卡片 | `.cinp` chat / `.olb` 卡片 | `.feed-card` + `.kline` | `.bn-card` banner | feed-card / chip / mono 数字 |
| 底部 | `.bbar` + `.hind` | 底 5-tab + `.hind` | `.app-tab` 横向 | tbar5 + home-ind |

**复盘提示**：v1 错在没用 `.scr` 切换（用 `.p-page` 多页），导致场景叙事丢失。

### 2. 个人主页 / 详情页

| 维度 | V8 | Community v3 | Activity v5.1 | 必备组件清单 |
|------|------|----|----|------|
| 头部 | 头像 + nm + 关注 fbtn | profile self/other 双视角 | `.app-hero` 详情 | 头像 ≥ 54px / 用户名 / 关注/订阅 CTA |
| 数据三连 | `.dtag` 标签 | 三连数据 + sub-TAB | — | 关注/粉丝/点赞 mono 数字 |
| TAB | `.dtag` chips | tabs2 (内容/战绩/带单) + sub-TAB (文章/动态) | `.app-tab` | 主 TAB 金线 + sub-TAB 灰文字 |
| sticky CTA | `.bbtn` + `.lmbtn` | C-3 双按钮 (关注 + 订阅 + 铃铛) | — | flex:1 主按钮 + 42px 副按钮 |

**复盘提示**：v2 第二轮 bug — 订阅按钮 click 后 remove `cta-blue` 丢 flex:1 缩窄。修复：只 add `cta-grey,subscribed`，layout class 永留。

### 3. 榜单 / 列表 / 表格

| 维度 | V8 | Community v3 | Activity v5.1 | 必备组件清单 |
|------|------|----|----|------|
| 容器 | `.olb` (online 榜) | `.dual` 双栏 | `.adr-item` 地址行 + `.adr-st` 状态 | row + chip 状态 + mono 数字 |
| 排序 / 筛选 | `.dtag` chips | chip 切换 | `.app-chips` | chip on/off |
| 空态 | `.emp` | placeholder | — | placeholder 灰底 |
| 分页 | — | — | — | 滚动加载 |

**复盘提示**：榜单默认走 row 不要走 card，每条信息密度更高。

### 4. 设置 / 表单 / 抽屉

| 维度 | V8 | Community v3 | Activity v5.1 | 必备组件清单 |
|------|------|----|----|------|
| 容器 | `.osh` (sheet 抽屉) + `.dim` (scrim) | sheet 抽屉 (E-2 战绩 / F-1 分享) | `.app-card` 表单 | scrim + sheet + handle |
| 行 | `.cinp` 输入 / `.mtog` 切换 | row + cell | row + input | row 14px 内边距 + 灰底 |
| 切换 | `.mtog on/off/locked` | toggle on/off | `.b b-sm op-on/off` | toggle 42×24 + 状态色 |
| 关闭 | scrim click + `.cic` ✕ | scrim click + ✕ | back button | 双关闭路径 |

**复盘提示**：toggle 跨场景（设置页 + 抽屉快捷视图）用同一份 `window._pubState`，click 同步两处 UI（v2 `_togglePub` 实战）。

### 5. 跨端 / 跨场景跳转

| 维度 | V8 | Community v3 | Activity v5.1 | 必备组件清单 |
|------|------|----|----|------|
| 跳转 | scene chip 切换 + `go(id)` | scene chip + `go(id)` | gnav-view-section 切换 + page 内导航 | `onclick="go('xx')"` 不复刻箭头 |
| 注解 | IMAP 「→ XX」不画进 phone | 同左 | view 切换不画进 phone | phone 框内 = UI / 框外 = 注解 |
| toast | `_toast()` | `_toast()` | toast | 通用 toast 函数 |

**复盘提示**：v2 C-4 误把 IMAP「→ D-2 ↗」标注画成订阅按钮，是把跨场景跳转标注当 UI。规则：phone 框内 = UI，框外 = 注解（详 [prototype-source-discipline.md § A](prototype-source-discipline.md)）。

## 范式选择 → 必备组件 checklist

### 单 phone + scene chips（V8 / Community v3 同档）

- ✅ `.phone` 容器 375×812 + 圆角 44 + Dynamic Island/notch
- ✅ `.scr` 多场景 div + `.scr.on{display:flex}` + `go(id)` 切换
- ✅ 顶部 `.nav` scene chips（`<button data-s="xx">{编号} {简称}</button>`）
- ✅ `.body` overflow-y:auto + 双引擎滚动条隐藏
- ✅ `.hind` home indicator 24px + 白条 134×5
- ✅ status bar `.sbar`（用 [crypto-app-vocabulary § B1-B3](crypto-app-vocabulary.md) 真品）
- ✅ 含订阅场景：`.cta-bar` 粘底（**不放 `.p-page` 内**）
- ✅ 含抽屉场景：`.scrim + .sheet` + `.sheet:not(.show){visibility:hidden}`

### 多 view 切换 gnav（Activity v5.1 同档）

- ✅ `.app-shell` 整端 shell（不是 .phone）
- ✅ `.gnav-view-section` 多 view 切换（前台 / 后台 / mgt）
- ✅ 每 view 独立 page 集合 + page 内导航（不用 .scr）
- ✅ `.app-navbar` Web 顶 nav（不是 phone 内 nav）
- ✅ 后台 view 走 `.adr-*` / `.bn-*` 列表 / 表格
- ✅ 双主题共存合法（前台 Binance dark / 后台 Claude Design 暖近黑）

### 单 phone 无 nav（≤ 3 场景小项目）

- ✅ `.phone` + 1-3 个 `.scr`
- ❌ 不需要 `.nav` chips（场景太少）
- ✅ `go(id)` 仍保留（场景内 CTA 跳转用）

### 单 view + sidebar（纯 Web 后台 / CMS）

- ✅ `.app-shell` + 左侧 `.sidebar`
- ❌ 无 `.phone`（不是 App）
- ✅ 主区 list / form 切换

## v1 / v2 复盘速览（反面 + 正面教材）

| 范式 | 实例 | 状态 | 教训 |
|------|------|------|------|
| 多 view + 多 page + goPage | 社区榜单 v1 | ❌ 错范式 | 没问端构成默认 view-page，IMAP 场景叙事丢失 |
| 单 phone + scene chips | 社区榜单 v2 | ✅ 修复 | 按 V8 抄范式，13 bug 全修后达标杆水平 |
| 多 view 切换 gnav | activity-center v5.1 | ✅ 标杆 | Web 前台 + Web 后台共建合法用法 |

下次启动 prototype，先跑 `check_paradigm.py` 推断 → 用户确认 → 直接照本表 checklist 写，不许跳。
