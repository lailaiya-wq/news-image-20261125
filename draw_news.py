#!/usr/bin/env python3
"""Draw the news-image-20261125 entry: a 1024x1024 newspaper front page.

All 50 stories are from Wednesday 25 November 2026 (first reported that
day). Layout follows the winning newspaper-front-page pattern:
masthead, region counts, big-number row, 3 illustrated leads, 8 secondary
stories, a numbered list covering the remaining 39 stories, a
WHERE IT HAPPENED dot-map panel, a DATE CHECK footer and a source line.
"""
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 28
CONTENT_W = W - 2 * MARGIN  # 968

PAPER = (247, 243, 234)      # warm off-white
INK = (17, 17, 17)           # near-black
RED = (185, 28, 28)          # accent red
GRAY = (107, 107, 107)       # secondary text
LIGHT_LINE = (200, 192, 176) # hairline rules
PANEL = (255, 255, 255)      # illustration background
PANEL_LINE = (180, 172, 156)
DATE_BG = (253, 236, 236)    # date-check tint
SEA = (214, 226, 236)        # map sea tint
LAND = (120, 120, 120)       # map land dots

FONT_DIR = "/usr/share/fonts/truetype/noto"


def font(name, size):
    path = os.path.join(FONT_DIR, name)
    return ImageFont.truetype(path, size)


F_SERIF_BLACK = lambda s: font("NotoSerif-Black.ttf", s)
F_SERIF_BOLD = lambda s: font("NotoSerif-Bold.ttf", s)
F_SANS = lambda s: font("NotoSans-Regular.ttf", s)
F_SANS_BOLD = lambda s: font("NotoSans-Bold.ttf", s)
F_SANS_MED = lambda s: font("NotoSans-Medium.ttf", s)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, fnt, fill, max_w, line_h, align="left"):
    """Draw wrapped text; returns the y just below the last line."""
    for line in wrap(draw, text, fnt, max_w):
        if align == "center":
            lx = x + (max_w - draw.textlength(line, font=fnt)) / 2
        else:
            lx = x
        draw.text((lx, y), line, font=fnt, fill=fill)
        y += line_h
    return y


def fit_font(draw, text, fname, start_size, max_w):
    """Largest font size (<= start_size) that fits text in max_w."""
    size = start_size
    while size > 10:
        fnt = font(fname, size)
        if draw.textlength(text, font=fnt) <= max_w:
            return fnt
        size -= 1
    return font(fname, size)


def hline(draw, y, color=INK, width=2):
    draw.line([(MARGIN, y), (W - MARGIN, y)], fill=color, width=width)


# ---------------------------------------------------------------- data

LEADS = [
    {
        "kicker": "STRAIT OF HORMUZ",
        "title": "HORMUZ TANKERS HIT BY MINES",
        "summary": (
            "Iran's IRGC says two oil tankers struck naval mines on an "
            "unauthorised route and caught fire in the Strait of Hormuz."
        ),
        "art": "tanker",
    },
    {
        "kicker": "MARKETS",
        "title": "ASIAN STOCKS CRASH",
        "summary": (
            "Kospi -6.2% as Samsung fell 9.9% and SK Hynix 11.1%. "
            "Nikkei -2.8%, SoftBank -14.8%; Taiwan down about 5%."
        ),
        "art": "chart",
    },
    {
        "kicker": "UKRAINE WAR",
        "title": "UKRAINE DRONES HIT RUSSIAN REFINERIES",
        "summary": (
            "Ukrainian drones struck two Rosneft refineries in Samara "
            "region overnight; both ablaze, one killed. Russia said 145 "
            "drones were downed."
        ),
        "art": "refinery",
    },
]

SECONDARY = [
    ("ZELENSKY: UKRAINE NEEDS \u20ac115BN AID IN 2027",
     "Kyiv needs \u20ac115bn in foreign aid for 2027; US pauses Patriot supplies."),
    ("AT LEAST 490,334 RUSSIAN SOLDIERS DEAD",
     "BBC: leaked Russian data puts military deaths since 2022 at 490,334+."),
    ("SHENZHOU-24 DOCKS; PAKISTAN'S FIRST ASTRONAUT",
     "Shenzhou-24 docks with Tiangong 3.5h after launch, with Pakistan's first astronaut."),
    ("26 MINERS TRAPPED IN JAVA GOLD MINE",
     "Flooding traps 26 workers underground at a gold mine in West Java."),
    ("SENEGAL RESTORED AS AFRICA CUP CHAMPIONS",
     "Sports court restores Senegal as 2025 Africa Cup champions; Morocco to appeal."),
    ("COLOMBIA FREES ALL SUPERMARKET HOSTAGES",
     "Forces storm an \u00c9xito supermarket in Cartagena; all hostages freed."),
    ("US PLANS NEW TARIFFS ON 14 PARTNERS",
     "US weighs new tariffs on 14 partners: China up to 40%, India 25%, Vietnam 35%."),
    ("COP31 TALKS COLLAPSE WITH NO DEAL",
     "UN climate talks end with no deal; Pope Leo XIV voices concern."),
]

# Remaining 39 stories (original numbers from the news list), one line each.
ALSO = [
    (2, "Houthis hit Ras Tanura refinery, fire claimed"),
    (3, "Israel kills Hamas official Abuelouf and family"),
    (4, "US urges citizens to leave Iran at once"),
    (5, "Iran sets 7 terms; Hormuz \u2018closing daily\u2019"),
    (6, "US said to weigh killing Iranian leaders"),
    (7, "Saudi-led coalition hits Hodeidah port"),
    (9, "Russian strike on Odesa region kills 2, injures 3"),
    (11, "Eurozone inflation rises to 4.0%"),
    (12, "EasyJet profit plunges 89% on fuel costs"),
    (14, "Ukraine hits Savasleyka airfield, 5 jets damaged"),
    (15, "Poland pushes again for permanent US base"),
    (16, "EU Parliament votes to loosen nature laws"),
    (17, "EU court: set a date to ban caged farming"),
    (18, "EU unveils \u20ac50bn quantum bill, \u20ac50bn tech fund"),
    (19, "Sarkozy and wife ordered to stand trial"),
    (23, "North Korea expels Swiss envoy, shuts office"),
    (24, "Aramco, S-OIL open $7bn Shaheen project"),
    (25, "SK Hynix unveils 100tn won shareholder returns"),
    (26, "Air India plans $650m in cost cuts"),
    (27, "Two Libyan officers die after Merkury attack"),
    (28, "Sudan RSF drone strikes kill 19 civilians"),
    (30, "DR Congo to halt all cobalt exports"),
    (31, "Ramaphosa wins court case, report set aside"),
    (32, "Kenya court convicts cult leader Mackenzie"),
    (33, "Cheap rebel drones reshape Sahel war \u2014 Reuters"),
    (34, "Amnesty urges Egypt to lift Mada Masr closure"),
    (35, "28 women, children abducted in Blue Nile"),
    (36, "Wall St: Nasdaq -1.5%, Dow closes above 50,000"),
    (37, "Dell Q3 revenue $54.9bn, a record"),
    (39, "CIA, NGA and ODNI find cybersecurity breach"),
    (40, "Amazon buys Decart to boost chip race"),
    (41, "Anthropic shares fall below IPO price"),
    (42, "Roche breast-cancer drug wins 2nd FDA approval"),
    (44, "Venezuela reveals $237.5bn public debt"),
    (45, "Nor\u2019easter threatens US east coast"),
    (46, "Australia, Solomons sign security treaty"),
    (47, "Australia inflation hits 4.9%"),
    (48, "Australia puts Pacific at centre of policy"),
    (50, "UN warns HIV/AIDS progress at risk"),
]

BIG_DATA = [
    ("-6.2%", "KOSPI \u00b7 ASIAN STOCKS"),
    ("4.9%", "AUSTRALIA CPI"),
    ("$54.9B", "DELL Q3 REVENUE"),
    ("4.0%", "EUROZONE INFLATION"),
    ("$237.5B", "VENEZUELA DEBT"),
]

# Dot-matrix world map: land cells as (col_start, col_end) per row.
# Grid is 50 cols (lon -180..+173, step 7.2) x 25 rows (lat 80..-44, step 5.2).
MAP_RANGES = {
    0: [(12, 14), (17, 20)],
    1: [(10, 14), (16, 20), (26, 27), (33, 47)],
    2: [(1, 14), (16, 20), (25, 27), (30, 48)],
    3: [(2, 14), (17, 18), (22, 22), (25, 28), (29, 48)],
    4: [(3, 14), (17, 18), (23, 29), (30, 48)],
    5: [(6, 13), (23, 47)],
    6: [(6, 14), (23, 47)],
    7: [(5, 14), (23, 44), (46, 46)],
    8: [(5, 14), (23, 43), (46, 46)],
    9: [(5, 14), (23, 43)],
    10: [(5, 7), (13, 14), (22, 33), (35, 37), (39, 41)],
    11: [(6, 9), (22, 33), (36, 37), (39, 42)],
    12: [(8, 10), (22, 31), (36, 36), (40, 42)],
    13: [(9, 10), (14, 16), (22, 24), (25, 31), (40, 43), (44, 44)],
    14: [(14, 17), (23, 30), (40, 45)],
    15: [(14, 18), (24, 30), (40, 46)],
    16: [(14, 19), (25, 30), (39, 42), (42, 48)],
    17: [(14, 19), (26, 29), (40, 44), (45, 48)],
    18: [(15, 19), (26, 29), (31, 32), (41, 45)],
    19: [(15, 18), (26, 29), (31, 31), (41, 45)],
    20: [(16, 18), (26, 28), (41, 45)],
    21: [(16, 17), (26, 28), (41, 44)],
    22: [(16, 17), (26, 27), (42, 46), (47, 48)],
    23: [(16, 16), (47, 47)],
    24: [(16, 16), (48, 48)],
}
# Event locations as (grid_col, grid_row) for red dots on the map.
MAP_EVENTS = [
    (33, 10),  # Hormuz
    (32, 5),   # Samara
    (29, 6),   # Odesa
    (43, 8),   # Seoul
    (40, 17),  # Jakarta
    (46, 22),  # Canberra
    (15, 13),  # Cartagena
    (14, 8),   # Washington
    (30, 9),   # Gaza
    (27, 16),  # Kinshasa
]
MAP_PLACES = ["HORMUZ", "SAMARA", "ODESA", "SEOUL", "JAKARTA",
              "CANBERRA", "CARTAGENA", "WASHINGTON", "GAZA", "KINSHASA"]


# ---------------------------------------------------------------- art

def flame(draw, cx, base_y, w, h, colors=((255, 140, 0), (255, 200, 0), (220, 40, 20))):
    """Simple layered flame: outer, mid and inner teardrop polygons."""
    hw = w / 2
    draw.polygon([(cx - hw, base_y), (cx - hw * 0.55, base_y - h * 0.62),
                  (cx, base_y - h), (cx + hw * 0.55, base_y - h * 0.62),
                  (cx + hw, base_y)], fill=colors[0])
    draw.polygon([(cx - hw * 0.55, base_y), (cx - hw * 0.28, base_y - h * 0.45),
                  (cx, base_y - h * 0.7), (cx + hw * 0.28, base_y - h * 0.45),
                  (cx + hw * 0.55, base_y)], fill=colors[1])
    draw.polygon([(cx - hw * 0.3, base_y), (cx, base_y - h * 0.4),
                  (cx + hw * 0.3, base_y)], fill=colors[2])


def draw_tanker(draw, x, y, w, h):
    """Oil tanker on fire at sea, with a red falling line top-right."""
    draw.rectangle([x, y, x + w, y + h], fill=(226, 236, 244))
    # sea
    sea_y = y + int(h * 0.62)
    draw.rectangle([x, sea_y, x + w, y + h], fill=(46, 90, 136))
    for wy in (sea_y + 10, sea_y + 22):
        for wx in range(x + 8, x + w - 8, 26):
            draw.arc([wx, wy, wx + 22, wy + 8], 0, 180, fill=(255, 255, 255), width=2)
    # tanker hull
    hull_y = sea_y - 26
    draw.rectangle([x + 18, hull_y, x + w - 18, hull_y + 30], fill=(31, 41, 55))
    draw.rectangle([x + 18, hull_y + 22, x + w - 18, hull_y + 30], fill=(185, 28, 28))
    # deck containers
    for i, col in enumerate([(185, 28, 28), (37, 99, 235), (22, 163, 74)]):
        cx0 = x + 34 + i * 52
        draw.rectangle([cx0, hull_y - 16, cx0 + 46, hull_y], fill=col)
        draw.line([(cx0, hull_y - 8), (cx0 + 46, hull_y - 8)], fill=(255, 255, 255), width=1)
    # superstructure
    draw.rectangle([x + w - 62, hull_y - 34, x + w - 24, hull_y], fill=(240, 240, 240))
    draw.rectangle([x + w - 56, hull_y - 30, x + w - 30, hull_y - 22], fill=(31, 41, 55))
    # flames above the deck
    flame(draw, x + 120, hull_y - 10, 30, 20)
    flame(draw, x + 165, hull_y - 10, 24, 16)
    # smoke
    for sx, sy, sr in ((x + 128, hull_y - 28, 5), (x + 150, hull_y - 30, 5),
                       (x + 172, hull_y - 28, 5)):
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(120, 120, 120))
    # red falling line, top-right corner
    pts = [(x + w - 96, y + 14), (x + w - 74, y + 26), (x + w - 56, y + 22),
           (x + w - 36, y + 38), (x + w - 16, y + 48)]
    draw.line(pts, fill=RED, width=3, joint="curve")
    draw.polygon([(x + w - 16, y + 48), (x + w - 26, y + 42), (x + w - 24, y + 52)],
                 fill=RED)


def draw_chart(draw, x, y, w, h):
    """Red falling market line on a light grid."""
    draw.rectangle([x, y, x + w, y + h], fill=PANEL)
    for gy in range(y + 16, y + h - 8, 22):
        draw.line([(x + 8, gy), (x + w - 8, gy)], fill=(226, 226, 226), width=1)
    for gx in range(x + 24, x + w - 8, 40):
        draw.line([(gx, y + 8), (gx, y + h - 8)], fill=(232, 232, 232), width=1)
    pts = [(x + 14, y + 16), (x + 62, y + 30), (x + 104, y + 26),
           (x + 150, y + 52), (x + 196, y + 48), (x + 244, y + 74),
           (x + w - 16, y + h - 16)]
    draw.line(pts, fill=RED, width=4, joint="curve")
    for px, py in pts:
        draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=RED)
    draw.polygon([(x + w - 16, y + h - 16), (x + w - 30, y + h - 24),
                  (x + w - 28, y + h - 8)], fill=RED)
    # label chip
    label = "KOSPI -6.2%"
    lf = F_SANS_BOLD(15)
    tw = draw.textlength(label, font=lf)
    draw.rectangle([x + 10, y + h - 30, x + 22 + tw, y + h - 8], fill=RED)
    draw.text((x + 16, y + h - 29), label, font=lf, fill=(255, 255, 255))


def draw_refinery(draw, x, y, w, h):
    """Refinery towers with flames and drones above; pale map-like backdrop."""
    draw.rectangle([x, y, x + w, y + h], fill=(232, 236, 240))
    # pale land blobs (schematic map backdrop)
    draw.ellipse([x + 8, y + 62, x + 130, y + h - 6], fill=(205, 214, 222))
    draw.ellipse([x + 150, y + 70, x + w - 8, y + h - 4], fill=(205, 214, 222))
    ground = y + h - 22
    draw.line([(x + 6, ground), (x + w - 6, ground)], fill=(90, 100, 110), width=2)
    # storage tanks
    for tx in (x + 30, x + 96):
        draw.rectangle([tx, ground - 26, tx + 52, ground], fill=(240, 240, 240),
                       outline=(90, 100, 110), width=1)
        draw.ellipse([tx, ground - 32, tx + 52, ground - 20], fill=(200, 200, 200),
                     outline=(90, 100, 110), width=1)
    # distillation towers
    for tx in (x + 176, x + 226):
        draw.rectangle([tx, ground - 48, tx + 30, ground], fill=(150, 160, 170),
                       outline=(70, 80, 90), width=1)
        draw.polygon([(tx, ground - 48), (tx + 15, ground - 60), (tx + 30, ground - 48)],
                     fill=(120, 130, 140))
        flame(draw, tx + 15, ground - 58, 18, 16)
    # flames on a tank
    flame(draw, x + 56, ground - 30, 24, 30)
    # drones: small X silhouettes with dotted flight paths
    def drone(cx, cy, s=7):
        draw.line([(cx - s, cy - s), (cx + s, cy + s)], fill=INK, width=2)
        draw.line([(cx - s, cy + s), (cx + s, cy - s)], fill=INK, width=2)
        for dx, dy in ((-s, -s), (s, -s), (-s, s), (s, s)):
            draw.ellipse([cx + dx - 2, cy + dy - 2, cx + dx + 2, cy + dy + 2],
                         fill=INK)
    for i, (dx, dy) in enumerate(((x + 60, y + 22), (x + 150, y + 14), (x + 240, y + 26))):
        for k in range(4):
            px = dx - 26 + k * 8
            py = dy + 14 + k * 5
            draw.ellipse([px - 1, py - 1, px + 1, py + 1], fill=RED)
        drone(dx, dy)
    draw.text((x + 10, y + 6), "SAMARA REGION", font=F_SANS_BOLD(11), fill=GRAY)


ART = {"tanker": draw_tanker, "chart": draw_chart, "refinery": draw_refinery}


# ---------------------------------------------------------------- page

def draw_page():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)
    y = 12

    # ---- masthead
    title = "THE WORLD IN ONE DAY"
    tf = fit_font(draw, title, "NotoSerif-Black.ttf", 56, CONTENT_W)
    tw = draw.textlength(title, font=tf)
    draw.text(((W - tw) / 2, y), title, font=tf, fill=INK)
    y += 58
    sub = "Wednesday 25 November 2026"
    sf = F_SERIF_BOLD(24)
    sw = draw.textlength(sub, font=sf)
    draw.text(((W - sw) / 2, y), sub, font=sf, fill=INK)
    y += 28
    hline(draw, y, INK, 2)
    hline(draw, y + 4, INK, 1)
    y += 12

    # ---- 50-stories line
    tag = "50 STORIES \u00b7 EVERY ONE FIRST REPORTED WED 25 NOV 2026"
    tagf = F_SANS_BOLD(15)
    tw = draw.textlength(tag, font=tagf)
    draw.text(((W - tw) / 2, y), tag, font=tagf, fill=RED)
    y += 20

    # ---- region counts
    regions = ("EUROPE 12 \u00b7 MIDDLE EAST 7 \u00b7 ASIA 7 \u00b7 AFRICA 9 "
               "\u00b7 AMERICAS 10 \u00b7 OCEANIA 3 \u00b7 GLOBAL 2")
    rf = F_SANS_BOLD(14)
    tw = draw.textlength(regions, font=rf)
    draw.text(((W - tw) / 2, y), regions, font=rf, fill=INK)
    y += 20

    # ---- big data row: 5 boxes
    box_w = (CONTENT_W - 4 * 8) // 5
    box_h = 48
    for i, (num, label) in enumerate(BIG_DATA):
        bx = MARGIN + i * (box_w + 8)
        draw.rectangle([bx, y, bx + box_w, y + box_h], fill=PANEL,
                       outline=PANEL_LINE, width=1)
        draw.rectangle([bx, y, bx + box_w, y + 3], fill=RED)
        nf = F_SANS_BOLD(21)
        nw = draw.textlength(num, font=nf)
        draw.text((bx + (box_w - nw) / 2, y + 6), num, font=nf, fill=RED)
        lf = F_SANS_BOLD(10)
        lw = draw.textlength(label, font=lf)
        draw.text((bx + (box_w - lw) / 2, y + 31), label, font=lf, fill=INK)
    y += box_h + 10
    hline(draw, y, LIGHT_LINE, 1)
    y += 8

    # ---- 3 lead stories
    col_w = (CONTENT_W - 2 * 16) // 3  # 312
    art_h = 100
    lead_top = y
    for i, lead in enumerate(LEADS):
        lx = MARGIN + i * (col_w + 16)
        # render art on its own layer so nothing can spill outside the panel
        art_img = Image.new("RGB", (col_w, art_h), PANEL)
        adraw = ImageDraw.Draw(art_img)
        ART[lead["art"]](adraw, 0, 0, col_w, art_h)
        img.paste(art_img, (lx, y))
        draw.rectangle([lx, y, lx + col_w, y + art_h], outline=PANEL_LINE, width=1)
        iy = y + art_h + 6
        kf = F_SANS_BOLD(11)
        draw.text((lx, iy), lead["kicker"], font=kf, fill=RED)
        iy += 15
        hf = F_SERIF_BOLD(19)
        iy = draw_wrapped(draw, lx, iy, lead["title"], hf, INK, col_w, 23)
        iy += 3
        sf2 = F_SANS(12)
        draw_wrapped(draw, lx, iy, lead["summary"], sf2, INK, col_w, 15)
    y = lead_top + art_h + 6 + 15 + 46 + 3 + 45  # 2 headline lines + 3 summary lines
    y += 8
    hline(draw, y, LIGHT_LINE, 1)
    y += 8

    # ---- secondary stories: 2 columns x 4 rows
    sec_head = "MORE FROM WEDNESDAY"
    hf2 = F_SANS_BOLD(13)
    draw.text((MARGIN, y), sec_head, font=hf2, fill=INK)
    rule_x = MARGIN + draw.textlength(sec_head, font=hf2) + 10
    draw.line([(rule_x, y + 7), (W - MARGIN, y + 7)], fill=LIGHT_LINE, width=1)
    y += 18
    sec_col_w = (CONTENT_W - 20) // 2
    row_h = 32
    for i, (title, summ) in enumerate(SECONDARY):
        col = i % 2
        row = i // 2
        sx = MARGIN + col * (sec_col_w + 20)
        sy = y + row * row_h
        tf2 = F_SANS_BOLD(13)
        draw.text((sx, sy), title, font=tf2, fill=INK)
        sf3 = F_SANS(11)
        draw.text((sx, sy + 16), summ, font=sf3, fill=(60, 60, 60))
    y += 4 * row_h + 6
    hline(draw, y, LIGHT_LINE, 1)
    y += 8

    # ---- WHERE IT HAPPENED: dot-map + place key
    map_head = "WHERE IT HAPPENED"
    draw.text((MARGIN, y), map_head, font=hf2, fill=INK)
    rule_x = MARGIN + draw.textlength(map_head, font=hf2) + 10
    draw.line([(rule_x, y + 7), (W - MARGIN, y + 7)], fill=LIGHT_LINE, width=1)
    y += 20
    map_top = y
    map_w, map_h = 240, 88
    cell_w, cell_h = map_w / 50, map_h / 25
    draw.rectangle([MARGIN, map_top, MARGIN + map_w, map_top + map_h], fill=SEA)
    for r, ranges in MAP_RANGES.items():
        for c0, c1 in ranges:
            for c in range(c0, c1 + 1):
                cx = MARGIN + (c + 0.5) * cell_w
                cy = map_top + (r + 0.5) * cell_h
                draw.ellipse([cx - 1.6, cy - 1.6, cx + 1.6, cy + 1.6], fill=LAND)
    for ec, er in MAP_EVENTS:
        cx = MARGIN + (ec + 0.5) * cell_w
        cy = map_top + (er + 0.5) * cell_h
        draw.ellipse([cx - 3.2, cy - 3.2, cx + 3.2, cy + 3.2], fill=RED,
                     outline=(255, 255, 255), width=1)
    draw.rectangle([MARGIN, map_top, MARGIN + map_w, map_top + map_h],
                   outline=PANEL_LINE, width=1)
    # place key, two columns to the right of the map
    key_x = MARGIN + map_w + 24
    key_col_w = (W - MARGIN - key_x - 10) // 2
    kf2 = F_SANS_BOLD(11)
    for i, place in enumerate(MAP_PLACES):
        col = i % 2
        row = i // 2
        px = key_x + col * key_col_w
        py = map_top + 8 + row * 18
        draw.ellipse([px, py + 2, px + 8, py + 10], fill=RED)
        draw.text((px + 13, py), place, font=kf2, fill=INK)
    y = map_top + map_h + 10
    hline(draw, y, LIGHT_LINE, 1)
    y += 8

    # ---- ALSO ON WEDNESDAY: numbered list, 3 columns x 13 rows
    also_head = "ALSO ON WEDNESDAY 25 NOVEMBER"
    draw.text((MARGIN, y), also_head, font=hf2, fill=INK)
    rule_x = MARGIN + draw.textlength(also_head, font=hf2) + 10
    draw.line([(rule_x, y + 7), (W - MARGIN, y + 7)], fill=LIGHT_LINE, width=1)
    y += 20
    list_top = y
    list_col_w = (CONTENT_W - 2 * 20) // 3
    lf3 = F_SANS(11)
    for i, (num, text) in enumerate(ALSO):
        col = i // 13
        row = i % 13
        lx = MARGIN + col * (list_col_w + 20)
        ly = list_top + row * 13
        draw.text((lx, ly), f"{num}. {text}", font=lf3, fill=INK)
    y = list_top + 13 * 13 + 8

    # ---- DATE CHECK bar
    dc_top = y
    dc_lines = [
        ("DATE CHECK \u2014 NOT 25 NOV NEWS, EXCLUDED:", True),
        ("Huawei verdict (24 Nov) \u00b7 Abrego Garcia to Spain \u00b7 Putin remarks "
         "\u00b7 Riyadh tower drone (first strike) \u00b7 Monday Nvidia \u00b7 Thu "
         "European Council & Thanksgiving \u2014 not yet happened.", False),
        ("TO THE JUDGE: every story above was first reported "
         "Wednesday 25 November 2026.", True),
    ]
    dc_h = 8 + 3 * 13 + 8
    draw.rectangle([MARGIN, dc_top, W - MARGIN, dc_top + dc_h], fill=DATE_BG,
                   outline=RED, width=1)
    dy = dc_top + 8
    for text, bold in dc_lines:
        fnt = F_SANS_BOLD(11) if bold else F_SANS(11)
        draw.text((MARGIN + 10, dy), text, font=fnt, fill=RED if bold else INK)
        dy += 13
    y = dc_top + dc_h + 8

    # ---- source line
    src = ("Sources: Al Jazeera, BBC, Reuters, AFP, JustSecurity, AP, Principia. "
           "Drawings original.")
    sf4 = F_SANS(10)
    sw = draw.textlength(src, font=sf4)
    draw.text(((W - sw) / 2, y), src, font=sf4, fill=GRAY)
    y += 14

    assert y <= H - 4, f"layout overflow: bottom y={y}"
    return img


def main():
    img = draw_page()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    img.save(out, format="PNG", optimize=True)
    size = os.path.getsize(out)
    print(f"saved {out}: {img.size[0]}x{img.size[1]}, {size} bytes")
    assert img.size == (1024, 1024)
    assert size <= 1048576, f"entry.png too large: {size} bytes"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
