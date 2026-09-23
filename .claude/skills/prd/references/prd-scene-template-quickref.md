# PRD 场景模板速查（写场景块前读这一页）

> 完整说明 → `prd-scene-templates.md`。本文只讲「拿起来就能用」的骨架 + 最易踩的 3 条约束。

## 一、选哪个模板

| 情况 | 模板 |
| :--- | :--- |
| delta PRD 的 UI 场景（有截图 + 页面分块明确）| **左图右文两列 `<table>`**（见下方骨架）|
| 横切策略 / 后端流程（无 UI 或 UI 是别人的）| 粗体段 + bullet，不用 `<table>` |

**铁律**：只要有图，就用左图右文。不分单端 / 双端 / 简单 / 复杂——有图必进 `<table>`。

## 二、左图右文骨架（直接复制填空）

```html
<table>
  <colgroup>
    <col style="width: 30%;" />
    <col style="width: 70%;" />
  </colgroup>
  <thead>
    <tr><th>示意图</th><th>页面元素 &amp; 规则</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <img src="./assets/proto-xxx.png" alt="场景描述" />
      </td>
      <td>
        <strong>1. 区块名</strong>
        <ul>
          <li><strong>显示逻辑</strong>
            <ul>
              <li>何时显示 / 不显示，权限 / 数据源（后端关心），一条一 bullet</li>
            </ul>
          </li>
          <li><strong>显示要素</strong>
            <ul>
              <li>字段 / 控件 / 文案逐项列（前端关心），一条一 bullet</li>
            </ul>
          </li>
          <li><strong>交互</strong>
            <ul>
              <li>点击 X → 跳 Y / 触发 Z（前后端关心）</li>
            </ul>
          </li>
        </ul>
        <strong>2. 下一个区块名</strong>
        <ul>
          <li><strong>显示逻辑</strong>
            <ul>
              <li>...</li>
            </ul>
          </li>
        </ul>
        <strong>验收</strong>
        <ul>
          <li>反向 / 边缘 / 跨端断言（能从规格图直读的不写）</li>
        </ul>
      </td>
    </tr>
  </tbody>
</table>
```

注意：左图右文是原生 HTML 表直通 wiki，cell 内 `；` **不会**被切成 bullet（那是 md 原生表格渲染路径的约定）——多条规则一律走上面的嵌套 bullet。

## 三、三段式含义（右列必须覆盖）

| 标签 | 谁看 | 写什么 |
| :--- | :--- | :--- |
| 显示逻辑 | 后端 | 接口要不要返数据 / 权限边界 / 灰度 / 何时不渲染 |
| 显示要素 | 前端 | 控件清单 + 文案 + 字段 + 状态 |
| 交互 | 前后端 | 事件触发 + 路由 + 弹窗 / 抽屉开关 |

「显示要素 = 无」或「交互 = 无」→ 不是独立 UI 区块，并入上一块或挪到 §4 全局规则。

## 四、4 条必守约束

1. **验收不复述规格**：每条验收 = QA 能勾的断言（做 X → 观察到 Y）。能从规格直读的删掉。
2. **埋点不进规格表**：埋点有专用 §7 十列表，规格表连提都不提。
3. **跨场景规则不塞进场景块**：三场景共用的规则写 §4 全局规则，场景块「显示逻辑」一句引用即可。
4. **标签做组头，规则缩一级**：显示逻辑 / 显示要素 / 交互 每个区块内各出现**一次**（加粗组头），具体规则一条一 bullet 缩进挂组头下。**只有一条规则也照挂组头，不并回行内**——组头形态在同一份文档里全文一致，不做「条目多就分组、条目少就并回」的例外（例外一开就回到混用）。禁逐条 `<li>` 重复「显示逻辑：」前缀平铺一列（`check_prd_md.sh` WARN 兜底：同一标签 ≥ 3 条连排即报）。

## 五、整篇形态迁移（平铺 → 组头式）

存量产物里平铺写着的一律走脚本，别手写转换（单遍扫描 + 文本等价门 + 自动备份都在脚本里）：

```bash
python3 .claude/skills/prd/scripts/migrate_scene_blocks.py <prd.md>            # 干跑：报可转块数 + 样例
python3 .claude/skills/prd/scripts/migrate_scene_blocks.py <prd.md> --apply    # 落盘（先备份 .bak）
python3 .claude/skills/prd/scripts/migrate_scene_blocks.py <产品线目录> --report  # 存量普查
```

顶层项混入非三段式标签的块脚本整块跳过并报行号（人工确认后手改）；改完跑 `check_prd_md.sh` 复核。
