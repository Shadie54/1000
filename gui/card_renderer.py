# gui/card_renderer.py

import pygame
import os
from game.card import Card
from game.trick import Trick
from config import (
    CARDS_MEDIUM_PATH, CARDS_SMALL_PATH, CARD_BACK_IMAGE,
    CARD_SIZE_MEDIUM, CARD_SIZE_SMALL,
    CARD_FAN_OFFSET, CARD_OVERLAP,
    TABLE_CENTER_X, TABLE_CENTER_Y,
    TALON_X, TALON_Y,
    COLOR_YELLOW, COLOR_GREEN, COLOR_WHITE, COLOR_GOLD,
    NUM_PLAYERS
)


class CardRenderer:
    def __init__(self, screen: pygame.Surface, debug: bool = False):
        self.screen = screen
        self.debug = debug
        self._cache: dict[str, pygame.Surface] = {}     # cache načítaných obrázkov

        # Pozície kariet na stole pre každého hráča v štichu
        self.trick_positions = {
            0: (TABLE_CENTER_X, TABLE_CENTER_Y + 120),   # človek (dole)
            1: (TABLE_CENTER_X - 150, TABLE_CENTER_Y),   # AI ľavý
            2: (TABLE_CENTER_X + 150, TABLE_CENTER_Y),   # AI pravý
        }

        # Pozície rúk hráčov
        self.hand_configs = {
            0: {"direction": "horizontal", "x": 200, "y": 860, "offset": 100},
            1: {"direction": "vertical", "x": 30, "y": 100, "offset": 50},
            2: {"direction": "vertical", "x": 1600, "y": 100, "offset": 50},
        }

    # ------------------------------------------------------------------
    # Načítanie obrázkov
    # ------------------------------------------------------------------

    def _load_image(self, filename: str, size: tuple, path: str) -> pygame.Surface:
        """Načíta obrázok z disku alebo z cache."""
        key = f"{path}/{filename}"
        if key not in self._cache:
            full_path = os.path.join(path, filename)
            try:
                img = pygame.image.load(full_path).convert_alpha()
                img = pygame.transform.scale(img, size)
                self._cache[key] = img
            except FileNotFoundError:
                # Ak obrázok chýba — nakreslíme placeholder
                surf = pygame.Surface(size, pygame.SRCALPHA)
                surf.fill((200, 200, 200))
                font = pygame.font.SysFont(None, 18)
                text = font.render(filename[:10], True, (0, 0, 0))
                surf.blit(text, (5, size[1] // 2 - 10))
                self._cache[key] = surf
        return self._cache[key]

    def _get_card_image(self, card: Card, size: str = "medium") -> pygame.Surface:
        """Vráti obrázok karty."""
        path = CARDS_MEDIUM_PATH if size == "medium" else CARDS_SMALL_PATH
        card_size = CARD_SIZE_MEDIUM if size == "medium" else CARD_SIZE_SMALL
        return self._load_image(card.image_name, card_size, path)

    def _get_card_back(self, size: str = "medium") -> pygame.Surface:
        """Vráti obrázok zadnej strany karty."""
        path = CARDS_MEDIUM_PATH if size == "medium" else CARDS_SMALL_PATH
        card_size = CARD_SIZE_MEDIUM if size == "medium" else CARD_SIZE_SMALL
        return self._load_image(CARD_BACK_IMAGE, card_size, path)

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

            if show_faces:
                img = self._get_card_image(card)
            else:
                img = self._get_card_back()

            # Rotácia pre vertikálne ruky (AI hráči)
            if config["direction"] == "vertical":
                img = pygame.transform.rotate(img, 90)

            self.screen.blit(img, (x, y))

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

    def _card_position(self, config: dict, index: int) -> tuple[int, int]:
        """Vypočíta pozíciu karty v ruke podľa konfigurácie."""
        if config["direction"] == "horizontal":
            x = config["x"] + index * config["offset"]
            y = config["y"]
        else:
            x = config["x"]
            y = config["y"] + index * config["offset"]
        return x, y

    def _draw_highlight(self, x: int, y: int, size: tuple, color: tuple):
        """Nakreslí farebný okraj okolo karty."""
        rect = pygame.Rect(x - 2, y - 2, size[0] + 4, size[1] + 4)
        pygame.draw.rect(self.screen, color, rect, width=3, border_radius=5)

    # ------------------------------------------------------------------
    # Kreslenie štichu na stole
    # ------------------------------------------------------------------

    def draw_trick(self, trick: Trick):
        """Nakreslí aktuálny štich na stole."""
        for player_index, card in trick.played_cards:
            pos = self.trick_positions[player_index]
            img = self._get_card_image(card)
            rect = img.get_rect(center=pos)
            self.screen.blit(img, rect)

            # V debug móde zobraz index hráča
            if self.debug:
                font = pygame.font.SysFont(None, 20)
                label = font.render(str(player_index), True, COLOR_WHITE)
                self.screen.blit(label, (rect.x, rect.y - 15))

    # ------------------------------------------------------------------
    # Kreslenie talonu
    # ------------------------------------------------------------------

    def draw_talon(self, count: int):
        """Nakreslí talon (zadná strana, počet kariet)."""
        for i in range(count):
            img = self._get_card_back()
            x = TALON_X + i * 15
            y = TALON_Y
            self.screen.blit(img, (x, y))

        # Popisok
        font = pygame.font.SysFont(None, 22)
        label = font.render("Talon", True, COLOR_WHITE)
        self.screen.blit(label, (TALON_X, TALON_Y - 20))

    def draw_talon_debug(self, talon_cards: list):
        """V debug móde zobrazí talon s lícom kariet."""
        for i, card in enumerate(talon_cards):
            img = self._get_card_image(card)
            x = TALON_X + i * 15
            y = TALON_Y
            self.screen.blit(img, (x, y))

        font = pygame.font.SysFont(None, 22)
        label = font.render("Talon [DEBUG]", True, COLOR_YELLOW)
        self.screen.blit(label, (TALON_X, TALON_Y - 20))

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