#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["uharfbuzz>=0.40"]
# ///
"""Draws the SVG sheets used by README.md and README.zh-CN.md.

The look follows qwq.my: a drawing sheet with a zoned frame, ink on paper,
one red pen. Text is converted to outlines, so the images render the same on
every system and need no web fonts. They switch to dark ink-on-black when the
viewer prefers a dark colour scheme.

Edit DATA below, then run one of:

    uv run assets/build.py
    pip install uharfbuzz && python assets/build.py

Fonts (Archivo, JetBrains Mono, Noto Sans SC; SIL Open Font License 1.1) are
downloaded into assets/.fonts on the first run.
"""

from __future__ import annotations

import urllib.request
from html import escape
from pathlib import Path

import uharfbuzz as hb

HERE = Path(__file__).resolve().parent
FONT_DIR = HERE / ".fonts"
FONT_URLS = {
    "Archivo.ttf": "https://github.com/google/fonts/raw/main/ofl/archivo/Archivo%5Bwdth,wght%5D.ttf",
    "JetBrainsMono.ttf": "https://github.com/google/fonts/raw/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
    "NotoSansSC.ttf": "https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf",
}

# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

DATA = {
    "en": {
        "role": "Student / Developer",
        "handle": "@SnowballXueQiu · 雪球",
        "status": [("Dev at Vastsea & KLPBBS, now working at ", "i"), ("Respan", "a"), (".", "i")],
        "quote": "“What you learn on paper stays shallow; to truly know a thing, do it.”",
        "titles": ["Profile", "Timeline", "Toolbox"],
        "tb": {"drawn": "Drawn by", "dwg": "Dwg no.", "rev": "Rev", "scale": "Scale", "sheet": "Sheet"},
        "nts": "Scale NTS",
        "bom": "Bill of materials",
        "cols": ["No.", "Group", "Parts", "Qty"],
        "timeline": [
            ("2021.09", "Vastsea", "co-founded the team"),
            ("2024.08", "The Rust Course", "became a collaborator"),
            ("2024.11", "KLPBBS", "head of tech"),
            ("2025.07", "AdventureX", "3rd Prize + Excellence Award"),
            ("2025.09", "Tianjin Normal Univ.", "started a degree in AI"),
            ("2026.10", "Hainan Bielefeld UAS", "invited to teach"),
            ("NOW", "Respan", "working here"),
        ],
        "skills": [
            ("Fluent", ["TypeScript", "JavaScript", "Python", "Java", "Kotlin"]),
            ("Familiar", ["Rust", "Go"]),
            ("Get by", ["C/C++", "C#", "Shell", "MATLAB"]),
            ("Frontend", ["Next.js", "React", "Vue", "Three.js", "GSAP"]),
            ("Native", ["Flutter", "Dart", "SwiftUI"]),
            ("Backend", ["Node.js", "Axum", "SeaORM", "FastAPI"]),
            ("Database", ["PostgreSQL", "MySQL", "SQLite", "MongoDB"]),
            ("DevOps", ["Docker", "Kubernetes", "GitHub Actions", "Gitea"]),
            ("AI tools", ["Claude Code", "Codex"]),
        ],
    },
    "zh": {
        "role": "学生 / 开发者",
        "handle": "@SnowballXueQiu · 雪球",
        "status": [("瀚海工艺、苦力怕论坛开发者，现于 ", "i"), ("Respan", "a"), (" 工作", "i")],
        "quote": "纸上得来终觉浅，绝知此事要躬行。",
        "titles": ["主页", "时间线", "技能清单"],
        "tb": {"drawn": "绘制", "dwg": "图号", "rev": "版本", "scale": "比例", "sheet": "图幅"},
        "nts": "比例 NTS",
        "bom": "物料清单 BOM",
        "cols": ["序号", "分组", "物料", "数量"],
        "timeline": [
            ("2021.09", "瀚海工艺", "联合创立技术团队"),
            ("2024.08", "Rust 语言圣经", "成为协作者"),
            ("2024.11", "苦力怕论坛", "技术总管"),
            ("2025.07", "AdventureX 黑客松", "三等奖 + 优秀奖"),
            ("2025.09", "天津师范大学", "人工智能专业"),
            ("2026.10", "受邀授课", "海南比勒费尔德应用科学大学"),
            ("现在", "Respan", "在这里工作"),
        ],
        "skills": [
            ("熟练", ["TypeScript", "JavaScript", "Python", "Java", "Kotlin"]),
            ("了解", ["Rust", "Go"]),
            ("够用", ["C/C++", "C#", "Shell", "MATLAB"]),
            ("前端", ["Next.js", "React", "Vue", "Three.js", "GSAP"]),
            ("原生", ["Flutter", "Dart", "SwiftUI"]),
            ("后端", ["Node.js", "Axum", "SeaORM", "FastAPI"]),
            ("数据库", ["PostgreSQL", "MySQL", "SQLite", "MongoDB"]),
            ("运维", ["Docker", "Kubernetes", "GitHub Actions", "Gitea"]),
            ("AI 工具", ["Claude Code", "Codex"]),
        ],
    },
}

SHEETS = 3

# ---------------------------------------------------------------------------
# Fonts and text outlines
# ---------------------------------------------------------------------------

FONT_SPECS = {
    # key: (file, variation axes, features, id prefix, fallback for missing glyphs)
    "display": ("Archivo.ttf", {"wght": 800, "wdth": 100}, {}, "d", "scb"),
    "cond": ("Archivo.ttf", {"wght": 900, "wdth": 62}, {}, "c", "scb"),
    "mono": ("JetBrainsMono.ttf", {"wght": 400}, {"calt": False, "liga": False}, "m", "sc"),
    "monob": ("JetBrainsMono.ttf", {"wght": 700}, {"calt": False, "liga": False}, "M", "scb"),
    "sc": ("NotoSansSC.ttf", {"wght": 400}, {}, "s", "sc"),
    "scb": ("NotoSansSC.ttf", {"wght": 700}, {}, "S", "scb"),
}


def fmt(v: float, nd: int = 2) -> str:
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


class PathPen:
    """Collects a glyph outline as SVG path data, in font units."""

    def __init__(self):
        self.parts: list[str] = []

    @staticmethod
    def _p(pt) -> str:
        return f"{round(pt[0])} {round(pt[1])}"

    def moveTo(self, pt):
        self.parts.append("M" + self._p(pt))

    def lineTo(self, pt):
        self.parts.append("L" + self._p(pt))

    def qCurveTo(self, *pts):
        # Split runs of off-curve points at their implied on-curve midpoints.
        *offs, end = pts
        for i, c in enumerate(offs):
            nxt = end if i == len(offs) - 1 else ((c[0] + offs[i + 1][0]) / 2, (c[1] + offs[i + 1][1]) / 2)
            self.parts.append("Q" + self._p(c) + " " + self._p(nxt))

    def curveTo(self, c1, c2, pt):
        self.parts.append("C" + self._p(c1) + " " + self._p(c2) + " " + self._p(pt))

    def closePath(self):
        self.parts.append("Z")

    def endPath(self):
        pass

    def d(self) -> str:
        return "".join(self.parts)


class Font:
    def __init__(self, key: str):
        file, axes, features, prefix, fallback = FONT_SPECS[key]
        self.face = hb.Face(hb.Blob.from_file_path(str(FONT_DIR / file)))
        self.font = hb.Font(self.face)
        if axes:
            self.font.set_variations(axes)
        self.upm = self.face.upem
        self.font.scale = (self.upm, self.upm)
        self.features, self.prefix, self.fallback = features, prefix, fallback
        self._outlines: dict[int, str] = {}

    def has(self, ch: str) -> bool:
        return self.font.get_nominal_glyph(ord(ch)) is not None

    def shape(self, s: str):
        buf = hb.Buffer()
        buf.add_str(s)
        buf.guess_segment_properties()
        hb.shape(self.font, buf, self.features)
        return [(i.codepoint, p.x_advance, p.x_offset, p.y_offset) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    def outline(self, gid: int) -> str:
        if gid not in self._outlines:
            pen = PathPen()
            self.font.draw_glyph_with_pen(gid, pen)
            self._outlines[gid] = pen.d()
        return self._outlines[gid]


F: dict[str, Font] = {}


def load_fonts():
    FONT_DIR.mkdir(exist_ok=True)
    for name, url in FONT_URLS.items():
        path = FONT_DIR / name
        if not path.exists():
            print(f"downloading {name}")
            urllib.request.urlretrieve(url, path)
    for key in FONT_SPECS:
        F[key] = Font(key)


# ---------------------------------------------------------------------------
# SVG document
# ---------------------------------------------------------------------------

STYLE = (
    "svg{--paper:#f1ede4;--ink:#141414;--soft:#716f6b;--rule:#c5c2ba;--accent:#e8402a}"
    "@media (prefers-color-scheme:dark){svg{--paper:#141414;--ink:#f1ede4;--soft:#94928d;--rule:#403f3e}}"
    ".bg,.p{fill:var(--paper)}.i{fill:var(--ink)}.s{fill:var(--soft)}.a{fill:var(--accent)}"
    ".ln{fill:none;stroke:var(--ink)}.lr{fill:none;stroke:var(--rule)}"
    ".ls{fill:none;stroke:var(--soft)}.la{fill:none;stroke:var(--accent)}"
    "@keyframes pulse{from{opacity:.6;transform:scale(1)}to{opacity:0;transform:scale(3.2)}}"
    ".pulse{opacity:0;transform-box:fill-box;transform-origin:center;animation:pulse 2.4s ease-out 2s infinite}"
    "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
)


class Svg:
    def __init__(self, w: int, h: int, label: str):
        self.w, self.h, self.alt = w, h, label
        self.defs: dict[str, str] = {}
        self.extra_defs: list[str] = []
        self.out: list[str] = []

    def add(self, s: str):
        self.out.append(s)

    def path(self, d: str, cls: str = "ln", width: float = 1, attrs: str = ""):
        self.add(f'<path class="{cls}" stroke-width="{fmt(width)}" d="{d}"{attrs}/>')

    # -- text -------------------------------------------------------------

    @staticmethod
    def runs(s: str, key: str):
        """Split text into runs of the font that has the glyphs, falling back for CJK."""
        out, cur, buf = [], None, ""
        for ch in s:
            k = key if F[key].has(ch) or not F[F[key].fallback].has(ch) else F[key].fallback
            if k != cur and buf:
                out.append((cur, buf))
                buf = ""
            cur, buf = k, buf + ch
        if buf:
            out.append((cur, buf))
        return out

    def measure(self, s: str, key: str, size: float, track: float = 0) -> float:
        width, n = 0.0, 0
        for k, part in self.runs(s, key):
            for _, adv, _, _ in F[k].shape(part):
                width += adv * size / F[k].upm
                n += 1
        return width + track * size * max(n - 1, 0)

    def text(self, s, x, y, key="mono", size=12.0, cls="i", anchor="start", track=0.0, attrs="") -> float:
        width = self.measure(s, key, size, track)
        x -= {"start": 0, "middle": width / 2, "end": width}[anchor]
        parts, pen = [f'<g class="{cls}"{attrs}>'], x
        for k, part in self.runs(s, key):
            f = F[k]
            scale, u, uses = size / f.upm, 0.0, []
            for gid, adv, xo, yo in f.shape(part):
                if f.outline(gid):
                    ref = f"{f.prefix}{gid}"
                    self.defs[ref] = f.outline(gid)
                    y_attr = f' y="{yo}"' if yo else ""
                    uses.append(f'<use xlink:href="#{ref}" x="{fmt(u + xo, 1)}"{y_attr}/>')
                u += adv + track * f.upm
            if uses:
                parts.append(
                    f'<g transform="translate({fmt(pen)} {fmt(y)}) scale({fmt(scale, 5)} {fmt(-scale, 5)})">'
                    + "".join(uses)
                    + "</g>"
                )
            pen += u * scale
        parts.append("</g>")
        self.add("".join(parts))
        return width

    def label(self, s, x, y, cls="s", anchor="start", size=10.5):
        """Small spaced caps, like the sheet labels on qwq.my."""
        return self.text(s.upper(), x, y, "mono", size, cls, anchor, track=0.12)

    def render(self) -> str:
        defs = "".join(f'<path id="{k}" d="{d}"/>' for k, d in self.defs.items()) + "".join(self.extra_defs)
        label = escape(self.alt)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{label}">\n'
            f"<!-- Generated by assets/build.py. Fonts: Archivo, JetBrains Mono, Noto Sans SC (SIL OFL 1.1). -->\n"
            f"<title>{label}</title>\n<style>{STYLE}</style>\n<defs>{defs}</defs>\n"
            + "\n".join(self.out)
            + "\n</svg>\n"
        )


# ---------------------------------------------------------------------------
# Drawing parts
# ---------------------------------------------------------------------------

OUTER, GUTTER = 6, 16
INNER = OUTER + GUTTER
BAR = 34  # height of the strip along the top of each sheet


def frame(svg: Svg, cols: int, rows: int):
    """Trimmed sheet with a zoned border and centring marks."""
    w, h, o, i = svg.w, svg.h, OUTER, INNER
    svg.add(f'<rect class="bg" width="{w}" height="{h}"/>')
    svg.add(f'<rect class="ln" stroke-width="1" x="{o}" y="{o}" width="{w - 2 * o}" height="{h - 2 * o}"/>')
    svg.add(f'<rect class="ln" stroke-width="1.5" x="{i}" y="{i}" width="{w - 2 * i}" height="{h - 2 * i}"/>')
    d = []
    cw = (w - 2 * i) / cols
    for c in range(cols):
        x = i + cw * c
        if c:
            d.append(f"M{fmt(x)} {o}V{i}M{fmt(x)} {h - i}V{h - o}")
        for y in (o + GUTTER / 2 + 3.2, h - o - GUTTER / 2 + 3.2):
            svg.text(str(c + 1), x + cw / 2, y, "mono", 9, "s", "middle")
    rh = (h - 2 * i) / rows
    for r in range(rows):
        y = i + rh * r
        if r:
            d.append(f"M{o} {fmt(y)}H{i}M{w - i} {fmt(y)}H{w - o}")
        for x in (o + GUTTER / 2, w - o - GUTTER / 2):
            svg.text("ABCDEFGH"[r], x, y + rh / 2 + 3.2, "mono", 9, "s", "middle")
    svg.path("".join(d))
    svg.path(f"M{w / 2} 0V{i}M{w / 2} {h}V{h - i}M0 {h / 2}H{i}M{w} {h / 2}H{w - i}", width=1.5)


def top_bar(svg: Svg, number: str, title: str, right: str):
    svg.path(f"M{INNER} {INNER + BAR}H{svg.w - INNER}")
    svg.text(number, INNER + 12, INNER + 22, "mono", 12, "a")
    svg.text(title, INNER + 38, INNER + 24.5, "display", 20)
    svg.label(right, svg.w - INNER - 12, INNER + 21.5, anchor="end")


def logo(svg: Svg, x: float, y: float, scale: float):
    """The QwQ mark from qwq.my: two Q-eyes and a red w."""
    eyes = "".join(
        f'<circle class="ln" cx="{cx}" cy="24" r="17" stroke-width="6"/>'
        f'<path class="ln" d="M{cx + 11} 36q4 7 10 10" stroke-width="6"/>'
        f'<circle class="i" cx="{cx}" cy="24" r="7.5"/>'
        f'<circle class="p" cx="{fmt(cx - 2.6)}" cy="21.2" r="2.2"/>'
        for cx in (24, 96)
    )
    svg.add(
        f'<g transform="translate({fmt(x)} {fmt(y)}) scale({fmt(scale, 3)})" stroke-linecap="round" stroke-linejoin="round">'
        f'{eyes}<path class="la" d="M49 23Q53.5 32 60 25.5Q66.5 32 71 23" stroke-width="5"/></g>'
    )


def snowball(svg: Svg, cx: float, cy: float, r: float):
    """A dimensioned circle: the snowball, Ø233."""
    svg.extra_defs.append(
        f'<mask id="crescent"><circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff"/>'
        f'<circle cx="{cx - 10}" cy="{cy - 10}" r="{r - 1}" fill="#000"/></mask>'
    )
    hatch = "".join(f"M{fmt(cx - r + k)} {fmt(cy + r)}L{fmt(cx + r + k)} {fmt(cy - r)}" for k in range(-2 * int(r), 2 * int(r), 6))
    svg.path(hatch, "lr", 1, ' mask="url(#crescent)"')
    ext = r + 13
    svg.path(f"M{cx - ext} {cy}H{cx + ext}M{cx} {cy - ext}V{cy + ext}", "ls", 0.8, ' stroke-dasharray="11 3 2 3"')
    svg.add(f'<circle class="ln" stroke-width="1.8" cx="{cx}" cy="{cy}" r="{r}"/>')
    # Highlight, as on the logo's pupils.
    hr = r * 0.72
    svg.path(
        f"M{fmt(cx - hr * 0.94)} {fmt(cy - hr * 0.34)}A{fmt(hr)} {fmt(hr)} 0 0 1 {fmt(cx - hr * 0.5)} {fmt(cy - hr * 0.87)}",
        "ln", 2, ' stroke-linecap="round"',
    )
    # Diameter callout: arrow on the rim, leader out to the lower left, shoulder, value.
    k = 0.7071
    tip = (cx - r * k, cy + r * k)
    knee = (cx - (r + 24) * k, cy + (r + 24) * k)
    end_x = knee[0] - 62
    a, b = 9, 3.2  # arrow length and half-width
    base = (tip[0] - a * k, tip[1] + a * k)
    arrow = f"M{fmt(tip[0])} {fmt(tip[1])}L{fmt(base[0] - b * k)} {fmt(base[1] - b * k)}L{fmt(base[0] + b * k)} {fmt(base[1] + b * k)}Z"
    svg.add(f'<path class="a" d="{arrow}"/>')
    svg.path(f"M{fmt(base[0])} {fmt(base[1])}L{fmt(knee[0])} {fmt(knee[1])}H{fmt(end_x)}", "la", 1.2)
    svg.text("Ø233", end_x + 2, knee[1] - 5, "monob", 14, "a")


def title_block(svg: Svg, D: dict, sheet: int, title: str):
    L = D["tb"]
    w, rows = 340, (30, 30, 22)
    x0, x1 = svg.w - INNER - w, svg.w - INNER
    y0 = svg.h - INNER - sum(rows)
    ya, yb = y0 + rows[0], y0 + rows[0] + rows[1]
    c1, c2 = x0 + 138, x0 + 276
    svg.add(f'<rect class="bg" x="{x0}" y="{y0}" width="{w}" height="{sum(rows)}"/>')
    svg.path(f"M{x0} {svg.h - INNER}V{y0}H{x1}M{x0} {ya}H{x1}M{x0} {yb}H{x1}M{c1} {y0}V{ya}M{c2} {y0}V{yb}")
    for text, x in ((L["drawn"], x0), (L["dwg"], c1), (L["rev"], c2)):
        svg.label(text, x + 8, y0 + 12, size=9)
    svg.text("Snowball_233", x0 + 8, y0 + 25)
    svg.text(f"QWQ-GH{sheet:02d}", c1 + 8, y0 + 25)
    svg.text("A", c2 + 8, y0 + 25, cls="a")
    svg.text(f"{sheet:02d}", x0 + 8, ya + 20, cls="a")
    svg.text(title, x0 + 32, ya + 22, "display", 20)
    svg.label(L["scale"], c2 + 8, ya + 12, size=9)
    svg.text("1:1", c2 + 8, ya + 25)
    svg.label(f"{L['sheet']} {sheet:02d}/{SHEETS:02d}", x0 + 8, yb + 15, size=9)
    bx0, bx1 = x0 + 104, x1 - 50
    svg.add(f'<rect class="ln" stroke-width="1" x="{bx0}" y="{yb + 8}" width="{bx1 - bx0}" height="6"/>')
    svg.add(f'<rect class="a" x="{bx0}" y="{yb + 8}" width="{fmt((bx1 - bx0) * sheet / SHEETS)}" height="6"/>')
    svg.text(f"{round(sheet / SHEETS * 100):03d}%", x1 - 8, yb + 15.5, size=11, anchor="end")


# ---------------------------------------------------------------------------
# Sheets
# ---------------------------------------------------------------------------


def header(lang: str) -> Svg:
    D = DATA[lang]
    status = "".join(s for s, _ in D["status"])
    svg = Svg(960, 300, f"Snowball_233 · {D['role']} · {status}")
    frame(svg, 8, 4)
    svg.path(f"M{INNER} {INNER + BAR}H{svg.w - INNER}")
    logo(svg, INNER + 12, INNER + 6, 0.42)
    svg.label("qwq.my", INNER + 74, INNER + 21.5)
    svg.label(D["role"], svg.w - INNER - 12, INNER + 21.5, anchor="end")

    x = 52
    svg.text(D["handle"], x, 100, "mono", 13, "s")
    svg.text("Snowball_233", x - 3, 170, "cond", 80)
    for part, cls in D["status"]:
        x += svg.text(part, x, 210, "display", 18, cls)
    svg.text(D["quote"], 52, 258, "mono", 12, "s")

    snowball(svg, 770, 120, 46)
    title_block(svg, D, 1, D["titles"][0])
    return svg


def timeline(lang: str) -> Svg:
    D = DATA[lang]
    entries = D["timeline"]
    svg = Svg(960, 300, "; ".join(f"{d} {t}, {n}" for d, t, n in entries))
    frame(svg, 8, 4)
    top_bar(svg, "02", D["titles"][1], f"{D['nts']} · {D['tb']['sheet']} 02/{SHEETS:02d}")

    ay, step = 172, 120
    xs = [120 + step * i for i in range(len(entries))]
    svg.path(f"M40 {ay}H{xs[-1]}", "ln", 1.5)
    svg.path(f"M{xs[-1]} {ay}H{xs[-1] + 66}", "ln", 1.5, ' stroke-dasharray="4 4"')
    end = xs[-1] + 76
    svg.add(f'<path class="i" d="M{end} {ay}l-10 -4v8z"/>')
    # Break in the axis: nothing much happened between 2021 and 2024.
    bx = (xs[0] + xs[1]) / 2
    svg.add(f'<rect class="bg" x="{bx - 5}" y="{ay - 3}" width="10" height="6"/>')
    svg.path(f"M{bx - 8} {ay + 8}L{bx - 2} {ay - 8}M{bx + 2} {ay + 8}L{bx + 8} {ay - 8}", "ln", 1.2)

    for i, (date, title, note) in enumerate(entries):
        x, up, now = xs[i], i % 2 == 0, i == len(entries) - 1
        if up:
            svg.path(f"M{x} {ay - 8}V140")
            ys = (84, 108, 128)
        else:
            svg.path(f"M{x} {ay + 8}V204")
            ys = (224, 248, 268)
        if now:
            svg.add(f'<circle class="a" cx="{x}" cy="{ay}" r="5.5"/>')
            svg.add(f'<circle class="la pulse" stroke-width="1.5" cx="{x}" cy="{ay}" r="5.5"/>')
        else:
            svg.add(f'<circle class="bg" cx="{x}" cy="{ay}" r="4.5"/><circle class="ln" stroke-width="1.5" cx="{x}" cy="{ay}" r="4.5"/>')
        svg.text(date, x, ys[0], "mono", 12, "a", "middle", 0.06)
        svg.text(title, x, ys[1], "display", 18, "i", "middle")
        svg.text(note, x, ys[2], "mono", 12, "s", "middle")
        widest = max(svg.measure(title, "display", 18), svg.measure(note, "mono", 12))
        if widest > 2 * step - 16:
            print(f"warning: timeline label too wide ({widest:.0f}px): {title} / {note}")
    return svg


def toolbox(lang: str) -> Svg:
    D = DATA[lang]
    rows = D["skills"]
    top, head, rh = INNER + BAR, 24, 32
    h = top + head + rh * len(rows) + INNER
    svg = Svg(960, h, "; ".join(f"{g}: {', '.join(items)}" for g, items in rows))
    frame(svg, 8, 6)
    top_bar(svg, "03", D["titles"][2], f"{D['bom']} · {D['tb']['sheet']} 03/{SHEETS:02d}")

    cols = (INNER + 58, INNER + 198, svg.w - INNER - 58)
    x_no, x_group, x_parts, x_qty = INNER + 14, cols[0] + 12, cols[1] + 12, svg.w - INNER - 14
    no, group, parts, qty = D["cols"]
    svg.label(no, x_no, top + 16)
    svg.label(group, x_group, top + 16)
    svg.label(parts, x_parts, top + 16)
    svg.label(qty, x_qty, top + 16, anchor="end")
    body = top + head
    svg.path(f"M{INNER} {body}H{svg.w - INNER}")
    svg.path("".join(f"M{c} {top}V{svg.h - INNER}" for c in cols), "lr")

    for r, (name, items) in enumerate(rows):
        y0 = body + rh * r
        hot = r == 0  # the first row is drawn inked in, like the active group on qwq.my
        if r:
            svg.path(f"M{INNER} {y0}H{svg.w - INNER}", "lr")
        if hot:
            svg.add(f'<rect class="a" x="{INNER + 0.75}" y="{y0}" width="3" height="{rh}"/>')
        svg.text(f"{r + 1:02d}", x_no, y0 + 21, cls="a" if hot else "s")
        svg.label(name, x_group, y0 + 20.5, cls="a" if hot else "i", size=11)
        x = x_parts
        for item in items:
            cw = svg.measure(item, "mono", 12) + 16
            if hot:
                svg.add(f'<rect class="i" x="{fmt(x)}" y="{y0 + 6}" width="{fmt(cw)}" height="20"/>')
            else:
                svg.add(f'<rect class="lr" stroke-width="1" x="{fmt(x)}" y="{y0 + 6}" width="{fmt(cw)}" height="20"/>')
            svg.text(item, x + 8, y0 + 20.5, cls="p" if hot else "i")
            x += cw + 6
        if x > cols[2]:
            print(f"warning: row {name!r} overflows the parts column")
        svg.text(f"{len(items):02d}", x_qty, y0 + 21, cls="s", anchor="end")
    return svg


def main():
    load_fonts()
    for lang in DATA:
        for name, draw in (("header", header), ("timeline", timeline), ("toolbox", toolbox)):
            path = HERE / f"{name}.{lang}.svg"
            path.write_text(draw(lang).render(), encoding="utf-8")
            print(f"wrote {path.relative_to(HERE.parent)} ({path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
