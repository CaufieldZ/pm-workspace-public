#!/usr/bin/env node
/**
 * 纯 deck 范式生成脚本模板（gen_deck_{主题}_v1.js）
 *
 * 用法：项目 scripts/ 目录复制此文件改写，调 Skill 内置 deck-fill.js。
 * 与 script-template.js（sidebar Doc 模式）并列 —— 演讲型 deck 走本模板。
 *
 * 模型：每张幻灯片 = 一个 HTML 字符串（一个 <section class="slide">），
 * 推入 slides 数组按序拼接（忠于 hundsun build.js，规避 innerHTML 转义）。
 *
 * 纪律：
 * 1. 颜色 / 字体走主题，禁手写 hex。默认 theme='hundsun-editorial'（teal/amber 双语义 + 浅深双底）。
 * 2. 四层骨架每页复用：eyebrow → h1.headline → body-area → deck-foot（含 .pagenum 占位，运行时注入页码）。
 * 3. 浅深交替：封面 / 章节转场 / 收尾用 class="slide dark"，论证页默认浅底。
 * 4. 组件类名唯一来源 = assets/deck-template.html 的 <style>，不发明新 class。
 */

const { fillDeck } = require('../../../../.claude/skills/ppt/assets/deck-fill.js');

// 章节胶囊（顶部进度，可空 → 不渲染）。start = 该幕起始页 index（0-based）
const ACTS = [
  { label: '开场', start: 0 },
  { label: '为什么', start: 1 },
  { label: '怎么做', start: 3 },
];

const slides = [];

// ── 封面（深底）──
slides.push(`
  <section class="slide dark cover">
    <div class="cover-rule"></div>
    <div class="eyebrow">项目 · 副标</div>
    <h1>主标题<br>第二行</h1>
    <div class="lead">一句话 <b>价值主张</b>，关键词用 b 切 accent 高亮。</div>
    <div class="deck-foot"><span>封面页脚</span><span></span></div>
  </section>
`);

// ── 论证页（浅底，四格结论先行 BLUF）──
slides.push(`
  <section class="slide">
    <div class="eyebrow">如果只看一页 / 结论先行</div>
    <h1 class="headline">做什么、要多少、出什么、风险怎么兜</h1>
    <div class="body-area">
      <div class="bluf-grid">
        <div class="bcell"><div class="bk">WHAT · 做什么</div><h3>一句结论</h3>
          <ul class="blist"><li>要点 <b>关键词</b></li><li>要点二</li></ul></div>
        <div class="bcell"><div class="bk">COST · 要多少</div><h3>一句结论</h3>
          <ul class="blist"><li>要点</li></ul></div>
        <div class="bcell"><div class="bk">VALUE · 出什么</div><h3>一句结论</h3>
          <ul class="blist"><li>要点</li></ul></div>
        <div class="bcell warn"><div class="bk">RISK · 怎么兜</div><h3>一句结论</h3>
          <ul class="blist"><li>要点</li></ul></div>
      </div>
      <div class="caption">// 后面每页都在展开这一页的四个格子</div>
    </div>
    <div class="deck-foot"><span>一页纸结论</span><span class="pagenum"></span></div>
  </section>
`);

// ── 三栏卡片页（浅底）──
slides.push(`
  <section class="slide">
    <div class="eyebrow">为什么做这件事</div>
    <h1 class="headline">最终要回答的三个问题</h1>
    <div class="body-area">
      <div class="card-grid">
        <div class="card"><div class="gn">GOAL 01</div><h3>标题</h3><p>描述。</p></div>
        <div class="card"><div class="gn">GOAL 02</div><h3>标题</h3><p>描述。</p></div>
        <div class="card warn"><div class="gn">GOAL 03</div><h3>标题</h3><p>描述。</p></div>
      </div>
      <div class="caption">// 后面每页都挂在这三个目标上</div>
    </div>
    <div class="deck-foot"><span>三个目标</span><span class="pagenum"></span></div>
  </section>
`);

fillDeck({
  title: '文档标题',
  theme: 'hundsun-editorial',
  acts: ACTS,
  slides: slides,
  outputPath: 'projects/{项目名}/deliverables/ppt-{主题}-v1.html',
});
