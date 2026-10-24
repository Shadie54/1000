# config.py

import pygame

from gui import display

pygame.init()

# Logický priestor (gui/display.py): šírka vždy 1920, výška 1080…1200
# podľa pomeru strán okna. Hra kreslí v týchto súradniciach cez Canvas
# (gui/canvas.py) priamo v rozlíšení okna. Logická VÝŠKA sa môže zmeniť
# za behu (Nastavenia → Zobrazenie) — preto tu nie je; obrazovky ju berú
# pri vytvorení z display.logical_height().
SCREEN_WIDTH = display.LOGICAL_W

FPS = 60

# ------------------------------------------------------------------
# Cesty k obrázkom kariet
# ------------------------------------------------------------------
CARDS_SMALL_PATH = "assets/cards-small"
CARDS_MEDIUM_PATH = "assets/cards-medium"
CARDS_LARGE_PATH = "assets/cards-large"
SUIT_ICONS_PATH = "assets/suit-icons"

# ------------------------------------------------------------------
# Veľkosti kariet (šírka x výška)
# ------------------------------------------------------------------
CARD_SIZE_SMALL = (91, 146)
CARD_SIZE_MEDIUM = (181, 293)
CARD_SIZE_LARGE = (363, 585)

# ------------------------------------------------------------------
# Karty
# ------------------------------------------------------------------
SUITS = ["heart", "bell", "leaf", "acorn"]
RANKS = ["seven", "eight", "nine", "under", "over", "king", "ten", "ace"]

CARD_POINTS = {
    "ace": 11,
    "ten": 10,
    "king": 4,
    "over": 3,
    "under": 2,
    "nine": 0,
    "eight": 0,
    "seven": 0,
}

TRUMP_POINTS = {
    "heart": 40,
    "bell": 60,
    "leaf": 80,
    "acorn": 100,
}
# Poradie farieb pre zoradenie kariet (zostupne)
SUIT_ORDER = ["acorn", "leaf", "bell", "heart"]

# ------------------------------------------------------------------
# Herné pravidlá
# ------------------------------------------------------------------
MIN_BID = 50
BID_STEP = 10
WINNING_SCORE = 1000
TALON_SIZE = 2
ROUND_ROUNDING = 5
NUM_PLAYERS = 3
MAX_BID = 400       # maximálny možný záväzok
# ------------------------------------------------------------------
# Debug režim
# ------------------------------------------------------------------
DEBUG_MODE = False

# ------------------------------------------------------------------
# GUI - Farby — téma: tmavé drevo
# ------------------------------------------------------------------
COLOR_BG = (45, 28, 15)                 # tmavá hnedá (fallback ak chýba obrázok)
COLOR_BG_DARK = (30, 18, 8)            # veľmi tmavá hnedá
COLOR_WHITE = (255, 248, 235)          # teplá biela (nie studená)
COLOR_BLACK = (15, 10, 5)              # teplá čierna
COLOR_YELLOW = (255, 220, 100)         # teplá žltá
COLOR_RED = (200, 60, 40)              # červená
COLOR_GREEN = (80, 180, 80)            # zelená
COLOR_GRAY = (120, 100, 80)            # teplá šedá
COLOR_DARK_GRAY = (60, 45, 30)         # tmavá teplá šedá
COLOR_GOLD = (212, 160, 40)            # sýtejšia zlatá — hlavný akcent
COLOR_TRUMP = (0, 190, 170)            # tyrkysová pre tromfy
COLOR_PANEL_BG = (25, 15, 8, 200)      # priehľadná tmavá hnedá pre panely
# Farby tlačidiel
COLOR_BUTTON_PRIMARY = (180, 110, 45)      # teplá zlatohnedá — hlavné tlačidlo
COLOR_BUTTON_SECONDARY = (60, 45, 30)      # tmavá hnedá — sekundárne tlačidlo

# ------------------------------------------------------------------
# GUI - Fonty
# ------------------------------------------------------------------
FONT_PATH = None
FONT_SIZE_SMALL = 18
FONT_SIZE_MEDIUM = 24
FONT_SIZE_LARGE = 32
FONT_SIZE_XLARGE = 48
FONT_SIZE_INFO = 28

# ------------------------------------------------------------------
# GUI - Rozmery
# Rozloženie hernej obrazovky (ruky, štich, talon, tlačidlá…) je v
# gui/layout.py — ukotvené podľa logickej výšky okna (1080…1200).
# ------------------------------------------------------------------
CARD_FAN_OFFSET = 100      # rozostup kariet talonu
BUTTON_RADIUS = 8


# ------------------------------------------------------------------
# GUI - Animácie
# ------------------------------------------------------------------
# Rýchlosť animácií (Nastavenia → Hra): násobok základnej rýchlosti
# letu karty na stôl (CardThrowAnimation) a zberu štichu (TrickAnimation,
# tá sa nikdy nespomalí pod 1.0×). Rozdávanie má pevnú rýchlosť.
ANIMATION_SPEED_MIN = 0.5
ANIMATION_SPEED_MAX = 2.0
ANIMATION_SPEED_DEFAULT = 1.5

# Smer hry (Nastavenia → Hra): "cw" = v smere hodinových ručičiek (zvyk
# v ČR, predvolené — česká hra), "ccw" = proti smeru (zvyk na Slovensku).
PLAY_DIRECTION_DEFAULT = "cw"
CARD_DEAL_DELAY = 50

# ------------------------------------------------------------------
# Obrázok zadnej strany karty
# ------------------------------------------------------------------
CARD_BACK_IMAGE = "card-back.png"

def get_font(size: int) -> pygame.font.Font:
    """Vráti font s podporou diakritiky."""
    for font_name in ("tahoma", "arial"):
        try:
            font = pygame.font.SysFont(font_name, size)
            return font
        except:
            continue
    return pygame.font.SysFont(None, size)  # fallback — systémový default