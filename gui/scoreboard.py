# gui/scoreboard.py

import pygame
from game.player import Player
from game.round import Round
from config import (
    SCORE_PANEL_X, SCORE_PANEL_Y, SCORE_PANEL_WIDTH, SCORE_PANEL_HEIGHT,
    COLOR_WHITE, COLOR_BLACK, COLOR_YELLOW, COLOR_GREEN, COLOR_RED,
    COLOR_PANEL_BG, COLOR_GRAY, COLOR_GOLD,
    FONT_SIZE_SMALL, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE,
    WINNING_SCORE
)


class Scoreboard:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_small = pygame.font.SysFont(None, FONT_SIZE_SMALL)
        self.font_medium = pygame.font.SysFont(None, FONT_SIZE_MEDIUM)
        self.font_large = pygame.font.SysFont(None, FONT_SIZE_LARGE)

    # ------------------------------------------------------------------
    # Hlavná metóda kreslenia
    # ------------------------------------------------------------------

    def draw(self, players: list[Player], current_round: Round | None):
        """Nakreslí scoresheet panel."""
        self._draw_background()
        self._draw_header()
        self._draw_player_scores(players, current_round)
        self._draw_round_info(players, current_round)

    # ------------------------------------------------------------------
    # Pozadie a hlavička
    # ------------------------------------------------------------------

    def _draw_background(self):
        """Nakreslí pozadie panelu."""
        panel_rect = pygame.Rect(
            SCORE_PANEL_X, SCORE_PANEL_Y,
            SCORE_PANEL_WIDTH, SCORE_PANEL_HEIGHT
        )
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_GOLD, panel_rect, width=2, border_radius=10)

    def _draw_header(self):
        """Nakreslí hlavičku panelu."""
        title = self.font_medium.render("SKÓRE", True, COLOR_GOLD)
        self.screen.blit(title, (SCORE_PANEL_X + 10, SCORE_PANEL_Y + 10))

        # Oddeľovacia čiara
        pygame.draw.line(
            self.screen, COLOR_GOLD,
            (SCORE_PANEL_X + 10, SCORE_PANEL_Y + 35),
            (SCORE_PANEL_X + SCORE_PANEL_WIDTH - 10, SCORE_PANEL_Y + 35),
            width=1
        )

    # ------------------------------------------------------------------
    # Skóre hráčov
    # ------------------------------------------------------------------

    def _draw_player_scores(self, players: list[Player], current_round: Round | None):
        """Nakreslí skóre každého hráča."""
        y_start = SCORE_PANEL_Y + 45

        for i, player in enumerate(players):
            y = y_start + i * 45

            # Zvýraznenie aktívneho hráča
            is_current = (
                current_round and
                current_round.get_current_player_index() == i
            )
            name_color = COLOR_YELLOW if is_current else COLOR_WHITE

            # Zvýraznenie hráča s povinnosťou
            is_obligation = (
                current_round and
                current_round.obligation_index == i
            )

            # Meno hráča
            name_text = f"{'► ' if is_current else '  '}{player.name}"
            if is_obligation:
                name_text += " (P)"
            name_surf = self.font_medium.render(name_text, True, name_color)
            self.screen.blit(name_surf, (SCORE_PANEL_X + 10, y))

            # Celkové skóre
            score_color = self._score_color(player.total_score)
            score_surf = self.font_medium.render(
                str(player.total_score), True, score_color
            )
            score_rect = score_surf.get_rect(
                right=SCORE_PANEL_X + SCORE_PANEL_WIDTH - 10,
                top=y
            )
            self.screen.blit(score_surf, score_rect)

            # Progress bar k 1000
            self._draw_progress_bar(
                x=SCORE_PANEL_X + 10,
                y=y + 22,
                width=SCORE_PANEL_WIDTH - 20,
                height=8,
                value=player.total_score,
                max_value=WINNING_SCORE
            )

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
        """Nakreslí progress bar skóre."""
        # Pozadie
        pygame.draw.rect(
            self.screen, COLOR_GRAY,
            (x, y, width, height),
            border_radius=4
        )

        # Výplň
        fill_ratio = max(0, min(value / max_value, 1.0))
        fill_width = int(width * fill_ratio)

        if fill_width > 0:
            if value < 0:
                color = COLOR_RED
            elif value >= 800:
                color = COLOR_GREEN
            else:
                color = COLOR_GOLD

            pygame.draw.rect(
                self.screen, color,
                (x, y, fill_width, height),
                border_radius=4
            )

        # Okraj
        pygame.draw.rect(
            self.screen, COLOR_WHITE,
            (x, y, width, height),
            width=1, border_radius=4
        )

    # ------------------------------------------------------------------
    # Info o aktuálnom kole
    # ------------------------------------------------------------------

    def _draw_round_info(self, players: list[Player], current_round: Round | None):
        """Nakreslí info o aktuálnom kole pod scoresheet."""
        if not current_round:
            return

        info_y = SCORE_PANEL_Y + SCORE_PANEL_HEIGHT + 10
        panel_rect = pygame.Rect(
            SCORE_PANEL_X, info_y,
            SCORE_PANEL_WIDTH, 130
        )
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_GOLD, panel_rect, width=2, border_radius=10)

        lines = []

        # Fáza hry
        phase_labels = {
            "dealing": "Rozdávanie",
            "bidding": "Dražba",
            "talon": "Talon",
            "tricks": "Štichy",
            "scoring": "Bodovanie",
            "done": "Koniec kola"
        }
        phase_text = phase_labels.get(current_round.phase, current_round.phase)
        lines.append(("Fáza:", phase_text, COLOR_WHITE))

        # Dražba
        if current_round.bidding:
            winner = current_round.bidding.winner
            bid_val = str(current_round.bidding.current_bid)
            lines.append(("Záväzok:", f"{winner.name} / {bid_val}", COLOR_YELLOW))

        # Tromf
        if current_round.trump_suit:
            trump_labels = {
                "heart": "Srdce ♥",
                "bell": "Zvon ●",
                "leaf": "Zeleň ♣",
                "acorn": "Žaluď ♠"
            }
            trump_text = trump_labels.get(current_round.trump_suit, current_round.trump_suit)
            lines.append(("Tromf:", trump_text, COLOR_GOLD))
        else:
            lines.append(("Tromf:", "—", COLOR_GRAY))

        # Číslo štichu
        if current_round.phase == "tricks":
            lines.append(("Štich:", f"{current_round.trick_number + 1} / 10", COLOR_WHITE))

        # Kreslenie riadkov
        for j, (label, value, color) in enumerate(lines):
            y = info_y + 10 + j * 27
            label_surf = self.font_small.render(label, True, COLOR_GRAY)
            value_surf = self.font_small.render(value, True, color)
            self.screen.blit(label_surf, (SCORE_PANEL_X + 10, y))
            value_rect = value_surf.get_rect(
                right=SCORE_PANEL_X + SCORE_PANEL_WIDTH - 10,
                top=y
            )
            self.screen.blit(value_surf, value_rect)

    def __repr__(self) -> str:
        return "Scoreboard()"