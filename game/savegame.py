# game/savegame.py
#
# Uloženie a obnova rozohratej hry — aby sa dala dohrať aj po zatvorení a
# znovuotvorení programu (prevzatý nápad z hry CHUJ).
#
# Princíp: na rozdiel od CHUJ (kde sa kolo prehráva od rozdania, lebo
# pamäť AI sa nedá vierohodne obnoviť) je celý stav 1000 čisté dáta —
# karty, dražba, štichy, skóre aj pamäť AI. Ukladá sa preto priamo
# "fotka" stavu. Screen pred uložením dorovná prechodné stavy (animácie,
# kompletný ale nezozbieraný štich, odkrytý talon) — pozri
# Screen._settle_for_save().
#
# Súbor: Documents/Tisic/savegame.json, vedľa settings.json.

import json
import os

from game.ai import AI
from game.bidding import Bidding
from game.card import Card
from game.game_state import GameState
from game.hand import Hand
from game.round import Round
from game.trick import Trick

SAVE_VERSION = 1


def save_path() -> str:
    # Počíta sa pri každom volaní — testy presmerúvajú domovský priečinok.
    return os.path.join(os.path.expanduser("~"), "Documents", "Tisic",
                        "savegame.json")


# ----------------------------------------------------------------------
# Karty
# ----------------------------------------------------------------------

def _c(card: Card) -> str:
    return f"{card.suit}:{card.rank}"


def _card(text: str) -> Card:
    suit, rank = text.split(":")
    return Card(suit, rank)


def _cards(cards) -> list[str]:
    return [_c(c) for c in cards]


def _plays(played) -> list:
    return [[i, _c(c)] for i, c in played]


def _plays_back(data) -> list:
    return [(i, _card(c)) for i, c in data]


# ----------------------------------------------------------------------
# Uloženie
# ----------------------------------------------------------------------

def _memory_to_dict(m) -> dict:
    return {
        # množiny → zoradené zoznamy (stabilný súbor pri každom uložení)
        "played_cards": sorted(_cards(m.played_cards)),
        "seen_cards": sorted(_cards(m.seen_cards)),
        "void_suits": {str(k): sorted(v) for k, v in m.void_suits.items()},
        "trick_winners": {str(k): v for k, v in m.trick_winners.items()},
        "declared_trumps": dict(m.declared_trumps),
        "current_trump": m.current_trump,
        "trick_history": [[leader, _plays(played)]
                          for leader, played in m.trick_history],
        "bidder_index": m.bidder_index,
        "bid_amount": m.bid_amount,
        "claim_lead_active": m.claim_lead_active,
        "first_trick_declarer": m.first_trick_declarer,
    }


def _tracker_to_dict(tracker) -> dict:
    """Stav trofejí viazaný na rozohratú hru/kolo (game_*, round_*).
    Odomknuté trofeje sa ukladajú zvlášť (achievements.json)."""
    out = {}
    for key, value in vars(tracker).items():
        if not key.startswith(("game_", "round_")):
            continue
        if isinstance(value, set):
            out[key] = {"set": sorted(value)}
        else:
            out[key] = value
    return out


def _trick_to_dict(t: Trick) -> dict:
    return {"leader": t.leader_index, "trump": t.trump_suit,
            "played": _plays(t.played_cards)}


def _round_to_dict(rnd: Round) -> dict | None:
    if rnd is None or rnd.phase in ("dealing", "scoring", "done"):
        # Kolo, ktoré skončilo (alebo nezačalo) — po načítaní sa rozdá ďalšie
        return None
    b = rnd.bidding
    return {
        "obligation_index": rnd.obligation_index,
        "phase": rnd.phase,
        "talon": _cards(rnd.talon),
        "bidding": None if b is None else {
            "current_bid": b.current_bid,
            "highest_bidder_index": b.highest_bidder_index,
            "active": list(b.active),
        },
        "tricks": [_trick_to_dict(t) for t in rnd.tricks],
        "current_trick": (None if rnd.current_trick is None
                          else _trick_to_dict(rnd.current_trick)),
        "trump_suit": rnd.trump_suit,
        "current_leader_index": rnd.current_leader_index,
        "trick_number": rnd.trick_number,
        "trump_declarer": rnd.trump_declarer,
        "declared_in_first_trick": rnd.declared_in_first_trick,
    }


def save_game(game_state: GameState, ai_players: list, tracker=None,
              ui_state: dict | None = None) -> bool:
    """Uloží rozohratú hru. Vracia True pri úspechu — zlyhanie zápisu
    nesmie zhodiť hru, hráč len príde o možnosť pokračovať.
    Dohratú hru (game_over) neukladá."""
    if game_state is None or game_state.phase == "game_over":
        return False

    data = {
        "version": SAVE_VERSION,
        "human_index": game_state.human_index,
        "players": [
            {
                "name": p.name,
                "hand": _cards(p.hand.cards),
                "total_score": p.total_score,
                "tricks_points": p.tricks_points,
                "declared_trumps_points": p.declared_trumps_points,
                "bid": p.bid,
                "is_bidder": p.is_bidder,
                "has_obligation": p.has_obligation,
                "declared_trumps": list(p.declared_trumps),
            }
            for p in game_state.players
        ],
        "obligation_index": game_state.obligation_index,
        "first_trick_trump": game_state.first_trick_trump,
        "round_number": game_state.round_number,
        "round_history": game_state.round_history,
        "round": _round_to_dict(game_state.current_round),
        "ai": [
            None if ai is None else {"difficulty": ai.difficulty,
                                     "memory": _memory_to_dict(ai.memory)}
            for ai in ai_players
        ],
        "tracker": None if tracker is None else _tracker_to_dict(tracker),
        "log": {"entries": list(game_state.logger.entries),
                "round_number": game_state.logger.round_number},
        "ui": ui_state or {},
    }

    path = save_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)      # nikdy nenecháme rozpísaný súbor
        return True
    except (OSError, TypeError, ValueError):
        return False


def has_save() -> bool:
    return os.path.exists(save_path())


def delete_save():
    try:
        os.remove(save_path())
    except OSError:
        pass


# ----------------------------------------------------------------------
# Načítanie
# ----------------------------------------------------------------------

def load_game(settings: dict | None = None, tracker=None):
    """Obnoví uloženú hru. Vracia (game_state, ai_players, ui_state),
    alebo None, ak uložená hra neexistuje, je poškodená alebo sa ju
    nepodarí obnoviť — vtedy sa súbor zmaže, nech menu donekonečna
    neponúka "Pokračovať", ktoré vždy zlyhá."""
    try:
        with open(save_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        delete_save()
        return None
    try:
        return _rebuild(data, tracker)
    except Exception:
        delete_save()
        return None


def _memory_from_dict(m, d: dict):
    m.played_cards = {_card(c) for c in d["played_cards"]}
    m.seen_cards = {_card(c) for c in d["seen_cards"]}
    m.void_suits = {int(k): set(v) for k, v in d["void_suits"].items()}
    m.trick_winners = {int(k): v for k, v in d["trick_winners"].items()}
    m.declared_trumps = dict(d["declared_trumps"])
    m.current_trump = d["current_trump"]
    m.trick_history = [(leader, _plays_back(played))
                       for leader, played in d["trick_history"]]
    m.bidder_index = d["bidder_index"]
    m.bid_amount = d["bid_amount"]
    m.claim_lead_active = d["claim_lead_active"]
    m.first_trick_declarer = d.get("first_trick_declarer")


def _trick_from_dict(players, d: dict) -> Trick:
    t = Trick(players, d["leader"], d["trump"])
    t.played_cards = _plays_back(d["played"])
    return t


def _rebuild(data: dict, tracker=None):
    if data.get("version") != SAVE_VERSION:
        raise ValueError("neznáma verzia uloženej hry")

    pdata = data["players"]
    game_state = GameState([p["name"] for p in pdata], data["human_index"])
    for player, saved in zip(game_state.players, pdata):
        player.hand = Hand()
        player.hand.add_cards([_card(c) for c in saved["hand"]])
        player.total_score = saved["total_score"]
        player.tricks_points = saved["tricks_points"]
        player.declared_trumps_points = saved["declared_trumps_points"]
        player.bid = saved["bid"]
        player.is_bidder = saved["is_bidder"]
        player.has_obligation = saved["has_obligation"]
        player.declared_trumps = list(saved["declared_trumps"])

    game_state.obligation_index = data["obligation_index"]
    game_state.first_trick_trump = bool(data.get("first_trick_trump", False))
    game_state.round_number = data["round_number"]
    game_state.round_history = data.get("round_history", [])
    game_state.phase = "playing"

    log = data.get("log") or {}
    game_state.logger.entries = list(log.get("entries", []))
    game_state.logger.round_number = log.get("round_number", 0)

    rd = data.get("round")
    if rd is not None:
        players = game_state.players
        # Round() by v konštruktore nič nerozdal — karty sú už na rukách
        rnd = Round(players, rd["obligation_index"], game_state.first_trick_trump)
        rnd.declared_in_first_trick = bool(rd.get("declared_in_first_trick", False))
        rnd.phase = rd["phase"]
        rnd.talon = [_card(c) for c in rd["talon"]]
        bd = rd["bidding"]
        if bd is not None:
            # Bidding.__init__ nastaví povinnosť hráčovi — hodnoty hráčov
            # (bid, has_obligation) potom prepíšeme uloženými.
            b = Bidding(players, rd["obligation_index"])
            b.current_bid = bd["current_bid"]
            b.highest_bidder_index = bd["highest_bidder_index"]
            b.active = list(bd["active"])
            rnd.bidding = b
            for player, saved in zip(players, pdata):
                player.bid = saved["bid"]
                player.has_obligation = saved["has_obligation"]
        rnd.tricks = [_trick_from_dict(players, t) for t in rd["tricks"]]
        rnd.current_trick = (None if rd["current_trick"] is None
                             else _trick_from_dict(players, rd["current_trick"]))
        rnd.trump_suit = rd["trump_suit"]
        rnd.current_leader_index = rd["current_leader_index"]
        rnd.trick_number = rd["trick_number"]
        rnd.trump_declarer = rd["trump_declarer"]
        game_state.current_round = rnd

    ai_players = []
    for i, ad in enumerate(data["ai"]):
        if ad is None:
            ai_players.append(None)
            continue
        ai = AI(game_state.players[i], difficulty=ad["difficulty"],
                logger=game_state.logger,
                first_trick_trump=game_state.first_trick_trump)
        _memory_from_dict(ai.memory, ad["memory"])
        ai_players.append(ai)

    if tracker is not None and data.get("tracker"):
        tracker.reset_game()
        tracker.reset_round()
        for key, value in data["tracker"].items():
            if isinstance(value, dict) and "set" in value:
                value = set(value["set"])
            setattr(tracker, key, value)

    return game_state, ai_players, data.get("ui") or {}
