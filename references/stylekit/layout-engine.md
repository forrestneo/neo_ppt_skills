# 定位排版引擎（蒸馏自 dsh-office / dsh-univer-office / pptx-harness）

> 来源与许可：[dsh-office](https://github.com/omdsh-dev/dsh-office) 与
> [dsh-univer-office](https://github.com/dream-num/dsh-univer-office)（Apache-2.0）、
> pptx-harness（MIT，本地引擎）。
> 用途：一切"往画布上放东西"的场景——模式 B 四层还原摆位、模式 D compose 组件
> 组装、原生重建与手排页面。**先网格后内容，写完必过 `scripts/layout_audit.py`。**

## 一、画布网格与版式脚手架（dsh-office ppt.ts）

16:9 宽屏 13.33×7.5in。七种规范版式的实测几何（英寸，坐标为左上角）：

| 版式 | 标题区 | 内容区 |
|---|---|---|
| title 封面 | 主标题 x0.5 y1.5 w90% h1.5 居中 40pt 粗；副标题 x1 y3.2 w80% h1 居中 18pt | — |
| section 章节页 | x0.5 y2 w90% h1.5 居中 36pt 粗 | — |
| content 正文 | x0.5 y0.4 w90% h0.8 36pt 粗 | 正文 x0.7 y1.5 w85% h4 14pt |
| two-column 双列 | 同 content | 左列 x0.5 y1.5 w4.2 h4；右列 x5.2 y1.5 w4.2 h4（中缝 0.5in） |
| image 配图 | 同 content | 图 x1 y1.5 w8 h4.5 |
| table 表格 | 同 content | 表 x0.5 y1.5 w90%，列宽均分，表头灰底加粗 |
| chart 图表 | 同 content | 图 x0.5 y1.5 w9 h5，多系列才出图例 |

版式选型对应本技能 stylekit 的 `image-type-templates.md`（按内容逻辑选）；
本表回答的是**选完之后东西放哪**。手排新页直接抄这些坐标起步，再按内容微调。

## 二、静态审计阈值（pptx-harness audit.py，已移植为 `scripts/layout_audit.py`）

不渲染即可判定，交付前对成品全量扫一遍；分级与精确阈值：

| 规则 | 判定 | 级别 |
|---|---|---|
| out-of-bounds | 形状出画布（容差 1px = 9525 EMU） | **error，一票否决** |
| placeholder | 残留 `lorem/xxx/TODO/click to add` | **error** |
| dangling-rel | 图片 rId 无对应关系 / 关系指向空部件 | **error** |
| overlap | 两文本形状包围盒重叠 > 较小盒面积 **10%** | warning |
| overflow-est | 估宽（CJK 全角 1.0em、其余 0.53em）×行高 1.25，估算高 > 可用高 **105%** | warning |
| font-ea-missing | run 设了 latin 无 ea 且含中文（中文不生效的头号坑） | warning |

用法与退出码：`python scripts/layout_audit.py 成品.pptx`（`--level error` 只看硬错，
`--json out.json` 结构化输出；rc=0 干净 / 1 有 error / 2 用法错）。
**warning 不是免罪**——修掉或写明有意为之，禁止无说明整批放行。

**预算制容量（budget.py 核心思想）**：模板设计师调好的原文长度已隐含正确答案，
`budget = 原文长度 × 1.1` 是防溢出的真正守门员，比任何字符宽度公式可靠。
role 判定：盒高 <1.5cm 或原文 ≤8 字或字号 ≥20pt → label（硬顶 max(原文,8)，
只许短语）；否则 body（budget 为硬顶）。deck-all 模板的逐槽预算已由
`deck_cli.py show 页码` 给出（12pt 口径），与此思想同源。

## 三、字形级 lint 三规则（dsh-univer-office univer-slide）

比包围盒更准一层：用**渲染后的字形几何**判三类违例，每条都必须修掉或凭证据
论证为有意设计：

1. **文本出页**——被裁切，必须修；
2. **文本逃出不透明矩形容器**——通常改短文案、显式换行或加大卡片；
3. **文本字形带重叠**——先看两元素颜色/透明度/层叠意图再判。

配套文本度量：单行高 `行数 × 字号px × 1.4` 起估；设计 px → pt 乘 0.75；
wrap/auto-fit/padding 一律显式设置，不依赖文本框默认值。
本技能的落地路径：LibreOffice → PDF → pymupdf 取字形框（`scripts/render_slides.py`
渲染），目检即此三规则的人工版；`layout_audit.py` 的 overflow-est 是其静态近似。

## 四、逐页闭环与缺陷模式化（univer-slide 工作流）

- **spec 先行**：动笔前写页面规格，一次定死 deck 级常量（色 `#RRGGBB`、字号、
  字体族、图标风格、页尺寸）；每页写明精确布局、结构类型、**一句核心信息**、
  逐字终稿文案。相邻页不重复同一结构。
- **逐页闭环**：页 N 干净了才开始页 N+1；改页用整页替换，**禁止在坏元素上叠新
  元素修修补补**（叠加修复=债）。
- **截图验收 8 项**：①元素出页/被裁 ②文字溢出卡片色块 ③文本框意外重叠
  ④形状遮住关键信息 ⑤低对比/文字压复杂图无衬底 ⑥缺要求内容 ⑦箭头断连/
  指向错/颜色不配 ⑧跨页一致性（色板/字体/图标风/边距/结构多样性）。
  每项给 PASS/FAIL + 证据；真需要人来设计的明确上报，不静默放行。
- **缺陷模式化**：一个缺陷=一类模式——全页搜同一处错，改源头，重跑受影响页。

## 五、生成方法论（dsh-office SKILL.md）

- **一页一核心信息**：讲不透就拆页；"少字是叙事选择，空白是设计失误"。
- **密度跟随目的**：告知型可密（听众既听又读）；说服/激励型压低密度
  （幻灯片是广告牌不是文档）。
- **先结构后视觉**：先定叙事（现状→问题→方案 / 钩子→主体→回报），再谈配色
  排版。叙事模式选型见 `narrative-and-review.md`。
- **编辑先读后改**：改已有 PPT 前先结构化读回（形状名 + cm 坐标）；只动文本
  节点 `<a:t>`，不碰布局字体配色——样式零破坏。
- **生成后读回自查**：出稿后读回结构确认内容完整、无占位符，再交付。

## 六、在本技能里的接线

| 场景 | 用什么 |
|---|---|
| 模式 D 出稿（deck-all 换字/compose） | 逐槽预算 `show` → build 内建 12pt 容量门禁 → `layout_audit.py` 终检 |
| 模式 B 四层还原 | 摆位抄第一节脚手架坐标 → 交付前 `layout_audit.py` |
| 手排/重组原生页 | 先画网格抄坐标 → 写完跑 `layout_audit.py` → LibreOffice 渲染按第三/四节目检 |
| 任何交付 | layout_audit（静态）→ palette_check（配色）→ 渲染目检 8 项，三道全过才算完 |
