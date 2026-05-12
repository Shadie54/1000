# gui/settings_screen.py

import pygame
import sys
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_WHITE, COLOR_BLACK, COLOR_GOLD, COLOR_GRAY,
    COLOR_BUTTON_PRIMARY, COLOR_BUTTON_SECONDARY,
    COLOR_GREEN, COLOR_YELLOW, COLOR_RED,
    FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_XLARGE,
    BUTTON_RADIUS, get_font
)


class SettingsScreen:
    def __init__(self, screen: pygame.Surface, settings: dict):
        """
        settings: slovník s aktuálnymi nastaveniami
        {
            "ai1_difficulty": "hard",
            "ai2_difficulty": "hard"
        }
        """
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.settings = settings.copy()

        self.font_title = get_font(72)
        self.font_large = get_font(FONT_SIZE_LARGE)
        self.font_medium = get_font(FONT_SIZE_MEDIUM)

        # Pozadie
        try:
            self.bg = pygame.image.load("assets/graphics/table.jpg").convert()
            self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except FileNotFoundError:
            self.bg = None

        # Difficulty options
        self.difficulties = ["easy", "medium", "hard"]
        self.difficulty_labels = {
            "easy": "Ľahká",
            "medium": "Stredná",
            "hard": "Ťažká"
        }
        self.difficulty_colors = {
            "easy": COLOR_GREEN,
            "medium": COLOR_YELLOW,
            "hard": COLOR_RED
        }

        # Tlačidlá obtiažnosti
        btn_w = 160
        btn_h = 55
        center_x = SCREEN_WIDTH // 2
        row1_y = SCREEN_HEIGHT // 2 - 80
        row2_y = SCREEN_HEIGHT // 2 + 80

        self.ai1_buttons = []
        self.ai2_buttons = []

        for i, diff in enumerate(self.difficulties):
            x = center_x - 250 + i * 200
            self.ai1_buttons.append({
                "difficulty": diff,
                "rect": pygame.Rect(x - btn_w // 2, row1_y, btn_w, btn_h),
                "hover": False
            })
            self.ai2_buttons.append({
                "difficulty": diff,
                "rect": pygame.Rect(x - btn_w // 2, row2_y, btn_w, btn_h),
                "hover": False
            })

        # Tlačidlo späť
        self.back_button = {
            "rect": pygame.Rect(center_x - 150, SCREEN_HEIGHT - 120, 300, 60),
            "hover": False
        }

    # ------------------------------------------------------------------
    # Hlavná slučka
    # ------------------------------------------------------------------

    def run(self) -> dict:
        """
        Zobrazí nastavenia a čaká na potvrdenie.
        Vracia aktualizovaný settings slovník.
        """
        while True:
            self.clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return self.settings

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        result = self._handle_click(event.pos)
                        if result == "back":
                            return self.settings

            self._update_hover(mouse_pos)
            self._draw()
            pygame.display.flip()

    # ------------------------------------------------------------------
    # Udalosti
    # ------------------------------------------------------------------

    def _handle_click(self, pos: tuple[int, int]) -> str | None:
        """Spracuje klik."""
        # AI 1 tlačidlá
        for btn in self.ai1_buttons:
            if btn["rect"].collidepoint(pos):
                self.settings["ai1_difficulty"] = btn["difficulty"]
                return None

        # AI 2 tlačidlá
        for btn in self.ai2_buttons:
            if btn["rect"].collidepoint(pos):
                self.settings["ai2_difficulty"] = btn["difficulty"]
                return None

        # Späť
        if self.back_button["rect"].collidepoint(pos):
            return "back"

        return None

    def _update_hover(self, mouse_pos: tuple[int, int]):
        """Aktualizuje hover stav."""
        for btn in self.ai1_buttons + self.ai2_buttons:
            btn["hover"] = btn["rect"].collidepoint(mouse_pos)
        self.back_button["hover"] = self.back_button["rect"].collidepoint(mouse_pos)

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def _draw(self):
        """Nakreslí obrazovku nastavení."""
        if self.bg:
            self.screen.blit(self.bg, (0, 0))
        else:
            self.screen.fill((45, 28, 15))

        # Tmavý overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        self._draw_title()
        self._draw_ai_section(
            "Počítač 1",
            self.ai1_buttons,
            self.settings["ai1_difficulty"],
            SCREEN_HEIGHT // 2 - 80  # ← zhoduje sa s row1_y
        )
        self._draw_ai_section(
            "Počítač 2",
            self.ai2_buttons,
            self.settings["ai2_difficulty"],
            SCREEN_HEIGHT // 2 + 80  # ← zhoduje sa s row2_y
        )
        self._draw_back_button()

    def _draw_title(self):
        """Nakreslí nadpis."""
        title = self.font_title.render("NASTAVENIA", True, COLOR_GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title, title_rect)

        # Oddeľovacia čiara
        pygame.draw.line(
            self.screen, COLOR_GOLD,
            (SCREEN_WIDTH // 2 - 300, 160),
            (SCREEN_WIDTH // 2 + 300, 160),
            width=2
        )

    def _draw_ai_section(self, label: str, buttons: list,
                         current: str, label_y: int):
        # Label
        label_surf = self.font_large.render(label, True, COLOR_WHITE)
        label_rect = label_surf.get_rect(
            center=(SCREEN_WIDTH // 2, label_y - 45)  # ← posun label vyššie
        )
        self.screen.blit(label_surf, label_rect)

        # Tlačidlá obtiažnosti
        for btn in buttons:
            diff = btn["difficulty"]
            is_selected = (diff == current)
            base_color = self.difficulty_colors[diff]

            # Pozadie
            overlay = pygame.Surface(
                (btn["rect"].width, btn["rect"].height),
                pygame.SRCALPHA
            )
            if is_selected:
                overlay.fill((*base_color, 230))
            elif btn["hover"]:
                overlay.fill((*base_color, 120))
            else:
                overlay.fill((40, 25, 10, 180))
            self.screen.blit(overlay, (btn["rect"].x, btn["rect"].y))

            # Okraj
            border_color = base_color if is_selected or btn["hover"] else COLOR_GRAY
            border_width = 3 if is_selected else 1
            pygame.draw.rect(
                self.screen, border_color,
                btn["rect"], width=border_width, border_radius=BUTTON_RADIUS
            )

            # Text
            text_color = COLOR_BLACK if is_selected else COLOR_WHITE
            text = self.font_medium.render(
                self.difficulty_labels[diff], True, text_color
            )
            text_rect = text.get_rect(center=btn["rect"].center)
            self.screen.blit(text, text_rect)

    def _draw_back_button(self):
        """Nakreslí tlačidlo späť."""
        rect = self.back_button["rect"]
        color = COLOR_BUTTON_PRIMARY if self.back_button["hover"] else COLOR_BUTTON_SECONDARY

        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((*color, 220))
        self.screen.blit(overlay, (rect.x, rect.y))

        pygame.draw.rect(
            self.screen, COLOR_GOLD,
            rect, width=2, border_radius=BUTTON_RADIUS
        )

        text = self.font_large.render("← Späť", True, COLOR_WHITE)
        text_rect = text.get_rect(center=rect.center)
        self.screen.blit(text, text_rect)