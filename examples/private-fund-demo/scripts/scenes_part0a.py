# PM-Workspace | (c) 2026 CaufieldZ | Apache 2.0 + AI Training Restriction
# Scene A-1, A-2 · H5 投资人端 · 认购流程

def _phone_open(label):
    return f'''
    <div class="flow-col">
      <span class="phone-label">{label}</span>
      <div class="phone" style="display:flex;flex-direction:column;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>'''

def _phone_top(title):
    return f'''
        <div class="ph-top">
          <span style="font-size:14px;color:var(--dark-text3);">‹</span>
          <div style="flex:1;text-align:center;"><div class="ph-name">{title}</div></div>
          <div style="width:14px;"></div>
        </div>'''

def _phone_close():
    return '''
        <div class="home-ind"><div></div></div>
      </div>'''

def _aw(color, label):
    return f'''
    <div class="aw"><div class="al {color}"></div><div class="tx {color}">{label}</div></div>'''


def fill_a1():
    """Scene A-1 · 基金详情 + 认购下单 · phone"""
    s1 = _phone_open("A-1 · 基金详情") + _phone_top("基金详情") + '''
        <div style="padding:14px 16px;flex:1;overflow:hidden;">
          <div style="font-size:15px;font-weight:800;color:var(--dark-text);margin-bottom:4px;">鑫远稳健一期私募证券基金</div>
          <div style="display:flex;gap:6px;margin-bottom:12px;">
            <span style="background:rgba(41,121,255,.15);color:#2979FF;font-size:10px;padding:2px 6px;border-radius:4px;">私募证券 · R3</span>
          </div>
          <div style="position:relative;margin-bottom:10px;">
            <div class="anno blue" style="top:-3px;left:-3px;right:-3px;bottom:-3px;"><div class="anno-n blue">1</div></div>
            <div style="background:rgba(14,203,129,.1);border:1px solid rgba(14,203,129,.3);border-radius:6px;padding:8px 10px;">
              <span style="font-size:11px;color:#0ECB81;font-weight:600;">✓ 合格投资者已认证 · 风险等级 C3 匹配 R3</span>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;">
            <div style="background:var(--dark2);border-radius:6px;padding:8px 10px;">
              <div style="font-size:9px;color:var(--dark-text3);">单位净值 (NAV)</div>
              <div style="font-size:15px;font-weight:800;color:var(--dark-text);font-family:'IBM Plex Mono',monospace;">1.2843</div>
            </div>
            <div style="background:var(--dark2);border-radius:6px;padding:8px 10px;">
              <div style="font-size:9px;color:var(--dark-text3);">成立以来收益</div>
              <div style="font-size:15px;font-weight:800;color:#0ECB81;font-family:'IBM Plex Mono',monospace;">+28.43%</div>
            </div>
          </div>
          <div style="position:relative;margin-bottom:10px;">
            <div class="anno red" style="top:-3px;left:-3px;right:-3px;bottom:-3px;"><div class="anno-n red">2</div></div>
            <div style="background:var(--dark2);border-radius:6px;padding:8px 10px;font-size:11px;color:var(--dark-text2);">
              风险等级 R3 · 本产品可能存在本金亏损风险，请仔细阅读产品说明书
            </div>
          </div>
          <div style="font-size:10px;color:var(--dark-text3);">开放日：每月最后一个工作日</div>
        </div>
        <div style="padding:12px 16px;background:var(--dark2);">
          <div style="background:var(--blue);color:#fff;border-radius:10px;padding:12px;text-align:center;font-size:14px;font-weight:700;">立即认购</div>
        </div>''' + _phone_close() + '''
      <div class="flow-note">详情页 · QI 校验通过态</div>
    </div>'''

    arr = _aw("b", "点击「立即认购」")

    s2 = _phone_open("A-1 · 认购下单") + _phone_top("认购下单") + '''
        <div style="padding:14px 16px;flex:1;overflow:hidden;">
          <div style="font-size:12px;color:var(--dark-text2);margin-bottom:12px;">鑫远稳健一期 · NAV 1.2843</div>
          <div style="font-size:11px;color:var(--dark-text3);margin-bottom:4px;">认购金额（元）</div>
          <div style="position:relative;margin-bottom:4px;">
            <div class="anno amber" style="top:-3px;left:-3px;right:-3px;bottom:-3px;"><div class="anno-n amber">3</div></div>
            <div style="background:var(--dark2);border-radius:8px;padding:12px 14px;">
              <div style="font-size:20px;font-weight:800;color:var(--dark-text);font-family:'IBM Plex Mono',monospace;">1,000,000</div>
            </div>
          </div>
          <div style="font-size:10px;color:#d97706;margin-bottom:14px;">最低认购金额 ¥1,000,000（100万元）</div>
          <div style="background:var(--dark2);border-radius:6px;padding:10px 12px;margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;">
              <span style="color:var(--dark-text3);">认购费率</span><span style="color:var(--dark-text);">1.00%</span>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:11px;">
              <span style="color:var(--dark-text3);">预计获得份额</span>
              <span style="color:var(--dark-text);font-family:'IBM Plex Mono',monospace;">7,788.08 份</span>
            </div>
          </div>
        </div>
        <div style="padding:12px 16px;background:var(--dark2);">
          <div style="background:var(--blue);color:#fff;border-radius:10px;padding:12px;text-align:center;font-size:14px;font-weight:700;">下一步 · 签署协议</div>
        </div>''' + _phone_close() + '''
      <div class="flow-note">认购下单 · 金额输入态</div>
    </div>'''

    card = '''
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card">
        <div class="card-title">A-1 · 基金详情 + 认购下单 <span class="ann-tag new">NEW</span><span class="ann-tag p0">P0</span></div>
        <div class="ann-item"><div class="ann-num blue">1</div><div class="ann-text"><b>合格投资者校验</b><span class="ann-tag p0">R1</span><br>进入认购前校验 QI 状态 + 风险等级匹配（C ≥ R）；未通过则拦截并引导认证入口</div></div>
        <div class="ann-item"><div class="ann-num red">2</div><div class="ann-text"><b>风险披露</b><span class="ann-tag p0">R2</span><br>合规要求强制展示风险等级说明，用户须知晓亏损可能</div></div>
        <div class="ann-item"><div class="ann-num amber">3</div><div class="ann-text"><b>最低认购额校验</b><span class="ann-tag p0">R3</span><br>单笔认购 ≥ 100 万元（¥1,000,000），低于此值「下一步」按钮置灰，实时提示</div></div>
        <div class="info-box blue"><b>跳转说明：</b>点击「下一步 · 签署协议」→ A-2 认购协议签署页</div>
      </div>
    </div>'''

    return s1 + arr + s2 + card


def fill_a2():
    """Scene A-2 · 认购协议签署 + 冷静期提示 · phone"""
    s1 = _phone_open("A-2 · 协议签署") + _phone_top("认购协议") + '''
        <div style="padding:14px 16px;flex:1;overflow:hidden;">
          <div style="background:var(--dark2);border-radius:6px;padding:10px;height:200px;overflow:hidden;margin-bottom:12px;">
            <div style="font-size:10px;font-weight:700;color:var(--dark-text);margin-bottom:6px;">鑫远稳健一期私募证券投资基金认购协议</div>
            <div style="font-size:9px;color:var(--dark-text3);line-height:1.6;">第一条 基本信息……本基金由XX基金管理人依法设立……投资者应仔细阅读本协议……</div>
          </div>
          <div style="position:relative;margin-bottom:10px;">
            <div class="anno green" style="top:-3px;left:-3px;right:-3px;bottom:-3px;"><div class="anno-n green">1</div></div>
            <div style="display:flex;align-items:flex-start;gap:8px;padding:8px 10px;background:var(--dark2);border-radius:6px;">
              <div style="width:14px;height:14px;border:2px solid var(--blue);border-radius:3px;flex-shrink:0;background:var(--blue);margin-top:1px;"></div>
              <div style="font-size:11px;color:var(--dark-text2);">我已阅读并同意《认购协议》《风险揭示书》《回访确认书》</div>
            </div>
          </div>
          <div style="position:relative;">
            <div class="anno amber" style="top:-3px;left:-3px;right:-3px;bottom:-3px;"><div class="anno-n amber">2</div></div>
            <div style="background:rgba(217,119,6,.1);border:1px solid rgba(217,119,6,.3);border-radius:6px;padding:8px 10px;">
              <div style="font-size:11px;font-weight:700;color:#d97706;margin-bottom:2px;">⚠ 冷静期提醒</div>
              <div style="font-size:10px;color:var(--dark-text2);">签署后 24 小时内可无条件撤销本次认购，资金原路退回，不收取任何费用</div>
            </div>
          </div>
        </div>
        <div style="padding:12px 16px;background:var(--dark2);">
          <div style="background:var(--blue);color:#fff;border-radius:10px;padding:12px;text-align:center;font-size:14px;font-weight:700;">确认签署</div>
        </div>''' + _phone_close() + '''
      <div class="flow-note">协议签署 · 勾选同意 + 冷静期提示</div>
    </div>'''

    arr = _aw("g", "签署成功")

    s2 = _phone_open("A-2 · 认购成功") + _phone_top("认购成功") + '''
        <div style="padding:24px 16px;flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;">
          <div style="font-size:40px;margin-bottom:12px;">✅</div>
          <div style="font-size:16px;font-weight:800;color:var(--dark-text);margin-bottom:4px;">认购申请已提交</div>
          <div style="font-size:11px;color:var(--dark-text3);margin-bottom:16px;text-align:center;">订单号：SUB-20260418-0001</div>
          <div style="position:relative;width:100%;">
            <div class="anno amber" style="top:-3px;left:-3px;right:-3px;bottom:-3px;"><div class="anno-n amber">3</div></div>
            <div style="background:var(--dark2);border-radius:6px;padding:10px 12px;">
              <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:4px;">
                <span style="color:var(--dark-text3);">冷静期截止</span>
                <span style="color:#d97706;font-weight:600;">2026-04-19 14:32</span>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:11px;">
                <span style="color:var(--dark-text3);">基金成立确认</span>
                <span style="color:var(--dark-text2);">募集期结束后</span>
              </div>
            </div>
          </div>
          <div style="margin-top:16px;font-size:11px;color:var(--dark-text3);text-align:center;">冷静期内可前往「我的 → 订单」撤销认购</div>
        </div>''' + _phone_close() + '''
      <div class="flow-note">认购成功 · 冷静期倒计时</div>
    </div>'''

    card = '''
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card">
        <div class="card-title">A-2 · 协议签署 + 冷静期 <span class="ann-tag new">NEW</span><span class="ann-tag p0">P0</span></div>
        <div class="ann-item"><div class="ann-num green">1</div><div class="ann-text"><b>三书签署</b><span class="ann-tag p0">R5</span><br>认购协议 + 风险揭示书 + 回访确认书，三者全勾选才可提交（替代「双录」合规要求）</div></div>
        <div class="ann-item"><div class="ann-num amber">2</div><div class="ann-text"><b>冷静期强制展示</b><span class="ann-tag p0">R4</span><br>签署前页面必须展示 24h 冷静期说明，不可折叠或隐藏</div></div>
        <div class="ann-item"><div class="ann-num amber">3</div><div class="ann-text"><b>冷静期截止时间</b><span class="ann-tag new">NEW</span><br>成功页展示精确截止时间戳 + 撤销入口（→ 我的订单）；超过截止时间后撤销按钮消失</div></div>
        <div class="info-box amber"><b>跨端：</b>认购提交后 → 运营后台 C-1 生成「待审核」订单，运营人员在 T+1 确认份额</div>
      </div>
    </div>'''

    return s1 + arr + s2 + card
