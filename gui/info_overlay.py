# gui/info_overlay.py
#
# Okno "Pravidlá a bodovanie" (tlačidlo Pravidlá v hre). Grafický rework
# 2026-10-28 podľa konceptu usera (ChatGPT) a štruktúry okna v hre CHUJ:
#   Bodovanie — hodnoty kariet, tromfové hlásenia, povinnosť, ostatní hráči,
#   Pravidlá  — cieľ hry, priebeh kola v 5 krokoch, animovaná ukážka
#               pravidiel štichov (gui/rules_demo.py), dražba a talón,
#               hlásenie tromfu.
# Medailóny s bodmi sú zlaté (v CHUJ červené = trestné).
#
# Všetky texty zodpovedajú logike hry (game/hand.py, game/round.py,
# game/player.py, config.py) — príklady štichov overuje
# tester/regression_rules_demo.py.
#
# Výkon: statický obsah okna (vrátane obrazu hry pod ním z chvíle otvorenia)
# sa kreslí raz do vrstvy (canvas.draw_static), každú snímku sa kreslí len
# hover záložiek a krížika a animovaná ukážka štichov.

import os

import pygame

from gui import display, ui_style
from gui.canvas import draw_static
from gui.rules_demo import TrickRulesDemo
from config import (
    SCREEN_WIDTH, CARD_POINTS, TRUMP_POINTS, MIN_BID, BID_STEP,
    CARD_BACK_IMAGE,
)

FRAME_MARGIN_X = 60
FRAME_MARGIN_Y = 18
SECTION_FILL = (27, 18, 11, 255)
SUBSECTION_FILL = (20, 13, 8, 255)
SECTION_RADIUS = 12
DIVIDER = (70, 54, 34)
CLOSE_R = 24
CARD_RATIO = 181 / 293

GOOD = (122, 200, 110)           # splnená povinnosť
BAD = (232, 112, 84)             # nesplnená povinnosť
# Zlatý medailón s bodmi (rozhodnutie usera 2026-10-28; v CHUJ červený)
MEDAL_RIM = (120, 82, 26)
MEDAL_DARK = (176, 128, 44)
MEDAL_LIGHT = (222, 172, 64)
MEDAL_TEXT = (48, 28, 8)
# Medailón s nulou — tmavý, tlmený
ZERO_RIM = (98, 76, 46)
ZERO_FILL = (30, 22, 14)

RANK_NAMES = (("ace", "Eso"), ("ten", "Desiatka"), ("king", "Kráľ"),
              ("over", "Horník"), ("under", "Dolník"), ("nine", "Deviatka"),
              ("eight", "Osmička"), ("seven", "Sedmička"))
TRUMP_ORDER = (("acorn", "ŽALUĎ"), ("leaf", "ZELEŇ"), ("bell", "GUĽA"),
               ("heart", "SRDCE"))


class InfoOverlay:
    def __init__(self, canvas):
        self.canvas = canvas
        self.H = display.logical_height()
        self._visible = False
        self._game_frame = None
        self.active_tab = "bodovanie"

        self.font_title = canvas.font(46)
        self.font_section = canvas.font(28)
        self.font_text = canvas.font(21)
        self.font_small = canvas.font(19)
        self.font_tab = canvas.font(24)

        # Rám okna, krížik, záložky
        self.frame = pygame.Rect(FRAME_MARGIN_X, FRAME_MARGIN_Y,
                                 SCREEN_WIDTH - 2 * FRAME_MARGIN_X,
                                 self.H - 2 * FRAME_MARGIN_Y)
        ccx, ccy = self.frame.right - 48, self.frame.top + 46
        self.btn_close = pygame.Rect(ccx - CLOSE_R - 4, ccy - CLOSE_R - 4,
                                     2 * CLOSE_R + 8, 2 * CLOSE_R + 8)
        tab_w, tab_h = 240, 46
        cx = SCREEN_WIDTH // 2
        self.tab_rects = {
            "bodovanie": pygame.Rect(cx - tab_w - 8, self.frame.top + 82, tab_w, tab_h),
            "pravidla": pygame.Rect(cx + 8, self.frame.top + 82, tab_w, tab_h),
        }
        self.content_top = self.tab_rects["bodovanie"].bottom + 24
        self.content_bottom = self.frame.bottom - 24
        self.x0, self.x1 = self.frame.left + 30, self.frame.right - 30

        self._checks: list = []           # presahy obsahu (layout_problems)
        self.rules_demo = TrickRulesDemo(canvas)
        self._demo_rect = self._rules_layout()["demo"]
        self.rules_demo.layout(self._demo_rect)

    # ------------------------------------------------------------------
    # Viditeľnosť
    # ------------------------------------------------------------------

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool):
        if value and not self._visible:
            self._game_frame = None          # nový obraz hry pod oknom
            self.rules_demo.reset()          # ukážka štichov od scény 1
        self._visible = bool(value)

    @property
    def covers_screen(self) -> bool:
        """True keď okno už má obraz hry pod sebou a kreslí celé okno."""
        return self._visible and self._game_frame is not None

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def toggle(self):
        self.visible = not self.visible

    # ------------------------------------------------------------------
    # Udalosti
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self._visible:
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
                    if key == "pravidla" and self.active_tab != key:
                        self.rules_demo.reset()
                    self.active_tab = key
                    return True
            if self.active_tab == "pravidla":
                self.rules_demo.handle_click(event.pos)
            return True  # blokuj klik cez okno
        return event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONUP)

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def draw(self):
        if not self._visible:
            return
        c = self.canvas
        if self._game_frame is None:
            # Volá sa na konci kreslenia hernej snímky — okno ju obsahuje
            self._game_frame = c.target.copy()
        draw_static(self, c, ("info", self.active_tab, id(self._game_frame)),
                    self._draw_static)
        mouse = display.mouse_pos()
        self._draw_tabs(mouse)
        self._draw_close(self.btn_close.collidepoint(mouse))
        if self.active_tab == "pravidla":
            self.rules_demo.draw(mouse)

    def _draw_static(self):
        c = self.canvas
        self._checks = []
        c.target.blit(self._game_frame, (0, 0))
        c.overlay_window((0, 0, 0, 200))
        c.overlay(self.frame, (17, 11, 7, 255), border_radius=ui_style.PANEL_RADIUS)
        ui_style.draw_panel(c, self.frame)
        ui_style.draw_screen_title(c, "PRAVIDLÁ A BODOVANIE", self.font_title,
                                   (SCREEN_WIDTH // 2, self.frame.top + 36),
                                   line_half_w=300, line_gap=32)
        if self.active_tab == "bodovanie":
            self._draw_scoring()
        else:
            self._draw_rules()

    def _draw_tabs(self, mouse):
        labels = {"bodovanie": "Bodovanie", "pravidla": "Pravidlá"}
        for key, rect in self.tab_rects.items():
            active = self.active_tab == key
            ui_style.draw_button(self.canvas, rect, labels[key], self.font_tab,
                                 1 if active else 3,
                                 hover=not active and rect.collidepoint(mouse),
                                 shadow=False)

    def _draw_close(self, hover: bool):
        c = self.canvas
        cx, cy = self.btn_close.center
        c.circle((24, 16, 10), (cx, cy), CLOSE_R)
        c.circle(ui_style.BTN_BORDER_HOVER if hover else ui_style.GOLD_SOFT,
                 (cx, cy), CLOSE_R, width=2)
        color = ui_style.BTN_TEXT_HOVER if hover else ui_style.GOLD
        d = 9
        c.line(color, (cx - d, cy - d), (cx + d, cy + d), width=3)
        c.line(color, (cx - d, cy + d), (cx + d, cy - d), width=3)

    # ------------------------------------------------------------------
    # Kontrola presahov (tester/regression_layout.py)
    # ------------------------------------------------------------------

    def _fit(self, name: str, panel: pygame.Rect, content: pygame.Rect):
        """Zapamätá si, kam siahol obsah panela — kontrola presahov."""
        self._checks.append((name, pygame.Rect(panel), pygame.Rect(content)))

    def layout_problems(self) -> list[str]:
        """Nakreslí obe záložky a vráti zoznam presahov obsahu mimo panelov
        (text, obrázok alebo ovládací prvok mimo hraníc svojho panela)."""
        c = self.canvas
        saved = (self.active_tab, self._game_frame)
        self._game_frame = c.target.copy()
        problems = []
        for tab in ("bodovanie", "pravidla"):
            self.active_tab = tab
            self._draw_static()
            if tab == "pravidla":
                d = self.rules_demo
                for nm, r in (("predchádzajúce", d.btn_prev), ("ďalšie", d.btn_next),
                              ("prehrať", d.btn_play), ("javisko", d.stage)):
                    self._fit(f"ukážka/{nm}", self._demo_rect, r)
                # odkiaľ v ukážke priletia karty — vždy celé na stole
                ch = round(d.cw / CARD_RATIO)
                for idx, (sx, sy) in d.seat.items():
                    card = pygame.Rect(0, 0, d.cw, ch)
                    card.center = (round(sx), round(sy))
                    self._fit(f"ukážka/štart karty {idx}", d.stage.inflate(16, 16), card)
            for name, panel, content in self._checks:
                inner = panel.inflate(-8, -8)
                if not inner.contains(content):
                    problems.append(f"{tab}/{name}: obsah {tuple(content)} "
                                    f"presahuje panel {tuple(panel)}")
        self.active_tab, self._game_frame = saved
        return problems

    # ------------------------------------------------------------------
    # Záložka BODOVANIE
    # ------------------------------------------------------------------

    def _draw_scoring(self):
        x0, x1 = self.x0, self.x1
        top, bottom = self.content_top, self.content_bottom
        gap = 18
        w_left = round((x1 - x0 - gap) * 0.55)
        w_right = x1 - x0 - gap - w_left
        # Spodný rad dostane toľko, koľko potrebuje jeho text; zvyšok sa
        # rozdelí medzi karty (rad 1) a tromfy (rad 2).
        h3 = max(self._obligation_height(w_left), self._others_height(w_right))
        avail = bottom - top - 2 * gap - h3
        h1 = round(avail * 0.47)
        h2 = avail - h1

        r1 = pygame.Rect(x0, top, x1 - x0, h1)
        self._section(r1, "1. HODNOTY KARIET", (
            ("Každá karta má svoju bodovú hodnotu.", ui_style.TEXT_DIM),
            ("Desiatka je druhá najsilnejšia karta, hneď po ese.", ui_style.TEXT)))
        self._draw_card_values(r1)

        r2 = pygame.Rect(x0, r1.bottom + gap, x1 - x0, h2)
        self._section(r2, "2. TROMFOVÉ HLÁSENIA", (
            ("Ak máš kráľa a horníka rovnakej farby, môžeš nahlásiť tromf "
             "a získať body navyše.", ui_style.TEXT_DIM),))
        self._draw_trump_values(r2)

        y3 = r2.bottom + gap
        r3 = pygame.Rect(x0, y3, w_left, bottom - y3)
        r4 = pygame.Rect(r3.right + gap, y3, x1 - r3.right - gap, bottom - y3)
        self._section(r3, "3. POVINNOSŤ")
        self._draw_obligation(r3)
        self._section(r4, "4. OSTATNÍ HRÁČI")
        self._draw_others(r4)

    def _draw_card_values(self, rect: pygame.Rect):
        c = self.canvas
        top = self._content_top(rect)
        name_h = self.font_text.get_height()
        medal_r = 24
        card_h = rect.bottom - 12 - name_h - 6 - medal_r - top
        card_w = round(card_h * CARD_RATIO)
        n = len(RANK_NAMES)
        step = min(card_w + 70, (rect.width - 80) // n)
        x_start = rect.centerx - (n - 1) * step // 2
        for i, (rank, name) in enumerate(RANK_NAMES):
            cx = x_start + i * step
            self._card(f"heart-{rank}", (cx - card_w // 2, top), (card_w, card_h))
            pts = CARD_POINTS[rank]
            my = top + card_h
            self._medal((cx, my), medal_r, str(pts), None, zero=pts == 0)
            s = self.font_text.render(name, True, ui_style.TEXT)
            r = s.get_rect(centerx=cx, top=my + medal_r + 6)
            c.blit(s, r)
            self._fit("hodnoty kariet", rect, r)

    def _draw_trump_values(self, rect: pygame.Rect):
        c = self.canvas
        top = self._content_top(rect)
        gap = 22
        n = len(TRUMP_ORDER)
        box_w = (rect.width - 44 - (n - 1) * gap) // n
        box_h = rect.bottom - 14 - top
        medal_r = min(40, box_h // 5)
        for i, (suit, label) in enumerate(TRUMP_ORDER):
            box = pygame.Rect(rect.x + 22 + i * (box_w + gap), top, box_w, box_h)
            c.overlay(box, SUBSECTION_FILL, border_radius=10)
            c.rect(DIVIDER, box, width=1, border_radius=10)
            icon = self._suit_icon(suit, 30)
            t = self.font_section.render(label, True, ui_style.GOLD)
            total = (icon.get_width() + 10 if icon else 0) + t.get_width()
            hx = box.centerx - total // 2
            hy = box.y + 8 + t.get_height() // 2
            if icon:
                c.blit(icon, icon.get_rect(midleft=(hx, hy)))
                hx += icon.get_width() + 10
            c.blit(t, t.get_rect(midleft=(hx, hy)))
            ctop = box.y + 8 + t.get_height() + 8
            card_h = box.bottom - ctop - medal_r - 6
            card_w = round(card_h * CARD_RATIO)
            g = 12
            self._card(f"{suit}-king", (box.centerx - card_w - g // 2, ctop), (card_w, card_h))
            self._card(f"{suit}-over", (box.centerx + g // 2, ctop), (card_w, card_h))
            my = ctop + card_h + 2
            self._medal((box.centerx, my), medal_r, str(TRUMP_POINTS[suit]), "bodov")
            self._fit("tromfové hlásenia", rect,
                      pygame.Rect(box.x, box.y, box.width, my + medal_r - box.y))

    # --- 3. Povinnosť -----------------------------------------------------

    OBLIGATION_INTRO = ("Vyhral si dražbu? Musíš uhrať aspoň toľko bodov, koľko si "
                        "vydražil. Počítajú sa štichy aj tromfové hlásenia.")
    OBLIGATION_BOXES = (
        (True, "Splnená povinnosť",
         "Uhral si dosť bodov. Pripíše sa ti vydražená hodnota.",
         "Vydražil si 100, uhral 112", "+100 bodov"),
        (False, "Nesplnená povinnosť",
         "Neuhral si dosť bodov. Vydražená hodnota sa ti odpočíta.",
         "Vydražil si 100, uhral 70", "−100 bodov"),
    )
    PILL_H = 38

    def _obligation_box_w(self, width: int) -> int:
        return (width - 44 - 18) // 2

    def _obligation_box_h(self, box_w: int) -> int:
        lh = self.font_small.get_height() + 3
        lines = max(len(self._wrap(b[2], self.font_small, box_w - 32))
                    for b in self.OBLIGATION_BOXES)
        return 14 + 34 + 10 + lines * lh + 10 + self.PILL_H + 12

    def _obligation_height(self, width: int) -> int:
        intro = len(self._wrap(self.OBLIGATION_INTRO, self.font_text, width - 44))
        return (self._header_h() + intro * (self.font_text.get_height() + 3) + 10
                + self._obligation_box_h(self._obligation_box_w(width)) + 14)

    def _draw_obligation(self, rect: pygame.Rect):
        c = self.canvas
        y = self._content_top(rect)
        y = self._paragraph(self.OBLIGATION_INTRO, rect.x + 22, y, rect.width - 44,
                            self.font_text, ui_style.TEXT, rect, "povinnosť")
        y += 10
        gap = 18
        bw = self._obligation_box_w(rect.width)
        bh = rect.bottom - 14 - y
        for j, (ok, title, line, example, pill) in enumerate(self.OBLIGATION_BOXES):
            color = GOOD if ok else BAD
            box = pygame.Rect(rect.x + 22 + j * (bw + gap), y, bw, bh)
            c.overlay(box, SUBSECTION_FILL, border_radius=10)
            c.rect(color, box, width=1, border_radius=10)
            icon = self._status_icon(ok, 34)
            ix, iy = box.x + 16, box.y + 14
            if icon:
                c.blit(icon, (ix, iy))
            t = self.font_section.render(title, True, color)
            c.blit(t, (ix + 44, iy + (34 - t.get_height()) // 2))
            ly = self._paragraph(line, box.x + 16, iy + 44, bw - 32,
                                 self.font_small, ui_style.TEXT, box, "povinnosť/box")
            # Príklad v jednom riadku dole: text → výsledok
            pr = pygame.Rect(0, 0, 140, self.PILL_H)
            pr.bottomright = (box.right - 14, box.bottom - 12)
            self._pill(pr, pill, color)
            ex = self.font_small.render(example, True, ui_style.TEXT_DIM)
            er = ex.get_rect(midleft=(box.x + 16, pr.centery))
            c.blit(ex, er)
            self._arrow(er.right + 10, pr.centery, 24, color)
            self._fit("povinnosť/príklad", box, er.union(pr))
            self._fit("povinnosť/box", rect, box)
            if er.right + 10 + 24 + 6 > pr.left or ly > pr.top:
                self._fit("povinnosť/príklad sa nezmestí", pygame.Rect(0, 0, 1, 1), er)

    # --- 4. Ostatní hráči ---------------------------------------------------

    OTHERS_INTRO = ("Ak si nevyhral dražbu, získavaš body za svoje štichy a hlásenia. "
                    "Výsledok sa zaokrúhli na desiatky – od 5 nahor.")
    OTHERS_ROWS = (("Štichy 33 + hlásenie 40 = 73", "70 bodov"),
                   ("Štichy 25", "30 bodov"),
                   ("Štichy 14", "10 bodov"))

    def _others_height(self, width: int) -> int:
        intro = len(self._wrap(self.OTHERS_INTRO, self.font_text, width - 44))
        row_h = self.font_text.get_height() + 12
        return (self._header_h() + intro * (self.font_text.get_height() + 3) + 10
                + 14 + self.font_text.get_height() + len(self.OTHERS_ROWS) * row_h
                + 10 + 14)

    def _draw_others(self, rect: pygame.Rect):
        c = self.canvas
        y = self._content_top(rect)
        y = self._paragraph(self.OTHERS_INTRO, rect.x + 22, y, rect.width - 44,
                            self.font_text, ui_style.TEXT, rect, "ostatní hráči")
        y += 10
        box = pygame.Rect(rect.x + 22, y, rect.width - 44, rect.bottom - 14 - y)
        c.overlay(box, SUBSECTION_FILL, border_radius=10)
        c.rect(DIVIDER, box, width=1, border_radius=10)
        t = self.font_text.render("PRÍKLAD", True, ui_style.GOLD)
        c.blit(t, (box.x + 16, box.y + 10))
        ry = box.y + 14 + t.get_height()
        row_h = (box.bottom - 10 - ry) / len(self.OTHERS_ROWS)
        for i, (text, result) in enumerate(self.OTHERS_ROWS):
            cy = round(ry + (i + 0.5) * row_h)
            s = self.font_text.render(text, True, ui_style.TEXT)
            c.blit(s, s.get_rect(midleft=(box.x + 16, cy)))
            r = self.font_text.render(result, True, GOOD)
            rr = r.get_rect(midright=(box.right - 18, cy))
            c.blit(r, rr)
            self._arrow(rr.left - 40, cy, 26, GOOD)
            self._fit("ostatní hráči/príklad", box, s.get_rect(midleft=(box.x + 16, cy)).union(rr))
            if i:
                ly = round(ry + i * row_h)
                c.line(DIVIDER, (box.x + 12, ly), (box.right - 12, ly), 1)
        self._fit("ostatní hráči", rect, box)

    # ------------------------------------------------------------------
    # Záložka PRAVIDLÁ
    # ------------------------------------------------------------------

    GOAL_TEXT = ("Zbieraj body za štichy a tromfové hlásenia. Kto ako prvý "
                 "dosiahne 1000 bodov, vyhráva.")
    FLOW_STEPS = (
        ("Rozdanie", "Každý dostane 10 kariet, ďalšie 2 tvoria talón."),
        ("Dražba", f"Hráči prihadzujú po {BID_STEP}, začína sa na {MIN_BID}."),
        ("Talón", "Víťaz dražby si vezme talón a odhodí 2 karty."),
        ("Štichy", "Hráči postupne odohrajú 10 štichov."),
        ("Bodovanie", "Spočítajú sa body a vyhodnotí povinnosť."),
    )
    BID_BULLETS = (
        f"Dražbu začína hráč s povinnosťou (P) na {MIN_BID} bodoch.",
        f"Môžeš prihodiť {BID_STEP} bodov alebo povedať „Dobrý“ a z dražby odstúpiť.",
        f"Ak nikto neprihodí, hráč s povinnosťou hrá za {MIN_BID}.",
        "Víťaz dražby si vezme talón a odhodí dve karty. Eso ani desiatku "
        "odhodiť nesmie.",
        "Body odhodených kariet sa mu započítajú. Po prezretí talónu môže "
        "povinnosť ešte zvýšiť.",
    )
    TRUMP_BULLETS = (
        "Tromf môžeš nahlásiť, ak máš kráľa a horníka rovnakej farby.",
        "Hlásiť môžeš od druhého štichu, keď si na rade vynášať.",
        "Tromf nahlásiš zahraním kráľa alebo horníka z tejto dvojice.",
        "Nahlásená farba sa stáva tromfovou – prebíja ostatné farby.",
        "Ak nahlásiš ďalší tromf, predchádzajúci prestáva platiť.",
    )
    BID_ILL_H = 52                 # výška ilustrácie (ponuky → talón)
    TRUMP_CARD_H = (96, 150)       # rozsah výšky kariet kráľ + horník

    def _rules_layout(self) -> dict:
        x0, x1 = self.x0, self.x1
        top, bottom = self.content_top, self.content_bottom
        gap = 16
        goal_h = max(64, 2 * (self.font_text.get_height() + 3) + 18)
        goal = pygame.Rect(x0, top, x1 - x0, goal_h)
        flow = pygame.Rect(x0, goal.bottom + gap, x1 - x0, 212)
        y = flow.bottom + gap
        h = bottom - y
        demo = pygame.Rect(x0, y, round((x1 - x0 - gap) * 0.565), h)
        rx = demo.right + gap
        w = x1 - rx
        # Výšky pravých panelov podľa ich obsahu, voľné miesto rovnomerne
        # Ak sa obsah nezmestí (písmo s väčšími metrikami pri niektorých
        # mierkach), najprv sa zmenšia ilustrácie a medzery, nie písmo.
        self.bid_ill_h, self.trump_card_lo, self.bullet_gap = (
            self.BID_ILL_H, self.TRUMP_CARD_H[0], self.BULLET_GAP)
        need_bid = self._bid_height(w)
        need_trump = self._trump_height(w)
        if need_bid + need_trump > h - gap:
            self.bid_ill_h, self.trump_card_lo, self.bullet_gap = 40, 76, 3
            need_bid = self._bid_height(w)
            need_trump = self._trump_height(w)
        slack = max(0, h - gap - need_bid - need_trump)
        h_bid = need_bid + slack // 2
        bid = pygame.Rect(rx, y, w, h_bid)
        trump = pygame.Rect(rx, bid.bottom + gap, w, bottom - bid.bottom - gap)
        return {"goal": goal, "flow": flow, "demo": demo, "bid": bid, "trump": trump}

    def _draw_rules(self):
        lay = self._rules_layout()
        self._draw_goal(lay["goal"])
        self._section(lay["flow"], "PRIEBEH KOLA")
        self._draw_flow(lay["flow"])
        self._panel_bg(lay["demo"])              # obsah kreslí rules_demo
        self._section(lay["bid"], "DRAŽBA A TALÓN")
        self._draw_bid_talon(lay["bid"])
        self._section(lay["trump"], "HLÁSENIE TROMFU")
        self._draw_trump_rules(lay["trump"])

    def _draw_goal(self, rect: pygame.Rect):
        c = self.canvas
        self._panel_bg(rect)
        icon = self._image("trophy.png", min(rect.height - 16, 56))
        x = rect.x + 24
        if icon:
            c.blit(icon, icon.get_rect(midleft=(x, rect.centery)))
            x += icon.get_width() + 20
        t = self.font_section.render("CIEĽ HRY", True, ui_style.GOLD)
        c.blit(t, t.get_rect(midleft=(x, rect.centery)))
        x += t.get_width() + 28
        lines = self._wrap(self.GOAL_TEXT, self.font_text, rect.right - 24 - x)
        lh = self.font_text.get_height() + 3
        y = rect.centery - len(lines) * lh // 2
        for ln in lines:
            s = self.font_text.render(ln, True, ui_style.TEXT)
            c.blit(s, (x, y))
            self._fit("cieľ hry", rect, s.get_rect(topleft=(x, y)))
            y += lh

    def _draw_flow(self, rect: pygame.Rect):
        c = self.canvas
        top = self._content_top(rect) - 6
        bottom = rect.bottom - 10
        n = len(self.FLOW_STEPS)
        x_start, x_end = rect.x + 16, rect.right - 16
        col_w = (x_end - x_start) / n
        head_h = 36
        lh = self.font_small.get_height() + 2
        descs = [self._wrap(d, self.font_small, col_w - 20) for _, d in self.FLOW_STEPS]
        desc_h = max(len(d) for d in descs) * lh
        ill_top = top + head_h + 4
        ill_h = bottom - desc_h - 8 - ill_top
        for i, (title, _desc) in enumerate(self.FLOW_STEPS):
            cx0 = round(x_start + i * col_w)
            cw = round(col_w)
            mid = cx0 + cw // 2
            if i > 0:
                c.line(DIVIDER, (cx0, top + 4), (cx0, bottom - 4), 1)
            t = self.font_section.render(title, True, ui_style.GOLD)
            r = 17
            total = 2 * r + 12 + t.get_width()
            hx = mid - total // 2
            self._number_circle((hx + r, top + head_h // 2), r, str(i + 1))
            c.blit(t, t.get_rect(midleft=(hx + 2 * r + 12, top + head_h // 2)))
            area = pygame.Rect(cx0 + 22, ill_top, cw - 44, ill_h)
            self._flow_illustration(i, area)
            if i < n - 1:
                self._arrow(cx0 + cw - 12, area.centery, 24)
            y = bottom - len(descs[i]) * lh
            for ln in descs[i]:
                s = self.font_small.render(ln, True, ui_style.TEXT)
                sr = s.get_rect(centerx=mid, top=y)
                c.blit(s, sr)
                self._fit("priebeh kola", pygame.Rect(cx0 + 4, rect.y, cw - 8, rect.height), sr)
                y += lh

    def _flow_illustration(self, step: int, area: pygame.Rect):
        c = self.canvas
        cx, cy = area.center
        h = min(area.height - 4, 116)
        w = round(h * CARD_RATIO)
        if step == 0:              # rozdanie — vejár rubov
            n, stp = 5, w * 0.34
            for i in range(n):
                t = i / (n - 1) - 0.5
                img = self._card_img(CARD_BACK_IMAGE, (w, h), round(-22 * t))
                if img:
                    c.blit(img, img.get_rect(center=(round(cx + t * (n - 1) * stp),
                                                     round(cy + abs(t) * h * 0.08))))
        elif step == 1:            # dražba — ponuky 50 / 60 / 70
            self._bid_chips((cx, cy), 1.0)
        elif step == 2:            # talón — dva ruby
            g = 10
            for j in range(2):
                img = self._card_img(CARD_BACK_IMAGE, (w, h), 0)
                if img:
                    c.blit(img, (cx - w - g // 2 + j * (w + g), cy - h // 2))
        elif step == 3:            # štichy — tri zahrané karty
            h2 = min(h, 104)
            w2 = round(h2 * CARD_RATIO)
            for k, (name, dx, ang) in enumerate((("leaf-king.png", -w2 * 0.8, 10),
                                                  ("leaf-ace.png", 0, 0),
                                                  ("acorn-seven.png", w2 * 0.8, -10))):
                img = self._card_img(name, (w2, h2), ang)
                if img:
                    c.blit(img, img.get_rect(center=(round(cx + dx),
                                                     cy + (6 if k != 1 else -4))))
        else:                      # bodovanie — zápisník
            icon = self._image("scoresheet.png", min(h, 112))
            if icon:
                c.blit(icon, icon.get_rect(center=(cx, cy)))

    def _bid_height(self, width: int) -> int:
        return (self._header_h() + self.bid_ill_h + 12
                + self._bullets_height(width - 44, self.BID_BULLETS) + 14)

    def _trump_text_width(self, width: int, card_h: int) -> int:
        card_w = round(card_h * CARD_RATIO)
        return width - 22 - (2 * card_w + 10) - 22 - 18

    def _trump_height(self, width: int) -> int:
        lo = self.trump_card_lo
        text_h = self._bullets_height(self._trump_text_width(width, lo), self.TRUMP_BULLETS)
        return self._header_h() + max(lo, text_h) + 14

    def _draw_bid_talon(self, rect: pygame.Rect):
        c = self.canvas
        top = self._content_top(rect)
        ill_h = self.bid_ill_h
        cy = top + ill_h // 2
        self._bid_chips((rect.x + 110, cy), 0.7 * ill_h / self.BID_ILL_H)
        self._arrow(rect.x + 196, cy, 26)
        w = round(ill_h * CARD_RATIO)
        for j in range(2):
            img = self._card_img(CARD_BACK_IMAGE, (w, ill_h), 0)
            if img:
                c.blit(img, (rect.x + 240 + j * (w + 8), cy - ill_h // 2))
        self._bullets(rect.x + 22, top + ill_h + 12, rect.width - 44, self.BID_BULLETS,
                      rect, "dražba a talón")

    def _draw_trump_rules(self, rect: pygame.Rect):
        top = self._content_top(rect)
        lo, hi = self.trump_card_lo, self.TRUMP_CARD_H[1]
        avail = rect.bottom - 14 - top
        # Najväčšie karty, pri ktorých sa text vedľa nich ešte zmestí
        card_h = lo
        for h in range(min(hi, avail), lo - 1, -4):
            tw = self._trump_text_width(rect.width, h)
            if self._bullets_height(tw, self.TRUMP_BULLETS) <= avail:
                card_h = h
                break
        card_w = round(card_h * CARD_RATIO)
        self._card("acorn-king", (rect.x + 22, top), (card_w, card_h))
        self._card("acorn-over", (rect.x + 22 + card_w + 10, top), (card_w, card_h))
        self._fit("hlásenie tromfu", rect,
                  pygame.Rect(rect.x + 22, top, 2 * card_w + 10, card_h))
        x = rect.x + 22 + 2 * card_w + 10 + 22
        self._bullets(x, top, rect.right - 18 - x, self.TRUMP_BULLETS,
                      rect, "hlásenie tromfu")

    # ------------------------------------------------------------------
    # Pomocné kreslenie
    # ------------------------------------------------------------------

    def _panel_bg(self, rect: pygame.Rect):
        c = self.canvas
        c.overlay(rect, SECTION_FILL, border_radius=SECTION_RADIUS)
        c.overlay((rect.x + 3, rect.y + 3, rect.width - 6, 40),
                  (255, 214, 140, 8), border_radius=SECTION_RADIUS - 3)
        c.rect(ui_style.GOLD_SOFT, rect, width=2, border_radius=SECTION_RADIUS)

    def _section(self, rect: pygame.Rect, title: str, subtitle=None):
        """Sekcia: o odtieň svetlejší podklad, zlatohnedý rám, zlatý nadpis
        s deliacou čiarou, voliteľný podnadpis vedľa nadpisu — zoznam
        (text, farba) za sebou v jednom riadku."""
        c = self.canvas
        self._panel_bg(rect)
        t = self.font_section.render(title, True, ui_style.GOLD)
        c.blit(t, (rect.x + 22, rect.y + 10))
        line_y = rect.y + 10 + t.get_height() + 5
        c.line(DIVIDER, (rect.x + 20, line_y), (rect.right - 20, line_y), 1)
        if subtitle:
            x = rect.x + 22 + t.get_width() + 22
            for text, color in subtitle:
                s = self.font_text.render(text, True, color)
                sr = s.get_rect(left=x, bottom=rect.y + 10 + t.get_height() - 3)
                c.blit(s, sr)
                self._fit(title.lower(), rect, sr)
                x = sr.right + 10

    def _header_h(self) -> int:
        return 10 + self.font_section.get_height() + 5 + 12

    def _content_top(self, rect: pygame.Rect) -> int:
        return round(rect.y + self._header_h())

    def _paragraph(self, text, x, y, width, font, color, panel, name) -> int:
        """Zalomený odsek; vráti y pod ním."""
        lh = font.get_height() + 3
        for ln in self._wrap(text, font, width):
            s = font.render(ln, True, color)
            self.canvas.blit(s, (x, y))
            self._fit(name, panel, s.get_rect(topleft=(x, y)))
            y += lh
        return y

    def _medal(self, center, r: int, number: str, unit: str | None,
               zero: bool = False):
        """Okrúhly medailón s bodmi: zlatý s tmavším lemom (body), alebo
        tmavý tlmený (0 bodov)."""
        c = self.canvas
        cx, cy = center
        c.circle((0, 0, 0), (cx + 2, cy + 4), r)
        if zero:
            c.circle(ZERO_FILL, (cx, cy), r)
            c.circle(ZERO_RIM, (cx, cy), r, width=2)
            color = ui_style.TEXT_DIM
        else:
            c.circle(MEDAL_RIM, (cx, cy), r)
            c.circle(MEDAL_DARK, (cx, cy), r - 4)
            c.circle(MEDAL_LIGHT, (cx, cy - r // 6), r - 10)
            c.circle(MEDAL_DARK, (cx, cy + r // 3), max(1, r - 16))
            c.circle((236, 190, 96), (cx, cy), r - 4, width=1)
            color = MEDAL_TEXT
        if unit:
            big = c.font(round(r * 0.8)).render(number, True, color)
            small = c.font(round(r * 0.36)).render(unit, True, color)
            c.blit(big, big.get_rect(centerx=cx, bottom=cy + r * 0.22))
            c.blit(small, small.get_rect(centerx=cx, top=cy + r * 0.16))
        else:
            s = c.font(round(r * 1.05)).render(number, True, color)
            c.blit(s, s.get_rect(center=(cx, cy)))

    def _pill(self, rect: pygame.Rect, text: str, color):
        c = self.canvas
        dark = tuple(int(ch * 0.35) for ch in color)
        c.rect(dark, rect, border_radius=rect.height // 2)
        c.rect(color, rect, width=2, border_radius=rect.height // 2)
        s = self.font_text.render(text, True, color)
        c.blit(s, s.get_rect(center=rect.center))

    def _status_icon(self, ok: bool, size: int):
        """Zelená fajka / červený krížik (assets/graphics/ok.png, circlex.png)."""
        return self._image("ok.png" if ok else "circlex.png", size)

    def _bid_chips(self, center, scale: float):
        """Tri prekrývajúce sa ponuky 50 / 60 / 70 (ako bublinky dražby)."""
        c = self.canvas
        cx, cy = center
        w, h = round(64 * scale), round(44 * scale)
        font = c.font(round(26 * scale))
        for val, dx, dy in ((MIN_BID, -46, 6), (MIN_BID + BID_STEP, 0, -6),
                            (MIN_BID + 2 * BID_STEP, 46, 6)):
            r = pygame.Rect(0, 0, w, h)
            r.center = (cx + round(dx * scale), cy + round(dy * scale))
            c.overlay(r.move(2, 4), (0, 0, 0, 110), border_radius=10)
            c.rect((238, 228, 208), r, border_radius=10)
            c.rect((120, 100, 70), r, width=2, border_radius=10)
            s = font.render(str(val), True, (40, 28, 16))
            c.blit(s, s.get_rect(center=r.center))

    BULLET_GAP = 6

    def _bullets_height(self, width: int, lines) -> int:
        lh = self.font_small.get_height() + 3
        n = sum(len(self._wrap(t, self.font_small, width - 22)) for t in lines)
        return n * lh + (len(lines) - 1) * self.bullet_gap

    def _bullets(self, x: int, y: int, width: int, lines, panel=None,
                 name: str = "") -> int:
        """Odrážky so zalomením; vráti y pod poslednou. S `panel` sa každý
        riadok zapíše do kontroly presahov."""
        c = self.canvas
        lh = self.font_small.get_height() + 3
        for i, text in enumerate(lines):
            if i:
                y += self.bullet_gap
            c.circle(ui_style.GOLD, (x + 6, y + lh // 2), 4)
            for p in self._wrap(text, self.font_small, width - 22):
                s = self.font_small.render(p, True, ui_style.TEXT)
                c.blit(s, (x + 20, y))
                if panel is not None:
                    self._fit(name, panel, s.get_rect(topleft=(x + 20, y)))
                y += lh
        return y

    def _number_circle(self, center, r: int, number: str):
        c = self.canvas
        c.circle((0, 0, 0), (center[0] + 1, center[1] + 3), r)
        c.circle(ui_style.GOLD, center, r)
        c.circle((150, 104, 30), center, r, width=2)
        s = c.font(round(r * 1.25)).render(number, True, (40, 24, 8))
        c.blit(s, s.get_rect(center=center))

    def _arrow(self, x: int, y: int, length: int = 22, color=None):
        """Malá zlatá šípka doprava, ľavý koniec v (x, y)."""
        color = color or ui_style.GOLD
        t = max(4, length // 5)
        hd = max(8, length // 2)
        self.canvas.polygon(color, [(x, y - t // 2), (x + length - hd, y - t // 2),
                                    (x + length - hd, y - hd // 2 - 2), (x + length, y),
                                    (x + length - hd, y + hd // 2 + 2),
                                    (x + length - hd, y + t // 2), (x, y + t // 2)])

    def _card(self, name: str, pos, size):
        c = self.canvas
        img = self._card_img(f"{name}.png", size, 0)
        if not img:
            return
        c.overlay((pos[0] + 4, pos[1] + 6, size[0], size[1]), (0, 0, 0, 110),
                  border_radius=8)
        c.blit(img, pos)

    def _card_img(self, filename: str, size, angle: int):
        try:
            return self.canvas.card(filename, angle, (max(1, size[0]), max(1, size[1])))
        except (FileNotFoundError, pygame.error):
            return None

    def _image(self, name: str, height: int):
        path = os.path.join("assets", "graphics", name)
        if not os.path.exists(path):
            return None
        try:
            iw, ih = self.canvas.image_size(path)
            return self.canvas.image(path, (max(1, round(height * iw / ih)), height))
        except pygame.error:
            return None

    def _suit_icon(self, suit: str, size: int):
        from gui.scoreboard import load_suit_icon
        return load_suit_icon(self.canvas, suit, size)

    @staticmethod
    def _wrap(text: str, font, width: float) -> list[str]:
        words, lines, line = text.split(), [], ""
        for word in words:
            test = f"{line} {word}".strip()
            if line and font.size(test)[0] > width:
                lines.append(line)
                line = word
            else:
                line = test
        if line:
            lines.append(line)
        return lines

    def __repr__(self) -> str:
        return f"InfoOverlay(visible={self._visible}, tab={self.active_tab})"
