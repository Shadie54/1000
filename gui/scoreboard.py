# gui/scoreboard.py

import pygame
import os
from game.player import Player
from game.round import Round
from config import (
    SCORE_PANEL_X, SCORE_PANEL_Y, SCORE_PANEL_WIDTH, SCORE_PANEL_HEIGHT,
    COLOR_WHITE, COLOR_BLACK, COLOR_YELLOW, COLOR_GREEN, COLOR_RED,
    COLOR_PANEL_BG, COLOR_GRAY, COLOR_GOLD,
    FONT_SIZE_SMALL, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE,
    WINNING_SCORE, SUIT_ICONS_PATH,
    INFO_PANEL_X, INFO_PANEL_Y, INFO_PANEL_WIDTH, INFO_PANEL_HEIGHT, FONT_SIZE_INFO
)


class Scoreboard:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_small = pygame.font.SysFont(None, FONT_SIZE_SMALL)
        self.font_medium = pygame.font.SysFont(None, FONT_SIZE_MEDIUM)
        self.font_large = pygame.font.SysFont(None, FONT_SIZE_LARGE)
        self.font_info = pygame.font.SysFont(None, FONT_SIZE_INFO)
        self._icon_cache: dict[str, pygame.Surface] = {}

    # ------------------------------------------------------------------
    # Načítanie ikoniek
    # ------------------------------------------------------------------

    def _load_suit_icon(self, suit: str, size: str = "medium") -> pygame.Surface | None:
        """Načíta ikonku farby zo súboru."""
        key = f"{suit}-{size}"
        if key not in self._icon_cache:
            path = os.path.join(SUIT_ICONS_PATH, f"{suit}-icon@{size}.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                # Zmenšíme na rozumný rozmer pre tabuľku
                img = pygame.transform.scale(img, (24, 24))
                self._icon_cache[key] = img
            except FileNotFoundError:
                self._icon_cache[key] = None
        return self._icon_cache[key]

    # ------------------------------------------------------------------
    # Hlavná metóda kreslenia
    # ------------------------------------------------------------------

    def draw(self, players: list[Player], current_round: Round | None):
        """Nakreslí oba panely."""
        self._draw_score_panel(players, current_round)
        self._draw_info_panel(players, current_round)

    # ------------------------------------------------------------------
    # Ľavý panel — skóre hráčov
    # ------------------------------------------------------------------

    def _draw_score_panel(self, players: list[Player], current_round: Round | None):
        """Nakreslí scoresheet panel."""
        self._draw_panel_bg(
            SCORE_PANEL_X, SCORE_PANEL_Y,
            SCORE_PANEL_WIDTH, SCORE_PANEL_HEIGHT
        )

        # Hlavička
        title = self.font_medium.render("SKÓRE", True, COLOR_GOLD)
        self.screen.blit(title, (SCORE_PANEL_X + 10, SCORE_PANEL_Y + 10))
        self._draw_divider(SCORE_PANEL_Y + 35)

        # Skóre hráčov
        y_start = SCORE_PANEL_Y + 45
        for i, player in enumerate(players):
            y = y_start + i * 45
            is_current = (
                current_round and
                current_round.get_current_player_index() == i
            )
            is_obligation = (
                current_round and
                current_round.obligation_index == i
            )
            name_color = COLOR_YELLOW if is_current else COLOR_WHITE
            name_text = f"{'► ' if is_current else '  '}{player.name}"
            if is_obligation:
                name_text += " (P)"

            name_surf = self.font_medium.render(name_text, True, name_color)
            self.screen.blit(name_surf, (SCORE_PANEL_X + 10, y))

            score_color = self._score_color(player.total_score)
            score_surf = self.font_medium.render(str(player.total_score), True, score_color)
            score_rect = score_surf.get_rect(
                right=SCORE_PANEL_X + SCORE_PANEL_WIDTH - 10,
                top=y
            )
            self.screen.blit(score_surf, score_rect)

            self._draw_progress_bar(
                x=SCORE_PANEL_X + 10,
                y=y + 22,
                width=SCORE_PANEL_WIDTH - 20,
                height=8,
                value=player.total_score,
                max_value=WINNING_SCORE
            )

    # ------------------------------------------------------------------
    # Pravý panel — info o kole
    # ------------------------------------------------------------------

    def _draw_info_panel(self, players: list[Player], current_round: Round | None):
        """Nakreslí info panel s fázou, záväzkom, bodmi a tromfom."""
        if not current_round:
            return

        # Vypočítame výšku panelu dynamicky
        panel_height = 200
        self._draw_panel_bg(
            INFO_PANEL_X, INFO_PANEL_Y,
            INFO_PANEL_WIDTH, panel_height
        )

        # Hlavička
        title = self.font_medium.render("KOLO", True, COLOR_GOLD)
        self.screen.blit(title, (INFO_PANEL_X + 10, INFO_PANEL_Y + 10))
        self._draw_divider_right(INFO_PANEL_Y + 35)

        y = INFO_PANEL_Y + 45
        line_h = 30

        # Fáza
        phase_labels = {
            "dealing": "Rozdávanie",
            "bidding": "Dražba",
            "talon": "Talon",
            "tricks": "Štychy",
            "scoring": "Bodovanie",
            "done": "Koniec kola"
        }
        phase_text = phase_labels.get(current_round.phase, current_round.phase)
        self._draw_info_row("Fáza:", phase_text, y, COLOR_WHITE)
        y += line_h

        # Záväzok
        if current_round.bidding:
            winner = current_round.bidding.winner
            bid_val = str(current_round.bidding.current_bid)
            self._draw_info_row("Povinnosť:", f"{winner.name} / {bid_val}", y, COLOR_YELLOW)
            y += line_h

            # Body zatiaľ — progress bar záväzku (len pre dražiteľa)
            if current_round.phase == "tricks":
                self._draw_bid_progress(
                    players, current_round, y
                )
                y += line_h + 8

        # Štich
        if current_round.phase == "tricks":
            self._draw_info_row(
                "Štych:",
                f"{current_round.trick_number + 1} / 10",
                y, COLOR_WHITE
            )
            y += line_h

        # Tromf s ikonkou
        self._draw_trump_row(current_round.trump_suit, y)

    def _draw_bid_progress(self, players: list[Player],
                           current_round: Round, y: int):
        """Nakreslí progress bar bodov dražiteľa voči záväzku."""
        bidder = current_round.bidding.winner
        current_points = bidder.round_points
        bid = bidder.bid

        label = self.font_info.render("Body zatiaľ:", True, COLOR_GRAY)
        self.screen.blit(label, (INFO_PANEL_X + 10, y))

        points_text = f"{current_points} / {bid}"
        color = COLOR_GREEN if current_points >= bid else COLOR_YELLOW
        points_surf = self.font_info.render(points_text, True, color)
        points_rect = points_surf.get_rect(
            right=INFO_PANEL_X + INFO_PANEL_WIDTH - 10,
            top=y
        )
        self.screen.blit(points_surf, points_rect)

        # Progress bar
        self._draw_progress_bar(
            x=INFO_PANEL_X + 10,
            y=y + 18,
            width=INFO_PANEL_WIDTH - 20,
            height=8,
            value=current_points,
            max_value=bid
        )

    def _draw_trump_row(self, trump_suit: str | None, y: int):
        """Nakreslí riadok tromfu s ikonkou."""
        label_surf = self.font_info.render("Tromf:", True, COLOR_GRAY)
        self.screen.blit(label_surf, (INFO_PANEL_X + 10, y))

        if trump_suit:
            # Ikonka farby
            icon = self._load_suit_icon(trump_suit, "medium")
            if icon:
                self.screen.blit(icon, (INFO_PANEL_X + INFO_PANEL_WIDTH - 80, y - 2))

            # Slovenský názov farby
            trump_labels = {
                "heart": "Srdce",
                "bell": "Guľa",
                "leaf": "Zeleň",
                "acorn": "Žaluď"
            }
            label = trump_labels.get(trump_suit, trump_suit)
            value_surf = self.font_info.render(label, True, COLOR_GOLD)
            value_rect = value_surf.get_rect(
                right=INFO_PANEL_X + INFO_PANEL_WIDTH - 90,
                top=y
            )
            self.screen.blit(value_surf, value_rect)
        else:
            none_surf = self.font_info.render("???", True, COLOR_GRAY)
            none_rect = none_surf.get_rect(
                right=INFO_PANEL_X + INFO_PANEL_WIDTH - 10,
                top=y
            )
            self.screen.blit(none_surf, none_rect)

    # ------------------------------------------------------------------
    # Pomocné metódy kreslenia
    # ------------------------------------------------------------------

    def _draw_panel_bg(self, x: int, y: int, w: int, h: int):
        """Nakreslí polopriehľadné pozadie panelu."""
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((25, 15, 8, 210))  # tmavá hnedá, 82% nepriehľadná
        self.screen.blit(overlay, (x, y))
        # Zlatý okraj
        pygame.draw.rect(
            self.screen, COLOR_GOLD,
            (x, y, w, h),
            width=2, border_radius=10
        )

    def _draw_divider(self, y: int):
        """Nakreslí oddeľovaciu čiaru v ľavom paneli."""
        pygame.draw.line(
            self.screen, COLOR_GOLD,
            (SCORE_PANEL_X + 10, y),
            (SCORE_PANEL_X + SCORE_PANEL_WIDTH - 10, y),
            width=1
        )

    def _draw_divider_right(self, y: int):
        """Nakreslí oddeľovaciu čiaru v pravom paneli."""
        pygame.draw.line(
            self.screen, COLOR_GOLD,
            (INFO_PANEL_X + 10, y),
            (INFO_PANEL_X + INFO_PANEL_WIDTH - 10, y),
            width=1
        )

    def _draw_info_row(self, label: str, value: str, y: int, color: tuple):
        """Nakreslí jeden riadok label: value."""
        label_surf = self.font_info.render(label, True, COLOR_GRAY)
        value_surf = self.font_info.render(value, True, color)
        self.screen.blit(label_surf, (INFO_PANEL_X + 10, y))
        value_rect = value_surf.get_rect(
            right=INFO_PANEL_X + INFO_PANEL_WIDTH - 10,
            top=y
        )
        self.screen.blit(value_surf, value_rect)

    def _score_color(self, score: int) -> tuple:
        """Vráti farbu skóre podľa hodnoty."""
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
        pygame.draw.rect(self.screen, COLOR_GRAY, (x, y, width, height), border_radius=4)

        fill_ratio = max(0, min(value / max_value, 1.0)) if max_value > 0 else 0
        fill_width = int(width * fill_ratio)

        if fill_width > 0:
            if value < 0:
                color = COLOR_RED
            elif value >= max_value:
                color = COLOR_GREEN
            else:
                color = COLOR_GOLD
            pygame.draw.rect(self.screen, color, (x, y, fill_width, height), border_radius=4)

        pygame.draw.rect(self.screen, COLOR_WHITE, (x, y, width, height), width=1, border_radius=4)

    def __repr__(self) -> str:
        return "Scoreboard()"