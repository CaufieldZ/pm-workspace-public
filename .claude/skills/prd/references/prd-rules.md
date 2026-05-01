# PRD 硬规则总册

> 13 条硬规则。SKILL.md 顶部只挂 5 条最致命的，本文是兜底全集。`check_prd.sh` + `pre-wiki-push-gate` hook 自动拦截。
>
> **macOS 注意**：`check_prd.sh` 早期版本用 `grep -P`（macOS BSD grep 不支持），会静默返回 0 触发 set -e 早退，让人误以为「自检通过」其实没跑。已修为 `grep -E`，并在 SCENE_COUNT == 0 时显式 exit。如发现自检输出只到「scene-list 中场景数: ...」就停了，先排查 grep 兼容性。
>
> **推 wiki 前硬闸**：`push_to_confluence_base.py` 默认调用 `gate_check_quality()` 扫圈数字 / 裸场景编号 / 决策编号 / 1.3 流水账启发式（左列含「v1.x / 早决策 / 中间稿」即警告），任一违规 exit 1 拒推。误报可加 `--skip-self-check` 强推。

---

## ① 框架函数复用（共 3 条）

### R1. 禁止在项目脚本里重定义框架函数

`set_cell_text` / `set_cell_blocks` / `replace_para_text` / `fill_cell_blocks` / `fix_dpi` 全部来自 `gen_prd_base` / `update_prd_base`，必须 `from gen_prd_base import *` / `from update_prd_base import *`。

- 旧脚本常见错误：自己写一个 `set_cell_text(cell, text)`，把含 `\n` 的多行字符串塞进单段落——右列会塌成无层次纯文本。
- 正确做法：多段落/多层次内容用 `set_cell_blocks(cell, [(title, [lines])...])`，它会渲染粗体模块 title + numbered 子项。

### R3. Scene 右列 lines 默认被 `fill_cell_blocks` 自动加 `1./2./3.` 编号（`numbered=True`）

lines 里写白话即可：
- 已含 `N. ` 前缀的行保持原样（不重复编号）
- 以 `  - ` 开头的二级缩进行跳过编号
- 需要关闭自动编号时显式传 `numbered=False`（如纯序号列表"1. Launch Pool / 2. 现货充值赛"这种本来就是数据枚举）

### R4. docx 已有 PNG 截图 DPI 默认 72

Playwright `deviceScaleFactor=2` 产物 DPI 元数据是 72，python-docx 误判尺寸强行缩放导致虚化。`replace_cell_image` 内部已自动 `fix_dpi`；批量修旧 docx 时自己写 loop 遍历 `doc.part.rels` 用 PIL 重写 `dpi=(144, 144)`。

---

## ② 项目脚本规范（共 1 条）

### R10. 项目脚本禁止硬编码 `BASE = '/Users/xxx/pm-workspace'`

`check_prd.sh` 会拦。统一用相对定位，脚本从 `projects/{项目}/scripts/` 执行，向上 3 层到工作区根：

```python
from pathlib import Path
BASE = Path(__file__).resolve().parents[3]  # pm-workspace 根
sys.path.insert(0, str(BASE / '.claude/skills/prd/scripts'))
```

硬编码的坑：① 换用户名/换机器立即炸 ② `sys.path.insert` 到不存在目录导致 `from gen_prd_base import *` 无声失败 → h1/h2 函数全失效 → docx 全 Normal style → Confluence 推上去大纲树失效。

---

## ③ docx 内容规范（共 4 条）

### R2. 禁止圈数字 ①②③④⑤⑥⑦⑧⑨⑩

CLAUDE.md 全局格式规范。章节 / 小节 / 步骤一律 `1. 2. 3.`。`humanize_doc` 自动归一（`CIRCLE_NUMS` 映射表），`check_prd.sh` 扫残留。

### R6. 所有 docx 产出必调 `normalize_punctuation(doc)`

soul.md 硬规则：中文相邻的半角 `,:()` 必须全角 `，：（）`。gen / update / refine 脚本保存 docx 前调用，`check_prd.sh` 会扫残留。

### R11. 正文禁用一切 PM 内部编号

场景编号（A-1/B-2/C-1）/ 决策编号（决策 1/决策 12）/ context.md 内部条目编号，全部禁出现在 scene_table 右列、第 5/6 章业务规则、bullet 等正文位置。

- 仅允许出现在：第 2 章场景地图映射表、scene_table 第二参数（标题 anchor，如 `📱 B-1 · 我看自己的个人主页`）
- 反例：`决策 1：订阅未来付费`、`TAB 切换 → C-1 / C-2 / C-4` —— 研发 / 运营都看不懂"决策 1"是什么、"C-1"对应哪个页面
- 正例：`订阅功能未来可能付费（本期免费）`、`切换"内容/交易战绩/带单战绩"TAB`
- `check_prd.sh` 已加扫描：扫 docx 正文（排除第 0 列场景标题 anchor）中的「决策 N」、「A-N/B-N/...」编号，命中即 fail
- 批量修复：

  ```python
  from update_prd_base import humanize_doc
  humanize_doc(doc, scene_to_human=[('A-3b','红包弹窗'),('A-1','直播间主页'),...])
  ```

  三步处理：删多编号括号 → 编号紧跟中文只删编号（避免重复词）→ 孤立编号查表换白话

- **重复词陷阱**：映射表写 `('F-1','CMS 主播认证')` 时，原文「F-1 主播认证管理」会变「CMS 主播认证 主播认证管理」 —— `humanize_doc` 内置「编号紧跟中文 → 仅删编号」步骤已处理，孤立编号才查表

### R13. PRD 必须讲人话（一眼看出 AI 写的就违规）

PRD 是产品 / 业务 / 项目经理读的文档，正文禁出现以下三类「AI 味」内容：

1. **流水账 / 版本痕迹（FAIL）**：`(YYYY-MM-DD ...)` / `(from vN ...)` / `(变更)` / `(新增)` / `决策 #N` / `反转说明：` / `砍掉：` 一律删。PRD 描述当前状态，多轮迭代过程归 context.md 第 7 章。
2. **代码字段 snake_case（WARN）**：`card_type / is_same_symbol / related_card_id / xxx_id / has_xxx` 等，正文应改白话。**例外（豁免）**：H2 标题含「枚举值/字段/埋点/事件/参数/对照/归因」、或表头含「ID/字段/事件/参数/枚举/指标/触发/层级/路由」的位置，必须保留原始 snake_case 给研发对账。
3. **UI 设计参数（WARN）**：`px / 颜色 hex / ms / opacity / 字体名 / 字号字重` 归设计稿。第 7 章 NFR 里的 `≤300ms` `1280px` 是性能契约保留。

**bspec / pspec / test-cases 不受此约束**——研发 / QA / 设计师消费，允许字段名 + 像素 + 编号引用。

**三道闸**（设计原则：第 1 道治本，第 2/3 道兜底）：
- **gen / update 时**：`save_prd(doc, path, extra_jargon=...)` 一键保存（自动 humanize + 标点 + 字体 + theme + 扫描）
- **本地自检 / hook 拉起**：`check_prd.sh` 跑共享模块 `humanize.scan_human_voice`
- **推 wiki 前**：`push_to_confluence_base.gate_check_quality` 同源调用，FAIL 拒推

**手动修复**：

```python
from update_prd_base import humanize_prd_voice
PROJECT_JARGON = [(re.compile(r'\bfutures_holding\b'), '合约持仓'), ...]
humanize_prd_voice(doc, extra_jargon=PROJECT_JARGON)
```

完整规范 + 替换映射表 + 工具链图：`references/prd-human-voice.md`

---

## ④ 升版补丁纪律（共 4 条）

### R5. Phone 比例截图（aspect < 0.7）必须圆角透明化

否则深色主题里 4 角残留白方块。`core.images.round_phone_corners` 用 `PIL.ImageDraw.rounded_rectangle` 生成 alpha mask（CSS `border-radius: 36px` × deviceScaleFactor 2 = 72px 半径，CSS 改 radius 后此处同步）。仅 phone 处理，webframe 本就是矩形。

### R7a. 升版 patch 路线必调 `assert_screenshots_fresh(docx_path, prototype_html, shot_dir)`

改完文字保存 docx 后立即断言截图 mtime ≥ 原型 mtime，过期 raise。配套 PostToolUse hook（`.claude/hooks/post-docx-screenshot-check.sh`）在 Bash 跑 `update_*.py` / `patch_proto_*.py` 时兜底 stderr 提醒。

### R7b. 升旧 docx 必调 `normalize_headings(doc)`

老脚本用 `add_paragraph(style='Heading 1')` 直接产 H1/H2 时不染 run，Word 渲染成黑色无下划线，视觉与新 PRD 不一致。`normalize_headings` 幂等：H1 补 `fg=#141413（Anthropic Dark）+ 下边框#D97757（terra cotta）`，H2 补 `fg=#D97757`。同步处理表头 bg 从旧 `D5E8F0` / `2D81FF` 升到 `141413` + 白字（`set_cell_bg` 已修复旧 shd 残留 bug，可直接调）。

### R8. patch 脚本插新段落用 helper，禁止模糊段落覆盖

- ✅ 插新章节: `insert_heading_before(anchor, '6.4 归因漏斗', level=2)`
- ✅ 插描述段: `insert_description_after(doc, '2.2 View 2', 'CMS 管理后台...')`
- ✅ 插普通段: `insert_paragraph_before(anchor, '补充说明', size_pt=9)`
- ⛔ `anchor.insert_paragraph_before(text)` 裸调用 —— 默认 Normal style，Confluence 大纲树失效
- ⛔ `for j in range(i+1, i+5): if not doc.paragraphs[j].text.startswith('2.'): 覆盖 text` 这种"查下一段落覆盖"模糊定位 —— 跳过条件容易咬错咬到下一级大标题，H1 text 被覆盖（patch_prd_v3_3.py 把第 3 章 H1 text 覆盖成描述段的踩坑案例）
- 正确姿势：任何"在 XX 位置插入新段"都用 helper；任何"覆盖已有段 text"先判断 `p.style.name.startswith('Heading')` 跳过，只覆盖 Normal 段

### R9. 无截图 Scene 禁止用 2 列 scene_table

CMS / 纯后台 / 本次 UI 不改只改后端的场景：

- ⛔ 留「← 此处粘贴原型截图」空占位的 2 列表格 —— 左列永远是空，右列被压窄，视觉冗余
- ✅ 用 `insert_scene_blocks(anchor, blocks, heading_level=3)`（body 级 H3 + numbered list）
- 判断准则：Scene 改动范围内**没有任何 UI 可以截图** → 降级 body 级；有任何 UI 改动 → 走 scene_table 配截图
- 迭代模式下常见场景：CMS 保留现状仅后端改字段响应、纯规则说明章节、功能已完整不改只做文档化
- 参考 prd-template.md「两种 Scene 展开模式」 + patch 示例 `htx-live-streaming-updateQ2/scripts/patch_prd_v27_ch7.py`

---

## ⑤ 字体三件套（共 1 条）

### R12. 老 docx 升版必跑字体三件套

framework 美学切到 Anthropic brand-guidelines 后，字体规范从 Source Serif 4 / Plus Jakarta Sans / HarmonyOS Sans SC 升到 Lora / Poppins / Noto Sans SC，老 docx 升版漏跑会残留旧字体风：

```python
from update_prd_base import normalize_punctuation, normalize_headings, normalize_fonts, ensure_theme
normalize_punctuation(doc)
normalize_headings(doc)
normalize_fonts(doc)         # 老 ascii=Arial / Source Serif 4 / Plus Jakarta Sans → Poppins; rFonts 缺失也补 design 字体
doc.save(path)
ensure_theme(path)            # 注入 word/theme/theme1.xml（python-docx 老模板漏）
```

三个层级缺一不可：
- **docDefaults themed**（走主题 fallback 链）
- **run 级写 design 字体名**（Word for Mac 走系统 substitute → SF Pro / PingFang）
- **theme1.xml 文件**（themed 引用解析依赖它）

症状对照：
- 缺 theme1.xml：docDefaults `<rFonts asciiTheme="minorHAnsi"/>` 引用悬空 → Word 无 fallback → 强制 Arial
- run 级 rFonts 缺失：走 docDefaults themed → 解析 theme1.xml minorFont（Cambria + 宋体）→ Mac 渲染 Cambria/STSong（衬线 Arial-classic 风）

`check_prd.sh` 已自动扫：缺 theme1.xml / 残留老字体 run → fail。

**错觉警告**：docx 没 CSS fallback chain，只有 Word/Mac 系统级 substitute。Lora / Poppins 没装时 Mac/Win 走系统衬线 / sans 替代，样式会偏离设计稿但可读。

---

## 速查（按违规症状反查规则）

| 症状 | 命中规则 | 工具 |
|------|---------|------|
| 单元格右列扁平字符串、无层次 | R1（禁重定义 set_cell_text） | `set_cell_blocks` |
| 圈数字 ①②③ 残留 | R2 | `humanize_doc` |
| `1./2.` 编号缺失或重复 | R3 | `fill_cell_blocks` 自动 / 已含跳过 |
| docx 截图模糊 | R4 | `fix_dpi` 已内置 `replace_cell_image` |
| 深色主题 phone 截图 4 角白方块 | R5 | `round_phone_corners` |
| 中文旁半角 `, : ( )` | R6 | `normalize_punctuation` |
| 截图比文档老（升版漏拍） | R7a | `assert_screenshots_fresh` |
| H1/H2 黑色无下划线 | R7b | `normalize_headings` |
| patch 后 H1 标题被覆盖 | R8 | `insert_*` helper |
| 空截图位 2 列表格视觉冗余 | R9 | `insert_scene_blocks` + `remove_table` |
| 换机器跑炸 / Confluence 推上去无大纲树 | R10 | `Path(__file__).resolve().parents[3]` |
| 正文残留 A-1 / 决策 1 等编号 | R11 | `humanize_doc(scene_to_human=...)` |
| docx 渲染成 Arial / 衬线 Cambria | R12 | 字体三件套 |
| PRD 一眼看出 AI 写 | R13 | `humanize_prd_voice` + `scan_human_voice` |
