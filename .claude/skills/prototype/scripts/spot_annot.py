"""演示点位标注库 · 呼吸光圈 + 序号徽标 + 壳外图例 + 标注开关。

评审演示要高亮「本轮改动落点」时用。机制在这里（版本无关），数据在项目侧：
图例文案 SPOT_LEGEND、哪个元素挂 .spot 由项目定义。

用法（extra_css / extra_js 尾部拼接）：
    from spot_annot import SPOT_CSS, SPOT_JS

    EXTRA_CSS = r'''...''' + SPOT_CSS
    EXTRA_JS = r'''
      const SPOT_LEGEND = { <scene>: [[1,'relink','说明'], ...], ... };  // 项目数据
      ...项目 JS...
    ''' + SPOT_JS
    # 壳外说明元素建好后：spotLegendMount(noteEl)
    # 切场景时：renderSpotLegend(sceneId)

屏内挂法：目标元素加 class `spot ring spot-relink|spot-new [wide]` + data-spot="序号"。
PRD 截图前 document.body.classList.add('noannot') 关标注，截产品原貌。

依赖骨架 token：--accent（蓝）/ --gold（金）；徽标文字用深底色 #0B0E11，
默认适配深色原型，浅色壳需项目侧覆盖。
"""

SPOT_CSS = r'''
/* 演示点位标注：分享/改动点位呼吸光圈 + 序号徽标。屏内只放光圈与数字，文字一律
   走壳外图例；点「标注 关」整套隐藏，回到干净原型好截图。呼吸节奏 2.4s，
   与分享面板目标渠道的呼吸高亮同一套视觉语言。金 = 线上已有本轮改接，
   蓝 = 本轮新增。*/
.spot{position:relative;--spot-c:var(--accent);}
.spot-relink{--spot-c:var(--gold);}
.spot-new{--spot-c:var(--accent);}
.spot::before{content:attr(data-spot);position:absolute;top:-6px;left:-6px;z-index:6;
  width:14px;height:14px;border-radius:50%;background:var(--spot-c);color:#0B0E11;
  font-size:9px;font-weight:800;line-height:14px;text-align:center;pointer-events:none;}
.spot.ring::after{content:'';position:absolute;inset:-3px;border-radius:12px;
  pointer-events:none;animation:spotBreath 2.4s ease-in-out infinite;}
.spot.ring.wide::after{border-radius:19px;}
@keyframes spotBreath{
  0%,100%{box-shadow:0 0 0 1px var(--spot-c),0 0 0 0 var(--spot-c);opacity:.5;}
  55%{box-shadow:0 0 0 1px var(--spot-c),0 0 0 6px transparent;opacity:1;}
}
body.noannot .spot::before,body.noannot .spot.ring::after{display:none;}

/* 壳外图例 + 开关（挂在壳外说明区之后）*/
.spot-legend{margin-top:9px;max-width:380px;display:flex;flex-direction:column;gap:5px;}
.sl-row{display:flex;align-items:flex-start;gap:7px;font-size:10.5px;line-height:1.45;color:#9aa7b6;--spot-c:var(--accent);}
.sl-row.spot-relink{--spot-c:var(--gold);}
.sl-no{width:14px;height:14px;border-radius:50%;background:var(--spot-c);color:#0B0E11;
  font-size:9px;font-weight:800;line-height:14px;text-align:center;flex-shrink:0;}
.sl-none{font-size:10.5px;color:#6b7787;text-align:center;}
.spot-switch{margin-top:10px;font-size:10.5px;color:#8b98a8;border:1px solid #2B3139;
  border-radius:14px;padding:4px 13px;cursor:pointer;user-select:none;}
.spot-switch:hover{color:#EAECEF;border-color:#3C434D;}
body.noannot .spot-legend{display:none;}
'''

SPOT_JS = r'''
// ── 演示点位标注 · 壳外图例与开关（图例数据 SPOT_LEGEND 由项目侧定义）──
function renderSpotLegend(id){
  const box = document.getElementById('spotLegend'); if(!box) return;
  // 顶层 const 不挂 window，用 typeof 探测（项目侧 const SPOT_LEGEND 也能读到）
  const rows = (typeof SPOT_LEGEND !== 'undefined' && SPOT_LEGEND[id]) || [];
  box.innerHTML = rows.length
    ? rows.map(function(r){
        return '<div class="sl-row spot-'+r[1]+'"><span class="sl-no">'+r[0]+'</span>'+r[2]+'</div>';
      }).join('')
    : '<div class="sl-none">本场景无标注点位。</div>';
}
// 标注开关：关掉后屏内光圈徽标与壳外图例一并隐藏，可直接截干净原型图
function toggleSpots(){
  const off = document.body.classList.toggle('noannot');
  const sw = document.getElementById('spotSwitch');
  if(sw) sw.textContent = off ? '标注 关' : '标注 开';
}
function spotLegendMount(anchor){
  const legend = document.createElement('div');
  legend.className = 'spot-legend';
  legend.id = 'spotLegend';
  anchor.parentNode.insertBefore(legend, anchor.nextSibling);
  const sw = document.createElement('div');
  sw.className = 'spot-switch';
  sw.id = 'spotSwitch';
  sw.textContent = '标注 开';
  sw.onclick = toggleSpots;
  legend.parentNode.insertBefore(sw, legend.nextSibling);
}
'''
