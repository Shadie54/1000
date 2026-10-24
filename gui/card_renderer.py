# gui/card_renderer.py

import os

import pygame

from config import (
    CARDS_MEDIUM_PATH, CARD_BACK_IMAGE,
    CARD_SIZE_MEDIUM, CARD_SIZE_SMALL,
    CARD_FAN_OFFSET,
    COLOR_YELLOW, COLOR_GREEN, COLOR_WHITE, COLOR_GOLD,
)
from game.card import Card
from game.trick import Trick
from gui import layout
from gui.canvas import LSurf


class CardRenderer:
    def __init__(self, canvas, debug: bool = False):
        # Kreslí cez Canvas (gui/canvas.py) v logických súradniciach;
        # pozície rúk, štichu a talonu sú z gui/layout.py.
        self.canvas = canvas
        self.debug = debug
        self._cache: dict[str, LSurf] = {}     # cache placeholderov

        lay = layout.game()
        # Pozície kariet na stole pre každého hráča v štichu
        self.trick_positions = dict(lay.trick_positions)
        self.hand_configs = {i: dict(cfg) for i, cfg in lay.hand_configs.items()}
        self.talon_pos = lay.talon_pos
    # ------------------------------------------------------------------
    # Načítanie obrázkov
    # ------------------------------------------------------------------

    def _load_image(self, filename: str, size: tuple, angle: int = 0) -> LSurf:
        """Karta cez Canvas (ostrá pri každom rozlíšení, cache v Canvase).
        Ak obrázok chýba — placeholder."""
        if os.path.exists(os.path.join(CARDS_MEDIUM_PATH, filename)):
            return self.canvas.card(filename, angle, size, smooth=False)
        key = f"{filename}/{size}/{angle}"
        if key not in self._cache:
            surf = self.canvas.new_surface(size)
            surf.phys.fill((200, 200, 200))
            text = self.canvas.font(18).render(filename[:10], True, (0, 0, 0))
            surf.phys.blit(text.phys, (round(5 * self.canvas.s),
                                       round((size[1] // 2 - 10) * self.canvas.s)))
            if angle:
                surf = LSurf(pygame.transform.rotate(surf.phys, angle),
                             *(size[::-1] if angle % 180 else size))
            self._cache[key] = surf
        return self._cache[key]

    def _get_card_image(self, card: Card, size: str = "medium", angle: int = 0) -> LSurf:
        """Vráti obrázok karty."""
        card_size = CARD_SIZE_MEDIUM if size == "medium" else CARD_SIZE_SMALL
        return self._load_image(card.image_name, card_size, angle)

    def _get_card_back(self, size: str = "medium", angle: int = 0) -> LSurf:
        """Vráti obrázok zadnej strany karty."""
        card_size = CARD_SIZE_MEDIUM if size == "medium" else CARD_SIZE_SMALL
        return self._load_image(CARD_BACK_IMAGE, card_size, angle)

    # ------------------------------------------------------------------
    # Kreslenie ruky hráča
    # ------------------------------------------------------------------

    def draw_hand(self, cards: list[Card], player_index: int,
                  is_human: bool, selected_cards: list[Card],
                  highlight_playable: bool, trump_suit: str | None,
                  lead_suit: str | None, played_cards: list = None):
        """Nakreslí ruku hráča."""
        if not cards:
            return

        config = self.hand_configs[player_index]
        show_faces = is_human or self.debug

        for i, card in enumerate(cards):
            x, y = self._card_position(config, i)

            # Posun vybranej karty nahor
            if card in selected_cards:
                y -= 20 if config["direction"] == "horizontal" else 0
                x -= 20 if config["direction"] == "vertical" else 0

            # Rotácia pre vertikálne ruky (AI hráči)
            angle = 90 if config["direction"] == "vertical" else 0
            if show_faces:
                img = self._get_card_image(card, angle=angle)
            else:
                img = self._get_card_back(angle=angle)

            self.canvas.blit(img, (x, y))

            # Zvýraznenie hrateľných kariet
            if highlight_playable and show_faces:
                from game.hand import Hand
                h = Hand()
                h.add_cards(cards)
                playable = h.get_playable_cards(lead_suit, trump_suit, played_cards or [])  # ← pridané
                if card in playable:
                    self._draw_highlight(x, y, CARD_SIZE_MEDIUM, COLOR_GREEN)
                else:
                    self._draw_highlight(x, y, CARD_SIZE_MEDIUM, (100, 100, 100, 100))

            # Zvýraznenie tromfového páru
            if show_faces and trump_suit is None and card.suit and \
               card.rank in ("over", "king"):
                from game.hand import Hand
                h = Hand()
                h.add_cards(cards)
                if h.has_trump_pair(card.suit):
                    self._draw_highlight(x, y, CARD_SIZE_MEDIUM, COLOR_GOLD)

    @staticmethod
    def _card_position(config: dict, index: int) -> tuple[int, int]:
        """Vypočíta pozíciu karty v ruke podľa konfigurácie."""
        if config["direction"] == "horizontal":
            x = config["x"] + index * config["offset"]
            y = config["y"]
        else:
            x = config["x"]
            y = config["y"] + index * config["offset"]
        return x, y

    def hand_card_center(self, player_index: int, cards: list[Card],
                         card: Card) -> tuple[int, int]:
        """Stred karty v ruke (odtiaľ letí pri zahratí — CardThrowAnimation)."""
        config = self.hand_configs[player_index]
        idx = cards.index(card) if card in cards else 0
        x, y = self._card_position(config, idx)
        cw, ch = CARD_SIZE_MEDIUM
        if config["direction"] == "vertical":
            return x + ch // 2, y + cw // 2      # karta otočená o 90°
        return x + cw // 2, y + ch // 2

    def _draw_highlight(self, x: int, y: int, size: tuple, color: tuple):
        """Nakreslí farebný okraj okolo karty."""
        rect = pygame.Rect(x - 2, y - 2, size[0] + 4, size[1] + 4)
        self.canvas.rect(color, rect, width=3, border_radius=5)

    # ------------------------------------------------------------------
    # Kreslenie štichu na stole
    # ------------------------------------------------------------------

    def draw_trick(self, trick: Trick, exclude_players: set | None = None):
        """Nakreslí aktuálny štich na stole. exclude_players = hráči, ktorých
        karta ešte letí (CardThrowAnimation ju kreslí sama)."""
        for player_index, card in trick.played_cards:
            if exclude_players and player_index in exclude_players:
                continue
            pos = self.trick_positions[player_index]
            img = self._get_card_image(card)
            rect = img.get_rect(center=pos)
            self.canvas.blit(img, rect)

            # V debug móde zobraz index hráča
            if self.debug:
                font = self.canvas.font(20)
                label = font.render(str(player_index), True, COLOR_WHITE)
                self.canvas.blit(label, (rect.x, rect.y - 15))

    # ------------------------------------------------------------------
    # Kreslenie talonu
    # ------------------------------------------------------------------

    def draw_talon(self, count: int):
        """Nakreslí talon (zadná strana kariet)."""
        tx, ty = self.talon_pos
        for i in range(count):
            img = self._get_card_back()
            self.canvas.blit(img, (tx + i * CARD_FAN_OFFSET, ty))

        # Popisok
        font = self.canvas.font(22)
        label = font.render("Talon", True, COLOR_WHITE)
        self.canvas.blit(label, (tx, ty - 40))

    def draw_talon_debug(self, talon_cards: list):
        """V debug móde zobrazí talon s lícom kariet."""
        tx, ty = self.talon_pos
        for i, card in enumerate(talon_cards):
            img = self._get_card_image(card)
            self.canvas.blit(img, (tx + i * CARD_FAN_OFFSET, ty))

        font = self.canvas.font(22)
        label = font.render("Talon [DEBUG]", True, COLOR_YELLOW)
        self.canvas.blit(label, (tx, ty - 40))

    # ------------------------------------------------------------------
    # Detekcia kliku na kartu
    # ------------------------------------------------------------------

    def get_clicked_card(self, pos: tuple[int, int],
                         cards: list[Card],
                         player_index: int) -> Card | None:
        """
        Vráti kartu na ktorú hráč klikol.
        Prechádza karty od poslednej (vrchnej) po prvú.
        """
        if not cards:
            return None

        config = self.hand_configs[player_index]
        card_w, card_h = CARD_SIZE_MEDIUM

        # Prechádzame od konca (vrchná karta je naposledy kreslená)
        for i in range(len(cards) - 1, -1, -1):
            x, y = self._card_position(config, i)

            if config["direction"] == "vertical":
                # Rotovaná karta má prehodené rozmery
                rect = pygame.Rect(x, y, card_h, card_w)
            else:
                rect = pygame.Rect(x, y, card_w, card_h)

            if rect.collidepoint(pos):
                return cards[i]

        return None

    def __repr__(self) -> str:
        return f"CardRenderer(debug={self.debug}, cached={len(self._cache)} images)"