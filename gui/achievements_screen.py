# gui/achievements_screen.py

import pygame
from gui import display
import os
import sys
from gui.canvas import draw_static
from gui import ui_style
from config import SCREEN_WIDTH, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE

# Vzhľad (grafický rework 2026-10-28, gui/ui_style.py)
DIVIDER = (70, 54, 34)
BORDER_DIM = (90, 72, 48)
HEADER_H = 140          # nadpis + ozdobná linka + počet odomknutých
from achievements.definitions import ACHIEVEMENTS
from achievements.storage import load_achievements


class AchievementsScreen:
    """Zoznam trofejí. Dva spôsoby použitia:
      - z menu: run() — vlastná slučka, pozadie stola (draw_backdrop),
      - počas hry: AchievementsOverlay nižšie — handle_event() + draw_overlay()
        z hernej slučky, pod panelom je stmavená rozohratá hra."""

    def __init__(self, screen: pygame.Surface | None = None, data: dict | None = None):
        # `screen` (logický povrch) sa už nepoužíva — kreslí sa cez Canvas.
        # data: živé dáta trofejí (AchievementTracker.data); inak zo súboru.
        self.canvas = display.canvas()
        self.H = display.logical_height()
        self.clock = pygame.time.Clock()

        self.font_title = self.canvas.font(FONT_SIZE_LARGE + 8)
        self.font_large = self.canvas.font(FONT_SIZE_LARGE)
        self.font_name  = self.canvas.font(FONT_SIZE_MEDIUM + 4)
        self.font_desc  = self.canvas.font(FONT_SIZE_MEDIUM - 2)

        # Trofej ikony — jednotná výška pre single aj group, líši sa len šírka
        self.icon_w, self.icon_h = 70, 113          # single riadky
        self.icon_w_small = 46                       # group riadky (rovnaká výška icon_h)

        # Cesty k ikonám trofejí (načítajú sa cez Canvas v potrebnej veľkosti)
        self.trophy_icons = {}
        for tier_name in ("bronze", "silver", "gold"):
            path = f"assets/graphics/trophy_{tier_name}.png"
            self.trophy_icons[tier_name] = path if os.path.exists(path) else None

        self.data = data if data is not None else load_achievements()
        self.scroll_offset = 0
        self.max_scroll = 0

        self.PAD = 30
        self.PANEL_X = 60
        self.PANEL_Y = 20
        self.PANEL_W = SCREEN_WIDTH - 120
        self.PANEL_H = self.H - 40

        # Vyhradený priestor pre tlačidlo späť (mimo scrollovateľnej oblasti)
        self.BACK_AREA_H = 80
        self.CONTENT_Y = self.PANEL_Y + HEADER_H
        self.CONTENT_H = self.PANEL_H - HEADER_H - self.BACK_AREA_H

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
            mouse_pos = display.mouse_pos()

            for event in display.get_events():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.handle_event(event) == "close":
                    return

            self._draw(mouse_pos)
            display.present()

    def handle_event(self, event) -> str | None:
        """Klávesy a myš zoznamu trofejí. Vráti "close" pri Esc / Späť."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "close"
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.back_button.collidepoint(event.pos):
                return "close"
            if event.button == 4:
                self.scroll_offset = max(0, self.scroll_offset - 50)
            if event.button == 5:
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 50)
        return None

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def _draw(self, mouse_pos):
        # Všetko okrem tlačidla Späť (hover) — prekreslí sa len pri scrolle
        draw_static(self, self.canvas, ("trofeje", self.scroll_offset),
                    self._draw_static)
        self._draw_back_button(mouse_pos)

    def _draw_static(self):
        ui_style.draw_backdrop(self.canvas)
        self._draw_content()

    def _draw_content(self):
        self._draw_panel_bg()
        self._draw_title()
        self._draw_progress()
        self._draw_rows()

    def draw_overlay(self, mouse_pos):
        """Kreslenie počas hry — cez stmavenú hernú obrazovku. Pod panelom
        ostáva obraz hry z chvíle otvorenia (vidno z neho len okraje), aby
        sa celý zoznam nekreslil každú snímku (pri 4K ~40 ms)."""
        if getattr(self, "_game_frame", None) is None:
            # Volá sa na konci kreslenia hernej snímky — okno ju práve obsahuje
            self._game_frame = self.canvas.target.copy()
        draw_static(self, self.canvas, ("hra", self.scroll_offset),
                    self._draw_over_game)
        self._draw_back_button(mouse_pos)

    def _draw_over_game(self):
        self.canvas.target.blit(self._game_frame, (0, 0))
        self.canvas.overlay_window((0, 0, 0, 200))
        self._draw_content()

    def _draw_panel_bg(self):
        panel = pygame.Rect(self.PANEL_X, self.PANEL_Y, self.PANEL_W, self.PANEL_H)
        ui_style.draw_panel(self.canvas, panel)
        line_y = self.PANEL_Y + self.PANEL_H - self.BACK_AREA_H
        self.canvas.line(DIVIDER, (self.PANEL_X + 24, line_y),
                         (self.PANEL_X + self.PANEL_W - 24, line_y), width=1)

    def _draw_title(self):
        ui_style.draw_screen_title(self.canvas, "TROFEJE", self.font_title,
                                   (SCREEN_WIDTH // 2, self.PANEL_Y + 44),
                                   line_half_w=220, line_gap=36)

    def _draw_progress(self):
        total = len(ACHIEVEMENTS)
        unlocked = sum(1 for v in self.data["unlocked"].values() if v)
        surf = self.font_desc.render(f"Odomknuté {unlocked} z {total}", True,
                                     ui_style.TEXT_DIM)
        self.canvas.blit(surf, surf.get_rect(centerx=SCREEN_WIDTH // 2,
                                             centery=self.PANEL_Y + 112))

    def _draw_rows(self):
        clip_rect = pygame.Rect(
            self.PANEL_X, self.CONTENT_Y, self.PANEL_W, self.CONTENT_H
        )
        old_clip = self.canvas.get_clip()
        self.canvas.set_clip(clip_rect)

        y = self.CONTENT_Y - self.scroll_offset

        for row in self.rows:
            if y + self.row_h >= self.CONTENT_Y and y <= self.CONTENT_Y + self.CONTENT_H:
                if row["type"] == "single":
                    self._draw_single_row(row["item"], y)
                else:
                    self._draw_group_row(row["items"], y)
            y += self.row_h

        self.canvas.set_clip(old_clip)

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
        color = (52, 37, 18, 200) if unlocked else (20, 14, 9, 170)
        self.canvas.overlay(rect, color, border_radius=10)
        border = ui_style.GOLD_SOFT if unlocked else BORDER_DIM
        self.canvas.rect(border, rect, width=1, border_radius=10)

    def _draw_trophy_slot(self, tier_name: str, cx: int, cy: int,
                          unlocked: bool, w: int, h: int):
        rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)

        if unlocked:
            icon_path = self.trophy_icons.get(tier_name)
            if icon_path:
                scaled = self.canvas.image(icon_path, (w, h), smooth=False)
                self.canvas.blit(scaled, rect.topleft)
                self.canvas.rect(ui_style.GOLD, rect, width=2, border_radius=6)
            else:
                r = min(w, h) // 2
                self.canvas.circle(ui_style.GOLD, (cx, cy), r)
                self.canvas.circle((15, 9, 4), (cx, cy), r - 4)
        else:
            # Prázdny rám s otáznikom — jediný vizuál pre zamknuté
            self.canvas.overlay(rect, (14, 10, 6, 200), border_radius=6)
            self.canvas.rect(BORDER_DIM, rect, width=2, border_radius=6)
            q_font = self.canvas.font(int(h * 0.4))
            q_surf = q_font.render("?", True, BORDER_DIM)
            self.canvas.blit(q_surf, q_surf.get_rect(center=(cx, cy)))

    def _draw_row_text(self, name: str, description: str, y: int,
                       unlocked: bool, icon_slot_w: int, hidden: bool = False):
        text_x = self.PANEL_X + icon_slot_w
        text_max_w = self.PANEL_X + self.PANEL_W - 30 - text_x

        name_color = ui_style.GOLD if unlocked else ui_style.TEXT_DIM
        name_surf = self.font_name.render(name, True, name_color)
        self.canvas.blit(name_surf, (text_x, y + 30))

        # ← Zobraz popis ak je odomknuté ALEBO ak achievement nie je hidden
        show_description = unlocked or not hidden
        if show_description:
            desc_color = ui_style.TEXT if unlocked else ui_style.TEXT_DIM
            desc_lines = self._wrap_text(description, self.font_desc, text_max_w)
            line_h = self.font_desc.get_height() + 2
            for i, line in enumerate(desc_lines[:2]):
                line_surf = self.font_desc.render(line, True, desc_color)
                self.canvas.blit(line_surf, (text_x, y + 66 + i * line_h))

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
        ui_style.draw_button(self.canvas, self.back_button, "← Späť",
                             self.font_large, 3,
                             self.back_button.collidepoint(mouse_pos))

    def __repr__(self):
        return "AchievementsScreen()"


class AchievementsOverlay:
    """Trofeje počas hry (tlačidlo Trofeje na hernej obrazovke) — rovnaký
    vzhľad ako obrazovka Trofeje v menu. Hra pod ním beží ďalej rovnako
    ako pod prehľadom Pravidlá."""

    def __init__(self, tracker=None):
        self.tracker = tracker
        self.view: AchievementsScreen | None = None

    @property
    def visible(self) -> bool:
        return self.view is not None

    @property
    def covers_screen(self) -> bool:
        """True keď už má obraz hry pod sebou — kreslí celé okno sám."""
        return getattr(self.view, "_game_frame", None) is not None

    def show(self):
        # Živé dáta trackera — trofej odomknutá v tejto hre je hneď vidieť
        data = self.tracker.data if self.tracker is not None else None
        self.view = AchievementsScreen(data=data)

    def hide(self):
        self.view = None

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()

    def handle_event(self, event) -> bool:
        """True = udalosť spracovaná (klik cez overlay sa do hry nedostane)."""
        if self.view is None or event.type == pygame.QUIT:
            return False
        if self.view.handle_event(event) == "close":
            self.hide()
            return True
        return event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN,
                              pygame.MOUSEBUTTONUP)

    def draw(self):
        if self.view is not None:
            self.view.draw_overlay(display.mouse_pos())