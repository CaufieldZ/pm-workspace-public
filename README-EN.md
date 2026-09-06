<div align="center">

# ATLAS

`THE AI-NATIVE PM WORKSPACE · PM-WS`

[中文](README.md) · **English**

Meeting notes / MRD / competitor screenshots → scene lists, interaction maps, PRDs. 17 Skills covering the full product-manager workflow.

[![License](https://img.shields.io/badge/license-Apache%202.0-1f54d6?style=flat-square)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-17-D97757?style=flat-square)](.claude/skills)
[![Hooks](https://img.shields.io/badge/hooks-14-000?style=flat-square)](.claude/hooks)
[![Audit](https://img.shields.io/badge/audit-21_categories-000?style=flat-square)](.claude/skills/workspace-audit)
[![Python](https://img.shields.io/badge/python-3.10+-000?style=flat-square)]()
[![Node](https://img.shields.io/badge/node-18+-000?style=flat-square)]()
[![Claude Code](https://img.shields.io/badge/claude_code-native-000?style=flat-square)](https://docs.anthropic.com/en/docs/claude-code)

</div>

---

## What it solves

| Dimension | Before | After |
|:--|:--|:--|
| Input | Meeting notes / MRD / competitor shots / verbal asks | Same |
| Process | PM hand-draws wireframes, writes PRDs, re-aligns repeatedly | AI produces per-Skill deliverables, PM reviews and tweaks |
| Time cost | 3–5 days | 10 min – 2 hours |
| Consistency | Different output each time, term drift | Locked IDs + globally consistent terms + 16-category audit |
| Downstream | PRD thrown to engineering to interpret | PRD md is the single source of truth — business objects / state machines / 5-section scenes / copy matrices all in one doc, dev / design / QA agents each take what they need |
| Methodology | Scattered across personal habits and docs | Three layers (strategy / workflow / project) written to disk, reusable across sessions and models |

---

## Demo first · a private-fund flow in 20 minutes

A fictional private-fund subscription/redemption project, walking through baseline → scene-list → interaction map → PRD end-to-end. Measured ~20 min on a mid-tier Sonnet-class model: [`examples/private-fund-demo/`](examples/private-fund-demo/).

![Interaction map hero](https://raw.githubusercontent.com/CaufieldZ/pm-workspace-public/main/examples/examples/private-fund-demo/screenshots/imap-hero.png)

> Above is the top of the interaction map, PART 0 · H5 investor view (A-1 fund detail + subscription / A-2 agreement signing + cooling-off). All 5 Scenes plus the cross-device dataflow table are in the [full HTML](examples/private-fund-demo/deliverables/imap-private-fund-v1.html).

| Deliverable | Scale |
|:--|:--|
| [prd-private-fund-baseline.md](examples/private-fund-demo/prd-private-fund-baseline.md) | living baseline / 5 locked scenes |
| [scene-list.md](examples/private-fund-demo/scene-list.md) | 2 Views / 5 Scenes / P0 × 5 |
| [Interaction map HTML](examples/private-fund-demo/deliverables/) | Single file / 9 phone mockups + 1 Web backend + cross-device dataflow table |
| [PRD docx](examples/private-fund-demo/deliverables/) | Landscape 8 chapters / 20 tables / 5 auto-inserted scene screenshots |

Private fund was picked because the compliance chain is representative (qualified-investor checks, cooling-off, large redemptions, NAV disclosure), so it showcases the whole path from a fuzzy ask to a PRD. Generator scripts live in `examples/private-fund-demo/scripts/` — copy them to your project and swap the data.

---

## Quick Start

```bash
# 1. Clone
git clone git@github.com:CaufieldZ/pm-workspace.git
cd pm-workspace

# 2. Install deps (macOS / Linux / WSL / Git Bash)
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
node --version   # Node 18+; no root npm dependencies, so npm install is not required

# Windows PowerShell: replace python3 with py -3 or python

# 3. Activate the anti-rot hook (pre-commit runs audit.sh 1,2,3,4,7,12,13,14,15,16,17,19,20,21)
git config core.hooksPath .githooks

# 4. Personalize (optional)
#    Write LEARNED.md at repo root with your communication preferences / term patches
#    (auto-read every session if present, gitignored).
#    For more structured style control, add files under .claude/output-styles/.

# 5. Open the project
#    VSCode + Claude Code extension (recommended)
#    Cursor is not advised — its Agent system conflicts with Skills / Hooks

# 6. First project
#    In Claude Code, type:
#    > new project my-first-project, the requirement is…
```

---

## Three knowledge layers

The whole system is held up by three layers — **strategy → workflow → project**. Lower layers reference upper layers; upper layers don't care about lower ones.

### Layer 1 · Strategy

`projects/product-lines.md` · **product-line map** (entry constitution of the projects/ domain). Read on demand — when triggered by strategic decisions, cross-line synergy, or new-project routing (trigger list lives in CLAUDE.md). It keeps the whole portfolio in view when deciding on a single line (5-stage funnel / 4-dimension trust / north-star KPIs / synergy matrix / three decision questions). **The `projects/` directory is excluded from public sync wholesale** — every company writes their own.

### Layer 2 · Workflow

Product-management methodology committed to disk, reused across projects. Injection split into two tiers:

| File | Load mode | What it owns |
|:--|:--|:--|
| `CLAUDE.md` | Injected every session | Tool ops · shortcut routes · incoming-request PM-GATE 4-risk scan · three pipeline routing · runbook trigger table |
| `.claude/runbooks/*.md` | Read on demand when trigger hits | 18 runbooks (methodology / artifact conventions / decision framework / LNO / project mgmt / version bump / human voice incl. conversation style / HTML pipeline / Confluence archaeology / AI platform specs entry / etc.) |
| `LEARNED.md` | Injected every session (optional) | Personal communication preferences + correction log (repo root, gitignored) |

### Layer 3 · Project

`projects/{line}/prd-{line}-baseline.md` + `scene-list.md` · **the project's single source of truth**. A structured distillation of PM + AI discussions (a living snapshot of current state); every downstream deliverable grows from it. Change a term or add a scene and the dependency chain is auto-scanned for blast radius.

**baseline + delta** model: the baseline is the living source of truth (no version number, reflects the full live state); each iteration is written as a delta (`deliverables/{quarter}/{version}/`) and merged back into the baseline on ship, with a changelog entry appended. Core rule: the baseline must reflect the latest state; delta changelog entries are append-only by date and never rewritten.

```
Source material (meeting notes / MRD / competitors / verbal)
        ↓ discuss + distill with AI
   baseline (living current state) + delta (this iteration)
        ↓ enter the deliverable pipeline
   scene-list → imap → prototype → prd → cross-check
        ↓
   Downstream AI agents consume directly
```

**Two layers of priority** (keep them separate):

- **Routing priority** (which path to take first): shortcut routes (CLAUDE.md table) > Skill > runbook > model default.
- **Execution-constraint priority** (within a path, whose word counts): Skill hard rules / hook block > CLAUDE.md / runbook > model default.

---

## Skill pipeline

6 pipeline-position Skills run in dependency order (including cross-check as the closing reconciliation); 6 standalone + 1 tool Skill can be called anytime; plus 3 scenario-specific extensions showing how to build your own. 16 total.

```
1 scene-list ─→ 2.5 arch-diagrams* ─→ 3 interaction-map
                                              │
  ┌───────────────────────────────────────────┘
  ▼
4 prototype* ─→ 5 prd ─→ 8 cross-check

                                       * = optional
```

> The PRD md format absorbed everything the former behavior-spec / page-structure skills uniquely owned (business-object dictionary / 5-section business actions / shared copy list / information-hierarchy matrix); they no longer exist as separate skills.

### Pipeline (6)

| # | Skill | Output | Format |
|:-|:-|:-|:-|
| 1 | scene-list | Break the ask into scenes; IDs lock all downstream references (md + optional visual HTML) | `.md` / `.html` |
| 2.5 | architecture-diagrams | Multi-system / money-flow architecture as a multi-tab doc | `.html` |
| 3 | interaction-map | Multi-device UI flows + cross-device dataflow, mockup-grade | `.html` |
| 4 | prototype | Clickable hi-fi prototype, data-driven linkage | `.html` |
| 5 | prd | 12-chapter md PRD with business objects / 5-section scenes / copy matrix / tracking / SLA; auto-pushes to Confluence | `.md` |
| 8 | cross-check | 7-dimension auto-reconciliation (IDs / terms / fields / states / compliance / tracking / assumptions) | terminal output |

### Standalone (6)

| Skill | Description |
|:-|:-|
| competitor-analysis | Competitor research: intel capture (App / Web screenshots / announcement scraping) + tri-way comparison + borrow-able insights |
| data-report | Weekly / monthly / quarterly reports, automated via Sensors + Youshu |
| flowchart | Flowcharts / swimlanes / approval flows, standalone output embeddable elsewhere |
| mrd-review | MRD review: voting table + value judgment + market-window check |
| ppt | Proposal / SOP → multi-tab HTML doc + narration script |
| user-manual | User manuals / help-center articles / launch marketing copy — user-facing launch deliverables |

### Extensions (3 · build-your-own examples)

| Skill | Description |
|:-|:-|
| promo-kit | Turn a feature / campaign into external promo content (video storyboard / 4-panel graphic / short copy, pick one or combine) |
| aihub-package | Enterprise AI-platform packaging pipeline (sanitization checklist → vet → pack → verify) — an example of distributing Skills across teams |
| hx-cli | Internal project-management CLI bridge (tasks / requirements / progress queries) — an example of wrapping an internal system as a tool Skill |

### Tool (1)

| Skill | Description |
|:-|:-|
| workspace-audit | Global diagnostic (Phase 1 script-based 18 + Phase 2 model-reasoning 4), includes hooks health and spec-promise consistency |

---

## Downstream AI consumption

The PRD md is the single source of truth — **chapter structure + locked field names** mean downstream agents don't need to re-parse anything:

```
            ┌─→ Ch. 3 business objects + 5-7 5-section scenes ─→ Dev AI   (Cursor · Copilot · Claude Code)
            │
PRD md ─────┼─→ 5-7 "Page structure & information hierarchy" tables ─→ Design / Frontend AI
            │
            └─→ Ch. 4 rules + scene exception tables + Ch. 9 tracking ─→ QA AI · test automation
```

| PRD section | Consumer | Value |
|:-|:-|:-|
| 3.2 business objects / 3.3 state machines / 5-7 5-section scenes | Dev AI | Complete business semantics + data impact → derive SQL / events / APIs directly |
| 5-7 "Page structure & information hierarchy" tables + screenshots | Design / frontend AI | Module → data source → hierarchy (primary / secondary / meta) all spelled out |
| Ch. 4 rules + per-scene exception tables + Ch. 9 tracking | QA AI · automation | Boundary values, exception branches, and tracking semantics ready to consume |

---

## Engineering guarantees

### Hard constraints (code-level blocks)

| Mechanism | Description |
|:-|:-|
| Anti-rot hook | `.githooks/pre-commit` runs secret scan + staged large-file/local-source-material blocks on every commit; Skill / rule / `.claude/hooks/` changes additionally run `audit.sh 1,2,3,4,7,12,13,14,15,16,17,19,20,21,23,25` (16 hard checks) |
| 16 runtime hooks | 16 hook files fan out into 28 automatic guards: CJK punctuation / plain-language / version sync / wiki push / scripts-first / prototype paradigm / risky-op fallback / Learn-Rule capture / session survival, etc. stderr warnings mean fix-now, blocking hooks reject the write |
| 21 workspace-audit categories | Phase 1 — 21 script-based hard checks (files / numbers / deps / rules / tokens / deliverables / SKILL_TABLE / scripts / imports / trinity purity / hooks health / spec-promise consistency / SKILL structure / dead links / dangling scene IDs / cross-platform / count reconciliation / hub health / script health / threshold distribution / proto reproducibility / gate health, etc.) + Phase 2 — 4 model-reasoning checks (rule conflicts / security / robustness / slimming) |
| Regression tests | 554 pytest cases in `scripts/tests/` (dashboard rendering / CJK punctuation / ID contracts / gate semantics, etc.) + 134 dual-probe assertions in `test-hooks.sh` (must-block forms block, harmless lookalikes pass) — run on any hook / renderer change |
| HTML iron rule | > 200 lines must be script-generated (Step A skeleton → B fill → C self-check), direct Write is forbidden |
| Self-check backpressure | Each Skill carries its own checklist; up to 2 auto-fix attempts, then stops and reports — silent skip is forbidden |
| pre-deliverable-source-gate | HTML with a gen script is read-only; changes go into the source files |

### Soft constraints (methodology)

| Mechanism | Description |
|:-|:-|
| ID locking | Scene IDs cannot change once confirmed; new ones are appended only |
| Term consistency | Module / component / state names defined once, reused end-to-end |
| Change cascade | baseline / delta edit → impact-check scans deps → version-bump along the pipeline → cross-check reconciles |
| baseline / delta split | The baseline reflects the full live state; deltas hold the current iteration and merge back on ship; the two must not contradict |
| Key-assumption list | PRD context 6.x explicitly enumerates prerequisites; cross-check validates landing |
| Bulk-change flow | ≥ 2 cross-file changes must go through impact-check → edit in pipeline order → finish with cross-check |

### Data driven

| Mechanism | Description |
|:-|:-|
| End-to-end telemetry | 16 hooks write `.claude/logs/usage.jsonl` via `lib/log.sh` (skill triggers / hook warn-block-clean / gate skip); biweekly dashboard drives decisions |
| dashboard | `python3 scripts/dashboard.py` aggregates hooks + skills + project snapshot → `.claude/workspace-dashboard.md` |
| Session survival | `pre-compact.sh` injects `session-state.md` + a live git snapshot into the summary before compaction, so progress survives |
| Rule half-life | `.claude/_meta/half-life.md` tags rules volatile/durable; biannual review prunes rarely-triggered ones |
| Public-repo desensitized sync | `sync_public.sh` pushes the framework layer to a separate public repo, using `.public/overrides/` for replacements. Strategy / projects / source material are excluded |

### Visual floor

HTML deliverables (imap / prototype / ppt / flowchart / arch) share `_shared/claude-design/tokens.css`:

| Dimension | Value |
|:-|:-|
| Primary | claude.ai chat-UI warm near-black `#1F1F1E` + warm off-white `#C3C2B7` |
| Accent | Anthropic terra cotta `#D97757` (secondary `#6A9BCC` / tertiary `#788C5D`, cycled across tracks) |
| Marketing-grade contrast | `.theme-cd-brand` → `#141413` / `#FAF9F5` |
| Semantic | success `#00B42A` · failure `#F53F3F` (cross-theme) |
| Font · display | `Noto Serif SC` + `Lora` |
| Font · body | `Noto Sans SC` + `Poppins` |
| Font · mono | `JetBrains Mono` |
| **CJK-first iron rule** | In any font stack, CJK fonts must precede Latin fonts |

Aligned with the [Anthropic official brand-guidelines](https://github.com/anthropics/skills/tree/main/skills/brand-guidelines) (free license).

**Six anti-AI-slop bans** (enforced at the rule layer · violations are rejected): full-screen gradients / emoji-decorated headings / rounded cards + ≥2px accent border (any side) / SVG-drawn people or scenes / generic fonts (Inter · Roboto · Space Grotesk) as CJK body / an icon on every card.

---

## Directory layout

```
pm-workspace/
├── CLAUDE.md                    # Claude Code project-instruction entry
├── sync_public.sh               # Framework → public repo desensitized sync
├── .githooks/pre-commit         # Anti-rot hook (secret / large files / audit)
├── .public/
│   └── overrides/               # public-sync replacement files
├── .claude/
│   ├── hooks/                   # 16 runtime hooks (fan out into 28 guards)
│   │   ├── lib/log.sh           #   shared telemetry (logs/usage.jsonl)
│   │   ├── pre-compact.sh       #   session-state survival
│   │   ├── post-cjk-punct-check.sh
│   │   ├── post-plain-language-check.sh  # plain-language self-check (blocks internal anchors leaking)
│   │   ├── pre-version-sync-gate.sh
│   │   ├── stop-learn-capture.sh         # extracts [LEARN] from transcript → LEARNED.md
│   │   └── ...                  #   16 total
│   ├── runbooks/               # 18 on-demand methodology / ops references, incl. conversation style (human-voice-rules.md §0) + AI platform specs entry (ai-platform-specs.md)
│   ├── _meta/                  # metadata (half-life.md rule half-life index)
│   ├── skills/                  # 17 Skills (trinity: SKILL.md + scripts/ + references/ + assets/)
│   │   ├── {skill}/scripts/     #   executable code (Claude calls; doesn't read source)
│   │   ├── {skill}/references/  #   .md docs (Read on demand)
│   │   ├── {skill}/assets/      #   templates / fonts / config (read by scripts into output)
│   │   └── _shared/
│   │       └── claude-design/   #     shared aesthetic tokens
│   ├── chat-templates/          # Chat-track fallback templates
│   ├── logs/                    # telemetry (usage.jsonl / skip-gates.log)
│   └── settings.json
├── examples/                    # desensitized example projects (visible in public)
│   └── private-fund-demo/       #   private-fund full-pipeline sample
├── scripts/                     # shared scripts
│   ├── lib/
│   │   ├── thresholds.py        #   threshold loader (from lib.thresholds import T)
│   │   └── thresholds.yaml      #   threshold SSOT (200/300/500/1500/Tab≥10)
│   ├── dashboard.py             #   aggregate hooks / skills / projects → workspace-dashboard.md
│   ├── call_mcp.py              #   generic MCP calls (zero schema overhead)
│   ├── fetch_confluence.py
│   ├── fetch_figma.py
│   ├── pull_meeting_notes.py    #   DingTalk Flash-Note puller
│   ├── md_to_confluence.py
│   ├── impact-check.sh          #   scene-change blast-radius scan
│   └── version-bump.sh          #   deliverable version bump
├── requirements.txt
├── package.json
├── references/                  # local source material (gitignored)
│   └── competitors/
└── projects/                    # working projects (excluded from public sync, Schema v2 two-level)
    ├── product-lines.md         # Strategy · product-line map (projects domain entry constitution)
    ├── {line}/
    │   ├── lessons.md           #   product-line layer · cross-project learnings
    │   └── {project}/
    │       ├── prd-{name}-baseline.md  #   single source of truth (living; product-line baseline sits at the line root)
    │       ├── scene-list.md    #   locked scene IDs
    │       ├── inputs/          #   source materials (placement rules in .claude/runbooks/project-mgmt.md)
    │       │   ├── meetings/    #     meeting notes (pull_meeting_notes default)
    │       │   ├── docs/        #     permanent refs (tech spec / API spec / fetched Confluence pages + images)
    │       │   ├── raw/         #     raw pdf / docx / uncategorized screenshots (transient)
    │       │   ├── figma/       #     Figma fetches
    │       │   └── competitors/ #     competitor screenshots
    │       ├── scripts/         #   project-level gen / fill / patch / build scripts
    │       └── deliverables/    #   outputs (prefixes prd- / imap- / proto- / arch- / ppt- / flow- / report-)
    │           ├── assets/      #     product images (svg tracked; png / mmd / drawio gitignored)
    │           │   ├── prd/     #       screenshot_for_prd default
    │           │   └── arch/    #       architecture diagrams
    │           └── archive/     #     old versions (grep with --exclude-dir=archive)
    └── {top-level}/             # proposal-type / infra that doesn't belong to a line
```

---

## Chat track (fallback)

Works without a Claude Code environment, at the cost of the strategy layer, hooks, telemetry and script automation — first-pass quality drops noticeably. Flow:

- Text deliverables (scene list / competitor analysis / text-only PRD): copy the matching prompt from `.claude/chat-templates/`, fill in the placeholders, send to Claude / ChatGPT
- HTML deliverables (interaction map / prototype / architecture): upload 3 files (`prd-{line}-baseline.md` + `scene-list.md` + the template HTML)

The Chat track is for emergencies or when you don't want to set up the tooling. For long-term use, move to Claude Code.

---

## Recommended models

Pick by tier — flagship for decisions, mid-tier for execution — rather than pinning specific versions (models iterate monthly; pinned names go stale):

| Role | Tier | Notes |
|:-|:-|:-|
| Requirement understanding · architecture · complex reasoning | Flagship (Claude Opus / peers) | Decision-making + main executor across the pipeline |
| Day-to-day coding · formatted output | Mid-tier (Claude Sonnet / peers) | Step B fill can be downgraded, saving ~46% |
| Cost-effective alternative | GLM / Kimi / peers | Fallback option; check context limits per model |

---

## Custom Skills

Hand-write the trinity under `.claude/skills/{name}/`: `SKILL.md` + `scripts/` + `references/` + `assets/`. Conventions / naming prefixes / frontmatter spec live in [`.claude/runbooks/skill-conventions.md`](.claude/runbooks/skill-conventions.md); `workspace-audit` Phase 1 validates automatically.

---

## Contributing

Issues and PRs welcome.

```bash
git clone git@github.com:CaufieldZ/pm-workspace.git
cd pm-workspace
git config core.hooksPath .githooks
git checkout -b feat/your-feature
# make changes, then commit (pre-commit hook validates automatically)
git commit -m "feat: your change"
```

---

## License

[Apache License 2.0](LICENSE)

---

## Contact

- GitHub · [@CaufieldZ](https://github.com/CaufieldZ)
- Email · [huajiangxiashu@gmail.com](mailto:huajiangxiashu@gmail.com)

---

<div align="center">

`BUILT WITH · CLAUDE CODE · PYTHON · NODE · HTML`

</div>
