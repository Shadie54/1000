# gui/menu.py

import pygame
import sys
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_WHITE, COLOR_BLACK, COLOR_GOLD, COLOR_GRAY,
    COLOR_BUTTON_PRIMARY, COLOR_BUTTON_SECONDARY,
    FONT_SIZE_LARGE, FONT_SIZE_XLARGE, FONT_SIZE_MEDIUM,
    BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_RADIUS
)


class Menu:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont(None, 96)
        self.font_subtitle = pygame.font.SysFont(None, FONT_SIZE_LARGE)
        self.font_button = pygame.font.SysFont(None, FONT_SIZE_LARGE)

        # Pozadie
        try:
            self.bg = pygame.image.load("assets/graphics/table.jpg").convert()
            self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except FileNotFoundError:
            self.bg = None

        # Logo
        try:
            self.logo = pygame.image.load("assets/graphics/1000.png").convert_alpha()
            self.logo = pygame.transform.scale(self.logo, (200, 200))
        except FileNotFoundError:
            self.logo = None

        # Tlačidlá
        btn_w = 300
        btn_h = 65
        center_x = SCREEN_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 + 50

        self.buttons = [
            {
                "label": "Nová hra",
                "action": "new_game",
                "rect": pygame.Rect(center_x - btn_w // 2, start_y, btn_w, btn_h),
                "color": COLOR_BUTTON_PRIMARY,
                "hover": False
            },
            {
                "label": "Nastavenia",
                "action": "settings",
                "rect": pygame.Rect(center_x - btn_w // 2, start_y + 85, btn_w, btn_h),
                "color": COLOR_BUTTON_SECONDARY,
                "hover": False
            },
            {
                "label": "Koniec",
                "action": "quit",
                "rect": pygame.Rect(center_x - btn_w // 2, start_y + 170, btn_w, btn_h),
                "color": COLOR_BUTTON_SECONDARY,
                "hover": False
            },
        ]

    # ------------------------------------------------------------------
    # Hlavná slučka menu
    # ------------------------------------------------------------------

    def run(self) -> str:
        """
        Zobrazí menu a čaká na výber.
        Vracia akciu: "new_game" / "settings" / "quit"
        """
        while True:
            self.clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        action = self._handle_click(event.pos)
                        if action:
                            return action

            self._update_hover(mouse_pos)
            self._draw()
            pygame.display.flip()

    # ------------------------------------------------------------------
    # Udalosti
    # ------------------------------------------------------------------

    def _handle_click(self, pos: tuple[int, int]) -> str | None:
        """Spracuje klik na tlačidlo."""
        for btn in self.buttons:
            if btn["rect"].collidepoint(pos):
                return btn["action"]
        return None

    def _update_hover(self, mouse_pos: tuple[int, int]):
        """Aktualizuje hover stav tlačidiel."""
        for btn in self.buttons:
            btn["hover"] = btn["rect"].collidepoint(mouse_pos)

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def _draw(self):
        """Nakreslí celé menu."""
        # Pozadie
        if self.bg:
            self.screen.blit(self.bg, (0, 0))
        else:
            self.screen.fill(COLOR_BLACK)

        # Tmavý overlay pre lepšiu čitateľnosť
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        self._draw_logo()
        self._draw_title()
        self._draw_buttons()

    def _draw_logo(self):
        """Nakreslí logo."""
        if self.logo:
            logo_rect = self.logo.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120)
            )
            self.screen.blit(self.logo, logo_rect)

    def _draw_title(self):
        """Nakreslí názov hry."""
        if not self.logo:
            # Ak nie je logo, zobraz textový názov
            title = self.font_title.render("TISÍC", True, COLOR_GOLD)
            title_rect = title.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120)
            )
            self.screen.blit(title, title_rect)

        # Podtitul
        subtitle = self.font_subtitle.render(
            "Kartová hra", True, COLOR_GRAY
        )
        subtitle_rect = subtitle.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10)
        )
        self.screen.blit(subtitle, subtitle_rect)

    def _draw_buttons(self):
        """Nakreslí všetky tlačidlá."""
        for btn in self.buttons:
            self._draw_button(btn)

    def _draw_button(self, btn: dict):
        """Nakreslí jedno tlačidlo s hover efektom."""
        rect = btn["rect"]
        color = btn["color"]

        # Hover efekt — trochu svetlejšie
        if btn["hover"]:
            hover_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            hover_surf.fill((255, 255, 255, 30))
            alpha = 240
        else:
            alpha = 200

        # Pozadie tlačidla
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((*color, alpha))
        self.screen.blit(overlay, (rect.x, rect.y))

        # Okraj
        border_color = COLOR_GOLD if btn["hover"] else COLOR_GRAY
        pygame.draw.rect(
            self.screen, border_color,
            rect, width=2, border_radius=BUTTON_RADIUS
        )

        # Hover highlight
        if btn["hover"]:
            self.screen.blit(hover_surf, (rect.x, rect.y))

        # Text
        text_color = COLOR_GOLD if btn["hover"] else COLOR_WHITE
        text_surf = self.font_button.render(btn["label"], True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def __repr__(self) -> str:
        return "Menu()"