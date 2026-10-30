# tester/sim_first_trick_trump.py
#
# Simulácia kôl troch počítačov bez grafiky — porovnanie pravidiel
# "Hlásenie tromfu od 2. štichu" (klasika) a "Aj v 1. štichu" (variant od
# hráčov, 2026-10-29). Herná logika je skutočná (game/round.py, game/ai.py),
# priebeh kola je rovnaký ako v gui/screen.py (dražba → talón → navýšenie →
# odhodenie → 10 štichov, hlásenie pri vynesení kráľa/horníka z páru).
#
# Použitie:
#   python tester/sim_first_trick_trump.py                 # 2000 kôl, obe pravidlá
#   python tester/sim_first_trick_trump.py --rounds 5000 --difficulty medium

import argparse
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from game.player import Player      # noqa: E402
from game.round import Round        # noqa: E402
from game.ai import AI              # noqa: E402


def play_round(players, ais, obligation_index, variant, stats):
    for p in players:
        p.reset_round()
    for ai in ais:
        ai.reset_memory()
    rnd = Round(players, obligation_index, variant)
    rnd.deal()
    rnd.start_bidding()
    b = rnd.bidding

    # Dražba — rovnaké poradie ako Screen._get_next_bidder_index
    while not b.bidding_over:
        idx = next(((b.highest_bidder_index + i) % 3 for i in range(1, 4)
                    if b.active[(b.highest_bidder_index + i) % 3]), None)
        if idx is None:
            break
        amount = ais[idx].decide_bid(b.current_bid)
        if rnd.process_bid(idx, amount):
            break
    if rnd.phase != "talon":
        b.finalize()
        rnd.phase = "talon"

    winner = b.winner_index
    for ai in ais:
        ai.memory.set_bidder(winner, b.current_bid)
    ais[winner].record_talon(rnd.talon)
    rnd.give_talon_to_winner()
    ai = ais[winner]
    ai.record_own_hand(players[winner].hand.cards)
    new_bid = ai.decide_raise_after_talon(b.current_bid)
    if new_bid:
        b.current_bid = new_bid
        players[winner].bid = new_bid
        for a in ais:
            a.memory.set_bidder(winner, new_bid)
    rnd.discard_cards(winner, ai.decide_discard(players[winner].hand.cards))

    while rnd.phase == "tricks":
        rnd.start_trick()
        for _ in range(3):
            pi = rnd.get_current_player_index()
            player = players[pi]
            playable = player.hand.get_playable_cards(
                rnd.current_trick.lead_suit, rnd.trump_suit,
                rnd.current_trick.played_cards)
            card = ais[pi].decide_card(playable, rnd.current_trick, rnd.trick_number)
            if (card.rank in ("over", "king") and rnd.trick_number == 0
                    and pi == winner and players[pi].hand.has_trump_pair(card.suit)
                    and not rnd.can_declare_trump(pi, card.suit)):
                stats["blocked_by_min_bid"] += variant
            if card.rank in ("over", "king") and rnd.can_declare_trump(pi, card.suit):
                first = rnd.trick_number == 0
                rnd.declare_trump(pi, card.suit)
                for a in ais:
                    a.record_trump_declaration(card.suit, pi)
                if first:
                    stats["first_trick_declarations"] += 1
                stats["declarations"] += 1
            rnd.play_card(pi, card)
        trick = rnd.current_trick
        w = rnd.finish_trick()
        for a in ais:
            a.record_trick(trick.leader_index, trick.played_cards, w, rnd.trick_number - 1)

    bidder = players[winner]
    fulfilled = rnd.bidder_fulfilled()
    stats["rounds"] += 1
    stats["bid_sum"] += bidder.bid
    stats["fulfilled"] += fulfilled
    if bidder.round_points >= bidder.bid and not fulfilled:
        stats["failed_no_trick"] += 1
    if rnd.declared_in_first_trick:
        stats["ft_rounds"] += 1
        stats["ft_fulfilled"] += fulfilled
    rnd.score_round()


def simulate(rounds, variant, difficulty, seed):
    random.seed(seed)
    players = [Player(f"P{i}", index=i) for i in range(3)]
    ais = [AI(p, difficulty=difficulty, first_trick_trump=variant) for p in players]
    stats = dict(rounds=0, bid_sum=0, fulfilled=0, declarations=0,
                 first_trick_declarations=0, failed_no_trick=0,
                 ft_rounds=0, ft_fulfilled=0, blocked_by_min_bid=0)
    for r in range(rounds):
        play_round(players, ais, r % 3, variant, stats)
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=2000)
    ap.add_argument("--difficulty", default="hard")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    for variant in (False, True):
        s = simulate(args.rounds, variant, args.difficulty, args.seed)
        n = s["rounds"]
        name = "Aj v 1. štichu" if variant else "Od 2. štichu (klasika)"
        print(f"== {name} — {n} kôl, AI {args.difficulty}")
        print(f"  priemerná povinnosť:       {s['bid_sum'] / n:.1f}")
        print(f"  povinnosť splnená:         {100 * s['fulfilled'] / n:.1f} %")
        print(f"  hlásení tromfu za kolo:    {s['declarations'] / n:.2f}")
        print(f"  hlásení v 1. štichu:       {s['first_trick_declarations']}")
        if s["ft_rounds"]:
            print(f"    z toho splnená povinnosť: "
                  f"{100 * s['ft_fulfilled'] / s['ft_rounds']:.1f} %")
        print(f"  nesplnené len pre 0 štichov: {s['failed_no_trick']}")
        if variant:
            print(f"  K/H páru v 1. štichu bez hlásenia (nízka povinnosť): "
                  f"{s['blocked_by_min_bid']}")


if __name__ == "__main__":
    main()
