"""check_decisions 纯函数测试：正 / 负 / 边界（SCRIPTS_WRITING §K——声明的检查维度必须自证能命中）。"""
import pytest

from check_decisions import check_filename, check_text, parse_sections


def note(lifecycle: str, sections: dict[str, str], title: str = "# Decision: 测试标题",
         status: str | None = None) -> str:
    """按骨架拼一篇 note；status=None 时按生命周期给合法缺省。"""
    if status is None:
        status = {"proposed": "Status: proposed", "implemented": "Status: implemented",
                  "rejected": "Status: rejected — 与既有机制重复"}[lifecycle]
    body = "\n\n".join(f"## {name}\n\n{content}" for name, content in sections.items())
    return f"{title}\n\n{status}\n\n{body}\n"


def codes(hits: list[tuple[int, str, str]]) -> set[str]:
    return {code for _, code, _ in hits}


FULL_IMPLEMENTED = {
    "Problem": "问题陈述。",
    "Decision": "已生效的决策。",
    "Alternatives considered": "- 备选 A：输了，因为 X。\n- 备选 B：输了，因为 Y。",
    "Consequences": "买到 Z，付出 W。",
}
FULL_PROPOSED = {
    "Problem": "问题陈述。",
    "Proposal": "拟做的事。",
    "Alternatives considered": "- 备选 A：输了，因为 X。",
}
FULL_REJECTED = dict(FULL_PROPOSED)


class TestValid:
    @pytest.mark.parametrize("lifecycle,sections", [
        ("proposed", FULL_PROPOSED),
        ("implemented", FULL_IMPLEMENTED),
        ("rejected", FULL_REJECTED),
    ])
    def test_full_skeleton_clean(self, lifecycle, sections):
        assert check_text(note(lifecycle, sections), lifecycle) == []

    def test_proposed_without_consequences_clean(self):
        """proposed 的 Consequences 可选——负对照，确认没把可选章当必需。"""
        assert codes(check_text(note("proposed", FULL_PROPOSED), "proposed")) == set()


class TestSections:
    @pytest.mark.parametrize("missing,code", [
        ("Problem", "section-missing"),
        ("Decision", "section-missing"),
        ("Alternatives considered", "section-missing"),
        ("Consequences", "section-missing"),
    ])
    def test_implemented_missing_required(self, missing, code):
        sections = {k: v for k, v in FULL_IMPLEMENTED.items() if k != missing}
        assert code in codes(check_text(note("implemented", sections), "implemented"))

    def test_implemented_spec_speak_banned(self):
        sections = {**FULL_IMPLEMENTED, "Proposal": "残留的提案期章节。"}
        assert "spec-speak" in codes(check_text(note("implemented", sections), "implemented"))

    def test_implemented_acceptance_criteria_banned(self):
        sections = {**FULL_IMPLEMENTED, "Acceptance criteria": "残留的验收清单。"}
        assert "spec-speak" in codes(check_text(note("implemented", sections), "implemented"))

    def test_rejected_accepts_decision_instead_of_proposal(self):
        sections = {k: v for k, v in FULL_REJECTED.items() if k != "Proposal"}
        sections["Decision"] = "提案期已按此定型后被否。"
        assert check_text(note("rejected", sections), "rejected") == []


class TestAlternatives:
    def test_empty_alternatives_hits(self):
        sections = {**FULL_IMPLEMENTED, "Alternatives considered": ""}
        assert "alternatives-empty" in codes(check_text(note("implemented", sections), "implemented"))

    def test_placeholder_tolerates_empty(self):
        sections = {**FULL_IMPLEMENTED,
                    "Alternatives considered": "<!-- alternatives-not-recorded -->"}
        assert "alternatives-empty" not in codes(
            check_text(note("implemented", sections), "implemented"))

    def test_whitespace_only_alternatives_hits(self):
        sections = {**FULL_IMPLEMENTED, "Alternatives considered": "  \n\n"}
        assert "alternatives-empty" in codes(check_text(note("implemented", sections), "implemented"))


class TestStatus:
    def test_status_folder_mismatch(self):
        hits = check_text(note("proposed", FULL_PROPOSED), "implemented")
        assert "status-value" in codes(hits)

    def test_status_missing(self):
        text = "# Decision: 测试\n\n## Problem\n\n问题。\n\n## Proposal\n\n拟做。\n\n## Alternatives considered\n\n- A 输。"
        assert "status-missing" in codes(check_text(text, "proposed"))

    def test_rejected_requires_reason(self):
        text = note("rejected", FULL_REJECTED, status="Status: rejected")
        assert "status-reason" in codes(check_text(text, "rejected"))

    def test_only_rejected_may_carry_reason(self):
        text = note("implemented", FULL_IMPLEMENTED, status="Status: implemented — 多余理由")
        assert "status-value" in codes(check_text(text, "implemented"))

    def test_bad_title(self):
        hits = check_text(note("implemented", FULL_IMPLEMENTED, title="# 决策：测试"), "implemented")
        assert "title" in codes(hits)


class TestFilename:
    @pytest.mark.parametrize("name", [
        "2026-08-17-adopt-decision-records.md",
        "2026-01-02-x.md",
    ])
    def test_valid(self, name):
        assert check_filename(name) is None

    @pytest.mark.parametrize("name", [
        "adopt-decision-records.md",        # 缺日期前缀
        "2026-8-17-no-pad.md",              # 日期未补零
        "2026-08-17-大写Slug.md",           # 非 ASCII
        "2026-08-17-Trailing-.md",          # 大写
    ])
    def test_invalid(self, name):
        assert check_filename(name) is not None


class TestParseSections:
    def test_parse_returns_line_numbers_and_bodies(self):
        text = "# Decision: t\n\nStatus: proposed\n\n## Problem\n\n问题。\n\n## Proposal\n\n拟做。"
        sections = parse_sections(text)
        assert set(sections) == {"Problem", "Proposal"}
        assert sections["Problem"][0] == 5
        assert "问题" in sections["Problem"][1]
