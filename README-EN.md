<div align="center">

# PM Workspace

`AI-NATIVE · PRODUCT MANAGEMENT · PM-WS`

[中文](README.md) · **English**

Meeting notes / MRD / competitor screenshots → scene lists, interaction maps, PRDs, behavior specs. 18 Skills covering the full product-manager workflow.

[![License](https://img.shields.io/badge/license-Apache%202.0-1f54d6?style=flat-square)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-18-D97757?style=flat-square)](.claude/skills)
[![Hooks](https://img.shields.io/badge/hooks-17-000?style=flat-square)](.claude/hooks)
[![Audit](https://img.shields.io/badge/audit-15_categories-000?style=flat-square)](.claude/skills/workspace-audit)
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
| Consistency | Different output each time, term drift | Locked IDs + globally consistent terms + 15-category audit |
| Downstream | PRD thrown to engineering to interpret | Split into behavior-spec / page-structure / test-cases, consumed directly by AI agents |
| Methodology | Scattered across personal habits and docs | Three layers (strategy / workflow / project) written to disk, reusable across sessions and models |

---

## Demo first · a private-fund flow in 20 minutes

A fictional private-fund subscription/redemption project, walking through context → scene-list → interaction map → PRD end-to-end. Measured ~20 min on Sonnet 4.6: [`examples/private-fund-demo/`](examples/private-fund-demo/).

![Interaction map hero](https://raw.githubusercontent.com/CaufieldZ/pm-workspace-public/main/examples/private-fund-demo/screenshots/imap-hero.png)

> Above is the top of the interaction map, PART 0 · H5 investor view (A-1 fund detail + subscription / A-2 agreement signing + cooling-off). All 5 Scenes plus the cross-device dataflow table are in the [full HTML](examples/private-fund-demo/deliverables/imap-private-fund-v1.html).

| Deliverable | Scale |
|:--|:--|
| [context.md](examples/private-fund-demo/context.md) | 9 chapters / 5 locked scenes |
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

# 2. Install deps
pip install -r requirements.txt   # python-docx · defusedxml · playwright · matplotlib · numpy
npx playwright install chromium   # headless browser for competitor capture
npm install                       # docx (Node)

# 3. Activate the anti-rot hook (pre-commit runs audit.sh 1,2,3,4,7,12,13,14,15)
git config core.hooksPath .githooks

# 4. Personalize (optional)
#    Edit .claude/rules/soul.md with your communication preferences (gitignored)

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

`product-lines.md` · **product-line map**. Required reading every session (referenced via `@` at the top of CLAUDE.md) so the model still sees the whole portfolio when deciding on a single line (core funnels / north-star KPIs / product-line synergy matrix). **This file is gitignored** and excluded from public sync — every company writes their own.

### Layer 2 · Workflow

Product-management methodology committed to disk, reused across projects:

| File | What it owns |
|:--|:--|
| `CLAUDE.md` | Claude Code tool-layer config · shortcut routes · context management |
| `.claude/rules/pm-workflow.md` | Requirement routing · the three pipelines · cross-Skill constraints · bulk-change flow |
| `.claude/rules/html-pipeline.md` | Step A/B/C HTML pipeline + aesthetic hard-floor (the six anti-AI-slop bans) |
| `.claude/rules/soul.md` | Personal communication preferences + correction log (gitignored) |

### Layer 3 · Project

`projects/{line}/{project}/context.md` · **the project's single source of truth**. A structured distillation of PM + AI discussions; every downstream deliverable grows from it. Change a term or add a scene and the dependency chain is auto-scanned for blast radius.

Nine-chapter structure: static chapters (1–6 · what the project looks like now) + dynamic chapters (7/9 · how it got here) + hybrid (8 · execution plan). Core rule: dynamic chapters are append-only by date and never rewritten; static chapters must reflect the latest state.

```
Source material (meeting notes / MRD / competitors / verbal)
        ↓ discuss + distill with AI
   context.md (9 chapters)
        ↓ enter the deliverable pipeline
   scene-list → imap → prototype → prd → bspec/pspec/test-cases → cross-check
        ↓
   Downstream AI agents consume directly
```

Execution priority: **Skill hard rules > workflow rules > model default behavior**.

---

## Skill pipeline

10 Pipeline Skills run in dependency order, 5 standalone + 3 tool Skills can be called anytime. 18 total.

```
1 scene-list ─→ 2.5 arch-diagrams* ─→ 3 interaction-map
                                              │
  ┌───────────────────────────────────────────┘
  ▼
4 prototype* ─→ 5 prd ──┬─→ 6 behavior-spec* ─┐
                        ├─→ 6 page-structure* ├─→ 8 cross-check
                        ├─→ 7 test-cases*     ┘
                        └─→ 9 ops-handbook*

                                                    * = optional
```

### Pipeline (10)

| # | Skill | Output | Format |
|:-|:-|:-|:-|
| 1 | scene-list | Break the ask into scenes; IDs lock all downstream references (md + optional visual HTML) | `.md` / `.html` |
| 2.5 | architecture-diagrams | Multi-system / money-flow architecture as a multi-tab doc | `.html` |
| 3 | interaction-map | Multi-device UI flows + cross-device dataflow, mockup-grade | `.html` |
| 4 | prototype | Clickable hi-fi prototype, data-driven linkage | `.html` |
| 5 | prd | Landscape left-image right-text PRD, driven by the context 6.x key-assumption list | `.docx` |
| 6 | behavior-spec | For dev AI: state machine + exception handling | `.md` |
| 6 | page-structure | For design / frontend AI: component tree + data binding | `.md` |
| 7 | test-cases | For QA AI: pairwise modeling + four-category full coverage | `.md` |
| 8 | cross-check | 7-dimension auto-reconciliation (IDs / terms / fields / states / compliance / tracking / assumptions) | terminal output |
| 9 | ops-handbook | Step-by-step doc for ops / CS / BD, produced after PRD sign-off | `.docx` |

### Standalone (5)

| Skill | Description |
|:-|:-|
| competitor-analysis | Competitor research, tri-way comparison + borrow-able insights |
| data-report | Weekly / monthly / quarterly reports, automated via Sensors + Youshu |
| flowchart | Flowcharts / swimlanes / approval flows, standalone output embeddable elsewhere |
| mrd-review | MRD review: voting table + value judgment + market-window check |
| ppt | Proposal / SOP → multi-tab HTML doc + narration script |

### Tool (3)

| Skill | Description |
|:-|:-|
| intel-collector | Intel capture: App screenshots / full-page Web shots / announcement scraping |
| skill-creator | Create a new Skill, auto-generates frontmatter + registration |
| workspace-audit | 15-category global diagnostic (10 hard + 5 soft checks), includes hooks health |

---

## Downstream AI consumption

A traditional PM flow ends at the PRD. This system goes one step further — **it splits the PRD into structured docs that AI agents consume directly**.

```
         ┌─→ behavior-spec  ─→ Dev AI    (Cursor · Copilot · Claude Code)
         │
PRD ─────┼─→ page-structure ─→ Design / Frontend AI
         │
         └─→ test-cases     ─→ QA AI · test automation
```

| Doc | Consumer | Value |
|:-|:-|:-|
| behavior-spec | Dev AI | Full "user does X → system responds Y" spec, no need to read the whole PRD |
| page-structure | Design / frontend AI | Component tree + data binding + interaction states, no guessing layout from screenshots |
| test-cases | QA AI · automation | Boundary values + exception scenarios + compliance checks, drop-in ready |

---

## Engineering guarantees

### Hard constraints (code-level blocks)

| Mechanism | Description |
|:-|:-|
| Anti-rot hook | `.githooks/pre-commit` runs `audit.sh 1,2,3,4,7,12,13,14,15` (9 hard checks) on Skill / rule / `.claude/hooks/` changes, blocks the commit on failure. Secret scan catches figd/sk-ant/ghp/AKIA tokens |
| 17 runtime hooks | CJK punctuation / plain-language / version sync / device naming / wiki push / Dippy destructive-command block / Learn-Rule correction capture, etc. stderr warnings mean fix-now, blocking hooks reject the write |
| 15 workspace-audit categories | 10 hard checks (files / numbers / deps / rules / tokens / deliverables / SKILL_TABLE / scripts / imports / trinity purity) + 5 soft checks (incl. hooks health) |
| HTML iron rule | > 200 lines must be script-generated (Step A skeleton → B fill → C self-check), direct Write is forbidden |
| Self-check backpressure | Each Skill carries its own checklist; up to 2 auto-fix attempts, then stops and reports — silent skip is forbidden |
| pre-deliverable-source-gate | HTML with a gen script is read-only; changes go into the source files |

### Soft constraints (methodology)

| Mechanism | Description |
|:-|:-|
| ID locking | Scene IDs cannot change once confirmed; new ones are appended only |
| Term consistency | Module / component / state names defined once, reused end-to-end |
| Change cascade | context.md edit → impact-check scans deps → version-bump along the pipeline → cross-check reconciles |
| Static/dynamic split in context.md | Static chapters reflect latest state; dynamic chapters are append-only by date; the two must not contradict |
| Key-assumption list | PRD context 6.x explicitly enumerates prerequisites; cross-check validates landing |
| Bulk-change flow | ≥ 2 cross-file changes must go through impact-check → edit in pipeline order → finish with cross-check |

### Data driven

| Mechanism | Description |
|:-|:-|
| End-to-end telemetry | 17 hooks write `.claude/logs/usage.jsonl` via `lib/log.sh` (skill triggers / hook warn-block-clean / gate skip); biweekly dashboard drives decisions |
| dashboard | `python3 scripts/dashboard.py` aggregates hooks + skills + project snapshot → `.claude/workspace-dashboard.md` |
| Session survival | `pre-compact.sh` injects `session-state.md` + a live git snapshot into the summary before compaction, so progress survives |
| Rule half-life | `.claude/runbooks/half-life.md` tags rules volatile/durable; biannual review prunes rarely-triggered ones |
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
├── product-lines.md             # Strategy · product-line map (gitignored)
├── sync_public.sh               # Framework → public repo desensitized sync
├── .githooks/pre-commit         # Anti-rot hook (audit.sh 9 categories)
├── .public/
│   └── overrides/               # public-sync replacement files
├── .claude/
│   ├── hooks/                   # 17 runtime hooks
│   │   ├── lib/log.sh           #   shared telemetry (logs/usage.jsonl)
│   │   ├── pre-compact.sh       #   session-state survival
│   │   ├── post-cjk-punct-check.sh
│   │   ├── post-plain-language-check.sh  # plain-language self-check (blocks internal anchors leaking)
│   │   ├── pre-version-sync-gate.sh
│   │   ├── pre-wiki-push-gate.sh
│   │   ├── stop-learn-capture.sh         # extracts [LEARN] from transcript → LEARNED.md
│   │   └── ...                  #   17 total
│   ├── rules/
│   │   ├── pm-workflow.md       #   workflow · methodology
│   │   ├── html-pipeline.md     #   workflow · HTML generation + aesthetics
│   │   └── soul.md              #   personal preferences (gitignored)
│   ├── skills/                  # 18 Skills (trinity: SKILL.md + scripts/ + references/ + assets/)
│   │   ├── {skill}/scripts/     #   executable code (Claude calls; doesn't read source)
│   │   ├── {skill}/references/  #   .md docs (Read on demand)
│   │   ├── {skill}/assets/      #   templates / fonts / config (read by scripts into output)
│   │   └── _shared/
│   │       └── claude-design/   #     shared aesthetic tokens
│   ├── chat-templates/          # Chat-track fallback templates
│   ├── runbooks/                # rule half-life / migration archive
│   ├── logs/                    # telemetry (usage.jsonl / skip-gates.log)
│   └── settings.json
├── examples/                    # desensitized example projects (visible in public)
│   └── private-fund-demo/       #   private-fund full-pipeline sample
├── scripts/                     # shared scripts
│   ├── dashboard.py             #   aggregate hooks / skills / projects → workspace-dashboard.md
│   ├── call_mcp.py              #   generic MCP calls (zero schema overhead)
│   ├── fetch_confluence.py
│   ├── fetch_figma.py
│   ├── fetch_web.py             #   SPA / multi-page capture (replaces firecrawl)
│   ├── pull_meeting_notes.py    #   DingTalk Flash-Note puller
│   ├── md_to_confluence.py
│   ├── impact-check.sh          #   scene-change blast-radius scan
│   └── version-bump.sh          #   deliverable version bump
├── requirements.txt
├── package.json
├── references/                  # local source material (gitignored)
│   └── competitors/
└── projects/                    # working projects (gitignored, Schema v2 two-level)
    ├── {line}/
    │   └── {project}/
    │       ├── context.md       #   project single source of truth (9 chapters)
    │       ├── scene-list.md    #   locked scene IDs
    │       ├── inputs/
    │       ├── scripts/
    │       └── deliverables/
    └── {top-level}/             # proposal-type / infra that doesn't belong to a line
```

---

## Chat track (fallback)

Works without a Claude Code environment, at the cost of the strategy layer, hooks, telemetry and script automation — first-pass quality drops noticeably. Flow:

- Text deliverables (scene list / competitor analysis / text-only PRD): copy the matching prompt from `.claude/chat-templates/`, fill in the placeholders, send to Claude / ChatGPT
- HTML deliverables (interaction map / prototype / architecture): upload 3 files (`context.md` + `templates-index.md` + the template HTML)

The Chat track is for emergencies or when you don't want to set up the tooling. For long-term use, move to Claude Code.

---

## Recommended models

| Role | Model | Notes |
|:-|:-|:-|
| Requirement understanding · architecture · complex reasoning | Claude Opus 4.7 (1M) | Decision-making + main executor across the pipeline |
| Day-to-day coding · formatted output | Claude Sonnet 4.6 (1M) | Step B fill can be downgraded, saving ~46% |
| Backup (when Sonnet isn't an option) | GLM 5.1 · Kimi K2.6 | Cost-effective fallback, check context per model |

---

## Custom Skills

Use `skill-creator` to build your own:

```
> create a skill: requirement-review checklist
```

Skill Creator walks you through trigger words → inputs/outputs → steps → self-check → pipeline registration. See [`.claude/skills/skill-creator/SKILL.md`](.claude/skills/skill-creator/SKILL.md).

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

<div align="center">

`BUILT WITH · CLAUDE CODE · PYTHON · NODE · HTML`

</div>
