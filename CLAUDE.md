# TISÍC — kartová hra (Python 3.11+, pygame)

3 hráči (1 človek + 2 AI), 32 kariet, hrá sa do 1000 bodov.

## Spustenie
```
python main.py                                    # hra (natívne rozlíšenie, bez rámu)
python main.py --resolution 1366x768 --windowed   # iné rozlíšenie v okne (vývoj)
python main.py --safe                             # núdzový štart v okne 1280×720
```

## Testy (headless, bez okna — nezapisujú do Documents/Tisic)
```
python tester/regression_screen.py --out po.txt         # stopa 3 kôl (~1 min)
python tester/regression_screen.py --full --out po.txt  # celá hra
python tester/regression_layout.py                      # rozloženie pri 15 rozlíšeniach
python tester/regression_savegame.py                    # uloženie/obnova hry (~5 min)
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

Pravidlá pre GUI kód:
- kresliť len cez `display.canvas()`, nikdy priamo na povrch okna,
- výšku brať z `display.logical_height()` pri vytvorení obrazovky
  (mení sa za behu), šírka je vždy `SCREEN_WIDTH` (1920),
- myš len cez `display.get_events()` / `display.mouse_pos()`,
- statický obsah hernej obrazovky je v `Screen._draw_static` — ak nový
  prvok mení vzhľad stola alebo rúk, pridať jeho stav do `_hands_key()`.

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
