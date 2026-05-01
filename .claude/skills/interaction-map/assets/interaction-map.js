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
