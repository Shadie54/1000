# gui/rules_demo.py
#
# Animovaná ukážka pravidiel štichov — panel "PRAVIDLÁ ŠTICHOV" v okne
# Pravidlá a bodovanie (gui/info_overlay.py). Prevzaté z hry CHUJ
# (2026-10-28) a prispôsobené pravidlám hry 1000: 3 hráči, povinnosť
# prebiť, povinnosť hrať tromf.
#
# Šesť pevných scén (nie náhodné rozdanie), každá trvá SCENE_LEN sekúnd:
#   0–1 s  príprava (karty na stole, názov),
#   1–3 s  animácia (pohyb kariet),
#   3–6 s  výsledok so zvýraznením,
#   6–7 s  plynulý prechod do ďalšej scény.
# Ukážka nesiaha na herný stav — kreslí vlastné karty podľa mien súborov.
# Miesta hráčov pri stole berie z gui/layout.py (smer hry ČR / SR).
#
# Správnosť príkladov (povolené karty, víťaz, poradie) overuje
# verify_scenes() skutočnými triedami hry Trick a Hand —
# tester/regression_rules_demo.py.
#
# Ovládanie: Predchádzajúce / Ďalšie / bodky (ručný výber = scéna sa prehrá
# raz a ostane stáť na výsledku), Pozastaviť / Prehrať. Pri otvorení okna
# reset() — začína sa scénou 1.

import math
import os

import pygame

from gui import layout, ui_style

SCENE_LEN = 7.0
HOLD_AT = 5.9                  # ručne zvolená scéna zastane na výsledku
CARD_RATIO = 181 / 293

GREEN = (96, 200, 80)
RED = (220, 60, 45)
NAME_DIM = (150, 132, 108)

SEATS = ("Hráč", "Počítač 1", "Počítač 2")      # index = hráč v hre
LEADER = 2                     # vynáša Počítač 2 → Hráč je hneď po ňom

# Scény: názov, vysvetlenie
SCENES = (
    ("Vynášajúci určí farbu",
     "Hráč, ktorý začína štich, určuje jeho farbu."),
    ("Musíš priznať farbu",
     "Ak máš kartu hranej farby, musíš ju zahrať."),
    ("Musíš prebiť",
     "Ak máš vyššiu kartu hranej farby, musíš zahrať vyššiu."),
    ("Nemáš farbu — hraj tromf",
     "Ak nemáš hranú farbu, musíš zahrať tromf (ak je zahlásený)."),
    ("Nemáš farbu ani tromf",
     "Potom môžeš zahrať ľubovoľnú kartu."),
    ("Kto berie štich",
     "Tromf bije ostatné farby, inak berie najvyššia karta hranej farby."),
)

# Karty scén — jediný zdroj pre kreslenie aj verify_scenes()
S1_LEAD = "leaf-nine"
S2_LEAD, S2_TRUMP = "leaf-nine", None
S2_HAND = ("heart-ace", "bell-king", "leaf-under", "acorn-ten")
S2_PLAY = "leaf-under"
S3_LEAD, S3_TRUMP = "leaf-king", None
S3_HAND = ("leaf-seven", "leaf-ace", "bell-ten")
S3_PLAY = "leaf-ace"
S4_LEAD, S4_TRUMP = "leaf-ten", "acorn"
S4_HAND = ("heart-king", "acorn-eight", "bell-nine")
S4_PLAY = "acorn-eight"
S5_LEAD, S5_TRUMP = "leaf-ten", "acorn"
S5_HAND = ("heart-seven", "bell-ace", "heart-under")
S5_PLAY = "bell-ace"
S6_TRUMP = "acorn"
S6_TRICK = ((2, "leaf-king"), (0, "acorn-seven"), (1, "leaf-ace"))
S6_WINNER = 0

# Názov tromfu v 4. a 6. scéne
TRUMP_NAME = {"heart": "srdce", "bell": "guľa", "leaf": "zeleň", "acorn": "žaluď"}


def _ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _lerp(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)


def _arc(a, b, k, bend=0.18):
    """Pohyb po jemnom oblúku (karta "letí"), nie po priamke."""
    x, y = _lerp(a, b, k)
    dx, dy = b[0] - a[0], b[1] - a[1]
    lift = math.sin(math.pi * k) * bend
    return (x - dy * lift, y + dx * lift)


def verify_scenes() -> list[str]:
    """Overí príklady skutočnou logikou hry. Vráti zoznam chýb."""
    from game.card import Card
    from game.hand import Hand
    from game.trick import Trick

    def card(name):
        suit, rank = name.split("-")
        return Card(suit, rank)

    def playable(hand_names, lead, trump):
        h = Hand()
        h.add_cards([card(n) for n in hand_names])
        played = [(LEADER, card(lead))]
        return {c.image_name[:-4] for c in
                h.get_playable_cards(card(lead).suit, trump, played)}

    errors = []
    for no, lead, trump, hand, expected in (
            (2, S2_LEAD, S2_TRUMP, S2_HAND, {S2_PLAY}),
            (3, S3_LEAD, S3_TRUMP, S3_HAND, {S3_PLAY}),
            (4, S4_LEAD, S4_TRUMP, S4_HAND, {S4_PLAY}),
            (5, S5_LEAD, S5_TRUMP, S5_HAND, set(S5_HAND))):
        got = playable(hand, lead, trump)
        if got != expected:
            errors.append(f"scéna {no}: povolené {sorted(got)}, čakané {sorted(expected)}")
    if S5_PLAY not in S5_HAND:
        errors.append("scéna 5: zahraná karta nie je v ruke")

    trick = Trick([None] * 3, S6_TRICK[0][0], S6_TRUMP)
    for idx, name in S6_TRICK:
        trick.play_card(idx, card(name))
    if trick.get_winner_index() != S6_WINNER:
        errors.append(f"scéna 6: víťaz {trick.get_winner_index()}, čakaný {S6_WINNER}")
    order = [idx for idx, _ in S6_TRICK]
    if order != [(order[0] + i) % 3 for i in range(3)]:
        errors.append(f"scéna 6: poradie hráčov {order} nezodpovedá hre")
    # Hráč v 6. scéne hrá tromf — musí to byť povolené (nemá zeleň)
    h = Hand()
    h.add_cards([card("acorn-seven"), card("bell-nine")])
    allowed = {c.image_name[:-4] for c in
               h.get_playable_cards("leaf", S6_TRUMP, [(2, card("leaf-king"))])}
    if allowed != {"acorn-seven"}:
        errors.append(f"scéna 6: Hráč by mohol hrať {sorted(allowed)}")
    return errors


class TrickRulesDemo:
    def __init__(self, canvas):
        self.canvas = canvas
        self.font_head = canvas.font(30)
        self.font_title = canvas.font(30)
        self.font_text = canvas.font(22)
        self.font_seat = canvas.font(18)
        self.font_btn = canvas.font(21)
        self.rect = pygame.Rect(0, 0, 1100, 516)
        self._stage_cache = None
        self.reset()

    # --- stav -------------------------------------------------------------

    def reset(self):
        self.scene = 0
        self.playing = True
        self.hold_at: float | None = None
        self._t0 = pygame.time.get_ticks()

    def _elapsed(self) -> float:
        t = (pygame.time.get_ticks() - self._t0) / 1000.0
        if self.playing:
            while t >= SCENE_LEN:
                t -= SCENE_LEN
                self.scene = (self.scene + 1) % len(SCENES)
                self._t0 += int(SCENE_LEN * 1000)
            return t
        return min(t, self.hold_at if self.hold_at is not None else HOLD_AT)

    def select(self, index: int):
        """Ručný výber scény — prehrá sa raz a zastane na výsledku."""
        self.scene = index % len(SCENES)
        self.playing = False
        self.hold_at = HOLD_AT
        self._t0 = pygame.time.get_ticks()

    def toggle_play(self):
        t = self._elapsed()
        if self.playing:
            self.playing = False
            self.hold_at = t
        else:
            self.playing = True
            self.hold_at = None
            if t >= HOLD_AT:          # zo zastaveného výsledku plynulo ďalej
                t = HOLD_AT
        self._t0 = pygame.time.get_ticks() - int(t * 1000)

    # --- rozloženie -------------------------------------------------------

    def layout(self, rect: pygame.Rect):
        self.rect = pygame.Rect(rect)
        r = self.rect
        self.stage = pygame.Rect(r.x + 20, r.y + 66, r.width - 40, r.height - 66 - 74)
        by = r.bottom - 62
        self.btn_prev = pygame.Rect(r.x + 22, by, 220, 44)
        self.btn_play = pygame.Rect(r.right - 22 - 200, by, 200, 44)
        self.btn_next = pygame.Rect(self.btn_play.x - 16 - 150, by, 150, 44)
        dots_x = (self.btn_prev.right + self.btn_next.left) // 2 - 75
        self.dots = [pygame.Rect(dots_x + i * 30 - 10, by + 12, 20, 20)
                     for i in range(len(SCENES))]
        # stôl vľavo, text a ruka hráča vpravo
        st = self.stage
        # mierka podľa výšky aj šírky javiska (pri 16:10 je javisko vyššie)
        k = min(st.height / 370, st.width / 1000)
        self.k = k
        self.cw = round(84 * k)
        cx, cy = st.x + round(st.width * 0.30), st.centery - round(10 * k)
        self.center = (cx, cy)
        seat_of = layout.game().seat_of           # 0 dole, 1/2 vľavo/vpravo
        side = {"left": -1, "right": 1}
        dy, dx = round(70 * k), round(105 * k)
        ldy, ldx = round(172 * k), round(205 * k)
        sdy, sdx = round(250 * k), round(300 * k)
        self.spot, self.label, self.seat = {}, {}, {}
        for idx in range(3):
            s = seat_of.get(idx, "bottom")
            if s == "bottom":
                self.spot[idx] = (cx, cy + dy)
                self.label[idx] = (cx, cy + ldy)
                half_h = round(self.cw / CARD_RATIO) // 2 + 10
                self.seat[idx] = (cx, cy + min(sdy, st.bottom - cy - half_h))
            else:
                sx = side[s]
                self.spot[idx] = (cx + sx * dx, cy - round(20 * k))
                self.label[idx] = (cx + sx * ldx, cy - round(95 * k))
                # Odkiaľ karta priletí — vždy celá na stole (pri smere SR je
                # Počítač 2 vľavo, kde je od stredu stola k okraju menej miesta)
                room = (cx - st.x) if sx < 0 else (st.right - cx)
                half_w = self.cw // 2 + 10
                self.seat[idx] = (cx + sx * min(sdx, room - half_w), cy - round(20 * k))
        self.text_x = st.x + round(st.width * 0.58)
        self.hand_y = st.bottom - round(88 * k)

    def hand_pos(self, i: int, n: int) -> tuple[int, int]:
        step = round(76 * self.k)
        w = self.stage.right - 18 - self.text_x
        x0 = self.text_x + w // 2 - (n - 1) * step // 2
        return (x0 + i * step, self.hand_y)

    # --- udalosti ---------------------------------------------------------

    def handle_click(self, pos) -> bool:
        if self.btn_prev.collidepoint(pos):
            self.select(self.scene - 1)
            return True
        if self.btn_next.collidepoint(pos):
            self.select(self.scene + 1)
            return True
        if self.btn_play.collidepoint(pos):
            self.toggle_play()
            return True
        for i, d in enumerate(self.dots):
            if d.inflate(10, 10).collidepoint(pos):
                self.select(i)
                return True
        return False

    # --- kreslenie --------------------------------------------------------

    def draw(self, mouse_pos):
        c = self.canvas
        t = self._elapsed()
        r = self.rect
        title = self.font_head.render("PRAVIDLÁ ŠTICHOV", True, ui_style.GOLD)
        c.blit(title, (r.x + 22, r.y + 14))
        num = self.font_head.render(f"{self.scene + 1} / {len(SCENES)}", True, ui_style.GOLD)
        c.blit(num, num.get_rect(right=r.right - 24, top=r.y + 14))
        c.line((70, 54, 34), (r.x + 20, r.y + 56), (r.right - 20, r.y + 56), 1)

        self._draw_stage()
        fade = 1.0
        if self.playing and t > SCENE_LEN - 1:
            fade = 1 - _ease(t - (SCENE_LEN - 1))      # prechod do ďalšej scény
        if t < 0.4:
            fade = min(fade, _ease(t / 0.4))
        self._draw_labels(self._glow_seat(t))
        self._draw_trump_note(fade)
        getattr(self, f"_scene{self.scene + 1}")(t, fade)
        self._draw_text()
        self._draw_controls(mouse_pos)

    def _draw_stage(self):
        """Tmavý výrez dreveného stola so zaoblenými rohmi (cachované)."""
        c = self.canvas
        pr = c.prect(self.stage)
        key = (pr.size, c.target.get_size())
        if self._stage_cache is None or self._stage_cache[0] != key:
            surf = pygame.Surface(pr.size, pygame.SRCALPHA)
            if os.path.exists(ui_style.TABLE_BG_PATH):
                bg = c.background(ui_style.TABLE_BG_PATH, c.target.get_size())
                src = pygame.Rect(pr.topleft, pr.size).clip(bg.get_rect())
                surf.blit(bg, (0, 0), src)
            else:
                surf.fill((45, 28, 15))
            dark = pygame.Surface(pr.size, pygame.SRCALPHA)
            dark.fill((0, 0, 0, 125))
            surf.blit(dark, (0, 0))
            mask = pygame.Surface(pr.size, pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                             border_radius=round(10 * c.s))
            surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            self._stage_cache = (key, surf)
        c.target.blit(self._stage_cache[1], pr.topleft)
        c.rect((70, 54, 34), self.stage, width=1, border_radius=10)

    def _scene_trump(self) -> str | None:
        return {3: S4_TRUMP, 4: S5_TRUMP, 5: S6_TRUMP}.get(self.scene)

    def _draw_trump_note(self, fade: float):
        """Vľavo hore na stole: aký je tromf (scény 4–6)."""
        trump = self._scene_trump()
        if not trump:
            return
        c = self.canvas
        st = self.stage
        size = round(34 * self.k)
        x, y = st.x + 16, st.y + 14
        lbl = self.font_seat.render("Tromf:", True, NAME_DIM)
        c.blit(lbl, (x, y + (size - lbl.get_height()) // 2))
        x += lbl.get_width() + 8
        path = os.path.join("assets", "suit-icons", f"{trump}-icon@medium.png")
        try:
            ic = c.image(path, (size, size))
            c.blit(ic, (x, y))
            x += size + 6
        except (FileNotFoundError, pygame.error):
            pass
        name = self.font_seat.render(TRUMP_NAME[trump], True, ui_style.GOLD)
        c.blit(name, (x, y + (size - name.get_height()) // 2))

    def _glow_seat(self, t) -> int | None:
        s = self.scene
        if s == 0:
            return LEADER
        if s in (1, 2, 3, 4):
            return 0
        return S6_WINNER if t >= 3.0 else None

    def _draw_labels(self, glow: int | None):
        c = self.canvas
        for idx, pos in self.label.items():
            g = idx == glow
            t = self.font_seat.render(SEATS[idx], True, ui_style.GOLD if g else NAME_DIM)
            r = t.get_rect(center=pos).inflate(14, 6)
            c.rect((15, 10, 6), r, border_radius=6)
            c.rect(ui_style.GOLD if g else (70, 54, 34), r, width=2 if g else 1,
                   border_radius=6)
            c.blit(t, t.get_rect(center=pos))

    def _draw_text(self):
        """Názov pravidla a vysvetlenie na tmavom podklade vpravo hore."""
        c = self.canvas
        title, line = SCENES[self.scene]
        x = self.text_x
        w = self.stage.right - 18 - x
        lines = _wrap(line, self.font_text, w - 36)
        line_h = self.font_text.get_height() + 4
        box_h = 20 + self.font_title.get_height() + 12 + len(lines) * line_h + 18
        box = pygame.Rect(x, self.stage.y + 18, w, box_h)
        c.overlay(box, (12, 8, 5, 215), border_radius=10)
        c.rect(ui_style.GOLD_SOFT, box, width=1, border_radius=10)
        c.rect(ui_style.GOLD, (box.x + 1, box.y + 14, 4, box_h - 28))   # zlatý akcent
        y = box.y + 20
        # Dlhý nadpis v užšom paneli — menšie písmo, aby nesiahal po okraj
        font = self.font_title
        size = 30
        while font.size(title)[0] > w - 40 and size > 22:
            size -= 1
            font = c.font(size)
        c.blit(font.render(title, True, (0, 0, 0)), (box.x + 22, y + 2))
        s = font.render(title, True, ui_style.GOLD)
        c.blit(s, (box.x + 20, y))
        y += s.get_height() + 12
        for ln in lines:
            c.blit(self.font_text.render(ln, True, ui_style.TEXT), (box.x + 20, y))
            y += line_h
        if self.scene in (1, 2, 3, 4):
            cap = self.font_seat.render("Tvoja ruka", True, NAME_DIM)
            c.blit(cap, cap.get_rect(centerx=x + w // 2,
                                     bottom=self.hand_y - round(70 * self.k)))

    def _draw_controls(self, mouse):
        c = self.canvas
        ui_style.draw_button(c, self.btn_prev, "‹  Predchádzajúce", self.font_btn, 3,
                             self.btn_prev.collidepoint(mouse), shadow=False)
        ui_style.draw_button(c, self.btn_next, "Ďalšie  ›", self.font_btn, 3,
                             self.btn_next.collidepoint(mouse), shadow=False)
        ui_style.draw_button(c, self.btn_play, "", self.font_btn, 3,
                             self.btn_play.collidepoint(mouse), shadow=False)
        b = self.btn_play
        ix, iy = b.x + 30, b.centery
        col = ui_style.GOLD
        if self.playing:
            c.rect(col, (ix - 8, iy - 9, 6, 18))
            c.rect(col, (ix + 2, iy - 9, 6, 18))
            label = "Pozastaviť"
        else:
            c.polygon(col, [(ix - 7, iy - 10), (ix + 10, iy), (ix - 7, iy + 10)])
            label = "Prehrať"
        s = self.font_btn.render(label, True, ui_style.TEXT)
        c.blit(s, s.get_rect(midleft=(ix + 24, iy)))
        for i, d in enumerate(self.dots):
            active = i == self.scene
            c.circle(ui_style.GOLD if active else (90, 70, 44), d.center, 7 if active else 5)

    # --- karty --------------------------------------------------------------

    def _card(self, name: str, center, scale: float = 1.0, alpha: float = 1.0,
              outline=None, mark: str | None = None, shadow: bool = True):
        c = self.canvas
        w = round(self.cw * scale)
        h = round(w / CARD_RATIO)
        try:
            img = c.card(f"{name}.png", lsize=(w, h))
        except (FileNotFoundError, pygame.error):
            return
        rect = img.get_rect(center=(round(center[0]), round(center[1])))
        a = int(255 * max(0.0, min(1.0, alpha)))
        if a <= 0:
            return
        if shadow and a > 200:
            c.overlay(rect.move(4, 6), (0, 0, 0, 100), border_radius=8)
        if a < 255:
            img = img.copy()
            img.set_alpha(a)
        c.blit(img, rect)
        if outline and a > 40:
            c.rect(outline, rect.inflate(6, 6), width=4, border_radius=10)
        if mark and a > 40:
            ic = self._icon(mark, round(40 * self.k))
            if ic:
                c.blit(ic, ic.get_rect(center=(rect.right - 4, rect.top + 4)))
        return rect

    def _icon(self, name: str, size: int):
        path = os.path.join("assets", "graphics", f"{name}.png")
        try:
            return self.canvas.image(path, (size, size))
        except (FileNotFoundError, pygame.error):
            return None

    def _hand(self, names, fade, moved=None, moved_k=0.0, dimmed=(), outlines=None,
              marks=None):
        """Ruka hráča vpravo dole; zahraná karta ostane ako priesvitný tieň."""
        for i, n in enumerate(names):
            pos = self.hand_pos(i, len(names))
            if n == moved:
                self._card(n, pos, 0.8, alpha=fade * (1 - 0.75 * moved_k), shadow=False)
            else:
                a = fade * (0.45 if n in dimmed else 1.0)
                self._card(n, pos, 0.8, alpha=a,
                           outline=(outlines or {}).get(n),
                           mark=(marks or {}).get(n))

    # --- scény (t = čas v scéne, fade = priehľadnosť obsahu) ---------------

    def _scene1(self, t, fade):
        k = _ease((t - 1.0) / 2.0)
        pos = _arc(self.seat[LEADER], self.spot[LEADER], k)
        self._card(S1_LEAD, pos, alpha=fade * min(1.0, 0.3 + k),
                   outline=ui_style.GOLD if t >= 3.0 else None)
        if t >= 3.0:
            a = _ease((t - 3.0) / 0.6) * fade
            c = self.canvas
            cx, cy = self.center
            r = round(36 * self.k)
            c.circle((20, 13, 8), (cx, cy), r)
            c.circle(ui_style.GOLD, (cx, cy), r, width=3)
            path = os.path.join("assets", "suit-icons", "leaf-icon@large.png")
            try:
                ic = c.image(path, (round(r * 1.05), round(r * 1.25))).copy()
                ic.set_alpha(int(255 * a))
                c.blit(ic, ic.get_rect(center=(cx, cy)))
            except (FileNotFoundError, pygame.error):
                pass

    def _respond(self, t, fade, lead, hand, play, forbidden=(), allowed=None):
        """Počítač 2 vynesie `lead`, Hráč odpovie kartou `play` z ruky.
        forbidden = karty, ktoré nesmie zahrať (červený rám a krížik),
        allowed = karty, ktoré smie (zelený rám)."""
        self._card(lead, self.spot[LEADER], alpha=fade)
        k = _ease((t - 1.0) / 2.0)
        show = t >= 0.6
        outlines = {}
        marks = {}
        if show:
            for n in forbidden:
                outlines[n] = RED
                marks[n] = "circlex"
            for n in (allowed or ()):
                if n != play:
                    outlines[n] = GREEN
        self._hand(hand, fade, moved=play, moved_k=k, dimmed=forbidden,
                   outlines=outlines, marks=marks)
        start = self.hand_pos(hand.index(play), len(hand))
        pos = _arc(start, self.spot[0], k, bend=0.15)
        self._card(play, pos, 0.8 + 0.2 * k, alpha=fade,
                   outline=GREEN if show else None,
                   mark="ok" if t >= 3.0 else None)

    def _scene2(self, t, fade):
        self._respond(t, fade, S2_LEAD, S2_HAND, S2_PLAY,
                      forbidden=tuple(n for n in S2_HAND if n != S2_PLAY))

    def _scene3(self, t, fade):
        self._respond(t, fade, S3_LEAD, S3_HAND, S3_PLAY,
                      forbidden=tuple(n for n in S3_HAND if n != S3_PLAY))

    def _scene4(self, t, fade):
        self._respond(t, fade, S4_LEAD, S4_HAND, S4_PLAY,
                      forbidden=tuple(n for n in S4_HAND if n != S4_PLAY))

    def _scene5(self, t, fade):
        self._respond(t, fade, S5_LEAD, S5_HAND, S5_PLAY, allowed=S5_HAND)

    def _scene6(self, t, fade):
        res = t >= 3.0
        for i, (idx, name) in enumerate(S6_TRICK):
            k = _ease((t - 1.0 - i * 0.45) / 0.5)
            if k <= 0:
                continue
            pos = _arc(self.seat[idx], self.spot[idx], k)
            winner = idx == S6_WINNER
            self._card(name, pos, alpha=fade * min(1.0, 0.3 + k),
                       outline=ui_style.GOLD if (res and winner) else None,
                       mark="ok" if (res and winner) else None)


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
