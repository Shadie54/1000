# HANDOFF.md — stav projektu 1000

Posledná aktualizácia: 2026-10-30

## Stav kódu
- Vetva `master`, commit `90dd96` „Rules update“. Pracovný strom bol čistý.
- Hotové: rozloženie animovaných ukážok na celú šírku, centrované ovládanie (Predchádzajúce / Ďalšie vedľa seba, Pozastaviť / Prehrať s odstupom), záložka „Štichy a tromfy“ s podzáložkami Pravidlá štichov a Hlásenie tromfu.
- Testy k poslednému stavu prešli: `regression_layout` pri všetkých 15 rozlíšeniach, `regression_rules_demo`, scenár záložiek.

## Otvorené úlohy
1. **Hlásenie tromfu – animované vysvetlenie.** Implementované pre oba varianty. Používateľ určil Pravidlá štichov ako záväzný vzor; rozloženie a výtvarný koncept zjednotené, čaká na používateľovu vizuálnu kontrolu a doladenie pracovných textov.
2. **Krok Rozdanie – animácia.** Zatiaľ len obrázok a popis. Nezačaté.
3. **Pravidlo prvého kola.** Podľa zadania sa má obligácia v prvom kole určiť náhodne, v hre je vždy Hráč (`obligation_index=0`). Čaká na rozhodnutie používateľa. Zatiaľ sa nemení.
4. **Bodovanie pri 1920×1200.** Prázdny priestor nad a pod blokmi. Kozmetická úprava, nie je naliehavá.
5. **Texty animácií** sú pracovné návrhy. Používateľ ich ešte bude upravovať.
6. Voliteľné: ikona `sort.png`.

## Rozhodnutia
- Ovládanie ukážok sa riadi jedným miestom (`TrickRulesDemo.layout`), zmena sa dedí do všetkých ukážok.
- Bodky scén sú vľavo, aby nedelili skupinu tlačidiel.
- Počítadlo snímok zostáva vpravo hore.
- Pravé panely pri ukážkach sa neobnovujú; obsah ide do animácií.

## Ako pokračovať
- Pred začatím: `git status` v GitKrakene musí byť čistý.
- Po úprave: spusti testy, zapíš zmeny sem a navrhni commit message.
- Commitne používateľ.

## Dokončené — zjednotenie Hlásenia tromfu (Codex, 2026-10-30)
- `gui/trump_demo.py`: prevziať koncept Pravidiel štichov bez zmien šablóny; používateľ výslovne zadal tento vzor.
- `HANDOFF.md`: zaznamenať výsledok a overenia.
- Vstupný pracovný strom už obsahuje zmeny v `gui/info_overlay.py`, `gui/trump_demo.py`, `tester/regression_rules_demo.py` a nové AGENTS.md/HANDOFF.md; cudzie zmeny zachovať.

### Výsledok
- `gui/trump_demo.py`: odstránené vlastné rozloženie, zmenšovanie kariet a presúvanie ruky. Rozloženie, menovky, ruka vpravo dole a ovládanie sa dedia priamo z `TrickRulesDemo`.
- Pohyb kariet používa rovnaké štartovacie a cieľové pozície, oblúky, časovanie zahrania, rámčeky a ikony výsledku ako Pravidlá štichov. Prevzaté sú aj nábeh a dobeh scén; dĺžka scén zostáva 14 s pre viacfázové príklady.
- Zachované oba varianty hlásenia, príklady a ich overovanie; odstránený samostatný pravý panel tromfu. Aktuálny tromf používa poznámku vľavo hore zo šablóny.
- `gui/rules_demo.py`, herný engine, existujúce ukážky aj cudzie úpravy v ostatných súboroch zostali bez zásahu.
- Overenia: `tester/regression_rules_demo.py` prešiel; `tester/regression_layout.py` prešiel pri všetkých 15 rozlíšeniach a oboch smeroch hry; 167-riadková stopa `tester/regression_screen.py` pred/po je identická.
- Vizuálne skontrolované vykreslené scény dvojice, potvrdenia hlášky, zmeny tromfu a neskoršieho získania štichu pri 1920×1080; bežné okno hry sa nespúšťalo.
- Zmenené v tomto kroku: `gui/trump_demo.py`, `HANDOFF.md`. Bez commitu a bez zmeny vetvy.
- Návrh commit message: `Zjednotiť hlásenie tromfu podľa ukážky pravidiel štichov`.

## Dokončené — herný panel tromfu v ukážkach (Codex, 2026-10-30)
- `gui/rules_demo.py`: nahradiť poznámku tromfu skutočným panelom zo Scoreboard; výslovne zadaná zmena šablóny.
- `gui/trump_demo.py`: doplniť meno hlásiaceho a odstrániť prekryv krátkej správy s panelom v oboch variantoch.
- `HANDOFF.md`: výsledok a overenia.

### Výsledok
- Spoločná metóda v `gui/rules_demo.py` používa priamo `Scoreboard._draw_trump_panel` z hry, s rovnakým rámom, nadpisom, ikonou, názvom farby a bodmi. Panel sa kreslí v mierke ukážky medzi menovkami hráčov nad stredom stola.
- Používa sa v Pravidlách štichov a oboch variantoch Hlásenia tromfu. V hlásení zobrazuje aj meno hráča; mení sa spolu s nahláseným tromfom. Krátka správa na jeho mieste sa pri zobrazení panelu nekreslí.
- V Pravidlách štichov sa meno hlásiaceho nevymýšľa, pretože príklady ho neurčujú.
- Overenie: `regression_rules_demo.py` OK; `regression_layout.py` všetkých 15 rozlíšení OK; 167-riadková stopa `regression_screen.py` zhodná s predchádzajúcim stavom. Vizuálne skontrolované vykreslenie panelu v Pravidlách štichov a Hlásení tromfu bez spustenia bežného okna hry.
- Zmenené v tomto kroku: `gui/rules_demo.py`, `gui/trump_demo.py`, `HANDOFF.md`. Herný Scoreboard zostáva bez úprav.
- Návrh commit message: `Použiť herný panel tromfu v animovaných ukážkach`.

## Dokončené — panel KOLO a časovanie Hlásenia tromfu (Codex, 2026-10-30)
- `gui/trump_demo.py`: panel KOLO podľa herného panela a Talónu, oba varianty, prvá scéna 11 s namiesto 14 s.
- `gui/rules_demo.py`, `gui/scoreboard.py`: voliteľné skrytie bodov v paneli tromfu pre Pravidlá štichov; hra zachová predvolené zobrazenie.
- `HANDOFF.md`: výsledok a overenia.

### Výsledok
- Hlásenie tromfu zobrazuje zjednodušený herný panel KOLO vľavo dole: Fáza: Štichy a Štich: 1 / 10 alebo 2 / 10; v zmene tromfu neskorší 3. štich. Využíva rovnaké kreslenie pozadia, hlavičky a riadkov ako herný Scoreboard; obsah je vybraný podobne ako v ukážke Talónu.
- Variant hlásenia v 1. štichu pridáva Povinnosť: Hráč / 100 alebo 110 (ukážka hranice), po nahlásení aj Aspoň 1 štich: chýba, po získaní neskoršieho štichu splnené. Panel KOLO aj TROMF sú v relevantných scénach súčasne.
- Prvá scéna Kráľ a horník má 11 s namiesto 14 s v oboch variantoch; ostatné zostávajú 14 s. Opravené počítanie prechodu pri rozdielnych dĺžkach scén. Overené automatické prechody aj ručný výber a čas zastavenia.
- Pravidlá štichov nezobrazujú body v paneli tromfu. Voliteľný parameter show_points v Scoreboard má predvolenú hodnotu True, preto herná obrazovka a Hlásenie tromfu body naďalej zobrazujú.
- Overenie: regression_rules_demo OK; regression_layout všetkých 15 rozlíšení OK; regression_screen 167 riadkov identických s predchádzajúcim stavom; vizuálne overené oba panely, chýbajúci/splnený štich, klasický variant a skrytie bodov. CRLF zachované, diff bez chýb bielych znakov.
- Zmenené v tomto kroku: gui/trump_demo.py, gui/rules_demo.py, gui/scoreboard.py, HANDOFF.md. Bez commitu a bez zmeny vetvy.
- Návrh commit message: Doplniť panel kola do hlásenia tromfu a upraviť časovanie ukážok.

## Dokončené — sústredená animácia (Codex, 2026-10-30)
- gui/info_overlay.py: prehľad/fokus, návrat, kompaktná hlavička a rozšírené javisko; zachovať stav.
- gui/trump_demo.py: umiestnenie KOLO do oblasti vysvetlenia v rozšírenom režime.
- tester/regression_focus.py: navigácia, podzáložky a ovládanie, rozšírené rozloženie.
- HANDOFF.md: výsledok a testy.

### Výsledok
- Prehľad Pravidiel zachováva Cieľ hry, päť fáz Priebehu kola a pôvodné ilustrácie/popisy. Klik na fázu otvorí sústredený režim s hlavičkou, návratom, existujúcim počítadlom scén a podzáložkami.
- Späť aj Escape vrátia prehľad bez resetu scény, podzáložky či stavu prehrávania; čas na prehľade sa odpočíta od hodín ukážok. Krížik zatvára celé okno. Na prehľade zostávajú dostupné hlavné záložky.
- Fokus využíva celú plochu pod kompaktnou hlavičkou. Existujúce layout() komponenty dostávajú väčší obdĺžnik, takže pri FHD má javisko 804 namiesto 408 logických pixelov na výšku, bez prepisovania scén a časovania.
- Panel KOLO v Hlásení tromfu sa pri dostatku výšky zoskupuje vpravo pod vysvetlením; pri nízkom širokom okne zostáva na stole, aby neprekryl ruku.
- Rozdanie zachováva pôvodný statický obrázok a popis, nevytvárala sa nová animácia ani ovládanie neexistujúcich scén. Texty, pravidlá, obsah scén a dĺžky bez zmien.
- Overené: regression_focus (všetkých 5 fáz, 3 podzáložky, predchádzajúce/ďalšie/bodky/prehrávanie, návrat a zmrazenie času) pri 1920x1080, 1280x720, 1920x1200, 3440x1440 a 1024x768; rozšírené rozloženie všetkých scén bez presahov. regression_layout všetkých 15 rozlíšení OK; regression_rules_demo OK; regression_screen stopa 167 riadkov identická.
- Vizuálne skontrolované FHD snímky rozšírenej Dražby, Talónu, Hlásenia tromfu a prehľadu, vykreslené aplikáciou bez viditeľného okna.
- Zmenené v tomto kroku: gui/info_overlay.py, gui/trump_demo.py, tester/regression_focus.py, HANDOFF.md. Bez commitu a zmeny vetvy.
- Návrh commit message: Pridať režim sústredenej animácie do tutoriálu pravidiel.
