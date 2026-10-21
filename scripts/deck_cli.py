# -*- coding: utf-8 -*-
"""deck-all 合辑模板调用工具（行业中立：内容骨架全行业通用，中英文皆可）
  python3 deck_cli.py find 关键词            # 按主题搜页（查 use_for/标题）
  python3 deck_cli.py show 页码              # 看某页版式与可编辑槽位
  python3 deck_cli.py build -o 输出.pptx 页码 "新标题" [页码 "标题" ...]
                                         [--set 页码:slot_id=文本 ...]
  不记 slot_id 时只给 页码+新标题 即可（自动命中该页 title_slot）。
  出稿自动过静态排版门禁（文字出界/占位符残留=error 拒绝交付 rc=4，
  --allow-layout-errors 显式豁免）；交付前建议再跑 visual_gate.py 渲染视觉门。
"""
import sys, os, json, re, shutil, subprocess
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
_skill_root = os.path.dirname(HERE)          # 技能根目录（scripts 的上一级）
_cands = [os.path.join(_skill_root, "templates", "deck-all"),
          os.path.join(HERE, "templates", "deck-all")]
_cands = [os.path.normpath(c) for c in _cands]
TPL = next((c for c in _cands
            if os.path.isfile(os.path.join(c, "detail.json.gz"))
            or os.path.isfile(os.path.join(c, "detail.json"))), _cands[0])
_b_cands = [os.path.normpath(c) for c in (
    os.path.join(HERE, "build_pptx.py"),
    os.path.join(_skill_root, "scripts", "build_pptx.py"))]
BUILD = next((c for c in _b_cands if os.path.isfile(c)), _b_cands[0])

def load():
    import gzip
    plain = os.path.join(TPL, "detail.json")
    packed = plain + ".gz"
    if os.path.isfile(packed):
        with gzip.open(packed, "rt", encoding="utf-8") as f:
            return json.load(f)
    return json.load(open(plain, encoding="utf-8"))

def page_title(d, pg):
    p = d["pages"][pg - 1]
    ts = next((x for x in p["text_slots"] if x["slot_id"] == p.get("title_slot_id")), None)
    return (ts or {}).get("current_text", "(无标题槽)")

def cap12(slot):
    """该正文槽按 12pt（小四）排版时的容量（CJK 等宽单位；英文≈2 字符/单位）。"""
    import math
    old = slot.get("font_size_pt")
    cpl, ml = slot.get("chars_per_line"), slot.get("max_lines")
    if not old or not cpl or not ml:
        return None
    cpl12 = max(1, math.floor(cpl * old / 12.0))
    ml12 = max(1, math.floor(ml * old / 12.0))
    return max(1, math.floor(cpl12 * ml12 * 0.9))


def cmd_find(kw):
    d = load()
    kw = kw.lower()
    hits = []
    for p in d["pages"]:
        hay = (p["use_for"] + " " + page_title(d, p["slide_number"])).lower()
        if kw in hay:
            hits.append(p)
    print(f"共 {len(hits)} 页命中「{kw}」：")
    for p in hits[:40]:
        print(f"  第{p['slide_number']:>3}页  {p['use_for'][:70]}")
    if len(hits) > 40:
        print(f"  ...（其余 {len(hits)-40} 页略）")

def cmd_components(pg):
    """列出某页的组件（顶层形状/组合），供 compose 组装挑选。"""
    from pptx import Presentation
    HERE = os.path.dirname(os.path.abspath(__file__))
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import build_pptx as bp
    tpl_dir = os.path.realpath(TPL)
    prs = Presentation(os.path.join(tpl_dir, "template.pptx"))
    slide = prs.slides[pg - 1]
    comps = bp.top_components(slide)
    EMU = 914400
    print(f"第{pg}页 共 {len(comps)} 个组件（顶层形状/组合，按面积降序）")
    for c in comps:
        summary = " / ".join(c["texts"])[:46] or "（无文字，纯图形）"
        x, y = c["bbox"][0] / EMU, c["bbox"][1] / EMU
        print(f"  组件{c['idx']:>3}  位置({x:5.2f},{y:5.2f})in  {summary}")
def load_palette():
    pal = os.path.join(TPL, "palette.json")
    if os.path.isfile(pal):
        return json.load(open(pal, encoding="utf-8"))
    return {}


def cmd_show(pg):
    d = load()
    p = d["pages"][pg - 1]
    print(f"第{pg}页  [{p['role']}]  密度:{p['text_density']}"
          "  （出稿正文一律 12pt=小四；下表容量即 12pt 容量，超字数会被拒绝）")
    print("use_for:", p["use_for"])
    ent = load_palette().get(str(pg))
    if ent:
        print("页主色:", " ".join("#" + c for c in ent.get("top3", [ent.get("dominant", "?")])),
          "  —— 整套 PPT 须同色系，混选会被配色铁律拒绝")
    ts = next((x for x in p["text_slots"] if x["slot_id"] == p.get("title_slot_id")), None)
    if ts:
        print(f"标题槽: {ts['slot_id']}  现:「{ts['current_text'][:36]}」  容量≈{ts['max_chars']}字")
    ed = [x for x in p["text_slots"] if x.get("editable")][:14]
    tiny = [x for x in p["text_slots"] if x.get("editable")
            and not cap12(x) and x["slot_id"] != p.get("title_slot_id")]
    if tiny:
        print(f"⚠ 本页含 {len(tiny)} 处天然小字槽（模板原文即小于 12pt 的轴标签/"
              "图例类，12pt 重排会拒绝）：出稿需 --allow-small-font 豁免，"
              "或只选其他页")
    print(f"可编辑槽位（前{len(ed)}个 / 共{len(p['text_slots'])}个）:")
    for x in ed:
        c = cap12(x)
        cap = f"≤{c}字" if c else "容量?"
        print(f"  {x['slot_id']}  <{x['role']}>  12pt{cap}  现:「{x['current_text'][:24]}」")
    more = [x for x in p["text_slots"] if x.get("editable") and x["role"] == "页面标题"
            and x["slot_id"] != p.get("title_slot_id")]
    if more:
        print("⚠ 本页还有其他标题段（多行标题请一并替换，否则叠字）:")
        for x in more:
            print(f"  {x['slot_id']}  现:「{x['current_text'][:30]}」")

def _confine(name):
    """把固定文件名规范化并限定在当前工作目录内，越界即拒写。"""
    cwd = os.path.realpath(os.getcwd())
    p = os.path.realpath(os.path.join(cwd, name))
    if not p.startswith(cwd + os.sep):
        raise ValueError(f"输出路径越界: {name}")
    return p

def cmd_build(argv):
    out = _confine("deck_out.pptx")
    if "-o" in argv:
        i = argv.index("-o")
        if i + 1 >= len(argv):
            print("用法错误：-o 后需要输出路径")
            return
        out = _confine(argv[i + 1])
        del argv[i:i + 2]
    build_tmp = _confine("deck_build_tmp.pptx")
    sets = []
    allow_small_font = allow_mixed = allow_layout = False
    theme_id = None
    font_id = "楷体"
    while "--set" in argv:
        i = argv.index("--set"); sets.append(argv[i + 1]); del argv[i:i + 2]
    if "--allow-small-font" in argv:
        allow_small_font = True
        argv.remove("--allow-small-font")
    if "--allow-mixed-palette" in argv:
        allow_mixed = True
        argv.remove("--allow-mixed-palette")
    if "--allow-layout-errors" in argv:
        allow_layout = True
        argv.remove("--allow-layout-errors")
    if "--theme" in argv:
        i = argv.index("--theme")
        theme_id = argv[i + 1]; del argv[i:i + 2]
    if "--font" in argv:
        i = argv.index("--font")
        font_id = argv[i + 1] or None; del argv[i:i + 2]
    compose_spec = []
    if "--compose" in argv:
        i = argv.index("--compose")
        cf = argv[i + 1]; del argv[i:i + 2]
        compose_spec = json.loads(Path(_confine(cf)).read_text(encoding="utf-8")).get("compose", [])
    pairs = list(zip(argv[0::2], argv[1::2]))
    if not pairs and not sets:
        print("用法: build 页码 \"新标题\" ... [--set 页码:slot_id=文本 ...]  （默认输出 deck_out.pptx，生成后自行改名）")
        return
    d = load()
    slides, edits = [], []
    for pg, title in pairs:
        try:
            pg = int(pg)
        except ValueError:
            print(f"✗ 页码必须是数字: {pg!r}")
            return
        p = d["pages"][pg - 1]
        slides.append(pg)
        if p.get("title_slot_id"):
            edits.append({"slide": pg, "slot_id": p["title_slot_id"], "new_text": title})
        else:
            print(f"⚠ 第{pg}页无标题槽，标题「{title}」未替换")
    for spec in sets:
        pg, rest = spec.split(":", 1)
        slot, txt = rest.split("=", 1)
        slides.append(int(pg))
        edits.append({"slide": int(pg), "slot_id": slot, "new_text": txt})
    slides = sorted(set(slides))
    spec = {"template_slug": "deck-all", "selected_slides": slides, "edits": edits,
            **({"compose": compose_spec} if compose_spec else {})}
    tmp = _confine("deck_edits.json")      # 规范化+限定目录后落盘，构建后保留供排查
    Path(tmp).write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    tpl_dir = os.path.realpath(TPL)
    if not tpl_dir.startswith(_skill_root):
        print("✗ 模板目录越界（须位于技能目录内）")
        return
    build_dir = os.path.dirname(BUILD)
    if build_dir not in sys.path:
        sys.path.insert(0, build_dir)
    import build_pptx                     # 固定名普通导入，无动态路径执行
    detail_path = os.path.join(tpl_dir, "detail.json.gz")
    if not os.path.isfile(detail_path):
        detail_path = os.path.join(tpl_dir, "detail.json")
    rc = build_pptx.build(os.path.join(tpl_dir, "template.pptx"), tmp, build_tmp,
                          detail=detail_path, allow_small_font=allow_small_font,
                          allow_mixed_palette=allow_mixed, theme=theme_id,
                          font=font_id)
    if rc != 0 or not os.path.isfile(build_tmp):
        print("✗ 构建未产出中间文件，中止")
        sys.exit(2)
    # 输出页序改为用户给定的顺序（build_pptx 固定按模板页序，这里做 zip 级重排：
    # 只重写 presentation.xml 的 sldIdLst 顺序，其余部件字节级原样拷贝。
    # 不要用 python-pptx 重排+重存——prune 后包内有同名部件对象，
    # 重存会产生重复 zip 条目导致 LibreOffice 拒载。
    if len(pairs) + len(sets) > 1:
        desired = [int(pg) for pg, _ in pairs] + [int(s.split(":", 1)[0]) for s in sets]
        desired = list(dict.fromkeys(desired))
        try:
            import zipfile
            zin = zipfile.ZipFile(build_tmp)
            xml = zin.read("ppt/presentation.xml").decode("utf-8")
            prels = zin.read("ppt/_rels/presentation.xml.rels").decode("utf-8")
            rid2tgt = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', prels))
            m = re.search(r"<p:sldIdLst>(.*?)</p:sldIdLst>", xml, re.S)
            entries = re.findall(r"<p:sldId [^>]*/>", m.group(1))
            bypage = {}
            for e in entries:
                rid = re.search(r'r:id="(rId\d+)"', e).group(1)
                npage = int(re.search(r"slide(\d+)\.xml", rid2tgt[rid]).group(1))
                bypage[npage] = e
            new_lst = "".join(bypage[p] for p in desired)
            new_xml = xml.replace(m.group(0), "<p:sldIdLst>" + new_lst + "</p:sldIdLst>")
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zo:
                for item in zin.infolist():
                    data = zin.read(item.filename)
                    if item.filename == "ppt/presentation.xml":
                        data = new_xml.encode("utf-8")
                    zo.writestr(item, data)
            zin.close()
            os.remove(build_tmp)
            print("✓ 页序已按指定顺序排列:", " → ".join(str(x) for x in desired))
        except Exception as e:
            if os.path.exists(build_tmp):
                shutil.move(build_tmp, out)
            print("（页序重排跳过：", e, "）")
    else:
        shutil.move(build_tmp, out)
    print("✓ 已生成:", os.path.abspath(out))
    # 出稿门禁 1：静态排版审计（error 一票否决；纯装饰出血已降 warning）。
    # rc=4 不得交付；--allow-layout-errors 为显式豁免。
    la = os.path.join(os.path.dirname(BUILD), "layout_audit.py")
    r = subprocess.run([sys.executable, la, os.path.abspath(out), "--level", "error"],
                       capture_output=True, text=True, encoding="utf-8")
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    if r.returncode == 1:
        if allow_layout:
            print("（--allow-layout-errors 豁免：静态排版 error 已知悉，仍交付）")
        else:
            print("✗ 静态排版门禁：存在 error（文字出界/占位符残留等），拒绝交付。"
                  "修文案或用 --allow-layout-errors 显式豁免。")
            sys.exit(4)
    # 出稿门禁 2：整套配色检查（铁律）。不通过 → 退出码 3，成品需重选/改版。
    chk = os.path.join(os.path.dirname(BUILD), "palette_check.py")
    r = subprocess.run([sys.executable, chk, os.path.abspath(out)],
                       capture_output=True, text=True, encoding="utf-8")
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    if r.returncode != 0:
        sys.exit(3)

def main(argv):
    if not argv:
        print(__doc__)
    elif argv[0] == "find":
        cmd_find(argv[1])
    elif argv[0] == "show":
        cmd_show(int(argv[1]))
    elif argv[0] == "components":
        cmd_components(int(argv[1]))
    elif argv[0] == "build":
        cmd_build(argv[1:])
    else:
        print(__doc__)

if __name__ == "__main__":
    main(sys.argv[1:])
