#!/usr/bin/env python3
"""PART 4 · 资源位 - Scene G · 申请交易员 Banner"""


def fill_g():
    """Scene G — G-1 Banner 占位（位置归社区 / 内容运营投放）"""
    return '''
    <!-- ─── G-1 · Banner 位 ─── -->
    <div class="flow-col">
      <span class="phone-label">G-1 · 申请交易员 Banner 位</span>
      <div class="phone" style="min-height:560px;display:flex;flex-direction:column;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top"><span style="font-size:14px;color:#828282;">‹</span><div style="flex:1;"></div></div>
        <div style="padding:14px 16px;flex:1;display:flex;flex-direction:column;gap:10px;">
          <div style="display:flex;align-items:flex-start;gap:12px;">
            <div style="width:48px;height:48px;border-radius:24px;background:linear-gradient(135deg,#667eea,#764ba2);"></div>
            <div style="flex:1;">
              <div style="font-size:14px;color:#FFFFFF;font-weight:900;">Felix.zhi</div>
              <div style="display:flex;gap:6px;margin-top:6px;">
                <button style="background:transparent;border:1px solid #828282;color:#FFFFFF;border-radius:14px;padding:5px 14px;font-size:11px;">设置</button>
              </div>
            </div>
          </div>
          <div style="display:flex;gap:18px;font-size:11px;color:#828282;padding:4px 2px;">
            <span>关注 <b style="color:#FFFFFF;">42</b></span>
            <span>粉丝 <b style="color:#FFFFFF;">1</b></span>
            <span>订阅 <b style="color:#FFFFFF;">3</b></span>
          </div>
          <div style="position:relative;background:linear-gradient(135deg,rgba(217,119,6,0.16),rgba(217,119,6,0.04));border:1px dashed #F0B90B;border-radius:10px;padding:18px;">
            <div class="anno red" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n red">1</div></div>
            <div style="display:flex;align-items:center;gap:10px;">
              <span style="font-size:24px;">🎯</span>
              <div style="flex:1;">
                <div style="font-size:13px;color:#FFFFFF;font-weight:900;">申请成为交易员</div>
                <div style="font-size:10px;color:#828282;margin-top:2px;line-height:1.5;">分享带单战绩 · 获得粉丝 · 上榜机会</div>
              </div>
              <span style="font-size:14px;color:#F0B90B;">›</span>
            </div>
            <div style="margin-top:8px;font-size:9px;color:#F0B90B;text-align:center;font-weight:700;background:rgba(217,119,6,0.1);padding:4px;border-radius:4px;">📢 广告资源位 · 内容运营 CMS 投放</div>
          </div>
          <div style="display:flex;gap:14px;border-bottom:1px solid #262626;padding:8px 0;opacity:.5;">
            <span style="font-size:12px;color:#FFFFFF;font-weight:700;">内容</span>
            <span style="font-size:12px;color:#828282;">🔒 交易战绩</span>
          </div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">位置在自己主页 header 下方 · 社区只占位，不归社区写内容</div>
    </div>

    <!-- ─── 箭头 ─── -->
    <div class="aw"><div class="al a"></div><div class="tx a">点击 Banner<br>（跨团队跳转）</div></div>

    <!-- ─── 跳出占位 · 牛人榜申请页 ─── -->
    <div class="flow-col">
      <span class="phone-label">→ 牛人榜申请交易员页（跨团队）</span>
      <div class="phone" style="min-height:560px;display:flex;flex-direction:column;border:2px dashed #F0B90B;opacity:0.85;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top"><span style="font-size:14px;color:#828282;">‹</span><div style="flex:1;text-align:center;"><div class="ph-name">申请成为交易员</div></div></div>
        <div style="padding:14px;flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;">
          <div style="font-size:32px;">🎯</div>
          <div style="font-size:14px;color:#FFFFFF;font-weight:900;text-align:center;">申请页归牛人榜</div>
          <div style="font-size:11px;color:#828282;text-align:center;line-height:1.6;">资质审核 / 协议签署 / 资料填写<br>社区不画内部细节</div>
          <div style="background:rgba(217,119,6,0.10);border:1px dashed #F0B90B;border-radius:6px;padding:10px 14px;color:#F0B90B;font-size:10px;font-weight:700;">埋点：跨端漏斗 → 牛人榜接续</div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">View 2 占位 · 跨端漏斗终点</div>
    </div>

    <!-- ─── 注释卡 ─── -->
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card" style="align-self:flex-start;margin-top:36px;">
        <div class="card-title">📋 G · 申请交易员 Banner 位 <span class="ann-tag p1">P1</span></div>
        <div class="ann-item"><div class="ann-num red">1</div><div class="ann-text"><b>位置归社区，内容归运营</b><br>社区前端只在 header 下方留位置 · 内容由广告资源运营 CMS 投放</div></div>
        <div class="info-box amber"><b>埋点：</b>申请交易员 Banner 点击 · 跳牛人榜申请页（牛人榜侧埋点接续），代号见 PRD §埋点</div>
        <div class="info-box blue"><b>仅自己视角显示</b>（自己的主页）· 已是交易员状态自动隐藏（运营策略）</div>
      </div>
    </div>
'''
