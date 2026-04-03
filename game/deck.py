# game/deck.py

import random
from game.card import Card
from config import SUITS, RANKS, TALON_SIZE


class Deck:
    def __init__(self):
        self.cards: list[Card] = []
        self._build()

    def _build(self):
        """Vytvorí kompletný balíček 32 kariet."""
        self.cards = [Card(suit, rank) for suit in SUITS for rank in RANKS]

    def shuffle(self):
        """Zamieša balíček."""
        random.shuffle(self.cards)

    def deal(self, num_players: int, talon_size: int = TALON_SIZE) -> tuple[list[list[Card]], list[Card]]:
        """
        Rozdá karty hráčom a vyčlení talon.
        Vráti (zoznamy kariet pre každého hráča, talon).
        """
        self.shuffle()

        total_cards = len(self.cards)           # 32
        play_cards = total_cards - talon_size   # 30
        cards_per_player = play_cards // num_players  # 10

        hands = []
        for i in range(num_players):
            start = i * cards_per_player
            end = start + cards_per_player
            hands.append(self.cards[start:end])

        talon = self.cards[play_cards:]         # posledné 2 karty

        return hands, talon

    def reset(self):
        """Resetuje balíček do pôvodného stavu (nová hra)."""
        self._build()

    def __repr__(self) -> str:
        return f"Deck({len(self.cards)} cards)"