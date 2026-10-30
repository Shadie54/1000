# gui/screen.py

import os

import pygame
from gui import display, layout
from gui.canvas import draw_backdrop, StaticLayer

from config import (
    SCREEN_WIDTH, FPS, DEBUG_MODE,
    COLOR_BG, COLOR_BG_DARK,
    FONT_SIZE_MEDIUM, FONT_SIZE_LARGE, FONT_SIZE_SMALL,
    COLOR_BUTTON_PRIMARY, COLOR_BUTTON_SECONDARY,
    CARD_FAN_OFFSET, TRUMP_POINTS, ANIMATION_SPEED_DEFAULT,
)
from game.ai import AI
from game.card import Card
from game.game_state import GameState
from game import savegame
from gui.bid_slider import BidSlider
from gui.card_renderer import CardRenderer
from gui.deal_animation import DealAnimation
from gui.info_overlay import InfoOverlay
from gui.last_trick_overlay import LastTrickOverlay
from gui.achievements_screen import AchievementsOverlay
from gui import ui_style
from game.round import first_trick_min_bid

# Stĺpec tlačidiel vpravo dole — tlačidlo s okrúhlym medailónom a ikonkou
# vľavo (grafický rework 2026-10-28, z CHUJ). Chýbajúca ikonka sa vynechá;
# pre "sort" je kreslená náhrada (_draw_sort_icon), kým nepribudne sort.png.
COLUMN_ICON_FILES = {
    "last_trick": "last_trick.png",
    "sort": "sort.png",
    "info": "rules.png",
    "trophies": "trophy.png",
    "menu": "menu.png",
}
COLUMN_MEDALLION_R = 28        # polomer medailónu (tlačidlo je vysoké 50)
COLUMN_ICON_SIZE = 38          # ikonka vnútri medailónu
COLUMN_RADIUS = 12             # zaoblenie rohov tlačidla
COLUMN_TEXT_X = 66             # začiatok textu od ľavého okraja tlačidla
from gui.scoreboard import Scoreboard
from gui.speech_bubble import SpeechBubble
from gui.trick_animation import TrickAnimation
from gui.card_throw_animation import CardThrowAnimation
from gui.achievement_popup import AchievementPopup

# Slovenské názvy farieb (tlačidlo tromfu, správa po zahlásení)
TRUMP_LABELS = {
    "heart": "Srdce", "bell": "Guľa",
    "leaf": "Zeleň", "acorn": "Žaluď"
}



class Screen:
    def __init__(self, game_state: GameState, ai_players: list[AI],
                 debug: bool = DEBUG_MODE, new_game: bool = True,
                 table_bg: str = "table.jpg", achievement_tracker=None,
                 animation_speed: float = ANIMATION_SPEED_DEFAULT,
                 restore_ui: dict | None = None, autosave: bool = True,
                 clockwise: bool = True):
        pygame.init()
        # Okno otvára výhradne gui/display.py. Kreslí sa cez Canvas
        # (gui/canvas.py) v logických súradniciach priamo do okna;
        # rozloženie hernej obrazovky je v gui/layout.py.
        self.canvas = display.canvas()
        # Smer hry (Nastavenia → Hra): mení len miesta počítačov pri stole
        layout.set_clockwise(clockwise)
        self.layout = layout.game()
        self.H = self.layout.l_h
        path = f"assets/graphics/{table_bg}"
        self.table_bg = path if os.path.exists(path) else None
        # Statická vrstva (stôl + ruky): pri 4K je kopírovanie pozadia a
        # ~30 kariet každú snímku drahé — kreslia sa len pri zmene stavu.
        self._static: StaticLayer | None = None
        self.clock = pygame.time.Clock()
        self.debug = debug

        self.game_state = game_state
        self.achievement_tracker = achievement_tracker
        self.achievement_popup = AchievementPopup(self.canvas)
        self.ai_players = ai_players

        self.card_renderer = CardRenderer(self.canvas, debug)
        self.scoreboard = Scoreboard(self.canvas)
        self.font_small = self.canvas.font(FONT_SIZE_SMALL)
        self.font_medium = self.canvas.font(FONT_SIZE_MEDIUM)
        self.font_large = self.canvas.font(FONT_SIZE_LARGE)

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
        self.trick_animation = TrickAnimation(self.canvas, self.card_renderer)
        # Let zahratej karty z ruky na stôl (prevzaté z CHUJ)
        self.card_throw_animation = CardThrowAnimation(
            self.canvas, self.card_renderer, animation_speed)
        # Zber štichu k víťazovi sa smie zrýchliť, ale nikdy nespomalí pod
        # základnú rýchlosť (cesta k súperom by bola nepríjemne pomalá).
        self.trick_animation.card_speed *= max(animation_speed, 1.0)
        self._trick_anim_started: bool = False
        #speech bubliny
        self.speech_bubble = SpeechBubble(self.canvas)
        #bid slider
        self.bid_slider = BidSlider(self.canvas)
        #animácia talonu ku hráčovi
        self.talon_anim_cards: list[dict] = []
        self.talon_animating: bool = False
        self.talon_anim_done: bool = True
        self._talon_anim_started: bool = False
        self.running = True
        self.new_game = new_game
        # Uloženie rozohratej hry (game/savegame.py): restore_ui = stav
        # obrazovky pri odchode (posuvník navýšenia a pod.), exit_ui sa
        # naplní pri odchode z run(). autosave=False pre testy.
        self.restore_ui = restore_ui or {}
        self.exit_ui: dict = {}
        self.autosave = autosave

        self.info_overlay = InfoOverlay(self.canvas,
                                        game_state.first_trick_trump)
        self.last_trick_overlay = LastTrickOverlay(self.canvas, self.card_renderer)
        # Ikonky stĺpca tlačidiel vpravo dole (assets/graphics, 512×512 —
        # Canvas ich zmenší z plného rozlíšenia, ostré aj pri 4K)
        self._column_icons = {}
        for key, name in COLUMN_ICON_FILES.items():
            path = os.path.join("assets", "graphics", name)
            try:
                self._column_icons[key] = self.canvas.image(
                    path, (COLUMN_ICON_SIZE, COLUMN_ICON_SIZE))
            except (FileNotFoundError, pygame.error):
                self._column_icons[key] = None
        # Trofeje počas hry (tlačidlo Trofeje v stĺpci)
        self.trophy_overlay = AchievementsOverlay(achievement_tracker)
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
            self._restore_after_continue()

        while self.running:
            self.clock.tick(FPS)
            if not self.step_frame():
                break
            display.present()  # ← správne miesto — vnútri while

        # Mimo while cyklu — dorovnaj prechodné stavy a ulož / zmaž hru
        self._settle_for_save()
        if self.game_state.phase == "game_over":
            if self.autosave:
                savegame.delete_save()
            return "game_over"
        self.exit_ui = {"can_raise_bid": self.can_raise_bid,
                        "raise_pending": self.bid_slider.visible}
        if self.autosave:
            savegame.save_game(self.game_state, self.ai_players,
                               self.achievement_tracker, self.exit_ui)
        return "menu"

    # ------------------------------------------------------------------
    # Odchod z hry a návrat ("Pokračovať", aj po reštarte programu)
    # ------------------------------------------------------------------

    def _settle_for_save(self):
        """Pri odchode z hry (Menu, zatvorenie okna) dorovná prechodné
        stavy, aby sa dala hra uložiť a neskôr presne obnoviť:
        - kompletný, ešte nezozbieraný štich sa uzavrie celou bežnou
          cestou (log, AI pamäť, trofeje, prípadne koniec kola),
        - odkrytý talon sa dá víťazovi dražby,
        - animácie a dočasné stavy sa zrušia."""
        rnd = self.game_state.current_round
        if (rnd is not None and rnd.current_trick is not None
                and rnd.current_trick.is_complete):
            self.trick_waiting = True
            self.trick_display_timer = 0
            self._process_waiting_trick()          # spustí animáciu zberu
            self.trick_animation.done = True
            self.trick_animation.cards_in_flight = []
            self._process_waiting_trick()          # uzavrie štich
        rnd = self.game_state.current_round
        if (self.talon_revealing and rnd is not None
                and rnd.phase == "talon" and rnd.talon):
            rnd.give_talon_to_winner()
            if rnd.bidding.winner.is_human:
                self.can_raise_bid = True
        self.talon_revealing = False
        self.talon_reveal_cards = []
        self.dealing = False
        self.deal_animation = None
        self._reset_trick_state()

    def _restore_after_continue(self):
        """Návrat do rozohratej hry: obnoví to, čo nie je v hernom stave
        (posuvník navýšenia, inštrukcie), alebo rozdá ďalšie kolo."""
        gs = self.game_state
        rnd = gs.current_round
        if gs.phase == "game_over":
            return
        if rnd is None or rnd.phase in ("dealing", "scoring", "done"):
            self._start_round()
            return
        self._auto_sort()
        hi = gs.human_index
        ui = self.restore_ui
        if rnd.phase == "talon" and rnd.bidding.winner_index == hi:
            # Víťaz dražby je hráč — má talon na ruke a ešte neodhodil
            self.can_raise_bid = ui.get("can_raise_bid", True)
            self.speech_bubble.show_instruction(hi, "Musím odhodiť 2 karty")
        elif (rnd.phase == "tricks" and rnd.current_trick is None
              and ui.get("raise_pending")):
            # Odhodil, ale ešte nepotvrdil navýšenie povinnosti
            self.can_raise_bid = True
            self.bid_slider.show(min_value=rnd.bidding.current_bid,
                                 current_value=rnd.bidding.current_bid)
            self.speech_bubble.show_instruction(hi, "Navýšim povinnosť?")
        elif rnd.phase == "tricks" and rnd.current_trick is None:
            rnd.start_trick()

    def step_frame(self) -> bool:
        """
        Jedna snímka hry: udalosti, logika, kreslenie (bez tick a flip).
        Volá ju run() a aj headless testy (tester/regression_screen.py,
        tools/screenshot_gallery.py), aby bežali presne tú istú cestu.
        Vráti False, ak sa má hlavná slučka ukončiť (koniec hry).
        """
        if self.game_over_timer and pygame.time.get_ticks() >= self.game_over_timer:
            self.running = False
            return False

        self._handle_events()

        if self.dealing and self.deal_animation:
            self.deal_animation.update()
            self.deal_animation.draw(self._draw_table, self._draw_static)
            self.speech_bubble.draw()
            # Prehľad otvorený z konca kola ostáva viditeľný aj pri rozdávaní
            self.info_overlay.draw()
            self.trophy_overlay.draw()
            if self.deal_animation.done:
                self.dealing = False
                self.deal_animation = None
                pygame.event.clear()
                self._auto_sort()
        else:
            self._process_talon_reveal()
            self._process_waiting_trick()
            self.trick_animation.update()
            self.card_throw_animation.update()
            self._handle_ai_turn()
            self._draw()
            # ← NOVÉ
            if self.achievement_tracker:
                notifications = self.achievement_tracker.pop_notifications()
                if notifications:
                    self.achievement_popup.add(notifications)
            self.achievement_popup.update()
            self.achievement_popup.draw()
        return True

    def _start_round(self):
        """Začne nové kolo a inicializuje AI pamäť."""
        if self.achievement_tracker:
            self.achievement_tracker.reset_round()

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

        self.deal_animation = DealAnimation(self.canvas, self.card_renderer)
        self.deal_animation.start(current_round.obligation_index)
        self.dealing = True

    # ------------------------------------------------------------------
    # Spracovanie udalostí
    # ------------------------------------------------------------------

    def _handle_events(self):
        for event in display.get_events():
            if event.type == pygame.QUIT:
                self.running = False

            # Popup trofeje leží navrch všetkého — klik naň ho zavrie
            if not self.dealing and self.achievement_popup.handle_event(event):
                continue
            # Otvorený prehľad (Trofeje / Pravidlá) dostane udalosť prvý —
            # Esc ho zavrie a nevyhodí hráča do menu.
            if self.trophy_overlay.visible:
                if self.trophy_overlay.handle_event(event):
                    continue
            if self.info_overlay.visible:
                if self.info_overlay.handle_event(event):
                    continue

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
        if self._button_trophies_rect().collidepoint(pos):
            self.trophy_overlay.show()
            return
        if self._button_menu_rect().collidepoint(pos):
            # Rozohraný štich/talon dorovná _settle_for_save() v run()
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

            # ← NOVÉ: achievement tracking
            if self.achievement_tracker:
                self.achievement_tracker.on_bid_placed()

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

                    # ← NOVÉ: achievement tracking
                    if self.achievement_tracker:
                        self.achievement_tracker.on_discard(self.selected_discards)

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
                        self._check_trump_streak()  # ← NOVÉ
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

        if self._play_card(player_index, clicked_card):
            self.selected_card = None

    def _play_card(self, player_index: int, card: Card) -> bool:
        """Zahrá kartu (človek aj AI): karta letí z ruky na stôl; ak je
        štich kompletný, počká sa, kým ho hráč uvidí."""
        current_round = self.game_state.current_round
        throw_start = self.card_renderer.hand_card_center(
            player_index, self.game_state.players[player_index].hand.cards, card)
        if not current_round.play_card(player_index, card):
            return False
        self.card_throw_animation.start(player_index, card, throw_start)
        if current_round.current_trick.is_complete:
            self.trick_waiting = True
            self.trick_display_timer = pygame.time.get_ticks() + 1500
        return True

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
        self.card_throw_animation.in_flight = {}
        self.waiting_for_ai = False
        self.pending_trump_card = None
        self.pending_trump_suit = None

        # Spusti nový štich ak hra pokračuje — nie však, kým hráč nepotvrdil
        # navýšenie povinnosti (štich spustí až _confirm_raise_bid)
        if (current_round and current_round.phase == "tricks"
                and current_round.current_trick is None
                and not self.bid_slider.visible):
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
        if current_round.current_trick and current_round.current_trick.played_cards:
            return False
        if card.rank not in ("over", "king"):
            return False
        if not self.game_state.players[player_index].hand.has_trump_pair(card.suit):
            return False

        self.pending_trump_card = card
        self.pending_trump_suit = card.suit
        # ← NOVÉ: zapamätaj či je prvý štich
        # Tromf sa (zatiaľ) hlásiť nedá — tlačidlo ostane neaktívne
        self.pending_trump_first_trick = not current_round.can_declare_trump(
            player_index, card.suit)
        return True

    def _handle_trump_decision_click(self, pos: tuple[int, int]):
        """Spracuje rozhodnutie hráča či chce hlásiť tromf."""
        current_round = self.game_state.current_round
        player_index = self.game_state.human_index

        if self._button_trump_yes_rect().collidepoint(pos):
            # ← prvý štich: zobraz info a nič nerob
            if self.pending_trump_first_trick:
                if current_round.first_trick_trump:
                    need = first_trick_min_bid(self.pending_trump_suit)
                    self._show_message(f"V 1. štichu len s povinnosťou aspoň {need}!")
                else:
                    self._show_message("Tromf nie je možný v prvom štichu!")
                return

            trump_suit = self.pending_trump_suit
            is_new = current_round.trump_suit is not None
            current_round.declare_trump(player_index, trump_suit)

            # ← NOVÉ: achievement tracking
            if self.achievement_tracker:
                self.achievement_tracker.on_trump_declared(
                    suit=trump_suit,
                    trick_number=current_round.trick_number,
                    hand_cards=self.game_state.players[player_index].hand.cards,
                    is_new_trump=is_new,
                    is_human = True  # ← NOVÉ
                )

            for ai in self.ai_players:
                if ai is not None:
                    ai.record_trump_declaration(trump_suit, player_index)
            # Log — tu poznáme trump_suit
            self.game_state.logger.log_trump(
                self.game_state.players[player_index].name,
                trump_suit,
                TRUMP_POINTS[trump_suit]
            )
            self._show_message(f"Tromf: {TRUMP_LABELS.get(trump_suit, trump_suit)}!")
            if current_round.declared_in_first_trick and current_round.trick_number == 0:
                self._show_message("Tromf v 1. štichu — musíš ešte zobrať "
                                   "aspoň jeden štich!", 5000)
            self._play_card(player_index, self.pending_trump_card)
            self.pending_trump_card = None
            self.pending_trump_suit = None
            self.speech_bubble.show_trump(player_index, trump_suit, is_new=is_new)

        elif self._button_trump_no_rect().collidepoint(pos):
            self._play_card(player_index, self.pending_trump_card)
            self.pending_trump_card = None
            self.pending_trump_suit = None
    # ------------------------------------------------------------------
    # Koniec štichu
    # ------------------------------------------------------------------

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

        # ← NOVÉ: achievement tracking
        if self.achievement_tracker:
            self.achievement_tracker.on_trick_won(
                winner_is_human=(winner_index == self.game_state.human_index),
                trick_points=trick.total_points
            )

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

            # ← NOVÉ: achievement tracking
            if self.achievement_tracker:
                human_index = self.game_state.human_index
                human = self.game_state.players[human_index]
                human_fulfilled = (current_round.bidder_fulfilled()
                                   if human.is_bidder else True)

                self.achievement_tracker.on_round_finished(
                    human_is_bidder=human.is_bidder,
                    human_bid=human.bid,
                    human_round_points=human.round_points,
                    human_fulfilled=human_fulfilled,
                    human_card_points_only=self.achievement_tracker.round_human_card_points
                )
                self.achievement_tracker.on_score_updated(human.total_score)

            # Bubliny s výsledkami
            for i, player in enumerate(self.game_state.players):
                if player.is_bidder:
                    fulfilled = current_round.bidder_fulfilled()
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
                    "fulfilled": (current_round.bidder_fulfilled()
                                  if player.is_bidder else True)
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
        if self.card_throw_animation.in_flight:
            # Nechaj doletieť kartu vo vzduchu — inak by ďalšie AI (a jeho
            # blokujúci delay() nižšie) zamrazilo slučku skôr, než sa
            # animácia stihne prehrať.
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
            for a in self.ai_players:
                if a is not None:
                    a.memory.set_bidder(player_index, new_bid)

        # Zahodenie
        cards = ai.decide_discard(self.game_state.players[player_index].hand.cards)
        current_round.discard_cards(player_index, cards)

        self.game_state.logger.log_discard(
            self.game_state.players[player_index].name,
            cards
        )
        self._check_trump_streak()
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

        if (current_round.get_current_player_index() == player_index
                and card.rank in ("over", "king")):

            if current_round.can_declare_trump(player_index, card.suit):
                trump_suit = card.suit
                is_new = current_round.trump_suit is not None
                current_round.declare_trump(player_index, trump_suit)

                # ← NOVÉ: achievement tracking (len počíta poradie, neodomyká human achievementy)
                if self.achievement_tracker:
                    self.achievement_tracker.on_trump_declared(
                        suit=trump_suit,
                        trick_number=current_round.trick_number,
                        hand_cards=[],  # nepoužije sa pri is_human=False
                        is_new_trump=is_new,
                        is_human=False
                    )

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

        self._play_card(player_index, card)

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
            for ai in self.ai_players:
                if ai is not None:
                    ai.memory.set_bidder(player_index, new_bid)
            self.game_state.logger.log_raise(
                self.game_state.players[player_index].name,
                new_bid
            )

        self.speech_bubble.hide_instruction(player_index)  # ← pridané
        self.bid_slider.hide()
        self.can_raise_bid = False
        self._check_trump_streak()  # ← NOVÉ
        current_round.start_trick()

    def _after_bidding(self):
        """Spracuje situáciu po skončení dražby."""
        current_round = self.game_state.current_round
        winner = current_round.bidding.winner
        winner_index = current_round.bidding.winner_index  # ← hneď po winner

        # ← NOVÉ: achievement tracking — tichý pozorovateľ
        if (self.achievement_tracker
                and not self.achievement_tracker.round_human_bid
                and winner_index != self.game_state.human_index):  # ← pridaná podmienka
            human_hand = self.game_state.players[self.game_state.human_index].hand
            trump_pair_count = len(human_hand.get_available_trumps())
            self.achievement_tracker.on_bidding_passed_with_trumps(trump_pair_count)

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

        # ← NOVÉ: achievement tracking — šťastný nákup (len ak human vyhral)
        if self.achievement_tracker and winner.is_human:
           self.achievement_tracker.on_talon_received(current_round.talon)

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
        if self.info_overlay.covers_screen:
            # Okno Pravidlá prekryje celé okno (s obrazom hry z chvíle
            # otvorenia) — hru netreba kresliť (výkon pri 4K).
            self.info_overlay.draw()
            return
        if self.trophy_overlay.covers_screen:
            # Otvorené Trofeje prekryjú celé okno (s obrazom hry z chvíle
            # otvorenia) — hru netreba kresliť (výkon pri 4K).
            self.trophy_overlay.draw()
            return
        # Stôl a ruky — zo statickej vrstvy, prekreslí sa len pri zmene
        self._draw_static(self._hands_key(),
                          lambda: (self._draw_table(), self._draw_hands()))
        if not self._trick_anim_started and (not self.trick_animation or self.trick_animation.is_done):
            self._draw_current_trick()
            self.card_throw_animation.draw()   # karty letiace z ruky na stôl

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
        self.trophy_overlay.draw()

    def _draw_static(self, key, draw_fn):
        """Nakreslí statický obsah cez StaticLayer: draw_fn() sa zavolá
        len vtedy, keď sa zmenil `key` (hashovateľný opis stavu), inak sa
        len skopíruje hotová vrstva. Výsledok je pixel po pixeli rovnaký
        ako priame kreslenie (vrstva má formát okna)."""
        c = self.canvas
        size = c.target.get_size()
        if self._static is None or self._static.surface.get_size() != size:
            self._static = StaticLayer(size)
        if self._static.needs_redraw(key):
            with self._static.drawing(c, key):
                draw_fn()
        self._static.blit_to(c.target)

    def _hands_key(self) -> tuple:
        """Všetko, od čoho závisí vzhľad stola a rúk (_draw_hands)."""
        rnd = self.game_state.current_round
        trick = rnd.current_trick if rnd else None
        if rnd and rnd.phase == "talon":
            selected = tuple(self.selected_discards)
        else:
            selected = (self.pending_trump_card,) if self.pending_trump_card else ()
        return (
            "game", self.table_bg, self.debug,
            rnd.trump_suit if rnd else None,
            trick.lead_suit if trick else None,
            tuple(trick.played_cards) if trick else (),
            rnd.get_current_player_index() if rnd else None,
            selected,
            tuple(tuple(p.hand.cards) for p in self.game_state.players),
        )

    def _draw_table(self):
        """Nakreslí herný stôl."""
        if self.table_bg:
            # Stôl cez celé okno (aj pásma pri 21:9)
            draw_backdrop(self.canvas, None, self.table_bg)
        else:
            # Fallback ak obrázok chýba
            self.canvas.fill_window(COLOR_BG)
            cx, cy = self.layout.table_center
            pygame.draw.ellipse(
                self.canvas.target, COLOR_BG_DARK,
                self.canvas.prect((cx - 400, cy - 250, 800, 500))
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

    def _active_player_index(self) -> int | None:
        """Kto je práve na rade (menovka sa zvýrazní): dražba — ďalší
        dražiteľ, talon — víťaz dražby, štichy — hráč na ťahu."""
        rnd = self.game_state.current_round
        if rnd is None or self.dealing:
            return None
        if rnd.phase == "bidding":
            return self._get_next_bidder_index()
        if rnd.phase == "talon":
            return rnd.bidding.winner_index
        if rnd.phase == "tricks" and not self.trick_waiting:
            return rnd.get_current_player_index()
        return None

    def _draw_player_labels(self):
        """Menovky hráčov — tmavý štítok so zlatohnedým rámom; hráč na rade
        má zlatý rám a zlaté meno (gui/ui_style.py, rework 2026-10-28)."""
        font = self.canvas.font(28)
        active_index = self._active_player_index()
        for i, player in enumerate(self.game_state.players):
            active = i == active_index
            surf = font.render(player.name, True,
                               ui_style.BTN_TEXT_HOVER if active else ui_style.TEXT)
            rect = surf.get_rect(center=self.layout.label_positions[i])
            bg_rect = rect.inflate(24, 10)
            self.canvas.overlay(bg_rect.move(0, 3), (0, 0, 0, 90), border_radius=8)
            self.canvas.overlay(bg_rect, (17, 11, 7, 225), border_radius=8)
            self.canvas.rect(ui_style.GOLD if active else ui_style.GOLD_SOFT,
                             bg_rect, width=2, border_radius=8)
            self.canvas.blit(surf, rect)

    def _draw_current_trick(self):
        """Nakreslí karty aktuálneho štichu."""
        current_round = self.game_state.current_round
        if current_round and current_round.current_trick:
            self.card_renderer.draw_trick(
                current_round.current_trick,
                exclude_players=set(self.card_throw_animation.in_flight))

    def _draw_last_trick_overlay(self):
        """Okno s posledným štichom (gui/last_trick_overlay.py, z CHUJ)."""
        current_round = self.game_state.current_round
        if not current_round or not current_round.tricks:
            self.show_last_trick = False
            return
        self.last_trick_overlay.update_hover(display.mouse_pos())
        self.last_trick_overlay.draw(current_round.tricks[-1], self.game_state.players)

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

        tx, ty = self.layout.talon_pos
        for i, card in enumerate(self.talon_reveal_cards):
            img = self.card_renderer._get_card_image(card)
            self.canvas.blit(img, (tx + i * CARD_FAN_OFFSET, ty))

    def _draw_buttons(self):
        # Stĺpec vpravo dole — tlačidlá s medailónom a ikonkou
        self._draw_column_button(self._button_sort_rect(), "Zoradiť karty", "sort")
        self._draw_column_button(self._button_info_rect(), "Pravidlá", "info")
        self._draw_column_button(self._button_trophies_rect(), "Trofeje", "trophies")
        self._draw_column_button(self._button_menu_rect(), "Menu", "menu")
        current_round = self.game_state.current_round
        if (current_round and current_round.tricks and
                current_round.phase == "tricks"):
            self._draw_column_button(self._button_last_trick_rect(),
                                     "Posledný štich", "last_trick")

        if not self.game_state.is_human_turn:
            return

        if self.pending_trump_card is not None:
            label = TRUMP_LABELS.get(self.pending_trump_suit, self.pending_trump_suit)

            if self.pending_trump_first_trick:
                # ← prvý štich: tromf sa ešte nedá hlásiť — neaktívne tlačidlo
                self._draw_button(self._button_trump_yes_rect(), f"Tromf: {label}",
                                  COLOR_BUTTON_SECONDARY, enabled=False)
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



    def _draw_button(self, rect: pygame.Rect, text: str, color: tuple,
                     enabled: bool = True):
        """Tlačidlo v strede stola (dražba, tromf, odhodenie) v štýle
        gui/ui_style.py: COLOR_BUTTON_PRIMARY = úroveň 1, inak úroveň 3."""
        ui_style.draw_button(self.canvas, rect, text, self.font_medium,
                             1 if color == COLOR_BUTTON_PRIMARY else 3,
                             rect.collidepoint(display.mouse_pos()),
                             enabled=enabled)

    def _draw_column_button(self, rect: pygame.Rect, text: str, icon_key: str):
        """Tlačidlo stĺpca vpravo dole (z CHUJ): tmavé zaoblené tlačidlo so
        zlatohnedým rámom, vľavo okrúhly medailón so zlatou ikonkou."""
        c = self.canvas
        hover = rect.collidepoint(display.mouse_pos())
        radius = COLUMN_RADIUS
        fill, highlight, border, text_color = ui_style.BTN_TIERS[3]
        c.overlay(rect.move(0, 3), (0, 0, 0, 100), border_radius=radius)
        c.overlay(rect, fill, border_radius=radius)
        top = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, rect.height // 2 - 2)
        c.overlay(top, (255, 214, 140, highlight), border_radius=radius - 2)
        if hover:
            c.overlay(rect, (255, 214, 140, 24), border_radius=radius)
            border, text_color = ui_style.BTN_BORDER_HOVER, ui_style.BTN_TEXT_HOVER
        c.rect(border, rect, width=2, border_radius=radius)

        # Medailón s ikonkou (mierne presahuje výšku tlačidla)
        mx, my = rect.x + rect.height // 2, rect.centery
        r = COLUMN_MEDALLION_R
        c.circle((0, 0, 0), (mx + 1, my + 3), r)
        c.circle((22, 14, 8), (mx, my), r)
        c.circle(ui_style.BTN_BORDER_HOVER if hover else ui_style.GOLD, (mx, my), r, width=2)
        c.circle((96, 70, 34), (mx, my), r - 4, width=1)
        icon = self._column_icons.get(icon_key)
        if icon is not None:
            c.blit(icon, icon.get_rect(center=(mx, my)))
        elif icon_key == "sort":
            self._draw_sort_icon(mx, my)

        surf = self.font_medium.render(text, True, text_color)
        c.blit(surf, surf.get_rect(midleft=(rect.x + COLUMN_TEXT_X, rect.centery)))

    def _draw_sort_icon(self, cx: int, cy: int):
        """Náhradná ikonka „Zoradiť karty“, kým nie je assets/graphics/
        sort.png: tri karty zoradené podľa veľkosti (zlaté obdĺžniky)."""
        c = self.canvas
        for i, h in enumerate((14, 20, 26)):
            x = cx - 13 + i * 9
            rect = pygame.Rect(x, cy + 13 - h, 8, h)
            c.rect(ui_style.GOLD, rect, border_radius=2)
            c.rect((120, 84, 30), rect, width=1, border_radius=2)

    def _draw_message(self):
        """Dočasná správa tesne nad kartami hráča — panel v štýle
        gui/ui_style.py."""
        if not self.message or pygame.time.get_ticks() >= self.message_timer:
            return
        surf = self.font_large.render(self.message, True, ui_style.BTN_TEXT_HOVER)
        msg_w = surf.get_width() + 60
        msg_h = surf.get_height() + 20
        cx = self.layout.table_center[0]
        msg_x = cx - msg_w // 2
        msg_y = self.layout.message_bottom_y - msg_h // 2
        if self.bid_slider.visible:
            # Panel navýšenia povinnosti siaha až k hláške — hláška nad neho
            msg_y = self.bid_slider.panel_y - msg_h - 16
        ui_style.draw_panel(self.canvas, (msg_x, msg_y, msg_w, msg_h))
        self.canvas.blit(surf, surf.get_rect(center=(cx, msg_y + msg_h // 2)))

    # ------------------------------------------------------------------
    # Rects — tlačidlá
    # ------------------------------------------------------------------

    # Rozloženie tlačidiel je v gui/layout.py (ukotvené podľa výšky okna).

    def _button_bid_rect(self) -> pygame.Rect:
        return self.layout.bid_rect()

    def _button_pass_rect(self) -> pygame.Rect:
        return self.layout.pass_rect()

    def _button_confirm_rect(self) -> pygame.Rect:
        return self.layout.confirm_rect()

    def _button_trump_yes_rect(self) -> pygame.Rect:
        return self.layout.trump_yes_rect()

    def _button_trump_no_rect(self) -> pygame.Rect:
        return self.layout.trump_no_rect()

    def _button_last_trick_rect(self) -> pygame.Rect:
        return self.layout.last_trick_rect()

    def _button_sort_rect(self) -> pygame.Rect:
        return self.layout.sort_rect()

    def _button_info_rect(self) -> pygame.Rect:
        return self.layout.info_rect()

    def _button_menu_rect(self) -> pygame.Rect:
        return self.layout.menu_rect()

    def _button_trophies_rect(self) -> pygame.Rect:
        return self.layout.trophies_rect()
    # ------------------------------------------------------------------
    # Pomocné metódy
    # ------------------------------------------------------------------
    def _auto_sort(self):
        self.game_state.players[self.game_state.human_index].hand.sort_hand()

    def _show_message(self, text: str, duration_ms: int = 2000):
        """Zobrazí správu na obrazovke."""
        self.message = text
        self.message_timer = pygame.time.get_ticks() + duration_ms

    def _check_trump_streak(self):
        """Skontroluje tromfový pár a esá human hráča pred prvým štichom kola."""
        if not self.achievement_tracker:
            return
        human_hand = self.game_state.players[self.game_state.human_index].hand
        has_pair = len(human_hand.get_available_trumps()) > 0
        has_ace = any(c.rank == "ace" for c in human_hand.cards)  # ← NOVÉ
        self.achievement_tracker.on_round_hand_ready(has_pair, has_ace)

    def __repr__(self) -> str:
        return f"Screen({SCREEN_WIDTH}x{self.H}, debug={self.debug})"