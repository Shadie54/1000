# game/ai_strategy.py

from game.card import Card
from game.ai_memory import AIMemory
from game.ai_evaluator import AIEvaluator
from game.trick import Trick
from game import ai_strategies_const as SC
from config import SUITS, TRUMP_POINTS


class AIStrategy:
    def __init__(self, memory: AIMemory, evaluator: AIEvaluator,
                 difficulty: str = "hard",
                 logger=None, player_name: str = "AI"):
        self.memory = memory
        self.evaluator = evaluator
        self.difficulty = difficulty
        self.logger = logger
        self.player_name = player_name

    def _log(self, strategy: str, details: str = ""):
        """Zaloguje stratégiu ak je logger dostupný."""
        if self.logger:
            self.logger.log_strategy(self.player_name, strategy, details)

    # ------------------------------------------------------------------
    # Bidding
    # ------------------------------------------------------------------

    def decide_bid(self, hand: list[Card], current_bid: int,
                   has_obligation: bool, trump_suit: str | None) -> int | None:
        if self.difficulty == "easy":
            return None

        # S14 — SECURE_TRUMP_BID
        if self.difficulty == "hard":
            secure_bid = self._check_secure_trump_bid(hand, current_bid)
            if secure_bid:
                self._log(SC.SECURE_TRUMP_BID,
                          f"plonkový tromf → bid {secure_bid}")
                return secure_bid

        # S27 — PASSIVE_BID
        if self.difficulty == "hard" and not has_obligation:
            if self._check_passive_bid(hand, current_bid):
                self._log(SC.PASSIVE_BID, "2+ esá + tromfy → pasuj")
                self.memory.claim_lead_active = True  # ← aktivuj S28
                return None

        # S11 — PASS_FOR_TRUMP
        if self.difficulty == "hard":
            if self.evaluator.should_pass_for_trumps(hand, current_bid):
                if not has_obligation:
                    self._log(SC.PASS_FOR_TRUMP,
                              "silné hlášky, slabé štichy → pas")
                    return None

        # S16 — LONG_SUIT_BID log
        long_bonus = self.evaluator.get_long_suit_bid_bonus(hand)
        if long_bonus > 0:
            self._log(SC.LONG_SUIT_BID, f"dlhá farba → bonus +{long_bonus}")

        # S10 — BID_ESTIMATE
        estimate = self.evaluator.calculate_bid_estimate(hand, trump_suit)
        if estimate >= current_bid + 10:
            self._log(SC.BID_ESTIMATE,
                      f"odhad={estimate} → bid {current_bid + 10}")
            return current_bid + 10

        if has_obligation:
            return None

        return None

    def _check_secure_trump_bid(self, hand: list[Card],
                                 current_bid: int) -> int | None:
        """
        S14 — Skontroluje či má AI plonkový tromf + eso.
        Vracia odporúčaný bid alebo None.
        """
        for suit in SUITS:
            has_over = any(c.suit == suit and c.rank == "over" for c in hand)
            has_king = any(c.suit == suit and c.rank == "king" for c in hand)
            if not (has_over and has_king):
                continue

            # Plonkový tromf = len 2 karty tejto farby
            suit_cards = [c for c in hand if c.suit == suit]
            if len(suit_cards) != 2:
                continue

            # Musí mať eso (akejkoľvek farby)
            has_ace = any(c.rank == "ace" for c in hand)
            if not has_ace:
                continue

            # Odporúčaný bid = eso(11) + tromf hodnota
            trump_val = TRUMP_POINTS[suit]
            recommended = ((11 + trump_val) // 10) * 10  # zaokrúhli na desiatky

            if recommended >= current_bid + 10:
                return current_bid + 10

        return None

    # ------------------------------------------------------------------
    # Navýšenie po talóne
    # ------------------------------------------------------------------

    def decide_raise_after_talon(self, hand: list[Card],
                                  current_bid: int,
                                  trump_suit: str | None) -> int | None:
        if self.difficulty == "easy":
            return None

        result = self.evaluator.should_raise_after_talon(
            hand, current_bid, trump_suit
        )
        if result:
            self._log(SC.RAISE_AFTER_TALON,
                     f"po talóne navýšenie na {result}")
        return result

    # ------------------------------------------------------------------
    # Zahadzovanie
    # ------------------------------------------------------------------

    def decide_discard(self, hand: list[Card]) -> list[Card]:
        if self.difficulty == "easy":
            candidates = [c for c in hand if c.rank not in ("ace", "ten")]
            return candidates[:2]

        candidates = self.evaluator.get_discard_candidates(hand)
        result = candidates[:2]
        self._log(SC.SMART_DISCARD,
                 f"zahodí: {[str(c) for c in result]}")
        return result

    # ------------------------------------------------------------------
    # Tromfy
    # ------------------------------------------------------------------

    def decide_trump(self, hand: list[Card], trick_number: int,
                     is_leader: bool, current_trump: str | None) -> str | None:
        if self.difficulty == "easy":
            return None
        if not is_leader or trick_number == 0:
            return None

        # Deaktivuj S28 keď sme leader ← pridané
        if self.memory.claim_lead_active:
            self.memory.claim_lead_active = False
            self._log(SC.CLAIM_LEAD, "lead získaný → deaktivujem S28")

        available = [
            suit for suit in SUITS
            if any(c.suit == suit and c.rank == "over" for c in hand)
               and any(c.suit == suit and c.rank == "king" for c in hand)
        ]
        if not available:
            return None

        if self.difficulty == "medium":
            best = max(available, key=lambda s: TRUMP_POINTS[s])
            self._log(SC.TRUMP_DECLARE, f"tromf: {best}")
            return best

        best = self._choose_best_trump(hand, available, current_trump)
        if best:
            self._log(SC.TRUMP_DECLARE,
                      f"tromf: {best} ({TRUMP_POINTS[best]} bodov)")
        return best

    def _choose_best_trump(self, hand: list[Card], available: list[str],
                            current_trump: str | None) -> str | None:
        best_suit = None
        best_score = -1

        for suit in available:
            score = TRUMP_POINTS[suit]
            has_ace = any(c.suit == suit and c.rank == "ace" for c in hand)
            if has_ace:
                score += 20
            suit_count = sum(1 for c in hand if c.suit == suit)
            score += suit_count * 5
            opponents_void = all(
                self.memory.is_suit_void(i, suit)
                for i in range(3)
                if i != self.memory.player_index
            )
            if opponents_void:
                score += 30
            if score > best_score:
                best_score = score
                best_suit = suit

        return best_suit

    # ------------------------------------------------------------------
    # Výber karty
    # ------------------------------------------------------------------

    def decide_card(self, hand: list[Card], playable: list[Card],
                    trick: Trick, trick_number: int,
                    player_index: int) -> Card:
        if self.difficulty == "easy":
            import random
            return random.choice(playable)

        is_leader = (trick.leader_index == player_index
                     and len(trick.played_cards) == 0)

        if is_leader:
            return self._decide_as_leader(hand, playable, trick_number)
        else:
            return self._decide_as_follower(hand, playable, trick)

    # ------------------------------------------------------------------
    # Výber karty — leader
    # ------------------------------------------------------------------

    def _decide_as_leader(self, hand: list[Card], playable: list[Card],
                          trick_number: int) -> Card:
        trump_suit = self.memory.current_trump

        # S21 — ENDGAME (posledné 2-3 štichy)
        if self.difficulty == "hard" and trick_number >= 7:
            endgame = self._get_endgame_card(hand, playable)
            if endgame:
                self._log(SC.ENDGAME, f"{endgame}")
                return endgame

        # S1 — CERTAIN_TRICK
        guaranteed = self.evaluator.get_guaranteed_tricks(hand, trump_suit)
        guaranteed_playable = [c for c in guaranteed if c in playable]
        if guaranteed_playable:
            card = max(guaranteed_playable, key=lambda c: c.points)
            self._log(SC.CERTAIN_TRICK, f"{card}")
            return card

        # S5 — TRUMP_DECLARE
        if trick_number > 0:
            for suit in SUITS:
                has_over = any(c.suit == suit and c.rank == "over" for c in hand)
                has_king = any(c.suit == suit and c.rank == "king" for c in hand)
                if has_over and has_king:
                    trump_card = next(
                        (c for c in playable
                         if c.suit == suit and c.rank in ("king", "over")),
                        None
                    )
                    if trump_card:
                        self._log(SC.TRUMP_DECLARE,
                                  f"{trump_card} → zahlási tromf {suit}")
                        return trump_card

        # S3 — FORCING
        if self.difficulty == "hard":
            forcing = self.evaluator.get_forcing_opportunities(hand, trump_suit)
            for opp in forcing:
                backup = opp.get("backup_count", 1)

                # Prah závisí od počtu záložných kariet
                if backup >= 2:
                    threshold = 0.3  # 2+ zálohy → aj 30% stačí
                elif backup == 1:
                    threshold = 0.5  # 1 záloha → aspoň 50%
                else:
                    threshold = 0.7  # žiadna záloha → vysoká istota

                if (opp["probability"] >= threshold
                        and opp["forcing_card"] in playable):
                    self._log(SC.FORCING,
                              f"{opp['forcing_card']} → chráni {opp['protected_card']} "
                              f"(p={opp['probability']:.0%}, backup={backup})")
                    return opp["forcing_card"]

        # S4 — PASSIVE
        card = self._play_safest_card(playable, hand)
        self._log(SC.PASSIVE, f"{card}")
        return card

    def _get_endgame_card(self, hand: list[Card],
                          playable: list[Card]) -> Card | None:
        """
        S21 — Koncovka (posledné 2-3 štichy).
        Prepočítaj presne čo ostalo — hraj matematicky.
        """
        trump_suit = self.memory.current_trump

        # Nájdi všetky istý štichy v koncovke
        guaranteed = self.evaluator.get_guaranteed_tricks(hand, trump_suit)
        guaranteed_playable = [c for c in guaranteed if c in playable]

        if guaranteed_playable:
            # Zahraj istý štych s najvyššími bodmi
            return max(guaranteed_playable, key=lambda c: c.points)

        # Ak nemám istý štych — zahraj najnižšiu kartu
        # (v koncovke nechceme riskovať)
        return min(playable, key=lambda c: (c.points, c.rank_order))

    # ------------------------------------------------------------------
    # Výber karty — follower
    # ------------------------------------------------------------------

    def _decide_as_follower(self, hand: list[Card], playable: list[Card],
                            trick: Trick) -> Card:
        current_best = self._get_current_best_card(trick)

        # S28 — CLAIM_LEAD (len ak aktívna po S27)
        if self.memory.claim_lead_active:
            claim = self._claim_lead(hand, playable, trick)
            if claim:
                return claim

        # S23 — TRACK_BIDDER (sleduj dražiteľa)
        if self.difficulty == "hard":
            track = self._track_bidder(playable, trick)
            if track:
                self._log(SC.TRACK_BIDDER, f"{track}")
                return track

        # S7 — PROTECT_TEN
        if self.difficulty in ("medium", "hard"):
            safe = self._protect_tens(playable, hand, trick)
            if safe:
                self._log(SC.PROTECT_TEN, f"{safe}")
                return safe

        # S9 — SAFE_DISCARD
        card = self._play_safest_card(playable, hand)
        self._log(SC.SAFE_DISCARD, f"{card}")
        return card

    # ------------------------------------------------------------------
    # Pomocné metódy
    # ------------------------------------------------------------------

    def _protect_tens(self, playable: list[Card], hand: list[Card],
                      trick: Trick) -> Card | None:
        lead_suit = trick.lead_suit
        if not lead_suit:
            return None
        ten = next(
            (c for c in hand if c.suit == lead_suit and c.rank == "ten"),
            None
        )
        if not ten:
            return None
        other = [
            c for c in playable
            if c.suit == lead_suit and c.rank != "ten"
        ]
        if other:
            return min(other, key=lambda c: c.rank_order)
        return None

    def _beats_current(self, card: Card, current_best: Card | None,
                       trick: Trick) -> bool:
        if current_best is None:
            return True
        trump = self.memory.current_trump
        if card.suit == trump and current_best.suit != trump:
            return True
        if card.suit == trump and current_best.suit == trump:
            return card.rank_order > current_best.rank_order
        if card.suit == current_best.suit:
            return card.rank_order > current_best.rank_order
        return False

    def _get_current_best_card(self, trick: Trick) -> Card | None:
        if not trick.played_cards:
            return None
        winner_idx = trick.get_winner_index()
        for idx, card in trick.played_cards:
            if idx == winner_idx:
                return card
        return None

    def _check_passive_bid(self, hand: list[Card], current_bid: int) -> bool:
        """
        S27 — Pasuj ak mám 2+ esá + kryté tromfy.
        Dostanem sa na štych bez záväzku.
        """
        ace_count = sum(1 for c in hand if c.rank == "ace")
        trump_points = self.evaluator.get_playable_trump_points(hand)

        # 2+ esá + aspoň jedna hláška
        if ace_count >= 2 and trump_points >= 40:
            return True

        # 3+ esá — dostanem sa na štych vždy
        if ace_count >= 3:
            return True

        return False

    def _play_safest_card(self, playable: list[Card],
                           hand: list[Card]) -> Card:
        # Vylúč nekryté desiatky
        protected_tens = self.evaluator.get_protected_tens(hand)
        unprotected_tens = [
            c for c in playable
            if c.rank == "ten"
            and not protected_tens.get(c.suit, False)
        ]
        safe = [c for c in playable if c not in unprotected_tens]
        if not safe:
            return min(playable, key=lambda c: (c.points, c.rank_order))

        singletons = self.evaluator.get_singleton_cards(hand)
        singleton_playable = [
            c for c in safe
            if c in singletons and c.points == 0
        ]
        if singleton_playable:
            return singleton_playable[0]

        return min(safe, key=lambda c: (c.points, c.rank_order))

    def _track_bidder(self, playable: list[Card],
                      trick: Trick) -> Card | None:
        """
        S23 — Sleduj dražiteľa.
        Ak štich berie dražiteľ → prebi ho aj lacnejším štychom.
        Ak štich neberie dražiteľ → nemusíme prebíjať.
        """
        # Nájdi dražiteľa
        bidder_index = None
        for i, player in enumerate(
                [p for p in self.memory.trick_winners.values()]
        ):
            pass

        # Získaj index dražiteľa z memory — potrebujeme ho pridať
        # Zatiaľ použijeme jednoduchšiu logiku:
        # Ak aktuálny víťaz štichu nie je ten istý hráč ako my →
        # skús prebiť

        current_best = self._get_current_best_card(trick)
        if not current_best:
            return None

        current_winner = trick.get_winner_index()

        # Môžeme prebiť?
        can_beat = [
            c for c in playable
            if self._beats_current(c, current_best, trick)
        ]
        if not can_beat:
            return None

        # Prebi ak štich berie niekto iný (nie my)
        # a štich má aspoň nejaké body
        if trick.total_points >= 2:
            return min(can_beat, key=lambda c: c.rank_order)

        return None

    def _claim_lead(self, hand: list[Card], playable: list[Card],
                    trick: Trick) -> Card | None:
        """
        S28 — CLAIM_LEAD
        Aktivuje sa len po S27. Cieľ: dostať sa na lead čo najrýchlejšie.
        """
        if not self.memory.claim_lead_active:
            return None

        played_count = len(trick.played_cards)

        # Som 2. v poradí — potrebujem istý štych
        if played_count == 1:
            lead_suit = trick.lead_suit
            same_suit = [c for c in playable if c.suit == lead_suit]

            if not same_suit:
                return None

            # Hľadaj kartu ktorá je 100% istá (najvyššia nezahraná)
            for card in sorted(same_suit, key=lambda c: c.rank_order, reverse=True):
                if self.memory.is_highest_in_suit(card, hand):
                    self._log(SC.CLAIM_LEAD,
                              f"{card} → istý štych (2. v poradí)")
                    return card

            # Nemám istú → nič nerobím
            return None

        # Som 3. v poradí — stačí prebiť čímkoľvek
        if played_count == 2:
            current_best = self._get_current_best_card(trick)
            can_beat = [
                c for c in playable
                if self._beats_current(c, current_best, trick)
            ]
            if can_beat:
                card = min(can_beat, key=lambda c: c.rank_order)
                self._log(SC.CLAIM_LEAD,
                          f"{card} → prebijem (3. v poradí)")
                return card

        return None

    def __repr__(self) -> str:
        return f"AIStrategy(difficulty={self.difficulty})"