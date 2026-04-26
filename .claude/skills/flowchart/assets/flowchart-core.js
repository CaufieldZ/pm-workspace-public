/* ═══════════════════════════════════════════════════════════
   flowchart-core.js · AntV X6 流程图核心
   节点类型:terminal/process/decision/success/fail
   路由: 同行相邻 → normal(直线), 其他 → manhattan(圆角折线)
   ═══════════════════════════════════════════════════════════ */

const { Graph } = window.X6;

// ── 主题常量 ────────────────────────────────────────
const FONT = "'Noto Sans SC','Inter',system-ui,sans-serif";
const STROKE = '#1F2329';
const FILL = {
  terminal: '#E8E5FF',
  process:  '#E7EFFE',
  decision: '#FDF3D5',
  success:  '#D9F5E5',
  fail:     '#FEE3E6',
};
const SIZE = {
  terminal: { w: 118, h: 42 },
  process:  { w: 130, h: 46 },
  decision: { w: 130, h: 58 },
  success:  { w: 140, h: 46 },
  fail:     { w: 140, h: 46 },
};

// ── 菱形节点注册 ──────────────────────────────────────
Graph.registerNode('diamond', {
  inherit: 'polygon',
  attrs: {
    body: { refPoints: '0,10 10,0 20,10 10,20', strokeWidth: 1.5 },
    label: {
      fontFamily: FONT, fontSize: 11, fontWeight: 600,
      fill: STROKE, textVerticalAnchor: 'middle'
    },
  },
}, true);

const PORTS = {
  groups: {
    top:    { position: 'top',    attrs: { circle: { r: 0, magnet: true } } },
    bottom: { position: 'bottom', attrs: { circle: { r: 0, magnet: true } } },
    left:   { position: 'left',   attrs: { circle: { r: 0, magnet: true } } },
    right:  { position: 'right',  attrs: { circle: { r: 0, magnet: true } } },
  },
  items: ['top','bottom','left','right'].map(g => ({ id: g, group: g })),
};

// ── 工厂函数 ────────────────────────────────────────
function nodeConfig(n) {
  const s = SIZE[n.type];
  const common = { id: n.id, width: s.w, height: s.h, label: n.label, ports: PORTS };
  if (n.type === 'decision') {
    return { ...common, shape: 'diamond',
      attrs: { body: { fill: FILL.decision, stroke: STROKE, strokeWidth: 1.5 } } };
  }
  const strokeCol = n.type === 'fail' ? '#F6465D'
                  : n.type === 'success' ? '#0ECB81' : STROKE;
  const rx = n.type === 'terminal' ? 21 : 8;
  return { ...common, shape: 'rect',
    attrs: {
      body: { rx, ry: rx, fill: FILL[n.type], stroke: strokeCol, strokeWidth: 1.5 },
      label: { fontFamily: FONT, fontSize: 11, fontWeight: 600, fill: STROKE },
    } };
}

function choosePorts(sPos, tPos) {
  const dx = tPos.x - sPos.x, dy = tPos.y - sPos.y;
  const TH = 20;
  let sp, tp;
  if (dy > TH)       { sp = 'bottom'; tp = 'top'; }
  else if (dy < -TH) { sp = 'top';    tp = 'bottom'; }
  else               { sp = dx > 0 ? 'right' : 'left';
                       tp = dx > 0 ? 'left'  : 'right'; }
  return { sp, tp };
}

function edgeConfig(sId, tId, sp, tp, label) {
  // 同行相邻 right→left / left→right 用 normal router(直线),避免 manhattan 降级 orth 产生绕圈
  const isHoriz = (sp === 'right' && tp === 'left') || (sp === 'left' && tp === 'right');
  const router = isHoriz
    ? { name: 'normal' }
    : { name: 'manhattan', args: {
        startDirections: [sp], endDirections: [tp], step: 8, padding: 10,
      } };
  return {
    id: `${sId}->${tId}`,
    source: { cell: sId, port: sp },
    target: { cell: tId, port: tp },
    router,
    connector: { name: 'rounded', args: { radius: 8 } },
    attrs: {
      line: { stroke: STROKE, strokeWidth: 1.2,
        targetMarker: { name: 'block', width: 7, height: 7 } },
    },
    labels: label ? [{
      position: 0.5,
      attrs: {
        text: { text: label, fontFamily: FONT, fontSize: 10, fontWeight: 700, fill: STROKE },
        rect: {
          ref: 'text',
          refWidth: 1.5, refHeight: 1.5,
          refX: -0.25, refY: -0.25,
          fill: '#FFFFFF', stroke: STROKE, strokeWidth: 0.6,
          rx: 3, ry: 3,
        },
      }
    }] : [],
  };
}

// ── 分支流程图渲染(dagre 自动布局) ─────────────────────
function renderBranch(containerId, chart) {
  const dg = new dagre.graphlib.Graph();
  dg.setGraph({
    rankdir: chart.layout || 'TB',
    nodesep: chart.nodesep || 70,
    ranksep: chart.ranksep || 60,
    marginx: 20, marginy: 20,
  });
  dg.setDefaultEdgeLabel(() => ({}));
  chart.nodes.forEach(n => {
    const s = SIZE[n.type];
    dg.setNode(n.id, { width: s.w, height: s.h });
  });
  chart.edges.forEach(e => dg.setEdge(e.s, e.t));
  dagre.layout(dg);

  const g = new Graph({
    container: document.getElementById(containerId),
    background: { color: 'transparent' },
    grid: false, interacting: false, panning: false,
  });
  chart.nodes.forEach(n => {
    const d = dg.node(n.id), s = SIZE[n.type];
    g.addNode({ ...nodeConfig(n), x: d.x - s.w/2, y: d.y - s.h/2 });
  });
  chart.edges.forEach(e => {
    const { sp, tp } = choosePorts(dg.node(e.s), dg.node(e.t));
    g.addEdge(edgeConfig(e.s, e.t, sp, tp, e.label));
  });
  g.zoomToFit({ padding: 24, maxScale: 1 });
  return g;
}

// ── 泳道图渲染(栅格定位) ───────────────────────────────
function renderSwimlane(containerIds, chart) {
  const { laneBgId, laneInnerId, laneWrapSelector, graphId, checkOutId } = containerIds;
  const LANES = chart.lanes;
  const LANE_H  = chart.laneHeight || 90;
  const COL_W   = chart.colWidth   || 150;
  const HEAD_W  = chart.headWidth  || 84;
  const PAD_X   = chart.padX       || 12;
  const laneIdx = id => LANES.indexOf(id);

  const centerOf = n => ({
    x: HEAD_W + PAD_X + n.col * COL_W + COL_W / 2,
    y: laneIdx(n.lane) * LANE_H + LANE_H / 2,
  });

  const COLS = Math.max(...chart.nodes.map(n => n.col)) + 1;
  const W = HEAD_W + PAD_X * 2 + COLS * COL_W;
  const H = LANES.length * LANE_H;

  // CSS 泳道背景
  const inner = document.getElementById(laneInnerId);
  inner.style.width  = W + 'px';
  inner.style.height = H + 'px';
  document.querySelector(laneWrapSelector).style.height = H + 'px';
  const bgEl = document.getElementById(laneBgId);
  LANES.forEach((_, i) => {
    const row = document.createElement('div');
    row.className = 'lane-row ' + (i % 2 === 0 ? 'white' : 'alt');
    row.style.top = (i * LANE_H) + 'px';
    bgEl.appendChild(row);
  });

  const g = new Graph({
    container: document.getElementById(graphId),
    width: W, height: H,
    background: { color: 'transparent' }, grid: false,
    interacting: false, panning: false,
  });

  const byId = Object.fromEntries(chart.nodes.map(n => [n.id, n]));
  chart.nodes.forEach(n => {
    const c = centerOf(n), s = SIZE[n.type];
    g.addNode({ ...nodeConfig(n), x: c.x - s.w/2, y: c.y - s.h/2 });
  });
  chart.edges.forEach(e => {
    let sp = e.sp, tp = e.tp;
    if (!sp || !tp) {
      const auto = choosePorts(centerOf(byId[e.s]), centerOf(byId[e.t]));
      sp = sp || auto.sp;
      tp = tp || auto.tp;
    }
    g.addEdge(edgeConfig(e.s, e.t, sp, tp, e.label));
  });

  // 自检:边路径采样 vs 节点形状(菱形内切 + rect bbox 4px buffer)
  if (checkOutId) {
    setTimeout(() => runSelfCheck(graphId, checkOutId), 600);
  }
  return g;
}

// ── 自检:边不穿节点 ───────────────────────────────────
function runSelfCheck(graphId, outId) {
  const out = document.getElementById(outId);
  const svg = document.querySelector('#' + graphId + ' svg.x6-graph-svg');
  if (!svg) { out.textContent = '⚠ svg not found'; return; }

  const nodeEls = [...svg.querySelectorAll(
    'g.x6-cell[data-shape="rect"], g.x6-cell[data-shape="diamond"]'
  )];
  const boxes = nodeEls.map(el => {
    const r = el.getBoundingClientRect();
    return {
      id: el.getAttribute('data-cell-id'),
      shape: el.getAttribute('data-shape'),
      l: r.left, r: r.right, t: r.top, b: r.bottom,
      cx: (r.left + r.right) / 2, cy: (r.top + r.bottom) / 2,
      hw: (r.right - r.left) / 2, hh: (r.bottom - r.top) / 2,
    };
  });

  function hitInside(x, y, nb, excludeId) {
    if (nb.id === excludeId) return false;
    if (nb.shape === 'diamond') {
      const nx = Math.abs(x - nb.cx) / nb.hw;
      const ny = Math.abs(y - nb.cy) / nb.hh;
      return nx + ny < 0.82;
    }
    return x > nb.l + 4 && x < nb.r - 4 && y > nb.t + 4 && y < nb.b - 4;
  }

  const edgeCells = [...svg.querySelectorAll('g.x6-cell[data-shape="edge"]')];
  const issues = [];
  edgeCells.forEach(cell => {
    const edgeId = cell.getAttribute('data-cell-id') || '?';
    const [sId, tId] = edgeId.split('->');
    const p = cell.querySelector('path.x6-edge, path[stroke]:not([stroke="none"])');
    if (!p || !p.getAttribute('d') || p.getAttribute('d').length < 5) return;
    const L = p.getTotalLength();
    if (L < 10) return;
    const ctm = p.getScreenCTM();
    if (!ctm) return;
    for (let k = 5; k <= 15; k++) {
      const pt = p.getPointAtLength(k * L / 20);
      const x = pt.x * ctm.a + pt.y * ctm.c + ctm.e;
      const y = pt.x * ctm.b + pt.y * ctm.d + ctm.f;
      for (const nb of boxes) {
        if (hitInside(x, y, nb, sId) && nb.id !== tId) {
          issues.push(`❌ ${edgeId} 穿过 ${nb.id}`);
          return;
        }
      }
    }
  });

  if (issues.length === 0) {
    out.innerHTML = `<span class="pass">✓ 自检通过</span> · ${edgeCells.length} 条边 × ${boxes.length} 节点 · 无穿节点`;
  } else {
    out.innerHTML = `<span class="fail">✗ 自检失败</span> · ${issues.length} 处:<br>` +
      [...new Set(issues)].map(x => `&nbsp;&nbsp;${x}`).join('<br>');
  }
  console.log('[SELF-CHECK]', issues.length === 0 ? 'PASS' : 'FAIL', [...new Set(issues)]);
}

window.FLOWCHART = { renderBranch, renderSwimlane };
