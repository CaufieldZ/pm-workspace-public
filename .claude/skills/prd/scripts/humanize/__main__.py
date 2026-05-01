"""CLI: python3 -m humanize <docx>

退出码:
    1 = 流水账 / 僵尸标题 / V 版本流水 / 旧蓝色 / 视觉死字（FAIL）
    0 = 仅 WARN 或全通过
"""
import sys

from .scan import scan_human_voice
from .report import report_violations


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print("用法: python3 -m humanize <docx>")
        print("功能: 扫描 PRD docx 的「讲人话」违规（流水账 / snake_case / CSS）")
        print("退出码: 1 = 流水账（FAIL）；0 = 仅 WARN 或全通过")
        sys.exit(0 if len(sys.argv) >= 2 and sys.argv[1] in ('-h', '--help') else 1)
    from docx import Document
    doc = Document(sys.argv[1])
    result = scan_human_voice(doc)
    fail = report_violations(result)
    if not fail and not result['snake_field_hits'] and not result['css_impl_hits']:
        print("✅ 讲人话检查通过（流水账 / snake_case / CSS 三项 0 违规）")
    sys.exit(fail)


if __name__ == '__main__':
    main()
