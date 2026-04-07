# config.py

import os
import pygame

pygame.init()

# Detekcia rozlíšenia monitora
_info = pygame.display.Info()
SCREEN_WIDTH = _info.current_w
SCREEN_HEIGHT = _info.current_h

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
# GUI - Pozície a rozmery (SCREEN_WIDTH/HEIGHT musia byť definované vyššie)
# ------------------------------------------------------------------
CARD_OVERLAP = 30
CARD_FAN_OFFSET = 100    # bolo 40, zvýšime na 100

HUMAN_HAND_Y = 850
HUMAN_HAND_X_START = 400

AI_LEFT_X = 30
AI_LEFT_Y_START = 200

AI_RIGHT_X = 1800
AI_RIGHT_Y_START = 200

TABLE_CENTER_X = SCREEN_WIDTH // 2      # 960
TABLE_CENTER_Y = SCREEN_HEIGHT // 2     # 540

TALON_X = TABLE_CENTER_X - (CARD_SIZE_MEDIUM[0] + CARD_FAN_OFFSET) // 2
TALON_Y = TABLE_CENTER_Y - (CARD_SIZE_MEDIUM[1] // 2)

# SKÓRE — pravý horný roh (kde bolo KOLO)
SCORE_PANEL_WIDTH = 300
SCORE_PANEL_HEIGHT = 220
SCORE_PANEL_X = SCREEN_WIDTH //2 - SCORE_PANEL_WIDTH // 2
SCORE_PANEL_Y = 20

# KOLO — pravý dolný roh
INFO_PANEL_X = SCREEN_WIDTH - 320
INFO_PANEL_Y = SCREEN_HEIGHT - 220
INFO_PANEL_WIDTH = 300
INFO_PANEL_HEIGHT = 300

BUTTON_Y = TABLE_CENTER_Y + CARD_SIZE_MEDIUM[1] // 2 + 18  # zhoduje sa so sliderom
BUTTON_WIDTH = 180                      # trochu širšie
BUTTON_HEIGHT = 55
BUTTON_RADIUS = 8

# SORT - tlačidlo na usporiadanie
BUTTON_SORT_X = INFO_PANEL_X
BUTTON_SORT_Y = INFO_PANEL_Y
BUTTON_SORT_WIDTH = 200
BUTTON_SORT_HEIGHT = 50

#MENU - tlačidlo počas hry
BUTTON_MENU_X = BUTTON_SORT_X
BUTTON_MENU_Y = BUTTON_SORT_Y + BUTTON_SORT_HEIGHT + 10
BUTTON_MENU_WIDTH = BUTTON_SORT_WIDTH
BUTTON_MENU_HEIGHT = BUTTON_SORT_HEIGHT
# ------------------------------------------------------------------
# GUI - Animácie
# ------------------------------------------------------------------
ANIMATION_SPEED = 8
CARD_DEAL_DELAY = 50

# ------------------------------------------------------------------
# Obrázok zadnej strany karty
# ------------------------------------------------------------------
CARD_BACK_IMAGE = "card-back.png"