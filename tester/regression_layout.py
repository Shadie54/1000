# tester/regression_layout.py
#
# Regresný test rozloženia obrazoviek pri rôznych rozlíšeniach — rework
# rozlíšení, krok 3 (claude/13_RESOLUTION_REWORK_ANALYSIS.md).
#
# Pre každé rozlíšenie postaví (headless) obrazovky hry a overí
# v LOGICKÝCH súradniciach (1920×L_h, gui/display.py):
#   1. prvky, ktoré sú na obrazovke súčasne, sa neprekrývajú (tlačidlá,
#      ruky hráčov, panely skóre, posúvač navýšenia…),
#   2. klikateľné prvky nevyčnievajú z logického priestoru,
#   3. ruka hráča je viditeľná aspoň MIN_HAND_VISIBLE px a ruky počítačov
#      sú aspoň z 2/3 na obrazovke.
#
# Každé rozlíšenie beží v samostatnom procese (config.py si logickú výšku
# číta pri importe — gui/display.py, TISIC_RESOLUTION).
#
# Použitie:
#   python tester/regression_layout.py              # všetky rozlíšenia
#   python tester/regression_layout.py --one 1366x768
#   python tester/regression_layout.py --verbose    # vypíše aj obdĺžniky

import argparse
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 16:9, 16:10, 21:9, 4:3 (záťažový prípad) — rovnaký zoznam ako v CHUJ.
RESOLUTIONS = [
    "1366x768", "1280x720", "1600x900", "1920x1080", "2560x1440", "3840x2160",
    "1280x800", "1440x900", "1680x1050", "1920x1200", "2560x1600", "2880x1800",
    "2560x1080", "3440x1440", "1024x768",
]

# Minimálna viditeľná výška ruky hráča (logické px). Pri 1080p je 221 z 293.
MIN_HAND_VISIBLE = 200


def _overlaps(group: dict) -> list[str]:
    problems = []
    names = list(group)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ra, rb = group[a], group[b]
            if ra.colliderect(rb):
                clip = ra.clip(rb)
                problems.append(f"prekryv {a} × {b}: {clip.width}×{clip.height}")
    return problems


def _outside(group: dict, width: int, height: int,
             allow: tuple = ()) -> list[str]:
    import pygame
    area = pygame.Rect(0, 0, width, height)
    return [f"mimo obrazovky {name}: {rect}"
            for name, rect in group.items()
            if name not in allow and not area.contains(rect)]


def run_one(resolution: str, verbose: bool) -> list[str]:
    """Beží v samostatnom procese — prostredie sa nastaví PRED importom."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    os.environ["TISIC_RESOLUTION"] = resolution
    os.environ["TISIC_DESKTOP"] = resolution     # ponuka veľkostí okna
    home = tempfile.mkdtemp(prefix="tisic_layout_")
    os.environ["HOME"] = home
    os.environ["USERPROFILE"] = home
    os.makedirs(os.path.join(home, "Documents", "Tisic"), exist_ok=True)
    os.chdir(ROOT)
    sys.path.insert(0, ROOT)

    import pygame
    pygame.time.delay = lambda ms: None

    from config import SCREEN_WIDTH
    from gui import display

    problems: list[str] = []

    def check(screen_name: str, group: dict, allow_outside: tuple = ()):
        W, H = SCREEN_WIDTH, display.logical_height()
        if verbose:
            for name, rect in group.items():
                print(f"    {screen_name}.{name}: {rect}")
        for p in _overlaps(group) + _outside(group, W, H, allow_outside):
            problems.append(f"{screen_name}: {p}")

    tag = {"text": ""}

    def tagged_check(screen_name, group, allow_outside=()):
        check(tag["text"] + screen_name, group, allow_outside)

    check_screens(display.get_surface(), tagged_check, problems)
    # Smer hry proti smeru hodinových ručičiek (SR) — počítače vymenené
    tag["text"] = "[SR] "
    check_screens(display.get_surface(), tagged_check, problems, clockwise=False)
    tag["text"] = ""

    if resolution == "1920x1080":
        # Prepnutie zobrazenia ZA BEHU (Nastavenia → Zobrazenie → Použiť →
        # Ponechať): okno 1440×900 = logicky 1920×1200 → všetko znova.
        from gui.settings_screen import SettingsScreen
        from gui import layout
        st = SettingsScreen(display.get_surface(), {
            "ai1_difficulty": "hard", "ai2_difficulty": "hard",
            "table_bg": "table.jpg"})
        st.pending_windowed = True
        st.pending_size = (1440, 900)
        st._apply_display()
        st._confirm_keep()
        mode, vp = display.current_mode(), display.viewport()
        if ((mode.width, mode.height, mode.windowed) != (1440, 900, True)
                or vp.l_h != 1200 or layout.game().l_h != 1200
                or st.settings.get("display") != {"mode": "window",
                                                  "width": 1440, "height": 900}):
            problems.append(f"prepnutie za behu: {mode} {vp} {st.settings.get('display')}")
        tag["text"] = "[po prepnutí 1440x900] "
        check_screens(display.get_surface(), tagged_check, problems)
    return problems


def check_screens(window, check, problems: list[str], clockwise: bool = True):
    """Postaví všetky obrazovky pre AKTUÁLNE okno a skontroluje ich."""
    import random
    import pygame
    from config import SCREEN_WIDTH, CARD_SIZE_MEDIUM
    from gui import display
    from gui.screen import Screen
    from gui.menu import Menu
    from gui.settings_screen import SettingsScreen
    from gui.achievements_screen import AchievementsScreen
    from gui.game_over_screen import GameOverScreen
    import main as game_main

    W, H = SCREEN_WIDTH, display.logical_height()
    area = pygame.Rect(0, 0, W, H)
    cw, ch = CARD_SIZE_MEDIUM

    # --- herná obrazovka -------------------------------------------------
    random.seed(1)
    settings = {"ai1_difficulty": "hard", "ai2_difficulty": "hard",
                "table_bg": "table.jpg"}
    game_state, ai_players = game_main._create_game(settings)
    screen = Screen(game_state, ai_players, debug=False, new_game=False,
                    clockwise=clockwise)
    screen._start_round()
    screen.dealing = False
    screen.deal_animation = None
    renderer = screen.card_renderer
    cfgs = renderer.hand_configs

    def human_hand(n_cards: int) -> pygame.Rect:
        """Viditeľná (klikateľná) časť ruky hráča; +20 px hore kvôli
        vysunutej vybranej karte pri odhadzovaní."""
        cfg = cfgs[0]
        rect = pygame.Rect(cfg["x"], cfg["y"],
                           (n_cards - 1) * cfg["offset"] + cw, ch)
        return rect.clip(area).inflate(0, 20).move(0, -10)

    def ai_hand(idx: int, n_cards: int = 10) -> pygame.Rect:
        cfg = cfgs[idx]   # vertikálna ruka — karta otočená o 90°
        return pygame.Rect(cfg["x"], cfg["y"], ch, (n_cards - 1) * cfg["offset"] + cw)

    hand10 = human_hand(10)
    if hand10.height - 20 < MIN_HAND_VISIBLE:
        problems.append(f"hra: ruka hráča viditeľná len {hand10.height - 20} px "
                        f"(min. {MIN_HAND_VISIBLE})")
    for idx, name in ((1, "Počítač 1"), (2, "Počítač 2")):
        rect = ai_hand(idx)
        vis = rect.clip(area)
        if vis.width * vis.height < 0.66 * rect.width * rect.height:
            problems.append(f"hra: ruka {name} väčšinou mimo obrazovky {rect}")

    sb = screen.scoreboard
    scoreboard = pygame.Rect(sb.start_x, sb.panel_y,
                             sb.info_x + sb.info_w - sb.start_x, sb.panel_h)

    # Prvky viditeľné vždy (ruky súperov a skóre nie sú klikateľné, ale
    # nesmú zakrývať tlačidlá ani sa navzájom prekrývať).
    always = {
        "Zoradiť karty": screen._button_sort_rect(),
        "Pravidlá": screen._button_info_rect(),
        "Trofeje": screen._button_trophies_rect(),
        "Menu": screen._button_menu_rect(),
        "ruka Počítač 1": ai_hand(1),
        "ruka Počítač 2": ai_hand(2),
        "skóre": scoreboard,
    }
    check("hra/dražba", {**always,
                         "Dám +10": screen._button_bid_rect(),
                         "Dobrý": screen._button_pass_rect(),
                         "ruka hráča": hand10},
          allow_outside=("ruka hráča",))
    check("hra/talon", {**always,
                        "Potvrdiť": screen._button_confirm_rect(),
                        "ruka hráča": human_hand(12)},
          allow_outside=("ruka hráča",))
    bs = screen.bid_slider
    track = pygame.Rect(bs.track_x, bs.track_y - 15, bs.track_w, 30)
    check("hra/navýšenie", {**always,
                            "posúvač −": bs.btn_minus,
                            "posúvač +": bs.btn_plus,
                            "posúvač dráha": track,
                            "posúvač Potvrdiť": bs.btn_confirm,
                            "ruka hráča": hand10},
          allow_outside=("ruka hráča",))
    if not area.contains(pygame.Rect(bs.panel_x, bs.panel_y, bs.panel_w, bs.panel_h)):
        problems.append("hra/navýšenie: panel posúvača mimo obrazovky")
    with_last = {**always, "Posledný štich": screen._button_last_trick_rect()}
    check("hra/štichy", {**with_last, "ruka hráča": hand10},
          allow_outside=("ruka hráča",))
    check("hra/tromf", {**with_last,
                        "Tromf": screen._button_trump_yes_rect(),
                        "Bez tromfu": screen._button_trump_no_rect(),
                        "ruka hráča": hand10},
          allow_outside=("ruka hráča",))

    # Popis musí byť vo vnútri tlačidla
    for text, rect in (("Trofeje", screen._button_trophies_rect()),
                       ("Menu", screen._button_menu_rect()),
                       ("Pravidlá", screen._button_info_rect())):
        if screen.font_medium.size(text)[0] > rect.width - 12:
            problems.append(f"hra: text „{text}“ sa nezmestí do tlačidla")

    screen.trophy_overlay.show()
    tv = screen.trophy_overlay.view
    check("hra/trofeje", {"Späť": tv.back_button,
                          "obsah": pygame.Rect(tv.PANEL_X, tv.CONTENT_Y,
                                               tv.PANEL_W, tv.CONTENT_H)})
    screen.trophy_overlay.hide()

    ov = screen.info_overlay
    group = {"Zavrieť": ov.btn_close}
    for key, rect in ov.tab_rects.items():
        group[f"záložka {key}"] = rect
    check("pravidlá", group)
    # Obsah okna Pravidlá a bodovanie nesmie presahovať svoje panely
    for p in ov.layout_problems():
        problems.append(f"pravidlá: {p}")

    # --- menu ------------------------------------------------------------
    menu = Menu(window, show_continue=True)
    check("menu", {b["label"]: b["rect"] for b in menu.buttons})

    st = SettingsScreen(window, settings)
    group = {"Späť": st.back_button["rect"]}
    for btn in st.ai1_buttons:
        group[f"Počítač 1/{btn['difficulty']}"] = btn["rect"]
    for btn in st.ai2_buttons:
        group[f"Počítač 2/{btn['difficulty']}"] = btn["rect"]
    for i, rect in enumerate(st.bg_rects):
        # miniatúra + popisok pod ňou (~24 px)
        group[f"pozadie {i + 1}"] = rect.inflate(0, 24).move(0, 12)
    for key, rect in st.tab_rects.items():
        group[f"záložka {key}"] = rect
    group["šípka ←"] = st.bg_arrow_left["rect"]
    group["šípka →"] = st.bg_arrow_right["rect"]
    group["posuvník"] = st.slider_rect.inflate(20, st.slider_handle_radius * 3)
    for btn in st.dir_buttons:
        group[f"smer {btn['value']}"] = btn["rect"]
    check("nastavenia", group)
    for name, panel in (("panel obtiažnosť", st.panel_ai),
                        ("panel smer", st.panel_dir),
                        ("panel animácie", st.panel_anim),
                        ("panel pozadie", st.panel_bg)):
        if panel.colliderect(st.back_button["rect"]):
            problems.append(f"nastavenia: {name} × Späť")
        for key, rect in st.tab_rects.items():
            if panel.colliderect(rect):
                problems.append(f"nastavenia: {name} × záložka {key}")
        if not area.contains(panel):
            problems.append(f"nastavenia: {name} mimo obrazovky {panel}")

    # Záložka Zobrazenie (režim Okno — vtedy je na nej najviac prvkov)
    st.active_tab = "zobrazenie"
    st.pending_windowed = bool(st.window_sizes)
    group = {"Späť": st.back_button["rect"], "Použiť": st._apply_rect()}
    for key, rect in st.tab_rects.items():
        group[f"záložka {key}"] = rect
    for btn in st.mode_buttons:
        group[btn["label"]] = btn["rect"]
    if st.pending_windowed:
        for btn in st.size_buttons:
            group["okno %dx%d" % btn["size"]] = btn["rect"]
    check("zobrazenie", group)
    panels = [("panel režim", st.panel_mode)]
    if st.pending_windowed:
        panels.append(("panel veľkosť", st.panel_size))
    for name, panel in panels:
        for other in ("Späť", "Použiť"):
            if panel.colliderect(group[other]):
                problems.append(f"zobrazenie: {name} × {other}")
    check("potvrdenie", {"Ponechať": st.confirm_keep, "Vrátiť": st.confirm_revert})
    if not st.confirm_panel.contains(st.confirm_keep.union(st.confirm_revert)):
        problems.append("potvrdenie: tlačidlá mimo panelu")

    ach = AchievementsScreen(window)
    check("trofeje", {"Späť": ach.back_button,
                      "obsah": pygame.Rect(ach.PANEL_X, ach.CONTENT_Y,
                                           ach.PANEL_W, ach.CONTENT_H)})

    go = GameOverScreen(window, game_state.players, game_state.players[0], 1)
    check("koniec hry", {"Nová hra": go.btn_new_game, "Menu": go.btn_menu})


def main():
    parser = argparse.ArgumentParser(description="Regresný test rozloženia.")
    parser.add_argument("--one", default=None, help="len jedno rozlíšenie")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    if args.one:
        problems = run_one(args.one, args.verbose)
        for p in problems:
            print(f"  {p}")
        sys.exit(1 if problems else 0)

    failed = []
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for res in RESOLUTIONS:
        cmd = [sys.executable, os.path.abspath(__file__), "--one", res]
        if args.verbose:
            cmd.append("--verbose")
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env,
                              encoding="utf-8", errors="replace")
        lines = [ln for ln in proc.stdout.splitlines()
                 if ln.startswith("  ") or args.verbose]
        status = "OK" if proc.returncode == 0 else "CHYBA"
        print(f"[{status}] {res}")
        for ln in lines:
            print(ln)
        if proc.returncode not in (0, 1):
            print(proc.stderr[-2000:])
        if proc.returncode != 0:
            failed.append(res)

    print()
    print("VÝSLEDOK: " + ("všetky rozlíšenia OK" if not failed
                          else f"chyby pri {', '.join(failed)}"))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
