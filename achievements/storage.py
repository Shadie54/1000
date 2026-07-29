# achievements/storage.py

import json
import os
from achievements.definitions import get_all_ids


def _get_achievements_path() -> str:
    """Vráti cestu k achievements.json v dokumentoch (vedľa settings.json)."""
    docs = os.path.join(os.path.expanduser("~"), "Documents", "Tisic")
    os.makedirs(docs, exist_ok=True)
    return os.path.join(docs, "achievements.json")


def _default_data() -> dict:
    """Vytvorí prázdnu štruktúru dát."""
    return {
        "unlocked": {aid: False for aid in get_all_ids()},
        "stats": {
            "wins_total": 0,
            "games_played": 0,
            "win_streak_current": 0,
            "win_streak_best": 0,
        }
    }


def load_achievements() -> dict:
    """Načíta achievementy zo súboru, prípadne vytvorí default."""
    path = _get_achievements_path()
    defaults = _default_data()

    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        # Zlúč s defaultmi — ošetrí nové achievementy pridané neskôr
        merged_unlocked = defaults["unlocked"].copy()
        merged_unlocked.update(loaded.get("unlocked", {}))

        merged_stats = defaults["stats"].copy()
        merged_stats.update(loaded.get("stats", {}))

        return {
            "unlocked": merged_unlocked,
            "stats": merged_stats,
        }
    except (FileNotFoundError, json.JSONDecodeError):
        return defaults


def save_achievements(data: dict):
    """Uloží achievementy do súboru."""
    path = _get_achievements_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass