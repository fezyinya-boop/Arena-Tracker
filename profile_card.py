from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import aiohttp
import io
import os
import re
from functools import lru_cache
from typing import Optional, Tuple

RGBA = Tuple[int, int, int, int]
RGB = Tuple[int, int, int]

# ----------------------------
# Paths
# ----------------------------
ROOT_DIR = os.path.dirname(__file__)
FONTS_DIR = os.path.join(ROOT_DIR, "fonts")
BADGES_DIR = os.path.join(ROOT_DIR, "badges")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")

# ----------------------------
# Badges (your existing mapping)
# ----------------------------
RANK_BADGES = {
    "DIAMOND":  os.path.join(BADGES_DIR, "rank_diamond.png"),
    "PLATINUM": os.path.join(BADGES_DIR, "rank_platinum.png"),
    "GOLD":     os.path.join(BADGES_DIR, "rank_gold.png"),
    "SILVER":   os.path.join(BADGES_DIR, "rank_silver.png"),
    "BRONZE":   os.path.join(BADGES_DIR, "rank_bronze.png"),
}

# ----------------------------
# Fonts (cached)
# ----------------------------
@lru_cache(maxsize=256)
def load_font(preferred_filename: str, size: int) -> ImageFont.ImageFont:
    """Load a font from ./fonts if available, else try common system fallbacks."""
    path = os.path.join(FONTS_DIR, preferred_filename)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)

    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheros-bold.otf",
    ):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)

    return ImageFont.load_default()

def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    try:
        return int(draw.textlength(text, font=font))
    except Exception:
        return int(len(text) * (getattr(font, "size", 16) * 0.6))

def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    preferred_filename: str,
    max_w: int,
    start_size: int,
    min_size: int,
) -> ImageFont.ImageFont:
    """Shrink font size until it fits max_w."""
    size = start_size
    while size >= min_size:
        f = load_font(preferred_filename, size)
        if text_width(draw, text, f) <= max_w:
            return f
        size -= 1
    return load_font(preferred_filename, min_size)

# ----------------------------
# Image helpers
# ----------------------------
def center_crop_square(img: Image.Image) -> Image.Image:
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))

def soft_circle_mask(size: int, feather: int = 4) -> Image.Image:
    """Slightly feathered circle mask for smooth avatar edges."""
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.ellipse((feather, feather, size - feather - 1, size - feather - 1), fill=255)
    # cheap AA: upscale then downscale
    m2 = m.resize((size * 2, size * 2), Image.Resampling.BICUBIC).resize((size, size), Image.Resampling.LANCZOS)
    return m2

async def fetch_avatar(url: str) -> Optional[Image.Image]:
    """Fetch avatar image and return RGBA PIL image."""
    try
