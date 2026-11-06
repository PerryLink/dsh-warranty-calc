#!/usr/bin/env python3
"""Generate README image assets for dsh-warranty-calc (docs/assets/).

Outputs (idempotent overwrite):
  dsh-warranty-calc-hero-{zh,en}-{light,dark}.webp   1440x576 raster banner
  dsh-warranty-calc-flow-v5-{light,dark}.svg         1100x660 structure diagram

The hero shows a real sample claim row: a blank claim number / part name, the
sale-claim-warranty-end dates on one timeline, the mileage bar against the cap
the ledger states, and 2 x 180 = 360 against a declared 400. Running that
material through the tool yields exactly two warn issues (WC-001, WC-005) and
one skipped rule (WC-007, whose claim number column is blank), so the summary
bar is observed output, not decoration.

The structure diagram is hand-written SVG: one claim row fans out into the four
field groups the seven rules actually read (identity, time, mileage, amount),
and the rule outcomes merge into two channels, issues[] and skipped[].
Text inside the SVG is short Chinese labels plus canonical field tokens, so all
five README languages share the same pair.

Run once:  python scripts/gen-readme-assets.py
Requires:  Pillow (pip install pillow)
"""
from __future__ import annotations

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")

FONT_CANDIDATES = [
    (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc"),
    (r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simhei.ttf"),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
     "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    ("/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/PingFang.ttc"),
]
CJK_REGULAR = next((r for r, _ in FONT_CANDIDATES if os.path.exists(r)), None)
CJK_BOLD = next((b for r, b in FONT_CANDIDATES
                 if os.path.exists(r) and os.path.exists(b)), None)
if CJK_REGULAR is None or CJK_BOLD is None:
    sys.exit("FATAL: no CJK font found; refusing to render Chinese as tofu boxes.")

MONO_PATH = r"C:\Windows\Fonts\consola.ttf"
MONO_BOLD_PATH = r"C:\Windows\Fonts\consolab.ttf"
EN_PATH = r"C:\Windows\Fonts\segoeui.ttf"
EN_BOLD_PATH = r"C:\Windows\Fonts\segoeuib.ttf"
for path in (MONO_PATH, MONO_BOLD_PATH, EN_PATH, EN_BOLD_PATH):
    if not os.path.exists(path):
        sys.exit(f"FATAL: required font missing: {path}")

_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    key = (kind, int(size))
    if key not in _CACHE:
        path = {
            "cjk": CJK_REGULAR,
            "cjk_bold": CJK_BOLD,
            "mono": MONO_PATH,
            "mono_bold": MONO_BOLD_PATH,
            "en": EN_PATH,
            "en_bold": EN_BOLD_PATH,
        }[kind]
        _CACHE[key] = ImageFont.truetype(path, int(size))
    return _CACHE[key]


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
THEMES = {
    "light": {
        "bg1": "#f9f6fd", "bg2": "#e4eaf8",
        "panel": "#ffffff", "panel_border": "#e6e2f2",
        "ticket": "#faf8ff", "ticket_border": "#ebe6f6",
        "card": "#fbfaff", "card_border": "#e8e4f3",
        "text": "#1f2430", "sub": "#596176", "faint": "#8a90a3",
        "family": "#4B67B4", "family_dark": "#33477f",
        "family_soft": "#eef1fb", "family_line": "#cfd7ef",
        "warn": "#B45309", "warn_soft": "#fdf2e3", "warn_line": "#f2d3ad",
        "green": "#15803d", "green_soft": "#eaf7ef",
        "rule": "#e3dfef", "shadow": (40, 36, 70, 40),
        "dot": "#d9d6e7",
    },
    "dark": {
        "bg1": "#131a2a", "bg2": "#0c1016",
        "panel": "#151c2c", "panel_border": "#2a3450",
        "ticket": "#1a2336", "ticket_border": "#2b3550",
        "card": "#182033", "card_border": "#2a3450",
        "text": "#eef2fb", "sub": "#9aa7c2", "faint": "#77839d",
        "family": "#8496f5", "family_dark": "#b9c4ff",
        "family_soft": "#202a44", "family_line": "#354468",
        "warn": "#fbbf24", "warn_soft": "#2d2410", "warn_line": "#5a4718",
        "green": "#4ade80", "green_soft": "#102a1c",
        "rule": "#2a3450", "shadow": (0, 0, 0, 120),
        "dot": "#26314a",
    },
}


def hx(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def gradient(width: int, height: int, c1: str, c2: str) -> Image.Image:
    a, b = hx(c1), hx(c2)
    img = Image.new("RGB", (width, height))
    d = ImageDraw.Draw(img)
    for y in range(height):
        t = y / max(1, height - 1)
        d.line((0, y, width, y), fill=tuple(round(a[i] + (b[i] - a[i]) * t)
                                            for i in range(3)))
    return img.convert("RGBA")


def glow(base: Image.Image, cx: int, cy: int, rx: int, ry: int,
         color: str, alpha: int) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry),
              fill=hx(color) + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(70))
    base.alpha_composite(layer)


def shadowed(base: Image.Image, box: tuple[int, int, int, int], radius: int,
             theme: dict, blur: int = 22, offset: int = 12,
             fill: str | None = None, border: str | None = None) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((box[0], box[1] + offset, box[2], box[3] + offset),
                        radius=radius, fill=theme["shadow"])
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)
    ImageDraw.Draw(base).rounded_rectangle(
        box, radius=radius, fill=fill or theme["panel"],
        outline=border or theme["panel_border"], width=1)


def card(base: Image.Image, box: tuple[int, int, int, int], radius: int,
         theme: dict, fill: str | None = None,
         border: str | None = None, width: int = 1) -> None:
    ImageDraw.Draw(base).rounded_rectangle(
        box, radius=radius, fill=fill or theme["card"],
        outline=border or theme["card_border"], width=width)


def dashed_hline(d: ImageDraw.ImageDraw, x1: int, x2: int, y: int,
                 color: str, width: int = 2, dash: int = 7,
                 gap: int = 6) -> None:
    x = x1
    while x < x2:
        d.line((x, y, min(x + dash, x2), y), fill=color, width=width)
        x += dash + gap


def fit_font(d: ImageDraw.ImageDraw, text: str, kind: str, max_width: int,
             max_size: int, min_size: int) -> ImageFont.FreeTypeFont:
    for size in range(max_size, min_size - 1, -1):
        f = font(kind, size)
        if d.textlength(text, font=f) <= max_width:
            return f
    return font(kind, min_size)


def text(d: ImageDraw.ImageDraw, xy: tuple[int, int], value: str,
         f: ImageFont.FreeTypeFont, color: str,
         anchor: str = "la") -> None:
    d.text(xy, value, font=f, fill=color, anchor=anchor)


def pill(d: ImageDraw.ImageDraw, box: tuple[int, int, int, int], value: str,
         f: ImageFont.FreeTypeFont, fg: str, bg: str) -> None:
    d.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=bg)
    d.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 1), value,
           font=f, fill=fg, anchor="mm")


# ---------------------------------------------------------------------------
# Hero copy (zh + en only; the other READMEs use the English hero)
# ---------------------------------------------------------------------------
HERO = {
    "zh": {
        "kicker_a": "DSH 插件",
        "kicker_b": " · 质保索赔台账核对",
        "title": "dsh-warranty-calc",
        "value": ["七条规则，逐行核对期限与金额",
                  "差异落到行号、栏名与修法"],
        "sub": ["时间、里程、金额各自核对；只列材料内部能指认的差异。",
                "不判受理、不判合规、不认定责任。"],
        "meta": "WC-001…WC-007 · 规则即数据 · skipped 逐条说明",
        "footer": "Apache-2.0 · PerryLink DSH plugin family",
        "panel_title": "索赔台账 · 一行样例",
        "badge": "只读原件",
        "panel_sub": "某某服务站 · 2026 版质保政策 · rows[1]",
        "ticket_title": "索赔单 · 第 1 行",
        "ticket_note": "读取层保留台账自己的栏名",
        "rows": [("索赔单号", "—（空）", True),
                 ("配件名称", "—（空）", True),
                 ("销售日期", "2024-03-10", False),
                 ("索赔日期", "2026-03-05", False),
                 ("索赔时里程", "48,600", False),
                 ("索赔金额", "400", True)],
        "time_title": "时间边界",
        "time_tag": "WC-002 · WC-006",
        "time_caps": ["销售", "索赔", "截止"],
        "dates": ["2024-03-10", "2026-03-05", "2027-03-09"],
        "time_note": "截止日来自台账，不按月数推算",
        "mileage_title": "里程边界",
        "mileage_tag": "WC-003 · WC-004",
        "mileage_left": "48,600",
        "mileage_right": "上限 100,000",
        "mileage_note": "上限取自台账，不内置任何数字",
        "amount_title": "金额算式",
        "amount_tag": "WC-005 · 容差 0.01",
        "equation": "2 × 180 = 360",
        "declared": "填报 400",
        "amount_note": "差 40，只做算术核对",
        "summary_left": "issues[] 2 条差异 · skipped[] 1 条未执行",
        "summary_right": "结论留给审核人",
    },
    "en": {
        "kicker_a": "DSH PLUGIN",
        "kicker_b": " · WARRANTY CLAIM LEDGER CHECK",
        "title": "dsh-warranty-calc",
        "value": ["Seven rules, one pass over the ledger",
                  "Every difference pinned to row and column"],
        "sub": ["Time, mileage and amount are checked as separate lines.",
                "No ruling on acceptance, compliance or liability."],
        "meta": "WC-001…WC-007 · rules as data · every skip explained",
        "footer": "Apache-2.0 · PerryLink DSH plugin family",
        "panel_title": "Claim ledger · one sample row",
        "badge": "read-only",
        "panel_sub": "Dealer · 2026 policy · rows[1]",
        "ticket_title": "Claim · row 1",
        "ticket_note": "reader keeps your column names",
        "rows": [("claimNo", "— (blank)", True),
                 ("partName", "— (blank)", True),
                 ("saleDate", "2024-03-10", False),
                 ("claimDate", "2026-03-05", False),
                 ("mileageAtClaim", "48,600", False),
                 ("claimAmount", "400", True)],
        "time_title": "Time boundary",
        "time_tag": "WC-002 · WC-006",
        "time_caps": ["sale", "claim", "end"],
        "dates": ["2024-03-10", "2026-03-05", "2027-03-09"],
        "time_note": "end date comes from the ledger, never derived",
        "mileage_title": "Mileage boundary",
        "mileage_tag": "WC-003 · WC-004",
        "mileage_left": "48,600",
        "mileage_right": "cap 100,000",
        "mileage_note": "cap from the ledger; no built-in number",
        "amount_title": "Amount equation",
        "amount_tag": "WC-005 · tolerance 0.01",
        "equation": "2 × 180 = 360",
        "declared": "declared 400",
        "amount_note": "off by 40; arithmetic only",
        "summary_left": "issues[] 2 differences · skipped[] 1 not run",
        "summary_right": "verdict with the reviewer",
    },
}


def draw_hero(lang: str, skin: str) -> None:
    theme = THEMES[skin]
    copy = HERO[lang]
    width, height = 1440, 576
    img = gradient(width, height, theme["bg1"], theme["bg2"])
    glow(img, 1260, 80, 290, 220, theme["family"], 26 if skin == "light" else 40)
    glow(img, 760, 560, 260, 180, theme["family"], 18 if skin == "light" else 32)
    d = ImageDraw.Draw(img)

    # ---- left column -----------------------------------------------------
    # Warranty-sheet badge, so the left column is not just type.
    bx, by = 84, 62
    d.rounded_rectangle((bx, by, bx + 44, by + 44), radius=13,
                        fill=theme["family"])
    d.line((bx + 13, by + 14, bx + 31, by + 14), fill="#ffffff", width=2)
    d.line((bx + 13, by + 22, bx + 31, by + 22), fill="#ffffff", width=2)
    d.line((bx + 13, by + 30, bx + 24, by + 30), fill="#ffffff", width=2)
    d.arc((bx + 25, by + 25, bx + 37, by + 37), 200, 340,
          fill="#ffffff", width=2)
    d.line((bx + 29, by + 33, bx + 31, by + 35), fill="#ffffff", width=2)
    d.line((bx + 31, by + 35, bx + 35, by + 30), fill="#ffffff", width=2)

    kf_a = font("cjk_bold" if lang == "zh" else "en_bold", 17)
    kf_b = font("cjk" if lang == "zh" else "en", 17)
    x = bx + 58
    d.text((x, by + 22), copy["kicker_a"], font=kf_a,
           fill=theme["family"], anchor="lm")
    x += d.textlength(copy["kicker_a"], font=kf_a)
    d.text((x, by + 22), copy["kicker_b"], font=kf_b,
           fill=theme["sub"], anchor="lm")

    title_font = fit_font(d, copy["title"], "en_bold", 580, 58, 48)
    text(d, (84, 166), copy["title"], title_font, theme["text"], "ls")

    value_kind = "cjk_bold" if lang == "zh" else "en_bold"
    value_size = 34 if lang == "zh" else 31
    for i, line in enumerate(copy["value"]):
        f = fit_font(d, line, value_kind, 580, value_size, 28)
        text(d, (84, 246 + i * 48), line, f, theme["text"], "ls")

    sub_kind = "cjk" if lang == "zh" else "en"
    for i, line in enumerate(copy["sub"]):
        f = fit_font(d, line, sub_kind, 580, 18, 15)
        text(d, (84, 356 + i * 29), line, f, theme["sub"], "ls")

    meta_f = fit_font(d, copy["meta"], "cjk" if lang == "zh" else "en",
                      580, 15, 13)
    text(d, (84, 446), copy["meta"], meta_f, theme["family"], "ls")
    footer_f = fit_font(d, copy["footer"], "en", 580, 14, 12)
    text(d, (84, 512), copy["footer"], footer_f, theme["faint"], "ls")

    # ---- right panel -----------------------------------------------------
    panel = (700, 48, 1364, 528)
    shadowed(img, panel, 22, theme, blur=26, offset=14,
             fill=theme["panel"], border=theme["panel_border"])
    d = ImageDraw.Draw(img)

    # header
    title_f = font("cjk_bold" if lang == "zh" else "en_bold", 18)
    text(d, (724, 84), copy["panel_title"], title_f, theme["text"], "ls")
    badge_f = font("cjk" if lang == "zh" else "en", 12)
    bw = int(d.textlength(copy["badge"], font=badge_f)) + 24
    pill(d, (1340 - bw, 70, 1340, 96), copy["badge"], badge_f,
         theme["family"], theme["family_soft"])
    sub_f = fit_font(d, copy["panel_sub"],
                     "cjk" if lang == "zh" else "en", 600, 13, 11)
    text(d, (724, 112), copy["panel_sub"], sub_f, theme["sub"], "ls")
    d.line((724, 130, 1340, 130), fill=theme["rule"], width=1)

    # ticket
    tbox = (724, 144, 976, 486)
    shadowed(img, tbox, 16, theme, blur=15, offset=7,
             fill=theme["ticket"], border=theme["ticket_border"])
    d = ImageDraw.Draw(img)
    ttitle = font("cjk_bold" if lang == "zh" else "en_bold", 12)
    text(d, (740, 168), copy["ticket_title"], ttitle, theme["family"], "ls")
    d.line((740, 178, 960, 178), fill=theme["ticket_border"], width=1)
    label_kind = "cjk" if lang == "zh" else "mono"
    label_f = font(label_kind, 13)
    value_f = font("mono", 15)
    warn_value_f = font("cjk" if lang == "zh" else "mono", 14)
    for i, (label, value, warn) in enumerate(copy["rows"]):
        y = 200 + i * 46
        text(d, (740, y), label, label_f, theme["sub"], "ls")
        if warn:
            text(d, (960, y), value, warn_value_f, theme["warn"], "rs")
            dashed_hline(d, 828, 960, y + 8, theme["warn_line"],
                         width=1, dash=4, gap=4)
            d.ellipse((966, y - 9, 972, y - 3), fill=theme["warn"])
        else:
            text(d, (960, y), value, value_f, theme["text"], "rs")
    note_f = fit_font(d, copy["ticket_note"],
                      "cjk" if lang == "zh" else "en", 220, 11, 11)
    text(d, (740, 466), copy["ticket_note"], note_f, theme["faint"], "ls")

    # time boundary card
    time_box = (992, 144, 1340, 268)
    card(img, time_box, 14, theme, fill=theme["card"])
    d = ImageDraw.Draw(img)
    card_title_f = font("cjk_bold" if lang == "zh" else "en_bold", 13)
    tag_f = font("cjk" if lang == "zh" else "mono", 11)
    text(d, (1008, 166), copy["time_title"], card_title_f, theme["text"], "ls")
    text(d, (1324, 166), copy["time_tag"], tag_f, theme["faint"], "rs")
    cap_f = font("cjk" if lang == "zh" else "en", 11)
    for label, xx, anchor in ((copy["time_caps"][0], 1012, "ls"),
                              (copy["time_caps"][1], 1210, "ms"),
                              (copy["time_caps"][2], 1320, "rs")):
        text(d, (xx, 190), label, cap_f, theme["faint"], anchor)
    # timeline
    d.line((1012, 212, 1320, 212), fill=theme["family_line"], width=4)
    d.line((1012, 212, 1320, 212), fill=theme["family"], width=2)
    d.line((1320, 202, 1320, 222), fill=theme["family"], width=3)
    d.ellipse((1007, 207, 1017, 217), fill=theme["card"],
              outline=theme["family"], width=2)
    d.ellipse((1202, 205, 1218, 221), fill=theme["family"])
    date_f = font("mono", 11)
    text(d, (1012, 238), copy["dates"][0], date_f, theme["sub"], "ls")
    text(d, (1210, 238), copy["dates"][1], date_f, theme["text"], "ms")
    text(d, (1320, 238), copy["dates"][2], date_f, theme["sub"], "rs")
    time_note_f = fit_font(d, copy["time_note"],
                           "cjk" if lang == "zh" else "en", 310, 11, 11)
    text(d, (1008, 260), copy["time_note"], time_note_f, theme["faint"], "ls")

    # mileage boundary card
    mile_box = (992, 280, 1340, 380)
    card(img, mile_box, 14, theme, fill=theme["card"])
    d = ImageDraw.Draw(img)
    text(d, (1008, 304), copy["mileage_title"], card_title_f,
         theme["text"], "ls")
    text(d, (1324, 304), copy["mileage_tag"], tag_f, theme["faint"], "rs")
    track_x0, track_x1, track_y = 1012, 1320, 326
    d.rounded_rectangle((track_x0, track_y, track_x1, track_y + 10),
                        radius=5, fill=theme["family_soft"])
    fill_x1 = track_x0 + int((track_x1 - track_x0) * 0.486)
    d.rounded_rectangle((track_x0, track_y, fill_x1, track_y + 10),
                        radius=5, fill=theme["family"])
    d.line((track_x1, track_y - 6, track_x1, track_y + 16),
           fill=theme["family"], width=3)
    value12 = font("mono", 12)
    text(d, (1012, 352), copy["mileage_left"], value12, theme["text"], "ls")
    text(d, (1320, 352), copy["mileage_right"],
         font("cjk" if lang == "zh" else "en", 12), theme["sub"], "rs")
    mile_note_f = fit_font(d, copy["mileage_note"],
                           "cjk" if lang == "zh" else "en", 310, 11, 11)
    text(d, (1008, 372), copy["mileage_note"], mile_note_f,
         theme["faint"], "ls")

    # amount equation card
    amount_box = (992, 392, 1340, 486)
    card(img, amount_box, 14, theme, fill=theme["card"])
    d = ImageDraw.Draw(img)
    text(d, (1008, 416), copy["amount_title"], card_title_f,
         theme["text"], "ls")
    text(d, (1324, 416), copy["amount_tag"], tag_f, theme["faint"], "rs")
    eq_f = font("mono", 19)
    text(d, (1008, 448), copy["equation"], eq_f, theme["family_dark"], "ls")
    declared_f = font("cjk" if lang == "zh" else "en", 17)
    text(d, (1324, 448), copy["declared"], declared_f, theme["warn"], "rs")
    amount_note_f = fit_font(d, copy["amount_note"],
                             "cjk" if lang == "zh" else "en", 310, 11, 11)
    text(d, (1008, 472), copy["amount_note"], amount_note_f,
         theme["warn"], "ls")

    # summary bar
    bar = (724, 492, 1340, 520)
    d.rounded_rectangle(bar, radius=14, fill=theme["family_soft"])
    summary_f = fit_font(d, copy["summary_left"],
                         "cjk" if lang == "zh" else "en", 430, 13, 11)
    text(d, (740, 506), copy["summary_left"], summary_f,
         theme["family_dark"], "ls")
    right_f = fit_font(d, copy["summary_right"],
                       "cjk" if lang == "zh" else "en", 190, 13, 11)
    text(d, (1324, 506), copy["summary_right"], right_f,
         theme["text"], "rs")

    path = os.path.join(OUT, f"dsh-warranty-calc-hero-{lang}-{skin}.webp")
    img.convert("RGB").save(path, "WEBP", quality=92, method=6)
    print(f"wrote {os.path.basename(path)}")


# ---------------------------------------------------------------------------
# Structure diagram (hand-written SVG, 1100 x 660)
# ---------------------------------------------------------------------------
FLOW = {
    "light": {
        "bg_from": "#f9f6fd", "bg_to": "#e4eaf8",
        "panel": "#ffffff", "panel_soft": "#faf8ff",
        "card": "#ffffff", "border": "#dde1f0", "edge": "#e9e6f4",
        "text": "#1c2333", "sub": "#5b6478", "faint": "#8a93a8",
        "family": "#4B67B4", "family_soft": "#eef1fb",
        "family_line": "#cfd7ef",
        "warn": "#B45309", "warn_soft": "#fdf3e5", "warn_line": "#f0d3ac",
        "info": "#2f5f9e", "info_soft": "#eaf1fb",
        "green": "#15803d", "rail": "#c9cfe4", "dot": "#d9dcea",
        "shadow": "#2a2545", "shadow_op": "0.10",
        "track": "#e7ebf7",
    },
    "dark": {
        "bg_from": "#131a2a", "bg_to": "#0c1016",
        "panel": "#151c2c", "panel_soft": "#1a2336",
        "card": "#182033", "border": "#2a3450", "edge": "#2b3550",
        "text": "#eef2fb", "sub": "#9aa7c2", "faint": "#77839d",
        "family": "#8496f5", "family_soft": "#202a44",
        "family_line": "#354468",
        "warn": "#fbbf24", "warn_soft": "#2d2410", "warn_line": "#5a4718",
        "info": "#93c5fd", "info_soft": "#16243c",
        "green": "#4ade80", "rail": "#33405e", "dot": "#26314a",
        "shadow": "#000000", "shadow_op": "0.50",
        "track": "#22304b",
    },
}
SANS = ("Microsoft YaHei, PingFang SC, Noto Sans CJK SC, "
        "ui-sans-serif, system-ui, sans-serif")
MONO = "Consolas, ui-monospace, SFMono-Regular, Menlo, monospace"


class Svg:
    def __init__(self, skin: str) -> None:
        self.s = FLOW[skin]
        self.parts: list[str] = []

    def esc(self, value: str) -> str:
        return (value.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;"))

    def add(self, value: str) -> None:
        self.parts.append(value)

    def t(self, x: float, y: float, value: str, size: float,
          color: str = "text", family: str = SANS, weight: int = 400,
          anchor: str = "start", spacing: float | None = None,
          opacity: float | None = None) -> None:
        extra = f' letter-spacing="{spacing}"' if spacing else ""
        extra += f' opacity="{opacity}"' if opacity else ""
        self.add(
            f'<text x="{x:g}" y="{y:g}" fill="{self.s[color]}" '
            f'font-family="{family}" font-size="{size:g}" '
            f'font-weight="{weight}" text-anchor="{anchor}"{extra}>'
            f'{self.esc(value)}</text>')

    def rect(self, x: float, y: float, w: float, h: float, r: float = 14,
             fill: str = "card", stroke: str | None = "border",
             sw: float = 1.4, dash: str | None = None,
             opacity: float | None = None) -> None:
        stroke_attr = (f' stroke="{self.s[stroke]}" stroke-width="{sw:g}"'
                       if stroke else "")
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        op = f' opacity="{opacity}"' if opacity else ""
        self.add(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
                 f'rx="{r:g}" fill="{self.s[fill]}"{stroke_attr}'
                 f'{dash_attr}{op}/>')

    def line(self, x1: float, y1: float, x2: float, y2: float,
             color: str = "rail", sw: float = 1.5,
             dash: str | None = None) -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" '
                 f'stroke="{self.s[color]}" stroke-width="{sw:g}"'
                 f'{dash_attr} stroke-linecap="round"/>')

    def arrow(self, x1: float, y1: float, x2: float, y2: float,
              color: str = "family", sw: float = 2) -> None:
        if abs(y2 - y1) < 0.01:
            # Horizontal arrow: the head must point right, not up-right.
            self.add(
                f'<path d="M{x1:g} {y1:g} L{x2 - 7:g} {y2:g} '
                f'M{x2 - 13:g} {y2 - 5:g} L{x2 - 7:g} {y2:g} '
                f'L{x2 - 13:g} {y2 + 5:g}" fill="none" '
                f'stroke="{self.s[color]}" stroke-width="{sw:g}" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')
            return
        self.add(
            f'<path d="M{x1:g} {y1:g} L{x2:g} {y2 - 7:g} '
            f'M{x2 - 5:g} {y2 - 13:g} L{x2:g} {y2 - 7:g} '
            f'L{x2 + 5:g} {y2 - 13:g}" fill="none" '
            f'stroke="{self.s[color]}" stroke-width="{sw:g}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')

    def chip(self, x: float, y: float, w: float, h: float, value: str,
             fg: str, bg: str, size: float = 11.5,
             family: str = MONO, stroke: str | None = None) -> None:
        stroke_attr = (f' stroke="{self.s[stroke]}" stroke-width="1"'
                       if stroke else "")
        self.add(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
                 f'rx="{h / 2:g}" fill="{self.s[bg]}"{stroke_attr}/>')
        self.t(x + w / 2, y + h / 2 + size * 0.36, value, size, fg,
               family, 600, "middle")

    def rule_card(self, x: float, y: float, w: float, h: float,
                  rule_id: str, sev: str, title: str, meta: str) -> None:
        color = "warn" if sev == "warn" else "info"
        soft = "warn_soft" if sev == "warn" else "info_soft"
        self.rect(x, y, w, h, 13, fill="card", stroke="border", sw=1.4)
        self.add(f'<rect x="{x:g}" y="{y + 1:g}" width="3.5" '
                 f'height="{h - 2:g}" rx="1.7" fill="{self.s[color]}"/>')
        self.t(x + 14, y + 19, rule_id, 12, "family", MONO, 700)
        # severity pill, right aligned
        pw = 44 if sev == "warn" else 40
        self.add(f'<rect x="{x + w - 14 - pw:g}" y="{y + 8:g}" '
                 f'width="{pw}" height="18" rx="9" fill="{self.s[soft]}"/>')
        self.t(x + w - 14 - pw / 2, y + 21, sev, 11, color, MONO, 600,
               "middle")
        self.t(x + 14, y + 44, title, 13, "text", SANS, 700)
        self.t(x + 14, y + 66, meta, 11, "sub", MONO)

    def note_card(self, x: float, y: float, w: float, h: float,
                  label: str, title: str, line1: str, line2: str) -> None:
        self.rect(x, y, w, h, 13, fill="panel_soft", stroke="edge",
                  sw=1.4, dash="5 4")
        self.t(x + 14, y + 19, label, 11, "family", MONO, 600)
        self.t(x + 14, y + 41, title, 13, "text", SANS, 700)
        self.t(x + 14, y + 59, line1, 11, "sub", SANS)
        self.t(x + 14, y + 75, line2, 11, "sub", MONO)

    def svg(self) -> str:
        header = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="1100" '
            'height="660" viewBox="0 0 1100 660" role="img" '
            'aria-label="dsh-warranty-calc structure: one claim row fans '
            'out into four field groups — identity, time, mileage and '
            'amount; seven rules hang off them and merge into two '
            'channels, issues[] with row and column locators and '
            'skipped[] with reasons">'
            '<title>dsh-warranty-calc: one claim row, four field groups, '
            'seven rules, two channels</title>'
            '<defs>'
            '<linearGradient id="bg" x1="0" y1="0" x2="0.3" y2="1">'
            f'<stop offset="0" stop-color="{self.s["bg_from"]}"/>'
            f'<stop offset="1" stop-color="{self.s["bg_to"]}"/>'
            '</linearGradient>'
            '<filter id="soft" x="-20%" y="-30%" width="140%" height="170%">'
            '<feDropShadow dx="0" dy="7" stdDeviation="10" '
            f'flood-color="{self.s["shadow"]}" '
            f'flood-opacity="{self.s["shadow_op"]}"/>'
            '</filter>'
            '<pattern id="dots" width="28" height="28" '
            'patternUnits="userSpaceOnUse">'
            f'<circle cx="1.2" cy="1.2" r="1.2" fill="{self.s["dot"]}"/>'
            '</pattern>'
            '</defs>'
            '<rect width="1100" height="660" fill="url(#bg)"/>'
            '<rect width="1100" height="660" fill="url(#dots)" '
            'opacity=".38"/>'
        )
        return header + "".join(self.parts) + "</svg>\n"


def flow_svg(skin: str) -> str:
    g = Svg(skin)

    # ---- header ----------------------------------------------------------
    g.t(40, 36, "结构图 · 一行索赔的字段解剖", 11, "family", MONO, 600,
        spacing=0.8)
    g.add('<rect x="824" y="22" width="236" height="26" rx="13" '
          f'fill="{g.s["family_soft"]}"/>')
    g.t(942, 40, "7 rules · 4 groups · 2 channels", 11, "family", MONO,
        600, "middle")
    g.t(40, 72, "一行索赔，四组字段，七条规则分四路核对", 26, "text",
        SANS, 700)
    g.t(40, 98, "读取层先把栏名归一；规则只读它声明的那几栏。有差异进 "
               "issues[]，不能执行的进 skipped[] 并写明原因。", 13, "sub",
        SANS)
    g.line(40, 112, 1060, 112, "edge", 1.4)

    # ---- stage 1: material + reader + rule pack --------------------------
    g.add('<g filter="url(#soft)">')
    g.rect(40, 126, 250, 80, 16, fill="card", stroke="border")
    g.add('</g>')
    g.t(56, 147, "INPUT · 只读", 11, "family", MONO, 700)
    g.t(56, 171, "file / material", 16, "text", MONO, 700)
    g.t(56, 191, "JSON · YAML · 原件不改", 11, "sub", SANS)

    g.add('<g filter="url(#soft)">')
    g.rect(306, 126, 300, 80, 16, fill="card", stroke="border")
    g.add('</g>')
    g.t(322, 148, "parseMaterial", 17, "text", MONO, 700)
    g.t(322, 170, "栏名归一：忽略大小写 / 空格 / _ / -", 11, "sub", SANS)
    g.t(322, 190, "rows[] · header{dealer, policyVersion}", 11, "sub", MONO)

    g.add('<g filter="url(#soft)">')
    g.rect(700, 126, 360, 80, 16, fill="card", stroke="border")
    g.add('</g>')
    g.t(716, 146, "RULESET · 数据，不是代码", 11, "family", MONO, 700)
    g.t(716, 168, "rules/warranty-calc.yaml · v2026.1", 13, "text", MONO,
        700)
    g.t(716, 187, "加载期校验逐字引文；严重级封顶", 11, "sub", SANS)
    g.t(716, 201, "direct≤error · principle≤warn · local≤info", 11, "sub",
        MONO)

    g.line(290, 166, 298, 166, "family_line", 2)
    g.arrow(296, 166, 306, 166, "family", 2)
    g.line(456, 206, 456, 214, "family_line", 2)
    g.arrow(456, 212, 456, 222, "family", 2)

    # ---- stage 2: the claim row, split into the four read groups ---------
    g.add('<g filter="url(#soft)">')
    g.rect(40, 222, 1020, 132, 18, fill="panel", stroke="border")
    g.add('</g>')
    g.t(56, 245, "台账写明的值 · 第 1 行（示例）", 11.5, "sub", SANS, 600)
    g.t(1044, 245, "栏名保留原样", 11, "faint", MONO, 400, "end")

    groups = [
        (56, 254, 190, "身份"),
        (256, 254, 310, "时间"),
        (576, 254, 260, "里程"),
        (846, 254, 190, "金额"),
    ]
    for x, y, w, _ in groups:
        g.rect(x, y, w, 84, 13, fill="panel_soft", stroke="edge", sw=1.2)

    # identity
    g.t(70, 275, "身份", 13, "text", SANS, 700)
    g.rect(70, 284, 162, 20, 10, fill="warn_soft", stroke="warn_line", sw=1)
    g.t(151, 298, "索赔单号 空", 11, "warn", SANS, 600, "middle")
    g.rect(70, 310, 162, 20, 10, fill="warn_soft", stroke="warn_line", sw=1)
    g.t(151, 324, "配件名称 空", 11, "warn", SANS, 600, "middle")

    # time
    g.t(270, 275, "时间", 13, "text", SANS, 700)
    g.t(280, 291, "销售", 11, "faint", SANS, 400, "start")
    g.t(411, 291, "索赔", 11, "faint", SANS, 400, "middle")
    g.t(550, 291, "截止", 11, "faint", SANS, 400, "end")
    g.line(280, 306, 550, 306, "family_line", 4)
    g.line(280, 306, 550, 306, "family", 2)
    g.line(550, 297, 550, 315, "family", 3)
    g.add(f'<circle cx="280" cy="306" r="5" fill="{g.s["panel_soft"]}" '
          f'stroke="{g.s["family"]}" stroke-width="2"/>')
    g.add(f'<circle cx="430" cy="306" r="7" fill="{g.s["family"]}"/>')
    g.t(280, 327, "2024-03-10", 11, "sub", MONO)
    g.t(430, 327, "2026-03-05", 11, "text", MONO, 600, "middle")
    g.t(550, 327, "2027-03-09", 11, "sub", MONO, 400, "end")

    # mileage
    g.t(590, 275, "里程", 13, "text", SANS, 700)
    g.rect(600, 299, 220, 10, 5, fill="track", stroke=None)
    g.rect(600, 299, int(220 * 0.486), 10, 5, fill="family", stroke=None)
    g.line(820, 294, 820, 314, "family", 3)
    g.t(600, 327, "48,600", 11, "text", MONO, 600)
    g.t(820, 327, "上限 100,000", 11, "sub", SANS, 400, "end")

    # amount
    g.t(860, 275, "金额", 13, "text", SANS, 700)
    g.t(860, 301, "2 × 180 = 360", 13, "text", MONO, 700)
    g.t(860, 325, "单上 400", 13, "warn", SANS, 700)

    # ports from the row into the rule columns
    for x in (151, 411, 706, 941):
        g.add(f'<circle cx="{x}" cy="338" r="3.2" fill="{g.s["family"]}"/>')
        g.line(x, 341, x, 358, "family_line", 1.6)
        g.arrow(x, 354, x, 368, "family", 1.8)

    # ---- stage 3: the seven rules, hung under their field group ----------
    g.rule_card(56, 368, 190, 82, "WC-001", "warn",
                "至少填写单号或配件名称", "claimNo | partName")
    g.rule_card(56, 460, 190, 82, "WC-007", "warn",
                "单号在台账内不重复", "unique(claimNo)")
    g.rule_card(256, 368, 310, 82, "WC-006", "warn",
                "销售日期不晚于索赔日期", "saleDate ≤ claimDate")
    g.rule_card(256, 460, 310, 82, "WC-002", "info",
                "索赔日期落在台账质保期内",
                "saleDate ≤ claimDate ≤ warrantyEndAt")
    g.rule_card(576, 368, 260, 82, "WC-003", "warn",
                "索赔时里程可解析为数", "numberOf(mileageAtClaim)")
    g.rule_card(576, 460, 260, 82, "WC-004", "info",
                "里程不超过台账上限", "mileageAtClaim ≤ warrantyMiles")
    g.rule_card(846, 368, 190, 82, "WC-005", "warn",
                "金额 = 数量 × 单价", "quantity × unitPrice")
    g.note_card(846, 460, 190, 82, "WC-005 的边界", "只覆盖配件金额",
                "工时 / 免赔额另栏", "容差 0.01")

    # ---- stage 4: one outcome bus, two channels -------------------------
    for x in (151, 411, 706, 941):
        g.line(x, 542, x, 552, "rail", 1.4)
    g.rect(40, 552, 1020, 18, 9, fill="family_soft", stroke="family_line",
           sw=1)
    g.t(550, 565, "每条规则 → 有差异：issues[] · 无法执行：skipped[] · "
                  "无差异：不出现", 11, "family", SANS, 600, "middle")
    g.arrow(340, 570, 340, 580, "family", 2)
    g.arrow(870, 570, 870, 580, "family", 2)

    g.add('<g filter="url(#soft)">')
    g.rect(40, 580, 620, 56, 14, fill="card", stroke="border")
    g.add('</g>')
    g.t(56, 600, "issues[]", 13, "family", MONO, 700)
    g.t(132, 600, "差异条目 · 行号 + 栏名", 12, "text", SANS, 600)
    g.t(56, 617, "found / expected / fix · severity 由依据封顶", 11, "sub",
        MONO)
    g.t(56, 632, "例：第 1 行 claimAmount 填报 400，而 2 × 180 = 360", 11,
        "warn", SANS)

    g.rect(680, 580, 380, 56, 14, fill="panel_soft", stroke="edge", sw=1.4,
           dash="5 4")
    g.t(696, 600, "skipped[] 未执行", 13, "text", MONO, 700)
    g.t(696, 617, "缺列 / 停用 / only 限制", 11, "sub", SANS)
    g.t(696, 632, "原因逐条写明；空 issues[] ≠ 通过", 11, "sub", SANS, 600)

    g.t(40, 650, "严重级封顶：direct ≤ error · principle ≤ warn · "
                 "local ≤ info　·　报告只列差异，不判受理 / 合规 / 责任",
        11, "faint", SANS)
    return g.svg()


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for lang in ("zh", "en"):
        for skin in ("light", "dark"):
            draw_hero(lang, skin)
    for skin in ("light", "dark"):
        path = os.path.join(OUT, f"dsh-warranty-calc-flow-v5-{skin}.svg")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(flow_svg(skin))
        print(f"wrote {os.path.basename(path)}")


if __name__ == "__main__":
    main()
