# game/round.py

from game.card import Card
from game.deck import Deck
from game.player import Player
from game.trick import Trick
from game.bidding import Bidding
from config import TALON_SIZE, NUM_PLAYERS, TRUMP_POINTS

# Variant first_trick_trump: v 1. štichu smie víťaz dražby hlásiť len tromf,
# ktorého hodnota + FIRST_TRICK_MARGIN nepresahuje jeho povinnosť.
FIRST_TRICK_MARGIN = 10


def first_trick_min_bid(suit: str) -> int:
    """Najnižšia povinnosť, s ktorou sa smie hlásiť `suit` v 1. štichu."""
    return TRUMP_POINTS[suit] + FIRST_TRICK_MARGIN


class Round:
    def __init__(self, players: list[Player], obligation_index: int,
                 first_trick_trump: bool = False):
        """
        players: zoznam všetkých hráčov
        obligation_index: index hráča s povinnosťou
        first_trick_trump: variant pravidiel (Nastavenia → Hra) — víťaz
            dražby smie hlásiť tromf už v 1. štichu; potom však musí za kolo
            zobrať aspoň jeden štich, inak má povinnosť nesplnenú; povinnosť
            musí byť aspoň hodnota hlášky + 10 (first_trick_min_bid).
        """
        self.first_trick_trump = first_trick_trump
        self.declared_in_first_trick = False   # víťaz dražby hlásil v 1. štichu
        self.players = players
        self.obligation_index = obligation_index
        self.deck = Deck()
        self.talon: list[Card] = []
        self.bidding: Bidding | None = None
        self.tricks: list[Trick] = []
        self.current_trick: Trick | None = None
        self.trump_suit: str | None = None
        self.current_leader_index: int = 0
        self.trick_number: int = 0          # aktuálne číslo štichu (0-9)
        self.phase: str = "dealing"         # fázy: dealing > bidding > talon > tricks > scoring
        self.trump_declarer: str | None = None #slúži na zobrazenie aktuálneho tromfu do scoreboardu
    # ------------------------------------------------------------------
    # FÁZA 1: Rozdávanie
    # ------------------------------------------------------------------

    def deal(self):
        """Rozdá karty hráčom a vyčlení talon."""
        hands, self.talon = self.deck.deal(NUM_PLAYERS, TALON_SIZE)
        for i, player in enumerate(self.players):
            player.receive_cards(hands[i])
        self.phase = "bidding"

    # ------------------------------------------------------------------
    # FÁZA 2: Dražba
    # ------------------------------------------------------------------

    def start_bidding(self):
        """Inicializuje dražbu."""
        self.bidding = Bidding(self.players, self.obligation_index)

    def process_bid(self, player_index: int, amount: int | None) -> bool:
        """
        Spracuje ponuku alebo pas hráča.
        amount=None znamená pas.
        Vráti True ak je dražba po tomto ťahu skončená.
        """
        if amount is None:
            # Hráč s povinnosťou nemôže pasovať ak je jediný aktívny
            if self.bidding.players[player_index].has_obligation:
                active_others = sum(
                    1 for i, active in enumerate(self.bidding.active)
                    if active and i != player_index
                )
                if active_others == 0:
                    # Nikto iný nie je aktívny — povinnosť vyhrala za 50
                    self.bidding.finalize()
                    self.phase = "talon"
                    return True
            self.bidding.pass_bid(player_index)
        else:
            self.bidding.place_bid(player_index, amount)

        if self.bidding.bidding_over:
            self.bidding.finalize()
            self.phase = "talon"
            return True
        return False

    # ------------------------------------------------------------------
    # FÁZA 3: Talon
    # ------------------------------------------------------------------

    def give_talon_to_winner(self):
        """Pridá talon do ruky víťaza dražby."""
        winner = self.bidding.winner
        winner.hand.add_cards(self.talon)
        self.talon = []

    def discard_cards(self, player_index: int, cards: list[Card]) -> bool:
        """
        Víťaz dražby zahodí 2 karty (nie eso ani desiatok).
        Vráti True ak je zahodenie platné.
        """
        if len(cards) != TALON_SIZE:
            return False

        for card in cards:
            if card.rank in ("ace", "ten"):
                return False

        winner = self.players[player_index]
        for card in cards:
            winner.hand.remove_card(card)
            # Zahodeným kartám sa body počítajú víťazovi
            winner.add_trick_points(card.points)

        self.current_leader_index = player_index
        self.phase = "tricks"
        return True

    # ------------------------------------------------------------------
    # FÁZA 4: Štichy
    # ------------------------------------------------------------------

    def start_trick(self):
        """Začne nový štich."""
        self.current_trick = Trick(
            self.players,
            self.current_leader_index,
            self.trump_suit
        )

    def declare_trump(self, player_index: int, suit: str) -> bool:
        """
        Hráč hlási tromf.
        Podmienky: hráč je leader, má over+king v danej farbe, nie prvý
        štich (variant first_trick_trump to dovolí — pozri can_declare_trump).
        Vráti True ak je tromf platný.
        """
        if not self.can_declare_trump(player_index, suit):
            return False
        if self.trick_number == 0:
            self.declared_in_first_trick = True

        self.trump_suit = suit
        self.trump_declarer = self.players[player_index].name  # ← pridané
        points = self.players[player_index].declare_trump(suit)
        # Aktualizujeme tromf aj v aktuálnom štichu
        if self.current_trick:
            self.current_trick.trump_suit = suit
        return True

    def trump_allowed_now(self, player_index: int) -> bool:
        """Smie hráč v tomto štichu hlásiť tromf (bez ohľadu na karty)?
        Len vynášajúci; v 1. štichu len pri variante first_trick_trump
        (vynáša vtedy víťaz dražby)."""
        if player_index != self.current_leader_index:
            return False
        if self.current_trick is not None and self.current_trick.played_cards:
            return False
        if self.trick_number == 0:
            return self.first_trick_trump
        return True

    def can_declare_trump(self, player_index: int, suit: str) -> bool:
        if not (self.trump_allowed_now(player_index)
                and self.players[player_index].hand.has_trump_pair(suit)):
            return False
        if self.trick_number == 0:
            return self.bidding.current_bid >= first_trick_min_bid(suit)
        return True

    def tricks_won_by(self, player_index: int) -> int:
        return sum(1 for t in self.tricks if t.get_winner_index() == player_index)

    def bidder_fulfilled(self) -> bool:
        """Splnil víťaz dražby povinnosť? Body kola ≥ vydražená hodnota;
        pri hlásení v 1. štichu musí navyše zobrať aspoň jeden štich."""
        bidder = self.bidding.winner
        if bidder.round_points < bidder.bid:
            return False
        if self.declared_in_first_trick and self.tricks_won_by(
                self.bidding.winner_index) == 0:
            return False
        return True

    def play_card(self, player_index: int, card: Card) -> bool:
        player = self.players[player_index]
        playable = player.hand.get_playable_cards(
            self.current_trick.lead_suit,
            self.trump_suit,
            self.current_trick.played_cards  # ← pridané
        )

        if card not in playable:
            return False

        player.play_card(card)
        self.current_trick.play_card(player_index, card)
        return True

    def finish_trick(self) -> int:
        """
        Uzavrie štich, určí víťaza, pripočíta body.
        Vráti index víťaza štichu.
        """
        winner_index = self.current_trick.get_winner_index()
        points = self.current_trick.total_points
        self.players[winner_index].add_trick_points(points)

        self.tricks.append(self.current_trick)
        self.current_trick = None
        self.current_leader_index = winner_index
        self.trick_number += 1

        if self.trick_number >= 10:
            self.phase = "scoring"

        return winner_index

    # ------------------------------------------------------------------
    # FÁZA 5: Bodovanie
    # ------------------------------------------------------------------

    def score_round(self):
        """
        Uzavrie kolo a aktualizuje skóre všetkých hráčov.
        """
        bidder_fulfilled = self.bidder_fulfilled()

        for player in self.players:
            player.finalize_round(bidder_fulfilled)

        self.phase = "done"

    # ------------------------------------------------------------------
    # Pomocné metódy
    # ------------------------------------------------------------------

    def get_current_player_index(self) -> int:
        """Vráti index hráča ktorý je aktuálne na ťahu."""
        if self.current_trick is None:
            return self.current_leader_index
        played_count = len(self.current_trick.played_cards)
        return (self.current_leader_index + played_count) % NUM_PLAYERS

    def __repr__(self) -> str:
        return (f"Round(phase={self.phase}, "
                f"trick={self.trick_number}/10, "
                f"trump={self.trump_suit})")