# game/ai_evaluator.py

from game.card import Card
from game.ai_memory import AIMemory
from config import SUITS, RANKS, TRUMP_POINTS, CARD_POINTS


class AIEvaluator:
    def __init__(self, memory: AIMemory):
        self.memory = memory

    # ------------------------------------------------------------------
    # Hodnotenie sily ruky
    # ------------------------------------------------------------------

    def estimate_hand_strength(self, hand: list[Card],
                                trump_suit: str | None) -> dict:
        """
        Kompletné hodnotenie sily ruky.
        Vracia slovník s detailným odhadom.
        """
        guaranteed = self.get_guaranteed_tricks(hand, trump_suit)
        probable = self.get_probable_tricks(hand, trump_suit, guaranteed)
        trump_points = self.get_playable_trump_points(hand)
        protected_tens = self.get_protected_tens(hand)
        singletons = self.get_singleton_cards(hand)
        long_suits = self.get_long_suits(hand)

        guaranteed_points = sum(c.points for c in guaranteed)
        probable_points = sum(c.points for c in probable) * 0.6

        estimated_total = (
            guaranteed_points +
            probable_points +
            trump_points
        )

        return {
            "guaranteed_cards": guaranteed,
            "guaranteed_points": guaranteed_points,
            "probable_cards": probable,
            "probable_points": probable_points,
            "trump_points": trump_points,
            "estimated_total": estimated_total,
            "protected_tens": protected_tens,
            "singletons": singletons,
            "long_suits": long_suits,
        }

    # ------------------------------------------------------------------
    # Istý štych
    # ------------------------------------------------------------------

    def get_guaranteed_tricks(self, hand: list[Card],
                               trump_suit: str | None) -> list[Card]:
        """
        Vráti karty ktoré sú istý štych.
        Karta je istý štych ak:
        - Je najvyššia nezahraná v danej farbe (žiadna vyššia u súperov)
        - Alebo je tromfová a je najvyššia nezahraná tromfová
        """
        guaranteed = []
        for card in hand:
            if self.memory.is_highest_in_suit(card, hand):
                guaranteed.append(card)
        return guaranteed

    # ------------------------------------------------------------------
    # Pravdepodobný štych
    # ------------------------------------------------------------------

    def get_probable_tricks(self, hand: list[Card],
                            trump_suit: str | None,
                            guaranteed: list[Card]) -> list[Card]:
        """
        Vráti karty ktoré sú pravdepodobný štych (nie istý ale vysoká šanca).
        Nikdy nevracia desiatky — tie nie sú pravdepodobný štych ak eso nepadlo.
        """
        probable = []
        guaranteed_set = set(id(c) for c in guaranteed)

        for card in hand:
            if id(card) in guaranteed_set:
                continue

            # Desiatka nikdy nie je pravdepodobný štych ako leader
            # (eso je vždy vyššie)
            if card.rank == "ten":
                continue

            higher = self.memory.get_higher_unplayed(card)
            higher_opponents = [c for c in higher if c not in hand]

            if len(higher_opponents) == 0:
                continue

            total_unplayed = self.memory.count_unplayed_in_suit(
                card.suit, exclude_cards=hand
            )

            if total_unplayed == 0:
                probable.append(card)
                continue

            p_wins = 1.0 - (len(higher_opponents) / total_unplayed)

            if p_wins >= 0.65:
                probable.append(card)

        return probable

    # ------------------------------------------------------------------
    # Tromfy
    # ------------------------------------------------------------------

    def get_playable_trump_points(self, hand: list[Card]) -> int:
        """
        Vráti body za tromfy ktoré môže hráč zahlásil.
        Počíta len páry (over + king) v ruke.
        """
        total = 0
        for suit in SUITS:
            has_over = any(c.suit == suit and c.rank == "over" for c in hand)
            has_king = any(c.suit == suit and c.rank == "king" for c in hand)
            if has_over and has_king:
                total += TRUMP_POINTS[suit]
        return total

    def get_best_trump_suit(self, hand: list[Card]) -> str | None:
        """
        Vráti farbu najlepšieho tromfu.
        Preferuje tromf s najvyššou hodnotou + krytosťou esom.
        """
        best_suit = None
        best_score = -1

        for suit in SUITS:
            has_over = any(c.suit == suit and c.rank == "over" for c in hand)
            has_king = any(c.suit == suit and c.rank == "king" for c in hand)
            if not (has_over and has_king):
                continue

            score = TRUMP_POINTS[suit]

            # Bonus ak má eso tej farby — tromf je krytý
            has_ace = any(c.suit == suit and c.rank == "ace" for c in hand)
            if has_ace:
                score += 20

            # Bonus za dlhú farbu
            suit_count = sum(1 for c in hand if c.suit == suit)
            score += suit_count * 5

            if score > best_score:
                best_score = score
                best_suit = suit

        return best_suit

    # ------------------------------------------------------------------
    # Ochrana desiatok
    # ------------------------------------------------------------------

    def get_protected_tens(self, hand: list[Card]) -> dict[str, bool]:
        """
        Vráti slovník či je desiatok každej farby chránený.
        Chránený = má k desiatke aspoň jednu inú kartu tej farby.
        """
        result = {}
        for suit in SUITS:
            has_ten = any(c.suit == suit and c.rank == "ten" for c in hand)
            if not has_ten:
                continue
            other_cards = [
                c for c in hand
                if c.suit == suit and c.rank != "ten"
            ]
            result[suit] = len(other_cards) > 0
        return result

    def get_forcing_opportunities(self, hand: list[Card],
                                  trump_suit: str | None) -> list[dict]:
        from game.card import Card as CardClass
        opportunities = []

        for suit in SUITS:
            ten = next(
                (c for c in hand if c.suit == suit and c.rank == "ten"), None
            )
            if not ten:
                continue

            # Išlo už eso? → forcing nepotrebný
            ace_card = CardClass(suit, "ace")
            if self.memory.is_played(ace_card):
                continue

            # Má eso v ruke? → 10 krytá esom → forcing nepotrebný
            if any(c.suit == suit and c.rank == "ace" for c in hand):
                continue

            # Všetky karty tej farby okrem desiatky
            same_suit = [
                c for c in hand
                if c.suit == suit and c.rank != "ten"
            ]
            if not same_suit:
                continue

            # Počet záložných kariet — čím viac, tým bezpečnejší forcing
            backup_count = len(same_suit)

            # Vyber NAJVYŠŠIU kartu ako forcing kartu
            # (vyššia = vyššia pravdepodobnosť vylákania esa)
            # Záložné karty ostanú na krytie 10
            best_forcing = max(same_suit, key=lambda c: c.rank_order)

            prob = self.memory.calculate_forcing_probability(
                best_forcing, ten, hand
            )

            # Bonus za počet záložných kariet
            # Každá záloha navyše zvyšuje bezpečnosť forcingu
            safety_bonus = (backup_count - 1) * 0.15
            adjusted_prob = min(prob + safety_bonus, 1.0)

            if adjusted_prob >= 0.3:
                opportunities.append({
                    "forcing_card": best_forcing,
                    "protected_card": ten,
                    "probability": adjusted_prob,
                    "base_probability": prob,
                    "backup_count": backup_count,
                    "suit": suit
                })

        opportunities.sort(key=lambda x: x["probability"], reverse=True)
        return opportunities

    # ------------------------------------------------------------------
    # Plonkové karty
    # ------------------------------------------------------------------

    def get_singleton_cards(self, hand: list[Card]) -> list[Card]:
        """
        Vráti karty ktoré sú jediné svojej farby (plonkové).
        Tieto karty sú rizikové — súper ich môže uchmatnúť.
        """
        singletons = []
        for suit in SUITS:
            suit_cards = [c for c in hand if c.suit == suit]
            if len(suit_cards) == 1:
                singletons.append(suit_cards[0])
        return singletons

    # ------------------------------------------------------------------
    # Dlhá farba
    # ------------------------------------------------------------------

    def get_long_suits(self, hand: list[Card]) -> dict[str, list[Card]]:
        """
        Vráti farby kde má hráč 3 a viac kariet.
        Dlhá farba = potenciálna dominancia v tej farbe.
        """
        long_suits = {}
        for suit in SUITS:
            suit_cards = [c for c in hand if c.suit == suit]
            if len(suit_cards) >= 3:
                long_suits[suit] = suit_cards
        return long_suits

    # ------------------------------------------------------------------
    # Bidding odhad
    # ------------------------------------------------------------------

    def calculate_bid_estimate(self, hand: list[Card],
                               trump_suit: str | None) -> int:
        strength = self.estimate_hand_strength(hand, trump_suit)
        estimated = strength["estimated_total"]

        # S16 — bonus za dlhú farbu
        long_suit_bonus = self.get_long_suit_bid_bonus(hand)
        estimated += long_suit_bonus

        for suit in SUITS:
            has_over = any(c.suit == suit and c.rank == "over" for c in hand)
            has_king = any(c.suit == suit and c.rank == "king" for c in hand)
            if has_over and has_king:
                trump_val = TRUMP_POINTS[suit]
                estimated = max(estimated, trump_val + 20)

        rounded = int(estimated // 10) * 10
        return max(50, rounded)

    def get_long_suit_bid_bonus(self, hand: list[Card]) -> int:
        """
        S16 — Bonus za dlhú farbu pri biddingu.
        4 karty + eso + 10 → +30
        5 kariet + eso → +25
        6 kariet + eso → +30
        7 kariet → +45
        """
        bonus = 0
        for suit in SUITS:
            suit_cards = [c for c in hand if c.suit == suit]
            count = len(suit_cards)
            if count < 4:
                continue

            has_ace = any(c.rank == "ace" for c in suit_cards)
            has_ten = any(c.rank == "ten" for c in suit_cards)

            if count == 4 and has_ace and has_ten:
                bonus += 30
            elif count == 5 and has_ace:
                bonus += 25
            elif count == 6 and has_ace:
                bonus += 30
            elif count >= 7:
                bonus += 45

        return bonus

    def should_pass_for_trumps(self, hand: list[Card],
                                current_bid: int) -> bool:
        """
        Rozhodne či je výhodnejšie pasovať a čakať na tromfy.
        Stratégia: ak mám silné hlášky ale slabé štichy,
        radšej pasnem a zahlásim tromf neskôr.
        """
        trump_points = self.get_playable_trump_points(hand)
        guaranteed = self.get_guaranteed_tricks(hand, None)
        guaranteed_points = sum(c.points for c in guaranteed)

        # Ak mám silné tromfy ale málo istých štichov
        # → lepšie pasovať
        if trump_points >= 80 and guaranteed_points < 30:
            return True

        # Ak odhadovaný bid je výrazne nižší ako aktuálny bid
        estimate = self.calculate_bid_estimate(hand, None)
        if estimate < current_bid - 10:
            return True

        return False

    def should_raise_after_talon(self, hand: list[Card],
                                 current_bid: int,
                                 trump_suit: str | None) -> int | None:
        """
        Rozhodne či navýšiť bid po zobratí talonu.
        Bez limitu navýšenia — zohľadní celú silu ruky.
        """
        # Istý štych body
        guaranteed = self.get_guaranteed_tricks(hand, trump_suit)
        guaranteed_points = sum(c.points for c in guaranteed)

        # 100% zahlásiteľné hlášky
        guaranteed_trump_points = 0
        for suit in SUITS:
            has_over = any(c.suit == suit and c.rank == "over" for c in hand)
            has_king = any(c.suit == suit and c.rank == "king" for c in hand)
            if has_over and has_king:
                guaranteed_trump_points += TRUMP_POINTS[suit]

        # Pravdepodobné štichy
        probable = self.get_probable_tricks(hand, trump_suit, guaranteed)
        probable_points = sum(c.points for c in probable) * 0.6

        # Celkový odhad
        total_estimate = (
                guaranteed_points +
                guaranteed_trump_points +
                probable_points
        )

        # Zaokrúhli na desiatky nadol (konzervatívne)
        total_rounded = int(total_estimate // 10) * 10
        total_rounded = max(50, total_rounded)

        if total_rounded >= current_bid + 10:
            return total_rounded  # ← bez limitu

        return None

    # ------------------------------------------------------------------
    # Zahadzovaie do talonu
    # ------------------------------------------------------------------

    def get_discard_candidates(self, hand: list[Card]) -> list[Card]:
        """
        Vráti karty zoradené podľa priority zahodenia.
        Najvyššia priorita zahodenia = index 0.
        Nikdy neodporúča zahodiť eso alebo desiatku.
        """
        candidates = [
            c for c in hand
            if c.rank not in ("ace", "ten")
        ]

        def discard_priority(card: Card) -> float:
            score = 0.0

            # Základná bodová hodnota — nižšie body = vyššia priorita zahodenia
            score -= card.points

            # Plonková karta bez hodnoty = dobrý kandidát na zahodenie
            suit_cards = [c for c in hand if c.suit == card.suit]
            if len(suit_cards) == 1:
                score += 10  # vyššia priorita zahodenia

            # Súčasť hlášky = nechceme zahodiť
            has_over = any(
                c.suit == card.suit and c.rank == "over" for c in hand
            )
            has_king = any(
                c.suit == card.suit and c.rank == "king" for c in hand
            )
            if has_over and has_king:
                score -= 50  # veľmi nízka priorita zahodenia

            # Karta chráni desiatku = nechceme zahodiť
            has_ten = any(
                c.suit == card.suit and c.rank == "ten" for c in hand
            )
            if has_ten and card.rank not in ("over", "king"):
                score -= 20

            return score

        candidates.sort(key=discard_priority, reverse=True)
        return candidates

    def __repr__(self) -> str:
        return "AIEvaluator()"