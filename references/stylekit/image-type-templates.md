# 图式构图模板（11 式）

> 蒸馏自 [ppt-master](https://github.com/hugohe3/ppt-master)（MIT License）references/image-type-templates。
> 用途：按内容逻辑选图式——对比/循环/流程/框架/漏斗/信息图/地图/矩阵/金字塔/场景/时间线。模式 A（imagegen）生成整页信息图时先在此选型，再把选型的构图骨架与渲染手法、色板组合进提示词；模式 B/C 画原生图示时参照其构图规则。

## 选型速查表

| 图式 | 中文名 | 何时用（内容逻辑） | 一句构图要点 |
|---|---|---|---|
| infographic | 信息图 | 数据摘要 / KPI 清单 / 步骤列表 / 卖点罗列（并列分区，无方向） | 2-5 个等权分区排成网格或放射状，每区一图标，无连接线 |
| flowchart | 流程图 | 过程 / 工作流 / 管线（有明确方向顺序） | 3-6 个同形阶段块，箭头串联，方向无歧义 |
| framework | 框架图 | 关系系统 / 架构（中心与外围的关系） | hub-spoke：1 中心节点 + 3-6 卫星，细线等粗辐射 |
| matrix | 矩阵 | 优先级 / 风险 / 投入-产出等两轴分区 | 两条垂直轴交于画布正中，分 4 等象限，每象限一图标 |
| cycle | 循环图 | 迭代 / 生命周期 / 持续改进（闭环无终点） | 3-6 步骤节点沿圆周排布，箭头顺时针闭合回起点 |
| funnel | 漏斗 | 营销 / 销售 / 招聘转化（逐层过滤） | 3-6 条横带自上而下逐级收窄 ~15-25%，沿中轴对齐 |
| pyramid | 金字塔 | 能力栈 / 价值层级 / 架构分层（底层托举上层） | 3-6 层自下而上逐层收窄，底宽顶尖，沿中轴对齐 |
| comparison | 对比图 | A/B、优劣势、Before-After、新旧转变 | 两个近等分半区 + 明确分割线，结构对称、内容互斥 |
| timeline | 时间线 | 历史 / 演进 / 路线图（按时间定位） | 一条细轴 + 3-6 个等距里程碑标记，左→右=早→晚 |
| map | 地图 | 办公点 / 市场布局 / 区域数据 / 供应链 | 简化陆地轮廓 + 3-12 个标记点，留白 ≥25% |
| scene | 场景图 | 故事 / 生活方式 / 案例叙事（环境中的瞬间） | 前景主体 + 中景环境 + 背景氛围三层纵深，光线定调 |

## 通用规则（来自 _index）

- 图式按**每张图**选定，非整套 PPT 统一；渲染手法与色板整套锁定，图式逐图变化。
- 跳过图式的情况：hero_page（封面/章节页/大数字/金句）、局部单主体/单人头像、内容无目录匹配时——直接用散文描述构图。
- `text_policy: none`：图内无任何文字（默认、低风险），标签由 SVG 外部叠加；`text_policy: embedded`：图内嵌 ≤2 词短标签，需呼应正文字体，精确/可编辑标签仍走 SVG。
- 提示词固定收尾语："Color values are rendering guidance only"（色值仅作渲染指导，勿显示 HEX）；人物一律 "simplified iconic symbols, no realistic faces"。
- 资源清单未给尺寸时的默认画幅见各节；hero_page 默认整页画布（16:9 即 1280×720）。

---

## infographic（信息图）
**何时用**：2-5 个并列要点（数据摘要/KPI/步骤/卖点），分区平行、无方向流。
**构图骨架**：
- 2-5 个等权分区：网格（2×2、3×1）或放射状（4-5 区绕小中心锚点）。
- 每区 1 图标 +（可选）1 短关键词；**不画连接线**（区别于 framework/flowchart）。
- 区间距 10-15% gutters，区内内容占 60-70%；各区视觉等权，无主次。
- 默认画幅 600×500 或 700×700（~1.2:1 / 1:1）。
**imagegen 提示词骨架（EN，原文保留）**：
> Clean flat vector illustration infographic. The composition is a 2×2 grid of equal-sized rounded-rectangle zones, separated by clean gutters (about 12% of canvas width). ... Crisp 2px outlines, single 8% soft drop shadow under each zone. Each zone contains one simple iconic symbol in white fill — chart bar, lightbulb, target, upward arrow. Background field secondary light gray showing through the gutters. Composed as a 600×600 half-page block with 14% inner padding around the grid. NO text, letters, numbers, or labels anywhere — SVG labels added externally.
**坑**：
- 别把并列分区画成带箭头的序列（那是 flowchart）或带连线辐射（那是 framework）。

## flowchart（流程图）
**何时用**：有明确先后方向的过程——工作流、上手步骤、管线、方法论序列。
**构图骨架**：
- 3-6 个阶段块 + 显式连接件（箭头/带箭头线的线）；方向无歧义。
- 三种子结构选一：水平流（最常用）、垂直流、环形回流。
- 各阶段同形同尺寸，连接线等粗，箭头样式统一；流程四周留白充足，不贴边。
- 默认画幅 1200×400 横幅（3:1）。
**imagegen 提示词骨架（EN，原文保留）**：
> Clean flat vector illustration flowchart banner. Four rounded-rectangle stages arranged horizontally across the canvas, separated by uniform gaps. ... Between each pair of stages, a thin uniform horizontal arrow with a clean triangular arrowhead. The third stage (highlighted as the focal stage) has a thin accent gold ring around it — under 5% accent area. Each stage contains one simple iconic symbol in white. ... Composed for a 1200×400 hero band with 14% inner padding. NO text, letters, numbers, or labels — SVG labels added externally.
**坑**：
- 与 infographic 的区别在"方向"；与 framework 的区别在"序列"——无方向不叫流程图。

## framework（框架图）
**何时用**：让关系系统/架构一眼可读——中心概念 + 外围子概念，或多组件关系结构。
**构图骨架**：
- 三种子结构每图只选一种，勿混用：① hub-spoke：1 个几何锚点（圆/圆角方/菱形/六边形）居中 + 3-6 卫星环绕，连线细且等粗；② 矩阵（2×2/3×3，等大格，每格一概念）；③ 分层栈（3-5 条横带纵向堆叠，视觉重量单调递增/递减）。
- 卫星同形族、同尺寸、同配色；径向留白充足，不挤中心也不贴画布边。
- 平衡：对称分布，或刻意强调某一个卫星——不允许偶然失衡。
- 默认画幅 700×700（1:1）。
**imagegen 提示词骨架（EN，原文保留）**：
> The composition is a hub-and-spokes framework: one central rounded-square node sits at the exact center; four satellite circles are evenly distributed around it (top, right, bottom, left), connected to the center by thin straight lines in a darker neutral. Each satellite contains one simple iconic symbol in white fill. ... Accent gold appears only as one thin emphasis ring around the central node — under 5% of canvas area. Composed as a 700×700 half-page block with 16% inner padding on all sides — satellites breathe well within the canvas, no element touches the edge. No text, letters, numbers, or labels anywhere in the image — SVG labels will be added externally.
**坑**：
- 三种子结构（hub-spoke / 矩阵 / 分层栈）一张图只用一种，混合即失焦。

## matrix（矩阵）
**何时用**：两条正交轴把内容划成定性区域——优先级、风险、投入-产出四象限。
**构图骨架**：
- 一横一纵两条轴交于画布正中心，切出 4 个等大象限（偶用 3×3）。
- 每象限 1 个简单图标，占该象限面积 40-60%；轴端可加指示（箭头/标签）；可选每象限不同底色微调。
- 四象限视觉等权，无单一象限主导。
- 默认画幅 800×800 或 1280×720（1:1 / 16:9）。
**imagegen 提示词骨架（EN，原文保留）**：
> Clean flat vector illustration of a 2×2 qualitative matrix. Two perpendicular thin lines cross at the exact canvas center, dividing the canvas into four equal quadrants. Each quadrant has a subtle background tint: upper-left in pale primary navy at 10% opacity ... Each quadrant contains one simple iconic symbol, centered within its quadrant. Each icon occupies about 45% of its quadrant. Small accent gold dots sit at the four outer corners. Composed as an 800×800 reference matrix block with 10% padding. NO text, letters, axis labels, or quadrant names anywhere — SVG will overlay all labels.
**坑**：
- 图像模型在四个位置渲染轴标签文字时一致性差——标签精度要求高时走 text_policy: none（SVG 叠加），这是低风险路径。
- 矩阵没有中心：意义在四格里，别画成 hub-spoke。

## cycle（循环图）
**何时用**：闭环过程——迭代、生命周期、持续改进；每步导向下一步，末步回到首步。
**构图骨架**：
- 3-6 个步骤节点沿圆周（或圆角方环）均布，箭头逐一相连并闭合回起点。
- 每步 1 个简单图标 + 弧形/直向箭头；可选圆心小锚点（循环名标签或小图标）。
- 圆心保持安静——留空或只放 1 个小锚点；节点等距，箭头等粗。
- 默认画幅 700×700 或 800×800（1:1）。
**imagegen 提示词骨架（EN，原文保留）**：
> Clean flat vector illustration of a closed-loop process cycle. Four step nodes arranged in a perfect circle on the canvas perimeter — at 12 o'clock, 3 o'clock, 6 o'clock, and 9 o'clock positions. ... Curved directional arrows connect each node to the next going clockwise, closing the loop. The center of the circle is calm — ... one small accent gold dot at the exact center as the cycle's anchor. ... Composed as a 700×700 half-page cycle block with 15% padding. NO text, letters, or step labels anywhere — SVG will overlay all step names.
**坑**：
- 区分近邻：flowchart 线性单向有终点；cycle 无终点、沿周边有方向运动；framework 中心辐射但无方向。

## funnel（漏斗）
**何时用**：逐层过滤的转化过程——营销漏斗、销售管线、招聘漏斗、客户旅程转化。
**构图骨架**：
- 3-6 条横带纵向堆叠，每条比上一条窄 ~15-25%；垂直中轴是漏斗脊柱，全部居中对齐。
- 每条带 1 个简单图标（置于左侧）+ 色块本体；带间可加细分隔线。
- 越往下两侧留白越大——下部窄带的外侧空场即呼吸空间。
- 默认画幅 600×800 竖幅（3:4）。
**imagegen 提示词骨架（EN，原文保留）**：
> Clean flat vector illustration of a marketing conversion funnel. Four horizontal bands stacked vertically, each band centered on the vertical axis and each ~20% narrower than the one above. Band 1 (top, widest): ... solid fill, with a simple white megaphone icon centered on the left. ... Each band has crisp straight edges and 8% drop shadow beneath. Thin dividers separate the bands. Composed as a 600×800 portrait funnel block with 12% padding. NO text, letters, numbers, or stage labels anywhere — SVG will overlay all band names.
**坑**：
- 永远上宽下窄、语义是"过滤"——不要画成上窄下宽，也别与"层级"语义的金字塔混用。
- 嵌入文字方案在窄带上难保可读；精确/可编辑标签一律转 SVG。

## pyramid（金字塔）
**何时用**：层级/价值堆叠——能力栈、价值层级、软件架构分层；"底层托举价值"。
**构图骨架**：
- 3-6 条横带自下而上逐层收窄；外形可为真三角（斜边）或阶梯式（直角分层）。
- 每层 1 个简单图标 + 色块本体；配色通常底层深/重 → 顶层亮/浅（或按隐喻反向）。
- 垂直中轴为脊柱，所有层居中对齐；越往上两侧留白越大。
- 默认画幅 600×800 竖幅（3:4）。
**imagegen 提示词骨架（EN，原文保留）**：
> Clean flat vector illustration of a hierarchy pyramid. Five horizontal stepped tiers stacked vertically, each tier centered on the canvas vertical axis and ~18% narrower than the tier below. From bottom to top: tier 1 (foundation, widest) in deeper primary; ... tier 5 (apex, narrowest) in accent gold. Each tier has one simple white iconic symbol centered — a brick, a shield, a gear, an upward arrow, and a star. Thin dividers separate the tiers. Composed as a 600×800 portrait pyramid block with 12% padding. NO text or labels — SVG will overlay tier names.
**坑**：
- 与 funnel 反向：金字塔向上收窄、语义是"堆叠层级"，漏斗向下收窄、语义是"过滤"。

## comparison（对比图）
**何时用**：二元对立——left vs right、before vs after、A/B、传统 vs 新、优劣评估、转变叙事。
**构图骨架**：
- 两个近等分半区 + 明确分割线；横切（最常用：左右分）或竖切（上下分）。
- 每侧有自己的锚元素（人物/图标簇/图表/风格化场景）；结构对称、内容互斥。
- 分割线要干净且有意图：手绘线、垂直细线、几何形或纯留白；外缘 12-15% padding。
- 可选一条弧形 "shift" 箭头在中部横跨两侧。
- 默认画幅 1200×500 双联（各 600×500）。
**imagegen 提示词骨架（EN，原文保留）**：
> The composition is a Before/After horizontal split with a clean vertical hand-drawn divider down the center. ... Left side ("Before"): a simplified stick-figure character with frustrated posture ... Right side ("After"): a confident stick-figure character with a checkmark above ... A curved "shift" arrow bridges left to right at mid-height. Sparse semantic accent: coral red only on left-side pain markers (about 4% area); muted teal only on right-side positive markers (about 3% area). Total color accent under 8%. Composed as a 1200×500 hero banner with 14% inner padding. Hand-lettered text kept to short keywords.
**坑**：
- 对比图的签名是"显式二元性"——分割线不能糊掉；两侧结构对称但内容必须区分（如负向标记/正向标记分色，总强调色 <8%）。

## timeline（时间线）
**何时用**：沿时间轴的进程——公司历史、产品演进、项目路线图、纪元叙事；重点是"时间位置"而非过程箭头。
**构图骨架**：
- 一条清晰的轴（横轴最常用，或竖轴）+ 3-6 个等距里程碑标记（圆点/小形）。
- 每个里程碑配近旁的简单图标/插画，风格平行统一；轴线细而均匀。
- 轴上/下（或左/右）留白充足；方向无歧义：左→右 = 早→晚。
- 可高亮某一里程碑（如中点加强调色环，强调面积 <5%）。
- 默认画幅 1200×350 横幅（3.4:1）。
**imagegen 提示词骨架（EN，原文保留）**：
> Clean flat vector illustration timeline banner. A thin horizontal axis line runs across the canvas at mid-height. Five circular milestone markers are evenly spaced along the axis. ... The third milestone (center) is highlighted with an accent gold ring around it (under 5% accent area). Above each marker is a small simple iconic symbol — a seed, a sprout, a plant, a tree, a forest — telling a growth sequence. Below each marker, a thin vertical tick mark drops to the axis. ... Composed for a 1200×500 hero banner with 12% inner padding above and below the axis. NO text, dates, or labels — SVG labels added externally.
**坑**：
- 时间线讲"何时"，不讲"如何流转"——别加流程箭头；嵌入文字只放短日期锚点（"2020"、"Q1"、"v1.0"），不放描述。

## map（地图）
**何时用**：地理叙事——办公点分布、市场覆盖、区域数据、供应链路线、扩张版图。
**构图骨架**：
- 1+ 个简化陆地轮廓（示意化而非写实），地理位置近似但一眼可辨。
- 3-12 个标记点/图钉落在有意义的位置；可选细连接弧线（航线感）、可选 1-2 个区域加深高亮。
- 海洋/负空间 ≥25% 画布；标记不挤陆地边缘；洲内不画国界——陆地为单色剪影。
- 默认画幅 1280×720 或 1200×500（16:9 / 2.4:1）。
**imagegen 提示词骨架（EN，原文保留）**：
> Clean flat vector illustration of a stylized world map. Simplified continental landmasses (recognizable but not photorealistic) in solid fill, positioned across the canvas with approximate geographic accuracy. Ocean/negative space is secondary light gray. Eight small accent gold circular markers placed at meaningful office locations — three in North America, two in Europe, one in East Asia, one in South Asia, one in Australia. Each marker has a thin pulsing-glow effect at 30% opacity (a subtle ring around the dot). Two thin connection lines (slightly curved, suggesting flight paths) connect three of the markers. ... No country borders within continents — landmasses are single-color solid silhouettes. Composed as a 1280×720 full-bleed world map with 12% padding. NO text, country names, or labels anywhere — SVG will overlay all labels.
**坑**：
- 是示意地图不是写实地球仪；embedded 地名仅限复古地图风等场景，且用前须人工核对拼写与位置。

## scene（场景图）
**何时用**：叙事性画面——案例、品牌故事、生活方式、个人叙事页；"环境中的一个瞬间"。
**构图骨架**：
- 三层纵深：前景（主体 + 紧邻语境）→ 中景（支撑环境/物件）→ 背景（氛围纵深）；背景比前景更淡（大气透视）。
- 人物（如有）按简化剪影处理，环境元素（太阳/灯/树/桌）服务于叙事。
- 光照方向、色温、情绪刻意设定（golden-hour、evening light、morning haze 等）。
- 默认画幅 1200×720 宽幅 / 800×600（16:10 / 4:3）。
**imagegen 提示词骨架（EN，原文保留）**：
> Atmospheric scene illustration with golden-hour cinematic lighting. The composition is a three-layer narrative: foreground left — a softly rendered simplified figure silhouette walking along a path with warm long shadows; middle ground — the warm path winds into a stylized hillside with a few suggested trees; background — atmospheric perspective creates pale warm distance, sky transitioning from amber at the horizon to soft cream at the top. ... No hard outlines — forms emerge from light and shadow. Subtle film grain at 8% opacity. Simplified silhouette figure only — no realistic face. NO text or labels.
**坑**：
- 场景默认 text_policy: none；若必须嵌剧情内文字（场景中的招牌/书封），渲染极易出错，仅叙事必需时用。
- 区分近邻：hero 是单一主宰主体，scene 有环境与叙事；background 无主体，scene 有"居民"。
