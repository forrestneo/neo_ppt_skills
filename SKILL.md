---
name: neo-ppt-skills
description: >-
  行业中立的端到端 PPT 生产技能（任意行业，中英文皆可）。四种工作模式：
  A 生成图片型 PPT（imagegen 逐页出图）；B 把 PPT 图片/截图还原为可编辑 PPTX（四层强制）；
  C 端到端 A→B 一键全流程；D 合辑模板换字（deck-all 577 页，分钟级出稿）。
  引擎强制四条铁律：正文 12pt（小四）、写作预算前置、配色体系统一、出稿末步配色检查。
  当用户要"做/出/生成 PPT"、"把图片/截图转成可编辑 PPTX"、"用模板换字出稿"、
  "既要好看又要能编辑的完整成品"时使用。
---

# neo_ppt_skills — 端到端 PPT 生产技能

一个技能，四种模式。所有模式交付**原生形状 + 真文本框**的可编辑 PPTX，
全部规则由 `scripts/` 出稿引擎强制执行（见文末铁律）。

## 模式选择

| 用户意图 | 模式 |
|---|---|
| 「按主题/内容做一份好看的 PPT / AI 出图幻灯片」 | **A 图片生成**（只交付图片型 PPT） |
| 「把 PPT 图片/截图转成可编辑 PPTX / 复刻背景 / 抠图标」 | **B 图片还原**（只做还原） |
| 「要一份既好看又能编辑的完整成品」（没点名时默认） | **C 端到端**（A→B 串联） |
| 「有现成内容，用合辑模板换字出稿」 | **D 模板换字**（最快） |

## 模式 C：端到端编排（默认）

```
内容 ─▶ 阶段1【模式A】图片型 PPT（outline → prompts → 逐页 imagegen → 图片版 .pptx）
     ─▶ 阶段2【模式B】对每页图四层还原（背景/骨架/图标/真文本）
     ─▶ 交付：图片型 PPT + 可编辑 PPTX + 全部中间产物
```

- [ ] 阶段1 完整跑模式 A（A1–A5），产出 outline.json、prompts/、imagegen-manifest.json、slides/、图片型 .pptx
- [ ] 阶段2 对每张图完整跑模式 B（B0–B9），四层缺一不可
- [ ] 一次性交付：① 页图片 ② 每页背景图 ③ 骨架图 ④ 图标/装饰 ⑤ layout.json ⑥ 图片型 PPTX ⑦ 可编辑 PPTX
- [ ] 比例全程统一（默认 16:9）；配色统一；数据零编造；语言跟随用户；页脚干净

## 模式 A：生成图片型 PPT

```
内容 ─▶ A2 大纲(outline.json) ─▶ A3 每页提示词 ─▶ A4 imagegen 逐页出图 ─▶ A5 合成图片型 .pptx
```

**imagegen 硬门禁**：「生成图片」只指调用图像生成模型。禁止 Python/PIL、SVG、
HTML、Canvas、matplotlib、PPT shapes、截图渲染；禁止先做可编辑 PPTX 再导出图；
禁止在已生成位图上用代码补字/盖字。imagegen 不可用时模式 A 停止（改走模式 D），
不得用代码绘图兜底。

**全局铁律**：
1. 🔴 **绝不出占位符图**——每页图必须含【全部真实文字 verbatim】，出现占位框/无字卡片即失败重出
2. **数据零编造**——只用用户提供的数据；数据少就做厚结构 + 大字排版，不编造
3. **语言跟随用户**——幻灯片文字用内容语言（默认中文，支持英文）
4. **少用纯绿**——下游绿幕抠图会冲突
5. **页脚干净**——不加页码/logo/水印（除非用户要求）

**默认风格**：信息密度极高、模块化网格、每页一个不重复的高阶框架（Bento/
同心雷达/鱼骨/漏斗/3D 阶梯…）。简单 = 不合格。每页 ≥4 个并列模块、每模块
标题+2~3 要点+1 特大指标，外加导语+底部横幅（≈20+ 信息点/页）。每页框架
不重复；全篇统一一套配色。

**工作流**：
- [ ] A1 确认风格/受众/页数/语言
- [ ] A2 outline.json：逐页指派不重复框架、统一配色、写厚 detailed_content
- [ ] A3 每页 self-contained 提示词（含全部真实文字），存 prompts/NN-*.md
- [ ] A4 逐页调用 imagegen → 复制源图 → 写 imagegen-manifest.json（缺 manifest 即失败）
- [ ] A5 合成图片型 .pptx：`python scripts/imagegen/compose_pptx.py deck.json out.pptx`

提示词体系与执行要点全文：[references/mode-a-imagegen.md](references/mode-a-imagegen.md)

## 模式 B：图片 → 可编辑 PPTX（四层强制）

```
背景图(imagegen 复刻) + 骨架图(imagegen 绿幕提取) + 元素图标(imagegen 绿幕提取) + 文本(视觉提取→真文本框)
```

**核心铁律**：任何一页都必须实打实生成「骨架图 B3」和「元素图标图 B4」并
抠图，缺一不可。禁止的退化做法：① 拿原图当背景叠文字（双重文字）；② 用
原生 shapes/色块重画卡片/框架/图标/装饰；③ 裁原图局部当素材；④ 省略骨架/
图标层。骨架图 = 页面里除背景/图标/艺术字/普通文本外的一切（含全部图表图形），
形状·大小·位置与原图 1:1。

**三大原则**：
- 🟣 直接转换：直接以用户给的当前图为唯一源图，不扫描历史输出找相似页
- 🧱 任务隔离：每次任务建唯一 `RUN_ROOT`（image2pptx_runs/时间戳_slug/），一切产物只进该目录
- 🟦 edit target 传图：每次生成前必须先 `view_image` 当前页源图再调 imagegen，
  prompt 写明"以刚刚显示的这张图作为唯一编辑目标"——只写文件路径不算传图

**工作流（勾选）**：
- [ ] B0 隔离 RUN_ROOT；B0a 每页出图前 view_image 传图
- [ ] B1 探色（`scripts/restore/probe_palette.py`）定抠图底色（默认 #00ff00，含绿改 #ff00ff）
- [ ] B2 背景：imagegen 复刻干净背景
- [ ] B3 骨架图：固定提示词在抠图底上提取全部框架/图表图形（1:1 一致，别漏数据线）
- [ ] B4 图标图：对比 frame 预览去重后，imagegen 生成缺失元素的 N×N 等分图标表（不画分割线）
- [ ] B5 抠图切分：`chroma_key.py --preset frame-safe/icon-safe --scale 2` + `slice_grid.py --auto --pad 24 --contact-sheet`
- [ ] B6 定位：layout.json 用 fraction 坐标（量源图实际像素 bbox 换算）
- [ ] B7 文字：视觉提取全部普通文本（内容/位置/字号/颜色/粗细/对齐）；先定粗细/字号/行距再回校位置
- [ ] B7a/b/c `layout_guard.py --strict` + `placement_qa.py` 源图框复核 + 框架锚点回校
- [ ] B8 `compose_pptx.py` 合成 + 预览
- [ ] B9 QA：`visual_compare_qa.py` 并排/叠图/差异热图 + 图标缺失门禁 + 至少一轮回校

**生成证据**：每页必须写 imagegen-assets-manifest.json（B2/B3/B4 的
generated_source/prompt_file/backend/copied_to），任一层非 imagegen 来源即失败重做。

B2/B3/B4 固定提示词全文、坐标/字号换算、QA 门禁：
[references/mode-b-rebuild.md](references/mode-b-rebuild.md)

**关键换算与 QA 顺序**：
- 坐标：layout.json 用 `units:"fraction"`；先量源图像素 bbox，`x=x_px/ref_width`
  写入，并保留 `source_bbox` 供 QA；缩略图上量的坐标必须按
  `源图宽/缩略图宽`、`源图高/缩略图高` 分别换回，禁止 x/y 混用坐标系
- 字号：`size_ratio = 源图文字高度px / ref_height`（compose 换算
  `pt = size_ratio × 页高in×72`）；或直接写绝对 `size` pt
- 回校顺序固定：**先定 bold/字号/line_spacing → 再修 bbox**（否则换行变化
  让已校位置再次漂移）；贴框文本最后按最终 frame.png 的视觉锚点回校
- 图标回校按中心点锚定：`new_x = cx − new_w/2`

**引擎脚本**（`scripts/restore/`）：probe_palette / chroma_key / slice_grid /
frame_parts_to_icons / layout_guard / placement_qa / visual_compare_qa / compose_pptx

## 模式 D：合辑模板换字（deck-all，577 页）

`templates/deck-all` 是 27 套商务演示版式的矢量合辑，内容骨架**行业无关**
（示例文案是占位，出稿时全部正文槽位按 12pt 重写），中英文皆可。

```bash
python scripts/deck_cli.py find 客户分层          # 按主题搜页
python scripts/deck_cli.py show 24                # 槽位与 12pt 写作预算
python scripts/deck_cli.py build -o 成品.pptx 24 "新标题" \
    --set 24:p24s16x0=正文按预算写
```

英文稿同理——容量按视觉宽度自动换算（1 汉字 ≈ 2 英文字符），字体沿用
模板 latin 槽位。

## 编辑铁律（引擎强制，非建议）

固化在 `scripts/build_pptx.py` 与 `tests/eval_slim.py`（57 项回归基线），
违反即拒绝出稿，`--allow-*` 为显式豁免：

| 铁律 | 内容 | 引擎行为 |
|---|---|---|
| **正文 12pt（小四）** | 出稿正文一律小四号（作用域=role「正文」；标题/卡头/序号/mockup 缩微标签豁免） | 换字时自动置 12pt；超 12pt 容量拒绝 |
| **写作预算前置** | 每槽 12pt 容量 `show 页码` 逐槽可见 | 按预算写，超容量精炼措辞而非缩字号 |
| **配色体系统一** | 模板 577 页已整体预统一为活力橙单色系（`scripts/recolor_orange.py` 批量重着色）；13 套主题见 `scripts/palettes.json`，`--theme <id>` 切换 | 填充时按占比映射主题色；跨色系混选拒绝 |
| **出稿末步配色检查** | 成品实际用色扫描，杂色页不得交付 | `palette_check.py` 自动，不通过 rc=3 |

中文字号→pt：初号42 / 小初36 / 一号26 / 二号22 / 小二18 / 三号16 / 四号14 /
**小四12** / 五号10.5 / 小五9 / 六号7.5 / 七号5.5 / 八号5。

## 仓库结构

```
SKILL.md            # 本文件（唯一技能卡）
scripts/            # 全部引擎：deck_cli/build_pptx/palette_check + restore/（四层还原）+ imagegen/
templates/deck-all/ # 577 页合辑模板 + detail（槽位容量）+ palette.json（页主色）
tests/eval_slim.py  # 回归基线
extras/ docs/       # 备线管线；教程
```

## 仓库体积

全仓 **8.53 MiB**：模板 6.3MB（577 页矢量合辑、91,700 个矢量形状，deflate 已至
压缩地板）+ 参考图 1.9MB + 脚本/文档/评测 0.4MB。
