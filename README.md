# neo_ppt_skills

**以 [GordenSuperPPTSkill](GordenSuperPPTSkill/SKILL.md) 为主线的端到端 PPT 生产技能：**
内容 → imagegen 逐页生成图片型 PPT → 四层还原（背景图/骨架图/元素图标/真文本）
→ **既好看又可编辑的 PPTX**，图片型与可编辑双成品一次交付。

另内置 **bank-all（27 套 577 页）/ bank-lite（18 套 339 页）银行营销合辑模板**
的 GordenPPTSkill 快线换字，以及一条不依赖 imagegen 的图片矢量复刻备选管线。

## 三条产线

| 产线 | 依赖 | 何时用 |
|---|---|---|
| **主线 · Super 端到端** | Codex 宿主 + imagegen（硬门禁） | 要"既好看又能编辑"的完整成品，视觉自由度最高 |
| **快线 · 模板换字** | 仅 python-pptx | 有现成内容，用内置 bank 合辑模板选页换字，分钟级出稿 |
| **备线 · 矢量复刻** | rapidocr + ppt-master（可选） | 手里已有 PPT 图片/截图，要逐页重建为可编辑 |

## 主线：GordenSuperPPTSkill 端到端

三个子技能已原样收录在本仓库（`GordenSuperPPTSkill/`、`GordenImagePPTGen/`、
`GordenImage2PPTX/`），编排规则以
[`GordenSuperPPTSkill/references/pipeline.md`](GordenSuperPPTSkill/references/pipeline.md)
为准：

```
内容 → 阶段1 outline+imagegen 逐页出图 → 图片型 PPT
     → 阶段2 每页四层还原（背景图/骨架图/元素图标/真文本）
     → 可编辑 PPTX + 全部中间产物
```

**硬门禁**：阶段 1 每页必须真实调用 imagegen（源图在
`$CODEX_HOME/generated_images/`，逐页记入 manifest）；阶段 2 的三个图片层同样
必须 imagegen 提取式生成。宿主无 imagegen 时主线停止，改走快线/备线，
不得用代码绘图冒充出图。

## 快线：bank 合辑模板换字

`templates/` 内置两套合辑（每页 use_for 带来源标签，槽位级容量已算）：

| 模板 | 页数 | 内容 |
|---|---|---|
| `templates/bank-lite` | 339 | 18 套精华（银行经营 14 + AI 落地 2 + 咨询方法 1 + 通用版式 1） |
| `templates/bank-all` | 577 | 27 套全量存档 |

```bash
python scripts/use_bank_all.py find 客户分层     # 按主题搜页
python scripts/use_bank_all.py build -o 成品.pptx 页码 "新标题"
```

## 备线：图片矢量复刻

`extras/` 收录微信文章下载器、OCR 坐标级重建（文字按原图坐标原位落位）、
ppt-master 代理施工规格与三工艺编排手册，流程见 `extras/pipeline.md`。

## 安装

```bash
# 克隆到 AI Agent 的技能目录（如 ~/.zcode/skills/），目录名保持 neo_ppt_skills
git clone <本仓库> ~/.zcode/skills/neo_ppt_skills

# 快线依赖
pip install python-pptx
# 主线依赖：Codex 宿主 + imagegen；两子技能的 Python 包见各自 SKILL.md
# 备线依赖：pip install rapidocr-onnxruntime；渲染预览建议 LibreOffice
```

## 质量口径

- 可编辑成品一律为原生形状 + 真文本框（主线的背景/骨架/图标层为图片，按
  Super 规范交付；快线与备线为 0 图片对象的全原生）
- 快线槽位级容量（每行字数 × 行数）与字号层级已经几何计算
- 备线交付前经"质量门禁 0 error + 结构清点 + 渲染与原图并排目检"三重校验

## 版权

bank 合辑全部页面由作者对公开微信文章预览图做逐页矢量重绘而来，非第三方
模板素材，可自由使用与二次修改。Gorden 系技能版权归原作者。
