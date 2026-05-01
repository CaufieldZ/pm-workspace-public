# Prototype 上游数据纪律

> Step A 前必读。此文件解决「凭印象画」问题 — 强制把视觉 anchor 钉到真品（Figma / IMAP phone screenshot / 竞品截图 / context 第 4 章详细描述），4 选 1 不能再少。
>
> 适用：所有 prototype 项目（含 社区榜单 v1 → v2 那种翻车场景）。

## A0. 上游分支判定（Step 1 第一动作）

```text
有上游 IMAP（projects/{项目}/deliverables/imap-*.html 存在）
  → 走 § A / B / C（IMAP 硬看流程）

无 IMAP，但 scene-list.md + context.md 第 4 章场景描述齐全
  → 走 § D（无 IMAP 替代流程，强制双 anchor）

二者都没
  → 停下来要求用户先出 scene-list 再回来；prototype 不接此输入
```

## § A. IMAP 元素分类（phone 框 vs 工具标注）

模型反复踩坑：把 IMAP 的「→ D-2 ↗」注解箭头当 UI 画进 phone（v2 C-4 误加订阅按钮就是此因）。

**判定规则**：

| 出现位置 | 是 UI 吗 | 处理 |
|----------|----------|------|
| phone 框（`.phone` / `.app-mock`）内部 | ✅ 真 UI | 必画 |
| phone 框外的虚线连接 | ❌ 注解 | 不画 |
| phone 框外的圆形编号（蓝/紫/橙）| ❌ 注解 | 不画 |
| phone 框外的注解卡（dashed border） | ❌ 注解 | 不画 |
| phone 框外的箭头 + 「→ XX」文字 | ❌ 跨场景跳转标注 | 用 `onclick="go('xx')"` 表达，不复刻箭头本身 |
| 跨端 phone 之间的连接线 | ❌ 跨端流标注 | 各端独立场景，跳转用 onclick |

**红色 / 蓝色 / 紫色 / 橙色 圆形编号**几乎一定是 IMAP 工具的注解，不是 UI。

## § B. IMAP 硬看流程（Step A 前置）

### B1. 单截每张 phone

```bash
python3 .claude/skills/prototype/scripts/imap_phone_shots.py \
  projects/{项目}/deliverables/imap-{项目}-v{N}.html \
  -o projects/{项目}/inputs/imap-phones/
# 输出：A-1.png, A-2.png, B-1.png, ..., G-1.png（每张 phone 独立 PNG）
```

### B2. 模型用 Read 多模态读每张图

每张图读完写 1 行清单到 `projects/{项目}/inputs/scene-anchors.md`：

```markdown
- A-1：顶部 search + 一级 nav（推荐/关注/直播/快讯/社区）+ Feed 卡片列表 + 底部 5-tab nav + FAB 发布按钮（右下）
- B-1：profile-self · 头像 + 用户名 + 设置按钮 + 三连数据 + G-1 banner + 内容/战绩/带单 TAB + 文章子 TAB + 文章卡片 ×2
- ...（每场景一行，列出主要可视组件，禁止泛泛「个人主页」）
```

### B3. 清单和 scene-list 编号对齐才进 Step A

- 编号缺漏 → 报错并停下问用户（prototype skill 不接残缺输入）
- 多余编号（IMAP 有但 scene-list 没有）→ 报错并问用户该编号是否纳入 prototype

## § C. 场景组合（base + state 变体）

共享 base 的场景禁止复制粘贴整页。用「base 函数 + 高亮参数」表达：

```python
# proto_v2/scenes_bc.py 的最佳实践
def _self_header(highlight=None):
    """B-1 / C-1 / C-2 / E-2 / G-1 共用头部"""
    sub_hi = "border:2px solid var(--accent);..." if highlight == "subscribe" else ""
    g1_hi = "border:2px solid var(--gold);..." if highlight == "g-1" else "..."
    return f'<div ...>{sub_hi}...{g1_hi}...</div>'

# B-1 = base
def scene_b1(): return f'<div class="scr" id="s-b-1">{_self_header()}...</div>'

# C-2 = B-1 + 切到 perf TAB + 提示条 highlight
def scene_c2(): return f'<div class="scr" id="s-c-2">{_self_perf_unlock_hint(highlight=True)}...</div>'

# E-2 = C-2 + 抽屉 open
def scene_e2(): return f'<div class="scr" id="s-e-2">...{_self_perf_unlock_hint()}<div class="sheet">...</div></div>'
```

**每个 .scr div 文末加注释**说明 base 关系：

```html
<div class="scr" id="s-c-2">
  <!-- C-2 = B-1 base + 切到 perf TAB + _self_perf_unlock_hint(highlight=True) -->
  ...
</div>
```

## § D. 无 IMAP 替代流程（强制双 anchor 不许凭印象）

### D1. 硬底线

scene-list.md 中**每个场景**必须满足下列任一才允许进 Step A：

- ✅ 有竞品截图（Step 0 已收集到 `inputs/competitors/`，每场景至少 1 张直接对应的截图）
- ✅ 有 Figma 真品（HTX 项目优先 — 见 [crypto-app-vocabulary.md § E](crypto-app-vocabulary.md)）
- ✅ context.md 第 4 章对该场景有「布局描述 + 必备组件清单 + 状态变体说明」三段式描述（≥ 200 字 / 场景）

至少 1 项满足；3 项都没 → 停下来问用户补，禁止继续。

### D2. Step A 前置动作

1. 模型逐场景列出依据来源（截图路径 / Figma node / context 段落锚点），写到 `projects/{项目}/inputs/scene-anchors.md`
2. 每条带：场景编号 + 依据来源（含本地路径）+ 1 句关键视觉提炼
3. 任一场景缺依据 → 停下问用户补，禁止继续

scene-anchors.md 模板：

```markdown
# Scene Anchors · {项目名}

- **A-1 Feed 推荐**：anchor=`inputs/competitors/binance-square-feed.png`
  · 视觉提炼：顶 search + 横滑话题 chip + 卡片含头像/正文/媒体/互动栏
- **B-1 我的主页**：anchor=Figma `node 12547-22326` + `inputs/competitors/okx-profile.png`
  · 视觉提炼：头像 + 三连数据 + 关注/订阅 CTA + 内容 TAB
- **C-3 战绩 TAB**：anchor=context.md L420-L530（200 字布局 + 组件 + 状态描述）
  · 视觉提炼：累计收益率大数 + spark 曲线 + 胜率/回撤/资产三联 + 底部 sticky 订阅
```

### D3. Step C 验证（无 IMAP 项目额外加项）

playwright click 验证集（同 SKILL.md 自检清单）+ **逐场景对比 anchor 截图**：

- 模型用 Read 多模态读 `inputs/competitors/{对应}.png` + 自己 screenshot 局部
- 写「视觉对齐度自评」≤ 3 行，**不对齐项必须列出**（不许只说"已对齐"）
- 输出存 `projects/{项目}/deliverables/visual-alignment-report.md`

### D4. 最低适用范围

- ≤ 3 场景的小项目允许全程依赖 context.md 第 4 章 + 竞品截图
- 模型必须在 Step 0 后明确告知：「无 imap 流程已激活，依赖竞品截图作为唯一视觉 anchor，请至少给 1 张主场景截图」
- 用户确认后才进 Step A
