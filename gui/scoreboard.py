# gui/scoreboard.py

import pygame
import os
from game.player import Player
from game.round import Round
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_WHITE, COLOR_BLACK, COLOR_YELLOW, COLOR_GREEN, COLOR_RED,
    COLOR_PANEL_BG, COLOR_GRAY, COLOR_GOLD,
    FONT_SIZE_SMALL, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE,
    WINNING_SCORE, SUIT_ICONS_PATH, get_font
)


class Scoreboard:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_small = get_font(18)
        self.font_medium = get_font(24)
        self.font_large = get_font(32)
        self._icon_cache: dict[str, pygame.Surface] = {}

        # Rozmery panelov
        self.panel_h = 220
        self.trump_w = 160
        self.score_w = 280
        self.info_w = 260
        self.padding = 10
        self.panel_y = 15

        # Celková šírka — vycentrovaná
        total_w = self.trump_w + self.score_w + self.info_w + self.padding * 2
        self.start_x = SCREEN_WIDTH // 2 - total_w // 2

        # X pozície jednotlivých panelov
        self.trump_x = self.start_x
        self.score_x = self.start_x + self.trump_w + self.padding
        self.info_x = self.start_x + self.trump_w + self.score_w + self.padding * 2

    # ------------------------------------------------------------------
    # Načítanie ikoniek
    # ------------------------------------------------------------------

    def _load_suit_icon(self, suit: str, size: int = 80) -> pygame.Surface | None:
        """Načíta ikonku farby."""
        key = f"{suit}-{size}"
        if key not in self._icon_cache:
            path = os.path.join(SUIT_ICONS_PATH, f"{suit}-icon@medium.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (size, size))
                self._icon_cache[key] = img
            except FileNotFoundError:
                self._icon_cache[key] = None
        return self._icon_cache[key]

    # ------------------------------------------------------------------
    # Hlavná metóda kreslenia
    # ------------------------------------------------------------------

    def draw(self, players: list[Player], current_round: Round | None):
        """Nakreslí všetky 3 panely."""
        self._draw_trump_panel(current_round)
        self._draw_score_panel(players, current_round)
        self._draw_info_panel(players, current_round)

    # ------------------------------------------------------------------
    # Panel 1 — TROMF
    # ------------------------------------------------------------------

    def _draw_trump_panel(self, current_round: Round | None):
        """Nakreslí panel tromfu."""
        self._draw_panel_bg(self.trump_x, self.panel_y, self.trump_w, self.panel_h)

        # Nadpis
        self._draw_panel_title("TROMF", self.trump_x, self.panel_y, self.trump_w)

        if not current_round or not current_round.trump_suit:
            return

        trump_suit = current_round.trump_suit
        cx = self.trump_x + self.trump_w // 2

        # Ikonka tromfu — medium veľkosť (80x80)
        icon = self._load_suit_icon(trump_suit, 80)
        if icon:
            icon_rect = icon.get_rect(centerx=cx, top=self.panel_y + 45)
            self.screen.blit(icon, icon_rect)

        # Slovenský názov + body
        trump_labels = {
            "heart": "Srdce",
            "bell": "Guľa",
            "leaf": "Zeleň",
            "acorn": "Žaluď"
        }
        trump_points = {
            "heart": 40, "bell": 60,
            "leaf": 80, "acorn": 100
        }

        label = trump_labels.get(trump_suit, trump_suit)
        points = trump_points.get(trump_suit, 0)

        label_surf = self.font_medium.render(label, True, COLOR_GOLD)
        label_rect = label_surf.get_rect(centerx=cx, top=self.panel_y + 135)
        self.screen.blit(label_surf, label_rect)

        points_surf = self.font_small.render(f"{points} bodov", True, COLOR_WHITE)
        points_rect = points_surf.get_rect(centerx=cx, top=self.panel_y + 158)
        self.screen.blit(points_surf, points_rect)

        # Kto zahlásil
        if current_round and hasattr(current_round, 'trump_declarer'):
            declarer = current_round.trump_declarer
            if declarer:
                decl_surf = self.font_small.render(declarer, True, COLOR_GRAY)
                decl_rect = decl_surf.get_rect(centerx=cx, top=self.panel_y + 178)
                self.screen.blit(decl_surf, decl_rect)

    # ------------------------------------------------------------------
    # Panel 2 — SKÓRE
    # ------------------------------------------------------------------

    def _draw_score_panel(self, players: list[Player], current_round: Round | None):
        """Nakreslí panel skóre."""
        self._draw_panel_bg(self.score_x, self.panel_y, self.score_w, self.panel_h)
        self._draw_panel_title("SKÓRE", self.score_x, self.panel_y, self.score_w)

        y_start = self.panel_y + 45

        for i, player in enumerate(players):
            y = y_start + i * 58

            is_current = (
                    current_round and (
                current_round.bidding.get_next_bidder(
                    current_round.bidding.highest_bidder_index
                ) == i
                if current_round.phase == "bidding"
                else current_round.get_current_player_index() == i
            )
            )
            is_obligation = (
                    current_round and (
                current_round.obligation_index == i
                if current_round.phase not in ("bidding", "talon", "tricks")
                else current_round.bidding.highest_bidder_index == i
            )
            )

            name_color = COLOR_YELLOW if is_current else COLOR_WHITE
            indicator = "► " if is_current else "  "
            obligation = f" (P{current_round.bidding.current_bid})" if is_obligation else ""
            name_text = f"{indicator}{player.name}{obligation}"

            name_surf = self.font_medium.render(name_text, True, name_color)
            self.screen.blit(name_surf, (self.score_x + 10, y))

            score_color = self._score_color(player.total_score)
            score_surf = self.font_medium.render(str(player.total_score), True, score_color)
            score_rect = score_surf.get_rect(
                right=self.score_x + self.score_w - 10,
                top=y
            )
            self.screen.blit(score_surf, score_rect)

            self._draw_progress_bar(
                x=self.score_x + 10,
                y=y + 36,
                width=self.score_w - 20,
                height=10,
                value=player.total_score,
                max_value=WINNING_SCORE
            )

    # ------------------------------------------------------------------
    # Panel 3 — KOLO
    # ------------------------------------------------------------------

    def _draw_info_panel(self, players: list[Player], current_round: Round | None):
        """Nakreslí panel info o kole."""
        self._draw_panel_bg(self.info_x, self.panel_y, self.info_w, self.panel_h)
        self._draw_panel_title("KOLO", self.info_x, self.panel_y, self.info_w)

        if not current_round:
            return

        y = self.panel_y + 45
        line_h = 28

        # Fáza
        phase_labels = {
            "dealing": "Rozdávanie",
            "bidding": "Dražba",
            "talon": "Talon",
            "tricks": "Štichy",
            "scoring": "Bodovanie",
            "done": "Koniec kola"
        }
        phase_text = phase_labels.get(current_round.phase, current_round.phase)
        self._draw_info_row("Fáza:", phase_text, y, COLOR_WHITE)
        y += line_h

        # štich
        if current_round.phase == "tricks":
            self._draw_info_row(
                "Štich:",
                f"{current_round.trick_number + 1} / 10",
                y, COLOR_WHITE
            )
            y += line_h

        # Povinnosť
        if current_round.bidding:
            winner = current_round.bidding.winner
            bid_val = str(current_round.bidding.current_bid)
            self._draw_info_row(
                "Povinnosť:",
                f"{winner.name} / {bid_val}",
                y, COLOR_YELLOW
            )
            y += line_h

            # Body zatiaľ
            if current_round.phase == "tricks":
                self._draw_bid_progress(current_round, y)
                y += line_h + 8

    def _draw_bid_progress(self, current_round: Round, y: int):
        """Nakreslí progress bodov dražiteľa."""
        bidder = current_round.bidding.winner
        current_points = bidder.round_points
        bid = bidder.bid

        label = self.font_small.render("Body zatiaľ:", True, COLOR_GRAY)
        self.screen.blit(label, (self.info_x + 10, y))

        color = COLOR_GREEN if current_points >= bid else COLOR_YELLOW
        points_surf = self.font_small.render(
            f"{current_points} / {bid}", True, color
        )
        points_rect = points_surf.get_rect(
            right=self.info_x + self.info_w - 10,
            top=y
        )
        self.screen.blit(points_surf, points_rect)

        self._draw_progress_bar(
            x=self.info_x + 10,
            y=y + 30,
            width=self.info_w - 20,
            height=10,
            value=current_points,
            max_value=bid
        )

    # ------------------------------------------------------------------
    # Pomocné metódy
    # ------------------------------------------------------------------

    def _draw_panel_bg(self, x: int, y: int, w: int, h: int):
        """Nakreslí pozadie panelu."""
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((20, 12, 5, 210))
        self.screen.blit(overlay, (x, y))
        pygame.draw.rect(
            self.screen, COLOR_GOLD,
            (x, y, w, h), width=2, border_radius=10
        )

    def _draw_panel_title(self, title: str, x: int, y: int, w: int):
        """Nakreslí nadpis panelu."""
        surf = self.font_medium.render(title, True, COLOR_GOLD)
        rect = surf.get_rect(centerx=x + w // 2, top=y + 8)
        self.screen.blit(surf, rect)

        pygame.draw.line(
            self.screen, COLOR_GOLD,
            (x + 10, y + 38),
            (x + w - 10, y + 38),
            width=1
        )

    def _draw_info_row(self, label: str, value: str, y: int, color: tuple):
        """Nakreslí jeden riadok label: value."""
        label_surf = self.font_small.render(label, True, COLOR_GRAY)
        value_surf = self.font_small.render(value, True, color)
        self.screen.blit(label_surf, (self.info_x + 10, y))
        value_rect = value_surf.get_rect(
            right=self.info_x + self.info_w - 10,
            top=y
        )
        self.screen.blit(value_surf, value_rect)

    def _score_color(self, score: int) -> tuple:
        """Vráti farbu skóre."""
        if score < 0:
            return COLOR_RED
        if score >= WINNING_SCORE:
            return COLOR_GOLD
        if score >= 800:
            return COLOR_GREEN
        return COLOR_WHITE

    def _draw_progress_bar(self, x: int, y: int, width: int, height: int,
                           value: int, max_value: int):
        """Nakreslí progress bar."""
        pygame.draw.rect(
            self.screen, COLOR_GRAY,
            (x, y, width, height), border_radius=4
        )

        fill_ratio = max(0, min(value / max_value, 1.0)) if max_value > 0 else 0
        fill_width = int(width * fill_ratio)

        if fill_width > 0:
            if value < 0:
                color = COLOR_RED
            elif value >= max_value:
                color = COLOR_GREEN
            else:
                color = COLOR_GOLD
            pygame.draw.rect(
                self.screen, color,
                (x, y, fill_width, height), border_radius=4
            )

        pygame.draw.rect(
            self.screen, COLOR_WHITE,
            (x, y, width, height), width=1, border_radius=4
        )

    def __repr__(self) -> str:
        return "Scoreboard()"