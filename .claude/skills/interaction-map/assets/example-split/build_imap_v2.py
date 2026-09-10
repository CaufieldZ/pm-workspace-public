#!/usr/bin/env python3
"""proj-community-leaderboard 交互大图 v2 — build 模式（单步生成）

主场景粒度对齐 scene-list.md（A/B/C/D/E/F/G 共 7 个），子场景作为手机节点放入对应主场景内。
PART X 跨端数据流表（9 项社区 × 牛人榜 × App 全局衔接）通过 scene_fns['cross-data-flow'] 注入。

改内容只改 scenes_*.py 的 fill_X 函数体，重跑本脚本即可。
"""
import os
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _DIR)

_ROOT = os.path.abspath(os.path.join(_DIR, '../../../..'))
sys.path.insert(0, os.path.join(_ROOT, '.claude/skills/interaction-map/scripts'))

from build_imap_skeleton import generate
from imap_v2.scenes_a import fill_a
from imap_v2.scenes_b import fill_b
from imap_v2.scenes_c import fill_c
from imap_v2.scenes_d import fill_d
from imap_v2.scenes_e import fill_e
from imap_v2.scenes_f import fill_f
from imap_v2.scenes_g import fill_g

OUTPUT = os.path.join(_DIR, '../deliverables/imap-proj-community-leaderboard-v2.html')

project = {
    'name': '示例社区 × 牛人榜打通',
    'subtitle': '交互大图 v2.0 · 社区侧',
    'nav_desc': 'Feed 入口 → 个人主页核心 → 订阅闭环 → 自己侧管理 → 资源位 ｜ 跨团队衔接已标注',
}

legends = [
    {'color': 'blue',   'label': '布局 / 导航'},
    {'color': 'green',  'label': '正向操作 / 订阅链路'},
    {'color': 'red',    'label': '权限 / 隐私状态'},
    {'color': 'purple', 'label': '牛人榜组件嵌入'},
    {'color': 'amber',  'label': '跨端 / 跨团队衔接'},
]

parts = [
    {
        'id': 'part0', 'num': 'PART 0', 'name': '入口与触达',
        'desc': 'A · Feed 流牛人榜卡片是核心 KPI 漏斗的第一站；用户从这里第一次被勾到牛人榜内容',
        'story': '用户刷 Feed 时被推荐的牛人战绩吸引，点进去看',
        'theme': 'cross-end', 'dot_color': 'amber',
        'scenes': [
            {'id': 'A', 'name': 'Feed 流牛人榜推荐',
             'trigger': 'feed 流浏览 ≥ 5 条触发首张曝光（行为触发）', 'device': 'phone'},
        ],
    },
    {
        'id': 'part1', 'num': 'PART 1', 'name': '核心承载 · 个人主页',
        'desc': '用户从 Feed / IM / 搜索 / 牛人榜列表落到主页；B 讲视角差异，C 讲 TAB 状态全集',
        'story': '用户落到主页，看到对方的内容、战绩、带单全貌',
        'theme': 'frontend', 'dot_color': 'blue',
        'scenes': [
            {'id': 'B', 'name': '个人主页 - 视角差异',
             'trigger': '我的 / 帖子作者 / 牛人榜 / IM / 搜索 / 分享链接', 'device': 'phone'},
            {'id': 'C', 'name': '个人主页 - TAB 状态全集',
             'trigger': 'B 内切换 TAB（含公开 / 私密权限态分支）', 'device': 'phone'},
        ],
    },
    {
        'id': 'part2', 'num': 'PART 2', 'name': '关键转化 · 订阅闭环（含跨团队）',
        'desc': '社区侧订阅入口（header 订阅数 + 战绩组件 sticky CTA），叠加牛人榜列表反向跳社区主页',
        'story': '用户被战绩吸引，点订阅；牛人榜列表反向引流回社区',
        'theme': 'cross-end', 'dot_color': 'green',
        'scenes': [
            {'id': 'D', 'name': '订阅链路（含跨团队 · 牛人榜列表反向跳社区）',
             'trigger': 'header 订阅数 / 战绩组件订阅 CTA / 牛人榜列表反向跳', 'device': 'phone'},
        ],
    },
    {
        'id': 'part3', 'num': 'PART 3', 'name': '自己侧管理 · 资料 / 设置 / 分享',
        'desc': 'E · 编辑资料 + 交易战绩管理；F · 分享菜单（社区自做主页卡 vs 调牛人榜 3 卡）',
        'story': '用户管理自己的资料、战绩公开度，把主页分享给朋友',
        'theme': 'frontend', 'dot_color': 'purple',
        'scenes': [
            {'id': 'E', 'name': '资料与设置',
             'trigger': '自己主页点 [编辑资料] · 战绩未公开提示条点「设置为公开模式」超链接', 'device': 'phone'},
            {'id': 'F', 'name': '分享菜单与卡片',
             'trigger': '自己主页 / 他人主页点 ⤴️', 'device': 'phone'},
        ],
    },
    {
        'id': 'part4', 'num': 'PART 4', 'name': '资源位 · 申请交易员 Banner',
        'desc': 'G · 位置归社区 / 内容运营 CMS 投放（本期只占位）',
        'story': '运营在自己主页的 header 下方投放申请交易员入口',
        'theme': 'frontend', 'dot_color': 'red',
        'scenes': [
            {'id': 'G', 'name': '申请交易员 Banner 位',
             'trigger': '自己主页 header 下方', 'device': 'phone'},
        ],
    },
    {
        'id': 'part-cross', 'num': 'PART X', 'name': '跨端数据流全集（社区 × 牛人榜 × App 全局）',
        'desc': '9 项跨端衔接 · 评审依据 · 接口契约对齐表',
        'story': '—',
        'theme': 'cross-end', 'dot_color': 'amber',
        'scenes': [],
        'cross_table': True,
    },
]


def cross_data_flow():
    """PART X 跨端数据流表 — 9 行衔接清单 + 接口契约对齐"""
    return '''
<div style="max-width:1200px;margin:0 auto 60px;background:#fff;border-radius:14px;padding:20px 24px;box-shadow:0 4px 24px rgba(0,0,0,0.06);">
  <div style="display:grid;grid-template-columns:36px 200px 60px 220px 1fr 200px;gap:8px;padding:10px 12px;background:#0B0E11;color:#fff;border-radius:8px;font-size:12px;font-weight:900;margin-bottom:6px;">
    <span>#</span><span>起点</span><span style="text-align:center;">→</span><span>终点</span><span>数据 / 接口</span><span>触发方式</span>
  </div>
  <div style="display:grid;grid-template-columns:36px 200px 60px 220px 1fr 200px;gap:8px;padding:10px 12px;font-size:12px;border-bottom:1px solid #f0f0f0;align-items:center;">
    <span style="font-weight:900;color:#d97706;">1</span><span><a href="#scene-a" style="color:#1f2937;text-decoration:none;font-weight:700;">A-1 · Feed 卡片露出</a></span><span style="text-align:center;color:#d97706;">→</span><span>牛人榜推荐池 API</span><span>30d 收益率 Top 30 ∪ 30d 订阅增量 Top 30，排除已订阅；池内随机 + 持仓币种匹配优先</span><span style="color:#5E6673;">浏览 ≥ 5 条 feed 自动触发</span>
  </div>
  <div style="display:grid;grid-template-columns:36px 200px 60px 220px 1fr 200px;gap:8px;padding:10px 12px;font-size:12px;border-bottom:1px solid #f0f0f0;align-items:center;background:#fafbfc;">
    <span style="font-weight:900;color:#d97706;">2</span><span><a href="#scene-a" style="color:#1f2937;text-decoration:none;font-weight:700;">A-2 · 卡片点击</a></span><span style="text-align:center;color:#d97706;">→</span><span><a href="#scene-b" style="color:#1f2937;text-decoration:none;">B-2 · 别人主页</a>（社区内）</span><span>主页进入埋点扩 source=feed_topTrader 属性</span><span style="color:#5E6673;">用户点击卡片</span>
  </div>
  <div style="display:grid;grid-template-columns:36px 200px 60px 220px 1fr 200px;gap:8px;padding:10px 12px;font-size:12px;border-bottom:1px solid #f0f0f0;align-items:center;">
    <span style="font-weight:900;color:#8b5cf6;">3</span><span><a href="#scene-c" style="color:#1f2937;text-decoration:none;font-weight:700;">C-3 · C-4 · 战绩 TAB</a></span><span style="text-align:center;color:#8b5cf6;">嵌入</span><span>牛人榜战绩组件</span><span>H5 嵌入 / 组件化（技术决策待研发对齐）· 累计收益率 / 总盈亏 / 胜率 / 回撤 / 跟单人数 / 带单规模</span><span style="color:#5E6673;">TAB 切换</span>
  </div>
  <div style="display:grid;grid-template-columns:36px 200px 60px 220px 1fr 200px;gap:8px;padding:10px 12px;font-size:12px;border-bottom:1px solid #f0f0f0;align-items:center;background:#fafbfc;">
    <span style="font-weight:900;color:#0ECB81;">4</span><span><a href="#scene-d" style="color:#1f2937;text-decoration:none;font-weight:700;">D-1 · header「订阅 K」</a></span><span style="text-align:center;color:#0ECB81;">→</span><span>牛人榜「我的订阅」页</span><span>路由跳转 · 社区不维护订阅列表</span><span style="color:#5E6673;">用户点击（仅自己可见）</span>
  </div>
  <div style="display:grid;grid-template-columns:36px 200px 60px 220px 1fr 200px;gap:8px;padding:10px 12px;font-size:12px;border-bottom:1px solid #f0f0f0;align-items:center;">
    <span style="font-weight:900;color:#0ECB81;">5</span><span><a href="#scene-d" style="color:#1f2937;text-decoration:none;font-weight:700;">D-2 · sticky 订阅按钮</a></span><span style="text-align:center;color:#0ECB81;">→</span><span>牛人榜订阅 API</span><span>UI 归社区，行为调牛人榜接口 · 入参 user_id · 出参 success/fail · 订阅事件归牛人榜</span><span style="color:#5E6673;">用户点击 sticky CTA</span>
  </div>
  <div style="display:grid;grid-template-columns:36px 200px 60px 220px 1fr 200px;gap:8px;padding:10px 12px;font-size:12px;border-bottom:1px solid #f0f0f0;align-items:center;background:#fafbfc;">
    <span style="font-weight:900;color:#d97706;">6</span><span><a href="#scene-d" style="color:#1f2937;text-decoration:none;font-weight:700;">D-3 · 牛人榜列表行</a></span><span style="text-align:center;color:#d97706;">→</span><span><a href="#scene-b" style="color:#1f2937;text-decoration:none;">B-2 · 社区主页</a></span><span>路由跳转 + user_id · source=leaderboard 埋点 · <b>牛人榜侧改造</b>，原详情页下线</span><span style="color:#5E6673;">用户在牛人榜列表点交易员</span>
  </div>
  <div style="display:grid;grid-template-columns:36px 200px 60px 220px 1fr 200px;gap:8px;padding:10px 12px;font-size:12px;border-bottom:1px solid #f0f0f0;align-items:center;">
    <span style="font-weight:900;color:#8b5cf6;">7</span><span><a href="#scene-f" style="color:#1f2937;text-decoration:none;font-weight:700;">F-3 · 分享 3 卡</a></span><span style="text-align:center;color:#8b5cf6;">×3 接口</span><span>牛人榜分享接口</span><span>分享交易战绩 / 合约带单 / 现货带单 · 接口契约待 04-28 对齐 · UI 由牛人榜出</span><span style="color:#5E6673;">用户点击 <a href="#scene-f" style="color:#1f2937;">F-1 · 分享菜单</a> 3 选项之一</span>
  </div>
  <div style="display:grid;grid-template-columns:36px 200px 60px 220px 1fr 200px;gap:8px;padding:10px 12px;font-size:12px;border-bottom:1px solid #f0f0f0;align-items:center;background:#fafbfc;">
    <span style="font-weight:900;color:#d97706;">8</span><span><a href="#scene-g" style="color:#1f2937;text-decoration:none;font-weight:700;">G-1 · Banner 点击</a></span><span style="text-align:center;color:#d97706;">→</span><span>牛人榜申请交易员页</span><span>路由跳转 · 内容由广告资源运营 CMS 投放 · 跨端漏斗终点</span><span style="color:#5E6673;">用户点击 Banner</span>
  </div>
  <div style="display:grid;grid-template-columns:36px 200px 60px 220px 1fr 200px;gap:8px;padding:10px 12px;font-size:12px;border-bottom:1px solid #f0f0f0;align-items:center;">
    <span style="font-weight:900;color:#F6465D;">9</span><span>订阅交易员开 / 平仓 推送</span><span style="text-align:center;color:#F6465D;">→</span><span>App 全局通知中心</span><span>事件归牛人榜实现 · 通知偏好归 App 全局 · 社区只做跳转入口</span><span style="color:#5E6673;">订阅事件触发（被动）</span>
  </div>
  <div style="margin-top:14px;padding:12px 14px;background:linear-gradient(135deg,rgba(43,127,255,0.08),rgba(43,127,255,0.02));border-radius:8px;border:1px solid rgba(43,127,255,0.2);">
    <div style="font-size:13px;font-weight:900;color:#1f2937;margin-bottom:6px;">📋 接口契约对齐清单（04-28 对齐）</div>
    <div style="font-size:11px;color:#374151;line-height:1.7;">
      1. 牛人榜推荐池 API（#1）：字段 / 入参时间窗 / 排除规则 · 2. 战绩组件嵌入方式（#3）：H5 vs 组件化 · 3. 订阅 API（#5）：入参 / 出参 / 失败降级 · 4. 4 个分享接口（#7）：UI 规范 + 调用方式 · 5. 反向跳转 source 埋点对齐（#6）
    </div>
  </div>
</div>
'''


scene_fns = {
    'scene-a': fill_a,
    'scene-b': fill_b,
    'scene-c': fill_c,
    'scene-d': fill_d,
    'scene-e': fill_e,
    'scene-f': fill_f,
    'scene-g': fill_g,
    'cross-data-flow': cross_data_flow,
}


if __name__ == '__main__':
    generate(project, legends, parts, scene_fns, OUTPUT)
