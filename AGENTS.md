# AGENTS.md — pravidlá pre AI agentov v projekte 1000

Projekt: hra Tisíc (1000) v Pythone a pygame. UI v slovenčine, identifikátory v angličtine, konce riadkov CRLF.

## Rozdelenie práce
- Claude: kód, logika AI, rozloženie a grafika GUI, animované ukážky, testy, galéria.
- Codex: slovenské texty, gramatika, štylistika, názvy a popisy v UI.
- Čokoľvek mimo svojej oblasti sa najprv navrhne a schváli používateľom.

## Pravidlá
1. Nespúšťaj hru bez vyžiadania.
2. Nemeň herné pravidlá ani herný engine (`game/`), pokiaľ to používateľ výslovne nechce.
3. Nemeň dokončené animácie (Dražba, Talón, Bodovanie, Pravidlá štichov) ani záložku „Prehľad bodovania“, okrem toho, čo je zadané.
4. Pri zmene rozloženia ovládania (Predchádzajúce / Ďalšie / Pozastaviť, bodky, počítadlo) nemeň ich správanie. Dedí sa to z `TrickRulesDemo`.
5. Pred úpravou súboru ho zapíš do `HANDOFF.md` ako „v práci“. Po dokončení zapíš výsledok.
6. Agenti nekomitujú, nepushujú a nemenia vetvy. Na konci napíš zoznam zmenených súborov a návrh commit message; commitne používateľ v GitKrakene.
7. Pred hotovou prácou spusti testy: `tester/regression_layout.py` a `tester/regression_rules_demo.py` musia prejsť. Stopa hry (`tester/regression_screen`) sa nesmie zmeniť, ak nejde o zadanú zmenu.
8. Ak niečo nie je jasné, najprv sa opýtaj.

## Štýl
- Komentáre v slovenčine, identifikátory v angličtine.
- Texty v UI píš správnou slovenčinou s diakritikou a konzistentnými názvami (napr. „Prehľad bodovania“, „Štichy a tromfy“).
- Nové animácie: podtrieda `TrickRulesDemo`, scény v `SCENES`, časovanie cez `SCENE_LEN` a `HOLD_AT`.

## Kde čo je
- `gui/rules_demo.py`: základ animovaných ukážok, ovládanie, `layout()`.
- `gui/scoring_demo.py`, `gui/round_demos.py`: vzorové ukážky (Bodovanie, Dražba, Talón).
- `gui/trump_demo.py`: placeholder „Hlásenie tromfu“.
- `gui/info_overlay.py`: okno Pravidlá a bodovanie, záložky a kroky.
- `game/ai_strategy.py`, `game/ai_evaluator.py`: AI logika.
- `CLAUDE.md`: podrobný popis projektu a variantu „tromf aj v 1. štichu“.
