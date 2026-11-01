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

## Dokončené — viditeľné ruky a zahrávanie (Codex, 2026-10-30)
- gui/rules_demo.py a gui/trump_demo.py: spoločný viditeľný pôvod, otočenie a odstránenie zahranej karty; len Štichy a tromfy.
- tester/regression_card_play.py: kontrola pôvodu, poradia, odstránenia a rozloženia.
- HANDOFF.md: výsledky. V aktuálnej verzii týchto dvoch súborov nie je zberný pohyb, iba výsledné zvýraznenie víťaza; zachovať ho.

### Výsledok
- Iba sústredené Štichy a tromfy používajú stabilné pozície Počítač 1 hore vľavo, Počítač 2 hore vpravo a Hráč dole. Rubové ruky počítačov, lícová ruka hráča a cieľové pozície sú oddelené od pravých vysvetlení a panelov.
- Spoločné _play_from_hand kreslí konkrétnu kartu iba raz: najprv v ruke, potom po oblúku do štichu. Počítačová karta sa počas letu otočí rub/líce cez zúženie šírky. Dve zostávajúce rubové karty sú na pôvodnom mieste; hráčova zahraná karta nezanecháva priesvitnú kópiu.
- Použité na classic/win, zahratie pri hlásení/effect/change, vynesenie a odpovede v Pravidlách štichov a výsledný štich. Karty počítačov v neaktívnych rukách zostávajú viditeľné aj pri vysvetľovaní dvojice a hlásenia. Ukážkové ruky nemusia mať desať kariet.
- Počet scén, texty, dĺžky scén, existujúce časy zahrávania a zvýraznenie víťaza bez zmien. Pôvodný statický výnos v odpovediach má teraz krátky pohyb pred existujúcou odpoveďou hráča. Pravidlá/engine ani ostatné fázy bez zásahu.
- Poznámka k zadaniu: aktuálne rules_demo.py/trump_demo.py neobsahujú samostatnú animáciu zbierania štichu, iba označenie víťaza. Nebola odstránená ani nahradená žiadna existujúca zberná animácia.
- Overené: regression_card_play pri 1920x1080, 3440x1440 a 1024x768 (pôvod, otočenie, odstránenie, poradie, výsledok, oddelenie ostatných fáz); regression_focus pri rovnakých troch rozlíšeniach vrátane ovládania a presahov všetkých scén; regression_layout všetkých 15 rozlíšení OK; regression_rules_demo OK. Herná stopa regression_screen má 167 riadkov identických s predchádzajúcim stavom.
- Vizuálne kontrolované FHD snímky classic pred zahratím, počas letu, po otočení a na výsledku; aj hlásenie a oddelenie hráčovej ruky od štichu. Kontrola vykreslením aplikácie bez viditeľného okna.
- Zmenené: gui/rules_demo.py, gui/trump_demo.py, tester/regression_card_play.py, HANDOFF.md. Bez commitu a zmeny vetvy.
- Návrh commit message: Zjednotiť zahrávanie kariet z viditeľných rúk v tutoriáli.

## Dokončené — choreografia klasického hlásenia (Codex, 2026-10-30)
- gui/trump_demo.py: iba päť scén variantu od 2. štichu, presná ruka, rozhodnutia, bubliny SpeechBubble a dve ukážky zberu.
- tester/regression_classic_trump.py: udalosti, herné pravidlá, body, časovanie a reset.
- HANDOFF.md: výsledok. Aktuálne zberný pohyb v tomto tutoriáli chýba; doplniť lokálne s existujúcimi oblúkmi, bez zmeny ostatných variantov.

### Výsledok
- Zmeny sú izolované do vetvy TrumpDemo(first_trick_trump=False). Druhý variant, Pravidlá štichov, ostatné fázy a vysvetľujúce texty zostávajú zachované.
- 1/5: presná ruka leaf-ace, acorn-king, acorn-over, heart-ten; statická zvýraznená dvojica, bez zahrania.
- 2/5: simulovaný výber horníka, neaktívna voľba Tromf: Žaluď, vizuálny pokus o kliknutie a herná informačná bublina. Výber aj tlačidlá sa zrušia bez aktivácie tromfu. Hráč vynesie zelené eso, počítače priznajú zeleň, hráč berie štich; od 10,5 s panel ukazuje 2 / 10.
- 3/5: zachovaný začiatok zahrania; aktívne rozhodnutie pulzuje, simulovaný klik, od 4,5 s tlačidlá zmiznú a karta zostáva na stole; štich sa nedohráva.
- 4/5: zachované zahranie a panel; úspech oznamuje priamo herný SpeechBubble.show_trump.
- 5/5: žaluďové eso počítača 1 berie štich s priznaním farby; následne tento počítač začína nový štich a zahráva guľového horníka zo svojej dvojice. Až od 8,3 s sa mení tromf a zobrazuje NOVÝ TROMF! cez SpeechBubble; Hráčových 100 bodov zostáva, počítaču pribudne 60. Nový štich sa nedohráva.
- Dĺžky klasických scén sú 11 / 16 / 11 / 11 / 14 s; reset a zastavenie na výsledku používajú existujúce časové rozhranie. Zber v ukážkach 2 a 5 používa lokálny oblúk/fade k víťazovi; ostatné existujúce pohyby a varianty sa nemenia. Simulácia nemení skutočný stav rozohratej hry.
- Overenia: regression_classic_trump pri FHD, 3440x1440 a 1024x768 (herné pravidlá, obidva štichy, bodovanie, udalosti, reset a presahy); regression_focus OK, regression_card_play OK, regression_layout všetkých 15 rozlíšení OK, regression_rules_demo OK. regression_screen stopa 167 riadkov identická s predošlou.
- Vizuálne skontrolovaných 12 FHD snímok zo všetkých piatich scén vrátane neaktívnej voľby, úspešného hlásenia, oboch zberov a novej farby. Kontrola vykreslením aplikácie bez viditeľného okna.
- Zmenené v tomto kroku: gui/trump_demo.py, tester/regression_classic_trump.py, HANDOFF.md. Predchádzajúce nekomitnuté zmeny zachované. Bez commitu a zmeny vetvy.
- Návrh commit message: Prepracovať päť scén klasického hlásenia tromfu.

## Dokončené — nadväznosť klasických scén (Codex, 2026-10-30)
- gui/trump_demo.py: fajočky dvojice, stlačenia podľa Dražby, polohy bublín, vysunutie v 3/5, odstránené eso a nadviazanie 5/5 na horníka zo 4/5.
- tester/regression_classic_trump.py: kontinuita rúk a horníka, prázdny panel v 3/5.
- HANDOFF.md: výsledok a overenia.

### Výsledok
- 1/5: zelené fajočky na kráľovi aj horníkovi.
- 2/5: stlačenia majú rovnaký efekt posunu o 2 px, tieňa a zvýraznenia ako Dražba; aktívne tlačidlá využívajú priamo _RoundDemo._press. Zakázaná voľba zostáva neaktívna. Informačná bublina je nad rukou hráča.
- 3/5: ruka už neobsahuje zelené eso; horník sa iba plynulo vysunie bez fajočky, neletí na stôl. Panel tromfu zobrazuje zatiaľ žiadny počas celej scény. Klik používa efekt Dražby.
- 4/5: eso odstránené, zachované zahranie horníka. Bublina TROMF! je nad červenou desiatkou pri hráčovi.
- 5/5: začína horníkom na stole a zvyšnými dvoma kartami v ruke zo 4/5. Zmizne iba fajočka; scéna sa na začiatku nerozplýva. Žaluďová sedma odstránená. Počítač 1 berie štich aj s už zahraným horníkom a následne hlási guľu. Číslo štichu nadväzuje 2 / 10 → 3 / 10. Jeho bublina je pri jeho ruke a chvost smeruje k nej.
- Opravené prenášanie starej bubliny hráča do scény počítača; každý výučbový oznam vykresľuje iba aktuálnu bublinu.
- Overenie: regression_classic_trump pri 1920x1080, 3440x1440 a 1024x768; doplnené overenie kontinuity rúk, prázdneho panelu, neprítomnosti esa/sedmy a horníka na stole od t=0. regression_focus OK; regression_layout všetkých 15 rozlíšení OK; regression_rules_demo OK; regression_screen 167 riadkov identických s predchádzajúcim stavom.
- Vizuálne skontrolované FHD snímky polôh bublín, vysunutej karty, prázdneho panela a novej hlášky bez presvitania starej bubliny; vykreslením bez viditeľného okna.
- Zmenené v tomto kroku: gui/trump_demo.py, tester/regression_classic_trump.py, HANDOFF.md. Bez commitu a zmeny vetvy.
- Návrh commit message: Doladiť nadväznosť kariet, kliknutia a bubliny hlásenia tromfu.

## Dokončené — slučky scén 2–5 (Codex)
- gui/trump_demo.py, tester/regression_classic_trump.py, HANDOFF.md: samostatné opakovanie klasických scén 2–5 aj po ručnom výbere.

- Výsledok: klasické scény 2–5 opakujú vlastný obsah bez automatického posunu na ďalšiu scénu; ručný výber spustí slučku. Pozastavenie/pokračovanie ostáva funkčné. Scéna 1 a druhý variant zachovávajú pôvodné správanie.
- Overenie: regression_classic_trump vrátane dvoch úplných slučiek každej scény a pauzy/pokračovania OK; regression_rules_demo OK; regression_layout všetkých 15 rozlíšení OK. Iba časovač tutoriálu, herná logika a kreslenie bez zásahu.
- Zmenené: gui/trump_demo.py, tester/regression_classic_trump.py, HANDOFF.md. Návrh commitu: Opakovať klasické scény hlásenia tromfu 2–5 v slučke.

## Dokončené — opakovanie bez stmavenia (Codex)
- gui/trump_demo.py, HANDOFF.md: odstrániť nábeh a dobeh priehľadnosti klasických scén 2–5; ponechať vnútorné animácie.

- Klasické scény 2–5 zachovávajú plnú viditeľnosť pri konci aj začiatku slučky; reštart priamy, bez stmavenia celého obsahu. Dĺžky scén, vnútorný pohyb/zber kariet, navigácia a druhý variant bez zmeny.
- Overenie: regression_classic_trump a regression_rules_demo OK; regression_layout všetkých 15 rozlíšení OK.
- Zmenené: gui/trump_demo.py, HANDOFF.md. Návrh commitu: Odstrániť stmievanie pri opakovaní scén hlásenia tromfu.

## Dokončené — kratšie slučky a bubliny pri kartách (Codex)
- gui/trump_demo.py, HANDOFF.md: skrátiť dobeh scén 2/5 a 3/5; úspešné hlásenia ukotviť pri zahranej karte namiesto ruky.

- Scéna 2 trvá 11 namiesto 16 s (reštart pol sekundy po prechode počítadla na 2/10); scéna 3 trvá 5 namiesto 11 s (reštart pol sekundy po potvrdení). Priebeh akcií bez zrýchľovania.
- Úspešné tromfové bubliny pri žaluďovom aj guľovom horníkovi sú napravo od zahranej karty; chvost smeruje ku karte. Zakázané hlásenie zostáva nad rukou.
- regression_classic_trump, regression_rules_demo a regression_layout (15 rozlíšení) OK. Zmenené: gui/trump_demo.py, HANDOFF.md. Návrh commitu: Skrátiť prestoje slučiek a ukotviť hlásenia pri kartách.

## Dokončené — ruky počítačov v 5/5 (Codex)
- gui/trump_demo.py, gui/rules_demo.py, tester/regression_classic_trump.py, HANDOFF.md: zachovať dve karty a pôvodné sloty po zbere, ďalší výnos zo správneho slotu.

- Príčina: po zbere sa počítaču 2 kreslila pôvodná trojkartová ruka namiesto dvoch zostávajúcich kariet. Teraz zostávajú v slotoch 1 a 2 počas celého zvyšku scény. Počítač 1 vynáša guľového horníka zo slotu 2; kráľ zostáva v slote 1. Spoločný helper má voliteľný origin, predvolené správanie nezmenené.
- Doplnený regresný test počtu a presných pozícií pri 5,9 / 6 / 6,8 / 8,4 / 12 s. regression_classic_trump, regression_rules_demo a regression_layout (15 rozlíšení) OK.
- Zmenené: gui/trump_demo.py, gui/rules_demo.py, tester/regression_classic_trump.py, HANDOFF.md. Návrh commitu: Opraviť kontinuitu rúk počítačov pri zmene tromfu.

## Dokončené — doladenie hlásenia v 1. štichu (Codex)
- gui/trump_demo.py: vzor klasickej záložky, stabilné sloty a ubúdanie kariet počas troch štichov, bubliny, rozhodnutia, slučky.
- tester/regression_first_trump.py: pravidlá nadväzujúcich štichov, kontinuita a počty rúk.
- HANDOFF.md: výsledok.

- V práci aj tester/regression_classic_trump.py: aktualizovať kontrolu dĺžky prvej scény druhého variantu (teraz 6 s podľa nového konceptu).

### Výsledok
- Hlásenie v 1. štichu používa klasickú záložku ako vzor: zvýraznenie dvojice s fajočkami, vysunutie karty pred rozhodnutím, rovnaké stlačenie tlačidiel z Dražby, prázdny panel pred hlásením, herné bubliny ukotvené pri zahranej karte, samostatné slučky bez stmievania a krátke dobehy.
- Zachovaných 7 scén a všetky vysvetľujúce texty. Dĺžky sú 11/6/7/5/7/13/14 s. Hranica povinnosti 100/110 v ukážke ostáva; panel KOLO po hlásení zobrazuje chýbajúci a následne splnený štich.
- Nadväznosť kola: horník z úvodného hlásenia je zahraný od začiatku scény získania štichu. Prvý štich berie počítač 1 žaluďovým esom; druhý začína žaluďovou osmou a hráč ho získa žaluďovou desiatkou. Potom hráč vynáša srdcovú sedmu, počítač 1 získa tretí štich srdcovým esom a vo štvrtom hlási guľu. Predchádzajúcich 100 bodov zostáva.
- Každá ruka má pevné sloty a zoznam konkrétnych kariet; zahrané karty sa nevracajú, zvyšné nemenia miesta. Na konci zostáva hráčovi žaluďový kráľ, počítaču 1 guľový kráľ a počítaču 2 žiadna z ukážkových kariet. Ide o výučbový výrez, nie úplné desaťkartové rozdanie.
- Klasické scény obsahovo ani choreograficky nezmenené. Ostatné fázy bez zásahu.
- Overenia: regression_first_trump pri 1920x1080, 3440x1440, 1024x768 (legálne karty v nadväzujúcich rukách, víťazi, ubúdanie a stabilné sloty, slučky, pauza a presahy); regression_classic_trump a regression_focus OK; regression_layout všetkých 15 rozlíšení OK; regression_rules_demo OK. regression_screen stopa 167 riadkov zhodná s predchádzajúcou.
- Vizuálne overené FHD snímky rozhodnutia, hlásenia, splnenia podmienky štichu a novej farby s ubúdajúcimi rukami; vykreslením aplikácie bez viditeľného okna.
- Zmenené v tomto kroku: gui/trump_demo.py, tester/regression_first_trump.py, tester/regression_classic_trump.py (očakávaná dĺžka scény), HANDOFF.md. Bez commitu a zmeny vetvy.
- Návrh commit message: Zjednotiť hlásenie v prvom štichu a zachovať kontinuitu kariet.

## Dokončené — päť kariet pre každého (Codex, 2026-10-31)
- gui/trump_demo.py, tester/regression_first_trump.py, HANDOFF.md: zjednotiť úvodné ruky variantu v 1. štichu na päť, zachovať legálnosť a stabilné sloty.

- V druhom variante má každá ruka na začiatku presne päť rôznych kariet (spolu 15 unikátnych). Hráčovi doplnené zelené eso, počítaču 2 zelený kráľ a guľová deviatka; nezahrávajú sa a nemenia legálnosť troch štichov. Počítač 1 bez zmeny. Ubúdanie a pôvodné sloty zachované.
- regression_first_trump (FHD a širokouhlé), regression_rules_demo a regression_layout (15 rozlíšení) OK.
- Zmenené: gui/trump_demo.py, tester/regression_first_trump.py, HANDOFF.md. Návrh commitu: Zjednotiť úvodné ruky na päť kariet v hlásení prvého štichu.

## Dokončené — zelený dolník ako piata karta (Codex, 2026-10-31)
- gui/trump_demo.py, tester/regression_first_trump.py, HANDOFF.md: iba výmena piatej karty hráča v druhom variante.

- Piata karta hráča v hlásení v 1. štichu je leaf-under (zelený dolník), namiesto leaf-ace. Klasický variant nezmenený. regression_first_trump, regression_rules_demo a regression_layout (15 rozlíšení) OK.
- Zmenené: gui/trump_demo.py, tester/regression_first_trump.py, HANDOFF.md. Návrh commitu: Nahradiť piate eso zeleným dolníkom v ukážke hlásenia.

## Dokončené — označenie voliteľného hlásenia (Codex, 2026-10-31)
- gui/info_overlay.py: nový názov tretej záložky.
- gui/trump_demo.py: upozornenie s oddeľovačom iba v paneli scény 1/7.
- HANDOFF.md: výsledok a overenie.

- Tretia záložka má názov Hlásenie v 1. štichu (voliteľné). Iba scéna 1/7 rozširuje existujúci textový panel o jemný oddeľovač a presne zadané upozornenie menším písmom; text sa zalamuje podľa šírky panela. Ostatné scény aj klasický variant bez zmeny.
- Vizuálna kontrola FHD vykreslenia OK; regression_first_trump, regression_rules_demo a regression_layout (15 rozlíšení) OK.
- Zmenené: gui/info_overlay.py, gui/trump_demo.py, HANDOFF.md. Návrh commitu: Označiť hlásenie v prvom štichu ako voliteľné a doplniť upozornenie.

## Dokončené — globálne slučky tutoriálu (Codex, 2026-10-31)
- gui/rules_demo.py, gui/trump_demo.py: spoločné slučky bez automatického posunu, každý ručný výber prehráva slučku, presná pauza/pokračovanie.
- tester/regression_classic_trump.py: nové spoločné správanie prvej scény.
- tester/regression_tutorial_loops.py: všetky scény všetkých animovaných fáz.
- HANDOFF.md: výsledok.

- Všetky animované ukážky (Pravidlá štichov, oba varianty hlásenia, Dražba, Talón, Bodovanie) dedičia spoločnú slučku aktuálnej scény. Automatický posun je odstránený aj z prvej scény. Ručný výber okamžite spúšťa opakovanie; navigácia a bodky ostávajú. Pozastavenie a pokračovanie zachová presný čas aj tesne pred koncom. Rozdanie ostáva statické.
- regression_tutorial_loops overuje každú scénu každej ukážky cez tri cykly a pauzu na konci; regression_focus, regression_classic_trump, regression_first_trump, regression_rules_demo a regression_layout (15 rozlíšení) OK.
- Zmenené: gui/rules_demo.py, gui/trump_demo.py, tester/regression_classic_trump.py, tester/regression_tutorial_loops.py, HANDOFF.md. Návrh commitu: Opakovať každú scénu tutoriálu bez automatického posunu.

## Dokončené — dvojstĺpcový prehľad (Codex, 2026-10-31)
- gui/info_overlay.py: šesť kapitol, predvolený Cieľ hry, obsah, pôvodné ilustrácie a samostatné otvorenie ukážky.
- tester/regression_focus.py: dvojkrokové otvorenie a zachovanie vybranej kapitoly.
- HANDOFF.md: výsledok.

### Výsledok
- Nové dvojstĺpcové menu: šesť zvislých položiek s pôvodnými grafickými kompozíciami, titulkom, podnadpisom a zvýraznením výberu. Cieľ hry je predvolený pri otvorení okna; používa trofej.
- Klik na kapitolu iba mení pravý obsah. Samostatné tlačidlo otvára existujúci sústredený režim; návrat zachová kapitolu aj animačný stav. Hlavné záložky, podzáložky, slučky a navigácia zostávajú.
- Pravý panel: hlavička s tmavým dreveným podkladom, opis, väčšia pôvodná ilustrácia, tri výučbové ciele, tri stručné údaje a otváracie tlačidlo. Cieľ hry nemá otváracie tlačidlo: obsahuje šesť prehľadných blokov základných pravidiel vrátane sekcie Čo sa naučíš.
- Údaje vychádzajú z kódu hry: 3 hráči, 32 kariet, 10 na hráča a 2 v talóne; nesprávnych 24 kariet z referencie sa nepoužilo. Obsah vysvetľuje povinnosť, talón, štichy, tromfové hlášky a výsledok kola.
- Ikony sú z pôvodných kompozícií, vykreslené do jednotných rámčekov bez presahov; pravé ilustrácie sa zväčšujú v rámci dostupného priestoru. Návrh kopíruje iba štruktúru referencií, používa existujúce panely, typografiu, farby a materiály hry.
- Rozdanie stále nemá vlastnú animáciu. Tlačidlo otvorí pôvodnú statickú ukážku v rozšírenom režime; upozornenie pri tlačidle to výslovne uvádza. Nová animácia sa nevytvárala.
- Overenie: regression_focus doplnený o nové menu, predvolený cieľ, textové hranice všetkých šiestich kapitol a návrat na vybranú kapitolu. Samostatne overené hranice pri 1920x1080, 3440x1440 a 1024x768. regression_layout všetkých 15 rozlíšení OK; regression_rules_demo OK; regression_screen stopa 167 riadkov identická.
- Vizuálne skontrolované FHD snímky Cieľa hry, Rozdania, Dražby a Štichov, vykreslené aplikáciou bez viditeľného okna. Opravený presah malej ikony Dražby zachytený pri prvej kontrole.
- Zmenené v tomto kroku: gui/info_overlay.py, tester/regression_focus.py, HANDOFF.md. Bez commitu a zmeny vetvy.
- Návrh commit message: Prepracovať prehľad pravidiel na dvojstĺpcové menu kapitol.

## Dokončené — finálne náhľady kapitol pravidiel (Claude, 2026-10-31)
- gui/info_overlay.py: pravý panel kapitol (Pravidlá a bodovanie → Pravidlá) prepracovaný podľa zadania.

### Výsledok
- Odstránená sekcia „Čo sa naučíš“ aj tri spodné informačné kartičky (CHAPTER_LESSONS, CHAPTER_FACTS). Nové rozloženie: názov kapitoly, podnadpis (KAPITOLA N/5), krátky schválený opis, veľký obrázkový náhľad a pri kapitolách 1–5 tlačidlo „Otvoriť animovanú ukážku“ (pri Cieli hry sa nezobrazuje).
- Texty kapitol (CHAPTER_DESCRIPTIONS) zodpovedajú presne zadaniu z 2026-10-31 (Cieľ hry, Rozdanie, Dražba, Talón, Štichy a tromfy, Bodovanie).
- Obrázky zo skutočnej hry (assets/graphics/rules/): Cieľ hry a Dražba/Talón/Štichy a tromfy automaticky striedajú viac obrázkov (4 s na obrázok, 0,5 s crossfade, plynulá slučka), Rozdanie a Bodovanie sú statické. Nová kapitola → slučka vždy začína od prvého obrázka.
- Obrázky sa škálujú bez deformácie (zachovaný pomer strán) a vycentrujú v dostupnej ploche — bez orezania. Kód skúša názov súboru aj s príponou navyše (`name.png` ako záložný pokus), takže funguje aj so súčasnými súbormi `dealing_cards.png.png` a `game_goal_round_end.png.png` na disku — odporúčam premenovať na `dealing_cards.png` a `game_goal_round_end.png` (odstrániť zdvojenú príponu), kód potom funguje rovnako.
- Ľavá navigácia (6 kapitol, ikonky, zvýraznenie) a existujúce animácie bez zmeny; tlačidlo stále otvára príslušnú existujúcu ukážku a návrat zachováva vybranú kapitolu.
- Overenia: regression_rules_demo, regression_focus (vrátane testu, že všetkých 6 kapitol vrátane Cieľa hry nemá textový/obrázkový presah), regression_classic_trump, regression_first_trump, regression_card_play, regression_tutorial_loops a regression_layout (15 rozlíšení) OK. Doplnená ručná kontrola obsahovania obrázka (_fit) pri strede crossfade (viac časových bodov) pre všetky kapitoly pri FHD, 1024×768, 1280×720, 2560×1600 a 3440×1440 — bez presahu. Herná stopa (regression_screen) nedotknutá, keďže zmena je len v gui/info_overlay.py (kreslenie okna Pravidlá), nie v hernom engine.
- Vizuálne skontrolované FHD snímky všetkých šiestich kapitol a snímka v strede prechodu (crossfade) pri Dražbe — text sa nezlieva s obrázkom, tlačidlo a poznámka pri Rozdaní sú čitateľné, obrázky vyplnia väčšinu plochy bez deformácie.
- Zmenené v tomto kroku: gui/info_overlay.py, HANDOFF.md. Bez commitu a zmeny vetvy.
- Návrh commit message: Prepracovať pravý panel kapitol na obrázkové náhľady zo skutočnej hry.

### Poznámka k obrázkom
Dva súbory v assets/graphics/rules majú zdvojenú príponu (`dealing_cards.png.png`, `game_goal_round_end.png.png`). Kód ich nájde aj takto, ale pre poriadok odporúčam premenovať na jednoduchú príponu `.png` priamo v Exploreri — žiadna ďalšia úprava kódu nebude potrebná.

## Dokončené — Rozdanie bez ukážky, zlúčenie scén a oprava presahu panela (Claude, 2026-10-31)
- gui/info_overlay.py: kapitola Rozdanie nemá tlačidlo „Otvoriť animovanú ukážku"; opravená aj samostatná hover funkcia.
- gui/trump_demo.py: zlúčenie scén 2+3 v variante „Hlásenie v 1. štichu (voliteľné)"; oprava presahu dvoch panelov.
- gui/rules_demo.py: rovnaká oprava presahu panela (spoločná báza, latentná chyba, ešte nevyvolaná).
- tester/regression_focus.py, regression_first_trump.py, regression_classic_trump.py: prispôsobené testy.

### Výsledok
- Rozdanie (kapitola 1): prehľad kapitoly (opis + galéria) teraz zaberá celú výšku pravého panela, tlačidlo a poznámka sú odstránené — všetko dôležité je vidno už v prehľade. Klik v danej oblasti teraz nič neotvára (`_chapter_open_rect` sa už nevyvoláva pre kapitolu 0).
- Nájdená a opravená súvisiaca chyba: `_draw_chapter_hover()` je samostatné prekreslenie nezávislé od statickej vrstvy a malo vlastnú podmienku na vykreslenie tlačidla — bez opravy sa tlačidlo „duchovito" zobrazovalo aj nad galériou Rozdania. Opravené rovnakou podmienkou ako v `_draw_chapters()`.
- Variant „Hlásenie v 1. štichu (voliteľné)": scény 2 (first) a 3 (bid) zlúčené do jednej scény „bid", keďže obe hovorili o dostatočne vysokej povinnosti a pôvodná scéna 2 samostatne nič poriadne nevysvetlila. Nový zlúčený text obsahuje konkrétny príklad (žaluďová hláška 100 → povinnosť aspoň 110). Scén je teraz 6 (bolo 7); vizuálna animácia disabled→enabled tlačidla hlásenia pri prekročení prahu zostala zachovaná.
- Počas overovania `regression_layout.py` sa pri 4 z 15 rozlíšení (1280x720, 1600x900, 1920x1080, 2560x1080) objavil presah javiska v scénach 2–6 tejto ukážky. Príčina: dlhší zlúčený text posunul spodnú hranicu textového panela nižšie, než počítali s rezervou dva samostatné výpočty pozície vedľajšieho panela (`_round_panel`, `_classic_empty_panel` v trump_demo.py) — oba umiestňovali panel na `text_box.bottom + 18` bez kontroly proti spodku javiska. Rovnaký nechránený vzor je aj v spoločnej základnej triede (`_draw_trump_note` v rules_demo.py, zdieľaná všetkými ukážkami štichov) — opravené preventívne, aj keď ešte nebol vyvolaný. Všetky tri miesta teraz obmedzujú `top` na `min(top, stage.bottom - 12*k - výška_panela)`.
- Overenia po oprave: regression_focus, regression_rules_demo, regression_tutorial_loops, regression_classic_trump, regression_first_trump, regression_card_play a regression_layout (všetkých 15 rozlíšení) OK. `layout_problems()` vrátil 0 problémov pri FHD aj vo všetkých rozlíšeniach v regression_layout.
- Herná stopa (regression_screen) nedotknutá — zmeny sú výhradne v kreslení okna Pravidlá, nie v hernom engine.
- Zmenené v tomto kroku: gui/info_overlay.py, gui/trump_demo.py, gui/rules_demo.py, tester/regression_focus.py, tester/regression_first_trump.py, tester/regression_classic_trump.py, HANDOFF.md. Bez commitu a zmeny vetvy.
- Návrh commit message: Odstrániť animovanú ukážku z Rozdania, zlúčiť scény hlásenia v 1. štichu a opraviť presah panela.

## Dokončené — galéria kapitol sa nehýbala (zamrznutá v statickej vrstve) (Claude, 2026-10-31)
- gui/info_overlay.py: kreslenie obrázkovej galérie presunuté mimo statickej vrstvy (cache).

### Výsledok
- Nahlásené userom: v náhľadoch kapitol (Cieľ hry, Dražba, Štichy a tromfy) bol vidno len jeden statický obrázok, hoci malo ísť o automatickú slučku viacerých.
- Príčina: celá metóda `_draw_chapters()` (vrátane volania `_draw_gallery()`) sa kreslí len z `_draw_static()`, ktorá je zabalená v `draw_static(...)` — statickej vrstve s cache kľúčom podľa záložky/kroku/kapitoly/fokusu. Kľúč sa nemení s časom, takže sa `_draw_gallery()` zavolala iba raz pri výbere kapitoly a odfotený obrázok (aktuálny v tom okamihu) zostal navždy — presne rovnaký mechanizmus, aký už predtým spôsoboval „duchovité" tlačidlo pri Rozdaní (tam to bolo opačne — niečo navyše kreslené mimo cache; tu niečo, čo *musí* byť mimo cache, bolo omylom v cache).
- Oprava: `_draw_chapters()` teraz iba vypočíta a uloží oblasť galérie (`self._gallery_rect`), nekreslí samotný obrázok. Skutočné vykreslenie `_draw_gallery(self._gallery_rect)` sa presunulo do `draw()` vedľa `_draw_chapter_hover()` — teda mimo cache, prekresľuje sa každú snímku, takže slučka a crossfade bežia normálne. `layout_problems()` (volá `_draw_static()` priamo, nie `draw()`) dostala vlastné dokreslenie galérie hneď po `_draw_static()`, aby `_fit` kontrola presahu obrázka zostala zachovaná.
- Overenia: ručný test cez `_gallery_state()` pri rastúcom `pygame.time.get_ticks()` potvrdil striedanie obrázkov a crossfade (predtým zamrznuté na indexe z okamihu vstupu do kapitoly). Celá sada: regression_focus, regression_rules_demo, regression_tutorial_loops, regression_classic_trump, regression_first_trump, regression_card_play, regression_layout (15 rozlíšení) OK. Herná stopa (regression_screen, 3 kolá) zhodná s ref_3kola.txt (zmena je iba v GUI kreslení, nie v engine).
- Zmenené v tomto kroku: gui/info_overlay.py, HANDOFF.md. Bez commitu a zmeny vetvy.
- Návrh commit message: Opraviť zamrznutú galériu náhľadov kapitol — kresliť mimo statickej vrstvy.

## Dokončené — obnovenie textov kapitol a náhodná povinnosť v 1. kole (Claude, 2026-10-31)
- gui/info_overlay.py: texty CHAPTER_DESCRIPTIONS (Cieľ hry, Dražba) podľa zadania "Obnovenie manuálne schválených textov".
- main.py: _create_game() — povinnosť v 1. kole novej hry je teraz náhodná.
- game/game_state.py: komentár pri obligation_index upresnený.
- ref_3kola.txt, ref_full.txt: prepočítané referenčné stopy (zmena je zámerná — ovplyvňuje aj poradie shuffle/AI pri rovnakom seede).

### Výsledok
- Kapitola **Cieľ hry**: text teraz hovorí len o cieli hry a podmienke výhry ({WINNING_SCORE} bodov), bez zmienky o dražbe (tá je už v kapitole Dražba).
- Kapitola **Dražba**: doplnená úvodná veta o náhodnom určení povinnosti na začiatku hry (uhradiť {MIN_BID} bodov, prednostný nárok na talón) a jej striedaní v smere hry v ďalších kolách; zvyšok textu (predbiehanie v ponukách, odstúpenie, záväzok víťaza) nezmenený.
- Kapitoly **Talón** a **Bodovanie**: zadanie žiadalo texty, ktoré už v kóde boli — bez zmeny.
- **Dôležité — zmena herného pravidla, nie len textu**: zadanie opisovalo náhodné určenie povinnosti v 1. kole, ale kód (`game_state.py: obligation_index = 0`) vždy začínal Hráčom — presne ten starý nevyriešený bod z archívu (17_VARIANT_TROMF_1_STICH.md). User sa pri doriešení rozhodol pre opravu kódu (nie len textu): `main._create_game()` teraz nastaví `game_state.obligation_index = random.randrange(len(game_state.players))` hneď po vytvorení `GameState`. Platí len pri novej hre (regression_screen.py ide presne touto cestou, takže ju testuje priamo); uloženie/obnova rozohratej hry (savegame) nie je týmto dotknuté — tam sa povinnosť načíta zo stavu.
- Dôsledok: referenčné stopy `ref_3kola.txt` a `ref_full.txt` (seed 20261024) sa pri rovnakom seede teraz líšia (1. kolo: povinnosť Počítač 2, nie Hráč) — prepočítané a nahradené, je to zámerný dôsledok zmeny pravidla, nie regresia.
- Overenia: regression_focus, regression_rules_demo, regression_layout (15 rozlíšení), regression_savegame, regression_classic_trump, regression_first_trump, regression_card_play, regression_tutorial_loops — všetko OK. Naviac ručne overené na 5 seedoch, že povinnosť v 1. kole skutočne padá na rôznych hráčov (nie vždy Hráč).
- Zmenené v tomto kroku: gui/info_overlay.py, main.py, game/game_state.py, ref_3kola.txt, ref_full.txt, HANDOFF.md. Bez commitu a zmeny vetvy.
- Návrh commit message: Obnoviť schválené texty kapitol a nastaviť náhodnú povinnosť v 1. kole novej hry.

## Dokončené — AI hlási tromf horníkom, nie kráľom (Claude, 2026-11-01)
- game/ai_strategy.py: S5-TRUMP_DECLARE a S1-CERTAIN_TRICK preferujú horníka pred kráľom pri hlásení tromfu.
- ref_3kola.txt, ref_full.txt: prepočítané referenčné stopy (zmena správania AI).

### Výsledok
- Zaužívaná konvencia (nie herné pravidlo — user 2026-11-01): keď AI hlási tromf a má v ruke kráľa aj horníka tej farby, mal by sa hlásiť horníkom, nie kráľom. Oba sú pravidlami rovnocenné.
- **S5 — TRUMP_DECLARE** (hlásenie od 2. štichu): pôvodne brala `next(c for c in playable if c.rank in ("king","over"))` — kvôli zoradeniu ruky (`Hand.sort_hand`, zostupne podľa rank_order) vychádzal takmer vždy kráľ (rank_order 5) pred horníkom (rank_order 4). Opravené: skúša sa najprv horník, kráľ len ako záložná možnosť (nemal by nastať, keď je pár v ruke celý).
- **S1 — CERTAIN_TRICK** (vedenie istým štichom): keď sú kráľ aj horník tej istej nezahlásenej farby súčasne "isté" karty, pôvodne sa vyberala podľa bodov (kráľ 4b > horník 3b), čo tiež viedlo k hláseniu kráľom. Opravené: kráľ sa z kandidátov vyradí, keď je jeho horník tiež medzi istými kartami tej farby — horník sa odohrá a zahlási tromf, kráľ ostáva v ruke na neskôr. Platí len pre nezahlásenú farbu (`c.suit != trump_suit`) — ak je farba už tromfová, výber ostáva podľa bodov ako doteraz (žiadne hlásenie sa už nekoná).
- Overené simuláciou (8000 kôl, varianty hlásenia v 1. štichu zapnuté aj klasika) a v hernej stope — tromfové hlásenia v trase teraz dôsledne `Card(suit, over)`, aj v prípade, ktoré predtým prechádzalo cez S1 ako kráľ.
- Variant "hlásenie v 1. štichu" (S29) už predtým vždy hlásil horníkom — bez zmeny.
- Overenia: regression_classic_trump, regression_first_trump, regression_card_play, regression_focus, regression_rules_demo, regression_tutorial_loops, regression_layout (15 rozlíšení), regression_savegame — všetko OK. Herná stopa (regression_screen) sa zámerne zmenila (AI teraz hrá iné karty pri hlásení) — prepočítaná a nahradená.
- Zmenené v tomto kroku: game/ai_strategy.py, ref_3kola.txt, ref_full.txt, HANDOFF.md. Bez commitu a zmeny vetvy.
- Návrh commit message: AI hlási tromf horníkom namiesto kráľom, keď má v ruke oba.

## Dokončené — hlásenie horníkom aj v koncovke (S21-ENDGAME) (Claude, 2026-11-01)
- game/ai_strategy.py: _get_endgame_card (S21, posledné 2-3 štichy) dostala rovnakú preferenciu horníka ako S1/S5.

### Výsledok
- User nahlásil z ostrej hry: počítač hlásil tromf kráľom v predposlednom štichu (mal v ruke už len samotný pár kráľ+horník). Predošlá oprava (S1/S5) toto nezachytila — `_get_endgame_card()` je úplne samostatná vetva pre posledné 2-3 štichy (trick_number ≥ 7), kontroluje sa PRED S1, a mala vlastný nezávislý výber `max(guaranteed_playable, key=points)` bez preferencie.
- Opravené rovnakým vzorom ako S1: kráľ sa vyradí z kandidátov, keď je jeho horník tej istej nezahlásenej farby tiež medzi istými kartami — horník sa odohrá (a zahlási tromf), kráľ zostáva v ruke.
- Overené simuláciou 10 000 kôl (klasika aj variant "hlásenie v 1. štichu"): 0/10000 prípadov hlásenia kráľom, keď bol horník k dispozícii (predtým sa to v koncovke dalo stať).
- Default-seed stopa (ref_3kola.txt, ref_full.txt) sa touto zmenou nezmenila — konkrétny scenár (pár isté kráľ+horník súčasne v koncovke) sa pri tomto seede nevyskytuje, takže referenčné súbory zostávajú z predošlého kroku bez úpravy.
- Overenia: regression_classic_trump, regression_first_trump, regression_card_play, regression_focus, regression_layout (15 rozlíšení), regression_savegame — všetko OK.
- Zmenené v tomto kroku: game/ai_strategy.py, HANDOFF.md. Bez commitu a zmeny vetvy.
- Návrh commit message: Hlásiť tromf horníkom aj v koncovke hry (posledné 2-3 štichy).

## Dokončené — redizajn záložky Prehľad bodovania (Claude, 2026-11-01)

### Zadanie
User priložil spec „Tisíc – Redizajn záložky „Prehľad bodovania“": prepracovať
záložku do rovnakého dvojstĺpcového rozloženia ako Pravidlá (vľavo navigácia
so 4 sekciami, vpravo obsah vybranej sekcie), odstrániť medailóny s bodmi
(hodnoty len textom), bez kalkulačiek/posuvníkov/animácií, zachovať skutočné
ilustrácie kariet a vizuálny štýl. Prepojiť kapitolu 5 Bodovanie v Pravidlách
na nový tab tlačidlom „Prejsť na prehľad bodovania" namiesto animovanej ukážky.

### Zmeny — gui/info_overlay.py
- Nová navigácia `_scoring_rects()`/`_draw_scoring_nav()`/`_draw_scoring_hover()`
  — rovnaký princíp ako `_chapter_areas()`/`_chapter_rects()` pre kapitoly
  Pravidiel (zdieľaná geometria ľavého/pravého panela), 4 položky: Hodnoty
  kariet, Tromfové hlášky, Povinnosť, Ostatní hráči. Stav `self.scoring_section`
  (0-3), klik v `handle_event`, aktívna položka zvýraznená zlatým rámom.
- `_draw_scoring()` prekreslená na dispatcher: nakreslí navigáciu a potom len
  obsah vybranej sekcie na celú šírku/výšku pravého panela (predtým všetky
  4 bloky naraz, zmenšené).
- Nové kresliace metódy len pre túto záložku (nepoužíva ich ukážka v
  Pravidlách): `_draw_values_section` (3 riadky kariet — Eso/Desiatka väčšie
  a výraznejšie, Kráľ/Horník/Dolník, Deviatka/Osmička/Sedmička — vycentrované,
  meno + bodová hodnota textom pod kartou, nulové hodnoty tlmenou farbou),
  `_draw_trumps_section` (2×2 mriežka Žaluď/Zeleň/Guľa/Srdce s kráľom+horníkom
  a textovou hodnotou), `_draw_obligation_section` (nový úvodný text + dva
  príklady Splnená/Nesplnená povinnosť s riadkami Povinnosť/Uhrané body/
  Výsledok), `_draw_others_section` (pôvodné texty, zväčšené na celú šírku
  pravého panela).
- Zdieľané metódy, ktoré používa aj animovaná ukážka `gui/scoring_demo.py`
  (Bodovanie v Priebehu kola — `_draw_card_values`, `_draw_card_row`,
  `_draw_trump_values`, `_draw_obligation`, `_draw_others`) upravené len
  v kresliacej časti: medailón nahradený textom bodovej hodnoty, geometria
  (rozmery, odsadenia) nezmenená — ukážka ďalej funguje a prechádza
  `layout_problems()` bez úprav v scoring_demo.py.
- Terminológia „povinnosť" namiesto „vydražená hodnota" (zadanie usera) —
  upravené aj v zdieľaných `OBLIGATION_INTRO`/`OBLIGATION_BOXES` (ukážka),
  nová záložka má vlastné `NEW_OBLIGATION_INTRO`/`OBLIGATION_EXAMPLES`
  s presným znením zo zadania.
- Odstránené: metóda `_medal()` a farby `MEDAL_RIM/MEDAL_DARK/MEDAL_LIGHT/
  MEDAL_TEXT/ZERO_RIM/ZERO_FILL` (nemali iné využitie), atribút
  `self.card_cycle` a `self._card_row` (animované striedanie farby kariet
  v tejto záložke — zadanie vylučuje animácie; `SuitCycle` trieda ostáva,
  používa ju len `scoring_demo.py`).
- Kapitola 5 Bodovanie v Pravidlách: tlačidlo „Otvoriť animovanú ukážku"
  nahradené „Prejsť na prehľad bodovania" (v `_draw_chapter_hover` aj
  v statickom `_draw_chapters`), klik prepína `active_tab` na "bodovanie"
  namiesto `select_step(4)`. Ostatné kapitoly nezmenené. `scoring_demo`
  a jeho wiring (`step_demos`, `layout_problems`) ostávajú nedotknuté —
  ukážka je už len nedosiahnuteľná z tohto tlačidla, kód aj testy naň
  mierené ďalej prechádzajú.
- Cache kľúč `draw_static` (`_draw_static`) rozšírený o `scoring_section`.

### Zmeny v testoch a nástrojoch
- `tester/regression_focus.py`: pridaný prípad `i == 4` v slučke klikov na
  kapitoly (ako Rozdanie/`i==0`) — klik na tlačidlo kapitoly Bodovanie teraz
  len prepne `active_tab` na "bodovanie", nezameria ukážku.
- `tools/screenshot_gallery.py`: snímka „stojaci žaluď (2. farba cyklu)"
  (`card_cycle`) nahradená snímkou sekcie Povinnosť (`scoring_section = 2`),
  keďže atribút `card_cycle` v tejto záložke už neexistuje.

### Overenie
- `regression_focus`, `regression_layout` (15 rozlíšení), `regression_rules_demo`,
  `regression_tutorial_loops`, `regression_classic_trump`, `regression_first_trump`,
  `regression_card_play`, `regression_screen` (stopa 3 kôl zhodná s
  `ref_3kola.txt` až na konce riadkov) — všetko OK. `regression_savegame`
  spustená (dlhotrvajúci test, nedotýka sa `InfoOverlay` ani uloženia hry).
- Herná logika, výpočty skóre a pravidlá hry neboli zmenené — len kreslenie
  okna Pravidlá a bodovanie.

### Technické obmedzenia / poznámky pre používateľa
- Ľavá navigácia (4 položky) nemá vlastné ilustrácie ako kapitoly Pravidiel
  (tie majú `_chapter_illustration`/galériu) — použité je len číslo sekcie
  v kruhu + názov + krátky podnadpis, v rovnakom vizuálnom ráme (zlatý rám,
  zvýraznenie aktívnej položky) ako kapitoly. Dá sa doplniť ilustráciou,
  ak to user bude chcieť.
- Karty v sekcii „Hodnoty kariet" sa kreslia natrvalo vo farbe zeleň
  (`VALUE_CARD_SUIT = "leaf"`) — predtým farba cyklicky striedala (zadanie
  animácie vylučuje). Dá sa zmeniť na inú farbu jednou konštantou.
- Zmenené len `gui/info_overlay.py`, `tester/regression_focus.py`,
  `tools/screenshot_gallery.py`, `CLAUDE.md`, `HANDOFF.md`. Bez commitu
  a zmeny vetvy.
- Návrh commit message: Redizajn záložky Prehľad bodovania na dvojstĺpcové
  rozloženie (bez medailónov a animácií).
## Dokončené — redizajn Nastavení, záložka Pravidlá (Claude, 2026-11-01)

### Zadanie
User priložil screenshot aktuálneho stavu (dva samostatné panely „SMER HRY"
a „HLÁSENIE TROMFU") a referenčný obrázok + spec „Tisíc – Redizajn Nastavení,
záložka Pravidlá": zjednotiť obe skupiny nastavení do jedného panela
(zaoblené rohy, tmavé priesvitné pozadie, zlatý rám), dve sekcie oddelené
deliacou čiarou, zachovať presné znenie tlačidiel (ČR/SR, „Od 2. štichu
(klasika)"/„Aj v 1. štichu") aj vysvetľujúci text, doplniť samostatný
informačný pás „Zmena pravidiel platí od novej hry." na konci panela,
zachovať funkčnosť a hodnoty nastavení bez zmeny.

### Zmeny — gui/settings_screen.py
- `__init__`: geometria záložky Pravidlá prepočítaná na sekvenčný kurzor
  (`y`/`y2` postupne), nie dva nezávislé panely. `panel_dir`/`panel_trump`
  zostávajú ako pôvodné atribúty (kvôli `tester/regression_layout.py`,
  ktorý ich testuje menom pri kolízii/hraniciach obrazovky), teraz
  reprezentujú logické podoblasti sekcií SMER HRY / HLÁSENIE TROMFU v rámci
  jedného nového orámovaného containera `panel_rules`. Výška pásu vysvetlenia
  je pevná na 3-riadkový (najdlhší) variant, aby pri prepnutí voľby
  nedochádzalo k zmene výšky panela.
- `_draw_rules_tab()` prepísaná: kreslí jeden spoločný panel (`_draw_panel`
  s `title=None`), v ňom sekciu SMER HRY (ikona + nadpis + deliaca čiara +
  dvojica tlačidiel ČR/SR), tenkú deliacu čiaru medzi sekciami, sekciu
  HLÁSENIE TROMFU (ikona + nadpis + deliaca čiara + tlačidlá + vysvetľujúci
  text pod nimi) a na konci samostatný informačný pás s tlmeným pozadím
  (`c.overlay`), vlastnou deliacou čiarou a ikonou „i".
- Nové pomocné metódy: `_draw_section_head()` (ikona + zlatý nadpis sekcie +
  deliaca čiara, spoločné pre obe sekcie), `_draw_rotate_icon()` (procedurálna
  zlatá ikona smeru — dva protiľahlé oblúky so šípkami, kreslená cez
  `pygame.draw.arc`/`c.polygon`, rovnaký princíp ako chýbajúci `sort.png`
  v `gui/screen.py`), `_draw_suit_icon()` (procedurálna zlatá ikona karovej
  farby — kruhy + trojuholník + stonka; skutočná ikona žaľuďa z
  `gui.scoreboard.load_suit_icon` bola vyskúšaná a zavrhnutá, prirodzená
  farba narúšala jednotný zlatý vzhľad ikon), `_draw_info_icon()` (krúžok +
  „i", zhodný princíp s ostatnými ikonami).
- Tlačidlá (`dir_buttons`/`trump_buttons`), ich popisky, hodnoty a logika
  výberu (`_draw_choice`, `_handle_click`, `_update_hover`) sú nezmenené —
  len repozicované podľa novej geometrie. Záložky Hra a Zobrazenie, ich
  obsah ani ukladanie nastavení (`settings.json`, `play_direction`,
  `first_trick_trump`) neboli dotknuté.

### Overenie
- `tester/regression_layout.py` — všetkých 15 rozlíšení OK (vrátane
  kolízie `panel_dir`/`panel_trump`/`panel_rules` s tlačidlom Späť
  a záložkami, aj obsiahnutia v hraniciach obrazovky).
- `tester/regression_rules_demo.py`, `tester/regression_focus.py` — OK,
  bez dopadu (záložka Pravidlá v Nastaveniach nesúvisí s ukážkami v okne
  Pravidlá a bodovanie).
- Vizuálne overené pri 1920×1080 render oboch variantov („Od 2. štichu" aj
  „Aj v 1. štichu" s 3-riadkovým vysvetlením) — zhoda s referenčným
  obrázkom, bez posunu/zmeny výšky panela pri prepnutí voľby, bez pretečenia
  textu. Overené aj pri 1280×720 a 1024×768, že `panel_rules` sa zmestí nad
  tlačidlo Späť.
- Herná logika, hodnoty a ukladanie nastavení neboli zmenené — len kreslenie
  záložky Pravidlá v okne Nastavenia.

### Technické obmedzenia / poznámky pre používateľa
- Ikony sekcií (smer, farba) aj informačná ikonka sú procedurálne kreslené
  (nie sú to samostatné súbory v `assets/`) — rovnaký princíp ako náhradná
  ikonka `sort.png`. Dá sa neskôr nahradiť vlastnou grafikou, ak bude
  treba.
- `tools/screenshot_gallery.py` snímka „menu_03e_nastavenia_pravidla"
  (záložka Pravidlá v Nastaveniach) bude po tejto zmene odlišná od starej
  referencie — zámerne, vizuálny redizajn. Treba ju u používateľa
  prerobiť (`--out` bez `--compare`), kód galérie nebolo treba meniť.
- Zmenené len `gui/settings_screen.py` a `HANDOFF.md`. Bez commitu a zmeny
  vetvy.
- Návrh commit message: Zjednotiť záložku Pravidlá v Nastaveniach do
  jedného panela s informačným pásom.
## Dokončené — galéria kapitol sa nehýbala (zamrznutá v statickej vrstve) (Claude, 2026-10-31)
- gui/info_overlay.py: kreslenie obrázkovej galérie presunuté mimo statickej vrstvy (cache).

### Výsledok
- Nahlásené userom: v náhľadoch kapitol (Cieľ hry, Dražba, Štichy a tromfy) bol vidno len jeden statický obrázok, hoci malo ísť o automatickú slučku viacerých.
- Príčina: celá metóda `_draw_chapters()` (vrátane volania `_draw_gallery()`) sa kreslí len z `_draw_static()`, ktorá je zabalená v `draw_static(...)` — statickej vrstve s cache kľúčom podľa záložky/kroku/kapitoly/fokusu. Kľúč sa nemení s časom, takže sa `_draw_gallery()` zavolala iba raz pri výbere kapitoly a odfotený obrázok (aktuálny v tom okamihu) zostal navždy — presne rovnaký mechanizmus, aký už predtým spôsoboval „duchovité" tlačidlo pri Rozdaní (tam to bolo opačne — niečo navyše kreslené mimo cache; tu niečo, čo *musí* byť mimo cache, bolo omylom v cache).
- Oprava: `_draw_chapters()` teraz iba vypočíta a uloží oblasť galérie (`self._gallery_rect`), nekreslí samotný obrázok. Skutočné vykreslenie `_draw_gallery(self._gallery_rect)` sa presunulo do `draw()` vedľa `_draw_chapter_hover()` — teda mimo cache, prekresľuje sa každú snímku, takže slučka a crossfade bežia normálne. `layout_problems()` (volá `_draw_static()` priamo, nie `draw()`) dostala vlastné dokreslenie galérie hneď po `_draw_static()`, aby `_fit` kontrola presahu obrázka zostala zachovaná.
- Overenia: ručný test cez `_gallery_state()` pri rastúcom `pygame.time.get_ticks()` potvrdil striedanie obrázkov a crossfade (predtým zamrznuté na indexe z okamihu vstupu do kapitoly). Celá sada: regression_focus, regression_rules_demo, regression_tutorial_loops, regression_classic_trump, regression_first_trump, regression_card_play, regression_layout (15 rozlíšení) OK. Herná stopa (regression_screen, 3 kolá) zhodná s ref_3kola.txt (zmena je iba v GUI kreslení, nie v engine).
- Zmenené v tomto kroku: gui/info_overlay.py, HANDOFF.md. Bez commitu a zmeny vetvy.
- Návrh commit message: Opraviť zamrznutú galériu náhľadov kapitol — kresliť mimo statickej vrstvy.

## Dokončené — odstránenie ikoniek sekcií v Nastaveniach/Pravidlá (Claude, 2026-11-01)

User upozornil, že procedurálne kreslené ikonky „smer" (šípky) a „farba"
(zeleň/pik) pri nadpisoch SMER HRY / HLÁSENIE TROMFU boli zbytočná
komplexnosť — žiadna grafika sa pre ne nemala vymýšľať bez spýtania.

- `gui/settings_screen.py`: `_draw_section_head()` už nekreslí ikonu, len
  zlatý nadpis zarovnaný doľava (`left + 24`) a deliacu čiaru. Odstránené
  metódy `_draw_rotate_icon()` a `_draw_suit_icon()` (nepoužívali sa inde).
  Informačná ikonka „i" v spodnom páse (`_draw_info_icon`) ostala — tú user
  nespomenul a vizuálne patrí k inému (jednoduchšiemu) prvku.
- Overenie: `regression_layout.py --one 1920x1080` (exit 0), `regression_focus.py`
  OK, modul sa importuje bez chýb. Vizuálne skontrolované oba varianty
  hlásenia tromfu pri 1920×1080 — bez ikoniek, nadpisy zarovnané, bez
  pretečenia textu.
- Zmenené len `gui/settings_screen.py`, `HANDOFF.md`. Bez commitu.
- Návrh commit message: Odstrániť procedurálne ikonky sekcií v Nastaveniach
  → Pravidlá.
## Dokončené — redizajn obsahu záložky Prehľad bodovania (Claude, 2026-11-01)

### Zadanie
User zadal šesť bodov úprav existujúcej záložky Prehľad bodovania:
číslovanie 1–4 v ľavej navigácii nahradiť existujúcimi hernými prvkami
danej sekcie; sekciu Povinnosť prerobiť na dve kompaktnejšie karty vedľa
seba so zarovnanými riadkami a výrazným „Výsledok kola"; sekciu Ostatní
hráči prerobiť na tri kompaktné horizontálne karty (výpočet vľavo,
výsledok vpravo); aktualizovať hlavné popisy všetkých štyroch sekcií aj
ich krátke popisy v navigácii; zjednotiť terminológiu v príkladoch
(Povinnosť, Uhrané body, Výsledok kola, Body za štichy, Tromfová hláška).

### Zmeny — gui/info_overlay.py
- `SCORING_SECTIONS`: nové krátke popisy v navigácii („Bodové hodnoty
  jednotlivých kariet", „Body za kráľa a horníka" — nezmenené, „Splnenie
  a nesplnenie povinnosti", „Bodovanie a zaokrúhľovanie").
- `_draw_scoring_nav()`: namiesto `_number_circle` (kruh s číslom 1–4)
  kreslí `_scoring_nav_icon()` — ikonová oblasť 88×72 v rovnakom mieste
  a rozmere ako ikony kapitol v Pravidlách (`_chapter_illustration`),
  panel aj zvýraznenie aktívnej/najetej položky (`_panel_bg`, zlatý rám)
  nezmenené. Nové pomocné metódy: `_nav_card_pair()` (dve mierne prekryté
  karty — eso/desiatka pre Hodnoty kariet, kráľ/horník prvej farby
  z `TRUMP_ORDER` pre Tromfové hlášky), `_nav_obligation_badges()`
  (zelená +100 a červená −100 značka cez existujúci `_pill()`), pre
  Ostatní hráči znovupoužitá existujúca ikonka `scoresheet.png` (rovnaká
  ako pri kroku Bodovanie v Priebehu kola, `_flow_illustration`).
  `_number_circle` zostáva — používa ho `_flow_illustration` pre číslované
  kroky Priebehu kola v Pravidlách.
- Hlavné popisy sekcií nahradené presným znením zo zadania — nové
  konštanty `NEW_VALUES_INTRO`, `NEW_TRUMPS_INTRO` (Hodnoty kariet,
  Tromfové hlášky; predtým 1–2 kratšie vety priamo v kóde),
  `NEW_OBLIGATION_INTRO` (upravené znenie), `NEW_OTHERS_INTRO` (nová
  konštanta, Ostatní hráči) — všetky samostatné od zdieľaných
  `OBLIGATION_INTRO`/`OTHERS_INTRO`, ktoré naďalej používa len animovaná
  ukážka bodovania v Pravidlách (`gui/scoring_demo.py`), beze zmeny.
- `_draw_obligation_section()`: nová metóda `_obligation_section_box_h()`
  počíta kompaktnú výšku karty z obsahu (ikona+nadpis, dva riadky
  Povinnosť/Uhrané body, deliaca čiara, Výsledok kola) namiesto
  roztiahnutia na celú výšku panela; riadok „Výsledok:" premenovaný na
  „Výsledok kola" a vykreslený väčším písmom (`canvas.font(32)` namiesto
  `font_section`) pre výraznosť. Príklady (100/112, 100/70) nezmenené.
- `_draw_others_section()`: namiesto jedného veľkého boxu s tromi riadkami
  teraz tri samostatné kompaktné horizontálne karty pod sebou (výpočet
  vľavo, výrazný výsledok vpravo so šípkou), cez celú dostupnú šírku
  pravého panela. Nová konštanta `OTHERS_EXAMPLES` so zjednotenou
  terminológiou („Body za štichy 33 + Tromfová hláška 40 = 73" → „70
  bodov" atď.) — číselné hodnoty 33+40=73→70, 25→30, 14→10 nezmenené,
  oddelené od zdieľanej `OTHERS_ROWS` (tá isté hodnoty, pôvodné znenie
  „Štichy"/„hláška", pre animovanú ukážku).

### Overenie
- `regression_layout.py` — všetkých 15 rozlíšení OK (dva nezávislé behy).
- `regression_focus.py`, `regression_rules_demo.py` — OK, bez dopadu
  (zdieľané kresliace metódy pre animovanú ukážku bodovania v Pravidlách
  neboli zmenené, len samostatné konštanty/metódy novej záložky).
- `regression_screen.py` prebehla bez chyby (166-riadková stopa — lokálne
  chýba referenčný `ref_3kola.txt` na porovnanie, no herná logika nebola
  v tomto kroku vôbec dotknutá, len kreslenie okna Pravidlá a bodovanie).
- `tools/screenshot_gallery.py --only game` prebehla bez chyby, vizuálne
  skontrolované všetky 4 sekcie pri 1920×1080 aj v hernom kontexte
  (game_11b_bodovanie_povinnost) — ikony v navigácii, kompaktné karty
  Povinnosti aj Ostatných hráčov zodpovedajú zadaniu.

### Technické obmedzenia / poznámky pre používateľa
- Snímky `game_11_pravidla_bodovanie`, `game_11b_bodovanie_povinnost`,
  `game_12d_pravidla_krok_bodovanie`, `game_12e_pravidla_bodovanie_povinnost`
  v `tools/screenshot_gallery.py` budú po tejto zmene odlišné od starej
  referencie — zámerne (vizuálny redizajn obsahu záložky), treba ich
  u teba na PC znova vygenerovať.
- Kompaktné karty v sekciách Povinnosť a Ostatní hráči už nevypĺňajú celú
  výšku pravého panela (zadanie žiadalo „kompaktnejšie" karty) — pri
  väčších rozlíšeniach/výškach obrazovky preto pod nimi ostáva prázdny
  priestor. Dá sa doplniť zvislé centrovanie, ak by to user chcel inak.
- Zmenené len `gui/info_overlay.py`, `HANDOFF.md`. Bez commitu a zmeny
  vetvy.
- Návrh commit message: Redizajn obsahu záložky Prehľad bodovania —
  ikony v navigácii, kompaktné karty Povinnosti a Ostatných hráčov,
  nové popisy a zjednotená terminológia.
## Dokončené — nový koncept Hodnôt kariet + farba kariet v slučke (Claude, 2026-11-01)

### Zadanie
User poslal obrázok nového konceptu pre sekciu Hodnoty kariet (jeden rad
piatich bodovaných kariet — Eso/Desiatka/Kráľ/Horník/Dolník, oddelený
nadpismi a čiarou od menšieho radu troch bezbodových kariet — Deviatka/
Osmička/Sedmička) a žiadal zároveň vrátiť animované striedanie farby
kariet v slučke, ktoré táto záložka od redizajnu 2026-11-01 nemala
(zadanie vtedy animácie vylučovalo).

### Zmeny — gui/info_overlay.py
- `VALUE_POINT_RANKS`/`VALUE_ZERO_RANKS`/`VALUE_GROUP_LABELS` nahradili
  `VALUE_ROWS` (predtým 3 rady 2+3+3, teraz 2 skupiny 5+3 s nadpismi
  „KARTY S BODOVOU HODNOTOU“/„KARTY BEZ BODOVEJ HODNOTY“ a deliacou
  čiarou, presne podľa priloženého konceptu).
- Nová čisto geometrická metóda `_values_layout(rect, y)` počíta pozície
  oboch skupín (karty väčšie 62 % výšky / menšie 38 %) — používa ju
  rovnako statické kreslenie popiskov aj živé kreslenie kariet, takže sú
  vždy presne zarovnané.
- `_draw_values_section()` teraz kreslí len nadpisy, deliacu čiaru a
  popisky (meno + body) pod každou kartou — bez obrázka karty; geometriu
  (`_values_items`, `_values_row`) si uloží na inštanciu.
- Farba kariet v slučke: nová trieda-inštancia `self.values_cycle =
  SuitCycle()` (tá istá trieda, akú už používala animovaná ukážka
  bodovania v Pravidlách, `gui/scoring_demo.py`) sa resetuje pri otvorení
  okna aj pri kliknutí na „Hodnoty kariet“ v navigácii. Nové metódy
  `_draw_values_cards()` (obrázky kariet v danej farbe) a
  `_draw_values_live()` (zavolá `values_cycle.draw(...)`) sa volajú z
  `InfoOverlay.draw()` MIMO cachovanej statickej vrstvy — rovnaký princíp
  ako animovaná galéria kapitol (`_draw_gallery`) — inak by farba
  zamrzla na obrázku z okamihu posledného prekreslenia statickej vrstvy.
- Opravená chyba objavená pri prvom behu `regression_focus`: kontrola
  presahu nadpisov (`_fit`) používala celú šírku panela bez odsadenia,
  čo `layout_problems` vyhodnotil ako falošný presah (deflatovaný `inner`
  bol o 8 px užší) — opravené odsadením `rect.x+10`/`rect.width-20`
  rovnako ako pri ostatných prvkoch v tejto záložke.

### Overenie
- `regression_layout.py` — všetkých 15 rozlíšení OK (dva nezávislé behy,
  druhý už s opravou nadpisov).
- `regression_focus.py`, `regression_rules_demo.py` — OK (zdieľaná
  animovaná ukážka bodovania v Pravidlách naďalej funguje, používa
  vlastnú inštanciu `SuitCycle`, nedotknutú touto zmenou).
- `tools/screenshot_gallery.py --only game` bez chyby; vizuálne overené
  pri 1920×1080 aj v hernom kontexte (game_11_pravidla_bodovanie) a pri
  simulovanom posune času (leaf → acorn) — rozloženie, popisky aj
  prechod farby zodpovedajú zadaniu, žiadne skákanie ani presah.

### Technické obmedzenia / poznámky pre používateľa
- Snímky `game_11_pravidla_bodovanie`, `game_12d_pravidla_krok_bodovanie`
  v `tools/screenshot_gallery.py` budú odlišné od starej referencie —
  zámerne (nové rozloženie), treba ich u teba na PC znova vygenerovať.
- Farba kariet sa mení v rovnakom rytme ako predtým v animovanej ukážke
  (3 s zotrvanie + 0,9 s prelínanie, poradie zeleň → žaluď → guľa →
  srdce) — dá sa upraviť v `SuitCycle.HOLD`/`FADE`, zdieľané s ukážkou.
- Zmenené len `gui/info_overlay.py`, `HANDOFF.md`. Bez commitu a zmeny
  vetvy.
- Návrh commit message: Nový koncept Hodnôt kariet (dve skupiny podľa
  bodovej hodnoty) a návrat farebnej slučky kariet.

## 2026-11-01 — Revízia trofejí (zadanie usera, chat)

### Zadanie
"rád by som spravil ešte revíziu trofejí, prečítal si podmienky a možno
niektoré upravil" — prešli sme spolu zoznam všetkých 32 trofejí
(definitions.py popis vs. tracker.py skutočná podmienka) a user vybral
konkrétne úpravy.

### Zmeny
- **Fénix** (`comeback`) — prah zníženy z −200 na −100 bodov
  (`achievements/tracker.py`, `on_game_finished`). Popis v
  `definitions.py` upravený na "...viac ako 100 bodov.".
- **Neporaziteľný — Zlato** (`unbeatable_gold`) — zo 10 na 7 výhier
  v rade (`achievements/tracker.py`, `on_game_finished`). Popis
  upravený na "Vyhraj 7 hier za sebou.".
- **Šťastný nákup** (`lucky_pickup`) — zrušená kombinácia eso+desiatka
  (bola najľahšia a najčastejšia); ostáva 2× eso, 2× desiatka,
  kompletný tromfový pár (`achievements/on_talon_received`). Popis
  v `definitions.py` sa nemenil (už predtým neuvádzal zmiešanú
  kombináciu).
- **Oprava bugu**: `GameOverScreen` (`gui/game_over_screen.py`) ani
  `main._show_game_over` nikdy nevolali `pop_notifications()`/
  `AchievementPopup` — trofeje odomknuté na konci hry (`on_game_finished`,
  napr. Smoliar, Začíname, Fénix, Presná tisícka, Trikrát a dosť,
  Neporaziteľný, Kto mlčí vyhráva) sa ticho uložili, ale popup sa
  NIKDY nezobrazil (bolo vidno len v obrazovke Trofeje). Oprava:
  `GameOverScreen.__init__` prijíma `achievement_tracker`, vytvorí
  vlastný `AchievementPopup` a naplní ho z `pop_notifications()`;
  `run()` ho update/draw-uje a spracúva jeho kliky (rovnaký vzorec ako
  `Screen`). `main._show_game_over` teraz posiela `achievement_tracker=`
  do konštruktora.
- **Nerozhodnuté**: "Kto mlčí, vyhráva" (`passivist`) — user ju
  považuje za príliš prísnu/závislú od šťastia s kartami, ale
  rozhodnutie o zmazaní/úprave ešte nepadlo — necháno bez zmeny.

### Overenie
- `achievements/test_achievements.py` — doplnené/upravené testy pre
  zmenené prahy (Fénix −100 unlock, −80 no-unlock; eso+desiatka teraz
  NEMÁ unlock-núť), všetky `[PASS]` (`python -m achievements.test_achievements`,
  headless).
- `tester/regression_screen.py` — stopa OK.
- `tester/regression_layout.py` — všetkých 15 rozlíšení OK.
- Ručne overené vytvorenie `GameOverScreen(..., achievement_tracker=...)`
  headless — `achievement_popup.queue` sa naplní z trackera.
- Byte-presne overené nasadenie všetkých 5 zmenených súborov na PC
  (diff po re-stage).

### Technické obmedzenia
- `achievements/storage.py` sa v tomto kole nemenil.
- "Kto mlčí, vyhráva" (`passivist`) čaká na rozhodnutie (ponechať/
  zmazať/zmierniť podmienku) — pôjde do ďalšieho kola úprav.

### Návrh commit message
`Revízia trofejí: Fénix/Neporaziteľný zmiernené, Šťastný nákup sprísnený, opravený chýbajúci popup trofejí na konci hry`

## 2026-11-01 — Revízia trofejí, kolo 2 (zadanie usera, konzultované s GPT)

### Zadanie
Užívateľ pripravil s GPT konkrétne zadanie na úpravu trofejí (premenovania,
nové podmienky, 2 nové trofeje) + dve staršie dohodnuté zmeny z predošlého
mobilného rozhovoru (zmazanie "Kto mlčí, vyhráva", výnimka pre "Bez poistky"
pri hlásení v 1. štichu).

### Zmeny — premenovania (podmienky nezmenené)
- Tichý pozorovateľ I./II./III. → **Ani muk I./II./III.** (id `silent_watcher_1/2/3`)
- Dominancia → **Čistý stôl** (id `dominance`)

### Zmeny — upravené podmienky
- **S odretými ušami** (`barely_made_it`) — pôvodne len presné splnenie
  bid=50 (prekrývalo sa so Skromný víťaz). Teraz: presné splnenie
  AKEJKOĽVEK povinnosti, ale len od **60 bodov vyššie**
  (`achievements/tracker.py`, `on_round_finished`: `human_bid >= 60 and
  human_round_points == human_bid`).
- **Posledné slovo** (`last_word`) — pôvodne sa odomklo hneď pri hlásení,
  ak bolo human v poradí 3. a ďalší. Nová podmienka: human zahlási svoju
  PRVÚ hlášku kola ako 3. alebo 4. v poradí A táto hláška je zároveň
  POSLEDNOU tromfovou hláškou kola (zisťuje sa až na konci kola).
  Implementácia: `round_human_first_trump_position` sa nastaví pri prvej
  human hláške v `on_trump_declared`, vyhodnotenie (porovnanie s finálnym
  `round_all_trump_declarations`) je v `on_round_finished`.
- **Bez poistky** (`no_safety_net`) — nová výnimka: nepočíta sa pri
  hlásení v 1. štichu (nový variant), len pri klasickom hlásení od
  2. štichu (`trick_number != 0`).

### Zmeny — nové trofeje
- **Dva kohúty na jednom smetisku** (`two_roosters`, kategória Tromfy) —
  human zahlási tromf, potom JEDEN konkrétny súper zahlási 1 alebo 2
  tromfy, a human zahlási znova. Odomkne sa okamžite pri hláške, ktorá
  postupnosť dokončí. Implementácia: `round_trump_order` (zoznam "human"
  / player_index súpera za celé kolo) + `_check_two_roosters()`
  (porovnáva posledné 1-2 položky so vzorom human→[rovnaký súper ×1-2]→human).
  `on_trump_declared` dostal nový parameter `player_index` (identifikuje
  KTORÉHO súpera — AI1 vs AI2).
- **Kto sa smeje naposledy** (`last_laugh`, kategória Štichy) — human
  vyhrá celú hru, hoci bezprostredne PRED posledným (rozhodujúcim) kolom
  mal aspoň jeden súper viac bodov než on. Implementácia: nová metóda
  `on_round_started(human_score, opponent_scores)` — zavolaná z
  `gui/screen.py._start_round()` pred každým kolom, prepisuje
  `game_round_start_human_score`/`game_round_start_opponent_scores`
  (prefix `game_` → prežije `reset_round()`, takže na konci hry obsahuje
  skóre z ÚVODU posledného kola); porovnanie v `on_game_finished`.

### Zmeny — zmazané (z predošlého mobilného rozhovoru)
- **"Kto mlčí, vyhráva"** (`passivist`) — zmazané úplne z `definitions.py`
  aj logika v `tracker.py` (`on_game_finished`). `game_was_bidder` atribút
  v trackeri ostáva (nastavuje ho `on_bid_placed`), už ho však nič
  nevyhodnocuje — neškodný mrtvý stav, nechaný pre prípadné budúce použitie.
  Staré odomknuté `passivist` v `achievements.json` u hráčov sa ignoruje
  (storage.py berie len ID zo zoznamu definícií).

### Overenie
- `achievements/test_achievements.py` — doplnené/upravené testy pre
  všetky zmenené aj nové podmienky (`test_last_word`, `test_two_roosters`,
  rozšírený `test_round_finished` pre bid>=60, rozšírený `test_game_finished`
  pre `last_laugh`, odstránené testy pre `passivist`), všetky `[PASS]`
  (`python -m achievements.test_achievements`, headless).
- `tester/regression_screen.py` — stopa hry bez zmeny.
- `gui/achievements_screen.py` — ručne overené headless vykreslenie
  s plným zoznamom odomknutých trofejí (35 trofejí), bez chyby.
- Byte-presne overené nasadenie všetkých 4 zmenených súborov na PC
  (diff po re-stage).

### Technické obmedzenia
- `gui/achievement_popup.py` (fronta popup notifikácií) sa nemenil —
  viacstupňové odomknutie naraz (napr. absolute_rule_1+2) sa už aj
  predtým zobrazovalo postupne cez `queue.extend()`, overené code-review.
- "Päťkrát a dosť" (slabšia úroveň k "Trikrát a dosť") — zámerne
  NEIMPLEMENTOVANÉ v tomto kole (user: "zatiaľ ponechaj bez zmeny").

### Návrh commit message
`Revízia trofejí kolo 2: premenovania (Ani muk, Čistý stôl), nové podmienky (S odretými ušami, Posledné slovo, Bez poistky), nové trofeje (Dva kohúty na jednom smetisku, Kto sa smeje naposledy), zmazané Kto mlčí vyhráva`

## 2026-11-01 — Bugfix: "Každý bod sa počíta" bolo nedosiahnuteľné pri discarde

### Zadanie
User nahlásil, že v ostrej hre zobral všetkých 10 štichov a všetky
bodované karty, "Čistý stôl" sa odomkol, ale "Každý bod sa počíta" nie.

### Diagnóza
`game/round.py.discard_cards()` pripočítava body zahodených kariet do
talonu priamo víťazovi dražby (`winner.add_trick_points(card.points)`) —
reálne skóre kola je teda správne. Trofejový tracker ale o tomto
zahodení nevedel: `round_human_card_points` (čítadlo pre "Každý bod sa
počíta", prah 120 = súčet všetkých kartových bodov v balíku) sa
zvyšovalo len cez `on_trick_won()`, volané len pri štichoch. Ak sa do
talonu zahodila čo i len jedna bodovaná karta (kráľ/horník/dolník —
eso a desiatka sa zahodiť nedajú), 120 bodov sa už v tom kole nedalo
dosiahnuť, aj pri zobratí všetkých 10 štichov.

### Oprava
`achievements/tracker.py`, `on_discard()` — na začiatku metódy pripočíta
body zahodených kariet: `self.round_human_card_points += sum(c.points
for c in discarded_cards)`. Logika "Hláška do koša" (`pretty_but_useless`)
zostala nezmenená, len presunuté `_save()` za koniec metódy (predtým bol
v cykle skorý `return`, ktorý by teraz obišiel aj `_save()` po novom
riadku bodov — upravené, aby sa vždy uložilo).

### Overenie
- `achievements/test_achievements.py` — 3 nové testy v `test_discard()`
  (body sa pripočítajú pri discarde kráľ+horník=7b aj dolník+sedmička=2b;
  "greedy" sa teraz odomkne aj pri 113 zvyšných bodoch zo štichov +
  7 zahodených = 120). Všetky `[PASS]`.
- `tester/regression_screen.py` — stopa bez zmeny.
- Byte-presne overené nasadenie `achievements/tracker.py` a
  `achievements/test_achievements.py` na PC.

### Návrh commit message
`Bugfix: body zahodené do talonu po dražbe sa teraz počítajú aj do trofeje "Každý bod sa počíta"`

## 2026-11-01 — Revízia trofejí (zadanie usera, chat)

### Zadanie
"rád by som spravil ešte revíziu trofejí, prečítal si podmienky a možno
niektoré upravil" — prešli sme spolu zoznam všetkých 32 trofejí
(definitions.py popis vs. tracker.py skutočná podmienka) a user vybral
konkrétne úpravy.

### Zmeny
- **Fénix** (`comeback`) — prah zníženy z −200 na −100 bodov
  (`achievements/tracker.py`, `on_game_finished`). Popis v
  `definitions.py` upravený na "...viac ako 100 bodov.".
- **Neporaziteľný — Zlato** (`unbeatable_gold`) — zo 10 na 7 výhier
  v rade (`achievements/tracker.py`, `on_game_finished`). Popis
  upravený na "Vyhraj 7 hier za sebou.".
- **Šťastný nákup** (`lucky_pickup`) — zrušená kombinácia eso+desiatka
  (bola najľahšia a najčastejšia); ostáva 2× eso, 2× desiatka,
  kompletný tromfový pár (`achievements/on_talon_received`). Popis
  v `definitions.py` sa nemenil (už predtým neuvádzal zmiešanú
  kombináciu).
- **Oprava bugu**: `GameOverScreen` (`gui/game_over_screen.py`) ani
  `main._show_game_over` nikdy nevolali `pop_notifications()`/
  `AchievementPopup` — trofeje odomknuté na konci hry (`on_game_finished`,
  napr. Smoliar, Začíname, Fénix, Presná tisícka, Trikrát a dosť,
  Neporaziteľný, Kto mlčí vyhráva) sa ticho uložili, ale popup sa
  NIKDY nezobrazil (bolo vidno len v obrazovke Trofeje). Oprava:
  `GameOverScreen.__init__` prijíma `achievement_tracker`, vytvorí
  vlastný `AchievementPopup` a naplní ho z `pop_notifications()`;
  `run()` ho update/draw-uje a spracúva jeho kliky (rovnaký vzorec ako
  `Screen`). `main._show_game_over` teraz posiela `achievement_tracker=`
  do konštruktora.
- **Nerozhodnuté**: "Kto mlčí, vyhráva" (`passivist`) — user ju
  považuje za príliš prísnu/závislú od šťastia s kartami, ale
  rozhodnutie o zmazaní/úprave ešte nepadlo — necháno bez zmeny.

### Overenie
- `achievements/test_achievements.py` — doplnené/upravené testy pre
  zmenené prahy (Fénix −100 unlock, −80 no-unlock; eso+desiatka teraz
  NEMÁ unlock-núť), všetky `[PASS]` (`python -m achievements.test_achievements`,
  headless).
- `tester/regression_screen.py` — stopa OK.
- `tester/regression_layout.py` — všetkých 15 rozlíšení OK.
- Ručne overené vytvorenie `GameOverScreen(..., achievement_tracker=...)`
  headless — `achievement_popup.queue` sa naplní z trackera.
- Byte-presne overené nasadenie všetkých 5 zmenených súborov na PC
  (diff po re-stage).

### Technické obmedzenia
- `achievements/storage.py` sa v tomto kole nemenil.
- "Kto mlčí, vyhráva" (`passivist`) čaká na rozhodnutie (ponechať/
  zmazať/zmierniť podmienku) — pôjde do ďalšieho kola úprav.

### Návrh commit message
`Revízia trofejí: Fénix/Neporaziteľný zmiernené, Šťastný nákup sprísnený, opravený chýbajúci popup trofejí na konci hry`

## 2026-11-01 — TROFEJE: rework na dvojpanelové rozhranie

### Zadanie
User zaslal detailné zadanie (6 bodov + 3 mockup obrázky) na prerobenie
okna TROFEJE z pôvodného jednostĺpcového zoznamu na moderné dvojpanelové
rozhranie: vľavo rolovateľný zoznam trofejí podľa kategórií (ikona, názov,
stav, pri viacúrovňových X zo Y úrovní), vpravo detail vybranej trofeje
(väčšia grafika, názov, podmienka ak je odhalená, stav; pri viacúrovňových
samostatné klikateľné kartičky úrovní, každá s vlastným názvom/podmienkou/
stavom). Postupné odhaľovanie podmienok: získanie úrovne odhalí podmienku
NASLEDUJÚCEJ; bez odomknutia žiadnej úrovne zostáva aj prvá (ak je hidden)
skrytá; skryté texty "Podmienka získania je zatiaľ skrytá." Nové podklady
bronz/striebro/zlato/platina + `lock.png`, mapovanie podľa počtu úrovní
(1→zlato, 2→striebro-zlato, 3→bronz-striebro-zlato, 4→+platina). Žiadna
zmena hernej logiky ani systému udeľovania — len UI a zobrazovacia/
odhaľovacia logika; zachovať ID trofejí, podmienky aj uložený progres.

### Zmeny
- `gui/achievements_screen.py` — kompletne prepísané (vnútro, nie
  verejné rozhranie): `AchievementsScreen` teraz kreslí dva pod-panely
  (`left_panel_bg`/`left_rect` zoznam, `right_panel_bg`/`right_content`
  detail) namiesto pôvodného jediného stĺpca; nové:
  - `_build_rows()` nezmenené zoskupovanie (single/group), ale rendering
    riadkov je teraz kompaktný (ikona + názov + podstav, bez popisu —
    popis sa presunul výhradne do pravého panela);
  - `self.selected_index`/`self.selected_tier` — stav výberu; klik na
    riadok vľavo vyberie trofej (pri skupine automaticky zvolí poslednú
    ODOMKNUTÚ úroveň, inak prvú), klik na kartičku úrovne vpravo prepne
    zobrazený detail bez zmeny vybraného riadku;
  - `_tier_states(items, unlocked)` — čistá funkcia nad uloženým stavom
    (`data["unlocked"]`): úroveň je `unlocked`/`revealed`/`hidden`, kde
    `revealed` nastáva buď keď `hidden=False`, alebo keď PREDCHÁDZAJÚCA
    úroveň je odomknutá — odvodené výhradne z uloženého stavu, funguje
    teda aj po reštarte hry bez nového ukladaného príznaku;
  - `_group_label()` (regex na rímsku číslicu / "— stupeň" na konci
    mena prvej úrovne) — stabilný názov skupiny v zozname aj v hlavičke
    detailu, nemenný naprieč výberom úrovne (opravuje aj kozmetickú
    chybu pôvodného `rsplit(" ", 1)` pri menách ako "Odvážny pokus");
  - `_draw_icon()` — spoločný kresliaci helper pre ikonu v zozname aj
    v detaile: odomknuté = skutočná grafika danej úrovne (pomer strán
    341:512 zachovaný, `image()` ho sám nezachováva), zamknuté = vždy
    `lock.png` bez ohľadu na to, akú farbu by úroveň inak mala;
  - `_draw_tier_card()` + `_draw_check_badge()` — kartičky úrovní
    v pravom paneli (vektorová fajočka cez `c.line`, žiadny textový
    glyf — v sandboxe sa "←" aj "✓" niekedy vykreslia ako prázdny
    štvorec kvôli chýbajúcemu glyfu v záložnom fonte; na reálnom PC
    (rovnaký font ako existujúce "← Späť" v `settings_screen.py`) by
    to malo byť v poriadku, overiť vizuálne po nasadení);
  - cache kľúče `draw_static` (`_draw`/`draw_overlay`) rozšírené o
    `selected_index`/`selected_tier`, aby sa vrstva prekreslila aj pri
    samotnom výbere (predtým len `scroll_offset`).
  Zachované bezo zmeny (API aj správanie): konštruktor
  `AchievementsScreen(screen=None, data=None)`, `.run()`,
  `.handle_event()` vracia `"close"`/`None`, `.PANEL_X/Y/W/H`,
  `.CONTENT_Y/H`, `.back_button`, `.scroll_offset`/`.max_scroll`,
  trieda `AchievementsOverlay` (`.visible`/`.covers_screen`/`.show()`/
  `.hide()`/`.toggle()`/`.handle_event()`/`.draw()`) — všetky volania
  v `main.py`, `tester/regression_layout.py`, `tools/screenshot_gallery.py`
  a `gui/screen.py` fungujú bez úprav.
- `achievements/definitions.py`, `get_tier_name()` — prepísané z
  pôvodného 3-stupňového odhadu (bronz/striebro/zlato podľa pozície)
  na explicitnú tabuľku `_TIER_SCHEMES` podľa POČTU úrovní v skupine
  (1→zlato; 2→striebro,zlato; 3→bronz,striebro,zlato; 4→bronz,striebro,
  zlato,platina) — jediná skupina so 4 úrovňami je `wins_milestone`
  (Začíname/Rozbehnutý/Stará škola/Legenda), tá teraz dostáva platinu
  na "Legenda" namiesto pôvodného (chybného) zlata na všetkých okrem
  prvej a poslednej úrovne.
- `gui/achievement_popup.py` — rozšírený zoznam načítavaných ikon
  o `"platinum"` (riadok s `for tier_name in (...)`), aby popup pri
  odomknutí `wins_100` ("Legenda") zobrazil správnu platinovú grafiku
  namiesto predtým jedinej dostupnej "gold" možnosti.

### Overenie
- `python -m achievements.test_achievements` — bez zmeny hernej/
  trofejovej logiky, všetky `[PASS]`.
- Nový priamy test `get_tier_name()` pre všetky existujúce skupiny
  (1/2/3/4 úrovne) — správne bronz/striebro/zlato/platina.
- Headless render + simulácia kliknutia na KAŽDÝ riadok zoznamu aj
  KAŽDÚ kartičku úrovne (24 riadkov, všetky skupiny) pri 7 rozlíšeniach
  (1024×768 … 3840×2160, vrátane 21:9) — bez výnimky.
- `tester/regression_layout.py` — všetkých 15 rozlíšení `[OK]`
  (kontroluje `.back_button` + `obsah` rect, nezmenené).
- `tester/regression_screen.py` — stopa 3 kôl byte-presne zhodná
  s `ref_3kola.txt` na PC (bez zmeny hernej logiky, len rozdiel
  v ukončení riadkov LF/CRLF medzi sandboxom a PC).
- Vizuálne overené headless screenshoty (skupina s 4/3/1 úrovňami,
  samostatná skrytá trofej) — zoznam, výber, kartičky úrovní,
  fajočka na odomknutej úrovni, text "Podmienka získania je zatiaľ
  skrytá." pri skrytých podmienkach — všetko zodpovedá mockupom.
- Byte-presne overené nasadenie všetkých 3 zmenených súborov na PC
  (diff po re-stage).

### Technické obmedzenia
- Ikona v ĽAVOM zozname je zjednodušená (len odomknuté/zamknuté —
  zlatá trofej alebo zámka), nerozlišuje farbu úrovne; farebné
  bronz/striebro/zlato/platina rozlíšenie je len na kartičkách úrovní
  v PRAVOM detaile (tak ako v mockupe). Dátum získania sa nezobrazuje —
  `achievements/storage.py` ho neukladá (zadanie: zobraziť "ak ho
  existujúce dáta obsahujú").
- Odporúčam po nasadení jedno vizuálne overenie na reálnom PC kvôli
  glyfu "←" na tlačidle Späť (pozri vyššie) — je to ale existujúci kód
  (`settings_screen.py` má rovnaký text), nie regresia tejto zmeny.

### Návrh commit message
`Trofeje: dvojpanelové rozhranie (zoznam + detail s úrovňami), postupné odhaľovanie podmienok, nová grafika bronz/striebro/zlato/platina + zámka`

## 2026-11-01 — Revízia trofejí, kolo 2 (zadanie usera, konzultované s GPT)

### Zadanie
Užívateľ pripravil s GPT konkrétne zadanie na úpravu trofejí (premenovania,
nové podmienky, 2 nové trofeje) + dve staršie dohodnuté zmeny z predošlého
mobilného rozhovoru (zmazanie "Kto mlčí, vyhráva", výnimka pre "Bez poistky"
pri hlásení v 1. štichu).

### Zmeny — premenovania (podmienky nezmenené)
- Tichý pozorovateľ I./II./III. → **Ani muk I./II./III.** (id `silent_watcher_1/2/3`)
- Dominancia → **Čistý stôl** (id `dominance`)

### Zmeny — upravené podmienky
- **S odretými ušami** (`barely_made_it`) — pôvodne len presné splnenie
  bid=50 (prekrývalo sa so Skromný víťaz). Teraz: presné splnenie
  AKEJKOĽVEK povinnosti, ale len od **60 bodov vyššie**
  (`achievements/tracker.py`, `on_round_finished`: `human_bid >= 60 and
  human_round_points == human_bid`).
- **Posledné slovo** (`last_word`) — pôvodne sa odomklo hneď pri hlásení,
  ak bolo human v poradí 3. a ďalší. Nová podmienka: human zahlási svoju
  PRVÚ hlášku kola ako 3. alebo 4. v poradí A táto hláška je zároveň
  POSLEDNOU tromfovou hláškou kola (zisťuje sa až na konci kola).
  Implementácia: `round_human_first_trump_position` sa nastaví pri prvej
  human hláške v `on_trump_declared`, vyhodnotenie (porovnanie s finálnym
  `round_all_trump_declarations`) je v `on_round_finished`.
- **Bez poistky** (`no_safety_net`) — nová výnimka: nepočíta sa pri
  hlásení v 1. štichu (nový variant), len pri klasickom hlásení od
  2. štichu (`trick_number != 0`).

### Zmeny — nové trofeje
- **Dva kohúty na jednom smetisku** (`two_roosters`, kategória Tromfy) —
  human zahlási tromf, potom JEDEN konkrétny súper zahlási 1 alebo 2
  tromfy, a human zahlási znova. Odomkne sa okamžite pri hláške, ktorá
  postupnosť dokončí. Implementácia: `round_trump_order` (zoznam "human"
  / player_index súpera za celé kolo) + `_check_two_roosters()`
  (porovnáva posledné 1-2 položky so vzorom human→[rovnaký súper ×1-2]→human).
  `on_trump_declared` dostal nový parameter `player_index` (identifikuje
  KTORÉHO súpera — AI1 vs AI2).
- **Kto sa smeje naposledy** (`last_laugh`, kategória Štichy) — human
  vyhrá celú hru, hoci bezprostredne PRED posledným (rozhodujúcim) kolom
  mal aspoň jeden súper viac bodov než on. Implementácia: nová metóda
  `on_round_started(human_score, opponent_scores)` — zavolaná z
  `gui/screen.py._start_round()` pred každým kolom, prepisuje
  `game_round_start_human_score`/`game_round_start_opponent_scores`
  (prefix `game_` → prežije `reset_round()`, takže na konci hry obsahuje
  skóre z ÚVODU posledného kola); porovnanie v `on_game_finished`.

### Zmeny — zmazané (z predošlého mobilného rozhovoru)
- **"Kto mlčí, vyhráva"** (`passivist`) — zmazané úplne z `definitions.py`
  aj logika v `tracker.py` (`on_game_finished`). `game_was_bidder` atribút
  v trackeri ostáva (nastavuje ho `on_bid_placed`), už ho však nič
  nevyhodnocuje — neškodný mrtvý stav, nechaný pre prípadné budúce použitie.
  Staré odomknuté `passivist` v `achievements.json` u hráčov sa ignoruje
  (storage.py berie len ID zo zoznamu definícií).

### Overenie
- `achievements/test_achievements.py` — doplnené/upravené testy pre
  všetky zmenené aj nové podmienky (`test_last_word`, `test_two_roosters`,
  rozšírený `test_round_finished` pre bid>=60, rozšírený `test_game_finished`
  pre `last_laugh`, odstránené testy pre `passivist`), všetky `[PASS]`
  (`python -m achievements.test_achievements`, headless).
- `tester/regression_screen.py` — stopa hry bez zmeny.
- `gui/achievements_screen.py` — ručne overené headless vykreslenie
  s plným zoznamom odomknutých trofejí (35 trofejí), bez chyby.
- Byte-presne overené nasadenie všetkých 4 zmenených súborov na PC
  (diff po re-stage).

### Technické obmedzenia
- `gui/achievement_popup.py` (fronta popup notifikácií) sa nemenil —
  viacstupňové odomknutie naraz (napr. absolute_rule_1+2) sa už aj
  predtým zobrazovalo postupne cez `queue.extend()`, overené code-review.
- "Päťkrát a dosť" (slabšia úroveň k "Trikrát a dosť") — zámerne
  NEIMPLEMENTOVANÉ v tomto kole (user: "zatiaľ ponechaj bez zmeny").

### Návrh commit message
`Revízia trofejí kolo 2: premenovania (Ani muk, Čistý stôl), nové podmienky (S odretými ušami, Posledné slovo, Bez poistky), nové trofeje (Dva kohúty na jednom smetisku, Kto sa smeje naposledy), zmazané Kto mlčí vyhráva`

## 2026-11-01 — TROFEJE: kolo 2 — horizontálny detail, poctivé proporcie, zamknuté karty

### Zadanie
User poslal mockup obrázok ("NÁVRH NOVÉHO DETAILU") a 7-bodové zadanie na
úpravu práve nasadeného dvojpanelového okna TROFEJE: každá úroveň sa má
počítať ako samostatná trofej (jediné počítadlo v hlavičke, zrušiť druhé
"X/Y" v pravom paneli); pravý panel prerobiť na horizontálne rozloženie
(veľká karta vľavo ~185-195px, text vpravo, pod tým samostatný rad
klikateľných kartičiek úrovní ~85×125px, bez zbytočného prepínača pri
samostatných trofejach); zamknutá trofej/úroveň musí mať rovnaké rozmery
ako odomknutá a použiť PRÍSLUŠNÚ (stupňovú) kovovú kartu stmavenú +
prekrytú ikonou zámku — nie generický štvorec; opraviť deformované
(naťahované) ikonky v ľavom zozname; zachovať postupné odhaľovanie
podmienok, rozloženie ľavého panela, ale vybranú položku zvýrazniť
výraznejšie. Žiadna zmena hernej logiky, žiadne nové grafické súbory.

### Zmeny (`gui/achievements_screen.py`)
- `_draw_card_icon(tier_name, box, unlocked)` — NOVÝ jednotný helper
  nahrádzajúci pôvodný `_draw_icon`: karta sa VŽDY vykreslí v pomere
  341:512 vycentrovaná v `box` (nikdy nedeformovaná, nech je box
  akéhokoľvek tvaru); zamknutá = tá istá kovová karta danej úrovne
  (rovnaké rozmery ako odomknutá), len stmavená (`overlay` čiernou,
  alfa 165) a prekrytá `lock.png` v strede — odhalenie textu podmienky
  (hidden/revealed) túto kresbu vôbec neovplyvňuje, mení sa výhradne
  podľa skutočného `is_unlocked`. Použité na 3 miestach: riadok zoznamu,
  veľká karta detailu, kartičky úrovní — žiadna duplicitná logika.
- `_row_tier_and_unlocked(row)` (nahrádza `_row_any_unlocked`) — farba
  ikony v ľavom zozname teraz zodpovedá SKUTOČNÉMU stupňu: pri skupine
  farba najvyššej ODOMKNUTEJ úrovne, alebo farba prvej úrovne (zamknutá),
  ak ešte nie je odomknutá žiadna — opravuje aj zadanú "deformáciu" (ikona
  už nie je nasilu naťahovaná do štvorca).
- `_detail_layout()` — prepísané na horizontálne rozloženie: veľká karta
  190px široká (pomer 341:512 → ~285px vysoká) vľavo v `right_content`,
  text vpravo od nej (`text_rect`); pri skupine pod oboma samostatný rad
  kartičiek úrovní 85×125 s nadpisom "ÚROVNE TROFEJE" (`tier_label_y`).
- `_draw_detail_text()` — nový zjednotený kresliaci helper pre
  názov/úroveň/stav/podmienku; status text a farba sú teraz parametrom
  volajúceho (nie odvodené z jedného `state`), takže samostatné trofeje
  naďalej hlásia binárne Získaná/Zamknuté (ako predtým), kým úrovne
  skupiny trojstavovo Získaná/Odhalená/Skrytá (`_tier_states`
  nezmenené) — pri prvom pokuse (`state`→`STATUS_LABELS` všade rovnako)
  by samostatné zamknuté-ale-odhalené trofeje nezmyselne hlásili
  "Odhalená" namiesto "Zamknuté"; opravené pred nasadením.
- `_draw_right_panel_bg()` — odstránený riadok s pozičným počítadlom
  "X/Y" (bolo pletúce vedľa jediného správneho počítadla v hlavičke,
  ktoré už aj predtým počítalo každú úroveň samostatne —
  `len(ACHIEVEMENTS)` má každú úroveň ako vlastné ID).
- `_draw_row()` — výraznejšie zvýraznenie vybranej položky: jasnejšia
  výplň, hrubší (3px) zlatý rám a zvislý akcentový pruh vľavo, namiesto
  pôvodného len o niečo hrubšieho rámu.
- `_draw_tier_card()` — rímsky štítok úrovne presunutý POD kartičku
  (predtým prekrýval spodok obrázka), karta sa kreslí cez `_draw_card_icon`.

### Overenie
- `python -m achievements.test_achievements` — bez zmeny logiky, PASS.
- Headless render + simulácia kliknutia na všetky riadky aj kartičky
  úrovní pri 7 rozlíšeniach (1024×768 … 3840×2160) — bez výnimky.
- `tester/regression_layout.py` — všetkých 15 rozlíšení `[OK]`.
- `tester/regression_screen.py` — stopa 3 kôl byte-presne zhodná
  s `ref_3kola.txt` na PC.
- Vizuálne overené headless screenshoty: skupina so 4 úrovňami (2
  odomknuté farebne správne — bronz+striebro, 2 zamknuté tou istou
  kartou stmavenou + zámkou), skupina s 3 úrovňami, samostatná
  zamknutá+skrytá trofej (karta stmavená+zámka, žiadny prepínač úrovní,
  stav "Zamknuté"), samostatná odomknutá trofej (plná farba, stav
  "Získaná", žiadny prepínač) — presne podľa mockupu.
- Byte-presne overené nasadenie na PC (diff po re-stage).

### Technické obmedzenia
- Rozmery kartičiek úrovní (85×125) sú chápané ako OHRANIČUJÚCI box —
  samotný obrázok sa doň vykreslí proporcionálne (pomer karty 341:512
  ≈ 0.666 vs. boxu 0.68 — rozdiel je vizuálne zanedbateľný, žiadne
  badateľné prázdne pruhy).

### Návrh commit message
`Trofeje kolo 2: horizontálny detail (veľká karta + text vedľa seba), zamknuté karty = stmavená príslušná kovová karta + zámka (rovnaké rozmery ako odomknuté), opravené proporcie ikoniek, výraznejšie zvýraznenie výberu, zrušené duplicitné počítadlo`

## 2026-11-01 — Bugfix: "Každý bod sa počíta" bolo nedosiahnuteľné pri discarde

### Zadanie
User nahlásil, že v ostrej hre zobral všetkých 10 štichov a všetky
bodované karty, "Čistý stôl" sa odomkol, ale "Každý bod sa počíta" nie.

### Diagnóza
`game/round.py.discard_cards()` pripočítava body zahodených kariet do
talonu priamo víťazovi dražby (`winner.add_trick_points(card.points)`) —
reálne skóre kola je teda správne. Trofejový tracker ale o tomto
zahodení nevedel: `round_human_card_points` (čítadlo pre "Každý bod sa
počíta", prah 120 = súčet všetkých kartových bodov v balíku) sa
zvyšovalo len cez `on_trick_won()`, volané len pri štichoch. Ak sa do
talonu zahodila čo i len jedna bodovaná karta (kráľ/horník/dolník —
eso a desiatka sa zahodiť nedajú), 120 bodov sa už v tom kole nedalo
dosiahnuť, aj pri zobratí všetkých 10 štichov.

### Oprava
`achievements/tracker.py`, `on_discard()` — na začiatku metódy pripočíta
body zahodených kariet: `self.round_human_card_points += sum(c.points
for c in discarded_cards)`. Logika "Hláška do koša" (`pretty_but_useless`)
zostala nezmenená, len presunuté `_save()` za koniec metódy (predtým bol
v cykle skorý `return`, ktorý by teraz obišiel aj `_save()` po novom
riadku bodov — upravené, aby sa vždy uložilo).

### Overenie
- `achievements/test_achievements.py` — 3 nové testy v `test_discard()`
  (body sa pripočítajú pri discarde kráľ+horník=7b aj dolník+sedmička=2b;
  "greedy" sa teraz odomkne aj pri 113 zvyšných bodoch zo štichov +
  7 zahodených = 120). Všetky `[PASS]`.
- `tester/regression_screen.py` — stopa bez zmeny.
- Byte-presne overené nasadenie `achievements/tracker.py` a
  `achievements/test_achievements.py` na PC.

### Návrh commit message
`Bugfix: body zahodené do talonu po dražbe sa teraz počítajú aj do trofeje "Každý bod sa počíta"`

## 2026-11-01 — TROFEJE: kolo 3 — dva režimy detailu (výstavný / zbierkový)

### Zadanie
User poslal 2 technické mockupy ("Samostatná trofej – výstavný režim",
"Viacúrovňová trofej – zbierkový režim") s pripomienkou, že práve
nasadený horizontálny detail má príliš veľa nevyužitého priestoru.
Zaviesť 2 odlišné režimy zobrazenia v pravom paneli: pri samostatnej
trofeji veľká karta VYCENTROVANÁ v paneli s textom pod ňou, celá
kompozícia vertikálne vyvážená, bez prepínača úrovní; pri viacúrovňovej
menšia hlavná karta vľavo + text vpravo (nezmenené z kola 2), ale pod
tým VÝRAZNE väčšie kartičky úrovní, rovnomerne rozložené a vycentrované
podľa počtu (2-4), nie natlačené na ľavý okraj; celá kompozícia tiež
vertikálne vyvážená, nie pritlačená hore. Zachovať dizajn, ľavý panel,
počítadlo, logiku trofejí, proporcie obrázkov a zamknuté-karty-s-zámkou
z predošlého kola.

### Zmeny (`gui/achievements_screen.py`)
- `_draw_detail_panel()` teraz vetví na 2 úplne samostatné kresliace
  metódy namiesto jednej spoločnej:
  - `_draw_single_detail(item)` — "výstavný režim": karta 210px vycentrovaná
    (`rc.centerx`), POD ňou názov/stav/podmienka (tiež centrované, vrátane
    viacriadkového popisu — každý riadok centrovaný samostatne). Výška
    celej kompozície (karta + medzery + texty, vrátane SKUTOČNÉHO počtu
    riadkov popisu po zalomení) sa spočíta vopred a kompozícia sa
    vycentruje v `right_content` (`start_y = rc.y + (rc.height-total_h)//2`),
    takže už nie je pritlačená k hornému okraju. Žiadny prepínač úrovní.
  - `_draw_group_detail(row)` + `_group_layout(row)` — "zbierkový režim":
    hlavná karta ZMENŠENÁ na 150px (viac miesta nižšie pre rad úrovní —
    presne ako poznámka v mockupe "Tu je karta o niečo menšia"), kartičky
    úrovní zväčšené na 130px šírky (predtým 85), rozložené rovnomerne:
    `tier_w = min(130, (šírka_panela - medzery)/počet)`, následne
    vycentrované (`start_x = rc.x + (šírka-celková_šírka_radu)/2`) —
    pri 2 úrovniach tak zaberú stred panela s veľkými medzerami, pri
    4 takmer celú šírku, nikdy nie zhluknuté vľavo. Celá kompozícia
    (karta+text blok + nadpis "ÚROVNE TROFEJE" + rad kartičiek + titulky
    pod nimi) je tiež vertikálne vycentrovaná v paneli rovnakým princípom.
  - Pod každou kartičkou úrovne teraz DVA riadky popisu: rímska číslica
    (podľa POZÍCIE v skupine, nie parsovaná z mena — opravuje chýbajúce
    číslovanie pri skupinách typu "Začíname/Rozbehnutý/Stará škola/
    Legenda", ktoré rímsku číslicu v názve vôbec nemajú) a názov kovu
    (Bronz/Striebro/Zlato/Platina, nový slovník `TIER_METAL_NAMES`).
    Odstránená pôvodná `_tier_short_label()` (parsovanie z mena), ktorá
    sa tým stala nepoužívanou.
  - `_draw_status_line()` — nový zdieľaný helper: stav (Získaná/Odhalená/
    Skrytá/Zamknutá) sa pri NEzískanej karte kreslí s malou ikonou zámku
    (`lock.png`) pred textom — vľavo zarovnané v zbierkovom režime,
    centrované vo výstavnom. Opravená aj gramatika: samostatná zamknutá
    trofej teraz hlási "Zamknutá" (zhoda s "trofej", ženský rod) namiesto
    pôvodného nesprávneho "Zamknuté" — platí aj pre podnadpis v ľavom
    zozname.
  - Text detailu "Úroveň II. · Striebro" (rímska číslica + bodka +
    názov kovu) nahrádza predošlé samostatné "Úroveň II.".

### Overenie
- `python -m achievements.test_achievements` — bez zmeny logiky, PASS.
- Headless render + klik na všetky riadky aj kartičky úrovní pri
  1366×768 / 1920×1080 / 3840×2160 — bez výnimky.
- `tester/regression_layout.py` — všetkých 15 rozlíšení `[OK]`.
- `tester/regression_screen.py` — stopa 3 kôl byte-presne zhodná
  s `ref_3kola.txt`.
- Vizuálne overené headless screenshoty: skupina so 4 úrovňami (veľké
  kartičky I-IV s rímskymi číslicami a názvami kovov, rovnomerne
  rozložené), skupina s 2 úrovňami (vycentrované, nie pri okraji),
  samostatná zamknutá+skrytá trofej (vycentrovaná, bez prepínača,
  "Zamknutá" so zámkou), samostatná odomknutá trofej (vycentrovaná,
  zlatá karta, "Získaná") — presne podľa oboch mockupov.
- Byte-presne overené nasadenie na PC (diff po re-stage).

### Návrh commit message
`Trofeje kolo 3: samostatný výstavný režim (vycentrovaná kompozícia) a zbierkový režim (väčšie, rovnomerne rozložené úrovne) v pravom paneli, oprava gramatiky "Zamknutá"`


## 2026-11-01 — TROFEJE: kolo 4 — doladenie zbierkového režimu (dominancia karty, kompaktnosť, zarovnanie)

### Zadanie
User poslal spätnú väzbu na screenshot zbierkového režimu (4 úrovne):
pochválil veľkosť kartičiek úrovní, rozlíšiteľnosť bronz/striebro/zlato/
platina, stmavené zamknuté úrovne so zámkom, čitateľnosť textu aj
prehľadnosť ľavého panela. Požiadal o 5 konkrétnych úprav a jeden
výslovný zákaz zmeny.

### Zmeny
V `gui/achievements_screen.py`, výhradne v zbierkovom režime
(`_group_layout`, `_draw_group_detail`, `_draw_tier_card`):
1. Hlavná karta zväčšená o ~27 % (`CARD_W` 150px → 190px) — teraz
   jednoznačne dominuje nad kartičkami úrovní namiesto rovnakej
   veľkosti.
2. Odstup medzi blokom karta+text a radom úrovní stiahnutý (medzera
   nad popiskom „ÚROVNE TROFEJE" 34px → 18px, pod popiskom 14px → 8px)
   — kompaktnejšie zoskupenie.
3. Horizontálne zarovnanie zjednotené: predtým bola hlavná karta
   pritlačená k ľavému okraju panelu a rad úrovní vycentrovaný
   nezávisle od nej, čo pôsobilo ako dve oddelené časti. Teraz sa
   počíta jedna spoločná šírka bloku (`block_w` = max z {šírka
   karta+text, šírka radu úrovní}) a celá kompozícia — karta, text
   aj rad úrovní — sa centruje v pravom paneli ako jeden celok okolo
   spoločného `block_x`.
4. Popisok „ÚROVNE TROFEJE" vycentrovaný nad radom kariet (pridané
   `label_center_x` do `_group_layout()`; predtým text začínal pri
   ľavom okraji panelu, zatiaľ čo karty boli vycentrované).
5. Výberový rámik vybranej úrovne v spodnom rade zväčšený mimo
   hraníc karty (`rect.inflate(10, 10)` namiesto rámika v rovnakých
   hraniciach ako karta) — pri odomknutej karte (ktorá má už vlastný
   zlatý rám z `_draw_card_icon`) predtým výberový rám splýval
   s jej okrajom; teraz je od karty viditeľne oddelený medzerou.

Výslovne NEZMENENÉ na žiadosť usera: šírka kartičiek úrovní (`TIER_W`
ostáva 130px — pri štyroch úrovniach už bola takmer ideálna, ďalšie
zväčšovanie by mohlo spôsobiť problémy pri menších rozlíšeniach).
Výstavný režim (samostatné trofeje) sa v tomto kole nemenil.

### Overenie
- `python -m achievements.test_achievements` — 67 testov, všetky
  `[PASS]` (bez zmeny trofejovej logiky).
- `tester/regression_layout.py` — všetkých 15 rozlíšení `[OK]`.
- `tester/regression_screen.py` — stopa 3 kôl byte-presne zhodná
  s `ref_3kola.txt` (diff --strip-trailing-cr), žiadny zásah do
  hernej logiky.
- Headless klik-test na KAŽDÝ riadok zoznamu aj KAŽDÚ kartičku
  úrovne pri 7 rozlíšeniach (1024×768 … 3840×2160, vrátane 21:9) —
  bez výnimky.
- Vizuálne overené headless screenshoty pre skupiny s 2, 3 aj
  4 úrovňami — nová centrovaná kompozícia a výberový rámik fungujú
  konzistentne naprieč rôznym počtom úrovní.
- Byte-presne overené nasadenie na PC (diff po re-stage).

### Návrh commit message
`Trofeje kolo 4: väčšia dominantná hlavná karta, kompaktnejšie a jednotne vycentrované rozloženie zbierkového režimu, zarovnanie popisku úrovní a oddelený výberový rámik`


## 2026-11-01 — TROFEJE: kolo 5 — ozdobný oddeľovač, progress bar, vlastné pozadie

### Zadanie
Trojbodová úprava hlavičky a pozadia obrazovky (zadanie usera + 2 mockup
obrázky): (1) "nejaký pekný oddeľovač" namiesto holého popisku „ÚROVNE
TROFEJE", (2) vizuálny progress bar k počítadlu „Odomknuté X z Y" (s
percentami), (3) vlastné pozadie `trophybg.png` (dodané userom priamo
do `assets/graphics/` na PC) namiesto bežného dreveného stola.

### Zmeny
- `gui/ui_style.py` — nová zdieľaná funkcia `draw_divider_label(c, text,
  font, center, half_w, …)`: vodorovný oddeľovač s popiskom v strede
  (tenká GOLD_SOFT čiara s medzerou na GOLD text), rovnaký ozdobný motív
  ako existujúci `draw_screen_title` (len vodorovne okolo textu namiesto
  pod ním) — opakovane použiteľné aj pre ďalšie obrazovky.
- `gui/achievements_screen.py`:
  - `_draw_group_detail()` — popisok „ÚROVNE TROFEJE" teraz kreslený cez
    `ui_style.draw_divider_label`, šírka čiar (`divider_half_w`) viazaná
    na spoločnú šírku bloku karta+text+kartičky úrovní z `_group_layout`
    (pridané do jej návratového slovníka spolu s `label_h`) — oddeľovač
    sa teda automaticky prispôsobí počtu úrovní (2–4) rovnako ako zvyšok
    kompozície z kola 4.
  - `_draw_progress()` — pod textom „Odomknuté X z Y" pribudol vodorovný
    progress bar (tmavý rámček so zaoblenými rohmi, GOLD_SOFT okraj,
    GOLD výplň podľa pomeru odomknutých trofejí) a percento vpravo od
    neho; `HEADER_H` zväčšené zo 140 na 158px, aby sa nová vrstva
    zmestila bez zásahu do zvyšku hlavičky (nadpis TROFEJE sa
    nepohol).
  - `_draw_trophy_backdrop()` (nahrádza `ui_style.draw_backdrop` len na
    tejto obrazovke) — `trophybg.png` (zlatý ozdobný rám na
    tmavomodrom zamate, 1080×768) kreslený cez rovnaký „cover" mechanizmus
    ako drevený stôl inde (`canvas.background`, zachová pomer strán,
    presah orezáva) — keďže hlavný panel prekrýva takmer celé okno
    (margin len 60/20px), v praxi je vidieť presne ozdobný rám obrázka
    na okrajoch, stred (ktorý by aj tak bol prekrytý panelom) sa
    neráta. Chýbajúci súbor nespadne — zástupný drevený stôl
    (`os.path.exists` fallback, rovnaký vzor ako `trophy_paths`/
    `lock_path`). Platí len pre samostatnú obrazovku (`run()` ←
    `_draw_static`); prekrytie počas hry (`AchievementsOverlay`,
    `_draw_over_game`) pozadie nemení — tam je vidieť stmavená
    rozohraná hra, nie backdrop.

### Overenie
- `python -m achievements.test_achievements` — všetky `[PASS]` (bez
  zmeny trofejovej logiky).
- `tester/regression_layout.py` — všetkých 15 rozlíšení `[OK]`.
- `tester/regression_screen.py` — stopa 3 kôl byte-presne zhodná
  s `ref_3kola.txt` (diff --strip-trailing-cr).
- Headless klik-test na KAŽDÝ riadok aj KAŽDÚ kartičku úrovne pri
  7 rozlíšeniach (1024×768 … 3840×2160) — bez výnimky.
- Vizuálne overené headless screenshoty — hlavička s progress barom
  a percentom, oddeľovač „ÚROVNE TROFEJE" pri 2/3/4-úrovňovej skupine,
  nové pozadie v zbierkovom aj výstavnom režime (`trophybg.png` lokálne
  skopírovaný z PC pre test, inak zdieľaný cez `assets/graphics/`).
- Byte-presne overené nasadenie oboch zmenených súborov na PC
  (diff po re-stage).

### Návrh commit message
`Trofeje kolo 5: ozdobný oddeľovač nad úrovňami, progress bar v hlavičke, vlastné pozadie trophybg.png`


## 2026-11-01 — TROFEJE: kolo 5 (oprava) — pozadie patrí do panela DETAIL TROFEJE, nie na celú obrazovku

User po nasadení kola 5 spresnil zadanie: `trophybg.png` bol pôvodne
myslený ako pozadie PRAVÉHO panela „DETAIL TROFEJE", nie ako pozadie
celej obrazovky. Oprava v `gui/achievements_screen.py`:

- `_draw_static()` — vrátené späť na pôvodný `ui_style.draw_backdrop`
  (drevený stôl na celej obrazovke, bezo zmeny oproti stavu pred
  kolom 5); pomocná metóda pre pozadie celého okna odstránená.
- `_draw_right_panel_bg()` — namiesto plnej tmavej výplne
  (`ui_style.draw_panel`) teraz kreslí `trophybg.png` orezaný „cover"
  na presný rozmer PRAVÉHO panela (`canvas.prect` + `canvas.background`),
  s jemným tmavým prekrytím navrchu kvôli čitateľnosti textu a kariet;
  rám (GOLD_SOFT) aj nadpis „DETAIL TROFEJE" + deliaca čiara zostali.
  Pomer strán obrázka (1080×768) je blízky pomeru strán tohto panela,
  takže sa pri orezaní stratí len minimum z rámu/vencov po stranách —
  presne tam, kde to zadanie pôvodne cielilo (laurel vence okolo veľkej
  karty vo "výstavnom" aj "zbierkovom" režime). Chýbajúci súbor
  nespadne — zástupná plná výplň (rovnaký `os.path.exists` vzor).

### Overenie
- `achievements.test_achievements`, `regression_layout` (15 rozlíšení),
  `regression_screen` stopa (diff --strip-trailing-cr) — všetko bezo
  zmeny/[OK]/[PASS], žiadny zásah do logiky.
- Headless klik-test bez výnimky pri 7 rozlíšeniach.
- Vizuálne overené — pozadie teraz viditeľné presne v pravom paneli
  (laurel vence po stranách veľkej karty), ľavý panel aj zvyšok
  obrazovky bezo zmeny (pôvodný drevený stôl).
- Byte-presne overené nasadenie na PC (diff po re-stage).

### Návrh commit message
`Trofeje kolo 5 (oprava): pozadie trophybg.png presunuté z celej obrazovky do panela DETAIL TROFEJE`


## 2026-11-01 — TROFEJE: kolo 5b — odsadenie v zbierkovom režime, čitateľnosť nadpisu DETAIL TROFEJE

Dolaďovanie po predošlej oprave pozadia (kolo 5 oprava):

- `_group_layout()` — odstupy v zbierkovom režime uvoľnené (po kole 4
  boli na hranici "natesno"): medzera pod hlavnou kartou 18→26px,
  medzera pod popiskom „ÚROVNE TROFEJE" 8→14px; `CAPTION_H` (priestor
  pre rímsku číslicu + názov kovu pod kartičkami úrovní) sa už nepočíta
  magickou konštantou, ale presne zo skutočnej výšky použitých fontov,
  aby vždy sedela s `_draw_tier_card`.
- `_draw_tier_card()` — text pod kartičkou (rímska číslica, názov kovu)
  posunutý z `rect.bottom + 6` na `rect.bottom + 14`: pri vybranej
  kartičke je výberový rámik `inflate(10, 10)` (5px navyše na stranu),
  takže text sa predtým do neho takmer dotýkal; medzera medzi rímskou
  číslicou a názvom kovu tiež zväčšená (2→4px).
- `_draw_right_panel_bg()` — nadpis „DETAIL TROFEJE" dostal čierny tieň
  (rovnaká technika ako hlavný nadpis TROFEJE v `draw_screen_title`)
  a pod celou hlavičkou panela (prvých 50px) pribudol o niečo tmavší
  pás navyše — pozadie `trophybg.png` tam má vlastnú ozdobnú kresbu
  a zlatý text v nej predtým zanikal.

### Overenie
- `achievements.test_achievements`, `regression_layout` (15 rozlíšení),
  `regression_screen` stopa (diff --strip-trailing-cr) — bezo zmeny/
  [OK]/[PASS], žiadny zásah do logiky.
- Headless klik-test bez výnimky pri 7 rozlíšeniach.
- Vizuálne overené pri 2/3/4-úrovňových skupinách aj pri samostatnej
  trofeji — odstupy pôsobia voľnejšie, nadpis DETAIL TROFEJE je
  čitateľný aj nad ozdobným pozadím.
- Byte-presne overené nasadenie na PC (diff po re-stage).

### Návrh commit message
`Trofeje kolo 5b: voľnejšie odsadenie v zbierkovom režime, čitateľnejší nadpis DETAIL TROFEJE nad pozadím`


## 2026-11-01 — TROFEJE: kolo 5c — kontrast obrysu zamknutých kariet na tmavomodrom pozadí

User nahlásil slabú viditeľnosť obrysu zamknutých bronzových a
platinových kariet na novom pozadí `trophybg.png` (pravý panel). Samotné
PNG assety sa nemenili — len farba obrysu kresleného navyše.

- `gui/achievements_screen.py` — nová konštanta `LOCKED_CARD_BORDER =
  (150, 126, 90)` (svetlejšia než pôvodný `BORDER_DIM = (90, 72, 48)`),
  použitá len v `_draw_card_icon()` pre obrys zamknutej karty (hlavná
  karta, kartičky úrovní, ikony v ľavom zozname). `BORDER_DIM` zostal
  bezo zmeny tam, kde sa používa inde (orámovanie riadku zamknutej
  skupiny v ľavom zozname).

### Overenie
- `achievements.test_achievements`, `regression_layout` (15 rozlíšení),
  `regression_screen` stopa (diff --strip-trailing-cr) — bezo zmeny/
  [OK]/[PASS].
- Headless klik-test bez výnimky pri 7 rozlíšeniach.
- Vizuálne overené (priblížené výrezy) — obrys zamknutých kariet
  bronz/striebro/zlato/platina je teraz jasne viditeľný na pozadí
  `trophybg.png`.
- Byte-presne overené nasadenie na PC (diff po re-stage).

### Návrh commit message
`Trofeje kolo 5c: svetlejší obrys zamknutých kariet pre lepší kontrast na pozadí trophybg.png`


## 2026-11-01 — TROFEJE: kolo 6 — čitateľnosť zamknutých položiek, verejné prvé ciele, gramatika

Tri drobné úpravy podľa spätnej väzby usera:

1. **Zamknuté trofeje v ľavom zozname pôsobili rovnako nedostupne** —
   `gui/achievements_screen.py`, nová konštanta `LOCKED_ROW_NAME =
   (192, 176, 148)`: názov zamknutej (nevybranej) položky v
   `_draw_row()` je teraz svetlejší než predtým (`TEXT_DIM`), kartička/
   ikona aj podnadpis ("Zamknutá", počet úrovní) ostávajú tlmené
   bezo zmeny — mení sa výhradne farba samotného názvu, pre lepšiu
   orientáciu pri nulovom progrese. Tri stavy zostávajú jasne odlíšené:
   zamknutá (tlmená karta, svetlejší názov) / vybraná (zlatý rámik,
   nezmenené) / získaná (plná farba, zlatý názov, nezmenené).
2. **Prvé dve trofeje odhalené od začiatku** — `achievements/
   definitions.py`: `first_win` ("Začíname I.") a `first_trump`
   ("Poslušne hlásim") stratili príznak `"hidden": True` (teda
   `get("hidden", False)` je teraz `False` — rovnaký vzor ako ostatné
   nikdy neskryté achievementy v súbore). Nový hráč tak od začiatku
   vidí dva konkrétne, okamžite dosiahnuteľné ciele ("Vyhraj svoju
   prvú hru.", "Zahlás svoj prvý tromf.") aj bez toho, aby čokoľvek
   odomkol — zvyšok skupiny `wins_milestone` (Rozbehnutý/Stará škola/
   Legenda) zostáva skrytý a odhaľuje sa ďalej postupne (kaskáda cez
   `_tier_states` sa nemenila, väzba je len na vlastný `hidden`
   príznak každej úrovne). Žiadny zásah do logiky udeľovania ani
   uloženého progresu — len dátový príznak viditeľnosti popisu.
3. **Gramatika** — `"{unlocked_count} zo {n} úrovní"` → `"z"` (predložka
   "zo" bola nesprávna pred číslovkami 2–4, napr. "0 zo 3 úrovní" →
   "0 z 3 úrovní").

### Overenie
- `achievements.test_achievements` (žiadna zmena v očakávaní
  `newly_unlocked` pre `first_win`/`first_trump` — testuje sa udelenie,
  nie viditeľnosť popisu), `regression_layout` (15 rozlíšení),
  `regression_screen` stopa (diff --strip-trailing-cr) — bezo zmeny/
  [OK]/[PASS]; zmena `hidden` je čisto zobrazovacia, na hernú stopu
  nemá vplyv (potvrdené, stopa zhodná).
- Headless klik-test bez výnimky pri 7 rozlíšeniach.
- Vizuálne overené — čerstvý hráč (0/35) vidí čitateľné názvy všetkých
  trofejí v ľavom zozname aj hneď viditeľnú podmienku pri "Začíname"
  a "Poslušne hlásim"; opravená gramatika vo všetkých počtoch úrovní
  (2/3/4).
- Byte-presne overené nasadenie oboch zmenených súborov na PC
  (diff po re-stage).

### Návrh commit message
`Trofeje kolo 6: čitateľnejšie zamknuté položky v zozname, dve prvé trofeje odhalené od začiatku, oprava gramatiky "z/zo"`
