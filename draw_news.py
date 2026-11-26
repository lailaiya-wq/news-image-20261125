#!/usr/bin/env python3
"""Render the deterministic 1024-square 'World in One Day' front page.

Story IDs refer to ../news-list.md; display numbers 1–50 are a separate,
continuous reading order. All copy is local: the source list and the supplied
v2 revision copy. The source's seven regions and two Cartagena arrests take
precedence over the two contradictory numbers in that revision copy.

No network, random state, external images, clock, or source-file reads are
used by the renderer. Fonts are the locally installed Noto families. Render
at 3x, check text bounds, and downsample once for clean small typography.
"""
import math
import os
from collections import Counter
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 28
CONTENT_W = W - 2 * MARGIN
SCALE = 3

PAPER = (247, 243, 234)
INK = (17, 17, 17)
RED = (185, 28, 28)
GRAY = (107, 107, 107)
LIGHT_LINE = (200, 192, 176)
PANEL = (255, 255, 255)
PANEL_LINE = (180, 172, 156)
DATE_BG = (253, 236, 236)
SEA = (227, 235, 237)
LAND = (142, 153, 153)
NAVY = (19, 36, 55)
TEAL = (42, 104, 111)
GOLD = (208, 165, 86)
FONT_DIR = "/usr/share/fonts/truetype/noto"


@lru_cache(maxsize=None)
def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), round(size * SCALE))


def F_SERIF_BLACK(s):
    return font("NotoSerif-Black.ttf", s)


def F_SERIF_BOLD(s):
    return font("NotoSerif-Bold.ttf", s)


def F_SERIF_BLACK_ITALIC(s):
    return font("NotoSerif-BlackItalic.ttf", s)


def F_SERIF_BOLD_ITALIC(s):
    return font("NotoSerif-BoldItalic.ttf", s)


def F_SANS(s):
    return font("NotoSans-Regular.ttf", s)


def F_SANS_BOLD(s):
    return font("NotoSans-Bold.ttf", s)


def F_SANS_MED(s):
    return font("NotoSans-Medium.ttf", s)


def F_COND(s):
    return font("NotoSans-Condensed.ttf", s)


class Canvas:
    """ImageDraw in logical pixels, with checked, top-anchored text."""

    def __init__(self, image):
        self.raw = ImageDraw.Draw(image)
        self.w, self.h = image.width / SCALE, image.height / SCALE
        self.text_boxes = []

    @staticmethod
    def box(xy):
        return tuple(round(v * SCALE) for v in xy)

    @staticmethod
    def points(xy):
        return [(round(x * SCALE), round(y * SCALE)) for x, y in xy]

    def textlength(self, text, font):
        return self.raw.textlength(text, font=font) / SCALE

    def textbbox(self, xy, text, font, anchor="lt"):
        b = self.raw.textbbox(self.box(xy), text, font=font, anchor=anchor)
        return tuple(v / SCALE for v in b)

    def text(self, xy, text, font, fill=INK, anchor="lt"):
        bounds = self.textbbox(xy, text, font, anchor)
        if anchor == "lt" and bounds[0] < xy[0]:
            # Noto's J and some italic glyphs have negative bearings.
            xy = (xy[0] + math.ceil((xy[0] - bounds[0]) * SCALE) / SCALE, xy[1])
            bounds = self.textbbox(xy, text, font, anchor)
        assert bounds[0] >= 0 and bounds[1] >= 0, (text, bounds)
        assert bounds[2] <= self.w and bounds[3] <= self.h, (text, bounds)
        self.text_boxes.append((bounds, text))
        self.raw.text(self.box(xy), text, font=font, fill=fill, anchor=anchor)

    def rectangle(self, xy, fill=None, outline=None, width=1):
        self.raw.rectangle(self.box(xy), fill=fill, outline=outline,
                           width=max(1, round(width * SCALE)))

    def rounded_rectangle(self, xy, radius=2, fill=None, outline=None, width=1):
        self.raw.rounded_rectangle(self.box(xy), radius=round(radius * SCALE),
                                   fill=fill, outline=outline,
                                   width=max(1, round(width * SCALE)))

    def ellipse(self, xy, fill=None, outline=None, width=1):
        self.raw.ellipse(self.box(xy), fill=fill, outline=outline,
                         width=max(1, round(width * SCALE)))

    def polygon(self, xy, fill=None):
        self.raw.polygon(self.points(xy), fill=fill)

    def line(self, xy, fill=INK, width=1, joint="curve"):
        self.raw.line(self.points(xy), fill=fill, width=max(1, round(width * SCALE)),
                      joint=joint)

    def arc(self, xy, start, end, fill=INK, width=1):
        self.raw.arc(self.box(xy), start, end, fill=fill,
                     width=max(1, round(width * SCALE)))


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; never silently truncate a word or a story."""
    lines, cur = [], ""
    for word in text.split(" "):
        assert draw.textlength(word, font=fnt) <= max_w, (word, max_w)
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, fnt, fill, max_w, line_h, align="left"):
    for line in wrap(draw, text, fnt, max_w):
        lx = x + (max_w - draw.textlength(line, font=fnt)) / 2 if align == "center" else x
        draw.text((lx, y), line, font=fnt, fill=fill)
        y += line_h
    return y


def fit_font(draw, text, fname, start_size, max_w, min_size=6):
    """Fit in 1/3-pixel increments, accounting for italic ink overhang."""
    for step in range(round(start_size * SCALE), round(min_size * SCALE) - 1, -1):
        fnt = font(fname, step / SCALE)
        bbox = draw.textbbox((0, 0), text, fnt)
        if max(draw.textlength(text, font=fnt), bbox[2] - bbox[0]) <= max_w:
            return fnt
    raise AssertionError(f"Text cannot fit in {max_w}px: {text}")


def fit_lines(draw, text, fname, size, width, max_lines, min_size):
    for step in range(round(size * SCALE), round(min_size * SCALE) - 1, -1):
        fnt = font(fname, step / SCALE)
        if len(wrap(draw, text, fnt, width)) <= max_lines:
            return fnt
    raise AssertionError(f"Too many lines: {text}")


def hline(draw, y, color=INK, width=2):
    draw.line([(MARGIN, y), (W - MARGIN, y)], fill=color, width=width)


def centered(draw, text, y, fnt, fill=INK, x=MARGIN, width=CONTENT_W):
    tw = draw.textlength(text, font=fnt)
    draw.text((x + (width - tw) / 2, y), text, font=fnt, fill=fill)


def section_heading(draw, text, y):
    fnt = F_SANS_BOLD(10)
    draw.text((MARGIN, y), text, font=fnt)
    rx = MARGIN + draw.textlength(text, font=fnt) + 10
    draw.line([(rx, y + 5), (W - MARGIN, y + 5)], fill=LIGHT_LINE, width=.65)


# ---------------------------------------------------------------- copy
# The extra name, clock times and market level are supplied v2 copy, not
# values inferred from the abbreviated Chinese source list.
LEADS = [
    dict(source_id=43, kicker="WASHINGTON · TRADE", status="OFFICIAL", art="ship",
         title="US proposes tariffs on 14 partners, up to 40% on China",
         deck="China faces the top 40% rate; India 25%, Vietnam 35%, the EU 15%. Beijing calls overcapacity 'a false issue'.",
         why="Two of the top US trade partners face duties"),
    dict(source_id=20, kicker="SEOUL · TOKYO · TAIPEI · MARKETS", status="REPORTED", art="chart",
         title="AI doubts sink Asian chip stocks: Kospi closes -6.2%",
         deck="Kospi ends at 4,697.51; SK hynix -11.1%, Samsung -9.9%. Taiwan's Taiex -4.8%, Japan's Nikkei -2.8%.",
         why="Investors doubt the AI spending boom will pay off"),
    dict(source_id=21, kicker="JIUQUAN, CHINA · SPACE", status="OFFICIAL", art="station",
         title="Pakistan's first astronaut docks at China's space station",
         deck="Muhammad Zeeshan Ali, 40, first foreigner on Tiangong, flew on Shenzhou-24; stays 5 to 10 days.",
         why="China's station takes its first foreign astronaut"),
]

SECONDARY = [
    dict(source_id=1, kicker="HORMUZ · WAR", status="CLAIM", art="tanker",
         title="Iran says two tankers hit by mines",
         deck="IRGC: ships took an 'unauthorised route'; no vessel named."),
    dict(source_id=8, kicker="SAMARA, RUSSIA · WAR", status="CONFIRMED", art="refinery",
         title="Ukrainian drones hit two Rosneft refineries",
         deck="Syzran and Kuibyshev ablaze; one killed, 145 drones downed."),
    dict(source_id=46, kicker="CANBERRA · DIPLOMACY", status="OFFICIAL", art="treaty",
         title="Solomon Islands signs security pact with Australia",
         deck="Treaty names Australia primary partner; no foreign bases."),
    dict(source_id=3, kicker="GAZA CITY · WAR", status="REPORTED", art="city",
         title="Israeli strike kills Hamas security chief",
         deck="Abuelouf, his wife and 2 daughters die in Shati camp."),
    dict(source_id=38, kicker="CARTAGENA · CRIME", status="CONFIRMED", art="store",
         title="Supermarket stormed, all hostages freed",
         deck="Forces storm Éxito store; one captor killed, two arrested."),
    dict(source_id=31, kicker="CAPE TOWN · JUSTICE", status="CONFIRMED", art="gavel",
         title="Court lifts 'Farmgate' ruling against Ramaphosa",
         deck="Judges void the 2022 panel report that opened the way to impeachment."),
    dict(source_id=22, kicker="BOGOR, INDONESIA · DISASTER", status="REPORTED", art="mine",
         title="26 miners trapped in flooded gold mine",
         deck="Flooding traps 26 workers underground at a gold mine in West Java."),
    dict(source_id=28, kicker="ED DAMAZIN, SUDAN · WAR", status="REPORTED", art="drones",
         title="RSF drones kill at least 19 in Sudan",
         deck="Drone strikes hit two cities; 19 civilians dead, 20 hurt."),
]

# Original IDs in source order. Display numbers are assigned from 12.
ALSO = [
    (2, "SAUDI ARABIA", "Houthis claim Ras Tanura refinery fire"),
    (4, "IRAN", "US urges citizens to leave at once"),
    (5, "HORMUZ", "Iran sets 7 terms; 'closing daily'"),
    (6, "WASHINGTON", "US weighs killing Iran leaders: report"),
    (7, "YEMEN", "Saudi-led coalition hits Hodeidah port"),
    (9, "ODESA", "Russian attacks kill 2, injure 3"),
    (10, "KYIV", "Zelensky: €115bn aid needed in 2027"),
    (11, "EUROZONE", "Inflation climbs to 4.0%"),
    (12, "UK", "EasyJet profit falls 89% on fuel costs"),
    (13, "RUSSIA", "BBC leak: at least 490,334 soldiers dead"),
    (14, "SAVASLEYKA", "Ukraine says 5 Russian jets damaged"),
    (15, "POLAND", "Push for permanent US military presence"),
    (16, "EUROPE", "Parliament votes to ease nature laws"),
    (17, "EUROPE", "Court: set timetable for cage-farming ban"),
    (18, "EUROPE", "€50bn quantum plan + €50bn tech fund"),
    (19, "FRANCE", "Sarkozy and Bruni ordered to stand trial"),
    (23, "PYONGYANG", "Swiss envoy expelled; office closed"),
    (24, "SEOUL", "Aramco, S-OIL open $7bn Shaheen project"),
    (25, "SEOUL", "SK hynix plans ₩100tn shareholder return"),
    (26, "INDIA", "Air India plans ₹600bn in cost cuts"),
    (27, "BENGHAZI", "Two Libyan officers die after ship attack"),
    (29, "SENEGAL", "Court restores Africa Cup title"),
    (30, "DR CONGO", "Cobalt exports to halt at month's end"),
    (32, "KENYA", "Cult leader Mackenzie convicted"),
    (33, "SAHEL", "Reuters: cheap drones reshape rebel war"),
    (34, "EGYPT", "Amnesty urges end to Mada Masr closure"),
    (35, "BLUE NILE", "28 women and children abducted"),
    (36, "WALL ST", "Tue: Dow above 50,000; Nasdaq -1.5%"),
    (37, "US", "Dell's record Q3 revenue: $54.9bn"),
    (39, "US", "CIA, NGA, ODNI report cyber breach fixed"),
    (40, "US", "Amazon buys Decart in AI chip race"),
    (41, "US", "Anthropic shares fall below IPO price"),
    (42, "US", "Roche cancer pill wins 2nd FDA approval"),
    (44, "VENEZUELA", "Public debt revealed: $237.5bn"),
    (45, "US EAST COAST", "Storm threatens holiday travel"),
    (47, "AUSTRALIA", "Inflation rises to 4.9%"),
    (48, "PACIFIC", "At centre of Australian foreign policy"),
    (49, "GLOBAL", "COP31 climate talks end without a deal"),
    (50, "GLOBAL", "UN: cuts threaten HIV/AIDS progress"),
]

REGIONS = [
    ("EUROPE", 12, (60, 93, 132)),
    ("MIDDLE EAST", 7, (132, 94, 69)),
    ("ASIA", 7, (186, 73, 49)),
    ("AFRICA", 9, (78, 115, 80)),
    ("AMERICAS", 10, (48, 111, 118)),
    ("OCEANIA", 3, (116, 94, 137)),
    ("GLOBAL", 2, (102, 106, 108)),
]

# An editorial primary-field classification: one field for each source ID.
FIELD_IDS = {
    "War": [1, 2, 3, 7, 8, 9, 10, 13, 14, 27, 28, 33],
    "Diplomacy": [4, 5, 6, 15, 23, 46, 48],
    "Markets": [20, 36, 41],
    "Economy": [11, 44, 47],
    "Business": [12, 25, 26, 37],
    "Space": [21],
    "Trade": [43],
    "Energy": [24],
    "Disaster": [22, 45],
    "Justice": [19, 31, 32],
    "Crime": [38],
    "Health": [42, 50],
    "Sport": [29],
    "Tech": [18, 40],
    "Climate": [49],
    "Rights": [35],
    "Nature": [16],
    "Welfare": [17],
    "Mining": [30],
    "Press": [34],
    "Cyber": [39],
}

BIG_DATA = [
    ("40%", "TOP PROPOSED US TARIFF ON CHINA"),
    ("-6.2%", "KOSPI CLOSE, WORST IN AI SELL-OFF"),
    ("1ST", "FOREIGNER ABOARD TIANGONG"),
    ("490,334", "RUSSIAN SOLDIERS DEAD, BBC LEAK"),
    ("26", "TRAPPED IN JAVA GOLD MINE"),
    ("€115BN", "UKRAINE AID NEEDED IN 2027"),
]

# Unchanged v1 dot-matrix land geometry: 50 columns x 25 rows.
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

MAP_EVENTS = [
    (14, 8, "WASHINGTON", "Trade"),
    (43, 8, "SEOUL", "Markets"),
    (39, 8, "JIUQUAN", "Space"),
    (33, 10, "HORMUZ", "War"),
    (32, 5, "SAMARA", "War"),
    (46, 22, "CANBERRA", "Diplomacy"),
    (30, 9, "GAZA CITY", "War"),
    (15, 13, "CARTAGENA", "Crime"),
    (28, 22, "CAPE TOWN", "Justice"),
    (40, 17, "WEST JAVA", "Disaster"),
    (30, 13, "ED DAMAZIN", "War"),
]


def validate_copy():
    illustrated = [s["source_id"] for s in LEADS + SECONDARY]
    others = [s[0] for s in ALSO]
    assert illustrated == [43, 20, 21, 1, 8, 46, 3, 38, 31, 22, 28]
    assert len(illustrated) == 11 and len(ALSO) == 39
    assert others == sorted(set(range(1, 51)) - set(illustrated))
    assert Counter(illustrated + others) == Counter(range(1, 51))
    assert len(REGIONS) == 7 and sum(r[1] for r in REGIONS) == 50
    assert len(FIELD_IDS) == 21
    assert Counter(i for ids in FIELD_IDS.values() for i in ids) == Counter(range(1, 51))
    assert len(MAP_EVENTS) == 11


# ---------------------------------------------------------------- art

def star(draw, cx, cy, radius, fill, points=5):
    vertices = []
    for k in range(points * 2):
        angle = -math.pi / 2 + k * math.pi / points
        r = radius if k % 2 == 0 else radius * 0.42
        vertices.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    draw.polygon(vertices, fill=fill)


def flame(draw, cx, base_y, w, h):
    draw.polygon([(cx - w / 2, base_y), (cx - w * .32, base_y - h * .56),
                  (cx, base_y - h), (cx + w * .18, base_y - h * .48),
                  (cx + w * .48, base_y - h * .67), (cx + w / 2, base_y)],
                 fill=(219, 92, 32))
    draw.polygon([(cx - w * .23, base_y), (cx, base_y - h * .68),
                  (cx + w * .25, base_y)], fill=(250, 191, 76))


def drone(draw, cx, cy, size=5, color=NAVY):
    for a, b in [((-size, -size), (size, size)), ((-size, size), (size, -size))]:
        draw.line([(cx + a[0], cy + a[1]), (cx + b[0], cy + b[1])], fill=color, width=1.7)
    draw.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=color)
    for dx, dy in [(-size, -size), (-size, size), (size, -size), (size, size)]:
        draw.ellipse([cx + dx - 2.5, cy + dy - 1, cx + dx + 2.5, cy + dy + 1], fill=color)


def draw_ship(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(222, 233, 235))
    sea_y = y + h * .69
    d.rectangle([x, sea_y, x + w, y + h], fill=(49, 103, 120))
    for j in range(2):
        for i in range(8):
            sx = x + 6 + i * 43 + j * 13
            d.line([(sx, sea_y + 9 + j * 12), (sx + 23, sea_y + 9 + j * 12)],
                   fill=(139, 181, 190), width=.7)
    d.polygon([(x + 19, y + 55), (x + w - 27, y + 55),
               (x + w - 47, y + 77), (x + 38, y + 77)], fill=NAVY)
    d.polygon([(x + 27, y + 68), (x + w - 39, y + 68),
               (x + w - 47, y + 77), (x + 38, y + 77)], fill=RED)
    colors = [TEAL, (185, 104, 66), GOLD, (143, 159, 154), (161, 55, 48)]
    for row in range(3):
        for col in range(5 - (row == 2)):
            bx, by = x + 43 + col * 35, y + 43 - row * 12
            c = colors[(col + row * 2) % len(colors)]
            d.rectangle([bx, by, bx + 33, by + 11], fill=c)
            for k in range(1, 5):
                d.line([(bx + k * 6, by + 2), (bx + k * 6, by + 9)], fill=PAPER, width=.35)
    d.rectangle([x + 220, y + 33, x + 241, y + 55], fill=(245, 241, 224))
    d.rectangle([x + 218, y + 29, x + 244, y + 35], fill=PAPER)
    d.rectangle([x + 222, y + 30, x + 240, y + 33], fill=NAVY)
    d.line([(x + 232, y + 14), (x + 232, y + 29)], fill=NAVY, width=1)
    d.line([(x + 224, y + 18), (x + 240, y + 18)], fill=NAVY, width=1)
    cx, cy, r = x + w - 42, y + 37, 31
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED)
    d.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], outline=PAPER, width=.6)
    centered(d, "UP TO", cy - 19, F_SANS_BOLD(8), PAPER, cx - r, r * 2)
    centered(d, "40%", cy - 5, F_SANS_BOLD(24), PAPER, cx - r, r * 2)


def draw_chart(d, x, y, w, h):
    """The v1 falling line, redrawn proportionally with a chip motif."""
    d.rectangle([x, y, x + w, y + h], fill=(252, 250, 245))
    for k in range(1, 5):
        gy = y + k * h / 5
        d.line([(x + 8, gy), (x + w - 8, gy)], fill=(225, 224, 219), width=.6)
    for k in range(1, 8):
        gx = x + k * w / 8
        d.line([(gx, y + 7), (gx, y + h - 7)], fill=(231, 228, 222), width=.6)
    pts = [(x + w * a, y + h * b) for a, b in
           [(.24, .17), (.38, .28), (.49, .25), (.62, .48),
            (.73, .44), (.85, .70), (.95, .81)]]
    d.polygon(pts + [(x + w * .95, y + h - 7), (x + w * .24, y + h - 7)],
              fill=(247, 221, 212))
    d.line(pts, fill=RED, width=3.6)
    d.polygon([(x + w * .95, y + h * .81), (x + w * .90, y + h * .79),
               (x + w * .94, y + h * .67)], fill=RED)
    for px, py in pts[:-1]:
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=RED)
    cx, cy = x + 49, y + 27
    for k in range(4):
        p = -10 + k * 6
        d.line([(cx - 21, cy + p), (cx + 21, cy + p)], fill=NAVY, width=2)
        d.line([(cx + p, cy - 21), (cx + p, cy + 21)], fill=NAVY, width=2)
    d.rounded_rectangle([cx - 15, cy - 15, cx + 15, cy + 15], radius=2, fill=NAVY)
    centered(d, "AI", cy - 7, F_SANS_BOLD(13), PAPER, cx - 15, 30)
    d.rectangle([x + 10, y + h - 29, x + 119, y + h - 8], fill=RED)
    d.text((x + 16, y + h - 26), "KOSPI -6.2%", font=F_SANS_BOLD(14), fill=PAPER)


def draw_station(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=NAVY)
    for a, b in [(9, 15), (23, 42), (47, 10), (75, 19), (100, 8), (122, 27),
                 (142, 7), (164, 15), (185, 8), (207, 20), (235, 9), (280, 39),
                 (298, 16), (19, 68), (90, 64), (204, 65), (268, 67)]:
        d.ellipse([x + a, y + b, x + a + 1, y + b + 1], fill=(215, 228, 225))
    d.ellipse([x - 45, y + h - 21, x + w + 45, y + h + 125],
              fill=(39, 100, 144), outline=(98, 188, 211), width=3)
    d.polygon([(x + 46, y + h - 9), (x + 79, y + h - 16),
               (x + 104, y + h - 9), (x + 131, y + h - 6),
               (x + 116, y + h), (x + 69, y + h)], fill=(67, 126, 129))
    d.line([(x + 57, y + 43), (x + 253, y + 43)], fill=(204, 213, 212), width=3)
    for sx in (43, 221):
        for sy in (20, 47):
            d.rectangle([x + sx, y + sy, x + sx + 48, y + sy + 20],
                        fill=(38, 91, 154), outline=(105, 174, 205), width=.8)
            for k in range(1, 6):
                d.line([(x + sx + k * 8, y + sy), (x + sx + k * 8, y + sy + 20)],
                       fill=(105, 174, 205), width=.45)
            d.line([(x + sx, y + sy + 10), (x + sx + 48, y + sy + 10)],
                   fill=(105, 174, 205), width=.45)
    d.rounded_rectangle([x + 98, y + 37, x + 214, y + 50], radius=4,
                        fill=(222, 225, 219), outline=(131, 161, 174), width=.7)
    d.rounded_rectangle([x + 149, y + 19, x + 164, y + 67], radius=4,
                        fill=(238, 234, 219), outline=(131, 161, 174), width=.7)
    for sx in (111, 134, 179, 201):
        d.line([(x + sx, y + 38), (x + sx, y + 49)], fill=(131, 161, 174), width=1)
    d.ellipse([x + 151, y + 38, x + 162, y + 49], fill=TEAL)
    d.rectangle([x + 148, y + 64, x + 165, y + 70], fill=(192, 197, 188))
    d.polygon([(x + 287, y + 32), (x + 281, y + 43),
               (x + 281, y + 59), (x + 293, y + 59), (x + 293, y + 43)], fill=PAPER)
    d.polygon([(x + 281, y + 51), (x + 277, y + 64), (x + 284, y + 59)], fill=RED)
    d.polygon([(x + 293, y + 51), (x + 297, y + 64), (x + 290, y + 59)], fill=RED)
    flame(d, x + 287, y + 73, 7, 14)
    d.ellipse([x + 284, y + 43, x + 290, y + 49], fill=(64, 117, 150))
    d.rectangle([x + 246, y + 6, x + 264, y + 17], fill=RED)
    star(d, x + 251, y + 10, 2.3, (255, 217, 98))
    d.rectangle([x + 271, y + 6, x + 290, y + 17], fill=(25, 106, 71))
    d.rectangle([x + 271, y + 6, x + 275, y + 17], fill=PAPER)
    d.ellipse([x + 278, y + 8, x + 285, y + 15], fill=PAPER)
    d.ellipse([x + 280, y + 7, x + 286, y + 13], fill=(25, 106, 71))
    star(d, x + 285, y + 10, 1.4, PAPER)


def draw_tanker(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(219, 231, 235))
    sy = y + h * .73
    d.rectangle([x, sy, x + w, y + h], fill=(50, 101, 119))
    d.polygon([(x + 34, sy - 9), (x + w - 29, sy - 9),
               (x + w - 43, sy + 8), (x + 46, sy + 8)], fill=NAVY)
    d.line([(x + 46, sy + 4), (x + w - 42, sy + 4)], fill=RED, width=3)
    d.rectangle([x + w - 66, sy - 24, x + w - 39, sy - 9], fill=PAPER)
    d.rectangle([x + w - 63, sy - 22, x + w - 42, sy - 18], fill=TEAL)
    for sx in (77, 117):
        d.rectangle([x + sx - 12, sy - 14, x + sx + 14, sy - 9], fill=(143, 158, 160))
        flame(d, x + sx, sy - 13, 17, 20)
        d.ellipse([x + sx - 5, y + 3, x + sx + 10, y + 15], fill=(104, 111, 112))
    for i in range(5):
        sx = x + 12 + i * 48
        d.line([(sx, y + h - 4), (sx + 22, y + h - 4)], fill=(151, 192, 202), width=.7)


def draw_refinery(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(223, 231, 231))
    ground = y + h - 5
    d.rectangle([x, ground, x + w, y + h], fill=(129, 147, 144))
    for tx in (x + 50, x + 97):
        d.rectangle([tx, ground - 17, tx + 35, ground], fill=(211, 216, 207), outline=TEAL, width=.6)
        d.ellipse([tx, ground - 21, tx + 35, ground - 13], fill=PAPER, outline=TEAL, width=.6)
    for tx, height in ((x + 151, 25), (x + 181, 28)):
        d.rectangle([tx, ground - height, tx + 13, ground], fill=(91, 120, 124))
        for k in range(3):
            d.line([(tx - 3, ground - 5 - k * 8), (tx + 16, ground - 5 - k * 8)], fill=TEAL, width=1)
        flame(d, tx + 6, ground - height + 1, 13, 10)
    flame(d, x + 68, ground - 18, 19, 20)
    drone(d, x + 121, y + 10, 4)
    for k in range(4):
        d.ellipse([x + 92 + k * 6, y + 3 + k * 2, x + 93 + k * 6, y + 4 + k * 2], fill=RED)


def draw_treaty(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(221, 232, 227))
    cx = x + w / 2
    d.rectangle([cx - 31, y + 4, cx + 31, y + h - 3], fill=PAPER, outline=(166, 177, 163), width=.7)
    d.polygon([(cx + 22, y + 4), (cx + 31, y + 13), (cx + 22, y + 13)], fill=(212, 217, 202))
    for k in range(4):
        d.line([(cx - 22, y + 12 + k * 5), (cx + 14, y + 12 + k * 5)], fill=(143, 156, 150), width=.7)
    d.ellipse([cx + 9, y + 29, cx + 23, y + 42], fill=RED)
    d.polygon([(cx + 10, y + 37), (cx + 9, y + 45), (cx + 15, y + 42),
               (cx + 21, y + 45), (cx + 22, y + 37)], fill=RED)
    fx, fy = x + 30, y + 12
    d.rectangle([fx, fy, fx + 41, fy + 24], fill=(36, 65, 109))
    d.line([(fx, fy), (fx + 16, fy + 11)], fill=PAPER, width=2)
    d.line([(fx + 16, fy), (fx, fy + 11)], fill=PAPER, width=2)
    d.line([(fx + 8, fy), (fx + 8, fy + 12)], fill=RED, width=2)
    d.line([(fx, fy + 6), (fx + 17, fy + 6)], fill=RED, width=2)
    for dx, dy in ((28, 5), (24, 11), (33, 13), (28, 20)):
        star(d, fx + dx, fy + dy, 1.8, PAPER)
    fx = x + w - 71
    d.rectangle([fx, fy, fx + 41, fy + 24], fill=(46, 83, 129))
    d.polygon([(fx, fy + 24), (fx + 41, fy), (fx + 41, fy + 24)], fill=(57, 119, 80))
    d.line([(fx, fy + 24), (fx + 41, fy)], fill=(234, 202, 89), width=3)
    for dx, dy in ((7, 4), (15, 4), (11, 8), (7, 12), (15, 12)):
        star(d, fx + dx, fy + dy, 1.1, PAPER)


def draw_city(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(231, 219, 197))
    for i, (xx, bw, bh) in enumerate([(22, 38, 24), (63, 37, 34), (103, 30, 21),
                                      (137, 40, 30), (181, 34, 25)]):
        bx, by = x + xx, y + h - bh
        d.rectangle([bx, by, bx + bw, y + h], fill=(158, 143, 117) if i % 2 else (188, 170, 140))
        for r in range(2):
            for c in range(3):
                wx, wy = bx + 6 + c * 9, by + 5 + r * 9
                d.rectangle([wx, wy, wx + 4, wy + 5], fill=(240, 215, 155))
    for dx, dy, r in [(153, 22, 7), (152, 14, 7), (158, 8, 6), (167, 5, 4)]:
        d.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=(74, 78, 74))


def draw_store(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(225, 233, 223))
    bx, by = x + 44, y + 8
    d.rectangle([bx, by, x + w - 30, y + h], fill=(214, 193, 153))
    d.rectangle([bx + 5, by + 3, x + w - 35, by + 13], fill=TEAL)
    centered(d, "ÉXITO", by + 4, F_SANS_BOLD(7.5), PAPER, bx + 5, w - 84)
    for k in range(12):
        ax = bx - 3 + k * (w - 68) / 12
        aw = (w - 68) / 12
        color = RED if k % 2 == 0 else PAPER
        d.rectangle([ax, by + 15, ax + aw, by + 21], fill=color)
        d.ellipse([ax, by + 18, ax + aw, by + 25], fill=color)
    d.rectangle([x + w * .51, by + 25, x + w * .62, y + h], fill=NAVY)
    d.rectangle([bx + 12, by + 27, x + w * .46, y + h - 4], fill=(125, 171, 171))
    d.rectangle([x + w * .68, by + 27, x + w - 42, y + h - 4], fill=(125, 171, 171))
    d.line([(x + 32, y + h - 1), (x + w - 18, y + h - 1)], fill=(120, 139, 130), width=2)


def draw_gavel(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(232, 221, 200))
    brown, light = (105, 71, 48), (165, 117, 73)
    d.line([(x + 83, y + 16), (x + 125, y + 37)], fill=brown, width=7)
    d.polygon([(x + 65, y + 5), (x + 74, y + 1), (x + 96, y + 24),
               (x + 86, y + 32), (x + 62, y + 10)], fill=light)
    d.line([(x + 65, y + 5), (x + 89, y + 29)], fill=brown, width=3)
    d.ellipse([x + 56, y + 35, x + 112, y + 44], fill=brown)
    d.rectangle([x + 56, y + 39, x + 112, y + 45], fill=brown)
    d.rounded_rectangle([x + w - 83, y + 12, x + w - 17, y + 36], radius=2, outline=RED, width=1.7)
    centered(d, "VOID", y + 16, F_SANS_BOLD(17), RED, x + w - 83, 66)


def draw_mine(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(149, 110, 76))
    d.rectangle([x, y, x + w, y + 5], fill=(202, 176, 130))
    sx = x + w * .50
    d.rectangle([sx - 12, y + 3, sx + 12, y + h], fill=(60, 56, 49))
    d.rectangle([x + 40, y + 29, x + w - 37, y + 39], fill=(60, 56, 49))
    d.line([(sx - 8, y + 2), (sx - 8, y + 35)], fill=(200, 184, 146), width=.7)
    d.line([(sx + 8, y + 2), (sx + 8, y + 35)], fill=(200, 184, 146), width=.7)
    d.rectangle([sx - 7, y + 14, sx + 7, y + 28], outline=GOLD, width=1.4)
    d.line([(sx, y + 14), (sx, y + 28)], fill=GOLD, width=.7)
    d.rectangle([x + 40, y + 35, x + w - 37, y + 39], fill=(65, 126, 148))
    d.rectangle([sx - 12, y + 35, sx + 12, y + h], fill=(65, 126, 148))
    d.line([(x + 40, y + 35), (x + w - 37, y + 35)], fill=(137, 192, 197), width=1)
    for rx, ry in ((25, 17), (62, 21), (158, 17), (185, 27), (210, 12)):
        d.polygon([(x + rx, y + ry), (x + rx + 6, y + ry - 4),
                   (x + rx + 10, y + ry + 2), (x + rx + 3, y + ry + 5)], fill=(193, 155, 108))


def draw_drones(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(230, 218, 191))
    for bx, bw, bh in [(22, 34, 12), (60, 39, 15), (103, 31, 10), (138, 44, 17), (187, 29, 12)]:
        d.rectangle([x + bx, y + h - bh, x + bx + bw, y + h], fill=(160, 136, 102))
        d.line([(x + bx - 1, y + h - bh), (x + bx + bw + 1, y + h - bh)], fill=(127, 111, 89), width=1.4)
    for cx, cy in [(66, 13), (131, 9), (191, 17)]:
        drone(d, x + cx, y + cy, 4)
        for k in range(4):
            px, py = x + cx - 25 + k * 5, y + cy - 2 + k * 2
            d.ellipse([px, py, px + 1, py + 1], fill=RED)


ART = {"ship": draw_ship, "chart": draw_chart, "station": draw_station,
       "tanker": draw_tanker, "refinery": draw_refinery, "treaty": draw_treaty,
       "city": draw_city, "store": draw_store, "gavel": draw_gavel,
       "mine": draw_mine, "drones": draw_drones}


# ---------------------------------------------------------------- page

def number_badge(d, number, cx, cy, radius=10.5, size=12):
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=RED,
              outline=PAPER, width=.8)
    text = str(number)
    fnt = F_SANS_BOLD(size)
    b = d.textbbox((0, 0), text, fnt)
    centered(d, text, cy - (b[3] - b[1]) / 2, fnt, PANEL, cx - radius, radius * 2)


def paste_art(img, d, name, x, y, width, height, number, mini=False):
    panel = Image.new("RGB", (round(width * SCALE), round(height * SCALE)), PANEL)
    pd = Canvas(panel)
    ART[name](pd, 0, 0, width, height)
    number_badge(pd, number, 13 if mini else 17, 12 if mini else 17,
                 radius=8 if mini else 10.5, size=9 if mini else 12)
    img.paste(panel, (round(x * SCALE), round(y * SCALE)))
    d.rectangle([x, y, x + width, y + height], outline=PANEL_LINE, width=.55)


def metadata(d, story, x, y, width, mini=False):
    size = 8 if mini else 8.5
    badge_font = F_SANS_BOLD(size - .1)
    label = story["status"]
    bw = d.textlength(label, font=badge_font) + 8
    bx = x + width - bw
    colors = {"OFFICIAL": ((226, 237, 227), (47, 93, 67)),
              "REPORTED": ((231, 229, 221), (83, 83, 78)),
              "CLAIM": ((244, 226, 193), (135, 77, 24)),
              "CONFIRMED": ((225, 235, 235), (37, 92, 98))}
    bg, fg = colors[label]
    d.rounded_rectangle([bx, y - 1.5, x + width, y + size + 2.2], radius=1.4, fill=bg)
    d.text((bx + 4, y), label, font=badge_font, fill=fg)
    kf = fit_font(d, story["kicker"], "NotoSans-Bold.ttf", size, bx - x - 6)
    d.text((x + 1, y), story["kicker"], font=kf, fill=RED)


def assert_column_text(d, start, left, top, right, bottom):
    for box, text in d.text_boxes[start:]:
        assert box[0] >= left - .4 and box[2] <= right + .4, ("column spill", text, box)
        assert box[1] >= top - .4 and box[3] <= bottom + .4, ("row spill", text, box)


def draw_page():
    validate_copy()
    img = Image.new("RGB", (W * SCALE, H * SCALE), PAPER)
    d = Canvas(img)

    # Giant date, not a small subtitle: the first visual read is the day.
    top = ("THE WORLD IN ONE DAY · 50 STORIES · 7 REGIONS · 21 FIELDS · "
           "ALL FIRST REPORTED ON WEDNESDAY 25 NOVEMBER 2026")
    centered(d, top, 10, F_SANS_BOLD(9.8))
    date = "Wednesday 25 November 2026"
    masthead = fit_font(d, date, "NotoSerif-Black.ttf", 64, CONTENT_W - 2)
    centered(d, date, 24, masthead)
    kicker = ("US proposes tariffs on 14 economies · AI doubts sink Asian chip stocks · "
              "Pakistan's first astronaut docks at Tiangong")
    kf = fit_font(d, kicker, "NotoSerif-BoldItalic.ttf", 15, CONTENT_W - 6)
    centered(d, kicker, 89, kf, RED)
    hline(d, 109, width=2)
    hline(d, 113, width=.7)

    # Exactly proportional widths, with a condensed label in the narrow tail.
    rx = MARGIN
    for index, (name, count, color) in enumerate(REGIONS):
        right = MARGIN + CONTENT_W * sum(r[1] for r in REGIONS[:index + 1]) / 50
        d.rectangle([rx, 119, right, 136], fill=color)
        label = f"{name} {count}"
        rf = fit_font(d, label, "NotoSans-CondensedBold.ttf", 9, right - rx - 4)
        centered(d, label, 124, rf, PANEL, rx, right - rx)
        if index:
            d.line([(rx, 119), (rx, 136)], fill=PAPER, width=1)
        rx = right
    fields = "21 FIELDS — " + " · ".join(f"{name} {len(ids)}" for name, ids in FIELD_IDS.items())
    ff = fit_font(d, fields, "NotoSans-Condensed.ttf", 8.6, CONTENT_W)
    centered(d, fields, 141, ff, GRAY)

    # Six iconic numbers, with a common baseline and no clipped labels.
    gap = 6
    bw = (CONTENT_W - gap * 5) / 6
    for i, (number, label) in enumerate(BIG_DATA):
        bx = MARGIN + i * (bw + gap)
        d.rectangle([bx, 154, bx + bw, 204], fill=(252, 250, 245), outline=PANEL_LINE, width=.6)
        d.rectangle([bx, 154, bx + bw, 156.5], fill=RED)
        nf = fit_font(d, number, "NotoSans-Bold.ttf", 28, bw - 12)
        centered(d, number, 161, nf, RED, bx, bw)
        lf = fit_font(d, label, "NotoSans-CondensedBold.ttf", 7.6, bw - 10)
        centered(d, label, 192, lf, INK, bx, bw)

    d.rectangle([MARGIN, 210, W - MARGIN, 230], fill=NAVY)
    utc = ("THE DAY IN UTC   00:18 Shenzhou-24 lifts off · 03:56 Tiangong docks · "
           "05:30 Taiex -4.8% · 06:30 Kospi -6.2% · 13:00 US tariffs proposed")
    uf = fit_font(d, utc, "NotoSans-Bold.ttf", 9.1, CONTENT_W - 18)
    centered(d, utc, 216, uf, PAPER)

    # Three leads. All have exactly two reserved headline/deck lines, then
    # a separately fitted 'why' sentence; every card checks its own bounds.
    y = 238
    lead_gap = 16
    lead_w = (CONTENT_W - 2 * lead_gap) / 3
    for i, story in enumerate(LEADS):
        x = MARGIN + i * (lead_w + lead_gap)
        start = len(d.text_boxes)
        paste_art(img, d, story["art"], x, y, lead_w, 92, i + 1)
        metadata(d, story, x, y + 98, lead_w)
        tf = fit_lines(d, story["title"], "NotoSerif-Black.ttf", 19.5, lead_w - 1, 2, 16)
        draw_wrapped(d, x, y + 112, story["title"], tf, INK, lead_w - 1, 21)
        df = fit_lines(d, story["deck"], "NotoSans-Condensed.ttf", 10.6, lead_w, 2, 9)
        draw_wrapped(d, x, y + 157, story["deck"], df, INK, lead_w, 11.5)
        why = "WHY IT MATTERS · " + story["why"]
        wf = fit_font(d, why, "NotoSans-CondensedBold.ttf", 8.5, lead_w)
        d.text((x, y + 185), why, font=wf, fill=RED)
        assert_column_text(d, start, x, y, x + lead_w, y + 197)
        if i:
            sx = x - lead_gap / 2
            d.line([(sx, y + 98), (sx, y + 194)], fill=LIGHT_LINE, width=.6)
    y += 200
    hline(d, y, LIGHT_LINE, .65)

    # Eight genuinely illustrated secondary stories, read across then down.
    section_heading(d, "MORE FROM WEDNESDAY · STORIES 4–11", y + 8)
    grid_top = y + 26
    mini_gap = 14
    mini_w = (CONTENT_W - mini_gap * 3) / 4
    row_h = 101
    for i, story in enumerate(SECONDARY):
        x = MARGIN + (i % 4) * (mini_w + mini_gap)
        sy = grid_top + (i // 4) * row_h
        start = len(d.text_boxes)
        paste_art(img, d, story["art"], x, sy, mini_w, 46, i + 4, mini=True)
        metadata(d, story, x, sy + 49, mini_w, mini=True)
        tf = fit_lines(d, story["title"], "NotoSans-Bold.ttf", 12.7, mini_w - 1, 2, 10.7)
        draw_wrapped(d, x, sy + 60, story["title"], tf, INK, mini_w - 1, 13.5)
        df = fit_font(d, story["deck"], "NotoSans-Condensed.ttf", 8.3, mini_w)
        d.text((x, sy + 89), story["deck"], font=df, fill=(62, 62, 57))
        assert_column_text(d, start, x, sy, x + mini_w, sy + 99)
        if i % 4:
            vx = x - mini_gap / 2
            d.line([(vx, sy), (vx, sy + 97)], fill=LIGHT_LINE, width=.55)
    y = grid_top + 2 * row_h
    hline(d, y - row_h - 3, LIGHT_LINE, .55)
    hline(d, y, LIGHT_LINE, .65)

    # Same small stacked map as v1, now with true story-number pins.
    section_heading(d, "WHERE IT HAPPENED", y + 8)
    map_top = y + 25
    map_w, map_h = 240, 88
    cw, ch = map_w / 50, map_h / 25
    d.rectangle([MARGIN, map_top, MARGIN + map_w, map_top + map_h], fill=SEA)
    for r, ranges in MAP_RANGES.items():
        for c0, c1 in ranges:
            for c in range(c0, c1 + 1):
                cx, cy = MARGIN + (c + .5) * cw, map_top + (r + .5) * ch
                d.ellipse([cx - 1.2, cy - 1.2, cx + 1.2, cy + 1.2], fill=LAND)
    for i, (col, row, _, _) in enumerate(MAP_EVENTS, 1):
        cx, cy = MARGIN + (col + .5) * cw, map_top + (row + .5) * ch
        number_badge(d, i, cx, cy, radius=6.1, size=7.5)
    d.rectangle([MARGIN, map_top, MARGIN + map_w, map_top + map_h], outline=PANEL_LINE, width=.6)
    d.text((MARGIN, map_top + map_h + 5), "Pins = story numbers", font=F_SANS(8), fill=GRAY)
    key_x = MARGIN + map_w + 24
    key_col_w = (W - MARGIN - key_x) / 3
    for i, (_, _, place, field) in enumerate(MAP_EVENTS):
        col, row = divmod(i, 4)
        x, ky = key_x + col * key_col_w, map_top + 7 + row * 21
        number_badge(d, i + 1, x + 7, ky + 5, radius=6.5, size=7)
        d.text((x + 20, ky), place, font=F_SANS_BOLD(9), fill=INK)
        pw = d.textlength(place, font=F_SANS_BOLD(9))
        d.text((x + 26 + pw, ky + .5), field, font=F_SANS(8.4), fill=GRAY)
    y = map_top + map_h + 20
    hline(d, y, LIGHT_LINE, .65)

    # 12–50 follow original source order, not the old source IDs. Three
    # newspaper columns, thirteen one-line briefs each, with place prefixes.
    section_heading(d, "ALSO ON WEDNESDAY 25 NOVEMBER", y + 8)
    list_top = y + 26
    list_gap = 16
    list_w = (CONTENT_W - list_gap * 2) / 3
    for i, (_, place, text) in enumerate(ALSO):
        col, row = divmod(i, 13)
        x, ly = MARGIN + col * (list_w + list_gap), list_top + row * 10.5
        prefix = f"{i + 12}. {place} — "
        # Both runs use the same fitted face size; the location is bold.
        fnt = fit_font(d, prefix + text, "NotoSans-Condensed.ttf", 9.6, list_w - 3)
        for step in range(fnt.size, 17, -1):
            body = font("NotoSans-Condensed.ttf", step / SCALE)
            bold = font("NotoSans-CondensedBold.ttf", step / SCALE)
            pw = d.textlength(prefix, font=bold)
            if pw + d.textlength(text, font=body) <= list_w - 2:
                break
        else:
            raise AssertionError(f"Brief does not fit: {prefix}{text}")
        start = len(d.text_boxes)
        d.text((x, ly), prefix, font=bold)
        d.text((x + pw, ly), text, font=body)
        assert_column_text(d, start, x, ly, x + list_w, ly + 10.4)
    for i in (1, 2):
        vx = MARGIN + i * (list_w + list_gap) - list_gap / 2
        d.line([(vx, list_top), (vx, list_top + 134)], fill=LIGHT_LINE, width=.55)
    y = math.ceil(list_top + 13 * 10.5 + 4)

    # Preserve the v1 exclusion discipline and source attribution, fitting
    # the entire exclusion sentence instead of letting it run off the page.
    dc_h = 36
    d.rectangle([MARGIN, y, W - MARGIN, y + dc_h], fill=DATE_BG, outline=RED, width=.7)
    footer_lines = [
        ("DATE CHECK — NOT 25 NOV NEWS, EXCLUDED:", "NotoSans-Bold.ttf", RED),
        ("Huawei verdict (24 Nov) · Abrego Garcia to Spain · Putin remarks · Riyadh tower drone (first strike) · Monday Nvidia · Thu European Council & Thanksgiving — not yet happened.",
         "NotoSans-Condensed.ttf", INK),
        ("TO THE JUDGE: every story above was first reported Wednesday 25 November 2026.", "NotoSans-Bold.ttf", RED),
    ]
    for i, (text, name, color) in enumerate(footer_lines):
        fnt = fit_font(d, text, name, 8.3, CONTENT_W - 18)
        d.text((MARGIN + 9, y + 5 + i * 10), text, font=fnt, fill=color)
    y += dc_h + 5
    src = "Sources: Al Jazeera, BBC, Reuters, AFP, JustSecurity, AP, Principia. Drawings original."
    centered(d, src, y, F_SANS(8), GRAY)
    y += 12

    # A second, global text check catches inter-section/column collisions.
    # Touching ink boxes are fine; actual positive-area overlap is not.
    for i, (a, at) in enumerate(d.text_boxes):
        for b, bt in d.text_boxes[i + 1:]:
            overlap_w = min(a[2], b[2]) - max(a[0], b[0])
            overlap_h = min(a[3], b[3]) - max(a[1], b[1])
            assert overlap_w <= .4 or overlap_h <= .4, ("text overlap", at, bt, a, b)
    assert y <= H - 4, f"layout overflow: bottom y={y}"
    print(f"layout checked: 50 stories, 21 fields, 11 numbered pins; bottom y={y}")
    return img.resize((W, H), Image.Resampling.LANCZOS)


def main():
    img = draw_page()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    img.save(out, format="PNG", optimize=True)
    size = os.path.getsize(out)
    print(f"saved {out}: {img.width}x{img.height}, {size} bytes")
    assert img.size == (1024, 1024)
    assert img.mode == "RGB"
    assert size <= 1048576, f"entry.png too large: {size} bytes"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
