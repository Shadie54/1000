# gui/speech_bubble.py

import random

import pygame
from gui import layout, ui_style
from gui.scoreboard import load_suit_icon

# Vzhľad bublín (grafický rework 2026-10-28, štýl gui/ui_style.py, z CHUJ):
# tmavé nepriehľadné telo so zaoblenými rohmi a tieňom, rám aj text vo
# farbe významu bubliny, chvost plynulo napojený na telo.
BUBBLE_BODY = (20, 13, 8)
BUBBLE_RADIUS = 14
TAIL_SIZE = 12

COLOR_TRUMP_BUBBLE = ui_style.GOLD               # tromf
COLOR_BID = ui_style.BTN_TEXT_HOVER              # DÁVAM …, inštrukcia
COLOR_BID_NONE = (170, 155, 135)                 # Ja som DOBRÝ …
COLOR_POINTS_GOOD = (122, 200, 110)              # body / splnená povinnosť
COLOR_POINTS_BAD = (232, 112, 84)                # nesplnená povinnosť


class SpeechBubble:
    def __init__(self, canvas):
        # Kreslí cez Canvas (gui/canvas.py); pozície z gui/layout.py.
        self.canvas = canvas
        self.font_large = canvas.font(32)
        self.font_medium = canvas.font(24)
        self._icon_cache: dict = {}

        # Aktívne bubliny [{player_index, text, suit, timer, color}]
        self.bubbles: list[dict] = []

        # Pozície bublín pre každého hráča
        lay = layout.game()
        self.bubble_positions = dict(lay.bubble_positions)
        self.seat_of = dict(lay.seat_of)        # chvost bubliny k hráčovi

    # ------------------------------------------------------------------
    # Pridanie bubliny
    # ------------------------------------------------------------------

    def show_trump(self, player_index: int, suit: str,
                   is_new: bool = False, duration_ms: int = 4000):
        """Zobrazí tromfovú bublinu."""
        text = "NOVÝ TROMF!" if is_new else "TROMF!"
        self._add_bubble(
            player_index=player_index,
            text=text,
            suit=suit,
            duration_ms=duration_ms,
            color=COLOR_TRUMP_BUBBLE
        )

    def show_bid(self, player_index: int, amount: int | None,
                 duration_ms: int = 5000):
        """Zobrazí biddingová bublinu."""
        if amount is None:
            answers = [
                "Ja som DOBRÝ",
                "Som DOBRÝ",
                "Tak si to BER",
                "NECHAJ si to",
                "DOBRÝ"
            ]

            text = random.choice(answers)
            color = COLOR_BID_NONE
        else:
            text = f"DÁVAM {amount}!"
            color = COLOR_BID

        self._add_bubble(
            player_index=player_index,
            text=text,
            suit=None,
            duration_ms=duration_ms,
            color=color
        )

    def show_instruction(self, player_index: int, text: str):
        """
        Zobrazí inštrukciu ako bublinu hráča.
        Ostáva zobrazená kým ju manuálne neodstránime.
        """
        self._add_bubble(
            player_index=player_index,
            text=text,
            suit=None,
            duration_ms=99999999,  # "nekonečno" — zmizne manuálne
            color=COLOR_BID
        )

    def hide_instruction(self, player_index: int):
        """Odstráni inštrukčnú bublinu."""
        self.bubbles = [
            b for b in self.bubbles
            if b["player_index"] != player_index
        ]

    def _add_bubble(self, player_index: int, text: str,
                    suit: str | None, duration_ms: int, color: tuple):
        """Pridá bublinu do zoznamu."""
        # Odstráň existujúcu bublinu toho istého hráča
        self.bubbles = [
            b for b in self.bubbles
            if b["player_index"] != player_index
        ]
        self.bubbles.append({
            "player_index": player_index,
            "text": text,
            "suit": suit,
            "timer": pygame.time.get_ticks() + duration_ms,
            "color": color
        })

    # ------------------------------------------------------------------
    # Aktualizácia
    # ------------------------------------------------------------------

    def update(self):
        """Odstráni expirované bubliny."""
        now = pygame.time.get_ticks()
        self.bubbles = [
            b for b in self.bubbles
            if now < b["timer"]
        ]

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def draw(self):
        """Nakreslí všetky aktívne bubliny."""
        self.update()
        for bubble in self.bubbles:
            self._draw_bubble(bubble)

    def _draw_bubble(self, bubble: dict):
        """Nakreslí jednu bublinu."""
        player_index = bubble["player_index"]
        cx, cy = self.bubble_positions[player_index]

        text_surf = self.font_large.render(bubble["text"], True, bubble["color"])
        text_w = text_surf.get_width()
        text_h = text_surf.get_height()

        # Rozmery bubliny
        icon_size = 40 if bubble["suit"] else 0
        padding = 16
        bubble_w = max(text_w, icon_size) + padding * 2
        bubble_h = text_h + icon_size + padding * 2 + (8 if bubble["suit"] else 0)

        bx = cx - bubble_w // 2
        by = cy - bubble_h

        rect = pygame.Rect(bx, by, bubble_w, bubble_h)
        c = self.canvas
        # Tieň, telo, jemné presvetlenie hornej časti, rám
        c.overlay(rect.move(0, 4), (0, 0, 0, 110), border_radius=BUBBLE_RADIUS)
        c.rect(BUBBLE_BODY, rect, border_radius=BUBBLE_RADIUS)
        c.overlay((bx + 2, by + 2, bubble_w - 4, bubble_h // 2 - 2),
                  (255, 214, 140, 10), border_radius=BUBBLE_RADIUS - 2)
        c.rect(bubble["color"], rect, width=2, border_radius=BUBBLE_RADIUS)

        # Chvost bubliny (trojuholník)
        self._draw_tail(cx, by + bubble_h, by, bubble_w, bubble_h, player_index, bubble["color"])

        # Text
        text_rect = text_surf.get_rect(
            centerx=cx,
            top=by + padding
        )
        self.canvas.blit(text_surf, text_rect)

        # Ikonka farby (ak je tromf)
        if bubble["suit"]:
            icon = self._load_icon(bubble["suit"], icon_size)
            if icon:
                icon_rect = icon.get_rect(
                    centerx=cx,
                    centery=by + padding + text_h + 8 + icon_size // 2
                )
                self.canvas.blit(icon, icon_rect)

    def _draw_tail(self, cx: int, base_y: int, by: int, bubble_w: int, bubble_h: int,
                   player_index: int, color: tuple):
        """Chvost k hráčovi podľa jeho miesta pri stole: výplň farbou tela
        (prekryje rám v mieste napojenia, takže chvost plynulo vychádza
        z bubliny) + dve hrany vo farbe rámu."""
        t = TAIL_SIZE
        bx = cx - bubble_w // 2
        mid_y = by + bubble_h // 2
        seat = self.seat_of.get(player_index, "bottom")
        if seat == "bottom":
            a, tip, b = (cx - t, base_y), (cx, base_y + 2 * t), (cx + t, base_y)
            inward = (0, -3)
        elif seat == "left":
            a, tip, b = (bx, mid_y - t), (bx - 2 * t, mid_y), (bx, mid_y + t)
            inward = (3, 0)
        else:
            right_x = bx + bubble_w
            a, tip, b = (right_x, mid_y - t), (right_x + 2 * t, mid_y), (right_x, mid_y + t)
            inward = (-3, 0)
        a_in = (a[0] + inward[0], a[1] + inward[1])
        b_in = (b[0] + inward[0], b[1] + inward[1])
        self.canvas.polygon(BUBBLE_BODY, [a_in, a, tip, b, b_in])
        self.canvas.line(color, a, tip, width=2)
        self.canvas.line(color, tip, b, width=2)

    def _load_icon(self, suit: str, size: int):
        """Načíta ikonku farby (LSurf, pomer strán zachovaný)."""
        key = f"{suit}-{size}"
        if key not in self._icon_cache:
            self._icon_cache[key] = load_suit_icon(self.canvas, suit, size)
        return self._icon_cache[key]

    def show_round_result(self, player_index: int, points: int,
                          is_bidder: bool, fulfilled: bool = True):
        """Zobrazí výsledok kola ako bublinu."""
        if is_bidder:
            if fulfilled:
                text = f"+{points}"
                color = COLOR_POINTS_GOOD
            else:
                text = f"-{points}"
                color = COLOR_POINTS_BAD
        else:
            text = f"+{points}"
            color = COLOR_POINTS_GOOD

        self._add_bubble(
            player_index=player_index,
            text=text,
            suit=None,
            duration_ms=3000,
            color=color
        )

    def __repr__(self) -> str:
        return f"SpeechBubble(active={len(self.bubbles)})"