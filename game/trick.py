# game/trick.py

from game.card import Card
from game.player import Player


class Trick:
    def __init__(self, players: list[Player], leader_index: int, trump_suit: str | None):
        """
        players: zoznam všetkých hráčov
        leader_index: index hráča ktorý začína štich
        trump_suit: aktuálna tromfová farba (alebo None ak nie je zahlásená)
        """
        self.players = players
        self.leader_index = leader_index
        self.trump_suit = trump_suit
        self.played_cards: list[tuple[int, Card]] = []  # (player_index, card)

    @property
    def lead_suit(self) -> str | None:
        """Farba prvej zahranej karty v štichu."""
        if self.played_cards:
            return self.played_cards[0][1].suit
        return None

    @property
    def is_complete(self) -> bool:
        """Štich je kompletný ak zahrali všetci hráči."""
        return len(self.played_cards) == len(self.players)

    def play_card(self, player_index: int, card: Card):
        """Zaznamená zahratú kartu hráča."""
        self.played_cards.append((player_index, card))

    def get_winner_index(self) -> int:
        """
        Určí víťaza štichu podľa pravidiel:
        - Tromfová farba bije všetky ostatné farby
        - V rámci tej istej farby vyhráva vyššia karta
        - Karty inej farby ako lead_suit a nie tromf nemôžu vyhrať
        """
        best_player_index = self.played_cards[0][0]
        best_card = self.played_cards[0][1]

        for player_index, card in self.played_cards[1:]:
            if self._beats(card, best_card):
                best_card = card
                best_player_index = player_index

        return best_player_index

    def _beats(self, challenger: Card, current_best: Card) -> bool:
        """
        Skontroluje či challenger porazí current_best.
        """
        # Challenger je tromf, current_best nie je tromf
        if challenger.suit == self.trump_suit and current_best.suit != self.trump_suit:
            return True

        # Obaja sú tromfy — vyhráva vyšší
        if challenger.suit == self.trump_suit and current_best.suit == self.trump_suit:
            return challenger.rank_order > current_best.rank_order

        # Challenger je rovnaká farba ako lead — porovnáme
        if challenger.suit == self.lead_suit and current_best.suit == self.lead_suit:
            return challenger.rank_order > current_best.rank_order

        # Challenger nie je ani tromf ani lead farba — nemôže vyhrať
        return False

    @property
    def total_points(self) -> int:
        """Celkové body kariet v štichu."""
        return sum(card.points for _, card in self.played_cards)

    def get_played_card(self, player_index: int) -> Card | None:
        """Vráti kartu ktorú zahral daný hráč v tomto štichu."""
        for idx, card in self.played_cards:
            if idx == player_index:
                return card
        return None

    def __repr__(self) -> str:
        cards_str = ", ".join(
            f"{self.players[i].name}: {card}" for i, card in self.played_cards
        )
        return f"Trick(trump={self.trump_suit}, cards=[{cards_str}])"