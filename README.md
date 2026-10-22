# neo_ppt_skills

**中文** ｜ [English](#english)

端到端中文/双语 PPT 生产技能：内容 → 逐页出图 → 四层还原 → **既美观又可编辑的 PPTX**。
行业中立——内容骨架全行业通用，中英文均可出稿。

End-to-end PPT production skill for Chinese/bilingual decks: content → page images →
four-layer restoration → **beautiful AND editable PPTX**. Domain-neutral content
skeletons, Chinese and English output.

> 📖 新人上手教程（中文）：[docs/教程-从文章到可编辑PPT.md](docs/教程-从文章到可编辑PPT.md)

---

## 目录结构（中文）

**三条产线**

| 产线 | 依赖 | 何时用 |
|---|---|---|
| **主线 · Super 端到端** | Codex 宿主 + imagegen（硬门禁） | 要"既好看又能编辑"的完整成品，视觉自由度最高 |
| **快线 · 合辑模板换字** | 仅 python-pptx | 有现成内容，用内置合辑模板选页换字，分钟级出稿 |
| **备线 · 矢量复刻** | rapidocr + ppt-master（可选） | 手里已有 PPT 图片/截图，要逐页重建为可编辑 |

### 主线：端到端（模式 C）

编排规则以 [`references/pipeline.md`](references/pipeline.md) 为准：

```
内容 → 阶段1 outline+imagegen 逐页出图 → 图片型 PPT
     → 阶段2 每页四层还原（背景图/骨架图/元素图标/真文本）
     → 可编辑 PPTX + 全部中间产物
```

**硬门禁**：阶段 1 每页必须真实调用 imagegen；阶段 2 的三个图片层同样必须
imagegen 提取式生成。宿主无 imagegen 时主线停止，改走快线/备线，不得用代码绘图冒充出图。

**风格与叙事选型（stylekit）**：`references/stylekit/` 十五篇蒸馏知识库——
[ppt-master](https://github.com/hugohe3/ppt-master)（MIT）四篇：18 种页面视觉
风格、20 种 imagegen 渲染手法 + 14 套图像色板（含 EN 提示词片段与适配矩阵）、
11 种图式构图骨架、5 种叙事模式 + 交付前视觉验收清单；定位排版一篇
（[dsh-office](https://github.com/omdsh-dev/dsh-office) /
[dsh-univer-office](https://github.com/dream-num/dsh-univer-office)（Apache-2.0）
+ pptx-harness）：7 规范版式坐标、静态审计阈值、字形级 lint 三规则、逐页闭环，
配 `scripts/layout_audit.py` 成品终检（文字出界/占位符含 XX=error，装饰出血/
重叠/溢出/孤字/装饰压字=warning）；`scripts/visual_gate.py` 渲染视觉门
（渲染后叠字/数字劈行/文字出页=error，压线=warning）；
排版四门四篇（蒸馏自 pptwise / dsh-ppt / dsh-ppt-maker / dsh-ppt-master /
PTT-Studio / PPT-Design-Skill / dsh-ppt-canvas / dsh-office-tools 八引擎，均 MIT；
deepseek-design 仅学习思想）：版式几何数字库（字号阶梯/版式坐标表/间距常数）、
防溢出与密度控制（双层容量/降级链/装饰宪法/禁词汇表）、验收协议（静态门阈值
全集/中文 fit 红线/视觉门/验收合同）、编辑保真（原树编辑十二细则/占位符继承
保护/最小改动纪律）；风格抽取与保真自评两篇（蒸馏自
[luobo-ppt](https://github.com/zhouwei713/luobo-ppt)（MIT））：参考图→风格抽取、
美化管线（原稿文字零改动）、品牌套件、"安静的改动"门禁与五维自评；过程纪律
一篇（蒸馏自 [codex-slides](https://github.com/nexu-io/codex-slides)（MIT）七分技能
与 [awesome-codex-ppt-skills](https://github.com/zhuyansen/awesome-codex-ppt-skills)
横评清单）：双信号验证、known-errors 故障恢复、checkpoint 可见化、版本不可变、
PEI 可编辑性分级与横评方法论。
风格（怎么画）、色板（颜色怎么上）、叙事模式（怎么论证）三者独立选型，
一套 PPT 各定一种；颜色纪律仍归主题色系统管。

### 快线：合辑模板换字（deck-all，577 页）

`templates/deck-all` 是 27 套商务演示版式的矢量合辑（577 页，每页 use_for 带
`bankNN·` 来源套号），内容骨架覆盖：工作总结、运营方案、销售管理、客户经营、
AI 落地、管理方法论、流程图/时间轴/架构图。**骨架行业无关**——页面里的示例
文案只是占位，出稿时全部正文槽位会按 12pt 排版重写。

```bash
# Agent 一键流程（选页 + 换字 + 三重门禁 + 末步配色检查）
python scripts/deck_cli.py find 客户分层          # 按主题搜页
python scripts/deck_cli.py show 24                # 看槽位与 12pt 写作预算
python scripts/deck_cli.py build -o 成品.pptx 24 "新标题" \
    --set 24:p24s16x0=正文文案按预算写

# 或直接用引擎：edits.json（选页+槽位替换）→ build_pptx 出稿
python scripts/build_pptx.py templates/deck-all/template.pptx edits.json 成品.pptx \
    --detail templates/deck-all/detail.json.gz
```

edits.json 示例（中文稿）：

```json
{
  "selected_slides": [280, 284],
  "edits": [
    {"slide": 280, "slot_id": "p280s19x0", "new_text": "零售客户分层运营方案"},
    {"slide": 284, "slot_id": "p284s3x0", "new_text": "分层与分类的逻辑关系"}
  ]
}
```

英文稿同理——容量按视觉宽度自动换算（1 个汉字 ≈ 2 个英文字符），字体沿用
模板的 latin 槽位：

```json
{
  "selected_slides": [4],
  "edits": [
    {"slide": 4, "slot_id": "p4s16x0", "new_text": "Risks under control"}
  ]
}
```

### 自由排版引擎（freelayout，从零排原生新稿）

蒸馏 luobo-ppt / dsh-ppt-master 的「版式=代码、AI 只填内容槽」架构：
19 种版式函数（封面/目录/章节/要点/卡片/KPI/对比/时间轴/流程/金字塔/漏斗/表格/
引言/宣言/大数字/结尾/**原生图表/配图/截图**），AI 只写 `deck.json`（每页 type + 内容字段），几何字号
全由引擎决定——字号阶梯回落 + 孤字防护、内容垂直居中不留空肚子、13 套主题色 +
派生色对比度兜底、出稿自动过静态排版门禁。

```bash
python scripts/freelayout.py deck.json -o 成品.pptx --theme orange-vitality
```

### 备线：图片矢量复刻

`extras/` 收录微信文章取图、OCR 坐标级重建（文字按原图坐标原位落位）、
ppt-master 代理施工规格与三工艺编排手册，流程见 `extras/pipeline.md`。

## 编辑铁律（引擎强制，非建议）

以下规则固化在 `scripts/build_pptx.py` 出稿引擎与 `tests/eval_slim.py`（57 项
回归基线）里，违反即拒绝出稿，`--allow-*` 旗标为显式豁免：

| 铁律 | 内容 | 引擎行为 |
|---|---|---|
| **正文 12pt（小四）** | 出稿正文一律小四号（作用域=role「正文」槽位；标题/卡头/序号/mockup 缩微标签豁免） | 换字时自动把选中页全部正文槽位置 12pt；字数超 12pt 容量直接拒绝 |
| **写作预算前置** | 每槽 12pt 容量在 `show 页码` 里逐槽可见（`12pt≤N字`） | 按预算写文案，超容量即拒，精炼措辞而非缩字号 |
| **配色体系统一** | 模板 577 页已整体预统一为活力橙单色系（饱和色色相批量重着色，中性色与位图不动）；13 套主题见 `scripts/palettes.json` | 填充时按占比映射主题色；跨色系混选拒绝出稿 |
| **出稿末步配色检查** | 扫描成品全部页面的实际用色，杂色页（过半饱和用色出系）不得交付 | `palette_check.py` 自动执行，不通过退出码 3 |

中文字号→pt 换算：初号42 / 小初36 / 一号26 / 二号22 / 小二18 / 三号16 /
四号14 / **小四12** / 五号10.5 / 小五9 / 六号7.5 / 七号5.5 / 八号5。

标准配色主题 13 套（`scripts/palettes.json`）——**咨询级七套**（对标 MBB+四大
品牌色）：McKinsey 深空蓝 / BCG 生长绿 / Bain 红 / PwC 橙 / Deloitte 青柠 /
KPMG 皇家蓝 / EY 黄；**经典六套**：商务蓝 / 典雅红 / 活力橙（默认）/ 青绿 /
紫韵 / 金香。出稿前确认用户提示词要求的色系并传 `--theme <id>` 整套统一；
也支持自定义色列表 `--theme "#1F4E79,#2E75B6"`。模板本体已预统一为活力橙
（=默认主题），选其他色系无需改模板，`--theme` 在出稿时整套映射即可；如想把
模板重着色为别的色系，改 `scripts/recolor_orange.py` 的 `HUE_LO/HUE_HI` 两个
常量重跑一遍即可（饱和色色相线性映射、明暗层级保留、黑白灰与位图不动）。

## 安装

```bash
git clone <本仓库> ~/.zcode/skills/neo_ppt_skills
pip install python-pptx          # 快线依赖
# 主线依赖：Codex 宿主 + imagegen；备线依赖：pip install rapidocr-onnxruntime
# 渲染预览建议 LibreOffice
```

## 仓库体积

全仓 **6.7 MiB**：模板合辑（含参考图）6.3MB（577 页矢量、91,700 个矢量形状，
deflate 已至压缩比地板）+ 脚本/文档/评测/stylekit 0.5MB。压缩手段：detail 走
minify+gzip（引擎透明解压）、裁掉引擎不读的元数据字段、内嵌 PNG 量化 256 色、
参考图 JPEG q72。

## 质量口径

- 可编辑成品一律为原生形状 + 真文本框（主线的背景/骨架/图标层为图片，按
  Super 规范交付；快线与备线为 0 图片对象的全原生）
- 快线槽位级容量与字号层级已经几何计算，出稿前过 12pt 容量硬校验与配色体系检查
- 出稿自动两道门禁：`layout_audit.py --level error`（静态排版：文字出界/占位符
  残留=error 拒绝交付 rc=4，装饰出血降 warning；`--allow-layout-errors` 豁免）
  → `palette_check.py`（配色体系，rc=3）；交付前再手动 `visual_gate.py`
  （渲染视觉门：叠字/数字劈行/文字出页=error）+ LibreOffice 目检
- 备线交付前经"质量门禁 0 error + 结构清点 + 渲染与原图并排目检"三重校验
- **101 项回归基线**：`python tests/eval_slim.py`（结构完整性 / CLI 全接口 /
  边界与安全路径 / 铁律门禁 / LibreOffice 渲染 / 依赖可导入）

## 版权

合辑全部页面由作者对公开商务 PPT 预览图做逐页矢量重绘而来，非第三方模板
素材，可自由使用与二次修改。

`references/stylekit/` 中 visual-styles / imagegen-styles / image-type-templates /
narrative-and-review 四篇蒸馏自 [ppt-master](https://github.com/hugohe3/ppt-master)
（MIT License，Copyright (c) 2025-2026 Hugo He）；layout-engine 一篇蒸馏自
[dsh-office](https://github.com/omdsh-dev/dsh-office) 与
[dsh-univer-office](https://github.com/dream-num/dsh-univer-office)
（Apache-2.0）及 pptx-harness（MIT）；layout-library / overflow-and-density /
audit-protocol / edit-fidelity 四篇蒸馏自 [pptwise](https://github.com/liustack/pptwise)、
[dsh-ppt](https://github.com/STARDUSTLC666/dsh-ppt)、
[dsh-ppt-maker](https://github.com/OMSociety/dsh-ppt-maker)、
[dsh-ppt-master](https://github.com/weijianguizhou/dsh-ppt-master)、
[PTT-Studio](https://github.com/ColdMagicchess/PTT-Studio)、
[PPT-Design-Skill](https://github.com/sunchaokun/PPT-Design-Skill)、
[dsh-ppt-canvas](https://github.com/hg1048596-pixel/dsh-ppt-canvas)、
[dsh-office-tools](https://github.com/kw78/dsh-office-tools)（均 MIT），
另参考 [deepseek-design](https://github.com/Devin-AXIS/deepseek-design)
（Source Available License，仅学习思想未复制文本）；
style-extraction / fidelity-and-review 两篇蒸馏自
[luobo-ppt](https://github.com/zhouwei713/luobo-ppt)（MIT License,
Copyright (c) 2026 zhouluobo）——参考图风格抽取、美化管线（原稿文字零改动）、
品牌套件、"安静的改动"门禁与五维自评；process-and-benchmark 一篇蒸馏自
[codex-slides](https://github.com/nexu-io/codex-slides)（MIT）与
[awesome-codex-ppt-skills](https://github.com/zhuyansen/awesome-codex-ppt-skills)
——双信号验证、故障恢复、checkpoint 可见化、PEI 可编辑性分级与横评方法论；
style-dimensions / measure-driven 两篇蒸馏自
[guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill)、
[baoyu-skills](https://github.com/JimLiu/baoyu-skills)、
[frontend-slides](https://github.com/zarazhangrui/frontend-slides)、
[deck-dna](https://github.com/opitaru-sys/deck-dna)、
[slide-skill](https://github.com/icgma/slide-skill)、
[PPTAgent](https://github.com/icip-cas/PPTAgent)、
[NBLM2PPTX](https://github.com/laihenyi/NBLM2PPTX)、
[AIPPT](https://github.com/LRriver/AIPPT)——四维风格参数化、测量驱动设计、
CJK 避头尾断行器（已内建 freelayout 引擎）与版式内容契约；
均依其许可证条款注明出处。

---

# English

End-to-end PPT production skill for Chinese and bilingual decks: content →
page images → four-layer restoration → **beautiful AND editable PPTX**, in one
run. Domain-neutral: the content skeletons work for any industry — banking,
retail, tech, healthcare, government — you replace every text slot when
authoring, in Chinese or English.

> Tutorial (Chinese): [docs/教程-从文章到可编辑PPT.md](docs/教程-从文章到可编辑PPT.md)

## Three pipelines

| Pipeline | Requires | Use when |
|---|---|---|
| **Main · Super end-to-end** | Codex host + imagegen (hard gate) | Full deliverable, both beautiful and editable |
| **Fast · Template refill** | python-pptx only | You have content; pick pages from the bundled collection, refill slots, done in minutes |
| **Fallback · Vector re-build** | rapidocr + ppt-master (optional) | You have slide images/screenshots that must become editable |

**Style & narrative kit (stylekit)**: `references/stylekit/` holds fifteen
distilled reference files — four from [ppt-master](https://github.com/hugohe3/ppt-master)
(MIT): 18 page visual styles, 20 imagegen rendering techniques + 14 image
palettes (EN prompt fragments and compatibility matrices), 11 diagram
composition blueprints, and 5 narrative modes plus a pre-delivery visual
acceptance checklist; one on layout positioning distilled from
[dsh-office](https://github.com/omdsh-dev/dsh-office) /
[dsh-univer-office](https://github.com/dream-num/dsh-univer-office) (Apache-2.0)
and pptx-harness: canonical slide geometry, static audit thresholds, glyph-level
lint rules, per-page closed loop — with `scripts/layout_audit.py` as the final
gate (off-canvas/placeholders = errors; overlaps/overflow/orphan-line = warnings);
four on layout craft distilled from eight engines (pptwise / dsh-ppt /
dsh-ppt-maker / dsh-ppt-master / PTT-Studio / PPT-Design-Skill / dsh-ppt-canvas /
dsh-office-tools, all MIT): a layout geometry library (type scales, per-layout
coordinate tables, spacing constants), overflow & density control (dual-layer
capacity, degradation chain, decoration constitution, banned phrases), an
acceptance protocol (full static-gate thresholds, CJK fit rules, visual-gate
loop, acceptance contracts), and edit fidelity (twelve rules for editing
foreign .pptx files without breaking layout); two on style extraction and
content fidelity distilled from [luobo-ppt](https://github.com/zhouwei713/luobo-ppt)
(MIT): reference-image style extraction, beautify pipeline (source text kept
verbatim), brand kits from VI manuals, the "quiet changes" gate (chart units,
axis titles, footnotes) and the five-dimension self-review; one on process
discipline distilled from [codex-slides](https://github.com/nexu-io/codex-slides)
(MIT) and the [awesome-codex-ppt-skills](https://github.com/zhuyansen/awesome-codex-ppt-skills)
benchmark list: dual-signal verification, known-errors recovery, visible
checkpoints, immutable versions, the PEI editability ladder and the
same-brief benchmark method; style-dimensions / measure-driven distilled from
guizang-ppt-skill / baoyu-skills / frontend-slides / deck-dna / slide-skill /
PPTAgent / NBLM2PPTX / AIPPT — the four-dimension style parameterization,
measurement-driven design, and the CJK line-breaking engine (now built into
freelayout); content-enrichment distilled from the SkillHub community skill
ppt-generator-skill — retrieval-based content filling, the de-AI-flavor ban
list (no underlined titles, no default blue, no 3-page same-layout runs) and
Chinese style keyword routing.
Style (how it is drawn), palette (how color is applied)
and narrative mode (how it argues) are chosen independently — one per deck;
color discipline still belongs to the theme system.

## Fast pipeline: the deck-all collection (577 pages)

`templates/deck-all` is a vector collection merged from 27 business slide
decks: work reports, operations plans, sales, customer management, AI
adoption, methodology, flow/timeline/architecture layouts. The skeletons are
industry-agnostic — sample copy inside is placeholder only; at build time
**every body slot is re-typeset at 12pt (CEO-four, 小四)** with your content.

```bash
python scripts/deck_cli.py find customer          # search pages by topic
python scripts/deck_cli.py show 24                # slots + 12pt writing budget
python scripts/deck_cli.py build -o deck.pptx 24 "New Title" \
    --set 24:p24s16x0=Body copy within budget
```

English works out of the box: slot capacity is measured in visual width units
(1 CJK char ≈ 2 latin chars), the overflow gate converts automatically, and
text keeps the template's latin typeface slot.

## Free-layout engine (freelayout, build a native deck from scratch)

Distilled from the "layouts are code, AI only fills content slots" architecture
of luobo-ppt / dsh-ppt-master: 19 layout functions (cover / toc / section /
bullets / cards / kpi / compare / timeline / process / pyramid / funnel / table /
quote / statement / big number / closing). The AI writes only `deck.json`
(one `type` + content fields per slide); geometry, type scale and spacing are
all decided by the engine — TYPE_SCALE fallback with orphan-line guard,
vertically centered content blocks (no hollow cards), 13 themes + derived-color
contrast fallback, and the static layout gate runs automatically at build.

```bash
python scripts/freelayout.py deck.json -o deck.pptx --theme orange-vitality
```

Quota overflow auto-switches to the fallback layout with an
`layout_auto` audit record; stylekit selection starts from
`references/stylekit/INDEX.md`. **Free layout on all 577 template pages**: `deck_cli build --overlay
"1=[{\"component\":\"kpi\",\"rect\":[x,y,w,h],...}]"` injects any freelayout
component (cards/bullets/kpi/chart/table) into any rectangle of any template
page — template skeleton preserved, theme-linked, with overlap detection and
zip dedup for LibreOffice compatibility. Also included: per-slide speaker notes (`notes` field / `deck_cli --note`),
content-level lint (assertion-title check, ghost-deck read-through, banned
vague words), the layout content-type contract (data-required layouts warn on
non-data content), `scripts/measure_deck.py` (five-dimension machine evidence),
`scripts/dna_extract.py` (measure the design DNA from approved old decks) and
`FILL-REPORT.md` (refill delivery report per build).

## Editing iron rules (engine-enforced, not advice)

Codified in `scripts/build_pptx.py` and guarded by `tests/eval_slim.py`
(93-item regression baseline). Violations refuse to save; `--allow-*` flags
are explicit opt-outs:

| Rule | Meaning | Engine behavior |
|---|---|---|
| **Body ≥ 12pt (小四)** | All body slots (role=正文) are typeset at 12pt; titles/chips/numerals/mockup micro-text exempt | Body slots auto-set to 12pt on refill; text over the 12pt capacity is rejected |
| **Budget-first writing** | Each slot's 12pt budget is visible via `show` (`12pt≤N units`) | Write within budget; condense wording instead of shrinking fonts |
| **One palette per deck** | The template's 577 pages are pre-unified to a single vitality-orange system (batch hue remap via `scripts/recolor_orange.py`); 13 themes in `scripts/palettes.json`, switch with `--theme <id>` | Saturated colors are mapped to the theme at build time; mixed-system selection is rejected |
| **Final palette check** | The finished file is scanned for actual colors; pages with >50% off-system accent mass cannot ship | `palette_check.py` runs automatically; exit code 3 on failure |

Chinese font size → pt: 初号42 / 小初36 / 一号26 / 二号22 / 小二18 / 三号16 /
四号14 / **小四12** / 五号10.5 / 小五9 / 六号7.5 / 七号5.5 / 八号5.

## Install

```bash
git clone <this repo> ~/.zcode/skills/neo_ppt_skills
pip install python-pptx
# Main pipeline: Codex host + imagegen. Fallback: pip install rapidocr-onnxruntime
# LibreOffice recommended for render previews.
```

## Repo size

**6.7 MiB** total: template collection incl. reference images 6.3MB (577-page
vector collection, 91,700 vector shapes — deflate is already at the compression
floor) + scripts/docs/tests/stylekit 0.5MB.

## License

All collection pages are hand vector-redraws by the author from public
business-PPT previews (not third-party template assets) — free to use and
modify.
