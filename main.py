# main.py

import ctypes
import os, json
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

import sys
import pygame
from game.game_state import GameState
from game.ai import AI
from gui.screen import Screen
from gui.menu import Menu
from gui.settings_screen import SettingsScreen
from gui.game_over_screen import GameOverScreen
from config import DEBUG_MODE
from achievements.tracker import AchievementTracker
from gui.achievements_screen import AchievementsScreen


def _get_settings_path() -> str:
    docs = os.path.join(os.path.expanduser("~"), "Documents", "Tisic")
    os.makedirs(docs, exist_ok=True)
    return os.path.join(docs, "settings.json")

def _load_settings() -> dict:
    defaults = {
        "ai1_difficulty": "hard",
        "ai2_difficulty": "hard",
        "table_bg": "table.jpg"
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
              settings: dict = {}, achievement_tracker=None) -> tuple:
    screen = Screen(game_state, ai_players, debug=DEBUG_MODE, new_game=new_game,
                    table_bg=settings.get("table_bg", "table.jpg"),
                    achievement_tracker=achievement_tracker)
    result = screen.run()
    return result, game_state, ai_players


def main():
    pygame.init()
    pygame.mixer.init()

    import config
    window = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Tisíc")

    settings = _load_settings()

    active_game_state = None
    active_ai_players = None
    achievement_tracker = AchievementTracker()

    while True:
        menu = Menu(window, show_continue=active_game_state is not None)
        action = menu.run()

        if action == "quit":
            pygame.quit()
            sys.exit()

        elif action == "achievements":
            achievements_screen = AchievementsScreen(window)
            achievements_screen.run()

        elif action == "settings":
            settings_screen = SettingsScreen(window, settings)
            settings = settings_screen.run()
            _save_settings(settings)


        elif action == "continue" and active_game_state is not None:
            result, active_game_state, active_ai_players = _run_game(
                window, active_game_state, active_ai_players,
                new_game=False, settings=settings, achievement_tracker=achievement_tracker
            )
            if result == "game_over" and active_game_state.winner is not None:
                # ← NOVÉ: achievement tracking
                human_player = active_game_state.players[0]  # human_index je vždy 0
                human_won = active_game_state.winner == human_player
                opponent_scores = [
                    p.total_score for p in active_game_state.players if p != human_player
                ]
                achievement_tracker.on_game_finished(
                    human_won=human_won,
                    human_final_score=human_player.total_score,
                    opponent_scores=opponent_scores
                )

                game_over = GameOverScreen(
                    window,
                    active_game_state.players,
                    active_game_state.winner,
                    active_game_state.round_number
                )
                next_action = game_over.run()
                active_game_state = None
                active_ai_players = None
                # next_action == "menu" → späť do menu (while True pokračuje)
                # next_action == "new_game" → nová hra
                if next_action == "new_game":
                    achievement_tracker.reset_game()
                    active_game_state, active_ai_players = _create_game(settings)
                    result, active_game_state, active_ai_players = _run_game(
                    window, active_game_state, active_ai_players, settings=settings, achievement_tracker=achievement_tracker
                    )
            # result == "menu" → späť do menu (while True pokračuje)


        elif action == "new_game":
            achievement_tracker.reset_game()
            active_game_state, active_ai_players = _create_game(settings)
            result, active_game_state, active_ai_players = _run_game(
            window, active_game_state, active_ai_players, settings=settings, achievement_tracker=achievement_tracker
            )

            if result == "game_over" and active_game_state.winner is not None:
                # ← NOVÉ: achievement tracking
                human_player = active_game_state.players[0]  # human_index je vždy 0
                human_won = active_game_state.winner == human_player
                opponent_scores = [
                    p.total_score for p in active_game_state.players if p != human_player
                ]
                achievement_tracker.on_game_finished(
                    human_won=human_won,
                    human_final_score=human_player.total_score,
                    opponent_scores=opponent_scores
                )

                game_over = GameOverScreen(
                    window,
                    active_game_state.players,
                    active_game_state.winner,
                    active_game_state.round_number
                )
                next_action = game_over.run()
                active_game_state = None
                active_ai_players = None
                if next_action == "new_game":
                    achievement_tracker.reset_game()
                    active_game_state, active_ai_players = _create_game(settings)
                    result, active_game_state, active_ai_players = _run_game(
                    window, active_game_state, active_ai_players, settings=settings, achievement_tracker=achievement_tracker
                    )
            # result == "menu" → active_game_state ostáva pre pokračovanie


if __name__ == "__main__":
    main()