# main.py

import ctypes
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


def main():
    pygame.init()

    import config
    window = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Tisíc")

    settings = {
        "ai1_difficulty": "hard",
        "ai2_difficulty": "hard"
    }

    while True:
        menu = Menu(window)
        action = menu.run()

        if action == "quit":
            pygame.quit()
            sys.exit()

        elif action == "settings":
            settings_screen = SettingsScreen(window, settings)
            settings = settings_screen.run()

        elif action == "new_game":
            while True:
                # Vytvor hru
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
                            AI(player, difficulty=difficulty,
                               logger=game_state.logger)
                        )

                screen = Screen(game_state, ai_players, debug=DEBUG_MODE)
                result = screen.run()

                # Game Over obrazovka
                if result == "game_over":
                    game_over = GameOverScreen(
                        window,
                        game_state.players,
                        game_state.winner,
                        game_state.round_number
                    )
                    next_action = game_over.run()
                    if next_action == "menu":
                        break                   # ← späť do hlavného menu
                    # next_action == "new_game" → nová hra v cykle
                else:
                    break


if __name__ == "__main__":
    main()

if action == "quit":
    pygame.quit()
    sys.exit()