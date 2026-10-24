# gui/menu.py

import pygame
from gui import display
import sys
import random
import os
from gui.canvas import draw_backdrop, draw_static
from config import (
    SCREEN_WIDTH,
    COLOR_WHITE, COLOR_GOLD, COLOR_GRAY,
    COLOR_BUTTON_PRIMARY, COLOR_BUTTON_SECONDARY,
    FONT_SIZE_LARGE, FONT_SIZE_MEDIUM,
    BUTTON_RADIUS,
    CARDS_MEDIUM_PATH, CARD_SIZE_MEDIUM,
    SUITS, RANKS,
)

TABLE_BG = "assets/graphics/table.jpg"
LOGO_PATH = "assets/graphics/tisic_logo.png"


class Menu:
    def __init__(self, screen: pygame.Surface, show_continue: bool = False):
        # `screen` (logický povrch) sa už nepoužíva — kreslí sa cez Canvas
        # priamo do okna v jeho rozlíšení (gui/display.py, gui/canvas.py).
        self.canvas = display.canvas()
        self.H = display.logical_height()
        self.clock = pygame.time.Clock()
        self.show_continue = show_continue

        self.font_button = self.canvas.font(FONT_SIZE_LARGE)
        self.font_medium = self.canvas.font(FONT_SIZE_MEDIUM)

        # Logo
        try:
            iw, ih = self.canvas.image_size(LOGO_PATH)
            logo_w = 500
            logo_h = int(logo_w * (ih / iw))
            self.logo = self.canvas.image(LOGO_PATH, (logo_w, logo_h), smooth=False)
        except (FileNotFoundError, pygame.error):
            self.logo = None

        # Náhodné karty v pozadí
        self.bg_cards = self._generate_bg_cards()

        # Tlačidlá
        btn_w = 300
        btn_h = 65
        center_x = SCREEN_WIDTH // 2

        buttons_data = []
        if show_continue:
            buttons_data.append(("Pokračovať", "continue", COLOR_BUTTON_PRIMARY))
        buttons_data.append(("Nová hra", "new_game", COLOR_BUTTON_PRIMARY))
        buttons_data.append(("Trofeje", "achievements", COLOR_BUTTON_SECONDARY))
        buttons_data.append(("Nastavenia", "settings", COLOR_BUTTON_SECONDARY))
        buttons_data.append(("Koniec", "quit", COLOR_BUTTON_SECONDARY))

        total_h = len(buttons_data) * (btn_h + 20) - 20
        start_y = self.H // 2 - total_h // 2 + (120 if self.logo else 50)

        self.buttons = []
        for i, (label, action, color) in enumerate(buttons_data):
            self.buttons.append({
                "label": label,
                "action": action,
                "rect": pygame.Rect(center_x - btn_w // 2, start_y + i * (btn_h + 20), btn_w, btn_h),
                "color": color,
                "hover": False
            })

    # ------------------------------------------------------------------
    # Náhodné karty v pozadí
    # ------------------------------------------------------------------

    def _generate_bg_cards(self) -> list[dict]:
        """Vygeneruje náhodné karty pre pozadie."""
        cards = []
        used_positions = []

        # Vyber 7 náhodných kariet
        card_names = [
            f"{suit}-{rank}.png"
            for suit in SUITS
            for rank in RANKS
        ]
        selected = random.sample(card_names, 12)

        for filename in selected:
            if not os.path.exists(os.path.join(CARDS_MEDIUM_PATH, filename)):
                continue
            try:
                # Zmenšená (0.8) a náhodne otočená karta
                w, h = CARD_SIZE_MEDIUM
                scale = 0.8
                angle = random.uniform(-35, 35)
                img = self.canvas.card(
                    filename, angle, (int(w * scale), int(h * scale)),
                    smooth=False).copy()

                # Náhodná pozícia — vyhni sa stredu (kde sú tlačidlá)
                attempts = 0
                while attempts < 20:
                    x = random.randint(50, SCREEN_WIDTH - 200)
                    y = random.randint(50, self.H - 200)

                    # Vyhni sa stredu obrazovky
                    cx, cy = SCREEN_WIDTH // 2, self.H // 2
                    if abs(x - cx) < 350 and abs(y - cy) < 300:
                        attempts += 1
                        continue

                    # Skontroluj či sa neprekrýva príliš s inými kartami
                    too_close = any(
                        abs(x - p[0]) < 120 and abs(y - p[1]) < 160
                        for p in used_positions
                    )
                    if too_close:
                        attempts += 1
                        continue

                    used_positions.append((x, y))
                    break

                # Polopriesvitnosť
                img.set_alpha(160)

                cards.append({
                    "image": img,
                    "x": x,
                    "y": y
                })

            except (FileNotFoundError, pygame.error):
                continue

        return cards

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

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        action = self._handle_click(event.pos)
                        if action:
                            return action

            self._update_hover(mouse_pos)
            self._draw()
            display.present()

    # ------------------------------------------------------------------
    # Udalosti
    # ------------------------------------------------------------------

    def _handle_click(self, pos: tuple[int, int]) -> str | None:
        for btn in self.buttons:
            if btn["rect"].collidepoint(pos):
                return btn["action"]
        return None

    def _update_hover(self, mouse_pos: tuple[int, int]):
        for btn in self.buttons:
            btn["hover"] = btn["rect"].collidepoint(mouse_pos)

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def _draw(self):
        # Všetko okrem tlačidiel (hover) je statické — kreslí sa raz
        draw_static(self, self.canvas, "menu", self._draw_static)
        self._draw_buttons()

    def _draw_static(self):
        c = self.canvas
        # Stôl cez celé okno (aj pásma) + tmavý overlay
        draw_backdrop(c, (0, 0, 0, 130), TABLE_BG)

        # Karty v pozadí
        for card in self.bg_cards:
            card["image"].set_alpha(250)
            c.blit(card["image"], (card["x"], card["y"]))

        # Tmavý panel v strede — celá výška obrazovky, zarovnaný so šírkou loga
        panel_w = max(560, self.logo.get_width() + 60) if self.logo else 560
        c.overlay((SCREEN_WIDTH // 2 - panel_w // 2, 0, panel_w, self.H),
                  (0, 0, 0, 140))

        self._draw_logo()

    def _draw_logo(self):
        if self.logo:
            logo_rect = self.logo.get_rect(
                centerx=SCREEN_WIDTH // 2,
                bottom=self.buttons[0]["rect"].top - 40  # ← relatívne k prvému tlačidlu
            )

            # Tmavý podklad pod logo
            pad = 20
            bg_rect = pygame.Rect(
                logo_rect.x - pad, logo_rect.y - pad,
                logo_rect.width + pad * 2, logo_rect.height + pad * 2
            )
            self.canvas.overlay(bg_rect, (0, 0, 0, 160))

            self.canvas.blit(self.logo, logo_rect)
        else:
            font_title = self.canvas.font(120)
            title = font_title.render("TISÍC", True, COLOR_GOLD)
            title_rect = title.get_rect(
                centerx=SCREEN_WIDTH // 2,
                bottom=self.buttons[0]["rect"].top - 40  # ← rovnaká logika pre fallback
            )
            pad = 20
            bg_rect = pygame.Rect(
                title_rect.x - pad, title_rect.y - pad,
                title_rect.width + pad * 2, title_rect.height + pad * 2
            )
            self.canvas.overlay(bg_rect, (0, 0, 0, 160))
            shadow = font_title.render("TISÍC", True, (0, 0, 0))
            self.canvas.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
            self.canvas.blit(title, title_rect)

    def _draw_buttons(self):
        for btn in self.buttons:
            self._draw_button(btn)

    def _draw_button(self, btn: dict):
        rect = btn["rect"]
        color = btn["color"]

        alpha = 240 if btn["hover"] else 200
        self.canvas.overlay(rect, (*color, alpha))

        # Hover efekt
        if btn["hover"]:
            self.canvas.overlay(rect, (255, 255, 255, 25))

        border_color = COLOR_GOLD if btn["hover"] else COLOR_GRAY
        self.canvas.rect(border_color, rect, width=2, border_radius=BUTTON_RADIUS)

        text_color = COLOR_GOLD if btn["hover"] else COLOR_WHITE
        text_surf = self.font_button.render(btn["label"], True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.canvas.blit(text_surf, text_rect)

    def __repr__(self) -> str:
        return "Menu()"