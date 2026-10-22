# 风格维度系统与选型组织（蒸馏自 baoyu-skills / guizang-ppt-skill / frontend-slides）

> 来源与许可：[baoyu-skills](https://github.com/JimLiu/baoyu-skills)（宝玉，四维风格系统）、
> [guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)（归藏，MIT，双视觉系统）、
> [frontend-slides](https://github.com/zarazhangrui/frontend-slides)（张咋啦，样张先行）。
> 定位：`visual-styles.md` 是"18 式平铺"，本篇是**风格系统的组织法**——
> 怎么让风格可组合、可路由、可渐进披露，而不是每次写一篇新文档。

## 一、四维风格参数化（baoyu：5×7×5×3 = 525 组合空间）

风格不是一个名字，是四个独立维度的组合。新增风格 = 加一行四元组，不是写一篇文档：

| 维度 | 取值 | 关键约束 |
|---|---|---|
| **Texture 质感** | clean / grid / organic / pixel / paper | grid=5-10% 透明度细网格（工程感）；organic=纸纹笔刷手绘边；pixel=粗像素格关抗锯齿；paper=做旧纸纹晕染 |
| **Mood 色彩** | professional / warm / macaron / cool / vibrant / dark / neutral | 每值带**完整 hex 调色板**（如 macaron=奶油底 #F5F0E8+四粉彩+珊瑚点缀） |
| **Typography 字体气质** | geometric / humanist / handwritten / editorial / technical | headline+body 双描述 + 具名锚点字体（editorial≈Playfair/Didot；technical=Inter+等宽） |
| **Density 密度** | minimal / balanced / dense | 附**受众映射**（高管 minimal、专家 dense）与**页型映射**（封面/章节/金句=minimal、数据页=dense） |

- **兼容矩阵**：每维登记 works-best-with / avoid-with（grid 纹理 avoid 手写体；paper avoid geometric 与 minimal；dense avoid handwritten+organic）——组合合法性有据可查，不靠感觉。
- **预设 = 四元组**：如 blueprint = grid+cool+technical+balanced；17 个预设全是一行四元组派生，另留"预设外推荐组合"示范自定义。
- **内容信号自动路由**：源文本关键词→预设（tutorial→sketch-notes、saas/dashboard→notion、investor→corporate），匹配不到回落默认——风格选择先推荐、用户可覆盖。

## 二、STYLE_INSTRUCTIONS：风格的单一事实源（baoyu）

风格选定后固化成一个七节结构块，嵌进大纲：**Design Aesthetic（2-3 句）/ Background
（texture+hex）/ Typography（headline+body）/ Color Palette（Role/Hex/Usage 表）/
Visual Elements（texture×mood 交叉生成：grid+cool→技术示意图标注尺寸线）/
Density Guidelines / Style Rules（Do 5 条 / Don't 5 条）**。

- 每页提示词 = base 模板 + 复制该块 + 本页内容，**禁止回头重读风格文件**（一致性 + 省 token）；
- 每页提示词**先落盘成 prompts/NN-slide.md 再调用生图**——prompt 目录即事实源，改稿先改 prompt 文件再重生成，可复现可换后端重放；
- 文本错的位图**禁止代码盖字修补**，只能改提示词重出并留废稿对比；
- 生图模型不认识字体名——字体必须译成视觉特征描述（"bold geometric sans-serif
  with perfect circular O shapes"而不是 "Futura"）。

## 三、双视觉系统与"类名唯一事实源"（guizang）

- **一个模板 = 一套完整视觉系统**：CSS/字体/装饰/交互全部预置，生成只做
  "拷模板 → 换主题色变量 → 粘版式骨架"。**类名的唯一事实源是模板的 style 块**——
  动手前先通读到 `</style>`；同名类在两套系统里语义完全不同，**一套 deck 只选一套，禁止混用**。
- **主题色只从预设选，拒绝自定义 hex**（"保护美学比给自由更重要"）；全模板颜色
  走 `var(--*-rgb)` 变量，换主题只改根节点几行。
- **chrome 与 kicker 分工**：chrome（页眉栏目标签）跨页稳定；kicker（本页钩子）每页不同——两者写重复是"一眼 AI"反例。
- **字号-字重反比阶梯（瑞士风精华，可直译进引擎）**：≥8vw 大字用 200 极细、
  13-15px 小字用 500-600；**同页小字字重必须 ≥ 大字**；大字号双约束限高
  `min(Xvw, Yvh)` 且 Y≥1.6X（16:9 下 1vw≈1.78vh，否则被视口截断缩水 20%）；
  **中文标题按字数分档降字号**：≤8 字一档、9-12 字降到约 0.8 档、3 行先改写标题。
- **主题节奏硬规则**：每页标 light/dark/hero 四态之一；**禁连续 3 页同主题**；
  8 页以上必须 ≥1 深色 hero + ≥1 浅色 hero；每 3-4 页插一个 hero 页换气。
- **版式内容类型契约**：每个版式登记"适用内容类型 / 必须用 / 严禁用"——
  **数据专用版式（KPI 塔/横条/台账）严禁用于无数据的概念列举**（"给概念编百分比
  会被识破"）；结构专用版式必须真有闭环/矩阵/层级。freelayout 引擎已落地此契约。

## 四、样张先行与三层渐进披露（frontend-slides）

- **Show, don't tell**：不问抽象偏好，直接出 3 张**用户真实内容的第一页**样张：
  1 个安全预设 + 至少 1 个大胆模板 + 1 个 wildcard（自创）；保守场合 wildcard
  收敛、表达性场合放飞。**预览真实性规则**：样张禁止出现"选项 A/模板名/预览"
  等内部字样，页眉页脚全用真实 deck 标题日期——样张即成品第一页。
- **模板文档三层分级（渐进披露省 token）**：
  1. **selection-index**（机器可读紧凑索引：mood/tone/formality/density/scheme/
     best_for/avoid_for 六到八字段×每模板一行）——选型只读这个；
  2. **preview 卡**（每模板约 50 行：视觉快照一段话 + 调色板 hex 清单 + 5 条
     signature moves + CJK 注意事项）；
  3. **design.md 全量**（选中才加载：机器可读 YAML tokens + 散文规则 + 专属
     CJK 章节含"已知缺口"如思源黑体无斜体轴）。
- **design.md 两个深度栏目**值得每套风格文档补上：**Signature Treatments
  "非可选清单"**（"标题中的强调词必须金色斜体衬线——没有这条就不是本系统"）
  与 **Iteration Guide**（给未来增改者守系统的守则）。

## 五、接线

- 模式 A 选风格：先查第一节四维组合 + 信号路由，用户点名风格后按第二节落
  STYLE_INSTRUCTIONS 块；样张确认走第四节三明治混样（freelayout 出三张真实
  首页成本极低）。
- 模式 E 选主题色：`--theme` 13 套 + 双约束限高与字数分档已内建引擎（title_tier）。
- 模式 D 选模板页：selection-index 思路对应 `deck_cli find` 的 use_for 筛选，
  渐进披露已天然成立（show 单页后才见全量槽位）。
