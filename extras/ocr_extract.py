# -*- coding: utf-8 -*-
"""对全部源图跑 OCR + 色块检测，输出 ocr/<deck>_pNNN.json
每条: {text, conf, x,y,w,h (1080源图坐标), color(文字色), bgcolor(块底色)}"""
import os, sys, io, json, glob
sys.stdout.reconfigure(encoding="utf-8")
from collections import Counter
try:
    from rapidocr_onnxruntime import RapidOCR
except ImportError:
    from rapidocr_paddle import RapidOCR
from PIL import Image

ocr = RapidOCR()
OUT = "ocr"
os.makedirs(OUT, exist_ok=True)

def sample_colors(im, box):
    """box=(x,y,w,h) 源图坐标; 返回(文字色, 底色) hex"""
    x, y, w, h = box
    im2 = im.crop((max(0, x - 2), max(0, y - 2), min(im.width, x + w + 2), min(im.height, y + h + 2))).convert("RGB")
    px = list(im2.getdata())
    if not px:
        return "#333333", "#FFFFFF"
    cnt = Counter(px)
    bg = cnt.most_common(1)[0][0]
    darks = [(c, n) for c, n in cnt.items() if abs(c[0]-bg[0]) + abs(c[1]-bg[1]) + abs(c[2]-bg[2]) > 120]
    if darks:
        darks.sort(key=lambda cn: -cn[1])
        fg = darks[0][0]
    else:
        fg = tuple(max(0, v - 90) for v in bg)
    return "#%02X%02X%02X" % fg, "#%02X%02X%02X" % bg

def color_rects(im, step=6, min_size=28):
    """检测大块纯色矩形（非白/近白），返回 [(x,y,w,h,hex)] 粗粒度"""
    im2 = im.convert("RGB").resize((im.width // step, im.height // step))
    w, h = im2.size
    px = im2.load()
    def is_colored(c):
        r, g, b = c
        return not (r > 238 and g > 238 and b > 238)
    seen = [[False] * w for _ in range(h)]
    rects = []
    for yy in range(h):
        for xx in range(w):
            if seen[yy][xx] or not is_colored(px[xx, yy]):
                continue
            c0 = px[xx, yy]
            rw = 0
            while xx + rw < w and not seen[yy][xx + rw] and is_colored(px[xx + rw, yy]) and \
                  abs(px[xx + rw, yy][0]-c0[0]) + abs(px[xx + rw, yy][1]-c0[1]) + abs(px[xx + rw, yy][2]-c0[2]) < 60:
                rw += 1
            rh = 0
            grow = True
            while yy + rh < h and grow:
                for k in range(rw):
                    if seen[yy + rh][xx + k] or not is_colored(px[xx + k, yy + rh]) or \
                       abs(px[xx + k, yy + rh][0]-c0[0]) + abs(px[xx + k, yy + rh][1]-c0[1]) + abs(px[xx + k, yy + rh][2]-c0[2]) >= 60:
                        grow = False
                        break
                if grow:
                    rh += 1
            if rw * step >= min_size and rh * step >= min_size:
                rects.append((xx * step, yy * step, rw * step, rh * step,
                              "#%02X%02X%02X" % c0))
            for dy in range(rh):
                for dx in range(rw):
                    seen[yy + dy][xx + dx] = True
    return rects

jobs = []
for d, pref in ((r"..\..\图片\24_2lWLM-Lp", "24"), (r"..\..\图片\23_SqHp6Sl4", "23")):
    for f in sorted(glob.glob(os.path.join(d, "0*.png")) + glob.glob(os.path.join(d, "0*.jpg"))):
        n = int(os.path.basename(f)[:3])
        if (pref == "24" and n > 18) or (pref == "23" and n > 17):
            continue
        jobs.append((f, pref, n))
for f, pref, n in jobs:
    outp = f"{OUT}/{pref}_p{n:03d}.json"
    if os.path.exists(outp):
        continue
    im = Image.open(f)
    result, _ = ocr(f)
    blocks = []
    for box, text, conf in result:
        xs = [p[0] for p in box]; ys = [p[1] for p in box]
        x, y = round(min(xs)), round(min(ys))
        w, h = round(max(xs) - min(xs)), round(max(ys) - min(ys))
        fg, bg = sample_colors(im, (x, y, w, h))
        blocks.append({"text": text, "conf": round(float(conf), 2), "x": x, "y": y, "w": w, "h": h,
                       "color": fg, "bg": bg})
    rects = color_rects(im)
    json.dump({"blocks": blocks, "rects": rects}, io.open(outp, "w", encoding="utf-8"),
              ensure_ascii=False)
    print(f"{pref} p{n:03d}: {len(blocks)} blocks, {len(rects)} rects")
