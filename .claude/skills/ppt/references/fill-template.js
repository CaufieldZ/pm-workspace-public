#!/usr/bin/env node
/**
 * PPT Skill 填充脚本 (Node.js 版)
 * 用途：读取骨架模板，填充 NAV 和 PAGE_RENDERERS，生成最终 HTML
 * 优势：相比 Python，Node 的模板字符串天然支持多行 HTML，无需复杂转义
 */

const fs = require('fs');
const path = require('path');

// 配置路径
const SKILL_DIR = path.dirname(__dirname); // .claude/skills/ppt/
const TEMPLATE_PATH = path.join(SKILL_DIR, 'references', 'ppt-template.html');

function esc(s) {
  /**
   * 转义 HTML 内容为 JS 字符串
   * 输出格式："\n<div class=\"page\">..."
   * 每个 \n 在文件中是字面两个字符 \ 和 n
   */
  return s
    .replace(/\\/g, '\\\\')      // \ -> \\
    .replace(/"/g, '\\"')        // " -> \\"
    .replace(/\n/g, '\\n');      // newline -> \n (两个字符)
}

function generateRenderer(key, htmlContent) {
  /**
   * 生成单个 PAGE_RENDERER 函数
   * 格式：'key': function(c) { c.innerHTML = "..."; },
   */
  const escaped = esc(htmlContent.trim());
  return `  '${key}': function(c) { c.innerHTML = "${escaped}"; },`;
}

function fillTemplate(options) {
  /**
   * 填充模板
   * @param {Object} options
   * @param {string} options.title - 文档标题
   * @param {Array} options.nav - NAV 数组
   * @param {Object} options.renderers - { key: htmlContent }
   * @param {string} options.outputPath - 输出文件路径
   */
  const { title, nav, renderers, outputPath } = options;

  // 读取骨架模板
  let template = fs.readFileSync(TEMPLATE_PATH, 'utf8');

  // 替换标题
  template = template.replace(/__TITLE__/g, title);

  // 生成 NAV JSON
  const navJSON = JSON.stringify(nav, null, 2);
  template = template.replace('/* __NAV_PLACEHOLDER__ */', navJSON);

  // 生成 PAGE_RENDERERS
  const rendererLines = Object.entries(renderers).map(([key, content]) => {
    return generateRenderer(key, content);
  }).join('\n');

  const renderersBlock = `const PAGE_RENDERERS = {\n${rendererLines}\n};`;
  template = template.replace('/* __RENDERERS_PLACEHOLDER__ */', renderersBlock);

  // 写出文件
  fs.writeFileSync(outputPath, template, 'utf8');

  // 验证 JS 语法
  const scriptMatch = template.match(/<script>([\s\S]*?)<\/script>/);
  if (scriptMatch) {
    try {
      new Function(scriptMatch[1]);
      console.log(`✅ 生成成功: ${outputPath}`);
      console.log(`   行数: ${template.split('\n').length}`);
      console.log(`   JS 语法: 通过`);
    } catch (e) {
      console.error(`❌ JS 语法错误: ${e.message}`);
      process.exit(1);
    }
  }
}

// 示例用法（参考）
if (require.main === module) {
  console.log('PPT Fill Template - Node.js 版');
  console.log('用法：require("./fill-template.js").fillTemplate({...})');
  console.log('');
  console.log('示例：');
  console.log(`
const { fillTemplate } = require('./fill-template.js');

fillTemplate({
  title: '10x 授信风控全景分析',
  nav: [
    { group: '基础概念', dot: 'green', items: [
      { id: 'overview', icon: '📊', label: '概览' }
    ]}
  ],
  renderers: {
    overview: \`<div class="page active">...</div>\`
  },
  outputPath: 'deliverables/ppt-demo-v1.html'
});
  `);
}

module.exports = { fillTemplate, esc, generateRenderer };
