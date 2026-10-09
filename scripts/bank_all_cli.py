# -*- coding: utf-8 -*-
"""bank-all 模板调用工具
  python3 bank_all_cli.py find 关键词            # 按主题搜页（查 use_for/标题）
  python3 bank_all_cli.py show 页码              # 看某页版式与可编辑槽位
  python3 bank_all_cli.py build -o 输出.pptx 页码 "新标题" [页码 "标题" ...]
                                             [--set 页码:slot_id=文本 ...]
  不记 slot_id 时只给 页码+新标题 即可（自动命中该页 title_slot）。
"""
import sys, os, json, re, shutil
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
_skill_root = os.path.dirname(HERE)          # 技能根目录（scripts 的上一级）
_cands = [os.path.join(_skill_root, "templates", "bank-all"),
          os.path.join(HERE, "templates", "bank-all")]
_cands = [os.path.normpath(c) for c in _cands]
_cands.append("C:/Users/w/.zcode/skills/GordenPPTSkill/templates/bank-all")
_cands.append("C:/Users/w/.zcode/skills/neo_ppt_skills/templates/bank-all")
TPL = next((c for c in _cands if os.path.isfile(os.path.join(c, "detail.json"))), _cands[0])
_b_cands = [os.path.normpath(c) for c in (
    os.path.join(HERE, "build_pptx.py"),
    "C:/Users/w/.zcode/skills/GordenPPTSkill/scripts/build_pptx.py")]
BUILD = next((c for c in _b_cands if os.path.isfile(c)), _b_cands[0])

def load():
    return json.load(open(os.path.join(TPL, "detail.json"), encoding="utf-8"))

def page_title(d, pg):
    p = d["pages"][pg - 1]
    ts = next((x for x in p["text_slots"] if x["slot_id"] == p.get("title_slot_id")), None)
    return (ts or {}).get("current_text", "(无标题槽)")

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

def cmd_show(pg):
    d = load()
    p = d["pages"][pg - 1]
    print(f"第{pg}页  [{p['role']}]  密度:{p['text_density']}")
    print("use_for:", p["use_for"])
    ts = next((x for x in p["text_slots"] if x["slot_id"] == p.get("title_slot_id")), None)
    if ts:
        print(f"标题槽: {ts['slot_id']}  现:「{ts['current_text'][:36]}」  容量≈{ts['max_chars']}字")
    ed = [x for x in p["text_slots"] if x["editable"]][:14]
    print(f"可编辑槽位（前{len(ed)}个 / 共{len(p['text_slots'])}个）:")
    for x in ed:
        print(f"  {x['slot_id']}  <{x['role']}>  ≤{x['max_chars']}字  现:「{x['current_text'][:24]}」")
    more = [x for x in p["text_slots"] if x["editable"] and x["role"] == "页面标题"
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
    out = _confine("bank_all_out.pptx")
    build_tmp = _confine("bank_all_build_tmp.pptx")
    sets = []
    if "--set" in argv:
        while "--set" in argv:
            i = argv.index("--set"); sets.append(argv[i + 1]); del argv[i:i + 2]
    pairs = list(zip(argv[0::2], argv[1::2]))
    if not pairs and not sets:
        print("用法: build 页码 \"新标题\" ... [--set 页码:slot_id=文本 ...]  （输出固定为 bank_all_out.pptx，生成后自行改名）")
        return
    d = load()
    slides, edits = [], []
    for pg, title in pairs:
        pg = int(pg)
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
    spec = {"template_slug": "bank-all", "selected_slides": slides, "edits": edits}
    tmp = _confine("bank_all_edits.json")      # 规范化+限定目录后落盘，构建后保留供排查
    Path(tmp).write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    tpl_dir = os.path.realpath(TPL)
    if not tpl_dir.startswith(_skill_root):
        print("✗ 模板目录越界（须位于技能目录内）")
        return
    build_dir = os.path.dirname(BUILD)
    if build_dir not in sys.path:
        sys.path.insert(0, build_dir)
    import build_pptx                     # 固定名普通导入，无动态路径执行
    rc = build_pptx.build(os.path.join(tpl_dir, "template.pptx"), tmp, build_tmp,
                          detail=os.path.join(tpl_dir, "detail.json"))
    if rc != 0 or not os.path.isfile(build_tmp):
        print("✗ 构建未产出中间文件，中止")
        return
    # 输出页序改为用户给定的顺序（build_pptx 固定按模板页序，这里做 zip 级重排：
    # 只重写 presentation.xml 的 sldIdLst 顺序，其余部件字节级原样拷贝。
    # 不要用 python-pptx 重排+重存——Gorden prune 后包内有同名部件对象，
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

def main(argv):
    if not argv:
        print(__doc__)
    elif argv[0] == "find":
        cmd_find(argv[1])
    elif argv[0] == "show":
        cmd_show(int(argv[1]))
    elif argv[0] == "build":
        cmd_build(argv[1:])
    else:
        print(__doc__)

if __name__ == "__main__":
    main(sys.argv[1:])
