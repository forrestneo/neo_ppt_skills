# 模式 B：四层还原 — 完整流水线
## B2. 复刻干净背景

用 imagegen  **复刻**本页背景，得到 `$RUN_ROOT/editable/01/background.png`（16:9，与原图同比例）。

硬门禁：
- `background.png` 必须是图像模型生成图。
- 禁止用 PPT 页面填充色、原生矩形、渐变色块、代码绘制或裁切原图来冒充背景。
- 生成源图路径、后端、prompt 文件必须写入本页 `imagegen-assets-manifest.json`；没有真实 imagegen 记录不得交付。

推荐做法（二选一）：

- **复刻式（默认，更干净）**：把当前可见源图作为 **edit target**，在它的基础上擦除文字、图标、框架、卡片和占位块，生成同款空背景。提示词：

```text
复刻这张 PPT 幻灯片的背景：保持完全一致的底色、渐变、光影、纹理和大面积的背景装饰色块，
但生成一张完全空白的背景——不要任何文字、不要任何图标、不要任何卡片/方框/占位块、不要任何分隔条。
16:9 横版，与原图同尺寸。
```

- **擦除式（背景是照片/复杂纹理时）**：对原图做 edit/inpaint，移除所有文字、图标、框架、卡片、装饰块，补全背景。

> 背景里**绝不**保留框架/卡片/容器/分隔线/占位块——这些**统一进 B3 框架图**（imagegen 纯色底出图→抠图→默认整张 `frame.png` 放入 PPT；用户明确要求时才切成框架部件）。
> Codex 用内置 `imagegen`；要 edit 本地图先 `view_image`。生成图记得复制到输出目录并保留默认生成目录原图。详见 [`runtime-notes.md`](runtime-notes.md)。

---


## B3. 提取框架结构（全幅透明层）

🟦 **框架图的定义（先记牢这一条）**：一页里**「背景图」「元素图标/装饰/艺术字」「普通文本」之外的所有图像，统统算框架图，一次性提取到这一层**。包括但不限于：容器/卡片的轮廓与**底色填充面板**、彩色标题条、分区/分隔线、标题下短分割线、下划线、连接线与指示箭头、节点圆点、药丸/标签边框、**所有图表的全部图形**（柱状/折线/阶梯/饼图/环形/雷达/鱼骨/莫比乌斯等的坐标轴、网格线、柱体、折线、数据点、扇区、填充、趋势线）、缎带/横幅、以及任何装饰线条与色块。

🟨 **艺术字归类规则**：艺术字属于 B4 图标/装饰层，不属于 B7 普通文本层。判断标准：带有渐变颜色、书法/笔刷造型、形变、描边/阴影/纹理、徽章式排版，或普通字体无法直接写出的文字。例如封面“灵芝”这类大字必须作为装饰元素提取成图片，不能用普通文本框替代。

🟥 **三条硬要求**：
> 0. **必须用 imagegen 提取式生成**：`frame_raw.png` 必须来自图像模型生成，不能用 PPT shapes/色块/线条、代码绘图或裁原图局部替代。生成源图路径必须写入 `imagegen-assets-manifest.json`。
> 0a. **必须留证据**：框架图 prompt 要保存为文件，manifest 要记录 imagegen 后端、生成源、prompt 文件和交付复制路径；程序绘图生成的框架图一律不合格。
> 1. **不漏**：动手前把原图里每一个"非背景、非图标、非文字"的图形列成清单再提取——尤其别漏**数据折线/柱状/阶梯/饼图等图表图形**和各种**装饰元素**（典型漏项：某页右侧的"阶梯/折线趋势图"、缎带、连接箭头、坐标网格）。漏了 = 不合格。
> 2. **与原图严格一致（1:1）**：框架图与原图里的框架必须**形状、大小、位置一模一样**。提取后**合到背景上应当几乎等于原图去掉文字和图标**；逐元素对照原图核对边框粗细/长度/弧度/颜色/坐标。

⚠️ **框架要"完整还原"，不是"光秃线框"**：要连同卡片的**底色填充、彩色标题条、辉光/阴影、渐变**一起提取——它们是框架的一部分。上一轮把框架做成只剩灰色细 outline（丢了填充和辉光），导致成品比原图"空、廉价、远不如预期"。正确目标：抠出的框架合到背景上应当**几乎等于原图去掉文字和图标**。

⚠️ **不要漏掉小装饰线**：标题下的短强调分割线、卡片顶部的彩色短条、下划线、节点小圆点、药丸/标签的边框、坐标轴与网格线——这些都属于框架，必须一并提取。先把原图所有"非文字、非图标"的线条/边框/**面板/填充**逐一列清，再写进提示词。

提示词（固定模板；只允许替换背景色值 XXXXXX）：

```text
生成一张图片，提取这张图片中的框架图，纯色背景，背景色值为XXXXXX，「框架图」= 原图里**除背景/图标/装饰/艺术字/普通文本外的一切**（容器轮廓与**底色填充/标题条/辉光**、分隔/连接线、**全部图表图形：折线/柱状/阶梯/饼图/坐标网格/趋势线**、缎带/装饰）→ 形状·大小·位置与原图 **1:1 一致**，保留原色与填充，别漏数据折线/装饰、别自己额外加空心线框、占位框；不要出现文字、不要出现图标；
```

`XXXXXX` 默认为 `#00ff00`。若 B1 探色发现原图有绿色或绿色会与内容冲突，只能把 `XXXXXX` 改为原图没有的纯色值，例如 `#ff00ff`、`#8000ff`；不要改模板其它文字，不要追加英文语义清单。

存为 `$RUN_ROOT/editable/01/frame_raw.png`（在 B5 去底成 `frame.png`）。

> 补救：若框架图仍漏掉某些细线（短分割线、下划线等），优先改提示词并重出 `frame_raw.png`。最终 PPT 默认不得用 `shapes` 补线或补色块，除非用户明确要求原生形状重建。

> 不论简单还是复杂，**容器/卡片/图表框架一律走 imagegen 生成的整张框架透明图（B3）**。不要用 PPT shapes、PPT 填充色块或代码绘图替代框架图。

---


## B4. 提取图标/装饰/艺术字到等分方格网

目标：用 imagegen 把本页**所有图标、装饰元素和艺术字**生成到一张**方形**图里，在抠图底色上**等分成 N×N 个相同大小的方格**，每格一个元素，居中、四周留白，便于切片抠图。

先做去重审查（强制）：

1. 把 B3 的 `frame.png` 叠到 `background.png` 上生成预览，和源图并排看。
2. 用 GPT 视觉列两张清单：`source_icon_inventory`（源图里全部图标/装饰/艺术字）与 `already_in_frame`（已经出现在 frame 里的图标/装饰）。
3. B4 prompt 只生成 `source_icon_inventory - already_in_frame` 的元素；已经在 frame 中且位置正确的元素，不再生成、不再写入 `layout.icons[]`。
4. 如果 frame 里误含某图标但位置/样式不对，优先重出 frame，把该图标从 frame 移除，再在 B4 生成；不要让同一个图标同时存在于 frame 和 icons。

> 这一步是硬门禁：同一图标不能同时在 `frame.png` 与 `icons[]` 出现，否则最终会有重叠双影。不能因为图标多或难切，就跳过图标层或把 `icons[]` 清空交付。

硬门禁：
- `icons_raw_*.png` 必须来自图像模型生成。
- 禁止从原始幻灯片截图裁切图标、车辆、插画、装饰块或艺术字。
- 禁止用代码绘制图标表。
- 生成源图路径、后端、prompt 文件必须写入本页 `imagegen-assets-manifest.json`；程序绘图生成的图标表一律不合格。

提示词（用户原文 · verbatim，其余按实际情况调整）：

> 我们生成一张图片，提取这张PPT图片当中所有的图标元素和装饰元素，纯绿色背景，不要文字，不要背景条。

在此基础上补全：

```text
要求：
- 方形画布，纯<底色>背景（底色 = B1 推荐色，默认 #00ff00 纯绿；含绿页改为 #ff00ff 等）。
- 把元素严格排成 <N>×<N> 等分网格，每个格子大小完全相同且为正方形，元素在各自格子内居中并留出均匀边距；任何笔画、阴影、外轮廓都不能接触格子边缘。
- 只要图标/装饰元素/艺术字本身，**不要普通文字、不要背景条、不要卡片底框**。艺术字中的字符必须作为图形保留，例如“灵芝”保留字形、渐变和笔画造型。
- 元素之间不要重叠、不要相连。
- 忠实还原每个图标的造型、颜色、风格（颜色不要用到<底色>）。
- 若元素较多，不要挤在一张图里；宁可拆成多张图标表，也要保证每个元素完整、有足够透明边距，避免切片时齿轮、火箭、箭头等被裁掉。
```

数量与网格规则：

- **小图标**：4×4（每张 16 个）。元素多了就出**多张**。例：一页有 32 个图标 → 出 2 张 4×4 的绿底图。
- **大装饰图 / 艺术字**（不是小图标的装饰性图片或装饰文字）：用 2×2 或单独一张 1×1，把尺寸生成得大一些。
- 同一页可同时有"图标图(4×4)"和"装饰图(2×2)"多张。
- 元素含绿时，整页底色按 B1 改非绿，避免抠不干净。

每张存为 `$RUN_ROOT/editable/01/icons_raw_1.png`、`icons_raw_2.png`…

---


### B5a. 生成证据检查（必须在合成前执行）

合成前读取本页 `imagegen-assets-manifest.json`，逐项检查：

- `background` / `frame` / `icons` 三类资产都存在记录。
- 每条记录的 `backend` 是 imagegen 类后端。
- 每条记录都有非空 `generated_source`、`copied_to`、`prompt_file`。
- `prompt_file` 指向的提示词文件存在，且内容对应本页当前源图与该层目标。
- 记录中不得出现 `programmatic`、`local layer generator`、`PIL`、`SVG`、`HTML`、`Canvas`、`matplotlib`、`screenshot renderer`、`prompt_file:null` 等程序绘图或无提示词证据。

任一项失败，停止合成并重做 B2/B3/B4。不得用程序绘图结果临时补交。


### B5b. 框架图/图标完整性检查（必须在合成前执行）

默认读取 `icons/icons_manifest.json` 并查看 `icons_contact_sheet.png`；同时把透明 `frame.png` 合成到灰底/背景上检查线条、圆弧、面板填充和透明边缘。若用户明确要求框架切分，再额外读取 `frame_parts/icons_manifest.json` 并查看 `frame_parts/icons_contact_sheet.png`：

- 默认整张 `frame.png` 必须视觉完整：框架线条不断裂、圆弧不残缺、面板填充/标题条/辉光不丢失，合到背景上位置应与源图 1:1 贴合。
- 可选切分时，框架部件必须由透明区域自然分割得到；一个切片里若仍包含多个互不相连的大框架块，或一个框架块被错分成多个无法独立还原的碎片 → 不交付，重出或重切。
- 图标 `edge_touch` 任一方向为 true → 不交付，重出或重切。框架部件如果本来贴近页面边缘，可在 QA 备注里保留，但必须视觉完整、不缺边。
- 图标索引图中任何元素被切掉、缺边、错分成多个碎片、多个图标粘连成一个 → 不交付，重出或重切。
- 图标索引图中的元素数量必须覆盖 B4 的缺失元素清单；少一个都要补出新图标表。
- 如果某元素已在 frame 中出现且不应单独摆放，在 `placements.json` 标记为 `covered_by_frame:true`，不要放进 `layout.icons[]`。

---

## B6. 定位框架图与图标 → 写 layout.json

默认最终 `$RUN_ROOT/editable/01/layout.json` 直接使用整张透明 `frame.png` 作为框架视觉层：

```json
{
  "background": "background.png",
  "frame": "frame.png",
  "icons": [],
  "texts": []
}
```

这样能最大限度保持框架整体线条、圆弧、面板填充、标题条、辉光和相互位置一致。再为每个普通图标确定它在原页中的位置和大小。卡片/容器已在 `frame.png` 里，无需再用原生形状重画，也无需默认切成 `frame_parts`。

### 可选：用户要求框架切分时

如果用户明确要求框架切分/框架部件可移动，则不要在最终 layout 使用整张 `frame` 视觉层；改为把 `frame_parts/` 的每个切片作为 `icons[]` 条目放回原位，并标记 `role:"frame_part"`。

**拼回原 frame 布局的保证**：`slice_grid.py --components` 在切出每个框架部件时，会在 `frame_parts/icons_manifest.json` 记录该切片来自 `frame.png` 的原始 `bbox:[l,t,r,b]`。`frame_parts_to_icons.py` 用这个 bbox 生成 `layout.icons[]`，所以每个切片按自己的原始位置和原始尺寸放回。所有切片叠加后，应当重建出原来的 `frame.png` 视觉布局；这不是手动估算。

可选框架部件 bbox 换算规则（默认输出比例坐标）：
- 读取 `frame_parts/icons_manifest.json` 中每个切片的 `bbox:[l,t,r,b]` 和 `size:[frame_w,frame_h]`。
- 若 layout 使用 `units:"fraction"`：`x=l/frame_w`、`y=t/frame_h`、`w=(r-l)/frame_w`、`h=(b-t)/frame_h`。
- 同时保留 `source_bbox:[l/frame_w*ref_width, t/frame_h*ref_height, (r-l)/frame_w*ref_width, (b-t)/frame_h*ref_height]` 作为源图像素 QA 记录。
- 写入 `icons[]`：`{"file":"frame_parts/fp_001.png","role":"frame_part","x":...,"y":...,"w":...,"h":...,"source_bbox":[x,y,w,h]}`。
- 推荐直接运行脚本生成条目：`python3 scripts/restore/frame_parts_to_icons.py "$RUN_ROOT/editable/01/frame_parts/icons_manifest.json" --ref-width <源图宽px> --ref-height <源图高px>`，再把输出的 `frame_parts_layout_icons.json` 内容并入 `layout.json` 的 `icons[]` 最前面。

> 📐 **必须记录每个图标在原图中的实际包围盒（核心要求，常被漏做）**：`slice_grid.py` 的 manifest **只记录素材表里每个图标的尺寸/宽高比，不含它在原幻灯片里的位置**。所以 B6 必须**看原图逐个量出每个图标在源图实际像素坐标系里的 `x, y, w, h` bbox，然后换算成比例写进 layout.json 的 `icons[]`**——放回任意 PPT 尺寸时大小/位置才能按比例一致。建议维护一张对照表：`图标文件 → 原图 x/y/w/h(px) → x/y/w/h(fraction)`（可顺手记进 manifest 旁的一个 `placements.json`）。**别只靠目测随手摆**，那会出现"图标偏大/偏小/错位"。

- 坐标默认用 **比例**：`units:"fraction"`。先量源图像素 bbox，再换算：`x=x_px/ref_width`、`y=y_px/ref_height`、`w=w_px/ref_width`、`h=h_px/ref_height`。`ref_width/ref_height` 仍写入 layout，供 QA、`source_bbox` 和旧字段换算使用。
- **坐标契约（合成前硬门禁）**：
  - `ref_width/ref_height` 必须等于当前页源图文件的实际像素尺寸，例如源图是 4096×2286，就写 `4096/2286`。
  - `source_bbox` 必须使用同一张源图的实际像素坐标，不能是 `view_image` 界面缩略图、预览 PNG、浏览器截图或人工缩放图上的坐标。`view_image` 常会把 4096×2286 显示成 2048×1143；此时量到的 `x/y/w/h/size_px` 必须全部乘以 2，不能只修 x 或只修 y。
  - 若为了方便在同宽高比缩略图上量测（例如 2048×1143），必须先按 `scale_x=源图宽/缩略图宽`、`scale_y=源图高/缩略图高` 分别换回源图坐标，或运行：
    `python3 scripts/restore/layout_guard.py "$RUN_ROOT/editable/01/slide-01.png" "$RUN_ROOT/editable/01/layout.json" --fix-ref-to-source --fix-fractions --in-place`
    然后重新复查关键文本/图标位置。
  - 合成前必须运行：
    `python3 scripts/restore/layout_guard.py "$RUN_ROOT/editable/01/slide-01.png" "$RUN_ROOT/editable/01/layout.json" --strict`
    任何 `ref_width/ref_height` 与源图尺寸不一致，或 `source_bbox` 与 `x/y/w/h` 不一致，都不得进入 B8。`layout_guard.py` 不用页面覆盖高度判错；有些真实页面本来只在上半页或局部区域有文字/图标。
  - `layout_guard.py` 只校验坐标契约，不能判断 bbox 是否圈住了正确对象。它通过以后，还必须打开 `qa-source-boxes/slide_01_source_boxes.png` 做视觉复核：每个框必须覆盖源图真实文本/图标，而不是覆盖到同一面板里的其它行、其它按钮或空白位置。
- **图标尺寸要对照原图逐个核准**（上一轮反馈"图标大小不合适"）：
  - 先在源图像素坐标里量宽高；若只量到宽度，用 manifest 的宽高比定 `h_px = w_px / aspect`（保持图标不变形）；再写 `w=w_px/ref_width`、`h=h_px/ref_height`。切勿随手给方形 w=h。
  - 小徽标图标（要点前的 badge）通常 `w≈40~90px`（以 2134px 宽源图计）；功能区图标 `w≈90~170px`；大艺术字/插画另量。
  - 摆放后必须跑 `placement_qa.py`，在源图和预览图上画框核对：图标不能比原图明显偏大/偏小、不能压住文字或溢出卡片。
- **首次预览后必须做图标回校**：
  - 把 `$RUN_ROOT/out/preview/slide_01.png` 与源图并排看，逐个记录 `source_bbox`、`preview_bbox`、`delta_center_x/y`、`scale_w/h` 和处理动作，写入 `$RUN_ROOT/editable/01/icons/placements.json` 或旁边的 `placement_fix_notes.json`。
  - 若图标整体偏小/偏大，按源图 bbox 中心点缩放，不要只改 `w/h`。计算方式：`cx = x + w/2`、`cy = y + h/2`，改尺寸后写回 `x = cx - new_w/2`、`y = cy - new_h/2`。
  - 若切片素材四周透明边距较大，预览视觉 bbox 会比 layout bbox 小；此时应放大 layout 的 `w/h` 或重切图标，不要接受“框对了但图标肉眼偏小”的结果。
  - 若同一张自动切片里混入多个小图标，导致无法单独贴原位，必须重切或重出图标表；不得把组合切片硬塞到页面上压住文字。
  - 图标与文字的相对位置以源图为准：源图没有重叠而预览重叠时，先修图标中心点和尺寸，再修文字框；不能通过删除图标、缩得过小或移动到无关空白处来规避。
- 默认框架走整张 `frame.png`；只有用户明确要求框架切分时，才走 `icons[] role:"frame_part"`。默认不使用原生 `shapes` 承载视觉内容。
- 顺序即图层：默认是背景 → frame → icons → texts；可选切分时是背景 → frame_parts(`icons[] role:"frame_part"`) → icons → texts。
- 写一个 `$RUN_ROOT/editable/01/icons/placements.json`：每个源图图标都要有记录，字段至少包括 `source_label`、`status`（`covered_by_frame` / `placed_icon` / `needs_regen`）、`file`（若已摆放）、`source_bbox`（源图像素）、`x/y/w/h`（比例坐标，若已摆放）。B9 用它检查缺失和重复。

### 框架锚点回校：贴框文本必须跟随最终 frame

`source_bbox` 和 fraction 坐标只说明文本在源图坐标系里数学一致；它不保证文本和最终 `frame.png` 视觉对齐。B3 的 `frame.png` 是 imagegen 提取式生成层，标题条、按钮、底栏、卡片容器可能相对源图有几个到几十个像素的漂移。凡是文本贴着这些框架元素摆放，都必须在首次合成后做 **frame-anchor calibration**：

- 适用对象：分区标题条、卡片/面板标题、按钮文字、底部总结条、页脚/横幅、步骤标签、贴在线条/箭头旁的短标签。
- 不适用对象：独立正文段落、图标旁说明、卡片内部自由排版内容。这些仍以源图文本 bbox 和文本自身基线为主。
- 方法：先按源图像素 bbox 写 `texts[]`，跑 `layout_guard --strict` 和 `placement_qa.py`；然后看最终预览中 `frame.png` 的实际标题条/按钮/底栏位置，量出该框架锚点的视觉中心线或内边距，与源图对应锚点的差值 `dx_px/dy_px`；把贴框文本整体平移同样的 `dx/dy`，保持 `w/h/size_ratio` 不变。
- 计算示例：按钮文本原 bbox 为 `[x,y,w,h]`，最终 frame 中按钮内容区中心比源图低 `dy=32px`，则写回 `source_bbox:[x,y+32,w,h]`，并同步 `y=(y+32)/ref_height`。不要只改 `y` fraction 而忘记更新 `source_bbox`。
- QA 记录：把每个调整写入 `$RUN_ROOT/editable/01/placement_fix_notes.json` 或 layout 旁边笔记，至少包含 `text`、`frame_anchor`、`old_source_bbox`、`new_source_bbox`、`dx_px/dy_px`、`reason`。
- 失败模式：`layout_guard` 通过但标题、按钮、底栏文字看起来偏上/偏下，通常不是坐标契约错，而是缺少这一步。不要反复用全局缩放修；按具体 frame 锚点逐项修。

---

