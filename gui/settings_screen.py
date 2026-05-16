# gui/settings_screen.py

import pygame
import sys
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_WHITE, COLOR_BLACK, COLOR_GOLD, COLOR_GRAY,
    COLOR_BUTTON_PRIMARY, COLOR_BUTTON_SECONDARY,
    COLOR_GREEN, COLOR_YELLOW, COLOR_RED,
    FONT_SIZE_LARGE, FONT_SIZE_MEDIUM,
    BUTTON_RADIUS, get_font
)


class SettingsScreen:
    def __init__(self, screen: pygame.Surface, settings: dict):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.settings = settings.copy()

        self.font_title  = get_font(72)
        self.font_large  = get_font(FONT_SIZE_LARGE)
        self.font_medium = get_font(FONT_SIZE_MEDIUM)

        try:
            self.bg = pygame.image.load("assets/graphics/table.jpg").convert()
            self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except FileNotFoundError:
            self.bg = None

        self.difficulties = ["easy", "medium", "hard"]
        self.difficulty_labels = {"easy": "Ľahká", "medium": "Stredná", "hard": "Ťažká"}
        self.difficulty_colors = {"easy": COLOR_GREEN, "medium": COLOR_YELLOW, "hard": COLOR_RED}

        btn_w, btn_h = 160, 55
        center_x = SCREEN_WIDTH // 2
        row1_y = SCREEN_HEIGHT // 2 - 280
        row2_y = SCREEN_HEIGHT // 2 - 120

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

        # Pozadie stolu
        self.bg_options = ["table.jpg", "table1.jpg", "table2.jpg",
                           "table3.jpg", "table4.jpg", "table5.jpg"]
        self.bg_labels = ["Stôl 1", "Stôl 2", "Stôl 3",
                          "Stôl 4", "Stôl 5", "Stôl 6"]

        self.bg_thumbnails = {}
        self._load_thumbnails()

        thumb_w, thumb_h = 240, 135
        gap_x, gap_y = 20, 20
        cols = 3
        total_w = cols * (thumb_w + gap_x) - gap_x
        thumb_start_x = center_x - total_w // 2
        thumb_y = row2_y + btn_h + 80

        self.bg_rects = []
        for i in range(len(self.bg_options)):
            col = i % cols
            row = i // cols
            x = thumb_start_x + col * (thumb_w + gap_x)
            y = thumb_y + row * (thumb_h + gap_y + 24)  # +24 pre label
            self.bg_rects.append(pygame.Rect(x, y, thumb_w, thumb_h))

        # Tlačidlo späť
        self.back_button = {
            "rect":  pygame.Rect(center_x - 150, SCREEN_HEIGHT - 80, 300, 55),
            "hover": False
        }

    # ------------------------------------------------------------------
    # Miniatúry
    # ------------------------------------------------------------------

    def _load_thumbnails(self):
        for fname in self.bg_options:
            try:
                img = pygame.image.load(f"assets/graphics/{fname}").convert()
                self.bg_thumbnails[fname] = pygame.transform.scale(img, (260, 150))
            except FileNotFoundError:
                self.bg_thumbnails[fname] = None

    # ------------------------------------------------------------------
    # Hlavná slučka
    # ------------------------------------------------------------------

    def run(self) -> dict:
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
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self._handle_click(event.pos) == "back":
                        return self.settings

            self._update_hover(mouse_pos)
            self._draw()
            pygame.display.flip()

    # ------------------------------------------------------------------
    # Udalosti
    # ------------------------------------------------------------------

    def _handle_click(self, pos) -> str | None:
        for btn in self.ai1_buttons:
            if btn["rect"].collidepoint(pos):
                self.settings["ai1_difficulty"] = btn["difficulty"]
                return None
        for btn in self.ai2_buttons:
            if btn["rect"].collidepoint(pos):
                self.settings["ai2_difficulty"] = btn["difficulty"]
                return None
        for i, (fname, rect) in enumerate(zip(self.bg_options, self.bg_rects)):
            if rect.collidepoint(pos):
                self.settings["table_bg"] = fname
                return None
        if self.back_button["rect"].collidepoint(pos):
            return "back"
        return None

    def _update_hover(self, mouse_pos):
        for btn in self.ai1_buttons + self.ai2_buttons:
            btn["hover"] = btn["rect"].collidepoint(mouse_pos)
        self.back_button["hover"] = self.back_button["rect"].collidepoint(mouse_pos)

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def _draw(self):
        if self.bg:
            self.screen.blit(self.bg, (0, 0))
        else:
            self.screen.fill((45, 28, 15))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        self._draw_title()
        self._draw_ai_section("Počítač 1", self.ai1_buttons,
                               self.settings["ai1_difficulty"],
                               self.ai1_buttons[0]["rect"].top)
        self._draw_ai_section("Počítač 2", self.ai2_buttons,
                               self.settings["ai2_difficulty"],
                               self.ai2_buttons[0]["rect"].top)
        self._draw_bg_section()
        self._draw_back_button()

    def _draw_title(self):
        title = self.font_title.render("NASTAVENIA", True, COLOR_GOLD)
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 80)))
        pygame.draw.line(self.screen, COLOR_GOLD,
                         (SCREEN_WIDTH // 2 - 300, 120),
                         (SCREEN_WIDTH // 2 + 300, 120), width=1)

    def _draw_ai_section(self, label: str, buttons: list, current: str, row_y: int):
        label_surf = self.font_large.render(label, True, COLOR_WHITE)
        self.screen.blit(label_surf, label_surf.get_rect(
            center=(SCREEN_WIDTH // 2, row_y - 30)
        ))
        for btn in buttons:
            diff        = btn["difficulty"]
            is_selected = diff == current
            base_color  = self.difficulty_colors[diff]

            surf = pygame.Surface((btn["rect"].width, btn["rect"].height), pygame.SRCALPHA)
            if is_selected:
                surf.fill((*base_color, 230))
            elif btn["hover"]:
                surf.fill((*base_color, 120))
            else:
                surf.fill((40, 25, 10, 180))
            self.screen.blit(surf, btn["rect"].topleft)

            pygame.draw.rect(self.screen,
                             base_color if is_selected or btn["hover"] else COLOR_GRAY,
                             btn["rect"], width=3 if is_selected else 1,
                             border_radius=BUTTON_RADIUS)

            text = self.font_medium.render(
                self.difficulty_labels[diff], True,
                COLOR_BLACK if is_selected else COLOR_WHITE
            )
            self.screen.blit(text, text.get_rect(center=btn["rect"].center))

    def _draw_bg_section(self):
        label_y = self.bg_rects[0].top - 35
        label   = self.font_large.render("POZADIE STOLU", True, COLOR_WHITE)
        self.screen.blit(label, label.get_rect(
            center=(SCREEN_WIDTH // 2, label_y)
        ))

        current = self.settings.get("table_bg", "table.jpg")
        for i, (fname, rect) in enumerate(zip(self.bg_options, self.bg_rects)):
            is_selected = fname == current
            is_hover    = rect.collidepoint(pygame.mouse.get_pos())

            thumb = self.bg_thumbnails.get(fname)
            if thumb:
                # Orezaj rohy miniatúry
                clipped = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                pygame.draw.rect(clipped, (255, 255, 255, 255),
                                 (0, 0, rect.w, rect.h), border_radius=6)
                clipped.blit(thumb, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
                self.screen.blit(clipped, rect)
            else:
                surf = pygame.Surface((rect.w, rect.h))
                surf.fill((40, 25, 10))
                self.screen.blit(surf, rect)
                no_img = self.font_medium.render("Nenájdený", True, COLOR_GRAY)
                self.screen.blit(no_img, no_img.get_rect(center=rect.center))

            pygame.draw.rect(self.screen,
                             COLOR_GOLD if is_selected else (COLOR_WHITE if is_hover else COLOR_GRAY),
                             rect, width=3 if is_selected else 1, border_radius=6)

            lbl = self.font_medium.render(
                self.bg_labels[i], True,
                COLOR_GOLD if is_selected else COLOR_WHITE
            )
            self.screen.blit(lbl, lbl.get_rect(
                centerx=rect.centerx, top=rect.bottom + 6
            ))

    def _draw_back_button(self):
        rect  = self.back_button["rect"]
        color = COLOR_BUTTON_PRIMARY if self.back_button["hover"] else COLOR_BUTTON_SECONDARY
        surf  = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surf.fill((*color, 220))
        self.screen.blit(surf, rect.topleft)
        pygame.draw.rect(self.screen, COLOR_GOLD, rect, width=2, border_radius=BUTTON_RADIUS)
        text = self.font_large.render("← Späť", True, COLOR_WHITE)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def __repr__(self):
        return "SettingsScreen()"