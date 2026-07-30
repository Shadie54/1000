# gui/achievement_popup.py

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_WHITE, COLOR_GOLD,
    FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
    get_font
)
from achievements.definitions import get_achievement, get_tier_name

class AchievementPopup:
    """
    Zobrazuje frontu popup notifikácií pre odomknuté achievementy.
    Jedna sa zobrazí naraz, ďalšia čaká vo fronte.
    """

    # gui/achievement_popup.py

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_title = get_font(FONT_SIZE_SMALL + 2)
        self.font_name = get_font(FONT_SIZE_LARGE)
        self.font_desc = get_font(FONT_SIZE_MEDIUM - 2)

        self.queue: list[str] = []
        self.current: dict | None = None
        self.show_until: int = 0
        self.slide_start: int = 0

        # ← 25% väčšie
        self.popup_w = int(420 * 1.25)  # 525
        self.popup_h = int(155 * 1.25)  # 194
        self.icon_w = int(70 * 1.25)  # 87
        self.icon_h = int(113 * 1.25)  # 141

        self.display_duration = 20000
        self.slide_duration = 350

        self.trophy_icons = {}
        for tier_name in ("bronze", "silver", "gold"):
            try:
                img = pygame.image.load(f"assets/graphics/trophy_{tier_name}.png").convert_alpha()
                img = pygame.transform.scale(img, (self.icon_w, self.icon_h))
                self.trophy_icons[tier_name] = img
            except (FileNotFoundError, pygame.error):
                self.trophy_icons[tier_name] = None

        try:
            self.unlock_sound = pygame.mixer.Sound("assets/sounds/trophy_unlock.mp3")
        except (FileNotFoundError, pygame.error):
            self.unlock_sound = None

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
                if self.unlock_sound:
                    self.unlock_sound.play()  # ← NOVÉ

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

        # Pozadie — tmavšie a nepriehľadnejšie, zladené s čiernou kartou
        surf = pygame.Surface((self.popup_w, self.popup_h), pygame.SRCALPHA)
        surf.fill((10, 6, 2, 245))
        self.screen.blit(surf, (x, y))
        pygame.draw.rect(
            self.screen, COLOR_GOLD,
            (x, y, self.popup_w, self.popup_h),
            width=3, border_radius=12
        )
        # Jemný vnútorný okraj — zladenie s kartou
        pygame.draw.rect(
            self.screen, COLOR_GOLD,
            (x + 5, y + 5, self.popup_w - 10, self.popup_h - 10),
            width=1, border_radius=9
        )

        # Ikona vľavo
        tier = get_tier_name(self.current["id"])
        icon = self.trophy_icons.get(tier)

        icon_x = x + 18
        icon_y = y + (self.popup_h - self.icon_h) // 2
        if icon:
            self.screen.blit(icon, (icon_x, icon_y))
            pygame.draw.rect(
                self.screen, COLOR_GOLD,
                (icon_x, icon_y, self.icon_w, self.icon_h),
                width=2, border_radius=8
            )
        else:
            self._draw_trophy_icon(icon_x + self.icon_w // 2, icon_y + self.icon_h // 2, self.icon_w)

        # Text vpravo od ikony
        text_x = icon_x + self.icon_w + 20
        text_max_w = self.popup_w - (text_x - x) - 18

        title_surf = self.font_title.render("TROFEJ ODOMKNUTÁ", True, COLOR_GOLD)
        self.screen.blit(title_surf, (text_x, y + 20))

        name_surf = self.font_name.render(self.current["name"], True, COLOR_WHITE)
        self.screen.blit(name_surf, (text_x, y + 48))

        # ← Lepšia farba popisu — teplá svetlá krémová namiesto šedej
        desc_color = (225, 210, 185)
        desc_lines = self._wrap_text(self.current["description"], self.font_desc, text_max_w)
        line_h = self.font_desc.get_height() + 3
        for i, line in enumerate(desc_lines[:3]):  # max 3 riadky (viac miesta teraz)
            line_surf = self.font_desc.render(line, True, desc_color)
            self.screen.blit(line_surf, (text_x, y + 84 + i * line_h))

    def _wrap_text(self, text: str, font, max_width: int) -> list[str]:
        """Zalomí text na viac riadkov podľa max šírky."""
        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

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