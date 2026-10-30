# tools/screenshot_gallery.py
#
# Galéria obrazoviek — headless (bez okna) vykreslí všetky dôležité
# obrazovky hry pri zadanom rozlíšení a uloží ich ako PNG.
#
# Načo: rework rozlíšení (claude/13_RESOLUTION_REWORK_ANALYSIS.md).
#   1. Pred zmenami GUI sa vyrobí REFERENCIA pri 1920×1080.
#   2. Po každom kroku reworku sa galéria vyrobí znova a porovná sa
#      (--compare): pri 1920×1080 sa nesmie zmeniť ani pixel (okrem
#      zámerných zmien).
#   3. Pri iných rozlíšeniach (aj väčších než monitor, napr. 4K) slúži na
#      vizuálnu kontrolu — PNG sa dá prezrieť pri 100 %.
#
# Nástroj hru NEMENÍ a NEZAPISUJE do Documents/Tisic (nastavenia, logy,
# trofeje) — domovský priečinok sa presmeruje do dočasného priečinka
# s vymyslenými trofejami. Výsledok je deterministický: pevné seedy,
# PYTHONHASHSEED=0 a falošné hodiny (16 ms na snímku).
#
# Použitie:
#   python tools/screenshot_gallery.py --out gallery/ref_1920x1080
#   python tools/screenshot_gallery.py --resolution 1366x768
#   python tools/screenshot_gallery.py --out gallery/po --compare gallery/ref_1920x1080
#   python tools/screenshot_gallery.py --out gallery/po --compare gallery/ref_1920x1080 --compare-only
#        (len porovná už vyrobenú galériu; numpy netreba)
#   python tools/screenshot_gallery.py --only menu,gameover
#
# Pozor: fonty. Hra používa Tahomu (Windows). Galériu na porovnanie treba
# vyrábať vždy na tom istom počítači — referencia z iného PC (iné fonty)
# sa pixel po pixeli líšiť bude.

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tester import regression_screen as rs   # noqa: E402  (spoločná príprava)

GAME_SEED = 20261024    # seed hernej scény
MENU_SEED = 1           # seed náhodných kariet v pozadí menu
GROUPS = ("menu", "game", "gameover")


def write_fake_achievements(home: str):
    """Približne polovica trofejí odomknutá — obrazovka Trofeje ukáže
    oba stavy (odomknutá / zamknutá, skrytý popis)."""
    sys.path.insert(0, ROOT)
    from achievements.definitions import get_all_ids
    ids = get_all_ids()
    data = {
        "unlocked": {aid: (i % 2 == 0) for i, aid in enumerate(ids)},
        "stats": {"wins_total": 7, "games_played": 12,
                  "win_streak_current": 2, "win_streak_best": 4},
    }
    path = os.path.join(home, "Documents", "Tisic", "achievements.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Gallery:
    def __init__(self, out_dir: str, width: int, height: int, clock):
        import pygame
        self.pygame = pygame
        self.out_dir = out_dir
        self.clock = clock
        self.window = rs.open_window(width, height)
        from gui import display
        self.display = display
        self.saved: list[str] = []
        os.makedirs(out_dir, exist_ok=True)

    def shot(self, name: str):
        """Uloží to, čo by videl hráč (fyzické okno)."""
        self.display.present()
        surface = self.pygame.display.get_surface()
        self.pygame.image.save(surface, os.path.join(self.out_dir, f"{name}.png"))
        self.saved.append(name)
        print(f"  {name}.png", file=sys.stderr)

    # --- pomocné pre Screen ---------------------------------------------

    def frame(self, screen, n: int = 1):
        for _ in range(n):
            self.clock.advance()
            rs.step(screen)

    def run_until(self, screen, cond, bot=None, max_frames: int = 6_000) -> bool:
        """Beží snímky, kým cond() nie je pravda. Podmienka sa kontroluje
        hneď po snímke, PRED ťahom bota — inak by bot zahral práve v
        snímke, keď sa hráč dostal na ťah."""
        if cond():
            return True
        for _ in range(max_frames):
            self.frame(screen)
            if cond():
                return True
            if bot is not None:
                bot.act()
        print(f"!! podmienka nesplnená po {max_frames} snímkach", file=sys.stderr)
        return False

    # --- skupina: menu ----------------------------------------------------

    def scenes_menu(self):
        import random
        from gui.menu import Menu
        from gui.settings_screen import SettingsScreen
        from gui.achievements_screen import AchievementsScreen

        random.seed(MENU_SEED)
        menu = Menu(self.window, show_continue=True)
        menu._update_hover((0, 0))
        menu._draw()
        self.shot("menu_01_hlavne")

        random.seed(MENU_SEED)
        menu = Menu(self.window, show_continue=False)
        menu._update_hover((0, 0))
        menu._draw()
        self.shot("menu_02_hlavne_bez_pokracovat")

        settings = {"ai1_difficulty": "hard", "ai2_difficulty": "medium",
                    "table_bg": "table1.jpg"}
        st = SettingsScreen(self.window, settings)
        st._update_hover((0, 0))
        st._draw()
        self.shot("menu_03_nastavenia")
        if hasattr(st, "tab_rects"):                 # záložky (krok 7)
            st.active_tab = "zobrazenie"
            st.pending_windowed = False
            st._draw()
            self.shot("menu_03b_nastavenia_zobrazenie")
            if st.window_sizes:
                st.pending_windowed = True
                st._draw()
                self.shot("menu_03c_nastavenia_okno")
            # dialóg po prepnutí — bez skutočného prepnutia okna
            import pygame
            st.confirm = {"old": None,
                          "deadline": pygame.time.get_ticks() + 15000}
            st._draw()
            self.shot("menu_03d_nastavenia_potvrdenie")
            st.confirm = None
            st.active_tab = "pravidla"
            st._draw()
            self.shot("menu_03e_nastavenia_pravidla")
            st.settings["first_trick_trump"] = True
            st._draw()
            self.shot("menu_03f_nastavenia_tromf_1_stich")
            st.active_tab = "hra"

        ach = AchievementsScreen(self.window)
        ach._draw((0, 0))
        self.shot("menu_04_trofeje")
        ach.scroll_offset = ach.max_scroll
        ach._draw((0, 0))
        self.shot("menu_05_trofeje_koniec")

    # --- skupina: game ----------------------------------------------------

    def scenes_game(self):
        screen, gs, tracker = rs.new_screen(GAME_SEED)
        screen.running = True
        # V galérii hráč prihadzuje vždy — vydraží a ukáže sa talon,
        # odhadzovanie aj posúvač navýšenia.
        bot = rs.HumanBot(screen, gs, bid_limit=400, require_pair=False)
        # Povinnosť má Počítač 2 → hráč je v dražbe na ťahu hneď po ňom.
        gs.obligation_index = 2
        screen._start_round()
        hi = gs.human_index
        human = gs.players[hi]

        self.frame(screen, 25)
        self.shot("game_01_rozdavanie")

        def human_bidding():
            rnd = gs.current_round
            return (not screen.dealing and rnd.phase == "bidding"
                    and not rnd.bidding.bidding_over
                    and screen._get_next_bidder_index() == hi)

        self.run_until(screen, human_bidding)
        self.frame(screen, 2)
        self.shot("game_02_drazba_hrac_na_tahu")

        def talon_shown():
            return screen.talon_revealing and not screen._talon_anim_started

        self.run_until(screen, talon_shown, bot)
        self.frame(screen, 2)
        self.shot("game_03_talon_odkryty")

        def discard_ready():
            rnd = gs.current_round
            return (rnd.phase == "talon" and len(human.hand.cards) == 12
                    and not screen.talon_revealing)

        if not self.run_until(screen, discard_ready, bot):
            return gs
        self.frame(screen, 2)
        self.shot("game_04_odhadzovanie")

        self.run_until(screen, lambda: len(screen.selected_discards) == 2, bot)
        self.frame(screen, 2)
        self.shot("game_05_odhadzovanie_potvrdit")

        self.run_until(screen, lambda: screen.bid_slider.visible, bot)
        self.frame(screen, 2)
        self.shot("game_06_navysenie_povinnosti")

        def human_turn_two_cards():
            rnd = gs.current_round
            return (rnd.phase == "tricks" and rnd.current_trick is not None
                    and len(rnd.current_trick.played_cards) == 2
                    and rnd.get_current_player_index() == hi
                    and not screen.trick_waiting
                    and screen.trick_animation.is_done
                    and not screen.card_throw_animation.in_flight)

        self.run_until(screen, human_turn_two_cards, bot)
        self.frame(screen, 2)
        self.shot("game_07_stich_hrac_na_tahu")

        # Smer hry proti smeru hodinových ručičiek (SR) — ten istý stav
        # hry, len počítače vymenené (Počítač 1 vpravo). Iba vykreslenie,
        # bez herných snímok — priebeh hry pre ďalšie scény sa nemení.
        from gui.screen import Screen
        from gui import layout
        sr = Screen(gs, screen.ai_players, debug=False, new_game=False,
                    achievement_tracker=tracker, autosave=False, clockwise=False)
        sr.speech_bubble.show_bid(1, 70)
        sr.speech_bubble.show_bid(2, 80)
        sr._draw()
        self.shot("game_07b_smer_SR")
        layout.set_clockwise(True)

        # Dialóg tromfu — len vykreslenie (stav sa hneď vráti)
        card = next((c for c in human.hand.cards
                     if c.rank in ("over", "king")), human.hand.cards[0])
        screen.pending_trump_card = card
        screen.pending_trump_suit = card.suit
        screen.pending_trump_first_trick = False
        screen._draw()
        self.shot("game_08_tromf_dialog")
        screen.pending_trump_card = None
        screen.pending_trump_suit = None

        self.run_until(screen, lambda: (
            gs.current_round.trick_number >= 2 and human_turn_two_cards()), bot)
        self.frame(screen, 2)
        self.shot("game_09_stich3_s_tlacidlom_posledny")

        screen.show_last_trick = True
        self.frame(screen)
        self.shot("game_10_posledny_stich")
        screen.show_last_trick = False

        screen.info_overlay.visible = True
        screen.info_overlay.active_tab = "bodovanie"
        self.frame(screen)
        self.shot("game_11_pravidla_bodovanie")
        # Hodnoty kariet striedajú farbu — stojaci žaluď (2. farba cyklu)
        cyc = screen.info_overlay.card_cycle
        cyc._t0 = self.pygame.time.get_ticks() - int((cyc.HOLD + cyc.FADE + 1.0) * 1000)
        self.frame(screen)
        self.shot("game_11b_bodovanie_karty_zalud")
        screen.info_overlay.active_tab = "pravidla"
        self.frame(screen)
        self.shot("game_12_pravidla_pravidla")
        # Priebeh kola ako navigácia: krok Bodovanie (scéna 1 a 3), krok Dražba
        ov = screen.info_overlay
        ov.select_step(4)
        ov.scoring_demo._t0 -= 2000            # po nábehu scény
        self.frame(screen)
        self.shot("game_12d_pravidla_krok_bodovanie")
        ov.scoring_demo.select(2)
        ov.scoring_demo._t0 -= 2000
        self.frame(screen)
        self.shot("game_12e_pravidla_bodovanie_povinnost")
        # Dražba (víťaz dražby) a Talón (eso ani desiatku nie) — scéna stojí
        # na výsledku (HOLD_AT), obrázok nezávisí od času snímky
        ov.select_step(1)
        ov.bidding_demo.select(4)
        ov.bidding_demo._t0 -= 100000
        self.frame(screen)
        self.shot("game_12f_pravidla_krok_drazba")
        ov.select_step(2)
        ov.talon_demo.select(1)
        ov.talon_demo._t0 -= 100000
        self.frame(screen)
        self.shot("game_12g_pravidla_krok_talon")
        # Štichy a tromfy — podzáložka Hlásenie tromfu (zatiaľ zástupný obsah)
        ov.select_step(3)
        ov.tricks_step.select_tab(1)
        ov.trump_demo._t0 -= 100000
        self.frame(screen)
        self.shot("game_12h_pravidla_hlasenie_tromfu")
        ov.select_step(3)
        ov.tricks_step.reset()
        screen.info_overlay.visible = False
        # Pravidlá pri variante „tromf aj v 1. štichu“
        from gui.info_overlay import InfoOverlay
        normal_ov = screen.info_overlay
        screen.info_overlay = InfoOverlay(screen.canvas, first_trick_trump=True)
        screen.info_overlay.visible = True
        screen.info_overlay.active_tab = "pravidla"
        self.frame(screen)
        self.shot("game_12c_pravidla_tromf_1_stich")
        screen.info_overlay = normal_ov

        screen.trophy_overlay.show()
        self.frame(screen)
        self.shot("game_12b_trofeje")
        screen.trophy_overlay.hide()

        # Koniec kola — bubliny s výsledkom počas rozdávania ďalšieho kola
        self.run_until(screen, lambda: gs.round_number >= 2, bot)
        self.frame(screen, 3)
        self.shot("game_13_koniec_kola")

        # Popup trofeje
        self.run_until(screen, lambda: not screen.dealing, bot)
        screen.achievement_popup.add(["first_trump"])
        self.frame(screen, 40)
        self.shot("game_14_trofej_popup")
        return gs

    # --- skupina: gameover ------------------------------------------------

    def scenes_gameover(self, gs=None):
        from gui.game_over_screen import GameOverScreen
        if gs is None:
            screen, gs, _ = rs.new_screen(GAME_SEED)
        for p, score in zip(gs.players, (1015, 640, 385)):
            p.total_score = score
        go = GameOverScreen(self.window, gs.players, gs.players[0], 23)
        go._draw((0, 0))
        self.shot("gameover_01_vyhra")

        for p, score in zip(gs.players, (720, 1005, 410)):
            p.total_score = score
        go = GameOverScreen(self.window, gs.players, gs.players[1], 19)
        go._draw((0, 0))
        self.shot("gameover_02_prehra")


# ----------------------------------------------------------------------
# Porovnanie
# ----------------------------------------------------------------------

def _diff_images(a, b):
    """Vráti (počet odlišných pixelov, obrázok s odlišnými pixelmi
    červenou). Funguje aj bez numpy — rýchla cesta pri zhode je
    porovnanie celých bajtov, pomalšia (po riadkoch) len pri rozdieloch."""
    import pygame
    bytes_a = pygame.image.tobytes(a, "RGB")
    bytes_b = pygame.image.tobytes(b, "RGB")
    if bytes_a == bytes_b:
        return 0, None
    w, h = a.get_size()
    diff = b.copy()
    stride = w * 3
    count = 0
    for y in range(h):
        row_a = bytes_a[y * stride:(y + 1) * stride]
        row_b = bytes_b[y * stride:(y + 1) * stride]
        if row_a == row_b:
            continue
        for x in range(w):
            i = x * 3
            if row_a[i:i + 3] != row_b[i:i + 3]:
                count += 1
                diff.set_at((x, y), (255, 0, 0))
    return count, diff


def compare_dirs(new_dir: str, ref_dir: str) -> bool:
    """Porovná PNG pixel po pixeli. Vypíše počet odlišných pixelov a
    uloží *_diff.png (odlišné pixely červenou)."""
    import pygame
    ok = True
    names = sorted(f for f in os.listdir(ref_dir)
                   if f.endswith(".png") and not f.endswith("_diff.png"))
    for name in names:
        new_path = os.path.join(new_dir, name)
        if not os.path.exists(new_path):
            print(f"[CHÝBA] {name}")
            ok = False
            continue
        a = pygame.image.load(os.path.join(ref_dir, name))
        b = pygame.image.load(new_path)
        if a.get_size() != b.get_size():
            print(f"[ROZMER] {name}: {a.get_size()} vs {b.get_size()}")
            ok = False
            continue
        count, diff = _diff_images(a, b)
        if count:
            ok = False
            pygame.image.save(diff, os.path.join(
                new_dir, name.replace(".png", "_diff.png")))
            print(f"[ROZDIEL] {name}: {count} px")
        else:
            print(f"[OK] {name}")
    extra = sorted(set(f for f in os.listdir(new_dir) if f.endswith(".png")
                       and not f.endswith("_diff.png")) - set(names))
    for name in extra:
        print(f"[NOVÁ] {name} (v referencii nie je)")
    return ok


# ----------------------------------------------------------------------

def parse_resolution(text: str) -> tuple[int, int]:
    w, h = text.lower().replace("×", "x").split("x")
    return int(w), int(h)


def main():
    parser = argparse.ArgumentParser(
        description="Headless galéria obrazoviek hry (PNG).")
    parser.add_argument("--resolution", default="1920x1080",
                        help="napr. 1366x768, 2560x1600, 3840x2160")
    parser.add_argument("--out", default=None,
                        help="priečinok na PNG (predvolené gallery/<rozlíšenie>)")
    parser.add_argument("--only", default=",".join(GROUPS),
                        help="skupiny oddelené čiarkou: " + ",".join(GROUPS))
    parser.add_argument("--compare", default=None,
                        help="priečinok s referenciou na porovnanie")
    parser.add_argument("--compare-only", action="store_true",
                        help="nevyrábať obrázky, len porovnať --out s --compare")
    args = parser.parse_args()

    if args.compare_only:
        if not (args.out and args.compare):
            parser.error("--compare-only potrebuje --out aj --compare")
        print(f"Porovnanie {args.out} s {args.compare}:")
        same = compare_dirs(os.path.abspath(args.out), os.path.abspath(args.compare))
        print("\nVÝSLEDOK: " + ("ZHODA" if same else "ROZDIELY"))
        sys.exit(0 if same else 1)

    rs.ensure_hashseed()
    width, height = parse_resolution(args.resolution)
    out_dir = os.path.abspath(args.out or os.path.join(
        ROOT, "gallery", f"{width}x{height}"))
    compare_dir = os.path.abspath(args.compare) if args.compare else None

    home = rs.isolate_home("tisic_gallery_")
    write_fake_achievements(home)
    clock = rs.setup_headless(width, height)

    gallery = Gallery(out_dir, width, height, clock)
    groups = [g.strip() for g in args.only.split(",") if g.strip()]
    print(f"Galéria {width}x{height} -> {out_dir}", file=sys.stderr)

    gs = None
    if "menu" in groups:
        gallery.scenes_menu()
    if "game" in groups:
        gs = gallery.scenes_game()
    if "gameover" in groups:
        gallery.scenes_gameover(gs)

    print(f"Uložených {len(gallery.saved)} obrázkov.", file=sys.stderr)

    if compare_dir:
        print(f"\nPorovnanie s {compare_dir}:")
        same = compare_dirs(out_dir, compare_dir)
        print("\nVÝSLEDOK: " + ("ZHODA" if same else "ROZDIELY"))
        sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()
