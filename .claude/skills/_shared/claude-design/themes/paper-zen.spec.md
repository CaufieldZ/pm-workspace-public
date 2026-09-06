# paper-zen 学院派教研美学速查

> 「东方质感的西方学院派 / 出版物美感」一图流 / 教学海报 / 研究报告封面场景的设计语言速查。
>
> 三件套：
> - [`paper-zen.css`](paper-zen.css) — CSS 变量（token 实装，调色 / 字号 / 间距已 sealed）
> - [`paper-zen.prompt.md`](paper-zen.prompt.md) — Chat Opus 设计 brief（要做全新一图流时整段贴给 Chat Opus）
> - 本文件 — Felix / Claude 本地速查（招式 + 决策框架，prompt.md 没的细节都在这里）

来源：Felix 老婆用 Chat Opus 调出来的（参考 `projects/proj-workflow-pre/deliverables/分层支持脚手架.html` / `数学思维五阶进阶.html`）。Opus 后续做的设计语言研究复盘定位为「**东方质感的西方学院派 / 出版物美感 / 研究报告封面感**」——不是国潮古风也不是 SaaS 落地页，参考坐标系是《读库》《单读》《信睿周报》深度报道 + FT Weekend / 麦肯锡报告封面。文件名 `paper-zen` 已固化（zen 取沉稳学院气，paper 取宣纸质感），不改。

底层哲学跟 Claude 暖近黑同源（暖色温 / 衬线主导 / 反工业 accent / 反 emoji / 反 SVG 插画），只是用国画颜料替代北欧灰阶 + 宋体替代 Lora。

## 触发场景

**适合**：
- 一图流（年度 PM 总结海报、季度战报海报、产品宣传海报）
- 教研文档（公开课说课、园本研修、研究报告封面、深度方案文档）
- 教学海报 / 学习卡片（私人给孩子做学习材料 / 给老婆做幼教文档）
- 印刷品（A4 横版打印物）
- 庆典级 PRD 配图（极少数情况）

**不适合**（明确反面，下次别误用）：
- 受众：儿童、家长、互联网年轻用户、需要快速决策的高管（高管要数据驱动的冷板）
- 场合：家长会通知（太冷）/ 用户增长素材（太慢）/ 儿童学习材料（太成人）/ 紧急通知（太装饰）
- 内容：纯数据 dashboard / 营销卖点页 / 操作指南 / PPT / SOP / 长阅读文档
- 主线 PM Skill 默认产出物（走 claude.ai 暖近黑 / fintech-dark）

**替代美学候选**（不适合 paper-zen 时换轨）：
- 深色科技风 → claude.ai 暖近黑 `cd-` 默认主题
- 金融垂类 → fintech-dark 主题
- 极简数据风 → muji-minimal 或 swiss-grid 主题
- 出版书版感 → book-architecture 或 ink-classic 主题

## 核心 token（已 sealed in paper-zen.css）

```
bg     #FAF6EC 米黄宣纸    paper #FFFDF7 宣纸白卡片
ink    #1F1B16 暖墨        ink-soft #5C5447 陈墨褐
accent #1B3A2F 松竹绿（主） accent-2 #A8804A 赭金（装饰） accent-3 #B85540 朱赤（重点）
line   #D9CFB8 浅米色分隔
```

## 5 阶情绪光谱（色温暖→冷→深，暗合「感性→理性」认知温度递进）

| 阶 | 主色 | -soft 浅版 | 情绪 |
|---|---|---|---|
| s1 琥珀 | `#D89A4B` | `#F4E3C8` | 暖起点 |
| s2 生长绿 / 竹青 | `#789B6C` | `#DCE7D4` | 萌发 |
| s3 湖蓝 / 远山黛 | `#3F7A95` | `#CFE0E8` | 沉静 |
| s4 陶土红 / 朱赤 | `#B85540` | `#EFD3CB` | 燃烧 |
| s5 深紫 / 紫绛 | `#4F3A65` | `#DDD2E5` | 深远 |

每色配 `-soft` 浅版做 tag 背景，全是低饱和度国画色。

## 字号阶梯（信息图 1600–1800px 画布）

- H1 主标题：46–56px / weight 900 / 宋体
- 副标题：18–21px / ink-soft 色
- H2 区块标题：24–30px / weight 900 / 宋体
- 卡片大标题：28–32px / weight 900 / 宋体
- 强调动作短语：21px / weight 700
- 正文：18–21px / weight 500 / 黑体
- 标签 / pill：15–17px / weight 700
- 元信息：13–15px

**铁律：信息图字号比 Web 文档大 30–50%**（最终大概率被截图缩放嵌入 Word / PPT，"略大"就是"刚刚好"）。

## 间距与圆角

- 圆角 2–3px（避开"完全直角"的古板 + "大圆角"的互联网感）
- 卡片 padding 22–26px / gap 14–18px
- 阴影 `0 14px 24px -16px rgba(31,27,22,.22)`（视网膜屏才隐约可见）
- 边框 `1.5px solid var(--line)` + 顶部 `5–7px solid var(--c)` 强调色横条

## 4 骨架模板（构图库，按场景选）

**骨架 A — 报头 + 主轴 + 内容**
- 顶：左标题 + 右元信息（左侧 1.5px 竖线分隔），底 2px 主色横线 + 7px 金棕短装饰线
- 中：起点标签 — 虚线 / 渐变轴 — 终点标签
- 下：内容区
- 适用：路径图、流程图、进阶图

**骨架 B — 3×3 矩阵**
- 横轴：能力梯度（基础 / 进阶 / 挑战）
- 纵轴：维度（材料 / 提问 / 指导）
- 顶行主色填底反白字 + 大圆形罗马数字徽章
- 适用：分层支持图、能力模型图、对比矩阵

**骨架 C — 阶梯式卡片**
- 5 张卡片 `margin-top: 64/48/32/16/0px` 实现楼梯感
- 卡片间用菱形连接点（CSS 旋转方块 + 阴影）
- 适用：进阶路径、成长阶段、roadmap

**骨架 D — 底部彩色渐变条带 + 三 / 五栏小结**
- 浅米色块 `#F2EAD3` + 顶部 5px 渐变条（横跨所有阶段色）
- 内部 3–5 栏并列，每栏：色块标签 + 宋体小标题 + 黑体描述
- 适用：原则 / 总结 / 结论区

## 14 招（点睛细节，单独看不起眼，累加起来决定专业度）

1. **数字也用衬线**（关键反差）：罗马 Ⅰ Ⅱ Ⅲ + 圆形徽章用 `Noto Serif CJK SC` + Songti，西方设计数字默认 sans / mono，**衬线数字立刻古籍味**
2. **三层标识**：罗马 Ⅰ Ⅱ Ⅲ + 中文层级名 + 英文小标（STARTER / EXPLORER / CHALLENGER）
3. **主标题荧光笔**：挑一个关键词加 `linear-gradient(180deg,transparent 60%,var(--c-soft) 60%)` 做浅色高亮块
4. **报头双线**：accent 长 + gold 短错落 7px 偏移
5. **卡片色带**：`border-top: 7px solid var(--c)` 或 `border-left: 6px solid var(--d)`
6. **虚线分隔**：`background: repeating-linear-gradient(90deg, var(--c) 0 5px, transparent 5px 9px)` 古籍栏线（**用虚线不用实线**，是出版物语言）
7. **断续虚线主轴 + 末尾 CSS 三角箭头**（不用 SVG）
8. **letter-spacing 中英分档**：CJK 0.04–0.1em（疏朗）/ 英文小标 0.22–0.3em（金石舒展）
9. **背景宣纸晕染**：`radial-gradient` opacity ≤ 6%，模拟纸纤维
10. **icon 全是纯字 + 圆形底**：「材」「问」「导」用 Songti 大字 + 圆形 accent bg，禁 SVG 禁 emoji
11. **彩色描边圆形数字徽章**（彩色 border + 浅 -soft 填底 + 主色文字，**不是实心填充**）
12. **章节符号**：`h2::before { content:"◇ "; color: var(--gold); }`
13. **同色系深浅对比 tag pill**：`--c-soft` 底色 + `--c` 文字
14. **CJK 标点全角铁律**：引号用全角「」不用半角 ""，破折号用 — 不用 -（output-style.md 已规则化覆盖）

## 切换方式

```css
@import url('../../_shared/claude-design/tokens.css');
@import url('../../_shared/claude-design/themes/paper-zen.css');
```

下次要做新一图流时另一种触发：直接把 `paper-zen.prompt.md` 整段贴给 Chat Opus，让 Opus 按这套底座产 HTML（适合需要全新构图的复杂场景）。

## 不要做的事

- 不和 Claude 暖近黑混搭（米黄底 + terra cotta 不和谐）
- 不写死 hex 进消费方 HTML，5 色 palette 也用 CSS 变量代理
- 不在 PPT skill 默认产出物用（PPT 默认 dark）
- 不用纯白 `#FFF`（没"质地感"），不用纯黑 `#000`（视觉重量过死）
- 不用 emoji / 渐变光效 / 玻璃拟态 / 重 box-shadow / 卡通插画 / 手写字体
