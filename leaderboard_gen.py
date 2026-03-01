from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- FONT LOADER ---
def load_custom_font(font_filename, size):
    font_path = os.path.join(os.path.dirname(__file__), "fonts", font_filename)
    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()

def make_leaderboard_image(players):
    """
    players: List of dicts [{"name": str, "pts": int, "rank_color": tuple}, ...]
    """
    # 1. DIMENSIONS
    # Base height for header/footer + 70px per player row
    header_h = 130
    row_h = 70
    W = 800
    H = header_h + (len(players) * row_h) + 40
    
    card = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    draw = ImageDraw.Draw(card)

    # 2. FONTS
    f_title = load_custom_font("Orbitron-VariableFont_wght.ttf", 40)
    f_rank  = load_custom_font("Michroma-Regular.ttf", 22)
    f_name  = load_custom_font("FunnelSans-Medium.ttf", 26)
    f_pts   = load_custom_font("Michroma-Regular.ttf", 20)
    f_label = load_custom_font("Michroma-Regular.ttf", 12)

    # 3. HEADER SECTION
    # Subtle dark grey bar for the title
    draw.rectangle([(0, 0), (W, 110)], fill=(15, 15, 15))
    draw.text((40, 35), "GLOBAL RANKINGS", font=f_title, fill=(255, 255, 255))
    
    # Column Headers
    draw.text((40, 115), "RANK", font=f_label, fill=(100, 100, 100))
    draw.text((140, 115), "PLAYER", font=f_label, fill=(100, 100, 100))
    draw.text((W - 150, 115), "RATING", font=f_label, fill=(100, 100, 100))

    # 4. DRAW PLAYER ROWS
    curr_y = header_h
    for i, p in enumerate(players):
        rank_num = i + 1
        color = p.get('rank_color', (255, 255, 255))
        
        # Zebra striping for rows
        if i % 2 == 0:
            draw.rectangle([(20, curr_y), (W-20, curr_y + row_h - 10)], fill=(10, 10, 10))

        # Rank (Michroma)
        rank_str = f"#{rank_num:02d}"
        rank_fill = color if rank_num <= 3 else (160, 160, 160)
        draw.text((40, curr_y + 15), rank_str, font=f_rank, fill=rank_fill)

        # Player Name (Funnel Sans)
        # Using .upper() to keep that aggressive game feel
        draw.text((140, curr_y + 12), p['name'].upper(), font=f_name, fill=(255, 255, 255))
        
        # Points (Michroma)
        draw.text((W - 150, curr_y + 15), str(p['pts']), font=f_pts, fill=color)

        # Top 3 Glow Accent
        if rank_num <= 3:
            draw.rectangle([(20, curr_y), (26, curr_y + row_h - 10)], fill=color)

        curr_y += row_h

    # 5. FOOTER
    draw.text((W//2, H - 20), "ARCHIVE ARENA // SEASON 1", font=f_label, fill=(60, 60, 60), anchor="mm")

    # Export to buffer
    buf = io.BytesIO()
    card.save(buf, 'PNG')
    buf.seek(0)
    return buf
  
