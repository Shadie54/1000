# game/bidding.py

from config import MIN_BID, BID_STEP, MAX_BID


class Bidding:
    def __init__(self, players: list, obligation_index: int):
        """
        players: zoznam všetkých hráčov
        obligation_index: index hráča s povinnosťou
        """
        self.players = players
        self.obligation_index = obligation_index
        self.current_bid: int = MIN_BID         # aktuálna najvyššia ponuka (začína na 50)
        self.highest_bidder_index: int = obligation_index  # aktuálny víťaz dražby
        self.active: list[bool] = [True] * len(players)   # kto ešte dráži

        # Hráč s povinnosťou automaticky "dáva" 50
        self.players[obligation_index].bid = MIN_BID
        self.players[obligation_index].has_obligation = True

    def can_bid(self, player_index: int) -> bool:
        """Skontroluje či hráč môže ešte dražiť."""
        return self.active[player_index]

    def place_bid(self, player_index: int, amount: int) -> bool:
        """
        Hráč ponúkne sumu.
        Vráti True ak je ponuka platná, False ak nie.
        """
        if not self.can_bid(player_index):
            return False
        if amount != self.current_bid + BID_STEP:
            return False
        if amount % BID_STEP != 0:
            return False
        if amount > MAX_BID:  # ← pridané
            return False

        self.current_bid = amount
        self.highest_bidder_index = player_index
        self.players[player_index].bid = amount
        return True

    def pass_bid(self, player_index: int):
        """Hráč pasuje — vypadne z dražby."""
        self.active[player_index] = False

    @property
    def bidding_over(self) -> bool:
        """
        Dražba je skončená ak:
        - Zostal len jeden aktívny hráč (víťaz)
        - ALEBO pasovali všetci okrem hráča s povinnosťou
        """
        active_count = sum(self.active)
        if active_count == 1:
            return True
        # Ak sú aktívni len hráč s povinnosťou — dražba skončila
        if active_count == 0:
            return True
        return False

    @property
    def winner_index(self) -> int:
        """Vráti index víťaza dražby."""
        return self.highest_bidder_index

    @property
    def winner(self):
        """Vráti hráča ktorý vyhral dražbu."""
        return self.players[self.highest_bidder_index]

    def get_next_bidder(self, current_index: int) -> int | None:
        """
        Vráti index nasledujúceho aktívneho hráča v poradí.
        Vráti None ak je dražba skončená.
        """
        if self.bidding_over:
            return None

        num_players = len(self.players)
        for i in range(1, num_players + 1):
            next_index = (current_index + i) % num_players
            if self.active[next_index]:
                return next_index
        return None

    def finalize(self):
        """Označí víťaza dražby."""
        winner = self.winner
        winner.is_bidder = True
        winner.bid = self.current_bid

    def __repr__(self) -> str:
        return (f"Bidding(current_bid={self.current_bid}, "
                f"winner={self.players[self.highest_bidder_index].name}, "
                f"active={self.active})")