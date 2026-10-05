# -*- coding: utf-8 -*-
"""下载微信文章里的 PPT 图片：python3 wechat_dl.py <url> <out_dir>"""
import re, sys, io, urllib.request, ssl
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
url, out = sys.argv[1], Path(sys.argv[2])
assert re.match(r"^https://mp\.weixin\.qq\.com/s/", url), "仅支持 https://mp.weixin.qq.com/s/ 链接"
out.mkdir(parents=True, exist_ok=True)

ctx = ssl.create_default_context()
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
html = io.open(out / "article.html", "wb")
with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
    data = r.read()
html.write(data); html.close()
text = data.decode("utf-8", "ignore")

m = re.search(r'<h1[^>]*class="rich_media_title"[^>]*>(.*?)</h1>', text, re.S) or \
    re.search(r'var msg_title = \'(.*?)\'', text) or \
    re.search(r'<meta property="og:title" content="(.*?)"', text)
title = re.sub(r"\s+", " ", m.group(1)).strip() if m else "(无标题)"
print("标题:", title)

srcs = re.findall(r'data-src="(https://mmbiz\.qpic\.cn/[^"]+)"', text)
seen, imgs = set(), []
for s in srcs:
    s = s.split("?")[0] + "?wx_fmt=jpeg" if "wx_fmt=" not in s else s
    key = s.split("?")[0]
    if key not in seen:
        seen.add(key); imgs.append(s)
print(f"找到 {len(imgs)} 张图片")

for i, src in enumerate(imgs, 1):
    ext = "png"
    mm = re.search(r"wx_fmt=(\w+)", src)
    if mm: ext = {"jpeg": "jpg", "jpg": "jpg", "png": "png", "gif": "gif"}.get(mm.group(1), "jpg")
    dest = out / f"{i:03d}.{ext}"
    try:
        rq = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(rq, timeout=30, context=ctx) as r:
            dest.write_bytes(r.read())
        print(f"  {dest.name}  {dest.stat().st_size//1024}KB")
    except Exception as e:
        print(f"  {dest.name}  FAIL {e}")
(out / "title.txt").write_text(title, encoding="utf-8")
