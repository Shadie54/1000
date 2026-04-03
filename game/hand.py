# game/hand.py

from game.card import Card
from config import SUITS


class Hand:
    def __init__(self):
        self.cards: list[Card] = []

    def add_card(self, card: Card):
        """Pridá kartu do ruky."""
        self.cards.append(card)

    def add_cards(self, cards: list[Card]):
        """Pridá viacero kariet do ruky."""
        self.cards.extend(cards)

    def remove_card(self, card: Card):
        """Odstráni kartu z ruky (po zahraní)."""
        self.cards.remove(card)

    def has_suit(self, suit: str) -> bool:
        """Skontroluje či hráč má kartu danej farby."""
        return any(card.suit == suit for card in self.cards)

    def has_trump_pair(self, suit: str) -> bool:
        """Skontroluje či hráč má tromfový pár (over + king) v danej farbe."""
        has_over = any(card.suit == suit and card.rank == "over" for card in self.cards)
        has_king = any(card.suit == suit and card.rank == "king" for card in self.cards)
        return has_over and has_king

    def get_available_trumps(self) -> list[str]:
        """Vráti zoznam farieb v ktorých má hráč tromfový pár."""
        return [suit for suit in SUITS if self.has_trump_pair(suit)]

    def get_cards_of_suit(self, suit: str) -> list[Card]:
        """Vráti všetky karty danej farby."""
        return [card for card in self.cards if card.suit == suit]

    def get_playable_cards(self, lead_suit: str | None, trump_suit: str | None,
                           played_cards: list = None) -> list[Card]:
        """
        Vráti karty ktoré môže hráč zahrať podľa pravidiel.
        played_cards: zoznam (player_index, Card) z aktuálneho štichu
        """
        if lead_suit is None:
            return self.cards.copy()

        # Najvyššia doteraz zahraná karta ktorú treba prebiť
        best_order = self._best_played_order(lead_suit, trump_suit, played_cards or [])

        # Má karty v hranej farbe
        same_suit = self.get_cards_of_suit(lead_suit)
        if same_suit:
            higher = [c for c in same_suit if c.rank_order > best_order] if best_order is not None else []
            return higher if higher else same_suit

        # Nemá hranú farbu — musí hrať tromf ak je nahlásený
        if trump_suit:
            trump_cards = self.get_cards_of_suit(trump_suit)
            if trump_cards:
                # Pri tromfe — prebiť aktuálny tromf ak má vyšší
                best_trump_order = self._best_trump_order(trump_suit, played_cards or [])
                higher_trump = [c for c in trump_cards if
                                c.rank_order > best_trump_order] if best_trump_order is not None else []
                return higher_trump if higher_trump else trump_cards

        return self.cards.copy()

    def _best_played_order(self, lead_suit: str, trump_suit: str | None,
                           played_cards: list) -> int | None:
        """Vráti rank_order najsilnejšej zahranej karty (tromf alebo lead farba)."""
        best = None
        for _, card in played_cards:
            if card.suit == trump_suit and trump_suit is not None:
                if best is None or card.rank_order > best:
                    best = card.rank_order
            elif card.suit == lead_suit and trump_suit is None:
                if best is None or card.rank_order > best:
                    best = card.rank_order
            elif card.suit == lead_suit:
                # Len ak žiadny tromf nebol zahraný
                has_trump = any(c.suit == trump_suit for _, c in played_cards if trump_suit)
                if not has_trump:
                    if best is None or card.rank_order > best:
                        best = card.rank_order
        return best

    def _best_trump_order(self, trump_suit: str, played_cards: list) -> int | None:
        """Vráti rank_order najsilnejšieho zahraného tromfu."""
        best = None
        for _, card in played_cards:
            if card.suit == trump_suit:
                if best is None or card.rank_order > best:
                    best = card.rank_order
        return best

    @property
    def total_points(self) -> int:
        """Celkové body kariet v ruke (pre výpočet na konci hry)."""
        return sum(card.points for card in self.cards)

    @property
    def is_empty(self) -> bool:
        """Skontroluje či je ruka prázdna."""
        return len(self.cards) == 0

    def __len__(self) -> int:
        return len(self.cards)

    def __repr__(self) -> str:
        return f"Hand({[str(c) for c in self.cards]})"