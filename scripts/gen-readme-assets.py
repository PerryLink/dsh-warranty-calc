#!/usr/bin/env python3
"""Generate README image assets for dsh-warranty-calc (docs/assets/).

Outputs (idempotent overwrite):
  dsh-warranty-calc-flow-light.svg / dsh-warranty-calc-flow-dark.svg
      Hero check-pipeline diagram. Two hand-written SVG files (vector — never
      rasterized to webp). Text inside is command-surface tokens only
      (parseMaterial, rules/warranty-calc.yaml, skipped, ...), so all five
      README languages share the same pair.

There is no benchmark data in this repository, so no evidence chart is
generated: the README has no "measured data" section by design.

Run once:  python scripts/gen-readme-assets.py
Requires:  Pillow (pip install pillow)
"""
from __future__ import annotations

import os
import sys

from PIL import ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")

# --- palette: PerryLink family (accent) + GitHub page backgrounds ----------
FAMILY = "#4B67B4"   # family accent (badges labelColor family uses #2B3245)
GREEN = {"light": "#16a34a", "dark": "#3fb950"}
SKIN = {
    "light": dict(bg="#ffffff", box="#f6f8fa", border="#d0d7de",
                  text="#1f2328", sub="#57606a", rule="#d0d7de"),
    "dark": dict(bg="#0d1117", box="#161b22", border="#30363d",
                 text="#f0f6fc", sub="#8b949e", rule="#30363d"),
}

# --- CJK font probe: the family template refuses to render tofu boxes ------
# The flow diagram itself uses ASCII tokens only, but the guard stays in place
# so a future localized asset can never ship with missing glyphs.
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",      # Microsoft YaHei
    r"C:\Windows\Fonts\simhei.ttf",    # SimHei
    r"C:\Windows\Fonts\Deng.ttf",      # DengXian
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
if FONT_PATH is None:
    sys.exit("FATAL: no CJK font found (looked for msyh.ttc, simhei.ttf, "
             "Deng.ttf, Noto Sans CJK, PingFang). Refusing to render Chinese "
             "as tofu boxes; install one of the probed fonts and re-run.")
FONT = ImageFont.truetype(FONT_PATH, 20)
if FONT.getlength("质保") <= 0:
    sys.exit("FATAL: the probed CJK font reports zero advance for 质保.")

# ---------------------------------------------------------------------------
# Hero check-pipeline SVG (light + dark)
# ---------------------------------------------------------------------------
FLOW_NODES = [
    ("file | material", "JSON · YAML"),
    ("parseMaterial", "rows[] · aliases"),
    ("rules/warranty-calc.yaml", "WC-001 … WC-007"),
    ("runTableCheck", "warn · info"),
    ("report", "markdown · reportJson"),
]


def flow_svg(skin: str) -> str:
    s = SKIN[skin]
    w, h = 1200, 420
    nw, nh, gap = 205, 112, 24
    y0 = 148
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="dsh-warranty-calc check pipeline">',
        '<title>dsh-warranty-calc check pipeline</title>',
        f'<rect width="{w}" height="{h}" rx="18" fill="{s["bg"]}"/>',
        f'<text x="60" y="58" fill="{s["text"]}" font-family="ui-sans-serif,'
        f'system-ui,sans-serif" font-size="30" font-weight="700">'
        f'dsh-warranty-calc</text>',
        f'<text x="60" y="92" fill="{s["sub"]}" font-family="ui-monospace,'
        f'monospace" font-size="16">warranty_calc · table self-consistency · '
        f'host-only</text>',
        f'<line x1="60" y1="116" x2="1140" y2="116" stroke="{s["rule"]}"/>',
    ]
    for i, (label, sub) in enumerate(FLOW_NODES):
        x = 60 + i * (nw + gap)
        accent = GREEN[skin] if i == len(FLOW_NODES) - 1 else (
            FAMILY if i in (2, 3) else s["border"])
        parts.append(
            f'<rect x="{x}" y="{y0}" width="{nw}" height="{nh}" rx="14" '
            f'fill="{s["box"]}" stroke="{accent}" stroke-width="2"/>')
        parts.append(
            f'<text x="{x + nw // 2}" y="{y0 + 38}" fill="{s["text"]}" '
            f'text-anchor="middle" font-family="ui-monospace,monospace" '
            f'font-size="{13 if len(label) > 18 else 15}" '
            f'font-weight="700">{label}</text>')
        parts.append(
            f'<text x="{x + nw // 2}" y="{y0 + 66}" fill="{s["sub"]}" '
            f'text-anchor="middle" font-family="ui-monospace,monospace" '
            f'font-size="12">{sub}</text>')
        if i < len(FLOW_NODES) - 1:
            ax = x + nw + 4
            ay = y0 + nh // 2
            parts.append(
                f'<path d="M{ax} {ay}h{gap - 8}" stroke="{s["sub"]}" '
                f'stroke-width="3"/>')
            parts.append(
                f'<path d="M{ax + gap - 12} {ay - 6}l8 6-8 6" fill="none" '
                f'stroke="{s["sub"]}" stroke-width="3" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')
    # report contract bar under the pipeline
    bx, bw, by, bh = 60, 1080, 300, 56
    parts.append(
        f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="12" '
        f'fill="{s["box"]}" stroke="{FAMILY}" stroke-width="2"/>')
    parts.append(
        f'<text x="{bx + bw // 2}" y="{by + 34}" fill="{s["text"]}" '
        f'text-anchor="middle" font-family="ui-monospace,monospace" '
        f'font-size="14">issueCount · skippedCount · locator{{row, field}} · '
        f'found / expected / fix</text>')
    parts.append(
        f'<text x="60" y="396" fill="{s["sub"]}" font-family="ui-monospace,'
        f'monospace" font-size="13">skipped ≠ pass · no network · no model '
        f'call · original register read-only</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for skin in ("light", "dark"):
        with open(os.path.join(OUT, f"dsh-warranty-calc-flow-{skin}.svg"),
                  "w", encoding="utf-8", newline="\n") as fh:
            fh.write(flow_svg(skin))
    print("wrote 2 SVG assets to docs/assets/")


if __name__ == "__main__":
    main()
