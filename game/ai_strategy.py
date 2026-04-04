# game/ai_strategy.py

from game.card import Card
from game.ai_memory import AIMemory
from game.ai_evaluator import AIEvaluator
from game.trick import Trick
from config import SUITS, TRUMP_POINTS


class AIStrategy:
    def __init__(self, memory: AIMemory, evaluator: AIEvaluator,
                 difficulty: str = "hard"):
        """
        difficulty: "easy" / "medium" / "hard"
        """
        self.memory = memory
        self.evaluator = evaluator
        self.difficulty = difficulty

    # ------------------------------------------------------------------
    # Bidding
    # ------------------------------------------------------------------

    def decide_bid(self, hand: list[Card], current_bid: int,
                   has_obligation: bool, trump_suit: str | None) -> int | None:
        """
        Rozhodne či dražiť alebo pasovať.
        Vracia sumu ak dráži, None ak pasuje.
        """
        if self.difficulty == "easy":
            return None

        # Stredná a ťažká úroveň
        estimate = self.evaluator.calculate_bid_estimate(hand, trump_suit)

        # Ťažká úroveň — pasovanie pre tromfy
        if self.difficulty == "hard":
            if self.evaluator.should_pass_for_trumps(hand, current_bid):
                if not has_obligation:
                    return None

        # Ak odhadujeme viac ako aktuálny bid → dražíme
        if estimate >= current_bid + 10:
            return current_bid + 10

        # Máme povinnosť — musíme zostať (None = nepridávame ale nepadáme)
        if has_obligation:
            return None

        return None

    # ------------------------------------------------------------------
    # Navýšenie po talóne
    # ------------------------------------------------------------------

    def decide_raise_after_talon(self, hand: list[Card],
                                  current_bid: int,
                                  trump_suit: str | None) -> int | None:
        """
        Rozhodne či navýšiť bid po zobratí talonu.
        Vracia nový bid alebo None.
        """
        if self.difficulty == "easy":
            return None

        return self.evaluator.should_raise_after_talon(
            hand, current_bid, trump_suit
        )

    # ------------------------------------------------------------------
    # Zahadzovaie
    # ------------------------------------------------------------------

    def decide_discard(self, hand: list[Card]) -> list[Card]:
        """
        Vyberie 2 karty na zahodenie.
        """
        if self.difficulty == "easy":
            # Ľahká — zahodí prvé 2 platné karty
            candidates = [c for c in hand if c.rank not in ("ace", "ten")]
            return candidates[:2]

        # Stredná a ťažká — inteligentné zahadzovaie
        candidates = self.evaluator.get_discard_candidates(hand)
        return candidates[:2]

    # ------------------------------------------------------------------
    # Tromfy
    # ------------------------------------------------------------------

    def decide_trump(self, hand: list[Card], trick_number: int,
                     is_leader: bool, current_trump: str | None) -> str | None:
        """
        Rozhodne či a aký tromf zahlásiť.
        """
        if self.difficulty == "easy":
            return None

        if not is_leader or trick_number == 0:
            return None

        available = [
            suit for suit in SUITS
            if any(c.suit == suit and c.rank == "over" for c in hand)
            and any(c.suit == suit and c.rank == "king" for c in hand)
        ]

        if not available:
            return None

        if self.difficulty == "medium":
            # Stredná — zahlási vždy ak môže
            return max(available, key=lambda s: TRUMP_POINTS[s])

        # Ťažká — zahlási len ak má krytý tromf alebo istý štych v tej farbe
        best = self._choose_best_trump(hand, available, current_trump)
        return best

    def _choose_best_trump(self, hand: list[Card], available: list[str],
                            current_trump: str | None) -> str | None:
        """
        Vyberie najlepší tromf na zahlásenie.
        Preferuje: vyššia hodnota + krytosť esom + dlhá farba
        """
        best_suit = None
        best_score = -1

        for suit in available:
            score = TRUMP_POINTS[suit]

            # Bonus za eso tej farby
            has_ace = any(c.suit == suit and c.rank == "ace" for c in hand)
            if has_ace:
                score += 20

            # Bonus za dlhú farbu
            suit_count = sum(1 for c in hand if c.suit == suit)
            score += suit_count * 5

            # Bonus ak vieme z pamäte že súperi nemajú tromfovú farbu
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
        """
        Hlavná metóda výberu karty.
        """
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
        """Stratégia výberu karty ak som leader štichu."""
        trump_suit = self.memory.current_trump

        # 1. Forcing príležitosti (ťažká úroveň)
        if self.difficulty == "hard":
            forcing = self.evaluator.get_forcing_opportunities(hand, trump_suit)
            for opp in forcing:
                if (opp["probability"] >= 0.8
                        and opp["forcing_card"] in playable):
                    return opp["forcing_card"]

        # 2. Istý štych — zahraj ho
        guaranteed = self.evaluator.get_guaranteed_tricks(hand, trump_suit)
        guaranteed_playable = [c for c in guaranteed if c in playable]
        if guaranteed_playable:
            # Zahraj istý štych s najvyššími bodmi
            return max(guaranteed_playable, key=lambda c: c.points)

        # 3. Pravdepodobný štych
        if self.difficulty in ("medium", "hard"):
            probable = self.evaluator.get_probable_tricks(
                hand, trump_suit, guaranteed
            )
            probable_playable = [c for c in probable if c in playable]
            if probable_playable:
                return max(probable_playable, key=lambda c: c.points)

        # 4. Zahraj najnižšiu bezpečnú kartu — nezasahuj do bodov
        return self._play_safest_card(playable, hand)

    # ------------------------------------------------------------------
    # Výber karty — follower
    # ------------------------------------------------------------------

    def _decide_as_follower(self, hand: list[Card], playable: list[Card],
                             trick: Trick) -> Card:
        """Stratégia výberu karty ak nie som leader štichu."""
        trump_suit = self.memory.current_trump
        current_winner = trick.get_winner_index()
        current_best = self._get_current_best_card(trick)

        # Zisti či štich berie súper alebo spoluhráč
        # (v Tisíci sú všetci súperi)

        # 1. Ochrana desiatok — ťažká úroveň
        if self.difficulty == "hard":
            safe = self._protect_tens(playable, hand, trick)
            if safe:
                return safe

        # 2. Môžem prebiť?
        can_beat = [c for c in playable if self._beats_current(c, current_best, trick)]

        if can_beat:
            # Prebíjam len ak sa oplatí (štich má body)
            trick_points = trick.total_points
            if trick_points >= 10:
                # Prebij najnižšou kartou ktorá vyhrá
                return min(can_beat, key=lambda c: c.rank_order)
            else:
                # Štich nemá body — prihoď najnižšiu kartu
                return self._play_safest_card(playable, hand)

        # 3. Nemôžem prebiť — prihoď kartu s najvyššími bodmi
        # (ak štich berie súper, aspoň mu prihodíme obrázok)
        if self.difficulty == "hard":
            trick_points = trick.total_points
            if trick_points >= 14:
                # Súper berie veľký štych — prihoď mu obrázok
                high_value = [c for c in playable if c.points >= 3]
                if high_value:
                    return max(high_value, key=lambda c: c.points)

        # 4. Zahraj najnižšiu kartu
        return self._play_safest_card(playable, hand)

    # ------------------------------------------------------------------
    # Pomocné metódy
    # ------------------------------------------------------------------

    def _protect_tens(self, playable: list[Card], hand: list[Card],
                      trick: Trick) -> Card | None:
        """
        Ak mám desiatku v ohrození, zahraj inú kartu tej farby.
        Vracia kartu na zahranie alebo None.
        """
        lead_suit = trick.lead_suit
        if not lead_suit:
            return None

        # Mám desiatku tejto farby?
        ten = next(
            (c for c in hand if c.suit == lead_suit and c.rank == "ten"),
            None
        )
        if not ten:
            return None

        # Mám inú kartu tej farby v hrateľných?
        other = [
            c for c in playable
            if c.suit == lead_suit and c.rank != "ten"
        ]
        if other:
            # Zahraj inú kartu, nie desiatku
            return min(other, key=lambda c: c.rank_order)

        return None

    def _beats_current(self, card: Card, current_best: Card | None,
                       trick: Trick) -> bool:
        """Skontroluje či karta prebije aktuálne najlepšiu kartu štichu."""
        if current_best is None:
            return True

        trump = self.memory.current_trump

        # Tromf bije non-tromf
        if card.suit == trump and current_best.suit != trump:
            return True

        # Obaja tromfy
        if card.suit == trump and current_best.suit == trump:
            return card.rank_order > current_best.rank_order

        # Rovnaká farba
        if card.suit == current_best.suit:
            return card.rank_order > current_best.rank_order

        return False

    def _get_current_best_card(self, trick: Trick) -> Card | None:
        """Vráti aktuálne najlepšiu kartu v štichu."""
        if not trick.played_cards:
            return None
        winner_idx = trick.get_winner_index()
        for idx, card in trick.played_cards:
            if idx == winner_idx:
                return card
        return None

    def _play_safest_card(self, playable: list[Card],
                           hand: list[Card]) -> Card:
        """
        Zahraj najbezpečnejšiu kartu — najnižšia bodová hodnota,
        preferuj plonkové karty na odhodenie.
        """
        # Preferuj plonkové karty (jediná farby) s nízkou hodnotou
        singletons = self.evaluator.get_singleton_cards(hand)
        singleton_playable = [
            c for c in playable
            if c in singletons and c.points == 0
        ]
        if singleton_playable:
            return singleton_playable[0]

        # Inak najnižšia hodnota
        return min(playable, key=lambda c: (c.points, c.rank_order))

    def __repr__(self) -> str:
        return f"AIStrategy(difficulty={self.difficulty})"