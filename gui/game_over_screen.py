# gui/game_over_screen.py

import sys

import pygame
from gui import display

from gui.canvas import draw_backdrop, draw_static
from config import (
    SCREEN_WIDTH,
    COLOR_WHITE, COLOR_GOLD, COLOR_GRAY,
    COLOR_RED,
    COLOR_BUTTON_PRIMARY, COLOR_BUTTON_SECONDARY,
    FONT_SIZE_MEDIUM, FONT_SIZE_LARGE, BUTTON_RADIUS, WINNING_SCORE
)


class GameOverScreen:
    def __init__(self, screen: pygame.Surface, players: list,
                 winner, round_number: int):
        # `screen` (logický povrch) sa už nepoužíva — kreslí sa cez Canvas.
        self.canvas = display.canvas()
        self.H = display.logical_height()
        self.players = players
        self.winner = winner
        self.round_number = round_number
        self.clock = pygame.time.Clock()

        self.font_title  = self.canvas.font(96)
        self.font_large  = self.canvas.font(FONT_SIZE_LARGE)       # 32
        self.font_medium = self.canvas.font(FONT_SIZE_MEDIUM)      # 24
        self.font_small  = self.canvas.font(FONT_SIZE_MEDIUM - 4)  # 20

        # Tlačidlá
        btn_w, btn_h = 240, 60
        cx = SCREEN_WIDTH // 2
        btn_y = self.H - 120
        self.btn_new_game = pygame.Rect(cx - btn_w - 20, btn_y, btn_w, btn_h)
        self.btn_menu     = pygame.Rect(cx + 20,         btn_y, btn_w, btn_h)

    # ------------------------------------------------------------------
    # Hlavná slučka
    # ------------------------------------------------------------------

    def run(self) -> str:
        while True:
            self.clock.tick(60)
            mouse_pos = display.mouse_pos()

            for event in display.get_events():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.btn_new_game.collidepoint(event.pos):
                        return "new_game"
                    if self.btn_menu.collidepoint(event.pos):
                        return "menu"

            self._draw(mouse_pos)
            display.present()

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def _draw(self, mouse_pos):
        # Všetko okrem tlačidiel (hover) je statické — kreslí sa raz
        draw_static(self, self.canvas, "koniec", self._draw_static)
        self._draw_buttons(mouse_pos)

    def _draw_static(self):
        # Pozadie
        draw_backdrop(self.canvas, (0, 0, 0, 170))
        self._draw_title()
        self._draw_scores()
        self._draw_info()

    def _draw_title(self):
        is_human_winner = self.winner.is_human
        title_text  = "VYHRAL SI!" if is_human_winner else "PREHRA!"
        title_color = COLOR_GOLD   if is_human_winner else COLOR_RED

        # Hlavný nadpis
        title = self.font_title.render(title_text, True, title_color)
        self.canvas.blit(title, title.get_rect(
            center=(SCREEN_WIDTH // 2, 110)
        ))

        # Meno víťaza
        sub = self.font_large.render(
            f"{self.winner.name} vyhral hru!", True, COLOR_WHITE
        )
        self.canvas.blit(sub, sub.get_rect(
            center=(SCREEN_WIDTH // 2, 185)
        ))

        # Čiara
        self.canvas.line(
            COLOR_GOLD,
            (SCREEN_WIDTH // 2 - 350, 215),
            (SCREEN_WIDTH // 2 + 350, 215),
            width=1
        )

    def _draw_scores(self):
        # Nadpis sekcie
        title = self.font_medium.render("FINÁLNE SKÓRE", True, COLOR_GOLD)
        self.canvas.blit(title, title.get_rect(
            center=(SCREEN_WIDTH // 2, 245)
        ))

        sorted_players = sorted(
            self.players, key=lambda p: p.total_score, reverse=True
        )

        panel_w = 560
        panel_x = SCREEN_WIDTH // 2 - panel_w // 2
        row_h   = 80
        start_y = 280

        for i, player in enumerate(sorted_players):
            y         = start_y + i * (row_h + 12)
            is_winner = player == self.winner

            # Panel pozadie
            self.canvas.overlay((panel_x, y, panel_w, row_h),
                                (212, 160, 40, 60) if is_winner else (20, 12, 5, 180))

            # Okraj
            self.canvas.rect(
                COLOR_GOLD if is_winner else COLOR_GRAY,
                (panel_x, y, panel_w, row_h),
                width=2, border_radius=10
            )

            # Poradie — veľké, vľavo
            rank_colors = [COLOR_GOLD, COLOR_WHITE, COLOR_GRAY]
            rank_surf = self.font_large.render(f"#{i+1}", True, rank_colors[i])
            self.canvas.blit(rank_surf, (panel_x + 18, y + row_h // 2 - rank_surf.get_height() // 2))

            # Meno
            name_color = COLOR_GOLD if is_winner else COLOR_WHITE
            name_surf  = self.font_large.render(player.name, True, name_color)
            self.canvas.blit(name_surf, (panel_x + 80, y + 10))

            # Skóre — vpravo
            score_surf = self.font_large.render(str(player.total_score), True, name_color)
            self.canvas.blit(score_surf, score_surf.get_rect(
                right=panel_x + panel_w - 18,
                top=y + 10
            ))

            # Progress bar — pod menom a skóre
            bar_x = panel_x + 80
            bar_w = panel_w - 80 - 18
            bar_y = y + row_h - 16
            bar_h = 6

            self.canvas.rect((60, 45, 30),
                             (bar_x, bar_y, bar_w, bar_h), border_radius=3)

            ratio   = min(max(player.total_score, 0) / WINNING_SCORE, 1.0)
            fill_w  = int(bar_w * ratio)
            if fill_w > 0:
                color = COLOR_GOLD if is_winner else COLOR_GRAY
                self.canvas.rect(color,
                                 (bar_x, bar_y, fill_w, bar_h), border_radius=3)

    def _draw_info(self):
        surf = self.font_small.render(
            f"Hra trvala {self.round_number} kôl", True, COLOR_GRAY
        )
        self.canvas.blit(surf, surf.get_rect(
            center=(SCREEN_WIDTH // 2, self.H - 160)
        ))

    def _draw_buttons(self, mouse_pos):
        self._draw_btn(self.btn_new_game, "Nová hra",
                       COLOR_BUTTON_PRIMARY,   self.btn_new_game.collidepoint(mouse_pos))
        self._draw_btn(self.btn_menu,     "Menu",
                       COLOR_BUTTON_SECONDARY, self.btn_menu.collidepoint(mouse_pos))

    def _draw_btn(self, rect: pygame.Rect, text: str, color: tuple, hover: bool):
        alpha = 245 if hover else 200
        self.canvas.overlay(rect, (*color, alpha))

        self.canvas.rect(COLOR_WHITE if hover else COLOR_GOLD,
                         rect, width=2, border_radius=BUTTON_RADIUS)

        text_surf = self.font_large.render(text, True, COLOR_WHITE)
        self.canvas.blit(text_surf, text_surf.get_rect(center=rect.center))