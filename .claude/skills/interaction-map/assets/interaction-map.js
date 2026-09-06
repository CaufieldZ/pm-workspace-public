// ── 进度条 ──
const progressBar = document.getElementById('progressBar');
window.addEventListener('scroll', () => {
  const h = document.documentElement;
  const pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
  progressBar.style.width = pct + '%';
});

// ── 侧导航高亮 ──
const navLinks = document.querySelectorAll('.side-nav a');
const sections = [];
navLinks.forEach(a => {
  const id = a.getAttribute('href').slice(1);
  const el = document.getElementById(id);
  if (el) sections.push({ el, link: a });
});

function updateNav() {
  const scrollY = window.scrollY + 200;
  let current = sections[0];
  for (const s of sections) {
    if (s.el.offsetTop <= scrollY) current = s;
  }
  navLinks.forEach(a => a.classList.remove('active'));
  if (current) current.link.classList.add('active');
}
window.addEventListener('scroll', updateNav);
updateNav();

// ── 滚动淡入 ──
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
    }
  });
}, { threshold: 0.05, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.fade-section').forEach(el => observer.observe(el));

// ── 注解 hover 联动 ──
// 注解卡下沉到 .flow 下方后，靠编号维持「屏幕元素 ↔ 注解条目」关联：
// 同一 scene 内，屏幕徽章 .anno-n 与卡内 .ann-item 按数字文本配对，hover 任一侧互亮。
// 不依赖 data 属性，复用规则 2/4 既有编号；配不上则静默。
document.querySelectorAll('.fade-section').forEach(section => {
  const norm = (t) => (t || '').trim();
  const groups = {};           // 数字 → { badges:[], items:[] }
  const reg = (key) => (groups[key] || (groups[key] = { badges: [], items: [] }));

  section.querySelectorAll('.anno-n').forEach(badge => {
    const key = norm(badge.textContent);
    if (key) reg(key).badges.push(badge);
  });
  section.querySelectorAll('.ann-item').forEach(item => {
    const num = item.querySelector('.ann-num');
    const key = norm(num && num.textContent);
    if (key) reg(key).items.push(item);
  });

  Object.values(groups).forEach(g => {
    if (!g.badges.length || !g.items.length) return;   // 配不上 → 不绑
    const all = [...g.badges, ...g.items];
    const toggle = (on) => {
      g.badges.forEach(b => {
        b.classList.toggle('hl', on);
        const box = b.closest('.anno');
        if (box) box.classList.toggle('hl', on);
      });
      g.items.forEach(it => {
        it.classList.toggle('hl', on);
        const n = it.querySelector('.ann-num');
        if (n) n.classList.toggle('hl', on);
      });
    };
    all.forEach(el => {
      el.addEventListener('mouseenter', () => toggle(true));
      el.addEventListener('mouseleave', () => toggle(false));
    });
  });
});
