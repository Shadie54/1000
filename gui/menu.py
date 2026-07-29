# gui/menu.py

import pygame
import sys
import random
import os
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_WHITE, COLOR_GOLD, COLOR_GRAY,
    COLOR_BUTTON_PRIMARY, COLOR_BUTTON_SECONDARY,
    FONT_SIZE_LARGE, FONT_SIZE_MEDIUM,
    BUTTON_RADIUS,
    CARDS_MEDIUM_PATH, CARD_SIZE_MEDIUM,
    SUITS, RANKS,
    get_font
)


class Menu:
    def __init__(self, screen: pygame.Surface, show_continue: bool = False):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.show_continue = show_continue

        self.font_button = get_font(FONT_SIZE_LARGE)
        self.font_medium = get_font(FONT_SIZE_MEDIUM)

        # Pozadie
        try:
            self.bg = pygame.image.load("assets/graphics/table.jpg").convert()
            self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except FileNotFoundError:
            self.bg = None

        # Logo
        try:
            self.logo = pygame.image.load("assets/graphics/1000.png").convert_alpha()
            logo_size = 280
            self.logo = pygame.transform.scale(self.logo, (logo_size, logo_size))
        except FileNotFoundError:
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
        start_y = SCREEN_HEIGHT // 2 - total_h // 2 + (120 if self.logo else 50)

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
            path = os.path.join(CARDS_MEDIUM_PATH, filename)
            try:
                img = pygame.image.load(path).convert_alpha()
                # Zmenši karty
                w, h = CARD_SIZE_MEDIUM
                scale = 0.8
                img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))

                # Náhodná rotácia
                angle = random.uniform(-35, 35)
                img = pygame.transform.rotate(img, angle)

                # Náhodná pozícia — vyhni sa stredu (kde sú tlačidlá)
                attempts = 0
                while attempts < 20:
                    x = random.randint(50, SCREEN_WIDTH - 200)
                    y = random.randint(50, SCREEN_HEIGHT - 200)

                    # Vyhni sa stredu obrazovky
                    cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
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

            except FileNotFoundError:
                continue

        return cards

    # ------------------------------------------------------------------
    # Hlavná slučka
    # ------------------------------------------------------------------

    def run(self) -> str:
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
        if self.bg:
            self.screen.blit(self.bg, (0, 0))
        else:
            self.screen.fill((45, 28, 15))

        # Tmavý overlay celá obrazovka
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        self.screen.blit(overlay, (0, 0))

        # Karty v pozadí
        for card in self.bg_cards:
            card["image"].set_alpha(250)
            self.screen.blit(card["image"], (card["x"], card["y"]))

        # Tmavý panel v strede — celá výška obrazovky
        center_overlay = pygame.Surface((500, SCREEN_HEIGHT), pygame.SRCALPHA)
        center_overlay.fill((0, 0, 0, 140))
        self.screen.blit(center_overlay, (SCREEN_WIDTH // 2 - 250, 0))

        self._draw_logo()
        self._draw_buttons()

    def _draw_logo(self):
        if self.logo:
            logo_rect = self.logo.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150)
            )
            self.screen.blit(self.logo, logo_rect)
        else:
            font_title = get_font(120)
            title = font_title.render("TISÍC", True, COLOR_GOLD)
            title_rect = title.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150)
            )
            # Tmavý podklad pod text
            pad = 20
            bg_rect = pygame.Rect(
                title_rect.x - pad, title_rect.y - pad,
                title_rect.width + pad * 2, title_rect.height + pad * 2
            )
            overlay = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (bg_rect.x, bg_rect.y))
            # Tieň
            shadow = font_title.render("TISÍC", True, (0, 0, 0))
            self.screen.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
            self.screen.blit(title, title_rect)

    def _draw_buttons(self):
        for btn in self.buttons:
            self._draw_button(btn)

    def _draw_button(self, btn: dict):
        rect = btn["rect"]
        color = btn["color"]

        alpha = 240 if btn["hover"] else 200
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((*color, alpha))
        self.screen.blit(overlay, (rect.x, rect.y))

        # Hover efekt
        if btn["hover"]:
            hover_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            hover_surf.fill((255, 255, 255, 25))
            self.screen.blit(hover_surf, (rect.x, rect.y))

        border_color = COLOR_GOLD if btn["hover"] else COLOR_GRAY
        pygame.draw.rect(
            self.screen, border_color,
            rect, width=2, border_radius=BUTTON_RADIUS
        )

        text_color = COLOR_GOLD if btn["hover"] else COLOR_WHITE
        text_surf = self.font_button.render(btn["label"], True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def __repr__(self) -> str:
        return "Menu()"