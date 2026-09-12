"""
Steam library artwork generator — regenerates everything in assets/steam/
from the current assets/icon.png and assets/logo.png, so the Steam art never
drifts out of sync with the app's own branding. Matches the sibling TWRAR/
TS4RLS projects' convention; TIGHC has no Steam store listing yet, but the
non-Steam-game shortcut art (icon.png) is also useful on its own for a
Steam/CurseForge launch-target shortcut.

Run this whenever icon.png or logo.png change:
    python src/build/create_steam_assets.py

Output:
    assets/steam/cover.png            600x900   portrait grid capsule
    assets/steam/wide_cover.png       920x430   landscape grid capsule
    assets/steam/background.png      3840x1240  library hero
    assets/steam/logo.png            1280x720   library logo, stacked (transparent bg)
    assets/steam/logo_horizontal.png 1280x720   library logo, icon+wordmark side by side (transparent bg)
    assets/steam/icon.png             256x256   library icon (transparent bg)
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageOps

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = REPO_ROOT / "assets"
STEAM_DIR = ASSETS_DIR / "steam"
ICON_PATH = ASSETS_DIR / "icon.png"
LOGO_PATH = ASSETS_DIR / "logo.png"

# Sampled from the current icon.png/logo.png's purple (accent, #7C5CFF)
# blended toward white, so regenerated art always matches the app's actual
# brand color instead of a hand-picked approximation.
BG_CENTER = (233, 227, 255)
BG_EDGE = (184, 167, 255)

# logo.png (see create_project_assets.py's draw_wordmark()) is a 200px icon
# square pasted at x=18, then the "TIGHC" / tagline wordmark starting at
# x=218 -- crop right at that boundary since draw_wordmark() controls both.
_WORDMARK_LEFT = 218
# Row split between the "TIGHC" title and tagline subtitle within the tight
# wordmark crop (found by inspecting logo.png's text pixel rows).
_TITLE_BOTTOM = 71
_SUBTITLE_TOP = 82


def _load_icon() -> Image.Image:
    return Image.open(ICON_PATH).convert("RGBA")


def _load_wordmark() -> Image.Image:
    """Crops the "TIGHC / The Intiface Game Haptics Controller" wordmark
    out of logo.png (which is icon + wordmark side by side), so every Steam
    asset reuses the exact same text art as the app itself instead of a
    separately hand-drawn (and driftable) copy. Title and subtitle stay
    left-aligned to each other in this single crop -- correct for a
    horizontal lockup (icon left, this block right), but NOT for stacking
    under a centered icon -- use _load_wordmark_parts() for that instead."""
    logo = Image.open(LOGO_PATH).convert("RGBA")
    text = logo.crop((_WORDMARK_LEFT, 0, logo.width, logo.height))
    return text.crop(text.getbbox())


def _load_wordmark_parts():
    """Same source crop as _load_wordmark(), split into separate title
    ("TIGHC") and subtitle ("The Intiface Game Haptics Controller") images
    so each can be centered independently under a stacked, centered icon --
    the subtitle is wider than the title, so centering the combined block
    as one piece leaves the title looking off-center."""
    tight = _load_wordmark()
    w, h = tight.size
    title = tight.crop((0, 0, w, _TITLE_BOTTOM))
    subtitle = tight.crop((0, _SUBTITLE_TOP, w, h))
    return title.crop(title.getbbox()), subtitle.crop(subtitle.getbbox())


def _radial_gradient(size, center_color, edge_color, small=384) -> Image.Image:
    """Builds the gradient on a small square canvas and lets resize()
    stretch it to the target aspect ratio -- cheaper than a per-pixel loop
    at full (up to 3840x1240) resolution, and the stretch itself is what
    gives banners their elliptical (rather than perfectly circular) falloff."""
    grad = Image.new("L", (small, small))
    px = grad.load()
    cx = cy = small / 2
    max_d = math.hypot(cx, cy)
    for y in range(small):
        for x in range(small):
            px[x, y] = int(255 * min(1.0, math.hypot(x - cx, y - cy) / max_d))
    grad = grad.resize(size, Image.BICUBIC)
    return ImageOps.colorize(grad, black=center_color, white=edge_color).convert("RGBA")


def _pattern_layer(size, icon, tile_size, opacity, spacing_factor=1.35) -> Image.Image:
    """Tiles a small, faded copy of the icon edge-to-edge in a staggered
    (brick-style) grid, so it reads as an actual background pattern rather
    than a few stray logos."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    tile = icon.resize((tile_size, tile_size), Image.LANCZOS)
    r, g, b, a = tile.split()
    a = a.point(lambda v: int(v * opacity))
    tile = Image.merge("RGBA", (r, g, b, a))

    spacing = int(tile_size * spacing_factor)
    row = 0
    y = -spacing
    while y < size[1] + spacing:
        x_offset = (spacing // 2) if row % 2 else 0
        x = -spacing + x_offset
        while x < size[0] + spacing:
            layer.alpha_composite(tile, (x, y))
            x += spacing
        y += spacing
        row += 1
    return layer


def _textured_background(size, tile_size, opacity, icon) -> Image.Image:
    bg = _radial_gradient(size, BG_CENTER, BG_EDGE)
    pattern = _pattern_layer(size, icon, tile_size, opacity)
    bg.alpha_composite(pattern)
    return bg


def _paste_centered(base: Image.Image, layer: Image.Image, cx: int, cy: int) -> None:
    base.alpha_composite(layer, (cx - layer.width // 2, cy - layer.height // 2))


def _scaled(img: Image.Image, target_width: int) -> Image.Image:
    ratio = target_width / img.width
    return img.resize((target_width, max(1, int(img.height * ratio))), Image.LANCZOS)


def _scaled_by(img: Image.Image, factor: float) -> Image.Image:
    return img.resize((max(1, int(img.width * factor)), max(1, int(img.height * factor))), Image.LANCZOS)


def _paste_stacked_wordmark(canvas, title, subtitle, target_subtitle_width, cx, top_y, gap=10) -> int:
    """Scales title/subtitle by one shared factor (so their relative size
    stays correct) and centers each on its own row under an icon -- unlike
    pasting the combined title+subtitle crop as a single left-aligned
    block, which leaves the (narrower) title looking off-center."""
    factor = target_subtitle_width / subtitle.width
    title_s = _scaled_by(title, factor)
    subtitle_s = _scaled_by(subtitle, factor)

    canvas.alpha_composite(title_s, (cx - title_s.width // 2, top_y))
    canvas.alpha_composite(subtitle_s, (cx - subtitle_s.width // 2, top_y + title_s.height + gap))
    return title_s.height + gap + subtitle_s.height


def build_cover(icon: Image.Image, title: Image.Image, subtitle: Image.Image) -> Image.Image:
    size = (600, 900)
    canvas = _textured_background(size, tile_size=56, opacity=0.16, icon=icon)

    big_icon = _scaled(icon, 340)
    target_subtitle_width = 460
    gap = 10
    icon_text_gap = 80

    factor = target_subtitle_width / subtitle.width
    title_h = int(title.height * factor)
    subtitle_h = int(subtitle.height * factor)

    total_height = big_icon.height + icon_text_gap + title_h + gap + subtitle_h
    top = (size[1] - total_height) // 2

    _paste_centered(canvas, big_icon, size[0] // 2, top + big_icon.height // 2)

    text_top = top + big_icon.height + icon_text_gap
    _paste_stacked_wordmark(
        canvas, title, subtitle, target_subtitle_width=target_subtitle_width,
        cx=size[0] // 2, top_y=text_top, gap=gap,
    )

    return canvas.convert("RGB")


def build_wide_cover(icon: Image.Image, wordmark: Image.Image) -> Image.Image:
    size = (920, 430)
    canvas = _textured_background(size, tile_size=48, opacity=0.16, icon=icon)

    big_icon = _scaled(icon, 300)
    canvas.alpha_composite(big_icon, (40, (size[1] - big_icon.height) // 2))

    text = _scaled(wordmark, 480)
    text_x = 40 + big_icon.width + 40
    canvas.alpha_composite(text, (text_x, (size[1] - text.height) // 2))

    return canvas.convert("RGB")


def build_background(icon: Image.Image) -> Image.Image:
    size = (3840, 1240)
    return _textured_background(size, tile_size=110, opacity=0.14, icon=icon).convert("RGB")


def build_logo(icon: Image.Image, title: Image.Image, subtitle: Image.Image) -> Image.Image:
    """Stacked variant: icon on top, title/subtitle centered underneath.
    Per Steam's requirements this stays transparent -- no gradient, no
    background pattern, just the mark for Steam to composite itself."""
    size = (1280, 720)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))

    big_icon = _scaled(icon, 300)
    _paste_centered(canvas, big_icon, size[0] // 2, 260)

    text_top = 260 + big_icon.height // 2 + 90
    _paste_stacked_wordmark(canvas, title, subtitle, target_subtitle_width=620, cx=size[0] // 2, top_y=text_top)

    return canvas


def build_icon(icon: Image.Image) -> Image.Image:
    """Steam's separate "Icon" custom-artwork slot (shown in the taskbar/
    shortcut, not the library grid art) -- just the app's own icon.png as
    is, since it's already a square, transparent mark at a sensible size."""
    return icon


def build_logo_horizontal(icon: Image.Image, wordmark: Image.Image) -> Image.Image:
    """Alternate variant: icon on the left, wordmark to its right (same
    lockup as wide_cover.png), for anyone who'd rather have a wide logo
    than a stacked one in that slot. Also transparent, per Steam's
    requirements for the logo asset."""
    size = (1280, 720)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))

    big_icon = _scaled(icon, 360)
    icon_x = 120
    canvas.alpha_composite(big_icon, (icon_x, (size[1] - big_icon.height) // 2))

    text = _scaled(wordmark, 680)
    text_x = icon_x + big_icon.width + 50
    canvas.alpha_composite(text, (text_x, (size[1] - text.height) // 2))

    return canvas


def build() -> None:
    print("TIGHC - Steam Artwork Generator")
    print("Regenerating assets/steam/ from icon.png + logo.png\n")

    icon = _load_icon()
    wordmark = _load_wordmark()
    title, subtitle = _load_wordmark_parts()
    STEAM_DIR.mkdir(parents=True, exist_ok=True)

    outputs = {
        "cover.png": build_cover(icon, title, subtitle),
        "wide_cover.png": build_wide_cover(icon, wordmark),
        "background.png": build_background(icon),
        "logo.png": build_logo(icon, title, subtitle),
        "logo_horizontal.png": build_logo_horizontal(icon, wordmark),
        "icon.png": build_icon(icon),
    }
    for name, image in outputs.items():
        dest = STEAM_DIR / name
        image.save(dest)
        print(f"  wrote {dest.relative_to(REPO_ROOT)} ({image.width}x{image.height})")

    print("\nDone.")


if __name__ == "__main__":
    build()
