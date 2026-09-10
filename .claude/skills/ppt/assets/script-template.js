#!/usr/bin/env node
/**
 * PPT 生成脚本模板（gen_ppt_{主题}_v1.js）
 *
 * 用法：项目 scripts/ 目录复制此文件改写。
 * 调用 Skill 内置 fill-template.js 模块完成填充。
 *
 * CSS 变量 / 字体引入纪律（弱模型易踩坑）：
 * 1. 禁手抄 :root 整块 token。源头唯一 .claude/skills/_shared/claude-design/tokens.css，
 *    必须 fs.readFileSync(tokens.css) 拼进。项目级扩展 token 在 tokens.css 后追加 :root {}。
 * 2. 字体 <link> = 实际用到的字体，不照搬 tokens.css 注释里的完整 CDN URL。
 *    CJK PPT 最小集 = Noto Sans SC + Noto Serif SC + JetBrains Mono。
 *    引 Lora / Poppins 但 CSS 没用 = 白下载 ~50KB。
 * 3. CJK 混排字体栈：--cd-sans / --cd-serif 中文字体必须排在英文字体前。
 *    tokens.css 默认值已经 CJK 优先（'Noto Sans SC','Poppins',system-ui）。
 *    Lora + Poppins 是 Anthropic brand-guidelines 钦定的免费字体，对标 claude.ai 的 Tiempos + Styrene B。
 */

const { fillTemplate } = require('../../../../.claude/skills/ppt/assets/fill-template.js');

// 定义 NAV 数据
const NAV = [
  { group: '分组名', dot: 'green', items: [
    { id: 'tab-id', icon: '📍', label: 'Tab 标题' }
  ]}
];

// 定义 PAGE_RENDERERS（每个 Tab 的渲染函数）
// 使用 JavaScript 模板字符串（反引号），HTML 属性用双引号，无需转义换行
const renderers = {
  'tab-id': `
    <div class="page active">
      <div class="page-title">标题</div>
      <div class="page-subtitle">副标题</div>
      <!-- 页面内容 -->
    </div>
  `
};

// 生成文件
fillTemplate({
  title: '文档标题',
  nav: NAV,
  renderers: renderers,
  outputPath: 'projects/{项目名}/deliverables/ppt-{主题}-v1.html'
});
