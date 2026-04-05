# game/ai.py

from game.player import Player
from game.card import Card
from game.trick import Trick
from game.ai_memory import AIMemory
from game.ai_evaluator import AIEvaluator
from game.ai_strategy import AIStrategy
from config import NUM_PLAYERS


class AI:
    def __init__(self, player: Player, difficulty: str = "hard", logger=None):
        """
        player: hráč ktorého táto AI ovláda
        difficulty: "easy" / "medium" / "hard"
        """
        self.player = player
        self.difficulty = difficulty
        self.logger = logger

        self.memory = AIMemory(player.index, NUM_PLAYERS)
        self.evaluator = AIEvaluator(self.memory)
        self.strategy = AIStrategy(
            self.memory, self.evaluator,
            difficulty, logger, player.name
        )

    # ------------------------------------------------------------------
    # Dražba
    # ------------------------------------------------------------------

    def decide_bid(self, current_bid: int) -> int | None:
        """
        Rozhodne či AI pridá do dražby alebo pasuje.
        Vracia sumu ak dráži, None ak pasuje.
        """
        hand = self.player.hand.cards
        trump_suit = self.memory.current_trump

        return self.strategy.decide_bid(
            hand, current_bid,
            self.player.has_obligation,
            trump_suit
        )

    # ------------------------------------------------------------------
    # Talon
    # ------------------------------------------------------------------

    def decide_discard(self, hand_cards: list[Card]) -> list[Card]:
        """
        Rozhodne ktoré 2 karty zahodí po zobratí talonu.
        """
        return self.strategy.decide_discard(hand_cards)

    def decide_raise_after_talon(self, current_bid: int) -> int | None:
        """
        Rozhodne či navýšiť bid po zobratí talonu.
        Vracia nový bid alebo None.
        """
        hand = self.player.hand.cards
        trump_suit = self.memory.current_trump
        return self.strategy.decide_raise_after_talon(
            hand, current_bid, trump_suit
        )

    # ------------------------------------------------------------------
    # Tromfy
    # ------------------------------------------------------------------

    def decide_trump(self, trick_number: int, leader_index: int,
                     player_index: int) -> str | None:
        """
        Rozhodne či AI zahlási tromf a v akej farbe.
        """
        hand = self.player.hand.cards
        is_leader = (leader_index == player_index)

        return self.strategy.decide_trump(
            hand, trick_number, is_leader,
            self.memory.current_trump
        )

    # ------------------------------------------------------------------
    # Výber karty
    # ------------------------------------------------------------------

    def decide_card(self, playable: list[Card],
                    current_trick: Trick,
                    trick_number: int) -> Card:
        """
        Vyberie kartu na zahranie zo zoznamu platných kariet.
        """
        hand = self.player.hand.cards
        return self.strategy.decide_card(
            hand, playable, current_trick,
            trick_number, self.player.index
        )

    # ------------------------------------------------------------------
    # Aktualizácia pamäte
    # ------------------------------------------------------------------

    def record_trick(self, trick_leader: int,
                     played_cards: list[tuple[int, Card]],
                     winner_index: int, trick_number: int):
        """Zaznamená odohraný štich do pamäte."""
        self.memory.record_trick(
            trick_leader, played_cards,
            winner_index, trick_number
        )

    def record_trump_declaration(self, suit: str, player_index: int):
        """Zaznamená zahlásený tromf."""
        self.memory.record_trump_declaration(suit, player_index)

    def record_own_hand(self, cards: list[Card]):
        """Zaznamená vlastné karty na začiatku kola."""
        self.memory.record_own_hand(cards)

    def record_talon(self, cards: list[Card]):
        """Zaznamená karty talonu (ak ich AI videla)."""
        self.memory.record_talon(cards)

    def reset_memory(self):
        """Resetuje pamäť pre nové kolo."""
        self.memory.reset()

    def __repr__(self) -> str:
        return f"AI({self.player.name}, difficulty={self.difficulty})"