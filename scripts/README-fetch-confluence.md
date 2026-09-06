# fetch_confluence.py — Confluence 一键拉到本地 markdown

一个脚本通吃 4 种 Confluence 页面形态，auto 嗅探自动选模式。PM / 开发用同一条命令。

```
                       ┌──────────────────────────────────┐
                       │      fetch_confluence.py         │
                       │                                  │
拉父+子页 PRD ────────►│  auto嗅探 ─► split-restore       │──► {stem}.md + scenes/ + assets/
拉单页 md push PRD ────│         ─► md-macro             │──► {title}.md + assets/
拉人编辑文档 ──────────│         ─► pandoc               │──► {title}.md + assets/
                       └──────────────────────────────────┘
```

---

## 1. 快速开始

### 1.1 准备凭证（任一即可）

**方式 A：环境变量**（开发推荐，不依赖私有配置）：

```bash
export CONF_BASE_URL=https://INTERNAL_URL_REDACTED
export CONF_TOKEN=<personal-access-token>
```

获取 token：Confluence → 头像 → Settings → Personal Access Tokens → Create token。**不要**进 Git。

**方式 B：仓库根 .mcp.json**（PM 工作流默认）：

```json
{
  "mcpServers": {
    "confluence": {
      "env": {
        "CONF_BASE_URL": "https://INTERNAL_URL_REDACTED",
        "CONF_TOKEN": "..."
      }
    }
  }
}
```

脚本优先读 env var，找不到再读 .mcp.json。

### 1.2 装 pandoc（仅 pandoc 模式需要）

```bash
# macOS
brew install pandoc

# Linux
apt install pandoc    # 或 yum install pandoc
```

不打算拉人编辑文档？这步可跳——其他模式（md-macro / split-restore / simple）都不用 pandoc。

### 1.3 一条命令拉

```bash
python3 scripts/fetch_confluence.py <Confluence URL> --out-dir ./dump
```

输出 `./dump/{页面标题}.md`，相关图自动落 `./dump/assets/`。VS Code 打开 md，`Cmd + Shift + V` 看预览，图、表全在原位渲染。

---

## 2. 形态嗅探决策树

`--mode auto`（默认）按 storage HTML 指纹自动选：

| 输入特征 | auto 选择 | 输出结构 |
|---------|----------|---------|
| 父+子页 + 子页含 markdown 宏 / 场景 heading | **split-restore** | `{stem}.md` + `{stem}-scenes/{view}-{id}-{name}.md` + `assets/` |
| 单页 + markdown 宏 ≥ 50% | **md-macro** | `{title}.md` + `assets/`（宏 CDATA 原样还原）|
| 单页 + 无 markdown 宏 | **pandoc** | `{title}.md` + `assets/`（HTML → GFM，复杂表保留 HTML）|

脚本运行时把嗅探结果输出到 stderr，可对账：

```
  → auto 嗅探 → mode=pandoc
  → storage 引用 6 张图，仅下载这些（忽略页 attachment 全集）
下载了 6 张图片到 ./dump/assets
```

---

## 3. CLI 参考

### 3.1 位置参数

| 参数 | 说明 |
|------|------|
| `<url>` | 必填。Confluence 页面 URL（推荐 `?pageId=N` 形式）或纯 pageId 数字也支持 |

### 3.2 输出位置（互斥二选一）

| 参数 | 说明 |
|------|------|
| `--out-dir DIR` | 通用输出目录。md 落 `{dir}/{title}.md`，图落 `{dir}/assets/` |
| `-p, --project PROJECT` | PM 工作流：落 `projects/{PROJECT}/inputs/` |
| 都不传 | md 输出到 stdout，不下载图（适合 grep / pipe）|

### 3.3 模式控制

| 参数 | 说明 |
|------|------|
| `--mode auto`（默认）| 按 storage 嗅探自动选 |
| `--mode pandoc` | 强制 pandoc 转换（人编辑文档无损还原）|
| `--mode md-macro` | 强制剥 markdown 宏 CDATA（md push 的 PRD）|
| `--mode split-restore` | 强制还原本地 split 目录结构（父+子页 PRD）|
| `--mode simple` | 旧 html_to_markdown（向后兼容保险插销）|

### 3.4 图片控制

| 参数 | 说明 |
|------|------|
| 默认 | 精准下图：只下 storage 实际引用的图，不下 page attachment 全集（避免历史版本污染）|
| `--no-images` | 纯文字模式，跳过图片下载，md 引用保留为占位 |

### 3.5 split-restore 专属

| 参数 | 说明 |
|------|------|
| `--view-map "4:broadcaster-h5,5:audience,..."` | 章节号 → view 前缀映射。决定场景文件名 `{view}-{id}-{name}.md` |
| `--stem NAME` | 主 md 文件名 stem（默认从父页标题派生）|

不传 `--view-map` 时用默认 `{5:front, 6:back, 7:cross}`。看子页标题对应不上业务时显式传精确映射。

### 3.6 其他（旧能力保留）

| 参数 | 说明 |
|------|------|
| `--html` | 输出单 HTML 文件（图片 base64 内嵌，可独立分发）|
| `--raw` | 输出原始 Confluence storage XML（debug 用）|
| `--with-children` | 父+子页拼合成**单个** md（不拆 split），子页 heading 自动下沉一级 |
| `-o, --output FILE` | 指定输出文件名（默认用页面标题派生）|

---

## 4. 4 种形态实战速查

### 4.1 形态 A — 父+子页 PRD（PM split push 上去的）

例：[pageId=169220843](https://INTERNAL_URL_REDACTED Q2 升级 PRD）

```bash
python3 scripts/fetch_confluence.py \
  'https://INTERNAL_URL_REDACTED' \
  --view-map "4:broadcaster-h5,5:audience,6:broadcaster-web,7:cms" \
  --out-dir ./dump
```

输出：

```
dump/
├── 示例-直播间-Q2-升级-·-产品需求文档.md      # 主 md，§1-3 + §4-7 章 + scene link 占位
├── 示例-直播间-Q2-升级-·-产品需求文档-scenes/
│   ├── audience-A-1-直播间完整全貌.md         # 19 个场景文件，跟 PM 本地 deliverables/ 1:1
│   ├── audience-A-2-在线观众-打赏榜.md
│   ├── broadcaster-web-D-0-创建房间-开播.md
│   ├── cms-F-2-直播列表管理.md
│   └── ... (共 19 个)
└── assets/                                    # 仅 storage 实际引用的图（17 张，非 attachment 全集）
```

view 前缀怎么填：打开父页看子页标题：

| Confluence 子页标题 | 章节号 | 常用 view 前缀 |
|--------------------|--------|---------------|
| 开播链路详细需求（Part 0）| 4 | `broadcaster-h5` |
| 观众端详细需求（Part 1）| 5 | `audience` |
| 主播工作台详细需求（Part 2）| 6 | `broadcaster-web` |
| CMS 运营后台详细需求（Part 3）| 7 | `cms` |

### 4.2 形态 B — 单页 md push 的 PRD

例：[pageId=169224502](https://INTERNAL_URL_REDACTED PRD）

```bash
python3 scripts/fetch_confluence.py \
  'https://INTERNAL_URL_REDACTED' \
  --out-dir ./dump
```

auto 嗅探到 md-macro，剥 markdown 宏 CDATA 原样还原（0 损失）。

### 4.3 形态 C/D — 人编辑文档（含复杂表 + 多图）

例：[pageId=164483743](https://INTERNAL_URL_REDACTED

```bash
python3 scripts/fetch_confluence.py \
  'https://INTERNAL_URL_REDACTED' \
  --out-dir ./dump
```

auto 嗅探到 pandoc，自动调 pandoc 转 GFM：

- 简单表 → GFM pipe table
- 复杂表（rowspan / colspan / 表内含图）→ 保留 HTML，IDE 预览原生渲染
- 嵌套列表正确缩进

### 4.4 纯文字模式（不要图）

```bash
python3 scripts/fetch_confluence.py <url> --no-images --out-dir ./dump
# 或 stdout
python3 scripts/fetch_confluence.py <url> --no-images > ./out.md
```

md 内 `<img>` / `![]()` 引用保留为占位（不破坏内容结构），文件不下载。VS Code 预览这些图会显示「图片加载失败」灰块，文字部分照常看。

---

## 5. PM 工作流补充

### 5.1 拉别人的 PRD 到自己项目 inputs/

```bash
python3 scripts/fetch_confluence.py \
  'https://INTERNAL_URL_REDACTED' \
  -p livestream/q2-update
```

落到 `projects/livestream/q2-update/inputs/`，做参考材料用。

### 5.2 自己 split push 上去的 PRD 拉回本地（恢复 deliverables）

换机器 / 本地丢了 deliverables/ 时：

```bash
python3 scripts/fetch_confluence.py <自己的父页 url> \
  --view-map "..." \
  -p {项目}
```

`-p` 模式下输出落 `projects/{项目}/inputs/`，可对照本地 deliverables/ 结构（注意：拉回的是 wiki 当前态，跟本地未推的改动可能漂移）。

### 5.3 跟 push 端配对使用

| 方向 | 命令 |
|------|------|
| 本地 split → 推 wiki | `python3 scripts/md_to_confluence.py {prd}.md --split-children-by-chapter --update-id <父页 ID>` |
| wiki → 本地 split（本脚本）| `python3 scripts/fetch_confluence.py <父页 url> --view-map ... --out-dir ./...` |

---

## 6. 故障排查

| 报错 / 现象 | 原因 / 处理 |
|------------|-----------|
| `找不到 confluence 凭据` | env var 没设 + .mcp.json 也没 confluence 配置。任选一种配上 |
| `Confluence HTTP 401/403` | token 错 / 失效，重新生成 |
| `Confluence HTTP 404` | pageId 错，或当前 token 对该页无权限 |
| `错误：--mode pandoc 需要 pandoc` | 没装 pandoc，`brew install pandoc` |
| auto 嗅探选了 split-restore 但子页 view 对不上 | 显式传 `--view-map` 精确指定，或用 `--mode pandoc` 强制走 pandoc 走单页路径 |
| 复杂表在 IDE markdown preview 显示乱 | 复杂表保留为 HTML `<table>`，markdown 预览原生支持 HTML，但简陋预览器可能不渲染。VS Code / GitHub 都 OK |
| 拉下来 274 张图但 md 只用 6 张 | 已修：默认只下 storage 引用的图，不下 page attachment 全集。重新拉一次即可 |
| `--view-map 格式错` | 格式 `"N:prefix,N:prefix"`，章节号是数字 4-7，冒号分隔，逗号串 |
| stdout 模式 + 图 → md 引用全裂 | 加 `--out-dir <目录>` 或 `--no-images`（纯文字）|

---

## 7. 实现说明

详细架构 + push 端说明：[md_to_confluence.py](md_to_confluence.py)（PRD v2 md 形态专用；docx 形态已废弃）。

形态嗅探逻辑：[scripts/fetch_confluence.py:detect_mode](fetch_confluence.py)

split-restore 文件名规则跟本地 PM 工作流 `split_prd._safe_filename` 1:1 对齐（复制了一份避免跨目录依赖），未来 split 规则有变需要两边同步。

精准下图原理：扫 storage 里 `<ri:attachment ri:filename="X"/>` 拿真实引用集合，只下载这部分；page attachment 全集含历史版本 + 未引用图，可能比真实引用多几十倍。
