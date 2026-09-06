#!/usr/bin/env python3
"""PART 1 · 核心承载 - Scene C · TAB 状态全集"""


def _phone_c1():
    """C-1 · 内容 TAB（文章/动态二级 TAB）"""
    return '''
    <div class="flow-col">
      <span class="phone-label">C-1 · 内容 TAB</span>
      <div class="phone" style="min-height:600px;display:flex;flex-direction:column;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top"><span style="font-size:14px;color:#828282;">‹</span><div style="flex:1;"></div><span style="font-size:14px;color:#828282;">↗</span></div>
        <div style="padding:10px 14px;flex:1;display:flex;flex-direction:column;gap:8px;">
          <div style="display:flex;gap:14px;border-bottom:1px solid #262626;padding:6px 0;">
            <span style="font-size:12px;color:#FFFFFF;font-weight:700;border-bottom:2px solid #007FFF;padding-bottom:4px;">内容</span>
            <span style="font-size:12px;color:#828282;">交易战绩</span>
            <span style="font-size:12px;color:#828282;">带单战绩</span>
          </div>
          <div style="position:relative;display:flex;gap:18px;padding:6px 0;">
            <div class="anno amber" style="top:-2px;left:-4px;right:-4px;bottom:-2px;"><div class="anno-n amber">1</div></div>
            <span style="font-size:12px;color:#FFFFFF;font-weight:700;border-bottom:1px solid #F0B90B;padding-bottom:2px;">文章</span>
            <span style="font-size:12px;color:#828282;">动态</span>
          </div>
          <div style="background:#262626;border-radius:6px;padding:10px;">
            <div style="font-size:11px;color:#FFFFFF;font-weight:700;margin-bottom:4px;">BTC 突破 71000 后续怎么看</div>
            <div style="font-size:9px;color:#828282;">📅 3 小时前 · 124 阅读 · 12 评</div>
          </div>
          <div style="background:#262626;border-radius:6px;padding:10px;">
            <div style="font-size:11px;color:#FFFFFF;font-weight:700;margin-bottom:4px;">现货长线策略复盘</div>
            <div style="font-size:9px;color:#828282;">📅 昨天 · 386 阅读 · 28 评</div>
          </div>
          <div style="background:#262626;border-radius:6px;padding:10px;opacity:.6;">
            <div style="font-size:11px;color:#FFFFFF;font-weight:700;margin-bottom:4px;">动态 TAB（点击切换）</div>
            <div style="font-size:9px;color:#828282;">展示该用户转发 / 点赞 / 评论记录</div>
          </div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">[内容] 一级 → [文章/动态] 二级</div>
    </div>'''


def _phone_c2():
    """C-2 · 交易战绩 TAB（自己未公开）"""
    return '''
    <div class="flow-col">
      <span class="phone-label">C-2 · 交易战绩 TAB（自己未公开）</span>
      <div class="phone" style="min-height:600px;display:flex;flex-direction:column;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top"><span style="font-size:14px;color:#828282;">‹</span><div style="flex:1;"></div><span style="font-size:14px;color:#828282;">↗</span></div>
        <div style="padding:10px 14px;flex:1;display:flex;flex-direction:column;gap:8px;">
          <div style="display:flex;gap:14px;border-bottom:1px solid #262626;padding:6px 0;">
            <span style="font-size:12px;color:#828282;">内容</span>
            <span style="font-size:12px;color:#FFFFFF;font-weight:700;border-bottom:2px solid #007FFF;padding-bottom:4px;">🔒 交易战绩</span>
            <span style="font-size:12px;color:#828282;">带单战绩</span>
          </div>
          <div style="position:relative;background:rgba(246,70,93,0.08);border:1px solid rgba(246,70,93,0.3);border-radius:6px;padding:10px;">
            <div class="anno red" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n red">2</div></div>
            <div style="display:flex;align-items:center;justify-content:space-between;">
              <div style="font-size:11px;color:#FFFFFF;line-height:1.5;">ⓘ 您的交易战绩仅自己可见。<br><span style="color:#007FFF;font-weight:700;text-decoration:underline;">设置为公开模式</span></div>
              <span style="color:#828282;font-size:14px;">✕</span>
            </div>
          </div>
          <div style="background:#262626;border-radius:6px;padding:14px;text-align:center;color:#828282;font-size:11px;line-height:1.8;opacity:.8;">
            （嵌入牛人榜战绩组件）<br>
            累计收益率 173.12% · 总盈亏 +1.2万<br>胜率 100% · 最大回撤 6.59%
          </div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">超链接 → 弹「战绩管理」弹窗（设置公开/私密 → 见 E ↗）</div>
    </div>'''


def _phone_c3():
    """C-3 · 交易战绩 TAB（已公开 / 别人看公开）— 完整 page-level header 双按钮共存

    顶部 [关注]（社交动作，page-level 常驻）+ 底部 sticky [订阅 · N 位订阅用户]（金融动作，仅战绩 TAB 出现）
    对齐 Binance 牛人详情页 IA：两个动作 risk level / 心智 / 触发场景全分离
    """
    return '''
    <div class="flow-col">
      <span class="phone-label">C-3 · 交易战绩 TAB（已公开 / 别人看公开）</span>
      <div class="phone" style="height:760px;display:flex;flex-direction:column;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top"><span style="font-size:14px;color:#828282;">‹</span><div style="flex:1;"></div><span style="font-size:14px;color:#828282;">⋯</span><span style="font-size:14px;color:#828282;margin-left:10px;">↗</span></div>
        <!-- ─── page-level header（社交主体 · 跨 TAB 常驻） ─── -->
        <div style="position:relative;padding:14px 16px 10px;border-bottom:1px solid #262626;">
          <div class="anno blue" style="top:6px;left:8px;right:8px;bottom:6px;"><div class="anno-n blue">3</div></div>
          <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:10px;">
            <div style="width:48px;height:48px;border-radius:24px;background:linear-gradient(135deg,#F7931A,#F0B90B);flex-shrink:0;"></div>
            <div style="flex:1;min-width:0;">
              <div style="display:flex;align-items:center;gap:6px;"><span style="color:#FFFFFF;font-size:15px;font-weight:900;">龙宫参谋长</span><span style="color:#F0B90B;font-size:10px;">🟡</span></div>
              <div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:5px;">
                <span style="background:rgba(0,127,255,.12);color:#007FFF;font-size:9px;font-weight:600;padding:2px 6px;border-radius:8px;">BTC 持有者</span>
                <span style="background:#262626;color:#828282;font-size:9px;font-weight:600;padding:2px 6px;border-radius:8px;">中频交易者</span>
              </div>
            </div>
            <button style="background:#007FFF;color:#fff;border:none;border-radius:14px;padding:7px 18px;font-size:12px;font-weight:700;flex-shrink:0;">关注</button>
          </div>
          <div style="display:flex;gap:14px;color:#828282;font-size:11px;">
            <span>关注 <b style="color:#FFFFFF;">126</b></span>
            <span>粉丝 <b style="color:#FFFFFF;">3.2万</b></span>
            <span>点赞 <b style="color:#FFFFFF;">882</b></span>
          </div>
        </div>
        <!-- ─── TAB 切换 ─── -->
        <div style="display:flex;gap:14px;border-bottom:1px solid #262626;padding:6px 16px;">
          <a href="#scene-b" style="font-size:13px;color:#828282;text-decoration:none;">内容</a>
          <span style="font-size:13px;color:#FFFFFF;font-weight:700;border-bottom:2px solid #007FFF;padding-bottom:6px;">交易战绩</span>
          <span style="font-size:13px;color:#828282;">带单战绩</span>
        </div>
        <!-- ─── 战绩数据卡（嵌入牛人榜组件） ─── -->
        <div style="padding:12px 16px;flex:1;display:flex;flex-direction:column;gap:10px;overflow:hidden;">
          <div style="position:relative;background:linear-gradient(135deg,rgba(6,153,92,0.10),transparent);border:1px solid rgba(6,153,92,0.25);border-radius:10px;padding:14px;">
            <div class="anno purple" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n purple">4</div></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:10px;">
              <div>
                <div style="color:#828282;font-size:10px;margin-bottom:2px;">累计收益率（30d）</div>
                <div style="color:#06995C;font-size:22px;font-weight:900;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;line-height:1;">+173.12%</div>
              </div>
              <div>
                <div style="color:#828282;font-size:10px;margin-bottom:2px;">总盈亏（USDT）</div>
                <div style="color:#06995C;font-size:22px;font-weight:900;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;line-height:1;">+12,480</div>
              </div>
            </div>
            <div style="height:48px;margin-bottom:10px;"><svg width="100%" height="48" viewBox="0 0 200 48" preserveAspectRatio="none"><defs><linearGradient id="gc3" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#06995C" stop-opacity=".3"/><stop offset="1" stop-color="#06995C" stop-opacity="0"/></linearGradient></defs><path d="M0 42 L24 36 L52 28 L80 32 L108 18 L136 12 L164 8 L200 2 L200 48 L0 48 Z" fill="url(#gc3)"/><polyline points="0,42 24,36 52,28 80,32 108,18 136,12 164,8 200,2" stroke="#06995C" stroke-width="1.5" fill="none"/></svg></div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
              <div><div style="color:#828282;font-size:10px;">胜率</div><div style="color:#FFFFFF;font-size:13px;font-weight:600;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;">100%</div></div>
              <div><div style="color:#828282;font-size:10px;">最大回撤</div><div style="color:#FFFFFF;font-size:13px;font-weight:600;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;">6.59%</div></div>
              <div><div style="color:#828282;font-size:10px;">资产</div><div style="color:#FFFFFF;font-size:13px;font-weight:600;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;">8.2万</div></div>
            </div>
          </div>
          <div style="font-size:10px;color:#828282;text-align:center;padding:2px;">嵌入牛人榜战绩组件（H5 / 组件化待研发对齐）</div>
        </div>
        <!-- ─── 底部 sticky 订阅 CTA（金融动作 · 战绩 TAB 专属） ─── -->
        <div style="position:relative;background:#161616;border-top:1px solid #262626;padding:10px 14px;flex-shrink:0;">
          <div class="anno red" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n red">5</div></div>
          <a href="#scene-d" style="display:block;background:#007FFF;color:#fff;border:none;width:100%;padding:10px;border-radius:8px;text-align:center;text-decoration:none;">
            <div style="font-size:14px;font-weight:700;line-height:1.2;">订阅</div>
            <div style="font-size:10px;font-weight:400;opacity:.85;margin-top:1px;">45,927 位订阅用户</div>
          </a>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">双按钮共存 · 顶 [关注]（社交·page-level 常驻）+ 底 sticky [订阅·N 位订阅用户]（金融·战绩 TAB 专属）</div>
    </div>'''


def _phone_c4():
    """C-4 · 带单战绩 TAB（仅有资格才显示）"""
    return '''
    <div class="flow-col">
      <span class="phone-label">C-4 · 带单战绩 TAB（有资格才显示）</span>
      <div class="phone" style="min-height:600px;display:flex;flex-direction:column;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top"><span style="font-size:14px;color:#828282;">‹</span><div style="flex:1;"></div><span style="font-size:14px;color:#828282;">↗</span></div>
        <div style="padding:10px 14px;flex:1;display:flex;flex-direction:column;gap:8px;">
          <div style="display:flex;gap:14px;border-bottom:1px solid #262626;padding:6px 0;">
            <span style="font-size:12px;color:#828282;">内容</span>
            <span style="font-size:12px;color:#828282;">交易战绩</span>
            <span style="font-size:12px;color:#FFFFFF;font-weight:700;border-bottom:2px solid #007FFF;padding-bottom:4px;">带单战绩</span>
          </div>
          <div style="position:relative;background:#262626;border-radius:8px;padding:12px;">
            <div class="anno green" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n green">6</div></div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
              <span style="background:#F0B90B;color:#fff;padding:2px 6px;border-radius:3px;font-size:9px;font-weight:700;">合约带单</span>
              <span style="background:#828282;color:#161616;padding:2px 6px;border-radius:3px;font-size:9px;font-weight:700;">Lv.5</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:6px 0;font-size:11px;border-bottom:1px solid rgba(255,255,255,.05);"><span style="color:#828282;">跟单人数</span><span style="color:#FFFFFF;font-weight:700;">6 / 200</span></div>
            <div style="display:flex;justify-content:space-between;padding:6px 0;font-size:11px;border-bottom:1px solid rgba(255,255,255,.05);"><span style="color:#828282;">总收益率</span><span style="color:#06995C;font-weight:700;">173.12%</span></div>
            <div style="display:flex;justify-content:space-between;padding:6px 0;font-size:11px;"><span style="color:#828282;">起跟金额</span><span style="color:#FFFFFF;">10 USDT</span></div>
          </div>
        </div>
        <!-- ─── 底部 sticky 订阅 CTA（与交易战绩 TAB 公开态 同结构） ─── -->
        <div style="position:relative;background:#161616;border-top:1px solid #262626;padding:10px 14px;flex-shrink:0;">
          <div class="anno red" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n red">5</div></div>
          <a href="#scene-d" style="display:block;background:#007FFF;color:#fff;border:none;width:100%;padding:10px;border-radius:8px;text-align:center;text-decoration:none;">
            <div style="font-size:14px;font-weight:700;line-height:1.2;">订阅</div>
            <div style="font-size:10px;font-weight:400;opacity:.85;margin-top:1px;">45,927 位订阅用户</div>
          </a>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">带单 TAB sticky 与战绩 TAB 同结构 · 订阅人数与战绩 TAB 共用同一计数（不分战绩 / 带单维度）· 无资格则整 TAB 隐藏</div>
    </div>'''


def fill_c():
    """Scene C — 4 个 TAB 状态横排"""
    arrow_b2 = '<div class="aw"><div class="al r"></div><div class="tx r">未公开 → 公开</div></div>'
    arrow_b3 = '<div class="aw"><div class="al p"></div><div class="tx p">切到带单</div></div>'
    arrow_b1 = '<div class="aw"><div class="al b"></div><div class="tx b">切到战绩</div></div>'
    ann_card = '''
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card" style="align-self:flex-start;margin-top:36px;">
        <div class="card-title">📋 C · TAB 状态全集 <span class="ann-tag p0">P0</span></div>
        <div class="ann-item"><div class="ann-num amber">1</div><div class="ann-text"><b>内容 TAB 二级</b><br>[文章] = 发帖记录 · [动态] = 转发/点赞/评论记录</div></div>
        <div class="ann-item"><div class="ann-num red">2</div><div class="ann-text"><b>未公开提示条</b><br>仅自己视角显示。超链接「设置为公开模式」→ 弹「战绩管理」快捷视图（与编辑资料页内 section 共用同一份数据，见 E ↗）</div></div>
        <div class="ann-item"><div class="ann-num blue">3</div><div class="ann-text"><b>page-level header</b><br>头像 / 用户名 / 资质标签（BTC 持有者 / 中频交易者）/ 关注粉丝点赞统计 + <b>右上 [关注] 按钮</b>。关注是社交动作，page-level 常驻，跨 TAB 都能看到</div></div>
        <div class="ann-item"><div class="ann-num purple">4</div><div class="ann-text"><b>战绩数据卡</b><br>累计收益率 / 总盈亏 / 胜率 / 最大回撤 / 资产 嵌入牛人榜组件。社区只画外壳，组件实现走 H5 嵌入或组件化（待研发对齐）</div></div>
        <div class="ann-item"><div class="ann-num red">5</div><div class="ann-text"><b>底部 sticky [订阅] 按钮</b><br>带副标题「45,927 位订阅用户」，金融动作 · 战绩 TAB 专属（看完战绩数据再决策）。UI 归社区，行为调牛人榜接口。<b>顶 [关注] + 底 sticky [订阅] 双按钮共存，对齐 Binance 牛人详情页 IA</b></div></div>
        <div class="ann-item"><div class="ann-num green">6</div><div class="ann-text"><b>带单战绩 TAB</b><br>合约 / 现货带单资格才显示；<b>底部 sticky 订阅按钮与战绩 TAB 完全同款</b>（蓝色全宽 + 主标题「订阅」+ 副标题「N 位订阅用户」），N 跟战绩 TAB 共用同一订阅人数（不分战绩 / 带单维度）。详见 <a href="#scene-d">订阅链路 ↗</a></div></div>
        <div class="info-box blue"><b>关注 vs 订阅独立：</b>两个 risk level 不同的动作 —— 关注 = 零成本社交动作（看动态/观点），订阅 = 金融决策动作（参考甚至跟单）。强行合并破坏漏斗指标（关注转订阅率算不出）+ 触发合规（signal subscription = 投资建议）+ 取消路径不对称</div>
        <div class="info-box amber"><b>埋点：</b>TAB 切换 + 订阅点击，代号见 PRD §埋点</div>
      </div>
    </div>'''
    return _phone_c1() + arrow_b1 + _phone_c2() + arrow_b2 + _phone_c3() + arrow_b3 + _phone_c4() + ann_card
