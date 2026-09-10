/* ═══════════════════════════════════════════════════════════════════════════
   crypto-dark · 组件层交互函数

   与 crypto-dark.css 配套，由 build_proto_skeleton 按 project['css_packs'] 一起拼入。
   骨架内置的 switchTab 绑的是 .p-tab + 固定的 ongoing/upcoming/ended 面板 id，
   形状对不上 cx- 组件，故本层自带一套。

   命名一律 cx 前缀，与骨架 / 项目函数不冲突。
   ═══════════════════════════════════════════════════════════════════════════ */

/* Tab 切换：同组 .cx-tab 里点谁谁 .on；面板 id 约定 {group}-{tab}
   用法 <div class="cx-tab" onclick="cxTab(this,'pos','hold')">持仓</div>
        <div id="pos-hold">...</div>
   不传 group 则只切 .on 不管面板（纯筛选场景）。 */
function cxTab(el, group, tab) {
  el.parentElement.querySelectorAll('.cx-tab').forEach(function (t) { t.classList.remove('on'); });
  el.classList.add('on');
  if (!group) return;
  var panes = document.querySelectorAll('[id^="' + group + '-"]');
  panes.forEach(function (p) { p.style.display = (p.id === group + '-' + tab) ? '' : 'none'; });
}

/* 胶囊筛选：同组 .cx-pill 单选 */
function cxPill(el) {
  el.parentElement.querySelectorAll('.cx-pill').forEach(function (p) { p.classList.remove('on'); });
  el.classList.add('on');
}

/* 列表行单选：同容器 .cx-row 里点谁谁 .on（左缘 accent 由 CSS 出） */
function cxRow(el) {
  el.parentElement.querySelectorAll('.cx-row').forEach(function (r) { r.classList.remove('on'); });
  el.classList.add('on');
}

/* 底部 sheet 开关：id 传 .cx-sheet 的 id，遮罩自动建/收，点遮罩关闭。
   手机壳内绝对定位，不脱出机框。 */
function cxSheet(id, show) {
  var sheet = document.getElementById(id);
  if (!sheet) return;
  var shell = sheet.closest('.app-mock, .phone, .web-front') || document.body;
  var scrim = shell.querySelector('.cx-scrim[data-for="' + id + '"]');
  if (show === false) {
    sheet.classList.remove('show');
    if (scrim) scrim.remove();
    return;
  }
  if (!scrim) {
    scrim = document.createElement('div');
    scrim.className = 'cx-scrim';
    scrim.setAttribute('data-for', id);
    scrim.onclick = function () { cxSheet(id, false); };
    sheet.parentElement.insertBefore(scrim, sheet);
  }
  sheet.classList.add('show');
}

/* 状态切换：叠类不换类，按钮宽度不跳变（.cx-btn.pri.done 由 CSS 承接）。
   再次点击回到初始态。 */
function cxToggle(el, onText, offText) {
  var on = el.dataset.cxOn === '1';
  el.dataset.cxOn = on ? '' : '1';
  el.classList.toggle('done', !on);
  if (onText) el.textContent = on ? (offText || el.dataset.cxOff || onText) : onText;
}

/* 轻提示：没有 toast 容器时自建，2s 后淡出 */
function cxToast(msg) {
  var t = document.querySelector('.cx-toast');
  if (!t) {
    t = document.createElement('div');
    t.className = 'cx-toast';
    t.style.cssText = 'position:fixed;left:50%;bottom:84px;transform:translateX(-50%);'
      + 'background:rgba(0,0,0,.88);color:#fff;padding:10px 20px;border-radius:10px;'
      + 'font-size:13px;z-index:900;opacity:0;transition:opacity .2s;pointer-events:none;';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  requestAnimationFrame(function () { t.style.opacity = '1'; });
  clearTimeout(t._cxTimer);
  t._cxTimer = setTimeout(function () { t.style.opacity = '0'; }, 2000);
}
