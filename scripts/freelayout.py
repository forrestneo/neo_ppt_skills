# -*- coding: utf-8 -*-
"""freelayout — 自由排版引擎：版式=代码函数，AI 只填内容槽。

架构蒸馏自 luobo-ppt / dsh-ppt-master（版式=代码、模板=数据，AI 永不写坐标），
几何数字取自 references/stylekit/layout-library.md，质量特性取自各家：
  - 字号沿 TYPE_SCALE 阶梯吸附 + 孤字防护 + 9pt 地板（luobo / dsh-ppt-master）
  - 稀疏页字号补偿、卡片不留空肚子、数值列自动右对齐（dsh-ppt-master）
  - takeaway 胶囊、role 色板、派生色对比度兜底（luobo Style 类）
  - 层级差 ≥1.5×、版心 ≤70%、装饰 ≤3 件不压字（overflow-and-density.md）

deck.json 格式（slides 里每页一个 type + 内容字段，见 build 函数 docstring）:
  {"meta": {"theme": "orange-vitality", "footer": "战略部"},
   "slides": [{"type": "cover", "title": "...", "subtitle": "...", "kicker": "...",
               "meta": "2026 Q3 · 战略部", "dark": false}, ...]}

用法:
  python scripts/freelayout.py deck.json -o out.pptx [--theme orange-vitality]
出稿自动过 layout_audit --level error，有 error 时退出码 1。
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
W, H = 13.333, 7.5          # 16:9 英寸
MX = 0.7                    # 左右页边距
CW = W - 2 * MX             # 内容宽 11.933
CONTENT_TOP = 1.72          # 页头下内容起点
CONTENT_BOTTOM = 6.85       # 内容底界（版心 ≤70%+ 的留白守线）
TITLE_MAX = 34.0            # 页题基准字号
BODY = 12.0                 # 正文章（小四铁律同源）
TYPE_SCALE = [9, 10.5, 12, 14, 16, 18, 20, 24, 28, 32, 36, 44, 54, 66, 80, 96, 120, 150]
_IN = 914400


# ---------------------------------------------------------------- 颜色工具
def _rgb(hexc) -> RGBColor:
    hexc = (hexc or "000000").lstrip("#")
    if len(hexc) == 3:
        hexc = "".join(c * 2 for c in hexc)
    return RGBColor(int(hexc[0:2], 16), int(hexc[2:4], 16), int(hexc[4:6], 16))


def _mix(c1: RGBColor, c2: RGBColor, t: float) -> RGBColor:
    return RGBColor(*(int(a + (b - a) * t) for a, b in zip(c1, c2)))


def _lum(c: RGBColor) -> float:
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def _contrast(a: RGBColor, b: RGBColor) -> float:
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _dark_ink(bg: RGBColor) -> RGBColor:
    """给底色配可读墨色：亮底近黑、深底近白。"""
    return RGBColor(0x26, 0x26, 0x26) if _lum(bg) > 0.35 else RGBColor(0xF5, 0xF5, 0xF5)


def _sub_ink(bg: RGBColor, ink: RGBColor, start: float = 0.30,
             min_contrast: float = 4.5) -> RGBColor:
    """深底页次级文字：从 start 混合比起步，对比度不达标逐步提亮。"""
    c = _mix(bg, ink, start)
    t = start
    while _contrast(c, bg) < min_contrast and t < 0.85:
        t += 0.07
        c = _mix(bg, ink, t)
    return c


class Theme:
    """主题角色派生：色板 → 版面可用的语义色。派生色对比度不达标自动加深。"""

    def __init__(self, theme_id: str | None, custom: list[str] | None = None):
        pal = {}
        ppath = os.path.join(HERE, "palettes.json")
        if os.path.isfile(ppath):
            data = json.load(open(ppath, encoding="utf-8"))
            themes = {t["id"]: t for t in data.get("themes", [])}
            tid = theme_id or data.get("default_theme")
            pal = themes.get(tid) or themes.get(data.get("default_theme"))
            self.id = pal["id"] if pal else (theme_id or "custom")
        else:
            self.id = theme_id or "custom"
        if custom:
            self.primary = _rgb(custom[0])
            self.secondary = _rgb(custom[1]) if len(custom) > 1 else _mix(self.primary, _rgb("000000"), 0.25)
            self.accent = _rgb(custom[2]) if len(custom) > 2 else self.secondary
        elif pal:
            self.primary = _rgb(pal["primary"])
            self.secondary = _rgb(pal.get("secondary", pal["primary"]))
            self.accent = _rgb(pal.get("accents", [pal["primary"]])[0])
        else:
            self.primary = _rgb("C4531A")
            self.secondary = _mix(self.primary, _rgb("000000"), 0.25)
            self.accent = self.secondary
        self.bg = _rgb("FFFFFF")
        self.surface = _mix(self.bg, self.primary, 0.05)
        self.tint = _mix(self.bg, self.primary, 0.12)
        self.deep = _mix(self.primary, _rgb("000000"), 0.30)
        self.text = _dark_ink(self.bg)
        self.muted = _mix(self.text, self.bg, 0.42)
        while _contrast(self.muted, self.bg) < 4.5:      # 对比度兜底（luobo Style 经验）
            self.muted = _mix(self.muted, self.text, 0.12)
        self.on_primary = _dark_ink(self.primary)
        self.strong = self.primary if _contrast(self.primary, self.bg) >= 3.0 \
            else _mix(self.primary, _rgb("000000"), 0.35)
        self.good = _rgb("2E9E6B")
        self.bad = _rgb("C62828")
        self.line = _mix(self.bg, self.muted, 0.35)

    def ramp(self, n: int) -> list[RGBColor]:
        """n 档主色渐层：首档实心 primary，向后 tint 递减（dsh-ppt-master 金字塔法）。"""
        out = []
        for i in range(n):
            t = 0.0 if n == 1 else i / (n - 1) * 0.72
            out.append(_mix(self.primary, self.bg, t) if i else self.primary)
        return out


# ---------------------------------------------------------------- 测量与字号
def units(text: str) -> float:
    return sum(1.0 if ord(c) > 0x2E80 else 0.55 for c in text or "")


def est_lines(text: str, pt: float, width_in: float) -> int:
    avail = max(width_in, 0.1) * _IN
    need = units(text) * pt * 12700
    return max(1, math.ceil(need / avail))


def fit_size(text: str, width_in: float, height_in: float, base: float,
             floor: float = 9.0, bold: bool = False, lh: float = 1.3,
             max_lines: int = 99) -> float:
    """字号沿 TYPE_SCALE 回落至装得下；末行孤字再降一档（孤字防护）。"""
    size = min(base, max(TYPE_SCALE, key=lambda s: s <= base) if base in TYPE_SCALE else base)
    candidates = [s for s in TYPE_SCALE if floor <= s <= base] or [floor]
    picked = candidates[-1]
    for s in candidates:
        lines = est_lines(text, s, width_in * (0.92 if bold else 1.0))
        if lines * s * lh / 72 <= height_in and lines <= max_lines:
            picked = s
            if lines >= 2:                            # 孤字防护：末行只剩 ~1 字再降一档
                last_w = units(text) * s - (lines - 1) * width_in * 72 / s * s / 72
                usable = width_in * 72
                if usable - (lines - 1) * usable / lines < 1.1 * s and s != candidates[0]:
                    picked = candidates[max(0, candidates.index(s) - 1)]
            break
    return picked


# ---------------------------------------------------------------- 绘制原语
class Deck:
    def __init__(self, theme: Theme, footer: str = ""):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Emu(int(W * _IN)), Emu(int(H * _IN))
        self.blank = self.prs.slide_layouts[6]
        self.theme = theme
        self.footer_text = footer
        self.total = 0
        self.n = 0

    # -- 基础件 ------------------------------------------------------------
    def _slide(self):
        self.n += 1
        return self.prs.slides.add_slide(self.blank)

    def _rect(self, slide, x, y, w, h, fill=None, line=None, round_=False, radius=0.08,
              shadow=False):
        shp = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE if round_ else MSO_SHAPE.RECTANGLE,
            Emu(int(x * _IN)), Emu(int(y * _IN)), Emu(int(w * _IN)), Emu(int(h * _IN)))
        if round_:
            try:
                shp.adjustments[0] = radius
            except Exception:
                pass
        if fill is None:
            shp.fill.background()
        else:
            shp.fill.solid()
            shp.fill.fore_color.rgb = fill
        if line is None:
            shp.line.fill.background()
        else:
            shp.line.color.rgb = line
            shp.line.width = Pt(0.75)
        shp.shadow.inherit = False
        return shp

    def _oval(self, slide, x, y, d, fill=None, line=None):
        shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, Emu(int(x * _IN)), Emu(int(y * _IN)),
                                     Emu(int(d * _IN)), Emu(int(d * _IN)))
        if fill is None:
            shp.fill.background()
        else:
            shp.fill.solid()
            shp.fill.fore_color.rgb = fill
        if line is None:
            shp.line.fill.background()
        else:
            shp.line.color.rgb = line
            shp.line.width = Pt(1)
        shp.shadow.inherit = False
        return shp

    def _text(self, slide, x, y, w, h, text, pt, color=None, bold=False,
              align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, lh=1.3, font=None,
              space_after=0.0):
        """文字盒：自动 fit_size（可关），中文 latin+ea 双写。"""
        tb = slide.shapes.add_textbox(Emu(int(x * _IN)), Emu(int(y * _IN)),
                                      Emu(int(w * _IN)), Emu(int(h * _IN)))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        lines = str(text).split("\n")
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            p.line_spacing = lh
            if space_after and i < len(lines) - 1:
                p.space_after = Pt(space_after)
            r = p.add_run()
            r.text = ln
            r.font.size = Pt(pt)
            r.font.bold = bold
            r.font.color.rgb = color or self.theme.text
            name = font or "Microsoft YaHei"
            r.font.name = name
            # 中文字形走 ea 槽：latin 已由 font.name 写入，ea 手动补（在 a:latin 之后）
            rPr = r._r.get_or_add_rPr()
            qn = __import__("pptx.oxml.ns", fromlist=["qn"]).qn
            ea = rPr.find(qn("a:ea"))
            if ea is None:
                ea = rPr.makeelement(qn("a:ea"), {})
                latin = rPr.find(qn("a:latin"))
                if latin is not None:
                    latin.addnext(ea)
                else:
                    rPr.append(ea)
            ea.set("typeface", "微软雅黑" if name == "Microsoft YaHei" else name)
        return tb

    def _auto_text(self, slide, x, y, w, h, text, base, color=None, bold=False,
                   align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, lh=1.3,
                   floor=9.0, max_lines=99):
        pt = fit_size(str(text), w, h, base, floor=floor, bold=bold, lh=lh,
                      max_lines=max_lines)
        return self._text(slide, x, y, w, h, text, pt, color=color, bold=bold,
                          align=align, anchor=anchor, lh=lh), pt

    # -- 版面公共件 ----------------------------------------------------------
    def header(self, slide, title, kicker=None, sub=None):
        t = self.theme
        y = 0.40
        if kicker:
            self._text(slide, MX, y, CW, 0.28, kicker, 11, color=t.primary, bold=True)
            y += 0.32
        _, pt = self._auto_text(slide, MX, y, CW, 0.66, title, TITLE_MAX, bold=True,
                                max_lines=1, floor=16)
        y += max(0.62, pt / 72 * 1.25) + 0.06
        self._rect(slide, MX, y, 0.9, 0.045, fill=t.primary)
        y += 0.045
        if sub:
            self._text(slide, MX, y + 0.10, CW, 0.3, sub, 12, color=t.muted)
            y += 0.40
        return max(CONTENT_TOP, y + 0.30)

    def footer(self, slide):
        if self.footer_text:
            self._text(slide, MX, 7.08, 8.0, 0.26, self.footer_text, 9, color=self.theme.muted)
        self._text(slide, W - MX - 1.2, 7.08, 1.2, 0.26,
                   f"{self.n:02d} / {self.total:02d}", 9,
                   color=self.theme.muted, align=PP_ALIGN.RIGHT)

    def takeaway(self, slide, text, y=None, w=None):
        """底部结论胶囊（tint 底 + primary 竖标 + 文字）。"""
        t = self.theme
        y = CONTENT_BOTTOM - 0.52 if y is None else y
        w = (w or CW)
        self._rect(slide, MX, y, w, 0.52, fill=t.tint, round_=True, radius=0.5)
        self._rect(slide, MX + 0.16, y + 0.14, 0.06, 0.24, fill=t.primary)
        self._auto_text(slide, MX + 0.36, y + 0.06, w - 0.55, 0.40, text, 13,
                        color=t.strong, bold=True, anchor=MSO_ANCHOR.MIDDLE)

    def card(self, slide, x, y, w, h, title, text=None, accent_top=True, num=None,
             fill=None, title_pt=15.0, text_pt=11.5):
        """圆角卡：surface 底 + 顶部 accent 细条 + 编号 + 标题 + 说明。

        内容少时整块（编号+标题+正文）在卡内垂直居中，不留空肚子。
        """
        t = self.theme
        self._rect(slide, x, y, w, h, fill=fill or t.surface, round_=True, radius=0.06)
        if accent_top:
            self._rect(slide, x + 0.18, y, min(0.6, w * 0.3), 0.05, fill=t.primary)
        tx = x + 0.2
        ty = y + 0.16
        avail_h = h - 0.16 - 0.14
        if text:
            tlines = est_lines(text, text_pt, w - 0.4)
            block_h = 0.38 + min(tlines, max(1, int(avail_h / (text_pt * 1.35 / 72)))) \
                * text_pt * 1.35 / 72
            ty += max(0.0, (avail_h - block_h) / 2)
        if num:
            d = 0.34
            self._oval(slide, tx, ty + 0.02, d, fill=t.primary)
            self._text(slide, tx, ty + 0.055, d, 0.26, str(num), 11,
                       color=t.on_primary, bold=True, align=PP_ALIGN.CENTER)
            tx += d + 0.14
            ty -= 0.02
        if text:
            self._auto_text(slide, tx, ty, w - (tx - x) - 0.2, 0.34, title,
                            title_pt, bold=True, max_lines=1, floor=10)
            self._auto_text(slide, x + 0.2, ty + 0.38, w - 0.4,
                            max(0.4, avail_h - (ty - y) - 0.38), text, text_pt,
                            color=t.muted)
        else:
            self._auto_text(slide, tx, ty, w - (tx - x) - 0.2, avail_h, title,
                            title_pt, bold=True, anchor=MSO_ANCHOR.MIDDLE)


# ---------------------------------------------------------------- 版式函数
def v_cover(d: Deck, slide, s):
    t = d.theme
    if s.get("dark"):
        bg = t.deep
        ink, sub_ink = _dark_ink(bg), _mix(_dark_ink(bg), bg, 0.30)
        d._rect(slide, 0, 0, W, H, fill=bg)
    else:
        ink, sub_ink = t.text, t.muted
        d._rect(slide, 0, 0, W, H, fill=t.bg)
        # 同心圆装饰组（≤3 件，右侧，primary 低饱和）
        for i, dd in enumerate((3.6, 2.7, 1.8)):
            d._oval(slide, W - MX - dd - 0.6, 3.75 - dd / 2, dd,
                    fill=None, line=_mix(t.bg, t.primary, 0.18 + i * 0.06))
        d._oval(slide, W - MX - 1.35, 3.4, 0.7, fill=_mix(t.bg, t.primary, 0.22))
        d._rect(slide, 0, H - 0.14, W, 0.14, fill=t.primary)
    x = MX + 0.2
    y = 1.75
    if s.get("kicker"):
        kw = max(1.3, units(s["kicker"]) * 0.16)
        d._rect(slide, x, y, kw, 0.4, fill=t.tint if not s.get("dark") else _mix(bg, _dark_ink(bg), 0.12),
                round_=True, radius=0.5)
        d._text(slide, x, y + 0.075, kw, 0.28, s["kicker"], 12,
                color=t.primary if not s.get("dark") else _dark_ink(bg), bold=True,
                align=PP_ALIGN.CENTER)
        y += 0.66
    d._auto_text(slide, x, y, 8.6, 2.1, s["title"], 48, color=ink, bold=True,
                 lh=1.12, floor=26)
    lines = est_lines(s["title"], 48, 8.6)
    y += lines * 48 * 1.12 / 72 + 0.22
    d._rect(slide, x, y, 1.3, 0.06, fill=t.primary)
    y += 0.32
    if s.get("subtitle"):
        d._auto_text(slide, x, y, 7.9, 0.9, s["subtitle"], 16, color=sub_ink, lh=1.45)
        y += 0.6
    if s.get("meta"):
        d._text(slide, x, H - 1.05, 8.0, 0.3, s["meta"], 11, color=sub_ink)


def v_toc(d: Deck, slide, s):
    t = d.theme
    if s.get("kicker"):
        d._text(slide, MX, 0.40, CW, 0.28, s["kicker"], 11, color=t.primary, bold=True)
    d._rect(slide, MX, 0.86, 0.9, 0.045, fill=t.primary)   # 简化头：左侧大字是主角，不画页题
    d._text(slide, MX, 2.1, 3.0, 1.0, s.get("big", "目录"), 32, color=t.strong, bold=True)
    d._text(slide, MX, 3.0, 3.0, 0.4, "CONTENTS", 12, color=t.muted)
    d._rect(slide, MX, 3.5, 0.6, 0.05, fill=t.primary)
    items = s.get("items", [])
    x0 = MX + 3.6
    n = max(1, len(items))
    row_h = min(0.95, (CONTENT_BOTTOM - 1.9) / n)
    y = 1.95 + max(0.0, (CONTENT_BOTTOM - 1.9 - row_h * n) / 2)
    for i, it in enumerate(items, 1):
        title = it if isinstance(it, str) else it.get("title", "")
        num = f"{i:02d}"
        d._oval(slide, x0, y + row_h / 2 - 0.17, 0.34, fill=t.primary)
        d._text(slide, x0, y + row_h / 2 - 0.125, 0.34, 0.26, num, 11,
                color=t.on_primary, bold=True, align=PP_ALIGN.CENTER)
        d._auto_text(slide, x0 + 0.52, y + row_h / 2 - 0.19, CW - 4.4, 0.4,
                     title, 16, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        if i < len(items):
            d._rect(slide, x0 + 0.52, y + row_h - 0.09, CW - 4.5, 0.012, fill=t.line)
        y += row_h


def v_section(d: Deck, slide, s):
    t = d.theme
    num = str(s.get("number", d.n))
    d._text(slide, W - MX - 5.2, H - 5.4, 5.2, 4.4, num, 150,
            color=_mix(t.bg, t.primary, 0.10), bold=True, align=PP_ALIGN.RIGHT)
    nw = max(0.62, units(num) * 0.30 + 0.3)
    d._rect(slide, MX + 0.2, 2.15, nw, 0.56, fill=t.primary, round_=True, radius=0.5)
    d._text(slide, MX + 0.2, 2.24, nw, 0.4, num, 16, color=t.on_primary, bold=True,
            align=PP_ALIGN.CENTER)
    d._auto_text(slide, MX + 0.2, 3.0, CW - 1.0, 1.3, s.get("title", ""), 36,
                 bold=True, floor=22)
    d._rect(slide, MX + 0.2, 4.45, 1.1, 0.055, fill=t.primary)
    if s.get("sub"):
        d._auto_text(slide, MX + 0.2, 4.72, 9.0, 0.8, s["sub"], 14, color=t.muted)


def v_bullets(d: Deck, slide, s):
    t = d.theme
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    items = s.get("items", [])
    has_take = bool(s.get("takeaway"))
    bottom = CONTENT_BOTTOM - (0.72 if has_take else 0.0)
    n = max(1, len(items))
    boost = 2.0 if n <= 4 else (1.0 if n == 5 else 0.0)   # 稀疏页字号补偿
    row_h = min(1.25, (bottom - y0) / n)
    y = y0 + max(0.0, (bottom - y0 - row_h * n) / 2)
    for i, it in enumerate(items, 1):
        title = it if isinstance(it, str) else it.get("title", "")
        text = "" if isinstance(it, str) else it.get("text", "")
        d._oval(slide, MX, y + 0.04, 0.4, fill=t.tint)
        d._text(slide, MX, y + 0.10, 0.4, 0.28, f"{i:02d}", 11, color=t.primary,
                bold=True, align=PP_ALIGN.CENTER)
        tx = MX + 0.58
        if text:
            d._auto_text(slide, tx, y, CW - 0.7, 0.34, title, 15 + boost, bold=True,
                         max_lines=1, floor=11)
            d._auto_text(slide, tx, y + 0.37, CW - 0.7, row_h - 0.42, text,
                         BODY + boost - 1.0, color=t.muted)
        else:
            d._auto_text(slide, tx, y, CW - 0.7, row_h - 0.06, title, 14 + boost,
                         anchor=MSO_ANCHOR.MIDDLE, floor=11)
        y += row_h
    if has_take:
        d.takeaway(slide, s["takeaway"])


def v_cards(d: Deck, slide, s):
    t = d.theme
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    items = s.get("items", [])
    has_take = bool(s.get("takeaway"))
    bottom = CONTENT_BOTTOM - (0.72 if has_take else 0.0)
    n = len(items)
    cols = 1 if n == 1 else (2 if n in (2, 4) else 3)
    rows = math.ceil(n / cols)
    gap = 0.24
    card_h = min((bottom - y0 - gap * (rows - 1)) / rows, rows * 1.9 + 0.3)  # 不留空肚子
    total_h = rows * card_h + gap * (rows - 1)
    y_top = y0 + max(0.0, (bottom - y0 - total_h) / 2)   # 内容块整体垂直居中
    cw = (CW - gap * (cols - 1)) / cols
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        row_items = min(cols, n - r * cols)
        row_w_total = row_items * cw + (row_items - 1) * gap
        x = MX + (CW - row_w_total) / 2 + c * (cw + gap)
        yy = y_top + r * (card_h + gap)
        d.card(slide, x, yy, cw, card_h, it.get("title", ""), it.get("text"),
               num=it.get("num", f"{i+1:02d}"),
               title_pt=14 + (1.0 if n <= 4 else 0.0),
               text_pt=11.5 if n > 3 else 12.0)
    if has_take:
        d.takeaway(slide, s["takeaway"])


def v_kpi(d: Deck, slide, s):
    t = d.theme
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    items = s.get("items", [])[:4]
    n = max(1, len(items))
    gap = 0.3
    cw = (CW - gap * (n - 1)) / n
    ch = min(2.75, CONTENT_BOTTOM - 0.8 - y0)
    area_bottom = CONTENT_BOTTOM - (0.72 if s.get("takeaway") else 0.15)
    ky = y0 + max(0.0, (area_bottom - y0 - ch) / 2)
    for i, it in enumerate(items):
        x = MX + i * (cw + gap)
        d._rect(slide, x, ky, cw, ch, fill=t.surface, round_=True, radius=0.06)
        d._rect(slide, x + 0.2, ky, min(0.6, cw * 0.3), 0.05, fill=t.primary)
        val = str(it.get("value", ""))
        vpt = 40 if units(val) <= 7 else 30
        d._auto_text(slide, x + 0.2, ky + 0.3, cw - 0.4, 0.95, val, vpt,
                     color=t.strong, bold=True, floor=18)
        d._auto_text(slide, x + 0.2, ky + 1.32, cw - 0.4, 0.35, it.get("label", ""),
                     12.5, bold=True, max_lines=1, floor=10)
        delta = it.get("delta")
        if delta:
            override = it.get("delta_color")
            if override == "good":
                up = True
            elif override == "bad":
                up = False
            else:
                up = not str(delta).startswith(("-", "−", "降"))
            dc = t.good if up else t.bad
            dw = units(str(delta)) * 0.13 + 0.42
            d._rect(slide, x + 0.2, ky + 1.78, dw, 0.32, fill=_mix(t.bg, dc, 0.16),
                    round_=True, radius=0.5)
            d._text(slide, x + 0.2, ky + 1.83, dw, 0.24, str(delta), 10.5, color=dc,
                    bold=True, align=PP_ALIGN.CENTER)
        if it.get("note"):
            d._auto_text(slide, x + 0.2, ky + 2.18, cw - 0.4, ch - 2.3,
                         it["note"], 10.5, color=t.muted)
    if s.get("takeaway"):
        d.takeaway(slide, s["takeaway"], y=ky + ch + 0.22)


def v_compare(d: Deck, slide, s):
    t = d.theme
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    has_take = bool(s.get("takeaway"))
    bottom = CONTENT_BOTTOM - (0.72 if has_take else 0.15)
    gap = 0.9
    cw = (CW - gap) / 2
    rec = s.get("recommend", "right")
    max_rows = max(1, max(len(s.get(k, {}).get("items", [])) for k in ("left", "right")))
    head_h = 0.55
    row_h = min(0.56, (bottom - y0 - head_h - 0.36) / max_rows)
    body_h = 0.18 + max_rows * row_h + 0.18
    block_h = head_h + body_h
    by = y0 + max(0.0, (bottom - y0 - block_h) / 2)   # 垂直居中
    for side_i, side_key in enumerate(("left", "right")):
        side = s.get(side_key, {})
        x = MX + side_i * (cw + gap)
        is_rec = (side_key == rec)
        d._rect(slide, x, by, cw, block_h, fill=t.surface, round_=True, radius=0.06)
        d._rect(slide, x, by, cw, head_h,
                fill=t.primary if is_rec else _mix(t.bg, t.text, 0.72),
                round_=True, radius=0.10)
        d._text(slide, x + 0.2, by + 0.10, cw - 1.2, 0.36, side.get("title", ""),
                14, color=t.on_primary, bold=True)
        if is_rec and side.get("tag", "推荐"):
            d._text(slide, x + cw - 1.05, by + 0.13, 0.9, 0.3,
                    side.get("tag", "推荐"), 11, color=t.on_primary,
                    align=PP_ALIGN.RIGHT)
        rows = side.get("items", [])
        ry = by + head_h + 0.18
        for ri, rtext in enumerate(rows):
            mark = "✓" if is_rec else "•"
            mc = t.good if is_rec else t.muted
            d._text(slide, x + 0.2, ry + ri * row_h, 0.3, row_h, mark, 12, color=mc,
                    bold=True, anchor=MSO_ANCHOR.MIDDLE)
            d._auto_text(slide, x + 0.52, ry + ri * row_h, cw - 0.75, row_h,
                         rtext, 12, color=t.text, anchor=MSO_ANCHOR.MIDDLE, floor=9.5)
    mid_y = by + head_h + 0.4
    d._oval(slide, MX + cw + gap / 2 - 0.36, mid_y - 0.36, 0.72, fill=t.accent)
    d._text(slide, MX + cw + gap / 2 - 0.36, mid_y - 0.16, 0.72, 0.32,
            s.get("vs", "VS"), 14, color=_dark_ink(t.accent), bold=True,
            align=PP_ALIGN.CENTER)
    if has_take:
        d.takeaway(slide, s["takeaway"])


def v_timeline(d: Deck, slide, s):
    t = d.theme
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    items = s.get("items", [])[:6]
    has_take = bool(s.get("takeaway"))
    bottom = CONTENT_BOTTOM - (0.72 if has_take else 0.0)
    n = max(1, len(items))
    axis_y = (y0 + bottom) / 2 + 0.35
    d._rect(slide, MX + 0.1, axis_y - 0.012, CW - 0.2, 0.024, fill=_mix(t.bg, t.primary, 0.45))
    step = CW / n
    for i, it in enumerate(items):
        cx = MX + step * i + step / 2
        up = (i % 2 == 0)
        dd = 0.24 if not it.get("emphasis") else 0.32
        d._oval(slide, cx - dd / 2, axis_y - dd / 2, dd, fill=t.primary)
        d._oval(slide, cx - 0.055, axis_y - 0.055, 0.11, fill=t.bg)
        date = it.get("date", f"{i+1}")
        d._text(slide, cx - step / 2, axis_y + (-0.44 if up else 0.12), step, 0.3,
                date, 12, color=t.strong, bold=True, align=PP_ALIGN.CENTER)
        card_y = axis_y - 1.62 if up else axis_y + 0.52
        card_w = min(3.1, step * 0.92)
        cx0 = max(MX, min(cx - card_w / 2, W - MX - card_w))
        d._rect(slide, cx0, card_y, card_w, 1.06, fill=t.surface, round_=True, radius=0.08)
        d._auto_text(slide, cx0 + 0.14, card_y + 0.10, card_w - 0.28, 0.3,
                     it.get("title", ""), 12.5, bold=True, max_lines=1, floor=9.5)
        if it.get("text"):
            d._auto_text(slide, cx0 + 0.14, card_y + 0.42, card_w - 0.28, 0.58,
                         it["text"], 10, color=t.muted)
    if has_take:
        d.takeaway(slide, s["takeaway"])


def v_process(d: Deck, slide, s):
    t = d.theme
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    steps = s.get("steps", s.get("items", []))[:5]
    has_take = bool(s.get("takeaway"))
    n = max(1, len(steps))
    gap = 0.12
    sw = (CW - gap * (n - 1)) / n
    sh = 0.95
    max_text_lines = max((est_lines(st.get("text", ""), 11, sw - 0.1)
                          for st in steps if st.get("text")), default=0)
    block_h = sh + (0.18 + max_text_lines * 11 * 1.35 / 72 if max_text_lines else 0)
    sy = y0 + max(0.0, (CONTENT_BOTTOM - 0.15 - y0 - block_h) / 2)  # 垂直居中
    ramp = t.ramp(n)
    for i, st in enumerate(steps):
        x = MX + i * (sw + gap)
        shp = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, Emu(int(x * _IN)),
                                     Emu(int(sy * _IN)), Emu(int(sw * _IN)),
                                     Emu(int(sh * _IN)))
        shp.fill.solid()
        shp.fill.fore_color.rgb = ramp[i]
        shp.line.fill.background()
        shp.shadow.inherit = False
        d._text(slide, x + (0.16 if i else 0.05), sy + 0.28, sw - 0.2, 0.4,
                st.get("title", f"步骤{i+1}"), 13,
                color=t.on_primary if i == 0 else _dark_ink(ramp[i]), bold=True,
                align=PP_ALIGN.CENTER)
        if st.get("text"):
            d._auto_text(slide, x + 0.05, sy + sh + 0.18, sw - 0.1, 1.1,
                         st["text"], 11, color=t.muted)
    if has_take:
        d.takeaway(slide, s["takeaway"])


def v_pyramid(d: Deck, slide, s):
    t = d.theme
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    layers = s.get("layers", s.get("items", []))
    has_take = bool(s.get("takeaway"))
    bottom = CONTENT_BOTTOM - (0.72 if has_take else 0.0)
    n = max(1, len(layers))
    lh = min(0.82, (bottom - y0) / n)
    total = n * lh
    py0 = y0 + max(0.0, (bottom - y0 - total) / 2)     # 垂直居中
    ramp = t.ramp(n)
    max_w = CW * 0.62
    cx = MX + max_w / 2
    for i, ly in enumerate(layers):
        wtop = max_w * (i + 1) / n
        yy = py0 + i * lh
        x = cx - wtop / 2
        d._rect(slide, x, yy + 0.05, wtop, lh - 0.10, fill=ramp[i], round_=True,
                radius=0.12)
        d._text(slide, x, yy + 0.05, wtop, lh - 0.10, ly.get("title", ""), 13,
                color=t.on_primary if i == 0 else _dark_ink(ramp[i]), bold=True,
                align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if ly.get("text"):
            lx = cx + max_w / 2 + 0.25
            d._rect(slide, cx + wtop / 2, yy + lh / 2 - 0.006,
                    max(0.15, lx - cx - wtop / 2 - 0.05), 0.012, fill=t.line)
            d._auto_text(slide, lx, yy + lh / 2 - 0.19, W - MX - lx, 0.4,
                         ly["text"], 11.5, color=t.muted, anchor=MSO_ANCHOR.MIDDLE)
    if has_take:
        d.takeaway(slide, s["takeaway"])


def v_funnel(d: Deck, slide, s):
    t = d.theme
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    items = s.get("items", [])
    has_take = bool(s.get("takeaway"))
    bottom = CONTENT_BOTTOM - (0.72 if has_take else 0.0)
    n = max(1, len(items))
    lh = min(0.82, (bottom - y0) / n)
    fn0 = y0 + max(0.0, (bottom - y0 - n * lh) / 2)    # 垂直居中
    ramp = t.ramp(n)
    wmax, wmin = CW * 0.72, CW * 0.30
    vals = [it.get("value") for it in items]
    nums = []
    for v in vals:
        try:
            nums.append(float(str(v).replace(",", "").rstrip("%")))
        except Exception:
            nums.append(None)
    cx = MX + wmax / 2
    for i, it in enumerate(items):
        if nums[i] and nums[0] and nums[0] > 0:
            wl = max(wmin, wmax * nums[i] / nums[0])   # 数值比例定宽
        else:
            wl = wmax - (wmax - wmin) * i / max(1, n - 1) if n > 1 else wmax
        yy = fn0 + i * lh
        d._rect(slide, cx - wl / 2, yy + 0.04, wl, lh - 0.08, fill=ramp[i],
                round_=True, radius=0.16)
        d._text(slide, cx - wl / 2, yy + 0.04, wl, lh - 0.08, it.get("label", ""),
                12.5, color=t.on_primary if i == 0 else _dark_ink(ramp[i]),
                bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if it.get("value"):
            d._text(slide, cx + wmax / 2 + 0.2, yy + lh / 2 - 0.16, 1.8, 0.34,
                    str(it["value"]), 15, color=t.strong, bold=True)
        if it.get("text"):
            d._auto_text(slide, cx + wmax / 2 + 2.1, yy + lh / 2 - 0.16,
                         W - MX - cx - wmax / 2 - 2.1, 0.36, it["text"], 10.5,
                         color=t.muted, anchor=MSO_ANCHOR.MIDDLE)
    if has_take:
        d.takeaway(slide, s["takeaway"])


def v_table(d: Deck, slide, s):
    t = d.theme
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    headers = s.get("headers", [])
    rows = s.get("rows", [])
    nr, nc = len(rows) + (1 if headers else 0), max(1, len(headers) or (len(rows[0]) if rows else 1))
    has_take = bool(s.get("takeaway"))
    bottom = CONTENT_BOTTOM - (0.72 if has_take else 0.15)
    rh = min(0.56, (bottom - y0) / max(1, nr))
    ty0 = y0 + max(0.0, (bottom - y0 - rh * nr) / 2)   # 表格垂直居中
    gf = slide.shapes.add_table(nr, nc, Emu(int(MX * _IN)), Emu(int(ty0 * _IN)),
                                Emu(int(CW * _IN)), Emu(int(rh * nr * _IN)))
    tbl = gf.table
    try:
        tbl.first_row = bool(headers)
        tbl.horz_banding = False
    except Exception:
        pass
    numeric = []
    for ci in range(nc):
        vals = [row[ci] if ci < len(row) else "" for row in rows]
        numeric.append(all(re_num(c) for c in vals) if vals else False)
    for ri in range(nr):
        tbl.rows[ri].height = Emu(int(rh * _IN))
        for ci in range(nc):
            if ri == 0 and headers:
                txt, fill_c, ink_c, bold = headers[ci], t.primary, t.on_primary, True
            else:
                data = rows[ri - 1 if headers else ri]
                txt = data[ci] if ci < len(data) else ""
                zebra = (ri % 2 == 0)
                fill_c = _mix(t.bg, t.primary, 0.05) if zebra else t.bg
                ink_c, bold = t.text, False
            cell = tbl.cell(ri, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = fill_c
            cell.margin_left = cell.margin_right = Emu(int(0.08 * _IN))
            cell.margin_top = cell.margin_bottom = Emu(int(0.03 * _IN))
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.RIGHT if (numeric[ci] and not (ri == 0 and headers)) \
                else PP_ALIGN.LEFT
            r = p.add_run()
            r.text = str(txt)
            r.font.size = Pt(min(13, max(9.5, rh * 26)))
            r.font.bold = bold
            r.font.color.rgb = ink_c
            r.font.name = "Microsoft YaHei"
    if s.get("note"):
        d._text(slide, MX, ty0 + rh * nr + 0.08, CW, 0.26, s["note"], 9.5,
                color=t.muted)
    if has_take:
        d.takeaway(slide, s["takeaway"], y=bottom + 0.05)


def re_num(s: str) -> bool:
    s = str(s).strip().replace(",", "").replace("%", "").replace("−", "-")
    if not s:
        return False
    try:
        float(s)
        return True
    except ValueError:
        return False


def v_quote(d: Deck, slide, s):
    t = d.theme
    d._text(slide, MX, 0.85, 2.0, 1.6, "\u201c", 96, color=_mix(t.bg, t.primary, 0.30),
            bold=True)
    y0 = d.header(slide, "", kicker=s.get("kicker"))
    d._auto_text(slide, MX + 0.25, 2.3, CW - 0.5, 2.6, s.get("text", ""), 24,
                 color=t.text, bold=True, lh=1.4, floor=14)
    d._rect(slide, MX + 0.25, 5.35, 0.5, 0.05, fill=t.primary)
    d._auto_text(slide, MX + 0.25, 5.55, CW - 0.5, 0.35, s.get("by", ""), 13,
                 bold=True)
    if s.get("role"):
        d._text(slide, MX + 0.25, 5.92, CW - 0.5, 0.3, s["role"], 11, color=t.muted)


def v_statement(d: Deck, slide, s):
    t = d.theme
    bg = t.deep
    ink = _dark_ink(bg)
    d._rect(slide, 0, 0, W, H, fill=bg)
    head = s.get("headline", "")
    hpt = fit_size(head, CW - 0.8, 2.2, 30, floor=16, bold=True, lh=1.25)
    hlines = est_lines(head, hpt, CW - 0.8)
    body = s.get("body", "")
    blines = est_lines(body, 14, CW - 1.2) if body else 0
    block = (0.4 if s.get("kicker") else 0) + hlines * hpt * 1.25 / 72 + \
            (0.35 + blines * 14 * 1.5 / 72 if body else 0)
    top = max(1.6, (H - block) / 2 - 0.2)              # 整块垂直居中
    y = top
    if s.get("kicker"):
        d._text(slide, MX + 0.55, y, 6.0, 0.3, s["kicker"], 11.5,
                color=_sub_ink(bg, ink, 0.55), bold=True)
        y += 0.40
    d._rect(slide, MX + 0.2, y + 0.05, 0.07, min(2.6, hlines * hpt * 1.25 / 72 + 0.3),
            fill=_mix(bg, ink, 0.75))
    d._auto_text(slide, MX + 0.55, y, CW - 0.8, 2.2, head, 30,
                 color=ink, bold=True, lh=1.25, floor=16)
    y += hlines * hpt * 1.25 / 72 + 0.30
    if body:
        d._auto_text(slide, MX + 0.55, y, CW - 1.2, 1.2, body, 14,
                     color=_sub_ink(bg, ink, 0.30), lh=1.5)


def v_big_number(d: Deck, slide, s):
    t = d.theme
    y0 = d.header(slide, s.get("title", ""), kicker=s.get("kicker")) \
        if s.get("title") else CONTENT_TOP
    num = str(s.get("number", ""))
    npt = 96 if units(num) <= 4 else (72 if units(num) <= 6 else 54)
    area_bottom = CONTENT_BOTTOM - (0.72 if s.get("takeaway") else 0.15)
    nl = est_lines(num, npt, 5.6)
    num_h = nl * npt * 1.2 / 72
    label_h = 0.5 if s.get("label") else 0
    body = s.get("body", "")
    blines = est_lines(body, 13, CW - 6.8) if body else 0
    card_h = min(0.6 + blines * 13 * 1.5 / 72 + 0.3, area_bottom - y0) if body else 0
    block = max(num_h + 0.2 + label_h, card_h)
    by = y0 + max(0.0, (area_bottom - y0 - block) / 2)  # 垂直居中
    d._auto_text(slide, MX, by, 5.6, num_h + 0.2, num, npt, color=t.strong,
                 bold=True, floor=36)
    if s.get("label"):
        d._auto_text(slide, MX, by + num_h + 0.22, 5.6, 0.5, s["label"], 18, bold=True)
    if body:
        cx0 = 7.0
        cy = by + max(0.0, (block - card_h) / 2)
        d._rect(slide, cx0, cy, CW - 6.3, card_h, fill=t.surface, round_=True,
                radius=0.06)
        d._rect(slide, cx0, cy, 0.9, 0.05, fill=t.primary)
        d._auto_text(slide, cx0 + 0.25, cy + 0.3, CW - 6.8, card_h - 0.5, body, 13,
                     color=t.muted, lh=1.5)
    if s.get("takeaway"):
        d.takeaway(slide, s["takeaway"], y=area_bottom + 0.05)


def v_closing(d: Deck, slide, s):
    t = d.theme
    if s.get("dark", True):
        bg = t.deep
        ink = _dark_ink(bg)
        d._rect(slide, 0, 0, W, H, fill=bg)
    else:
        ink = t.text
        d._rect(slide, 0, 0, W, H, fill=t.bg)
    cx = W / 2
    d._auto_text(slide, MX + 0.5, 2.55, W - 2 * MX - 1.0, 1.4, s.get("title", "谢谢"),
                 32, color=ink, bold=True, align=PP_ALIGN.CENTER, floor=18)
    d._rect(slide, cx - 0.55, 4.15, 1.1, 0.055, fill=t.primary)
    if s.get("body"):
        d._auto_text(slide, MX + 0.8, 4.45, W - 2 * MX - 1.6, 0.9, s["body"], 14,
                     color=_sub_ink(bg, ink, 0.30) if s.get("dark", True) else t.muted,
                     align=PP_ALIGN.CENTER)
    if s.get("contact"):
        d._text(slide, MX + 0.8, 5.6, W - 2 * MX - 1.6, 0.35, s["contact"], 12,
                color=_sub_ink(bg, ink, 0.45) if s.get("dark", True) else t.muted,
                align=PP_ALIGN.CENTER)


LAYOUTS = {
    "cover": v_cover, "toc": v_toc, "section": v_section, "bullets": v_bullets,
    "cards": v_cards, "kpi": v_kpi, "compare": v_compare, "timeline": v_timeline,
    "process": v_process, "pyramid": v_pyramid, "funnel": v_funnel,
    "table": v_table, "quote": v_quote, "statement": v_statement,
    "big_number": v_big_number, "closing": v_closing,
}

# 容量配额（条数上限，超出打警告——layout-library.md 配额表）
QUOTA = {"bullets": 8, "cards": 6, "kpi": 4, "timeline": 6, "process": 5,
         "pyramid": 5, "funnel": 5, "toc": 8, "compare": 5}


# ---------------------------------------------------------------- 组装
def build(deck_path, out_path, theme_id=None, footer_text=None, quiet=False):
    spec = json.load(open(deck_path, encoding="utf-8"))
    meta = spec.get("meta", {})
    theme = Theme(theme_id or meta.get("theme"),
                  custom=meta.get("colors") or None)
    footer = footer_text if footer_text is not None else meta.get("footer", "")
    d = Deck(theme, footer=footer)
    d.total = len(spec.get("slides", []))
    warns = []
    for s in spec.get("slides", []):
        typ = s.get("type", "bullets")
        fn = LAYOUTS.get(typ)
        if fn is None:
            warns.append(f"未知版式 {typ!r}（可用: {', '.join(LAYOUTS)}），已按 bullets 处理")
            fn = v_bullets
        quota = QUOTA.get(typ)
        if quota is None and fn is v_bullets:
            quota = QUOTA["bullets"]          # 未知版式按 bullets 降级后同配额
        if quota:
            key = "items" if "items" in s else ("steps" if "steps" in s else None)
            if key and len(s[key]) > quota:
                warns.append(f"第{d.n+1}页 {typ}: {len(s[key])} 条 > 配额 {quota}（建议拆页）")
        slide = d._slide()
        fn(d, slide, s)
        if typ not in ("cover",):
            d.footer(slide)
    d.prs.save(out_path)
    for w in warns:
        print("⚠", w)
    # 内建静态排版门禁（error 拒绝）
    la = os.path.join(HERE, "layout_audit.py")
    if os.path.isfile(la) and not quiet:
        sys.path.insert(0, HERE)
        import layout_audit
        from pptx import Presentation as _P
        findings = layout_audit.audit(_P(out_path), level="error")
        for f in findings:
            print(f"[{f.severity}] p{f.slide} {f.rule} shape={f.shape_id}: {f.message}")
        if findings:
            print(f"✗ 自由排版门禁：{len(findings)} error，请修内容后重试")
            return 1
        print("✓ 静态排版门禁通过")
    print(f"✓ 已生成: {os.path.abspath(out_path)}（{d.total} 页，主题 {theme.id}）")
    return 0


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    src = None
    out = "freelayout_out.pptx"
    theme_id = None
    i = 0
    while i < len(argv):
        if argv[i] == "-o" and i + 1 < len(argv):
            out = argv[i + 1]
            i += 2
        elif argv[i] == "--theme" and i + 1 < len(argv):
            theme_id = argv[i + 1]
            i += 2
        else:
            src = argv[i]
            i += 1
    if not src or not os.path.isfile(src):
        print(f"✗ 用法: python scripts/freelayout.py deck.json -o out.pptx [--theme id]")
        return 2
    return build(src, out, theme_id=theme_id)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
