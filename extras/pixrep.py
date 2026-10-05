# -*- coding: utf-8 -*-
"""真·像素级复刻渲染器：读 ocr/<deck>_pNNN.json（原图坐标）→ 原位重建 pptx。
源图 1080 宽 → 1280 画布，等比 scale=1.18519。
每行文字：位置/字号(块高反推)/颜色(原图取色)全按原图；色块按检测矩形原位铺。"""
import os, sys, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rep_lib import *

SC = 1280 / 1080.0

def est_pt(h):
    return max(7.5, min(42, h * 0.75))

def render_page(prs, jf, serif_big=False):
    d = json.load(open(jf, encoding="utf-8"))
    s = add_slide(prs)
    rects = [r for r in d["rects"] if not (r[2] > 1000 and r[3] > 500)]
    rects = [r for r in rects if not (
        (255 - int(r[4][1:3], 16)) + (255 - int(r[4][3:5], 16)) + (255 - int(r[4][5:7], 16)) < 36 and r[2] < 200)]
    rects.sort(key=lambda r: -(r[2] * r[3]))
    for (x, y, w, h, c) in rects:
        rect(s, x * SC, y * SC, w * SC, h * SC, fill=c)
    for b in d["blocks"]:
        if b["conf"] < 0.3 or not b["text"].strip():
            continue
        x, y, w, h = b["x"] * SC, b["y"] * SC, b["w"] * SC, b["h"] * SC
        pt = est_pt(b["h"])
        col = b["color"]
        bold = b.get("bold", b["h"] >= 22)
        font = "微软雅黑"
        if serif_big and b["h"] >= 26:
            font = "宋体"
        tb = text(s, x - 2, y - pt * 0.32, w + 24, h + pt * 1.6, b["text"],
                  size=round(pt, 1), color=col, bold=bold, font=font, spacing=1.0)
        try:
            tb.text_frame.word_wrap = False
        except Exception:
            pass
    return s

def main(deck, pages, out):
    prs = new_deck()
    for n in pages:
        jf = f"ocr/{deck}_p{n:03d}.json"
        if os.path.exists(jf):
            render_page(prs, jf, serif_big=(deck == "23"))
    prs.save(out)
    print("saved", out)

if __name__ == "__main__":
    main("24", range(1, 19), "pix24.pptx")
    main("23", range(1, 18), "pix23.pptx")
