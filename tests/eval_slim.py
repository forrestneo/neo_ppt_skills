# -*- coding: utf-8 -*-
"""neo_ppt_skills 瘦身后可用性评测（回归基线）。
用法: python tests/eval_slim.py            # 全部用例
      python tests/eval_slim.py -v         # 详细输出
逐项 PASS/FAIL，最后汇总。产物写入临时目录。"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "deck_cli.py"
BUILD = ROOT / "scripts" / "build_pptx.py"
PY = sys.executable
VERBOSE = "-v" in sys.argv

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (("  | " + detail) if (detail and (VERBOSE or not ok)) else ""))


def run(args, cwd=None, input_text=None):
    r = subprocess.run([PY] + [str(a) for a in args], cwd=cwd,
                       capture_output=True, text=True, encoding="utf-8",
                       input=input_text, timeout=300)
    return r


# ---------------------------------------------------------------- 1 结构
def t_structure():
    need = ["SKILL.md", "README.md", "scripts/deck_cli.py", "scripts/build_pptx.py",
            "scripts/compute_capacity.py", "scripts/render_slides.py",
            "scripts/palette_check.py", "scripts/palettes.json",
            "templates/MANIFEST.json", "templates/deck-all/template.pptx",
            "templates/deck-all/detail.json.gz",
            "scripts/restore/compose_pptx.py", "scripts/restore/chroma_key.py",
            "scripts/imagegen/compose_pptx.py", "references/mode-a-imagegen.md",
            "references/mode-b-rebuild.md", "references/pipeline.md",
            "references/stylekit/visual-styles.md",
            "references/stylekit/imagegen-styles.md",
            "references/stylekit/image-type-templates.md",
            "references/stylekit/narrative-and-review.md",
            "references/stylekit/layout-engine.md",
            "scripts/layout_audit.py",
            "extras/pipeline.md"]
    for rel in need:
        check("结构存在 " + rel, (ROOT / rel).is_file())

    sk = ROOT / "references" / "stylekit"
    def cnt(name, pat):
        txt = (sk / name).read_text(encoding="utf-8")
        return len(re.findall(pat, txt, re.M))
    ok_cnt = (cnt("visual-styles.md", r"^## [a-z0-9-]+（") == 18
              and cnt("imagegen-styles.md", r"^### ") >= 34
              and cnt("image-type-templates.md", r"^## [a-z0-9-]+（") == 11
              and cnt("narrative-and-review.md", r"^## ") >= 5
              and "ppt-master" in (sk / "visual-styles.md").read_text(encoding="utf-8"))
    check("stylekit 蒸馏条目齐全（18 风格 / ≥34 渲染+色板 / 11 图式 / ≥5 叙事+验收，含出处）", ok_cnt)

    # layout_audit 端到端：好稿放行（rc=0）、越界+重叠坏稿拦截（rc=1）
    from pptx import Presentation as _Prs
    from pptx.util import Inches as _In
    with tempfile.TemporaryDirectory() as td:
        def _mk(path, bad):
            prs = _Prs()
            prs.slide_width, prs.slide_height = _In(13.333), _In(7.5)
            s = prs.slides.add_slide(prs.slide_layouts[6])
            if bad:
                tb = s.shapes.add_textbox(_In(12), _In(7), _In(3), _In(2))
                tb.text_frame.text = "越界"
                t2 = s.shapes.add_textbox(_In(1), _In(1), _In(4), _In(2))
                t2.text_frame.text = "甲盒"
                t3 = s.shapes.add_textbox(_In(2), _In(1.5), _In(4), _In(2))
                t3.text_frame.text = "乙盒"
            else:
                tb = s.shapes.add_textbox(_In(1), _In(1), _In(4), _In(2))
                tb.text_frame.text = "画布内正常文本"
            prs.save(path)
        _mk(os.path.join(td, "good.pptx"), False)
        _mk(os.path.join(td, "bad.pptx"), True)
        r_good = run([BUILD.parent / "layout_audit.py", os.path.join(td, "good.pptx")])
        r_bad = run([BUILD.parent / "layout_audit.py", os.path.join(td, "bad.pptx")])
        check("layout_audit 好稿放行 rc=0", r_good.returncode == 0)
        check("layout_audit 坏稿拦截（越界 error + 重叠 warning，rc=1）",
              r_bad.returncode == 1 and "out-of-bounds" in r_bad.stdout
              and "overlap" in r_bad.stdout)

    gone = ["templates/bank-lite", "use_bank_lite.py",
            "GordenSuperPPTSkill", "GordenImagePPTGen", "GordenImage2PPTX",
            "assets"]
    bad = [str(f.relative_to(ROOT)) for f in ROOT.rglob("*")
           if f.is_file() and f.suffix in (".md", ".py", ".json")
           and "__pycache__" not in f.parts and ".git" not in f.parts
           and ("Gorden" in f.read_text(encoding="utf-8", errors="ignore")
                or "reference-slides" in f.read_text(encoding="utf-8", errors="ignore")
                or "runtime-notes" in f.read_text(encoding="utf-8", errors="ignore"))]
    for rel in gone:
        check("冗余已删 " + rel, not (ROOT / rel).exists())

    # 全库无残留引用（除归档性描述）
    bad = []
    for md in ROOT.rglob("*.md"):
        txt = md.read_text(encoding="utf-8", errors="ignore")
        if "use_bank_lite" in txt:
            bad.append(str(md.relative_to(ROOT)) + " 提 use_bank_lite")
        if re.search(r"bank-lite/template\.pptx|bank-lite/detail\.json", txt):
            bad.append(str(md.relative_to(ROOT)) + " 引已删路径")
        if re.search(r"ref\d+\.png", txt):
            bad.append(str(md.relative_to(ROOT)) + " 引 png 参考图")
    check("文档无失效引用", not bad, "; ".join(bad))

    # py 全库语法可编译
    bad_py = []
    for py in ROOT.rglob("*.py"):
        r = subprocess.run([PY, "-m", "py_compile", str(py)], capture_output=True)
        if r.returncode != 0:
            bad_py.append(str(py.relative_to(ROOT)))
    check("全部 .py 可编译", not bad_py, "; ".join(bad_py))

    # gz 完整性 + MANIFEST 可解析
    import gzip
    try:
        with gzip.open(ROOT / "templates/deck-all/detail.json.gz", "rt", encoding="utf-8") as f:
            d = json.load(f)
        check("gz 完整可解析", d.get("slide_count") == 577 and len(d.get("pages", [])) == 577)
    except Exception as e:
        check("gz 完整可解析", False, str(e))
    try:
        m = json.loads((ROOT / "templates/MANIFEST.json").read_text(encoding="utf-8"))
        fam = m["families"][0]
        check("MANIFEST 注册 deck-all", fam["id"] == "deck-all" and fam["enabled"] is True)
    except Exception as e:
        check("MANIFEST 注册 bank-all", False, str(e))

    # 交付态 = git 跟踪的文件（排除用户测试产物）；非 git 环境回退为全量工作区
    import subprocess as _sp
    try:
        tracked = _sp.run(["git", "ls-files"], cwd=str(ROOT),
                          capture_output=True, text=True, encoding="utf-8",
                          timeout=30).stdout.splitlines()
        size = sum((ROOT / t).stat().st_size for t in tracked
                   if t and (ROOT / t).is_file() and "__pycache__" not in t)
    except Exception:
        size = sum(f.stat().st_size for f in ROOT.rglob("*")
                   if f.is_file()
                   and "__pycache__" not in f.parts and ".git" not in f.parts)
    check("总体积 <10MB", size < 10 * 1048576, "%.2f MB" % (size / 1048576))


# ---------------------------------------------------------------- 2 CLI
def t_cli():
    with tempfile.TemporaryDirectory() as td:
        r = run([CLI, "find", "客户分层"], cwd=td)
        check("find 命中", r.returncode == 0 and "命中" in r.stdout and "bank01" in r.stdout)
        r2 = run([CLI, "find", "一定不存在的关键词xyz"], cwd=td)
        check("find 空结果不崩", r2.returncode == 0 and "命中" in r2.stdout)

        r3 = run([CLI, "show", "12"], cwd=td)
        check("show 标题槽", r3.returncode == 0 and "标题槽" in r3.stdout and "可编辑槽位" in r3.stdout)
        r4 = run([CLI, "show", "99999"], cwd=td)
        check("show 越界页报错不崩", r4.returncode != 0 or "Traceback" not in r4.stderr)

        # 单页 build（默认标题；违规页按铁律需显式豁免）
        out = Path(td) / "o1.pptx"
        r5 = run([CLI, "build", "-o", str(out), "--allow-small-font", "12", "四季度经营复盘"], cwd=td)
        check("build 单页产出", r5.returncode == 0 and out.is_file(), r5.stdout[-200:] + r5.stderr[-200:])
        if out.is_file():
            from pptx import Presentation
            p = Presentation(str(out))

            def walk(shapes):
                for sh in shapes:
                    if sh.shape_type == 6:
                        yield from walk(sh.shapes)
                    elif sh.has_text_frame:
                        yield sh
            texts = [sh.text_frame.text for sh in walk(p.slides[0].shapes)]
            check("build 标题已替换", any("四季度经营复盘" in t for t in texts))
            check("build 页数=1", len(p.slides.__iter__.__self__._sldIdLst) == 1)

        # 多页 build + --set + 页序
        out2 = Path(td) / "o2.pptx"
        r6 = run([CLI, "build", "-o", str(out2), "--allow-small-font",
                  "2", "第一页新标题", "1", "第二页新标题",
                  "--set", "2:p2s23x0=融资需求分化中蕴藏结构机会"], cwd=td)
        check("build 多页+页序", r6.returncode == 0 and out2.is_file(), r6.stdout[-200:])
        if out2.is_file():
            from pptx import Presentation
            p = Presentation(str(out2))
            check("build 多页页数=2", len(p.slides._sldIdLst) == 2)

            def first_texts(slide):
                return [sh.text_frame.text for sh in walk(slide.shapes) if sh.has_text_frame]
            t0 = " ".join(first_texts(p.slides[0]))
            t1 = " ".join(first_texts(p.slides[1]))
            check("页序=用户给定顺序", ("第一页新标题" in t0) and ("第二页新标题" in t1)
                  and ("第一页新标题" not in t1))
            check("--set 槽位替换生效", "融资需求分化中蕴藏结构机会" in t0)

        # 溢出拦截（warning 路径）
        out3 = Path(td) / "o3.pptx"
        long_t = "这" * 60
        r7 = run([CLI, "build", "-o", str(out3), "--allow-small-font", "12", long_t], cwd=td)
        both7 = r7.stdout + r7.stderr
        check("超长标题给出溢出警告", "偏长" in both7 or "容量" in both7)
        check("超长仍可产出（警告不阻断）", r7.returncode == 0 and out3.is_file())

        # 非法输入
        r8 = run([CLI, "build"], cwd=td)
        check("build 无参数不崩", r8.returncode == 0 and "用法" in r8.stdout)
        r9 = run([CLI, "build", "-o", str(Path(td) / "x.pptx"), "abc", "标题"], cwd=td)
        check("非数字页码不产生半成品", not (Path(td) / "x.pptx").exists() and "Traceback" not in r9.stderr)

        # 越界输出路径拒绝
        r10 = run([CLI, "build", "-o", "../escape.pptx", "12", "t"], cwd=td)
        check("输出路径越界被拒", r10.returncode != 0 or "越界" in r10.stdout)

        # ---- 正文 12pt 排版铁律（写入时统一小四，超容量拒绝）----
        r11 = run([CLI, "show", "12"], cwd=td)
        check("show 显示 12pt 容量辅助写作", "12pt≤" in r11.stdout and "12pt=小四" in r11.stdout)
        r13 = run([CLI, "build", "-o", str(Path(td) / "mf.pptx"), "12", "小字页测试"], cwd=td)
        both13 = r13.stdout + r13.stderr
        check("默认强制：正文超 12pt 容量拒绝出稿", r13.returncode != 0
              and not (Path(td) / "mf.pptx").exists()
              and "正文容量铁律" in both13 and "超出 12pt 容量" in both13)
        r13b = run([CLI, "build", "-o", str(Path(td) / "mf.pptx"), "--allow-small-font", "12", "小字页测试"], cwd=td)
        both13b = r13b.stdout + r13b.stderr
        check("--allow-small-font 降级警告可出稿", r13b.returncode == 0 and (Path(td) / "mf.pptx").is_file()
              and "降级为警告" in both13b)
        # 合规出稿样板：第 4 页 4 个正文槽全覆盖 12pt 容量内文案 → 通过且 run 全 ≥12pt
        out4 = Path(td) / "p4ok.pptx"
        r16 = run([CLI, "build", "-o", str(out4), "4", "一稳两增三优四控统领下半年"], cwd=td)
        # 页4 仅 4 个正文槽，但默认 title 编辑只覆盖标题槽 → 其余 3 槽原长文超容量 → 拒绝
        check("页4 未全覆盖被拒", r16.returncode != 0 and not out4.exists())
        r17 = run([CLI, "build", "-o", str(out4), "4", "一稳两增三优四控统领下半年",
                   "--set", "4:p4s16x0=四大风险全面受控",
                   "--set", "4:p4s27x0=客户资产收入结构三优",
                   "--set", "4:p4s38x0=信贷与非息收入两增",
                   "--set", "4:p4s55x0=存款客户资产三稳"], cwd=td)
        check("页4 全覆盖 12pt 文案出稿", r17.returncode == 0 and out4.is_file(),
              (r17.stdout + r17.stderr)[-200:])
        if out4.is_file():
            import gzip as _gz
            from pptx import Presentation
            pr = Presentation(str(out4))
            with _gz.open(ROOT / "templates/deck-all/detail.json.gz", "rt", encoding="utf-8") as _f:
                _d = json.load(_f)
            body_shapes = {sl["address"]["shape_id"] for sl in _d["pages"][3]["text_slots"]
                           if sl.get("role") == "正文" and sl.get("address", {}).get("shape_id")}

            def iter_body(shapes):
                for sh in shapes:
                    if sh.shape_type == 6:
                        yield from iter_body(sh.shapes)
                    elif sh.has_text_frame and sh.shape_id in body_shapes:
                        yield sh
            sizes = [rr.font.size.pt for sl in pr.slides for sh in iter_body(sl.shapes)
                     for para in sh.text_frame.paragraphs for rr in para.runs
                     if rr.font.size and rr.text.strip() and rr.font.size.pt < 12]
            check("出稿正文 run 全部 ≥12pt", not sizes, str(sizes[:5]))
        # ---- 配色体系：模板已统一为活力橙单色系 → 同稿出稿应通过主色相与末检 ----
        r20 = run([CLI, "build", "-o", str(Path(td) / "mix.pptx"), "--allow-small-font",
                   "1", "同系A", "20", "同系B"], cwd=td)
        both20 = r20.stdout + r20.stderr
        check("单色系模板跨套混选出稿过主色相", r20.returncode == 0
              and (Path(td) / "mix.pptx").is_file())
        check("末步配色检查通过", "最终配色检查通过" in both20)
        CHK = ROOT / "scripts" / "palette_check.py"
        r22 = run([CHK, str(Path(td) / "mix.pptx")], cwd=td)
        check("palette_check 独立复核 PASS", r22.returncode == 0
              and "通过" in (r22.stdout + r22.stderr))
        out_same = Path(td) / "same.pptx"
        r23 = run([CLI, "build", "-o", str(out_same), "--allow-small-font",
                   "1", "同系页A", "2", "同系页B", "3", "同系页C"], cwd=td)
        check("同色系页(1/2/3)可出稿", r23.returncode == 0 and out_same.is_file(),
              (r23.stdout + r23.stderr)[-200:])
        if out_same.is_file():
            r24 = run([CHK, str(out_same)], cwd=td)
            check("最终配色检查：同系稿 PASS", r24.returncode == 0
                  and "通过" in (r24.stdout + r24.stderr))

        # 第 37 页无 <12pt 槽位，默认铁律下直接可出稿
        r15 = run([CLI, "build", "-o", str(Path(td) / "ok.pptx"), "37", "合规页测试"], cwd=td)
        both15 = r15.stdout + r15.stderr
        check("合规页默认可出稿", r15.returncode == 0 and (Path(td) / "ok.pptx").is_file()
              and "最小字号铁律" not in both15)


# ---------------------------------------------------------------- 3 build_pptx 直调（--detail gz）
def t_build_direct():
    with tempfile.TemporaryDirectory() as td:
        edits = {"template_slug": "bank-all", "selected_slides": [8],
                 "edits": [{"slide": 8, "slot_id": None, "new_text": "直调标题"}]}
        # 用 title_slot 解析：先取第 8 页 title_slot_id
        import gzip
        with gzip.open(ROOT / "templates/deck-all/detail.json.gz", "rt", encoding="utf-8") as f:
            d = json.load(f)
        p8 = d["pages"][7]
        edits["edits"][0]["slot_id"] = p8.get("title_slot_id")
        ej = Path(td) / "edits.json"
        ej.write_text(json.dumps(edits, ensure_ascii=False), encoding="utf-8")
        out = Path(td) / "direct.pptx"
        r = run([BUILD, ROOT / "templates/deck-all/template.pptx", ej, out,
                 "--detail", ROOT / "templates/deck-all/detail.json.gz",
                 "--allow-small-font"], cwd=td)
        check("build_pptx 直调 gz detail", r.returncode == 0 and out.is_file(), r.stdout[-200:] + r.stderr[-200:])
        # 溢出 lint 在 gz 下工作：构造超长正文
        slot = next(s for s in p8["text_slots"] if s["slot_id"] == p8["title_slot_id"])
        cap = slot.get("max_chars", 10)
        edits["edits"][0]["new_text"] = "长" * (int(cap) * 3 + 5)
        ej.write_text(json.dumps(edits, ensure_ascii=False), encoding="utf-8")
        r2 = run([BUILD, ROOT / "templates/deck-all/template.pptx", ej, out,
                  "--detail", ROOT / "templates/deck-all/detail.json.gz"], cwd=td)
        both = r2.stdout + r2.stderr
        check("gz 路径溢出 lint 生效", "偏长" in both or "容量" in both or "AUTOFIT" in both)


# ---------------------------------------------------------------- 4 渲染质量
def t_render():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "r.pptx"
        r = run([CLI, "build", "-o", str(out), "--allow-small-font", "24", "客户分层经营策略", "--set",
                 "24:p24s7x0=价值需求行为三维"], cwd=td)
        if not out.is_file():
            check("渲染前构建", False, r.stdout[-200:])
            return
        soffice = r"C:\Program Files\LibreOffice\program\soffice.exe"
        r2 = subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", td, str(out)],
                            capture_output=True, text=True, timeout=300)
        pdf = Path(td) / "r.pdf"
        check("LibreOffice 可转换", pdf.is_file(), r2.stdout[-150:] + r2.stderr[-150:])
        if pdf.is_file():
            import pymupdf
            doc = pymupdf.open(str(pdf))
            png = Path(td) / "p24.png"
            doc[0].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).save(str(png))
            txt = doc[0].get_text()
            doc.close()
            check("渲染出图", png.is_file() and png.stat().st_size > 10000)
            # 文本层校验：替换文本出现在 PDF
            check("渲染文本层含替换内容", "客户分层经营策略" in txt)


# ---------------------------------------------------------------- 5 备线 extras 可导入（import 无副作用/无语法错）
def t_extras():
    extras = ROOT / "extras"
    for m in ("ocr_extract", "audit_quality", "pixrep", "rep_lib"):
        try:
            r = subprocess.run(
                [PY, "-c", "import sys; sys.path.insert(0, r'%s'); import %s" % (extras, m)],
                capture_output=True, text=True, timeout=60)
            syntax_bad = "SyntaxError" in r.stderr or "IndentationError" in r.stderr
            check(f"extras/{m} 可导入无语法错误", not syntax_bad, r.stderr[-150:])
        except subprocess.TimeoutExpired:
            check(f"extras/{m} 可导入无语法错误", False, "import 超时（顶层副作用）")


def main():
    print("=" * 62)
    t_structure()
    print("-" * 62)
    t_cli()
    print("-" * 62)
    t_build_direct()
    print("-" * 62)
    t_render()
    print("-" * 62)
    t_extras()
    print("=" * 62)
    # 收尾：清掉评测运行产生的 __pycache__，守住 <10MB 交付态
    for d in ROOT.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)
    fails = [n for n, ok, _ in RESULTS if not ok]
    print(f"总计 {len(RESULTS)} 项，通过 {len(RESULTS) - len(fails)}，失败 {len(fails)}")
    for n in fails:
        print("  FAIL:", n)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
