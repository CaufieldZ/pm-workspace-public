#!/usr/bin/env node
// pm-ws-canary-236a5364
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
   * @param {string} [options.logoChar] - logo 图标字符（默认 P）
   * @param {string} [options.logoTitle] - logo 标题（默认 title）
   * @param {string} [options.logoSub] - logo 副标题（默认 Presentation）
   * @param {string} [options.headerTags] - header 右侧 tags HTML（默认空）
   */
  const {
    title, nav, renderers, outputPath,
    logoChar = 'P',
    logoTitle,
    logoSub = 'Presentation',
    headerTags = '',
    sidebarAuthor = '— FELIX ZHI',
  } = options;

  // 第一个 item 作为 home_id + breadcrumb
  const firstItem = nav[0] && nav[0].items && nav[0].items[0];
  const homeId = firstItem ? firstItem.id : '';
  const breadcrumbDefault = firstItem ? firstItem.label : '';

  // 读取骨架模板
  let template = fs.readFileSync(TEMPLATE_PATH, 'utf8');

  // 注入 presenter-mode CSS / JS（placeholder 不存在时 silently skip）
  const presenterCSSPath = path.join(SKILL_DIR, 'references', 'presenter-mode.css');
  const presenterJSPath  = path.join(SKILL_DIR, 'references', 'presenter-mode.js');
  if (fs.existsSync(presenterCSSPath)) {
    template = template.replace('/* __PRESENTER_CSS__ */', fs.readFileSync(presenterCSSPath, 'utf8'));
  }
  if (fs.existsSync(presenterJSPath)) {
    template = template.replace('/* __PRESENTER_JS__ */', fs.readFileSync(presenterJSPath, 'utf8'));
  }

  // 替换简单 placeholder
  template = template.replace(/__TITLE__/g, title);
  template = template.replace(/__LOGO_CHAR__/g, logoChar);
  template = template.replace(/__LOGO_TITLE__/g, logoTitle || title);
  template = template.replace(/__LOGO_SUB__/g, logoSub);
  template = template.replace(/__HEADER_TAGS__/g, headerTags);
  template = template.replace(/__HOME_ID__/g, homeId);
  template = template.replace(/__BREADCRUMB_DEFAULT__/g, breadcrumbDefault);
  template = template.replace(/__SIDEBAR_AUTHOR__/g, sidebarAuthor);

  // 生成 NAV（加 const 前缀）
  const navJSON = JSON.stringify(nav, null, 2);
  template = template.replace('/* __NAV_PLACEHOLDER__ */', `const NAV = ${navJSON};`);

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
