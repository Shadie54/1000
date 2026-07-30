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
        self.font_name  = get_font(FONT_SIZE_MEDIUM + 4)
        self.font_desc  = get_font(FONT_SIZE_MEDIUM - 2)

        try:
            self.bg = pygame.image.load("assets/graphics/table.jpg").convert()
            self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except FileNotFoundError:
            self.bg = None

        # Trofej ikony — jednotná výška pre single aj group, líši sa len šírka
        self.icon_w, self.icon_h = 70, 113          # single riadky
        self.icon_w_small = 46                       # group riadky (rovnaká výška icon_h)

        self.trophy_icons = {}
        for tier_name in ("bronze", "silver", "gold"):
            try:
                img = pygame.image.load(f"assets/graphics/trophy_{tier_name}.png").convert_alpha()
                self.trophy_icons[tier_name] = img
            except (FileNotFoundError, pygame.error):
                self.trophy_icons[tier_name] = None

        self.data = load_achievements()
        self.scroll_offset = 0
        self.max_scroll = 0

        self.PAD = 30
        self.PANEL_X = 60
        self.PANEL_Y = 20
        self.PANEL_W = SCREEN_WIDTH - 120
        self.PANEL_H = SCREEN_HEIGHT - 40

        # Vyhradený priestor pre tlačidlo späť (mimo scrollovateľnej oblasti)
        self.BACK_AREA_H = 80
        self.CONTENT_Y = self.PANEL_Y + 105
        self.CONTENT_H = self.PANEL_H - 105 - self.BACK_AREA_H

        self.back_button = pygame.Rect(
            SCREEN_WIDTH // 2 - 150,
            self.PANEL_Y + self.PANEL_H - self.BACK_AREA_H + 15,
            300, 50
        )

        self.row_h = 140  # konzistentná výška pre VŠETKY riadky
        self._build_rows()

    # ------------------------------------------------------------------
    # Príprava riadkov
    # ------------------------------------------------------------------

    def _build_rows(self):
        """Zoskupí achievementy — stupňované pod seba, ostatné samostatne.
        Poradie ACHIEVEMENTS v definitions.py určuje poradie zobrazenia."""
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

        total_h = len(self.rows) * self.row_h
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
                    if event.button == 4:
                        self.scroll_offset = max(0, self.scroll_offset - 50)
                    if event.button == 5:
                        self.scroll_offset = min(self.max_scroll, self.scroll_offset + 50)

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
        surf.fill((12, 8, 4, 248))
        self.screen.blit(surf, (self.PANEL_X, self.PANEL_Y))
        pygame.draw.rect(
            self.screen, COLOR_GOLD,
            (self.PANEL_X, self.PANEL_Y, self.PANEL_W, self.PANEL_H),
            width=2, border_radius=14
        )
        line_y = self.PANEL_Y + self.PANEL_H - self.BACK_AREA_H
        pygame.draw.line(
            self.screen, COLOR_GOLD,
            (self.PANEL_X + 20, line_y), (self.PANEL_X + self.PANEL_W - 20, line_y),
            width=1
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
        surf = self.font_large.render(text, True, COLOR_WHITE)
        self.screen.blit(surf, surf.get_rect(
            centerx=SCREEN_WIDTH // 2, top=self.PANEL_Y + 64
        ))

    def _draw_rows(self):
        clip_rect = pygame.Rect(
            self.PANEL_X, self.CONTENT_Y, self.PANEL_W, self.CONTENT_H
        )
        old_clip = self.screen.get_clip()
        self.screen.set_clip(clip_rect)

        y = self.CONTENT_Y - self.scroll_offset

        for row in self.rows:
            if y + self.row_h >= self.CONTENT_Y and y <= self.CONTENT_Y + self.CONTENT_H:
                if row["type"] == "single":
                    self._draw_single_row(row["item"], y)
                else:
                    self._draw_group_row(row["items"], y)
            y += self.row_h

        self.screen.set_clip(old_clip)

    def _tier_icon_name(self, index: int, total: int) -> str:
        if total <= 1:
            return "gold"
        if total == 2:
            return "silver" if index == 0 else "gold"
        if index == 0:
            return "bronze"
        if index == total - 1:
            return "gold"
        return "silver"

    # ------------------------------------------------------------------
    # Riadky
    # ------------------------------------------------------------------

    def _draw_single_row(self, item: dict, y: int):
        unlocked = self.data["unlocked"].get(item["id"], False)
        self._draw_row_bg(y, unlocked)

        cx = self.PANEL_X + 30 + self.icon_w // 2
        cy = y + self.row_h // 2
        self._draw_trophy_slot("gold", cx, cy, unlocked, self.icon_w, self.icon_h)

        icon_slot_w = 30 + self.icon_w + 30
        self._draw_row_text(item["name"], item["description"], y, unlocked, icon_slot_w,
                            hidden=item.get("hidden", False))

    def _draw_group_row(self, items: list, y: int):
        unlocked_tiers = [
            item for item in items
            if self.data["unlocked"].get(item["id"], False)
        ]
        any_unlocked = len(unlocked_tiers) > 0
        highest = unlocked_tiers[-1] if unlocked_tiers else None

        self._draw_row_bg(y, any_unlocked)

        # ← Rovnaká šírka aj výška ako single trofeje
        icon_gap = self.icon_w + 12
        icon_start_x = self.PANEL_X + 30 + self.icon_w // 2
        cy = y + self.row_h // 2

        for i, item in enumerate(items):
            is_unlocked = self.data["unlocked"].get(item["id"], False)
            tier_name = self._tier_icon_name(i, len(items))
            cx = icon_start_x + i * icon_gap
            self._draw_trophy_slot(tier_name, cx, cy, is_unlocked,
                                   self.icon_w, self.icon_h)

        icon_slot_w = 30 + len(items) * icon_gap - 12 + 30
        item_to_show = highest if highest else items[0]
        name = item_to_show["name"] if highest else items[0]["name"].rsplit(" ", 1)[0]
        desc = item_to_show["description"]
        self._draw_row_text(name, desc, y, any_unlocked, icon_slot_w,
                            hidden=item_to_show.get("hidden", False))

    # ------------------------------------------------------------------
    # Vizuálne prvky
    # ------------------------------------------------------------------

    def _draw_row_bg(self, y: int, unlocked: bool):
        rect = pygame.Rect(self.PANEL_X + 20, y + 8, self.PANEL_W - 40, self.row_h - 16)
        color = (42, 32, 12, 190) if unlocked else (22, 17, 12, 150)
        surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surf.fill(color)
        self.screen.blit(surf, rect.topleft)
        border = COLOR_GOLD if unlocked else (90, 80, 65)
        pygame.draw.rect(self.screen, border, rect, width=1, border_radius=10)

    def _draw_trophy_slot(self, tier_name: str, cx: int, cy: int,
                          unlocked: bool, w: int, h: int):
        rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)

        if unlocked:
            icon = self.trophy_icons.get(tier_name)
            if icon:
                scaled = pygame.transform.scale(icon, (w, h))
                self.screen.blit(scaled, rect.topleft)
                pygame.draw.rect(self.screen, COLOR_GOLD, rect, width=2, border_radius=6)
            else:
                r = min(w, h) // 2
                pygame.draw.circle(self.screen, COLOR_GOLD, (cx, cy), r)
                pygame.draw.circle(self.screen, (15, 9, 4), (cx, cy), r - 4)
        else:
            # Prázdny rám s otáznikom — jediný vizuál pre zamknuté
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            surf.fill((25, 18, 10, 180))
            self.screen.blit(surf, rect.topleft)
            pygame.draw.rect(self.screen, (90, 80, 65), rect, width=2, border_radius=6)
            q_font = get_font(int(h * 0.4))
            q_surf = q_font.render("?", True, (90, 80, 65))
            self.screen.blit(q_surf, q_surf.get_rect(center=(cx, cy)))

    def _draw_row_text(self, name: str, description: str, y: int,
                       unlocked: bool, icon_slot_w: int, hidden: bool = False):
        text_x = self.PANEL_X + icon_slot_w
        text_max_w = self.PANEL_X + self.PANEL_W - 30 - text_x

        name_color = COLOR_GOLD if unlocked else (160, 150, 135)
        name_surf = self.font_name.render(name, True, name_color)
        self.screen.blit(name_surf, (text_x, y + 30))

        # ← Zobraz popis ak je odomknuté ALEBO ak achievement nie je hidden
        show_description = unlocked or not hidden
        if show_description:
            desc_color = (225, 210, 185) if unlocked else (150, 140, 125)
            desc_lines = self._wrap_text(description, self.font_desc, text_max_w)
            line_h = self.font_desc.get_height() + 2
            for i, line in enumerate(desc_lines[:2]):
                line_surf = self.font_desc.render(line, True, desc_color)
                self.screen.blit(line_surf, (text_x, y + 66 + i * line_h))

    def _wrap_text(self, text: str, font, max_width: int) -> list[str]:
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