# TISÍC — kartová hra (Python 3.11+, pygame)

3 hráči (1 človek + 2 AI), 32 kariet, hrá sa do 1000 bodov.

## Spustenie
```
python main.py                                    # hra (natívne rozlíšenie, bez rámu)
python main.py --resolution 1366x768 --windowed   # iné rozlíšenie v okne (vývoj)
python main.py --safe                             # núdzový štart v okne 1280×720
```

## Build exe (PyInstaller, onedir)
```
build.bat          # → dist\Tisic\Tisic.exe + dist\Tisic\_internal\
```
`Tisic.spec` pribalí `assets\` (v exe ležia v `_internal\`); main.py si
na štarte nastaví pracovný priečinok na `sys._MEIPASS` (exe) / priečinok
main.py (zdrojáky) — cesty `assets/...` preto ostávajú relatívne. Na
rozdanie sa zbalí celý `dist\Tisic`. Nastavenia, uložená hra, trofeje a
logy sú v `Documents\Tisic` (nie pri exe).

## Testy (headless, bez okna — nezapisujú do Documents/Tisic)
```
python tester/regression_screen.py --out po.txt         # stopa 3 kôl (~1 min)
python tester/regression_screen.py --full --out po.txt  # celá hra
python tester/regression_layout.py                      # rozloženie pri 15 rozlíšeniach
python tester/regression_savegame.py                    # uloženie/obnova hry (~5 min)
python tester/regression_rules_demo.py                  # ukážka štichov v Pravidlách vs. logika hry
python tools/screenshot_gallery.py --out gallery/po --compare gallery/ref_1920x1080
python tools/screenshot_gallery.py --out gallery/po --compare gallery/ref_1920x1080 --compare-only
python tools/screenshot_gallery.py --resolution 3840x2160   # vizuálna kontrola
```
Stopa hry sa pri zmenách GUI nesmie zmeniť; galéria pri 1920×1080 sa
nesmie zmeniť ani o pixel (okrem zámerných zmien). Galériu porovnávať
vždy z toho istého PC (fonty).

## Zobrazenie a rozlíšenia (doc 13 v projekte)
- `gui/display.py` — JEDINÉ miesto so `set_mode()`/`flip()`: režim okna
  (CLI → `TISIC_RESOLUTION` → settings.json `"display"` → natívne),
  logický priestor 1920×L_h (L_h 1080…1200), prepočet myši
  (`get_events()`, `mouse_pos()`), `apply_mode()` za behu.
- `gui/canvas.py` — kreslenie v logických súradniciach priamo vo fyzickom
  rozlíšení (`canvas.font/card/image/overlay/rect…`), `draw_backdrop`,
  `StaticLayer`/`draw_static` (výkon pri 4K).
- `gui/layout.py` — rozloženie hernej obrazovky podľa L_h (ruky, štich,
  talon, tlačidlá, bubliny…). Nové prvky hernej obrazovky pridávať sem.
  Smer hry (Nastavenia → Hra, `settings["play_direction"]` "cw"/"ccw")
  mení len miesta počítačov pri stole (`layout.seats()`); poradie ťahov
  v hernej logike je vždy Hráč → Počítač 1 → Počítač 2. Pozície podľa
  hráča brať vždy z layoutu (nie `if player_index == 1: vľavo`).
- `gui/ui_style.py` — spoločný vzhľad (z CHUJ, doc 15 v projekte):
  farby `GOLD/GOLD_SOFT/TEXT/TEXT_DIM`, tlačidlá v 3 úrovniach
  (`draw_button`, tier 1 = hlavná akcia), `draw_panel`,
  `draw_screen_title`, `draw_backdrop` (stôl + svetlo), `blit_soft_ellipse`.
  Grafický rework (2026-10-28) je hotový na všetkých obrazovkách: menu,
  Nastavenia, Trofeje, Koniec hry, panely, menovky, bubliny, tlačidlá
  v hre (stĺpec s medailónmi — `COLUMN_ICON_FILES` v screen.py; chýbajúci
  sort.png nahrádza kreslená ikonka), posuvník povinnosti, okná Posledný
  štich (`gui/last_trick_overlay.py`, z CHUJ) a Pravidlá a bodovanie
  (`gui/info_overlay.py` + animovaná ukážka štichov `gui/rules_demo.py` —
  príklady musia prejsť regression_rules_demo; texty pravidiel musia
  zodpovedať logike v game/; záložka Prehľad bodovania — karty v Hodnotách
  kariet striedajú farbu cez `SuitCycle`; názvy: „Tromfové hlášky“ = body,
  „Hlásenie tromfu“ = úkon; v Pravidlách je Priebeh kola navigácia — krok
  vyberie obsah veľkého panela: Dražba a Talón = `gui/round_demos.py`
  (stav dražby prehráva skutočná `Bidding`, overuje regression_rules_demo),
  Štichy a tromfy = podzáložky Pravidlá štichov (rules_demo) a Hlásenie
  tromfu (`gui/trump_demo.py`, zatiaľ zástupný obsah) — `TricksTrumpStep`
  v info_overlay.py, Bodovanie = `gui/scoring_demo.py` (scény kreslia
  bloky Prehľadu bodovania tým istým kódom, žiadne kópie), Rozdanie zatiaľ
  obrázok a popis; všetky ukážky = podtriedy `TrickRulesDemo`; panel ukážky
  je na celú šírku pod Priebehom kola — pravé textové panely sú zrušené, ich
  texty (`BID_BULLETS`, `TRUMP_BULLETS…`) sú podklad pre ďalšie scény;
  ovládanie má vlastný pás pod javiskom — layout_problems kontroluje, že
  žiadna scéna nekreslí mimo javiska), popup trofeje
  (vpravo dole, 15 s, klik naň ho zavrie). Nové prvky kresliť cez ui_style.
  K `table.jpg` patrí `table_4k.jpg` (použije sa pri okne > Full HD).

Pravidlá pre GUI kód:
- kresliť len cez `display.canvas()`, nikdy priamo na povrch okna,
- výšku brať z `display.logical_height()` pri vytvorení obrazovky
  (mení sa za behu), šírka je vždy `SCREEN_WIDTH` (1920),
- myš len cez `display.get_events()` / `display.mouse_pos()`,
- prehľady cez hru (Pravidlá `InfoOverlay`, Trofeje `AchievementsOverlay`)
  dostanú udalosti v `_handle_events` ako prvé (Esc ich zavrie); hra pod
  nimi beží ďalej,
- statický obsah hernej obrazovky je v `Screen._draw_static` — ak nový
  prvok mení vzhľad stola alebo rúk, pridať jeho stav do `_hands_key()`.

## Variant pravidiel: tromf aj v 1. štichu (2026-10-29, od hráčov)
Nastavenia → Pravidlá → Hlásenie tromfu, `settings["first_trick_trump"]`
(predvolene vypnuté). Platí pre celú hru: `GameState.first_trick_trump` →
`Round(first_trick_trump)` → `AI(first_trick_trump)`, ukladá sa do savegame.
Víťaz dražby smie hlásiť už v 1. štichu (`Round.trump_allowed_now`,
`can_declare_trump`) — len ak má povinnosť aspoň hodnota hlášky + 10
(`round.first_trick_min_bid`) — potom musí za kolo zobrať aspoň jeden štich, inak
povinnosť nesplnil (`Round.bidder_fulfilled` — jediné miesto vyhodnotenia).
AI: B6 nepasuje kvôli hláške a po talóne navýši na hlášku + 10, L6 hlási v 1. štichu (len bez esa,
bez istého štichu a s ≥ 4 tromfami alebo 3 a desiatkou — `_first_trick_candidates`), F5 obrancovia
prebíjajú hlásiaceho bez štichu, F6 hlásiaci si štich zaistí (`_secure_first_trick`).
Hláška bez esa sa do dražby a navýšenia nepočíta (aj v klasike, `_countable_pairs`); stredný
počítač občas riskuje (`TALON_ACE_RISK`, `FIRST_TRICK_WEAK_RISK` v ai_strategy.py).
```
python tester/sim_first_trick_trump.py            # porovnanie pravidiel (AI vs AI)
python tester/regression_screen.py --first-trick-trump --full --out po.txt
python tester/regression_savegame.py --first-trick-trump
```
Pri vypnutom variante sa stopa hry nesmie zmeniť.

## Uloženie rozohratej hry
`game/savegame.py` — `Documents/Tisic/savegame.json`. Ukladá sa „fotka“
stavu (karty, dražba, štichy, skóre, pamäť AI, trofeje kola/hry, herný
log) pri každom odchode z hernej obrazovky (Screen.run → _settle_for_save
→ save_game); dohratá hra súbor zmaže. Nový herný stav (atribút hráča,
kola, pamäte AI…) treba doplniť do save_game aj _rebuild — inak ho
regression_savegame odhalí len ak ovplyvní priebeh hry.

## Konvencie
- Komentáre slovensky, názvy tried/funkcií/premenných anglicky.
- Súbory majú koncovky riadkov CRLF.
- Nespúšťať hru bez vyžiadania — otvára okno.
