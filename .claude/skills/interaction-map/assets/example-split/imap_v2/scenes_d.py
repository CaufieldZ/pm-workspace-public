#!/usr/bin/env python3
"""PART 2 · 关键转化 - Scene D · 订阅闭环（含跨团队 D-3）"""


def _phone_d1():
    """D-1 · header 订阅数 → 牛人榜订阅页"""
    return '''
    <div class="flow-col">
      <span class="phone-label">D-1 · header 订阅数 → 牛人榜订阅页</span>
      <div class="phone" style="min-height:580px;display:flex;flex-direction:column;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top"><span style="font-size:14px;color:#828282;">‹</span><div style="flex:1;"></div></div>
        <div style="padding:14px 16px;flex:1;display:flex;flex-direction:column;gap:10px;">
          <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:46px;height:46px;border-radius:23px;background:linear-gradient(135deg,#667eea,#764ba2);"></div>
            <div><div style="font-size:14px;color:#FFFFFF;font-weight:900;">Felix.zhi</div></div>
          </div>
          <div style="position:relative;display:flex;gap:14px;font-size:11px;color:#828282;padding:6px 2px;background:#262626;border-radius:6px;padding:8px 10px;">
            <div class="anno green" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n green">1</div></div>
            <span>关注 <b style="color:#FFFFFF;">42</b></span>
            <span>粉丝 <b style="color:#FFFFFF;">1</b></span>
            <span style="background:rgba(14,203,129,0.15);padding:2px 6px;border-radius:3px;color:#06995C;font-weight:700;">订阅 3 →</span>
          </div>
          <div style="font-size:10px;color:#828282;text-align:center;padding:24px 0;">点击「订阅 3 →」<br>跳转牛人榜「我的订阅」页</div>
          <div style="background:rgba(43,127,255,0.10);border:1px dashed #007FFF;border-radius:6px;padding:14px;text-align:center;color:#007FFF;font-size:11px;font-weight:700;">→ 牛人榜「我的订阅」页（社区不维护订阅列表）</div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">订阅数仅自己视角可见 · 跳转走牛人榜既有页面</div>
    </div>'''


def _phone_d2():
    """D-2 · 订阅成功后态：sticky 按钮变 [已订阅 + 人维度铃铛 toggle]"""
    return '''
    <div class="flow-col">
      <span class="phone-label">D-2 · 订阅成功后状态（已订阅 + 人维度推送 toggle）</span>
      <div class="phone" style="min-height:580px;display:flex;flex-direction:column;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top"><span style="font-size:14px;color:#828282;">‹</span><div style="flex:1;"></div></div>
        <div style="padding:10px 14px;flex:1;display:flex;flex-direction:column;gap:8px;">
          <div style="display:flex;gap:14px;border-bottom:1px solid #262626;padding:6px 0;">
            <a href="#scene-c" style="font-size:12px;color:#828282;text-decoration:none;">内容</a>
            <a href="#scene-c" style="font-size:12px;color:#FFFFFF;font-weight:700;border-bottom:2px solid #007FFF;padding-bottom:4px;text-decoration:none;">交易战绩</a>
            <a href="#scene-c" style="font-size:12px;color:#828282;text-decoration:none;">带单战绩</a>
          </div>
          <div style="background:linear-gradient(135deg,rgba(14,203,129,0.10),transparent);border:1px solid rgba(14,203,129,0.25);border-radius:8px;padding:10px;">
            <div style="font-size:9px;color:#828282;">累计收益率（30d）</div>
            <div style="font-size:20px;color:#06995C;font-weight:900;font-family:'JetBrains Mono',monospace;">+173.12%</div>
            <div style="height:24px;margin:4px 0;"><svg width="100%" height="24" viewBox="0 0 100 24"><polyline points="0,20 12,18 28,14 45,16 60,10 75,5 90,3 100,1" stroke="#0ECB81" stroke-width="1.5" fill="none"/></svg></div>
            <div style="display:flex;justify-content:space-between;font-size:9px;color:#828282;"><span>胜率 100%</span><span>回撤 6.59%</span></div>
            <a href="#scene-c" style="display:block;font-size:9px;color:#007FFF;text-align:center;padding:4px 0 0;text-decoration:none;font-weight:700;">查看完整战绩 → C-3 ↗</a>
          </div>
        </div>
        <div style="background:#161616;border-top:1px solid #262626;padding:10px 14px;flex-shrink:0;position:relative;">
          <div class="anno green" style="top:-2px;left:-4px;right:-4px;bottom:-2px;"><div class="anno-n green">2</div></div>
          <div style="display:flex;align-items:stretch;gap:8px;">
            <div style="background:#262626;border-radius:8px;padding:6px 10px;display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:48px;">
              <span style="font-size:16px;line-height:1;">🔔</span>
              <span style="font-size:9px;color:#FFFFFF;font-weight:600;margin-top:2px;">开启</span>
            </div>
            <div style="flex:1;background:#262626;border-radius:8px;padding:8px;text-align:center;">
              <div style="font-size:14px;color:#FFFFFF;font-weight:700;line-height:1.1;">已订阅</div>
              <div style="font-size:10px;color:#828282;margin-top:1px;">45,929 位订阅用户</div>
            </div>
          </div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">订阅成功后 sticky 变 [铃铛 + 已订阅] · 铃铛 = 人维度推送 toggle，点击直接切换 + toast 反馈 · 进 <a href="#scene-b">他人主页 ↗</a> / <a href="#scene-c">战绩 TAB ↗</a> 时拉牛人榜接口刷状态，禁本地缓存（用户可能在跟单 / 牛人榜入口改过）</div>
    </div>'''


def _phone_d3():
    """D-3 · 牛人榜列表 → 跳社区主页（跨团队改造）"""
    return '''
    <div class="flow-col">
      <span class="phone-label">D-3 · 牛人榜列表 → 跳社区主页（牛人榜侧改造）</span>
      <div class="phone" style="min-height:580px;display:flex;flex-direction:column;border:2px dashed #F0B90B;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top"><span style="font-size:14px;color:#828282;">‹</span><div style="flex:1;text-align:center;"><div class="ph-name">牛人榜</div></div></div>
        <div style="padding:10px 14px;flex:1;display:flex;flex-direction:column;gap:8px;">
          <div style="display:flex;gap:8px;font-size:10px;color:#828282;padding:4px 0;"><span style="color:#FFFFFF;font-weight:700;border-bottom:1px solid #F0B90B;padding-bottom:2px;">总收益</span><span>胜率</span><span>跟单数</span></div>
          <div style="position:relative;background:#262626;border-radius:6px;padding:10px;display:flex;align-items:center;gap:10px;">
            <div class="anno amber" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n amber">3</div></div>
            <div style="font-size:11px;color:#FFFFFF;font-weight:900;width:14px;">1</div>
            <div style="width:32px;height:32px;border-radius:16px;background:linear-gradient(135deg,#f5af19,#f12711);"></div>
            <div style="flex:1;"><div style="font-size:12px;color:#FFFFFF;font-weight:700;">龙宫参谋长</div><div style="font-size:9px;color:#06995C;font-weight:700;">+173.12% / 100% 胜率</div></div>
            <span style="font-size:11px;color:#F0B90B;">›</span>
          </div>
          <div style="background:#262626;border-radius:6px;padding:10px;display:flex;align-items:center;gap:10px;opacity:.7;">
            <div style="font-size:11px;color:#FFFFFF;width:14px;">2</div>
            <div style="width:32px;height:32px;border-radius:16px;background:linear-gradient(135deg,#667eea,#764ba2);"></div>
            <div style="flex:1;"><div style="font-size:12px;color:#FFFFFF;font-weight:700;">SOL_Master</div></div>
          </div>
          <div style="background:rgba(217,119,6,0.10);border:1px dashed #F0B90B;border-radius:6px;padding:10px;text-align:center;color:#F0B90B;font-size:10px;font-weight:700;">点击行 → 跳社区他人主页<br>原详情页下线（牛人榜侧改造）</div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">View 2 · 牛人榜侧改造 · 社区只画箭头引出</div>
    </div>'''


def fill_d():
    """Scene D · 订阅链路（D-1 / D-2 / D-3）"""
    arrow_12 = '<div class="aw"><div class="al g"></div><div class="tx g">订阅另一入口</div></div>'
    arrow_23 = '<div class="aw"><div class="al a"></div><div class="tx a">反向入口</div></div>'
    ann_card = '''
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card" style="align-self:flex-start;margin-top:36px;">
        <div class="card-title">📋 D · 订阅闭环（含跨团队反向入口） <span class="ann-tag p0">P0</span></div>
        <div class="ann-item"><div class="ann-num green">1</div><div class="ann-text"><b>header 订阅数入口</b><br>仅自己视角可见 · 点击直接跳牛人榜「我的订阅」页 · 社区不维护订阅列表</div></div>
        <div class="ann-item"><div class="ann-num green">2</div><div class="ann-text"><b>sticky 双状态：订阅前 [订阅] CTA · 订阅后 [铃铛 + 已订阅]</b><br>左侧铃铛 = <b>人维度推送 toggle</b>（仅订阅后出现 · 默认开启 · 点击直接切换 + toast 反馈，不弹确认）<br>右侧主区显示「已订阅 / N 位订阅用户」副标题<br>UI 归社区，订阅行为 + 推送 toggle 状态均调牛人榜接口<br><b>N 计数</b> = 这个用户被多少人订阅（合并计数，不分战绩 / 带单维度），战绩 / 带单两 TAB sticky 共用同一个订阅人数（牛人榜单接口）<br><b>显示前置</b>：用户开启「公开战绩」或具备带单资格才出现订阅按钮（自洽于 TAB 显示规则——两者皆无则战绩 / 带单 TAB 隐藏，订阅按钮天然无入口）</div></div>
        <div class="ann-item"><div class="ann-num amber">3</div><div class="ann-text"><b>牛人榜列表反向入口</b><br>牛人榜列表点交易员 → 跳社区他人主页，原详情页下线<br><b>归牛人榜 PM 改造</b></div></div>
        <div class="info-box blue"><b>关注 vs 订阅独立（强论据）：</b><br>1. risk level / 心智不同 —— 关注 = 零成本社交（看动态/观点），订阅 = 金融决策（参考甚至跟单）<br>2. 用户意图分离 —— 想看一个交易员喷市场但不想跟单 / 抄一个一句话不发的量化大佬的单，两种 case 都常见<br>3. 合规 —— signal subscription 多数司法辖区视为投资建议，要 KYC/适当性匹配，绑社交侧整个 social engagement 做不动<br>4. 指标归因 —— 合并后关注数 = 订阅数，关注转订阅率核心漏斗算不出<br>5. 取消路径不对称 —— 订阅有未平仓位/合规通知，关注秒退订零成本<br>6. 行业惯例 —— Binance Square / Bitget Copy Trade / OKX 跟单广场 / Bybit 全分开</div>
        <div class="info-box red"><b>不做 follow 后引导订阅：</b>跨产品域引导（社交→金融）会让用户对关注产生"附加责任"错觉，反而压低关注率，跟想保住的轻量心智反向</div>
        <div class="info-box green"><b>人维度推送 toggle 三层粒度（AND 关系：任一关闭即不推）：</b><br>1. App 全局推送总开关（归 App「我的→设置→通知」，社区不做）<br>2. 类型级（实盘消息 / 直播预告 / 社区动态，归 App 通知设置二级页）<br>3. <b>人维度（本场景）</b>—— 订阅按钮旁铃铛，控制单个交易员的实盘消息推送</div>
        <div class="info-box amber"><b>三入口订阅状态共享（04-30 决策）：</b>跟单（合约带单主页）/ 牛人榜 / 社区个人主页订阅按钮三处订阅同一份关系（牛人榜单一存储）。社区进 <a href="#scene-b">他人主页 ↗</a> / <a href="#scene-c">战绩 TAB ↗</a> 时调牛人榜接口拉最新订阅 + 关注状态，<b>禁用本地缓存</b>。跟单 / 牛人榜端 UI 仅 [订阅] 按钮（无关注概念），点订阅 → 后台默认带关注（金融→社交隐式），社区关注表必须接受牛人榜侧外部写入。跟「不做一键升级」不冲突——前者卡社交→金融在社区主页 UI 内引导，后者是金融→社交跨端隐式带，方向相反</div>
        <div class="info-box amber"><b>订阅推送内容分流（牛人榜实现，按钮文案不区分）：</b>仅公开战绩 → 推实盘（U 本位合约账户）开平仓动态 · 仅有带单 → 推带单（合约带单账户）开平仓动态 · 两者都有 → 实盘 + 带单都推</div>
        <div class="info-box amber"><b>埋点：</b>订阅点击 + 订阅成功 + 铃铛切换（带开关属性）+ 列表点击，代号见 PRD §埋点</div>
      </div>
    </div>'''
    return _phone_d1() + arrow_12 + _phone_d2() + arrow_23 + _phone_d3() + ann_card
