# -*- coding: utf-8 -*-
"""measure_deck — 五维排版量化（自评工具，蒸馏 luobo-ppt critique/review 证据表）。

对成品 .pptx 输出五维机器证据（统一/层级/传达/节奏/细节），分数槽留给人打分
——五项各算各的，不许取平均（"统一 9 分、节奏 4 分"是合法且常见的）。

用法:
  python scripts/measure_deck.py 成品.pptx [--json out.json]
退出码: 0 恒定（测量器不拦截交付，只出证据）。
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

IN = 914400


def walk(shapes):
    for sh in shapes:
        yield sh
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            try:
                yield from walk(sh.shapes)
            except Exception:
                pass


def measure(path: str) -> dict:
    prs = Presentation(path)
    all_sizes, all_fonts = [], []
    pages = []
    for idx, slide in enumerate(prs.slides, 1):
        sizes, n_pic, n_shape, lefts, units = [], 0, 0, [], 0
        for sh in walk(slide.shapes):
            n_shape += 1
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                n_pic += 1
            try:
                if not (sh.has_text_frame and sh.text_frame.text.strip()):
                    continue
            except Exception:
                continue
            if sh.left is not None:
                lefts.append(sh.left / IN)
            for para in sh.text_frame.paragraphs:
                for r in para.runs:
                    txt = (r.text or "").strip()
                    if not txt:
                        continue
                    units += len(re.findall(r"[\u4e00-\u9fff]", txt))
                    units += len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\.\-%]*", txt))
                    if r.font.size:
                        sizes.append(r.font.size.pt)
                        all_sizes.append(r.font.size.pt)
                    if r.font.name:
                        all_fonts.append(r.font.name)
        med = sorted(sizes)[len(sizes) // 2] if sizes else 0
        mx = max(sizes) if sizes else 0
        pages.append({"page": idx, "shapes": n_shape, "pictures": n_pic,
                      "runs": len(sizes), "max_pt": mx, "median_pt": med,
                      "level_ratio": round(mx / med, 2) if med else 0,
                      "text_units": units})
    # near-miss：同页文本框左缘差 0.03~0.18in 的"差一点没对齐"
    near_miss = 0
    for slide in prs.slides:
        ls = sorted(sh.left / IN for sh in walk(slide.shapes)
                    if sh.has_text_frame and sh.text_frame.text.strip()
                    and sh.left is not None)
        for i in range(len(ls)):
            for j in range(i + 1, len(ls)):
                d = ls[j] - ls[i]
                if 0.03 <= d <= 0.18:
                    near_miss += 1
                if d > 0.18:
                    break
    size_hist = Counter(round(s, 1) for s in all_sizes)
    fp = [p["shapes"] for p in pages]
    worst_streak, cur = 1, 1
    for a, b in zip(fp, fp[1:]):
        cur = cur + 1 if a == b else 1
        worst_streak = max(worst_streak, cur)
    return {
        "unity": {"font_size_kinds": len(size_hist),
                  "standard": "≤8 好，>10 散",
                  "fonts": sorted(set(all_fonts))[:8],
                  "size_histogram": sorted(size_hist.items())},
        "hierarchy": {"per_page_ratio": [p["level_ratio"] for p in pages],
                      "standard": "每页最大/中位字号 ≥1.5",
                      "weak_pages": [p["page"] for p in pages if p["level_ratio"] < 1.5]},
        "details": {"near_miss_count": near_miss,
                    "standard": "左缘差 0.03-0.18in 的对齐近失误，应接近 0"},
        "communication": {"per_page_units": [p["text_units"] for p in pages],
                          "standard": "阅读档 ≤200 字/页（口播档减半）"},
        "rhythm": {"layout_fingerprint": fp, "worst_same_layout_streak": worst_streak,
                   "standard": "无连续 ≥3 页同指纹"},
        "pei": {"picture_ratio": round(sum(p["pictures"] for p in pages) /
                                       max(1, sum(p["shapes"] for p in pages)), 3),
                "standard": "位图占比越低可编辑性越高（L3 目标≈0）"},
        "pages": pages,
    }


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    src = argv[0]
    json_out = None
    if "--json" in argv:
        i = argv.index("--json")
        json_out = argv[i + 1]
    m = measure(src)
    print("=== 统一 ===")
    print(f"字号种数: {m['unity']['font_size_kinds']} ({m['unity']['standard']})")
    print(f"字体: {m['unity']['fonts']}")
    print("=== 层级（逐页最大/中位）===")
    print(f"{m['hierarchy']['per_page_ratio']}  弱页(<1.5): {m['hierarchy']['weak_pages'] or '无'}")
    print("=== 细节 ===")
    print(f"near-miss 对齐近失误: {m['details']['near_miss_count']} ({m['details']['standard']})")
    print("=== 传达（逐页字数）===")
    print(f"{m['communication']['per_page_units']}  ({m['communication']['standard']})")
    print("=== 节奏 ===")
    print(f"版式指纹: {m['rhythm']['layout_fingerprint']}  最长连续同指纹: "
          f"{m['rhythm']['worst_same_layout_streak']} ({m['rhythm']['standard']})")
    print("=== PEI ===")
    print(f"位图/形状占比: {m['pei']['picture_ratio']} ({m['pei']['standard']})")
    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False, indent=1)
        print(f"（JSON 已写 {json_out}）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
