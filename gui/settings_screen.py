# gui/settings_screen.py
#
# Nastavenia so záložkami (štýl prevzatý z hry CHUJ):
#   "Hra"        — panely Obtiažnosť počítačov, Smer hry (ČR/SR — miesta
#                  počítačov pri stole), Rýchlosť animácií
#                  (posuvník 0.5×–2.0×) a Pozadie stola (miniatúry so
#                  šípkami; zoznam sa číta z assets/graphics — stačí pridať
#                  súbor tableN.jpg a objaví sa sám),
#   "Zobrazenie" — režim (Celá obrazovka / Okno) a veľkosť okna. Po
#                  "Použiť" sa okno prepne hneď a hra sa 15 s pýta
#                  "Ponechať toto zobrazenie?" — bez potvrdenia sa vráti
#                  pôvodné. Do settings.json ("display") sa voľba zapíše
#                  až po Ponechať (uloží ju main.py po návrate do menu).
# Posledná otvorená záložka sa pamätá počas jedného spustenia hry.

import math
import os
import re
import sys

import pygame
from gui import display
from gui.canvas import draw_static
from gui import ui_style
from config import (
    SCREEN_WIDTH,
    COLOR_GREEN, COLOR_YELLOW, COLOR_RED,
    FONT_SIZE_SMALL, FONT_SIZE_LARGE, FONT_SIZE_MEDIUM,
    ANIMATION_SPEED_MIN, ANIMATION_SPEED_MAX, ANIMATION_SPEED_DEFAULT,
    PLAY_DIRECTION_DEFAULT,
)

# Smer hry — mení len miesta počítačov pri stole (gui/layout.py::seats)
DIRECTIONS = (("cw", "V smere hodinových ručičiek (ČR)"),
              ("ccw", "Proti smeru hodinových ručičiek (SR)"))

TABS = (("hra", "Hra"), ("zobrazenie", "Zobrazenie"))
_last_tab = "hra"

# Pás záložiek pod nadpisom (čiara pod nadpisom je na y 120)
TAB_TOP, TAB_W, TAB_H, TAB_GAP = 140, 240, 46, 16
CONTENT_TOP = 206          # začiatok panelov pod záložkami
PANEL_GAP = 14
# Farby doplnkov (k paletke gui/ui_style.py)
DIVIDER = (70, 54, 34)        # deliace čiary v paneloch
BORDER_DIM = (98, 76, 46)     # rám nevybraných prvkov
TRACK_EMPTY = (52, 40, 26)    # nevyplnená časť posuvníka

# Po prepnutí zobrazenia sa hra o toľko ms sama vráti k pôvodnému, ak
# hráč zmenu nepotvrdí (napr. okno sa mu zobrazilo mimo monitora).
CONFIRM_MS = 15000

# Pozadia stola sa nehardkódujú — prečítajú sa priamo z assets/graphics/
# podľa vzoru "table.jpg", "table1.jpg", "table2.jpg", ... Pridanie
# ďalšieho súboru (napr. table6.jpg) sa tak v Nastaveniach objaví
# automaticky, bez zásahu do kódu.
_BG_PATTERN = re.compile(r"^table(\d*)\.jpg$", re.IGNORECASE)
_BG_DIR = "assets/graphics"


def discover_table_backgrounds(graphics_dir: str = _BG_DIR) -> list[str]:
    """Zoznam pozadí stola z disku, zoradený table.jpg, table1.jpg, …
    Pri chybe vráti aspoň ["table.jpg"], aby Nastavenia nespadli."""
    try:
        names = os.listdir(graphics_dir)
    except OSError:
        return ["table.jpg"]
    matches = []
    for name in names:
        m = _BG_PATTERN.match(name)
        if m:
            matches.append((int(m.group(1)) if m.group(1) else 0, name))
    matches.sort(key=lambda pair: pair[0])
    found = [name for _, name in matches]
    return found if found else ["table.jpg"]


def bg_label(index: int) -> str:
    """Popisok miniatúry podľa poradia: Stôl 1, Stôl 2, … (rovnako ako
    doteraz — table.jpg je „Stôl 1“)."""
    return f"Stôl {index + 1}"


class SettingsScreen:
    def __init__(self, screen: pygame.Surface, settings: dict):
        # `screen` (povrch okna) sa nepoužíva — kreslí sa cez Canvas
        # priamo do okna v jeho rozlíšení (gui/display.py, gui/canvas.py).
        self.screen = screen
        self.canvas = display.canvas()
        self.active_tab = _last_tab
        H = self.H = display.logical_height()
        self.clock = pygame.time.Clock()
        self.settings = settings.copy()
        self.settings.setdefault("animation_speed", ANIMATION_SPEED_DEFAULT)
        self.settings.setdefault("play_direction", PLAY_DIRECTION_DEFAULT)

        self.font_title  = self.canvas.font(72)
        self.font_large  = self.canvas.font(FONT_SIZE_LARGE)
        self.font_medium = self.canvas.font(FONT_SIZE_MEDIUM)
        self.font_small  = self.canvas.font(FONT_SIZE_SMALL)

        self.difficulties = ["easy", "medium", "hard"]
        self.difficulty_labels = {"easy": "Ľahká", "medium": "Stredná", "hard": "Ťažká"}
        self.difficulty_colors = {"easy": COLOR_GREEN, "medium": COLOR_YELLOW, "hard": COLOR_RED}

        center_x = self.center_x = SCREEN_WIDTH // 2
        self.panel_width = 1000
        panel_x = self.panel_x = center_x - self.panel_width // 2

        # Pás záložiek
        tabs_w = len(TABS) * TAB_W + (len(TABS) - 1) * TAB_GAP
        tabs_x = center_x - tabs_w // 2
        self.tab_rects = {
            key: pygame.Rect(tabs_x + i * (TAB_W + TAB_GAP), TAB_TOP, TAB_W, TAB_H)
            for i, (key, _label) in enumerate(TABS)
        }
        self.tab_hover: str | None = None

        # --------------------------------------------------------------
        # Panel 1 — Obtiažnosť počítačov (popis a tlačidlá v riadku)
        # --------------------------------------------------------------
        btn_w, btn_h, btn_gap = 150, 52, 18
        row_side_pad, ai_top_pad, ai_row_h, ai_bottom_pad = 40, 65, 80, 20
        ai_rows = (("Počítač 1", "ai1_difficulty"), ("Počítač 2", "ai2_difficulty"))
        self.panel_ai = pygame.Rect(
            panel_x, CONTENT_TOP, self.panel_width,
            ai_top_pad + len(ai_rows) * ai_row_h + ai_bottom_pad)
        buttons_total_w = 3 * btn_w + 2 * btn_gap
        buttons_start_x = self.panel_ai.right - row_side_pad - buttons_total_w
        self.ai_label_x = self.panel_ai.left + row_side_pad
        self.ai_rows = []          # [(meno, kľúč v settings, tlačidlá)]
        for row, (name, key) in enumerate(ai_rows):
            row_top = self.panel_ai.top + ai_top_pad + row * ai_row_h
            row_y = row_top + (ai_row_h - btn_h) // 2
            buttons = [
                {"difficulty": diff, "key": key, "hover": False,
                 "rect": pygame.Rect(buttons_start_x + i * (btn_w + btn_gap),
                                     row_y, btn_w, btn_h)}
                for i, diff in enumerate(self.difficulties)
            ]
            self.ai_rows.append((name, key, buttons))
        # Spätná kompatibilita (testy, galéria)
        self.ai1_buttons = self.ai_rows[0][2]
        self.ai2_buttons = self.ai_rows[1][2]

        # --------------------------------------------------------------
        # Panel 2 — Smer hry (dve prepínacie tlačidlá)
        # --------------------------------------------------------------
        self.panel_dir = pygame.Rect(
            panel_x, self.panel_ai.bottom + PANEL_GAP, self.panel_width, 125)
        dw, dh, dgap = 440, 48, 30
        dx0 = center_x - (2 * dw + dgap) // 2
        self.dir_buttons = [
            {"value": value, "label": label, "hover": False,
             "rect": pygame.Rect(dx0 + i * (dw + dgap), self.panel_dir.top + 64, dw, dh)}
            for i, (value, label) in enumerate(DIRECTIONS)
        ]

        # --------------------------------------------------------------
        # Panel 3 — Rýchlosť animácií (posuvník)
        # --------------------------------------------------------------
        self.panel_anim = pygame.Rect(
            panel_x, self.panel_dir.bottom + PANEL_GAP, self.panel_width, 150)
        slider_pad = 80
        self.slider_rect = pygame.Rect(
            self.panel_anim.left + slider_pad, self.panel_anim.top + 95,
            self.panel_anim.width - slider_pad * 2, 6)
        self.slider_handle_radius = 13
        self.slider_dragging = False

        # --------------------------------------------------------------
        # Panel 4 — Pozadie stola (okno miniatúr posúvané šípkami)
        # --------------------------------------------------------------
        self.bg_options = discover_table_backgrounds()
        self.bg_labels = [bg_label(i) for i in range(len(self.bg_options))]
        thumb_w, thumb_h, thumb_gap = 150, 88, 16
        self.bg_thumbnails = {}
        self._load_thumbnails(thumb_w, thumb_h)

        self.bg_visible_count = min(5, len(self.bg_options))
        self.bg_max_scroll = max(0, len(self.bg_options) - self.bg_visible_count)
        bg_top_pad, bg_label_h, bg_bottom_pad = 62, 30, 14
        self.panel_bg = pygame.Rect(
            panel_x, self.panel_anim.bottom + PANEL_GAP, self.panel_width,
            bg_top_pad + thumb_h + bg_label_h + bg_bottom_pad)
        total_w = self.bg_visible_count * (thumb_w + thumb_gap) - thumb_gap
        thumb_start = center_x - total_w // 2
        thumb_y = self.panel_bg.top + bg_top_pad
        self.bg_rects = [
            pygame.Rect(thumb_start + i * (thumb_w + thumb_gap), thumb_y, thumb_w, thumb_h)
            for i in range(self.bg_visible_count)
        ]
        # Šípky — medzi okrajom panelu a oknom miniatúr
        arrow_cy = thumb_y + thumb_h // 2
        left_cx = (panel_x + thumb_start) // 2
        right_cx = (thumb_start + total_w + panel_x + self.panel_width) // 2
        self.bg_arrow_left = {"rect": pygame.Rect(left_cx - 18, arrow_cy - 28, 36, 56),
                              "center": (left_cx, arrow_cy), "hover": False}
        self.bg_arrow_right = {"rect": pygame.Rect(right_cx - 18, arrow_cy - 28, 36, 56),
                               "center": (right_cx, arrow_cy), "hover": False}
        # Okno sa posunie tak, aby bolo hneď vidno vybrané pozadie
        current_bg = self.settings.get("table_bg", "table.jpg")
        self.bg_scroll = 0
        if current_bg in self.bg_options:
            idx = self.bg_options.index(current_bg)
            if idx >= self.bg_visible_count:
                self.bg_scroll = min(idx - (self.bg_visible_count - 1),
                                     self.bg_max_scroll)

        # Tlačidlo späť
        self.back_button = {
            "rect":  pygame.Rect(center_x - 150, H - 80, 300, 55),
            "hover": False
        }

        self._init_display_tab()

    # ------------------------------------------------------------------
    # Záložka Zobrazenie — rozloženie a stav výberu
    # ------------------------------------------------------------------

    def _init_display_tab(self):
        mode = display.current_mode()
        self.window_sizes = display.window_sizes()
        cx = self.center_x

        # Panel režim (Celá obrazovka / Okno)
        self.panel_mode = pygame.Rect(self.panel_x, CONTENT_TOP, self.panel_width, 230)
        bw, bh, bgap = 320, 56, 30
        x0 = cx - (2 * bw + bgap) // 2
        by = self.panel_mode.top + 75
        self.mode_buttons = [
            {"windowed": False, "label": "Celá obrazovka",
             "rect": pygame.Rect(x0, by, bw, bh), "hover": False},
            {"windowed": True, "label": "Okno",
             "rect": pygame.Rect(x0 + bw + bgap, by, bw, bh), "hover": False},
        ]

        # Panel veľkosť okna — mriežka po 4 (len v režime Okno)
        cols, sw, sh, sgap, row_h = 4, 200, 52, 18, 70
        rows = max(1, math.ceil(len(self.window_sizes) / cols))
        self.panel_size = pygame.Rect(self.panel_x, self.panel_mode.bottom + PANEL_GAP,
                                      self.panel_width, 65 + rows * row_h + 20)
        self.size_buttons = []
        for i, size in enumerate(self.window_sizes):
            r, c = divmod(i, cols)
            in_row = min(cols, len(self.window_sizes) - r * cols)
            row_w = in_row * sw + (in_row - 1) * sgap
            x = cx - row_w // 2 + c * (sw + sgap)
            y = self.panel_size.top + 65 + r * row_h + (row_h - sh) // 2
            self.size_buttons.append(
                {"size": size, "rect": pygame.Rect(x, y, sw, sh), "hover": False})

        # "Použiť" — pod posledným viditeľným panelom
        self._apply_rect_full = pygame.Rect(cx - 150, self.panel_mode.bottom + 30, 300, 56)
        self._apply_rect_window = pygame.Rect(cx - 150, self.panel_size.bottom + 30, 300, 56)
        self.apply_hover = False

        # Výber čakajúci na "Použiť"
        self.pending_windowed = mode.windowed and bool(self.window_sizes)
        self.pending_size = self._initial_window_size(mode)

        # Potvrdzovací dialóg po prepnutí: {"old": DisplayMode, "deadline": ms}
        self.confirm: dict | None = None
        cy = self.H // 2
        self.confirm_panel = pygame.Rect(cx - 380, cy - 150, 760, 300)
        self.confirm_keep = pygame.Rect(cx - 250, cy + 50, 230, 56)
        self.confirm_revert = pygame.Rect(cx + 20, cy + 50, 230, 56)
        self.confirm_hover: str | None = None

    def _initial_window_size(self, mode) -> tuple[int, int] | None:
        """Veľkosť okna predvolená v mriežke: aktuálne okno, inak
        zapamätaná veľkosť zo settings.json, inak najväčšia, čo sa zmestí."""
        if mode.windowed and (mode.width, mode.height) in self.window_sizes:
            return (mode.width, mode.height)
        saved = self.settings.get("display")
        if isinstance(saved, dict):
            try:
                size = (int(saved["width"]), int(saved["height"]))
            except (KeyError, TypeError, ValueError):
                size = None
            if size in self.window_sizes:
                return size
        return self.window_sizes[-1] if self.window_sizes else None

    def _apply_rect(self) -> pygame.Rect:
        return self._apply_rect_window if self.pending_windowed \
            else self._apply_rect_full

    def _display_changed(self) -> bool:
        """Líši sa výber od aktuálneho zobrazenia? (inak je Použiť sivé)"""
        mode = display.current_mode()
        if self.pending_windowed != mode.windowed:
            return True
        if self.pending_windowed:
            return self.pending_size != (mode.width, mode.height)
        return (mode.width, mode.height) != display.desktop_size()

    # ------------------------------------------------------------------
    # Prepnutie zobrazenia za behu + potvrdenie
    # ------------------------------------------------------------------

    def _rebuild(self):
        """Po zmene okna: nový Canvas (mierka), fonty, miniatúry aj
        rozloženie podľa novej logickej výšky — stav výberu ostáva."""
        keep = (self.settings, self.active_tab, self.pending_windowed,
                self.pending_size, self.bg_scroll)
        self._static_layer = None
        self.__init__(display.get_surface(), self.settings)
        (self.settings, self.active_tab, self.pending_windowed,
         self.pending_size, self.bg_scroll) = keep

    def _apply_display(self):
        old = display.current_mode()
        if self.pending_windowed and self.pending_size:
            w, h = self.pending_size
            new = display.DisplayMode(w, h, True, "settings")
        else:
            new = display.fullscreen_mode()
        display.apply_mode(new)
        self._rebuild()
        self.confirm = {"old": old,
                        "deadline": pygame.time.get_ticks() + CONFIRM_MS}

    def _confirm_keep(self):
        """Ponechať — až teraz sa voľba zapíše (main.py uloží settings)."""
        entry = {"mode": "window" if self.pending_windowed else "borderless"}
        if self.pending_size:
            # Veľkosť okna sa pamätá aj pri celej obrazovke — po návrate
            # do režimu Okno je predvolená.
            entry["width"], entry["height"] = self.pending_size
        self.settings["display"] = entry
        self.confirm = None

    def _confirm_revert(self):
        old = self.confirm["old"]
        display.apply_mode(old)
        self._rebuild()
        mode = display.current_mode()
        self.pending_windowed = mode.windowed and bool(self.window_sizes)
        self.pending_size = self._initial_window_size(mode)
        self.confirm = None

    def _confirm_seconds_left(self) -> int:
        left = self.confirm["deadline"] - pygame.time.get_ticks()
        return max(0, math.ceil(left / 1000))

    # ------------------------------------------------------------------
    # Miniatúry
    # ------------------------------------------------------------------

    def _load_thumbnails(self, w: int, h: int):
        """Miniatúry v rozmere rámika (w×h) so zaoblenými rohmi —
        pripravené raz, nie každú snímku."""
        c = self.canvas
        for fname in self.bg_options:
            try:
                thumb = c.image(f"{_BG_DIR}/{fname}", (w, h), alpha=False)
            except (FileNotFoundError, pygame.error):
                self.bg_thumbnails[fname] = None
                continue
            clipped = c.new_surface((w, h))
            pw, ph = clipped.phys.get_size()
            pygame.draw.rect(clipped.phys, (255, 255, 255, 255),
                             (0, 0, pw, ph), border_radius=round(6 * c.s))
            clipped.phys.blit(thumb.phys, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            self.bg_thumbnails[fname] = clipped

    # ------------------------------------------------------------------
    # Hlavná slučka
    # ------------------------------------------------------------------

    def run(self) -> dict:
        while True:
            self.clock.tick(60)

            if self.confirm is not None:
                self._run_confirm_events()
                if (self.confirm is not None
                        and self._confirm_seconds_left() == 0):
                    self._confirm_revert()
                self._update_hover(display.mouse_pos())
                self._draw()
                display.present()
                continue

            mouse_pos = display.mouse_pos()
            for event in display.get_events():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return self.settings
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.active_tab == "hra" and self._slider_hit(event.pos):
                        self.slider_dragging = True
                        self._update_slider_from_pos(event.pos[0])
                    elif self._handle_click(event.pos) == "back":
                        return self.settings
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.slider_dragging = False
                if event.type == pygame.MOUSEMOTION and self.slider_dragging:
                    self._update_slider_from_pos(event.pos[0])

            self._update_hover(mouse_pos)
            self._draw()
            display.present()

    def _run_confirm_events(self):
        """Udalosti počas dialógu "Ponechať toto zobrazenie?" — Enter =
        ponechať, Esc = vrátiť; ostatné klikanie je zablokované."""
        for event in display.get_events():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._confirm_keep()
                    return
                if event.key == pygame.K_ESCAPE:
                    self._confirm_revert()
                    return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.confirm_keep.collidepoint(event.pos):
                    self._confirm_keep()
                    return
                if self.confirm_revert.collidepoint(event.pos):
                    self._confirm_revert()
                    return

    # ------------------------------------------------------------------
    # Posuvník — rýchlosť animácií
    # ------------------------------------------------------------------

    def _slider_hit(self, pos) -> bool:
        """Rozšírená plocha okolo dráhy posuvníka (ľahšie sa trafí)."""
        return self.slider_rect.inflate(20, self.slider_handle_radius * 3).collidepoint(pos)

    def _update_slider_from_pos(self, mouse_x: int):
        frac = (mouse_x - self.slider_rect.left) / self.slider_rect.width
        frac = max(0.0, min(1.0, frac))
        value = ANIMATION_SPEED_MIN + frac * (ANIMATION_SPEED_MAX - ANIMATION_SPEED_MIN)
        # Krok 0.1 — hodnota sa zobrazuje s jedným desatinným miestom
        self.settings["animation_speed"] = round(value, 1)

    def _slider_handle_pos(self) -> tuple[int, int]:
        value = self.settings.get("animation_speed", ANIMATION_SPEED_DEFAULT)
        frac = (value - ANIMATION_SPEED_MIN) / (ANIMATION_SPEED_MAX - ANIMATION_SPEED_MIN)
        frac = max(0.0, min(1.0, frac))
        return (self.slider_rect.left + int(frac * self.slider_rect.width),
                self.slider_rect.centery)

    # ------------------------------------------------------------------
    # Udalosti
    # ------------------------------------------------------------------

    def _handle_click(self, pos) -> str | None:
        global _last_tab
        for key, rect in self.tab_rects.items():
            if rect.collidepoint(pos):
                self.active_tab = _last_tab = key
                return None
        if self.back_button["rect"].collidepoint(pos):
            return "back"
        if self.active_tab == "zobrazenie":
            return self._handle_display_click(pos)

        for _name, key, buttons in self.ai_rows:
            for btn in buttons:
                if btn["rect"].collidepoint(pos):
                    self.settings[key] = btn["difficulty"]
                    return None
        for btn in self.dir_buttons:
            if btn["rect"].collidepoint(pos):
                self.settings["play_direction"] = btn["value"]
                return None
        if self.bg_arrow_left["rect"].collidepoint(pos):
            self.bg_scroll = max(0, self.bg_scroll - 1)
            return None
        if self.bg_arrow_right["rect"].collidepoint(pos):
            self.bg_scroll = min(self.bg_max_scroll, self.bg_scroll + 1)
            return None
        for i, rect in enumerate(self.bg_rects):
            idx = self.bg_scroll + i
            if idx < len(self.bg_options) and rect.collidepoint(pos):
                self.settings["table_bg"] = self.bg_options[idx]
                return None
        return None

    def _handle_display_click(self, pos) -> None:
        for btn in self.mode_buttons:
            if btn["rect"].collidepoint(pos):
                if btn["windowed"] and not self.window_sizes:
                    return None          # okno sa na tento monitor nezmestí
                self.pending_windowed = btn["windowed"]
                return None
        if self.pending_windowed:
            for btn in self.size_buttons:
                if btn["rect"].collidepoint(pos):
                    self.pending_size = btn["size"]
                    return None
        if self._apply_rect().collidepoint(pos) and self._display_changed():
            self._apply_display()
        return None

    def _update_hover(self, mouse_pos):
        for _name, _key, buttons in self.ai_rows:
            for btn in buttons:
                btn["hover"] = btn["rect"].collidepoint(mouse_pos)
        self.back_button["hover"] = self.back_button["rect"].collidepoint(mouse_pos)
        self.bg_arrow_left["hover"] = self.bg_arrow_left["rect"].collidepoint(mouse_pos)
        self.bg_arrow_right["hover"] = self.bg_arrow_right["rect"].collidepoint(mouse_pos)
        for btn in self.mode_buttons + self.size_buttons + self.dir_buttons:
            btn["hover"] = btn["rect"].collidepoint(mouse_pos)
        self.apply_hover = self._apply_rect().collidepoint(mouse_pos)
        self.confirm_hover = (
            "keep" if self.confirm_keep.collidepoint(mouse_pos) else
            "revert" if self.confirm_revert.collidepoint(mouse_pos) else None)
        self.tab_hover = next(
            (key for key, rect in self.tab_rects.items()
             if rect.collidepoint(mouse_pos)), None)

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def _draw(self):
        # Pozadie so stmavením a nadpis sú statické — kreslia sa raz
        draw_static(self, self.canvas, "settings", self._draw_static)
        self._draw_tabs()
        if self.active_tab == "zobrazenie":
            self._draw_display_tab()
        else:
            self._draw_game_tab()
        self._draw_back_button()
        if self.confirm is not None:
            self._draw_confirm()

    def _draw_static(self):
        # Vzhľad: gui/ui_style.py (grafický rework 2026-10-28, z CHUJ)
        ui_style.draw_backdrop(self.canvas)
        self._draw_title()

    def _draw_title(self):
        ui_style.draw_screen_title(self.canvas, "NASTAVENIA", self.font_title,
                                   (SCREEN_WIDTH // 2, 78), line_gap=42)

    def _draw_tabs(self):
        for key, label in TABS:
            active = key == self.active_tab
            hover = key == self.tab_hover and not active
            ui_style.draw_button(self.canvas, self.tab_rects[key], label,
                                 self.font_medium, 1 if active else 3, hover)

    def _draw_panel(self, rect: pygame.Rect, title: str):
        """Panel so zlatohnedým rámom a nadpisom (gui/ui_style.py)."""
        ui_style.draw_panel(self.canvas, rect, title, self.font_medium)

    # --- záložka Hra ----------------------------------------------------

    def _draw_game_tab(self):
        self._draw_panel(self.panel_ai, "OBTIAŽNOSŤ POČÍTAČOV")
        self._draw_ai_rows()
        self._draw_panel(self.panel_dir, "SMER HRY")
        current = self.settings.get("play_direction", PLAY_DIRECTION_DEFAULT)
        for btn in self.dir_buttons:
            self._draw_choice(btn["rect"], btn["label"],
                              selected=btn["value"] == current,
                              hover=btn["hover"], enabled=True)
        self._draw_panel(self.panel_anim, "RÝCHLOSŤ ANIMÁCIÍ")
        self._draw_speed_slider()
        self._draw_panel(self.panel_bg, "POZADIE STOLA")
        self._draw_bg_section()
        self._draw_bg_arrows()

    def _draw_ai_rows(self):
        c = self.canvas
        r = ui_style.BTN_RADIUS
        for row, (name, key, buttons) in enumerate(self.ai_rows):
            row_cy = buttons[0]["rect"].centery
            label = self.font_medium.render(name, True, ui_style.TEXT)
            c.blit(label, label.get_rect(midleft=(self.ai_label_x, row_cy)))
            if row > 0:
                y = buttons[0]["rect"].top - 14
                c.line(DIVIDER, (self.panel_ai.left + 24, y),
                       (self.panel_ai.right - 24, y), width=1)
            current = self.settings[key]
            for btn in buttons:
                diff = btn["difficulty"]
                is_selected = diff == current
                base = self.difficulty_colors[diff]
                # Farba obtiažnosti ostáva (zelená/žltá/červená nesú
                # význam), ale stlmená do tmavého štýlu: zvolená = farebná
                # výplň, ostatné tmavé (ako v CHUJ).
                if is_selected:
                    c.overlay(btn["rect"], (*base, 165), border_radius=r)
                    c.overlay(btn["rect"], (0, 0, 0, 60), border_radius=r)
                elif btn["hover"]:
                    c.overlay(btn["rect"], (*base, 70), border_radius=r)
                else:
                    c.overlay(btn["rect"], (27, 19, 12, 230), border_radius=r)
                c.rect(base if is_selected or btn["hover"] else BORDER_DIM,
                       btn["rect"], width=2, border_radius=r)
                text = self.font_medium.render(
                    self.difficulty_labels[diff], True,
                    (255, 246, 228) if is_selected else ui_style.TEXT)
                c.blit(text, text.get_rect(center=btn["rect"].center))

    def _draw_speed_slider(self):
        c = self.canvas
        track = self.slider_rect
        slow = self.font_small.render("Pomalšie", True, ui_style.TEXT_DIM)
        fast = self.font_small.render("Rýchlejšie", True, ui_style.TEXT_DIM)
        c.blit(slow, (track.left, track.top - 28))
        c.blit(fast, fast.get_rect(topright=(track.right, track.top - 28)))
        c.line(TRACK_EMPTY, (track.left, track.centery),
               (track.right, track.centery), width=6)
        hx, hy = self._slider_handle_pos()
        c.line(ui_style.GOLD_SOFT, (track.left, track.centery), (hx, hy), width=6)
        c.circle(ui_style.BTN_TEXT_HOVER if self.slider_dragging else ui_style.GOLD,
                 (hx, hy), self.slider_handle_radius)
        c.circle((40, 28, 14), (hx, hy), self.slider_handle_radius, width=2)
        value = self.settings.get("animation_speed", ANIMATION_SPEED_DEFAULT)
        text = self.font_medium.render(f"{value:.1f}×", True, ui_style.TEXT)
        c.blit(text, text.get_rect(midtop=(self.center_x, track.bottom + 16)))

    def _draw_bg_section(self):
        current = self.settings.get("table_bg", "table.jpg")
        mouse = display.mouse_pos()
        for i, rect in enumerate(self.bg_rects):
            idx = self.bg_scroll + i
            if idx >= len(self.bg_options):
                continue
            fname = self.bg_options[idx]
            is_selected = fname == current
            is_hover = rect.collidepoint(mouse)
            thumb = self.bg_thumbnails.get(fname)
            if thumb:
                self.canvas.blit(thumb, rect)
            else:
                self.canvas.rect((40, 25, 10), rect)
            border = ui_style.GOLD if is_selected else (
                ui_style.BTN_BORDER_HOVER if is_hover else BORDER_DIM)
            self.canvas.rect(border, rect, width=3 if is_selected else 1,
                             border_radius=6)
            lbl = self.font_small.render(
                self.bg_labels[idx], True,
                ui_style.GOLD if is_selected else ui_style.TEXT)
            self.canvas.blit(lbl, lbl.get_rect(centerx=rect.centerx, top=rect.bottom + 6))

    def _draw_bg_arrows(self):
        """Šípky posúvajú okno miniatúr; stlmené, keď sa už nedá ďalej."""
        self._draw_bg_arrow(self.bg_arrow_left, "left", self.bg_scroll > 0)
        self._draw_bg_arrow(self.bg_arrow_right, "right",
                            self.bg_scroll < self.bg_max_scroll)

    def _draw_bg_arrow(self, arrow: dict, direction: str, enabled: bool):
        cx, cy = arrow["center"]
        color = BORDER_DIM if not enabled else (
            ui_style.BTN_TEXT_HOVER if arrow["hover"] else ui_style.GOLD)
        hw, hh = 10, 16
        if direction == "left":
            points = [(cx + hw, cy - hh), (cx + hw, cy + hh), (cx - hw, cy)]
        else:
            points = [(cx - hw, cy - hh), (cx - hw, cy + hh), (cx + hw, cy)]
        self.canvas.polygon(color, points)

    # --- záložka Zobrazenie ---------------------------------------------

    def _draw_display_tab(self):
        mode = display.current_mode()
        vp = display.viewport()
        c = self.canvas

        self._draw_panel(self.panel_mode, "REŽIM ZOBRAZENIA")
        for btn in self.mode_buttons:
            enabled = not btn["windowed"] or bool(self.window_sizes)
            self._draw_choice(btn["rect"], btn["label"],
                              selected=btn["windowed"] == self.pending_windowed,
                              hover=btn["hover"], enabled=enabled)
        dw, dh = display.desktop_size()
        if not self.window_sizes:
            hint = "Okno sa na tento monitor nezmestí (je menší než 1366 × 768)."
        elif self.pending_windowed:
            hint = "Okno s rámom — veľkosť zvoľ nižšie."
        else:
            hint = f"Bez rámu cez celú obrazovku, natívne rozlíšenie monitora {dw} × {dh}"
        surf = self.font_small.render(hint, True, ui_style.TEXT_DIM)
        c.blit(surf, surf.get_rect(centerx=self.center_x,
                                   centery=self.panel_mode.top + 158))
        current = (f"Aktuálne: {mode.width} × {mode.height}, "
                   + ("okno" if mode.windowed else "celá obrazovka")
                   + f", mierka obrazu {round(vp.scale * 100)} %")
        surf = self.font_small.render(current, True, ui_style.TEXT)
        c.blit(surf, surf.get_rect(centerx=self.center_x,
                                   centery=self.panel_mode.top + 196))

        if self.pending_windowed:
            self._draw_panel(self.panel_size, "VEĽKOSŤ OKNA")
            for btn in self.size_buttons:
                w, h = btn["size"]
                self._draw_choice(btn["rect"], f"{w} × {h}",
                                  selected=btn["size"] == self.pending_size,
                                  hover=btn["hover"], enabled=True)

        rect = self._apply_rect()
        enabled = self._display_changed() and self.confirm is None
        ui_style.draw_button(c, rect, "Použiť", self.font_large, 1,
                             self.apply_hover, enabled=enabled)

        if mode.source in ("cli", "safe"):
            note = self.font_small.render(
                "Hra je spustená s parametrom príkazového riadka — pri štarte "
                "má prednosť pred uloženým nastavením.", True, ui_style.TEXT_DIM)
            c.blit(note, note.get_rect(centerx=self.center_x, top=rect.bottom + 18))

    def _draw_choice(self, rect: pygame.Rect, label: str, selected: bool,
                     hover: bool, enabled: bool):
        """Prepínacie tlačidlo (smer hry, režim, veľkosť okna): zvolené =
        úroveň 1, ostatné úroveň 3."""
        ui_style.draw_button(self.canvas, rect, label, self.font_medium,
                             1 if selected else 3, hover and not selected,
                             enabled=enabled, shadow=False)

    def _draw_confirm(self):
        """Dialóg "Ponechať toto zobrazenie?" s odpočtom návratu."""
        c = self.canvas
        c.overlay_window((0, 0, 0, 170))
        panel = self.confirm_panel
        ui_style.draw_panel(c, panel)
        title = self.font_large.render("Ponechať toto zobrazenie?", True, ui_style.GOLD)
        c.blit(title, title.get_rect(centerx=panel.centerx, top=panel.top + 40))
        secs = self._confirm_seconds_left()
        text = self.font_medium.render(
            f"Návrat k predchádzajúcemu zobrazeniu o {secs} s", True, ui_style.TEXT)
        c.blit(text, text.get_rect(centerx=panel.centerx, top=panel.top + 110))
        for key, rect, label, tier in (("keep", self.confirm_keep, "Ponechať", 1),
                                       ("revert", self.confirm_revert, "Vrátiť", 3)):
            ui_style.draw_button(c, rect, label, self.font_large, tier,
                                 self.confirm_hover == key)

    def _draw_back_button(self):
        ui_style.draw_button(self.canvas, self.back_button["rect"], "← Späť",
                             self.font_large, 3, self.back_button["hover"])

    def __repr__(self):
        return "SettingsScreen()"
