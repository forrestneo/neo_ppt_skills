# 复刻管线编排手册（pipeline）

三种"图片 → 可编辑 PPTX"工艺的选型与标准流程。所有工艺共享同一验收口径：
**成品为原生形状+真文本框，逐页渲染与原图并排目检对位**。

## 工艺选型

| 场景 | 工艺 | 单页成本 | 保真度 |
|---|---|---|---|
| 整套复刻（10 页以上、版式复杂） | ppt-master 代理精复刻 | 10-25 分钟 | 最高（逐页对照+门禁） |
| 版式稀疏、只要文字和色块位置对 | OCR 坐标级 | 1-2 分钟 | 中高（文字/色块原位，图形占位） |
| 页数少（≤5）、版式简单 | 主线程手绘 python-pptx | 5-15 分钟 | 高（依赖绘制者） |

## 公共步骤

1. **取图**：微信文章用 `scripts/wechat_dl.py <url> <outdir>`；
   人工排除首尾装饰图/推广图/重复页（sha256 比对）。
2. **转录**：多模态逐页读图产出蒸馏.md——每页 `## P<页码> <标题>` +
   版式一句话描述 + 全部文字逐字。[不清] 标注，成品不得残留。
3. **约定**：成品页序=源图有效页序；文字以蒸馏稿为准、版式以源图为准。

## 工艺一：ppt-master 代理精复刻

依赖：同目录安装 ppt-master 技能。规格全文见
`references/图片复刻施工规格.md`（SUBAGENT_BRIEF），要点：

- 项目初始化：`svg_quality_checker.py` 同目录技能的
  `project_manager.py init <项目> --quick-generate --format ppt169`
- 每页手写 SVG（viewBox 1280×720，页眉公式、bounds 不重叠、
  preset 形状经 `preset_shape_svg.py render-batch`、图标经 fetch_icons 预取）
- 门禁：`svg_quality_checker.py <项目> --quick-generate --canonical-authoring
  --stage final --json` 逐页 0 errors
- 导出：`svg_to_pptx.py <项目> --quick-generate --no-notes`
- 验收：python-pptx 清点（真文本框/0 图片）+ LibreOffice 渲染并排对照
- 编排：多代理并行（每人 ≤9 页），中断残留先验收再续作；
  主线程负责终检/导出/对照/交付

## 工艺二：OCR 坐标级

```bash
python3 scripts/ocr_extract.py     # 全源图：OCR boxes + 取色 + 色块连通域 → ocr/*.json
python3 scripts/fix_colors.py      # 重算：调色板近邻分类色块 + 直方图取色（参数见文件头）
python3 scripts/pixrep.py          # 原位重建：源图坐标×1.185 → 1280 画布
```

- 文字：每行按原图 x/y 落位，字号=块高×0.75，颜色=直方图取色
- 色块：调色板（近白阈值 246、频次 ≥0.18%、min_px 22）+ BFS 连通域，
  渲染时过滤近白小伪影
- 适用：白底稀疏版式。不适用：渐变/插画密集页（图形只能占位）
- 已知边界：浅色面板可能低于近白阈值被漏检；金色文字取色偶有偏色

## 工艺三：主线程手绘

参照 `scripts/rep_lib.py`（1280×720 画布助手：text/rect/oval/line/stars/pageno），
每页一个构建函数，数据（文字）来自蒸馏稿、坐标对照源图。流程 =
写代码 → soffice 渲染 → 并排目检 → 修坐标重建，直至对位。
适合页数少、版式简单的快速成稿。

## 交付口径

- 结构：python-pptx 清点页数/真文本框/图片对象（复刻件应 0 图片，
  原稿照片类除外）
- 视觉：并排对照图存档（源图上、复刻下）
- 位置：`成品/<原编号>_<标题>.pptx`；SVG 源与 PROJECT_STATE.md 留在
  bank*_ppt169_* 项目目录
