# Animované hlásenie tromfu; príklady nemenia stav rozohratej hry.
import pygame
from gui import ui_style
from gui.rules_demo import TrickRulesDemo, _ease, _arc, GREEN, RED

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
FIRST_TRICK = ((0, "acorn-over"), (1, "acorn-ace"), (2, "acorn-seven"))
LATER_TRICK = ((1, "acorn-eight"), (2, "acorn-nine"), (0, "acorn-ten"))

class TrumpDemo(TrickRulesDemo):
    TITLE = "HLÁSENIE TROMFU"
    SHOW_TRUMP_POINTS = True

    @property
    def SCENE_LEN(self):
        return 11.0 if self.keys[self.scene] == "pair" else 14.0

    @property
    def HOLD_AT(self):
        return self.SCENE_LEN - 1.2

    def _elapsed(self):
        # Pri prechode použijeme dĺžku odchádzajúcej scény, nie nasledujúcej.
        t = (pygame.time.get_ticks() - self._t0) / 1000.0
        if self.playing:
            while t >= self.SCENE_LEN:
                duration = self.SCENE_LEN
                t -= duration
                self._t0 += round(duration * 1000)
                self.scene = (self.scene + 1) % len(self.SCENES)
            return t
        return min(t, self.hold_at if self.hold_at is not None else self.HOLD_AT)

    def __init__(self, canvas, first_trick_trump=False):
        self.first_trick_trump = first_trick_trump
        self.keys = (("pair", "first", "bid", "declare", "effect", "win", "change")
                     if first_trick_trump else ("pair", "classic", "declare", "effect", "change"))
        self.SCENES = tuple(TEXTS[key] for key in self.keys)
        super().__init__(canvas)

    # Rozloženie, mierka, menovky, ruka aj ovládanie sú priamo zo šablóny.
    # Mení sa iba obsah scén, nie súradnice prvkov Pravidiel štichov.

    def _show_hand_caption(self):
        return self.keys[self.scene] not in ("win", "change")

    def _scene_trump(self):
        key = self.keys[self.scene]
        t = self._elapsed()
        if key == "effect" and t >= 3:
            return "acorn"
        if key == "win":
            return "acorn"
        if key == "change":
            return "bell" if t >= 3 else "acorn"
        return None

    def _trump_declarer(self):
        return "Počítač 1" if self.keys[self.scene] == "change" and self._elapsed() >= 3 else "Hráč"

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
            trick = 1 if t < 6 else 2
        elif key == "win":
            trick = 1 if t < 7 else 2
        elif key == "change":
            trick = 3
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
        c.blit(LSurf(image, w, h), rect)

    def _hand_demo(self, t, fade, play=False, allowed=True):
        k = _ease((t - 1) / 2) if play else 0.0
        color = GREEN if allowed else RED
        self._hand(HAND, fade, moved="acorn-over" if play else None,
                   moved_k=k, dimmed=tuple(n for n in HAND if n not in PAIR),
                   outlines={n: color for n in PAIR} if t >= .6 else {},
                   marks={n: "circlex" for n in PAIR} if not allowed else {})
        if play:
            start = self.hand_pos(HAND.index("acorn-over"), len(HAND))
            pos = _arc(start, self.spot[0], k, bend=.15)
            self._card("acorn-over", pos, .8 + .2 * k, alpha=fade,
                       outline=color if t >= .6 else None,
                       mark="ok" if t >= 3 and allowed else None)

    def _trick(self, plays, t, fade, winner):
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
        t = self._elapsed()
        self._draw_header()
        self._draw_stage()
        fade = 1.0
        if self.playing and t > self.SCENE_LEN - 1:
            fade = 1 - _ease(t - (self.SCENE_LEN - 1))
        if t < .4:
            fade = min(fade, _ease(t / .4))
        key = self.keys[self.scene]
        glow = 1 if key == "change" else 0
        if key == "classic" and t < 6:
            glow = 0 if t >= 3 else 2
        if key == "win":
            glow = (1 if t >= 3 else 0) if t < 7 else (0 if t >= 10 else 1)
        self._draw_labels(glow)
        self._draw_trump_note(fade)
        if key == "pair":
            self._hand_demo(t, fade)
        elif key == "classic":
            if t < 6:
                self._trick(CLASSIC_TRICK, t, fade, 0)
            else:
                self._hand_demo(t - 6, fade)
        elif key in ("first", "bid"):
            allowed = key == "first" or t >= 5
            self._hand_demo(t, fade, allowed=allowed)
        elif key == "declare":
            self._hand_demo(t, fade, play=True)
            if t >= 3:
                self._confirmation(t)
        elif key == "effect":
            self._hand_demo(t, fade, play=True)
            if t >= 3:
                self._status("+100 bodov za hlášku", GREEN)
        elif key == "win":
            if t < 7:
                self._trick(FIRST_TRICK, t, fade, 1)
                self._status("1. štich · zatiaľ nemáš štich")
            else:
                self._trick(LATER_TRICK, t - 7, fade, 0)
                self._status("Neskôr · získavaš štich" if t >= 10 else "Neskorší štich",
                             GREEN if t >= 10 else ui_style.GOLD)
        else:
            k = _ease((t - 1) / 2)
            self._card("bell-king", self.seat[1], .8, alpha=fade,
                       outline=GREEN if t >= .6 else None)
            pos = _arc(self.seat[1], self.spot[1], k)
            self._card("bell-over", pos, .8 + .2 * k, alpha=fade,
                       outline=GREEN if t >= .6 else None,
                       mark="ok" if t >= 3 else None)
            if t >= 3:
                self._status("Tvojich 100 bodov za žaluď zostáva", GREEN)
        self._round_panel(t, fade)
        self._draw_text()
        self._draw_controls(mouse_pos)


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
