---
name: cross-check
description: >
  当 PRD 完成后需要最终交付前验收时触发，或用户说「自检」「拉通检查」「校验一下」
  「cross-check」「检查一致性」时触发。PRD 完成后应主动建议执行此步。
  即使用户只说「检查一下有没有问题」也应触发。
type: pipeline
output_format: 对话内
pipeline_position: 8
depends_on: [scene-list]
optional_inputs: [interaction-map, prototype, prd, behavior-spec, page-structure, test-cases]
consumed_by: []
---

# 跨产出物拉通自检 Skill（Cross Check）

## 作用

单个 skill 有各自的自检清单，但跨文件的一致性没人管。这个 skill 在链路末尾或用户要求时执行，拉通检查所有已产出文件（含行为规格、页面结构、测试用例集）。

## 触发时机

1. PRD 完成后，**主动建议**用户执行拉通自检
2. 用户主动说「拉通检查」「全部自检」「对齐一下」
3. 方案变更后，需要确认变更已同步到所有文件

## 执行步骤

### Step 1：动态盘点产出物

#### 1.1 构建前缀映射

扫描所有 SKILL.md frontmatter 中有 `output_prefix` 的 skill，构建前缀 → skill 名映射：

```bash
for f in .claude/skills/*/SKILL.md; do
  prefix=$(sed -n 's/^output_prefix: *//p' "$f")
  name=$(sed -n 's/^name: *//p' "$f")
  [ -n "$prefix" ] && echo "$prefix → $name"
done
```

#### 1.2 扫描 deliverables/ 匹配

```bash
ls projects/{项目名}/deliverables/ | grep -v '^archive' | while read file; do
  echo "$file"
done
```

根据文件名前缀自动识别 skill 类型（imap-* → interaction-map，proto-* → prototype，以此类推）。

**只检查实际存在的产出物**，不报「缺少 XXX」——不是所有项目都走全链路。

**最低要求**：至少存在 `scene-list.md` + 1 个 pipeline 型产出物，才能跑 cross-check。

列出已发现产出物，格式：
```
✅ scene-list.md
✅ deliverables/imap-xxx-v1.html  → interaction-map
✅ deliverables/prd-xxx-v1.docx   → prd
⬜ prototype（未产出，跳过相关检查项）
```

### Step 2：逐项检查

按以下 7 个维度逐项检查，每项给出 ✅ 通过 / ❌ 不通过 + 具体问题：

---

#### 2.1 场景编号一致性

> scene-list.md 为基准，检查所有**已发现的 pipeline 型产出物**

遍历 Step 1 发现的产出物，逐文件检查：
- [ ] 每个已发现产出物中的 Scene 编号 ⊆ scene-list.md 编号集合（无多余编号）
- [ ] scene-list.md 编号集合 ⊆ 已发现产出物编号的并集（无遗漏编号，允许单个文件只覆盖部分场景）
- 跳过未产出的文件，不报「缺少 XXX」

#### 2.2 View 划分一致性

- [ ] 交互大图的 gnav PART 数量 = scene-list View 数量
- [ ] 原型的全局 Tab 数量 = scene-list View 数量
- [ ] PRD 的章（3/4 章）= scene-list View 划分
- [ ] 各文件中 View 名称完全相同（不是"用户端"vs"前台"vs"App端"）

#### 2.3 术语一致性

> 基于 Registry 中声明了依赖关系的产出物对（如 test-cases depends_on behavior-spec）优先检查术语一致性

- [ ] 模块/组件名称：已发现产出物之间的标注、UI 文案、描述、术语表用词相同
- [ ] 状态名：如「进行中/即将开始/已结束」三个文件用词相同
- [ ] 字段名：表单字段、列表列名，三个文件一致
- [ ] 枚举值：业务线、角色、分类等枚举，三个文件一致

#### 2.4 引用关系完整性

- [ ] PRD 左列截图能在原型中找到对应页面
- [ ] PRD 中的 `→ 见 X-N` 跳转编号存在
- [ ] 交互大图中的 `→ 见 X-N` 跳转编号存在
- [ ] 交互大图跨端表的起点/终点 View 名 = scene-list View 名
- [ ] 架构图模块名 = PRD 业务规则中的系统名称（如有架构图）

#### 2.5 优先级同步

- [ ] scene-list 的 P0/P1/P2 = PRD 场景地图表的优先级列
- [ ] 交互大图的 `.ann-tag.p0/.p1/.p2` 标注与 scene-list 一致
- [ ] 无优先级矛盾（如 scene-list 标 P1 但 PRD 写了 P0 的详细需求）

#### 2.6 数据一致性

- [ ] 交互大图展示的字段 = 原型实际渲染的字段
- [ ] 原型弹窗中的表单字段 = PRD 业务规则中定义的字段
- [ ] 交互大图标注的业务规则 = PRD 业务规则章节内容
- [ ] 行为规格的业务规则数值 = PRD 业务规则中的数值（阈值、限制、计算公式）
- [ ] 页面结构的状态矩阵状态 = PRD 中定义的状态（不多不少）
- [ ] 数字自洽（如 PRD 说"最多 5 个"，原型默认数据没超过 5 个）

#### 2.7 异常场景覆盖

- [ ] 交互大图标注了异常态（空态/错误态/边界态）
- [ ] 原型有异常态展示（如空列表、网络错误）
- [ ] PRD 异常场景有描述 + 处理方案
- [ ] 行为规格异常场景覆盖了 PRD 中定义的异常场景
- [ ] 页面结构异常路径覆盖了 PRD 中定义的异常场景
- [ ] 测试用例集异常场景用例覆盖了 behavior-spec 中定义的异常场景
- [ ] 所有文件的异常处理策略一致

---

### Step 3：输出报告

格式：

```markdown
# 拉通自检报告 · {项目名}

检查时间：{日期}
检查范围：{列出已检查的文件}

## 检查结果

| 维度 | 结果 | 问题数 |
|------|------|--------|
| 2.1 场景编号 | ✅ 通过 | 0 |
| 2.2 View 划分 | ✅ 通过 | 0 |
| 2.3 术语一致 | ❌ 不通过 | 2 |
| 2.4 引用关系 | ❌ 不通过 | 1 |
| 2.5 优先级同步 | ✅ 通过 | 0 |
| 2.6 数据一致 | ❌ 不通过 | 3 |
| 2.7 异常覆盖 | ✅ 通过 | 0 |

**总计**：4/7 通过，6 个问题待修

## 问题明细

### ❌ 2.3 术语一致

1. **「活动专区」vs「活动中心」**
   - 交互大图 Scene B 标题写「活动专区」
   - 原型 Tab 名写「活动中心」
   - PRD 3.2 章标题写「活动中心」
   → 建议统一为「活动中心」，修改交互大图

2. **状态名不一致**
   - 交互大图标注：「活跃/待开始/结束」
   - 原型 UI：「进行中/即将开始/已结束」
   → 建议以原型为准，修改交互大图标注

### ❌ 2.4 引用关系
...

## 修复建议

按优先级排序，逐个修复。修复后可再次执行拉通自检确认。
```

### Step 4：辅助修复

如果用户说「帮我修」，按报告中的修复建议逐文件修改，每改一处说明改了什么。全部改完后重新执行自检确认 0 问题。

## 注意

- 这个 skill **只读不写**（除非用户明确说"帮我修"）
- 检查基于文件内容，不是猜测——读不到的文件跳过并标注
- 如果只完成了 2 个产出物，只检查这 2 个之间的一致性，不报「缺少 PRD」之类的问题
- 最低触发条件：scene-list.md + 至少 1 个 pipeline 型产出物（2 个文件即可跑）
- 产出物类型通过 SKILL.md frontmatter 的 output_prefix 动态识别，不硬编码文件名映射
- 检查粒度到具体行/具体编号，不说"大致一致"这种废话
