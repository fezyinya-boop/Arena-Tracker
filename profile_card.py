"""
profile_card.py — Archive Arena profile card generator.


2. Create a /badges/ folder and add your rank badge images:
       badges/rank_diamond.png
       badges/rank_platinum.png
       badges/rank_gold.png
       badges/rank_silver.png
       badges/rank_bronze.png
   (Download each custom emoji the same way you got the others)
3. Add 'pillow' to requirements.txt
4. In main.py add at the top:
       from profile_card import make_profile_card, fetch_avatar
5. Replace your existing profile command with the one at the bottom of this file
"""

from PIL import Image, ImageDraw, ImageFont
import aiohttp
import io
import math
import re
import os
import discord

# ── Font paths ──
FONT_BOLD = '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheros-bold.otf'
FONT_REG  = '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheros-regular.otf'
FONT_COND = '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheroscn-bold.otf'

try:
    ImageFont.truetype(FONT_BOLD, 12)
except:
    FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    FONT_REG  = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    FONT_COND = FONT_BOLD

# ── Rank badge image paths ──
BADGES_DIR = os.path.join(os.path.dirname(__file__), 'badges')
RANK_BADGES = {
    "DIAMOND":  os.path.join(BADGES_DIR, 'rank_diamond.png'),
    "PLATINUM": os.path.join(BADGES_DIR, 'rank_platinum.png'),
    "GOLD":     os.path.join(BADGES_DIR, 'rank_gold.png'),
    "SILVER":   os.path.join(BADGES_DIR, 'rank_silver.png'),
    "BRONZE":   os.path.join(BADGES_DIR, 'rank_bronze.png'),
}


def clean_rank_name(name: str) -> str:
    """Strip Discord custom emoji tags e.g. <:Diamond:123456> from rank name."""
    return re.sub(r'<:[^:]+:\d+>\s*', '', name).strip()


def get_rank_badge(rank_name_raw: str, size: int = 40) -> Image.Image | None:
    """Load and resize a rank badge image by rank name."""
    clean = clean_rank_name(rank_name_raw).upper()
    path = RANK_BADGES.get(clean)
    if not path or not os.path.exists(path):
        return None
    try:
        return Image.open(path).convert('RGBA').resize((size, size), Image.LANCZOS)
    except:
        return None


async def fetch_avatar(url: str) -> Image.Image | None:
    """Fetch a Discord avatar URL and return as PIL Image."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(str(url)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(io.BytesIO(data)).convert('RGBA')
    except:
        pass
    return None


def make_profile_card(
    display_name: str,
    p_title: str,
    p_move: str,
    pts: int,
    wins: int,
    losses: int,
    streak: int,
    pct: float,                   # 0.0–1.0 progress to next rank
    current_rank_raw: str,        # raw rank name e.g. "<:novice:123> SILVER"
    next_rank_raw: str | None,    # raw next rank name, or None if max rank
    rank_color: tuple,            # RGB tuple e.g. (192, 192, 192)
    avatar_img: Image.Image | None = None,
) -> io.BytesIO:
    """
    Generate a profile card and return a BytesIO PNG buffer
    ready to send with discord.File().
    """

    W, H = 800, 360

    # ── Background ──
    card = Image.new('RGBA', (W, H), (30, 31, 36, 255))

    # Edge vignette
    grad = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for x in range(W):
        t = x / W
        alpha = int(55 * (1 - math.sin(t * math.pi)))
        gd.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))
    card = Image.alpha_composite(card, grad)

    # Left accent bar + glow
    acc = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ad = ImageDraw.Draw(acc)
    for i in range(22, 0, -1):
        a = int(16 * (i / 22) ** 2)
        ad.rectangle([(0, 0), (5 + i, H)], fill=(*rank_color, a))
    ad.rectangle([(0, 0), (5, H)], fill=(*rank_color, 255))
    card = Image.alpha_composite(card, acc)

    # Dot grid texture
    dots = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dots)
    for y in range(20, H, 30):
        for x in range(20, W, 30):
            dd.ellipse([(x-1, y-1), (x+1, y+1)], fill=(255, 255, 255, 10))
    card = Image.alpha_composite(card, dots)

    draw = ImageDraw.Draw(card)

    # ── Fonts ──
    f_name   = ImageFont.truetype(FONT_BOLD, 32)
    f_rank   = ImageFont.truetype(FONT_BOLD, 13)
    f_label  = ImageFont.truetype(FONT_REG,  12)
    f_value  = ImageFont.truetype(FONT_BOLD, 15)
    f_pts    = ImageFont.truetype(FONT_COND, 44)
    f_prog   = ImageFont.truetype(FONT_REG,  13)
    f_footer = ImageFont.truetype(FONT_REG,  11)

    # ── Avatar ──
    av_size = 90
    av_x, av_y = 24, 24

    if avatar_img:
        av = avatar_img.resize((av_size, av_size))
    else:
        av = Image.new('RGBA', (av_size, av_size), (55, 57, 63, 255))

    mask = Image.new('L', (av_size, av_size), 0)
    ImageDraw.Draw(mask).ellipse([(0, 0), (av_size-1, av_size-1)], fill=255)
    av_circ = Image.new('RGBA', (av_size, av_size), (0, 0, 0, 0))
    av_circ.paste(av, mask=mask)

    # Rank-colored ring around avatar
    ring_size = av_size + 6
    ring = Image.new('RGBA', (ring_size, ring_size), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse(
        [(0, 0), (ring_size-1, ring_size-1)], outline=(*rank_color, 255), width=3)
    card.paste(ring, (av_x-3, av_y-3), ring)
    card.paste(av_circ, (av_x, av_y), av_circ)

    # Current rank badge pinned to bottom-right corner of avatar
    cur_badge = get_rank_badge(current_rank_raw, size=28)
    if cur_badge:
        card.paste(cur_badge, (av_x + av_size - 24, av_y + av_size - 24), cur_badge)

    # ── Name & rank label ──
    name_x = av_x + av_size + 18
    name_y = av_y + 4
    clean_cur = clean_rank_name(current_rank_raw)
    draw.text((name_x, name_y), display_name, font=f_name, fill=(240, 240, 240, 255))
    draw.text((name_x, name_y + 40), f"{clean_cur}  ·  {p_title}",
              font=f_rank, fill=(*rank_color, 210))

    # ── Divider ──
    sep_y = av_y + av_size + 18
    draw.line([(24, sep_y), (W-24, sep_y)], fill=(255, 255, 255, 18), width=1)

    # ── Stats ──
    col1_x, col2_x, col3_x = 24, 290, 530
    row1_y = sep_y + 16
    row2_y = row1_y + 82

    def stat_block(x, y, label, value, color=(220, 220, 220, 255)):
        draw.text((x, y), label.upper(), font=f_label, fill=(130, 133, 142, 255))
        draw.text((x, y+17), value, font=f_value, fill=color)

    # Rating — large display
    draw.text((col1_x, row1_y-2), "RATING", font=f_label, fill=(130, 133, 142, 255))
    pts_str = str(pts)
    draw.text((col1_x, row1_y+14), pts_str, font=f_pts, fill=(*rank_color, 255))
    rp_offset = len(pts_str) * 24 + 4
    draw.text((col1_x + rp_offset, row1_y+36), "RP", font=f_label, fill=(130, 133, 142, 255))

    # Record
    total = wins + losses
    wr = round((wins / total) * 100) if total > 0 else 0
    stat_block(col2_x, row1_y, "Record", f"{wins}W  {losses}L")
    draw.text((col2_x, row1_y+36), f"{wr}% win rate", font=f_label, fill=(130, 133, 142, 200))

    # Streak
    streak_color = (255, 165, 30, 255) if streak >= 3 else (220, 220, 220, 255)
    stat_block(col3_x, row1_y, "🔥 Streak" if streak >= 3 else "Streak",
               f"{streak} Win Streak" if streak > 0 else "No Streak", streak_color)

    draw.line([(24, row2_y-10), (W-24, row2_y-10)], fill=(255, 255, 255, 12), width=1)

    # Signature move
    stat_block(col1_x, row2_y, "✨ Signature Move", p_move)

    # ── Progress bar ──
    bar_y = row2_y + 54
    bar_x = 24
    badge_size = 40
    bar_w = W - 48 - badge_size - 14
    bar_h = 10
    bar_r = 5

    draw.rounded_rectangle([(bar_x, bar_y), (bar_x+bar_w, bar_y+bar_h)],
                             radius=bar_r, fill=(48, 50, 57, 255))
    fill_w = max(int(bar_w * min(pct, 1.0)), bar_r * 2)
    draw.rounded_rectangle([(bar_x, bar_y), (bar_x+fill_w, bar_y+bar_h)],
                             radius=bar_r, fill=(*rank_color, 255))

    # Glow at fill tip
    glow_x = bar_x + fill_w
    for gi in range(14, 0, -1):
        ga = int(55 * (gi / 14) ** 2)
        draw.ellipse([(glow_x-gi, bar_y-gi//2), (glow_x+gi, bar_y+bar_h+gi//2)],
                      fill=(*rank_color, ga))

    # Progress text + next rank badge
    if next_rank_raw:
        clean_next = clean_rank_name(next_rank_raw)
        pct_int = int(pct * 100)
        draw.text((bar_x, bar_y+bar_h+7), f"{pct_int}% to {clean_next}",
                  font=f_prog, fill=(150, 153, 162, 255))
        next_badge = get_rank_badge(next_rank_raw, size=badge_size)
        if next_badge:
            badge_x = bar_x + bar_w + 10
            badge_y = bar_y + bar_h // 2 - badge_size // 2
            card.paste(next_badge, (badge_x, badge_y), next_badge)
    else:
        draw.text((bar_x, bar_y+bar_h+7), "MAX RANK REACHED",
                  font=f_prog, fill=(*rank_color, 255))

    # ── Footer ──
    footer_y = H - 20
    draw.line([(24, footer_y-10), (W-24, footer_y-10)], fill=(255, 255, 255, 12), width=1)
    draw.text((W // 2, footer_y), "Archive Arena  ·  Season 1",
              font=f_footer, fill=(75, 77, 86, 255), anchor="mm")

    # ── Rounded border ──
    border = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(
        [(0, 0), (W-1, H-1)], radius=12, outline=(58, 60, 67, 255), width=1)
    card = Image.alpha_composite(card, border)

    buf = io.BytesIO()
    card.save(buf, 'PNG')
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════════════
# DROP-IN REPLACEMENT FOR YOUR profile COMMAND IN main.py
# ══════════════════════════════════════════════════════════════════

"""
@bot.command()
async def profile(ctx, member: discord.Member = None):
    member = member or ctx.author

    # 1. Fetch user data (unchanged)
    data = get_or_create_user(member.id, member.display_name)
    pts = data[2]

    # 2. Fetch profile data (unchanged)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT title, signature_move, embed_color FROM profiles WHERE user_id = ?", (str(member.id),))
    bio = c.fetchone() or ("Aspirant", "None", None)
    conn.close()
    p_title, p_move, p_color = bio

    # 3. Rank logic (unchanged)
    r_info = get_rank_info(pts)
    next_rank = next((r for r in reversed(RANKS) if r['min'] > pts), None)

    # 4. Progress percent
    if next_rank:
        total_needed = next_rank['min'] - r_info['min']
        current_progress = pts - r_info['min']
        pct = max(0.0, min(current_progress / total_needed, 1.0))
        next_rank_raw = next_rank['name']
    else:
        pct = 1.0
        next_rank_raw = None

    # 5. Rank color — convert hex int to RGB tuple
    try:
        hex_color = p_color if p_color else hex(r_info["color"])[2:].zfill(6)
        rank_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    except:
        rank_color = (230, 160, 30)

    # 6. Fetch avatar
    avatar_img = await fetch_avatar(member.display_avatar.url)

    # 7. Generate and send card
    async with ctx.typing():
        buf = make_profile_card(
            display_name=member.display_name,
            p_title=p_title,
            p_move=p_move,
            pts=pts,
            wins=data[3],
            losses=data[4],
            streak=data[5],
            pct=pct,
            current_rank_raw=r_info['name'],
            next_rank_raw=next_rank_raw,
            rank_color=rank_color,
            avatar_img=avatar_img,
        )

    await ctx.send(file=discord.File(buf, filename='profile.png'))
"""
  
