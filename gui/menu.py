# gui/menu.py
#
# Hlavné menu — grafický rework (2026-10-28, štýl z hry CHUJ, project doc
# 15_UI_STYLE_REWORK.md): tmavý stôl s mäkkým svetlom (gui/ui_style.py),
# logo na tmavej plakete so žiarou, karty len vľavo a vpravo s tieňom,
# tlačidlá v troch úrovniach dôležitosti.
#
# Všetko vrátane tlačidiel v pokojovom stave sa kreslí raz do statickej
# vrstvy (gui/canvas.py::draw_static); každú snímku sa len blitne a navrch
# sa dokreslí zvýraznenie tlačidla pod myšou (výkon pri 4K).

import math
import os
import random
import sys

import pygame

from gui import display
from gui.canvas import LSurf, draw_static
from gui import ui_style
from gui.ui_style import (
    BTN_RADIUS, BTN_BORDER_HOVER, BTN_TEXT_HOVER,
)
from config import (
    SCREEN_WIDTH,
    FONT_SIZE_LARGE,
    CARD_SIZE_MEDIUM,
    SUITS, RANKS,
)

LOGO_PATH = os.path.join("assets", "graphics", "tisic_logo.png")
LOGO_W = 560

# Karty v pozadí:
#   "pairs"  — hlášky (kráľ + horník) všetkých štyroch farieb ako vejáre,
#   "random" — náhodné karty vľavo a vpravo (ako v CHUJ).
BG_CARD_MODE = "pairs"
BG_CARD_SCALE = 0.8
CARD_SHADOW_OFFSET = (7, 10)       # logické px — svetlo zľava hore
CARD_SHADOW_ALPHA = 140
# Jemné "zostarnutie" bielej karty do krémova (násobenie farby) — karty na
# tmavom stole inak pôsobia príliš žiarivo.
CARD_TINT = (236, 226, 206)

# Hlášky: (farba, stred vejára v logických px pri 1080, uhol vejára).
# Zvislé pozície sa pri 16:10 roztiahnu podľa výšky.
PAIR_FANS = (
    ("heart", (330, 300), -12),
    ("acorn", (470, 770), 9),
    ("leaf", (1590, 290), 11),
    ("bell", (1450, 780), -8),
)
PAIR_SPREAD = 100                  # vzdialenosť stredov kariet vo vejári
PAIR_FAN_ANGLE = 8                 # ± uhol kariet okolo uhla vejára

# Náhodný režim (CHUJ)
BG_CARD_COUNT = 10
BG_CARD_SAFE_HALF_W = 310
BG_CARD_MARGIN = 30

# Tlačidlá
BTN_W, BTN_H, BTN_GAP = 340, 60, 16
LOGO_GAP = 48                      # medzera logo → prvé tlačidlo
# Úrovne tlačidiel (ui_style.BTN_TIERS): 1 = Pokračovať (bez rozohratej hry
# Nová hra), 2 = Nová hra pri zobrazenom Pokračovať, 3 = ostatné.

# Plaketa pod logom — vnútro ozdobného rámu (zlomky rozmeru tisic_logo.png
# 866×288: rám siaha od x≈12 po 854, y≈30 po 258, rohy zrezané ~24 px).
LOGO_PLATE = (14 / 866, 32 / 288, 852 / 866, 257 / 288, 26 / 866)
LOGO_PLATE_COLOR = (16, 11, 7)


class Menu:
    def __init__(self, screen: pygame.Surface, show_continue: bool = False):
        # `screen` (logický povrch) sa už nepoužíva — kreslí sa cez Canvas
        # priamo do okna v jeho rozlíšení (gui/display.py, gui/canvas.py).
        self.canvas = display.canvas()
        self.H = display.logical_height()
        self.clock = pygame.time.Clock()
        self.show_continue = show_continue

        self.font_button = self.canvas.font(FONT_SIZE_LARGE)

        try:
            iw, ih = self.canvas.image_size(LOGO_PATH)
            self.logo = self.canvas.image(LOGO_PATH, (LOGO_W, round(LOGO_W * ih / iw)))
        except (FileNotFoundError, pygame.error):
            self.logo = None

        buttons_data = []
        if show_continue:
            buttons_data.append(("Pokračovať", "continue"))
        buttons_data.append(("Nová hra", "new_game"))
        buttons_data.append(("Trofeje", "achievements"))
        buttons_data.append(("Nastavenia", "settings"))
        buttons_data.append(("Koniec", "quit"))

        # Blok logo + tlačidlá zvislo na strede okna
        step = BTN_H + BTN_GAP
        buttons_h = len(buttons_data) * step - BTN_GAP
        logo_h = (self.logo.get_height() + LOGO_GAP) if self.logo else 170
        start_y = (self.H - logo_h - buttons_h) // 2 + logo_h

        self.buttons = []
        for i, (label, action) in enumerate(buttons_data):
            tier = 1 if i == 0 else (2 if action == "new_game" else 3)
            self.buttons.append({
                "label": label,
                "action": action,
                "rect": pygame.Rect(SCREEN_WIDTH // 2 - BTN_W // 2,
                                    start_y + i * step, BTN_W, BTN_H),
                "tier": tier,
                "hover": False,
            })

        self.bg_cards = (self._pair_cards() if BG_CARD_MODE == "pairs"
                         else self._random_cards())

    # ------------------------------------------------------------------
    # Karty v pozadí
    # ------------------------------------------------------------------

    def _card(self, filename: str, angle: float) -> LSurf:
        w, h = CARD_SIZE_MEDIUM
        size = (int(w * BG_CARD_SCALE), int(h * BG_CARD_SCALE))
        img = self.canvas.card(filename, angle=angle, lsize=size).copy()
        img.phys.fill(CARD_TINT, special_flags=pygame.BLEND_RGB_MULT)
        return img

    def _pair_cards(self) -> list[dict]:
        """Hlášky (kráľ + horník) štyroch farieb ako malé vejáre — vľavo a
        vpravo od loga a tlačidiel."""
        cards = []
        stretch = self.H / 1080
        for suit, (cx, cy), base in PAIR_FANS:
            cy = round(cy * stretch)
            rad = math.radians(base)
            # Stredy kariet vo vejári: posun pozdĺž uhla vejára
            dx, dy = math.cos(rad) * PAIR_SPREAD / 2, -math.sin(rad) * PAIR_SPREAD / 2
            for rank, sign in (("king", -1), ("over", 1)):
                try:
                    img = self._card(f"{suit}-{rank}.png", base - sign * PAIR_FAN_ANGLE)
                except (FileNotFoundError, pygame.error):
                    continue
                rect = img.get_rect(center=(round(cx + sign * dx),
                                            round(cy + sign * dy)))
                cards.append({"image": img, "x": rect.x, "y": rect.y,
                              "shadow": self._card_shadow(img)})
        return cards

    def _random_cards(self) -> list[dict]:
        """Náhodne rozhodené karty striedavo vľavo a vpravo mimo stredu
        (mechanizmus z CHUJ)."""
        cards = []
        used = []
        names = [f"{s}-{r}.png" for s in SUITS for r in RANKS]
        width, height = SCREEN_WIDTH, self.H
        center_x = width // 2
        per_side = (BG_CARD_COUNT + 1) // 2
        for i, filename in enumerate(random.sample(names, BG_CARD_COUNT)):
            try:
                img = self._card(filename, random.uniform(-35, 35))
            except (FileNotFoundError, pygame.error):
                continue
            lw, lh = img.get_size()
            if i % 2 == 0:
                x_min, x_max = BG_CARD_MARGIN, center_x - BG_CARD_SAFE_HALF_W - lw
            else:
                x_min, x_max = center_x + BG_CARD_SAFE_HALF_W, width - BG_CARD_MARGIN - lw
            y_min, y_max = BG_CARD_MARGIN, height - BG_CARD_MARGIN - lh
            band = (y_max - y_min) / per_side
            slot = i // 2
            y_lo = max(y_min, round(y_min + (slot - 0.35) * band))
            y_hi = min(y_max, round(y_min + (slot + 1.35) * band))
            x, y = x_min, y_min
            for _ in range(20):
                x = random.randint(x_min, max(x_min, x_max))
                y = random.randint(y_lo, max(y_lo, y_hi))
                if not any(abs(x - p[0]) < 110 and abs(y - p[1]) < 170 for p in used):
                    break
            used.append((x, y))
            cards.append({"image": img, "x": x, "y": y,
                          "shadow": self._card_shadow(img)})
        return cards

    def _card_shadow(self, card: LSurf) -> tuple:
        """Mäkký tieň karty: čierna silueta s alfou karty, rozmazaná
        zmenšením a zväčšením (počíta sa raz pri otvorení menu).
        Vráti (LSurf, logický posun ľavého horného rohu voči karte)."""
        c = self.canvas
        src = card.phys
        k = 8                                   # miera rozmazania
        pad = max(4, round(14 * c.s))
        pw, ph = src.get_width() + 2 * pad, src.get_height() + 2 * pad
        sw, sh = max(1, pw // k), max(1, ph // k)
        small = pygame.Surface((sw, sh), pygame.SRCALPHA)
        small.blit(pygame.transform.smoothscale(
            src, (max(1, src.get_width() // k), max(1, src.get_height() // k))),
            (pad // k, pad // k))
        small.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGB_MIN)
        small.fill((255, 255, 255, CARD_SHADOW_ALPHA),
                   special_flags=pygame.BLEND_RGBA_MULT)
        blurred = pygame.transform.smoothscale(small, (pw, ph))
        shadow = LSurf(blurred, round(pw / c.s), round(ph / c.s))
        off = (CARD_SHADOW_OFFSET[0] - pad / c.s,
               CARD_SHADOW_OFFSET[1] - pad / c.s)
        return shadow, off

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
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = self._handle_click(event.pos)
                    if action:
                        return action

            self._update_hover(mouse_pos)
            self._draw()
            display.present()

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
        draw_static(self, self.canvas, "menu", self._draw_static)
        for btn in self.buttons:
            if btn["hover"]:
                self._draw_button_hover(btn)

    def _draw_static(self):
        """Pozadie, svetlo, karty, logo a pokojové tlačidlá."""
        c = self.canvas
        ui_style.draw_backdrop(c, center_shade=False)

        for card in self.bg_cards:
            shadow, (dx, dy) = card["shadow"]
            c.blit(shadow, (card["x"] + dx, card["y"] + dy))
            c.blit(card["image"], (card["x"], card["y"]))

        # Mäkké stmavenie stredu až NAD kartami — prípadný roh karty pri
        # strede splynie so šerom (bez ostrých hraníc pásu).
        ui_style.apply_center_shade(c.target)

        # Jemná zlatá žiara za hlavným tlačidlom
        ui_style.blit_soft_ellipse(c, self.buttons[0]["rect"].inflate(140, 70),
                                   (255, 190, 90), 40, additive=True)

        self._draw_logo()
        for btn in self.buttons:
            self._draw_button(btn)

    def _draw_logo(self):
        c = self.canvas
        bottom = self.buttons[0]["rect"].top - LOGO_GAP
        if self.logo:
            logo_rect = self.logo.get_rect(centerx=SCREEN_WIDTH // 2, bottom=bottom)
            self._draw_logo_plate(logo_rect)
            c.blit(self.logo, logo_rect)
        else:
            font_title = c.font(120)
            title = font_title.render("TISÍC", True, ui_style.GOLD)
            rect = title.get_rect(centerx=SCREEN_WIDTH // 2, bottom=bottom)
            c.blit(font_title.render("TISÍC", True, (0, 0, 0)), (rect.x + 3, rect.y + 3))
            c.blit(title, rect)

    def _draw_logo_plate(self, logo_rect: pygame.Rect):
        """Tmavá plaketa vo vnútri ozdobného rámu loga (zrezané rohy ako
        rám), pod ňou mäkký tieň a jemná teplá žiara."""
        c = self.canvas
        fx0, fy0, fx1, fy1, fcut = LOGO_PLATE
        x0 = logo_rect.x + fx0 * logo_rect.width
        y0 = logo_rect.y + fy0 * logo_rect.height
        x1 = logo_rect.x + fx1 * logo_rect.width
        y1 = logo_rect.y + fy1 * logo_rect.height
        cut = fcut * logo_rect.width
        points = [(x0 + cut, y0), (x1 - cut, y0), (x1, y0 + cut),
                  (x1, y1 - cut), (x1 - cut, y1), (x0 + cut, y1),
                  (x0, y1 - cut), (x0, y0 + cut)]

        glow_rect = pygame.Rect(round(x0) - 90, round(y0) - 70,
                                round(x1 - x0) + 180, round(y1 - y0) + 140)
        ui_style.blit_soft_ellipse(c, glow_rect, (255, 196, 100), 34, additive=True)
        shadow_rect = pygame.Rect(round(x0) - 24, round(y0) - 8,
                                  round(x1 - x0) + 48, round(y1 - y0) + 40)
        ui_style.blit_soft_ellipse(c, shadow_rect, (0, 0, 0), 150,
                                   additive=False, square=True)

        c.polygon(LOGO_PLATE_COLOR, points)
        c.overlay((x0 + cut, y0 + 2, x1 - x0 - 2 * cut, (y1 - y0) * 0.45),
                  (255, 220, 160, 9))

    def _draw_button(self, btn: dict):
        """Tlačidlo v pokojovom stave (kreslí sa do statickej vrstvy)."""
        ui_style.draw_button(self.canvas, btn["rect"], btn["label"],
                             self.font_button, tier=btn["tier"])

    def _draw_button_hover(self, btn: dict):
        """Zvýraznenie pod myšou — každú snímku NAD pokojové tlačidlo
        z vrstvy: presvetlenie, zlatý rám a zlatý text."""
        c = self.canvas
        rect = btn["rect"]
        c.overlay(rect, (255, 214, 140, 24), border_radius=BTN_RADIUS)
        c.rect(BTN_BORDER_HOVER, rect, width=2, border_radius=BTN_RADIUS)
        surf = self.font_button.render(btn["label"], True, BTN_TEXT_HOVER)
        c.blit(surf, surf.get_rect(center=rect.center))

    def __repr__(self) -> str:
        return "Menu()"
