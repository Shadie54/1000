# gui/achievement_popup.py

import pygame
from gui import display, ui_style
from config import (
    SCREEN_WIDTH,
    FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
)

# Popup prichádza sprava dole (ako sú hráči zvyknutí z iných hier).
# Vzhľad: gui/ui_style.py (grafický rework 2026-10-28).
POPUP_MARGIN = 30
from achievements.definitions import get_achievement, get_tier_name

class AchievementPopup:
    """
    Zobrazuje frontu popup notifikácií pre odomknuté achievementy.
    Jedna sa zobrazí naraz, ďalšia čaká vo fronte.
    """

    # gui/achievement_popup.py

    def __init__(self, canvas):
        # Kreslí cez Canvas; poloha v pravom dolnom rohu podľa logickej výšky.
        self.canvas = canvas
        self.H = display.logical_height()
        self.font_title = canvas.font(FONT_SIZE_SMALL + 2)
        self.font_name = canvas.font(FONT_SIZE_LARGE)
        self.font_desc = canvas.font(FONT_SIZE_MEDIUM - 2)

        self.queue: list[str] = []
        self.current: dict | None = None
        self.show_until: int = 0
        self.slide_start: int = 0

        # ← 25% väčšie
        self.popup_w = int(420 * 1.25)  # 525
        self.popup_h = int(155 * 1.25)  # 194
        self.icon_w = int(70 * 1.25)  # 87
        self.icon_h = int(113 * 1.25)  # 141

        self.display_duration = 15000
        self.slide_duration = 350

        self.trophy_icons = {}
        for tier_name in ("bronze", "silver", "gold"):
            path = f"assets/graphics/trophy_{tier_name}.png"
            try:
                self.trophy_icons[tier_name] = canvas.image(
                    path, (self.icon_w, self.icon_h), smooth=False)
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

        x, y = self._rect().topleft

        c = self.canvas
        rect = pygame.Rect(x, y, self.popup_w, self.popup_h)
        # Tieň, nepriehľadný panel so zlatým rámom a jemný vnútorný okraj
        c.overlay(rect.move(0, 6), (0, 0, 0, 120), border_radius=ui_style.PANEL_RADIUS)
        c.overlay(rect, (17, 11, 7, 250), border_radius=ui_style.PANEL_RADIUS)
        c.overlay((x + 3, y + 3, self.popup_w - 6, 40), (255, 214, 140, 8),
                  border_radius=ui_style.PANEL_RADIUS - 3)
        c.rect(ui_style.GOLD, rect, width=2, border_radius=ui_style.PANEL_RADIUS)
        c.rect(ui_style.GOLD_SOFT, rect.inflate(-10, -10), width=1,
               border_radius=ui_style.PANEL_RADIUS - 4)

        # Ikona vľavo
        tier = get_tier_name(self.current["id"])
        icon = self.trophy_icons.get(tier)

        icon_x = x + 18
        icon_y = y + (self.popup_h - self.icon_h) // 2
        if icon:
            self.canvas.blit(icon, (icon_x, icon_y))
            self.canvas.rect(ui_style.GOLD, (icon_x, icon_y, self.icon_w, self.icon_h),
                             width=2, border_radius=8)
        else:
            self._draw_trophy_icon(icon_x + self.icon_w // 2, icon_y + self.icon_h // 2, self.icon_w)

        # Text vpravo od ikony
        text_x = icon_x + self.icon_w + 20
        text_max_w = self.popup_w - (text_x - x) - 18

        title_surf = self.font_title.render("TROFEJ ODOMKNUTÁ", True, ui_style.TEXT_DIM)
        self.canvas.blit(title_surf, (text_x, y + 20))

        name_surf = self.font_name.render(self.current["name"], True, ui_style.GOLD)
        self.canvas.blit(name_surf, (text_x, y + 48))

        # ← Lepšia farba popisu — teplá svetlá krémová namiesto šedej
        desc_color = ui_style.TEXT
        desc_lines = self._wrap_text(self.current["description"], self.font_desc, text_max_w)
        line_h = self.font_desc.get_height() + 3
        for i, line in enumerate(desc_lines[:3]):  # max 3 riadky (viac miesta teraz)
            line_surf = self.font_desc.render(line, True, desc_color)
            self.canvas.blit(line_surf, (text_x, y + 84 + i * line_h))

    def _rect(self) -> pygame.Rect:
        """Aktuálna poloha popupu (vysúva sa sprava, na konci sa zasúva)."""
        now = pygame.time.get_ticks()
        elapsed = now - self.slide_start
        remaining = self.show_until - now
        target_x = SCREEN_WIDTH - self.popup_w - 30
        start_x = SCREEN_WIDTH + 20
        if elapsed < self.slide_duration:
            progress = elapsed / self.slide_duration
            x = start_x + (target_x - start_x) * self._ease_out(progress)
        elif remaining < self.slide_duration:
            progress = 1 - (remaining / self.slide_duration)
            x = target_x + (start_x - target_x) * self._ease_out(progress)
        else:
            x = target_x
        return pygame.Rect(int(x), self.H - self.popup_h - POPUP_MARGIN,
                           self.popup_w, self.popup_h)

    def handle_event(self, event) -> bool:
        """Klik na popup ho zavrie (zasunie sa) a k tlačidlám pod ním sa
        nedostane — popup zakrýva stĺpec tlačidiel vpravo dole."""
        if (self.current is None or event.type != pygame.MOUSEBUTTONDOWN
                or event.button != 1 or not self._rect().collidepoint(event.pos)):
            return False
        now = pygame.time.get_ticks()
        self.show_until = min(self.show_until, now + self.slide_duration)
        return True

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
        self.canvas.circle(ui_style.GOLD, (cx, cy), size // 2)
        self.canvas.circle((15, 9, 4), (cx, cy), size // 2 - 4)

        # Jednoduchá hviezda v strede
        star_points = self._star_points(cx, cy, size // 2 - 8, size // 4 - 2)
        self.canvas.polygon(ui_style.GOLD, star_points)

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