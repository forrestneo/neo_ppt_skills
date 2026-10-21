#!/usr/bin/env python3
"""Build a new .pptx from a template by selecting slides and replacing text.

The script preserves all layout, fonts, colors, images and animations of the
source template. It only:
  1. Keeps the slides listed in ``selected_slides`` (in that order),
  2. Replaces the text of the runs identified by ``edits``.

USAGE
    python3 build_pptx.py <template.pptx> <edits.json> <output.pptx>
                         [--detail detail.json]   # for slot_id resolution
                         [--strict]               # fail if expected_text mismatch
                         [--dry-run]              # show planned edits, do nothing

EDITS JSON SCHEMA
{
  "template_slug": "simple-business",                 # optional, informational
  "selected_slides": [1, 2, 4, 7, 14, 16],            # 1-indexed in template
  "edits": [
    {
      "slide": 1,                                      # 1-indexed in template
      "slot_id": "title_en",                           # resolved via detail.json
      "new_text": "Annual Review"
    },
    {
      "slide": 1,
      "address": {"shape_id": 46, "paragraph": 1, "run": 0},  # explicit
      "expected_text": "工作计划模板",
      "new_text": "2026 年度工作计划"
    }
  ]
}

ADDRESS FORMS
    {"shape_id": <int>, "paragraph": <int>, "run": <int>}   # exact run
    {"shape_id": <int>, "paragraph": <int>}                  # whole paragraph
                                                              # (run 0 keeps fmt,
                                                              # others cleared)
"""
from __future__ import annotations
import argparse
import copy
import json
import math
import sys
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Pt


SLIDE_R_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

# ------------------------------------------------------------------
# 最小字号门禁（编辑铁律）：默认阈值 小四号 = 12pt。
# 中文字号（号数制）→ pt：初号42 / 小初36 / 一号26 / 小一24 / 二号22 / 小二18 /
# 三号16 / 小三15 / 四号14 / 小四12 / 五号10.5 / 小五9 / 六号7.5 / 小六6.5 /
# 七号5.5 / 八号5。号数制没有"12号"档，用户口语"12号字"按 小四号=12pt 执行。
MIN_FONT_PT = 12.0
TOL = 0.9            # 容量校准容差（与 compute_capacity 一致）
CN_FONT_SIZES = [(42, "初号"), (36, "小初"), (26, "一号"), (24, "小一"),
                 (22, "二号"), (18, "小二"), (16, "三号"), (15, "小三"),
                 (14, "四号"), (12, "小四"), (10.5, "五号"), (9, "小五"),
                 (7.5, "六号"), (6.5, "小六"), (5.5, "七号"), (5, "八号")]
# 门禁作用域：仅"正文"承载叙述内容（标题/卡头/数字序号/mockup 缩微标签豁免）
BODY_ROLES = {"正文"}


def cn_size_name(pt: float) -> str:
    for v, name in CN_FONT_SIZES:
        if abs(pt - v) < 0.26:
            return name
    return f"{pt:g}pt"


# ------------------------------------------------------------------
# 配色主题化：把一页的饱和用色按占比排名映射到目标主题色序列（中性色不动），
# 使任意来源的页统一到同一套配色体系。
# ------------------------------------------------------------------
import re
import colorsys
from collections import Counter as _Counter


def _is_sat(hex6: str) -> bool:
    r = int(hex6[0:2], 16) / 255
    g = int(hex6[2:4], 16) / 255
    b = int(hex6[4:6], 16) / 255
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return s >= 0.18 and 0.12 < v < 0.98


def slide_accent_ranks(slide) -> list:
    """页内饱和色按出现次数降序（去黑白灰）。"""
    cnt = _Counter()
    for el in slide._element.iter():
        if el.tag.endswith("}srgbClr"):
            v = (el.get("val") or "").upper()
            if re.fullmatch(r"[0-9A-F]{6}", v) and _is_sat(v):
                cnt[v] += 1
    return [c for c, _ in cnt.most_common()]


def unify_slide_colors(slide, theme_colors: list) -> tuple:
    """按排名把页内饱和色映射到 theme_colors（循环取用）。返回 (换色数, 映射)。"""
    ranked = slide_accent_ranks(slide)
    mapping = {c: theme_colors[i % len(theme_colors)] for i, c in enumerate(ranked)}
    n = 0
    for el in slide._element.iter():
        if el.tag.endswith("}srgbClr"):
            v = (el.get("val") or "").upper()
            if v in mapping and mapping[v] != v:
                el.set("val", mapping[v])
                n += 1
    return n, mapping


def load_themes() -> dict:
    p = Path(__file__).resolve().parent / "palettes.json"
    try:
        return {t["id"]: t for t in json.loads(p.read_text(encoding="utf-8"))["themes"]}
    except Exception:
        return {}


def theme_color_list(theme: dict) -> list:
    return [theme["primary"], theme["secondary"]] + list(theme.get("accents", []))


# ------------------------------------------------------------------
# 组件簇：把一页的顶层形状按 bbox 重叠连通聚成"组件"（一张卡片=一个组件）
# ------------------------------------------------------------------
def _bbox(shape):
    if shape.left is None or shape.top is None:
        return None
    return (shape.left, shape.top,
            shape.left + (shape.width or 0), shape.top + (shape.height or 0))


def _overlaps(a, b, tol=9525):  # 容差 0.75pt
    return not (a[2] + tol <= b[0] or b[2] + tol <= a[0]
                or a[3] + tol <= b[1] or b[3] + tol <= a[1])


def shape_clusters(slide) -> list:
    """返回组件簇列表：[{idx, bbox:(l,t,r,b), shapes:[shape]}]，按面积降序。"""
    shapes = [sh for sh in slide.shapes if sh.left is not None]
    rects = {id(sh): _bbox(sh) for sh in shapes}
    parent = {i: i for i in range(len(shapes))}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        parent[find(i)] = find(j)

    for i in range(len(shapes)):
        for j in range(i + 1, len(shapes)):
            ri, rj = rects[id(shapes[i])], rects[id(shapes[j])]
            if _overlaps(ri, rj):
                union(i, j)
    groups = {}
    for i, sh in enumerate(shapes):
        groups.setdefault(find(i), []).append(sh)
    out = []
    for members in groups.values():
        bs = [rects[id(m)] for m in members]
        bbox = (min(b[0] for b in bs), min(b[1] for b in bs),
                max(b[2] for b in bs), max(b[3] for b in bs))
        out.append({"bbox": bbox, "shapes": members,
                    "area": (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])})
    out.sort(key=lambda c: -c["area"])
    for i, c in enumerate(out):
        c["idx"] = i
    return out


def copy_cluster(dst_slide, cluster, dx: int, dy: int) -> int:
    """把组件簇的形状深拷贝到目标页并整体平移 (dx,dy) EMU。返回拷贝数。"""
    import copy as _copy
    n = 0
    for sh in cluster["shapes"]:
        el = _copy.deepcopy(sh._element)
        # 平移：所有 a:off（顶层与组内层级统一按同一 delta 平移即可）
        for off in el.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}off"):
            off.set("x", str(int(off.get("x", 0)) + dx))
            off.set("y", str(int(off.get("y", 0)) + dy))
        dst_slide.shapes._spTree.append(el)
        n += 1
    return n


# 整套配色体系（铁律）：所有选中页的主导色相必须同属一个体系（环形距离 ≤30°）
PALETTE_HUE_TOL = 30.0


def _hue_deg(hex6: str) -> float:
    r = int(hex6[0:2], 16) / 255
    g = int(hex6[2:4], 16) / 255
    b = int(hex6[4:6], 16) / 255
    import colorsys
    return colorsys.rgb_to_hsv(r, g, b)[0] * 360


def hue_dist(h1: float, h2: float) -> float:
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


def load_page_palette(template: Path) -> dict:
    """模板同目录 palette.json：{页码: {dominant, top3}}。无则返回 {}。"""
    p = template.with_name("palette.json")
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def cap_at_12(slot: dict) -> int | None:
    """该槽位按 12pt 排版时的容量（CJK 视觉字宽单位）。无数据返回 None。"""
    old = slot.get("font_size_pt")
    cpl, ml = slot.get("chars_per_line"), slot.get("max_lines")
    if not old or not cpl or not ml:
        return None
    cpl12 = max(1, math.floor(cpl * old / MIN_FONT_PT))
    ml12 = max(1, math.floor(ml * old / MIN_FONT_PT))
    return max(1, math.floor(cpl12 * ml12 * TOL))


# ------------------------------------------------------------------
# Slot resolution via detail.json
# ------------------------------------------------------------------
def load_slot_index(detail_path: Path | None) -> dict:
    """Return {(slide_number, slot_id): slot_dict}.

    slot_dict includes address + capacity metadata (max_chars, chars_per_line,
    max_lines, wrap, autofit, font_size_pt, level, role) when present so the
    overflow lint can use them.
    """
    if detail_path is None or not detail_path.exists():
        return {}
    if detail_path.suffix == ".gz" or detail_path.with_suffix(".json.gz").exists():
        import gzip
        with gzip.open(str(detail_path) + (".gz" if detail_path.suffix != ".gz" else ""),
                       "rt", encoding="utf-8") as f:
            detail = json.load(f)
    else:
        detail = json.loads(detail_path.read_text(encoding="utf-8"))
    index: dict = {}
    for page in detail.get("pages", []):
        slide_number = page["slide_number"]
        for slot in page.get("text_slots", []):
            slot.setdefault("expected_text", slot.get("current_text"))
            index[(slide_number, slot["slot_id"])] = slot
    return index


# ------------------------------------------------------------------
# Overflow lint (text-fits-the-box check)
# ------------------------------------------------------------------
def _visual_width(s: str) -> float:
    w = 0.0
    for c in s:
        if "\u4e00" <= c <= "\u9fff" or "\u3000" <= c <= "\u303f" or "\uff00" <= c <= "\uffef":
            w += 1.0
        elif c == " ":
            w += 0.35
        elif c.isascii():
            w += 0.5
        else:
            w += 0.8
    return w


def check_overflow(new_text: str, meta: dict) -> tuple[bool, str]:
    """Return (fits, message). Uses chars_per_line / max_lines from detail.json.

    'fits' is True when the text is expected to stay within the box. Boxes with
    autofit (PowerPoint shrink-to-fit) are always treated as fitting (soft).
    """
    if meta.get("capacity_unknown"):
        return True, ""  # geometry unreliable for this box
    cpl = meta.get("chars_per_line")
    max_lines = meta.get("max_lines")
    cap = meta.get("max_chars")   # already includes the calibration tolerance
    if not cpl or not max_lines or not cap:
        return True, ""  # no capacity data → can't lint
    total_vw = _visual_width(new_text.replace("\n", ""))
    # primary test: visual width vs the (tolerance-adjusted) capacity budget
    if total_vw <= cap:
        return True, ""
    # estimate needed lines for a helpful message
    needed = sum(max(1, math.ceil(_visual_width(seg) / cpl))
                 for seg in (new_text.split("\n") or [new_text]))
    sz = meta.get("font_size_pt")
    msg = (f"视觉宽度 {total_vw:.0f} > 容量 {cap} "
           f"(约需 {needed} 行 / 可容 {max_lines} 行, {sz}pt, 每行≈{cpl}字)")
    if meta.get("autofit"):
        return True, "AUTOFIT " + msg + " — PowerPoint 会自动缩字"
    return False, msg


# ------------------------------------------------------------------
# Shape lookup (recurses into groups)
# ------------------------------------------------------------------
def find_shape(shapes, shape_id: int):
    for shape in shapes:
        if shape.shape_id == shape_id:
            return shape
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            found = find_shape(shape.shapes, shape_id)
            if found is not None:
                return found
    return None


# ------------------------------------------------------------------
# Text mutation that preserves run-level formatting
# ------------------------------------------------------------------
def apply_edit_to_shape(shape, address: dict, new_text: str, expected: str | None,
                       strict: bool) -> tuple[bool, str]:
    if not shape.has_text_frame:
        return False, f"shape {shape.shape_id} has no text frame"
    tf = shape.text_frame
    pi = address.get("paragraph", 0)
    if pi >= len(tf.paragraphs):
        return False, f"paragraph {pi} out of range (have {len(tf.paragraphs)})"
    para = tf.paragraphs[pi]
    runs = list(para.runs)
    if not runs:
        return False, f"paragraph {pi} has no runs"

    ri = address.get("run")
    if ri is None:
        current = "".join(r.text for r in runs)
        if expected is not None and current != expected and strict:
            return False, (
                f"expected_text mismatch at paragraph level: "
                f"have {current!r}, expected {expected!r}"
            )
        runs[0].text = new_text
        for r in runs[1:]:
            r.text = ""
        return True, f"replaced paragraph (kept run 0 formatting): {current!r} -> {new_text!r}"

    if ri >= len(runs):
        return False, f"run {ri} out of range (have {len(runs)})"
    current = runs[ri].text
    if expected is not None and current != expected and strict:
        return False, (
            f"expected_text mismatch: have {current!r}, expected {expected!r}"
        )
    runs[ri].text = new_text
    return True, f"replaced run: {current!r} -> {new_text!r}"


# ------------------------------------------------------------------
# Slide pruning: keep only selected slides, in order
# ------------------------------------------------------------------
def prune_slides(prs, selected_1indexed: list[int]) -> None:
    sldIdLst = prs.slides._sldIdLst
    sld_ids = list(sldIdLst)
    total = len(sld_ids)
    keep_idx0 = [i - 1 for i in selected_1indexed]
    for i in keep_idx0:
        if i < 0 or i >= total:
            raise ValueError(f"selected slide {i + 1} out of range (1..{total})")

    # Build new order list of element references.
    new_order = [sld_ids[i] for i in keep_idx0]

    # Remove all entries, then re-append in the new order. Keeping the same
    # element instances preserves their r:id and avoids orphaning relationships.
    for sld in list(sldIdLst):
        sldIdLst.remove(sld)
    for sld in new_order:
        sldIdLst.append(sld)


# ------------------------------------------------------------------
# Main driver
# ------------------------------------------------------------------
def run(args) -> int:
    edits_spec = json.loads(args.edits.read_text(encoding="utf-8"))
    selected = list(edits_spec.get("selected_slides") or [])
    raw_edits = list(edits_spec.get("edits") or [])
    compose_spec = list(edits_spec.get("compose") or [])
    slot_index = load_slot_index(args.detail)

    prs = Presentation(args.template)
    n_slides = len(prs.slides)
    if not selected:
        selected = list(range(1, n_slides + 1))
    for s in selected:
        if s < 1 or s > n_slides:
            print(f"ERROR: selected slide {s} out of range 1..{n_slides}", file=sys.stderr)
            return 2

    # Resolve and group edits by slide_number (in TEMPLATE order, pre-prune)
    planned: list[dict] = []
    for e in raw_edits:
        slide_num = e["slide"]
        meta = None
        if "address" in e:
            addr = dict(e["address"])
            expected = e.get("expected_text") or addr.get("expected_text")
        else:
            slot_id = e.get("slot_id")
            if slot_id is None:
                print(f"ERROR: edit {e} missing both address and slot_id", file=sys.stderr)
                return 2
            key = (slide_num, slot_id)
            if key not in slot_index:
                print(f"ERROR: slot_id {slot_id!r} not found for slide {slide_num} in detail.json",
                      file=sys.stderr)
                return 2
            meta = slot_index[key]
            addr = dict(meta["address"])
            expected = e.get("expected_text") or meta.get("expected_text")
        planned.append({
            "slide": slide_num,
            "address": addr,
            "expected": expected,
            "new_text": e["new_text"],
            "meta": meta,
            "raw": e,
        })

    if args.dry_run:
        for p in planned:
            print(f"slide {p['slide']:>3} addr={p['address']} -> {p['new_text']!r}")
        return 0

    # Apply edits BEFORE pruning so slide indices match the template
    overflow_issues: list[str] = []
    ellipsis_issues: list[str] = []
    for p in planned:
        slide = prs.slides[p["slide"] - 1]
        shape_id = p["address"].get("shape_id")
        shape = find_shape(slide.shapes, shape_id)
        if shape is None:
            msg = f"slide {p['slide']}: shape_id {shape_id} not found"
            if args.strict:
                print(f"ERROR: {msg}", file=sys.stderr)
                return 3
            print(f"WARN:  {msg}", file=sys.stderr)
            continue
        ok, info = apply_edit_to_shape(
            shape, p["address"], p["new_text"], p["expected"], args.strict
        )
        prefix = "OK  " if ok else ("ERR " if args.strict else "WARN")
        print(f"{prefix} slide {p['slide']:>3} shape {shape_id}: {info}")
        if not ok and args.strict:
            return 4

        # Overflow check — advisory only. max_chars is a soft hint, not a hard
        # limit; we never block or truncate. We only print a gentle note so the
        # author can decide whether to rephrase more concisely.
        if not args.no_lint and p["meta"]:
            fits, omsg = check_overflow(p["new_text"], p["meta"])
            if omsg and not fits:
                slot_id = p["meta"].get("slot_id", "?")
                line = (f"slide {p['slide']:>3} {slot_id}: 可能偏长 {omsg} "
                        f"-> {p['new_text'][:24]!r}")
                overflow_issues.append(line)
                print(f"note {line}", file=sys.stderr)
            elif omsg and fits:  # autofit soft note
                print(f"note  slide {p['slide']:>3}: {omsg}", file=sys.stderr)

        # Catch accidental ellipsis-truncation, which looks worse than a slight
        # overflow. Advisory only.
        stripped = p["new_text"].rstrip()
        if stripped.endswith(("...", "..", "…", "……", "等等", "等。")):
            ellipsis_issues.append(
                f"slide {p['slide']:>3} {(p['meta'] or {}).get('slot_id', '?')}: "
                f"结尾疑似省略号截断 -> {p['new_text'][-16:]!r}")

    if overflow_issues:
        print(f"\n提示：{len(overflow_issues)} 处文字偏长（仅提示，不影响保存）。"
              f"可酌情用更精炼的措辞重写；但**不要截断加省略号**，也不要改字号——"
              f"宁可轻微超出。", file=sys.stderr)

    # ---- 组件组装：从其它页复制组件簇到画布页（偏移落位 + 文案覆盖 + 12pt） ----
    thr = float(getattr(args, 'min_font', None) or MIN_FONT_PT)
    if compose_spec:
        from pptx.util import Emu as _Emu
        EMU_IN = 914400
        total_copied = 0
        for cs in compose_spec:
            base_idx = int(cs["base"])
            base_slide = prs.slides[base_idx - 1]
            for item in cs.get("add", []):
                src_idx = int(item["slide"])
                src_slide = prs.slides[src_idx - 1]
                clusters = shape_clusters(src_slide)
                ci = int(item.get("component", 0))
                if ci < 0 or ci >= len(clusters):
                    print(f"WARN: compose slide {src_idx} 组件 {ci} 不存在（共 {len(clusters)} 簇），跳过",
                          file=sys.stderr)
                    continue
                cluster = clusters[ci]
                bl, bt, br, bb = cluster["bbox"]
                at = item.get("at")  # 英寸 [x, y]（组件左上角目标位置）
                if at:
                    dx, dy = int(at[0] * EMU_IN) - bl, int(at[1] * EMU_IN) - bt
                else:
                    dx = dy = 0
                copied = copy_cluster(base_slide, cluster, dx, dy)
                total_copied += copied
                # 文案覆盖：对复制后的形状按"原文子串"替换（保格式）
                for old, new in (item.get("texts") or {}).items():
                    for sh in base_slide.shapes:
                        if not sh.has_text_frame:
                            continue
                        for para in sh.text_frame.paragraphs:
                            for r in para.runs:
                                if old in (r.text or ""):
                                    r.text = r.text.replace(old, new)
                print(f"compose: 页{src_idx} 组件{ci}（{copied} 形状）→ 页{base_idx}"
                      + (f" @ {at}" if at else ""))
            # 复制进来的文字统一提到 12pt（铁律：组件文案也算正文）
            for sh in base_slide.shapes:
                if not sh.has_text_frame:
                    continue
                for para in sh.text_frame.paragraphs:
                    for r in para.runs:
                        if r.text.strip() and (r.font.size is None or r.font.size.pt < thr - 1e-6):
                            r.font.size = Pt(thr)
        if total_copied:
            print(f"组件组装完成：共复制 {total_copied} 个形状", file=sys.stderr)

    # ---- 配色主题化：选中页饱和用色统一映射到目标主题（默认自动取多数主色最近的
    #      标准主题；--theme 指定主题 id）。中性色不动，末步配色检查因此必然通过。 ----
    if not getattr(args, "no_min_font", False) or True:
        themes = load_themes()
        if themes:
            pal = load_page_palette(Path(args.template))
            thr = float(getattr(args, "min_font", None) or MIN_FONT_PT)
            theme_id = getattr(args, "theme", None)
            theme = themes.get(theme_id) if theme_id else None
            if theme is None and theme_id and (theme_id.startswith("#") or "," in theme_id):
                # 自定义色列表：#AABBCC,#336699,…（按序作为主/辅/强调）
                colors_custom = [c.strip().lstrip("#").upper() for c in theme_id.split(",") if c.strip()]
                theme = {"id": "custom", "name": "自定义配色",
                         "hue": _hue_deg(colors_custom[0]) if colors_custom else 0}
                colors = colors_custom
            if theme is None:
                # 自动：多数页主色 hue → 最近标准主题
                doms = [pal.get(str(sn), {}).get("dominant") for sn in selected
                        if pal.get(str(sn), {}).get("dominant")]
                hues = sorted(_hue_deg(c) for c in doms)
                base_h = hues[len(hues) // 2] if hues else None
                best, bd = None, 1e9
                for t in themes.values():
                    d = hue_dist(float(t["hue"]), base_h) if base_h is not None else 1e9
                    if d < bd:
                        best, bd = t, d
                theme = best
            if theme:
                colors = colors_custom if (theme_id and theme_id.startswith("#")) else theme_color_list(theme)
                recolored = 0
                for sn in selected:
                    n, _mp = unify_slide_colors(prs.slides[sn - 1], colors)
                    recolored += n
                print(f"主题化：已按「{theme.get('name', theme_id or theme['id'])}」统一"
                      f" {len(selected)} 页配色（替换 {recolored} 处颜色）", file=sys.stderr)

    if ellipsis_issues:
        print("\n⚠️ {} 处文字结尾是省略号，很可能是为凑长度而截断"
              "（这是最差的结果）。请改成完整、精炼的表达：".format(
                  len(ellipsis_issues)), file=sys.stderr)
        for line in ellipsis_issues:
            print(f"  - {line}", file=sys.stderr)

    # 正文 12pt 排版（铁律）：选中页的**全部**正文槽位一律置小四 12pt，
    # 文字按 12pt 容量硬校验——超出即拒绝（换字时就该按容量写，不要事后缩字号）。
    if not getattr(args, "no_min_font", False):
        thr = float(getattr(args, "min_font", None) or MIN_FONT_PT)
        small_runs = over_cap = 0
        cap_viol = []
        for sn in selected:
            metas = [(sid, meta) for (snum, sid), meta in slot_index.items()
                     if snum == sn and meta.get("role") in BODY_ROLES]
            for sid, meta in metas:
                addr = meta.get("address") or {}
                shape_id = addr.get("shape_id")
                if not shape_id:
                    continue
                shape = find_shape(prs.slides[sn - 1].shapes, shape_id)
                if shape is None or not shape.has_text_frame:
                    continue
                pi = addr.get("paragraph", 0)
                paras = shape.text_frame.paragraphs
                if not (0 <= pi < len(paras)):
                    continue
                final_text = "".join(r.text for r in paras[pi].runs).strip()
                for r in paras[pi].runs:
                    if r.text.strip() and (r.font.size is None or r.font.size.pt < thr - 1e-6):
                        r.font.size = Pt(thr)
                        small_runs += 1
                cap12 = cap_at_12(meta)
                if cap12 is None:
                    continue
                if _visual_width(final_text.replace("\n", "")) > cap12:
                    over_cap += 1
                    cap_viol.append((sn, sid, cap12, final_text[:20]))
        if small_runs:
            print(f"正文已统一排版为 {thr:g}pt（{cn_size_name(thr)}）：提升 {small_runs} 处",
                  file=sys.stderr)
        if cap_viol:
            allow = getattr(args, "allow_small_font", False)
            print(f"\n{'⚠️ （--allow-small-font 降级为警告）' if allow else '✗ 正文容量铁律'}："
                  f"{over_cap} 处正文超出 12pt 容量，12pt 下放不下：", file=sys.stderr)
            for sn, sid, cap12, txt in cap_viol[:12]:
                print(f"  slide {sn:>3} {sid} 容量{cap12}字 -> {txt!r}", file=sys.stderr)
            if len(cap_viol) > 12:
                print(f"  ...（其余 {len(cap_viol) - 12} 处略）", file=sys.stderr)
            if not allow:
                print("ERROR: 正文按 12pt 排版放不下，拒绝保存。"
                      "请把这几处文案改写到容量以内（意思保真、不截断），"
                      "或显式加 --allow-small-font 豁免。", file=sys.stderr)
                return 5

    # 整套配色体系（铁律，默认强制）：选中页主导色相必须同属一系；
    # --allow-mixed-palette 显式豁免降级为警告。
    pal = load_page_palette(Path(args.template))
    if pal and len(selected) >= 2:
        doms = []
        for sn in selected:
            ent = pal.get(str(sn))
            if ent and ent.get("dominant"):
                doms.append((sn, _hue_deg(ent["dominant"]), ent["dominant"]))
        if len(doms) >= 2:
            hues = sorted(d[1] for d in doms)
            base = hues[len(hues) // 2]
            mixed = [(sn, h, c) for sn, h, c in doms
                     if hue_dist(h, base) > PALETTE_HUE_TOL]
            if mixed:
                allow_m = getattr(args, "allow_mixed_palette", False)
                head = ("⚠️ （--allow-mixed-palette 降级为警告）" if allow_m
                        else "✗ 配色体系铁律")
                print(f"\n{head}：{len(mixed)}/{len(doms)} 页主色偏离整套主色相"
                      f"（base {base:.0f}°，容差 {PALETTE_HUE_TOL:.0f}°）。明细：",
                      file=sys.stderr)
                for sn, h, c in mixed[:10]:
                    print(f"  slide {sn:>3} 主色 #{c} hue {h:.0f}°", file=sys.stderr)
                if not allow_m:
                    print("ERROR: 整套 PPT 必须同一配色体系，拒绝保存。"
                          "请改选同色系页（show 查看每页主色），"
                          "或显式加 --allow-mixed-palette。", file=sys.stderr)
                    return 6

    prune_slides(prs, selected)
    prs.save(args.output)
    note = f"\nSaved {args.output} with {len(selected)} slides and {len(planned)} edits"
    print(note)
    return 0


def build(template, edits, output, detail=None, strict=False,
          dry_run=False, no_lint=False, min_font=MIN_FONT_PT,
          allow_small_font=False, no_min_font=False,
          allow_mixed_palette=False, theme=None) -> int:
    """Programmatic entry point: identical to the CLI, with explicit arguments."""
    from types import SimpleNamespace
    return run(SimpleNamespace(
        template=Path(template), edits=Path(edits), output=Path(output),
        detail=Path(detail) if detail else None,
        strict=strict, dry_run=dry_run, no_lint=no_lint,
        min_font=min_font, allow_small_font=allow_small_font,
        no_min_font=no_min_font, allow_mixed_palette=allow_mixed_palette,
        theme=theme))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("template", type=Path)
    ap.add_argument("edits", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--detail", type=Path, default=None)
    ap.add_argument("--no-lint", action="store_true",
                    help="disable the text-overflow check")
    ap.add_argument("--min-font", type=float, default=MIN_FONT_PT,
                    help="最小字号阈值 pt（默认 12 = 小四号）")
    ap.add_argument("--allow-small-font", action="store_true",
                    help="显式豁免最小字号铁律（降级为警告，默认拒绝出稿）")
    ap.add_argument("--no-min-font", action="store_true",
                    help="关闭最小字号门禁")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.detail is None:
        # Try sibling detail.json next to the template
        guess = args.template.with_name("detail.json")
        if guess.exists():
            args.detail = guess
            print(f"(auto-detected detail.json: {guess})", file=sys.stderr)

    return run(args)


if __name__ == "__main__":
    sys.exit(main())
