# game/player.py

from game.hand import Hand
from game.card import Card


class Player:
    def __init__(self, name: str, is_human: bool = False, index: int = 0):
        self.name = name
        self.is_human = is_human
        self.index = index
        self.hand = Hand()

        # Skóre a štatistiky
        self.total_score: int = 0           # celkové skóre cez všetky hry
        self.tricks_points: int = 0         # body zo štichov v aktuálnom kole
        self.declared_trumps_points: int = 0  # body za zahlásené tromfy v aktuálnom kole

        # Dražba
        self.bid: int = 0                   # aktuálna ponuka v dražbe
        self.is_bidder: bool = False        # vyhral dražbu?
        self.has_obligation: bool = False   # má povinnosť?

        # Tromfy
        self.declared_trumps: list[str] = []  # farby zahlásených tromfov v kole

    def receive_cards(self, cards: list[Card]):
        """Dostane karty na ruku (po rozdaní)."""
        self.hand.add_cards(cards)

    def play_card(self, card: Card) -> Card:
        """Zahrá kartu z ruky."""
        self.hand.remove_card(card)
        return card

    def declare_trump(self, suit: str) -> int:
        """
        Zahlási tromf v danej farbe.
        Vráti body za tromf.
        """
        points = 0
        for card in self.hand.cards:
            if card.suit == suit and card.rank in ("over", "king"):
                points = card.trump_points
                break
        self.declared_trumps.append(suit)
        self.declared_trumps_points += points
        return points

    def add_trick_points(self, points: int):
        """Pripočíta body zo získaného štichu."""
        self.tricks_points += points

    @property
    def round_points(self) -> int:
        """Celkové body v aktuálnom kole (štichy + tromfy)."""
        return self.tricks_points + self.declared_trumps_points

    def finalize_round(self, bidder_fulfilled: bool):
        """
        Uzavrie kolo a pripočíta body k celkovému skóre.
        - Ak je hráč dražiteľ: pripočíta alebo odpočíta záväzok podľa výsledku
        - Ostatní hráči: vždy dostanú svoje body
        """
        if self.is_bidder:
            if bidder_fulfilled:
                self.total_score += self.bid
            else:
                self.total_score -= self.bid
        else:
            self.total_score += self._rounded_points(self.round_points)

    def _rounded_points(self, points: int) -> int:
        """Zaokrúhli body podľa pravidiel (od 5 nahor)."""
        remainder = points % 10
        if remainder >= 5:
            return points + (10 - remainder)
        else:
            return points - remainder

    def reset_round(self):
        """Resetuje stav hráča pre nové kolo."""
        self.hand = Hand()
        self.bid = 0
        self.is_bidder = False
        self.has_obligation = False
        self.tricks_points = 0
        self.declared_trumps_points = 0
        self.declared_trumps = []

    def __repr__(self) -> str:
        return f"Player({self.name}, score={self.total_score})"