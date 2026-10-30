# gui/round_demos.py
#
# Animované ukážky krokov Priebehu kola „Dražba“ a „Talón“ (okno Pravidlá
# a bodovanie, záložka Pravidlá, 2026-10-29). Rovnaký systém ako ukážka
# štichov (gui/rules_demo.py — TrickRulesDemo): pevné scény, časovanie,
# ovládanie (Predchádzajúce / Ďalšie / bodky / Prehrať), stôl, menovky,
# rámik s textom vpravo hore. Herná obrazovka je zjednodušená: panel
# SKÓRE / KOLO s označením povinnosti (P60), hráč na ťahu, talón uprostred,
# tlačidlá „Dám +10“ a „Dobrý“, bubliny, správa „… vydražil za …“, posuvník
# NAVÝŠIŤ POVINNOSŤ.
#
# Stav dražby v každej scéne sa NEVYMÝŠĽA — prehrá sa skutočnou triedou
# game.bidding.Bidding (kto je na rade = rovnaké pravidlo ako
# Screen._get_next_bidder_index). Talón (odhodenie, zákaz esa a desiatky,
# body odhodených kariet) overuje verify_round_demos() skutočnými triedami
# Round / Hand / Player — tester/regression_rules_demo.py.
#
# Texty sú pracovné (user 2026-10-29) — finálnu štylistiku doladíme.

import math

import pygame

from gui import ui_style
from gui.rules_demo import (TrickRulesDemo, SEATS, NAME_DIM, GREEN, RED,
                            _ease, _arc, _lerp, _wrap)
from config import MIN_BID, BID_STEP, MAX_BID, CARD_BACK_IMAGE

BUBBLE_BODY = (20, 13, 8)
BID_COLOR = ui_style.BTN_TEXT_HOVER            # DÁVAM … (ako v hre)
PASS_COLOR = (170, 155, 135)                   # Ja som DOBRÝ (ako v hre)
OUT_NAME = (95, 84, 70)                        # hráč, ktorý povedal Dobrý
PANEL_FILL = (17, 11, 7, 235)
ACTIVE = (255, 214, 140)                       # hráč na ťahu v paneli SKÓRE


# ----------------------------------------------------------------------
# Dražba — scény a ich priebeh
# ----------------------------------------------------------------------

BID_SCENES = (
    ("Hráč s povinnosťou",
     f"Jeden hráč má povinnosť: hrá aspoň za {MIN_BID} bodov. Každé kolo sa "
     "povinnosť posunie na ďalšieho hráča v smere hry."),
    ("Prihodiť o 10",
     f"Na rade je hráč po povinnom. Tlačidlom „Dám +{BID_STEP}“ ponúkne "
     f"o {BID_STEP} bodov viac."),
    ("„Dobrý“ — odstúpenie",
     "Kto nechce prihodiť, povie „Dobrý“. Z dražby vypadne a ďalej už nedraží."),
    ("Dražba ide dokola",
     "Na rade sú postupne všetci, ktorí ešte nepovedali „Dobrý“ — aj hráč "
     "s povinnosťou."),
    ("Víťaz dražby",
     "Kto ostane posledný, vyhral dražbu. Musí uhrať aspoň toľko bodov, "
     "koľko vydražil."),
    ("Nikto neprihodil",
     f"Ak všetci ostatní povedia „Dobrý“, hráč s povinnosťou hrá za {MIN_BID}."),
)

# Scéna: povinnosť (index hráča), akcie pred scénou (bez animácie), akcie
# scény. Akcia = (hráč, suma) alebo (hráč, None) = Dobrý. Scény 2–5 sú
# jedna dražba po kúskoch.
BID_SCRIPTS = (
    None,                                                       # rotácia
    (2, (), ((0, 60),)),
    (2, ((0, 60),), ((1, None),)),
    (2, ((0, 60), (1, None)), ((2, 70),)),
    (2, ((0, 60), (1, None), (2, 70)), ((0, None),)),
    (1, (), ((2, None), (0, None))),
)
ROTATION = (0, 1, 2)            # scéna 1: povinnosť v 1., 2., 3. kole
ACT_T0, ACT_STEP = 2.0, 2.2     # čas prvej akcie v scéne, odstup akcií


def _next_bidder(bidding) -> int | None:
    """Kto je na rade — rovnako ako Screen._get_next_bidder_index."""
    if bidding.bidding_over:
        return None
    n = len(bidding.players)
    for i in range(1, n + 1):
        idx = (bidding.highest_bidder_index + i) % n
        if bidding.active[idx]:
            return idx
    return None


def replay_bidding(obligation: int, actions) -> tuple[list[dict], list[str]]:
    """Prehrá akcie skutočnou dražbou. Vráti stavy (pred 1. akciou a po
    každej) a zoznam chýb (akcia mimo poradia, neplatná ponuka)."""
    from game.bidding import Bidding
    from game.player import Player
    players = [Player(name, index=i) for i, name in enumerate(SEATS)]
    b = Bidding(players, obligation)

    def snap():
        return {"bid": b.current_bid, "high": b.highest_bidder_index,
                "active": list(b.active), "over": b.bidding_over,
                "turn": _next_bidder(b)}

    states, errors = [snap()], []
    for who, amount in actions:
        if states[-1]["turn"] != who:
            errors.append(f"na rade je {states[-1]['turn']}, nie {who}")
        if amount is None:
            b.pass_bid(who)
        elif not b.place_bid(who, amount):
            errors.append(f"ponuka {amount} hráča {who} je neplatná")
        states.append(snap())
    return states, errors


# ----------------------------------------------------------------------
# Talón — karty scén
# ----------------------------------------------------------------------

TALON_SCENES = (
    ("Talón dostane víťaz dražby",
     "Talón sa otočí, aby ho videli všetci. Víťaz dražby si obe karty "
     "vezme do ruky."),
    ("Eso ani desiatku nie",
     "Teraz máš 12 kariet a dve musíš odhodiť. Eso ani desiatku odhodiť "
     "nesmieš."),
    ("Odhoď dve karty",
     "Vyber dve karty, ktoré nechceš, a odhoď ich. V ruke ti ostane 10 kariet."),
    ("Body odhodených kariet",
     "Body odhodených kariet sa ti započítajú, ako keby si ich zobral "
     "v štichu."),
    ("Navýšenie povinnosti",
     "Po prezretí talónu môžeš povinnosť ešte zvýšiť. Znížiť ju nemôžeš."),
)
T_BID = 60                       # Hráč vydražil za 60
T_RAISE = 100                    # … a po talóne navýši na 100
T_HAND = ("acorn-ace", "acorn-ten", "acorn-king", "acorn-over",
          "leaf-ten", "leaf-nine", "bell-king", "bell-eight",
          "heart-ace", "heart-seven")
T_TALON = ("leaf-ace", "heart-under")
T_DISCARD = ("bell-king", "bell-eight")
T_TRY = "acorn-ten"              # pokus odhodiť desiatku (scéna 2)


def _card_obj(name):
    from game.card import Card
    suit, rank = name.split("-")
    return Card(suit, rank)


def _sorted_names(names) -> tuple:
    """Poradie kariet ako v hre (Hand.sort_hand)."""
    from game.hand import Hand
    h = Hand()
    h.add_cards([_card_obj(n) for n in names])
    h.sort_hand()
    return tuple(c.image_name[:-4] for c in h.cards)


def verify_round_demos() -> list[str]:
    """Overí ukážky Dražby a Talónu skutočnou logikou hry."""
    from game.game_state import GameState
    from game.player import Player
    from game.round import Round
    errors = []

    # Dražba — povinnosť sa posúva (GameState._advance_obligation)
    class _G:
        obligation_index = ROTATION[0]
    g = _G()
    for nxt in ROTATION[1:]:
        GameState._advance_obligation(g)
        if g.obligation_index != nxt:
            errors.append(f"dražba/scéna 1: povinnosť ide na {g.obligation_index}, "
                          f"nie na {nxt}")
    for no, script in enumerate(BID_SCRIPTS, 1):
        if script is None:
            continue
        ob, pre, acts = script
        states, errs = replay_bidding(ob, tuple(pre) + tuple(acts))
        errors += [f"dražba/scéna {no}: {e}" for e in errs]
        if states[0]["bid"] != MIN_BID or states[0]["high"] != ob:
            errors.append(f"dražba/scéna {no}: povinnosť nezačína na {MIN_BID}")
    # scéna 5 — víťaz Počítač 2 za 70, scéna 6 — povinný za 50
    end5 = replay_bidding(2, BID_SCRIPTS[4][1] + BID_SCRIPTS[4][2])[0][-1]
    if not end5["over"] or end5["high"] != 2 or end5["bid"] != 70:
        errors.append("dražba/scéna 5: víťazom nie je Počítač 2 za 70")
    end6 = replay_bidding(1, BID_SCRIPTS[5][2])[0][-1]
    if not end6["over"] or end6["high"] != 1 or end6["bid"] != MIN_BID:
        errors.append(f"dražba/scéna 6: povinný nehrá za {MIN_BID}")

    # Talón — skutočné Round.discard_cards
    def bidder_round(names):
        players = [Player(n, index=i) for i, n in enumerate(SEATS)]
        rnd = Round(players, 0)
        players[0].hand.add_cards([_card_obj(n) for n in names])
        return rnd, players[0]

    hand12 = tuple(T_HAND) + tuple(T_TALON)
    if len(T_HAND) != 10 or len(T_TALON) != 2 or len(set(hand12)) != 12:
        errors.append("talón: ruka nemá 10 + 2 rôzne karty")
    rnd, p = bidder_round(hand12)
    bad = [_card_obj(T_TRY), _card_obj(T_DISCARD[1])]
    if rnd.discard_cards(0, bad):
        errors.append("talón/scéna 2: hra dovolila odhodiť desiatku")
    rnd, p = bidder_round(hand12)
    if not rnd.discard_cards(0, [_card_obj(n) for n in T_DISCARD]):
        errors.append("talón/scéna 3: hra nedovolila odhodiť zvolené karty")
    elif len(p.hand.cards) != 10:
        errors.append("talón/scéna 3: v ruke neostalo 10 kariet")
    elif p.round_points != discard_points():
        errors.append(f"talón/scéna 4: započítané {p.round_points} b, "
                      f"ukážka ukazuje {discard_points()}")
    if not (T_BID < T_RAISE <= MAX_BID and T_RAISE % BID_STEP == 0):
        errors.append("talón/scéna 5: navýšenie mimo rozsahu posuvníka")
    return errors


def discard_points() -> int:
    return sum(_card_obj(n).points for n in T_DISCARD)


# ----------------------------------------------------------------------
# Spoločný základ
# ----------------------------------------------------------------------

class _RoundDemo(TrickRulesDemo):
    SCENE_LEN = 9.0
    HOLD_AT = 7.6

    def __init__(self, canvas):
        super().__init__(canvas)
        self.font_panel = canvas.font(19)
        self.font_bubble = canvas.font(20)
        self.font_msg = canvas.font(24)
        self._text_cache = {}

    def _show_hand_caption(self) -> bool:
        return False

    def layout(self, rect):
        super().layout(rect)
        c = self.canvas
        self.font_panel = c.font(round(19 * self.fs))
        self.font_bubble = c.font(round(20 * self.fs))
        self.font_msg = c.font(round(24 * self.fs))
        self._text_cache = {}

    def _render(self, font, text, _aa, color):
        """Text s cache — panely a bubliny sa kreslia každú snímku (4K)."""
        key = (id(font), text, color)
        surf = self._text_cache.get(key)
        if surf is None:
            if len(self._text_cache) > 400:
                self._text_cache.clear()
            surf = self._text_cache[key] = font.render(text, True, color)
        return surf

    def draw(self, mouse_pos):
        t = self._elapsed()
        self._draw_header()
        self._draw_stage()
        fade = 1.0
        if self.playing and t > self.SCENE_LEN - 1:
            fade = 1 - _ease(t - (self.SCENE_LEN - 1))
        if t < 0.4:
            fade = min(fade, _ease(t / 0.4))
        self._draw_scene(t, fade)
        self._draw_text()
        self._draw_controls(mouse_pos)

    # --- pomocné kreslenie -------------------------------------------------

    def _panel(self, rect, title: str | None = None):
        c = self.canvas
        c.overlay(rect, PANEL_FILL, border_radius=10)
        c.rect(ui_style.GOLD_SOFT, rect, width=1, border_radius=10)
        y = rect.y + 8
        if title:
            s = self._render(self.font_panel, title, True, ui_style.GOLD)
            c.blit(s, s.get_rect(centerx=rect.centerx, top=y))
            y += s.get_height() + 5
            c.line((70, 54, 34), (rect.x + 12, y), (rect.right - 12, y), 1)
            y += 7
        return y

    def _row(self, rect, y, label, value, value_color=None, flash=0.0):
        """Riadok panela KOLO: popis vľavo, hodnota vpravo."""
        c = self.canvas
        h = self.font_panel.get_height() + 6
        if flash > 0:
            a = round(flash * 6) * 14
            if a:
                c.overlay((rect.x + 6, y - 2, rect.width - 12, h),
                          (255, 214, 140, a), border_radius=6)
        s = self._render(self.font_panel, label, True, ui_style.TEXT_DIM)
        c.blit(s, (rect.x + 14, y + 1))
        v = self._render(self.font_panel, value, True, value_color or ui_style.GOLD)
        c.blit(v, v.get_rect(right=rect.right - 14, top=y + 1))
        return y + h

    def _bubble(self, text, anchor, below, color, alpha: float = 1.0,
                area: pygame.Rect | None = None):
        """Bublina ako v hre (tmavé telo, rám a text vo farbe významu),
        chvost k menovke `anchor`; `below` = True pod menovkou, False nad
        ňou, "right" = vpravo vedľa (anchor = pravý okraj menovky)."""
        if alpha <= 0.05:
            return
        c = self.canvas
        s = self._render(self.font_bubble, text, True, color)
        w, h = s.get_width() + 26, s.get_height() + 14
        ax, ay = anchor
        r = pygame.Rect(0, 0, w, h)
        gap = round(40 * self.fs)
        if below == "right":
            r.midleft = (ax + 18, ay)
        else:
            r.center = (ax, ay + gap if below else ay - gap)
        if area is not None:
            r.clamp_ip(area)
        a = int(255 * min(1.0, alpha))
        body = (*BUBBLE_BODY, round(235 * min(1.0, alpha)))
        tx = max(r.x + 14, min(r.right - 14, ax))
        if below == "right":
            tail = [(r.x + 1, r.centery - 8), (r.x + 1, r.centery + 8), (r.x - 10, r.centery)]
        elif below:
            tail = [(tx - 9, r.y + 1), (tx + 9, r.y + 1), (tx, r.y - 10)]
        else:
            tail = [(tx - 9, r.bottom - 1), (tx + 9, r.bottom - 1), (tx, r.bottom + 10)]
        c.overlay(r.move(2, 4), (0, 0, 0, round(90 * min(1.0, alpha))), border_radius=12)
        c.overlay(r, body, border_radius=12)
        if a > 200:
            c.polygon(BUBBLE_BODY, tail)
            c.rect(color, r, width=2, border_radius=12)
            c.line(color, tail[0], tail[2], 2)
            c.line(color, tail[1], tail[2], 2)
        s = self._render(self.font_bubble, text, True, color)
        if a < 255:
            s = s.copy()
            s.set_alpha(a)
        c.blit(s, s.get_rect(center=r.center))

    def _message(self, text, center, alpha: float = 1.0):
        """Správa ako v hre („Hráč vydražil za 60“)."""
        if alpha <= 0.05:
            return
        c = self.canvas
        s = self._render(self.font_msg, text, True, ui_style.GOLD)
        r = s.get_rect(center=center).inflate(30, 16)
        area = getattr(self, "table_area", None)
        if area is not None:
            r.clamp_ip(area)
        c.overlay(r.move(2, 4), (0, 0, 0, round(100 * alpha)), border_radius=10)
        c.overlay(r, (20, 13, 8, round(235 * alpha)), border_radius=10)
        if alpha > 0.8:
            c.rect(ui_style.GOLD_SOFT, r, width=2, border_radius=10)
        if alpha < 1:
            s = s.copy()
            s.set_alpha(int(255 * alpha))
        c.blit(s, s.get_rect(center=r.center))
        return r

    def _chip(self, text, center, alpha=1.0, scale=1.0):
        """Žetón s hodnotou (P50, +4) — zlatý ako medailóny s bodmi."""
        if alpha <= 0.05:
            return
        c = self.canvas
        font = c.font(max(12, round(20 * scale)))
        s = font.render(text, True, (48, 28, 8))
        r = s.get_rect(center=(round(center[0]), round(center[1]))).inflate(
            round(20 * scale), round(10 * scale))
        a = round(255 * min(1.0, alpha))
        c.overlay(r.move(1, 3), (0, 0, 0, round(110 * alpha)), border_radius=r.height // 2)
        c.overlay(r, (222, 172, 64, a), border_radius=r.height // 2)
        if alpha > 0.8:
            c.rect((120, 82, 26), r, width=2, border_radius=r.height // 2)
        if a < 255:
            s = s.copy()
            s.set_alpha(a)
        c.blit(s, s.get_rect(center=r.center))

    def _card_sized(self, name, center, w, alpha=1.0, outline=None, mark=None,
                    flip=1.0, back=False):
        """Karta šírky w; flip 0…1 = zúženie pri otáčaní (otočenie karty)."""
        c = self.canvas
        h = round(w / (181 / 293))
        fw = max(2, round(w * abs(flip) / 4) * 4) if flip < 1 else w
        fname = CARD_BACK_IMAGE if back else f"{name}.png"
        try:
            img = c.card(fname, lsize=(fw, h))
        except (FileNotFoundError, pygame.error):
            return None
        rect = img.get_rect(center=(round(center[0]), round(center[1])))
        a = int(255 * max(0.0, min(1.0, alpha)))
        if a <= 0:
            return rect
        if a > 200 and fw == w:
            c.overlay(rect.move(3, 5), (0, 0, 0, 100), border_radius=7)
        if a < 255:
            img = img.copy()
            img.set_alpha(a)
        c.blit(img, rect)
        if outline and a > 40:
            c.rect(outline, rect.inflate(6, 6), width=3, border_radius=9)
        if mark and a > 40:
            ic = self._icon(mark, round(34 * self.k))
            if ic:
                c.blit(ic, ic.get_rect(center=(rect.right - 4, rect.top + 4)))
        return rect

    def _press(self, rect, label, pressed: bool, tier=3, alpha=1.0):
        """Tlačidlo hry; `pressed` = hráč naň práve klikne (zvýraznenie)."""
        if alpha < 0.5:
            return
        r = rect.move(0, 2) if pressed else rect
        ui_style.draw_button(self.canvas, r, label, self.font_btn, tier,
                             hover=pressed, shadow=not pressed)


# ----------------------------------------------------------------------
# DRAŽBA
# ----------------------------------------------------------------------

class BiddingDemo(_RoundDemo):
    TITLE = "DRAŽBA"
    SCENES = BID_SCENES

    def __init__(self, canvas):
        super().__init__(canvas)
        self._replays = {}
        for i, script in enumerate(BID_SCRIPTS):
            if script is not None:
                ob, pre, acts = script
                states, _ = replay_bidding(ob, tuple(pre) + tuple(acts))
                self._replays[i] = (ob, len(pre), tuple(pre) + tuple(acts), states)

    def layout(self, rect):
        super().layout(rect)
        k = self.k
        cx, cy = self.center
        self.talon_c = (cx, cy - round(14 * k))
        self.tw = round(self.cw * 0.72)
        self.chip_c = (cx, cy - round(108 * k))
        bw, bh, g = round(118 * k), round(36 * k), round(14 * k)
        by = cy + round(64 * k)
        self.btn_bid_r = pygame.Rect(cx - g // 2 - bw, by - bh // 2, bw, bh)
        self.btn_pass_r = pygame.Rect(cx + g // 2, by - bh // 2, bw, bh)
        self.msg_c = (cx, by)
        # oblasť stola (bubliny nesmú zasahovať do textu vpravo)
        st = self.stage
        self.table_area = pygame.Rect(st.x + 6, st.y + 6, self.text_x - 12 - st.x,
                                      st.height - 12)
        # panel SKÓRE / KOLO vpravo pod textom (rovnaká poloha vo všetkých scénach)
        top = max(self._text_box(i)[0].bottom for i in range(len(self.SCENES))) + 14
        # SKÓRE a KOLO vedľa seba (ako v hre), na šírku stĺpca s textom
        fh = self.font_panel.get_height()
        need = 8 + fh + 12 + 3 * (fh + 9) + 8
        self.info_r = pygame.Rect(self.text_x, top, st.right - 18 - self.text_x,
                                  min(need, st.bottom - 14 - top))

    # --- časovanie ------------------------------------------------------

    def _state_at(self, t):
        """(stav dražby, index stavu, čas poslednej akcie) v čase t."""
        ob, n_pre, acts, states = self._replays[self.scene]
        done = n_pre
        last_t = None
        for j in range(n_pre, len(acts)):
            at = ACT_T0 + (j - n_pre) * ACT_STEP
            if t >= at:
                done = j + 1
                last_t = at
        return states[done], done, last_t

    # --- kreslenie --------------------------------------------------------

    def _draw_scene(self, t, fade):
        if self.scene == 0:
            self._scene_rotation(t, fade)
            return
        ob, n_pre, acts, states = self._replays[self.scene]
        state, done, last_t = self._state_at(t)
        prev = states[done - 1] if done > 0 else state
        over = state["over"]
        winner = state["high"] if over else None
        # kto je na rade (pred koncom) — zvýraznená menovka a šípka v paneli
        turn = state["turn"]
        self._draw_talon(fade)
        bid_flash = 0.0
        if last_t is not None and prev["bid"] != state["bid"]:
            bid_flash = max(0.0, 1 - (t - last_t) / 1.2)
        self._chip(f"{state['bid']}", self.chip_c, fade, scale=1.25 + 0.25 * bid_flash)
        cap = self._render(self.font_seat, "Dražba", True, NAME_DIM)
        self.canvas.blit(cap, cap.get_rect(centerx=self.chip_c[0],
                                           bottom=self.chip_c[1] - round(24 * self.k)))
        # menovky
        for idx in range(3):
            if winner is not None:
                mode = "win" if idx == winner else "out"
            elif not state["active"][idx]:
                mode = "out"
            else:
                mode = "turn" if idx == turn else "normal"
            self._seat_label(idx, mode)
        # tlačidlá Hráča — keď je na rade; klik tesne pred jeho akciou
        nxt = done if done < len(acts) else None
        if not over and turn == 0:
            press = None
            if nxt is not None and acts[nxt][0] == 0:
                at = ACT_T0 + (nxt - n_pre) * ACT_STEP
                if at - 0.55 <= t < at:
                    press = "bid" if acts[nxt][1] else "pass"
            self._press(self.btn_bid_r, f"Dám +{BID_STEP}", press == "bid", tier=1, alpha=fade)
            self._press(self.btn_pass_r, "Dobrý", press == "pass", tier=3, alpha=fade)
        # bubliny — posledná akcia každého hráča v tejto scéne
        latest = {}
        for j in range(n_pre, done):
            latest[acts[j][0]] = j
        for who, j in latest.items():
            at = ACT_T0 + (j - n_pre) * ACT_STEP
            age = t - at
            a = min(1.0, age / 0.25) * fade
            amount = acts[j][1]
            text = f"DÁVAM {amount}!" if amount else "Ja som DOBRÝ"
            if self._seat_side(who) == "bottom":      # Hráč — vpravo vedľa menovky
                lx, ly = self.label[who]
                half = self.font_seat.size(SEATS[who])[0] / 2 + 7
                anchor, side = (round(lx + half), ly), "right"
            else:
                anchor, side = self.label[who], True
            self._bubble(text, anchor, side,
                         color=BID_COLOR if amount else PASS_COLOR, alpha=a,
                         area=self.table_area)
        if over and last_t is not None:
            a = _ease((t - last_t - 0.6) / 0.5) * fade
            self._message(f"{SEATS[winner]} vydražil za {state['bid']}", self.msg_c, a)
        # panel SKÓRE / KOLO
        p_flash = 0.0
        if last_t is not None and prev["high"] != state["high"]:
            p_flash = max(0.0, 1 - (t - last_t) / 1.4)
        self._info_panel(state["high"], state["bid"], None if over else turn,
                         p_flash, "Talón" if over and t - last_t > 1.2 else "Dražba")

    def _seat_side(self, idx) -> str:
        from gui import layout
        return layout.game().seat_of.get(idx, "bottom")

    def _seat_label(self, idx, mode):
        c = self.canvas
        pos = self.label[idx]
        color = {"turn": ui_style.GOLD, "win": ui_style.GOLD,
                 "out": OUT_NAME}.get(mode, NAME_DIM)
        t = self._render(self.font_seat, SEATS[idx], True, color)
        r = t.get_rect(center=pos).inflate(14, 6)
        c.rect((15, 10, 6), r, border_radius=6)
        strong = mode in ("turn", "win")
        c.rect(ui_style.GOLD if strong else (70, 54, 34), r, width=2 if strong else 1,
               border_radius=6)
        c.blit(t, t.get_rect(center=pos))
        if mode == "win":
            ic = self._icon("ok", round(26 * self.k))
            if ic:
                c.blit(ic, ic.get_rect(center=(r.right + 2, r.top + 2)))
        return r

    def _draw_talon(self, fade):
        x, y = self.talon_c
        g = round(6 * self.k)
        for j in (-1, 1):
            self._card_sized(None, (x + j * (self.tw + g) // 2, y), self.tw,
                             alpha=fade, back=True)

    def _info_panel(self, high, bid, turn, p_flash, phase="Dražba", round_no=None):
        """Zjednodušený horný panel hry: SKÓRE (P60, hráč na ťahu) a vedľa
        neho KOLO (fáza / kolo, povinnosť)."""
        c = self.canvas
        g = 14
        score_w = round((self.info_r.width - g) * 0.52)
        r = pygame.Rect(self.info_r.x, self.info_r.y, score_w, self.info_r.height)
        kr = pygame.Rect(r.right + g, r.y, self.info_r.right - r.right - g, r.height)
        y = self._panel(r, "SKÓRE")
        row_h = self.font_panel.get_height() + 9
        for idx in range(3):
            name = SEATS[idx] + (f" (P{bid})" if idx == high else "")
            col = ACTIVE if idx == turn else ui_style.TEXT
            if idx == high and p_flash > 0:
                a = round(p_flash * 6) * 14
                if a:
                    c.overlay((r.x + 6, y - 2, r.width - 12, row_h - 2),
                              (255, 214, 140, a), border_radius=6)
            if idx == turn:
                cy = y + self.font_panel.get_height() // 2 + 1
                c.polygon(ACTIVE, [(r.x + 14, cy - 6), (r.x + 22, cy), (r.x + 14, cy + 6)])
            s = self._render(self.font_panel, name, True, col)
            c.blit(s, (r.x + 30, y))
            z = self._render(self.font_panel, "0", True, ui_style.TEXT_DIM)
            c.blit(z, z.get_rect(right=r.right - 14, top=y))
            y += row_h
        y = self._panel(kr, "KOLO")
        if round_no is not None:
            y = self._row(kr, y, "Kolo:", f"{round_no}.")
        else:
            y = self._row(kr, y, "Fáza:", phase, ui_style.TEXT)
        self._row(kr, y, "Povinnosť:", f"{SEATS[high]} / {bid}", flash=p_flash)

    # --- scéna 1: povinnosť sa posúva ---------------------------------------

    def _p_spot(self, idx):
        """Kde leží žetón povinnosti pri menovke hráča."""
        x, y = self.label[idx]
        if self._seat_side(idx) == "bottom":
            return (x + round(92 * self.k), y)
        return (x, y + round(40 * self.k))

    def _scene_rotation(self, t, fade):
        self._draw_talon(fade)
        # 3 kolá: žetón stojí, potom preletí k ďalšiemu hráčovi
        stops = (0.0, 2.6, 5.2)
        fly = 0.8
        holder, pos, flash = ROTATION[0], self._p_spot(ROTATION[0]), 0.0
        rnd = 1
        for i in range(1, len(ROTATION)):
            t0 = stops[i] - fly
            if t >= t0:
                k = _ease((t - t0) / fly)
                pos = _arc(self._p_spot(ROTATION[i - 1]), self._p_spot(ROTATION[i]), k, 0.25)
                if k >= 1:
                    holder, rnd = ROTATION[i], i + 1
                    flash = max(0.0, 1 - (t - stops[i]) / 1.2)
        for idx in range(3):
            self._seat_label(idx, "turn" if idx == holder else "normal")
        self._chip(f"P{MIN_BID}", pos, fade, scale=1.1)
        self._message(f"{rnd}. kolo", self.msg_c, fade)
        self._info_panel(holder, MIN_BID, None, flash, round_no=rnd)


# ----------------------------------------------------------------------
# TALÓN
# ----------------------------------------------------------------------

class TalonDemo(_RoundDemo):
    TITLE = "TALÓN"
    SCENES = TALON_SCENES

    def layout(self, rect):
        super().layout(rect)
        st = self.stage
        k = self.k
        # karta v ruke — hore musí ostať miesto na talón a správu pod ním
        self.hh = min(round(self.cw * 0.95 / (181 / 293)), (st.height - 150) // 2)
        self.hw = round(self.hh * (181 / 293))
        self.hand_cy = st.bottom - 14 - self.hh // 2
        self.lift = round(22 * k)
        self.info_r = pygame.Rect(st.x + 16, st.y + 16, round(240 * k), 0)
        self.info_r.height = (8 + self.font_panel.get_height() + 12
                              + 3 * (self.font_panel.get_height() + 6) + 8)
        mid_x = (self.info_r.right + self.text_x) // 2
        self.talon_c = (mid_x, st.y + 18 + self.hh // 2)
        # odhodené karty ležia tam, kde bol talón (talón je už v ruke)
        self.discard_c = (self.talon_c[0] - round(self.hw * 0.28), self.talon_c[1])
        self.msg_c = (mid_x, self.talon_c[1] + self.hh // 2 + 32)
        self.table_area = pygame.Rect(st.x + 8, st.y + 8, self.text_x - 16 - st.x,
                                      st.height - 16)
        self.h10 = _sorted_names(T_HAND)
        self.h12 = _sorted_names(T_HAND + T_TALON)
        self.h10b = tuple(n for n in self.h12 if n not in T_DISCARD)

    def _hand_x(self, i, n):
        st = self.stage
        step = min(round(self.hw * 1.12), (st.width - 40 - self.hw) // max(1, n - 1))
        x0 = st.centerx - (n - 1) * step // 2
        return x0 + i * step

    def _draw_hand(self, before, after, k, fade, lifted=None, outlines=None,
                   marks=None, skip=(), shake=None):
        """Ruka: karty sa plynule presúvajú z rozloženia `before` (zoznam
        mien) do `after` podľa k. Karty, ktoré v `before` nie sú, kreslí
        volajúci (prilietajú). lifted = {meno: 0…1} vysunutie."""
        lifted = lifted or {}
        rects = {}
        for i, name in enumerate(after):
            if name in skip:
                continue
            x1 = self._hand_x(i, len(after))
            if name in before:
                x0 = self._hand_x(before.index(name), len(before))
                x = x0 + (x1 - x0) * k
            else:
                continue
            y = self.hand_cy - self.lift * lifted.get(name, 0.0)
            if shake and name == shake[0]:
                x += math.sin(shake[1] * math.pi * 6) * 6 * (1 - shake[1])
            rects[name] = self._card_sized(name, (x, y), self.hw, fade,
                                           outline=(outlines or {}).get(name),
                                           mark=(marks or {}).get(name))
        return rects

    def _info(self, bid, points, flash_bid=0.0, flash_pts=0.0):
        r = self.info_r
        y = self._panel(r, "KOLO")
        y = self._row(r, y, "Fáza:", "Talón", ui_style.TEXT)
        y = self._row(r, y, "Povinnosť:", f"Hráč / {bid}", flash=flash_bid)
        self._row(r, y, "Body zatiaľ:", f"{points} / {bid}", flash=flash_pts)

    def _discard_label(self, fade):
        if fade < 0.5:
            return
        cap = self._render(self.font_seat, "Odhodené", True, NAME_DIM)
        self.canvas.blit(cap, cap.get_rect(centerx=self.discard_c[0],
                                           bottom=self.discard_c[1] - self.hh // 2 - 6))

    def _hand_caption(self):
        cap = self._render(self.font_seat, "Tvoja ruka", True, NAME_DIM)
        self.canvas.blit(cap, (self._hand_x(0, 12) - self.hw // 2,
                               self.hand_cy - self.hh // 2 - self.lift - cap.get_height() - 2))

    def _discard_pile(self, fade, face_up=0.0):
        """Odhodené karty pri víťazovi — rubom nahor, alebo otočené."""
        x, y = self.discard_c
        dx = round(self.hw * 0.56)
        rects = []
        for j, name in enumerate(T_DISCARD):
            pos = (x + j * dx, y)
            if face_up <= 0:
                rects.append(self._card_sized(name, pos, self.hw, fade, back=True))
            else:
                k = min(1.0, face_up)
                flip = abs(1 - 2 * k)
                rects.append(self._card_sized(name, pos, self.hw, fade, flip=flip,
                                              back=k < 0.5))
        return rects

    def _draw_scene(self, t, fade):
        getattr(self, f"_t{self.scene + 1}")(t, fade)

    # --- 1: talón do ruky ---------------------------------------------------

    def _t1(self, t, fade):
        self._info(T_BID, 0)
        self._message(f"Hráč vydražil za {T_BID}", self.msg_c,
                      _ease((t - 0.3) / 0.4) * fade * (1 - _ease((t - 2.4) / 0.4)))
        flip_k = _ease((t - 1.0) / 0.6)                       # otočenie talónu
        fly_k = _ease((t - 2.6) / 1.0)                        # let do ruky
        x, y = self.talon_c
        g = round(8 * self.k)
        for j, name in enumerate(T_TALON):
            start = (x + (j * 2 - 1) * (self.hw + g) // 2, y)
            i = self.h12.index(name)
            end = (self._hand_x(i, 12), self.hand_cy)
            if fly_k <= 0:
                flip = abs(1 - 2 * flip_k)
                self._card_sized(name, start, self.hw, fade, flip=flip,
                                 back=flip_k < 0.5)
        self._hand_caption()
        self._draw_hand(self.h10, self.h12, fly_k, fade)
        if fly_k > 0:
            for j, name in enumerate(T_TALON):
                start = (x + (j * 2 - 1) * (self.hw + g) // 2, y)
                end = (self._hand_x(self.h12.index(name), 12), self.hand_cy)
                self._card_sized(name, _arc(start, end, fly_k, 0.12), self.hw, fade,
                                 outline=ui_style.GOLD if fly_k >= 1 else None)

    # --- 2: eso ani desiatku nie ------------------------------------------

    def _t2(self, t, fade):
        self._info(T_BID, 0)
        self._hand_caption()
        mark_a = t >= 0.8
        forbidden = [n for n in self.h12 if n.split("-")[1] in ("ace", "ten")]
        outlines, marks = {}, {}
        if mark_a:
            for n in forbidden:
                outlines[n], marks[n] = RED, "circlex"
        if t >= 4.2:
            for n in self.h12:
                if n not in forbidden:
                    outlines[n] = GREEN
        lift = {}
        shake = None
        if 1.6 <= t < 2.4:
            lift[T_TRY] = _ease((t - 1.6) / 0.3)
        elif 2.4 <= t < 3.0:
            lift[T_TRY] = 1 - _ease((t - 2.4) / 0.5)
            shake = (T_TRY, (t - 2.4) / 0.6)
        self._draw_hand(self.h12, self.h12, 1.0, fade, lifted=lift, outlines=outlines,
                        marks=marks, shake=shake)
        if t >= 2.4:
            self._message("Eso a desiatku nemôžeš zahodiť!", self.msg_c,
                          _ease((t - 2.4) / 0.3) * fade)

    # --- 3: odhoď dve karty -------------------------------------------------

    def _t3(self, t, fade):
        self._info(T_BID, 0)
        self._hand_caption()
        lift = {}
        for j, name in enumerate(T_DISCARD):
            lift[name] = _ease((t - 1.0 - j * 0.6) / 0.3)
        fly_k = _ease((t - 2.8) / 0.9)
        outl = {n: ui_style.GOLD for n in T_DISCARD if lift[n] > 0.5}
        self._draw_hand(self.h12, self.h10b, fly_k, fade, lifted=lift, outlines=outl,
                        skip=T_DISCARD)
        if fly_k > 0:
            self._discard_label(fade)
        dx = round(self.hw * 0.56)
        for j, name in enumerate(T_DISCARD):
            start = (self._hand_x(self.h12.index(name), 12), self.hand_cy - self.lift)
            end = (self.discard_c[0] + j * dx, self.discard_c[1])
            pos = _arc(start, end, fly_k, 0.15)
            if fly_k < 1:
                self._card_sized(name, pos, self.hw, fade,
                                 outline=ui_style.GOLD if fly_k == 0 and lift[name] > 0.5 else None,
                                 flip=abs(1 - 2 * fly_k) if fly_k > 0 else 1.0,
                                 back=fly_k >= 0.5)
            else:
                self._card_sized(name, pos, self.hw, fade, back=True)
        if fly_k >= 1:
            self._message("V ruke 10 kariet", self.msg_c, _ease((t - 3.9) / 0.4) * fade)

    # --- 4: body odhodených kariet --------------------------------------

    def _t4(self, t, fade):
        pts = discard_points()
        fly_k = _ease((t - 3.0) / 0.8)
        got = fly_k >= 1
        self._info(T_BID, pts if got else 0,
                   flash_pts=max(0.0, 1 - (t - 3.8) / 1.4) if got else 0.0)
        self._hand_caption()
        self._draw_hand(self.h10b, self.h10b, 1.0, fade)
        self._discard_label(fade)
        rects = self._discard_pile(fade, face_up=_ease((t - 0.8) / 0.6))
        if t >= 1.8:
            a = _ease((t - 1.8) / 0.3) * fade
            for name, r in zip(T_DISCARD, rects):
                if r is not None:
                    self._chip(str(_card_obj(name).points), (r.centerx, r.bottom - 6), a)
        if 2.6 <= t and not got:
            x = self.discard_c[0] + round(self.hw * 0.28)
            start = (x, self.discard_c[1] - self.hh // 2)
            end = (self.info_r.right - round(40 * self.k), self.info_r.bottom - 14)
            self._chip(f"+{pts}", _lerp(start, end, fly_k), fade * _ease((t - 2.6) / 0.3), 1.2)

    # --- 5: navýšenie povinnosti ----------------------------------------

    def _t5(self, t, fade):
        k = _ease((t - 1.2) / 1.6)
        value = T_BID + round(k * (T_RAISE - T_BID) / BID_STEP) * BID_STEP
        done = t >= 3.6
        flash = max(0.0, 1 - (t - 3.6) / 1.4) if done else 0.0
        bid = T_RAISE if done else T_BID
        self._info(bid, discard_points(), flash_bid=flash, flash_pts=flash)
        self._hand_caption()
        self._draw_hand(self.h10b, self.h10b, 1.0, fade)
        self._slider((self.talon_c[0], self.stage.y + 14 + round(88 * self.k)), value,
                     pressed=3.1 <= t < 3.6, alpha=fade * (1 - _ease((t - 4.0) / 0.4)))
        if done:
            self._message(f"Povinnosť {T_RAISE}", self.msg_c,
                          _ease((t - 4.2) / 0.4) * fade)

    def _slider(self, center, value, pressed, alpha):
        """Zjednodušený posuvník NAVÝŠIŤ POVINNOSŤ z hry (min = povinnosť)."""
        if alpha < 0.3:
            return
        c = self.canvas
        k = self.k
        w = min(round(300 * k), self.text_x - self.info_r.right - 24)
        h = round(176 * k)
        r = pygame.Rect(0, 0, w, h)
        r.center = center
        c.overlay(r.move(2, 5), (0, 0, 0, 110), border_radius=10)
        c.overlay(r, PANEL_FILL, border_radius=10)
        c.rect(ui_style.GOLD_SOFT, r, width=2, border_radius=10)
        y = self._panel_title(r, "NAVÝŠIŤ POVINNOSŤ")
        track = pygame.Rect(r.x + 26, y + round(44 * k), w - 52, 6)
        ratio = (value - T_BID) / (MAX_BID - T_BID)
        kx = track.x + round(ratio * track.width)
        v = self._render(self.font_msg, str(value), True, ui_style.TEXT)
        c.blit(v, v.get_rect(centerx=kx, bottom=track.y - 8))
        c.rect((60, 44, 26), track, border_radius=3)
        c.rect(ui_style.GOLD, (track.x, track.y, kx - track.x, track.height), border_radius=3)
        c.circle(ui_style.GOLD, (kx, track.centery), round(11 * k))
        for val, x in ((T_BID, track.x), (MAX_BID, track.right)):
            s = self._render(self.font_seat, str(val), True, ui_style.TEXT_DIM)
            c.blit(s, s.get_rect(centerx=x, top=track.bottom + 8))
        btn = pygame.Rect(r.x + 30, r.bottom - round(46 * k), w - 60, round(34 * k))
        self._press(btn, "Potvrdiť", pressed, tier=1)

    def _panel_title(self, r, title):
        c = self.canvas
        s = self._render(self.font_panel, title, True, ui_style.GOLD)
        c.blit(s, s.get_rect(centerx=r.centerx, top=r.y + 8))
        y = r.y + 8 + s.get_height() + 5
        c.line((70, 54, 34), (r.x + 12, y), (r.right - 12, y), 1)
        return y
