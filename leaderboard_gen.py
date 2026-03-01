from PIL import Image, ImageDraw, ImageFont
import io
import os
import re

# --- FONT LOADER ---
def load_custom_font(font_filename, size):
    font_path = os.path.join(os.path.dirname(__file__), "fonts", font_filename)
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()

# --- RANK BADGE UTILS ---
def clean_rank_name(name: str) -> str:
    return re.sub(r'<:[^:]+:\d+>\s*', '', name).strip()

BADGES_DIR = os.path.join(os.path.dirname(__file__), 'badges')
RANK_BADGES = {
    "DIAMOND":  os.path.join(BADGES_DIR, 'rank_diamond.png'),
    "PLATINUM": os.path.join(BADGES_DIR, 'rank_platinum.png'),
    "GOLD":     os.path.join(BADGES_DIR, 'rank_gold.png'),
    "SILVER":   os.path.join(BADGES_DIR, 'rank_silver.png'),
    "BRONZE":   os.path.join(BADGES_DIR, 'rank_bronze.png'),
}

def get_rank_badge(rank_name_raw: str, size: int = 40):
    clean = clean_rank_name(str(rank_name_raw)).upper()
    path = RANK_BADGES.get(clean)
    if not path or not os.path.exists(path):
        return None
    try:
        return Image.open(path).convert('RGBA').resize((size, size), Image.LANCZOS)
    except:
        return None

# --- MAIN GENERATOR ---
def make_leaderboard_image(players):
    # 1. DIMENSIONS
    header_h = 140
    row_h = 85 # Taller rows for bigger names/badges
    W = 900    # Wider to accommodate everything
    H = header_h + (len(players) * row_h) + 40
    
    card = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(card)

    # 2. FONTS
    f_title = load_custom_font("Orbitron-VariableFont_wght.ttf", 45)
    f_rank  = load_custom_font("Michroma-Regular.ttf", 24)
    f_name  = load_custom_font("FunnelSans-Medium.ttf", 36) # BUMPED SIZE
    f_pts   = load_custom_font("Michroma-Regular.ttf", 22)
    f_label = load_custom_font("Michroma-Regular.ttf", 14)

    # 3. HEADER
    draw.rectangle([(0, 0), (W, 115)], fill=(18, 18, 18))
    draw.text((40, 35), "ARENA RANKINGS", font=f_title, fill=(255, 255, 255))
    
    draw.text((40, 118), "RANK", font=f_label, fill=(100, 100, 100))
    draw.text((160, 118), "CONTENDER", font=f_label, fill=(100, 100, 100))
    draw.text((W - 160, 118), "RATING", font=f_label, fill=(100, 100, 100))

    # 4. PLAYER ROWS
    curr_y = header_h
    for i, p in enumerate(players):
        rank_num = i + 1
        color = p.get('rank_color', (255, 255, 255))
        rank_name = p.get('rank_name', "BRONZE") # Default to bronze if missing
        
        # Row Background
        if i % 2 == 0:
            draw.rectangle([(15, curr_y), (W-15, curr_y + row_h - 10)], fill=(12, 12, 12))

        # Rank Number
        rank_str = f"#{rank_num:02d}"
        text_color = color if rank_num <= 3 else (180, 180, 180)
        draw.text((40, curr_y + 20), rank_str, font=f_rank, fill=text_color)

        # --- RANK EMBLEM ---
        badge = get_rank_badge(rank_name, size=55)
        name_x_offset = 160
        if badge:
            card.paste(badge, (160, curr_y + 10), badge)
            name_x_offset += 70 # Move name to the right of badge

        # --- BIG PLAYER NAME ---
        # Draw a very subtle shadow for "Pop"
        draw.text((name_x_offset + 2, curr_y + 14), p['name'].upper(), font=f_name, fill=(0, 0, 0, 150))
        draw.text((name_x_offset, curr_y + 12), p['name'].upper(), font=f_name, fill=(255, 255, 255))
        
        # Rating
        draw.text((W - 160, curr_y + 20), str(p['pts']), font=f_pts, fill=color)

        # Side Accent
        if rank_num <= 3:
            draw.rectangle([(15, curr_y), (22, curr_y + row_h - 10)], fill=color)

        curr_y += row_h

    # 5. FOOTER
    draw.text((W//2, H - 20), "BATTLE DATA VERIFIED // SEASON 1", font=f_label, fill=(70, 70, 70), anchor="mm")

    buf = io.BytesIO()
    card.save(buf, 'PNG')
    buf.seek(0)
    return buf
