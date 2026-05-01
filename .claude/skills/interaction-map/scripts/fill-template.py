# fill 脚本模板 — 仅在编写 fill 脚本时参考
# 公共工具在 scripts/fill_utils.py，fill 脚本只需写 Scene 内容函数。
#
# 契约：骨架只提供空 .flow 容器 + 单个 FILL 标记，
#       fill 函数负责生成全部内容（设备壳 + 屏幕 + 箭头 + 注释卡）。
#       设备类型由 Scene 的 device 字段决定（不是 PART 的 theme）：
#         device="phone" → .phone 壳（375px 深色，App 端）
#         device="web"   → .webframe 壳（720px+ 浅色，Web 前台或后台）
#       同一个前台 PART 下可以同时有 phone 和 web Scene。
#
# ⚠️ 反模式警告（必读）：
# ❌ BAD: 只写 ann-card + ann-num，不写 card-title / ann-item / ann-text 子结构 → 产出扁平无层次
# ❌ BAD: 不写 .anno 虚线标注框 → 读者不知道注释对应屏幕哪个区域
# ❌ BAD: 不写 .ann-tag (p0/p1/p2) → 无法区分优先级。注意 .ann-tag.new/chg/del 已退役，见 interaction-map SKILL.md L58
# ❌ BAD: 不写 .info-box → 缺少补充说明和备注信息
# ❌ BAD: 不写 .aw 箭头 → 屏幕间无流向关系
# ❌ BAD: 不写 .flow-note → 屏幕缺少状态说明
# ✅ GOOD: 每个 Scene 必须包含: 屏幕(.phone/.webframe) + 箭头(.aw) + 标注(.anno)
#          + 注释卡(.ann-card 含 .card-title + .ann-item > .ann-text + .ann-tag) + 说明(.flow-note)
#          + 至少每 PART 1 个 .info-box

# ────────────────────────────────────────────────────
# 基础模板（Scene ≤ 6）
# ────────────────────────────────────────────────────
#!/usr/bin/env python3
import os, sys
_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_DIR, '../../..')
sys.path.insert(0, os.path.join(_ROOT, 'scripts'))
from fill_utils import run_fill

TARGET = os.path.join(_DIR, '../deliverables/imap-xxx-v1.html')


# ── 前台 Scene（phone 壳）──────────────────────────
def fill_a():
    """Scene A · 首页 — device=phone，使用 .phone 壳"""
    return '''
    <!-- ─── 屏幕 1 ─── -->
    <div class="flow-col">
      <span class="phone-label">A · 首页</span>
      <div class="phone" style="min-height:660px;display:flex;flex-direction:column;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top">
          <span style="font-size:14px;color:var(--dark-text3);">‹</span>
          <div style="flex:1;text-align:center;">
            <div class="ph-name">首页</div>
          </div>
          <div style="width:14px;"></div>
        </div>
        <div style="padding:16px 18px;flex:1;overflow:hidden;">
          <!-- 实际页面内容 -->
          <!-- ─── 标注框：包裹需要标注的 UI 元素 ─── -->
          <div style="position:relative;margin-top:12px;">
            <div class="anno amber" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n amber">①</div></div>
            <div style="background:var(--blue);border-radius:10px;padding:14px;text-align:center;">
              <div style="font-size:14px;font-weight:800;color:#fff;">核心操作按钮</div>
              <div style="font-size:10px;color:rgba(255,255,255,.6);margin-top:2px;">按钮说明文字</div>
            </div>
          </div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">默认状态</div>
    </div>

    <!-- ─── 箭头 ─── -->
    <div class="aw">
      <div class="al a"></div>
      <div class="tx a">点击某项</div>
    </div>

    <!-- ─── 屏幕 2 ─── -->
    <div class="flow-col">
      <span class="phone-label">A · 首页（详情态）</span>
      <div class="phone" style="min-height:660px;display:flex;flex-direction:column;">
        <div class="ph-status"><span>9:41</span><span>⚡ 📶 ■■■</span></div>
        <div class="ph-top">
          <span style="font-size:14px;color:var(--dark-text3);">‹</span>
          <div style="flex:1;text-align:center;">
            <div class="ph-name">详情</div>
          </div>
          <div style="width:14px;"></div>
        </div>
        <div style="padding:16px 18px;flex:1;overflow:hidden;">
          <!-- 实际页面内容 -->
          <div style="position:relative;margin-top:12px;">
            <div class="anno green" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n green">②</div></div>
            <div style="background:var(--dark2);border-radius:8px;padding:12px;">
              <div style="font-size:13px;font-weight:700;color:var(--dark-text);">详情内容区</div>
            </div>
          </div>
        </div>
        <div class="home-ind"><div></div></div>
      </div>
      <div class="flow-note">详情态</div>
    </div>

    <!-- ─── 注释卡（纵向容器） ─── -->
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card">
        <div class="card-title">📋 A · 首页 说明 <span class="ann-tag p0">P0</span></div>
        <div class="ann-item"><div class="ann-num amber">①</div><div class="ann-text"><b>核心操作按钮</b><br>按钮文案和样式调整，增加副标题说明</div></div>
        <div class="ann-item"><div class="ann-num green">②</div><div class="ann-text"><b>详情内容区</b><br>新增详情展示模块，支持下拉刷新</div></div>
        <div class="info-box blue"><b>备注：</b>首页改动需同步更新缓存策略，详见后端接口文档</div>
      </div>
    </div>
'''


# ── 后台 Scene（webframe 壳）──────────────────────────
def fill_m1():
    """Scene M-1 · 配置管理 — device=web，使用 .webframe 壳"""
    return '''
    <!-- ─── 屏幕 1 ─── -->
    <div class="flow-col">
      <span class="phone-label">M-1 · 配置管理</span>
      <div class="webframe" style="width:720px;min-height:480px;">
        <div class="wf-bar">
          <div class="wf-dots"><i></i><i></i><i></i></div>
          <div class="wf-url">admin.example.com/config</div>
        </div>
        <div class="webframe-body" style="padding:20px;">
          <!-- 实际后台内容 -->
          <!-- ─── 标注框：包裹需要标注的 UI 元素 ─── -->
          <div style="position:relative;margin-top:12px;">
            <div class="anno blue" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n blue">①</div></div>
            <div style="background:#f2f3f5;border-radius:6px;padding:12px;">
              <div style="font-size:13px;font-weight:700;color:#1d2129;">配置列表区域</div>
            </div>
          </div>
        </div>
      </div>
      <div class="flow-note">列表态</div>
    </div>

    <!-- ─── 箭头 ─── -->
    <div class="aw">
      <div class="al a"></div>
      <div class="tx a">点击编辑</div>
    </div>

    <!-- ─── 屏幕 2 ─── -->
    <div class="flow-col">
      <span class="phone-label">M-1 · 配置管理（编辑态）</span>
      <div class="webframe" style="width:720px;min-height:480px;">
        <div class="wf-bar">
          <div class="wf-dots"><i></i><i></i><i></i></div>
          <div class="wf-url">admin.example.com/config/edit</div>
        </div>
        <div class="webframe-body" style="padding:20px;">
          <!-- 实际后台内容 -->
          <div style="position:relative;margin-top:12px;">
            <div class="anno green" style="top:-4px;left:-4px;right:-4px;bottom:-4px;"><div class="anno-n green">②</div></div>
            <div style="background:#f2f3f5;border-radius:6px;padding:12px;">
              <div style="font-size:13px;font-weight:700;color:#1d2129;">编辑表单区域</div>
            </div>
          </div>
        </div>
      </div>
      <div class="flow-note">编辑态</div>
    </div>

    <!-- ─── 注释卡（纵向容器） ─── -->
    <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
      <div class="ann-card">
        <div class="card-title">📋 M-1 · 配置管理 说明 <span class="ann-tag p1">P1</span></div>
        <div class="ann-item"><div class="ann-num blue">①</div><div class="ann-text"><b>配置列表</b><br>列表增加排序和筛选功能</div></div>
        <div class="ann-item"><div class="ann-num green">②</div><div class="ann-text"><b>编辑表单</b><br>新增批量编辑模式，支持多行同时修改</div></div>
        <div class="info-box amber"><b>注意：</b>批量编辑需后端支持事务性保存，失败时整体回滚</div>
      </div>
    </div>
'''


run_fill(TARGET, [
    ('scene-a', fill_a),
    ('scene-m-1', fill_m1),
])


# ────────────────────────────────────────────────────
# 大项目拆分模板（Scene > 6 时）
# ────────────────────────────────────────────────────
#
# 主脚本: fill_imap_v1.py（< 50 行，只做 import + run_fill）
# ──────────────────────────────
# import os, sys
# _DIR = os.path.dirname(os.path.abspath(__file__))
# _ROOT = os.path.join(_DIR, '../../..')
# sys.path.insert(0, os.path.join(_ROOT, 'scripts'))
# from fill_utils import run_fill
#
# TARGET = os.path.join(_DIR, '../deliverables/imap-xxx-v1.html')
#
# # 按 PART 拆分的 Scene 函数（每文件 ≤ 150 行）
# from scenes_part0 import fill_a, fill_a1, fill_b
# from scenes_part1 import fill_m1, fill_m2
#
# run_fill(TARGET, [
#     ('scene-a',   fill_a),
#     ('scene-a-1', fill_a1),
#     ('scene-b',   fill_b),
#     ('scene-m-1', fill_m1),
#     ('scene-m-2', fill_m2),
# ])
#
# 数据文件: scenes_part0.py（前台，≤ 150 行，全部用 .phone 壳）
# ──────────────────────────────
# def fill_a():
#     """Scene A · 首页 — 前台 phone"""
#     return '''
#     <div class="flow-col">
#       <span class="phone-label">A · 首页</span>
#       <div class="phone" style="min-height:660px;...">
#         ...（每个函数 ≤ 80 行 HTML）...
#       </div>
#     </div>
#     <div class="aw">...</div>
#     <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0;">
#       <div class="ann-card">...</div>
#     </div>
#     '''
#
# def fill_a1():
#     """Scene A-1 · 列表页 — 前台 phone"""
#     return '''...'''
#
# 数据文件: scenes_part1.py（后台，≤ 150 行，全部用 .webframe 壳）
# ──────────────────────────────
# def fill_m1():
#     """Scene M-1 · 配置管理 — 后台 webframe"""
#     return '''...'''
