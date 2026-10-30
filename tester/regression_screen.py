# tester/regression_screen.py
#
# Regresný test celej hernej obrazovky (gui/screen.py::Screen) — headless.
#
# Odohrá niekoľko kôl (alebo celú hru) cez skutočný Screen.step_frame(),
# teda presne tou cestou, ktorou ide hra. Za ľudského hráča "kliká" cez
# skutočné udalosti myši (pygame.event.post), takže sa otestuje aj
# _handle_events, _handle_click, card_renderer.get_clicked_card, BidSlider.
#
# Načo: rework rozlíšení (claude/13_RESOLUTION_REWORK_ANALYSIS.md) mení
# GUI, nie pravidlá. Stopa (rozdania, dražba, talon, tromfy, štichy, skóre,
# trofeje) musí zostať pri každom kroku IDENTICKÁ.
#
# Použitie:
#   python tester/regression_screen.py                    # vypíše stopu (3 kolá)
#   python tester/regression_screen.py --out pred.txt     # uloží stopu
#   python tester/regression_screen.py --full --out pred_full.txt   # celá hra
#   ...zmeny v kóde...
#   python tester/regression_screen.py --out po.txt
#   fc pred.txt po.txt        (Windows)  /  diff pred.txt po.txt  (Linux)
#
# Nástroj NEZAPISUJE do Documents/Tisic (logy, trofeje) — domovský
# priečinok sa presmeruje do dočasného priečinka. Čas je falošný
# (16 ms na snímku), takže test beží rýchlejšie než reálny čas a je
# deterministický. Stopa neobsahuje časy ani počty snímok.

import argparse
import os
import random
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_SEED = 20261024
DEFAULT_ROUNDS = 3
MAX_FRAMES = 2_000_000
FRAME_MS = 16
RESOLUTION = (1920, 1080)

# Ľudský hráč v teste: s tromfovým párom prihadzuje do tejto hranice
# (dostane sa k talónu, odhadzovaniu, posúvaču navýšenia), bez páru pasuje.
HUMAN_BID_LIMIT = 100


# ----------------------------------------------------------------------
# Príprava prostredia — MUSÍ prebehnúť pred importom pygame/config/game
# ----------------------------------------------------------------------

def ensure_hashseed():
    """AI iteruje cez množiny/slovníky — bez PYTHONHASHSEED=0 by sa
    priebeh hry medzi behmi mohol líšiť. Reštart cez subprocess."""
    # Windows konzola/presmerovanie: tracker vypisuje emoji (🏆) — bez
    # UTF-8 by print() v cp1250 spadol.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    if os.environ.get("PYTHONHASHSEED") != "0":
        env = dict(os.environ, PYTHONHASHSEED="0", PYTHONIOENCODING="utf-8")
        sys.exit(subprocess.run([sys.executable] + sys.argv, env=env).returncode)


def isolate_home(prefix: str = "tisic_test_") -> str:
    """Presmeruje ~ (Windows USERPROFILE, Linux HOME) do dočasného
    priečinka — logy aj trofeje idú tam, nie do skutočných Documents."""
    home = tempfile.mkdtemp(prefix=prefix)
    os.environ["HOME"] = home
    os.environ["USERPROFILE"] = home
    os.makedirs(os.path.join(home, "Documents", "Tisic"), exist_ok=True)
    return home


def force_resolution(width: int, height: int):
    """Vnúti hre rozlíšenie bez skutočného monitora — gui/display.py ho
    číta z premennej TISIC_RESOLUTION (TISIC_DESKTOP = falošná plocha
    pre ponuku veľkostí okna; dummy ovládač hlási 1024×768)."""
    os.environ["TISIC_RESOLUTION"] = f"{width}x{height}"
    os.environ.setdefault("TISIC_DESKTOP", f"{width}x{height}")


class FakeClock:
    """Deterministický čas — pygame.time.get_ticks() vracia self.now."""

    def __init__(self):
        self.now = 1000

    def advance(self, ms: int = FRAME_MS):
        self.now += ms


def setup_headless(width: int, height: int) -> FakeClock:
    """Spoločná príprava pre test aj galériu. Volať pred importom hry."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.chdir(ROOT)                      # assety sa hľadajú relatívne
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    import pygame
    clock = FakeClock()
    pygame.time.get_ticks = lambda: clock.now
    pygame.time.delay = lambda ms: None
    pygame.time.wait = lambda ms: None
    force_resolution(width, height)
    pygame.init()
    return clock


def open_window(width: int, height: int):
    """Okno hry — otvára ho výhradne gui/display.py (podľa
    TISIC_RESOLUTION nastaveného v setup_headless)."""
    from gui import display
    return display.get_surface()


# ----------------------------------------------------------------------
# Hra a "ľudský hráč"
# ----------------------------------------------------------------------

# Variant pravidiel "tromf aj v 1. štichu" (--first-trick-trump)
FIRST_TRICK_TRUMP = False


def new_screen(seed: int, with_tracker: bool = True):
    """Vytvorí hru rovnako ako main.py (_create_game + _run_game)."""
    import main as game_main
    from gui.screen import Screen
    from achievements.tracker import AchievementTracker

    random.seed(seed)
    settings = {"ai1_difficulty": "hard", "ai2_difficulty": "hard",
                "table_bg": "table.jpg", "first_trick_trump": FIRST_TRICK_TRUMP}
    game_state, ai_players = game_main._create_game(settings)
    tracker = AchievementTracker() if with_tracker else None
    screen = Screen(game_state, ai_players, debug=False, new_game=True,
                    table_bg=settings["table_bg"],
                    achievement_tracker=tracker)
    return screen, game_state, tracker


def step(screen) -> bool:
    """Jedna snímka — presne tá istá cesta ako Screen.run()."""
    return screen.step_frame()


def click(pos):
    """Klik ľavým tlačidlom — skutočná udalosť, spracuje ju step_frame()."""
    import pygame
    pos = (int(pos[0]), int(pos[1]))
    # Hra číta udalosti cez display.get_events(), ktoré prepočíta
    # fyzické súradnice okna na logické — klik musí byť fyzický.
    from gui import display
    pos = display.viewport().to_physical(pos)
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos))


def hand_card_point(screen, index: int) -> tuple[int, int]:
    """Bod na viditeľnej časti karty v ruke hráča (ľavý pruh karty —
    karty sa prekrývajú, ďalšia začína o `offset` px vpravo)."""
    renderer = screen.card_renderer
    cfg = renderer.hand_configs[screen.game_state.human_index]
    x, y = renderer._card_position(cfg, index)
    return x + cfg["offset"] // 2, y + 100


class HumanBot:
    """Deterministický "ľudský hráč" — kliká ako človek, cez GUI."""

    def __init__(self, screen, game_state, bid_limit: int = HUMAN_BID_LIMIT,
                 require_pair: bool = True):
        self.screen = screen
        self.gs = game_state
        self.bid_limit = bid_limit          # do koľko prihadzuje
        self.require_pair = require_pair    # prihadzuje len s tromfovým párom

    def act(self) -> str | None:
        """Ak je hráč na ťahu, pošle jeden klik. Vráti popis akcie."""
        s, gs = self.screen, self.gs
        rnd = gs.current_round
        if (rnd is None or s.dealing or s.talon_revealing or s.trick_waiting
                or s.waiting_for_ai or not s.trick_animation.is_done
                or s.card_throw_animation.in_flight
                or s.game_over_timer):
            return None
        hi = gs.human_index
        human = gs.players[hi]

        # Posúvač navýšenia — po odhodení (fáza je už "tricks", štich ešte nezačal)
        if s.bid_slider.visible:
            if s.bid_slider.current_value < 100:
                click(s.bid_slider.btn_plus.center)
                return "slider+"
            click(s.bid_slider.btn_confirm.center)
            return "slider_ok"

        if rnd.phase == "bidding":
            b = rnd.bidding
            if b.bidding_over or s._get_next_bidder_index() != hi:
                return None
            from config import MAX_BID
            wants = (not self.require_pair
                     or bool(human.hand.get_available_trumps()))
            if wants and b.current_bid < min(self.bid_limit, MAX_BID):
                click(s._button_bid_rect().center)
                return "bid"
            click(s._button_pass_rect().center)
            return "pass"

        if rnd.phase == "talon":
            if rnd.bidding.winner_index != hi:
                return None
            if len(human.hand.cards) != 12:
                return None
            if len(s.selected_discards) == 2:
                click(s._button_confirm_rect().center)
                return "discard_ok"
            for i, card in enumerate(human.hand.cards):
                if card.rank in ("ace", "ten") or card in s.selected_discards:
                    continue
                click(hand_card_point(s, i))
                return "discard_pick"
            return None

        if rnd.phase == "tricks":
            if rnd.current_trick is None or rnd.get_current_player_index() != hi:
                return None
            if s.pending_trump_card is not None:
                if s.pending_trump_first_trick:
                    click(s._button_trump_no_rect().center)
                    return "trump_no"
                click(s._button_trump_yes_rect().center)
                return "trump_yes"
            playable = human.hand.get_playable_cards(
                rnd.current_trick.lead_suit, rnd.trump_suit,
                rnd.current_trick.played_cards)
            if not playable:
                return None
            card = playable[0]
            # Ako leader od 2. štichu vynesie kartu z tromfového páru,
            # aby sa otestoval aj dialóg "Tromf / Bez tromfu".
            if (rnd.current_leader_index == hi and not rnd.current_trick.played_cards
                    and (rnd.trick_number > 0 or rnd.first_trick_trump)):
                for c in playable:
                    if (c.rank in ("over", "king")
                            and human.hand.has_trump_pair(c.suit)):
                        card = c
                        break
            idx = human.hand.cards.index(card)
            click(hand_card_point(s, idx))
            return "play"
        return None


# ----------------------------------------------------------------------
# Stopa
# ----------------------------------------------------------------------

def build_trace(seed: int, rounds: int | None, clock: FakeClock) -> list[str]:
    """rounds=None → hrá sa do konca hry."""
    screen, gs, tracker = new_screen(seed)
    bot = HumanBot(screen, gs)
    trace = [f"seed={seed} rounds={'full' if rounds is None else rounds}"]

    log_seen = 0
    last_bid_state = None
    unlocked_before = {k for k, v in tracker.data["unlocked"].items() if v}
    pending_action_frames = 0
    # Stav dražby a trofeje sa zisťujú po snímkach — ich poradie voči
    # riadkom herného logu by záviselo od dĺžky animácií. Zbierajú sa preto
    # bokom a zapíšu sa pohromade pred výsledkom kola (a na konci testu).
    observed: list[str] = []

    def flush_observed():
        trace.extend(observed)
        observed.clear()

    def flush_log():
        nonlocal log_seen
        for line in gs.logger.entries[log_seen:]:
            line = line.rstrip()
            if line.strip() and not line.strip().startswith("==="):
                if line.startswith("VÝSLEDOK KOLA"):
                    flush_observed()
                trace.append(line)
        log_seen = len(gs.logger.entries)

    screen.running = True
    screen._start_round()
    frames = 0
    while frames < MAX_FRAMES:
        frames += 1
        clock.advance()
        alive = step(screen)
        flush_log()

        rnd = gs.current_round
        if rnd is not None and rnd.bidding is not None:
            b = rnd.bidding
            state = (gs.round_number, b.current_bid, b.highest_bidder_index,
                     tuple(b.active))
            if state != last_bid_state:
                observed.append(f"  [dražba] kolo {state[0]} bid={state[1]} "
                                f"vedie={state[2]} aktívni={list(state[3])}")
                last_bid_state = state

        unlocked = {k for k, v in tracker.data["unlocked"].items() if v}
        for aid in sorted(unlocked - unlocked_before):
            observed.append(f"  [trofej] {aid}")
        unlocked_before = unlocked

        if not alive or gs.phase == "game_over" and not screen.running:
            break
        if gs.phase == "game_over" and screen.game_over_timer:
            # Koniec hry — dobehni časovač ako hra
            continue
        if rounds is not None and gs.round_number > rounds:
            break
        if bot.act():
            pending_action_frames += 1

    flush_log()
    flush_observed()
    trace.append("KONIEC TESTU")
    trace.append(f"  kolo={gs.round_number} fáza={gs.phase}")
    trace.append("  skóre: " + " ".join(f"{p.name}={p.total_score}"
                                        for p in gs.players))
    if gs.winner is not None:
        trace.append(f"  víťaz: {gs.winner.name}")
    if frames >= MAX_FRAMES:
        trace.append("!! test narazil na MAX_FRAMES — hra sa zasekla?")
    return trace


def main():
    parser = argparse.ArgumentParser(
        description="Regresný test hernej obrazovky (headless).")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS)
    parser.add_argument("--full", action="store_true",
                        help="hrať do konca hry (1000 bodov)")
    parser.add_argument("--out", default=None, help="súbor pre stopu")
    parser.add_argument("--first-trick-trump", action="store_true",
                        help="variant pravidiel: tromf aj v 1. štichu")
    args = parser.parse_args()
    global FIRST_TRICK_TRUMP
    FIRST_TRICK_TRUMP = args.first_trick_trump

    ensure_hashseed()
    isolate_home()
    clock = setup_headless(*RESOLUTION)
    open_window(*RESOLUTION)

    trace = build_trace(args.seed, None if args.full else args.rounds, clock)
    text = "\n".join(trace)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"stopa uložená do {args.out} ({len(trace)} riadkov)",
              file=sys.stderr)
    else:
        print(text)
    stuck = any(line.startswith("!!") for line in trace)
    sys.exit(1 if stuck else 0)


if __name__ == "__main__":
    main()
