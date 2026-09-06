"""sync_hx_status 纯函数回归：火效字段解析 / 状态映射 / PRD TAG 日期 / 两条管线回写。

只测纯函数（吃字符串 → 返回结构），不触网络——hx-cli 调用在 sync_one 的 I/O 层，
纯函数与网络解耦，这里锁定「火效状态 → 本地缓存投影」的映射与回写契约。
"""
import sync_hx_status as s

# ── 火效字段 / 状态解析 ────────────────────────────────────────────────

def test_parse_hx_work_id_real():
    assert s.parse_hx_work_id("- **火效**：https://INTERNAL_URL_REDACTED") == "402040"


def test_parse_hx_work_id_bare_h():
    assert s.parse_hx_work_id("**火效**：H388202") == "388202"


def test_parse_hx_work_id_placeholder_none():
    assert s.parse_hx_work_id("- **火效**：https://INTERNAL_URL_REDACTED<work_id>（H 号）") is None


def test_parse_hx_work_id_missing_none():
    assert s.parse_hx_work_id("- **baseline**：xxx\n- **状态**：开发中") is None


def test_current_local_status():
    assert s.current_local_status("- **状态**：已合并") == "已合并"


# ── 火效流程 → 本地受控词映射 ──────────────────────────────────────────

def test_map_status_live_by_prd_tag():
    assert s.map_status("测试中", has_prd_tag=True) == "已上线"


def test_map_status_live_by_process():
    assert s.map_status("已完成", has_prd_tag=False) == "已上线"


def test_map_status_dev():
    assert s.map_status("研发中", has_prd_tag=False) == "开发中"
    assert s.map_status("验收中", has_prd_tag=False) == "开发中"


def test_map_status_unknown_returns_empty():
    # 未知节点 → 空串，调用方保留本地值不猜
    assert s.map_status("某个没见过的节点", has_prd_tag=False) == ""


# ── PRD TAG 上线日期 ───────────────────────────────────────────────────

def test_earliest_prd_date_picks_min():
    rows = [
        {"tag": "PRD_1", "created_at": "2026-07-15 10:00:00"},
        {"tag": "PRD_2", "created_at": "2026-07-10 09:00:00"},
    ]
    assert s.earliest_prd_date(rows) == "2026-07-10"


def test_earliest_prd_date_empty():
    assert s.earliest_prd_date([]) is None


def test_earliest_prd_date_normalizes():
    assert s.earliest_prd_date([{"t": "2026/7/3"}]) == "2026-07-03"


# ── 管线 1：头部状态回写 ───────────────────────────────────────────────

def test_rewrite_header_status_changes():
    text = "- **状态**：开发中\n正文"
    new, ch = s.rewrite_header_status(text, "已上线")
    assert "**状态**：已上线" in new
    assert ch and "开发中 → 已上线" in ch


def test_rewrite_header_status_merged_not_overwritten():
    # 本地「已合并」是本地动作，火效无此态，不被覆盖
    text = "- **状态**：已合并\n正文"
    new, ch = s.rewrite_header_status(text, "已上线")
    assert new == text
    assert ch is None


def test_rewrite_header_status_noop_when_same():
    text = "- **状态**：已上线"
    new, ch = s.rewrite_header_status(text, "已上线")
    assert new == text and ch is None


# ── 协作表头部形态（骨架 v5 起头部是表格，不再是 bullet）───────────────────

_TABLE_HEAD = """# 示例直播 · Delta PRD · 2.3

| 项 | 内容 | 项 | 内容 |
| :--- | :--- | :--- | :--- |
| PRD 版本 | 2.3 | 状态 | 开发中 |
| 拟制人 / 日期 | Felix / 2026-07-25 | 火效 | https://INTERNAL_URL_REDACTED |

# 1. 背景与价值

# 8. 排期 / 上线节奏

| 阶段 | 起止 | 进度 | 状态 | 影响指标 |
| :--- | :--- | :--- | :--- | :--- |
| 上线 | 2026-08-01 | — | 待启 | 推流失败率 |
"""


def test_parse_hx_work_id_from_table_cell():
    assert s.parse_hx_work_id(_TABLE_HEAD) == "405340"


def test_parse_hx_work_id_table_placeholder_none():
    text = "# T\n\n| 项 | 内容 |\n| :--- | :--- |\n| 火效 | {{ 待填：H 号 }} |\n\n# 1. 背景\n"
    assert s.parse_hx_work_id(text) is None


def test_current_local_status_from_table_cell():
    assert s.current_local_status(_TABLE_HEAD) == "开发中"


def test_rewrite_header_status_table_cell():
    new, ch = s.rewrite_header_status(_TABLE_HEAD, "已上线")
    assert "| 状态 | 已上线 |" in new
    assert ch and "开发中 → 已上线" in ch


def test_rewrite_header_status_table_does_not_touch_schedule():
    # §排期表有「状态」列头，回写只能落头部块，不许改到排期行
    new, _ = s.rewrite_header_status(_TABLE_HEAD, "已上线")
    assert "| 上线 | 2026-08-01 | — | 待启 | 推流失败率 |" in new
    assert new.count("已上线") == 1


# ── 管线 2：§排期表回写（含 4 列变体）──────────────────────────────────

_SCHEDULE_4COL = """# 8. 排期 / 上线节奏

| 阶段 | 起止 | 状态 | 说明 |
| :--- | :--- | :--- | :--- |
| 前端 web + h5 | 待定 | 待启 | 无需 app 跟版 |
| 联调 / 灰度 / 全量 | 待定 | 待启 | 可分批灰度 |

# 9. 反向合并
"""


def test_rewrite_schedule_hits_rollout_row():
    new, changes = s.rewrite_schedule(_SCHEDULE_4COL, "2026-07-15")
    # 「联调 / 灰度 / 全量」行命中（含灰度/全量关键词）
    assert "2026-07-15" in new
    assert any("2026-07-15" in c for c in changes)
    assert any("已完成" in c for c in changes)
    # 非上线行（纯前端）不动
    assert "| 前端 web + h5 | 待定 | 待启" in new


def test_rewrite_schedule_no_table():
    text = "# 1. 背景\n没有排期表"
    new, changes = s.rewrite_schedule(text, "2026-07-15")
    assert new == text
    assert any("未找到" in c for c in changes)


def test_rewrite_schedule_5col_variant():
    five = """# 5. 排期 / 上线节奏

| 阶段 | 起止 | 进度 | 状态 | 影响指标 |
| :--- | :--- | :--- | :--- | :--- |
| 上线全量 | 待定 | 0% | 待启 | DAU |

# 6. 下一章
"""
    new, changes = s.rewrite_schedule(five, "2026-07-20")
    assert "2026-07-20" in new
    assert "已完成" in new
    # 进度列不被误改
    assert "| 0% |" in new
