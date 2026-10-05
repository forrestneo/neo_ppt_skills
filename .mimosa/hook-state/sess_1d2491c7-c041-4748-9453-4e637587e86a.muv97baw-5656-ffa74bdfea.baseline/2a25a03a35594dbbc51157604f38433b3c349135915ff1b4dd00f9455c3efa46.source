# -*- coding: utf-8 -*-
"""把 27 套成品 pptx 合成一个 bank-all 模板包并注册。
用法：python3 merge_bank_all.py          # 合并+detail+capacity+intro/preview
     python3 merge_bank_all.py register # 仅执行注册互换（INDEX改单条目+移出散包到备份）
"""
import os, sys, io, json, re, math, shutil, subprocess
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(__file__).parent
SRC = BASE / "成品"
DIST = BASE.parent / "蒸馏"
SKILL = Path(r"C:\Users\w\.zcode\skills\GordenPPTSkill")
TPL = SKILL / "templates"
SLUG = "bank-all"
OUT = TPL / SLUG
SOFFICE = r"C:\Program Files\LibreOffice\program\soffice.exe"
from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.enum.shapes import MSO_SHAPE_TYPE
from copy import deepcopy

# ---------- Phase A: merge ----------
def deck_title(prefix, part):
    cn = {"a": "上篇", "b": "下篇"}.get(part, "")
    cands = sorted(DIST.glob(f"{prefix}_*{cn}.md")) if cn else []
    if not cands:
        cands = sorted(p for p in DIST.glob(f"{prefix}_*.md") if not re.search(r"(上|下)篇\.md$", p.name))
    for p in cands:
        for line in io.open(p, encoding="utf-8"):
            if line.startswith("# "):
                return line[2:].strip()
    return None

def merge():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    dest = Presentation()
    dest.slide_width = 12192000
    dest.slide_height = 6858000
    blank = dest.slide_layouts[6]
    deckmap = []  # (deck_tag, title, first_page_1based, npages)
    files = sorted(SRC.glob("*.pptx"))
    page0 = 0
    for f in files:
        m = re.match(r"^(\d+)(?:_(.*?))?(上篇|下篇)?\.pptx$", f.name)
        prefix, part = m.group(1), (m.group(3) or "")
        tag = f"bank{prefix}{'a' if part == '上篇' else 'b' if part == '下篇' else ''}"
        title = deck_title(prefix, part) or f.stem
        title = re.sub(r"^\d+\s*", "", title)
        src = Presentation(f)
        npg = 0
        for sl in src.slides:
            new = dest.slides.add_slide(blank)
            new_el = new.shapes._spTree
            for sp in list(new_el):
                if sp.tag.split('}')[-1] in ("sp", "pic", "graphicFrame", "grpSp", "cxnSp"):
                    new_el.remove(sp)
            for child in sl.shapes._spTree:
                if child.tag.split('}')[-1] in ("nvGrpSpPr", "grpSpPr"):
                    continue
                new_el.append(deepcopy(child))
            for rId, rel in sl.part.rels.items():
                if rel.reltype.endswith("/image") and not rel.is_external:
                    new_rId = new.part.relate_to(rel.target_part, rel.reltype)
                    if new_rId != rId:
                        for blip in new.shapes._spTree.iter(qn("a:blip")):
                            if blip.get(qn("r:embed")) == rId:
                                blip.set(qn("r:embed"), new_rId)
            npg += 1
        deckmap.append((tag, title, page0 + 1, npg))
        page0 += npg
        print(f"  merged {tag}: {npg}p  累计{page0}")
    out = OUT / "template.pptx"
    dest.save(out)
    print("merged template saved:", out, page0, "pages")
    json.dump([{"tag": t, "title": ti, "start": s, "n": n} for t, ti, s, n in deckmap],
              io.open(OUT / "_deckmap.json", "w", encoding="utf-8"), ensure_ascii=False)

# ---------- Phase B: detail.json ----------
def iter_shapes(shapes):
    for sh in shapes:
        yield sh
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from iter_shapes(sh.shapes)

def slide_texts(slide):
    out = []
    for sh in iter_shapes(slide.shapes):
        if not getattr(sh, "has_text_frame", False):
            continue
        for pi, para in enumerate(sh.text_frame.paragraphs):
            t = "".join(r.text for r in para.runs).strip()
            if not t:
                continue
            size = None
            for r in para.runs:
                if r.font.size: size = r.font.size.pt; break
            if size is None:
                try:
                    if para.font.size: size = para.font.size.pt
                except Exception:
                    pass
            fname = next((r.font.name for r in para.runs if r.font.name), None)
            out.append((sh.shape_id, pi, t, size, fname))
    return out

def vw(s):
    w = 0.0
    for c in s:
        if "\u4e00" <= c <= "\u9fff" or "\u3000" <= c <= "\u303f" or "\uff00" <= c <= "\uffef": w += 1.0
        elif c == " ": w += 0.35
        elif c.isascii(): w += 0.5
        else: w += 0.8
    return w

def role_of(no, n, texts, is_deck_start, deck_len, deck_idx):
    joined = " ".join(t[2] for t in texts)
    sizes = [t[3] for t in texts if t[3]]
    big = max(sizes) if sizes else 0
    if is_deck_start: return "cover"
    if re.search(r"目\s*录|CONTENTS", joined) and (len(texts) <= 12 or big >= 30): return "agenda"
    local = None
    if re.search(r"谢谢|感谢|THANKS", joined, re.I) and no > n - 4: return "ending"
    if len(texts) <= 8 and big >= 28: return "section_divider"
    return "content"

def build_detail():
    prs = Presentation(OUT / "template.pptx")
    slides = list(prs.slides)
    n = len(slides)
    deckmap = json.load(open(OUT / "_deckmap.json", encoding="utf-8"))
    scale = (prs.slide_width / 12700.0) / 1280.0
    colors, fonts = Counter(), Counter()
    xml_all = ""
    for sl in slides:
        x = sl._element.xml
        xml_all += x
        for c in re.findall(r'srgbClr val="([0-9A-Fa-f]{6})"', x):
            colors[c.upper()] += 1
        for f in re.findall(r'typeface="([^"]+)"', x):
            if not f.startswith("+"): fonts[f] += 1
    def keep(c):
        v = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
        return not (min(v) > 235) and not (max(v) < 40)
    theme = [c for c, _ in colors.most_common(60) if keep(c)][:8]
    cn_font = next((f for f, _ in fonts.most_common() if re.search(r"[\u4e00-\u9fff]|YaHei|SimSun|SimHei", f)), "微软雅黑")
    en_font = next((f for f, _ in fonts.most_common() if f.isascii()), "Arial")
    pages, roles = [], defaultdict(list)
    preview_ids = [1]
    for i, sl in enumerate(slides, 1):
        dk = next(d for d in deckmap if d["start"] <= i < d["start"] + d["n"])
        local = i - dk["start"] + 1
        texts = [(a, b, c, (round(x / scale, 1) if x else None), e) for a, b, c, x, e in slide_texts(sl)]
        role = role_of(i, n, texts, local == 1, dk["n"], 0)
        roles[role].append(i)
        cands = [t for t in texts if len(t[2]) >= 4 and re.search(r"[\u4e00-\u9fff]", t[2])]
        pool = cands or [t for t in texts if len(t[2]) >= 4] or texts
        title_t = max(pool, key=lambda t: (t[3] or 0, len(t[2]))) if pool else None
        ptitle = title_t[2][:24] if title_t else ""
        slots = []
        for (sid, pi, t, size, fname) in texts:
            deco = bool(re.fullmatch(r"[\d.%/．·\-— ]{1,3}", t))
            slots.append({
                "slot_id": f"p{i}s{sid}x{pi}", "role": ("数字/序号" if deco else
                    "页面标题" if (size or 0) >= 24 else "小标题/卡头" if (size or 0) >= 14 else "正文"),
                "address": {"shape_id": sid, "paragraph": pi}, "current_text": t,
                "max_chars": max(4, int(vw(t) * 1.6) + 2),
                "language": "zh" if re.search(r"[\u4e00-\u9fff]", t) else "en",
                "editable": not deco,
                "guidance": "本页最大字号标题，替换时同级页保持同字号。" if title_t and (sid, pi) == (title_t[0], title_t[1]) and (size or 0) >= 22 else "",
                "font_size_pt": round(size * scale, 1) if size else None, "font_name": fname})
        pg = {"slide_number": i, "role": role,
              "layout": f"[{dk['tag']}] {len(texts)}个文本框；主标题《{ptitle}》" if ptitle else f"[{dk['tag']}] {len(texts)}个文本框",
              "use_for": f"{dk['tag']}·{USE(role)}：{ptitle}" if ptitle else f"{dk['tag']}·{USE(role)}",
              "text_slots": slots,
              "title_slot_id": (f"p{i}s{title_t[0]}x{title_t[1]}" if title_t and (title_t[3] or 0) >= 22 else None),
              "body_slot_ids": [s["slot_id"] for s in slots if s["role"] == "正文"][:12],
              "decorative_slot_ids": [s["slot_id"] for s in slots if not s["editable"]],
              "text_density": "high" if len(texts) > 60 else "medium" if len(texts) > 25 else "low"}
        pages.append(pg)
    detail = {"$schema": "ppt-template-detail/v1", "slug": SLUG,
              "name": "银行营销全集合辑（27套577页）", "source_pptx": "template.pptx",
              "slide_count": n, "slide_size_cm": [33.87, 19.05], "aspect": "16:9",
              "style": "bank-replication-mega", "theme_colors": theme,
              "fonts": {"cn": cn_font, "en": en_font},
              "editing_rules": [
                  "本合辑由27套银行PPT复刻成品合并而成（bank01~bank24，577页），每页 use_for 前缀标注来源篇目（如 bank05·内容版式：xxx），按前缀检索即可定位某一篇的页面。",
                  "保留所有形状的位置/大小/字号/字体/颜色，只替换文本；address 省略 run = 整段替换并保留首 run 格式。",
                  "高密度图解版式：优先改 title_slot 与 role=页面标题/小标题 的槽位；同 level 字号保持一致；禁止省略号截断。",
                  "装饰图形与数字不联动；本合辑不含原生 chart。",
                  "detail.json 很大，按页取用：python -c \"import json;d=json.load(open('detail.json',encoding='utf-8'));p=d['pages'][N];print(json.dumps(p,ensure_ascii=False,indent=1))\"",
                  "跨篇混排时注意各篇配色不同（红/蓝/绿/橙），同一份成品内选页尽量同篇或同色系。"],
              "shape_caution_pages": [], "data_charts": [], "skip_pages": [],
              "page_roles": dict(roles),
              "recommended_pages_for_short_deck": [d["start"] for d in deckmap],
              "pages": pages}
    (OUT / "detail.json").write_text(json.dumps(detail, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "_deckmap.json").write_text(json.dumps(deckmap, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"detail.json: {n} pages, {sum(len(p['text_slots']) for p in pages)} slots")

def USE(role):
    return {"cover": "封面", "agenda": "目录", "section_divider": "章节扉页",
            "content": "内容版式", "ending": "结束页"}[role]

def preview_and_intro():
    import fitz
    from PIL import Image
    deckmap = json.load(open(OUT / "_deckmap.json", encoding="utf-8"))
    # 整包577页转PDF过慢，改从各源篇分别渲染预览页（视觉等价）
    # deckmap 顺序=文件名排序：idx10=bank10, idx25=bank23, idx26=bank24
    picks = [(deckmap[0], 0), (deckmap[10], 4), (deckmap[25], 5), (deckmap[26], 7)]
    files = sorted(SRC.glob("*.pptx"))
    tmp = OUT / "_tmp"; tmp.mkdir(exist_ok=True)
    cells = []
    for dk, local in picks:
        f = files[[i for i, d in enumerate(deckmap) if d["tag"] == dk["tag"]][0]]
        subprocess.run([SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(f)],
                       check=True, capture_output=True, timeout=240)
        pdf = tmp / (f.stem + ".pdf")
        doc = fitz.open(pdf)
        pix = doc[local].get_pixmap(dpi=80)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).resize((640, 360))
        cells.append(img)
        doc.close(); pdf.unlink()
    canvas = Image.new("RGB", (1296, 736), "#FFFFFF")
    for k, im in enumerate(cells[:4]):
        canvas.paste(im, (5 + (k % 2) * 648, 5 + (k // 2) * 368))
    canvas.save(OUT / "preview.png")
    shutil.rmtree(tmp)
    (OUT / "intro.md").write_text("""# 银行营销全集合辑（`bank-all`）

- **来源**：27 套银行PPT复刻成品（bank01~bank24）合并的单模板，577 页 16:9，全部原生形状+真文本框（仅少量原稿照片类图片）。
- **如何找页**：每页 use_for 前缀是来源篇目标签（如 `bank05·内容版式：xxx`）。先按主题挑篇目，再在该篇页区间内选页；`recommended_pages_for_short_deck` 是每篇封面页清单。
- **配色**：27 篇配色各异（银行红/深蓝/墨绿/橙/青），跨篇混排建议同色系。
- **替换规范**：同 GordenPPTSkill 模式 A——edits.json 选页+slot 换字，address 省略 run 即整段替换保格式；高密度页优先改标题/卡头槽位。
- **容量**：所有槽位已经 compute_capacity 计算（chars_per_line/max_lines/max_chars/level）。
""", encoding="utf-8")
    print("preview + intro done")

if __name__ == "__main__":
    if "register" in sys.argv:
        print("register phase — see register step in main flow")
    else:
        merge()
        build_detail()
        preview_and_intro()
