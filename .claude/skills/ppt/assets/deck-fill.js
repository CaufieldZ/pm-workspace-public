#!/usr/bin/env node
/**
 * deck-fill.js — 纯 deck 范式填充器（与 fill-template.js 的 sidebar Doc 模式并列）
 *
 * 用途：拼 1280×720 演讲 deck。slides 为 HTML 字符串数组（每个 = 一张 .slide），
 * 不走 fill-template.js 的 innerHTML 转义路径，直接字符串拼接（忠于 hundsun build.js 模型）。
 *
 * 入口：fillDeck({ title, theme, acts, slides, outputPath })
 *   - title      文档标题（注入 <title>）
 *   - theme      主题名，默认 'hundsun-editorial'（追加 _shared/themes/{theme}.css 覆盖 tokens）
 *   - acts       章节胶囊数组 [{ label, start }]，可空 → 不渲染胶囊
 *   - slides     HTML 字符串数组，每个是一张 <section class="slide ...">...</section>
 *   - outputPath 输出 HTML 路径
 */
'use strict';

const fs = require('fs');
const path = require('path');

const SKILL_DIR = path.dirname(__dirname); // .claude/skills/ppt/
const TEMPLATE_PATH = path.join(SKILL_DIR, 'assets', 'deck-template.html');
const RUNTIME_PATH = path.join(SKILL_DIR, 'assets', 'deck-runtime.js');
const SHARED_DIR = path.join(SKILL_DIR, '..', '_shared', 'claude-design');

function fillDeck(options) {
  const {
    title,
    theme = 'hundsun-editorial',
    acts = null,
    slides,
    outputPath,
  } = options;

  if (!Array.isArray(slides) || slides.length === 0) {
    throw new Error('fillDeck: slides 必须是非空 HTML 字符串数组');
  }

  let template = fs.readFileSync(TEMPLATE_PATH, 'utf8');

  // 注入 tokens.css（CSS 变量源头唯一）+ theme 覆盖
  let tokensCSS = fs.readFileSync(path.join(SHARED_DIR, 'tokens.css'), 'utf8');
  if (theme) {
    const themePath = path.join(SHARED_DIR, 'themes', `${theme}.css`);
    if (fs.existsSync(themePath)) {
      tokensCSS += `\n\n/* === Theme override: ${theme} === */\n` + fs.readFileSync(themePath, 'utf8');
    } else {
      console.warn(`⚠️  Theme '${theme}' not found at ${themePath}`);
    }
  }
  template = template.replace('/* __TOKENS_CSS__ */', tokensCSS);

  // 注入 runtime JS
  const runtimeJS = fs.readFileSync(RUNTIME_PATH, 'utf8');
  template = template.replace('/* __RUNTIME_JS__ */', runtimeJS);

  // 注入 ACTS 配置
  const actsJS = acts && acts.length
    ? `window.__DECK_ACTS__ = ${JSON.stringify(acts)};`
    : 'window.__DECK_ACTS__ = null;';
  template = template.replace('/* __ACTS__ */', actsJS);

  // 拼 slides
  const slidesHTML = slides.map((s) => s.trim()).join('\n');
  template = template.replace('<!-- __SLIDES__ -->', slidesHTML);

  // 替换标题
  template = template.replace(/__TITLE__/g, title || 'Deck');

  fs.writeFileSync(outputPath, template, 'utf8');

  // 校验内嵌 runtime JS 语法
  const scriptMatch = template.match(/<script>([\s\S]*?)<\/script>/);
  if (scriptMatch) {
    try {
      new Function(scriptMatch[1]);
    } catch (e) {
      console.error(`❌ deck runtime JS 语法错误: ${e.message}`);
      process.exit(1);
    }
  }

  console.log(`✅ deck 生成: ${outputPath}`);
  console.log(`   slides: ${slides.length} · theme: ${theme} · 行数: ${template.split('\n').length}`);
}

module.exports = { fillDeck };
