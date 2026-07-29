# gui/achievements_screen.py

import pygame
import sys
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_WHITE, COLOR_GOLD, COLOR_GRAY,
    COLOR_BUTTON_PRIMARY, COLOR_BUTTON_SECONDARY,
    FONT_SIZE_SMALL, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE,
    BUTTON_RADIUS, get_font
)
from achievements.definitions import ACHIEVEMENTS
from achievements.storage import load_achievements


class AchievementsScreen:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()

        self.font_title = get_font(FONT_SIZE_LARGE + 8)
        self.font_large = get_font(FONT_SIZE_LARGE)
        self.font_medium = get_font(FONT_SIZE_MEDIUM)
        self.font_small = get_font(FONT_SIZE_SMALL)

        try:
            self.bg = pygame.image.load("assets/graphics/table.jpg").convert()
            self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except FileNotFoundError:
            self.bg = None

        self.data = load_achievements()
        self.scroll_offset = 0
        self.max_scroll = 0

        # Panel rozmery
        self.PAD = 30
        self.PANEL_X = 60
        self.PANEL_Y = 20
        self.PANEL_W = SCREEN_WIDTH - 120
        self.PANEL_H = SCREEN_HEIGHT - 40
        self.CONTENT_Y = self.PANEL_Y + 100
        self.CONTENT_H = self.PANEL_H - 160

        # Tlačidlo späť
        self.back_button = pygame.Rect(
            SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 60, 300, 45
        )

        self._build_rows()

    # ------------------------------------------------------------------
    # Príprava riadkov
    # ------------------------------------------------------------------

    def _build_rows(self):
        """Zoskupí achievementy — stupňované pod seba, ostatné samostatne."""
        self.rows = []
        seen_groups = set()

        for a in ACHIEVEMENTS:
            group = a.get("group")
            if group:
                if group in seen_groups:
                    continue
                seen_groups.add(group)
                tier_items = [x for x in ACHIEVEMENTS if x.get("group") == group]
                self.rows.append({"type": "group", "items": tier_items})
            else:
                self.rows.append({"type": "single", "item": a})

        row_h = 70
        total_h = len(self.rows) * row_h
        self.max_scroll = max(0, total_h - self.CONTENT_H)

    # ------------------------------------------------------------------
    # Hlavná slučka
    # ------------------------------------------------------------------

    def run(self):
        while True:
            self.clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and self.back_button.collidepoint(event.pos):
                        return
                    if event.button == 4:  # scroll up
                        self.scroll_offset = max(0, self.scroll_offset - 40)
                    if event.button == 5:  # scroll down
                        self.scroll_offset = min(self.max_scroll, self.scroll_offset + 40)

            self._draw(mouse_pos)
            pygame.display.flip()

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def _draw(self, mouse_pos):
        if self.bg:
            self.screen.blit(self.bg, (0, 0))
        else:
            self.screen.fill((45, 28, 15))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        self._draw_panel_bg()
        self._draw_title()
        self._draw_progress()
        self._draw_rows()
        self._draw_back_button(mouse_pos)

    def _draw_panel_bg(self):
        surf = pygame.Surface((self.PANEL_W, self.PANEL_H), pygame.SRCALPHA)
        surf.fill((15, 9, 4, 245))
        self.screen.blit(surf, (self.PANEL_X, self.PANEL_Y))
        pygame.draw.rect(
            self.screen, COLOR_GOLD,
            (self.PANEL_X, self.PANEL_Y, self.PANEL_W, self.PANEL_H),
            width=2, border_radius=14
        )

    def _draw_title(self):
        title = self.font_title.render("TROFEJE", True, COLOR_GOLD)
        self.screen.blit(title, title.get_rect(
            centerx=SCREEN_WIDTH // 2, top=self.PANEL_Y + 16
        ))

    def _draw_progress(self):
        total = len(ACHIEVEMENTS)
        unlocked = sum(1 for v in self.data["unlocked"].values() if v)
        text = f"Odomknuté trofeje: {unlocked} / {total}"
        surf = self.font_medium.render(text, True, COLOR_WHITE)
        self.screen.blit(surf, surf.get_rect(
            centerx=SCREEN_WIDTH // 2, top=self.PANEL_Y + 60
        ))

    def _draw_rows(self):
        # Orezanie oblasti obsahu (scroll)
        clip_rect = pygame.Rect(
            self.PANEL_X, self.CONTENT_Y, self.PANEL_W, self.CONTENT_H
        )
        old_clip = self.screen.get_clip()
        self.screen.set_clip(clip_rect)

        row_h = 70
        y = self.CONTENT_Y - self.scroll_offset

        for row in self.rows:
            if y + row_h >= self.CONTENT_Y and y <= self.CONTENT_Y + self.CONTENT_H:
                if row["type"] == "single":
                    self._draw_single_row(row["item"], y, row_h)
                else:
                    self._draw_group_row(row["items"], y, row_h)
            y += row_h

        self.screen.set_clip(old_clip)

    def _draw_single_row(self, item: dict, y: int, row_h: int):
        unlocked = self.data["unlocked"].get(item["id"], False)
        self._draw_row_bg(y, row_h, unlocked)
        self._draw_trophy(self.PANEL_X + 45, y + row_h // 2, unlocked)
        self._draw_row_text(item["name"], item["description"], y, row_h, unlocked)

    def _draw_group_row(self, items: list, y: int, row_h: int):
        """Zobrazí stupňovaný achievement ako jeden riadok s viacerými trofejami."""
        # Najvyšší dosiahnutý tier
        unlocked_tiers = [
            item for item in items
            if self.data["unlocked"].get(item["id"], False)
        ]
        highest = unlocked_tiers[-1] if unlocked_tiers else items[0]
        any_unlocked = len(unlocked_tiers) > 0

        self._draw_row_bg(y, row_h, any_unlocked)

        # Trofeje pre každý tier vedľa seba
        icon_x = self.PANEL_X + 45
        for i, item in enumerate(items):
            is_unlocked = self.data["unlocked"].get(item["id"], False)
            self._draw_trophy(icon_x + i * 36, y + row_h // 2, is_unlocked, size=24)

        text_x_offset = 45 + len(items) * 36 - 20
        name = highest["name"] if any_unlocked else items[0]["name"].rsplit(" ", 1)[0]
        desc = highest["description"] if any_unlocked else items[0]["description"]
        self._draw_row_text(name, desc, y, row_h, any_unlocked, x_offset=text_x_offset)

    def _draw_row_bg(self, y: int, row_h: int, unlocked: bool):
        rect = pygame.Rect(self.PANEL_X + 20, y + 4, self.PANEL_W - 40, row_h - 8)
        color = (40, 30, 10, 160) if unlocked else (20, 15, 10, 140)
        surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surf.fill(color)
        self.screen.blit(surf, rect.topleft)
        border = COLOR_GOLD if unlocked else COLOR_GRAY
        pygame.draw.rect(self.screen, border, rect, width=1, border_radius=8)

    def _draw_trophy(self, cx: int, cy: int, unlocked: bool, size: int = 28):
        color = COLOR_GOLD if unlocked else (70, 70, 70)
        pygame.draw.circle(self.screen, color, (cx, cy), size // 2)
        pygame.draw.circle(self.screen, (15, 9, 4), (cx, cy), size // 2 - 4)
        if unlocked:
            star_points = self._star_points(cx, cy, size // 2 - 7, size // 4 - 1)
            pygame.draw.polygon(self.screen, COLOR_GOLD, star_points)

    def _star_points(self, cx, cy, r_outer, r_inner):
        import math
        points = []
        for i in range(10):
            angle = math.pi / 5 * i - math.pi / 2
            r = r_outer if i % 2 == 0 else r_inner
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        return points

    def _draw_row_text(self, name: str, description: str, y: int, row_h: int,
                       unlocked: bool, x_offset: int = 45):
        text_x = self.PANEL_X + x_offset + 40
        name_color = COLOR_GOLD if unlocked else COLOR_GRAY
        name_surf = self.font_medium.render(name, True, name_color)
        self.screen.blit(name_surf, (text_x, y + 10))

        desc_color = COLOR_WHITE if unlocked else (90, 85, 80)
        desc_text = description if unlocked else "???"
        desc_surf = self.font_small.render(desc_text, True, desc_color)
        self.screen.blit(desc_surf, (text_x, y + 38))

    def _draw_back_button(self, mouse_pos):
        hover = self.back_button.collidepoint(mouse_pos)
        color = COLOR_BUTTON_PRIMARY if hover else COLOR_BUTTON_SECONDARY
        surf = pygame.Surface((self.back_button.width, self.back_button.height), pygame.SRCALPHA)
        surf.fill((*color, 220))
        self.screen.blit(surf, self.back_button.topleft)
        pygame.draw.rect(self.screen, COLOR_GOLD, self.back_button, width=2, border_radius=BUTTON_RADIUS)
        text = self.font_large.render("← Späť", True, COLOR_WHITE)
        self.screen.blit(text, text.get_rect(center=self.back_button.center))

    def __repr__(self):
        return "AchievementsScreen()"