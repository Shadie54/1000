# test_achievements.py — DOČASNÝ testovací skript na overenie logiky trackera
# Spusti: python test_achievements.py
# POZOR: zapisuje do skutočného achievements.json — po teste ho zmaž pre čistý štart

from achievements.tracker import AchievementTracker
from game.card import Card


def fresh_tracker():
    """Vytvorí tracker a rovno vynuluje jeho dáta, aby každý test začínal odznova."""
    t = AchievementTracker()
    for k in t.data["unlocked"]:
        t.data["unlocked"][k] = False
    t.data["stats"] = {
        "wins_total": 0, "games_played": 0,
        "win_streak_current": 0, "win_streak_best": 0
    }
    t.reset_game()
    t.reset_round()
    return t


def check(name, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}")


# ------------------------------------------------------------------
# Šťastný nákup
# ------------------------------------------------------------------

def test_lucky_pickup():
    print("\n--- Sťastný nákup ---")

    t = fresh_tracker()
    t.on_talon_received([Card("heart", "ace"), Card("bell", "ace")])
    check("2x eso", "lucky_pickup" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_talon_received([Card("heart", "ten"), Card("bell", "ten")])
    check("2x desiatka", "lucky_pickup" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_talon_received([Card("heart", "ace"), Card("bell", "ten")])
    check("eso + desiatka", "lucky_pickup" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_talon_received([Card("heart", "king"), Card("heart", "over")])
    check("kompletny tromfovy par", "lucky_pickup" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_talon_received([Card("heart", "king"), Card("bell", "over")])
    check("NEMA byt: par roznych farieb", "lucky_pickup" not in t.newly_unlocked)

    t = fresh_tracker()
    t.on_talon_received([Card("heart", "seven"), Card("bell", "eight")])
    check("NEMA byt: nahodne karty", "lucky_pickup" not in t.newly_unlocked)


# ------------------------------------------------------------------
# Tromfy
# ------------------------------------------------------------------

def test_trump_declarations():
    print("\n--- Tromfy ---")

    t = fresh_tracker()
    t.on_trump_declared(suit="heart", trick_number=1, hand_cards=[], is_new_trump=False)
    check("Prvy tromf", "first_trump" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_trump_declared(suit="heart", trick_number=1, hand_cards=[], is_new_trump=False)
    t.on_trump_declared(suit="bell", trick_number=3, hand_cards=[], is_new_trump=True)
    check("Tromfovy kral I. (2 farby)", "trump_king_2" in t.newly_unlocked)
    check("Karta sa obratila (is_new_trump)", "trump_override" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_trump_declared(suit="heart", trick_number=1, hand_cards=[], is_new_trump=False)
    t.on_trump_declared(suit="bell", trick_number=2, hand_cards=[], is_new_trump=True)
    t.on_trump_declared(suit="leaf", trick_number=3, hand_cards=[], is_new_trump=True)
    check("Tromfovy kral II. (3 farby)", "trump_king_3" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_trump_declared(suit="heart", trick_number=1, hand_cards=[], is_new_trump=False, is_human=False)
    t.on_trump_declared(suit="bell", trick_number=2, hand_cards=[], is_new_trump=True, is_human=False)
    t.on_trump_declared(suit="leaf", trick_number=3, hand_cards=[], is_new_trump=True, is_human=True)
    check("Posledne slovo (3. v poradi)", "last_word" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_trump_declared(suit="heart", trick_number=1, hand_cards=[], is_new_trump=False, is_human=True)
    check("NEMA byt: Posledne slovo pri 1. hlaseni", "last_word" not in t.newly_unlocked)

    t = fresh_tracker()
    t.on_trump_declared(suit="heart", trick_number=8, hand_cards=[], is_new_trump=False)
    check("Lepsie neskoro ako nikdy (trick_number=8)", "last_chance_trump" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_trump_declared(suit="heart", trick_number=5, hand_cards=[], is_new_trump=False)
    check("NEMA byt: trick_number=5", "last_chance_trump" not in t.newly_unlocked)

    t = fresh_tracker()
    t.round_had_ace_at_start = False
    t.on_trump_declared(suit="heart", trick_number=1, hand_cards=[], is_new_trump=False)
    check("Bez poistky (no ace at start)", "no_safety_net" in t.newly_unlocked)

    t = fresh_tracker()
    t.round_had_ace_at_start = True
    t.on_trump_declared(suit="heart", trick_number=1, hand_cards=[], is_new_trump=False)
    check("NEMA byt: Bez poistky ak mal eso", "no_safety_net" not in t.newly_unlocked)


# ------------------------------------------------------------------
# Tichy pozorovatel
# ------------------------------------------------------------------

def test_silent_watcher():
    print("\n--- Tichy pozorovatel ---")

    t = fresh_tracker()
    t.on_bidding_passed_with_trumps(1)
    check("Tichy pozorovatel I. (1 par)", "silent_watcher_1" in t.newly_unlocked)
    check("NEMA byt II. stupen pri 1 pare", "silent_watcher_2" not in t.newly_unlocked)

    t = fresh_tracker()
    t.on_bidding_passed_with_trumps(2)
    check("Tichy pozorovatel I.+II. (2 pary)", "silent_watcher_1" in t.newly_unlocked
          and "silent_watcher_2" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_bidding_passed_with_trumps(3)
    check("Tichy pozorovatel I.+II.+III. (3 pary)",
          all(x in t.newly_unlocked for x in
              ["silent_watcher_1", "silent_watcher_2", "silent_watcher_3"]))

    t = fresh_tracker()
    t.on_bidding_passed_with_trumps(0)
    check("NEMA byt nic pri 0 paroch", len(t.newly_unlocked) == 0)


# ------------------------------------------------------------------
# Krasne ale zbytocne (odhodenie hlasky do talonu)
# ------------------------------------------------------------------

def test_discard():
    print("\n--- Hlaska do kosa ---")

    t = fresh_tracker()
    t.on_discard([Card("heart", "king"), Card("heart", "over")])
    check("kompletny par v discarde", "pretty_but_useless" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_discard([Card("heart", "king"), Card("bell", "over")])
    check("NEMA byt: par roznych farieb", "pretty_but_useless" not in t.newly_unlocked)

    t = fresh_tracker()
    t.on_discard([Card("heart", "king"), Card("heart", "seven")])
    check("NEMA byt: len kral bez hornika", "pretty_but_useless" not in t.newly_unlocked)


# ------------------------------------------------------------------
# Uz bolo na case (streak bez tromfu)
# ------------------------------------------------------------------

def test_too_late_now():
    print("\n--- Uz bolo na case ---")

    t = fresh_tracker()
    for _ in range(7):
        t.on_round_hand_ready(has_trump_pair=False)
    check("Po 7 kolach bez tromfu este NIC", len(t.newly_unlocked) == 0)

    t.on_round_hand_ready(has_trump_pair=True)
    check("8. kolo s tromfom po 7 bez neho", "too_late_now" in t.newly_unlocked)

    t2 = fresh_tracker()
    for _ in range(3):
        t2.on_round_hand_ready(has_trump_pair=False)
    t2.on_round_hand_ready(has_trump_pair=True)
    check("NEMA byt: len 3 kola bez tromfu", "too_late_now" not in t2.newly_unlocked)


# ------------------------------------------------------------------
# Koniec kola — dominancia, greedy, bid tiery, barely_made_it
# ------------------------------------------------------------------

def test_round_finished():
    print("\n--- Koniec kola ---")

    t = fresh_tracker()
    t.round_tricks_won_by_human = 10
    t.round_trumps_declared = {"heart"}
    t.on_round_finished(human_is_bidder=True, human_bid=50,
                        human_round_points=50, human_fulfilled=True,
                        human_card_points_only=0)
    check("Dominancia (10 stichov)", "dominance" in t.newly_unlocked)
    check("Absolutna nadvlada I. (1 tromf)", "absolute_rule_1" in t.newly_unlocked)
    check("NEMA byt II. stupen (len 1 tromf)", "absolute_rule_2" not in t.newly_unlocked)

    t = fresh_tracker()
    t.round_tricks_won_by_human = 10
    t.round_trumps_declared = {"heart", "bell"}
    t.on_round_finished(human_is_bidder=True, human_bid=50,
                        human_round_points=50, human_fulfilled=True,
                        human_card_points_only=0)
    check("Absolutna nadvlada II. (2 tromfy)", "absolute_rule_2" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_round_finished(human_is_bidder=False, human_bid=0,
                        human_round_points=0, human_fulfilled=True,
                        human_card_points_only=120)
    check("Kazdy bod sa pocita (120b)", "greedy" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_round_finished(human_is_bidder=True, human_bid=50,
                        human_round_points=60, human_fulfilled=True,
                        human_card_points_only=0)
    check("Skromny vitaz (bid=50, splnil)", "modest_winner" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_round_finished(human_is_bidder=True, human_bid=50,
                        human_round_points=50, human_fulfilled=True,
                        human_card_points_only=0)
    check("S odretymi usami (presne na bid)", "barely_made_it" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_round_finished(human_is_bidder=True, human_bid=200,
                        human_round_points=200, human_fulfilled=True,
                        human_card_points_only=0)
    check("Odvazny pokus (bid 200)", "bid_200" in t.newly_unlocked)
    check("NEMA byt Velke oci pri bid 200", "bid_250" not in t.newly_unlocked)

    t = fresh_tracker()
    t.on_round_finished(human_is_bidder=True, human_bid=300,
                        human_round_points=300, human_fulfilled=True,
                        human_card_points_only=0)
    check("Podrzte mi pivo (bid 300) + nizsie stupne",
          "bid_200" in t.newly_unlocked and "bid_250" in t.newly_unlocked
          and "bid_300" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_round_finished(human_is_bidder=True, human_bid=200,
                        human_round_points=150, human_fulfilled=False,
                        human_card_points_only=0)
    check("NEMA byt nic ak nesplnil povinnost", len(t.newly_unlocked) == 0)


# ------------------------------------------------------------------
# Koniec hry
# ------------------------------------------------------------------

def test_game_finished():
    print("\n--- Koniec hry ---")

    t = fresh_tracker()
    t.on_game_finished(human_won=True, human_final_score=1050, opponent_scores=[800, 700])
    check("Zaciname (prva vyhra)", "first_win" in t.newly_unlocked)

    t = fresh_tracker()
    t.game_was_bidder = False
    t.on_game_finished(human_won=True, human_final_score=1000, opponent_scores=[500, 400])
    check("Kto mlci vyhrava (nikdy nedrazil)", "passivist" in t.newly_unlocked)

    t = fresh_tracker()
    t.game_was_bidder = True
    t.on_game_finished(human_won=True, human_final_score=1000, opponent_scores=[500, 400])
    check("NEMA byt Kto mlci vyhrava ak drazil", "passivist" not in t.newly_unlocked)

    t = fresh_tracker()
    t.game_min_score = -250
    t.on_game_finished(human_won=True, human_final_score=1000, opponent_scores=[500, 400])
    check("Fenix (comeback z -250)", "comeback" in t.newly_unlocked)

    t = fresh_tracker()
    t.game_min_score = -100
    t.on_game_finished(human_won=True, human_final_score=1000, opponent_scores=[500, 400])
    check("NEMA byt Fenix (len -100)", "comeback" not in t.newly_unlocked)

    t = fresh_tracker()
    t.on_game_finished(human_won=True, human_final_score=1000, opponent_scores=[500, 400])
    check("Presna tisicka (presne 1000)", "close_win" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_game_finished(human_won=True, human_final_score=1050, opponent_scores=[500, 400])
    check("NEMA byt Presna tisicka (1050)", "close_win" not in t.newly_unlocked)

    t = fresh_tracker()
    t.game_trump_declarations = 3
    t.on_game_finished(human_won=True, human_final_score=1000, opponent_scores=[500, 400])
    check("Trikrat a dost (3 tromfy)", "discreet" in t.newly_unlocked)

    t = fresh_tracker()
    t.game_trump_declarations = 1
    t.on_game_finished(human_won=True, human_final_score=1000, opponent_scores=[500, 400])
    check("Trikrat a dost (1 tromf, <=3)", "discreet" in t.newly_unlocked)

    t = fresh_tracker()
    t.game_trump_declarations = 5
    t.on_game_finished(human_won=True, human_final_score=1000, opponent_scores=[500, 400])
    check("NEMA byt Trikrat a dost (5 tromfov)", "discreet" not in t.newly_unlocked)

    # Streak
    t = fresh_tracker()
    for _ in range(3):
        t.data["stats"]["win_streak_current"] += 1  # simulacia predchadzajucich vyhier
    t.on_game_finished(human_won=True, human_final_score=1000, opponent_scores=[500, 400])
    check("Neporazitelny Bronz (streak 3)", "unbeatable_bronze" in t.newly_unlocked)

    # Smoliar
    t = fresh_tracker()
    t.on_game_finished(human_won=False, human_final_score=950, opponent_scores=[980, 700])
    check("Smoliar (prehra o 30b)", "unlucky" in t.newly_unlocked)

    t = fresh_tracker()
    t.on_game_finished(human_won=False, human_final_score=800, opponent_scores=[980, 700])
    check("NEMA byt Smoliar (prehra o 180b)", "unlucky" not in t.newly_unlocked)


# ------------------------------------------------------------------
# Spustenie vsetkych testov
# ------------------------------------------------------------------

if __name__ == "__main__":
    test_lucky_pickup()
    test_trump_declarations()
    test_silent_watcher()
    test_discard()
    test_too_late_now()
    test_round_finished()
    test_game_finished()
    print("\nHotovo. Skontroluj vyssie ci su vsetky testy [PASS].")