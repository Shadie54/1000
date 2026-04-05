# game/ai_memory.py

from game.card import Card
from config import SUITS, RANKS


class AIMemory:
    def __init__(self, player_index: int, num_players: int = 3):
        """
        player_index: index hráča ktorého pamäť sledujeme
        """
        self.player_index = player_index
        self.num_players = num_players

        # Všetky karty ktoré už padli (zahraté v štichoch)
        self.played_cards: set[Card] = set()

        # Karty ktoré videl tento hráč (vlastná ruka + zahraté)
        self.seen_cards: set[Card] = set()

        # Pre každého hráča — farby ktoré nemá (priznal inak)
        # {player_index: set of suits}
        self.void_suits: dict[int, set] = {
            i: set() for i in range(num_players)
        }

        # Kto vyhral ktorý štich {trick_number: player_index}
        self.trick_winners: dict[int, int] = {}

        # Zahlásené tromfy {suit: player_index}
        self.declared_trumps: dict[str, int] = {}

        # Aktuálna tromfová farba
        self.current_trump: str | None = None

        # História štichov [(leader, [(player_index, card)])]
        self.trick_history: list[tuple[int, list]] = []

        #Set bidder
        self.bidder_index: int | None = None
        self.bid_amount: int = 0
    # ------------------------------------------------------------------
    # Aktualizácia pamäte
    # ------------------------------------------------------------------

    def record_trick(self, trick_leader: int, played_cards: list[tuple[int, Card]],
                     winner_index: int, trick_number: int):
        """
        Zaznamená odohraný štich.
        played_cards: [(player_index, card), ...]
        """
        lead_suit = played_cards[0][1].suit

        for player_idx, card in played_cards:
            self.played_cards.add(card)
            self.seen_cards.add(card)

            # Ak hráč nehral lead_suit a nezahral tromf — nemá lead_suit
            if player_idx != trick_leader:
                if card.suit != lead_suit:
                    if card.suit != self.current_trump:
                        self.void_suits[player_idx].add(lead_suit)
                    # Ak zahral inú farbu ako tromf — nemá ani lead_suit
                    else:
                        self.void_suits[player_idx].add(lead_suit)

        self.trick_winners[trick_number] = winner_index
        self.trick_history.append((trick_leader, played_cards))

    def record_trump_declaration(self, suit: str, player_index: int):
        """Zaznamená zahlásený tromf."""
        self.declared_trumps[suit] = player_index
        self.current_trump = suit

    def record_own_hand(self, cards: list[Card]):
        """Zaznamená vlastné karty (videné na začiatku)."""
        for card in cards:
            self.seen_cards.add(card)

    def record_talon(self, cards: list[Card]):
        """Zaznamená karty talonu (ak ich hráč videl)."""
        for card in cards:
            self.seen_cards.add(card)

    # ------------------------------------------------------------------
    # Dotazy na stav hry
    # ------------------------------------------------------------------

    def is_played(self, card: Card) -> bool:
        """Skontroluje či karta už padla."""
        return card in self.played_cards

    def is_card_alive(self, card: Card) -> bool:
        """Skontroluje či karta ešte môže byť v hre."""
        return card not in self.played_cards and card not in self.seen_cards

    def get_played_in_suit(self, suit: str) -> list[Card]:
        """Vráti všetky zahraté karty danej farby."""
        return [c for c in self.played_cards if c.suit == suit]

    def get_unplayed_in_suit(self, suit: str) -> list[Card]:
        """Vráti všetky nezahraté karty danej farby (okrem vlastných)."""
        all_in_suit = [Card(suit, rank) for rank in RANKS]
        return [c for c in all_in_suit if c not in self.played_cards]

    def get_higher_unplayed(self, card: Card) -> list[Card]:
        """Vráti nezahraté karty vyššie ako daná karta tej istej farby."""
        all_in_suit = [Card(card.suit, rank) for rank in RANKS]
        return [
            c for c in all_in_suit
            if c.rank_order > card.rank_order
            and c not in self.played_cards
        ]

    def get_lower_unplayed(self, card: Card) -> list[Card]:
        """Vráti nezahraté karty nižšie ako daná karta tej istej farby."""
        all_in_suit = [Card(card.suit, rank) for rank in RANKS]
        return [
            c for c in all_in_suit
            if c.rank_order < card.rank_order
            and c not in self.played_cards
        ]

    def is_highest_in_suit(self, card: Card, own_cards: list[Card]) -> bool:
        """
        Skontroluje či je karta najvyššia zo zvyšných kariet danej farby.
        Berie do úvahy vlastné karty (tie nie sú u súperov).
        """
        higher = self.get_higher_unplayed(card)
        # Odstráň vlastné karty — tie nie sú hrozbou
        higher_opponents = [c for c in higher if c not in own_cards]
        return len(higher_opponents) == 0

    def is_suit_void(self, player_index: int, suit: str) -> bool:
        """Skontroluje či hráč nemá danú farbu."""
        return suit in self.void_suits[player_index]

    def count_unplayed_in_suit(self, suit: str, exclude_cards: list[Card] = None) -> int:
        """Počet nezahratých kariet danej farby (okrem zadaných)."""
        exclude = set(exclude_cards or [])
        all_in_suit = [Card(suit, rank) for rank in RANKS]
        return sum(
            1 for c in all_in_suit
            if c not in self.played_cards and c not in exclude
        )

    # ------------------------------------------------------------------
    # Forcing pravdepodobnosť
    # ------------------------------------------------------------------

    def calculate_forcing_probability(self, forcing_card: Card,
                                      protected_card: Card,
                                      own_cards: list[Card]) -> float:
        """
        Vypočíta pravdepodobnosť úspechu forcingu.
        forcing_card: karta ktorou forcujeme
        protected_card: karta ktorú chránime
        own_cards: naše vlastné karty

        Vracia hodnotu 0.0 - 1.0
        """
        if forcing_card.suit != protected_card.suit:
            return 0.0
        if forcing_card.rank_order <= protected_card.rank_order:
            return 0.0

        # Karty vyššie ako forcing_card ktoré ešte nepadli
        higher_unplayed = self.get_higher_unplayed(forcing_card)
        higher_opponents = [c for c in higher_unplayed if c not in own_cards]

        # Všetky nezahraté karty tejto farby okrem našich
        total_unplayed = self.count_unplayed_in_suit(
            forcing_card.suit, exclude_cards=own_cards
        )

        if total_unplayed == 0:
            return 1.0

        # Pravdepodobnosť že niekto má vyššiu kartu
        p_has_higher = len(higher_opponents) / total_unplayed

        # Pravdepodobnosť úspechu forcingu
        return 1.0 - p_has_higher

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self):
        """Resetuje pamäť pre nové kolo."""
        self.played_cards = set()
        self.seen_cards = set()
        self.void_suits = {i: set() for i in range(self.num_players)}
        self.trick_winners = {}
        self.declared_trumps = {}
        self.current_trump = None
        self.trick_history = []

    # ------------------------------------------------------------------
    # Sleduj biddera
    # ------------------------------------------------------------------
    def set_bidder(self, player_index: int, bid: int):
        """Zaznamená dražiteľa a jeho záväzok."""
        self.bidder_index = player_index
        self.bid_amount = bid

    def __repr__(self) -> str:
        return (f"AIMemory(played={len(self.played_cards)}, "
                f"trump={self.current_trump})")