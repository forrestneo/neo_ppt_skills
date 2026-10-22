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
import re
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
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
    """字符宽度模型的粗估行数（与 layout_audit 同口径，用于快速判定）。"""
    avail = max(width_in, 0.1) * _IN
    need = units(text) * pt * 12700
    return max(1, math.ceil(need / avail))


# CJK 排版断行器（蒸馏 slide-skill text_wrap.py + guizang 中文分档，MIT）：
# 避头尾（kinsoku）+ 数字量词不可断簇 + 孤行修复。折行模拟与 fit_size
# 共用同一模型——生成与测量一致才不会"估算说放得下、PowerPoint 里折三行"。
_KINSOKU_HEAD = set("，。、；：！？）》」』】〕…％‰°”’·")     # 行首禁则字
_KINSOKU_TAIL = set("（《「『【〔“‘")                          # 行尾禁则字
_MEASURE_WORDS = ("小时", "分钟", "公里", "千克", "万元", "亿元", "个月", "年级",
                  "平米", "百分点", "个百分点", "亿", "万", "%", "°")

def _tokens(text: str):
    """分词：CJK 逐字；拉丁/数字串整词；数字+量词合并为不可断簇。"""
    out, buf, i = [], "", 0
    while i < len(text):
        c = text[i]
        if ord(c) > 0x2E80:
            if buf:
                out.append(buf)
                buf = ""
            # 数字+量词簇：跳过空格回看，数字结尾的 token 与量词并簇（"6.5 小时"不可断）
            if any(text[i:].startswith(q) for q in _MEASURE_WORDS):
                j = len(out) - 1
                if j >= 0 and out[j] == " ":
                    j -= 1
                if j >= 0 and out[j] and out[j][-1:].isdigit():
                    q = max((q for q in _MEASURE_WORDS if text[i:].startswith(q)), key=len)
                    glued = out[j] + (" " if j + 1 < len(out) else "") + q
                    out = out[:j] + [glued]
                    i += len(q)
                    continue
            out.append(c)
            i += 1
        elif c.isspace():
            if buf:
                out.append(buf)
                buf = ""
            out.append(" ")
            i += 1
        else:
            buf += c
            i += 1
    if buf:
        out.append(buf)
    return out


def wrap_lines(text: str, pt: float, width_in: float, bold: bool = False):
    """模拟 PowerPoint 折行（含避头尾），返回行列表。"""
    if not text:
        return [""]
    avail_pt = max(width_in, 0.1) * 72 * (0.94 if bold else 1.0)
    lines, cur, cur_w = [], "", 0.0
    for tk in _tokens(text):
        w = units(tk) * pt
        if cur and cur_w + w > avail_pt:
            # 避头尾修正：行首禁则字 → 把标点连带前字下移；行尾禁则字 → 标点上提
            if len(tk) == 1 and tk in _KINSOKU_HEAD and cur:
                lines.append(cur)
                cur, cur_w = tk, w
            elif len(cur) >= 2 and cur[-1] in _KINSOKU_HEAD and len(cur) > 1:
                carry = cur[-1]
                lines.append(cur[:-1])
                cur, cur_w = carry + tk, units(carry) * pt + w
            else:
                lines.append(cur)
                cur, cur_w = tk, w
        else:
            cur, cur_w = cur + tk, cur_w + w
    if cur:
        lines.append(cur)
    # 孤行修复：末行只剩 1 个字且 >1 行 → 把前行末字拉下来（PTT-Studio 孤字规则）
    if len(lines) >= 2 and len(lines[-1].replace(" ", "")) == 1 \
            and len(lines[-2]) >= 2:
        lines[-1] = lines[-2][-1] + lines[-1]
        lines[-2] = lines[-2][:-1]
    return lines


def fit_size(text: str, width_in: float, height_in: float, base: float,
             floor: float = 9.0, bold: bool = False, lh: float = 1.3,
             max_lines: int = 99) -> float:
    """字号沿 TYPE_SCALE 回落至装得下；折行模拟含避头尾，末行孤字自动再降一档。"""
    candidates = [s for s in TYPE_SCALE if floor <= s <= base] or [floor]
    picked = candidates[-1]
    for s in candidates:
        lines = wrap_lines(text, s, width_in, bold=bold)
        if len(lines) * s * lh / 72 <= height_in and len(lines) <= max_lines:
            picked = s
            break
    return picked


def title_tier(text: str, base: float):
    """标题按字数分档（guizang 瑞士规则）：≤8 字一档、9-16 降档、>16 再降并建议改写。"""
    n = len(text)
    if n <= 8:
        return base
    if n <= 16:
        return base * 0.78
    return base * 0.60


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

    def _picture_cover(self, slide, path, x, y, w, h):
        """图片按 cover 语义裁切填盒（绝不拉伸变形）。返回 None=文件缺失。"""
        if not path or not os.path.isfile(path):
            return None
        from PIL import Image
        try:
            iw, ih = Image.open(path).size
        except Exception:
            return None
        box_ar, img_ar = w / h, iw / ih
        pic = slide.shapes.add_picture(path, Emu(int(x * _IN)), Emu(int(y * _IN)),
                                       Emu(int(w * _IN)), Emu(int(h * _IN)))
        if img_ar > box_ar:                       # 图偏宽 → 裁左右
            keep = box_ar / img_ar
            c = (1 - keep) / 2
            pic.crop_left = pic.crop_right = c
        elif img_ar < box_ar:                     # 图偏高 → 裁上下
            keep = img_ar / box_ar
            c = (1 - keep) / 2
            pic.crop_top = pic.crop_bottom = c
        return pic

    def _pin(self, slide, cx, cy, n, d=0.34):
        """截图上的编号定位 pin：白环 + 主色芯 + 白字（luobo shot_notes 式）。"""
        t = self.theme
        self._oval(slide, cx - d / 2, cy - d / 2, d, fill=t.bg)
        dd = d * 0.72
        self._oval(slide, cx - dd / 2, cy - dd / 2, dd, fill=t.primary)
        self._text(slide, cx - d / 2, cy - 0.09, d, 0.2, str(n), 9.5,
                   color=t.on_primary, bold=True, align=PP_ALIGN.CENTER)

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
    d._auto_text(slide, x, y, 8.6, 2.1, s["title"], title_tier(s["title"], 48),
                 color=ink, bold=True, lh=1.12, floor=26)
    tpt = fit_size(s["title"], 8.6, 2.1, title_tier(s["title"], 48), bold=True,
                   lh=1.12, floor=26)
    lines = len(wrap_lines(s["title"], tpt, 8.6, bold=True))
    y += lines * tpt * 1.12 / 72 + 0.22
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


def comp_bullets(d: Deck, slide, x, y, w, h, s):
    """要点组件：可在任意矩形渲染（模板页 overlay 与整页版式共用）。"""
    t = d.theme
    items = s.get("items", [])
    n = max(1, len(items))
    boost = 2.0 if n <= 4 else (1.0 if n == 5 else 0.0)   # 稀疏页字号补偿
    row_h = min(1.25, h / n)
    yy = y + max(0.0, (h - row_h * n) / 2)
    for i, it in enumerate(items, 1):
        title = it if isinstance(it, str) else it.get("title", "")
        text = "" if isinstance(it, str) else it.get("text", "")
        d._oval(slide, x, yy + 0.04, 0.4, fill=t.tint)
        d._text(slide, x, yy + 0.10, 0.4, 0.28, f"{i:02d}", 11, color=t.primary,
                bold=True, align=PP_ALIGN.CENTER)
        tx = x + 0.58
        if text:
            d._auto_text(slide, tx, yy, w - 0.7, 0.34, title, 15 + boost, bold=True,
                         max_lines=1, floor=11)
            d._auto_text(slide, tx, yy + 0.37, w - 0.7, row_h - 0.42, text,
                         BODY + boost - 1.0, color=t.muted)
        else:
            d._auto_text(slide, tx, yy, w - 0.7, row_h - 0.06, title, 14 + boost,
                         anchor=MSO_ANCHOR.MIDDLE, floor=11)
        yy += row_h


def v_bullets(d: Deck, slide, s):
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    has_take = bool(s.get("takeaway"))
    bottom = CONTENT_BOTTOM - (0.72 if has_take else 0.0)
    comp_bullets(d, slide, MX, y0, CW, bottom - y0, s)
    if has_take:
        d.takeaway(slide, s["takeaway"])


def comp_cards(d: Deck, slide, x, y, w, h, s):
    """卡片网格组件：可在任意矩形渲染。"""
    items = s.get("items", [])
    n = len(items)
    cols = 1 if n == 1 else (2 if n in (2, 4) else 3)
    rows = math.ceil(n / cols)
    gap = 0.24
    card_h = min((h - gap * (rows - 1)) / rows, rows * 1.9 + 0.3)  # 不留空肚子
    total_h = rows * card_h + gap * (rows - 1)
    y_top = y + max(0.0, (h - total_h) / 2)               # 内容块整体垂直居中
    cw = (w - gap * (cols - 1)) / cols
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        row_items = min(cols, n - r * cols)
        row_w_total = row_items * cw + (row_items - 1) * gap
        xx = x + (w - row_w_total) / 2 + c * (cw + gap)
        yy = y_top + r * (card_h + gap)
        d.card(slide, xx, yy, cw, card_h, it.get("title", ""), it.get("text"),
               num=it.get("num", f"{i+1:02d}"),
               title_pt=14 + (1.0 if n <= 4 else 0.0),
               text_pt=11.5 if n > 3 else 12.0)


def v_cards(d: Deck, slide, s):
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    has_take = bool(s.get("takeaway"))
    bottom = CONTENT_BOTTOM - (0.72 if has_take else 0.0)
    comp_cards(d, slide, MX, y0, CW, bottom - y0, s)
    if has_take:
        d.takeaway(slide, s["takeaway"])


def comp_kpi(d: Deck, slide, x, y, w, h, s):
    """KPI 瓦片组件：可在任意矩形渲染。返回瓦片底部 y。"""
    t = d.theme
    items = s.get("items", [])[:4]
    n = max(1, len(items))
    gap = 0.3
    cw = (w - gap * (n - 1)) / n
    ch = min(2.75, h)
    ky = y + max(0.0, (h - ch) / 2)
    for i, it in enumerate(items):
        x0 = x + i * (cw + gap)
        d._rect(slide, x0, ky, cw, ch, fill=t.surface, round_=True, radius=0.06)
        d._rect(slide, x0 + 0.2, ky, min(0.6, cw * 0.3), 0.05, fill=t.primary)
        val = str(it.get("value", ""))
        vpt = 40 if units(val) <= 7 else 30
        d._auto_text(slide, x0 + 0.2, ky + 0.3, cw - 0.4, 0.95, val, vpt,
                     color=t.strong, bold=True, floor=18)
        d._auto_text(slide, x0 + 0.2, ky + 1.32, cw - 0.4, 0.35, it.get("label", ""),
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
            d._rect(slide, x0 + 0.2, ky + 1.78, dw, 0.32, fill=_mix(t.bg, dc, 0.16),
                    round_=True, radius=0.5)
            d._text(slide, x0 + 0.2, ky + 1.83, dw, 0.24, str(delta), 10.5, color=dc,
                    bold=True, align=PP_ALIGN.CENTER)
        if it.get("note"):
            d._auto_text(slide, x0 + 0.2, ky + 2.18, cw - 0.4, ch - 2.3,
                         it["note"], 10.5, color=t.muted)
    return ky + ch


def v_kpi(d: Deck, slide, s):
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    kpi_bottom = comp_kpi(d, slide, MX, y0, CW, CONTENT_BOTTOM - 0.8 - y0, s)
    if s.get("takeaway"):
        d.takeaway(slide, s["takeaway"], y=kpi_bottom + 0.22)


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


def comp_table(d: Deck, slide, x, y, w, h, s):
    """原生表格组件：可在任意矩形渲染。返回表格底部 y。"""
    t = d.theme
    headers = s.get("headers", [])
    rows = s.get("rows", [])
    nr, nc = len(rows) + (1 if headers else 0), max(1, len(headers) or (len(rows[0]) if rows else 1))
    rh = min(0.56, h / max(1, nr))
    ty0 = y + max(0.0, (h - rh * nr) / 2)              # 表格垂直居中
    gf = slide.shapes.add_table(nr, nc, Emu(int(x * _IN)), Emu(int(ty0 * _IN)),
                                Emu(int(w * _IN)), Emu(int(rh * nr * _IN)))
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
        d._text(slide, x, ty0 + rh * nr + 0.08, w, 0.26, s["note"], 9.5,
                color=t.muted)
    return ty0 + rh * nr


def v_table(d: Deck, slide, s):
    t = d.theme
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    has_take = bool(s.get("takeaway"))
    bottom = CONTENT_BOTTOM - (0.72 if has_take else 0.15)
    comp_table(d, slide, MX, y0, CW, bottom - y0, s)
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


def comp_chart(d: Deck, slide, x, y, w, h, s):
    """原生图表组件：可在任意矩形渲染。返回内容底部 y。"""
    t = d.theme
    cats = s.get("categories", [])
    series = s.get("series", [])
    ctype = s.get("chart_type", "bar")
    insights = s.get("insights", [])[:3]
    if len(cats) > 10:
        print(f"⚠ chart: 类目 {len(cats)} > 10（柱子变细，建议归并）")
    if ctype == "pie" and len(cats) > 5:
        print("⚠ chart: 饼图 >5 片，建议取 Top5 + 其他")
    if ctype == "line" and len(series) > 3:
        print(f"⚠ chart: 折线 {len(series)} 系列 > 3，建议拆图")
    chart_w = w * 0.63 if insights else w
    ch = h - (0.30 if s.get("unit") else 0)
    ct_map = {"bar": XL_CHART_TYPE.COLUMN_CLUSTERED, "hbar": XL_CHART_TYPE.BAR_CLUSTERED,
              "line": XL_CHART_TYPE.LINE_MARKERS, "area": XL_CHART_TYPE.AREA,
              "pie": XL_CHART_TYPE.PIE}
    data = CategoryChartData()
    data.categories = cats
    for ser in series:
        data.add_series(ser.get("name", ""), ser.get("values", []))
    try:
        gf = slide.shapes.add_chart(ct_map.get(ctype, XL_CHART_TYPE.COLUMN_CLUSTERED),
                                    Emu(int(x * _IN)), Emu(int(y * _IN)),
                                    Emu(int(chart_w * _IN)), Emu(int(ch * _IN)), data)
    except Exception as e:
        print(f"✗ chart 生成失败: {e}")
        return y + h
    chart = gf.chart
    chart.has_title = False
    chart.font.size = Pt(10)
    chart.font.color.rgb = t.text
    plot = chart.plots[0]
    ramp = t.ramp(max(2, len(series))) if len(series) > 1 else t.ramp(len(cats))
    try:
        if ctype == "pie":
            chart.has_legend = False
            plot.has_data_labels = True
            dl = plot.data_labels
            dl.show_percentage = True
            dl.show_value = False
            dl.font.size = Pt(10)
            for i, pt_ in enumerate(plot.series[0].points):
                pt_.format.fill.solid()
                pt_.format.fill.fore_color.rgb = ramp[i % len(ramp)]
        else:
            multi = len(series) > 1
            chart.has_legend = multi
            if multi:
                chart.legend.position = XL_LEGEND_POSITION.BOTTOM
                chart.legend.include_in_layout = False
            for i, ser in enumerate(plot.series):
                ser.format.fill.solid()
                ser.format.fill.fore_color.rgb = ramp[i % len(ramp)]
            va = chart.value_axis
            va.has_major_gridlines = True
            va.major_gridlines.format.line.color.rgb = _mix(t.bg, t.muted, 0.25)
            va.tick_labels.font.size = Pt(9)
            chart.category_axis.tick_labels.font.size = Pt(10)
    except Exception:
        pass
    if s.get("unit"):
        d._text(slide, x, y + ch + 0.04, chart_w, 0.24, f"单位：{s['unit']}", 9.5,
                color=t.muted)
    if insights:
        ix = x + chart_w + 0.35
        iw = x + w - ix
        ih = min(1.35, (h - 0.3) / max(1, len(insights)))
        for i, ins in enumerate(insights):
            iy = y + i * (ih + 0.15)
            d.card(slide, ix, iy, iw, ih, f"{i+1:02d}", ins, num=None,
                   title_pt=13, text_pt=10.5)
    return y + h


def v_chart(d: Deck, slide, s):
    """原生可编辑图表 + 右侧 insight 解读卡（dsh-ppt-master 规则）。"""
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    has_take = bool(s.get("takeaway"))
    bottom = CONTENT_BOTTOM - (0.72 if has_take else 0.15)
    comp_chart(d, slide, MX, y0, CW, bottom - y0, s)
    if has_take:
        d.takeaway(slide, s["takeaway"])


def v_image(d: Deck, slide, s):
    """图片 + 对侧要点（图占 52%，cover 裁切绝不拉伸；缺图出占位框并警告）。"""
    t = d.theme
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    has_take = bool(s.get("takeaway"))
    bottom = CONTENT_BOTTOM - (0.72 if has_take else 0.15)
    side = s.get("image_side", "left")
    img_w = CW * 0.52
    img_h = min(bottom - y0, 4.4)
    ix = MX if side == "left" else MX + CW - img_w
    tx = MX + img_w + 0.4 if side == "left" else MX
    tw = CW - img_w - 0.4
    img = d._picture_cover(slide, s.get("image"), ix, y0, img_w, img_h)
    if img is None:
        d._rect(slide, ix, y0, img_w, img_h, fill=t.surface, round_=True, radius=0.04)
        d._text(slide, ix, y0 + img_h / 2 - 0.15, img_w, 0.3, "图片待补", 12,
                color=t.muted, align=PP_ALIGN.CENTER)
        print(f"⚠ image: 找不到图片文件 {s.get('image')!r}（已画占位框）")
    if s.get("caption"):
        d._text(slide, ix, y0 + img_h + 0.08, img_w, 0.26, s["caption"], 9.5,
                color=t.muted)
    items = s.get("items", [])
    n = max(1, len(items))
    row_h = min(1.0, (bottom - y0) / n)
    yy = y0 + max(0.0, (bottom - y0 - row_h * n) / 2)
    for i, it in enumerate(items, 1):
        title = it if isinstance(it, str) else it.get("title", "")
        text = "" if isinstance(it, str) else it.get("text", "")
        d._oval(slide, tx, yy + 0.03, 0.34, fill=t.tint)
        d._text(slide, tx, yy + 0.085, 0.34, 0.24, f"{i:02d}", 10.5, color=t.primary,
                bold=True, align=PP_ALIGN.CENTER)
        if text:
            d._auto_text(slide, tx + 0.5, yy, tw - 0.5, 0.32, title, 14.5, bold=True,
                         max_lines=1, floor=10.5)
            d._auto_text(slide, tx + 0.5, yy + 0.34, tw - 0.5, row_h - 0.38, text,
                         11, color=t.muted)
        else:
            d._auto_text(slide, tx + 0.5, yy, tw - 0.5, row_h - 0.06, title, 13.5,
                         anchor=MSO_ANCHOR.MIDDLE, floor=10.5)
        yy += row_h
    if has_take:
        d.takeaway(slide, s["takeaway"])


def v_screenshot(d: Deck, slide, s):
    """截图窗口外框 + 编号步骤 + 图上 pin（luobo shot_notes 规则）：
    横截图占 62% 宽、窗口三圆点标题栏、右侧步骤 ≤5 条、pin 白环主色芯。"""
    t = d.theme
    y0 = d.header(slide, s["title"], kicker=s.get("kicker"), sub=s.get("sub"))
    has_take = bool(s.get("takeaway"))
    bottom = CONTENT_BOTTOM - (0.72 if has_take else 0.15)
    imgs = s.get("images", [])
    steps = s.get("steps", [])[:5]
    frame_w = CW * (0.62 if steps else 1.0)
    if len(imgs) > 3:
        print(f"⚠ screenshot: {len(imgs)} 张 > 3（多图建议走流程页）")
    fh = bottom - y0
    bar = 0.26
    fx = MX
    d._rect(slide, fx, y0, frame_w, fh, fill=t.surface, round_=True, radius=0.03)
    d._rect(slide, fx, y0, frame_w, bar, fill=_mix(t.bg, t.muted, 0.30))
    for k in range(3):
        d._oval(slide, fx + 0.14 + k * 0.17, y0 + bar / 2 - 0.05, 0.1,
                fill=_mix(t.bg, t.primary, 0.35))
    inner_y = y0 + bar + 0.08
    inner_h = fh - bar - 0.16
    n = max(1, len(imgs))
    gap = 0.12
    iw = (frame_w - 0.24 - gap * (n - 1)) / n
    for i, ip in enumerate(imgs):
        ix = fx + 0.12 + i * (iw + gap)
        pic = d._picture_cover(slide, ip, ix, inner_y, iw, inner_h)
        if pic is None:
            d._rect(slide, ix, inner_y, iw, inner_h, fill=_mix(t.bg, t.muted, 0.18))
            print(f"⚠ screenshot: 找不到图片 {ip!r}")
    for pin in s.get("pins", [])[:8]:
        at = pin.get("at", [0.5, 0.5])
        px = fx + 0.12 + (frame_w - 0.24) * min(1.0, max(0.0, at[0]))
        py = inner_y + inner_h * min(1.0, max(0.0, at[1]))
        d._pin(slide, px, py, pin.get("n", 1))
    if steps:
        sx = fx + frame_w + 0.3
        sw = W - MX - sx
        row_h = min(0.9, (bottom - y0) / max(1, len(steps)))
        yy = y0 + max(0.0, (bottom - y0 - row_h * len(steps)) / 2)
        for i, st in enumerate(steps, 1):
            title = st if isinstance(st, str) else st.get("title", "")
            text = "" if isinstance(st, str) else st.get("text", "")
            d._pin(slide, sx + 0.17, yy + 0.17, i)
            if text:
                d._auto_text(slide, sx + 0.5, yy, sw - 0.5, 0.3, title, 13, bold=True,
                             max_lines=1, floor=10)
                d._auto_text(slide, sx + 0.5, yy + 0.32, sw - 0.5, row_h - 0.36, text,
                             10.5, color=t.muted)
            else:
                d._auto_text(slide, sx + 0.5, yy, sw - 0.5, row_h - 0.06, title, 12.5,
                             anchor=MSO_ANCHOR.MIDDLE, floor=10)
            yy += row_h
    if has_take:
        d.takeaway(slide, s["takeaway"])


# 组件注册表：矩形化渲染，模板页 overlay 与整页版式共用同一实现
COMPONENTS = {"cards": comp_cards, "bullets": comp_bullets, "kpi": comp_kpi,
              "chart": comp_chart, "table": comp_table}


def render_component(d: Deck, slide, spec: dict):
    """在任意矩形渲染一个自由排版组件（577 页模板页 overlay 的入口）。

    spec: {"component": "cards|bullets|kpi|chart|table",
           "rect": [x, y, w, h](英寸，可省略默认内容区), ...内容字段(items/series 等)}
    """
    comp = spec.get("component")
    fn = COMPONENTS.get(comp)
    if fn is None:
        raise ValueError(f"未知组件 {comp!r}（可用: {', '.join(COMPONENTS)}）")
    rect = spec.get("rect") or [MX, CONTENT_TOP, CW, CONTENT_BOTTOM - CONTENT_TOP]
    if len(rect) != 4:
        raise ValueError("rect 须为 [x, y, w, h]（英寸）")
    return fn(d, slide, *[float(v) for v in rect], spec)


LAYOUTS = {
    "cover": v_cover, "toc": v_toc, "section": v_section, "bullets": v_bullets,
    "cards": v_cards, "kpi": v_kpi, "compare": v_compare, "timeline": v_timeline,
    "process": v_process, "pyramid": v_pyramid, "funnel": v_funnel,
    "table": v_table, "quote": v_quote, "statement": v_statement,
    "big_number": v_big_number, "closing": v_closing,
    "chart": v_chart, "image": v_image, "screenshot": v_screenshot,
}

# 容量配额（条数上限，超出打警告——layout-library.md 配额表）
QUOTA = {"bullets": 8, "cards": 6, "kpi": 4, "timeline": 6, "process": 5,
         "pyramid": 5, "funnel": 5, "toc": 8, "compare": 5}

# 版式内容契约（蒸馏 guizang swiss-layout-lock）：数据专用版式收到无数据内容
# 时警告——"给概念列表编百分比会被识破"，宁换通用版式也不编数。
_DATA_CONTRACT = {"kpi": "kpi/items", "big_number": "number", "funnel": "items[].value",
                  "table": "rows", "chart": "series/categories"}

# 容量候选链：主版式超配额时的自动降级（零静默丢失——全部内容随迁，只换容器）
LAYOUT_FALLBACK = {"cards": "bullets", "kpi": "bullets", "timeline": "bullets",
                   "process": "bullets", "pyramid": "bullets", "funnel": "table",
                   "toc": "bullets"}


def _adapt_for(new_type: str, s: dict) -> dict:
    """版式降级时的内容搬运：字段形状适配，不丢任何信息。"""
    s = dict(s)
    items = s.get("items", s.get("steps", []))
    if new_type == "bullets":
        norm = []
        for it in items:
            if isinstance(it, str):
                norm.append(it)
            else:
                head = " · ".join(str(v) for v in (
                    it.get("date"), it.get("value"), it.get("label") or it.get("title", "")
                ) if v)
                norm.append({"title": head or it.get("title", ""),
                             "text": it.get("text") or it.get("note", "")})
        s["items"] = norm
        s.pop("steps", None)
    elif new_type == "table":
        s["headers"] = s.get("headers", ["阶段", "数值", "说明"])
        s["rows"] = [[it.get("label", ""), it.get("value", ""), it.get("text", "")]
                     for it in items]
        s.pop("items", None)
    return s


# ---------------------------------------------------------------- 内容级 lint
# （蒸馏 luobo outline_check / dsh-ppt-master lintDeck：写大纲时就把平庸拦住）
_TOPIC_SUFFIX = ("介绍", "概述", "总结", "背景", "注意事项", "优势", "方法", "原理",
                 "现状", "分析", "要点", "内容", "问题", "结论", "汇报", "说明",
                 "情况", "工作", "方案", "措施")
_VAGUE_WORDS = ("赋能", "抓手", "闭环", "生态", "打法", "组合拳", "颗粒度")
_THANKS_PAT = None  # 惰性编译


def lint_title(title: str):
    """结论式标题检查，返回问题描述或 None（luobo looks_like_topic 量化版）。"""
    global _THANKS_PAT
    title = (title or "").strip()
    if not title:
        return "空标题"
    for suf in _TOPIC_SUFFIX:
        if title.endswith(suf) and len(title) <= len(suf) + 6:
            return f"话题名而非结论（以「{suf}」结尾，写发现不写主题）"
    if re.match(r"^(什么是|如何|怎么)", title) and len(title) <= 8 \
            and not any(p in title for p in "，。！？"):
        return "疑问式短标题，建议改写为可判断的结论句"
    for w in _VAGUE_WORDS:
        if w in title:
            return f"空洞词「{w}」"
    if _THANKS_PAT is None:
        _THANKS_PAT = __import__("re").compile(r"^谢谢(观看|收听|聆听|大家)?$|^thanks$|^q&a$", re.I)
    if _THANKS_PAT.match(title):
        return "结尾页放结论或行动号召，不放「谢谢观看」"
    return None


def content_lint(slides):
    """对 deck.json 的 slides 做内容级 lint，返回警告列表（含幽灵稿）。"""
    warns = []
    for i, s in enumerate(slides, 1):
        title = s.get("title") or s.get("headline") or ""
        issue = lint_title(title)
        if issue:
            tag = "建议改写" if not _THANKS_PAT or not _THANKS_PAT.match(title.strip()) else "结尾页建议"
            warns.append(f"第{i}页 [{s.get('type')}] 标题「{title[:20]}」: {issue}（{tag}）")
    ghosts = [((s.get("title") or s.get("headline") or "").strip() or f"（无题 {s.get('type')}）")
              for s in slides]
    warns.append("幽灵稿自检——只读以下标题应能讲通整个故事：" + " → ".join(ghosts))
    return warns


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
    slides = spec.get("slides", [])
    # 内容级 lint（写大纲时拦平庸：话题式标题/空洞词/疑问短句/谢谢观看 + 幽灵稿）
    if not quiet:
        for lw in content_lint(slides):
            warns.append(lw)
    for s in slides:
        typ = s.get("type", "bullets")
        fn = LAYOUTS.get(typ)
        if fn is None:
            warns.append(f"未知版式 {typ!r}（可用: {', '.join(LAYOUTS)}），已按 bullets 处理")
            fn = v_bullets
        quota = QUOTA.get(typ)
        if quota is None and fn is v_bullets:
            quota = QUOTA["bullets"]          # 未知版式按 bullets 降级后同配额
        # 容量表驱动自动换版式（luobo capacity 思想）：主版式超配额 → 沿候选链
        # 换装得下的版式，写 layout_auto 审计记录（想要 X 换成 Y 因为超容量）。
        layout_auto = None
        hops = 0
        while quota and hops < 3:
            key = "items" if "items" in s else ("steps" if "steps" in s else None)
            if not (key and len(s[key]) > quota):
                break
            fb = LAYOUT_FALLBACK.get(typ)
            if not fb or not LAYOUTS.get(fb):
                warns.append(f"第{d.n+1}页 {typ}: {len(s[key])} 条 > 配额 {quota}（无候选版式，建议拆页）")
                break
            warns.append(f"第{d.n+1}页 {typ}: {len(s[key])} 条 > 配额 {quota}，"
                         f"自动换版式 → {fb}（想要 {typ} 请精简条目）")
            s = _adapt_for(fb, s)
            layout_auto = {"wanted": typ, "switched_to": fb,
                           "reason": f"{len(s.get('items', s.get('steps', [])))} 条超配额" if not layout_auto else layout_auto.get("reason")}
            typ, fn = fb, LAYOUTS[fb]
            quota = QUOTA.get(typ)
            hops += 1
        if layout_auto:
            warns.append(f"第{d.n+1}页 layout_auto: wanted={layout_auto['wanted']} "
                         f"→ {layout_auto['switched_to']}（{layout_auto['reason']}）")
        if typ in _DATA_CONTRACT:
            blob = json.dumps(s, ensure_ascii=False)
            if not any(ch.isdigit() for ch in blob):
                warns.append(f"第{d.n+1}页 {typ}: 数据专用版式但内容不含任何数字——"
                             f"请补真实数据，或改用通用版式（{_DATA_CONTRACT[typ]} 字段应承载数值）")
        slide = d._slide()
        seen_types = getattr(d, "_types", None)
        if seen_types is None:
            seen_types = d._types = []
        seen_types.append(typ)
        if len(seen_types) >= 3 and seen_types[-1] == seen_types[-2] == seen_types[-3]:
            warns.append(f"第{d.n}页 {typ}: 同一版式连续 3 页（节奏单调，建议换版式或插大字页）")
        fn(d, slide, s)
        if typ not in ("cover",):
            d.footer(slide)
        notes = s.get("notes")
        if notes:
            try:
                slide.notes_slide.notes_text_frame.text = str(notes)
            except Exception:
                pass
            nl = len(str(notes))
            if meta.get("scenario") == "oral" and not (40 <= nl <= 260):
                warns.append(f"第{d.n}页 口播备注 {nl} 字（建议 40-260 字 ≈ 15-60 秒）")
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
    quiet = False
    i = 0
    while i < len(argv):
        if argv[i] == "-o" and i + 1 < len(argv):
            out = argv[i + 1]
            i += 2
        elif argv[i] == "--theme" and i + 1 < len(argv):
            theme_id = argv[i + 1]
            i += 2
        elif argv[i] == "--quiet":
            quiet = True
            i += 1
        else:
            src = argv[i]
            i += 1
    if not src or not os.path.isfile(src):
        print(f"✗ 用法: python scripts/freelayout.py deck.json -o out.pptx [--theme id]")
        return 2
    return build(src, out, theme_id=theme_id, quiet=quiet)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
