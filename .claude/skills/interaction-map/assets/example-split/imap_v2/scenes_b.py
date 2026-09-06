#!/usr/bin/env python3
"""PART 1 · 核心承载 - Scene B · 个人主页视角差异"""


def fill_b():
    """Scene B — B-1 我看自己 + B-2 我看别人（header / 订阅数 / 简介 差异）"""
    return '''
    <!-- ─── B-1 · 我看自己主页 ─── -->
    <div class="flow-col">
      <span class="phone-label">B-1 · 我看自己的个人主页</span>
      <div class="phone" style="min-height:660px;display:flex;flex-direction:column;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top">
          <span style="font-size:14px;color:#828282;">‹</span>
          <div style="flex:1;"></div>
          <span style="font-size:14px;color:#828282;">↗</span>
        </div>
        <div style="padding:14px 16px;flex:1;display:flex;flex-direction:column;gap:10px;">
          <div style="position:relative;">
            <div class="anno blue" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n blue">1</div></div>
            <div style="display:flex;align-items:flex-start;gap:12px;">
              <div style="width:54px;height:54px;border-radius:27px;background:linear-gradient(135deg,#667eea,#764ba2);"></div>
              <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:6px;"><span style="font-size:15px;color:#FFFFFF;font-weight:900;">Felix.zhi</span><span style="font-size:10px;color:#FFC83C;">🟡</span></div>
                <div style="display:flex;gap:6px;margin-top:8px;">
                  <button style="background:transparent;border:1px solid #828282;color:#FFFFFF;border-radius:14px;padding:5px 14px;font-size:11px;font-weight:600;">设置</button>
                </div>
              </div>
            </div>
          </div>
          <div style="position:relative;display:flex;gap:18px;font-size:11px;color:#828282;padding:6px 2px;">
            <div class="anno green" style="top:-2px;left:-4px;right:-4px;bottom:-2px;"><div class="anno-n green">2</div></div>
            <span>关注 <b style="color:#FFFFFF;">42</b></span>
            <span>粉丝 <b style="color:#FFFFFF;">1</b></span>
            <span>订阅 <b style="color:#FFFFFF;">3</b> <span style="color:#828282;font-size:9px;">（仅自己可见）</span></span>
          </div>
          <div style="position:relative;">
            <div class="anno red" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n red">3</div></div>
            <div style="background:#262626;border-radius:6px;padding:14px;text-align:center;color:#828282;font-size:10px;border:1px dashed #828282;">📢 申请交易员 Banner（位置归社区 / 内容运营投放 → <a href="#scene-g" style="color:#828282;">G-1 · 资源位 ↗</a>）</div>
          </div>
          <div style="display:flex;gap:14px;border-bottom:1px solid #262626;padding:8px 0;">
            <a href="#scene-c" style="font-size:12px;color:#FFFFFF;font-weight:700;border-bottom:2px solid #007FFF;padding-bottom:6px;text-decoration:none;">内容</a>
            <a href="#scene-c" style="font-size:12px;color:#828282;text-decoration:none;">🔒 交易战绩</a>
            <a href="#scene-c" style="font-size:12px;color:#828282;text-decoration:none;">带单战绩</a>
          </div>
          <div style="display:flex;gap:14px;font-size:11px;padding:2px 0 6px;">
            <a href="#scene-c" style="color:#FFFFFF;font-weight:700;border-bottom:1px solid #F0B90B;padding-bottom:2px;text-decoration:none;">文章</a>
            <a href="#scene-c" style="color:#828282;text-decoration:none;">动态</a>
          </div>
          <div style="background:#262626;border-radius:6px;padding:8px;display:flex;flex-direction:column;gap:6px;">
            <div style="background:#161616;border-radius:4px;padding:6px 8px;"><div style="font-size:10px;color:#FFFFFF;font-weight:700;">BTC 突破 71000 后续怎么看</div><div style="font-size:8px;color:#828282;">3h · 124 阅读 · 12 评</div></div>
            <div style="background:#161616;border-radius:4px;padding:6px 8px;"><div style="font-size:10px;color:#FFFFFF;font-weight:700;">现货长线策略复盘</div><div style="font-size:8px;color:#828282;">昨天 · 386 阅读</div></div>
            <a href="#scene-c" style="font-size:9px;color:#007FFF;text-align:center;padding:2px;text-decoration:none;font-weight:700;">查看 TAB 完整状态 → C ↗</a>
          </div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">单按钮 [设置]（砍齿轮 · 资料/战绩管理/通知管理三合一，详 <a href="#scene-e">资料与设置 ↗</a>）· 订阅数仅自己视角可见</div>
    </div>

    <!-- ─── 箭头 ─── -->
    <div class="aw"><div class="al b"></div><div class="tx b">视角切换<br>（不同用户看）</div></div>

    <!-- ─── B-2 · 我看别人主页 ─── -->
    <div class="flow-col">
      <span class="phone-label">B-2 · 我看别人的个人主页</span>
      <div class="phone" style="min-height:660px;display:flex;flex-direction:column;font-family:'HarmonyOS Sans SC','Noto Sans SC',sans-serif;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top">
          <span style="font-size:14px;color:#828282;">‹</span>
          <div style="flex:1;"></div>
          <span style="font-size:14px;color:#828282;">⋯</span>
          <span style="font-size:14px;color:#828282;margin-left:10px;">↗</span>
        </div>
        <div style="padding:14px 16px;flex:1;display:flex;flex-direction:column;gap:10px;">
          <div style="position:relative;">
            <div class="anno blue" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n blue">1</div></div>
            <div style="display:flex;align-items:flex-start;gap:12px;">
              <div style="width:54px;height:54px;border-radius:27px;background:linear-gradient(135deg,#f5af19,#f12711);"></div>
              <div style="flex:1;">
                <div style="display:flex;align-items:center;gap:6px;"><span style="font-size:15px;color:#FFFFFF;font-weight:900;">龙宫参谋长</span><span style="font-size:10px;color:#FFC83C;">🟡</span></div>
              </div>
              <button style="background:#007FFF;color:#fff;border:none;border-radius:14px;padding:6px 14px;font-size:11px;font-weight:700;">关注</button>
            </div>
          </div>
          <div style="position:relative;display:flex;gap:18px;font-size:11px;color:#828282;padding:6px 2px;">
            <div class="anno green" style="top:-2px;left:-4px;right:-4px;bottom:-2px;"><div class="anno-n green">2</div></div>
            <span>关注 <b style="color:#FFFFFF;">126</b></span>
            <span>粉丝 <b style="color:#FFFFFF;">3.2万</b></span>
            <span style="color:#828282;opacity:.4;">（无订阅数）</span>
          </div>
          <div style="position:relative;">
            <div class="anno purple" style="top:-2px;left:-4px;right:-4px;bottom:-2px;"><div class="anno-n purple">3</div></div>
            <div style="font-size:11px;color:#FFFFFF;line-height:1.6;background:#262626;border-radius:6px;padding:8px 10px;">合约长线 · 全网同名 龙宫参</div>
          </div>
          <div style="background:#262626;border-radius:6px;padding:10px;text-align:center;color:#828282;font-size:10px;border:1px dashed #828282;">📢 广告资源位</div>
          <div style="display:flex;gap:14px;border-bottom:1px solid #262626;padding:8px 0;">
            <a href="#scene-c" style="font-size:12px;color:#FFFFFF;font-weight:700;border-bottom:2px solid #007FFF;padding-bottom:6px;text-decoration:none;">内容</a>
            <a href="#scene-c" style="font-size:12px;color:#FFFFFF;text-decoration:none;">交易战绩</a>
            <a href="#scene-c" style="font-size:12px;color:#FFFFFF;text-decoration:none;">带单战绩</a>
          </div>
          <div style="display:flex;gap:14px;font-size:11px;padding:2px 0 6px;">
            <a href="#scene-c" style="color:#FFFFFF;font-weight:700;border-bottom:1px solid #F0B90B;padding-bottom:2px;text-decoration:none;">文章</a>
            <a href="#scene-c" style="color:#828282;text-decoration:none;">动态</a>
          </div>
          <div style="background:#262626;border-radius:6px;padding:8px;display:flex;flex-direction:column;gap:6px;">
            <div style="background:#161616;border-radius:4px;padding:6px 8px;"><div style="font-size:10px;color:#FFFFFF;font-weight:700;">合约长线 BTC 思路</div><div style="font-size:8px;color:#828282;">2h · 8.2k 阅读</div></div>
            <div style="background:#161616;border-radius:4px;padding:6px 8px;"><div style="font-size:10px;color:#FFFFFF;font-weight:700;">这周回撤策略</div><div style="font-size:8px;color:#828282;">昨天 · 4.5k 阅读</div></div>
            <a href="#scene-c" style="font-size:9px;color:#007FFF;text-align:center;padding:2px;text-decoration:none;font-weight:700;">切到战绩 TAB → C-3 ↗ · 切到带单 → C-4 ↗</a>
          </div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">header [关注] · 无订阅数 · 多个人简介区 · 入口含 Feed 推荐 / 牛人榜列表 / IM / 搜索</div>
    </div>

    <!-- ─── 注释卡 ─── -->
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card" style="align-self:flex-start;margin-top:36px;">
        <div class="card-title">📋 B · 个人主页视角差异 <span class="ann-tag p0">P0</span></div>
        <div class="ann-item">
          <div class="ann-num blue">1</div>
          <div class="ann-text"><b>header 按钮差异</b><br>自己视角：单按钮 [设置]（资料 + 战绩管理 + 通知管理 三合一入口，详 <a href="#scene-e">资料与设置 ↗</a>）<br>他人视角：[关注] 黄色按钮 + ⋯ 菜单（关注是 page-level 社交动作，随主页常驻）</div>
        </div>
        <div class="ann-item">
          <div class="ann-num green">2</div>
          <div class="ann-text"><b>统计数差异</b><br>自己视角：关注 / 粉丝 / 订阅（订阅数仅自己可见）<br>他人视角：关注 / 粉丝（不展示订阅数）</div>
        </div>
        <div class="ann-item">
          <div class="ann-num purple">3</div>
          <div class="ann-text"><b>个人简介区</b><br>他人视角才显示（"全网同名 xxx" 等内容）<br>自己视角不显示，节省 header 空间</div>
        </div>
        <div class="info-box blue"><b>TAB 显示规则：</b>内容（始终显示） / 交易战绩（自己视角始终显示，未公开加 🔒；他人视角仅对方公开才显示） / 带单战绩（仅有资格才显示）</div>
        <div class="info-box amber"><b>埋点：</b>主页进入行为按入口分类（Feed 推荐 / 牛人榜列表 / IM 聊天 / 搜索 / 分享链 / 我的订阅列表 / 我的关注列表 / 其他），代号见 PRD §埋点</div>
      </div>
    </div>
'''
