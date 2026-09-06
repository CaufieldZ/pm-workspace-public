// ============================================================
// PRESENTER MODE — Doc ⇄ Deck 双模式
// P：Doc / Deck 切换；ESC：退 Deck 回 Doc
// →/Space/PageDown：下一步（先显 data-step，再翻页）
// ←/PageUp：上一步（先退 data-step，再退页）
// Home/End：首页 / 末页
// 滚轮 throttle 800ms 翻页；触屏左右滑 50px 翻页
// URL hash #deck:{pageId} 进入 deck 直达
// ============================================================

(function() {

let mode = 'doc';        // 'doc' | 'deck'
let deckIdx = 0;
let currentStep = 0;
let pageOrder = [];      // [{id, label, kicker, groupLabel, footTitle, footRight}, ...]
let lastWheelTime = 0;
let touchStartX = 0;

function escHtml(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function flatPageOrder() {
  const out = [];
  if (typeof NAV === 'undefined') return out;
  NAV.forEach(g => g.items.forEach(i => out.push(i)));
  return out;
}

// ---- 构建 deck-track（首次进 Deck 时调用，只建一次） ----
function buildDeckTrack() {
  const track = document.getElementById('deck-track');
  if (!track || track.dataset.built) return;
  pageOrder = flatPageOrder();
  const total = pageOrder.length;

  track.innerHTML = pageOrder.map((item, idx) => {
    const fn = (typeof PAGE_RENDERERS !== 'undefined') ? PAGE_RENDERERS[item.id] : null;
    let bodyHtml = '';
    if (typeof fn === 'function') {
      const stub = document.createElement('div');
      try { fn(stub); bodyHtml = stub.innerHTML; }
      catch (e) { console.warn('[deck] render fail:', item.id, e); }
    }

    const hasChrome = item.kicker || item.groupLabel;
    const chrome = hasChrome ? `
      <div class="deck-chrome">
        <span class="chrome-l">${escHtml(item.groupLabel || '')}</span>
        <span class="chrome-r">${escHtml(item.kicker || '')}${item.kicker ? ' · ' : ''}${String(idx + 1).padStart(2, '0')} / ${String(total).padStart(2, '0')}</span>
      </div>` : '';

    const hasFoot = item.footTitle || item.footRight;
    const foot = hasFoot ? `
      <div class="deck-foot">
        <span class="foot-l">${escHtml(item.footTitle || '')}</span>
        <span class="foot-r">${escHtml(item.footRight || '')}</span>
      </div>` : '';

    return `<section class="deck-page" data-deck-idx="${idx}" data-page-id="${item.id}">
      ${chrome}
      <div class="deck-page-body">${bodyHtml}</div>
      ${foot}
    </section>`;
  }).join('');

  track.dataset.built = '1';
}

// ---- 构建底部圆点导航 ----
function buildDeckNav() {
  const nav = document.getElementById('deck-nav');
  if (!nav || nav.dataset.built) return;
  nav.innerHTML = pageOrder.map((it, idx) =>
    `<span class="deck-dot" data-idx="${idx}" title="${escHtml(it.label || '')}"></span>`
  ).join('');
  nav.querySelectorAll('.deck-dot').forEach(d => {
    d.addEventListener('click', () => jumpToPage(+d.dataset.idx));
  });
  nav.dataset.built = '1';
}

function applyDeckOffset() {
  const track = document.getElementById('deck-track');
  if (track) track.style.setProperty('--deck-offset', `-${deckIdx * 100}vw`);
  document.querySelectorAll('#deck-nav .deck-dot').forEach((d, i) => {
    d.classList.toggle('active', i === deckIdx);
  });
  updateHUD();
  updateHash();
}

function getStepsForCurrentDeck() {
  const page = document.querySelector(`#deck-track .deck-page[data-deck-idx="${deckIdx}"]`);
  if (!page) return [];
  return Array.from(page.querySelectorAll('[data-step]'))
    .sort((a, b) => (+a.dataset.step || 0) - (+b.dataset.step || 0));
}

function revealSteps() {
  getStepsForCurrentDeck().forEach(el => {
    el.classList.toggle('revealed', (+el.dataset.step || 0) <= currentStep);
  });
}

function setStepMax() {
  const steps = getStepsForCurrentDeck();
  currentStep = steps.length
    ? Math.max(...steps.map(el => +el.dataset.step || 0))
    : 0;
  revealSteps();
}

function updateHUD() {
  const hud = document.getElementById('presenterHUD');
  if (hud) hud.textContent =
    String(deckIdx + 1).padStart(2, '0') + ' / ' + String(pageOrder.length).padStart(2, '0');
}

function updateHash() {
  if (mode !== 'deck' || !pageOrder[deckIdx]) return;
  const want = `#deck:${pageOrder[deckIdx].id}`;
  if (location.hash !== want) {
    history.replaceState(null, '', location.pathname + location.search + want);
  }
}

// ---- 进入 Deck 模式 ----
function enterDeck(targetIdx) {
  mode = 'deck';
  document.body.classList.add('deck-mode');
  buildDeckTrack();
  buildDeckNav();
  pageOrder = flatPageOrder();

  if (typeof targetIdx === 'number') {
    deckIdx = Math.max(0, Math.min(pageOrder.length - 1, targetIdx));
  } else {
    const i = pageOrder.findIndex(p => p.id === currentPage);
    deckIdx = i >= 0 ? i : 0;
  }
  currentStep = 0;
  applyDeckOffset();
  revealSteps();

  const hint = document.getElementById('presenterEnterHint');
  if (hint) hint.style.display = 'none';
}

// ---- 退出 Deck 回 Doc ----
function exitDeck() {
  mode = 'doc';
  document.body.classList.remove('deck-mode');

  // 同步 currentPage 到当前 deck 位置
  if (pageOrder[deckIdx] && typeof goPage === 'function'
      && currentPage !== pageOrder[deckIdx].id) {
    goPage(pageOrder[deckIdx].id);
  }

  // Doc 模式所有 data-step 全显（不影响查阅）
  document.querySelectorAll('[data-step]').forEach(el => el.classList.add('revealed'));

  const hint = document.getElementById('presenterEnterHint');
  if (hint) hint.style.display = '';

  if (location.hash.startsWith('#deck:')) {
    history.replaceState(null, '', location.pathname + location.search);
  }
}

function jumpToPage(i) {
  const max = pageOrder.length - 1;
  deckIdx = Math.max(0, Math.min(max, i));
  currentStep = 0;
  applyDeckOffset();
  revealSteps();
}

function nextStep() {
  const steps = getStepsForCurrentDeck();
  const maxStep = steps.length
    ? Math.max(...steps.map(el => +el.dataset.step || 0))
    : 0;
  if (currentStep < maxStep) {
    currentStep++;
    revealSteps();
    return;
  }
  if (deckIdx < pageOrder.length - 1) {
    jumpToPage(deckIdx + 1);
  }
}

function prevStep() {
  if (currentStep > 0) {
    currentStep--;
    revealSteps();
    return;
  }
  if (deckIdx > 0) {
    jumpToPage(deckIdx - 1);
    setStepMax();
  }
}

// ---- 键盘 ----
document.addEventListener('keydown', function(e) {
  if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;

  if (e.key === 'p' || e.key === 'P') {
    if (mode === 'deck') exitDeck(); else enterDeck();
    return;
  }
  if (mode !== 'deck') return;

  if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
    e.preventDefault(); nextStep();
  } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
    e.preventDefault(); prevStep();
  } else if (e.key === 'Escape') {
    exitDeck();
  } else if (e.key === 'Home') {
    jumpToPage(0);
  } else if (e.key === 'End') {
    jumpToPage(pageOrder.length - 1);
    setStepMax();
  }
});

// ---- 滚轮翻页（throttle 800ms） ----
document.addEventListener('wheel', function(e) {
  if (mode !== 'deck') return;
  const now = Date.now();
  if (now - lastWheelTime < 800) return;
  if (Math.abs(e.deltaY) < 30 && Math.abs(e.deltaX) < 30) return;
  lastWheelTime = now;
  if (e.deltaY > 0 || e.deltaX > 0) nextStep(); else prevStep();
}, { passive: true });

// ---- 触屏左右滑动 50px 翻页 ----
document.addEventListener('touchstart', function(e) {
  if (mode !== 'deck') return;
  touchStartX = e.touches[0].clientX;
}, { passive: true });
document.addEventListener('touchend', function(e) {
  if (mode !== 'deck') return;
  const dx = e.changedTouches[0].clientX - touchStartX;
  if (Math.abs(dx) < 50) return;
  if (dx < 0) nextStep(); else prevStep();
}, { passive: true });

// ---- 初始：Doc 模式所有 data-step 全显 ----
document.querySelectorAll('[data-step]').forEach(el => el.classList.add('revealed'));

// ---- URL hash 直达：#deck:{pageId} ----
function initFromHash() {
  const m = location.hash.match(/^#deck:(.+)$/);
  if (!m) return;
  const order = flatPageOrder();
  const idx = order.findIndex(p => p.id === m[1]);
  if (idx >= 0) {
    setTimeout(() => enterDeck(idx), 50);
  }
}
initFromHash();

})();
