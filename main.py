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
from config import DEBUG_MODE


def main():
    pygame.init()

    # Vytvor okno
    import config
    window = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    pygame.display.set_caption("Tisíc")

    while True:
        # Zobraz menu
        menu = Menu(window)
        action = menu.run()

        if action == "quit":
            pygame.quit()
            sys.exit()

        elif action == "settings":
            # Placeholder — zatiaľ nič
            pass

        elif action == "new_game":
            # Spusti hru
            player_names = ["Hráč", "Počítač 1", "Počítač 2"]
            human_index = 0

            game_state = GameState(player_names, human_index)

            ai_players = []
            for i, player in enumerate(game_state.players):
                if player.is_human:
                    ai_players.append(None)
                else:
                    ai_players.append(AI(player, difficulty="hard"))

            screen = Screen(game_state, ai_players, debug=DEBUG_MODE)
            screen.run()
            # Po skončení hry sa vrátime do menu


if __name__ == "__main__":
    main()