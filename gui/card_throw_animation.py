# gui/card_throw_animation.py
#
# Prevzaté z hry CHUJ: karta pri zahratí letí z ruky hráča na svoje
# miesto na stole (gui/layout.py::trick_positions).

from gui import layout


class CardThrowAnimation:
    """
    Veľmi rýchla animácia — karta letí z ruky hráča (odkiaľ bola
    zahraná) na svoje miesto na stole.

    Na rozdiel od TrickAnimation (ktorá zbiera už kompletný štich
    k víťazovi na konci) toto rieši samotné zahratie JEDNEJ karty —
    aby sa karta neobjavila na stole okamžite, bez prechodu.
    """

    BASE_SPEED = 100.0   # logické px za snímku pri rýchlosti 1.0×

    def __init__(self, canvas, card_renderer, speed_mult: float = 1.0):
        self.canvas = canvas
        self.card_renderer = card_renderer
        self.in_flight: dict[int, dict] = {}  # player_index -> karta v lete
        self.card_speed: float = self.BASE_SPEED * speed_mult
        self.targets = dict(layout.game().trick_positions)

    def start(self, player_index: int, card, start_pos: tuple[int, int]):
        """Spustí let karty zo start_pos (stred karty v ruke) na stôl."""
        target_x, target_y = self.targets[player_index]
        sx, sy = start_pos
        self.in_flight[player_index] = {
            "card": card,
            "x": float(sx),
            "y": float(sy),
            "target_x": float(target_x),
            "target_y": float(target_y),
            "settled": False,
        }

    def update(self):
        """Aktualizuje pozície letiacich kariet."""
        if not self.in_flight:
            return

        arrived = []
        for player_index, c in self.in_flight.items():
            dx = c["target_x"] - c["x"]
            dy = c["target_y"] - c["y"]
            dist = (dx ** 2 + dy ** 2) ** 0.5

            if dist <= self.card_speed:
                # Posledný krok — dorovnaj PRESNE na cieľ (rovnaká pozícia,
                # akú potom kreslí draw_trick), nech nie je viditeľný skok.
                # Doletená karta sa ešte 1 snímku kreslí cez animáciu
                # (settled), až potom ju prevezme draw_trick.
                if c["settled"]:
                    arrived.append(player_index)
                else:
                    c["x"] = c["target_x"]
                    c["y"] = c["target_y"]
                    c["settled"] = True
            else:
                c["x"] += dx / dist * self.card_speed
                c["y"] += dy / dist * self.card_speed

        for player_index in arrived:
            del self.in_flight[player_index]

    def draw(self):
        """Nakreslí karty v lete."""
        for c in self.in_flight.values():
            img = self.card_renderer._get_card_image(c["card"])
            rect = img.get_rect(center=(int(c["x"]), int(c["y"])))
            self.canvas.blit(img, rect)

    def __repr__(self) -> str:
        return f"CardThrowAnimation(in_flight={len(self.in_flight)})"
