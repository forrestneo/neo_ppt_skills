# 叙事模式与视觉验收（蒸馏自 ppt-master，MIT License，github.com/hugohe3/ppt-master）

> 用途：第一部分=整套 PPT 的论证/叙事结构选型（模式 C 端到端出稿前先选一种）；第二部分=交付前视觉验收清单。

---

# 第一部分：叙事模式（5 式）

**选型要点**：
- mode = 论证方式（how you argue），≠ 视觉风格（how it looks）；两者独立解析、任意搭配（pyramid 可以配 swiss-minimal 也可以配 dark-tech）。整套 deck 只解析一种 mode。
- 多意图并存时按正文页的主导论证走向判断（看正文，不看封面或第一个意图词）；用户提供的大纲默认是 Reference，mode 可重组/重排/改标题（保留事实与关系），仅当用户声明其为最终页面计划时原样保留。briefing 对骨架的改造最少。

| 模式 | 中文名 | 适用受众/场合 | 叙事骨架 |
|---|---|---|---|
| `pyramid` | 金字塔·结论先行 | 决策支持、分析、战略、董事会/高管汇报 | 结论先行；结构化论据；数据配支持的对比语境化 |
| `narrative` | 故事弧 | pitch、案例研究、品牌之旅、融资 | 情境→张力→解决；悬念与转折 |
| `instructional` | 教学式 | 培训、教程、讲解、onboarding、知识分享 | 概念分解；分步递进；平行展开 |
| `showcase` | 展示式 | 发布会、品牌揭幕、活动开场、宣传 | 视觉主导冲击；大图/大数字；情绪节奏 |
| `briefing` | 简报式 | 状态同步、参考册、目录、会议包、FAQ | 中立完整可扫读；主题式标题；等权重无论点 |

相邻对判据：要落建议→pyramid，要完整告知不辩论→briefing；故事弧落点→narrative，结论前置再支撑→pyramid；论证经故事传播→narrative，存在感领先→showcase；逐步建理解→instructional，完整参考供扫读→briefing。"Keynote-style" 是 showcase 节奏请求（主想法+hero 级视觉+reveal 韵律），不是视觉风格。

## pyramid（金字塔·结论先行）
**适用**：要"先给结果"的决策受众——高管、董事会、投资人；用于决策支持、分析、战略汇报。
**叙事骨架**：页面标题即结论，正文在其下展开结构化证据。开场 SCQA：Situation 建立共识语境 → Complication 提出张力/问题 → Question 过渡出隐含问题 → Answer 给建议并结构化展开（来源支持时用 MECE）。数据须配"有依据的对比"做语境化（当该对比会改变决策时）；绝不虚构前期、基准、竞对、目标或排名。拆解驱动/分段/选项时分支须实质区分并覆盖决策所需，保留真实重叠或公开缺口，不硬凑完美 MECE。
**标题写法**：断言式（assertion title）——写发现，不写主题：
- "Market Overview" → "Domestic market grows 23% YoY, outpacing the global average"
- "Challenges" → "Three structural contradictions block scaled deployment"
- "Our Solution" → "Three-phase path: Focus, Expand, Scale"
**页面结构倾向**：
- 标题（结论）→ 一句话 takeaway → 支撑证据；每个正文页围绕一个决策相关问题，关系紧密的子问题可同页。
- 拆解页（driver tree / MECE breakdown / 2×2 矩阵）承担分析载荷。
- 每个数据页标注来源（Source attribution）。
**备注**：备注以 takeaway 开头再给紧凑论据，语域沉稳、权威；数字配支持的对比（"23% — nearly double the industry's 12%"），否则直接讲含义；口语中百分比拼成单词更自然。

## narrative（故事弧）
**适用**：pitch、案例研究、品牌之旅、融资路演——要点先情感落地、再逻辑落地。
**叙事骨架**：全 deck 走 scenario → conflict → resolution 弧线，合适的 beat 内也可复现：设置利害 → 升级张力 → 解决 → 桥接下一 beat，不强求每页完整弧。在恰当处提问、在证据落点的 beat 作答（悬念+回报）；抽象点锚定在主角/时刻/具体利害上（"a team that shipped in two weeks instead of three months"）；素材支持处用 reframe、reveal 或利害转换推进——序列要"动"，不是平铺重贴标签。
**标题写法**：标题是推进弧线的 beat，不是标签——如 "Then the numbers stopped adding up"。
**页面结构倾向**：
- 密/疏 beat 依张力、回报与观众疲劳而变，不做机械交替；章内连续、章间变化。
- 视觉重量引导视线的 beat：hero 图、单一焦点数字、pull quote。
- 结构服务于弧线，而非网格。
**备注**：对话式叙述（与观众聊天而非念报告），页面内也可走 scenario-conflict-resolution；反问造悬念并从上一页桥接；比喻化抽象（"like adding a turbocharger"）；数据口语化（"nearly a third"、"more than doubled"）。

## instructional（教学式）
**适用**：培训、教程、讲解、onboarding、科学/知识分享——目标是逐步建立理解。
**叙事骨架**：先分解后排序：简单 → 复杂、前置 → 依赖、概览 → 细节。每页是一个聚焦的学习单元（相关概念在其"关系本身是学习目标"时可同页）；兄弟概念平行展开——同形状同深度，便于对比映射；用具体例子或类比落地抽象原则，按学习者前置需求安排例子与讲解先后；路标式定向（已覆盖什么 → 接下来什么）。
**标题写法**：主题式，写"本页教什么"，清楚优先于聪明——如 "How attention weights are computed"、"Step 2 — Scoring each token against the query"。
**页面结构倾向**：
- 流程用编号步骤/有序流；兄弟概念用平行卡片。
- 图示增量搭建，并标注当前正在讲解的部分。
- 具体例子锚定抽象点（确能提升迁移/理解时才用）。
**备注**：耐心解释语域——先定义后使用、先类比后原理、预答学习者疑问、稳速并路标过渡（"now that we have X, we can ask Y"）；数据口语化。

## showcase（展示式）
**适用**：产品发布、品牌揭幕、活动开场、宣传 deck——存在感优先（"Keynote-style"即此节奏：一个主想法、hero 级视觉、reveal 韵律）。
**叙事骨架**：图像/数字领先、文字辅助——以 hero 图、大数字或短语建立主导视觉层级，辅助元素可同页但不得争焦点。情绪节奏"蓄势—释放"：连续强势页中插一页安静的，按感受而非密度定速。每页围绕一个放大表达的核心要点；观众需要理解或信任该要点时保留支撑语境。reveal 结构：先藏后露（产品/结果/tagline），求最大效果。
**标题写法**：短而 evocative 的短语，不是句子——如 "Meet the new standard."、巨大数字 "10×"。
**页面结构倾向**：
- 全出血图像 + 覆盖文字；单一 hero 数字/短语 + 大量留白。
- 封面/章节页大胆用主题色造氛围。
**备注**：energetic、evocative 语域——短促有力的句子，围绕视觉渲染情绪与期待，让画面自己干活。

## briefing（简报式）
**适用**：状态同步、参考册、目录、会议材料、FAQ、数据参考——完整可扫读，无论点无故事。
**叙事骨架**：刻意无论点：不造结论先行（那是 pyramid）、不造转折（那是 narrative）——素材即"这里是事实"。core_message 写覆盖面不写主张（写"本页铺开 Q3 各团队人数"，而非"人数正在向工程集中"）。完整优先于选择性：给出受众扫读所需的全部参考集，而非只留支持某论点的条目；兄弟条目平行等权，可快速对比定位；按可预测顺序分节导航（时间/类别/字母序）。
**标题写法**：主题式（topic title），直白命名主题——如 "Q3 headcount by team"、"Supported file formats"、"Q3 deliverables by workstream"——是 pyramid 断言式标题的刻意反面。
**页面结构倾向**：
- 表格、定义列表、状态卡、参考网格、dashboard——可扫读结构优先于 hero 构图。
- 节内等层级，兄弟页布局一致，视线始终知道往哪看。
- 真正关键的数字（总量/状态旗/例外）可凸出；内容没有 punchline 就不发明。
**备注**：平稳、事实、平铺的 read-out 语域；数字照直说；无反问无悬念。

---

# 第二部分：视觉验收清单

**前置与纪律**：顺序为 页面完成 → 静态检查器通过（字号锚点 ±2px 漂移、id 唯一、XML 合法、动画配置等由它把关，不重复检查）→ 渲染 PNG → 本清单；静态检查未跑或未过 → `prereq_failed` 中止。软违例只在"明显坏"时动手，拿不准就放过（宁欠勿震荡）；默认 1 轮迭代预算。

### 前置（渲染 sanity）
- [ ] PNG 存在且非空，尺寸等于记录的 png_width × png_height
- [ ] 背景色像素 <99%（仅防空白渲染；深色稀疏版式不算失败）

### 版面越界与结构（硬违例，逐条必改）
- [ ] 无元素 bbox 超出画布 view_box（越界 → 缩小或移回画布内）
- [ ] 文本未溢出其视觉容器（溢出 → 降字号或断行）
- [ ] 规范声明的页码/页眉/页脚未被遮挡、缺失或越界；只恢复已声明的页框，禁止发明未声明的 chrome
- [ ] 规范要求的关键元素在渲染中存在（缺失 → 按规范重建）

### 重叠与碰撞
- [ ] 任意两个 `<text>` bbox 不相交（同一 text 内 tspans 除外；相交 → 重定位或缩放）
- [ ] rect/circle/path 无 z 顺序违背语义的 bbox 重叠（违例 → 拉开间距）
- [ ] 检测顺序固定：越界/溢出/页框 → 文本与元素碰撞 → 可读性 → 图像与关键元素

### 可读性与用色
- [ ] 小字对比度 ≥4.5；字号 ≥24px 的文字 ≥3.0
- [ ] 复杂图像上直接压文字必须加 scrim 底衬
- [ ] 对比修复受限：两色皆非品牌 token → 只允许加 `<rect>` scrim 或把文字提到 ≥24px；任一色为品牌 token → 不动 SVG，记入 brand_review.json 交人工做 deck 级决策（例："正文 token 从 `#6E7681` 提到 `#8B949E`，全 deck 生效"）

### 图像
- [ ] `<image>` 非空、未损坏、无严重变形（坏 → 修 href；adaptive 用 meet 或更安全裁切；新增"完整显示"要求须回到 Crop Policy 与锁投影）

### 留白与纵向节奏（软违例）
- [ ] 同一文本块相邻基线间距 ≥1.05× 较大字号（过紧 → 开到 1.15–1.3×）
- [ ] 同一块内非装饰性空白 ≤150px（>150px 视为空洞 → 收紧；breathing 页豁免）

### 对齐与网格
- [ ] 主视觉/标题块落在规范明确声明的锚点上（画布中心仅在计划要求居中时算锚；有意非对称、留白、图像焦点放置豁免）
- [ ] 同列 x / 同行基线差 ≤4px（本应共线而超差 → 吸附网格）
- [ ] N 卡行相邻间距差 ≤平均值的 5%（超差 → 重新均匀分布）

### 排版细节与强调
- [ ] CJK letter-spacing / font-size ≤2%（>5% 为违例 → 降下来）
- [ ] 装饰色不与主强调色争抢：多个无语义装饰色互抢 → 并入既有强调色；品牌色/数据系列色/状态色等语义色豁免，绝不重涂锁定元素
- [ ] 页面最显眼元素 = 规范声明的主元素（不符 → 重新定比例）

### 图文关系与呼吸页
- [ ] 图注距其图像 ≤60px；busy 图上的文字必须有 scrim；明显无目的的图移除
- [ ] breathing 页无 ≥3 张圆角卡的网格（违例 → 换成裸文本或单一 hero）

### 修改纪律（Don't-touch，与硬违例同权重）
- [ ] 不动品牌决策：色彩 token、字体族、几何风格
- [ ] 不动布局重构：列数、图表类型、分节
- [ ] 不动内容：不增删文案；文字编辑仅限位置、字号（锚点 ±2px 内）、间距、字距、对齐、scrim
- [ ] 不动其他文件：design_spec / spec_lock / 动画 / image_prompts / 素材图 / 其他页 SVG
- [ ] 原子编辑：一次修复只改一处，禁止批量多元素替换
- [ ] 首次编辑前备份：`svg_output/<page>.svg` → `.review/backup/<page>.iter<N>.svg`
- [ ] 修复引入新硬违例 → 回滚备份，状态 needs_human（"rolled back fix X — created Hard Y"）；软规则每轮 ≤2 处修复，余下记 untouched_concerns
- [ ] 需重新解读设计规范才能判定的"违例" → needs_human + 一行 suggested_fix_summary
- [ ] 交付判定：0 硬违例且余 ≤1 软违例 → ok（未动手）/ fixed（动过手）；否则 needs_human
