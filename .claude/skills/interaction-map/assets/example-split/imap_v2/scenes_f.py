#!/usr/bin/env python3
"""PART 3 · 自己侧管理 - Scene F · 分享菜单与卡片"""


def _phone_f1():
    """F-1 · 分享菜单（4 选项）"""
    return '''
    <div class="flow-col">
      <span class="phone-label">F-1 · 分享菜单</span>
      <div class="phone" style="min-height:520px;display:flex;flex-direction:column;background:rgba(0,0,0,.6);font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div style="flex:1;"></div>
        <div style="position:relative;background:#262626;border-radius:14px 14px 0 0;padding:14px;">
          <div class="anno blue" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n blue">1</div></div>
          <div style="text-align:center;font-size:13px;color:#FFFFFF;font-weight:900;margin-bottom:14px;">分享至</div>
          <div style="display:flex;align-items:center;gap:10px;padding:10px;background:rgba(43,127,255,0.08);border-radius:6px;margin-bottom:8px;">
            <span style="font-size:18px;">📤</span>
            <div style="flex:1;"><div style="font-size:12px;color:#FFFFFF;font-weight:700;">分享主页</div><div style="font-size:9px;color:#007FFF;font-weight:700;">[社区自做 ↗]</div></div>
          </div>
          <div style="display:flex;align-items:center;gap:10px;padding:10px;background:#161616;border-radius:6px;margin-bottom:8px;">
            <span style="font-size:18px;">📊</span>
            <div style="flex:1;"><div style="font-size:12px;color:#FFFFFF;font-weight:700;">分享交易战绩</div><div style="font-size:9px;color:#9945FF;">[牛人榜接口 ↗]</div></div>
          </div>
          <div style="display:flex;align-items:center;gap:10px;padding:10px;background:#161616;border-radius:6px;margin-bottom:8px;">
            <span style="font-size:18px;">💹</span>
            <div style="flex:1;"><div style="font-size:12px;color:#FFFFFF;font-weight:700;">分享合约带单</div><div style="font-size:9px;color:#9945FF;">[牛人榜接口 ↗]</div></div>
          </div>
          <div style="display:flex;align-items:center;gap:10px;padding:10px;background:#161616;border-radius:6px;">
            <span style="font-size:18px;">💰</span>
            <div style="flex:1;"><div style="font-size:12px;color:#FFFFFF;font-weight:700;">分享现货带单</div><div style="font-size:9px;color:#9945FF;">[牛人榜接口 ↗]</div></div>
          </div>
          <button style="background:transparent;border:none;color:#828282;font-size:13px;width:100%;padding:14px 0 4px;">取消</button>
        </div>
      </div>
      <div class="flow-note">个人主页 ⤴️ 入口 · 4 选 1 · 1 张社区自做 + 3 张调牛人榜接口</div>
    </div>'''


def _phone_f2():
    """F-2 · 分享主页卡片（社区自做，对齐 OKX）"""
    return '''
    <div class="flow-col">
      <span class="phone-label">F-2 · 分享主页卡片（社区自做）</span>
      <div class="phone" style="min-height:520px;display:flex;flex-direction:column;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top"><span style="font-size:14px;color:#828282;">‹</span><div style="flex:1;text-align:center;"><div class="ph-name">分享主页</div></div></div>
        <div style="padding:14px;flex:1;display:flex;align-items:center;justify-content:center;">
          <div style="position:relative;background:linear-gradient(160deg,#1e293b,#0f172a);border-radius:14px;padding:18px 16px;width:100%;color:#fff;">
            <div class="anno green" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n green">2</div></div>
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:14px;"><span style="background:#FFC83C;color:#000;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:900;">Platform C</span><span style="font-size:11px;font-weight:700;">Platform C</span></div>
            <div style="display:flex;flex-direction:column;align-items:center;text-align:center;gap:8px;">
              <div style="width:64px;height:64px;border-radius:32px;background:linear-gradient(135deg,#667eea,#764ba2);"></div>
              <div style="font-size:16px;font-weight:900;">Felix.zhi</div>
              <div style="font-size:10px;color:rgba(255,255,255,.6);line-height:1.5;">合约长线策略 · 全网同名 龙宫参</div>
              <div style="display:flex;gap:18px;font-size:10px;color:rgba(255,255,255,.6);"><span>关注 <b style="color:#fff;">42</b></span><span>粉丝 <b style="color:#fff;">3.2万</b></span></div>
              <div style="width:80px;height:80px;background:repeating-linear-gradient(45deg,#fff,#fff 3px,#0f172a 3px,#0f172a 6px);border-radius:6px;margin-top:6px;"></div>
              <div style="font-size:10px;color:rgba(255,255,255,.6);">扫码访问 ta 的主页</div>
            </div>
          </div>
        </div>
        <div style="padding:10px 14px;display:flex;gap:8px;">
          <button style="flex:1;background:#262626;color:#FFFFFF;border:none;padding:10px;border-radius:8px;font-size:12px;font-weight:700;">保存图片</button>
          <button style="flex:1;background:#007FFF;color:#fff;border:none;padding:10px;border-radius:8px;font-size:12px;font-weight:700;">分享</button>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">字段全部走社区 API · 不依赖牛人榜 · 视觉对齐 OKX</div>
    </div>'''


def _phone_f3():
    """F-3 · 分享其他 3 卡（牛人榜接口）"""
    return '''
    <div class="flow-col">
      <span class="phone-label">F-3 · 分享其他 3 种（牛人榜接口）</span>
      <div class="phone" style="min-height:520px;display:flex;flex-direction:column;border:2px dashed #9945FF;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top"><span style="font-size:14px;color:#828282;">‹</span><div style="flex:1;text-align:center;"><div class="ph-name">分享 · 牛人榜出图</div></div></div>
        <div style="padding:14px;flex:1;display:flex;align-items:center;justify-content:center;">
          <div style="position:relative;background:linear-gradient(160deg,#2d1810,#1a0c08);border-radius:14px;padding:18px 16px;width:100%;color:#fff;">
            <div class="anno purple" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n purple">3</div></div>
            <div style="font-size:11px;color:rgba(255,255,255,.6);margin-bottom:6px;">交易战绩 · 30 日</div>
            <div style="font-size:32px;font-weight:900;color:#0ECB81;font-family:'JetBrains Mono',monospace;">+173.12%</div>
            <div style="height:40px;margin:8px 0;"><svg width="100%" height="40" viewBox="0 0 100 40"><polyline points="0,36 12,30 28,22 45,28 60,15 75,8 90,4 100,2" stroke="#0ECB81" stroke-width="2" fill="none"/></svg></div>
            <div style="font-size:10px;color:rgba(255,255,255,.6);text-align:center;padding:12px;border:1px dashed rgba(255,255,255,.15);border-radius:8px;">UI 由牛人榜出 · 社区只调接口</div>
          </div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">入口归社区，渲染走牛人榜接口（与牛人榜列表反向入口同属跨端协作）</div>
    </div>'''


def fill_f():
    """Scene F · 分享菜单与卡片"""
    arrow_12 = '<div class="aw"><div class="al g"></div><div class="tx g">点击「分享主页」</div></div>'
    arrow_23 = '<div class="aw"><div class="al p"></div><div class="tx p">点击其他 3 项</div></div>'
    ann_card = '''
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card" style="align-self:flex-start;margin-top:36px;">
        <div class="card-title">📋 F · 分享菜单与卡片 <span class="ann-tag p0">P0</span> <span class="ann-tag p1">P1</span></div>
        <div class="ann-item"><div class="ann-num blue">1</div><div class="ann-text"><b>分享菜单</b><br>4 选 1 · 主页归社区，3 张牛人榜出图（交易战绩 / 合约带单 / 现货带单）</div></div>
        <div class="ann-item"><div class="ann-num green">2</div><div class="ann-text"><b>主页卡（社区自做）</b><br>头像 / 昵称 / 简介 / 关注粉丝 / 二维码 · 字段全社区 API · 视觉对齐 OKX</div></div>
        <div class="ann-item"><div class="ann-num purple">3</div><div class="ann-text"><b>其他 3 卡（牛人榜出）</b><br>UI 由牛人榜出 · 社区只调接口（4 个分享接口契约待对齐）</div></div>
        <div class="info-box amber"><b>埋点：</b>分享菜单点击按分享类型分类（主页 / 战绩 / 合约带单 / 现货带单），代号见 PRD §埋点</div>
      </div>
    </div>'''
    return _phone_f1() + arrow_12 + _phone_f2() + arrow_23 + _phone_f3() + ann_card
