#!/usr/bin/env python3
"""PART 3 · 自己侧管理 - Scene E · 设置页 + 战绩管理底部抽屉

04-28（晚）会议变更：
- E-1 标题「编辑资料」改「设置」（资料 + 战绩管理 + 通知管理 三合一入口）
- 战绩管理改为单条 + 右侧 toggle 开关 + 下方免责小字（不再是「公开/私密」二选块）
- 新增「通知管理」一级入口 → 跳 App 全局通知中心（Bruce 团队），返回回到本设置页
- E-2 中央弹窗改为底部抽屉（drawer），从底部升起
"""


def fill_e():
    """Scene E — E-1 设置（含战绩管理 toggle + 通知管理跨端入口）+ E-2 战绩管理底部抽屉"""
    return '''
    <!-- ─── E-1 · 设置页（资料 + 战绩管理 + 通知管理 三合一） ─── -->
    <div class="flow-col">
      <span class="phone-label">E-1 · 设置</span>
      <div class="phone" style="min-height:720px;display:flex;flex-direction:column;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top"><span style="font-size:14px;color:#828282;">‹</span><div style="flex:1;text-align:center;"><div class="ph-name">设置</div></div><span style="font-size:13px;color:#007FFF;font-weight:700;">完成</span></div>
        <div style="padding:12px 16px;flex:1;display:flex;flex-direction:column;gap:14px;overflow:hidden;">
          <!-- 1. 个人资料 section -->
          <div style="position:relative;">
            <div class="anno blue" style="top:-2px;left:-4px;right:-4px;bottom:-2px;"><div class="anno-n blue">1</div></div>
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;"><span style="width:3px;height:13px;background:#007FFF;border-radius:2px;"></span><span style="color:#FFFFFF;font-size:12px;font-weight:900;">个人资料</span></div>
            <div style="background:#1F1F1F;border-radius:8px;padding:4px 12px;">
              <div style="display:flex;align-items:center;justify-content:space-between;padding:9px 0;border-bottom:1px solid #262626;">
                <span style="font-size:12px;color:#FFFFFF;">头像</span>
                <div style="display:flex;align-items:center;gap:8px;"><div style="width:32px;height:32px;border-radius:16px;background:linear-gradient(135deg,#667eea,#764ba2);"></div><span style="color:#828282;font-size:14px;">›</span></div>
              </div>
              <div style="display:flex;align-items:center;justify-content:space-between;padding:9px 0;border-bottom:1px solid #262626;">
                <span style="font-size:12px;color:#FFFFFF;">用户名</span>
                <div style="display:flex;align-items:center;gap:6px;"><span style="font-size:12px;color:#828282;">Felix.zhi</span><span style="color:#828282;font-size:14px;">›</span></div>
              </div>
              <div style="display:flex;align-items:center;justify-content:space-between;padding:9px 0;border-bottom:1px solid #262626;">
                <span style="font-size:12px;color:#FFFFFF;">个人简介</span>
                <div style="display:flex;align-items:center;gap:6px;max-width:60%;"><span style="font-size:11px;color:#828282;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">合约长线策略 · 全网同名 龙宫参</span><span style="color:#828282;font-size:14px;">›</span></div>
              </div>
              <div style="display:flex;align-items:center;justify-content:space-between;padding:9px 0;">
                <span style="font-size:12px;color:#FFFFFF;">KYC 等级</span>
                <span style="font-size:12px;color:#828282;">Lv.2 已认证</span>
              </div>
            </div>
          </div>
          <!-- 2. 交易战绩管理（单条 + toggle 开关 + 免责小字） -->
          <div style="position:relative;">
            <div class="anno red" style="top:-2px;left:-4px;right:-4px;bottom:-2px;"><div class="anno-n red">2</div></div>
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;"><span style="width:3px;height:13px;background:#D9415B;border-radius:2px;"></span><span style="color:#FFFFFF;font-size:12px;font-weight:900;">交易战绩管理</span></div>
            <div style="background:#1F1F1F;border-radius:8px;padding:4px 12px;">
              <div style="display:flex;align-items:center;justify-content:space-between;padding:11px 0;">
                <div style="flex:1;min-width:0;">
                  <div style="font-size:12px;color:#FFFFFF;font-weight:600;">公开我的交易战绩</div>
                </div>
                <div style="width:38px;height:22px;border-radius:11px;background:#06995C;position:relative;flex-shrink:0;">
                  <div style="position:absolute;top:2px;right:2px;width:18px;height:18px;border-radius:9px;background:#FFFFFF;"></div>
                </div>
              </div>
            </div>
            <div style="font-size:9px;color:#828282;line-height:1.6;padding:6px 4px 0;">公开后所有人可见你的累计收益率 / 胜率 / 回撤 / 资产量等指标，且有机会进入牛人榜推荐池。战绩数据来源于你的真实交易记录，不构成投资建议</div>
          </div>
          <!-- 3. 通知管理（跨端入口 → App 全局通知中心） -->
          <div style="position:relative;">
            <div class="anno purple" style="top:-2px;left:-4px;right:-4px;bottom:-2px;"><div class="anno-n purple">3</div></div>
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;"><span style="width:3px;height:13px;background:#8b5cf6;border-radius:2px;"></span><span style="color:#FFFFFF;font-size:12px;font-weight:900;">通知管理</span></div>
            <div style="background:#1F1F1F;border-radius:8px;padding:4px 12px;">
              <div style="display:flex;align-items:center;justify-content:space-between;padding:11px 0;">
                <div style="display:flex;align-items:center;gap:8px;"><span style="font-size:14px;">🔔</span><span style="font-size:12px;color:#FFFFFF;">通知设置</span></div>
                <div style="display:flex;align-items:center;gap:6px;"><span style="font-size:9px;color:#828282;">App 通知中心</span><span style="color:#828282;font-size:14px;">›</span></div>
              </div>
            </div>
            <div style="font-size:9px;color:#828282;line-height:1.6;padding:6px 4px 0;">跨端入口 · 跳 App 全局通知中心（Bruce 团队维护）· 左上返回直接回本设置页，不丢上下文</div>
          </div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">设置页 = 资料 + 战绩管理 toggle + 通知管理跨端入口（三合一）</div>
    </div>

    <!-- ─── 箭头 ─── -->
    <div class="aw"><div class="al r"></div><div class="tx r">未公开提示条<br>「设置为公开模式」</div></div>

    <!-- ─── E-2 · 战绩管理底部抽屉（战绩未公开提示条专属快捷入口） ─── -->
    <div class="flow-col">
      <span class="phone-label">E-2 · 战绩管理底部抽屉</span>
      <div class="phone" style="min-height:720px;display:flex;flex-direction:column;background:#161616;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;position:relative;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <!-- 背景半透明遮罩（战绩 TAB 未公开态模糊隐显） -->
        <div style="flex:1;padding:12px 14px;display:flex;flex-direction:column;gap:6px;opacity:.3;">
          <div style="background:rgba(246,70,93,0.08);border:1px solid rgba(246,70,93,0.3);border-radius:6px;padding:8px;font-size:9px;color:#FFFFFF;">ⓘ 您的交易战绩仅自己可见</div>
          <div style="background:#262626;border-radius:6px;padding:14px;text-align:center;color:#828282;font-size:9px;">（战绩 TAB 未公开态内容）</div>
        </div>
        <!-- 全屏遮罩 -->
        <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.55);"></div>
        <!-- 底部抽屉（drawer） -->
        <div style="position:absolute;left:0;right:0;bottom:0;background:#1F1F1F;border-radius:16px 16px 0 0;padding:14px 16px 18px;">
          <div class="anno purple" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n purple">4</div></div>
          <div style="width:36px;height:4px;border-radius:2px;background:#828282;margin:0 auto 14px;opacity:.5;"></div>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
            <span style="font-size:14px;color:#FFFFFF;font-weight:900;">交易战绩管理</span>
            <span style="color:#828282;font-size:14px;">✕</span>
          </div>
          <div style="background:#262626;border-radius:8px;padding:4px 12px;margin-bottom:10px;">
            <div style="display:flex;align-items:center;justify-content:space-between;padding:11px 0;">
              <span style="font-size:13px;color:#FFFFFF;font-weight:600;">公开我的交易战绩</span>
              <div style="width:38px;height:22px;border-radius:11px;background:#06995C;position:relative;flex-shrink:0;">
                <div style="position:absolute;top:2px;right:2px;width:18px;height:18px;border-radius:9px;background:#FFFFFF;"></div>
              </div>
            </div>
          </div>
          <div style="font-size:10px;color:#828282;line-height:1.6;margin-bottom:14px;">公开后所有人可见你的累计收益率 / 胜率 / 回撤 / 资产量等指标，且有机会进入牛人榜推荐池。战绩数据来源于你的真实交易记录，不构成投资建议</div>
          <button style="background:#007FFF;color:#fff;border:none;width:100%;padding:11px;border-radius:8px;font-size:13px;font-weight:700;">确认</button>
          <div style="text-align:center;color:#828282;font-size:9px;margin-top:8px;">与设置页内 toggle 共用同一份数据</div>
        </div>
      </div>
      <div class="flow-note">底部抽屉（drawer）从底部升起 · 不绕回设置页深处 · 同数据双入口</div>
    </div>

    <!-- ─── 注释卡 ─── -->
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card" style="align-self:flex-start;margin-top:36px;">
        <div class="card-title">📋 E · 设置页 + 战绩管理底部抽屉 <span class="ann-tag p0">P0</span></div>
        <div class="ann-item"><div class="ann-num blue">1</div><div class="ann-text"><b>个人资料 section</b><br>头像 / 用户名 / 个人简介 / KYC 等级 · 标准 list 形态，每条单独跳详情或内联编辑</div></div>
        <div class="ann-item"><div class="ann-num red">2</div><div class="ann-text"><b>交易战绩管理（一级开关）</b><br>单条 + 右侧 toggle 开关（默认私密 / 关）· 下方小字免责说明（"不构成投资建议"）<br>战绩公开度是 profile attribute，归同一 domain</div></div>
        <div class="ann-item"><div class="ann-num purple">3</div><div class="ann-text"><b>通知管理（跨端入口）</b><br>点击 → 跳 App 全局通知中心（Bruce 团队维护，社区不开发新页）<br><b>关键：左上返回必须回到本设置页</b>，不能丢上下文 / 不能直接退到 App 首页 / 不能退到社区主页</div></div>
        <div class="ann-item"><div class="ann-num purple">4</div><div class="ann-text"><b>战绩管理底部抽屉（drawer）</b><br>战绩 TAB 「设置为公开模式」超链接 → 从底部升起抽屉（不是中央弹窗），单条 toggle + 免责 + 确认<br>抽屉与设置页内交易战绩管理 section 共用同一份数据，两个入口同源</div></div>
        <div class="info-box blue"><b>IA 原理：</b>设置页 = 资料 + 战绩管理 + 通知管理 三合一。资料和战绩管理是 profile-domain（"我对外长啥样"）；通知管理是 system-domain，跨端跳 App 通知中心，社区不重复实现</div>
        <div class="info-box green"><b>通知三层粒度（关键，AND 关系：任一关闭即不推）：</b><br>1. App 全局总开关（→ 本场景通知管理入口跳 App 通知中心）<br>2. 类型级（实盘消息 / 直播预告 / 社区动态）<br>3. 人维度（订阅按钮旁铃铛 · 单交易员推送）</div>
        <div class="info-box amber"><b>埋点：</b>设置入口点击（区分 header 按钮 / 抽屉快捷入口）+ 公开战绩切换 + 通知设置跳转（跨端），代号见 PRD §埋点</div>
      </div>
    </div>
'''
