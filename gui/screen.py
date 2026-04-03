# gui/screen.py

import pygame
from game.card import Card
from game.game_state import GameState
from game.ai import AI
from gui.card_renderer import CardRenderer
from gui.scoreboard import Scoreboard
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, DEBUG_MODE,
    COLOR_BG, COLOR_BG_DARK, COLOR_YELLOW, COLOR_GRAY,
    COLOR_WHITE, COLOR_BLACK, COLOR_PANEL_BG, COLOR_GOLD,
    COLOR_GREEN,
    FONT_SIZE_MEDIUM, FONT_SIZE_LARGE, FONT_SIZE_SMALL,
    TABLE_CENTER_X, TABLE_CENTER_Y,
    BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_RADIUS,
    NUM_PLAYERS
)


class Screen:
    def __init__(self, game_state: GameState, ai_players: list[AI], debug: bool = DEBUG_MODE):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tisíc")
        try:
            self.table_bg = pygame.image.load("assets/graphics/table.jpg").convert()
            self.table_bg = pygame.transform.scale(self.table_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except FileNotFoundError:
            self.table_bg = None

        self.clock = pygame.time.Clock()
        self.debug = debug

        self.game_state = game_state
        self.ai_players = ai_players

        self.card_renderer = CardRenderer(self.screen, debug)
        self.scoreboard = Scoreboard(self.screen)

        self.font_small = pygame.font.SysFont(None, FONT_SIZE_SMALL)
        self.font_medium = pygame.font.SysFont(None, FONT_SIZE_MEDIUM)
        self.font_large = pygame.font.SysFont(None, FONT_SIZE_LARGE)

        self.selected_card = None
        self.selected_discards = []
        self.message = ""
        self.message_timer = 0

        # Tromf
        self.pending_trump_card: Card | None = None
        self.pending_trump_suit: str | None = None

        # Navýšenie dražby po talóne
        self.can_raise_bid: bool = False

        self.trick_display_timer: int = 0  # kedy zmiznú karty zo stola
        self.trick_waiting: bool = False  # čakáme na zobrazenie štichu

        self.running = True

    # ------------------------------------------------------------------
    # Hlavná slučka
    # ------------------------------------------------------------------

    def run(self):
        """Hlavná herná slučka."""
        self.game_state.start_new_round()
        self.game_state.current_round.start_bidding()

        while self.running:
            self.clock.tick(FPS)
            self._handle_events()
            self._process_waiting_trick()  # ← pridané
            self._handle_ai_turn()
            self._draw()
            pygame.display.flip()

        pygame.quit()

    # ------------------------------------------------------------------
    # Spracovanie udalostí
    # ------------------------------------------------------------------

    def _handle_events(self):
        """Spracuje pygame udalosti."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    self.debug = not self.debug
                    self.card_renderer.debug = self.debug

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._handle_click(event.pos)

    def _handle_click(self, pos: tuple[int, int]):
        """Spracuje klik myši podľa aktuálnej fázy hry."""
        if not self.game_state.is_human_turn:
            return

        # Ak čakáme na rozhodnutie o tromfe
        if self.pending_trump_card is not None:
            self._handle_trump_decision_click(pos)
            return

        phase = self.game_state.current_round.phase

        if phase == "bidding":
            self._handle_bidding_click(pos)
        elif phase == "talon":
            self._handle_talon_click(pos)
        elif phase == "tricks":
            self._handle_tricks_click(pos)

    # ------------------------------------------------------------------
    # Klikanie v jednotlivých fázach
    # ------------------------------------------------------------------

    def _handle_bidding_click(self, pos: tuple[int, int]):
        """Spracuje klik počas dražby."""
        current_round = self.game_state.current_round
        player_index = self.game_state.human_index

        if not current_round.bidding.can_bid(player_index):
            return

        if self._button_bid_rect().collidepoint(pos):
            new_bid = current_round.bidding.current_bid + 10
            done = current_round.process_bid(player_index, new_bid)
            if done:
                self._after_bidding()
            return  # ← pridané

        if self._button_pass_rect().collidepoint(pos):
            done = current_round.process_bid(player_index, None)
            if done:
                self._after_bidding()
            return  # ← pridané

    def _handle_talon_click(self, pos: tuple[int, int]):
        """Spracuje klik počas zahadzovania talonu."""
        current_round = self.game_state.current_round
        player_index = self.game_state.human_index

        if current_round.bidding.winner_index != player_index:
            return

        # Tlačidlá VŽDY ako prvé — pred kontrolou kariet
        if self.can_raise_bid and self._button_raise_rect().collidepoint(pos):
            new_bid = current_round.bidding.current_bid + 10
            current_round.bidding.current_bid = new_bid
            self.game_state.players[player_index].bid = new_bid
            self._show_message(f"Záväzok navýšený na {new_bid}")
            return  # ← return zabraňuje ďalšiemu spracovaniu

        if self._button_confirm_rect().collidepoint(pos):
            if len(self.selected_discards) == 2:
                success = current_round.discard_cards(player_index, self.selected_discards)
                if success:
                    self.selected_discards = []
                    self.can_raise_bid = False
                    current_round.start_trick()
            return  # ← return aj keď podmienka nesplnená

        # Klik na kartu — len ak neklikol na tlačidlo
        clicked_card = self.card_renderer.get_clicked_card(
            pos,
            self.game_state.players[player_index].hand.cards,
            player_index
        )

        if clicked_card:
            if clicked_card.rank in ("ace", "ten"):
                self._show_message("Eso a desiatok sa nedajú zahodiť!")
                return
            if clicked_card in self.selected_discards:
                self.selected_discards.remove(clicked_card)
            elif len(self.selected_discards) < 2:
                self.selected_discards.append(clicked_card)

    def _handle_tricks_click(self, pos: tuple[int, int]):
        """Spracuje klik počas štichov."""
        current_round = self.game_state.current_round
        player_index = self.game_state.human_index

        if current_round.get_current_player_index() != player_index:
            return

        playable = self.game_state.players[player_index].hand.get_playable_cards(
            current_round.current_trick.lead_suit,
            current_round.trump_suit,
            current_round.current_trick.played_cards
        )

        clicked_card = self.card_renderer.get_clicked_card(
            pos,
            self.game_state.players[player_index].hand.cards,
            player_index
        )

        if not clicked_card:
            return
        if clicked_card not in playable:
            self._show_message("Túto kartu nemôžeš zahrať!")
            return
        if self._try_declare_trump(player_index, clicked_card):
            return

        success = current_round.play_card(player_index, clicked_card)
        if success:
            self.selected_card = None
            # Ak je štich kompletný — počkáme kým sa nakreslí
            if current_round.current_trick.is_complete:
                self.trick_waiting = True
                self.trick_display_timer = pygame.time.get_ticks() + 1500

    # ------------------------------------------------------------------
    # Tromf
    # ------------------------------------------------------------------

    def _try_declare_trump(self, player_index: int, card: Card) -> bool:
        """
        Skontroluje či karta môže spustiť tromf.
        Vráti True ak čakáme na rozhodnutie hráča.
        """
        current_round = self.game_state.current_round

        if current_round.trick_number == 0:
            return False
        if current_round.get_current_player_index() != player_index:
            return False
        if current_round.current_leader_index != player_index:  # ← pridané
            return False
        if card.rank not in ("over", "king"):
            return False
        if not self.game_state.players[player_index].hand.has_trump_pair(card.suit):
            return False

        self.pending_trump_card = card
        self.pending_trump_suit = card.suit
        return True

    def _handle_trump_decision_click(self, pos: tuple[int, int]):
        """Spracuje rozhodnutie hráča či chce hlásiť tromf."""
        current_round = self.game_state.current_round
        player_index = self.game_state.human_index

        if self._button_trump_yes_rect().collidepoint(pos):
            current_round.declare_trump(player_index, self.pending_trump_suit)
            self._show_message(f"Tromf: {self.pending_trump_suit}!")
            current_round.play_card(player_index, self.pending_trump_card)
            self.pending_trump_card = None
            self.pending_trump_suit = None
            if current_round.current_trick.is_complete:
                self.trick_waiting = True
                self.trick_display_timer = pygame.time.get_ticks() + 1500

        elif self._button_trump_no_rect().collidepoint(pos):
            current_round.play_card(player_index, self.pending_trump_card)
            self.pending_trump_card = None
            self.pending_trump_suit = None
            if current_round.current_trick.is_complete:
                self.trick_waiting = True
                self.trick_display_timer = pygame.time.get_ticks() + 1500

    # ------------------------------------------------------------------
    # Koniec štichu
    # ------------------------------------------------------------------

    def _check_trick_done(self):
        """Skontroluje či je štich hotový a spracuje výsledok."""
        current_round = self.game_state.current_round
        if current_round.current_trick and current_round.current_trick.is_complete:
            # Štich je kompletný — počkáme kým hráč uvidí karty
            self.trick_waiting = True
            self.trick_display_timer = pygame.time.get_ticks() + 1500  # 1.5 sekundy
            winner_index = current_round.finish_trick()
            winner_name = self.game_state.players[winner_index].name
            self._show_message(f"{winner_name} vyhral štich!")

            if current_round.phase == "scoring":
                self.game_state.finish_round()
                if self.game_state.phase == "game_over":
                    self._show_message(f"{self.game_state.winner.name} vyhral hru!")
                else:
                    self.game_state.start_new_round()
                    self.game_state.current_round.start_bidding()
            else:
                current_round.start_trick()

    def _process_waiting_trick(self):
        """Spracuje štich po uplynutí zobrazovacieho času."""
        if not self.trick_waiting:
            return
        if pygame.time.get_ticks() < self.trick_display_timer:
            return

        current_round = self.game_state.current_round
        if not current_round:
            self.trick_waiting = False
            return
        if not current_round.current_trick:
            self.trick_waiting = False
            return
        if not current_round.current_trick.is_complete:
            self.trick_waiting = False
            return

        self.trick_waiting = False
        winner_index = current_round.finish_trick()
        winner_name = self.game_state.players[winner_index].name
        self._show_message(f"{winner_name} vyhral štich!")

        if current_round.phase == "scoring":
            self.game_state.finish_round()
            if self.game_state.phase == "game_over":
                self._show_message(f"{self.game_state.winner.name} vyhral hru!", 5000)
            else:
                self.game_state.start_new_round()
                self.game_state.current_round.start_bidding()
        else:
            current_round.start_trick()

    # ------------------------------------------------------------------
    # AI ťahy
    # ------------------------------------------------------------------

    def _handle_ai_turn(self):
        """Spracuje ťah AI hráča ak je na rade."""
        if self.game_state.current_round is None:
            return
        if self.trick_waiting:  # ← pridané
            return
        current_round = self.game_state.current_round
        phase = current_round.phase

        if phase == "bidding":
            bidding = current_round.bidding
            if bidding.bidding_over:
                return

            for _ in range(len(self.game_state.players)):
                if bidding.bidding_over:
                    self._after_bidding()
                    return

                current_index = self._get_next_bidder_index()
                if current_index is None:
                    self._after_bidding()
                    return

                player = self.game_state.players[current_index]
                if player.is_human:
                    return

                pygame.time.delay(500)
                ai = self.ai_players[current_index]
                amount = ai.decide_bid(bidding.current_bid)
                done = current_round.process_bid(current_index, amount)
                if done:
                    self._after_bidding()
                    return
            return

        if self.game_state.is_human_turn:
            return

        current_index = current_round.get_current_player_index()
        ai = self.ai_players[current_index]

        pygame.time.delay(500)

        if phase == "talon":
            winner_index = self.game_state.current_round.bidding.winner_index
            if self.game_state.players[winner_index].is_human:
                return
            ai = self.ai_players[winner_index]
            pygame.time.delay(500)
            self._ai_discard(winner_index, ai)
        elif phase == "tricks":
            self._ai_play_card(current_index, ai)

    def _get_next_bidder_index(self) -> int | None:
        """Vráti index hráča ktorý je aktuálne na rade v dražbe."""
        bidding = self.game_state.current_round.bidding
        num = len(self.game_state.players)
        last_bidder = bidding.highest_bidder_index

        for i in range(1, num + 1):
            idx = (last_bidder + i) % num
            if bidding.active[idx]:
                return idx
        return None

    def _ai_bid(self, player_index: int, ai: AI):
        """AI rozhodne v dražbe."""
        current_round = self.game_state.current_round
        if not current_round.bidding.can_bid(player_index):
            return
        amount = ai.decide_bid(current_round.bidding.current_bid)
        done = current_round.process_bid(player_index, amount)
        if done:
            self._after_bidding()

    def _ai_discard(self, player_index: int, ai: AI):
        """AI zahodí 2 karty."""
        current_round = self.game_state.current_round
        if current_round.bidding.winner_index != player_index:
            return
        cards = ai.decide_discard(self.game_state.players[player_index].hand.cards)
        current_round.discard_cards(player_index, cards)
        current_round.start_trick()

    def _ai_play_card(self, player_index: int, ai: AI):
        """AI zahrá kartu."""
        current_round = self.game_state.current_round
        player = self.game_state.players[player_index]
        playable = player.hand.get_playable_cards(
            current_round.current_trick.lead_suit,
            current_round.trump_suit,
            current_round.current_trick.played_cards
        )

        if current_round.trick_number > 0 and \
                current_round.get_current_player_index() == player_index:
            trump_suit = ai.decide_trump(
                current_round.trick_number,
                current_round.current_leader_index,
                player_index
            )
            if trump_suit:
                current_round.declare_trump(player_index, trump_suit)

        card = ai.decide_card(playable, current_round.current_trick, current_round.trick_number)
        current_round.play_card(player_index, card)

        # Nekontrolujeme štich tu — hlavná slučka to spracuje cez _process_waiting_trick()
        # Najprv sa karta nakreslí, až potom sa štich uzavrie
        if current_round.current_trick.is_complete:
            self.trick_waiting = True
            self.trick_display_timer = pygame.time.get_ticks() + 1500

    # ------------------------------------------------------------------
    # Po dražbe
    # ------------------------------------------------------------------

    def _after_bidding(self):
        """Spracuje situáciu po skončení dražby."""
        current_round = self.game_state.current_round
        winner = current_round.bidding.winner
        self._show_message(f"{winner.name} vydražil za {winner.bid}")
        current_round.give_talon_to_winner()

        if winner.is_human:
            self.can_raise_bid = True

    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def _draw(self):
        """Nakreslí celú obrazovku."""
        self._draw_table()  # ← musí byť prvé (prekryje všetko)
        self._draw_hands()
        self._draw_current_trick()
        self._draw_talon()
        self._draw_info_panel()
        self.scoreboard.draw(
            self.game_state.players,
            self.game_state.current_round
        )
        self._draw_buttons()
        self._draw_message()

    def _draw_table(self):
        """Nakreslí herný stôl."""
        if self.table_bg:
            self.screen.blit(self.table_bg, (0, 0))
        else:
            # Fallback ak obrázok chýba
            self.screen.fill(COLOR_BG)
            pygame.draw.ellipse(
                self.screen, COLOR_BG_DARK,
                (TABLE_CENTER_X - 400, TABLE_CENTER_Y - 250, 800, 500)
            )

    def _draw_hands(self):
        """Nakreslí karty všetkých hráčov."""
        current_round = self.game_state.current_round
        trump_suit = current_round.trump_suit if current_round else None

        for i, player in enumerate(self.game_state.players):
            is_current = (
                current_round and
                current_round.get_current_player_index() == i
            )
            self.card_renderer.draw_hand(
                player.hand.cards,
                player_index=i,
                is_human=player.is_human,
                selected_cards=self.selected_discards if current_round and current_round.phase == "talon" else [],
                highlight_playable=is_current and player.is_human,
                trump_suit=trump_suit,
                lead_suit=current_round.current_trick.lead_suit if current_round and current_round.current_trick else None,
                played_cards=current_round.current_trick.played_cards if current_round and current_round.current_trick else []

            )

    def _draw_current_trick(self):
        """Nakreslí karty aktuálneho štichu."""
        current_round = self.game_state.current_round
        if current_round and current_round.current_trick:
            self.card_renderer.draw_trick(current_round.current_trick)

    def _draw_talon(self):
        """Nakreslí talon."""
        current_round = self.game_state.current_round
        if current_round and current_round.phase == "bidding":
            self.card_renderer.draw_talon(len(current_round.talon))

    def _draw_info_panel(self):
        """Nakreslí info panel."""
        current_round = self.game_state.current_round
        if not current_round:
            return

        from config import INFO_PANEL_X, INFO_PANEL_Y, INFO_PANEL_WIDTH, INFO_PANEL_HEIGHT
        pygame.draw.rect(
            self.screen, COLOR_PANEL_BG,
            (INFO_PANEL_X, INFO_PANEL_Y, INFO_PANEL_WIDTH, INFO_PANEL_HEIGHT),
            border_radius=10
        )

        lines = []
        if current_round.bidding:
            winner = current_round.bidding.winner
            lines.append(f"Dražba: {current_round.bidding.current_bid}")
            lines.append(f"Dražiteľ: {winner.name}")
        if current_round.trump_suit:
            lines.append(f"Tromf: {current_round.trump_suit}")
        lines.append(f"Štich: {current_round.trick_number + 1}/10")

        for j, line in enumerate(lines):
            surf = self.font_medium.render(line, True, COLOR_WHITE)
            self.screen.blit(surf, (INFO_PANEL_X + 10, INFO_PANEL_Y + 10 + j * 30))

    def _draw_buttons(self):
        """Nakreslí akčné tlačidlá podľa fázy hry."""
        if not self.game_state.is_human_turn:
            return

        # Tlačidlá pre rozhodnutie o tromfe
        if self.pending_trump_card is not None:
            trump_labels = {
                "heart": "Srdce",
                "bell": "Zvon",
                "leaf": "Zeleň",
                "acorn": "Žaluď"
            }
            label = trump_labels.get(self.pending_trump_suit, self.pending_trump_suit)
            self._draw_button(
                self._button_trump_yes_rect(),
                f"Tromf: {label}",
                COLOR_GOLD
            )
            self._draw_button(
                self._button_trump_no_rect(),
                "Bez tromfu",
                COLOR_GRAY
            )
            return

        phase = self.game_state.current_round.phase if self.game_state.current_round else None

        if phase == "bidding":
            self._draw_button(self._button_bid_rect(), "Pridať +10", COLOR_GOLD)
            self._draw_button(self._button_pass_rect(), "Pasovať", COLOR_GRAY)
        elif phase == "talon":
            if self.can_raise_bid:
                current_bid = self.game_state.current_round.bidding.current_bid
                self._draw_button(
                    self._button_raise_rect(),
                    f"Navýšiť ({current_bid + 10})",
                    COLOR_GREEN
                )
            if len(self.selected_discards) == 2:
                self._draw_button(self._button_confirm_rect(), "Potvrdiť", COLOR_GOLD)

    def _draw_button(self, rect: pygame.Rect, text: str, color: tuple):
        """Nakreslí jedno tlačidlo."""
        pygame.draw.rect(self.screen, color, rect, border_radius=BUTTON_RADIUS)
        surf = self.font_medium.render(text, True, COLOR_BLACK)
        text_rect = surf.get_rect(center=rect.center)
        self.screen.blit(surf, text_rect)

    def _draw_message(self):
        """Zobrazí správu pre hráča."""
        if self.message and pygame.time.get_ticks() < self.message_timer:
            surf = self.font_large.render(self.message, True, COLOR_YELLOW)
            rect = surf.get_rect(center=(TABLE_CENTER_X, TABLE_CENTER_Y - 150))
            self.screen.blit(surf, rect)

    # ------------------------------------------------------------------
    # Rects — tlačidlá
    # ------------------------------------------------------------------

    def _button_bid_rect(self) -> pygame.Rect:
        return pygame.Rect(TABLE_CENTER_X - 180, 980, BUTTON_WIDTH, BUTTON_HEIGHT)

    def _button_pass_rect(self) -> pygame.Rect:
        return pygame.Rect(TABLE_CENTER_X + 20, 980, BUTTON_WIDTH, BUTTON_HEIGHT)

    def _button_raise_rect(self) -> pygame.Rect:
        return pygame.Rect(TABLE_CENTER_X - 180, 980, BUTTON_WIDTH, BUTTON_HEIGHT)

    def _button_confirm_rect(self) -> pygame.Rect:
        return pygame.Rect(TABLE_CENTER_X + 20, 980, BUTTON_WIDTH, BUTTON_HEIGHT)

    def _button_trump_yes_rect(self) -> pygame.Rect:
        return pygame.Rect(TABLE_CENTER_X - 180, 980, BUTTON_WIDTH, BUTTON_HEIGHT)

    def _button_trump_no_rect(self) -> pygame.Rect:
        return pygame.Rect(TABLE_CENTER_X + 20, 980, BUTTON_WIDTH, BUTTON_HEIGHT)

    # ------------------------------------------------------------------
    # Pomocné metódy
    # ------------------------------------------------------------------

    def _show_message(self, text: str, duration_ms: int = 2000):
        """Zobrazí správu na obrazovke."""
        self.message = text
        self.message_timer = pygame.time.get_ticks() + duration_ms

    def __repr__(self) -> str:
        return f"Screen({SCREEN_WIDTH}x{SCREEN_HEIGHT}, debug={self.debug})"