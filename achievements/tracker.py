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
        # ← NOVÉ (2026-11-01): skóre na začiatku posledne odohraného kola —
        # pre "Kto sa smeje naposledy" (porovnanie pred rozhodujúcim kolom)
        self.game_round_start_human_score: int | None = None
        self.game_round_start_opponent_scores: list[int] | None = None

        self.round_trumps_declared: set[str] = set()
        self.round_tricks_won_by_human: int = 0
        self.round_human_bid: bool = False
        self.round_human_card_points: int = 0
        self.round_all_trump_declarations: int = 0  # ← NOVÉ: všetky (aj AI) v kole
        # ← NOVÉ (2026-11-01): poradie hlášok v kole (pre "Dva kohúty..."
        # a "Posledné slovo") — "human" alebo player_index súpera
        self.round_trump_order: list = []
        # ← NOVÉ (2026-11-01): poradie (1-indexované) human-ovej PRVEJ
        # hlášky v kole, pre "Posledné slovo"
        self.round_human_first_trump_position: int | None = None

    # ------------------------------------------------------------------
    # Reset stavu
    # ------------------------------------------------------------------

    def reset_game(self):
        self.game_min_score = 0
        self.game_was_bidder = False
        self.game_trump_declarations = 0
        self.game_no_trump_streak = 0  # ← NOVÉ
        self.game_round_start_human_score = None
        self.game_round_start_opponent_scores = None
        self.newly_unlocked = []

    def reset_round(self):
        self.round_trumps_declared = set()
        self.round_tricks_won_by_human = 0
        self.round_human_bid = False
        self.round_human_card_points = 0
        self.round_all_trump_declarations = 0
        self.round_had_ace_at_start = True  # ← NOVÉ
        self.round_trump_order = []
        self.round_human_first_trump_position = None

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
                          is_human: bool = True, player_index: int | None = None):
        """
        is_human: True ak tromf hlási human hráč (False pre AI — voláme len
                  kvôli počítaniu poradia pre 'last_word'/'two_roosters')
        player_index: index hráča, ktorý hlási (human aj AI) — identifikuje
                      KTORÝ súper hlási, pre 'two_roosters' ("human" pre
                      human sa ukladá vždy, nech sa pozná od AI indexov)
        """
        self.round_all_trump_declarations += 1
        self.round_trump_order.append("human" if is_human else player_index)

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

        # Posledné slovo — poradie PRVEJ human hlášky v kole si len
        # zapamätáme (1-indexovane); samotné odomknutie je v
        # on_round_finished, kedy už vieme, či bola aj posledná v kole.
        if self.round_human_first_trump_position is None:
            self.round_human_first_trump_position = self.round_all_trump_declarations

        # Dva kohúty na jednom smetisku — human, potom 1-2 hlášky JEDNÉHO
        # súpera, potom opäť human (vyhodnotí sa vždy pri human hláške).
        self._check_two_roosters()

        if trick_number == 8:
            self._unlock("last_chance_trump")

        # Bez poistky sa nepočíta pri hlásení v 1. štichu (nový variant) —
        # tam je riziko iné (hlásiš bez zabezpečeného štichu, nie bez esa).
        if not self.round_had_ace_at_start and trick_number != 0:
            self._unlock("no_safety_net")

        self._save()

    def _check_two_roosters(self):
        """'Dva kohúty na jednom smetisku': human hlási, potom JEDEN
        konkrétny súper hlási 1 alebo 2 tromfy, a human hlási znova."""
        seq = self.round_trump_order
        if len(seq) < 3 or seq[-1] != "human":
            return
        opp = seq[-2]
        if opp == "human" or opp is None:
            return
        if seq[-3] == "human":
            self._unlock("two_roosters")
            return
        if len(seq) >= 4 and seq[-3] == opp and seq[-4] == "human":
            self._unlock("two_roosters")

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
            # Na doraz — presne bid, žiadne body navyše (len od povinnosti
            # 60+, aby sa neprekrývala so "Skromný víťaz" pri 50)
            if human_bid >= 60 and human_round_points == human_bid:
                self._unlock("barely_made_it")  # nie "on_the_edge"

        # Posledné slovo — human zahlásil svoju PRVÚ hlášku kola ako 3. či
        # 4. v poradí A nikto (ani on sám) po nej už v tomto kole nehlásil.
        if (self.round_human_first_trump_position in (3, 4)
                and self.round_human_first_trump_position
                    == self.round_all_trump_declarations):
            self._unlock("last_word")

        self._save()

    # ------------------------------------------------------------------
    # Event: aktualizácia skóre (volať po každom kole pre comeback tracking)
    # ------------------------------------------------------------------

    def on_score_updated(self, human_total_score: int):
        if human_total_score < self.game_min_score:
            self.game_min_score = human_total_score

    # ------------------------------------------------------------------
    # Event: nové kolo začína (volať PRED rozdaním, so skóre PRED kolom)
    # ------------------------------------------------------------------

    def on_round_started(self, human_score: int, opponent_scores: list[int]):
        """Zapamätá skóre na začiatku kola — prepisuje sa každé kolo, takže
        na konci hry obsahuje skóre pred POSLEDNÝM (rozhodujúcim) kolom.
        Pre 'Kto sa smeje naposledy'."""
        self.game_round_start_human_score = human_score
        self.game_round_start_opponent_scores = list(opponent_scores)

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
        # ← NOVÉ (2026-11-01): body zahodených kariet sa víťazovi dražby
        # reálne počítajú (game/round.py: discard_cards → add_trick_points),
        # takže musia ísť aj do počítadla pre "Každý bod sa počíta" — inak
        # bolo nedosiahnuteľné, keď sa do talonu zahodila čo i len jedna
        # bodovaná karta (kráľ/horník/dolník; eso a desiatka sa zahodiť
        # nedajú).
        self.round_human_card_points += sum(c.points for c in discarded_cards)

        suits_discarded = {}
        for card in discarded_cards:
            if card.rank in ("king", "over"):
                suits_discarded.setdefault(card.suit, set()).add(card.rank)

        for suit, ranks in suits_discarded.items():
            if "king" in ranks and "over" in ranks:
                self._unlock("pretty_but_useless")

        self._save()

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
            if streak >= 7:
                self._unlock("unbeatable_gold")

            if self.game_min_score <= -100:
                self._unlock("comeback")

            if human_final_score == 1000:
                self._unlock("close_win")

            if 1 <= self.game_trump_declarations <= 3:
                self._unlock("discreet")

            # Kto sa smeje naposledy — pred posledným (rozhodujúcim) kolom
            # mal aspoň jeden súper viac bodov než human, a napriek tomu
            # human vyhral celú hru.
            if (self.game_round_start_opponent_scores
                    and self.game_round_start_human_score is not None
                    and any(s > self.game_round_start_human_score
                            for s in self.game_round_start_opponent_scores)):
                self._unlock("last_laugh")

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