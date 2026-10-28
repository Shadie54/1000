# gui/game_over_screen.py
#
# Koniec hry — výsledky (grafický rework 2026-10-28: ui_style, panel
# FINÁLNE SKÓRE s poradím v medailónoch, tlačidlá v úrovniach).

import sys

import pygame
from gui import display

from gui.canvas import draw_static
from gui import ui_style
from config import SCREEN_WIDTH, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE, WINNING_SCORE

# Vzhľad (grafický rework 2026-10-28, gui/ui_style.py)
LOSS_COLOR = (200, 96, 74)          # nadpis PREHRA — stlmená červená
BORDER_DIM = (98, 76, 46)
TRACK_EMPTY = (52, 40, 26)
RANK_COLORS = ((222, 172, 64), (214, 206, 190), (176, 120, 72))   # zlato, striebro, bronz
PANEL_HEADER = 70                   # nadpis panela + čiara
ROW_H, ROW_GAP, ROW_PAD = 84, 12, 22


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

        self.font_title  = self.canvas.font(84)
        self.font_large  = self.canvas.font(FONT_SIZE_LARGE)       # 32
        self.font_medium = self.canvas.font(FONT_SIZE_MEDIUM)      # 24
        self.font_small  = self.canvas.font(FONT_SIZE_MEDIUM - 4)  # 20

        # Rozloženie: nadpis, panel skóre, info a tlačidlá ako jeden blok
        # zvislo na strede okna
        cx = SCREEN_WIDTH // 2
        panel_h = PANEL_HEADER + 3 * ROW_H + 2 * ROW_GAP + ROW_PAD
        block_h = 170 + panel_h + 70 + 60
        top = (self.H - block_h) // 2
        self.title_cy = top + 40
        self.score_panel = pygame.Rect(cx - 330, top + 170, 660, panel_h)
        btn_w, btn_h = 240, 60
        btn_y = self.score_panel.bottom + 70
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
        # Všetko okrem zvýraznenia tlačidiel (hover) je statické
        draw_static(self, self.canvas, "koniec", self._draw_static)
        self._draw_buttons(mouse_pos)

    def _draw_static(self):
        # Vzhľad: gui/ui_style.py (grafický rework 2026-10-28)
        ui_style.draw_backdrop(self.canvas)
        self._draw_title()
        self._draw_scores()
        self._draw_info()

    def _draw_title(self):
        won = self.winner.is_human
        ui_style.draw_screen_title(
            self.canvas, "VYHRAL SI!" if won else "PREHRA",
            self.font_title, (SCREEN_WIDTH // 2, self.title_cy),
            line_half_w=300, line_gap=62,
            color=ui_style.GOLD if won else LOSS_COLOR)
        sub = self.font_large.render(f"{self.winner.name} vyhral hru!", True,
                                     ui_style.TEXT)
        self.canvas.blit(sub, sub.get_rect(
            center=(SCREEN_WIDTH // 2, self.title_cy + 106)))

    def _draw_scores(self):
        c = self.canvas
        panel = self.score_panel
        ui_style.draw_panel(c, panel, "FINÁLNE SKÓRE", self.font_medium)

        ranked = sorted(self.players, key=lambda p: p.total_score, reverse=True)
        x = panel.x + ROW_PAD
        w = panel.width - 2 * ROW_PAD
        for i, player in enumerate(ranked):
            y = panel.y + PANEL_HEADER + i * (ROW_H + ROW_GAP)
            row = pygame.Rect(x, y, w, ROW_H)
            is_winner = player == self.winner
            c.overlay(row, (64, 46, 20, 210) if is_winner else (24, 17, 11, 200),
                      border_radius=10)
            c.rect(ui_style.GOLD if is_winner else BORDER_DIM, row,
                   width=2, border_radius=10)

            # Poradie v medailóne
            mc = (row.x + 40, row.centery)
            c.circle((14, 10, 6), mc, 24)
            c.circle(RANK_COLORS[i], mc, 24, width=2)
            rank = self.font_medium.render(str(i + 1), True, RANK_COLORS[i])
            c.blit(rank, rank.get_rect(center=mc))

            text_color = ui_style.GOLD if is_winner else ui_style.TEXT
            name = self.font_large.render(player.name, True, text_color)
            c.blit(name, (row.x + 84, row.y + 12))
            score = self.font_large.render(str(player.total_score), True, text_color)
            c.blit(score, score.get_rect(right=row.right - 20, top=row.y + 12))

            # Ukazovateľ k 1000 bodom
            bar = pygame.Rect(row.x + 84, row.bottom - 20, row.width - 84 - 20, 6)
            c.rect(TRACK_EMPTY, bar, border_radius=3)
            ratio = min(max(player.total_score, 0) / WINNING_SCORE, 1.0)
            if int(bar.width * ratio) > 0:
                c.rect(ui_style.GOLD if is_winner else ui_style.GOLD_SOFT,
                       (bar.x, bar.y, int(bar.width * ratio), bar.height),
                       border_radius=3)

    def _draw_info(self):
        surf = self.font_small.render(
            f"Hra trvala {self.round_number} kôl", True, ui_style.TEXT_DIM)
        self.canvas.blit(surf, surf.get_rect(
            center=(SCREEN_WIDTH // 2, self.score_panel.bottom + 34)))
        # Tlačidlá v pokojovom stave patria do statickej vrstvy
        ui_style.draw_button(self.canvas, self.btn_new_game, "Nová hra",
                             self.font_large, 1)
        ui_style.draw_button(self.canvas, self.btn_menu, "Menu",
                             self.font_large, 3)

    def _draw_buttons(self, mouse_pos):
        for rect, label in ((self.btn_new_game, "Nová hra"),
                            (self.btn_menu, "Menu")):
            if rect.collidepoint(mouse_pos):
                c = self.canvas
                c.overlay(rect, (255, 214, 140, 24), border_radius=ui_style.BTN_RADIUS)
                c.rect(ui_style.BTN_BORDER_HOVER, rect, width=2,
                       border_radius=ui_style.BTN_RADIUS)
                surf = self.font_large.render(label, True, ui_style.BTN_TEXT_HOVER)
                c.blit(surf, surf.get_rect(center=rect.center))
