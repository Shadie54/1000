# gui/bid_slider.py

import pygame
from gui import display

from gui import layout, ui_style
from config import (
    FONT_SIZE_MEDIUM, FONT_SIZE_LARGE, FONT_SIZE_XLARGE,
    MIN_BID, BID_STEP, MAX_BID
)

# Vzhľad (grafický rework 2026-10-28, gui/ui_style.py)
DIVIDER = (70, 54, 34)
TRACK_EMPTY = (52, 40, 26)


class BidSlider:

    # ------------------------------------------------------------------
    # Inicializácia
    # ------------------------------------------------------------------

    def __init__(self, canvas):
        # Kreslí cez Canvas; poloha panelu z gui/layout.py (stred stola).
        self.canvas = canvas
        self.font_small = canvas.font(FONT_SIZE_MEDIUM)         # 24
        self.font_medium = canvas.font(FONT_SIZE_LARGE)         # 32
        self.font_large = canvas.font(FONT_SIZE_XLARGE)         # 48

        self.visible = False
        self.current_value = MIN_BID
        self.min_value = MIN_BID
        self.max_value = MAX_BID
        self.dragging = False

        # Panel rozmery
        self.panel_w = 460
        self.panel_h = 250
        lay = layout.game()
        self.panel_x = lay.table_center[0] - self.panel_w // 2
        self.panel_y = lay.bid_panel_y

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
        c = self.canvas
        mouse = display.mouse_pos()

        # Panel (gui/ui_style.py, rework 2026-10-28) s nadpisom v strede
        panel = pygame.Rect(self.panel_x, self.panel_y, self.panel_w, self.panel_h)
        c.overlay(panel.move(0, 5), (0, 0, 0, 110), border_radius=ui_style.PANEL_RADIUS)
        ui_style.draw_panel(c, panel)
        title = self.font_small.render("NAVÝŠIŤ POVINNOSŤ", True, ui_style.GOLD)
        c.blit(title, title.get_rect(centerx=panel.centerx, top=panel.y + 14))
        c.line(DIVIDER, (panel.x + 24, panel.y + 48), (panel.right - 24, panel.y + 48), width=1)

        # Dráha posuvníka
        track = pygame.Rect(self.track_x, self.track_y - self.track_h // 2,
                            self.track_w, self.track_h)
        c.rect(TRACK_EMPTY, track, border_radius=5)
        hx = self._handle_x()
        if hx - self.track_x > 0:
            c.rect(ui_style.GOLD_SOFT, (track.x, track.y, hx - self.track_x, track.height),
                   border_radius=5)

        # Min / max pod dráhou
        min_surf = self.font_small.render(str(self.min_value), True, ui_style.TEXT_DIM)
        c.blit(min_surf, (self.track_x, self.track_y + 14))
        max_surf = self.font_small.render(str(self.max_value), True, ui_style.TEXT_DIM)
        c.blit(max_surf, max_surf.get_rect(right=self.track_x + self.track_w,
                                           top=self.track_y + 14))

        # Úchyt
        c.circle(ui_style.BTN_TEXT_HOVER if self.dragging else ui_style.GOLD,
                 (hx, self.track_y), self.handle_r)
        c.circle((40, 28, 14), (hx, self.track_y), self.handle_r, width=2)

        # Hodnota nad úchytom
        val = self.font_medium.render(str(self.current_value), True, ui_style.TEXT)
        c.blit(val, val.get_rect(centerx=hx, bottom=self.track_y - self.handle_r - 8))

        self._draw_round_btn(self.btn_minus, "−", mouse)
        self._draw_round_btn(self.btn_plus, "+", mouse)
        ui_style.draw_button(c, self.btn_confirm, "Potvrdiť", self.font_medium, 1,
                             self.btn_confirm.collidepoint(mouse))

    def _draw_round_btn(self, rect: pygame.Rect, text: str, mouse):
        """Okrúhle −/+ tlačidlo — medailón ako v stĺpci tlačidiel."""
        hover = rect.collidepoint(mouse)
        cx, cy = rect.center
        r = rect.width // 2
        c = self.canvas
        c.circle((0, 0, 0), (cx + 1, cy + 3), r)
        c.circle((52, 36, 18) if hover else (22, 14, 8), (cx, cy), r)
        c.circle(ui_style.BTN_BORDER_HOVER if hover else ui_style.GOLD, (cx, cy), r, width=2)
        surf = self.font_medium.render(text, True,
                                       ui_style.BTN_TEXT_HOVER if hover else ui_style.TEXT)
        c.blit(surf, surf.get_rect(center=(cx, cy)))

    def __repr__(self) -> str:
        return f"BidSlider(value={self.current_value}, visible={self.visible})"