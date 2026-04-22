// ================================================================
// PRESENTER MODE — Doc ⇄ Presenter 双模式
// 按 P 切换；→/Space/PageDown 下一步；←/PageUp 上一步；ESC 退出
// data-step="N" 分步揭示（Keynote Build-in 同款）
// ================================================================

(function() {

let presenterMode = false;
let currentStep = 0;

// 扁平化 NAV 为线性页面顺序
function flatPageOrder() {
  const out = [];
  NAV.forEach(g => g.items.forEach(i => out.push(i.id)));
  return out;
}

// 当前页所有 data-step 元素，按 step 编号排序
function getSteps() {
  return Array.from(document.querySelectorAll('.page.active [data-step]'))
    .sort((a, b) => (+a.dataset.step || 0) - (+b.dataset.step || 0));
}

function revealSteps() {
  getSteps().forEach(el => {
    el.classList.toggle('revealed', (+el.dataset.step || 0) <= currentStep);
  });
}

// 把 currentStep 设为当前页的实际 max step（用于从后往前进入一页时全显）
function setStepMax() {
  const steps = getSteps();
  currentStep = steps.length > 0
    ? Math.max(...steps.map(el => +el.dataset.step || 0))
    : 0;
  revealSteps();
}

function updateHUD() {
  const order = flatPageOrder();
  const idx = order.indexOf(currentPage);
  const hud = document.getElementById('presenterHUD');
  if (hud) hud.textContent = (idx + 1) + ' / ' + order.length;
}

function enterPresenter() {
  presenterMode = true;
  document.body.classList.add('presenter-mode');
  currentStep = 0;
  revealSteps();
  updateHUD();
  const hint = document.getElementById('presenterEnterHint');
  if (hint) hint.style.display = 'none';
}

function exitPresenter() {
  presenterMode = false;
  document.body.classList.remove('presenter-mode');
  // 退出后全部显现（doc 模式不应有隐藏内容）
  document.querySelectorAll('[data-step]').forEach(el => el.classList.add('revealed'));
  const hint = document.getElementById('presenterEnterHint');
  if (hint) hint.style.display = '';
}

function nextStep() {
  const steps = getSteps();
  const maxStep = steps.length > 0
    ? Math.max(...steps.map(el => +el.dataset.step || 0))
    : 0;
  if (currentStep < maxStep) {
    currentStep++;
    revealSteps();
    return;
  }
  // 所有 step 已显现 → 翻到下一页
  const order = flatPageOrder();
  const idx = order.indexOf(currentPage);
  if (idx < order.length - 1) {
    goPage(order[idx + 1]);
    // goPage 会触发 wrap 重置 step
  }
}

function prevStep() {
  if (currentStep > 0) {
    currentStep--;
    revealSteps();
    return;
  }
  // 已在第一 step → 退到上一页，currentStep 设为该页实际 max step（全显）
  const order = flatPageOrder();
  const idx = order.indexOf(currentPage);
  if (idx > 0) {
    goPage(order[idx - 1]);
    setStepMax();
  }
}

// ── wrap 原 goPage，翻页后重置 step 状态 ──
const _origGoPage = goPage;
goPage = function(id) {
  _origGoPage(id);
  if (presenterMode) {
    currentStep = 0;
    // 等 renderPage 执行完（同步）再 revealSteps
    revealSteps();
    updateHUD();
  }
};

// ── 键盘监听 ──
document.addEventListener('keydown', function(e) {
  if (e.key === 'p' || e.key === 'P') {
    if (presenterMode) exitPresenter(); else enterPresenter();
    return;
  }
  if (!presenterMode) return;

  if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
    e.preventDefault();
    nextStep();
  } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
    e.preventDefault();
    prevStep();
  } else if (e.key === 'Escape') {
    exitPresenter();
  } else if (e.key === 'Home') {
    const order = flatPageOrder();
    goPage(order[0]);
    currentStep = 0;
    revealSteps();
    updateHUD();
  } else if (e.key === 'End') {
    const order = flatPageOrder();
    goPage(order[order.length - 1]);
    setStepMax();
    updateHUD();
  }
});

// Doc 模式下所有 data-step 内容默认全显（不影响查阅）
document.querySelectorAll('[data-step]').forEach(el => el.classList.add('revealed'));

})();
