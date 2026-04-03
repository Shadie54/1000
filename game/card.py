# game/card.py

from config import CARD_POINTS, TRUMP_POINTS, RANKS, SUITS


class Card:
    def __init__(self, suit: str, rank: str):
        self.suit = suit    # "heart", "bell", "leaf", "acorn"
        self.rank = rank    # "seven", "eight", ..., "king", "ace"

    @property
    def points(self) -> int:
        """Bodová hodnota karty."""
        return CARD_POINTS[self.rank]

    @property
    def trump_points(self) -> int:
        """Body za zahlásenie tromfu (over + king tejto farby). 0 ak táto karta nie je súčasťou tromfu."""
        if self.rank in ("over", "king"):
            return TRUMP_POINTS[self.suit]
        return 0

    @property
    def rank_order(self) -> int:
        """Poradie karty pre porovnávanie v štichu (vyššie = silnejšia)."""
        return RANKS.index(self.rank)

    @property
    def image_name(self) -> str:
        """Názov PNG súboru pre túto kartu."""
        return f"{self.suit}-{self.rank}.png"

    def __repr__(self) -> str:
        return f"Card({self.suit}, {self.rank})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        return hash((self.suit, self.rank))