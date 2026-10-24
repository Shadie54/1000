# gui/layout.py
#
# Rozloženie hernej obrazovky ako funkcia logickej výšky L_h — rework
# rozlíšení, krok 5 (claude/13_RESOLUTION_REWORK_ANALYSIS.md §3).
#
# Logická šírka je vždy 1920, výška L_h = 1080 (16:9) … 1200 (16:10).
# Prvky sú ukotvené ZVISLE (d = L_h − 1080):
#   hore   — panely Tromf / Skóre / Kolo                        (+0)
#   stred  — štich, talon, tlačidlá dražby/tromfu, posúvač
#            navýšenia, ruky počítačov, ich menovky a bubliny,
#            cieľ animácie štichu k počítačom                   (+d/2)
#   dole   — ruka hráča, tlačidlá vpravo dole, menovka, bublina
#            a správa hráča, hint rozdávania, cieľ animácie
#            štichu k hráčovi                                   (+d)
# Pri 16:10 sa tak extra výška (120 px) rozdelí: +60 px medzi panely
# a štich, +60 px medzi štich a ruku hráča.
#
# Pri L_h = 1080 dáva tento modul PRESNE tie isté čísla, aké boli predtým
# v config.py / card_renderer / speech_bubble / trick_animation / screen
# (overené pixelovým porovnaním galérie). Jediný zdroj rozloženia hernej
# obrazovky — duplicitné kópie súradníc v komponentoch sú odstránené.
#
# Rozloženie sa počíta pre AKTUÁLNU logickú výšku okna (gui/display.py),
# nie pre tú pri štarte — pripravené na zmenu rozlíšenia za behu (krok 7).

from dataclasses import dataclass, field

import pygame

from config import CARD_SIZE_MEDIUM, CARD_FAN_OFFSET

LOGICAL_W = 1920
REF_H = 1080
CARD_W, CARD_H = CARD_SIZE_MEDIUM


@dataclass(frozen=True)
class GameLayout:
    l_h: int
    width: int = LOGICAL_W
    table_center: tuple[int, int] = (0, 0)
    hand_configs: dict = field(default_factory=dict)
    trick_positions: dict = field(default_factory=dict)
    trick_collect_targets: dict = field(default_factory=dict)
    talon_pos: tuple[int, int] = (0, 0)
    button_y: int = 0
    bid_panel_y: int = 0
    side_buttons_y: int = 0
    label_positions: dict = field(default_factory=dict)
    bubble_positions: dict = field(default_factory=dict)
    message_bottom_y: int = 0
    deal_hint_y: int = 0

    # --- tlačidlá v strede stola (pygame.Rect je meniteľný — vždy nový) --

    def _center_button(self, dx: int) -> pygame.Rect:
        return pygame.Rect(self.table_center[0] + dx, self.button_y, 180, 55)

    def bid_rect(self) -> pygame.Rect:          # "Dám +10"
        return self._center_button(-200)

    def pass_rect(self) -> pygame.Rect:         # "Dobrý"
        return self._center_button(20)

    def confirm_rect(self) -> pygame.Rect:      # "Potvrdiť" (odhodenie)
        return self._center_button(-90)

    def trump_yes_rect(self) -> pygame.Rect:
        return self._center_button(-200)

    def trump_no_rect(self) -> pygame.Rect:
        return self._center_button(20)

    # --- tlačidlá vpravo dole --------------------------------------------

    def _side_button(self, row: int) -> pygame.Rect:
        return pygame.Rect(LOGICAL_W - 320, self.side_buttons_y + row * 60, 200, 50)

    def last_trick_rect(self) -> pygame.Rect:
        return self._side_button(-1)

    def sort_rect(self) -> pygame.Rect:
        return self._side_button(0)

    def info_rect(self) -> pygame.Rect:
        return self._side_button(1)

    def menu_rect(self) -> pygame.Rect:
        return self._side_button(2)


def build(l_h: int) -> GameLayout:
    """Rozloženie pre logickú výšku l_h (1080…1200)."""
    d = l_h - REF_H
    mid = d // 2
    cx, cy = LOGICAL_W // 2, l_h // 2
    human_y = l_h - 221                  # 1080 → 859 (= int(1080·0.796))
    ai_y = 97 + mid                      # 1080 → 97  (= int(1080·0.09))

    hand_configs = {
        0: {"direction": "horizontal", "x": 200, "y": human_y, "offset": 100},
        1: {"direction": "vertical", "x": 30, "y": ai_y, "offset": 50},
        2: {"direction": "vertical", "x": LOGICAL_W - 330, "y": ai_y, "offset": 50},
    }
    return GameLayout(
        l_h=l_h,
        table_center=(cx, cy),
        hand_configs=hand_configs,
        trick_positions={
            0: (cx, cy + 120),           # hráč (dole)
            1: (cx - 150, cy),           # Počítač 1 (vľavo)
            2: (cx + 150, cy),           # Počítač 2 (vpravo)
        },
        trick_collect_targets={          # kam letí vyhratý štich / talon
            0: (cx, l_h - 50),
            1: (50, 270 + mid),          # 1080 → 270 (= H // 4)
            2: (LOGICAL_W - 50, 270 + mid),
        },
        talon_pos=(cx - (CARD_W + CARD_FAN_OFFSET) // 2, cy - CARD_H // 2),
        button_y=cy + CARD_H // 2 + 18,            # 1080 → 704
        bid_panel_y=cy + CARD_H // 2 - 130,        # 1080 → 556
        side_buttons_y=l_h - 220,                  # 1080 → 860
        label_positions={
            0: (cx, l_h - 30),
            1: (120, cy - 120),
            2: (LOGICAL_W - 120, cy - 120),
        },
        bubble_positions={
            0: (cx - LOGICAL_W // 4, human_y - 30),
            1: (int(LOGICAL_W * 0.24), 324 + mid),  # 1080 → 324 (= 0.3·H)
            2: (int(LOGICAL_W * 0.82), 324 + mid),
        },
        message_bottom_y=human_y - 55,   # správa: stred = toto − výška/2
        deal_hint_y=l_h - 60,
    )


_cache: dict[int, GameLayout] = {}


def game() -> GameLayout:
    """Rozloženie pre aktuálnu logickú výšku okna (cache podľa L_h)."""
    from gui import display
    l_h = display.logical_height()
    layout = _cache.get(l_h)
    if layout is None:
        layout = _cache[l_h] = build(l_h)
    return layout
