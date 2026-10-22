# -*- coding: utf-8 -*-
"""dna_extract — 从客户旧 PPT 量出"设计 DNA"（蒸馏 deck-dna：测量品味，不描述品味）。

对 1-3 份被认可的参考稿测量五类硬参数，产出 DNA JSON，供 freelayout 等引擎
按量出的参数出稿（而不是 AI 自己发明品味）：
  composition 节奏   —— 每页形状数指纹（识别"低密度分隔页→数据页"循环）
  colors             —— 实际渲染用色统计（不信主题声明，母版覆写常不符）
  fonts              —— 引用字体 + 嵌入字体（ppt/fonts/ 是否存在）
  text budget        —— 每页词数 median/mean/max + 最密 3 页（median 当新稿硬上限）
  recurring          —— 页脚/页码/来源行等跨页重复元素

用法:
  python scripts/dna_extract.py 旧稿1.pptx [旧稿2.pptx ...] -o dna.json
退出码: 0 成功 / 2 用法错。
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from collections import Counter
from statistics import mean, median

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from pptx.oxml.ns import qn


def walk(shapes):
    for sh in shapes:
        yield sh
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            try:
                yield from walk(sh.shapes)
            except Exception:
                pass


def extract(path: str) -> dict:
    prs = Presentation(path)
    words_per_page, fingerprints = [], []
    size_counter, font_counter, color_counter = Counter(), Counter(), Counter()
    footers = Counter()
    for slide in prs.slides:
        n_shapes, words = 0, 0
        for sh in walk(slide.shapes):
            n_shapes += 1
            # 实际填充色（不信主题声明）
            try:
                if sh.fill.type is not None and sh.fill.type == 1:
                    color_counter[str(sh.fill.fore_color.rgb)] += 1
            except Exception:
                pass
            try:
                if not (sh.has_text_frame and sh.text_frame.text.strip()):
                    continue
            except Exception:
                continue
            txt = sh.text_frame.text
            words += len(re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]", txt))
            if sh.top is not None and sh.top / 914400 > 6.8:
                footers[txt.strip()[:24]] += 1       # 页底重复元素
            for para in sh.text_frame.paragraphs:
                for r in para.runs:
                    if r.font.size:
                        size_counter[round(r.font.size.pt, 1)] += 1
                    if r.font.name:
                        font_counter[r.font.name] += 1
                    try:
                        rPr = r._r.rPr
                        if rPr is not None:
                            for sf in rPr.findall(qn("a:solidFill")):
                                c = sf.find(qn("a:srgbClr"))
                                if c is not None:
                                    color_counter[c.get("val")] += 1
                    except Exception:
                        pass
        words_per_page.append(words)
        fingerprints.append(n_shapes)
    embedded = []
    try:
        with zipfile.ZipFile(path) as z:
            embedded = [n for n in z.namelist() if n.startswith("ppt/fonts/")]
    except Exception:
        pass
    top_sizes = [s for s, _ in size_counter.most_common(8)]
    top_colors = [c for c, _ in color_counter.most_common(10)]
    densest = sorted(range(len(words_per_page)),
                     key=lambda i: -words_per_page[i])[:3]
    return {
        "source": path,
        "pages": len(words_per_page),
        "composition_fingerprint": fingerprints,
        "chaptering_hint": ("低密度分隔页→数据页循环"
                            if max(fingerprints, default=0) > 3 * min(fingerprints, default=1)
                            else "密度均匀"),
        "text_budget": {
            "median": int(median(words_per_page)) if words_per_page else 0,
            "mean": round(mean(words_per_page)) if words_per_page else 0,
            "max": max(words_per_page, default=0),
            "densest_pages": [{"page": i + 1, "words": words_per_page[i]} for i in densest],
            "note": "新稿每页硬上限取 median（略上取整）；不取 mean——离群页不抬高目标；超预算砍内容或拆页，禁止缩字号塞字",
        },
        "colors_actual": top_colors,
        "fonts": {"referenced": [f for f, _ in font_counter.most_common(8)],
                  "embedded_parts": len(embedded),
                  "note": "只引用未嵌入的字体在他人机器会劣质替换" if not embedded else ""},
        "recurring_footer": [t for t, _ in footers.most_common(5)],
        "type_scale": top_sizes,
    }


def main(argv):
    srcs, out = [], "dna.json"
    i = 0
    while i < len(argv):
        if argv[i] == "-o" and i + 1 < len(argv):
            out = argv[i + 1]
            i += 2
        else:
            srcs.append(argv[i])
            i += 1
    if not srcs:
        print(__doc__)
        return 2
    decks = [extract(s) for s in srcs if s.endswith(".pptx")]
    if not decks:
        print("✗ 未找到可解析的 .pptx 参考稿")
        return 2
    merged_budget = sorted(d["text_budget"]["median"] for d in decks)
    dna = {
        "version": 1,
        "sources": [d["source"] for d in decks],
        "per_deck": decks,
        "budget_hard_cap": merged_budget[len(merged_budget) // 2] if merged_budget else 0,
        "usage": ("把 budget_hard_cap 作为新稿每页词数硬上限；主题色取 per_deck[].colors_actual "
                  "的前几名；type_scale 作为字号阶梯基准。"),
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(dna, f, ensure_ascii=False, indent=1)
    print(f"✓ DNA 已写 {out}")
    print(f"  参考稿 {len(decks)} 份，词数硬上限 = {dna['budget_hard_cap']} 字/页")
    for d in decks:
        print(f"  {d['source']}: {d['pages']} 页，实际主色 {d['colors_actual'][:4]}，"
              f"字号档 {d['type_scale'][:5]}，{d['chaptering_hint']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
