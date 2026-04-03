# game/ai.py

from game.player import Player
from game.hand import Hand
from game.card import Card
from game.trick import Trick
from config import MIN_BID, BID_STEP


class AI:
    def __init__(self, player: Player):
        """
        player: hráč ktorého táto AI ovláda
        """
        self.player = player

    # ------------------------------------------------------------------
    # Dražba
    # ------------------------------------------------------------------

    def decide_bid(self, current_bid: int) -> int | None:
        """
        Rozhodne či AI pridá do dražby alebo pasuje.
        Náhodná AI: vždy pasuje (jednoduchá základná verzia).
        Vráti sumu ak dráži, None ak pasuje.
        """
        # Základná náhodná AI vždy pasuje
        # Neskôr tu pridáme inteligentnú logiku
        return None

    # ------------------------------------------------------------------
    # Talon
    # ------------------------------------------------------------------

    def decide_discard(self, hand_cards: list[Card]) -> list[Card]:
        """
        Rozhodne ktoré 2 karty zahodí po zobratí talonu.
        Pravidlo: nesmie zahodiť eso ani desiatok.
        Náhodná AI: zahodí prvé 2 platné karty.
        """
        discardable = [
            card for card in hand_cards
            if card.rank not in ("ace", "ten")
        ]
        return discardable[:2]

    # ------------------------------------------------------------------
    # Tromfy
    # ------------------------------------------------------------------

    def decide_trump(self, trick_number: int, leader_index: int,
                     player_index: int) -> str | None:
        """
        Rozhodne či AI zahlási tromf a v akej farbe.
        Podmienky sú už overené v Round — tu len rozhodujeme či chceme.
        Náhodná AI: nikdy nehlási tromf.
        Vráti farbu tromfu alebo None.
        """
        # Základná náhodná AI nikdy nehlási tromf
        # Neskôr tu pridáme inteligentnú logiku
        return None

    # ------------------------------------------------------------------
    # Výber karty
    # ------------------------------------------------------------------

    def decide_card(self, playable_cards: list[Card],
                    current_trick: Trick,
                    trick_number: int) -> Card:
        """
        Vyberie kartu na zahranie zo zoznamu platných kariet.
        Náhodná AI: zahrá vždy prvú platnú kartu.
        """
        import random
        return random.choice(playable_cards)

    # ------------------------------------------------------------------
    # Pomocné metódy (pre budúcu inteligentnú AI)
    # ------------------------------------------------------------------

    def _estimate_hand_strength(self) -> int:
        """
        Odhadne silu ruky na základe bodov kariet a možných tromfov.
        Zatiaľ len súčet bodov kariet.
        """
        return self.player.hand.total_points

    def _has_strong_suit(self) -> str | None:
        """
        Nájde farbu v ktorej má AI najviac kariet.
        Použijeme neskôr pri inteligentnej dražbe.
        """
        from config import SUITS
        suit_counts = {suit: 0 for suit in SUITS}
        for card in self.player.hand.cards:
            suit_counts[card.suit] += 1
        best_suit = max(suit_counts, key=suit_counts.get)
        return best_suit if suit_counts[best_suit] >= 3 else None

    def __repr__(self) -> str:
        return f"AI({self.player.name})"