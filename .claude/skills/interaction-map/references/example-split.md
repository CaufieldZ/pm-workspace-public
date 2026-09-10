# 档 B 拆分范例（orchestrator + 每场景一模块）

`html-build-split.md §二` 的 Python 轨标准结构活样板。代码冻结副本在 `../assets/example-split/`（只读、只示结构，不参与任何项目构建、不必跑通）。

```
assets/example-split/
  build_imap_v2.py        # orchestrator（≤ 150 行：import skeleton.generate + 收 fill_X + 调 generate）
  imap_v2/
    __init__.py
    scenes_a.py … scenes_g.py   # 一主场景一模块，每个导出 fill_X(...) 函数体
```

要点：
- orchestrator 只做装配（import + 组 scene_fns 字典 + 调 `build_imap_skeleton.generate`），不写内容。
- 改单场景 = 改对应 `scenes_{id}.py` 的 `fill_{id}` 函数体，重跑 orchestrator。
- 设备壳由 skeleton 提供（interaction-map 契约），scenes 只写内部内容。

实战落点：imap/proto 是 delta-scoped 产物，活样板随 delta 包住 `deliverables/{季度}/{版本}/scripts/`，本目录仅作脱离项目的结构参照。
