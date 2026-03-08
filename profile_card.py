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
# Helper Functions
# ----------------------------
def draw_hex_grid(draw: ImageDraw.ImageDraw, area: Tuple[int, int, int, int], size: int, color: RGBA):
    """Draws a subtle hexagonal grid for a tech/carbon-fiber look."""
    x1, y1, x2, y2 = area
    w_step = int(size * 1.732)
    h_step = int(size * 1.5)
    
    for y in range(y1, y2 + h_step, h_step):
        shift = (size * 0.866) if ((y - y1) // h_step) % 2 == 1 else 0
        for x in range(x1 - int(size), x2 + w_step, w_step):
            draw.regular_polygon((x + shift, y), 6, rotation=30, outline=color, fill=None)

@lru_cache(maxsize=256)
def load_font(preferred_filename: str, size: int) -> ImageFont.ImageFont:
    path = os.path.join(FONTS_DIR, preferred_filename)
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    return int(draw.textlength(text, font=font))

def fit_font(draw, text, font_name, max_w, start_size, min_size):
    size = start_size
    while size >= min_size:
        f = load_font(font_name, size)
        if text_width(draw, text, f) <= max_w:
            return f
        size -= 2
    return load_font(font_name, min_size)

def draw_tracked_name(base_img, text_value, pos, font, tracking, fill=(255, 255, 255, 255),
                      underline_fill=(255, 200, 90, 220), underline_offset=54, underline_width=3):
    x, y = pos
    chars = list(text_value)
    widths = [font.getlength(ch) for ch in chars]
    total_w = sum(widths) + (tracking * (len(chars) - 1))

    d = ImageDraw.Draw(base_img)
    cx = x
    for i, ch in enumerate(chars):
        # Drop shadow
        d.text((cx, y + 2), ch, font=font, fill=(0, 0, 0, 150))
        # Main text (No fade)
        d.text((cx, y), ch, font=font, fill=fill, stroke_width=2, stroke_fill=(0, 0, 0, 180))
        cx += widths[i] + tracking

    # Permanent Underline
    if underline_width > 0:
        ul_y = y + underline_offset
        d.line((x, ul_y, x + total_w, ul_y), fill=underline_fill, width=underline_width)
    return int(total_w)

# [Remaining fetch_avatar, get_rank_badge, etc. remain unchanged from your source]

def make_profile_card(
    display_name: str, p_title: str, p_move: str, pts: int, wins: int, losses: int,
    streak: int, pct: float, current_rank_raw: str, next_rank_raw: Optional[str],
    rank_color: RGB, avatar_img: Optional[Image.Image] = None,
) -> io.BytesIO:
    SCALE = 2
    W, H = 1024 * SCALE, 512 * SCALE
    def S(x): return x * SCALE
    rc = rank_color
    PANEL_FILL = (8, 8, 12, 255)

    card = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(card)

    # 1. Background Panel with Hex Grid
    panel_y = S(205) - S(80)
    panel_y2 = H - S(24)
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle((0, panel_y, W, panel_y2), radius=S(28), fill=PANEL_FILL)
    
    # Draw Carbon Fiber Texture
    draw_hex_grid(pd, (0, panel_y, W, panel_y2), S(14), (255, 255, 255, 8))
    
    card = Image.alpha_composite(card, panel)
    draw = ImageDraw.Draw(card)

    # 2. Stylized Avatar Border
    av_x, av_y, av_size = S(50), panel_y + S(64), S(174)
    # [Avatar pasting logic here...]

    # Triple Ring Style
    # Outer Glow
    glow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_img)
    gd.ellipse((av_x-S(10), av_y-S(10), av_x+av_size+S(10), av_y+av_size+S(10)), outline=(rc[0], rc[1], rc[2], 85), width=S(8))
    card = Image.alpha_composite(card, glow_img.filter(ImageFilter.GaussianBlur(S(5))))
    # Main Gold Frame
    draw.ellipse((av_x-S(3), av_y-S(3), av_x+av_size+S(3), av_y+av_size+S(3)), outline=(255, 214, 96, 255), width=S(5))
    # Inner Tech Bezel
    for a in range(0, 360, 30):
        draw.arc((av_x+S(5), av_y+S(5), av_x+av_size-S(5), av_y+av_size-S(5)), start=a, end=a+15, fill=(255,255,255,140), width=S(2))

    # 3. Nameplate Scaling & Styling
    name_text = (display_name or "PLAYER").upper()
    name_x, name_y = av_x + av_size + S(56), panel_y + S(72)
    
    # Scale font to prevent right-side overlap
    f_name = fit_font(draw, name_text, "Cinzel-Bold.ttf", max_w=S(480), start_size=S(52), min_size=S(32))
    
    draw_tracked_name(
        card, name_text, (name_x, name_y), f_name, S(10),
        fill=(255, 255, 255, 255), underline_fill=(255, 200, 90, 220)
    )

    # [Rest of the RP and Stats rendering...]
    buf = io.BytesIO()
    card.resize((1024, 512), Image.Resampling.LANCZOS).save(buf, "PNG")
    buf.seek(0)
    return buf
