# game/game_state.py

from game.player import Player
from game.round import Round
from config import NUM_PLAYERS, WINNING_SCORE
from game.game_logger import GameLogger

class GameState:
    def __init__(self, player_names: list[str], human_index: int = 0):
        """
        player_names: mená hráčov v poradí ako sú na scoresheete
        human_index: index ľudského hráča (zvyčajne 0)
        """
        self.players: list[Player] = [
            Player(name, is_human=(i == human_index), index=i)
            for i, name in enumerate(player_names)
        ]
        self.human_index = human_index
        self.obligation_index: int = 0      # index hráča s povinnosťou
        self.round_number: int = 0          # číslo aktuálneho kola
        self.current_round: Round | None = None
        self.round_history: list[dict] = [] # história kôl pre scoresheet
        self.phase: str = "setup"           # fázy: setup > playing > game_over
        self.logger = GameLogger()

    # ------------------------------------------------------------------
    # Správa kôl
    # ------------------------------------------------------------------

    def start_new_round(self):
        """Začne nové kolo."""
        for player in self.players:
            player.reset_round()

        self.current_round = Round(self.players, self.obligation_index)
        self.current_round.deal()
        self.round_number += 1
        self.phase = "playing"

    def finish_round(self):
        """
        Uzavrie aktuálne kolo:
        - Zapíše výsledky do histórie
        - Posunie povinnosť
        - Skontroluje či niekto vyhral hru
        """
        self.current_round.score_round()
        self._record_round_history()
        self._advance_obligation()

        if self._check_winner():
            self.phase = "game_over"

    def _record_round_history(self):
        """Zaznamená výsledky kola do histórie."""
        round_data = {
            "round_number": self.round_number,
            "obligation": self.players[self.obligation_index].name,
            "bidder": self.current_round.bidding.winner.name,
            "bid": self.current_round.bidding.current_bid,
            "trump_suit": self.current_round.trump_suit,
            "scores": {
                player.name: player.total_score
                for player in self.players
            },
            "round_points": {
                player.name: player.round_points
                for player in self.players
            },
            "bid_fulfilled": (
                self.current_round.bidding.winner.round_points >=
                self.current_round.bidding.current_bid
            )
        }
        self.round_history.append(round_data)

    def _advance_obligation(self):
        """Posunie povinnosť na ďalšieho hráča v poradí."""
        self.obligation_index = (self.obligation_index + 1) % NUM_PLAYERS

    def _check_winner(self) -> bool:
        """Skontroluje či niekto dosiahol 1000 bodov."""
        return any(player.total_score >= WINNING_SCORE for player in self.players)

    # ------------------------------------------------------------------
    # Pomocné metódy
    # ------------------------------------------------------------------

    @property
    def winner(self) -> Player | None:
        """Vráti víťaza hry alebo None ak hra ešte neskončila."""
        for player in self.players:
            if player.total_score >= WINNING_SCORE:
                return player
        return None

    @property
    def current_player(self) -> Player | None:
        """Vráti hráča ktorý je aktuálne na ťahu."""
        if self.current_round is None:
            return None
        idx = self.current_round.get_current_player_index()
        return self.players[idx]

    @property
    def is_human_turn(self) -> bool:
        """Skontroluje či je na ťahu ľudský hráč."""
        if self.current_round is None:
            return False
        phase = self.current_round.phase
        if phase == "talon":
            # Pri talóne záleží kto vyhral dražbu
            winner_index = self.current_round.bidding.winner_index
            return self.players[winner_index].is_human
        return self.current_player == self.players[self.human_index]

    def get_scores(self) -> dict[str, int]:
        """Vráti aktuálne skóre všetkých hráčov."""
        return {player.name: player.total_score for player in self.players}

    def get_last_round_summary(self) -> dict | None:
        """Vráti súhrn posledného kola."""
        if self.round_history:
            return self.round_history[-1]
        return None

    def __repr__(self) -> str:
        scores = ", ".join(f"{p.name}={p.total_score}" for p in self.players)
        return (f"GameState(round={self.round_number}, "
                f"phase={self.phase}, "
                f"scores=[{scores}])")