# game/ai_strategy.py

from game.card import Card
from game.ai_memory import AIMemory
from game.ai_evaluator import AIEvaluator
from game.trick import Trick
from game import ai_strategies_const as SC
from config import SUITS, RANKS, TRUMP_POINTS


# Hláška bez esa (návrh usera 2026-10-29): bez esa sa AI v klasike
# k vynášaniu a hláseniu väčšinou nedostane, preto sa hláška do dražby
# nepočíta — jedine ak AI „riskuje“, že eso získa z talónu (pravdepodobnosť
# eso v 2-kartovom talóne ≈ 34 %). Podiel rúk, pri ktorých AI riskuje —
# ťažký počítač neriskuje nikdy (simulácia: každé riskovanie stráca body),
# stredný občas, ako človek:
TALON_ACE_RISK = {"hard": 0.0, "medium": 0.25}

# Variant „tromf aj v 1. štichu“: slabé ruky na hlásenie v 1. štichu
# (len 2 tromfy; 3 tromfy bez desiatky — splnené len 43–54 %) — podiel
# rúk, s ktorými AI aj tak hlási:
FIRST_TRICK_WEAK_RISK = {"hard": 0.0, "medium": 0.25}


def _hand_share(hand: list[Card]) -> float:
    """Deterministické „náhodné“ číslo 0…1 z karát na ruke — rozhodnutie
    sa počas kola nemení a nezávisí od generátora náhody (savegame)."""
    key = sum((SUITS.index(c.suit) * 8 + RANKS.index(c.rank) + 1) ** 2
              for c in hand)
    return (key * 37 % 100) / 100


class AIStrategy:
    def __init__(self, memory: AIMemory, evaluator: AIEvaluator,
                 difficulty: str = "hard",
                 logger=None, player_name: str = "AI",
                 first_trick_trump: bool = False):
        # first_trick_trump — variant pravidiel: víťaz dražby smie hlásiť
        # tromf už v 1. štichu, musí však za kolo zobrať aspoň jeden štich
        self.first_trick_trump = first_trick_trump
        self.memory = memory
        self.evaluator = evaluator
        self.difficulty = difficulty
        self.logger = logger
        self.player_name = player_name
        # Fáza pre započítanie hlášok do odhadu: "bid" (dražba) / "talon"
        self._phase = "bid"
        evaluator.pair_filter = self._countable_pairs

    def _log(self, strategy: str, details: str = ""):
        """Zaloguje stratégiu ak je logger dostupný."""
        if self.logger:
            self.logger.log_strategy(self.player_name, strategy, details)

    # ------------------------------------------------------------------
    # Bidding
    # ------------------------------------------------------------------

    def decide_bid(self, hand: list[Card], current_bid: int,
                   has_obligation: bool, trump_suit: str | None) -> int | None:
        if self.difficulty == "easy":
            return None
        self._phase = "bid"

        # S14 — SECURE_TRUMP_BID
        if self.difficulty == "hard":
            secure_bid = self._check_secure_trump_bid(hand, current_bid)
            if secure_bid:
                self._log(SC.SECURE_TRUMP_BID,
                          f"plonkový tromf → bid {secure_bid}")
                return secure_bid

        # S27 — PASSIVE_BID
        if self.difficulty == "hard" and not has_obligation:
            if self._check_passive_bid(hand, current_bid):
                self._log(SC.PASSIVE_BID, "2+ esá + tromfy → pasuj")
                self.memory.claim_lead_active = True  # ← aktivuj S28
                return None

        # S11 — PASS_FOR_TRUMP
        # Pri variante "tromf v 1. štichu" netreba pasovať kvôli hláške —
        # víťaz dražby ju zahlási hneď (ak má šancu zobrať aspoň jeden štich).
        skip_pass = (self.first_trick_trump
                     and self._first_trick_trump_suit(hand, bid_limit=None) is not None)
        if skip_pass and self.difficulty == "hard":
            self._log(SC.FIRST_TRICK_BID, "hláška sa dá zahlásiť v 1. štichu")
        if self.difficulty == "hard" and not skip_pass:
            if self.evaluator.should_pass_for_trumps(hand, current_bid):
                if not has_obligation:
                    self._log(SC.PASS_FOR_TRUMP,
                              "silné hlášky, slabé štichy → pas")
                    return None

        # S16 — LONG_SUIT_BID log
        long_bonus = self.evaluator.get_long_suit_bid_bonus(hand)
        if long_bonus > 0:
            self._log(SC.LONG_SUIT_BID, f"dlhá farba → bonus +{long_bonus}")

        # S10 — BID_ESTIMATE
        estimate = self.evaluator.calculate_bid_estimate(hand, trump_suit)
        if estimate >= current_bid + 10:
            self._log(SC.BID_ESTIMATE,
                      f"odhad={estimate} → bid {current_bid + 10}")
            return current_bid + 10

        if has_obligation:
            return None

        return None

    def _check_secure_trump_bid(self, hand: list[Card],
                                 current_bid: int) -> int | None:
        """
        S14 — Skontroluje či má AI plonkový tromf + eso.
        Vracia odporúčaný bid alebo None.
        """
        for suit in SUITS:
            has_over = any(c.suit == suit and c.rank == "over" for c in hand)
            has_king = any(c.suit == suit and c.rank == "king" for c in hand)
            if not (has_over and has_king):
                continue

            # Plonkový tromf = len 2 karty tejto farby
            suit_cards = [c for c in hand if c.suit == suit]
            if len(suit_cards) != 2:
                continue

            # Musí mať eso (akejkoľvek farby)
            has_ace = any(c.rank == "ace" for c in hand)
            if not has_ace:
                continue

            # Odporúčaný bid = eso(11) + tromf hodnota
            trump_val = TRUMP_POINTS[suit]
            recommended = ((11 + trump_val) // 10) * 10  # zaokrúhli na desiatky

            if recommended >= current_bid + 10:
                return current_bid + 10

        return None

    # ------------------------------------------------------------------
    # Navýšenie po talóne
    # ------------------------------------------------------------------

    def decide_raise_after_talon(self, hand: list[Card],
                                  current_bid: int,
                                  trump_suit: str | None) -> int | None:
        if self.difficulty == "easy":
            return None
        self._phase = "talon"

        result = self.evaluator.should_raise_after_talon(
            hand, current_bid, trump_suit
        )
        # Variant: hlásenie v 1. štichu je dovolené len s povinnosťou aspoň
        # hláška + 10 — navýš na túto hranicu, ak sa hláška inak nedá
        # zahlásiť (bez istého štichu) a odhad ruky ju unesie.
        if self.first_trick_trump and self.difficulty != "easy":
            from game.round import first_trick_min_bid
            bid = result or current_bid
            guaranteed = self.evaluator.get_guaranteed_tricks(hand, trump_suit)
            suit = self._first_trick_trump_suit(hand, bid_limit=None)
            if suit and not guaranteed:
                need = first_trick_min_bid(suit)
                estimate = self.evaluator.calculate_bid_estimate(hand, trump_suit)
                if bid < need <= estimate:
                    self._log(SC.FIRST_TRICK_BID,
                              f"navýšenie na {need} kvôli hláseniu v 1. štichu")
                    result = need
        if result:
            self._log(SC.RAISE_AFTER_TALON,
                     f"po talóne navýšenie na {result}")
        return result

    # ------------------------------------------------------------------
    # Zahadzovanie
    # ------------------------------------------------------------------

    def decide_discard(self, hand: list[Card]) -> list[Card]:
        if self.difficulty == "easy":
            candidates = [c for c in hand if c.rank not in ("ace", "ten")]
            return candidates[:2]

        candidates = self.evaluator.get_discard_candidates(hand)
        result = candidates[:2]
        self._log(SC.SMART_DISCARD,
                 f"zahodí: {[str(c) for c in result]}")
        return result

    # ------------------------------------------------------------------
    # Tromfy
    # ------------------------------------------------------------------

    def decide_trump(self, hand: list[Card], trick_number: int,
                     is_leader: bool, current_trump: str | None) -> str | None:
        if self.difficulty == "easy":
            return None
        if not is_leader:
            return None
        if trick_number == 0 and not self.first_trick_trump:
            return None

        # Deaktivuj S28 keď sme leader ← pridané
        if self.memory.claim_lead_active:
            self.memory.claim_lead_active = False
            self._log(SC.CLAIM_LEAD, "lead získaný → deaktivujem S28")

        available = [
            suit for suit in SUITS
            if any(c.suit == suit and c.rank == "over" for c in hand)
               and any(c.suit == suit and c.rank == "king" for c in hand)
        ]
        if not available:
            return None

        if self.difficulty == "medium":
            best = max(available, key=lambda s: TRUMP_POINTS[s])
            self._log(SC.TRUMP_DECLARE, f"tromf: {best}")
            return best

        best = self._choose_best_trump(hand, available, current_trump)
        if best:
            self._log(SC.TRUMP_DECLARE,
                      f"tromf: {best} ({TRUMP_POINTS[best]} bodov)")
        return best

    def _choose_best_trump(self, hand: list[Card], available: list[str],
                            current_trump: str | None) -> str | None:
        best_suit = None
        best_score = -1

        for suit in available:
            score = TRUMP_POINTS[suit]
            has_ace = any(c.suit == suit and c.rank == "ace" for c in hand)
            if has_ace:
                score += 20
            suit_count = sum(1 for c in hand if c.suit == suit)
            score += suit_count * 5
            opponents_void = all(
                self.memory.is_suit_void(i, suit)
                for i in range(3)
                if i != self.memory.player_index
            )
            if opponents_void:
                score += 30
            if score > best_score:
                best_score = score
                best_suit = suit

        return best_suit

    # ------------------------------------------------------------------
    # Výber karty
    # ------------------------------------------------------------------

    def decide_card(self, hand: list[Card], playable: list[Card],
                    trick: Trick, trick_number: int,
                    player_index: int) -> Card:
        if self.difficulty == "easy":
            import random
            return random.choice(playable)

        is_leader = (trick.leader_index == player_index
                     and len(trick.played_cards) == 0)

        if is_leader:
            return self._decide_as_leader(hand, playable, trick_number)
        else:
            return self._decide_as_follower(hand, playable, trick)

    # ------------------------------------------------------------------
    # Výber karty — leader
    # ------------------------------------------------------------------

    def _decide_as_leader(self, hand: list[Card], playable: list[Card],
                          trick_number: int) -> Card:
        trump_suit = self.memory.current_trump

        # S21 — ENDGAME (posledné 2-3 štichy)
        if self.difficulty == "hard" and trick_number >= 7:
            endgame = self._get_endgame_card(hand, playable)
            if endgame:
                self._log(SC.ENDGAME, f"{endgame}")
                return endgame

        # S1 — CERTAIN_TRICK
        guaranteed = self.evaluator.get_guaranteed_tricks(hand, trump_suit)
        guaranteed_playable = [c for c in guaranteed if c in playable]

        # ← NOVÉ: v prvom kole vylúč potenciálny tromfový pár
        if trick_number == 0:
            guaranteed_playable = [
                c for c in guaranteed_playable
                if not (c.rank in ("king", "over") and
                        any(cc.suit == c.suit and cc.rank in ("king", "over")
                            and cc != c for cc in hand))
            ]

        if guaranteed_playable:
            card = max(guaranteed_playable, key=lambda c: c.points)
            self._log(SC.CERTAIN_TRICK, f"{card}")
            return card

        # S29 — FIRST_TRICK_TRUMP (variant): bez istého štichu by sa víťaz
        # dražby k hláseniu nedostal — zahlási ju hneď v 1. štichu.
        if trick_number == 0 and self.first_trick_trump:
            suit = self._first_trick_trump_suit(hand)
            if suit:
                card = next((c for c in playable
                             if c.suit == suit and c.rank == "over"), None)
                if card:
                    self._log(SC.FIRST_TRICK_TRUMP,
                              f"{card} → tromf {suit} v 1. štichu")
                    return card

        # S5 — TRUMP_DECLARE
        if trick_number > 0:
            for suit in SUITS:
                has_over = any(c.suit == suit and c.rank == "over" for c in hand)
                has_king = any(c.suit == suit and c.rank == "king" for c in hand)
                if has_over and has_king:
                    trump_card = next(
                        (c for c in playable
                         if c.suit == suit and c.rank in ("king", "over")),
                        None
                    )
                    if trump_card:
                        self._log(SC.TRUMP_DECLARE,
                                  f"{trump_card} → zahlási tromf {suit}")
                        return trump_card

        # S3 — FORCING
        if self.difficulty == "hard":
            forcing = self.evaluator.get_forcing_opportunities(hand, trump_suit)
            for opp in forcing:
                backup = opp.get("backup_count", 1)

                if backup >= 2:
                    threshold = 0.3
                elif backup == 1:
                    threshold = 0.5
                else:
                    threshold = 0.7

                forcing_card = opp["forcing_card"]

                # ← NOVÉ: v prvom kole vylúč potenciálny tromfový pár
                if trick_number == 0 and forcing_card.rank in ("king", "over"):
                    has_pair = any(
                        c.suit == forcing_card.suit and c.rank in ("king", "over")
                        and c != forcing_card for c in hand
                    )
                    if has_pair:
                        continue  # preskočí túto forcing príležitosť

                if (opp["probability"] >= threshold
                        and forcing_card in playable):
                    self._log(SC.FORCING,
                              f"{forcing_card} → chráni {opp['protected_card']} "
                              f"(p={opp['probability']:.0%}, backup={backup})")
                    return forcing_card

        # S4 — PASSIVE
        card = self._play_safest_card(playable, hand)

        # ← NOVÉ: v prvom kole nehrať potenciálny tromfový pár
        if trick_number == 0 and card.rank in ("king", "over"):
            has_pair = any(
                c.suit == card.suit and c.rank in ("king", "over") and c != card
                for c in hand
            )
            if has_pair:
                alternatives = [
                    c for c in playable
                    if not (c.rank in ("king", "over") and
                            any(cc.suit == c.suit and cc.rank in ("king", "over")
                                and cc != c for cc in hand))
                ]
                if alternatives:
                    card = min(alternatives, key=lambda c: (c.points, c.rank_order))

        self._log(SC.PASSIVE, f"{card}")
        return card

    def _get_endgame_card(self, hand: list[Card],
                          playable: list[Card]) -> Card | None:
        """
        S21 — Koncovka (posledné 2-3 štichy).
        Prepočítaj presne čo ostalo — hraj matematicky.
        """
        trump_suit = self.memory.current_trump

        # Nájdi všetky istý štichy v koncovke
        guaranteed = self.evaluator.get_guaranteed_tricks(hand, trump_suit)
        guaranteed_playable = [c for c in guaranteed if c in playable]

        if guaranteed_playable:
            # Zahraj istý štich s najvyššími bodmi
            return max(guaranteed_playable, key=lambda c: c.points)

        # Ak nemám istý štich — zahraj najnižšiu kartu
        # (v koncovke nechceme riskovať)
        return min(playable, key=lambda c: (c.points, c.rank_order))

    # ------------------------------------------------------------------
    # Výber karty — follower
    # ------------------------------------------------------------------

    def _decide_as_follower(self, hand: list[Card], playable: list[Card],
                            trick: Trick) -> Card:
        current_best = self._get_current_best_card(trick)

        # S28 — CLAIM_LEAD (len ak aktívna po S27)
        if self.memory.claim_lead_active:
            claim = self._claim_lead(hand, playable, trick)
            if claim:
                return claim

        # S31 — SECURE_TRICK (variant): sám som hlásil v 1. štichu a ešte
        # nemám štich — ber štich, kedykoľvek sa dá.
        if self.first_trick_trump and self.difficulty in ("medium", "hard"):
            secure = self._secure_first_trick(hand, playable, trick)
            if secure:
                return secure

        # S30 — DENY_TRICK (variant): kto hlásil v 1. štichu, musí zobrať
        # aspoň jeden štich — kým ho nemá, prebi ho, ak sa dá.
        if self.first_trick_trump and self.difficulty in ("medium", "hard"):
            deny = self._deny_first_trick_declarer(playable, trick)
            if deny:
                self._log(SC.DENY_TRICK, f"{deny}")
                return deny

        # S23 — TRACK_BIDDER (sleduj dražiteľa)
        if self.difficulty == "hard":
            track = self._track_bidder(playable, trick)
            if track:
                self._log(SC.TRACK_BIDDER, f"{track}")
                return track

        # S7 — PROTECT_TEN
        if self.difficulty in ("medium", "hard"):
            safe = self._protect_tens(playable, hand, trick)
            if safe:
                self._log(SC.PROTECT_TEN, f"{safe}")
                return safe

        # S9 — SAFE_DISCARD
        card = self._play_safest_card(playable, hand)
        self._log(SC.SAFE_DISCARD, f"{card}")
        return card

    # ------------------------------------------------------------------
    # Pomocné metódy
    # ------------------------------------------------------------------

    def _first_trick_trump_suit(self, hand: list[Card],
                                bid_limit: int | None = -1) -> str | None:
        """Farba hlášky, ktorú sa oplatí zahlásiť v 1. štichu (variant) —
        z _first_trick_candidates, ak to povinnosť dovolí."""
        candidates = self._first_trick_candidates(hand)
        # Povinnosť musí byť aspoň hláška + 10 (bid_limit -1 = aktuálna
        # povinnosť z pamäte, None = nekontrolovať — dražba, navýšenie)
        if bid_limit == -1:
            bid_limit = self.memory.bid_amount
        if bid_limit is not None:
            from game.round import first_trick_min_bid
            candidates = [s for s in candidates
                          if first_trick_min_bid(s) <= bid_limit]
        if not candidates:
            return None
        return self._choose_best_trump(hand, candidates, self.memory.current_trump)

    def _first_trick_candidates(self, hand: list[Card]) -> list[str]:
        """Páry vhodné na hlásenie v 1. štichu (bez kontroly povinnosti).
        Len BEZ ESA (s esom AI hlási klasicky v 2. štichu). Aspoň 4 karty
        tromfovej farby, alebo 3 a desiatka na ruke. Slabšie ruky (2 tromfy;
        3 bez desiatky — v simulácii len 43–54 % splnených) len s podielom
        FIRST_TRICK_WEAK_RISK. Rozhodnutia usera 2026-10-29."""
        if not self.first_trick_trump:
            return []
        if any(c.rank == "ace" for c in hand):
            return []
        has_ten = any(c.rank == "ten" for c in hand)
        weak_ok = (_hand_share(hand)
                   < FIRST_TRICK_WEAK_RISK.get(self.difficulty, 0))
        result = []
        for s in SUITS:
            if not (any(c.suit == s and c.rank == "over" for c in hand)
                    and any(c.suit == s and c.rank == "king" for c in hand)):
                continue
            n = sum(1 for c in hand if c.suit == s)
            strong = n >= 4 or (n == 3 and has_ten)
            weak = n == 3 or (n == 2 and has_ten)
            if strong or (weak and weak_ok):
                result.append(s)
        return result

    def _countable_pairs(self, hand: list[Card], pairs: list[str]) -> list[str]:
        """Hlášky, ktoré sa započítajú do odhadu dražby / navýšenia.
        S esom všetky (eso zoberie štich → AI vynáša a hlási). Bez esa len
        tie, ktoré sa dajú zahlásiť v 1. štichu (variant); v dražbe všetky,
        ak AI riskuje eso z talónu (TALON_ACE_RISK). Po talóne bez esa sa
        hláška nepočíta (napr. základná povinnosť 50 — nenavyšuj na ňu)."""
        if not pairs or any(c.rank == "ace" for c in hand):
            return pairs
        if (self._phase == "bid"
                and _hand_share(hand) < TALON_ACE_RISK.get(self.difficulty, 0)):
            return pairs
        ft = self._first_trick_candidates(hand)
        return [s for s in pairs if s in ft]

    def _secure_first_trick(self, hand: list[Card], playable: list[Card],
                            trick: Trick) -> Card | None:
        """S31 — hlásiaci v 1. štichu ešte nemá štich (bez neho povinnosť
        nesplní). Ako 2./3. v poradí prebije, kedykoľvek môže:
        - karta, ktorú už nikto neprebije (3. v poradí každá víťazná,
          2. v poradí vyššiu nemá súper ani v tromfoch) → najnižšia z nich,
        - inak, ak štich nemá body → najnižšia víťazná (ide len o štich),
        - inak (body v štichu) → najvyššia víťazná, aby ju 3. hráč
          neprebil (napr. vyšším tromfom, ak tiež nemá farbu).
        Pravidlá z návrhu usera 2026-10-29."""
        me = self.memory.player_index
        if self.memory.first_trick_declarer != me:
            return None
        if me in self.memory.trick_winners.values():
            return None                      # štich už mám
        current_best = self._get_current_best_card(trick)
        if current_best is None:
            return None
        winning = [c for c in playable
                   if self._beats_current(c, current_best, trick)]
        if not winning:
            return None
        if len(trick.played_cards) == 2:
            card = min(winning, key=lambda c: (c.rank_order, c.points))
            self._log(SC.SECURE_TRICK, f"{card} → prvý štich (3. v poradí)")
            return card

        # 2. v poradí — po mne hrá ešte jeden súper
        trump = self.memory.current_trump
        on_table = [c for _, c in trick.played_cards]
        outstanding = {Card(s, r) for s in SUITS for r in RANKS} - set(
            self.memory.played_cards) - set(self.memory.seen_cards) - set(
            hand) - set(on_table)
        lead_suit = trick.lead_suit
        opp_trumps = [c for c in outstanding if c.suit == trump]

        def unbeatable(card: Card) -> bool:
            higher = [c for c in outstanding
                      if c.suit == card.suit and c.rank_order > card.rank_order]
            if higher:
                return False
            # farba výnosu bez tromfu — súper ju môže prebiť tromfom
            if card.suit != trump and lead_suit != trump and opp_trumps:
                return False
            return True

        sure = [c for c in winning if unbeatable(c)]
        if sure:
            card = min(sure, key=lambda c: (c.rank_order, c.points))
            reason = "istá"
        elif trick.total_points == 0:
            card = min(winning, key=lambda c: (c.rank_order, c.points))
            reason = "štich bez bodov, najnižšia"
        else:
            card = max(winning, key=lambda c: (c.rank_order, c.points))
            reason = "najvyššia"
        self._log(SC.SECURE_TRICK, f"{card} → prvý štich ({reason})")
        return card

    def _deny_first_trick_declarer(self, playable: list[Card],
                                   trick: Trick) -> Card | None:
        declarer = self.memory.first_trick_declarer
        if declarer is None or declarer == self.memory.player_index:
            return None
        if declarer in self.memory.trick_winners.values():
            return None                  # štich už má — podmienku splnil
        current_best = self._get_current_best_card(trick)
        if current_best is None or trick.get_winner_index() != declarer:
            return None
        can_beat = [c for c in playable
                    if self._beats_current(c, current_best, trick)]
        if not can_beat:
            return None
        return min(can_beat, key=lambda c: (c.rank_order, c.points))

    def _protect_tens(self, playable: list[Card], hand: list[Card],
                      trick: Trick) -> Card | None:
        lead_suit = trick.lead_suit
        if not lead_suit:
            return None
        ten = next(
            (c for c in hand if c.suit == lead_suit and c.rank == "ten"),
            None
        )
        if not ten:
            return None
        other = [
            c for c in playable
            if c.suit == lead_suit and c.rank != "ten"
        ]
        if other:
            return min(other, key=lambda c: c.rank_order)
        return None

    def _beats_current(self, card: Card, current_best: Card | None,
                       trick: Trick) -> bool:
        if current_best is None:
            return True
        trump = self.memory.current_trump
        if card.suit == trump and current_best.suit != trump:
            return True
        if card.suit == trump and current_best.suit == trump:
            return card.rank_order > current_best.rank_order
        if card.suit == current_best.suit:
            return card.rank_order > current_best.rank_order
        return False

    def _get_current_best_card(self, trick: Trick) -> Card | None:
        if not trick.played_cards:
            return None
        winner_idx = trick.get_winner_index()
        for idx, card in trick.played_cards:
            if idx == winner_idx:
                return card
        return None

    def _check_passive_bid(self, hand: list[Card], current_bid: int) -> bool:
        """
        S27 — Pasuj ak mám 2+ esá + kryté tromfy.
        Dostanem sa na štich bez záväzku.
        """
        ace_count = sum(1 for c in hand if c.rank == "ace")
        trump_points = self.evaluator.get_playable_trump_points(hand)

        # 2+ esá + aspoň jedna hláška
        if ace_count >= 2 and trump_points >= 40:
            return True

        # 3+ esá — dostanem sa na štich vždy
        if ace_count >= 3:
            return True

        return False

    def _play_safest_card(self, playable: list[Card],
                           hand: list[Card]) -> Card:
        # Vylúč nekryté desiatky
        protected_tens = self.evaluator.get_protected_tens(hand)
        unprotected_tens = [
            c for c in playable
            if c.rank == "ten"
            and not protected_tens.get(c.suit, False)
        ]
        safe = [c for c in playable if c not in unprotected_tens]
        if not safe:
            return min(playable, key=lambda c: (c.points, c.rank_order))

        singletons = self.evaluator.get_singleton_cards(hand)
        singleton_playable = [
            c for c in safe
            if c in singletons and c.points == 0
        ]
        if singleton_playable:
            return singleton_playable[0]

        return min(safe, key=lambda c: (c.points, c.rank_order))

    def _track_bidder(self, playable: list[Card],
                      trick: Trick) -> Card | None:
        """
        S23 — Sleduj dražiteľa.
        Ak štich berie dražiteľ → prebi ho aj lacnejším štichom.
        Ak štich neberie dražiteľ → nemusíme prebíjať.
        """
        # Nájdi dražiteľa
        bidder_index = None
        for i, player in enumerate(
                [p for p in self.memory.trick_winners.values()]
        ):
            pass

        # Získaj index dražiteľa z memory — potrebujeme ho pridať
        # Zatiaľ použijeme jednoduchšiu logiku:
        # Ak aktuálny víťaz štichu nie je ten istý hráč ako my →
        # skús prebiť

        current_best = self._get_current_best_card(trick)
        if not current_best:
            return None

        current_winner = trick.get_winner_index()

        # Môžeme prebiť?
        can_beat = [
            c for c in playable
            if self._beats_current(c, current_best, trick)
        ]
        if not can_beat:
            return None

        # Prebi ak štich berie niekto iný (nie my)
        # a štich má aspoň nejaké body
        if trick.total_points >= 2:
            return min(can_beat, key=lambda c: c.rank_order)

        return None

    def _claim_lead(self, hand: list[Card], playable: list[Card],
                    trick: Trick) -> Card | None:
        """
        S28 — CLAIM_LEAD
        Aktivuje sa len po S27. Cieľ: dostať sa na lead čo najrýchlejšie.
        """
        if not self.memory.claim_lead_active:
            return None

        played_count = len(trick.played_cards)

        # Som 2. v poradí — potrebujem istý štich
        if played_count == 1:
            lead_suit = trick.lead_suit
            same_suit = [c for c in playable if c.suit == lead_suit]

            if not same_suit:
                return None

            # Hľadaj kartu ktorá je 100% istá (najvyššia nezahraná)
            for card in sorted(same_suit, key=lambda c: c.rank_order, reverse=True):
                if self.memory.is_highest_in_suit(card, hand):
                    self._log(SC.CLAIM_LEAD,
                              f"{card} → istý štich (2. v poradí)")
                    return card

            # Nemám istú → nič nerobím
            return None

        # Som 3. v poradí — stačí prebiť čímkoľvek
        if played_count == 2:
            current_best = self._get_current_best_card(trick)
            can_beat = [
                c for c in playable
                if self._beats_current(c, current_best, trick)
            ]
            if can_beat:
                card = min(can_beat, key=lambda c: c.rank_order)
                self._log(SC.CLAIM_LEAD,
                          f"{card} → prebijem (3. v poradí)")
                return card

        return None

    def __repr__(self) -> str:
        return f"AIStrategy(difficulty={self.difficulty})"