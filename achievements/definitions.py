# achievements/definitions.py

"""
Definície všetkých achievementov v hre.
Každý achievement má:
- id: unikátny identifikátor (string)
- name: zobrazovaný názov
- description: popis ako ho získať
- tier: voliteľné (pre viacstupňové achievementy) — napr. 1, 2, 3
- group: voliteľné — zoskupenie stupňovaných achievementov pod jeden vizuálny celok
"""

ACHIEVEMENTS = [

    # 🏆 Základné míľniky
    {"id": "first_win", "name": "Začíname", "description": "Vyhraj svoju prvú hru.", "group": "wins_milestone", "tier": 1, "hidden": True},
    {"id": "wins_10", "name": "Rozbehnutý", "description": "Vyhraj 10 hier.", "group": "wins_milestone", "tier": 2, "hidden": True},
    {"id": "wins_50", "name": "Stará škola", "description": "Vyhraj 50 hier.", "group": "wins_milestone", "tier": 3, "hidden": True},
    {"id": "wins_100", "name": "Legenda", "description": "Vyhraj 100 hier.", "group": "wins_milestone", "tier": 4, "hidden": True},

    # 🎯 Dražba
    {"id": "bid_200", "name": "Odvážny pokus", "description": "Vydraž 200 a splň povinnosť.", "group": "bid_tier", "tier": 1, "hidden": True},
    {"id": "bid_250", "name": "Veľké oči", "description": "Vydraž 250 a splň povinnosť.", "group": "bid_tier", "tier": 2, "hidden": True},
    {"id": "bid_300", "name": "Podržte mi pivo", "description": "Vydraž 300 a splň povinnosť.", "group": "bid_tier", "tier": 3, "hidden": True},
    {"id": "modest_winner", "name": "Skromný víťaz", "description": "Splň minimálnu povinnosť 50.", "hidden": True},
    {"id": "barely_made_it", "name": "S odretými ušami", "description": "Splň tesne povinnosť 50 - bez jediného bodu navyše.", "hidden": True},
    {"id": "passivist", "name": "Kto mlčí, vyhráva", "description": "Vyhraj celú hru bez toho, aby si čo i len raz vydražil."},

    # 🃏 Tromfy
    {"id": "first_trump", "name": "Poslušne hlásim", "description": "Zahlás svoj prvý tromf.", "hidden": True},
    {"id": "trump_king_2", "name": "Tromfový kráľ I.", "description": "Zahlás 2 rôzne tromfy v jednom kole.", "group": "trump_king", "tier": 1, "hidden": True},
    {"id": "trump_king_3", "name": "Tromfový kráľ II.", "description": "Zahlás 3 rôzne tromfy v jednom kole.", "group": "trump_king", "tier": 2, "hidden": True},
    {"id": "silent_watcher_1", "name": "Tichý pozorovateľ I.", "description": "Nebi sa o talon, ak máš 1 tromf na ruke.", "group": "silent_watcher", "tier": 1, "hidden": True},
    {"id": "silent_watcher_2", "name": "Tichý pozorovateľ II.", "description": "Nebi sa o talon, ak máš 2 tromfy na ruke", "group": "silent_watcher", "tier": 2, "hidden": True},
    {"id": "silent_watcher_3", "name": "Tichý pozorovateľ III.", "description": "Nebi sa o talon, ak máš 3 tromfy na ruke.", "group": "silent_watcher", "tier": 3, "hidden": True},
    {"id": "trump_override", "name": "Karta sa obrátila", "description": "Prehlás súperov tromf svojim vlastným tromfom.", "hidden": True},
    {"id": "last_word", "name": "Posledné slovo", "description": "Zahlás tromf ako tretí (alebo ďalší) v poradí v jednom kole.", "hidden": True},
    {"id": "last_chance_trump", "name": "Lepšie neskoro ako nikdy", "description": "Zahlás tromf až v poslednom (9.) štichu.", "hidden": True},
    {"id": "no_safety_net", "name": "Bez poistky", "description": "Zahlás tromf bez toho, aby si mal čo i len jedno eso na ruke.", "hidden": True},
    {"id": "too_late_now", "name": "Už bolo na čase", "description": "Prežil si 7 kôl bez tromfového páru.", "hidden": True},
    {"id": "pretty_but_useless", "name": "Hláška do koša", "description": "Zahoď tromfovú hlášku do talonu.", "hidden": True},

    # ⚔️ Štichy
    {"id": "dominance", "name": "Dominancia", "description": "Vyhraj všetkých 10 štichov v jednom kole.", "hidden": True},
    {"id": "greedy", "name": "Každý bod sa počíta", "description": "Nazbieraj 120 bodov v jednom kole (bez hlášiek).", "hidden": True},
    {"id": "absolute_rule_1", "name": "Absolútna nadvláda I.", "description": "Vyhraj všetkých 10 štichov a zahlás 1 tromf v tom istom kole.", "group": "absolute_rule", "tier": 1, "hidden": True},
    {"id": "absolute_rule_2", "name": "Absolútna nadvláda II.", "description": "Vyhraj všetkých 10 štichov a zahlás 2 tromfy v tom istom kole.", "group": "absolute_rule", "tier": 2, "hidden": True},
    {"id": "comeback", "name": "Fénix", "description": "Vyhraj hru po tom, čo si zaostal o viac ako 200 bodov", "hidden": True},
    {"id": "close_win", "name": "Presná tisícka", "description": "Vyhraj hru s presne 1000 bodmi.", "hidden": True},

    # 😈 Proti AI
    {"id": "unbeatable_bronze", "name": "Neporaziteľný — Bronz", "description": "Vyhraj 3 hry za sebou.", "group": "unbeatable", "tier": 1, "hidden": True},
    {"id": "unbeatable_silver", "name": "Neporaziteľný — Striebro", "description": "Vyhraj 5 hier za sebou.", "group": "unbeatable", "tier": 2, "hidden": True},
    {"id": "unbeatable_gold", "name": "Neporaziteľný — Zlato", "description": "Vyhraj 10 hier za sebou.", "group": "unbeatable", "tier": 3, "hidden": True},

    # 🎭 Humorné
    {"id": "unlucky", "name": "Smoliar", "description": "Prehraj hru so stratou do 50 bodov od víťaza.", "hidden": True},
    {"id": "discreet", "name": "Trikrát a dosť", "description": "Zahlás najviac 3 tromfy a vyhraj hru"},
    { "id": "lucky_pickup", "name": "Šťastný nákup", "description": "Nájdi v talone 2 ESÁ, DESIATKY alebo HLÁŠKU.", "hidden": True},

]

def get_tier_name(achievement_id: str) -> str:
    """Vráti 'bronze'/'silver'/'gold' podľa pozície v skupine, alebo 'gold' ak nie je súčasťou skupiny."""
    achievement = get_achievement(achievement_id)
    if not achievement or "group" not in achievement:
        return "gold"

    group = achievement["group"]
    group_items = [a for a in ACHIEVEMENTS if a.get("group") == group]
    index = next((i for i, a in enumerate(group_items) if a["id"] == achievement_id), 0)
    total = len(group_items)

    if total <= 1:
        return "gold"
    if total == 2:
        return "silver" if index == 0 else "gold"
    if index == 0:
        return "bronze"
    if index == total - 1:
        return "gold"
    return "silver"

def get_achievement(achievement_id: str) -> dict | None:
    """Vráti definíciu achievementu podľa ID."""
    for a in ACHIEVEMENTS:
        if a["id"] == achievement_id:
            return a
    return None


def get_all_ids() -> list[str]:
    """Vráti zoznam všetkých ID achievementov."""
    return [a["id"] for a in ACHIEVEMENTS]