# gui/achievement_popup.py

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_WHITE, COLOR_GOLD, COLOR_GRAY,
    FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
    get_font
)
from achievements.definitions import get_achievement


class AchievementPopup:
    """
    Zobrazuje frontu popup notifikácií pre odomknuté achievementy.
    Jedna sa zobrazí naraz, ďalšia čaká vo fronte.
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_title = get_font(FONT_SIZE_SMALL + 2)
        self.font_name = get_font(FONT_SIZE_LARGE)  # bolo FONT_SIZE_MEDIUM
        self.font_desc = get_font(FONT_SIZE_MEDIUM - 2)  # bolo FONT_SIZE_SMALL - 2

        self.queue: list[str] = []
        self.current: dict | None = None
        self.show_until: int = 0
        self.slide_start: int = 0

        self.popup_w = 420  # zväčšené kvôli väčšiemu textu
        self.popup_h = 130  # zväčšené
        self.icon_w = 70
        self.icon_h = 113  # pomer strán karty (70 / 0.62)
        self.display_duration = 8000
        self.slide_duration = 350

        # Podkladová ikona (pozadie karty)
        try:
            self.icon_bg = pygame.image.load("assets/graphics/trophy_bg.png").convert_alpha()
            self.icon_bg = pygame.transform.scale(self.icon_bg, (self.icon_w, self.icon_h))
        except FileNotFoundError:
            self.icon_bg = None

    # ------------------------------------------------------------------
    # Pridanie do fronty
    # ------------------------------------------------------------------

    def add(self, achievement_ids: list[str]):
        """Pridá zoznam achievement ID do fronty na zobrazenie."""
        self.queue.extend(achievement_ids)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self):
        now = pygame.time.get_ticks()

        if self.current is None and self.queue:
            next_id = self.queue.pop(0)
            achievement = get_achievement(next_id)
            if achievement:
                self.current = achievement
                self.slide_start = now
                self.show_until = now + self.display_duration

        if self.current and now >= self.show_until:
            self.current = None

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def draw(self):
        if not self.current:
            return

        now = pygame.time.get_ticks()
        elapsed = now - self.slide_start
        remaining = self.show_until - now

        target_x = SCREEN_WIDTH - self.popup_w - 30
        start_x = SCREEN_WIDTH + 20
        y = SCREEN_HEIGHT - self.popup_h - 30

        if elapsed < self.slide_duration:
            progress = elapsed / self.slide_duration
            x = start_x + (target_x - start_x) * self._ease_out(progress)
        elif remaining < self.slide_duration:
            progress = 1 - (remaining / self.slide_duration)
            x = target_x + (start_x - target_x) * self._ease_out(progress)
        else:
            x = target_x

        x = int(x)

        # Pozadie
        surf = pygame.Surface((self.popup_w, self.popup_h), pygame.SRCALPHA)
        surf.fill((15, 9, 4, 235))
        self.screen.blit(surf, (x, y))
        pygame.draw.rect(
            self.screen, COLOR_GOLD,
            (x, y, self.popup_w, self.popup_h),
            width=2, border_radius=10
        )

        # Ikona vľavo
        icon_x = x + 15
        icon_y = y + (self.popup_h - self.icon_h) // 2
        if self.icon_bg:
            self.screen.blit(self.icon_bg, (icon_x, icon_y))
            pygame.draw.rect(
                self.screen, COLOR_GOLD,
                (icon_x, icon_y, self.icon_w, self.icon_h),
                width=1, border_radius=6
            )
        else:
            self._draw_trophy_icon(icon_x + self.icon_w // 2, icon_y + self.icon_h // 2, self.icon_w)

        text_x = icon_x + self.icon_w + 16
        text_max_w = self.popup_w - (text_x - x) - 14

        title_surf = self.font_title.render("TROFEJ ODOMKNUTÁ", True, COLOR_GOLD)
        self.screen.blit(title_surf, (text_x, y + 16))

        name_surf = self.font_name.render(self.current["name"], True, COLOR_WHITE)
        self.screen.blit(name_surf, (text_x, y + 42))

        desc_text = self.current["description"]
        desc_surf = self.font_desc.render(desc_text, True, COLOR_GRAY)
        while desc_surf.get_width() > text_max_w and len(desc_text) > 10:
            desc_text = desc_text[:-4] + "..."
            desc_surf = self.font_desc.render(desc_text, True, COLOR_GRAY)
        self.screen.blit(desc_surf, (text_x, y + 76))

    def _draw_trophy_icon(self, cx: int, cy: int, size: int):
        """Nakreslí jednoduchú ikonu trofeje (kruh + hviezda)."""
        pygame.draw.circle(self.screen, COLOR_GOLD, (cx, cy), size // 2)
        pygame.draw.circle(self.screen, (15, 9, 4), (cx, cy), size // 2 - 4)

        # Jednoduchá hviezda v strede
        star_points = self._star_points(cx, cy, size // 2 - 8, size // 4 - 2)
        pygame.draw.polygon(self.screen, COLOR_GOLD, star_points)

    def _star_points(self, cx: int, cy: int, r_outer: int, r_inner: int) -> list:
        import math
        points = []
        for i in range(10):
            angle = math.pi / 5 * i - math.pi / 2
            r = r_outer if i % 2 == 0 else r_inner
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        return points

    def _ease_out(self, t: float) -> float:
        return 1 - (1 - t) ** 3

    def __repr__(self):
        return f"AchievementPopup(queue={len(self.queue)})"