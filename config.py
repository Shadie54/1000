# config.py

import os

# ------------------------------------------------------------------
# Obrazovka
# ------------------------------------------------------------------
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

# ------------------------------------------------------------------
# Cesty k obrázkom kariet
# ------------------------------------------------------------------
CARDS_SMALL_PATH = "assets/cards-small"
CARDS_MEDIUM_PATH = "assets/cards-medium"
CARDS_LARGE_PATH = "assets/cards-large"

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

# ------------------------------------------------------------------
# Herné pravidlá
# ------------------------------------------------------------------
MIN_BID = 50
BID_STEP = 10
WINNING_SCORE = 1000
TALON_SIZE = 2
ROUND_ROUNDING = 5
NUM_PLAYERS = 3

# ------------------------------------------------------------------
# Debug režim
# ------------------------------------------------------------------
DEBUG_MODE = False

# ------------------------------------------------------------------
# GUI - Farby (R, G, B)
# ------------------------------------------------------------------
COLOR_BG = (34, 85, 34)
COLOR_BG_DARK = (20, 60, 20)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_YELLOW = (255, 215, 0)
COLOR_RED = (200, 30, 30)
COLOR_GREEN = (50, 200, 50)
COLOR_GRAY = (150, 150, 150)
COLOR_DARK_GRAY = (80, 80, 80)
COLOR_GOLD = (212, 175, 55)
COLOR_PANEL_BG = (20, 50, 20)

# ------------------------------------------------------------------
# GUI - Fonty
# ------------------------------------------------------------------
FONT_PATH = None
FONT_SIZE_SMALL = 18
FONT_SIZE_MEDIUM = 24
FONT_SIZE_LARGE = 32
FONT_SIZE_XLARGE = 48

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

TALON_X = TABLE_CENTER_X - 100
TALON_Y = 80

SCORE_PANEL_X = 20
SCORE_PANEL_Y = 20
SCORE_PANEL_WIDTH = 280
SCORE_PANEL_HEIGHT = 200

INFO_PANEL_X = SCREEN_WIDTH - 320
INFO_PANEL_Y = 20
INFO_PANEL_WIDTH = 300
INFO_PANEL_HEIGHT = 200

BUTTON_WIDTH = 160
BUTTON_HEIGHT = 50
BUTTON_RADIUS = 8

# ------------------------------------------------------------------
# GUI - Animácie
# ------------------------------------------------------------------
ANIMATION_SPEED = 8
CARD_DEAL_DELAY = 50

# ------------------------------------------------------------------
# Obrázok zadnej strany karty
# ------------------------------------------------------------------
CARD_BACK_IMAGE = "card-back.png"