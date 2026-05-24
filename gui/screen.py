# gui/screen.py

import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, DEBUG_MODE,
    COLOR_BG, COLOR_BG_DARK, COLOR_YELLOW, COLOR_GRAY,
    COLOR_WHITE, COLOR_GOLD,
    FONT_SIZE_MEDIUM, FONT_SIZE_LARGE, FONT_SIZE_SMALL,
    TABLE_CENTER_X, TABLE_CENTER_Y,
    BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_RADIUS,
    COLOR_BUTTON_PRIMARY, COLOR_BUTTON_SECONDARY,
    TALON_X, TALON_Y, CARD_FAN_OFFSET, TRUMP_POINTS,
    get_font, HUMAN_HAND_Y
)
from game.ai import AI
from game.card import Card
from game.game_state import GameState
from gui.bid_slider import BidSlider
from gui.card_renderer import CardRenderer
from gui.deal_animation import DealAnimation
from gui.info_overlay import InfoOverlay
from gui.scoreboard import Scoreboard
from gui.speech_bubble import SpeechBubble
from gui.trick_animation import TrickAnimation


class Screen:
    def __init__(self, game_state: GameState, ai_players: list[AI],
                 debug: bool = DEBUG_MODE, new_game: bool = True,
                 table_bg: str = "table.jpg"):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tisíc")
        try:
            self.table_bg = pygame.image.load(f"assets/graphics/{table_bg}").convert()
            self.table_bg = pygame.transform.scale(
                self.table_bg, (SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        except FileNotFoundError:
            self.table_bg = None
        self.clock = pygame.time.Clock()
        self.debug = debug

        self.game_state = game_state
        self.ai_players = ai_players

        self.card_renderer = CardRenderer(self.screen, debug)
        self.scoreboard = Scoreboard(self.screen)
        self.font_small = get_font(FONT_SIZE_SMALL)
        self.font_medium = get_font(FONT_SIZE_MEDIUM)
        self.font_large = get_font(FONT_SIZE_LARGE)

        self.selected_card = None
        self.selected_discards = []
        self.message = ""
        self.message_timer = 0

        # Tromf
        self.pending_trump_card: Card | None = None
        self.pending_trump_suit: str | None = None
        self.pending_trump_first_trick = False

        # Ukáž posledný štich
        self.show_last_trick: bool = False

        # Navýšenie dražby po talóne
        self.can_raise_bid: bool = False

        #Krátke zobrazenie celého štichu pred resetom kola
        self.trick_display_timer: int = 0  # kedy zmiznú karty zo stola
        self.trick_waiting: bool = False  # čakáme na zobrazenie štichu
        self.game_over_timer: int = 0    # kedy ukončiť hru po výhre

        #Zobrazenie talonu pre ostatných hráčov po dražbe
        self.talon_reveal_timer: int = 0  # kedy zmiznú karty talonu
        self.talon_revealing: bool = False  # zobrazujeme talon?
        self.talon_reveal_cards: list = []  # karty talonu na zobrazenie

        self.waiting_for_ai: bool = False  # blokuje klikanie počas AI ťahu
        # animácia rozdávania
        self.deal_animation: DealAnimation | None = None
        self.dealing: bool = False
        #animácia vyhratého štichu
        self.trick_animation = TrickAnimation(self.screen, self.card_renderer)
        self._trick_anim_started: bool = False
        #speech bubliny
        self.speech_bubble = SpeechBubble(self.screen)
        #bid slider
        self.bid_slider = BidSlider(self.screen)
        #animácia talonu ku hráčovi
        self.talon_anim_cards: list[dict] = []
        self.talon_animating: bool = False
        self.talon_anim_done: bool = True
        self._talon_anim_started: bool = False
        self.running = True
        self.new_game = new_game

        self.info_overlay = InfoOverlay(self.screen)
    # ------------------------------------------------------------------
    # Hlavná slučka
    # ------------------------------------------------------------------

    def run(self) -> str:
        pygame.event.clear()
        self.running = True

        if self.new_game:
            self._start_round()  # ← len pre novú hru
        else:
            # Pokračujeme — obnov stav bez restartu kola
            self.dealing = False
            self.trick_waiting = False
            self.talon_revealing = False
            self._trick_anim_started = False
            self._talon_anim_started = False

        while self.running:
            self.clock.tick(FPS)

            if self.game_over_timer and pygame.time.get_ticks() >= self.game_over_timer:
                self.running = False
                break

            self._handle_events()

            if self.dealing and self.deal_animation:
                self.deal_animation.update()
                self.deal_animation.draw(self.table_bg)
                self.speech_bubble.draw()
                if self.deal_animation.done:
                    self.dealing = False
                    self.deal_animation = None
                    pygame.event.clear()
                    self._auto_sort()
            else:
                self._process_talon_reveal()
                self._process_waiting_trick()
                self.trick_animation.update()
                self._handle_ai_turn()
                self._draw()

            pygame.display.flip()  # ← správne miesto — vnútri while

        # Mimo while cyklu — tu vrátime výsledok
        if self.game_state.phase == "game_over":
            return "game_over"
        return "menu"

    def _start_round(self):
        """Začne nové kolo a inicializuje AI pamäť."""
        self.game_state.start_new_round()
        self.game_state.current_round.start_bidding()

        # Reset pamäte + zaznamenaj vlastné karty
        for i, ai in enumerate(self.ai_players):
            if ai is not None:
                ai.reset_memory()
                ai.record_own_hand(self.game_state.players[i].hand.cards)

        # Log — AŽ PO rozdaní kariet
        current_round = self.game_state.current_round
        hands = {
            p.name: p.hand.cards
            for p in self.game_state.players
        }
        self.game_state.logger.new_round(
            self.game_state.round_number,
            self.game_state.players[current_round.obligation_index].name,
            hands,
            current_round.talon
        )

        # Log povinnosti — automatické 50
        obligation_player = self.game_state.players[current_round.obligation_index]
        self.game_state.logger.log_bid(obligation_player.name, 50)

        # Spusti animáciu rozdávania

        self.deal_animation = DealAnimation(self.screen, self.card_renderer)
        self.deal_animation.start(current_round.obligation_index)
        self.dealing = True

    # ------------------------------------------------------------------
    # Spracovanie udalostí
    # ------------------------------------------------------------------

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    self.debug = not self.debug
                    self.card_renderer.debug = self.debug
                if event.key == pygame.K_ESCAPE:  # ← pridané
                    self.running = False
            if self.dealing and self.deal_animation:
                self.deal_animation.handle_event(event)
                if self.deal_animation.done:  # ← okamžitá kontrola
                    self.dealing = False
                    self.deal_animation = None
                    pygame.event.clear()
                    self._auto_sort()
                continue

            if self.info_overlay.visible:
                if self.info_overlay.handle_event(event):
                    continue

            # Slider povinnosti
            if self.bid_slider.visible:
                result = self.bid_slider.handle_event(event)
                if result == "confirm":
                    self._confirm_raise_bid()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._handle_click(event.pos)

    def _handle_click(self, pos: tuple[int, int]):
        """Spracuje klik myši podľa aktuálnej fázy hry."""


        # Posledný štich overlay — zatvoriť kliknutím kdekoľvek
        if self.show_last_trick:
            self.show_last_trick = False
            return

        # Tlačidlo posledného štichu
        if self._button_last_trick_rect().collidepoint(pos):
            current_round = self.game_state.current_round
            if current_round and current_round.tricks:
                self.show_last_trick = True
            return

        # Tlačidlo zoradenia — kedykoľvek
        if self._button_sort_rect().collidepoint(pos):
            self.game_state.players[self.game_state.human_index].hand.sort_hand()
            return
        if self._button_info_rect().collidepoint(pos):
            self.info_overlay.toggle()
            return
        if self._button_menu_rect().collidepoint(pos):
            self._reset_trick_state()
            self.running = False
            return
        if self.waiting_for_ai:  # ← pridané
            return
        if self.trick_waiting:  # ← pridané
            return
        if not self.game_state.is_human_turn:
            return

        # Ak čakáme na rozhodnutie o tromfe
        if self.pending_trump_card is not None:
            human_index = self.game_state.human_index
            human_cards = self.game_state.players[human_index].hand.cards
            clicked = self.card_renderer.get_clicked_card(pos, human_cards, human_index)
            if clicked == self.pending_trump_card:
                # Opätovný klik na tú istú kartu = zrušenie
                self.pending_trump_card = None
                self.pending_trump_suit = None
                return
            self._handle_trump_decision_click(pos)
            return

        phase = self.game_state.current_round.phase

        if phase == "bidding":
            self._handle_bidding_click(pos)
        elif phase == "talon":
            self._handle_talon_click(pos)
        elif phase == "tricks":
            self._handle_tricks_click(pos)

    def _process_talon_reveal(self):
        if not self.talon_revealing:
            return
        if pygame.time.get_ticks() < self.talon_reveal_timer:
            return

        # Spusti animáciu talonu ak ešte nezačala
        if not hasattr(self, '_talon_anim_started') or not self._talon_anim_started:
            winner_index = self.game_state.current_round.bidding.winner_index

            # Vytvor fake played_cards pre animáciu
            # Talon karty štartujú z pozície talonu
            fake_played = []
            for i, card in enumerate(self.talon_reveal_cards):
                fake_played.append((i, card))  # použijeme index 0 a 1

            # Upravíme start pozície v trick_animation
            self.trick_animation.start_talon(
                self.talon_reveal_cards,
                winner_index
            )
            self._talon_anim_started = True
            return

        # Čakaj kým animácia dobehne
        if not self.trick_animation.is_done:
            return

        # Animácia hotová
        self._talon_anim_started = False
        self.talon_revealing = False
        self.talon_reveal_cards = []

        current_round = self.game_state.current_round
        current_round.give_talon_to_winner()

        winner = current_round.bidding.winner

        if winner.is_human:
            self.can_raise_bid = True
            self.speech_bubble.show_instruction(
                self.game_state.human_index,
                "Musím odhodiť 2 karty"
            )
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
            self.speech_bubble.show_bid(player_index, new_bid)
            self.game_state.logger.log_bid(  # ← log priamo tu
                self.game_state.players[player_index].name,
                new_bid
            )
            done = current_round.process_bid(player_index, new_bid)
            if done:
                self._after_bidding()
            return

        if self._button_pass_rect().collidepoint(pos):
            self.speech_bubble.show_bid(player_index, None)
            self.game_state.logger.log_bid(  # ← log priamo tu
                self.game_state.players[player_index].name,
                None
            )
            done = current_round.process_bid(player_index, None)
            if done:
                self._after_bidding()
            return

    def _handle_talon_click(self, pos: tuple[int, int]):
        current_round = self.game_state.current_round
        player_index = self.game_state.human_index

        if current_round.bidding.winner_index != player_index:
            return

        # Tlačidlo Potvrdiť
        if self._button_confirm_rect().collidepoint(pos):
            if len(self.selected_discards) == 2:
                success = current_round.discard_cards(
                    player_index, self.selected_discards
                )
                if success:
                    self.game_state.logger.log_discard(
                        self.game_state.players[player_index].name,
                        self.selected_discards
                    )
                    self.selected_discards = []
                    self.speech_bubble.hide_instruction(player_index)

                    # Zobraz slider až teraz
                    if self.can_raise_bid:
                        self.bid_slider.show(
                            min_value=current_round.bidding.current_bid,
                            current_value=current_round.bidding.current_bid
                        )
                        # Bublina pre slider
                        self.speech_bubble.show_instruction(
                            player_index,
                            "Navýšim povinnosť?"
                        )
                    else:
                        self.can_raise_bid = False
                        current_round.start_trick()
            return

        # Klik na kartu
        clicked_card = self.card_renderer.get_clicked_card(
            pos,
            self.game_state.players[player_index].hand.cards,
            player_index
        )

        if clicked_card:
            if clicked_card.rank in ("ace", "ten"):
                self._show_message("Eso a desiatku nemôžeš zahodiť!")
                return
            if clicked_card in self.selected_discards:
                self.selected_discards.remove(clicked_card)
            elif len(self.selected_discards) < 2:
                self.selected_discards.append(clicked_card)

    def _handle_tricks_click(self, pos: tuple[int, int]):
        """Spracuje klik počas štichov."""
        current_round = self.game_state.current_round
        player_index = self.game_state.human_index

        if current_round.current_trick is None:  # ← pridané
            return

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

    def _reset_trick_state(self):
        """Resetuje stav štichu pri odchode z hry."""
        # Ak je štich kompletný ale neuzavretý — uzavri ho
        current_round = self.game_state.current_round
        if (current_round and current_round.current_trick and
                current_round.current_trick.is_complete):
            trick = current_round.current_trick
            winner_index = trick.get_winner_index()
            for ai in self.ai_players:
                if ai is not None:
                    ai.record_trick(
                        trick.leader_index,
                        trick.played_cards,
                        winner_index,
                        current_round.trick_number
                    )
            current_round.finish_trick()
            if current_round.phase == "scoring":
                self.game_state.finish_round()
                self.game_state.logger.save_round()

        # Reset stavov
        self.trick_waiting = False
        self.trick_display_timer = 0
        self._trick_anim_started = False
        self._talon_anim_started = False
        self.talon_revealing = False
        self.talon_reveal_cards = []
        self.trick_animation.done = True
        self.trick_animation.cards_in_flight = []
        self.waiting_for_ai = False
        self.pending_trump_card = None
        self.pending_trump_suit = None

        # Spusti nový štich ak hra pokračuje
        if (current_round and current_round.phase == "tricks"
                and current_round.current_trick is None):
            current_round.start_trick()

    # ------------------------------------------------------------------
    # Tromf
    # ------------------------------------------------------------------

    def _try_declare_trump(self, player_index: int, card: Card) -> bool:
        current_round = self.game_state.current_round

        if current_round.get_current_player_index() != player_index:
            return False
        if current_round.current_leader_index != player_index:
            return False
        if card.rank not in ("over", "king"):
            return False
        if not self.game_state.players[player_index].hand.has_trump_pair(card.suit):
            return False

        self.pending_trump_card = card
        self.pending_trump_suit = card.suit
        # ← NOVÉ: zapamätaj či je prvý štich
        self.pending_trump_first_trick = (current_round.trick_number == 0)
        return True

    def _handle_trump_decision_click(self, pos: tuple[int, int]):
        """Spracuje rozhodnutie hráča či chce hlásiť tromf."""
        current_round = self.game_state.current_round
        player_index = self.game_state.human_index

        if self._button_trump_yes_rect().collidepoint(pos):
            # ← prvý štich: zobraz info a nič nerob
            if self.pending_trump_first_trick:
                self._show_message("Tromf nie je možný v prvom štichu!")
                return

        if self._button_trump_yes_rect().collidepoint(pos):
            trump_suit = self.pending_trump_suit  # ← ulož pred vymazaním
            is_new = current_round.trump_suit is not None
            current_round.declare_trump(player_index, trump_suit)
            for ai in self.ai_players:
                if ai is not None:
                    ai.record_trump_declaration(trump_suit, player_index)
            # Log — tu poznáme trump_suit
            self.game_state.logger.log_trump(
                self.game_state.players[player_index].name,
                trump_suit,
                TRUMP_POINTS[trump_suit]
            )
            self._show_message(f"Tromf: {trump_suit}!")
            current_round.play_card(player_index, self.pending_trump_card)
            self.pending_trump_card = None
            self.pending_trump_suit = None
            self.speech_bubble.show_trump(player_index, trump_suit, is_new=is_new)
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
                    self._start_round()
                    self.game_state.current_round.start_bidding()
            else:
                current_round.start_trick()

    def _process_waiting_trick(self):
        if not self.trick_waiting:
            return

        current_round = self.game_state.current_round
        if not current_round or not current_round.current_trick:
            self.trick_waiting = False
            return
        if not current_round.current_trick.is_complete:
            self.trick_waiting = False
            return

        # Najprv počkaj kým uplynie display timer (karty viditeľné na stole)
        if pygame.time.get_ticks() < self.trick_display_timer:
            return  # ← čakaj, karty ostávajú na stole

        # Spusti animáciu až po uplynutí timera
        if not self._trick_anim_started:
            winner_index = current_round.current_trick.get_winner_index()
            self.trick_animation.start(
                current_round.current_trick.played_cards,
                winner_index
            )
            self._trick_anim_started = True
            return

        # Čakaj kým animácia dobehne
        if not self.trick_animation.is_done:
            return

        # Všetko hotovo — uzavri štich
        self._trick_anim_started = False
        self.trick_waiting = False

        trick = current_round.current_trick
        winner_index = trick.get_winner_index()

        # Log štichu ← pridané
        played = [
            (self.game_state.players[idx].name, card)
            for idx, card in trick.played_cards
        ]
        self.game_state.logger.log_trick(
            current_round.trick_number + 1,
            played,
            self.game_state.players[winner_index].name,
            trick.total_points
        )

        for ai in self.ai_players:
            if ai is not None:
                ai.record_trick(
                    trick.leader_index,
                    trick.played_cards,
                    winner_index,
                    current_round.trick_number
                )

        winner_index = current_round.finish_trick()
        winner_name = self.game_state.players[winner_index].name
        self._show_message(f"{winner_name} vyhral štich!")

        if current_round.phase == "scoring":
            self.game_state.finish_round()

            # Bubliny s výsledkami
            for i, player in enumerate(self.game_state.players):
                if player.is_bidder:
                    fulfilled = player.round_points >= player.bid
                    points = player.bid
                    self.speech_bubble.show_round_result(i, points, True, fulfilled)
                else:
                    # Zaokrúhli body rovnako ako _rounded_points() v player.py
                    rounded = player._rounded_points(player.round_points)
                    self.speech_bubble.show_round_result(i, rounded, False)

            # Log výsledku kola
            results = {}
            for player in self.game_state.players:
                results[player.name] = {
                    "is_bidder": player.is_bidder,
                    "bid": player.bid,
                    "round_points": player.round_points,
                    "total_score": player.total_score,
                    "fulfilled": (
                        player.round_points >= player.bid
                        if player.is_bidder else True
                    )
                }
            self.game_state.logger.log_round_result(results)
            self.game_state.logger.save_round()

            if self.game_state.phase == "game_over":
                self._show_message(
                    f"{self.game_state.winner.name} vyhral hru!", 5000
                )
                self.game_over_timer = pygame.time.get_ticks() + 3000
            else:
                self._start_round()
        else:
            current_round.start_trick()

    # ------------------------------------------------------------------
    # AI ťahy
    # ------------------------------------------------------------------

    def _handle_ai_turn(self):
        """Spracuje ťah AI hráča ak je na rade."""
        if self.dealing:  # ← pridané
            return
        if self.game_state.current_round is None:
            return
        if self.trick_waiting:  # ← pridané
            return
        if self.talon_revealing:  # ← pridané
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

                #pygame.time.delay(500)
                ai = self.ai_players[current_index]
                amount = ai.decide_bid(bidding.current_bid)
                self.speech_bubble.show_bid(current_index, amount)
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
        """AI zahodí 2 karty a rozhodne o navýšení."""
        current_round = self.game_state.current_round
        if current_round.bidding.winner_index != player_index:
            return

        # Zaznamená vlastnú ruku
        ai.record_own_hand(self.game_state.players[player_index].hand.cards)

        # Navýšenie po talóne
        new_bid = ai.decide_raise_after_talon(current_round.bidding.current_bid)
        if new_bid:
            current_round.bidding.current_bid = new_bid
            self.game_state.players[player_index].bid = new_bid
            self._show_message(f"{self.game_state.players[player_index].name} navýšil na {new_bid}")

        # Zahodenie
        cards = ai.decide_discard(self.game_state.players[player_index].hand.cards)
        current_round.discard_cards(player_index, cards)

        self.game_state.logger.log_discard(
            self.game_state.players[player_index].name,
            cards
        )

        current_round.start_trick()

    def _ai_play_card(self, player_index: int, ai: AI):
        self.waiting_for_ai = True

        current_round = self.game_state.current_round
        player = self.game_state.players[player_index]
        playable = player.hand.get_playable_cards(
            current_round.current_trick.lead_suit,
            current_round.trump_suit,
            current_round.current_trick.played_cards
        )

        card = ai.decide_card(
            playable, current_round.current_trick, current_round.trick_number
        )

        if (current_round.trick_number > 0
                and current_round.get_current_player_index() == player_index
                and current_round.current_leader_index == player_index
                and card.rank in ("over", "king")):

            if player.hand.has_trump_pair(card.suit):
                trump_suit = card.suit
                is_new = current_round.trump_suit is not None
                current_round.declare_trump(player_index, trump_suit)
                self.speech_bubble.show_trump(player_index, trump_suit, is_new=is_new)
                for a in self.ai_players:
                    if a is not None:
                        a.record_trump_declaration(trump_suit, player_index)
                # Log tromfu — priamo tu kde poznáme trump_suit
                from config import TRUMP_POINTS
                self.game_state.logger.log_trump(
                    player.name,
                    trump_suit,
                    TRUMP_POINTS[trump_suit]
                )

        current_round.play_card(player_index, card)

        if current_round.current_trick.is_complete:
            self.trick_waiting = True
            self.trick_display_timer = pygame.time.get_ticks() + 1500

        self.waiting_for_ai = False
    # ------------------------------------------------------------------
    # Po dražbe
    # ------------------------------------------------------------------

    def _confirm_raise_bid(self):
        current_round = self.game_state.current_round
        player_index = self.game_state.human_index
        new_bid = self.bid_slider.current_value

        if new_bid > current_round.bidding.current_bid:
            current_round.bidding.current_bid = new_bid
            self.game_state.players[player_index].bid = new_bid
            self._show_message(f"Povinnosť navýšená na {new_bid}", 5000)
            self.game_state.logger.log_raise(
                self.game_state.players[player_index].name,
                new_bid
            )

        self.speech_bubble.hide_instruction(player_index)  # ← pridané
        self.bid_slider.hide()
        self.can_raise_bid = False
        current_round.start_trick()

    def _after_bidding(self):
        """Spracuje situáciu po skončení dražby."""
        current_round = self.game_state.current_round
        winner = current_round.bidding.winner
        winner_index = current_round.bidding.winner_index  # ← hneď po winner

        # Uložíme karty talonu na zobrazenie
        self.talon_reveal_cards = current_round.talon.copy()
        self.talon_revealing = True
        self.talon_reveal_timer = pygame.time.get_ticks() + 2000

        self._show_message(f"{winner.name} vydražil za {winner.bid}", 5000)

        # Zaznamená dražiteľa do pamäte všetkých AI
        for ai in self.ai_players:
            if ai is not None:
                ai.memory.set_bidder(
                    winner_index,
                    current_round.bidding.current_bid
                )

        # AI víťaz si zapamätá talon
        ai = self.ai_players[winner_index]
        if ai is not None:
            ai.record_talon(current_round.talon)

        if winner.is_human:
            self.can_raise_bid = True
            # Bublina inštrukcie
            self.speech_bubble.show_instruction(
                self.game_state.human_index,
                "Musím odhodiť 2 karty"
            )

        self.game_state.logger.log_bid_winner(
            winner.name,
            current_round.bidding.current_bid
        )
        self.game_state.logger.log_talon_received(
            winner.name,
            current_round.talon
        )
    # ------------------------------------------------------------------
    # Kreslenie
    # ------------------------------------------------------------------

    def _draw(self):
        """Nakreslí celú obrazovku."""
        self._draw_table()
        self._draw_hands()
        if not self._trick_anim_started and (not self.trick_animation or self.trick_animation.is_done):
            self._draw_current_trick()

        self._draw_talon()
        # Talon reveal — len ak animácia ešte nezačala
        if self.talon_revealing and not self._talon_anim_started:
            self._draw_talon_reveal()
        self.trick_animation.draw()
        self._draw_player_labels()
        self.scoreboard.draw(
            self.game_state.players,
            self.game_state.current_round
        )
        self._draw_buttons()
        self.bid_slider.draw()
        self.speech_bubble.draw()
        self._draw_message()
        self.info_overlay.draw()
        if self.show_last_trick:
            self._draw_last_trick_overlay()

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
                selected_cards=self.selected_discards if current_round and current_round.phase == "talon" else (
                    [self.pending_trump_card] if self.pending_trump_card else []
                ),
                highlight_playable=is_current and player.is_human,
                trump_suit=trump_suit,
                lead_suit=current_round.current_trick.lead_suit if current_round and current_round.current_trick else None,
                played_cards=current_round.current_trick.played_cards if current_round and current_round.current_trick else []

            )

    def _draw_player_labels(self):
        """Nakreslí menovky hráčov."""

        font = get_font(28)

        label_positions = {
            0: (TABLE_CENTER_X, SCREEN_HEIGHT - 30),
            1: (120, TABLE_CENTER_Y -120),
            2: (SCREEN_WIDTH - 120, TABLE_CENTER_Y -120)
        }

        for i, player in enumerate(self.game_state.players):
            pos = label_positions[i]

            surf = font.render(player.name, True, COLOR_WHITE)
            rect = surf.get_rect(center=pos)

            bg_rect = rect.inflate(16, 8)

            bg = pygame.Surface(
                (bg_rect.width, bg_rect.height),
                pygame.SRCALPHA
            )

            bg.fill((0, 0, 0, 160))

            self.screen.blit(bg, bg_rect.topleft)

            pygame.draw.rect(
                self.screen,
                COLOR_GOLD,
                bg_rect,
                width=1,
                border_radius=6
            )

            self.screen.blit(surf, rect)

    def _draw_current_trick(self):
        """Nakreslí karty aktuálneho štichu."""
        current_round = self.game_state.current_round
        if current_round and current_round.current_trick:
            self.card_renderer.draw_trick(current_round.current_trick)

    def _draw_last_trick_overlay(self):
        """Nakreslí overlay s posledným štichom."""
        from config import CARD_SIZE_MEDIUM
        current_round = self.game_state.current_round
        if not current_round or not current_round.tricks:
            self.show_last_trick = False
            return

        dark = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 200))
        self.screen.blit(dark, (0, 0))

        last_trick = current_round.tricks[-1]
        winner_index = last_trick.get_winner_index()
        played = last_trick.played_cards  # [(player_idx, card), ...]

        card_w, card_h = CARD_SIZE_MEDIUM
        gap = 30
        total_w = len(played) * (card_w + gap) - gap
        x0 = SCREEN_WIDTH // 2 - total_w // 2
        y0 = SCREEN_HEIGHT // 2 - card_h // 2 - 40

        title = self.font_large.render("POSLEDNÝ ŠTICH", True, COLOR_GOLD)
        self.screen.blit(title, title.get_rect(
            centerx=SCREEN_WIDTH // 2, top=y0 - 60
        ))

        for i, (player_idx, card) in enumerate(played):
            cx = x0 + i * (card_w + gap)
            is_winner = (player_idx == winner_index)

            img = self.card_renderer._get_card_image(card)
            self.screen.blit(img, (cx, y0))

            border_color = COLOR_GOLD if is_winner else COLOR_GRAY
            border_width = 3 if is_winner else 1
            pygame.draw.rect(self.screen, border_color,
                             (cx, y0, card_w, card_h),
                             width=border_width, border_radius=6)

            name = self.game_state.players[player_idx].name
            name_surf = self.font_large.render(
                name, True, COLOR_GOLD if is_winner else COLOR_WHITE
            )
            self.screen.blit(name_surf, name_surf.get_rect(
                centerx=cx + card_w // 2, top=y0 + card_h + 8
            ))

        hint = self.font_medium.render("Klikni pre zavretie", True, COLOR_GRAY)
        self.screen.blit(hint, hint.get_rect(
            centerx=SCREEN_WIDTH // 2, top=y0 + card_h + 50
        ))

    def _draw_talon(self):
        """Nakreslí talon."""
        current_round = self.game_state.current_round
        if current_round and current_round.phase == "bidding":
            if self.debug:
                # V debug móde ukáž karty talonu
                self.card_renderer.draw_talon_debug(current_round.talon)
            else:
                self.card_renderer.draw_talon(len(current_round.talon))

    def _draw_talon_reveal(self):
        """Zobrazí karty talonu v strede obrazovky."""
        if not self.talon_revealing or not self.talon_reveal_cards:
            return

        for i, card in enumerate(self.talon_reveal_cards):
            img = self.card_renderer._get_card_image(card)
            x = TALON_X + i * CARD_FAN_OFFSET
            y = TALON_Y
            self.screen.blit(img, (x, y))

    def _draw_buttons(self):
        self._draw_button(
            self._button_sort_rect(),
            "Zoradiť karty",
            COLOR_BUTTON_SECONDARY
        )
        self._draw_button(
            self._button_info_rect(),
            "Pravidlá",
            COLOR_BUTTON_SECONDARY
        )
        # Menu tlačidlo — vždy viditeľné
        self._draw_button(
            self._button_menu_rect(),
            "Menu",
            COLOR_BUTTON_SECONDARY
        )
        current_round = self.game_state.current_round
        if (current_round and current_round.tricks and
                current_round.phase == "tricks"):
            self._draw_button(
                self._button_last_trick_rect(),
                "Posledný štich",
                COLOR_BUTTON_SECONDARY
            )

        if not self.game_state.is_human_turn:
            return

        if self.pending_trump_card is not None:
            trump_labels = {
                "heart": "Srdce", "bell": "Guľa",
                "leaf": "Zeleň", "acorn": "Žaluď"
            }
            label = trump_labels.get(self.pending_trump_suit, self.pending_trump_suit)

            if self.pending_trump_first_trick:
                # ← prvý štich: šedé/disabled tromf tlačidlo + bez tromfu
                self._draw_button(self._button_trump_yes_rect(), f"Tromf: {label}", COLOR_BUTTON_SECONDARY)
                self._draw_button(self._button_trump_no_rect(), "Bez tromfu", COLOR_BUTTON_SECONDARY)
            else:
                self._draw_button(self._button_trump_yes_rect(), f"Tromf: {label}", COLOR_BUTTON_PRIMARY)
                self._draw_button(self._button_trump_no_rect(), "Bez tromfu", COLOR_BUTTON_SECONDARY)
            return

        phase = self.game_state.current_round.phase if self.game_state.current_round else None

        if phase == "bidding":
            from config import MAX_BID
            current_round = self.game_state.current_round  # ← pridané
            current_bid = current_round.bidding.current_bid
            if current_bid < MAX_BID:
                self._draw_button(self._button_bid_rect(), "Dám +10", COLOR_BUTTON_PRIMARY)
            self._draw_button(self._button_pass_rect(), "Dobrý", COLOR_BUTTON_SECONDARY)
        elif phase == "talon":
            if len(self.selected_discards) == 2:
                self._draw_button(self._button_confirm_rect(), "Potvrdiť", COLOR_BUTTON_PRIMARY)



    def _draw_button(self, rect: pygame.Rect, text: str, color: tuple):
        """Nakreslí jedno tlačidlo."""
        mouse_pos = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mouse_pos)

        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        alpha = 240 if is_hover else 200
        overlay.fill((*color, alpha))
        self.screen.blit(overlay, (rect.x, rect.y))

        border_color = COLOR_WHITE if is_hover else COLOR_GOLD
        pygame.draw.rect(self.screen, border_color, rect, width=2, border_radius=BUTTON_RADIUS)

        surf = self.font_medium.render(text, True, COLOR_WHITE)
        text_rect = surf.get_rect(center=rect.center)
        self.screen.blit(surf, text_rect)

    def _draw_message(self):
        """Zobrazí správu s priehľadným pozadím tesne nad kartami hráča."""
        if not self.message or pygame.time.get_ticks() >= self.message_timer:
            return

        surf = self.font_large.render(self.message, True, COLOR_YELLOW)
        msg_w = surf.get_width() + 60
        msg_h = surf.get_height() + 20

        # Pozícia — tesne nad karty hráča (y=860 je HUMAN_HAND_Y)
        msg_x = TABLE_CENTER_X - msg_w // 2
        msg_y = HUMAN_HAND_Y - 55 - msg_h // 2

        # Priehľadný overlay
        overlay = pygame.Surface((msg_w, msg_h), pygame.SRCALPHA)
        overlay.fill((25, 15, 8, 200))
        self.screen.blit(overlay, (msg_x, msg_y))

        # Zlatý okraj
        pygame.draw.rect(
            self.screen, COLOR_GOLD,
            (msg_x, msg_y, msg_w, msg_h),
            width=2, border_radius=8
        )

        # Text
        text_rect = surf.get_rect(center=(TABLE_CENTER_X, msg_y + msg_h // 2))
        self.screen.blit(surf, text_rect)

    # ------------------------------------------------------------------
    # Rects — tlačidlá
    # ------------------------------------------------------------------

    @staticmethod
    def _button_bid_rect() -> pygame.Rect:
        return pygame.Rect(TABLE_CENTER_X - 200, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)

    @staticmethod
    def _button_pass_rect() -> pygame.Rect:
        return pygame.Rect(TABLE_CENTER_X + 20, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)

    @staticmethod
    def _button_confirm_rect() -> pygame.Rect:
        return pygame.Rect(TABLE_CENTER_X - BUTTON_WIDTH // 2, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)

    @staticmethod
    def _button_trump_yes_rect() -> pygame.Rect:
        return pygame.Rect(TABLE_CENTER_X - 200, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)

    @staticmethod
    def _button_trump_no_rect() -> pygame.Rect:
        return pygame.Rect(TABLE_CENTER_X + 20, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)

    @staticmethod
    def _button_last_trick_rect() -> pygame.Rect:
        from config import BUTTON_SORT_X, BUTTON_SORT_Y, BUTTON_SORT_WIDTH, BUTTON_SORT_HEIGHT
        return pygame.Rect(BUTTON_SORT_X, BUTTON_SORT_Y - BUTTON_SORT_HEIGHT - 10,
                           BUTTON_SORT_WIDTH, BUTTON_SORT_HEIGHT)

    @staticmethod
    def _button_sort_rect() -> pygame.Rect:
        from config import BUTTON_SORT_X, BUTTON_SORT_Y, BUTTON_SORT_WIDTH, BUTTON_SORT_HEIGHT
        return pygame.Rect(BUTTON_SORT_X, BUTTON_SORT_Y, BUTTON_SORT_WIDTH, BUTTON_SORT_HEIGHT)

    @staticmethod
    def _button_info_rect() -> pygame.Rect:
        from config import BUTTON_INFO_X, BUTTON_INFO_Y, BUTTON_INFO_WIDTH, BUTTON_INFO_HEIGHT
        return pygame.Rect(BUTTON_INFO_X, BUTTON_INFO_Y, BUTTON_INFO_WIDTH, BUTTON_INFO_HEIGHT)

    @staticmethod
    def _button_menu_rect() -> pygame.Rect:
        from config import BUTTON_MENU_X, BUTTON_MENU_Y, BUTTON_MENU_WIDTH, BUTTON_MENU_HEIGHT
        return pygame.Rect(BUTTON_MENU_X, BUTTON_MENU_Y, BUTTON_MENU_WIDTH, BUTTON_MENU_HEIGHT)
    # ------------------------------------------------------------------
    # Pomocné metódy
    # ------------------------------------------------------------------
    def _auto_sort(self):
        self.game_state.players[self.game_state.human_index].hand.sort_hand()

    def _show_message(self, text: str, duration_ms: int = 2000):
        """Zobrazí správu na obrazovke."""
        self.message = text
        self.message_timer = pygame.time.get_ticks() + duration_ms

    def __repr__(self) -> str:
        return f"Screen({SCREEN_WIDTH}x{SCREEN_HEIGHT}, debug={self.debug})"