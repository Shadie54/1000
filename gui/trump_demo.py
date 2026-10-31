# Animované hlásenie tromfu; príklady nemenia stav rozohratej hry.
import pygame
from gui import ui_style
from gui.rules_demo import TrickRulesDemo, _ease, _arc, _wrap, GREEN, RED

PAIR = ("acorn-king", "acorn-over")
HAND = ("heart-seven", *PAIR, "acorn-ten")
TEXTS = {
    "pair": ("Kráľ a horník", "Tromf môžeš nahlásiť, ak máš v ruke kráľa a horníka rovnakej farby."),
    "classic": ("Kedy môžeš hlásiť tromf?", "Tromf môžeš zahlásiť najskôr v 2. štichu, keď ho začínaš ty."),
    "first": ("Hlásenie už v prvom štichu", "Víťaz dražby môže nahlásiť tromf už v prvom štichu, ak má dostatočne vysokú povinnosť."),
    "bid": ("Povinnosť musí byť vyššia", "Ak chceš nahlásiť tromf v prvom štichu, tvoja povinnosť musí byť aspoň o 10 bodov vyššia než hodnota hlášky."),
    "declare": ("Ako nahlásiť tromf?", "Začni štich kráľom alebo horníkom z dvojice. Potom potvrď hlásenie tromfu alebo zahraj bez neho."),
    "effect": ("Tromf je nahlásený!", "Nahlásená farba sa okamžite stáva tromfovou a za hlášku získavaš príslušné body."),
    "win": ("Musíš získať aspoň jeden štich", "Ak nahlásiš tromf už v prvom štichu, musíš počas kola získať aspoň jeden štich. Nemusí to však byť hneď ten prvý."),
    "change": ("Zmena tromfu", "Ak neskôr niekto nahlási inú farbu, tá sa stáva novým tromfom. Body za predchádzajúce hlášky zostávajú."),
}
# Poradie a víťazi sa overujú skutočnou hernou logikou.
CLASSIC_TRICK = ((2, "leaf-king"), (0, "leaf-ace"), (1, "leaf-seven"))
CLASSIC_HAND = ("leaf-ace", *PAIR, "heart-ten")
CLASSIC_OPENING = ((0, "leaf-ace"), (1, "leaf-king"), (2, "leaf-seven"))
CLASSIC_CHANGE = ((0, "acorn-over"), (1, "acorn-ace"), (2, "acorn-nine"))
AFTER_FIRST_HAND = (*PAIR, "heart-ten")
CHANGE_HAND = AFTER_FIRST_HAND
FIRST_TRICK = ((0, "acorn-over"), (1, "acorn-ace"), (2, "acorn-seven"))
LATER_TRICK = ((1, "acorn-eight"), (2, "acorn-nine"), (0, "acorn-ten"))
FIRST_CHANGE = ((0, "heart-seven"), (1, "heart-ace"), (2, "heart-nine"))
FIRST_HANDS = ((*HAND, "leaf-under"), ("acorn-ace", "acorn-eight", "heart-ace", "bell-king", "bell-over"),
               ("acorn-seven", "acorn-nine", "heart-nine", "leaf-king", "bell-nine"))

class TrumpDemo(TrickRulesDemo):
    VISIBLE_PLAY_HANDS = True
    TITLE = "HLÁSENIE TROMFU"
    SHOW_TRUMP_POINTS = True

    @property
    def SCENE_LEN(self):
        if not self.first_trick_trump:
            return {"pair": 11., "classic": 11., "declare": 5., "effect": 11., "change": 14.}[self.keys[self.scene]]
        return {"pair": 11., "first": 6., "bid": 7., "declare": 5.,
                "effect": 7., "win": 13., "change": 14.}[self.keys[self.scene]]

    @property
    def HOLD_AT(self):
        return self.SCENE_LEN - 1.2

    def __init__(self, canvas, first_trick_trump=False):
        self.first_trick_trump = first_trick_trump
        self.keys = (("pair", "first", "bid", "declare", "effect", "win", "change")
                     if first_trick_trump else ("pair", "classic", "declare", "effect", "change"))
        self.SCENES = tuple(TEXTS[key] for key in self.keys)
        super().__init__(canvas)

    # Rozloženie, mierka, menovky, ruka aj ovládanie sú priamo zo šablóny.
    # Mení sa iba obsah scén, nie súradnice prvkov Pravidiel štichov.

    FIRST_TRICK_NOTICE = (
        "Hlásenie v 1. štichu musí byť povolené v nastaveniach hry. "
        "Inak platia klasické pravidlá – hlásiť možno až od 2. štichu."
    )

    def _notice_layout(self, box):
        font = self.canvas.font(round(18 * self.fs))
        lines = _wrap(self.FIRST_TRICK_NOTICE, font, box.width - 40)
        return font, lines, font.get_height() + 4

    def _text_box(self, scene):
        box, lines = super()._text_box(scene)
        if self.first_trick_trump and scene == 0:
            _, notice, line_h = self._notice_layout(box)
            box.height += 30 + len(notice) * line_h
        return box, lines

    def _draw_text(self):
        super()._draw_text()
        if not self.first_trick_trump or self.scene != 0:
            return
        original, _ = super()._text_box(0)
        font, lines, line_h = self._notice_layout(original)
        y = original.bottom - 2
        self.canvas.line(ui_style.GOLD_SOFT, (original.x + 20, y),
                         (original.right - 20, y), width=1)
        y += 14
        for line in lines:
            self.canvas.blit(font.render(line, True, ui_style.TEXT_DIM),
                             (original.x + 20, y))
            y += line_h

    def _show_hand_caption(self):
        return self.keys[self.scene] not in ("win", "change")

    def _scene_trump(self):
        key = self.keys[self.scene]
        t = self._elapsed()
        if not self.first_trick_trump:
            return self._classic_state(t)["trump"]
        if key == "effect" and t >= 3:
            return "acorn"
        if key == "win":
            return "acorn"
        if key == "change":
            return "bell" if t >= 8.3 else "acorn"
        return None

    def _trump_declarer(self):
        if not self.first_trick_trump:
            return self._classic_state(self._elapsed())["declarer"]
        return "Počítač 1" if self.keys[self.scene] == "change" and self._elapsed() >= 8.3 else "Hráč"

    def _status(self, text, color=None):
        # Po hlásení túto oblasť zaberá herný panel s farbou a bodmi.
        if self._scene_trump():
            return
        # Krátky výsledok nad stolom; podrobné vysvetlenie patrí vpravo.
        surf = self.font_seat.render(text, True, color or ui_style.GOLD)
        cx, cy = self.center
        self.canvas.blit(surf, surf.get_rect(center=(cx, cy - round(135 * self.k))))

    def _round_panel(self, t, fade):
        """Vybrané riadky herného panela KOLO, podobne ako v Talóne."""
        key = self.keys[self.scene]
        if key == "pair":
            return
        from gui.scoreboard import Scoreboard, GOOD, BAD
        from gui.canvas import Canvas, LSurf
        trick = 1 if self.first_trick_trump else 2
        if key == "classic":
            trick = 1 if t < (10.5 if not self.first_trick_trump else 6) else 2
        elif key == "win":
            trick = 1 if t < 7 else 2
        elif key == "change":
            trick = (2 if t < 6 else 3) if not self.first_trick_trump else (3 if t < 6 else 4)
        rows = [("Fáza:", "Štichy", ui_style.TEXT),
                ("Štich:", f"{trick} / 10", ui_style.TEXT)]
        if self.first_trick_trump:
            bid = 100 if key == "bid" and t < 5 else 110
            rows.append(("Povinnosť:", f"Hráč / {bid}", BAD if bid == 100 else ui_style.GOLD))
            declared = key in ("win", "change") or key == "effect" and t >= 3
            if declared:
                done = key == "win" and t >= 10 or key == "change"
                rows.append(("Aspoň 1 štich:", "splnené" if done else "chýba",
                             GOOD if done else BAD))
        # Zmenšený výrez sa zmestí pod ľavého hráča bez presúvania stola.
        source_w, source_h = 260, 50 + 24 * len(rows)
        factor = .8 * self.k
        w, h = round(source_w * factor), round(source_h * factor)
        c = self.canvas
        size = (max(1, round(w * c.s)), max(1, round(h * c.s)))
        cache_key = (tuple(rows), size)
        if getattr(self, "_round_panel_key", None) != cache_key:
            scale = size[0] / source_w
            surface = pygame.Surface((size[0], max(1, round(source_h * scale))), pygame.SRCALPHA)
            panel = Scoreboard(Canvas(surface, scale))
            panel.info_x = panel.panel_y = 0
            panel.info_w, panel.panel_h = source_w, source_h
            panel._draw_panel_bg(0, 0, source_w, source_h)
            panel._draw_panel_title("KOLO", 0, 0, source_w)
            for i, (label, value, color) in enumerate(rows):
                panel._draw_info_row(label, value, 45 + 24 * i, color)
            if surface.get_size() != size:
                surface = pygame.transform.smoothscale(surface, size)
            self._round_panel_key, self._round_panel_image = cache_key, surface
        image = self._round_panel_image.copy()
        image.set_alpha(round(255 * max(0, min(1, fade))))
        rect = pygame.Rect(0, 0, w, h)
        rect.bottomleft = (self.stage.x + round(16 * self.k),
                           self.stage.bottom - round(12 * self.k))
        if self._visible_hands():
            rect.topleft = (self.text_x, self._text_box(self.scene)[0].bottom + 18)
        elif getattr(self, "focus_layout", False):
            top = self._text_box(self.scene)[0].bottom + 18
            # Pri nízkom širokouhlom okne zostane panel na stole;
            # vysvetlenie ani ruka sa nesmú prekryť.
            hand_top = self.hand_y - round(70 * self.k) - self.font_seat.get_height()
            if top + h + 12 <= hand_top:
                rect.topleft = (self.text_x, top)
        c.blit(LSurf(image, w, h), rect)

    def _hand_demo(self, t, fade, play=False, allowed=True):
        k = _ease((t - 1) / 2) if play else 0.0
        color = GREEN if allowed else RED
        self._hand(HAND, fade, moved="acorn-over" if play else None,
                   moved_k=k, dimmed=tuple(n for n in HAND if n not in PAIR),
                   outlines={n: color for n in PAIR} if t >= .6 else {},
                   marks={n: "circlex" for n in PAIR} if not allowed else {})
        if play and self._visible_hands():
            self._play_from_hand(0, "acorn-over", t, 1, 2, fade, hand=HAND,
                                 outline=color if t >= .6 else None,
                                 mark="ok" if t >= 3 and allowed else None, draw_hand=False)
        elif play:
            start = self.hand_pos(HAND.index("acorn-over"), len(HAND))
            pos = _arc(start, self.spot[0], k, bend=.15)
            self._card("acorn-over", pos, .8 + .2 * k, alpha=fade,
                       outline=color if t >= .6 else None,
                       mark="ok" if t >= 3 and allowed else None)

    def _trick(self, plays, t, fade, winner):
        if self._visible_hands():
            for i, (player, name) in enumerate(plays):
                won = t >= 3 and player == winner
                self._play_from_hand(player, name, t, 1 + i * .45, .5, fade,
                                     outline=ui_style.GOLD if won else None,
                                     mark="ok" if won else None)
            return
        # Rovnaké poradie, oblúk, časovanie a výsledok ako v 6. scéne šablóny.
        for i, (player, name) in enumerate(plays):
            k = _ease((t - 1 - i * .45) / .5)
            if k <= 0:
                continue
            pos = _arc(self.seat[player], self.spot[player], k)
            won = t >= 3 and player == winner
            self._card(name, pos, alpha=fade * min(1, .3 + k),
                       outline=ui_style.GOLD if won else None,
                       mark="ok" if won else None)

    def _confirmation(self, t):
        # Ilustrácia hernej voľby na stole; nejde o nové ovládanie ukážky.
        cx, cy = self.center
        width, height = round(190 * self.k), round(36 * self.k)
        for i, title in enumerate(("Tromf: Žaluď", "Bez tromfu")):
            rect = pygame.Rect(0, 0, width, height)
            rect.center = (cx, cy - round((90 - i * 44) * self.k))
            ui_style.draw_button(self.canvas, rect, title, self.font_seat,
                                 1 if i == 0 else 3,
                                 hover=i == 0 and t >= 3, shadow=False)

    def draw(self, mouse_pos):
        if self.first_trick_trump:
            return self._draw_first(mouse_pos)
        return self._draw_classic(mouse_pos)

    def _first_origin(self, player, name):
        names = FIRST_HANDS[player]
        slot = names.index(name)
        if player == 0:
            return self.hand_pos(slot, len(names))
        x, y = self.seat[player]
        return (x + slot * self.cw * .25, y)

    def _first_hands(self, removed, fade, selected=False, marks=False):
        from config import CARD_BACK_IMAGE
        for player, names in enumerate(FIRST_HANDS):
            for name in names:
                if name in removed[player]:
                    continue
                pos = self._first_origin(player, name)
                if player == 0 and name == "acorn-over" and selected:
                    pos = (pos[0], pos[1] - round(12 * self.k * selected))
                self._card(name if player == 0 else CARD_BACK_IMAGE[:-4], pos, .8, alpha=fade,
                           outline=GREEN if player == 0 and name in PAIR else None,
                           mark="ok" if marks and player == 0 and name in PAIR else None)

    def _first_sequence(self, plays, t, start, collect, winner, previous=(), preplayed=False):
        removed = [set() for _ in range(3)]
        for player, name in previous:
            removed[player].add(name)
        for player, name in plays:
            removed[player].add(name)
        self._first_hands(removed, 1)
        for i, (player, name) in enumerate(plays):
            if t >= collect:
                k = _ease((t - collect) / 1.3)
                if k < 1:
                    self._card(name, _arc(self.spot[player], self.seat[winner], k),
                               1 - .2 * k, alpha=1 - k,
                               outline=ui_style.GOLD if player == winner else None)
            elif preplayed and player == 0:
                self._card(name, self.spot[player], outline=GREEN)
            else:
                won = t >= start + 2.5 and player == winner
                self._play_from_hand(player, name, t, start + i * .8, .75, 1,
                                     origin=self._first_origin(player, name), draw_hand=False,
                                     outline=ui_style.GOLD if won else None,
                                     mark="ok" if won else None)

    def _draw_first(self, mouse_pos):
        t = self._elapsed()
        key = self.keys[self.scene]
        self._draw_header()
        self._draw_stage()
        self._draw_labels(1 if key == "change" and t >= 3.5 else 0)
        self._draw_trump_note(1)
        empty = (set(), set(), set())
        if key in ("pair", "first", "bid", "declare"):
            self._first_hands(empty, 1,
                              selected=_ease((t - 1) / .4) if key == "declare" else False,
                              marks=key == "pair")
            if key in ("first", "bid", "declare"):
                self._classic_empty_panel()
            if key == "first" and 1 <= t < 4:
                self._classic_choice(1.5)
            if key == "bid":
                self._classic_choice(1.5, disabled=t < 5)
            if key == "declare" and 1 <= t < 4.5:
                self._classic_choice(t)
        elif key == "effect":
            self._first_hands(({"acorn-over"}, set(), set()), 1)
            self._play_from_hand(0, "acorn-over", t, 1, 2, 1, draw_hand=False,
                                 origin=self._first_origin(0, "acorn-over"),
                                 outline=GREEN, mark="ok" if t >= 3 else None)
            self._classic_bubble(0, t, 3, 6.5, suit="acorn")
        elif key == "win":
            if t < 7:
                self._first_sequence(FIRST_TRICK, t, 1, 4.2, 1, preplayed=True)
            else:
                self._first_sequence(LATER_TRICK, t, 7, 10.8, 0, previous=FIRST_TRICK)
        else:
            previous = FIRST_TRICK + LATER_TRICK
            if t < 6:
                self._first_sequence(FIRST_CHANGE, t, 1, 4.2, 1, previous=previous)
            else:
                removed = [set() for _ in range(3)]
                for player, name in previous + FIRST_CHANGE + ((1, "bell-over"),):
                    removed[player].add(name)
                self._first_hands(removed, 1)
                self._play_from_hand(1, "bell-over", t, 7, 1.3, 1, draw_hand=False,
                                     origin=self._first_origin(1, "bell-over"),
                                     outline=GREEN if t >= 8.3 else None,
                                     mark="ok" if t >= 8.3 else None)
            self._classic_bubble(1, t, 8.3, 12.3, suit="bell", is_new=True)
            if t >= 8.3:
                text = self.font_seat.render("Hráč: 100 bodov · Počítač 1: 60 bodov", True, GREEN)
                self.canvas.blit(text, text.get_rect(right=self.stage.right - 18,
                                                     bottom=self.stage.bottom - 16))
        self._round_panel(t, 1)
        self._draw_text()
        self._draw_controls(mouse_pos)

    def _classic_state(self, t):
        """Čistý časový stav ukážky; nikdy nemení rozohratú hru."""
        key = self.keys[self.scene]
        trump = ("bell" if t >= 8.3 else "acorn") if key == "change" else (
            "acorn" if key == "effect" and t >= 3 else None)
        return {"trump": trump,
                "declarer": "Počítač 1" if trump == "bell" else "Hráč" if trump else None,
                "player_points": 100 if key == "change" or trump == "acorn" else 0,
                "computer_points": 60 if trump == "bell" else 0,
                "trick": (1 if t < 10.5 else 2) if key == "classic" else (
                    (2 if t < 6 else 3) if key == "change" else 2),
                "buttons": key == "classic" and 1.2 <= t < 5 or key == "declare" and 1 <= t < 4.5}

    def _classic_hand(self, names, fade, omit=None, selected=False, marks=False):
        for i, name in enumerate(names):
            if name == omit:
                continue
            pos = self.hand_pos(i, len(names))
            if selected and name == "acorn-over":
                pos = (pos[0], pos[1] - round(12 * self.k * selected))
            self._card(name, pos, .8, alpha=fade,
                       outline=GREEN if name in PAIR else None,
                       mark="ok" if marks and name in PAIR else None)

    def _classic_choice(self, t, disabled=False):
        cx, cy = self.center
        width = min(round(190 * self.k), self.text_x - self.stage.x - 60)
        height = round(36 * self.k)
        from gui.round_demos import _RoundDemo
        click_at = 2.7 if disabled else 4
        for i, title in enumerate(("Tromf: Žaluď", "Bez tromfu")):
            rect = pygame.Rect(0, 0, width, height)
            rect.center = (cx, cy - round((90 - i * 44) * self.k))
            pressed = i == 0 and click_at - .2 <= t < click_at + .25
            if disabled and i == 0:
                # Rovnaký pohyb o 2 px ako v Dražbe, bez aktivácie voľby.
                ui_style.draw_button(self.canvas, rect.move(0, 2) if pressed else rect,
                                     title, self.font_btn, 1, enabled=False,
                                     shadow=not pressed)
            else:
                _RoundDemo._press(self, rect, title, pressed, tier=1 if i == 0 else 3)

    def _classic_empty_panel(self):
        from types import SimpleNamespace
        from gui.canvas import Canvas, LSurf
        from gui.scoreboard import Scoreboard
        w, h = round(112 * self.k), round(154 * self.k)
        c = self.canvas
        size = (max(1, round(w * c.s)), max(1, round(h * c.s)))
        if getattr(self, "_empty_panel_size", None) != size:
            surface = pygame.Surface(size, pygame.SRCALPHA)
            panel = Scoreboard(Canvas(surface, size[0] / 160))
            panel.trump_x = panel.panel_y = 0
            panel._draw_trump_panel(SimpleNamespace(trump_suit=None))
            self._empty_panel_size, self._empty_panel_image = size, surface
        rect = pygame.Rect(0, 0, w, h)
        rect.topright = (self.stage.right - 18, self._text_box(self.scene)[0].bottom + 18)
        c.blit(LSurf(self._empty_panel_image, w, h), rect)

    def _classic_bubble(self, player, t, start, end, text=None, suit=None, is_new=False):
        if not start <= t < end:
            return
        from gui.speech_bubble import SpeechBubble
        if not hasattr(self, "_tutorial_bubble"):
            self._tutorial_bubble = SpeechBubble(self.canvas)
        bubble = self._tutorial_bubble
        bubble.bubbles.clear()     # bublina predchádzajúcej scény nesmie presvitať
        bubble.font_large = self.canvas.font(round(22 * self.fs))
        bubble.font_medium = self.font_seat
        # Bubliny sú ukotvené pri príslušnej ruke, nie v informačnom stĺpci.
        if player == 0:
            names = CLASSIC_HAND if text else AFTER_FIRST_HAND
            anchor = self.hand_pos(names.index("heart-ten"), len(names)) if suit else self.seat[0]
            x = anchor[0] + self.cw * .35 if suit else anchor[0]
            bubble.bubble_positions[player] = (round(x),
                round(anchor[1] - .4 * self.cw / (181 / 293) - 30))
            bubble.seat_of[player] = "bottom"
        else:
            text_width = bubble.font_large.size("NOVÝ TROMF!" if is_new else "TROMF!")[0] + 32
            x, y = self.seat[player]
            bubble.bubble_positions[player] = (
                round(x + .65 * self.cw + text_width / 2 + 30), round(y + 60))
            bubble.seat_of[player] = "left"
        if suit:
            # Bublina napravo od zahranej karty, chvost smeruje ku karte.
            label = "NOVÝ TROMF!" if is_new else "TROMF!"
            width = max(bubble.font_large.size(label)[0], 40) + 32
            text_h = bubble.font_large.get_height()
            height = text_h + 40 + 32 + 8
            x, y = self.spot[player]
            bubble.bubble_positions[player] = (
                round(x + self.cw / 2 + width / 2 + 30), round(y + height / 2))
            bubble.seat_of[player] = "left"
        if suit:
            bubble.show_trump(player, suit, is_new=is_new)
        else:
            bubble.show_instruction(player, text)
        bubble.draw()

    def _classic_trick(self, plays, hand, t, start, winner, collect, fade, preplayed=False):
        """Zahranie spoločným komponentom; zber po oblúku do ruky víťaza."""
        self._classic_hand(hand, fade, omit=plays[0][1])
        for i, (player, name) in enumerate(plays):
            if t < collect and preplayed and player == 0:
                self._card(name, self.spot[0], alpha=fade, outline=GREEN)
            elif t < collect:
                self._play_from_hand(player, name, t, start + i * .8, .75, fade,
                                     hand=hand if player == 0 else None,
                                     draw_hand=player != 0,
                                     outline=ui_style.GOLD if player == winner and t >= start + 2.5 else None,
                                     mark="ok" if player == winner and t >= start + 2.5 else None)
            else:
                if player:
                    from config import CARD_BACK_IMAGE
                    for j in (1, 2):
                        x, y = self.seat[player]
                        self._card(CARD_BACK_IMAGE[:-4], (x + j * self.cw * .25, y), .8, alpha=fade)
                k = _ease((t - collect) / 1.3)
                if k < 1:
                    pos = _arc(self.spot[player], self.seat[winner], k, bend=.15)
                    self._card(name, pos, 1 - .2 * k, alpha=fade * (1 - k),
                               outline=ui_style.GOLD if player == winner else None)

    def _draw_classic(self, mouse_pos):
        t = self._elapsed()
        key = self.keys[self.scene]
        # Opakované scény sa reštartujú priamo, bez dojmu prechodu na iný krok.
        fade = 1.0
        if key == "pair":
            fade = _ease(t / .4) if t < .4 else 1
            if self.playing and t > self.SCENE_LEN - 1:
                fade *= 1 - _ease(t - self.SCENE_LEN + 1)
        self._draw_header()
        self._draw_stage()
        self._draw_labels(1 if key == "change" and t >= 3.5 else 0)
        self._draw_trump_note(fade)
        if key == "pair":
            self._draw_idle_hands((1, 2), fade)
            self._classic_hand(CLASSIC_HAND, fade, marks=True)
        elif key == "classic":
            if t < 5.5:
                self._draw_idle_hands((1, 2), fade)
                self._classic_hand(CLASSIC_HAND, fade, selected=1 <= t < 5)
            else:
                self._classic_trick(CLASSIC_OPENING, CLASSIC_HAND, t, 5.5, 0, 9, fade)
            if self._classic_state(t)["buttons"]:
                self._classic_choice(t, disabled=True)
            self._classic_bubble(0, t, 3.2, 4.9, text="Tromf nie je možný v prvom štichu!")
        elif key == "declare":
            self._draw_idle_hands((1, 2), fade)
            self._classic_hand(AFTER_FIRST_HAND, fade, selected=_ease((t - 1) / .4))
            self._classic_empty_panel()
            if self._classic_state(t)["buttons"]:
                self._classic_choice(t)
        elif key == "effect":
            self._draw_idle_hands((1, 2), fade)
            self._classic_hand(AFTER_FIRST_HAND, fade, omit="acorn-over")
            self._play_from_hand(0, "acorn-over", t, 1, 2, fade,
                                 hand=AFTER_FIRST_HAND, draw_hand=False, outline=GREEN,
                                 mark="ok" if t >= 3 else None)
            self._classic_bubble(0, t, 3, 7, suit="acorn")
        else:
            if t < 6:
                self._classic_trick(CLASSIC_CHANGE, CHANGE_HAND, t, 1, 1, 4.2, fade, preplayed=True)
            else:
                self._classic_hand(CHANGE_HAND, fade, omit="acorn-over")
                from config import CARD_BACK_IMAGE
                # Počítaču 2 po štichu zostávajú pôvodné sloty 1 a 2.
                for slot in (1, 2):
                    sx, sy = self.seat[2]
                    self._card(CARD_BACK_IMAGE[:-4],
                               (sx + slot * self.cw * .25, sy), .8, alpha=fade)
                x, y = self.seat[1]
                self._card(CARD_BACK_IMAGE[:-4], (x + self.cw * .25, y), .8, alpha=fade)
                self._play_from_hand(1, "bell-over", t, 7, 1.3, fade, draw_hand=False,
                                     origin=(x + self.cw * .5, y),
                                     outline=GREEN if t >= 8.3 else None,
                                     mark="ok" if t >= 8.3 else None)
            self._classic_bubble(1, t, 8.3, 12.3, suit="bell", is_new=True)
            # Pôvodná hláška zostáva jasne oddelená od novej farby tromfu.
            if t >= 8.3:
                state = self._classic_state(t)
                text = f"Hráč: {state['player_points']} bodov · Počítač 1: {state['computer_points']} bodov"
                surf = self.font_seat.render(text, True, GREEN)
                self.canvas.blit(surf, surf.get_rect(right=self.stage.right - 18,
                                                     bottom=self.stage.bottom - 16))
        self._round_panel(t, fade)
        self._draw_text()
        self._draw_controls(mouse_pos)

    def _draw_change_legacy(self, t, fade):
        k = _ease((t - 1) / 2)
        self._card("bell-king", self.seat[1], .8, alpha=fade,
                   outline=GREEN if t >= .6 else None)
        pos = _arc(self.seat[1], self.spot[1], k)
        self._card("bell-over", pos, .8 + .2 * k, alpha=fade,
                   outline=GREEN if t >= .6 else None,
                   mark="ok" if t >= 3 else None)


def verify_trump_demo():
    """Overí ukážkové štichy a hraničné podmienky oboch variantov."""
    from game.card import Card
    from game.player import Player
    from game.round import Round, first_trick_min_bid
    from game.trick import Trick
    errors = []
    def check(ok, message):
        if not ok:
            errors.append("Hlásenie tromfu: " + message)
    def card(name):
        return Card(*name.split("-"))
    for variant in (False, True):
        players = [Player(str(i), index=i) for i in range(3)]
        rnd = Round(players, 0, variant)
        rnd.start_bidding()
        rnd.bidding.finalize()
        players[0].hand.add_cards([card(n) for n in PAIR])
        rnd.start_trick()
        for bid in (100, 110):
            rnd.bidding.current_bid = players[0].bid = bid
            check(rnd.can_declare_trump(0, "acorn") == (variant and bid >= 110), "hranica povinnosti")
        check(not rnd.can_declare_trump(1, "acorn"), "hlási iba vynášajúci")
        rnd.trick_number = 1
        rnd.bidding.current_bid = players[0].bid = 50
        check(rnd.can_declare_trump(0, "acorn"), "od druhého štichu bez hranice hlášky")
        rnd.declare_trump(0, "acorn")
        check(rnd.current_trick.trump_suit == "acorn", "okamžitý účinok")
        players[1].hand.add_cards([card("bell-king"), card("bell-over")])
        rnd.current_leader_index = 1
        rnd.start_trick()
        rnd.declare_trump(1, "bell")
        check(players[0].declared_trumps_points == 100 and rnd.trump_suit == "bell", "zachovanie predchádzajúcich bodov")
    for plays, trump, winner in ((CLASSIC_TRICK, None, 0), (FIRST_TRICK, "acorn", 1), (LATER_TRICK, "acorn", 0)):
        trick = Trick(players, plays[0][0], trump)
        for index, name in plays:
            trick.play_card(index, card(name))
        check(trick.get_winner_index() == winner, "víťaz ukážkového štichu")
    check(first_trick_min_bid("acorn") == 110, "žaluďová hláška")
    rnd.declared_in_first_trick = True
    players[0].bid = 110
    players[0].tricks_points = 0
    rnd.tricks = []
    check(not rnd.bidder_fulfilled(), "žiadny štich")
    rnd.tricks = [trick]
    check(not rnd.bidder_fulfilled(), "samotný štich nestačí")
    players[0].tricks_points = trick.total_points
    check(rnd.bidder_fulfilled(), "štich aj dostatok bodov")
    return errors
