#!/usr/bin/env python3
"""v4.7 交互大图 → v4.9 patch（04-23 八项决策 + 04-24 外显标签）

变更项（7 项，MGT 侧 M-2 + 场景总览）：
  1. title v4.7 → v4.9
  2. M-2 全局配置区 mock 重写（副标题回归 + 业务线多选 + 外显标签单选 + 画像包 ID + 删置顶大卡）
  3. M-2 多语种配置区 mock（简中/英文必配 + 图片扩至 4 套）
  4. M-2 flow-note 更新版本号 + 变更点
  5. M-2 标注区补全（3b 业务线 / 3c 外显标签 / 3d 副标题 / 3e 画像包 / 4 删置顶 / 5 图片 4 套 / 6 多语言兜底）
  6. 场景总览标题 8 → 9
  7. 场景总览补 M-9 活动日历行

对应决策：20/23/24/25/27/28/29/31/32（context.md §7）

用法：
  python3 projects/growth/activity-center/scripts/patch_imap_v49.py
  生成：deliverables/活动中心_交互大图_v4.9.html（以 v4.7 为底）
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(ROOT, 'deliverables/archive/活动中心_交互大图_v4.7.html')
DST = os.path.join(ROOT, 'deliverables/活动中心_交互大图_v4.9.html')

with open(SRC, 'r', encoding='utf-8') as f:
    html = f.read()


def patch(old, new, desc, n=1):
    global html
    cnt = html.count(old)
    if cnt != n:
        raise SystemExit(f'[FAIL] {desc}: expected {n} match, got {cnt}')
    html = html.replace(old, new)
    print(f'[OK] {desc}' + (f' (×{n})' if n != 1 else ''))


# ═══ 1. Title ═══
patch(
    '<title>活动中心 · 交互大图 v4.7</title>',
    '<title>活动中心 · 交互大图 v4.9</title>',
    '1. title v4.7 → v4.9',
)

# ═══ 2. M-2 全局配置区 mock 重写 ═══
patch(
    '''            <!-- 全局配置区 -->
            <div class="f-sec" style="background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:8px;">
              <div class="f-sec-t" style="color:#92400e;">① 全局配置区 <span class="badge-n" style="background:#fde68a;color:#78350f;">必填</span></div>
              <div class="f-row"><div class="f-lbl"><span class="req">*</span> 业务线</div><div><span class="f-sel" style="color:#d97706;font-weight:600;">全站 ▾</span><div class="f-hint">单选 · 巅峰赛选「全站」，合约活动选「合约」</div></div></div>
              <div class="f-row"><div class="f-lbl"><span class="req">*</span> 活动品牌</div>
                <div>
                  <div class="f-chks" style="max-width:200px;">
                    <span class="f-chk" style="background:#dcfce7;color:#15803d;border-color:#86efac;">☑ 巅峰赛</span>
                    <span class="f-chk">☐ 交易赛</span>
                    <span class="f-chk">☐ 积分赛</span>
                    <span class="f-chk">☐ …</span>
                  </div>
                  <div class="f-hint">多选 · 15 个枚举值 · 一个活动可属多个品牌</div>
                </div>
              </div>
              <div class="f-row"><div class="f-lbl">币种</div>
                <div>
                  <div class="f-chks" style="max-width:200px;">
                    <span class="f-chk" style="background:#dcfce7;color:#15803d;border-color:#86efac;">☑ BTC</span>
                    <span class="f-chk">☐ ETH</span>
                    <span class="f-chk">☐ SOL</span>
                    <span class="f-chk">☐ …</span>
                  </div>
                  <div class="f-hint">多选 · Platform C 已上线币种</div>
                </div>
              </div>
              <div class="f-row"><div class="f-lbl"><span class="req">*</span> 时间</div><div><input class="f-inp" value="2026-04-10" style="width:80px" readonly> ~ <input class="f-inp" value="2026-05-10" style="width:80px" readonly></div></div>
              <div class="f-row"><div class="f-lbl">命中人群</div><div><span class="f-sel">全量 ▾</span></div></div>
              <div class="f-row"><div class="f-lbl">置顶大卡</div><div><span style="font-size:10px;">☑ 启用（Wide Card 置顶展示）</span></div></div>
            </div>''',
    '''            <!-- 全局配置区 -->
            <div class="f-sec" style="background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:8px;">
              <div class="f-sec-t" style="color:#92400e;">① 全局配置区 <span class="badge-n" style="background:#fde68a;color:#78350f;">必填</span></div>
              <div class="f-row"><div class="f-lbl"><span class="req">*</span> 主标</div><div><input class="f-inp" value="BTC Summit Race II（内部）" style="width:180px" readonly><div class="f-hint">内部使用 · 系统内唯一</div></div></div>
              <div class="f-row"><div class="f-lbl">副标题 <span class="badge-n" style="background:#dcfce7;color:#15803d;">v4.9 回归</span></div><div><input class="f-inp" value="单笔 ≥ 100 USDT 即可参与" style="width:180px" readonly><div class="f-hint">前台卡片展示 · 长度后台限制</div></div></div>
              <div class="f-row"><div class="f-lbl"><span class="req">*</span> 业务线 <span class="badge-n" style="background:#dcfce7;color:#15803d;">v4.9 改多选</span></div>
                <div>
                  <div class="f-chks" style="max-width:200px;">
                    <span class="f-chk" style="background:#dcfce7;color:#15803d;border-color:#86efac;">☑ 全站</span>
                    <span class="f-chk">☐ 现货</span>
                    <span class="f-chk">☐ 合约</span>
                    <span class="f-chk">☐ …</span>
                  </div>
                  <div class="f-hint">多选 Checkbox · 跨业务活动可多勾 · 「全站」为独立枚举</div>
                </div>
              </div>
              <div class="f-row"><div class="f-lbl"><span class="req">*</span> 活动品牌</div>
                <div>
                  <div class="f-chks" style="max-width:200px;">
                    <span class="f-chk" style="background:#dcfce7;color:#15803d;border-color:#86efac;">☑ 巅峰赛</span>
                    <span class="f-chk">☐ 交易赛</span>
                    <span class="f-chk">☐ 积分赛</span>
                    <span class="f-chk">☐ …</span>
                  </div>
                  <div class="f-hint">多选 · 15 个枚举值 · 合约类退役合并进通用品牌</div>
                </div>
              </div>
              <div class="f-row"><div class="f-lbl">外显标签 <span class="badge-n" style="background:#dcfce7;color:#15803d;">v4.9 收口</span></div>
                <div>
                  <span class="f-sel" style="color:#d97706;font-weight:600;">🔥 火爆 ▾</span>
                  <div class="f-hint">单选 · 11 值固定池（火爆/NEW/新手/限时/高奖励/独家/专属/限量/VIP/邀请专属/每日福利）· <b>不参与专题规则</b> · 多语言技术预埋 i18n key</div>
                </div>
              </div>
              <div class="f-row"><div class="f-lbl">币种</div>
                <div>
                  <div class="f-chks" style="max-width:200px;">
                    <span class="f-chk" style="background:#dcfce7;color:#15803d;border-color:#86efac;">☑ BTC</span>
                    <span class="f-chk">☐ ETH</span>
                    <span class="f-chk">☐ SOL</span>
                    <span class="f-chk">☐ …</span>
                  </div>
                  <div class="f-hint">多选 · Platform C 已上线币种</div>
                </div>
              </div>
              <div class="f-row"><div class="f-lbl"><span class="req">*</span> 时间</div><div><input class="f-inp" value="2026-04-10" style="width:80px" readonly> ~ <input class="f-inp" value="2026-05-10" style="width:80px" readonly></div></div>
              <div class="f-row"><div class="f-lbl">适用人群 <span class="badge-n" style="background:#dcfce7;color:#15803d;">v4.9 扩展</span></div>
                <div>
                  <span style="font-size:10px;"><label><input type="radio" checked> 全量</label> &nbsp; <label><input type="radio"> 画像包 ID</label></span>
                  <div class="f-hint">选「画像包 ID」时填画像中台返回的 ID（支持离线 / 实时）</div>
                </div>
              </div>
              <div class="f-row" style="opacity:.45;"><div class="f-lbl"><s>置顶大卡</s> <span class="badge-del">v4.9 删</span></div><div><div class="f-hint" style="color:#F53F3F;">改由广告管理系统承载（右侧 Banner 接 Gas 资源位）</div></div></div>
            </div>''',
    '2. M-2 全局配置区 mock 重写（副标题/业务线多选/外显标签/画像包/删置顶大卡）',
)

# ═══ 3. M-2 多语种配置区 mock（简中+英文必配 + 图片 4 套）═══
patch(
    '''              <div class="f-sec-t" style="color:#1e40af;">② 多语种配置区 <span style="font-weight:400;font-size:8px;">（Tab 切换，各语种独立）</span></div>
              <div style="display:flex;gap:3px;border-bottom:1px solid #bfdbfe;margin-bottom:8px;">
                <span style="padding:3px 8px;color:#2D81FF;border-bottom:2px solid #2D81FF;font-weight:600;">英文 ✓</span>
                <span style="padding:3px 8px;color:#86909C;">简中</span>
                <span style="padding:3px 8px;color:#86909C;">繁中</span>
                <span style="padding:3px 8px;color:#86909C;">…</span>
              </div>
              <div class="f-row"><div class="f-lbl"><span class="req">*</span> 活动标题</div><div><input class="f-inp" value="BTC Summit Race II" style="width:160px" readonly></div></div>
              <div class="f-row">
                <div class="f-lbl">图片（白底）</div>
                <div class="f-img" style="background:#f8fafc;border:1px dashed #cbd5e1;">🖼 白</div>
                <div class="f-lbl" style="margin-left:6px;">图片（黑底）</div>
                <div class="f-img" style="background:#1e293b;border:1px dashed #475569;color:#fff;">🖼 黑</div>
              </div>
              <div class="f-hint" style="margin:-4px 0 6px;">图片跟语种走 · 白底/黑底各自独立上传</div>''',
    '''              <div class="f-sec-t" style="color:#1e40af;">② 多语种配置区 <span style="font-weight:400;font-size:8px;">（Tab 切换；简中 + 英文必配，其他语种走兜底 v4.9）</span></div>
              <div style="display:flex;gap:3px;border-bottom:1px solid #bfdbfe;margin-bottom:8px;">
                <span style="padding:3px 8px;color:#2D81FF;border-bottom:2px solid #2D81FF;font-weight:600;">英文★ ✓</span>
                <span style="padding:3px 8px;color:#86909C;">简中★</span>
                <span style="padding:3px 8px;color:#86909C;">繁中</span>
                <span style="padding:3px 8px;color:#86909C;">越南</span>
                <span style="padding:3px 8px;color:#86909C;">…</span>
              </div>
              <div class="f-row"><div class="f-lbl"><span class="req">*</span> 活动标题</div><div><input class="f-inp" value="BTC Summit Race II" style="width:160px" readonly></div></div>
              <div class="f-row">
                <div class="f-lbl">图片 <span class="badge-n" style="background:#dcfce7;color:#15803d;">v4.9 扩 4 套</span></div>
                <div style="display:flex;gap:4px;flex-wrap:wrap;">
                  <div class="f-img" style="background:#f8fafc;border:1px dashed #cbd5e1;font-size:8px;">H5白</div>
                  <div class="f-img" style="background:#1e293b;border:1px dashed #475569;color:#fff;font-size:8px;">H5黑</div>
                  <div class="f-img" style="background:#f8fafc;border:1px dashed #cbd5e1;font-size:8px;">Web白</div>
                  <div class="f-img" style="background:#1e293b;border:1px dashed #475569;color:#fff;font-size:8px;">Web黑</div>
                </div>
              </div>
              <div class="f-hint" style="margin:-4px 0 6px;">H5×白 / H5×黑 / Web×白 / Web×黑 共 4 套 · 跟语种走独立上传</div>''',
    '3. M-2 多语种配置区 mock（简中英文必配 + 图片 4 套）',
)

# ═══ 4. M-2 flow-note ═══
patch(
    '<div class="flow-note">M-2 重排（v4.7）：全局配置区 → 专题命中预览 → 多语种配置区（标题/图片白黑/链接）→ 产品运营专属区<br>品牌改多选 · 链接改相对路径 · 图片跟语种走</div>',
    '<div class="flow-note">M-2 重排（v4.9）：全局配置区 → 专题命中预览 → 多语种配置区（标题/图片 4 套/链接）→ 产品运营专属区<br>副标题回归 · 业务线多选 · 外显标签单选 11 值 · 画像包 ID · 图片 4 套 · 简中英文必配 · 删置顶大卡</div>',
    '4. M-2 flow-note 更新版本号 + 变更点',
)

# ═══ 5. M-2 标注区补全（插入 3b/3c/3d/3e/4/5/6 七条，替换原 3 和 4）═══
patch(
    '''    <div class="ann-item"><div class="ann-num amber">3</div><div class="ann-text"><b>全局配置区（新）</b>：业务线（单选）+ 活动品牌（<b>多选，从单选改！</b>）+ 币种（多选）+ 时间 + 命中人群 + 置顶大卡。下方实时显示「专题命中预览」胶囊。 <span class="ann-tag p0">P0</span></div></div>
    <div class="ann-item"><div class="ann-num green">4</div><div class="ann-text"><b>置顶大卡</b>：开启后 Wide Card 置顶展示。 <span class="ann-tag p0">P0</span></div></div>''',
    '''    <div class="ann-item"><div class="ann-num amber">3</div><div class="ann-text"><b>全局配置区（v4.9 重定义）</b>：主标 + 副标题（回归）+ 业务线（<b>多选</b>）+ 活动品牌（多选）+ 外显标签（<b>单选 11 值</b>）+ 币种（多选）+ 时间 + 适用人群（全量 / 画像包 ID）。下方实时显示「专题命中预览」胶囊。 <span class="ann-tag p0">P0</span></div></div>
    <div class="ann-item"><div class="ann-num amber">3b</div><div class="ann-text"><b>业务线改多选（决策 23, v4.9）</b>：从单选下拉 → 多选 Checkbox。绝大多数活动勾 1 个；跨业务线活动（现货+合约联动）可多勾。「全站」保留独立枚举，非「勾所有」语法糖。专题匹配语义：活动业务线集合 ∩ 专题 bizList ≠ ∅ 即命中。 <span class="ann-tag p0">P0</span></div></div>
    <div class="ann-item"><div class="ann-num amber">3c</div><div class="ann-text"><b>外显标签字段（决策 32, v4.9）</b>：卡片装饰标，单选，11 值固定池（火爆 / NEW / 新手 / 限时 / 高奖励 / 独家 / 专属 / 限量 / VIP / 邀请专属 / 每日福利）。<b>不参与专题规则</b>。多语言由技术预埋 i18n key，所有语种翻译随包发布，运营不可改。替代原「其他标签」设计（决策 26 作废）。 <span class="ann-tag p0">P0</span></div></div>
    <div class="ann-item"><div class="ann-num amber">3d</div><div class="ann-text"><b>副标题字段回归（决策 31, v4.9）</b>：前台卡片展示，解释主标含义，长度后台限制。 <span class="ann-tag p0">P0</span></div></div>
    <div class="ann-item"><div class="ann-num amber">3e</div><div class="ann-text"><b>适用人群扩展（决策 27, v4.9）</b>：单选「全量 / 画像包 ID」，选 ID 时填画像中台返回的 ID（支持离线 / 实时画像包）。 <span class="ann-tag p0">P0</span></div></div>
    <div class="ann-item"><div class="ann-num red">4</div><div class="ann-text"><b>删除置顶大卡（决策 25, v4.9）</b>：改由广告管理系统在活动页加广告位承载（右侧 Banner 接 Gas 资源位接口）。 <span class="ann-tag p0">P0</span></div></div>
    <div class="ann-item"><div class="ann-num amber">5</div><div class="ann-text"><b>图片维度扩至 4 套（决策 28, v4.9）</b>：每语种 Tab 下图片拆为 H5×白 / H5×黑 / Web×白 / Web×黑 共 4 套，跟语种走独立上传。 <span class="ann-tag p0">P0</span></div></div>
    <div class="ann-item"><div class="ann-num amber">6</div><div class="ann-text"><b>多语言兜底（决策 24, v4.9）</b>：活动中心模块简中 + 英文必配；其他语种未配置则走简中/英文兜底（默认英文优先，可调）。范围限定仅活动中心，其他模块维持「无兜底」。 <span class="ann-tag p0">P0</span></div></div>''',
    '5. M-2 标注区补全（3 重定义 + 3b/3c/3d/3e + 4 删除 + 5 图片 + 6 兜底）',
)

# ═══ 6. 场景总览标题 8 → 9 ═══
patch(
    '<div class="st"><h2>场景总览 · 8 个 MGT 后台场景</h2></div>',
    '<div class="st"><h2>场景总览 · 9 个 MGT 后台场景</h2></div>',
    '6. 场景总览 8 → 9',
)

# ═══ 7. 场景总览补 M-9 活动日历行 ═══
patch(
    '''      <tr style="background:#fafbfc;"><td style="padding:10px 16px;font-weight:700;color:#2D81FF;">M-8</td><td style="padding:10px 16px;">语种配置规则</td><td style="padding:10px 16px;">多语言</td><td style="padding:10px 16px;"><span style="background:#dcfce7;color:#15803d;padding:1px 6px;border-radius:3px;font-size:10px;font-weight:800;">P0</span></td><td style="padding:10px 16px;">Scene M-E</td></tr>
    </tbody>''',
    '''      <tr style="background:#fafbfc;"><td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;font-weight:700;color:#2D81FF;">M-8</td><td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;">语种配置规则（活动中心简中+英文必配）</td><td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;">多语言</td><td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;"><span style="background:#dcfce7;color:#15803d;padding:1px 6px;border-radius:3px;font-size:10px;font-weight:800;">P0</span></td><td style="padding:10px 16px;border-bottom:1px solid #f1f5f9;">Scene M-E</td></tr>
      <tr><td style="padding:10px 16px;font-weight:700;color:#2D81FF;">M-9 <span style="font-size:9px;background:#dcfce7;color:#15803d;padding:1px 4px;border-radius:2px;">v4.9 迁入</span></td><td style="padding:10px 16px;">活动日历（从福利中心迁出 → 运营工具一级）</td><td style="padding:10px 16px;">运营工具</td><td style="padding:10px 16px;"><span style="background:#dcfce7;color:#15803d;padding:1px 6px;border-radius:3px;font-size:10px;font-weight:800;">P0</span></td><td style="padding:10px 16px;">Scene M-F 详见 context 4.9</td></tr>
    </tbody>''',
    '7. 场景总览补 M-9 活动日历行',
)

# ═══ Write ═══
with open(DST, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\n✓ Generated: {DST}')
