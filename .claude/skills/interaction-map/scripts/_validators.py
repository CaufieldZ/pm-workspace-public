#!/usr/bin/env python3
"""IMAP invariant 共享校验模块。

PART / Scene 结构级 invariant 集中在此，gen_imap_skeleton / update_imap_base / check
按需 import。当前阶段（PR6 最小重构）只迁入 _validate_part_stories；后续按场景扩规则。

import 方式：
    from _validators import validate_part_stories
"""


def validate_part_stories(parts):
    """每个 PART 必须填 story 字段（pm-workflow.md「PART/章节用户故事陈述」强制）。

    技术骨架 / 数据流类 PART 可填 '—' 显式跳过；缺字段直接报错，不静默放空。
    """
    missing = [p.get('id', '?') for p in parts if not p.get('story')]
    if missing:
        raise ValueError(
            f'❌ 以下 PART 缺 story 字段（用户故事一句话，≤30 字）：{missing}\n'
            '   pm-workflow.md「演讲叙事顺序」要求每个 PART 起头一句用户故事陈述。\n'
            '   技术骨架/数据流 PART 可填 "—" 显式跳过。'
        )
