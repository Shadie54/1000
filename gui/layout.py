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
#
# Smer hry (Nastavenia → Hra → Smer hry) mení len MIESTA počítačov pri
# stole (seats()); poradie ťahov v hernej logike je vždy 0 → 1 → 2.

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
    clockwise: bool = True
    seat_of: dict = field(default_factory=dict)   # hráč → "bottom"/"left"/"right"
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
        return pygame.Rect(LOGICAL_W - 340, self.side_buttons_y + row * 60, 240, 50)

    # Stĺpec zdola: Menu, Trofeje, Pravidlá, Zoradiť karty, Posledný štich
    # (posledný len počas štichov). Horné tlačidlo pri 1080 končí 12 px
    # pod rukou počítača s 10 kartami.
    def last_trick_rect(self) -> pygame.Rect:
        return self._side_button(-2)

    def sort_rect(self) -> pygame.Rect:
        return self._side_button(-1)

    def info_rect(self) -> pygame.Rect:
        return self._side_button(0)

    def trophies_rect(self) -> pygame.Rect:
        return self._side_button(1)

    def menu_rect(self) -> pygame.Rect:
        return self._side_button(2)


def seats(clockwise: bool) -> dict[int, str]:
    """Miesto pri stole pre každého hráča. Poradie ťahov je vždy
    Hráč → Počítač 1 → Počítač 2 (herná logika sa nemení):
      v smere hodinových ručičiek (ČR) — Počítač 1 vľavo, Počítač 2 vpravo,
      proti smeru (SR)                 — Počítač 1 vpravo, Počítač 2 vľavo."""
    if clockwise:
        return {0: "bottom", 1: "left", 2: "right"}
    return {0: "bottom", 1: "right", 2: "left"}


def build(l_h: int, clockwise: bool = True) -> GameLayout:
    """Rozloženie pre logickú výšku l_h (1080…1200) a smer hry."""
    d = l_h - REF_H
    mid = d // 2
    cx, cy = LOGICAL_W // 2, l_h // 2
    human_y = l_h - 221                  # 1080 → 859 (= int(1080·0.796))
    ai_y = 97 + mid                      # 1080 → 97  (= int(1080·0.09))

    # Geometria podľa MIESTA pri stole (dole / vľavo / vpravo)
    by_seat = {
        "hand": {
            "bottom": {"direction": "horizontal", "x": 200, "y": human_y, "offset": 100},
            "left": {"direction": "vertical", "x": 30, "y": ai_y, "offset": 50},
            "right": {"direction": "vertical", "x": LOGICAL_W - 330, "y": ai_y, "offset": 50},
        },
        "trick": {                       # karta v štichu
            "bottom": (cx, cy + 120),
            "left": (cx - 150, cy),
            "right": (cx + 150, cy),
        },
        "collect": {                     # kam letí vyhratý štich / talon
            "bottom": (cx, l_h - 50),
            "left": (50, 270 + mid),     # 1080 → 270 (= H // 4)
            "right": (LOGICAL_W - 50, 270 + mid),
        },
        "label": {
            "bottom": (cx, l_h - 30),
            "left": (120, cy - 120),
            "right": (LOGICAL_W - 120, cy - 120),
        },
        "bubble": {
            "bottom": (cx - LOGICAL_W // 4, human_y - 30),
            "left": (int(LOGICAL_W * 0.24), 324 + mid),   # 1080 → 324 (= 0.3·H)
            "right": (int(LOGICAL_W * 0.82), 324 + mid),
        },
    }
    seat_of = seats(clockwise)

    def per_player(kind: str) -> dict:
        return {i: by_seat[kind][seat] for i, seat in seat_of.items()}

    return GameLayout(
        l_h=l_h,
        clockwise=clockwise,
        seat_of=seat_of,
        table_center=(cx, cy),
        hand_configs={i: dict(cfg) for i, cfg in per_player("hand").items()},
        trick_positions=per_player("trick"),
        trick_collect_targets=per_player("collect"),
        talon_pos=(cx - (CARD_W + CARD_FAN_OFFSET) // 2, cy - CARD_H // 2),
        button_y=cy + CARD_H // 2 + 18,            # 1080 → 704
        bid_panel_y=cy + CARD_H // 2 - 130,        # 1080 → 556
        side_buttons_y=l_h - 220,                  # 1080 → 860
        label_positions=per_player("label"),
        bubble_positions=per_player("bubble"),
        message_bottom_y=human_y - 55,   # správa: stred = toto − výška/2
        deal_hint_y=l_h - 60,
    )


_cache: dict[tuple[int, bool], GameLayout] = {}
_clockwise = True        # smer hry z Nastavení — nastavuje Screen


def set_clockwise(clockwise: bool):
    """Smer hry pre nasledujúce volania game() (Screen pri vytvorení)."""
    global _clockwise
    _clockwise = bool(clockwise)


def game() -> GameLayout:
    """Rozloženie pre aktuálnu logickú výšku okna a smer hry (cache)."""
    from gui import display
    key = (display.logical_height(), _clockwise)
    layout = _cache.get(key)
    if layout is None:
        layout = _cache[key] = build(*key)
    return layout
