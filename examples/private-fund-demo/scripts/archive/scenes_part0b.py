# Scene B-1, B-2 · H5 投资人端 · 赎回流程

def _aw(color, label):
    return f'''
    <div class="aw"><div class="al {color}"></div><div class="tx {color}">{label}</div></div>'''


def fill_b1():
    """Scene B-1 · 持仓列表 + 赎回入口 · phone"""
    s1 = '''
    <div class="flow-col">
      <span class="phone-label">B-1 · 持仓列表</span>
      <div class="phone" style="display:flex;flex-direction:column;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top">
          <span style="font-size:14px;color:var(--dark-text3);">‹</span>
          <div style="flex:1;text-align:center;"><div class="ph-name">我的持仓</div></div>
          <div style="width:14px;"></div>
        </div>
        <div style="padding:14px 16px;flex:1;overflow:hidden;">
          <div style="background:var(--dark2);border-radius:8px;padding:10px 12px;margin-bottom:10px;">
            <div style="font-size:10px;color:var(--dark-text3);margin-bottom:2px;">持仓总市值（元）</div>
            <div style="font-size:20px;font-weight:800;color:var(--dark-text);font-family:'IBM Plex Mono',monospace;">1,284,300.00</div>
            <div style="font-size:11px;color:#0ECB81;margin-top:2px;">↑ +28,430.00（+28.43%）</div>
          </div>
          <div style="position:relative;margin-bottom:6px;">
            <div class="anno green" style="top:-3px;left:-3px;right:-3px;bottom:-3px;"><div class="anno-n green">1</div></div>
            <div style="background:var(--dark2);border-radius:8px;padding:10px 12px;">
              <div style="font-size:13px;font-weight:700;color:var(--dark-text);margin-bottom:4px;">鑫远稳健一期</div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:8px;">
                <div><div style="font-size:9px;color:var(--dark-text3);">持有份额</div><div style="font-size:12px;font-weight:700;color:var(--dark-text);font-family:'IBM Plex Mono',monospace;">7,788.08</div></div>
                <div><div style="font-size:9px;color:var(--dark-text3);">当前净值</div><div style="font-size:12px;font-weight:700;color:var(--dark-text);font-family:'IBM Plex Mono',monospace;">1.2843</div></div>
                <div><div style="font-size:9px;color:var(--dark-text3);">持仓市值</div><div style="font-size:12px;font-weight:700;color:var(--dark-text);font-family:'IBM Plex Mono',monospace;">1,284,300</div></div>
                <div><div style="font-size:9px;color:var(--dark-text3);">浮动盈亏</div><div style="font-size:12px;font-weight:700;color:#0ECB81;font-family:'IBM Plex Mono',monospace;">+284,300</div></div>
              </div>
              <div style="position:relative;">
                <div class="anno amber" style="top:-3px;left:-3px;right:-3px;bottom:-3px;"><div class="anno-n amber">2</div></div>
                <div style="background:var(--blue);color:#fff;border-radius:8px;padding:8px;text-align:center;font-size:13px;font-weight:700;">申请赎回</div>
              </div>
            </div>
          </div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">持仓列表 · 开放日可见「申请赎回」</div>
    </div>'''

    arr = _aw("a", "点击「申请赎回」")

    s2 = '''
    <div class="flow-col">
      <span class="phone-label">B-1 · 赎回须知</span>
      <div class="phone" style="display:flex;flex-direction:column;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top">
          <span style="font-size:14px;color:var(--dark-text3);">‹</span>
          <div style="flex:1;text-align:center;"><div class="ph-name">赎回须知</div></div>
          <div style="width:14px;"></div>
        </div>
        <div style="padding:14px 16px;flex:1;overflow:hidden;">
          <div style="background:rgba(217,119,6,.08);border:1px solid rgba(217,119,6,.3);border-radius:8px;padding:10px 12px;margin-bottom:12px;">
            <div style="font-size:12px;font-weight:700;color:#d97706;margin-bottom:6px;">⚠ 赎回须知</div>
            <div style="font-size:10px;color:var(--dark-text2);line-height:1.7;">
              · 赎回申请当日（T 日）为本月最后工作日<br>
              · T+5 工作日内资金到账<br>
              · 赎回申请提交后不可撤销
            </div>
          </div>
          <div style="position:relative;">
            <div class="anno red" style="top:-3px;left:-3px;right:-3px;bottom:-3px;"><div class="anno-n red">3</div></div>
            <div style="background:rgba(246,70,93,.08);border:1px solid rgba(246,70,93,.2);border-radius:8px;padding:10px 12px;">
              <div style="font-size:11px;font-weight:700;color:#F6465D;margin-bottom:4px;">大额赎回说明</div>
              <div style="font-size:10px;color:var(--dark-text2);line-height:1.6;">若本次赎回份额超过基金总份额的 10%，超出部分将顺延至下一开放日，按下一开放日净值结算</div>
            </div>
          </div>
        </div>
        <div style="padding:12px 16px;background:var(--dark2);">
          <div style="background:var(--blue);color:#fff;border-radius:10px;padding:12px;text-align:center;font-size:14px;font-weight:700;">我已了解，继续赎回</div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">赎回须知 · B4/B5 规则披露</div>
    </div>'''

    card = '''
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card">
        <div class="card-title">B-1 · 持仓列表 + 赎回入口 <span class="ann-tag new">NEW</span><span class="ann-tag p0">P0</span></div>
        <div class="ann-item"><div class="ann-num green">1</div><div class="ann-text"><b>持仓卡片</b><span class="ann-tag new">NEW</span><br>展示：持有份额 / 当前 NAV / 持仓市值 / 浮动盈亏（差额和百分比双展示）</div></div>
        <div class="ann-item"><div class="ann-num amber">2</div><div class="ann-text"><b>赎回按钮可见性</b><span class="ann-tag p0">B1</span><br>仅在开放日（每月最后工作日）展示「申请赎回」；非开放日显示「下次开放日：XX-XX-XX」</div></div>
        <div class="ann-item"><div class="ann-num red">3</div><div class="ann-text"><b>大额赎回预警</b><span class="ann-tag p0">B5</span><br>进入赎回前强制展示大额顺延说明，用户知情后方可继续</div></div>
        <div class="info-box green"><b>后台联动：</b>赎回申请提交后 → C-1 生成「待风控审核」赎回订单，需合规风控双签</div>
      </div>
    </div>'''

    return s1 + arr + s2 + card


def fill_b2():
    """Scene B-2 · 赎回下单（含大额顺延提示）· phone"""
    s1 = '''
    <div class="flow-col">
      <span class="phone-label">B-2 · 赎回下单</span>
      <div class="phone" style="display:flex;flex-direction:column;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top">
          <span style="font-size:14px;color:var(--dark-text3);">‹</span>
          <div style="flex:1;text-align:center;"><div class="ph-name">申请赎回</div></div>
          <div style="width:14px;"></div>
        </div>
        <div style="padding:14px 16px;flex:1;overflow:hidden;">
          <div style="font-size:12px;color:var(--dark-text2);margin-bottom:12px;">鑫远稳健一期 · 可赎回份额 7,788.08</div>
          <div style="font-size:11px;color:var(--dark-text3);margin-bottom:4px;">赎回份额</div>
          <div style="background:var(--dark2);border-radius:8px;padding:12px 14px;margin-bottom:6px;">
            <div style="font-size:20px;font-weight:800;color:var(--dark-text);font-family:'IBM Plex Mono',monospace;">5,000.00</div>
          </div>
          <div style="display:flex;gap:8px;margin-bottom:12px;">
            <div style="background:var(--dark2);border-radius:6px;padding:5px 10px;font-size:11px;color:var(--dark-text2);">25%</div>
            <div style="background:var(--dark2);border-radius:6px;padding:5px 10px;font-size:11px;color:var(--dark-text2);">50%</div>
            <div style="background:var(--blue);border-radius:6px;padding:5px 10px;font-size:11px;color:#fff;font-weight:700;">全部赎回</div>
          </div>
          <div style="position:relative;margin-bottom:10px;">
            <div class="anno amber" style="top:-3px;left:-3px;right:-3px;bottom:-3px;"><div class="anno-n amber">1</div></div>
            <div style="background:var(--dark2);border-radius:6px;padding:10px 12px;">
              <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;">
                <span style="color:var(--dark-text3);">预计赎回金额</span>
                <span style="color:var(--dark-text);font-family:'IBM Plex Mono',monospace;">¥6,421.50</span>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:11px;">
                <span style="color:var(--dark-text3);">预计到账日（T+5）</span>
                <span style="color:var(--dark-text2);">2026-05-08（工作日）</span>
              </div>
            </div>
          </div>
        </div>
        <div style="padding:12px 16px;background:var(--dark2);">
          <div style="background:#F6465D;color:#fff;border-radius:10px;padding:12px;text-align:center;font-size:14px;font-weight:700;">确认提交赎回</div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">正常赎回 · 份额 &lt; 10% 总份额</div>
    </div>'''

    arr = _aw("r", "份额 > 10% 触发")

    s2 = '''
    <div class="flow-col">
      <span class="phone-label">B-2 · 大额顺延弹窗</span>
      <div class="phone" style="display:flex;flex-direction:column;position:relative;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div style="flex:1;opacity:.3;background:var(--dark);"></div>
        <div style="position:absolute;top:80px;left:20px;right:20px;background:#1e2329;border-radius:12px;padding:16px;">
          <div style="font-size:14px;font-weight:800;color:var(--dark-text);margin-bottom:6px;">大额赎回顺延提醒</div>
          <div style="position:relative;margin-bottom:12px;">
            <div class="anno red" style="top:-3px;left:-3px;right:-3px;bottom:-3px;"><div class="anno-n red">2</div></div>
            <div style="background:rgba(246,70,93,.08);border-radius:6px;padding:10px;">
              <div style="font-size:11px;color:var(--dark-text2);line-height:1.7;">
                本次赎回 <b style="color:#F6465D;">7,788.08 份</b>，超出当前基金总份额的 10%（上限 350 份）。<br><br>
                超出部分 <b style="color:#F6465D;">7,438.08 份</b> 将顺延至下一开放日（2026-05-29）按当日净值结算。
              </div>
            </div>
          </div>
          <div style="display:flex;gap:8px;">
            <div style="flex:1;background:var(--dark2);border-radius:8px;padding:10px;text-align:center;font-size:13px;color:var(--dark-text2);">取消</div>
            <div style="flex:1;background:#F6465D;border-radius:8px;padding:10px;text-align:center;font-size:13px;font-weight:700;color:#fff;">知悉并确认</div>
          </div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">大额赎回 · 顺延规则强提示</div>
    </div>'''

    card = '''
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card">
        <div class="card-title">B-2 · 赎回下单 + 大额顺延 <span class="ann-tag new">NEW</span><span class="ann-tag p0">P0</span></div>
        <div class="ann-item"><div class="ann-num amber">1</div><div class="ann-text"><b>T+5 到账说明</b><span class="ann-tag p0">B4</span><br>实时展示预计到账日（跳过节假日计算），让投资者清楚预期</div></div>
        <div class="ann-item"><div class="ann-num red">2</div><div class="ann-text"><b>大额赎回顺延弹窗</b><span class="ann-tag p0">B5</span><br>超出 10% 阈值时强制弹出：展示可赎回份额 + 顺延份额 + 下次开放日，用户知情才可确认</div></div>
        <div class="info-box red"><b>合规约束：</b>顺延份额按下一开放日净值（非申请日净值）结算，可能不利于投资者，必须醒目提示</div>
      </div>
    </div>'''

    return s1 + arr + s2 + card
