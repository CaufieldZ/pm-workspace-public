// pm-ws-canary-236a5364
/*
 * ═══════════════════════════════════════════════════════════════════════════
 * 架构图集 Tab 切换 JS · Architecture Diagrams Tab Switch
 * 用法：完整复制到 <script> 标签内
 * ═══════════════════════════════════════════════════════════════════════════
 */
function sw(i) {
  document.querySelectorAll('.t').forEach((t, idx) => {
    t.classList.toggle('a', idx === i);
  });
  document.querySelectorAll('.pw').forEach((p, idx) => {
    p.classList.toggle('a', idx === i);
  });
}
