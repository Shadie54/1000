# tester/regression_savegame.py
#
# Test uloženia a obnovy rozohratej hry (game/savegame.py) — headless.
#
# Hra sa (rovnako ako v regression_screen.py) hrá cez skutočný Screen a
# v rôznych chvíľach sa "odíde" — presne to, čo spraví Screen.run() pri
# odchode do menu alebo zatvorení okna (_settle_for_save + save_game).
# Potom sa v tej istej chvíli pokračuje dvoma spôsobmi:
#   A) bez reštartu programu — nový Screen nad tými istými objektmi
#      (v menu "Pokračovať" v tom istom spustení),
#   B) po reštarte — hra načítaná zo savegame.json.
# Oba priebehy (dve ďalšie kolá) sa musia zhodovať do posledného riadku
# herného logu, skóre aj pamäte AI. Navyše: uloženie → načítanie →
# uloženie musí dať identický súbor.
#
# Použitie:
#   python tester/regression_savegame.py            # všetky kontrolné body
#   python tester/regression_savegame.py --verbose

import argparse
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tester import regression_screen as rs   # noqa: E402

SEED = 20261024
CONTINUE_ROUNDS = 2
MAX_FRAMES = 60_000


def _checkpoints():
    """(popis, podmienka nad (screen, game_state, frame))"""
    def phase(s, gs):
        rnd = gs.current_round
        return rnd.phase if rnd else None

    return [
        ("rozdávanie", lambda s, gs, f: s.dealing and f > 30),
        ("dražba — hráč na ťahu", lambda s, gs, f: (
            not s.dealing and phase(s, gs) == "bidding"
            and s._get_next_bidder_index() == gs.human_index)),
        ("odkrytý talon", lambda s, gs, f: s.talon_revealing),
        ("odhadzovanie (12 kariet)", lambda s, gs, f: (
            phase(s, gs) == "talon" and not s.talon_revealing
            and len(gs.players[gs.human_index].hand.cards) == 12)),
        ("posuvník navýšenia", lambda s, gs, f: s.bid_slider.visible),
        ("štich — karta v lete", lambda s, gs, f: bool(s.card_throw_animation.in_flight)),
        ("kompletný štich na stole", lambda s, gs, f: s.trick_waiting),
        ("štich 5 — hráč na ťahu", lambda s, gs, f: (
            phase(s, gs) == "tricks" and gs.current_round.trick_number >= 4
            and gs.current_round.current_trick is not None
            and gs.current_round.get_current_player_index() == gs.human_index
            and not s.trick_waiting)),
        ("posledný štich kola", lambda s, gs, f: (
            phase(s, gs) == "tricks" and gs.current_round.trick_number == 9
            and s.trick_waiting)),
        ("2. kolo — dražba", lambda s, gs, f: (
            gs.round_number >= 2 and not s.dealing and phase(s, gs) == "bidding")),
    ]


def _memory_key(ai) -> str:
    from game import savegame
    return json.dumps(savegame._memory_to_dict(ai.memory), sort_keys=True)


def _continue(screen_factory, gs, clock, bot_kwargs) -> list[str]:
    """Pokračuje v hre (nový Screen) dve kolá s botom; vráti stopu."""
    screen = screen_factory()
    bot = rs.HumanBot(screen, gs, **bot_kwargs)
    log_start = len(gs.logger.entries)
    start_round = gs.round_number
    # rovnaké kroky ako Screen.run() pri new_game=False
    screen.running = True
    screen.dealing = False
    screen.trick_waiting = False
    screen.talon_revealing = False
    screen._restore_after_continue()
    for _ in range(MAX_FRAMES):
        clock.advance()
        if not rs.step(screen):
            break
        if gs.round_number > start_round + CONTINUE_ROUNDS - 1 \
                and gs.current_round.phase == "bidding" and not screen.dealing:
            break
        bot.act()
    trace = [ln for ln in gs.logger.entries[log_start:] if ln.strip()]
    trace.append("skóre: " + " ".join(str(p.total_score) for p in gs.players))
    trace.append(f"kolo: {gs.round_number} fáza: {gs.phase}")
    trace.append("ruky: " + " | ".join(
        " ".join(f"{c.suit}:{c.rank}" for c in p.hand.cards) for p in gs.players))
    return trace


def run_checkpoint(name, cond, clock, verbose) -> list[str]:
    from game import savegame
    from gui.screen import Screen
    from achievements.tracker import AchievementTracker

    problems = []
    screen, gs, tracker = rs.new_screen(SEED)
    bot_kwargs = {"bid_limit": 400, "require_pair": False}
    bot = rs.HumanBot(screen, gs, **bot_kwargs)
    screen.running = True
    screen._start_round()
    reached = False
    for frame in range(MAX_FRAMES):
        clock.advance()
        rs.step(screen)
        if cond(screen, gs, frame):
            reached = True
            break
        bot.act()
    if not reached:
        return [f"{name}: kontrolný bod sa nedosiahol"]

    # --- odchod z hry: presne to, čo robí koniec Screen.run() -----------
    screen._settle_for_save()
    if gs.phase == "game_over":
        return [f"{name}: hra skončila pri odchode (neočakávané)"]
    ui = {"can_raise_bid": screen.can_raise_bid,
          "raise_pending": screen.bid_slider.visible}
    if not savegame.save_game(gs, screen.ai_players, tracker, ui):
        return [f"{name}: uloženie zlyhalo"]
    with open(savegame.save_path(), encoding="utf-8") as f:
        saved_text = f.read()

    # --- B) načítanie zo súboru + kontrola uloženie→načítanie→uloženie ---
    tracker_b = AchievementTracker()
    loaded = savegame.load_game({}, tracker_b)
    if loaded is None:
        return [f"{name}: načítanie zlyhalo"]
    gs_b, ai_b, ui_b = loaded
    saved_phase = gs_b.current_round.phase if gs_b.current_round else None
    savegame.save_game(gs_b, ai_b, tracker_b, ui_b)
    with open(savegame.save_path(), encoding="utf-8") as f:
        if f.read() != saved_text:
            problems.append(f"{name}: uloženie po načítaní sa líši od pôvodného")
    for a, b in zip(screen.ai_players, ai_b):
        if a is not None and _memory_key(a) != _memory_key(b):
            problems.append(f"{name}: pamäť AI {a.player.name} sa nezhoduje")

    rnd_state = random.getstate()
    clock_now = clock.now

    # --- A) pokračovanie bez reštartu -------------------------------------
    def make_a():
        return Screen(gs, screen.ai_players, debug=False, new_game=False,
                      achievement_tracker=tracker, restore_ui=ui, autosave=False)
    trace_a = _continue(make_a, gs, clock, bot_kwargs)

    # --- B) pokračovanie po reštarte ------------------------------------
    random.setstate(rnd_state)
    clock.now = clock_now

    def make_b():
        return Screen(gs_b, ai_b, debug=False, new_game=False,
                      achievement_tracker=tracker_b, restore_ui=ui_b, autosave=False)
    trace_b = _continue(make_b, gs_b, clock, bot_kwargs)

    if trace_a != trace_b:
        for i, (la, lb) in enumerate(zip(trace_a, trace_b)):
            if la != lb:
                problems.append(f"{name}: priebeh sa líši na riadku {i}: "
                                f"{la!r} ≠ {lb!r}")
                break
        else:
            problems.append(f"{name}: priebeh sa líši dĺžkou "
                            f"{len(trace_a)} ≠ {len(trace_b)}")
    if verbose:
        print(f"    {name}: uložené vo fáze {saved_phase}, ui {ui}, "
              f"pokračovanie {len(trace_a)} riadkov", file=sys.stderr)
    if len(trace_a) < 20:
        problems.append(f"{name}: pokračovanie podozrivo krátke ({len(trace_a)})")
    return problems


def main():
    parser = argparse.ArgumentParser(description="Test uloženia rozohratej hry.")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--first-trick-trump", action="store_true",
                        help="variant pravidiel: tromf aj v 1. štichu")
    args = parser.parse_args()
    rs.FIRST_TRICK_TRUMP = args.first_trick_trump

    rs.ensure_hashseed()
    rs.isolate_home("tisic_save_")
    clock = rs.setup_headless(*rs.RESOLUTION)
    rs.open_window(*rs.RESOLUTION)

    failed = 0
    for name, cond in _checkpoints():
        problems = run_checkpoint(name, cond, clock, args.verbose)
        status = "OK" if not problems else "CHYBA"
        print(f"[{status}] {name}")
        for p in problems:
            print(f"    {p}")
        failed += bool(problems)
    print()
    print("VÝSLEDOK: " + ("všetky kontrolné body OK" if not failed
                          else f"{failed} kontrolných bodov s chybou"))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
