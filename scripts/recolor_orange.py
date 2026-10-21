# -*- coding: utf-8 -*-
"""deck-all 模板整体重着色 → 橙色系（活力橙）。
所有饱和色（s>=0.18）的色相线性映射进 8°~38° 橙色窗口，保留明度/饱和度层级；
中性色（黑白灰）与位图媒体不动。完成后重建 palette.json 页主色索引。"""
import colorsys
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

TPL = Path(__file__).resolve().parent.parent / "templates" / "deck-all" / "template.pptx"
PAL = Path(__file__).resolve().parent.parent / "templates" / "deck-all" / "palette.json"

HUE_LO, HUE_HI = 8.0, 38.0   # 橙色窗口
SAT_MIN = 0.18


def recolor_hex(hex6: str) -> str | None:
    r = int(hex6[0:2], 16) / 255
    g = int(hex6[2:4], 16) / 255
    b = int(hex6[4:6], 16) / 255
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    if s < SAT_MIN:
        return None
    hd = h * 360
    new_h = (HUE_LO + (hd % 360) / 360 * (HUE_HI - HUE_LO)) / 360
    nr, ng, nb = colorsys.hsv_to_rgb(new_h, s, v)
    return "%02X%02X%02X" % (round(nr * 255), round(ng * 255), round(nb * 255))


def main():
    global replaced
    replaced = 0
    zin = zipfile.ZipFile(TPL)
    tmp = str(TPL) + ".tmp"
    replaced = 0
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zo:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if re.fullmatch(r"ppt/slides/slide\d+\.xml", item.filename):
                xml = data.decode("utf-8")
                def sub(m):
                    global replaced
                    new = recolor_hex(m.group(1).upper())
                    if new is None:
                        return m.group(0)
                    replaced += 1
                    return 'val="' + new + '"'
                xml = re.sub(r'val="([0-9A-Fa-f]{6})"', sub, xml)
                data = xml.encode("utf-8")
            zo.writestr(item.filename, data)
    zin.close()
    os_replace(tmp, TPL)
    print(f"重着色 {replaced} 处颜色 -> {TPL.name} {TPL.stat().st_size/1048576:.2f}MB")

    # 重建 palette.json（页主色速查）
    z = zipfile.ZipFile(TPL)
    pages = {}
    for n in z.namelist():
        m = re.fullmatch(r"ppt/slides/slide(\d+)\.xml", n)
        if not m:
            continue
        pg = int(m.group(1))
        c = Counter(re.findall(r'val="([0-9A-Fa-f]{6})"', z.read(n).decode("utf-8", "ignore")))
        acc = Counter()
        for h, n_ in c.items():
            r = int(h[0:2], 16) / 255
            g = int(h[2:4], 16) / 255
            b = int(h[4:6], 16) / 255
            hdeg, s, v = colorsys.rgb_to_hsv(r, g, b)
            if s >= 0.25 and 0.15 < v < 0.95:
                acc[h.upper()] += n_
        if acc:
            pages[str(pg)] = {"dominant": acc.most_common(1)[0][0],
                              "top3": [c for c, _ in acc.most_common(3)]}
    PAL.write_text(json.dumps(pages, indent=0), encoding="utf-8")
    print(f"palette.json 重建：{len(pages)} 页")


def os_replace(a, b):
    os.replace(a, b)


import os  # noqa: E402
main()
