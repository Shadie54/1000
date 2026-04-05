# game/game_logger.py

import os
from datetime import datetime
from game.card import Card


class GameLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.entries: list[str] = []
        self.round_number = 0

        os.makedirs(log_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def new_round(self, round_number: int, obligation: str,
                  hands: dict[str, list[Card]], talon: list[Card]):
        """Zaznamená začiatok kola."""
        self.round_number = round_number
        self.entries.append(f"\n{'='*60}")
        self.entries.append(f"KOLO {round_number}")
        self.entries.append(f"{'='*60}")
        self.entries.append(f"Povinnosť: {obligation}")
        self.entries.append(f"Talon: {self._cards_str(talon)}")
        self.entries.append("")
        for name, cards in hands.items():
            self.entries.append(f"Ruka [{name}]: {self._cards_str(cards)}")
        self.entries.append("")

    def log_bid(self, player: str, amount: int | None):
        """Zaznamená dražbu."""
        if amount is None:
            self.entries.append(f"  Dražba [{player}]: PAS")
        else:
            self.entries.append(f"  Dražba [{player}]: {amount}")

    def log_bid_winner(self, player: str, amount: int):
        """Zaznamená víťaza dražby."""
        self.entries.append(f"  → Vydražil: {player} za {amount}")
        self.entries.append("")

    def log_talon_received(self, player: str, talon: list[Card]):
        """Zaznamená zobratý talon."""
        self.entries.append(f"  Talon zobral: {player} → {self._cards_str(talon)}")

    def log_discard(self, player: str, cards: list[Card]):
        """Zaznamená zahodené karty."""
        self.entries.append(f"  Zahodil [{player}]: {self._cards_str(cards)}")
        self.entries.append("")

    def log_raise(self, player: str, new_bid: int):
        """Zaznamená navýšenie."""
        self.entries.append(f"  Navýšil [{player}]: {new_bid}")

    def log_trump(self, player: str, suit: str, points: int):
        """Zaznamená tromf."""
        self.entries.append(f"  *** TROMF [{player}]: {suit} (+{points} bodov)")

    def log_trick(self, trick_number: int, played: list[tuple[str, Card]],
                  winner: str, trick_points: int):
        """Zaznamená štich."""
        cards_str = "  |  ".join(
            f"{name}: {self._card_str(card)}"
            for name, card in played
        )
        self.entries.append(
            f"  Štich {trick_number:2d}: {cards_str}"
            f"  → {winner} (+{trick_points})"
        )

    def log_round_result(self, results: dict[str, dict]):
        """
        Zaznamená výsledok kola.
        results: {player_name: {bid, round_points, total_score, fulfilled}}
        """
        self.entries.append("")
        self.entries.append("VÝSLEDOK KOLA:")
        for name, data in results.items():
            if data.get("is_bidder"):
                status = "✓ splnil" if data["fulfilled"] else "✗ nesplnil"
                self.entries.append(
                    f"  {name}: záväzok {data['bid']} → "
                    f"nahral {data['round_points']} → {status} → "
                    f"celkom: {data['total_score']}"
                )
            else:
                self.entries.append(
                    f"  {name}: nahral {data['round_points']} → "
                    f"celkom: {data['total_score']}"
                )

    def log_comment(self, comment: str):
        """Pridá komentár do logu (pre manuálne poznámky)."""
        self.entries.append(f"  # {comment}")

    # ------------------------------------------------------------------
    # Uloženie
    # ------------------------------------------------------------------

    def save(self):
        """Uloží log do súboru."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.log_dir, f"game_{timestamp}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(self.entries))
        print(f"[LOG] Uložený: {filename}")
        return filename

    def save_round(self):
        """Uloží priebežný log po každom kole."""
        filename = os.path.join(self.log_dir, "current_game.txt")
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(self.entries))

    # ------------------------------------------------------------------
    # Pomocné
    # ------------------------------------------------------------------

    def _card_str(self, card: Card) -> str:
        suit_symbols = {
            "heart": "♥", "bell": "●",
            "leaf": "♣", "acorn": "♠"
        }
        rank_symbols = {
            "seven": "7", "eight": "8", "nine": "9",
            "ten": "10", "under": "J", "over": "Q",
            "king": "K", "ace": "A"
        }
        suit = suit_symbols.get(card.suit, card.suit)
        rank = rank_symbols.get(card.rank, card.rank)
        return f"{rank}{suit}"

    def log_strategy(self, player: str, strategy: str, details: str = ""):
        """Zaznamená použitú stratégiu AI."""
        if details:
            self.entries.append(f"  [AI {player}] {strategy}: {details}")
        else:
            self.entries.append(f"  [AI {player}] {strategy}")

    def _cards_str(self, cards: list[Card]) -> str:
        return " ".join(self._card_str(c) for c in cards)

    def __repr__(self) -> str:
        return f"GameLogger(rounds={self.round_number})"