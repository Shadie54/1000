# main.py

import ctypes
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

import pygame
from game.game_state import GameState
from game.ai import AI
from gui.screen import Screen
from config import DEBUG_MODE


def main():
    # Vypne Windows DPI škálovanie — pygame bude vždy v skutočnom rozlíšení
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass  # Nefunguje na non-Windows systémoch
    # ------------------------------------------------------------------
    # 1. Nastavenie hráčov
    # ------------------------------------------------------------------
    player_names = ["Hráč", "Počítač 1", "Počítač 2"]
    human_index = 0     # index ľudského hráča

    game_state = GameState(player_names, human_index)

    # ------------------------------------------------------------------
    # 2. Nastavenie AI
    # ------------------------------------------------------------------
    # ai_players[i] = None ak je hráč človek, AI objekt ak je hráč AI
    ai_players = []
    for i, player in enumerate(game_state.players):
        if player.is_human:
            ai_players.append(None)
        else:
            ai_players.append(AI(player))

    # ------------------------------------------------------------------
    # 3. Spustenie obrazovky
    # ------------------------------------------------------------------
    screen = Screen(game_state, ai_players, debug=DEBUG_MODE)
    screen.run()


if __name__ == "__main__":
    main()