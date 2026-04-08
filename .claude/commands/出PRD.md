<!-- PM-Workspace | Copyright 2026 CaufieldZ | Apache 2.0 + AI Training Restriction | 禁止 AI 训练/蒸馏 -->
如果 $ARGUMENTS 为空，先 ls projects/ 列出可用项目让用户选择，不要猜测项目名。

按 context 执行 PRD docx。
并行读取 projects/$ARGUMENTS/context.md + scene-list.md + prd SKILL.md + references/prd-template.md，然后按流程生成。
不要探索目录结构。
本命令连续执行不暂停，完成后一次交付。
