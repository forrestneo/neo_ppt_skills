# -*- coding: utf-8 -*-
"""重算颜色层：调色板连通域色块 + 直方图取色。复用已有 OCR boxes，只补 color/bg/rects/bold。"""
import os, sys, io, json, glob
from collections import Counter, deque
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8")

def dist(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[2]-b[2])

def fg_bg(im, box):
    x, y, w, h = box
    c = im.crop((max(0, x), max(0, y), min(im.width, x+w), min(im.height, y+h))).convert("RGB")
    q = Counter(((r//24*24, g//24*24, b//24*24) for r, g, b in c.getdata()))
    bg = q.most_common(1)[0][0]
    cands = [(n, col) for col, n in q.items() if dist(col, bg) > 140]
    if not cands:
        cands = [(n, col) for col, n in q.items() if dist(col, bg) > 80]
    fg = max(cands)[1] if cands else tuple(max(0, v-90) for v in bg)
    return "#%02X%02X%02X" % fg, "#%02X%02X%02X" % bg

def palette_rects(im, step=4, min_px=22):
    small = im.convert("RGB").resize((im.width//step, im.height//step))
    w, h = small.size
    px = list(small.getdata())
    hist = Counter(px)
    pal = []
    for col, n in hist.most_common(400):
        if n < w*h*0.0018:
            continue
        if min(col) > 246:
            continue
        if any(dist(col, p[0]) < 40 for p in pal):
            continue
        pal.append((col, n))
        if len(pal) >= 8:
            break
    if not pal:
        return []
    cls = []
    for p in px:
        best, bd = -1, 999
        for i, (col, _) in enumerate(pal):
            dd = dist(p, col)
            if dd < bd:
                bd, best = dd, i
        cls.append(best if bd < 90 else -1)
    out = []
    for ci in range(len(pal)):
        seen = [False]*(w*h)
        for start in range(w*h):
            if seen[start] or cls[start] != ci:
                continue
            qx = deque([start]); seen[start] = True
            minx, miny, maxx, maxy, cnt = w, h, 0, 0, 0
            while qx:
                cur = qx.popleft()
                cy, cx = divmod(cur, w)
                minx = min(minx, cx); maxx = max(maxx, cx)
                miny = min(miny, cy); maxy = max(maxy, cy); cnt += 1
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = cx+dx, cy+dy
                    if 0 <= nx < w and 0 <= ny < h:
                        ni = ny*w+nx
                        if not seen[ni] and cls[ni] == ci:
                            seen[ni] = True; qx.append(ni)
            bw, bh = (maxx-minx+1)*step, (maxy-miny+1)*step
            if bw >= min_px and bh >= min_px and cnt >= (bw//step)*(bh//step)*0.45:
                out.append((minx*step, miny*step, bw, bh, "#%02X%02X%02X" % pal[ci][0]))
    return out

for jf in sorted(glob.glob("ocr/*_p*.json")):
    pref = os.path.basename(jf)[:2]
    num = int(os.path.basename(jf)[4:7])
    src = glob.glob(rf"..\..\图片\{pref}_*\{num:03d}.*")[0]
    im = Image.open(src)
    d = json.load(open(jf, encoding="utf-8"))
    for b in d["blocks"]:
        fg, bg = fg_bg(im, (b["x"], b["y"], b["w"], b["h"]))
        b["color"], b["bg"] = fg, bg
        sat = dist(tuple(int(bg[i:i+2], 16) for i in (1, 3, 5)), (255, 255, 255))
        b["bold"] = b["h"] >= 20 or sat > 100
    d["rects"] = palette_rects(im)
    json.dump(d, io.open(jf, "w", encoding="utf-8"), ensure_ascii=False)
    print(os.path.basename(jf), len(d["rects"]), "rects")
