# gui/deal_animation.py

import pygame

from config import (
    CARD_SIZE_MEDIUM, CARD_FAN_OFFSET, COLOR_WHITE, FONT_SIZE_MEDIUM,
)
from gui import layout


class DealAnimation:
    def __init__(self, canvas, card_renderer):
        # Kreslí cez Canvas; cieľové pozície = ruky z gui/layout.py
        # (tie isté, z ktorých kreslí CardRenderer).
        self.canvas = canvas
        self.card_renderer = card_renderer
        self.font = canvas.font(FONT_SIZE_MEDIUM)
        self.layout = layout.game()

        # Cieľové pozície pre každého hráča
        # {player_index: [(x, y), (x, y), ...]} — pozícia každej karty
        self.target_positions = {
            0: [],  # človek — dole
            1: [],  # AI ľavý
            2: [],  # AI pravý
        }
        self.talon_positions = []

        # Animačný stav
        self.cards_in_flight: list[dict] = []   # karty ktoré letia
        self.dealt_cards: list[dict] = []        # karty ktoré už doleteli
        self.deal_queue: list[dict] = []         # fronta kariet na rozdanie
        self.current_deal_index: int = 0
        self.deal_timer: int = 0
        self.deal_interval: int = 80            # ms medzi kartami
        self.card_speed: float = 25.0           # px za frame
        self.done: bool = False
        self.skipped: bool = False

        self._build_target_positions()

    # ------------------------------------------------------------------
    # Inicializácia pozícií
    # ------------------------------------------------------------------

    def _build_target_positions(self):
        """Vypočíta cieľové pozície kariet pre každého hráča — rovnako ako
        CardRenderer._card_position (karty doletia presne na miesto v ruke)."""
        from gui.card_renderer import CardRenderer
        for player_idx in (0, 1, 2):
            cfg = self.layout.hand_configs[player_idx]
            for i in range(10):
                self.target_positions[player_idx].append(
                    CardRenderer._card_position(cfg, i))

        # Talon
        tx, ty = self.layout.talon_pos
        for i in range(2):
            self.talon_positions.append((tx + i * CARD_FAN_OFFSET, ty))

    def _build_deal_queue(self, obligation_index: int):
        """
        Zostaví frontu kariet podľa poradia rozdávania.
        3-3-3 + 2(talon) + 4-4-4 + 3-3-3
        Začína hráčom s povinnosťou.
        """
        self.deal_queue = []

        # Počítadlá kariet pre každého hráča
        card_counters = {0: 0, 1: 0, 2: 0}
        talon_counter = 0

        def add_cards(player_idx: int, count: int):
            for _ in range(count):
                idx = card_counters[player_idx]
                self.deal_queue.append({
                    "target_player": player_idx,
                    "target_pos": self.target_positions[player_idx][idx],
                    "is_talon": False
                })
                card_counters[player_idx] += 1

        def add_talon(count: int):
            nonlocal talon_counter
            for _ in range(count):
                self.deal_queue.append({
                    "target_player": -1,
                    "target_pos": self.talon_positions[talon_counter],
                    "is_talon": True
                })
                talon_counter += 1

        # Poradie hráčov od povinnosti
        order = [
            (obligation_index + i) % 3
            for i in range(3)
        ]

        # 3-3-3
        for p in order:
            add_cards(p, 3)

        # 2 talon
        add_talon(2)

        # 4-4-4
        for p in order:
            add_cards(p, 4)

        # 3-3-3
        for p in order:
            add_cards(p, 3)

    # ------------------------------------------------------------------
    # Spustenie animácie
    # ------------------------------------------------------------------

    def start(self, obligation_index: int):
        """Spustí animáciu rozdávania."""
        self._build_deal_queue(obligation_index)
        self.current_deal_index = 0
        self.cards_in_flight = []
        self.dealt_cards = []
        self.deal_timer = pygame.time.get_ticks()
        self.done = False
        self.skipped = False

    # ------------------------------------------------------------------
    # Hlavná aktualizácia
    # ------------------------------------------------------------------

    def update(self):
        """Aktualizuje stav animácie."""
        if self.done or self.skipped:
            return

        now = pygame.time.get_ticks()

        # Pridaj novú kartu do letu
        if (self.current_deal_index < len(self.deal_queue)
                and now >= self.deal_timer):
            card_data = self.deal_queue[self.current_deal_index]
            self.cards_in_flight.append({
                "x": float(self.layout.table_center[0] - CARD_SIZE_MEDIUM[0] // 2),
                "y": float(self.layout.table_center[1] - CARD_SIZE_MEDIUM[1] // 2),
                "target_x": float(card_data["target_pos"][0]),
                "target_y": float(card_data["target_pos"][1]),
                "target_player": card_data["target_player"],
                "is_talon": card_data["is_talon"],
                "arrived": False
            })
            self.current_deal_index += 1
            self.deal_timer = now + self.deal_interval

        # Pohni kartami v lete
        for card in self.cards_in_flight:
            if card["arrived"]:
                continue

            dx = card["target_x"] - card["x"]
            dy = card["target_y"] - card["y"]
            dist = (dx ** 2 + dy ** 2) ** 0.5

            if dist <= self.card_speed:
                card["x"] = card["target_x"]
                card["y"] = card["target_y"]
                card["arrived"] = True
            else:
                card["x"] += dx / dist * self.card_speed
                card["y"] += dy / dist * self.card_speed

        # Presuň doletené karty do dealt_cards
        arrived = [c for c in self.cards_in_flight if c["arrived"]]
        for card in arrived:
            self.cards_in_flight.remove(card)
            self.dealt_cards.append(card)

        # Skontroluj či je animácia hotová
        if (self.current_deal_index >= len(self.deal_queue)
                and not self.cards_in_flight):
            self.done = True

    def handle_event(self, event: pygame.event.Event):
        """Spracuje udalosti — medzerník preskočí animáciu."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.skipped = True
                self.done = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.skipped = True
                self.done = True

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def draw(self, draw_table, draw_static=None):
        """Nakreslí stav animácie. draw_table = funkcia, ktorá nakreslí
        stôl (Screen._draw_table); draw_static = Screen._draw_static —
        stôl a doletené karty sa potom prekreslia len keď pribudne karta."""
        def static_part():
            draw_table()
            for card in self.dealt_cards:
                self._draw_card(card)

        if draw_static is not None:
            draw_static(("deal", len(self.dealt_cards)), static_part)
        else:
            static_part()

        # Karty v lete
        for card in self.cards_in_flight:
            self._draw_card(card)

        # Hint — preskočiť
        self._draw_skip_hint()

    def _draw_card(self, card: dict):
        """Nakreslí jednu kartu (zadná strana)."""
        # Rotácia pre AI hráčov — rovnako ako v ruke (CardRenderer.draw_hand)
        angle = 90 if card["target_player"] in (1, 2) else 0
        img = self.card_renderer._get_card_back(angle=angle)
        self.canvas.blit(img, (int(card["x"]), int(card["y"])))

    def _draw_skip_hint(self):
        """Zobrazí hint na preskočenie."""
        text = self.font.render(
            "Medzerník / klik — preskočiť", True, COLOR_WHITE
        )
        w, h = text.get_width() + 20, text.get_height() + 10
        x = self.layout.table_center[0] - w // 2
        y = self.layout.deal_hint_y
        self.canvas.overlay((x, y, w, h), (25, 15, 8, 180))
        self.canvas.blit(text, (x + 10, y + 5))

    def __repr__(self) -> str:
        return f"DealAnimation(done={self.done}, cards={len(self.deal_queue)})"