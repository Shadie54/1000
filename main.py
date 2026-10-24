# main.py

import ctypes
import os, json
try:
    # Per-Monitor DPI (Win 8.1+) — skutočné rozlíšenie aj pri zväčšení
    # Windows 125 % / 150 %; staršie Windows: celosystémové DPI.
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import sys

# Pracovný priečinok = priečinok s hrou. Cesty k obrázkom a zvukom sú
# relatívne ("assets/..."): v exe (PyInstaller onedir) ležia v _internal\
# (sys._MEIPASS), pri spustení zo zdrojákov vedľa main.py. Bez toho by
# hra spustená zo zástupcu alebo iného priečinka nenašla assets.
if getattr(sys, "frozen", False):
    os.chdir(sys._MEIPASS)
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

import pygame
from game.game_state import GameState
from game.ai import AI
from gui.screen import Screen
from gui.menu import Menu
from gui.settings_screen import SettingsScreen
from gui.game_over_screen import GameOverScreen
from config import DEBUG_MODE, ANIMATION_SPEED_DEFAULT, PLAY_DIRECTION_DEFAULT
from achievements.tracker import AchievementTracker
from gui.achievements_screen import AchievementsScreen
from gui import display
from game import savegame


def _get_settings_path() -> str:
    docs = os.path.join(os.path.expanduser("~"), "Documents", "Tisic")
    os.makedirs(docs, exist_ok=True)
    return os.path.join(docs, "settings.json")

def _load_settings() -> dict:
    defaults = {
        "ai1_difficulty": "hard",
        "ai2_difficulty": "hard",
        "table_bg": "table.jpg",
        "animation_speed": ANIMATION_SPEED_DEFAULT,
        "play_direction": PLAY_DIRECTION_DEFAULT,
    }
    try:
        with open(_get_settings_path(), "r") as f:
            loaded = json.load(f)
            defaults.update(loaded)
            return defaults
    except (FileNotFoundError, json.JSONDecodeError):
        return defaults

def _save_settings(settings: dict):
    try:
        with open(_get_settings_path(), "w") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass

def _create_game(settings: dict) -> tuple:
    player_names = ["Hráč", "Počítač 1", "Počítač 2"]
    human_index = 0
    game_state = GameState(player_names, human_index)
    ai_players = []
    for i, player in enumerate(game_state.players):
        if player.is_human:
            ai_players.append(None)
        else:
            difficulty = (
                settings["ai1_difficulty"] if i == 1
                else settings["ai2_difficulty"]
            )
            ai_players.append(
                AI(player, difficulty=difficulty, logger=game_state.logger)
            )
    return game_state, ai_players


def _run_game(window, game_state, ai_players, new_game: bool = True,
              settings: dict = {}, achievement_tracker=None,
              restore_ui: dict | None = None) -> tuple:
    """Spustí hernú obrazovku. Vráti (výsledok, stav obrazovky pri odchode)."""
    screen = Screen(game_state, ai_players, debug=DEBUG_MODE, new_game=new_game,
                    table_bg=settings.get("table_bg", "table.jpg"),
                    achievement_tracker=achievement_tracker,
                    animation_speed=settings.get("animation_speed",
                                                 ANIMATION_SPEED_DEFAULT),
                    restore_ui=restore_ui,
                    clockwise=settings.get("play_direction",
                                           PLAY_DIRECTION_DEFAULT) != "ccw")
    result = screen.run()
    return result, screen.exit_ui


def _show_game_over(window, game_state, achievement_tracker) -> str:
    """Trofeje za dohratú hru + obrazovka konca hry. Vráti "menu"/"new_game"."""
    human_player = game_state.players[game_state.human_index]
    human_won = game_state.winner == human_player
    opponent_scores = [
        p.total_score for p in game_state.players if p != human_player
    ]
    achievement_tracker.on_game_finished(
        human_won=human_won,
        human_final_score=human_player.total_score,
        opponent_scores=opponent_scores
    )
    game_over = GameOverScreen(
        window,
        game_state.players,
        game_state.winner,
        game_state.round_number
    )
    return game_over.run()


def main():
    pygame.init()
    pygame.mixer.init()

    # Okno (režim, rozlíšenie, ikonka, titulok) otvára výhradne
    # gui/display.py — podľa príkazového riadka (--resolution 1366x768
    # --windowed, --safe), premennej TISIC_RESOLUTION, settings.json alebo
    # natívneho rozlíšenia monitora.
    window = display.get_surface()

    settings = _load_settings()

    # Rozohratá hra v tomto spustení (alebo načítaná zo savegame.json)
    active_game_state = None
    active_ai_players = None
    active_ui: dict = {}
    achievement_tracker = AchievementTracker()

    while True:
        # "Pokračovať" sa ponúka aj vtedy, keď v tomto spustení žiadna hra
        # nebeží, ale na disku čaká rozohratá z minula (game/savegame.py).
        menu = Menu(window, show_continue=(active_game_state is not None
                                           or savegame.has_save()))
        action = menu.run()

        if action == "quit":
            pygame.quit()
            sys.exit()

        elif action == "achievements":
            achievements_screen = AchievementsScreen(window)
            achievements_screen.run()
            continue

        elif action == "settings":
            settings_screen = SettingsScreen(window, settings)
            settings = settings_screen.run()
            _save_settings(settings)
            # Nastavenia mohli prepnúť zobrazenie (Zobrazenie → Použiť)
            window = display.get_surface()
            continue

        elif action == "continue":
            if active_game_state is None:
                loaded = savegame.load_game(settings, achievement_tracker)
                if loaded is None:
                    # Poškodená alebo zmiznutá uložená hra — savegame ju
                    # zmazal, menu už "Pokračovať" neponúkne.
                    continue
                active_game_state, active_ai_players, active_ui = loaded
            start_new = False

        elif action == "new_game":
            # Nová hra nahrádza rozohratú (aj tú uloženú z minula)
            savegame.delete_save()
            start_new = True

        else:
            continue

        # Hra — opakuje sa, ak hráč na obrazovke konca hry zvolí Nová hra
        while True:
            if start_new:
                achievement_tracker.reset_game()
                active_game_state, active_ai_players = _create_game(settings)
                active_ui = {}
            result, active_ui = _run_game(
                window, active_game_state, active_ai_players,
                new_game=start_new, settings=settings,
                achievement_tracker=achievement_tracker, restore_ui=active_ui
            )
            if result != "game_over" or active_game_state.winner is None:
                # Odchod do menu — hra ostáva rozohratá (a je uložená)
                break
            next_action = _show_game_over(window, active_game_state,
                                          achievement_tracker)
            active_game_state = None
            active_ai_players = None
            active_ui = {}
            if next_action != "new_game":
                break
            start_new = True


if __name__ == "__main__":
    main()