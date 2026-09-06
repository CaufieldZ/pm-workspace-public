#!/usr/bin/env python3
"""PART 0 · 入口与触达 — Scene A · Feed 流牛人榜推荐

V2 翻新（2026-04-28）：套 biz-social V2 #9 Feed 结构 · 夜间主题
色板：#161616/#262626 + #007FFF + #06995C/#D9415B
字体：HarmonyOS Sans SC + JetBrains Mono
"""


def fill_a():
    """Scene A — A-1 Feed 主体（V2 夜间） + A-2 跳转后态 + 注释卡"""
    return _a1_feed() + _a_arrow() + _a2_jump() + _a_anncard()


def _a1_feed():
    """A-1 · Feed 流主体 — 直接复用 biz-social V2 #9 完整 Feed 结构，
    在第二张完整卡之前插入「热门交易员」推荐位（牛人榜横滑卡）。
    保留 V2 完整卡（含 BTCUSDT永续持仓卡 + BTC/ETH/Platform C 涨跌条）+ 直播预告卡 + FAB + 底 Tab Bar。
    """
    return '''
    <!-- ─── A-1 · Feed 流主体（biz-social V2 #9 夜间完整版 · 嵌入热门交易员） ─── -->
    <div class="flow-col">
      <span class="phone-label">A-1 · Feed 流牛人榜推荐卡片</span>
      <div class="phone" style="height:840px;background:#161616;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;display:flex;flex-direction:column;position:relative;">
        <div class="ph-status" style="color:#FFFFFF;"><span>9:41</span><span>5G ▁▂▃▅ 🔋</span></div>
        <div style="display:flex;align-items:center;gap:8px;padding:8px 16px;">
          <div style="flex:1;height:32px;border-radius:16px;background:#262626;padding:0 12px;display:flex;align-items:center;gap:6px;color:#828282;font-size:13px;">🔍 搜索</div>
          <span style="font-size:18px;color:#FFFFFF;position:relative;">🔔<span style="position:absolute;top:-2px;right:-2px;width:6px;height:6px;border-radius:3px;background:#D9415B;"></span></span>
        </div>
        <div style="display:flex;padding:0 16px;border-bottom:1px solid #333333;">
          <div style="padding:8px 12px;color:#FFFFFF;font-size:15px;font-weight:700;">发现</div>
          <div style="padding:8px 12px;color:#828282;font-size:15px;">关注</div>
          <div style="padding:8px 12px;color:#828282;font-size:15px;">快讯</div>
          <div style="padding:8px 12px;color:#828282;font-size:15px;">直播</div>
          <div style="padding:8px 12px;color:#828282;font-size:15px;">公告</div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;padding:10px 16px;border-bottom:1px solid #333333;"><span style="font-size:14px;">🔥</span><span style="flex:1;color:#FFFFFF;font-size:13px;">#CPI数据利好！降息进一步逼近?</span><span style="color:#828282;font-size:11px;">›</span></div>
        ''' + _a1_post_card() + _a1_top_traders() + '''
        <div class="fab" style="position:absolute;bottom:80px;right:16px;width:48px;height:48px;border-radius:24px;background:#007FFF;color:#fff;display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;box-shadow:0 4px 12px rgba(0,127,255,.3);">+</div>
        <div style="position:absolute;bottom:0;left:0;right:0;height:50px;background:#161616;border-top:1px solid #333333;display:flex;">
          <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#FFFFFF;font-size:10px;font-weight:700;"><span style="font-size:14px;">🏠</span>发现</div>
          <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#828282;font-size:10px;font-weight:400;"><span style="font-size:14px;">📈</span>行情</div>
          <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#828282;font-size:10px;font-weight:400;"><span style="font-size:14px;">🔄</span>交易</div>
          <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#828282;font-size:10px;font-weight:400;"><span style="font-size:14px;">🎯</span>跟单</div>
          <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#828282;font-size:10px;font-weight:400;"><span style="font-size:14px;">👤</span>我的</div>
        </div>
      </div>
      <div class="flow-note">浏览 ≥ 5 条 feed 后插入首张 · 横滑 2.x 张暗示可滑（套 biz-social V2 #9 完整结构）</div>
    </div>
    '''


def _a1_post_card():
    """biz-social V2 #9 完整帖子卡 1（币圈彦祖ME + BTCUSDT永续持仓卡 + 涨跌行）"""
    return '''
        <div style="padding:14px 16px;border-bottom:8px solid #262626;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <div style="width:36px;height:36px;border-radius:18px;background:linear-gradient(135deg,#F7931A,#F0B90B);display:flex;align-items:center;justify-content:center;font-size:14px;color:#fff;font-weight:700;">币</div>
            <div style="flex:1;"><div style="color:#FFFFFF;font-size:14px;font-weight:600;">币圈彦祖ME</div><div style="color:#828282;font-size:11px;">02-04 12:12</div></div>
          </div>
          <div style="color:#FFFFFF;font-size:14px;line-height:1.5;margin-bottom:10px;"><span style="background:#007FFF;color:#fff;padding:1px 6px;border-radius:10px;font-size:11px;font-weight:600;">$BTC</span> 早间点位分享，币圈彦祖ME 直播热力测评中早盘…</div>
          <div style="background:#262626;border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="display:flex;align-items:center;gap:6px;"><span style="font-size:14px;">₿</span><span style="color:#FFFFFF;font-size:14px;font-weight:700;">BTCUSDT永续</span><span style="background:rgba(6,153,92,.2);color:#06995C;font-size:10px;font-weight:600;padding:1px 5px;border-radius:3px;">正在做多</span><span style="margin-left:auto;color:#06995C;font-size:13px;font-weight:600;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;">+1,234.55 USDT</span></div>
          </div>
          <div style="display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap;">
            <span style="background:#262626;border-radius:14px;padding:5px 10px;display:inline-flex;align-items:center;gap:4px;font-size:12px;"><span style="color:#FFFFFF;">BTC</span><span style="color:#06995C;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;">+21.03%</span></span>
            <span style="background:#262626;border-radius:14px;padding:5px 10px;display:inline-flex;align-items:center;gap:4px;font-size:12px;"><span style="color:#FFFFFF;">ETH</span><span style="color:#06995C;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;">+11.56%</span></span>
            <span style="background:#262626;border-radius:14px;padding:5px 10px;display:inline-flex;align-items:center;gap:4px;font-size:12px;"><span style="color:#FFFFFF;">Platform C</span><span style="color:#D9415B;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;">-0.03%</span></span>
          </div>
          <div style="display:flex;justify-content:space-between;color:#828282;font-size:12px;"><span>❤️ 5</span><span>💬 12</span><span>🔄 3</span><span>📊 96</span></div>
        </div>
    '''


def _a1_top_traders():
    """牛人榜「热门交易员」横滑推荐位（核心 KPI 漏斗第一站）—— 对齐 OKX 视觉：
    标题 + › 极简头 / 大卡片 / Hero 30天收益额 / 大曲线占主舞台 / 资产量底部行
    """
    return '''
        <div style="padding:18px 16px 16px;border-bottom:8px solid #262626;position:relative;">
          <div class="anno blue" style="top:6px;left:6px;right:6px;bottom:6px;border-style:solid;border-width:1px;opacity:.45;"><div class="anno-n blue" style="width:18px;height:18px;font-size:10px;top:-9px;left:8px;right:auto;">1</div></div>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;padding:0 2px;">
            <span style="color:#FFFFFF;font-size:17px;font-weight:700;letter-spacing:.5px;">热门交易员</span>
            <span style="color:#828282;font-size:18px;font-weight:300;">›</span>
          </div>
          <div style="display:flex;gap:10px;overflow:hidden;">
            ''' + _trader_card(
                avatar='linear-gradient(135deg,#F7931A,#F0B90B)',
                username='tal***@proton.me',
                curve='M0 92 Q14 85 28 78 T56 70 Q72 50 88 56 T120 38 Q138 26 156 32 T184 14 Q198 18 210 8',
                profit_amount='+$8,760,267.23',
                profit_pct='+51.29%',
                asset='$19,165,658.88',
            ) + _trader_card(
                avatar='linear-gradient(135deg,#06b6d4,#0891b2)',
                username='查理斯，你给我...',
                curve='M0 86 Q16 84 32 88 T64 78 Q82 60 100 66 T136 42 Q156 30 172 36 T200 18 Q208 14 210 10',
                profit_amount='+$2,460,393.06',
                profit_pct='+18.00%',
                asset='$16,130,176.31',
            ) + '''
          </div>
        </div>
    '''


def _trader_card(avatar, username, curve, profit_amount, profit_pct, asset):
    """单张牛人推荐卡 · 对齐 OKX 视觉"""
    return f'''
            <div style="flex:0 0 196px;background:#1F1F1F;border-radius:14px;padding:12px;display:flex;flex-direction:column;gap:8px;">
              <div style="display:flex;align-items:center;gap:8px;">
                <div style="width:32px;height:32px;border-radius:16px;background:{avatar};flex-shrink:0;"></div>
                <span style="color:#FFFFFF;font-size:13px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{username}</span>
              </div>
              <div style="height:80px;margin:2px -2px;">
                <svg width="100%" height="96" viewBox="0 0 210 96" preserveAspectRatio="none">
                  <path d="{curve}" stroke="#06995C" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <div style="display:flex;flex-direction:column;gap:2px;">
                <span style="color:#828282;font-size:11px;">30 天收益额</span>
                <span style="color:#06995C;font-size:18px;font-weight:700;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;line-height:1.1;letter-spacing:-.3px;">{profit_amount}</span>
                <span style="color:#06995C;font-size:13px;font-weight:600;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;line-height:1.2;">{profit_pct}</span>
              </div>
              <div style="display:flex;justify-content:space-between;align-items:center;padding-top:8px;border-top:1px solid #2A2A2A;">
                <span style="color:#828282;font-size:11px;">资产量</span>
                <span style="color:#FFFFFF;font-size:12px;font-weight:500;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;">{asset}</span>
              </div>
            </div>
    '''


def _a1_live_card():
    """biz-social V2 #9 完整帖子卡 2（CryptoLive + ETH Cancun 直播预告卡）"""
    return '''
        <div style="padding:14px 16px;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <div style="width:36px;height:36px;border-radius:18px;background:linear-gradient(135deg,#667eea,#764ba2);"></div>
            <div style="flex:1;"><div style="color:#FFFFFF;font-size:14px;font-weight:600;">CryptoLive</div><div style="color:#828282;font-size:11px;">15 分钟前</div></div>
          </div>
          <div style="color:#FFFFFF;font-size:13px;line-height:1.5;margin-bottom:8px;">本场直播聚焦 ETH Cancun 升级…</div>
          <div style="background:linear-gradient(135deg,#7C3AED,#A855F7);border-radius:14px;padding:14px;color:#fff;">
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;"><span style="background:rgba(255,255,255,.2);font-size:10px;font-weight:700;padding:2px 6px;border-radius:3px;">示例 Live</span><span style="font-size:11px;opacity:.85;">02-04 20:00</span></div>
            <div style="font-size:14px;font-weight:700;line-height:1.4;margin-bottom:10px;">Exploring the ETH Cancun Upgrade</div>
            <div style="display:flex;gap:6px;">
              <div style="flex:1;background:rgba(0,0,0,.25);border-radius:8px;padding:8px;"><div style="font-size:9px;opacity:.7;">HOST</div><div style="font-size:11px;font-weight:600;">Darko</div></div>
              <div style="flex:1;background:rgba(0,0,0,.25);border-radius:8px;padding:8px;"><div style="font-size:9px;opacity:.7;">GUEST</div><div style="font-size:11px;font-weight:600;">Ruth</div></div>
              <div style="flex:1;background:rgba(0,0,0,.25);border-radius:8px;padding:8px;"><div style="font-size:9px;opacity:.7;">HOST</div><div style="font-size:11px;font-weight:600;">Mike</div></div>
            </div>
          </div>
        </div>
    '''


def _a_arrow():
    return '''
    <!-- ─── 箭头 ─── -->
    <div class="aw"><div class="al a"></div><div class="tx a">点击牛人卡片</div></div>
    '''


def _a2_jump():
    """A-2 · 跳转后态：落到他人主页（V2 夜间简化）"""
    return '''
    <div class="flow-col">
      <span class="phone-label">A-2 · 进交易员个人主页</span>
      <div class="phone" style="height:680px;background:#161616;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;display:flex;flex-direction:column;opacity:0.95;">
        <div class="ph-status" style="color:#FFFFFF;"><span>9:41</span><span>🔋</span></div>
        <div style="display:flex;align-items:center;padding:8px 16px;border-bottom:1px solid #333333;"><span style="color:#FFFFFF;font-size:18px;">←</span><div style="flex:1;"></div><span style="color:#FFFFFF;font-size:18px;">⋯</span><span style="color:#FFFFFF;font-size:18px;margin-left:14px;">↗</span></div>
        <div style="padding:14px 16px;display:flex;align-items:flex-start;gap:12px;">
          <div style="width:54px;height:54px;border-radius:27px;background:linear-gradient(135deg,#F7931A,#F0B90B);"></div>
          <div style="flex:1;">
            <div style="display:flex;align-items:center;gap:6px;"><span style="color:#FFFFFF;font-size:15px;font-weight:900;">龙宫参谋长</span><span style="color:#F0B90B;font-size:10px;">🟡</span></div>
            <div style="display:flex;gap:14px;margin-top:6px;color:#828282;font-size:11px;"><span>关注 <b style="color:#FFFFFF;">126</b></span><span>粉丝 <b style="color:#FFFFFF;">3.2万</b></span></div>
            <div style="color:#828282;font-size:10px;margin-top:4px;line-height:1.5;">合约长线策略 · 全网同名 龙宫参</div>
          </div>
          <button style="background:#007FFF;color:#fff;border:none;border-radius:14px;padding:6px 14px;font-size:11px;font-weight:700;">关注</button>
        </div>
        <div style="display:flex;gap:14px;border-bottom:1px solid #333333;padding:6px 16px;">
          <a href="#scene-b" style="color:#828282;font-size:12px;text-decoration:none;">内容</a>
          <a href="#scene-c" style="color:#FFFFFF;font-size:12px;font-weight:700;border-bottom:2px solid #007FFF;padding-bottom:4px;text-decoration:none;">交易战绩</a>
          <a href="#scene-c" style="color:#828282;font-size:12px;text-decoration:none;">带单战绩</a>
        </div>
        <div style="padding:10px 16px;display:flex;flex-direction:column;gap:8px;">
          <div style="background:linear-gradient(135deg,rgba(6,153,92,0.10),transparent);border:1px solid rgba(6,153,92,0.25);border-radius:8px;padding:10px;">
            <div style="color:#828282;font-size:9px;margin-bottom:2px;">累计收益率（30d）</div>
            <div style="color:#06995C;font-size:22px;font-weight:900;font-family:'JetBrains Mono','SF Mono',ui-monospace,monospace;line-height:1;">+173.12%</div>
            <div style="height:24px;margin:6px 0;"><svg width="100%" height="24" viewBox="0 0 100 24" preserveAspectRatio="none"><polyline points="0,20 12,18 28,14 45,16 60,10 75,5 90,3 100,1" stroke="#06995C" stroke-width="1.5" fill="none"/></svg></div>
            <div style="display:flex;justify-content:space-between;color:#828282;font-size:9px;"><span>胜率 <b style="color:#FFFFFF;">100%</b></span><span>回撤 <b style="color:#FFFFFF;">6.59%</b></span></div>
          </div>
          <a href="#scene-c" style="color:#007FFF;font-size:10px;text-align:center;padding:4px;text-decoration:none;font-weight:700;">查看完整战绩 → C ↗</a>
        </div>
      </div>
      <div class="flow-note">推荐卡来源 → 默认落「交易战绩」TAB · 入口决定落点</div>
    </div>
    '''


def _a_anncard():
    return '''
    <!-- ─── 注释卡 ─── -->
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card" style="align-self:flex-start;margin-top:36px;">
        <div class="card-title">📋 A · Feed 流交易员推荐 <span class="ann-tag p0">P0</span></div>
        <div class="ann-item">
          <div class="ann-num blue">1</div>
          <div class="ann-text"><b>卡片字段（合约带单 / 牛人榜共用一套）</b><br>头像 / 昵称 / 30d 收益曲线 / 30d 收益额 / 收益率 / 胜率 / 资产量 · <b>缺失字段前端隐藏</b> · 卡片组件由设计输出统一规格，适配两种数据口径 · 第一期砍"动态摘要"，避免冷启动期描述失真</div>
        </div>
        <div class="ann-item">
          <div class="ann-num green">2</div>
          <div class="ann-text"><b>数据源（前端可配）</b><br>第一期默认 <b>合约带单交易员池</b>（数据完整度更高）· 未来可切牛人榜池 / 现货带单池 · 运营 CMS key 控制不发版 · 露出规则：浏览 ≥ 5 条插首张 / 每 10 条一张 / 单 session ≤ 3 张 / 同一交易员 24h 不重复 / 不让用户关闭</div>
        </div>
        <div class="ann-item">
          <div class="ann-num blue">3</div>
          <div class="ann-text"><b>推荐池规则</b><br>当前数据源 30d 收益率 Top 30 ∪ 30d 订阅增量 Top 30，排除已订阅 · <b>战绩公开前置</b>（未公开战绩的人不进池，避免落点空状态）· 池内随机 + 持仓币种匹配优先</div>
        </div>
        <div class="ann-item">
          <div class="ann-num red">4</div>
          <div class="ann-text"><b>点击落点策略</b><br>本场景（推荐卡来源）→ 默认落「交易战绩」TAB（不是内容 TAB）<br>本质：「Ta 希望被关注的是什么」决定落点 —— 推荐上榜的人希望被关注的是战绩<br>其他来源（IM / 搜索 / 分享链接 / 牛人榜列表）保持默认内容 TAB</div>
        </div>
        <div class="info-box amber"><b>埋点：</b>牛人推荐位曝光 + 卡片点击 + 横滑切换，代号见 PRD §埋点</div>
        <div class="info-box blue"><b>跨场景衔接：</b>点击卡片后落「他人视角 · 战绩 TAB」 · 漏斗第一站，决定后续订阅转化的曝光量</div>
      </div>
    </div>
    '''
