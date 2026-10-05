---
name: neo_ppt_skills
description: 以 GordenSuperPPTSkill 为主线的端到端 PPT 生产技能：阶段一用 imagegen 逐页生成「图片型 PPT」，阶段二把每页图四层还原为可编辑 PPTX（背景图/骨架图/元素图标/真文本），同时交付图片型 PPT 与可编辑 PPTX。另内置 bank-all（27 套 577 页）与 bank-lite（18 套 339 页）银行营销合辑模板的 GordenPPTSkill 快线换字，以及图片矢量复刻备选管线。当用户要"端到端出一份既好看又能编辑的 PPT"、"按主题/文章出 PPT"、"用 bank 模板换字出稿"、"把图片转成可编辑 PPTX"时使用。
---

# neo_ppt_skills

**主线：GordenSuperPPTSkill 端到端 PPT 生产。**
`GordenSuperPPTSkill/` 已原样收录在本技能内，编排规则、阶段门禁、
运行手册以其 SKILL.md 与 `GordenSuperPPTSkill/references/pipeline.md` 为准：

```
阶段1 GordenImagePPTGen   内容 → outline → imagegen 逐页出图 → 图片型 PPT
阶段2 GordenImage2PPTX    每页图四层还原（背景图/骨架图/元素图标/真文本）→ 可编辑 PPTX
交付：图片型 PPT + 可编辑 PPTX + 全部中间产物
```

**硬门禁（不可绕过）**：阶段 1 每页必须真实调用 imagegen（源图来自
`$CODEX_HOME/generated_images/`，逐页记入 imagegen-manifest.json）；阶段 2 的
背景/骨架/图标三层同样必须 imagegen 提取式生成并留证据。宿主无 imagegen 时
主线停止——改走下方快线或备线，不得用代码绘图冒充出图。

## 快线：模板换字（无 imagegen 环境的默认出稿方式）

`templates/` 内置两套合辑模板（`bank-lite` 339 页精选 / `bank-all` 577 页全量，
由 27 套银行 PPT 矢量复刻成品合并，原生形状+真文本框），配 GordenPPTSkill
三件套脚本与一键调用器：

```bash
python3 scripts/use_bank_all.py find 客户分层      # 按主题搜页
python3 scripts/use_bank_all.py show 页码          # 看槽位与容量
python3 scripts/use_bank_all.py build 页码 "新标题"   # 输出固定为 bank_all_out.pptx
```

页面 use_for 带来源标签（如 `bank16·内容版式：客户分层…`），选页不破坏叙事；
编辑铁律继承 GordenPPTSkill（只换字、禁省略号、同级字号一致、装饰序号不动）。

## 备线：图片矢量复刻（无 imagegen 时的图片转可编辑）

`extras/`：微信下载器、OCR 坐标级重建（文字按原图坐标原位落位）、
ppt-master 代理施工规格与三工艺编排手册。依赖与流程见 `extras/pipeline.md`。

## 目录

```
GordenSuperPPTSkill/   # 主线编排技能（含 references/pipeline.md 运行手册）
GordenImagePPTGen/     # 阶段1：imagegen 图片型 PPT（含提示词体系与脚本）
GordenImage2PPTX/      # 阶段2：四层还原为可编辑 PPTX（compose/chroma_key/slice_grid）
templates/             # bank-lite 339 页 + bank-all 577 页合辑模板
scripts/               # GordenPPTSkill 引擎三件套 + use_bank_all.py 调用器
extras/                # 备选：矢量复刻管线与质量审计
```

## 环境依赖

| 能力 | 依赖 |
|---|---|
| 主线（Super 端到端） | Codex 宿主 + imagegen（硬性）；Python 包见两子技能 SKILL.md |
| 快线（模板换字） | Python 3.10+、`python-pptx`；渲染预览需 LibreOffice |
| 备线（矢量复刻） | `rapidocr-onnxruntime`；ppt-master 技能（同目录自动探测） |
