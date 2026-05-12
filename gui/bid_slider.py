# gui/bid_slider.py

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TABLE_CENTER_X, TABLE_CENTER_Y,
    CARD_SIZE_MEDIUM,
    COLOR_WHITE, COLOR_BLACK, COLOR_GOLD, COLOR_GRAY,
    COLOR_BUTTON_PRIMARY, COLOR_BUTTON_SECONDARY,
    FONT_SIZE_MEDIUM, FONT_SIZE_LARGE, FONT_SIZE_XLARGE,
    BUTTON_RADIUS, MIN_BID, BID_STEP, MAX_BID, get_font
)


class BidSlider:

    # ------------------------------------------------------------------
    # Inicializácia
    # ------------------------------------------------------------------

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_small = get_font(FONT_SIZE_MEDIUM)         # 24
        self.font_medium = get_font(FONT_SIZE_LARGE)         # 32
        self.font_large = get_font(FONT_SIZE_XLARGE)         # 48

        self.visible = False
        self.current_value = MIN_BID
        self.min_value = MIN_BID
        self.max_value = MAX_BID
        self.dragging = False

        # Panel rozmery
        self.panel_w = 460
        self.panel_h = 250
        self.panel_x = TABLE_CENTER_X - self.panel_w // 2
        self.panel_y = TABLE_CENTER_Y + CARD_SIZE_MEDIUM[1] // 2 - 130

        # Padding
        pad = 20

        # Slider track — horizontálny, v strede panelu
        self.track_h = 10
        btn_size = 50
        self.track_x = self.panel_x + pad + btn_size + 15
        self.track_w = self.panel_w - pad * 2 - btn_size * 2 - 30
        self.track_y = self.panel_y + 110

        # Handle
        self.handle_r = 16

        # Tlačidlá - / + (vľavo a vpravo od tracku)
        self.btn_minus = pygame.Rect(
            self.panel_x + pad,
            self.track_y - btn_size // 2,
            btn_size, btn_size
        )
        self.btn_plus = pygame.Rect(
            self.track_x + self.track_w + 15,
            self.track_y - btn_size // 2,
            btn_size, btn_size
        )

        # Tlačidlo Potvrdiť — široké, dole v paneli
        confirm_w = self.panel_w - pad * 4
        confirm_h = 50
        self.btn_confirm = pygame.Rect(
            self.panel_x + (self.panel_w - confirm_w) // 2,
            self.panel_y + self.panel_h - confirm_h - pad,
            confirm_w, confirm_h
        )

    # ------------------------------------------------------------------
    # Zobrazenie / skrytie
    # ------------------------------------------------------------------

    def show(self, min_value: int, current_value: int):
        self.visible = True
        self.min_value = min_value
        self.current_value = current_value

    def hide(self):
        self.visible = False
        self.dragging = False

    # ------------------------------------------------------------------
    # Udalosti
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if not self.visible:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            if self.btn_minus.collidepoint(pos):
                self.current_value = max(self.min_value, self.current_value - BID_STEP)
                return None

            if self.btn_plus.collidepoint(pos):
                self.current_value = min(self.max_value, self.current_value + BID_STEP)
                return None

            if self.btn_confirm.collidepoint(pos):
                return "confirm"

            if self._is_on_track(pos) or self._is_on_handle(pos):
                self.current_value = self._pos_to_value(pos[0])
                self.dragging = True
                return None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        if event.type == pygame.MOUSEMOTION and self.dragging:
            self.current_value = self._pos_to_value(event.pos[0])

        return None

    # ------------------------------------------------------------------
    # Pomocné metódy
    # ------------------------------------------------------------------

    def _handle_x(self) -> int:
        ratio = (self.current_value - self.min_value) / max(1, self.max_value - self.min_value)
        return int(self.track_x + ratio * self.track_w)

    def _pos_to_value(self, x: int) -> int:
        ratio = (x - self.track_x) / self.track_w
        ratio = max(0.0, min(1.0, ratio))
        raw = self.min_value + ratio * (self.max_value - self.min_value)
        stepped = round(raw / BID_STEP) * BID_STEP
        return max(self.min_value, min(self.max_value, stepped))

    def _is_on_track(self, pos: tuple) -> bool:
        x, y = pos
        return (self.track_x <= x <= self.track_x + self.track_w and
                abs(y - self.track_y) <= 15)

    def _is_on_handle(self, pos: tuple) -> bool:
        hx = self._handle_x()
        dx = pos[0] - hx
        dy = pos[1] - self.track_y
        return (dx ** 2 + dy ** 2) ** 0.5 <= self.handle_r + 5

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def draw(self):
        if not self.visible:
            return

        # Panel pozadie
        overlay = pygame.Surface((self.panel_w, self.panel_h), pygame.SRCALPHA)
        overlay.fill((15, 9, 4, 230))
        self.screen.blit(overlay, (self.panel_x, self.panel_y))
        pygame.draw.rect(
            self.screen, COLOR_GOLD,
            (self.panel_x, self.panel_y, self.panel_w, self.panel_h),
            width=2, border_radius=14
        )

        # Nadpis
        title_surf = self.font_small.render("NAVÝŠIŤ POVINNOSŤ", True, COLOR_GOLD)
        title_rect = title_surf.get_rect(
            centerx=self.panel_x + self.panel_w // 2,
            top=self.panel_y + 14
        )
        self.screen.blit(title_surf, title_rect)

        # Oddeľovacia čiara pod nadpisom
        pygame.draw.line(
            self.screen, COLOR_GOLD,
            (self.panel_x + 15, self.panel_y + 44),
            (self.panel_x + self.panel_w - 15, self.panel_y + 44),
            width=1
        )

        # Track pozadie
        pygame.draw.rect(
            self.screen, (60, 45, 30),
            (self.track_x, self.track_y - self.track_h // 2,
             self.track_w, self.track_h),
            border_radius=5
        )

        # Track výplň
        hx = self._handle_x()
        fill_w = hx - self.track_x
        if fill_w > 0:
            pygame.draw.rect(
                self.screen, COLOR_GOLD,
                (self.track_x, self.track_y - self.track_h // 2,
                 fill_w, self.track_h),
                border_radius=5
            )

        # Min / Max hodnoty pod trackom
        min_surf = self.font_small.render(str(self.min_value), True, COLOR_GRAY)
        self.screen.blit(min_surf, (self.track_x, self.track_y + 14))

        max_surf = self.font_small.render(str(self.max_value), True, COLOR_GRAY)
        max_rect = max_surf.get_rect(right=self.track_x + self.track_w)
        self.screen.blit(max_surf, (max_rect.x, self.track_y + 14))

        # Handle — dvojitý kruh
        pygame.draw.circle(self.screen, COLOR_GOLD, (hx, self.track_y), self.handle_r)
        pygame.draw.circle(self.screen, (15, 9, 4), (hx, self.track_y), self.handle_r - 5)
        pygame.draw.circle(self.screen, COLOR_GOLD, (hx, self.track_y), self.handle_r - 9)

        # Hodnota nad handle
        val_surf = self.font_medium.render(str(self.current_value), True, COLOR_WHITE)
        val_rect = val_surf.get_rect(
            centerx=hx,
            bottom=self.track_y - self.handle_r - 8
        )
        self.screen.blit(val_surf, val_rect)

        # Tlačidlo mínus
        self._draw_round_btn(self.btn_minus, "−")

        # Tlačidlo plus
        self._draw_round_btn(self.btn_plus, "+")

        # Tlačidlo Potvrdiť
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.btn_confirm.collidepoint(mouse_pos)
        alpha = 255 if is_hover else 210
        btn_overlay = pygame.Surface(
            (self.btn_confirm.width, self.btn_confirm.height), pygame.SRCALPHA
        )
        btn_overlay.fill((*COLOR_BUTTON_PRIMARY, alpha))
        self.screen.blit(btn_overlay, (self.btn_confirm.x, self.btn_confirm.y))
        pygame.draw.rect(
            self.screen, COLOR_WHITE if is_hover else COLOR_GOLD,
            self.btn_confirm, width=2, border_radius=BUTTON_RADIUS
        )
        confirm_surf = self.font_medium.render("Potvrdiť", True, COLOR_WHITE)
        self.screen.blit(confirm_surf, confirm_surf.get_rect(center=self.btn_confirm.center))

    def _draw_round_btn(self, rect: pygame.Rect, text: str):
        """Nakreslí okrúhle +/- tlačidlo."""
        mouse_pos = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mouse_pos)
        cx, cy = rect.center
        r = rect.width // 2

        color_fill = (100, 70, 30) if is_hover else (50, 35, 15)
        pygame.draw.circle(self.screen, color_fill, (cx, cy), r)
        pygame.draw.circle(self.screen, COLOR_GOLD, (cx, cy), r, width=2)

        surf = self.font_medium.render(text, True, COLOR_WHITE)
        self.screen.blit(surf, surf.get_rect(center=(cx, cy)))

    def __repr__(self) -> str:
        return f"BidSlider(value={self.current_value}, visible={self.visible})"