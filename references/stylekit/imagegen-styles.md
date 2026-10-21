# imagegen 风格词汇（20 渲染手法 + 14 图像色板）

> 蒸馏自 [ppt-master](https://github.com/hugohe3/ppt-master)（MIT License）references/image-renderings 与 image-palettes。
> 用途：模式 A（imagegen）组提示词时的风格词汇表。渲染手法=画面怎么画（材质/笔触/构图语言），色板=颜色怎么用（含适配/互斥渲染）。两者组合前先查色板的"适配渲染"列。

通用规则：整套 PPT 锁定一种渲染手法，同 deck 内所有 AI 图共用，不换手法；源文件中的 hex 均为示例值，实际填充用 deck 色彩锚点替换。

---

## 一、渲染手法

| 手法 | 中文名 | 一句定义 |
|---|---|---|
| vector-illustration | 扁平矢量插画 | 干净扁平矢量、粗几何形+实色填充，通用安全默认 |
| flat | 现代扁平几何 | 比 vector 更大胆的几何色块，更有品牌感 |
| minimalist-swiss | 极简瑞士网格 | 瑞士网格/包豪斯式克制，激进留白 |
| glassmorphism | 玻璃拟态 | 磨砂玻璃半透明叠层面板+柔和阴影 |
| 3d-isometric | 3D 等距 | 30° 等距 3D 体块+柔和阴影，科技架构感 |
| digital-dashboard | 数字仪表盘 | 精修 UI/数据可视化产品截图感 |
| corporate-photo | 商业摄影 | 编辑级摄影、真实主体、专业调色 |
| blueprint | 工程蓝图 | 网格上的技术示意图、等宽线、克制用色 |
| editorial | 杂志编辑风 | 杂志式信息图版式、克制用色、编辑节奏 |
| sketch-notes | 手绘涂鸦笔记 | 暖米纸+黑色手绘线+粉彩色块，亲和教育感 |
| ink-notes | 墨线视觉笔记 | 纯白纸+黑墨线+稀疏语义色，宣言感 |
| chalkboard | 黑板粉笔 | 深色板面+粉笔笔触，课堂感 |
| paper-cut | 剪纸叠层 | 多层彩纸剪裁叠放、剪刀边+纸影 |
| watercolor | 水彩 | 柔边颜料晕染、留白即画面 |
| warm-scene | 暖光场景 | 黄金时刻电影光叙事插画 |
| screen-print | 丝网印刷海报 | 2-5 色丝网海报、半调网点、大胆剪影 |
| vintage-poster | 复古中世纪海报 | 1950-70 年代中世纪现代海报、半调+纸纹 |
| fantasy-animation | 手绘动画绘本 | 吉卜力/迪士尼式手绘温暖 |
| pixel-art | 像素艺术 | 8-bit 复古游戏像素网格、无抗锯齿 |
| nature | 有机自然插画 | 植物自然母题、大地色、有机曲线 |

### vector-illustration（扁平矢量插画）
**定义**：干净扁平矢量插画，大胆几何形+实色填充+自信留白，通用 PPT 默认安全选项。
**提示词核心（EN，原文保留）**：Clean flat vector illustration with bold geometric shapes and confident solid fills; crisp outlines (1.5-2px equivalent stroke weight, consistent across all elements) define every form; no gradients within shapes — color is applied as flat blocks; subtle shadow only where it adds depth (soft 8% opacity drop, no harsh edges); composition is grid-aware and balanced, with deliberate negative space carrying as much weight as filled areas; iconography simplified to essential geometry, recognizable at small sizes.
**禁忌**：色块内禁渐变，禁噪点/纸纹/笔触痕迹；不做透视渲染。

### flat（现代扁平几何）
**定义**：现代扁平设计，大胆几何色块与自信色彩分区，比 vector 更有设计意图与品牌感。
**提示词核心（EN，原文保留）**：Modern flat design illustration with bold geometric blocks and confident color zones; forms simplified to essential silhouettes — circles, rectangles, triangles, rounded squares; no outlines, or very thin uniform outlines as a deliberate accent; flat solid fills with deliberate juxtaposition (one block of saturated color against a large field of neutral); subtle layered overlap creates flat depth without shadows; one dominant block, one secondary, one accent.
**禁忌**：禁阴影——层次只靠形状叠压与颜色对比。

### minimalist-swiss（极简瑞士网格）
**定义**：严格瑞士网格极简主义，一切吸附网格、几何基元、大量负空间，最克制的渲染。
**提示词核心（EN，原文保留）**：Strict Swiss-grid minimalism; every element snaps to grid lines, deliberate column-and-row alignment carries the whole page; forms reduced to essential geometric primitives — clean rectangles, perfect circles, single-weight lines; sans-serif typographic character, often Helvetica-adjacent, set with rigorous spacing; color applied sparingly — one primary block, large fields of white or near-white, single accent; negative space carries as much weight as filled areas.
**禁忌**：No gradients, no shadows, no texture, no decoration；accent 面积不超过画布 2-3%（一条细线或一个小点）。

### glassmorphism（玻璃拟态）
**定义**：磨砂玻璃半透明叠层面板浮于柔和渐变底上，大而软的阴影造真实纵深，现代 App UI 质感。
**提示词核心（EN，原文保留）**：Modern glassmorphism aesthetic; layered semi-transparent panels with frosted-glass blur (gaussian blur ~10-15px over background) floating slightly above a soft gradient background; panel edges subtly defined with thin 1px highlight strokes (whitespace at top/left, slight shadow at bottom/right) suggesting refraction; drop shadows under panels large and soft (15-25% opacity, generous spread); panel fills semi-transparent (~40-60% opacity) tints; interior content uses crisp solid color shapes.
**禁忌**：忌重饱和——玻璃感适合中亮色调；primary 过深时只用于面板内部内容形状，不进背景渐变。

### 3d-isometric（3D 等距）
**定义**：标准 30° 等距投影 3D 体块（盒/层/卡），单色暗面+柔和落影，科技架构与产品结构首选。
**提示词核心（EN，原文保留）**：3D isometric illustration in true 30°/30°/30° projection; all edges crisp and uniform — no perspective distortion, no vanishing points; surfaces use flat solid fills with subtle tonal shifts (a single darker shade for shadowed faces, ~15% darker than the light-facing face); composition emphasizes stackable, modular forms — boxes, blocks, layers, cards floating in arrangement; soft 8% drop shadows beneath floating elements.
**禁忌**：禁透视灭点与光泽/照片级材质——只用平涂+调性暗面。

### digital-dashboard（数字仪表盘）
**定义**：精修 UI/数据可视化美感，圆角卡片+均匀软阴影+风格化图表元素，像产品截图。
**提示词核心（EN，原文保留）**：Polished digital UI / dashboard aesthetic; clean card-based layout with rounded corners (8-12px radius), uniform soft shadows (8% opacity, slight Y-offset), crisp pixel-aligned edges; chart-like visual elements (bar graphs, line graphs, sparklines, donut segments, KPI tiles) appear stylized — recognizable as charts but without specific data values; NO text, no numbers, no chart labels, no axes — pure visual chart elements only.
**禁忌**：禁任何文字、数字、图表标签、坐标轴。

### corporate-photo（商业摄影）
**定义**：编辑级摄影风格，真实人物/产品/环境，自然构图+专业调色，HEX 体现为调色倾向而非填色。
**提示词核心（EN，原文保留）**：Editorial photography style with natural composition and professional color grading; rule of thirds, leading lines, deliberate foreground/background separation; lighting natural or studio-soft, never harsh; shallow depth of field — subjects sharp, background gently blurred; diverse, professionally attired subjects rendered photorealistically; no posed stock-photo stiffness, no exaggerated expressions, no fashion-shoot artificiality.
**禁忌**：禁摆拍图库僵硬感、夸张表情、时尚大片式做作。

### blueprint（工程蓝图）
**定义**：技术示意图美学，细网格上的精确线条+示意化基元，工程精确感与克制用色。
**提示词核心（EN，原文保留）**：Technical blueprint schematic style; clean precise lines on an implied or subtle grid, with deliberate geometric rigor — right angles, parallel rules, measured spacing; elements simplified to essential schematic forms — boxes, rounded rectangles, connector lines, anchor dots, callout markers; crisp 1.5px uniform stroke; subtle grid background at very low opacity (5-8%); connector lines route at right angles, with small dot anchors at junctions.
**禁忌**：No textures, no shading, no painterly artifacts——纯平面示意，无明暗。

### editorial（杂志编辑风）
**定义**：杂志式编辑插画，精密层级+自信负空间+编辑节奏排版，财经/新闻/解读类默认。
**提示词核心（EN，原文保留）**：Magazine-style editorial illustration with sophisticated visual hierarchy and confident negative space; editorial pacing — one dominant focal area, deliberate alignment to invisible columns, generous gutters between blocks; color restrained and balanced — typically one rich brand tone, one neutral, one subtle accent; optional duotone or limited-color treatment reinforces the magazine feel; refined thin precise rules as dividers; subtle paper grain at 5-10% opacity.
**禁忌**：平涂+有意分层，禁阴影。

### sketch-notes（手绘涂鸦笔记）
**定义**：暖米纸上的黑色微抖手绘线+柔和粉彩色块，最亲和的渲染，教育/培训/科普。
**提示词核心（EN，原文保留）**：Warm hand-drawn sketchnote style; lines with deliberate slight wobble, never perfectly straight — the human-hand quality of a thoughtful teacher's whiteboard; soft color blocks as restrained pastel tints; color fills do not completely reach their outlines (slight hand-painted overshoot); simple cartoon icons and small doodle decorations (stars, sparkles, dots, underlines) appear sparingly; subtle paper grain at 8-12% opacity; airy composition with generous whitespace.
**禁忌**：线条绝不完全笔直；标注文字仅限 ≤2 词的关键词。

### ink-notes（墨线视觉笔记）
**定义**：纯白纸+黑墨微抖线+稀疏语义色（Mike Rohde sketchnote 传统），比 sketch-notes 更锐利专业、宣言感。
**提示词核心（EN，原文保留）**：Professional hand-drawn visual-note style on a clean paper field; line work with slight wobble — confident, intentional, the human-hand quality of a thoughtful whiteboard session; hand-lettered titles bold and slightly oversized; color is intentionally sparse: line work dominates ~85% of the visible content, one or two semantic accents cover less than 10% combined; backgrounds and shape fills remain mostly empty; pure white background, no paper grain.
**禁忌**：彩色 accent 合计面积 <10% 画布；纸纹禁用（纯白底）。

### chalkboard（黑板粉笔）
**定义**：深绿/近黑板面上的粉笔笔触美学，粉笔灰颗粒质感，教学/教程/课堂氛围。
**提示词核心（EN，原文保留）**：Classroom chalkboard aesthetic; dark green or near-black slate background with visible subtle chalk-dust texture (15-25% opacity); all marks appear as soft chalk strokes — slightly diffused edges, off-white or pastel colors that look powdery rather than saturated; hand-drawn lines confident but with the characteristic dry-medium quality of real chalk; white chalk dominates, one or two pastel accents (yellow, soft pink, light cyan) appear sparingly.
**禁忌**：材质色倾向极强（深板+浅粉笔），仅当 deck 底/字角色支持该对比时可用；accent 不得粉彩化。

### paper-cut（剪纸叠层）
**定义**：多层彩纸剪裁叠放的手作质感，剪刀边不规则+层间柔和纸影，教育/儿童/文化/节庆。
**提示词核心（EN，原文保留）**：Layered paper-cut craft aesthetic; the composition is built as if cut from colored construction paper and stacked in layers; each shape has crisp scissor-cut edges (slightly irregular, hand-aware, not mathematically perfect) and casts a soft 8-12% drop shadow onto the layer beneath; each color appears as its own paper sheet with subtle paper grain at 10-15% opacity; forms are simplified and stylized — recognizable as paper craft rather than illustration.
**禁忌**：全图禁描边——形状只由纸边定义（no outlines anywhere — shapes are defined by paper edges only）。

### watercolor（水彩）
**定义**：柔边水彩颜料晕染，形体由颜料变深处浮现而非轮廓线，留白纸面即构图一部分。
**提示词核心（EN，原文保留）**：Watercolor painting style with soft painterly edges and natural color bleeding; forms emerge from washes of pigment rather than outlines — sometimes a subject is suggested by where the wash darkens; color pools and bleeds at edges, with characteristic wet-on-wet zones; negative space is part of the artwork (untouched paper); optional very subtle pencil lines suggest underlying structure; paper grain at 12-18% visible; depth through saturation gradient — saturated foreground, paler background.
**禁忌**：禁轮廓线定形；无明确线稿。

### warm-scene（暖光场景）
**定义**：黄金时刻电影光插画场景，明确光源+长软影+大气透视，成长故事/品牌叙事；介于水彩与实拍之间。
**提示词核心（EN，原文保留）**：Atmospheric scene illustration with golden-hour cinematic lighting; forms are softly rendered — recognizable but not photorealistic, with soft edges and intentional light direction; a clear primary light source (low sun, lamplight, window light) casting long soft shadows; foreground subject, middle-ground context, atmospheric background; no hard outlines — forms emerge from light and shadow; subtle bloom and film grain at 8% opacity.
**禁忌**：禁硬轮廓；人物只用简化剪影/无写实面孔；不得用通用橙色滤镜抹掉冷色品牌身份。

### screen-print（丝网印刷海报）
**定义**：大胆丝网海报，2-5 色平涂+半调网点+轻微套印错位，剪影化主体，文化/媒体/电影封面。
**提示词核心（EN，原文保留）**：Bold silkscreen poster art with limited flat color palette — 2-5 flat colors maximum; halftone dot patterns add texture in transition zones (dot density varying from dense to sparse); slight color layer misregistration (one color block offset by 1-2 pixels) gives an authentic silkscreen feel; subjects rendered as bold silhouettes with stencil-cut edges — no fine detail, no realistic anatomy; subtle paper grain texture at 15% opacity; negative space and geometric framing.
**禁忌**：色块内禁渐变；主体禁细节与写实解剖。

### vintage-poster（复古中世纪海报）
**定义**：1950-70 年代中世纪现代海报语言（旅行海报/爵士封面/Saul Bass），有限平涂色+半调/纸纹+复古几何。
**提示词核心（EN，原文保留）**：Mid-century modern poster aesthetic — the design language of 1950s–1970s travel posters, jazz album covers, and Saul Bass title cards; bold geometric shapes with rounded organic edges, often slightly off-axis for retro tension; color applied in limited flat blocks (typically 3-5 colors total) with subtle halftone or screen-print texture over the fills; lines thick but hand-aware; imagery stylized and reduced — never photorealistic; paper grain at ~10% opacity for tactile age.
**禁忌**：忌照片级写实；深度只靠形状叠压，禁阴影。

### fantasy-animation（手绘动画绘本）
**定义**：吉卜力/经典迪士尼绘本式手绘动画，柔光+氛围透视+友好卡通角色，儿童/故事/治愈。
**提示词核心（EN，原文保留）**：Hand-drawn animation style inspired by Ghibli and classic Disney storybook aesthetics; forms are softly rendered with painterly fills and gentle outlines — never harsh; dreamy warmth may derive through soft window light, gentle glow, morning haze, brush texture, atmospheric perspective; characters stylized in a friendly cartoon manner — large expressive eyes, simplified anatomy, warm body language; strong atmospheric perspective — distant elements paler and softer; hand-painted animation cel.
**禁忌**：人物一律柔和卡通剪影，无写实面孔。

### pixel-art（像素艺术）
**定义**：8/16-bit 复古游戏像素美学，严格像素网格+无抗锯齿+有限复古色板，游戏/怀旧。
**提示词核心（EN，原文保留）**：8-bit pixel art style with strict pixel-grid alignment and no anti-aliasing; all elements constructed from discrete colored pixels — visible chunky pixel edges, sharp transitions between color blocks, no soft gradients; color palette limited and intentionally retro (often 16-32 distinct colors total); optional 1-pixel-wide outlines in darker shades of the fill color; composition often references classic NES / SNES / arcade game framing; all elements visibly pixel-stepped — no smooth curves.
**禁忌**：禁抗锯齿与平滑曲线；角色不做细致面孔。

### nature（有机自然插画）
**定义**：植物与自然母题的有机插画，柔和不对称曲线+微降饱和大地色，环保/康养/户外/食品。
**提示词核心（EN，原文保留）**：Organic illustration style with botanical and natural motifs; forms are softly curved and asymmetric — leaves, branches, organic curves, irregular shapes that feel grown rather than drawn; color palette leans earthy and slightly muted — forest greens, warm earth browns, terracotta, soft cream, occasional sky blue; outlines minimal or absent — forms are defined by color and texture; subtle organic textures (leaf veins, wood grain, stone speckle) appear sparingly.
**禁忌**：构图忌网格对齐（never grid-aligned），忌硬轮廓线。

---

## 二、图像色板

| 色板 | 中文名 | 气质 | 适配渲染 | 禁用渲染 |
|---|---|---|---|---|
| cool-corporate | 冷调商务 | 稳重克制专业 | vector/flat/3d-isometric/dashboard/blueprint/photo/editorial ✓✓ | sketch-notes、fantasy-animation、pixel-art、dark-cinematic 合并 |
| dark-cinematic | 暗黑电影感 | 高级暗场低光 | 3d-isometric/dashboard/photo/warm-scene/screen-print ✓✓ | sketch-notes、fantasy-animation、nature、chalkboard、macaron、warm-earth |
| duotone | 双色海报 | 双色纪律海报感 | screen-print、flat ✓✓ | corporate-photo、watercolor、dashboard、3d-isometric 等 |
| earthy-dusty | 莫兰迪灰调 | 降饱和克制 | watercolor/editorial/photo/flat/vector ✓✓ | tech-neon、vivid-launch、pixel-art、dashboard、chalkboard |
| editorial-classic | 经典杂志 | 高级杂志克制 | editorial/vector/ink-notes/photo ✓✓ | sketch-notes、fantasy-animation、pixel-art |
| frost-ice | 冰霜清冷 | 近白冷调洁净 | dashboard/vector/flat/swiss/glass ✓✓ | sketch-notes、chalkboard、fantasy-animation、pixel-art、dark-cinematic |
| jewel-tone | 宝石浓色 | 浓郁奢华夜宴 | editorial、corporate-photo ✓✓ | sketch-notes、chalkboard、pixel-art、fantasy-animation、dashboard |
| macaron | 马卡龙粉彩 | 粉彩亲和温暖 | sketch-notes/flat/vector/watercolor/fantasy/chalkboard ✓✓ | tech-neon、dark-cinematic、blueprint、corporate-photo、dashboard |
| mono-ink | 黑白墨线 | 黑白+语义色 | ink-notes、editorial ✓✓ | sketch-notes、watercolor、fantasy、nature、tech-neon、dashboard、photo、chalkboard |
| nature-organic | 自然大地色 | 大地色康养 | nature/watercolor/warm-scene/fantasy/sketch-notes/photo ✓✓ | tech-neon、dark-cinematic、dashboard、blueprint、pixel-art |
| sunset-gradient | 落日渐变 | 暖渐变流动 | flat、watercolor、warm-scene ✓✓ | swiss、blueprint、mono-ink、pixel-art、sketch/ink-notes、chalkboard、photo |
| tech-neon | 科技霓虹 | 高能未来高对比 | 3d-isometric/dashboard/flat/blueprint ✓✓ | sketch-notes、watercolor、fantasy、nature、corporate-photo |
| vivid-launch | 高饱和发布 | 高饱和夺目 | flat/vector/3d-isometric/screen-print/pixel-art ✓✓ | sketch-notes、ink-notes、nature、watercolor、warm-scene |
| warm-earth | 暖调大地 | 温暖接地人性化 | vector/flat/sketch-notes/watercolor/warm-scene/fantasy/nature/photo ✓✓ | tech-neon 主题、dark-cinematic、blueprint |

### cool-corporate（冷调商务）
**气质与适用**：稳定、专业、克制——咨询/金融/B2B 默认色板，可信度即视觉信号。
**用色行为**：secondary 浅灰大面积留白垫底，primary 深色做对角主块，accent 仅一条细线+一个小点；示例：浅灰 `#F8F9FA` 占 65%，深蓝 `#1E3A5F` 约 28%，金 `#D4AF37` 合计 <5%，无额外色。
**提示词片段（EN）**：secondary light gray carries 65% of the canvas as calm breathing space; primary deep navy forms a confident diagonal block; accent gold appears only as one thin horizontal line and a single small geometric dot, together under 5% of the area. No additional colors.
**适配/禁用渲染**：✓✓ vector-illustration（默认配对）/flat/3d-isometric（阴影保持软且 8%）/digital-dashboard/blueprint/corporate-photo（冷调 grade）/editorial；✗ sketch-notes、fantasy-animation、pixel-art（气质冲突，改用 warm-earth 或 macaron）；✗ 勿与 dark-cinematic 混合。

### dark-cinematic（暗黑电影感）
**气质与适用**：高级、氛围、低光——高端发布/影视娱乐/夜生活/电影感科技；深暗底+精心布光亮色。
**用色行为**：可覆盖 deck 的浅色 secondary（暗底即身份）：深暗底 `#0A0E27` 约 65%；primary 亮色做被照主体约 25%，带 8% 隐性光晕；accent 只给单一高亮 KPI，更强光晕约 10%；卡片底用稍浅暗色 `#1E293B` 与深渊区分。
**提示词片段（EN）**：deep dark covers about 65% of the surface as the cinema background; primary bright teal carries the main chart bars with implied 8%-opacity glow halo; accent gold reserved for one highlighted KPI with stronger glow; card backgrounds slightly lighter dark separating cards from the deeper void. Premium, cinematic, sophisticated.
**适配/禁用渲染**：✓✓ 3d-isometric（暗色模式架构）/digital-dashboard/corporate-photo（低光摄影）/warm-scene（夜景）/screen-print（电影海报）；✓ blueprint、vector-illustration；✗ sketch-notes、fantasy-animation、nature、chalkboard（气质不符）；✗ macaron、warm-earth（明度身份冲突）。

### duotone（双色海报）
**气质与适用**：双色纪律、海报感——文化/封面 hero/电影海报，用色彩克制本身撑页面。
**用色行为**：仅两色+背景，无第三色相；示例：深蓝 `#1E3A5F` 占下 55%（含山形剪影），焦橙 `#C2410C` 占上 45% 作天空，一个近白小圆 <3%；两色交界处加半调网点。
**提示词片段（EN）**：Only these two colors appear in the composition — no third hue. Halftone dot texture at the horizon between the two color zones. Slight color misregistration adds silkscreen authenticity.
**适配/禁用渲染**：✓✓ screen-print（签名配对）/flat；✓ vector-illustration、editorial、blueprint、pixel-art、chalkboard（粉彩双色粉笔）；✗ corporate-photo（除非 duotone 调色）；✗ sketch-notes、fantasy-animation、nature、watercolor（气质冲突）；✗ digital-dashboard、3d-isometric（需要更多色彩层次）。

### earthy-dusty（莫兰迪灰调）
**气质与适用**：哑光降饱和大地色（灰粉/鼠尾草绿/褪陶土/灰赭），莫兰迪式高级克制——生活方式/室内/正念/慢生活/极简品牌。
**用色行为**：所有颜色相对源 HEX 一律降饱和 30%（哪怕原色更鲜艳）；示例：燕麦 `#E8E0D5` 占上 60%，灰陶土 `#C9A38C` 占下 30%，灰鼠尾草 `#A8B5A0` 合计约 10%（一条细线+一个小点）；画面无任何鲜艳色。
**提示词片段（EN）**：every color appears desaturated 30% from its source HEX; muted oat carries the upper 60% of the canvas as calm field; muted dusty terracotta forms a confident block across the lower 30%; accent muted sage appears as one thin horizontal line and one small dusty dot. No vivid color anywhere. Refined, contemplative.
**适配/禁用渲染**：✓✓ watercolor（材质天然哑）/editorial/corporate-photo（莫兰迪 grade）/flat/vector-illustration；✓ paper-cut、warm-scene（dusted grade）；✗ tech-neon、vivid-launch、pixel-art、digital-dashboard（依赖饱和度）；✗ chalkboard（材质冲突）。

### editorial-classic（经典杂志）
**气质与适用**：精致、杂志感、均衡——财经新闻/评论/复杂 B2B；比 cool-corporate 的 primary 更浓、accent 细则更讲究。
**用色行为**：奶白场+浓 primary 数据块+单条 accent 细线与单点标记；示例：暖奶白 `#FAF7F2` 约 55% 带 8% 纸纹，深藏青 `#0F2C4C` 约 32% 做左侧数据主块，焦橙 `#C2410C` 合计约 12%。
**提示词片段（EN）**：secondary warm cream covers about 55% of the canvas with subtle paper-grain at 8% opacity; primary deep navy carries the dominant data block on the left; accent burnt orange appears as one thin horizontal rule and a single small data marker at the highlighted point. Magazine-spread composition with deliberate gutters.
**适配/禁用渲染**：✓✓ editorial（完美契合）/vector-illustration/ink-notes（杂志克制+墨线正式感）/corporate-photo（杂志摄影）；✓ flat（略装饰）、blueprint、screen-print；✗ sketch-notes、fantasy-animation、pixel-art（太俏皮）。

### frost-ice（冰霜清冷）
**气质与适用**：近白场+淡冷点缀（冰蓝/淡银灰/微晶体感），洁净临床、高级极简、安宁——医疗/美妆/护肤/康养/高端 SaaS。
**用色行为**：近白占绝对主导，仅一个淡冷色块+一个精准小点缀，无暖色无高饱和；示例：近白 `#F8FBFD` 约 80%，淡冷蓝 `#DBEAFE` 圆角形约 12%，钢蓝 `#3B82F6` 单点/细线约 5%。
**提示词片段（EN）**：near-white occupies about 80% of the canvas as vast calm field; a single soft pale cool rounded shape appears in the lower third; accent steel blue appears as one small deliberate dot or thin line at a rule-of-thirds intersection. No warm tones, no saturated colors. Maximum breathing room.
**适配/禁用渲染**：✓✓ digital-dashboard（洁净临床 UI）/vector-illustration/flat/minimalist-swiss（场与网格配对）/glassmorphism；✓ corporate-photo（临床冷 grade）、blueprint（淡色示意）；✗ sketch-notes、chalkboard、fantasy-animation、pixel-art（偏暖）；✗ dark-cinematic（明度身份相反）。

### jewel-tone（宝石浓色）
**气质与适用**：深饱和宝石色（翡翠/蓝宝石/红宝石/紫晶/金），浓郁奢华晚宴感——奢侈/时尚/珠宝/高端产品/遗产品牌；想要"浓"用它，想要"氛围"用 dark-cinematic。
**用色行为**：高饱和大块+丝绒底场+金属点缀，无灰调；示例：浓翡翠绿 `#047857` 高饱和占下 40%，深奶白 `#FEF3C7` 丝绒场占上 48%，金 `#D4AF37` 一条金属细线+一颗抛光金点约 10%。
**提示词片段（EN）**：rich primary deep emerald forms a confident block across the lower 40% of the canvas with high saturation; secondary deep cream carries the upper 48% as velvet field; accent gold appears as a single thin metallic horizontal line at the meeting point and one small polished gold dot. No muted tints. No additional colors. Premium evening feel.
**适配/禁用渲染**：✓✓ editorial（杂志奢华）/corporate-photo（宝石调 grade）；✓ flat（大胆宝石平块）、vector-illustration（损失材质暗示）、screen-print（限色海报奢华）；✗ sketch-notes、chalkboard、pixel-art、fantasy-animation（气质不符）；✗ digital-dashboard（数据 UI 与奢华冲突）。

### macaron（马卡龙粉彩）
**气质与适用**：柔和粉彩、温和亲和——教育/入职/儿童内容/知识卡片的招牌色板；deck 的 HEX 全部渲染为粉彩 tint，置于暖奶白场上。
**用色行为**：暖奶白纸底约 50%，四个圆角信息盒用粉彩填充（primary 的粉彩 tint、薄荷、薰衣草、蜜桃），填充带手绘溢出轮廓；accent 只上一条高亮手绘箭头约 6%；示例底 `#F5F0E8`、accent coral `#F97316`。
**提示词片段（EN）**：warm cream paper background covers about 50%. Four rounded info boxes filled with soft pastels — light blue (pastel tint of primary), mint, lavender, peach. Each fill has slight hand-painted overshoot beyond its black ink outline. Accent warm coral appears only on one highlighted hand-drawn arrow. Friendly educational temperament.
**适配/禁用渲染**：✓✓ sketch-notes（默认色板）/flat/vector-illustration/watercolor/fantasy-animation/chalkboard（深板上粉彩粉笔）；✓ pixel-art（粉彩复古）；✗ tech-neon、dark-cinematic、blueprint（气质冲突）；✗ corporate-photo（摄影要自然色）；✗ digital-dashboard（仪表盘要鲜艳不要粉彩）。

### mono-ink（黑白墨线）
**气质与适用**：高对比黑白+稀疏语义色，最自律的色板——方法论/宣言/Before-After/思维转变叙事；最可能覆盖 deck 色的色板。
**用色行为**：覆盖 primary 与 secondary——墨色恒近黑 `#1A1A1A`（约 38%），底恒纯白 `#FFFFFF`（约 55%）；deck 的 primary/secondary 不作为图像色出现；accent 只做语义强调且 <10%（示例：coral `#E8655A` 标 pain-point 约 4%，teal `#5FA8A8` 标 solution 约 3%，合计 <8%）。
**提示词片段（EN）**：mono-ink palette intentionally uses near-black on white as the structural language; the deck's primary and secondary are not represented as image colors. The deck's accent is reserved for the semantic emphasis role under 10% of canvas.
**适配/禁用渲染**：✓✓ ink-notes（默认色板）/editorial（杂志克制+墨线自律）；✓ vector-illustration（失去手绘感）、blueprint（示意克制）；✗ sketch-notes、watercolor、fantasy-animation、nature（偏暖）；✗ tech-neon、digital-dashboard（mono-ink 刻意非数字感）；✗ corporate-photo（摄影无法黑白墨线）；✗ chalkboard（白纸黑墨的反面）。

### nature-organic（自然大地色）
**气质与适用**：大地色+冷暖绿+奶白/土棕底——环境/可持续/康养/户外/食品/农业。
**用色行为**：奶白底约 50%，深林绿做叶与树影约 35%，蜂蜜琥珀做小细节亮点（基部小花、叶尖受光）约 13%；整体大地调微降饱和；示例 `#FEF3C7` / `#166534` / `#D4AF37`。
**提示词片段（EN）**：soft cream background (about 50%); primary deep forest green in stylized leaves and a central tree silhouette (about 35%); accent warm honey-amber in small detail pops — a few hand-drawn flowers at the base, sunlit highlights on leaf tips. Earth-toned and slightly desaturated.
**适配/禁用渲染**：✓✓ nature（直接契合）/watercolor/warm-scene/fantasy-animation/sketch-notes/corporate-photo（户外康养摄影）；✓ vector-illustration（自然矢量）；✗ tech-neon、dark-cinematic、digital-dashboard、blueprint（气质冲突）；✗ pixel-art（大地感不像素网格）。

### sunset-gradient（落日渐变）
**气质与适用**：粉→橙→紫暖渐变流动，氛围+能量——生活方式/创意机构/旅行/音乐/活动；唯一以"过渡"而非色块为核心的色板。
**用色行为**：HEX 作渐变 stop 而非离散填充；示例对角渐变：粉 `#EC4899`（左下）→ 橙 `#F97316`（中带）→ 紫 `#9333EA`（右上），平滑融合无硬边；渐变场上可放一个近黑扁平剪影（如棕榈树）作焦点约 6%。Override 规则：若所选渲染禁渐变（如 vector-illustration），渐变只用于背景场，前景形状仍按渲染规则平涂。
**提示词片段（EN）**：smooth diagonal gradient flowing from primary deep pink in the lower-left corner, transitioning through secondary warm orange across the middle band, into accent purple in the upper-right corner. Smooth blending — no hard color edges. Atmospheric, energetic, optimistic.
**适配/禁用渲染**：✓✓ flat（几何上的平滑渐变）/watercolor（渐变是水彩母语）/warm-scene（落日级电影氛围）；✓ vector-illustration（仅背景渐变 override）、glassmorphism（用 tame 变体的柔冷渐变）、3d-isometric（等距体块后的渐变天空）；✗ minimalist-swiss、blueprint、mono-ink（气质冲突）；✗ pixel-art、sketch-notes、ink-notes、chalkboard（材质冲突）；✗ corporate-photo（摄影用真实调色非绘画渐变）。

### tech-neon（科技霓虹）
**气质与适用**：高能、未来、高对比+发光感——AI/SaaS/产品发布/赛博/前沿科技；饱和品牌色压在更暗或对比场上。
**用色行为**：深色场垫底，饱和亮色平涂主体+边缘微光晕，accent 连接线更强发光；示例：深 navy `#0A0E27` 约 50%（背景面+暗面），电蓝 `#0EA5E9` 亮面约 35% 且每块边缘带 8% 外发光，青 `#06B6D4` 连接线+一块高亮面约 12%；全程高对比。
**提示词片段（EN）**：secondary deep navy covers the background plane and shadowed faces; primary electric blue carries the lit faces of the stacked blocks in saturated solid fills with a subtle 8%-opacity outer glow around each block's edge; accent vivid cyan appears on connecting lines and one highlighted block's lit face with stronger implied glow. High contrast throughout.
**适配/禁用渲染**：✓✓ 3d-isometric（发光边缘科技架构）/digital-dashboard（霓虹高亮产品 UI）/flat（大胆平块+霓虹 accent）/blueprint（发光技术示意）；✓ vector-illustration（观感偏闷）、pixel-art（复古霓虹游戏）；✗ sketch-notes、watercolor、fantasy-animation、nature（暖 vs 赛博冲突）；✗ corporate-photo（摄影要自然色不要霓虹）。

### vivid-launch（高饱和发布）
**气质与适用**：大胆、饱和、夺目——产品发布/营销战役/活动主旨/促销；比 tech-neon 暖冷平衡更好、多色并存更自信。
**用色行为**：多色同台、双色对垒+主次分明；示例：近白 `#FAFAFA` 底约 38%，品牌洋红 `#E11D48` 做中央主导几何爆发形约 35%，橙 `#F97316` 做 co-star——右上大型支撑块约 25%，深中性 `#171717` 做一处小定义细节约 2%；全色自信饱和。
**提示词片段（EN）**：primary saturated brand magenta carries the dominant central shape — a bold geometric burst; accent vivid orange is co-star — a large supporting block or burst in the upper right; one small detail in deep neutral for definition. All colors confident and saturated. Promotional energy.
**适配/禁用渲染**：✓✓ flat/vector-illustration/3d-isometric（鲜活产品 3D）/screen-print（鲜活促销海报）/pixel-art（复古鲜活游戏发布）；✓ digital-dashboard（软件产品可）、corporate-photo（vivid grade）；✗ sketch-notes、ink-notes、nature（偏克制）；✗ watercolor、warm-scene（饱和度不匹配）。

### warm-earth（暖调大地）
**气质与适用**：友好、接地、人性——cool-corporate 的暖面；品牌故事/生活方式/教育/康养，人情味优先于商务克制。
**用色行为**：奶白天空场+陶土暖块+金色小光点，全画面暖调；示例：奶白 `#FEF3C7` 上 1/3 作天空与呼吸空间约 50%，深陶土 `#9A3412` 中景山丘+前景大地约 35%，金 `#D4AF37` 地平线小光晕+前景一只金鸟合计 <15%；无冷蓝绿（天空至多一丝若有似无）。
**提示词片段（EN）**：secondary cream occupies the upper third as soft sky and breathing space; primary deep terracotta carries the midground hills and foreground earth in confident warm washes; accent warm gold appears as a small concentrated glow near the horizon and a single golden bird shape in the foreground. All tones warm, no cool blues or greens beyond a barely-perceptible suggestion in the sky.
**适配/禁用渲染**：✓✓ vector-illustration/flat/sketch-notes/watercolor/warm-scene/fantasy-animation/nature/corporate-photo（暖 grade）；✓ editorial（有时偏好冷）；✗ tech-neon 主题、dark-cinematic（气质冲突）；✗ blueprint（要克制冷，暖调相抵）。
