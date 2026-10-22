# -*- coding: utf-8 -*-
"""visual_gate — 渲染视觉门：把成品渲染成 PDF 后在字形级机器查版面缺陷。

背景（2026-10-21 自评评测）：静态审计（容量/配色/layout_audit）全绿的稿子，
渲染出来仍可能"数字被千分位逗号劈行、表格文字互相叠压、文字压在装饰线上"
——静态全绿 ≠ 能看。本脚本是能机器化的最便宜视觉门，规则蒸馏自
pptwise（渲染后几何审计）与 PTT-Studio（逐页检查清单）：

  text-overlap    渲染后两段文字包围盒重叠 >较小者 30%（error，叠字不可读）
  number-split    数字被断行/劈开：片段以 , 结尾且右邻片段以数字开头
                  （error，"86,000" 显示成 "86,00 / 0"）
  text-out        文字出页面（error）
  decor-over-text 文字与细长矢量线/条相交（warning，kicker 压线类）

用法:
  python scripts/visual_gate.py 成品.pptx               # 渲染+全查
  python scripts/visual_gate.py 成品.pptx --keep pdf    # 保留中间 PDF
  python scripts/visual_gate.py 成品.pptx --json r.json # 结构化输出
  python scripts/visual_gate.py 成品.pptx --sheet       # 附加 4 页 2×2 联络表 PNG
                                                        # （deck 级一致性交叉审查用）
退出码: 0 = 无 error（warning 仅报告）；1 = 有 error；2 = 环境/用法错。
依赖: LibreOffice（soffice）+ pymupdf。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

TOL = 2.0          # 出页容差（pt）
OVERLAP_RATIO = 0.30
SPLIT_GAP = 2.0    # 判定"右邻"的最大横向间距（pt）
LINE_THICK = 3.0   # 细线判定：宽或高 < 3pt
LINE_MIN_LEN = 20.0


def _fix_ladder(px: float) -> str:
    """先量后改（guizang 修正阶梯）：按超出量分档给修法，并防"修过头"。"""
    if px <= 40:
        return "修法阶梯：微调间距/字号即可（≤40px 档）；改后复查留白防修过头"
    if px <= 90:
        return "修法阶梯：压块间距（40-90px 档）"
    if px <= 160:
        return "修法阶梯：压标题/正文或拆页（90-160px 档）"
    return "修法阶梯：换版式或删内容（>160px 档）"


@dataclass
class Finding:
    severity: str
    rule: str
    page: int
    message: str


def _find_soffice():
    p = shutil.which("soffice")
    if p:
        return p
    for cand in (r"C:\Program Files\LibreOffice\program\soffice.exe",
                 r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                 "/usr/bin/soffice", "/usr/local/bin/soffice",
                 "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if Path(cand).is_file():
            return cand
    return None


def render_pdf(pptx: Path, out_dir: Path) -> Path:
    soffice = _find_soffice()
    if not soffice:
        raise RuntimeError("未找到 soffice（LibreOffice），无法渲染")
    subprocess.run(
        [soffice, "--headless", "--norestore", "--nologo",
         "--convert-to", "pdf", "--outdir", str(out_dir), str(pptx)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        timeout=300)
    pdfs = list(out_dir.glob("*.pdf"))
    if not pdfs:
        raise RuntimeError("soffice 未产出 PDF")
    return pdfs[0]


def _spans(page):
    """[(text, x0, y0, x1, y1)] 按 pymupdf 字形 span 取。"""
    out = []
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for sp in line.get("spans", []):
                t = (sp.get("text") or "").strip()
                if t:
                    out.append((t, *sp["bbox"]))
    return out


def _inter(a, b):
    ix = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    iy = max(0.0, min(a[4], b[4]) - max(a[2], b[2]))
    return ix * iy


def audit_page(page, pno: int, out: list):
    pw, ph = page.rect.width, page.rect.height
    spans = _spans(page)
    for t, x0, y0, x1, y1 in spans:
        if x0 < -TOL or y0 < -TOL or x1 > pw + TOL or y1 > ph + TOL:
            over_px = max(-x0, -y0, x1 - pw, y1 - ph, 0)
            out.append(Finding("error", "text-out", pno,
                               f"文字出页: {t[:24]!r}（超出 {over_px:.0f}px；"
                               f"{_fix_ladder(over_px)}）"))
    # 渲染级叠字
    for i in range(len(spans)):
        for j in range(i + 1, len(spans)):
            a, b = spans[i], spans[j]
            inter = _inter(a, b)
            if not inter:
                continue
            aa = (a[3] - a[1]) * (a[4] - a[2])
            ab = (b[3] - b[1]) * (b[4] - b[2])
            smaller = min(aa, ab)
            if smaller and inter / smaller > OVERLAP_RATIO:
                out.append(Finding(
                    "error", "text-overlap", pno,
                    f"文字重叠 {inter / smaller:.0%}: {a[0][:14]!r} × {b[0][:14]!r}"
                    f"（重排两盒或换分栏版式；{_fix_ladder(inter / smaller * 100)}）"))
    # 数字被劈行：片段以 ,/，/- 结尾，右邻同线片段以数字开头
    right_of = {}
    for t, x0, y0, x1, y1 in spans:
        cy = (y0 + y1) / 2
        right_of.setdefault(round(cy / 4), []).append((x0, x1, t))
    for t, x0, y0, x1, y1 in spans:
        if not t or t[-1] not in ",，-":
            continue
        for sx0, sx1, st in right_of.get(round((y0 + y1) / 2 / 4), []):
            if st != t and 0 <= sx0 - x1 <= SPLIT_GAP and st[:1].isdigit() and t[-2:-1].isdigit():
                out.append(Finding(
                    "error", "number-split", pno,
                    f"数字被劈行: {t[-8:]!r} + {st[:8]!r}（改用不换行的数字格式或加宽）"))
                break
    # 文字压细线/细条（kicker 压线类）
    try:
        draws = page.get_drawings()
    except Exception:
        draws = []
    thin = []
    for d in draws:
        r = d.get("rect")
        if r is None:
            continue
        w, h = r.width, r.height
        if (w < LINE_THICK or h < LINE_THICK) and max(w, h) >= LINE_MIN_LEN:
            thin.append(r)
    for t, x0, y0, x1, y1 in spans:
        sa = (x1 - x0) * (y1 - y0)
        if not sa:
            continue
        for r in thin:
            inter = max(0.0, min(x1, r.x1) - max(x0, r.x0)) * \
                    max(0.0, min(y1, r.y1) - max(y0, r.y0))
            if inter / sa > 0.15:
                out.append(Finding(
                    "warning", "decor-over-text", pno,
                    f"文字压在细线上: {t[:20]!r}（装饰让位或文字重排）"))
                break


def contact_sheets(pdf: Path, out_prefix: Path, per_sheet: int = 4):
    """联络表：每 per_sheet 页拼一张 2×2 深底 PNG，带页码角标（PPTAgent 式）。"""
    import pymupdf
    from PIL import Image, ImageDraw
    doc = pymupdf.open(str(pdf))
    try:
        tiles = []
        for i, page in enumerate(doc, 1):
            pm = page.get_pixmap(matrix=pymupdf.Matrix(0.9, 0.9))
            img = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
            dr = ImageDraw.Draw(img)
            dr.rectangle([img.width - 74, img.height - 34, img.width - 6, img.height - 6],
                         fill=(20, 20, 20))
            dr.text((img.width - 66, img.height - 30), f"p{i:02d}", fill=(255, 255, 255))
            tiles.append(img)
    finally:
        doc.close()
    if not tiles:
        return []
    tw, th = tiles[0].size
    out_files = []
    for si in range(0, len(tiles), per_sheet):
        chunk = tiles[si:si + per_sheet]
        cols, rows = 2, 2
        sheet = Image.new("RGB", (cols * tw + 24, rows * th + 24), (16, 16, 16))
        for k, img in enumerate(chunk):
            sheet.paste(img, (8 + (k % cols) * (tw + 8), 8 + (k // cols) * (th + 8)))
        n = si // per_sheet + 1
        fp = Path(f"{out_prefix}-contact-{n:02d}.png")
        sheet.save(fp)
        out_files.append(str(fp))
    return out_files


def audit(pdf: Path) -> list:
    import pymupdf
    findings: list[Finding] = []
    doc = pymupdf.open(str(pdf))
    try:
        for i, page in enumerate(doc, 1):
            audit_page(page, i, findings)
    finally:
        doc.close()
    return findings


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    src = Path(argv[0])
    if not src.is_file():
        print(f"✗ 文件不存在: {src}")
        return 2
    keep = "--keep" in argv
    json_out = None
    if "--json" in argv:
        i = argv.index("--json")
        json_out = argv[i + 1]
    do_sheet = "--sheet" in argv
    try:
        with tempfile.TemporaryDirectory(prefix="vgate_") as td:
            pdf = render_pdf(src, Path(td))
            kept = None
            if keep:
                kept = src.with_suffix(".vgate.pdf")
                shutil.copy(pdf, kept)
            findings = audit(pdf)
            if kept:
                print(f"（中间 PDF 已保留: {kept}）")
            if do_sheet:
                try:
                    for fp in contact_sheets(pdf, src.with_suffix("")):
                        print(f"✓ 联络表: {fp}（deck 级一致性交叉审查：翻页节奏/离群页/整体风格）")
                except Exception as e:
                    print(f"（联络表跳过: {e}）")
    except RuntimeError as e:
        print(f"✗ {e}")
        return 2
    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump({"source": str(src),
                       "findings": [f.__dict__ for f in findings],
                       "error_count": sum(1 for x in findings if x.severity == "error"),
                       "warning_count": len(findings) - sum(1 for x in findings if x.severity == "error")},
                      f, ensure_ascii=False, indent=1)
    n_err = sum(1 for f in findings if f.severity == "error")
    n_warn = len(findings) - n_err
    for f in findings:
        print(f"[{f.severity}] p{f.page} {f.rule}: {f.message}")
    if not findings:
        print("✓ 渲染视觉门通过：无叠字 / 劈行 / 出页 / 压线")
    print(f"—— 共 {n_err} error / {n_warn} warning")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
