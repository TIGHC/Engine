"""One-off generator for assets/icon.png, assets/icon.ico, assets/icon.icns,
assets/logo.png, and the sibling Website repo's matching icon.png,
logo.png, and favicon.ico.

Run with: python src/build/create_project_assets.py
Requires Pillow (dev-only; not a runtime dependency of the app itself).

Reproduces the existing hand-made icon/logo in code: a purple, fully
rounded ("pill") game-controller body with a transparent-cutout D-pad
cross and two face buttons, plus two comet-shaped "haptic wave" ticks
radiating from its top-right corner.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent.parent.parent / "assets"
ASSETS.mkdir(exist_ok=True)

# Sibling Website repo's assets/ - gets its own copy of icon.png/logo.png
# (so the site never drifts out of sync with the app's branding) plus
# favicon.ico, which is a Website-only asset that has no business living
# in this repo.
WEBSITE_ASSETS = Path(__file__).resolve().parent.parent.parent.parent / "Website" / "assets"

PURPLE = (124, 92, 255, 255)  # sampled from the existing hand-made icon.png
TRANSPARENT = (0, 0, 0, 0)

FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"

# Capsule ("controller body") bounding box, as a fraction of `size` - not
# centered: it leaves clear headroom in the top-right for the haptic wave
# ticks, matching the original art.
CAPSULE_LEFT_FRAC = 15 / 256
CAPSULE_RIGHT_FRAC = 199 / 256
CAPSULE_TOP_FRAC = 95 / 256
CAPSULE_BOTTOM_FRAC = 203 / 256

# D-pad cross: two overlapping rectangles (vertical + horizontal bar),
# cut out of the capsule as real transparent holes (not a white fill) -
# same technique the original icon.png uses, so the mark stays legible on
# any background color, not just white.
CROSS_CENTER_FRAC = (77 / 256, 148 / 256)
CROSS_V_HALF_W_FRAC = 7 / 256
CROSS_V_HALF_H_FRAC = 20 / 256
CROSS_H_HALF_W_FRAC = 21 / 256
CROSS_H_HALF_H_FRAC = 6 / 256

# Two face buttons (also transparent cutouts), same radius, arranged
# diagonally to the cross's right.
BUTTON_RADIUS_FRAC = 11.5 / 256
BUTTON_A_CENTER_FRAC = (157 / 256, 132 / 256)  # upper-right button
BUTTON_B_CENTER_FRAC = (139 / 256, 158 / 256)  # lower-left button

# Haptic wave ticks: two comet-shaped marks (pointed away from the pivot,
# flat near it) radiating up-and-right from the capsule's top-right
# corner, like a signal/vibration indicator.
WAVE_PIVOT_FRAC = (194 / 256, 94 / 256)
WAVE_ANGLE_DEG = -42  # image coords: up-and-right
WAVE_TAPER_FRAC = 0.5  # where the comet starts narrowing toward its point
WAVES = [
    # (distance from pivot to this wave's near edge, length, width), all
    # as a fraction of `size`.
    (0.03, 0.085, 0.072),
    (0.155, 0.125, 0.088),
]


def _wave_polygon(pivot: tuple[float, float], anchor_dist: float, length: float, width: float):
    angle = math.radians(WAVE_ANGLE_DEG)
    dx, dy = math.cos(angle), math.sin(angle)
    px, py = -dy, dx  # perpendicular to (dx, dy)

    anchor = (pivot[0] + dx * anchor_dist, pivot[1] + dy * anchor_dist)
    taper_u = length * WAVE_TAPER_FRAC
    half_w = width / 2

    local_points = [
        (length, 0),
        (taper_u, half_w),
        (0, half_w),
        (0, -half_w),
        (taper_u, -half_w),
    ]
    return [
        (anchor[0] + u * dx + v * px, anchor[1] + u * dy + v * py)
        for u, v in local_points
    ]


def draw_glyph(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    left, right = CAPSULE_LEFT_FRAC * size, CAPSULE_RIGHT_FRAC * size
    top, bottom = CAPSULE_TOP_FRAC * size, CAPSULE_BOTTOM_FRAC * size
    radius = (bottom - top) / 2  # fully rounded ("pill") ends
    draw.rounded_rectangle([left, top, right, bottom], radius=radius, fill=PURPLE)

    pivot = (WAVE_PIVOT_FRAC[0] * size, WAVE_PIVOT_FRAC[1] * size)
    for anchor_dist, length, width in WAVES:
        draw.polygon(
            _wave_polygon(pivot, anchor_dist * size, length * size, width * size),
            fill=PURPLE,
        )

    # Cut the D-pad cross and both face buttons out as real transparent
    # holes (drawn last, after the wave ticks, since they only ever
    # overlap the capsule body).
    ccx, ccy = CROSS_CENTER_FRAC[0] * size, CROSS_CENTER_FRAC[1] * size
    vhw, vhh = CROSS_V_HALF_W_FRAC * size, CROSS_V_HALF_H_FRAC * size
    hhw, hhh = CROSS_H_HALF_W_FRAC * size, CROSS_H_HALF_H_FRAC * size
    draw.rectangle([ccx - vhw, ccy - vhh, ccx + vhw, ccy + vhh], fill=TRANSPARENT)
    draw.rectangle([ccx - hhw, ccy - hhh, ccx + hhw, ccy + hhh], fill=TRANSPARENT)

    br = BUTTON_RADIUS_FRAC * size
    for bcx_frac, bcy_frac in (BUTTON_A_CENTER_FRAC, BUTTON_B_CENTER_FRAC):
        bcx, bcy = bcx_frac * size, bcy_frac * size
        draw.ellipse([bcx - br, bcy - br, bcx + br, bcy + br], fill=TRANSPARENT)

    return img


def draw_wordmark() -> Image.Image:
    height = 260
    icon_x, icon_size = 18, 200
    icon_y = (height - icon_size) // 2
    text_x = icon_x + icon_size + 28
    text_tagline_gap = 12

    acronym_font = ImageFont.truetype(FONT_BOLD, 96)
    tagline_font = ImageFont.truetype(FONT_BOLD, 26)
    acronym = "TIGHC"
    tagline = "The Intiface Game Haptics Controller"

    # Measure both lines first (on a throwaway image - textbbox doesn't
    # need a real canvas) so the whole text block can be vertically
    # centered against the icon's own center, and the canvas sized to fit
    # the actual content instead of a hardcoded, wider-than-necessary width.
    measure_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    acronym_bbox = measure_draw.textbbox((0, 0), acronym, font=acronym_font)
    tagline_bbox = measure_draw.textbbox((0, 0), tagline, font=tagline_font)
    acronym_h = acronym_bbox[3] - acronym_bbox[1]
    tagline_h = tagline_bbox[3] - tagline_bbox[1]
    text_block_h = acronym_h + text_tagline_gap + tagline_h
    text_block_top = (height - text_block_h) // 2  # same vertical center as the icon

    acronym_w = acronym_bbox[2] - acronym_bbox[0]
    tagline_w = tagline_bbox[2] - tagline_bbox[0]
    right_margin = icon_x  # mirror the left margin, for a symmetric-looking gap
    width = text_x + max(acronym_w, tagline_w) + right_margin

    img = Image.new("RGBA", (width, height), TRANSPARENT)
    draw = ImageDraw.Draw(img)

    icon = draw_glyph(icon_size)
    img.paste(icon, (icon_x, icon_y), icon)

    draw.text((text_x, text_block_top - acronym_bbox[1]), acronym, font=acronym_font, fill=PURPLE)
    tagline_top = text_block_top + acronym_h + text_tagline_gap
    draw.text((text_x, tagline_top - tagline_bbox[1]), tagline, font=tagline_font, fill=PURPLE)

    return img


def main() -> None:
    logo = draw_wordmark()
    logo.save(ASSETS / "logo.png")

    icon_sizes = [16, 24, 32, 48, 64, 128, 256]
    icon_base = draw_glyph(256)
    icon_base.save(ASSETS / "icon.png")
    icon_base.save(ASSETS / "icon.ico", sizes=[(s, s) for s in icon_sizes])

    icon_hires = draw_glyph(1024)
    icon_hires.save(ASSETS / "icon.icns")

    print(
        f"Wrote {ASSETS / 'logo.png'}, {ASSETS / 'icon.png'}, "
        f"{ASSETS / 'icon.ico'}, {ASSETS / 'icon.icns'}"
    )

    # The website gets its own copies of icon.png/logo.png (kept in sync
    # with the app's own branding) plus favicon.ico, which isn't used by
    # the Engine app itself - it's only for the Website repo's
    # <link rel="shortcut icon">.
    if WEBSITE_ASSETS.is_dir():
        favicon_sizes = [16, 32, 48]
        icon_base.save(WEBSITE_ASSETS / "favicon.ico", sizes=[(s, s) for s in favicon_sizes])
        icon_base.save(WEBSITE_ASSETS / "icon.png")
        logo.save(WEBSITE_ASSETS / "logo.png")
        print(
            f"Wrote {WEBSITE_ASSETS / 'favicon.ico'}, "
            f"{WEBSITE_ASSETS / 'icon.png'}, {WEBSITE_ASSETS / 'logo.png'}"
        )
    else:
        print(f"Skipped Website assets - no sibling checkout at {WEBSITE_ASSETS}")


if __name__ == "__main__":
    main()
