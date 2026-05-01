"""违规报告（CLI 报告 + push gate 报告共享）。"""
import sys


def report_violations(result: dict, file=sys.stderr) -> int:
    """打印扫描结果到 stderr，返回 fail 标志（1 = 有 FAIL 级违规）。"""
    fail = 0
    if result['date_tag_hits']:
        n = len(result['date_tag_hits'])
        print(f"❌ 流水账日期 / 版本痕迹 {n} 处（PRD 必须讲人话，禁 (YYYY-MM-DD) / (from vN) / (变更) / (新增) / 反转说明 / 砍掉）：", file=file)
        for h in result['date_tag_hits'][:5]:
            print(f"   {h}", file=file)
        print("   修复: from humanize import humanize_prd_voice; humanize_prd_voice(doc)", file=file)
        print("   规范: .claude/skills/prd/references/prd-human-voice.md", file=file)
        fail = 1
    if result['snake_field_hits']:
        n = len(result['snake_field_hits'])
        print(f"⚠️  正文 snake_case 字段名 {n} 处（PRD 给 PM/业务读，正文应改白话；字段表/枚举值/埋点表豁免）：", file=file)
        for h in result['snake_field_hits'][:5]:
            print(f"   {h}", file=file)
        print("   修复: humanize_prd_voice(doc, extra_jargon=[(re.compile(r'\\bxxx_yyy\\b'), '中文')])", file=file)
        print("   bspec / pspec / test-cases 不受此约束（研发/QA/设计师消费，允许字段名）", file=file)
    if result['css_impl_hits']:
        n = len(result['css_impl_hits'])
        print(f"⚠️  正文疑似 CSS 实现细节 {n} 处（PRD 描述 What 不描述 How）：", file=file)
        for h in result['css_impl_hits'][:3]:
            print(f"   {h}", file=file)
        print("   产品描述说「半透明遮罩 / 蓝色按钮」即可，具体值由设计稿定", file=file)
    if result.get('zombie_heading_hits'):
        n = len(result['zombie_heading_hits'])
        print(f"❌ 僵尸 Scene/章节 {n} 处（标题含「砍掉/已删除/废弃」，PRD 描述当前态应物理删除整段）：", file=file)
        for h in result['zombie_heading_hits'][:5]:
            print(f"   {h}", file=file)
        print("   修复: H2 + 紧跟 scene_table 一起 remove；delta 写到 1.3 变更范围「本期不做」", file=file)
        fail = 1
    if result.get('v_tag_heading_hits'):
        n = len(result['v_tag_heading_hits'])
        print(f"❌ 标题含 V 版本流水 {n} 处（H2/H3 应描述当前态，版本 delta 归 1.3）：", file=file)
        for h in result['v_tag_heading_hits'][:5]:
            print(f"   {h}", file=file)
        print("   修复: humanize_prd_voice(doc) 自动剥离标题里的「(V x.y …)」括号", file=file)
        fail = 1
    if result.get('legacy_blue_hits'):
        n = len(result['legacy_blue_hits'])
        print(f"❌ 旧版蓝色 cell shading {n} 处（V2.7-era 残留 #2D81FF / #D5E8F0，新规范无填色 / #F8FAFB）：", file=file)
        for h in result['legacy_blue_hits'][:5]:
            print(f"   {h}", file=file)
        print("   修复: humanize_prd_voice(doc) 自动归一为新规范配色", file=file)
        fail = 1
    if result.get('invisible_text_hits'):
        n = len(result['invisible_text_hits'])
        print(f"❌ 视觉死字 {n} 处（run color=#FFFFFF 但 cell 非深色填色 → 白字白底看不见）：", file=file)
        for h in result['invisible_text_hits'][:5]:
            print(f"   {h}", file=file)
        print("   修复: humanize_prd_voice(doc) 自动改色为 #333333（textPrimary）", file=file)
        fail = 1
    if result.get('dirty_cell_hits'):
        n = len(result['dirty_cell_hits'])
        print(f"❌ Dirty cell {n} 处（单段 ≥80 字 + ≥2 emoji 或 ≥2 个「→」= 上游 gen 脚本误用 set_cell_text 塞 \\n 串）：", file=file)
        for h in result['dirty_cell_hits'][:5]:
            print(f"   {h}", file=file)
        print("   根因: SKILL.md R1 警告项 — set_cell_text 塞多行字符串 → Word 渲染成单段无层次纯文本", file=file)
        print("   修复: 项目脚本改用 set_cell_blocks(cell, [(title, [lines])])  结构化重写", file=file)
        fail = 1
    return fail
