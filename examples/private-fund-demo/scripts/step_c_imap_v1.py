"""Step C: 插入跨端数据流表格 + 底部 Callout"""
import os

HTML = os.path.join(os.path.dirname(__file__), '../deliverables/imap-private-fund-v1.html')

CROSS_TABLE = '''
<!-- ═══ 跨端数据流表格 ═══ -->
<div style="padding:40px 60px 0;">
  <div style="background:#fff;border-radius:12px;padding:24px;box-shadow:0 2px 12px rgba(0,0,0,.06);max-width:960px;margin:0 auto;">
    <div style="font-size:15px;font-weight:800;color:#1d2129;margin-bottom:4px;">跨端数据流 · H5 投资人端 ↔ Web 运营后台</div>
    <div style="font-size:11px;color:#8c8c8c;margin-bottom:16px;">以下交互跨越两个产品端，需确保前后端接口对齐</div>
    <div style="display:grid;grid-template-columns:28px 1fr 40px 1fr 1fr 1fr;gap:0;border:1px solid #e8e8e8;border-radius:6px;overflow:hidden;font-size:12px;">
      <div style="background:#fafafa;padding:8px 10px;font-weight:600;color:#595959;">#</div>
      <div style="background:#fafafa;padding:8px 10px;font-weight:600;color:#595959;">起点（H5 投资人端）</div>
      <div style="background:#fafafa;padding:8px 10px;font-weight:600;color:#595959;text-align:center;">→</div>
      <div style="background:#fafafa;padding:8px 10px;font-weight:600;color:#595959;">终点（Web 运营后台）</div>
      <div style="background:#fafafa;padding:8px 10px;font-weight:600;color:#595959;">传递数据</div>
      <div style="background:#fafafa;padding:8px 10px;font-weight:600;color:#595959;">触发方式</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;color:#8c8c8c;">1</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;">A-2 签署认购协议</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;text-align:center;color:#1890FF;">→</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;">C-1 生成「待审核」认购订单</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;font-size:11px;color:#595959;">投资人 ID / 基金 ID / 认购金额 / 冷静期截止时间</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;"><span style="background:#fff7e6;color:#d97706;border-radius:3px;padding:2px 6px;font-size:10px;">用户提交</span></div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;color:#8c8c8c;">2</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;">A-2 冷静期内撤销认购</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;text-align:center;color:#F6465D;">→</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;">C-1 订单状态 → 已撤销</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;font-size:11px;color:#595959;">订单 ID / 撤销时间（需在冷静期内）</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;"><span style="background:#fff1f0;color:#F6465D;border-radius:3px;padding:2px 6px;font-size:10px;">用户主动</span></div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;color:#8c8c8c;">3</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;">B-2 确认赎回（知情大额顺延）</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;text-align:center;color:#1890FF;">→</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;">C-1 生成「待风控审核」赎回订单</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;font-size:11px;color:#595959;">赎回份额 / 是否大额 / 顺延份额（如有）</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;"><span style="background:#fff7e6;color:#d97706;border-radius:3px;padding:2px 6px;font-size:10px;">用户提交</span></div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;color:#8c8c8c;">4</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;">B-1 持仓市值展示</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;text-align:center;color:#52c41a;">←</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;">运营发布当日净值（NAV）</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;font-size:11px;color:#595959;">基金 ID / NAV / 净值日期（每月末 ≤17:00）</div>
      <div style="padding:8px 10px;border-top:1px solid #e8e8e8;"><span style="background:#f6ffed;color:#52c41a;border-radius:3px;padding:2px 6px;font-size:10px;">系统推送</span></div>
    </div>
  </div>
</div>
'''

CALLOUT = '''
<!-- ═══ 底部 Callout ═══ -->
<div style="padding:32px 60px 60px;">
  <div style="max-width:960px;margin:0 auto;display:flex;flex-direction:column;gap:10px;">
    <div class="co bl">📖 <b>阅读指引：</b>横向滚动查看各 Scene，场景间箭头表示页面跳转方向。标注编号（圆圈数字）与右侧注释卡对应。两个 PART 分别代表 H5 投资人端和 Web 运营后台。</div>
    <div class="co am">
      <b>优先级说明：</b>
      <span class="ann-tag p0">P0</span> 合规强制要求，必须上线 ·
      <span class="ann-tag new">NEW</span> v1.1 新增功能 ·
      <span class="ann-tag chg">改动</span> 在原有功能上调整 ·
      <b style="color:#d97706;font-size:11px;">R1-R5</b> 监管合规规则编号（详见 context.md §6）
    </div>
  </div>
</div>
'''

content = open(HTML).read()

# 幂等：如果已插入则跳过；否则在 </body> 前注入（跨端表 → Callout）
marker = '<!-- ═══ 跨端数据流表格 ═══ -->'
if marker in content:
    print('[skip] cross-table already present')
else:
    content = content.replace('</body>', CROSS_TABLE + CALLOUT + '</body>')
    open(HTML, 'w').write(content)
    print(f'[ok] step C inserted cross-table + callout → {HTML}')
