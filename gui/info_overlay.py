# gui/info_overlay.py

import os

import pygame

from gui import display
from config import (
    SCREEN_WIDTH,
    COLOR_WHITE, COLOR_GOLD, COLOR_GRAY,
    FONT_SIZE_SMALL, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE,
    CARDS_MEDIUM_PATH
)


class InfoOverlay:
    def __init__(self, canvas):
        # Kreslí cez Canvas; panel cez celú logickú výšku.
        self.canvas = canvas
        self.H = display.logical_height()
        self.visible = False
        self.active_tab = "bodovanie"

        self.font_small  = canvas.font(FONT_SIZE_SMALL)       # 18
        self.font_medium = canvas.font(FONT_SIZE_MEDIUM)      # 24
        self.font_large  = canvas.font(FONT_SIZE_LARGE)       # 32
        self.font_title  = canvas.font(FONT_SIZE_LARGE + 8)   # 40

        # ------------------------------------------------------------------
        # Konštanty layoutu
        # ------------------------------------------------------------------
        self.PAD       = 30
        self.PANEL_X   = 60
        self.PANEL_Y   = 20
        self.PANEL_W   = SCREEN_WIDTH  - 120
        self.PANEL_H   = self.H - 40
        self.INNER_X   = self.PANEL_X  + self.PAD
        self.INNER_W   = self.PANEL_W  - self.PAD * 2
        self.CONTENT_Y = self.PANEL_Y  + 130   # pod nadpisom a záložkami

        # Záložky
        tab_w, tab_h = 220, 44
        cx = SCREEN_WIDTH // 2
        self.tab_rects = {
            "bodovanie": pygame.Rect(cx - tab_w - 8, self.PANEL_Y + 72, tab_w, tab_h),
            "pravidla": pygame.Rect(cx + 8, self.PANEL_Y + 72, tab_w, tab_h),
        }

        # Tlačidlo zavrieť
        self.btn_close = pygame.Rect(
            self.PANEL_X + self.PANEL_W - 44,
            self.PANEL_Y + 10,
            36, 36
        )

    # ------------------------------------------------------------------
    # Verejné metódy
    # ------------------------------------------------------------------

    def show(self):    self.visible = True
    def hide(self):    self.visible = False
    def toggle(self):  self.visible = not self.visible

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_i):
                self.hide()
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_close.collidepoint(event.pos):
                self.hide()
                return True
            for key, rect in self.tab_rects.items():
                if rect.collidepoint(event.pos):
                    self.active_tab = key
                    return True
            return True  # blokuj klik cez overlay
        return False

    # ------------------------------------------------------------------
    # Kreslenie — hlavná metóda
    # ------------------------------------------------------------------

    def draw(self):
        if not self.visible:
            return

        # Tmavý backdrop (cez celé okno aj pásma)
        self.canvas.overlay_window((0, 0, 0, 220))

        # Panel
        self._draw_panel_bg()

        # Nadpis
        title = self.font_title.render("PRAVIDLÁ A BODOVANIE", True, COLOR_GOLD)
        self.canvas.blit(title, title.get_rect(
            centerx=SCREEN_WIDTH // 2, top=self.PANEL_Y + 14
        ))

        # Záložky
        self._draw_tabs()

        # Tlačidlo zavrieť
        self._draw_close_btn()

        # Obsah
        if self.active_tab == "bodovanie":
            self._draw_bodovanie()
        else:
            self._draw_pravidla()

    # ------------------------------------------------------------------
    # Panel a záložky
    # ------------------------------------------------------------------

    def _draw_panel_bg(self):
        self.canvas.overlay((self.PANEL_X, self.PANEL_Y, self.PANEL_W, self.PANEL_H),
                            (15, 9, 4, 245))
        self.canvas.rect(
            COLOR_GOLD,
            (self.PANEL_X, self.PANEL_Y, self.PANEL_W, self.PANEL_H),
            width=2, border_radius=14
        )

    def _draw_tabs(self):
        labels = {"bodovanie": "Bodovanie", "pravidla": "Pravidlá"}
        for key, rect in self.tab_rects.items():
            active = self.active_tab == key
            bg = (45, 30, 10) if active else (20, 12, 5)
            self.canvas.rect(bg, rect, border_radius=8)
            border = COLOR_GOLD if active else COLOR_GRAY
            self.canvas.rect(border, rect, width=2, border_radius=8)
            color = COLOR_GOLD if active else COLOR_GRAY
            surf = self.font_medium.render(labels[key], True, color)
            self.canvas.blit(surf, surf.get_rect(center=rect.center))

    def _draw_close_btn(self):
        self.canvas.rect((50, 30, 10), self.btn_close, border_radius=6)
        self.canvas.rect(COLOR_GOLD, self.btn_close, width=2, border_radius=6)
        surf = self.font_medium.render("X", True, COLOR_WHITE)
        self.canvas.blit(surf, surf.get_rect(center=self.btn_close.center))

    # ------------------------------------------------------------------
    # Tab: Bodovanie
    # ------------------------------------------------------------------

    def _draw_bodovanie(self):
        y = self.CONTENT_Y

        # — Sekcia 1: Hodnoty kariet —
        self._section_title("HODNOTY KARIET", y)
        y += 36

        ranks  = ["ace", "ten", "king", "over", "under", "nine", "eight", "seven"]
        points = {"ace": 11, "ten": 10, "king": 4, "over": 3,
                  "under": 2, "nine": 0, "eight": 0, "seven": 0}

        card_w, card_h = 120, 194
        gap = 16
        total_w = len(ranks) * (card_w + gap) - gap
        cx = SCREEN_WIDTH // 2
        x0 = cx - total_w // 2

        for i, rank in enumerate(ranks):
            x = x0 + i * (card_w + gap)
            img = self._load_card("heart", rank, (card_w, card_h))
            if img:
                self.canvas.blit(img, (x, y))
            pts  = points[rank]
            col  = COLOR_GOLD if pts > 0 else COLOR_GRAY
            psurf = self.font_large.render(str(pts), True, col)
            self.canvas.blit(psurf, psurf.get_rect(
                centerx=x + card_w // 2, top=y + card_h + 14
            ))

        y += card_h + 60

        # Oddeľovač
        self._divider(y)
        y += 28

        # — Sekcia 2: Tromfy —
        self._section_title("TROMFY  (kráľ + horník rovnakej farby)", y)
        y += 48

        trump_data = [("acorn", 100), ("leaf", 80), ("bell", 60), ("heart", 40)]
        pair_w  = card_w * 2 + 10
        t_gap   = 60
        total_t = len(trump_data) * (pair_w + t_gap) - t_gap
        tx0     = cx - total_t // 2

        for i, (suit, pts) in enumerate(trump_data):
            x = tx0 + i * (pair_w + t_gap)
            for j, rank in enumerate(["king", "over"]):
                img = self._load_card(suit, rank, (card_w, card_h))
                if img:
                    self.canvas.blit(img, (x + j * (card_w + 10), y))
            psurf = self.font_title.render(str(pts), True, COLOR_GOLD)
            self.canvas.blit(psurf, psurf.get_rect(
                centerx=x + pair_w // 2, top=y + card_h + 14
            ))

    # ------------------------------------------------------------------
    # Tab: Pravidlá
    # ------------------------------------------------------------------

    def _draw_pravidla(self):
        sections = [
            ("CIEL HRY", [
                "Prvý hráč ktorý dosiahne 1000 bodov vyhráva.",
            ]),
            ("PRIEBEH KOLA", [
                "1.  Rozdanie — každý dostane 10 kariet, 2 idú do talonu",
                "2.  Dražba   — hráči dražia kto zoberie talon (min. 50)",
                "3.  Talon    — víťaz zoberie 2 karty, zahodí 2",
                "     (nemožno zahodiť eso ani desiatku)",
                "4.  Štichy   — hráči hrajú 10 štichov",
                "5.  Bodovanie — víťaz musí splniť povinnosť",
            ]),
            ("DRAŽBA", [
                "Hráč s povinnosťou (P) začína automaticky na 50.",
                "Každý môže pridávať po 10 alebo pasovať.",
                "Kto vydraží, zoberie talon a môže navýšiť povinnosť.",
                "Ak nikto nepridá, povinnosť berie hráč (P) za 50.",
            ]),
            ("ŠTICHY", [
                "Leader zahrá ľubovoľnú kartu.",
                "Ostatní MUSIA zahrať kartu rovnakej farby.",
                "Ostatní MUSIA zahrať vyššiu kartu ak majú (prebiť).",
                "Ak nemáš farbu — MUSÍŠ zahrať tromfovú kartu.",
                "Ak nemáš ani farbu ani tromf — zahraj čokoľvek.",
                "Vyššia karta v hranej farbe vyhráva štich.",
                "Tromfová karta bije všetky ostatné farby.",
            ]),
            ("TROMFY", [
                "Tromf = kráľ + horník (K+H) rovnakej farby na ruke.",
                "Hlásiť môžeš až od 2. štichu.",
                "Musíš byť leader (začínať štich).",
                "Tromf nahlásiš vynesením kráľa ALEBO horníka.",
                "Tromfová farba sa stáva najsilnejšou.",
            ]),
            ("BODOVANIE", [
                "Víťaz dražby MUSÍ nazbierať aspoň toľko bodov",
                "  koľko vydražil (povinnosť).",
                "Splnil povinnosť  →  dostane body rovné povinnosti.",
                "Nesplnil          →  odpočítajú sa mu body povinnosti.",
                "Ostatní hráči vždy dostanú zaokrúhlené body štichov.",
                "Body za tromf sa pripočítajú automaticky.",
            ]),
        ]

        # 2 stĺpce
        col_w = (self.INNER_W - 40) // 2
        cols  = [
            (self.INNER_X,              sections[:3]),
            (self.INNER_X + col_w + 40, sections[3:]),
        ]

        for col_x, col_sections in cols:
            y = self.CONTENT_Y
            for title, lines in col_sections:
                # Nadpis sekcie
                tsurf = self.font_large.render(title, True, COLOR_GOLD)
                self.canvas.blit(tsurf, (col_x, y))
                y += tsurf.get_height() + 2
                self.canvas.line(
                    COLOR_GOLD,
                    (col_x, y), (col_x + col_w, y), width=1
                )
                y += 8
                # Riadky
                for line in lines:
                    surf = self.font_medium.render(line, True, COLOR_WHITE)
                    self.canvas.blit(surf, (col_x, y))
                    y += surf.get_height() + 4
                y += 18  # medzera medzi sekciami

    # ------------------------------------------------------------------
    # Pomocné metódy
    # ------------------------------------------------------------------

    def _section_title(self, text: str, y: int):
        surf = self.font_large.render(text, True, COLOR_GOLD)
        self.canvas.blit(surf, surf.get_rect(
            centerx=SCREEN_WIDTH // 2, top=y
        ))

    def _divider(self, y: int):
        self.canvas.line(
            COLOR_GRAY,
            (self.INNER_X, y),
            (self.INNER_X + self.INNER_W, y),
            width=1
        )

    def _load_card(self, suit: str, rank: str, lsize: tuple[int, int]):
        """Karta v logickej veľkosti lsize (cache v Canvase)."""
        name = f"{suit}-{rank}.png"
        if not os.path.exists(os.path.join(CARDS_MEDIUM_PATH, name)):
            return None
        return self.canvas.card(name, 0, lsize, smooth=False)

    def __repr__(self) -> str:
        return f"InfoOverlay(visible={self.visible}, tab={self.active_tab})"