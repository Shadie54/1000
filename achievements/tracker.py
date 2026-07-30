# achievements/tracker.py

from achievements.storage import load_achievements, save_achievements


class AchievementTracker:
    """
    Sleduje herné udalosti a odomyká achievementy.
    Jedna inštancia žije počas celého behu aplikácie (drží perzistentné dáta),
    ale resetuje kolo/hru-špecifický stav pri každej novej hre/kole.
    """

    def __init__(self):
        self.data = load_achievements()
        self.newly_unlocked: list[str] = []

        self.game_min_score: int = 0
        self.game_was_bidder: bool = False
        self.game_trump_declarations: int = 0
        self.game_no_trump_streak: int = 0  # ← NOVÉ

        self.round_trumps_declared: set[str] = set()
        self.round_tricks_won_by_human: int = 0
        self.round_human_bid: bool = False
        self.round_human_card_points: int = 0
        self.round_all_trump_declarations: int = 0  # ← NOVÉ: všetky (aj AI) v kole

    # ------------------------------------------------------------------
    # Reset stavu
    # ------------------------------------------------------------------

    def reset_game(self):
        self.game_min_score = 0
        self.game_was_bidder = False
        self.game_trump_declarations = 0
        self.game_no_trump_streak = 0  # ← NOVÉ
        self.newly_unlocked = []

    def reset_round(self):
        self.round_trumps_declared = set()
        self.round_tricks_won_by_human = 0
        self.round_human_bid = False
        self.round_human_card_points = 0
        self.round_all_trump_declarations = 0
        self.round_had_ace_at_start = True  # ← NOVÉ

    # ------------------------------------------------------------------
    # Odomykanie — jadro
    # ------------------------------------------------------------------

    def _unlock(self, achievement_id: str):
        """Odomkne achievement ak ešte nebol odomknutý."""
        if not self.data["unlocked"].get(achievement_id, False):
            self.data["unlocked"][achievement_id] = True
            self.newly_unlocked.append(achievement_id)
            print(f"🏆 ACHIEVEMENT UNLOCKED: {achievement_id}")  # ← DOČASNÉ

    def _save(self):
        save_achievements(self.data)

    def pop_notifications(self) -> list[str]:
        """Vráti a vyprázdni zoznam novo odomknutých achievementov (pre popup)."""
        result = self.newly_unlocked
        self.newly_unlocked = []
        return result

    # ------------------------------------------------------------------
    # Event: hráč zahlásil tromf
    # ------------------------------------------------------------------

    def on_trump_declared(self, suit: str, trick_number: int,
                          hand_cards: list, is_new_trump: bool,
                          is_human: bool = True):
        """
        is_human: True ak tromf hlási human hráč (False pre AI — voláme len
                  kvôli počítaniu poradia pre 'last_word')
        """
        self.round_all_trump_declarations += 1

        if not is_human:
            return  # zvyšok metódy sleduje len human achievementy

        self.game_trump_declarations += 1
        self.round_trumps_declared.add(suit)

        if self.game_trump_declarations == 1:
            self._unlock("first_trump")

        if len(self.round_trumps_declared) >= 2:
            self._unlock("trump_king_2")
        if len(self.round_trumps_declared) >= 3:
            self._unlock("trump_king_3")

        if is_new_trump:
            self._unlock("trump_override")

        # ← NOVÉ: Posledné slovo — human je 3. alebo ďalší v poradí
        if self.round_all_trump_declarations >= 3:
            self._unlock("last_word")

        if trick_number == 8:
            self._unlock("last_chance_trump")

        if not self.round_had_ace_at_start:
            self._unlock("no_safety_net")

        self._save()

    # ------------------------------------------------------------------
    # Event: hráč pasoval v dražbe (na konci dražby)
    # ------------------------------------------------------------------

    def on_bidding_passed_with_trumps(self, trump_pair_count: int):
        """
        Volať keď human PASOVAL (nikdy nezvýšil bid) a dražba skončila.
        trump_pair_count: koľko rôznych tromfových párov mal na ruke pri rozdaní.
        """
        if trump_pair_count >= 1:
            self._unlock("silent_watcher_1")
        if trump_pair_count >= 2:
            self._unlock("silent_watcher_2")
        if trump_pair_count >= 3:
            self._unlock("silent_watcher_3")
        self._save()

    def on_bid_placed(self):
        """Volať keď human položí akúkoľvek ponuku (nie pas)."""
        self.game_was_bidder = True
        self.round_human_bid = True  # ← NOVÉ

    # ------------------------------------------------------------------
    # Event: štich vyhraný
    # ------------------------------------------------------------------

    def on_trick_won(self, winner_is_human: bool, trick_points: int = 0):
        if winner_is_human:
            self.round_tricks_won_by_human += 1
            self.round_human_card_points += trick_points  # ← NOVÉ

    # ------------------------------------------------------------------
    # Event: koniec kola
    # ------------------------------------------------------------------

    def on_round_finished(self, human_is_bidder: bool, human_bid: int,
                          human_round_points: int, human_fulfilled: bool,
                          human_card_points_only: int):
        """
        human_round_points: celkové body kola (vrátane tromfov)
        human_card_points_only: body len z kariet (bez tromfu) — pre 'greedy'
        """
        # Dominancia
        if self.round_tricks_won_by_human == 10:
            self._unlock("dominance")
            trumps_this_round = len(self.round_trumps_declared)
            if trumps_this_round >= 1:
                self._unlock("absolute_rule_1")
            if trumps_this_round >= 2:
                self._unlock("absolute_rule_2")

        # Nenásytný — 120 bodov z kariet bez tromfu
        if human_card_points_only >= 120:
            self._unlock("greedy")

        if human_is_bidder and human_fulfilled:
            # Skromný víťaz
            if human_bid == 50:
                self._unlock("modest_winner")
            # Stupňovaná dražba
            if human_bid >= 200:
                self._unlock("bid_200")
            if human_bid >= 250:
                self._unlock("bid_250")
            if human_bid >= 300:
                self._unlock("bid_300")
            # Na doraz — presne bid, žiadne body navyše
            if human_round_points == human_bid:
                self._unlock("barely_made_it")  # nie "on_the_edge"

        self._save()

    # ------------------------------------------------------------------
    # Event: aktualizácia skóre (volať po každom kole pre comeback tracking)
    # ------------------------------------------------------------------

    def on_score_updated(self, human_total_score: int):
        if human_total_score < self.game_min_score:
            self.game_min_score = human_total_score

    # ------------------------------------------------------------------
    # Event: Máme tromf či eso v ruke
    # ------------------------------------------------------------------

    def on_round_hand_ready(self, has_trump_pair: bool, has_ace: bool = True):
        if has_trump_pair:
            if self.game_no_trump_streak >= 7:
                self._unlock("too_late_now")
            self.game_no_trump_streak = 0
        else:
            self.game_no_trump_streak += 1

        self.round_had_ace_at_start = has_ace  # ← NOVÉ

    # ------------------------------------------------------------------
    # Event: Zahodenie hlášky do talonu, Získanie talonu
    # ------------------------------------------------------------------

    def on_discard(self, discarded_cards: list):
        """Volať keď human zahodí karty do talonu."""
        suits_discarded = {}
        for card in discarded_cards:
            if card.rank in ("king", "over"):
                suits_discarded.setdefault(card.suit, set()).add(card.rank)

        for suit, ranks in suits_discarded.items():
            if "king" in ranks and "over" in ranks:
                self._unlock("pretty_but_useless")
                self._save()
                return

    def on_talon_received(self, talon_cards: list):
        """Volať keď human dostane karty z talonu (pred zahodením)."""
        if len(talon_cards) != 2:
            return

        ranks = [c.rank for c in talon_cards]
        suits = [c.suit for c in talon_cards]

        is_lucky = False

        # 2x eso
        if ranks.count("ace") == 2:
            is_lucky = True
        # 2x desiatka
        elif ranks.count("ten") == 2:
            is_lucky = True
        # eso + desiatka (v ľubovoľnom poradí)
        elif set(ranks) == {"ace", "ten"}:
            is_lucky = True
        # kompletný tromfový pár (king + over rovnakej farby)
        elif set(ranks) == {"king", "over"} and suits[0] == suits[1]:
            is_lucky = True

        if is_lucky:
            self._unlock("lucky_pickup")
            self._save()

    # ------------------------------------------------------------------
    # Event: koniec hry
    # ------------------------------------------------------------------

    def on_game_finished(self, human_won: bool, human_final_score: int,
                         opponent_scores: list[int]):
        self.data["stats"]["games_played"] += 1

        if human_won:
            self.data["stats"]["wins_total"] += 1
            self.data["stats"]["win_streak_current"] += 1
            self.data["stats"]["win_streak_best"] = max(
                self.data["stats"]["win_streak_best"],
                self.data["stats"]["win_streak_current"]
            )

            wins = self.data["stats"]["wins_total"]
            if wins >= 1:
                self._unlock("first_win")
            if wins >= 10:
                self._unlock("wins_10")
            if wins >= 50:
                self._unlock("wins_50")
            if wins >= 100:
                self._unlock("wins_100")

            streak = self.data["stats"]["win_streak_current"]
            if streak >= 3:
                self._unlock("unbeatable_bronze")
            if streak >= 5:
                self._unlock("unbeatable_silver")
            if streak >= 10:
                self._unlock("unbeatable_gold")

            if not self.game_was_bidder:
                self._unlock("passivist")

            if self.game_min_score <= -200:
                self._unlock("comeback")

            if human_final_score == 1000:
                self._unlock("close_win")

            if 1 <= self.game_trump_declarations <= 3:
                self._unlock("discreet")

        else:
            self.data["stats"]["win_streak_current"] = 0

            best_opponent = max(opponent_scores) if opponent_scores else 0
            diff = best_opponent - human_final_score
            if 0 <= diff <= 50:
                self._unlock("unlucky")

        self._save()

    def __repr__(self):
        unlocked_count = sum(1 for v in self.data["unlocked"].values() if v)
        return f"AchievementTracker({unlocked_count} unlocked)"