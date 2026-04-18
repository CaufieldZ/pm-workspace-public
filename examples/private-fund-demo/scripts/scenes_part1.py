# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
# Scene C-1 · Web 运营后台 · 订单审核队列

def fill_c1():
    """Scene C-1 · 运营后台订单审核队列 · webframe"""
    screen = '''
    <div class="flow-col">
      <span class="phone-label">C-1 · 订单审核队列</span>
      <div class="webframe" style="width:820px;min-height:520px;">
        <div class="wf-bar">
          <div class="wf-dots"><i></i><i></i><i></i></div>
          <div class="wf-url">fund-admin.example.com/orders/review</div>
        </div>
        <div class="webframe-body" style="padding:0;">
          <!-- 顶部导航 -->
          <div style="background:#001529;padding:0 20px;height:48px;display:flex;align-items:center;gap:20px;">
            <span style="font-size:14px;font-weight:800;color:#fff;">Fund Admin</span>
            <span style="font-size:12px;color:rgba(255,255,255,.5);">订单中心</span>
            <span style="font-size:12px;color:#1890FF;font-weight:600;border-bottom:2px solid #1890FF;padding-bottom:2px;">审核队列</span>
            <span style="margin-left:auto;font-size:11px;color:rgba(255,255,255,.6);">运营专员 · admin</span>
          </div>
          <div style="padding:16px 20px;">
            <!-- Tab 切换 -->
            <div style="display:flex;gap:0;margin-bottom:14px;border-bottom:1px solid #e8e8e8;">
              <div style="position:relative;">
                <div class="anno purple" style="top:-3px;left:-3px;right:-3px;bottom:0;"><div class="anno-n purple">1</div></div>
                <div style="padding:8px 16px;font-size:13px;font-weight:600;color:#1890FF;border-bottom:2px solid #1890FF;">认购订单 <span style="background:#F6465D;color:#fff;border-radius:10px;padding:1px 6px;font-size:10px;margin-left:4px;">3</span></div>
              </div>
              <div style="padding:8px 16px;font-size:13px;color:#595959;">赎回订单 <span style="background:#d97706;color:#fff;border-radius:10px;padding:1px 6px;font-size:10px;margin-left:4px;">1</span></div>
            </div>
            <!-- 筛选栏 -->
            <div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;">
              <div style="background:#f5f5f5;border-radius:4px;padding:5px 12px;font-size:12px;color:#595959;">状态：待审核 ▾</div>
              <div style="background:#f5f5f5;border-radius:4px;padding:5px 12px;font-size:12px;color:#595959;">基金：全部 ▾</div>
              <div style="background:#1890FF;border-radius:4px;padding:5px 12px;font-size:12px;color:#fff;margin-left:auto;">+ 批量审核</div>
            </div>
            <!-- 表头 -->
            <div style="display:grid;grid-template-columns:120px 130px 160px 100px 80px 100px 100px;gap:0;background:#fafafa;border:1px solid #e8e8e8;border-radius:4px 4px 0 0;">
              <div style="padding:8px 10px;font-size:11px;font-weight:600;color:#595959;">订单号</div>
              <div style="padding:8px 10px;font-size:11px;font-weight:600;color:#595959;">投资人</div>
              <div style="padding:8px 10px;font-size:11px;font-weight:600;color:#595959;">基金</div>
              <div style="padding:8px 10px;font-size:11px;font-weight:600;color:#595959;text-align:right;">认购金额</div>
              <div style="padding:8px 10px;font-size:11px;font-weight:600;color:#595959;">状态</div>
              <div style="padding:8px 10px;font-size:11px;font-weight:600;color:#595959;">申请时间</div>
              <div style="padding:8px 10px;font-size:11px;font-weight:600;color:#595959;text-align:center;">操作</div>
            </div>
            <!-- 数据行 1 -->
            <div style="position:relative;">
              <div class="anno green" style="top:0;left:-2px;right:-2px;bottom:0;"><div class="anno-n green">2</div></div>
              <div style="display:grid;grid-template-columns:120px 130px 160px 100px 80px 100px 100px;border:1px solid #e8e8e8;border-top:none;background:#fff;">
                <div style="padding:8px 10px;font-size:11px;color:#1d2129;font-family:'IBM Plex Mono',monospace;">SUB-0418-001</div>
                <div style="padding:8px 10px;font-size:11px;color:#1d2129;">张**（QI）</div>
                <div style="padding:8px 10px;font-size:11px;color:#1d2129;">鑫远稳健一期</div>
                <div style="padding:8px 10px;font-size:11px;color:#1d2129;text-align:right;font-family:'IBM Plex Mono',monospace;">100万</div>
                <div style="padding:8px 10px;"><span style="background:#fff7e6;color:#d97706;border-radius:4px;padding:2px 6px;font-size:10px;font-weight:600;">待审核</span></div>
                <div style="padding:8px 10px;font-size:10px;color:#8c8c8c;">04-18 14:32</div>
                <div style="padding:8px 10px;display:flex;gap:4px;justify-content:center;">
                  <div style="background:#1890FF;color:#fff;border-radius:3px;padding:3px 8px;font-size:10px;font-weight:600;cursor:pointer;">通过</div>
                  <div style="background:#fff;border:1px solid #F6465D;color:#F6465D;border-radius:3px;padding:3px 8px;font-size:10px;cursor:pointer;">驳回</div>
                </div>
              </div>
            </div>
            <!-- 数据行 2 -->
            <div style="display:grid;grid-template-columns:120px 130px 160px 100px 80px 100px 100px;border:1px solid #e8e8e8;border-top:none;background:#fff;">
              <div style="padding:8px 10px;font-size:11px;color:#1d2129;font-family:'IBM Plex Mono',monospace;">SUB-0418-002</div>
              <div style="padding:8px 10px;font-size:11px;color:#1d2129;">李**（QI）</div>
              <div style="padding:8px 10px;font-size:11px;color:#1d2129;">鑫远稳健一期</div>
              <div style="padding:8px 10px;font-size:11px;color:#1d2129;text-align:right;font-family:'IBM Plex Mono',monospace;">500万</div>
              <div style="padding:8px 10px;"><span style="background:#f6ffed;color:#52c41a;border-radius:4px;padding:2px 6px;font-size:10px;font-weight:600;">已通过</span></div>
              <div style="padding:8px 10px;font-size:10px;color:#8c8c8c;">04-18 10:15</div>
              <div style="padding:8px 10px;display:flex;gap:4px;justify-content:center;">
                <div style="background:#f5f5f5;color:#bfbfbf;border-radius:3px;padding:3px 8px;font-size:10px;">查看</div>
              </div>
            </div>
            <!-- 数据行 3 -->
            <div style="position:relative;">
              <div class="anno red" style="top:0;left:-2px;right:-2px;bottom:0;"><div class="anno-n red">3</div></div>
              <div style="display:grid;grid-template-columns:120px 130px 160px 100px 80px 100px 100px;border:1px solid #e8e8e8;border-top:none;border-radius:0 0 4px 4px;background:#fffbe6;">
                <div style="padding:8px 10px;font-size:11px;color:#1d2129;font-family:'IBM Plex Mono',monospace;">SUB-0418-003</div>
                <div style="padding:8px 10px;font-size:11px;color:#1d2129;">王**（QI）</div>
                <div style="padding:8px 10px;font-size:11px;color:#1d2129;">鑫远稳健一期</div>
                <div style="padding:8px 10px;font-size:11px;color:#1d2129;text-align:right;font-family:'IBM Plex Mono',monospace;">3000万</div>
                <div style="padding:8px 10px;"><span style="background:#fff7e6;color:#d97706;border-radius:4px;padding:2px 6px;font-size:10px;font-weight:600;">待双签</span></div>
                <div style="padding:8px 10px;font-size:10px;color:#8c8c8c;">04-18 09:00</div>
                <div style="padding:8px 10px;display:flex;gap:4px;justify-content:center;">
                  <div style="background:#d97706;color:#fff;border-radius:3px;padding:3px 8px;font-size:10px;font-weight:600;">合规双签</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="flow-note">运营后台 · 认购订单审核队列</div>
    </div>'''

    card = '''
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card">
        <div class="card-title">C-1 · 订单审核队列 <span class="ann-tag new">NEW</span><span class="ann-tag p0">P0</span></div>
        <div class="ann-item"><div class="ann-num purple">1</div><div class="ann-text"><b>认购 / 赎回双 Tab</b><span class="ann-tag new">NEW</span><br>Tab 上展示待审核计数 badge，切换 Tab 共享同一套筛选器</div></div>
        <div class="ann-item"><div class="ann-num green">2</div><div class="ann-text"><b>常规订单审核</b><span class="ann-tag p0">P0</span><br>运营专员一键通过/驳回；驳回需填写原因；通过后 T+1 系统自动确认份额</div></div>
        <div class="ann-item"><div class="ann-num red">3</div><div class="ann-text"><b>大额订单双签</b><span class="ann-tag p0">B5</span><br>单笔 ≥ 1000 万进入「待双签」状态，需运营专员 + 合规风控分别确认后生效</div></div>
        <div class="info-box blue"><b>状态机：</b>待审核 → 已通过（T+1 确认份额）/ 已驳回（资金原路退回 T+3）<br>大额路径：待审核 → 待双签 → 已通过 / 已驳回</div>
      </div>
    </div>'''

    return screen + card
