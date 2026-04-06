# gui/bid_slider.py

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TABLE_CENTER_X, TABLE_CENTER_Y,
    CARD_SIZE_MEDIUM,
    COLOR_WHITE, COLOR_BLACK, COLOR_GOLD, COLOR_GRAY,
    COLOR_BUTTON_PRIMARY, COLOR_BUTTON_SECONDARY,
    FONT_SIZE_MEDIUM, FONT_SIZE_LARGE,
    BUTTON_RADIUS, MIN_BID, BID_STEP, MAX_BID
)


class BidSlider:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.font_medium = pygame.font.SysFont(None, FONT_SIZE_MEDIUM)
        self.font_large = pygame.font.SysFont(None, FONT_SIZE_LARGE)

        self.visible = False
        self.current_value = MIN_BID
        self.min_value = MIN_BID
        self.max_value = MAX_BID
        self.dragging = False

        # Rozmery a pozície
        self.y = TABLE_CENTER_Y + CARD_SIZE_MEDIUM[1] // 2 + 15

        # Slider track
        self.track_x = TABLE_CENTER_X - 200
        self.track_w = 400
        self.track_h = 8
        self.track_y = self.y + 40

        # Handle (ťahateľný bod)
        self.handle_r = 14

        # Tlačidlá - / +
        btn_w = 45
        btn_h = 45
        self.btn_minus = pygame.Rect(
            self.track_x - btn_w - 15,
            self.track_y - btn_h // 2,
            btn_w, btn_h
        )
        self.btn_plus = pygame.Rect(
            self.track_x + self.track_w + 15,
            self.track_y - btn_h // 2,
            btn_w, btn_h
        )

        # Tlačidlo Potvrdiť
        self.btn_confirm = pygame.Rect(
            self.track_x + self.track_w + 75,
            self.track_y - btn_h // 2,
            160, btn_h
        )

    # ------------------------------------------------------------------
    # Zobrazenie / skrytie
    # ------------------------------------------------------------------

    def show(self, min_value: int, current_value: int):
        self.visible = True
        self.min_value = min_value
        self.current_value = current_value

    def hide(self):
        """Skryje slider."""
        self.visible = False
        self.dragging = False

    # ------------------------------------------------------------------
    # Udalosti
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """
        Spracuje udalosť.
        Vracia: "confirm" ak hráč potvrdil, None inak.
        """
        if not self.visible:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # Tlačidlo mínus
            if self.btn_minus.collidepoint(pos):
                self.current_value = max(
                    self.min_value,
                    self.current_value - BID_STEP
                )
                return None

            # Tlačidlo plus
            if self.btn_plus.collidepoint(pos):
                self.current_value = min(
                    self.max_value,
                    self.current_value + BID_STEP
                )
                return None

            # Tlačidlo Potvrdiť
            if self.btn_confirm.collidepoint(pos):
                return "confirm"

            # Klik na track — preskoč na pozíciu
            if self._is_on_track(pos):
                self.current_value = self._pos_to_value(pos[0])
                self.dragging = True
                return None

            # Klik na handle
            if self._is_on_handle(pos):
                self.dragging = True
                return None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        if event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.current_value = self._pos_to_value(event.pos[0])

        return None

    # ------------------------------------------------------------------
    # Pomocné metódy
    # ------------------------------------------------------------------

    def _handle_x(self) -> int:
        """Vráti X pozíciu handle podľa aktuálnej hodnoty."""
        ratio = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        return int(self.track_x + ratio * self.track_w)

    def _pos_to_value(self, x: int) -> int:
        """Prevedie X pozíciu na hodnotu zaokrúhlenú na BID_STEP."""
        ratio = (x - self.track_x) / self.track_w
        ratio = max(0.0, min(1.0, ratio))
        raw = self.min_value + ratio * (self.max_value - self.min_value)
        # Zaokrúhli na BID_STEP
        stepped = round(raw / BID_STEP) * BID_STEP
        return max(self.min_value, min(self.max_value, stepped))

    def _is_on_track(self, pos: tuple) -> bool:
        """Skontroluje či klik je na tracku."""
        x, y = pos
        return (self.track_x <= x <= self.track_x + self.track_w and
                abs(y - self.track_y) <= 15)

    def _is_on_handle(self, pos: tuple) -> bool:
        """Skontroluje či klik je na handle."""
        hx = self._handle_x()
        dx = pos[0] - hx
        dy = pos[1] - self.track_y
        return (dx ** 2 + dy ** 2) ** 0.5 <= self.handle_r + 5

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def draw(self):
        """Nakreslí slider."""
        if not self.visible:
            return

        # Pozadie
        bg_w = self.btn_confirm.right - self.btn_minus.left + 20
        bg_h = 90
        bg_x = self.btn_minus.left - 10
        bg_y = self.track_y - bg_h // 2

        overlay = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        overlay.fill((20, 12, 5, 200))
        self.screen.blit(overlay, (bg_x, bg_y))
        pygame.draw.rect(
            self.screen, COLOR_GOLD,
            (bg_x, bg_y, bg_w, bg_h),
            width=2, border_radius=10
        )

        # Track pozadie
        pygame.draw.rect(
            self.screen, COLOR_GRAY,
            (self.track_x, self.track_y - self.track_h // 2,
             self.track_w, self.track_h),
            border_radius=4
        )

        # Track výplň (od min po handle)
        hx = self._handle_x()
        fill_w = hx - self.track_x
        if fill_w > 0:
            pygame.draw.rect(
                self.screen, COLOR_GOLD,
                (self.track_x, self.track_y - self.track_h // 2,
                 fill_w, self.track_h),
                border_radius=4
            )

        # Handle
        pygame.draw.circle(
            self.screen, COLOR_GOLD,
            (hx, self.track_y), self.handle_r
        )
        pygame.draw.circle(
            self.screen, COLOR_WHITE,
            (hx, self.track_y), self.handle_r - 4
        )

        # Tlačidlo mínus
        self._draw_btn(self.btn_minus, "-")

        # Tlačidlo plus
        self._draw_btn(self.btn_plus, "+")

        # Aktuálna hodnota nad handle
        val_surf = self.font_large.render(
            str(self.current_value), True, COLOR_GOLD
        )
        val_rect = val_surf.get_rect(
            centerx=hx,
            bottom=self.track_y - self.handle_r - 4
        )
        self.screen.blit(val_surf, val_rect)

        # Tlačidlo Potvrdiť
        overlay_btn = pygame.Surface(
            (self.btn_confirm.width, self.btn_confirm.height),
            pygame.SRCALPHA
        )
        overlay_btn.fill((*COLOR_BUTTON_PRIMARY, 220))
        self.screen.blit(overlay_btn, (self.btn_confirm.x, self.btn_confirm.y))
        pygame.draw.rect(
            self.screen, COLOR_GOLD,
            self.btn_confirm, width=2, border_radius=BUTTON_RADIUS
        )
        confirm_surf = self.font_medium.render("Potvrdiť", True, COLOR_WHITE)
        confirm_rect = confirm_surf.get_rect(center=self.btn_confirm.center)
        self.screen.blit(confirm_surf, confirm_rect)

    def _draw_btn(self, rect: pygame.Rect, text: str):
        """Nakreslí - alebo + tlačidlo."""
        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((*COLOR_BUTTON_SECONDARY, 220))
        self.screen.blit(overlay, (rect.topleft))
        pygame.draw.rect(
            self.screen, COLOR_GOLD,
            rect, width=2, border_radius=BUTTON_RADIUS
        )
        surf = self.font_large.render(text, True, COLOR_WHITE)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def __repr__(self) -> str:
        return f"BidSlider(value={self.current_value}, visible={self.visible})"