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
