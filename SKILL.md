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
| 「从零排出一份原生可编辑的新 deck / 要现代风组件」 | **E 自由排版**（freelayout，16 版式） |

## 模式 C：端到端编排（默认）

```
内容 ─▶ 阶段1【模式A】图片型 PPT（outline → prompts → 逐页 imagegen → 图片版 .pptx）
     ─▶ 阶段2【模式B】对每页图四层还原（背景/骨架/图标/真文本）
     ─▶ 交付：图片型 PPT + 可编辑 PPTX + 全部中间产物
```

- [ ] 阶段1 完整跑模式 A（A1–A5），产出 outline.json、prompts/、imagegen-manifest.json、slides/、图片型 .pptx
- [ ] 出大纲前先选叙事模式（pyramid/narrative/instructional/showcase/briefing，查 stylekit 的 narrative-and-review）；标题写断言式（写发现不写主题）
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
- [ ] A1 确认风格/受众/页数/语言（用户点名视觉风格查 stylekit 的 visual-styles）
- [ ] A2 outline.json：逐页指派不重复框架（选型查 stylekit 的 image-type-templates）、统一配色、写厚 detailed_content
- [ ] A3 每页 self-contained 提示词（含全部真实文字），存 prompts/NN-*.md（组词：图式骨架 × 渲染手法 × 色板行为，词汇查 imagegen-styles）
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

## 模式 E：自由排版（freelayout，从零排原生新稿）

蒸馏 luobo-ppt / dsh-ppt-master 的「版式=代码、AI 只填内容槽」架构：
**19 种版式函数**（cover/toc/section/bullets/cards/kpi/compare/timeline/process/
pyramid/funnel/table/quote/statement/big_number/closing/**chart/image/screenshot**），AI 永不写坐标——
只写 deck.json（每页 type + 内容字段），几何、字号、间距全部由引擎决定。
组件灵活：卡片 1-6 张自动网格、KPI 涨跌徽章（`delta_color: good/bad` 覆盖语义色）、
双栏对比推荐侧、时间轴交错卡、漏斗数值定宽、原生表格（斑马+数值列自动右对齐）。

```bash
python scripts/freelayout.py deck.json -o 成品.pptx [--theme orange-vitality]
```

- deck.json 格式：`{"meta": {"theme", "footer"}, "slides": [{"type": "...", ...}]}`
  ——每页一个 `type` + 内容字段（title/kicker/items/takeaway 等），写前先看
  `references/stylekit/layout-library.md` 的配额表（bullets 1-8、cards ≤6、kpi ≤4、
  timeline ≤6、process ≤5、pyramid/funnel ≤5）；超配额引擎会警告并自动缩排
- 质量内建：字号沿 TYPE_SCALE 阶梯回落 + CJK 避头尾断行器（wrap_lines：行首尾
  禁则+数字量词不可断簇）+ 孤字防护 + 9pt 地板；内容块垂直居中不留空肚子；
  主题色读 `scripts/palettes.json`（13 套，`--theme` 切换或 `meta.colors` 自定义
  hex），派生色对比度自动兜底；出稿自动过静态排版门禁
- 内容级 lint（出稿即打警告）：话题式标题/疑问短句/空洞词/「谢谢观看」结尾 +
  **幽灵稿清单**（只读全部标题应能讲通故事）；每页 `notes` 字段写演讲者备注
  （口播稿 40-260 字口径）
- 配套工具：`scripts/measure_deck.py`（五维机器证据：统一/层级/细节/传达/节奏+PEI）、
  `scripts/dna_extract.py`（从客户旧稿量 DNA：median 词数硬上限/实际主色/字号档）、
  visual_gate `--json` 结构化输出
- 版式选型对齐内容形状：并列要点→bullets，多卡并列→cards，数字→kpi/big_number，
  方案取舍→compare，节点推进→timeline/process，层级→pyramid，转化→funnel，
  他者观点→quote，全篇结论→statement

## 风格库与叙事选型（stylekit）

蒸馏自 [ppt-master](https://github.com/hugohe3/ppt-master)（MIT）与 16 个
DSH/独立 PPT 引擎（pptwise、dsh-ppt、dsh-ppt-maker、dsh-ppt-master、PTT-Studio、
PPT-Design-Skill、dsh-ppt-canvas、dsh-office-tools、deepseek-design、luobo-ppt、
codex-slides、guizang-ppt-skill、baoyu-skills、frontend-slides、slide-skill、
deck-dna 等）、awesome-codex-ppt-skills 横评清单及 SkillHub 社区技能的知识库，
各篇头部注明来源与许可；按需查阅、只读选中的一篇：

| 文件 | 内容 | 何时查 |
|---|---|---|
| `references/stylekit/visual-styles.md` | 18 种页面视觉风格（瑞士极简/孟菲斯/水墨/玻璃拟态…）速查+逐式规则 | 用户点名风格，或模式 A 定画面气质 |
| `references/stylekit/imagegen-styles.md` | 20 种 imagegen 渲染手法 + 14 套图像色板（含 EN 提示词片段与适配矩阵） | 模式 A 的 A3 组提示词 |
| `references/stylekit/image-type-templates.md` | 11 种图式构图（漏斗/矩阵/金字塔/时间线…）骨架与提示词 | 模式 A 选每页框架；模式 B/C 画原生图示 |
| `references/stylekit/narrative-and-review.md` | 5 种叙事模式（金字塔/故事弧/教学/展示/简报）+ 视觉验收清单 | 模式 C 出大纲前选论证结构；交付前验收 |
| `references/stylekit/layout-engine.md` | 定位排版技术：7 规范版式坐标、静态审计阈值、字形级 lint 三规则、逐页闭环（蒸馏自 dsh-office/dsh-univer-office/pptx-harness） | 模式 B 摆位、compose 组装、手排页；配 `scripts/layout_audit.py` 终检 |
| `references/stylekit/layout-library.md` | 版式几何数字库：画布/单位换算锚点、通用网格、字号阶梯与倍率、边界页与 11 种内容版式坐标表、间距常数（蒸馏自 pptwise/dsh-ppt 系 9 引擎） | 手排任何页面先抄坐标起步；选版式查配额上限 |
| `references/stylekit/overflow-and-density.md` | 防溢出与密度：双层容量模型、降级链、孤字红线、密度上限表、覆盖率与装饰宪法、禁词汇表 | 写文案前定预算；页面发空/发满时查补满手法 |
| `references/stylekit/audit-protocol.md` | 验收协议：静态几何门阈值全集、中文 fit 红线、视觉门协议、双门审查、验收合同、无渲染自检 | 交付前走完整流程；对用户报告三态（静态/渲染/视觉） |
| `references/stylekit/edit-fidelity.md` | 编辑保真：原树编辑十二细则、占位符继承几何保护、最小改动纪律、无损撤销、能力边界哲学 | 改别人的 .pptx（改错字/更新数字/局部重排）必读 |
| `references/stylekit/style-extraction.md` | 风格抽取与美化：参考图→风格单（脚本管数字/模型管气质）、14 套预设组织（rules 与 forbid 分离）、三样张选型、品牌套件（VI 手册→色板吸附） | 用户给参考图要"照这个风格改"、给企业 VI 手册、或挑风格定不下来时 |
| `references/stylekit/fidelity-and-review.md` | 内容保真与自评：安静的改动五类门禁、QA 防作弊三设计、五维自评（统一/层级/细节/传达/节奏）、大纲门禁（结论式标题判定/幽灵稿） | 美化改稿交付前、内容生成出大纲后 |
| `references/stylekit/process-and-benchmark.md` | 过程纪律与评测：双信号验证（JSON 不是视觉 QA）、known-errors 先分类再重试、checkpoint 可见化、版本不可变、PEI 可编辑性分级、横评方法论 | 长流程出稿/改稿时、对外声明能力时、重大改版后自测 |
| `references/stylekit/style-dimensions.md` | 风格维度系统：四维参数化（质感×色彩×字体×密度=525 组合+兼容矩阵）、STYLE_INSTRUCTIONS 单一事实源、双视觉系统、样张先行与三层渐进披露 | 模式 A 定风格体系、风格文档要可组合/可路由时 |
| `references/stylekit/measure-driven.md` | 测量驱动设计：参考稿 DNA 五字段、median 词数硬上限、CJK 断行与字号三信号、spec 冻结防漂移、哈希证据链、生成式重建合并策略 | 有客户旧稿要沿用风格、四层还原取字号、长会话多页防跑偏 |
| `references/stylekit/content-enrichment.md` | 内容检索填充与去 AI 感：缺口识别→检索技巧→饱满度口径、AI 感禁止清单（标题下划线/默认蓝/同版式连用）、中文风格关键词路由 | 用户只给一句话主题要补内容、交付前审美自检、用户说"莫兰迪/MUJI 感"时 |

用法约束：**风格（怎么画）、色板（颜色怎么上）、叙事模式（怎么论证）三者独立
选型、一套 PPT 各定一种**；风格不携带固定 HEX——颜色一律走模板主题或
`--theme` 色系，imagegen 色板仅描述用色行为。摆位与间距问题查
`layout-engine.md` 与 `layout-library.md`；文案量与装饰查
`overflow-and-density.md`；deck-all 出稿已**自动**过静态排版门禁
（`layout_audit.py --level error`：文字出界/占位符残留=error 拒绝交付 rc=4，
`--allow-layout-errors` 显式豁免；纯装饰出血/重叠/溢出/孤字/装饰压字=warning），
交付前再手动跑 `python scripts/visual_gate.py 成品.pptx` 渲染视觉门
（渲染后叠字/数字劈行/文字出页=error，压线=warning——静态全绿≠能看），
最后按 `audit-protocol.md` 人工抽查。

## 编辑铁律（引擎强制，非建议）

固化在 `scripts/build_pptx.py` 与 `tests/eval_slim.py`（111 项回归基线），
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
scripts/            # 全部引擎：deck_cli/build_pptx/palette_check + freelayout（自由排版 16 版式）+ restore/（四层还原）+ imagegen/
templates/deck-all/ # 577 页合辑模板（已预统一活力橙）+ detail（槽位容量）+ palette.json（页主色）
references/         # mode-a/mode-b/pipeline 执行细则 + stylekit/（风格·色板·图式·叙事·排版五门·风格抽取·保真自评·过程纪律·风格维度·测量驱动，蒸馏自 ppt-master 与 16 个 PPT 引擎）
tests/eval_slim.py  # 回归基线
extras/ docs/       # 备线管线；教程
```

## 仓库体积

全仓 **6.7 MiB**：模板合辑（含参考图）6.3MB（577 页矢量、91,700 个矢量形状，
deflate 已至压缩地板）+ 脚本/文档/评测/stylekit 0.4MB。
