# -*- coding: utf-8 -*-
"""出稿最后一步：整套 PPT 配色检查（铁律，写在 skills 出稿流程末尾）。

扫描成品 pptx 全部页面的饱和用色，判定整套是否属于同一个配色体系：
  - 主色相环形距离 ≤ --max-dist（默认 30°）视为同系
  - 一页 30% 以上饱和用色落在体系外 → 记为杂色页；杂色页 >0 → 拒绝交付
  - 报告最接近的标准配色主题（scripts/palettes.json）

用法:
  python palette_check.py 成品.pptx            # 通过 rc=0，不通过 rc=3
  python palette_check.py 成品.pptx --json     # 机器可读输出
"""
import colorsys
import json
import math
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
PALETTES = HERE / "palettes.json"
SAT_MIN = 0.25
VAL_MIN, VAL_MAX = 0.15, 0.97
PAGE_OUT_RATIO = 0.50   # 单页过半饱和用色出系 → 杂色页（二级辅助色属正常）


def hue_deg(hex6: str) -> float:
    r = int(hex6[0:2], 16) / 255
    g = int(hex6[2:4], 16) / 255
    b = int(hex6[4:6], 16) / 255
    return colorsys.rgb_to_hsv(r, g, b)[0] * 360


def sv(hex6: str):
    r = int(hex6[0:2], 16) / 255
    g = int(hex6[2:4], 16) / 255
    b = int(hex6[4:6], 16) / 255
    return colorsys.rgb_to_hsv(r, g, b)[1], colorsys.rgb_to_hsv(r, g, b)[2]


def hue_dist(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def scan(path: str):
    """逐页统计饱和用色：{页码: Counter{hex: 次数}}。
    只统计 presentation.xml 实际引用的页（prune 会遗留孤儿 slide 部件）。"""
    z = zipfile.ZipFile(path)
    try:
        rels = z.read("ppt/_rels/presentation.xml.rels").decode("utf-8")
        rid2tgt = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels))
        pres = z.read("ppt/presentation.xml").decode("utf-8")
        used = set()
        for rid in re.findall(r"<p:sldId[^>]*r:id=\"(rId\d+)\"", pres):
            tgt = rid2tgt.get(rid, "")
            tgt = tgt.lstrip("/")
            if not tgt.startswith("ppt/"):
                tgt = "ppt/" + tgt
            used.add(tgt)
    except Exception:
        used = None
    out = {}
    for n in z.namelist():
        m = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", n)
        if not m:
            continue
        if used is not None and n not in used:
            continue  # 孤儿部件（已从放映列表剔除）
        pg = int(m.group(1))
        c = Counter()
        for h in re.findall(r'srgbClr val="([0-9A-Fa-f]{6})"', z.read(n).decode("utf-8", "ignore")):
            h = h.upper()
            s, v = sv(h)
            if s >= SAT_MIN and VAL_MIN < v < VAL_MAX:
                c[h] += 1
        if c:
            out[pg] = c
    return out


def nearest_theme(hue: float):
    try:
        themes = json.loads(PALETTES.read_text(encoding="utf-8"))["themes"]
    except Exception:
        return None
    best, bd = None, 1e9
    for t in themes:
        d = hue_dist(float(t["hue"]), hue)
        if d < bd:
            best, bd = t, d
    return (best, bd) if best and bd <= 30 else None


def check(path: str, max_dist: float = 30.0):
    pages = scan(path)
    if not pages:
        return {"ok": True, "note": "无饱和用色（纯黑白灰稿），视为通过", "pages": 0}
    # 环形中位主色
    masses = []
    for pg, c in pages.items():
        tot = sum(c.values())
        h = hue_deg(c.most_common(1)[0][0])
        masses.append((pg, h, tot))
    masses.sort(key=lambda x: x[1])
    base = masses[len(masses) // 2][1]
    bad_pages = []
    for pg, c in pages.items():
        tot = sum(c.values())
        out_w = sum(n for h, n in c.items() if hue_dist(hue_deg(h), base) > max_dist)
        if out_w / tot > PAGE_OUT_RATIO:
            bad_pages.append((pg, round(100 * out_w / tot)))
    theme = nearest_theme(base)
    ok = not bad_pages
    return {"ok": ok, "pages": len(pages), "base_hue": round(base, 1),
            "theme": theme[0]["id"] if theme else None,
            "theme_name": theme[0]["name"] if theme else "无匹配标准主题",
            "bad_pages": [{"page": pg, "out_ratio": r} for pg, r in bad_pages]}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    path = argv[0]
    res = check(path)
    if res.get("json") or "--json" in argv:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        if res["ok"]:
            t = f"（匹配标准主题：{res['theme_name']}）" if res.get("theme") else ""
            print(f"✓ 最终配色检查通过：{res['pages']} 页同属一套配色体系"
                  f"（主色相 {res.get('base_hue', 0):.0f}°）{t}")
        else:
            print(f"✗ 最终配色检查未通过：出现体系外配色页。"
                  f"主色相 {res.get('base_hue', 0):.0f}°，杂色页：", file=sys.stderr)
            for bp in res.get("bad_pages", []):
                print(f"  第{bp['page']}页 体系外用色占比 {bp['out_ratio']}%", file=sys.stderr)
            print("ERROR: 整套 PPT 必须同一配色体系（铁律）。"
                  "请移除/改版杂色页，或统一替换主色后重新出稿。", file=sys.stderr)
    return 0 if res["ok"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
