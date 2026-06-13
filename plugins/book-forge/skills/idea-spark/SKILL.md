---
name: idea-spark
description: >
  Użyj, gdy autor chce SAM szczegółowo zaprojektować powieść w serii pytań — kierunek, bohaterów i świat — a potem dostać 5 wariantów fabuły w tych ramach. Wyzwalacze: "iskra pomysłu", "idea spark", "szczegółowy kwestionariusz", "sam zaprojektuj powieść", "trzon powieści", "5 wariantów fabuły", "autorska wizja książki", "book-forge pomysły". Autorski wariant etapu 1 (zamiast market-report z badaniem rynku): autor ustala TRZON (kierunek/temat, bohaterowie, świat) w szczegółowym kwestionariuszu, a rój generuje 5 różnych zalążków fabuły w tych ramach, ocenia je (bez WebSearch) i wybiera zwycięzcę. Wynik: interaktywny HTML po polsku (trzon + 5 fabuł + werdykt) + .book-forge/pomysl.json (ten sam most do outline i book-bible co market-report). Działa dla DOWOLNEGO gatunku — zawsze pyta o gatunek i docelowego czytelnika.
argument-hint: "(opcjonalnie gatunek i czytelnik — skill i tak dopyta interaktywnie)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit
---

# Iskra pomysłu → autorski trzon + 5 wariantów fabuły

Generuje **interaktywny raport HTML** dla autora, który chce **sam szczegółowo zaprojektować
powieść** — zdecydować o kierunku, bohaterach i świecie — zanim zacznie pisać. To **autorski
wariant etapu 1**: zamiast roju z `market-report` (10 bestsellerów, 3 luki rynkowe, ocena
z WebSearch) jest **szczegółowy kwestionariusz**, w którym autor ustala **trzon** powieści, a
rój przez narzędzie **Workflow** generuje **5 wariantów fabuły** w jego ramach: fabuły → ocena
(bez WebSearch) → werdykt → redakcja językowa.

**Model hybrydowy:** autor ustala **TRZON** (kierunek/temat, bohaterowie, świat) — stały we
wszystkich propozycjach; rój różnicuje **tylko fabułę** — proponuje 5 różnych zalążków fabuły
w ramach trzonu, ocenia je i wybiera najlepszy.

> **idea-spark daje trzon + zarys zwycięskiej fabuły, NIE gotową biblię ani konspekt.** Pełne
> rozwinięcie świata i postaci to `book-bible` (etap 3), rozpisanie fabuły to `outline` (etap 2).
> „Ramy fabuły" w kwestionariuszu to **preferencje przekazane rojowi**, nie scenariusz.

Wynik odpowiada na cztery pytania:
1. jaki jest **trzon** powieści (decyzje autora: kierunek, bohaterowie, świat),
2. **5 wariantów fabuły** z roboczymi tytułami w ramach tego trzonu,
3. ocena każdej fabuły pod kątem rzemiosła i potencjału (1–10),
4. którą fabułę rozwijać i dlaczego.

> **Kiedy `market-report`, a kiedy `idea-spark`?** `market-report` jest dla autora, który chce,
> by **rynek podsunął pomysł** — analizuje bestsellery i luki (WebSearch) i sam proponuje 5
> pomysłów. `idea-spark` jest dla autora, który **ma już wizję i chce nią sterować** — to on
> w szczegółowym kwestionariuszu projektuje trzon (kierunek, bohaterów, świat), a rój tylko
> wariantuje fabułę. idea-spark nie sięga po dane rynkowe — jego fabuły i oceny opierają się na
> **wiedzy gatunkowej modelu**. Zaznacz tę różnicę autorowi (Rule 10 — fail loud).

## Zasada nadrzędna: polszczyzna (czytaj najpierw)

Mówimy o **literaturze**. Jeśli pomysł brzmi sztucznie albo niezrozumiale, nie powstanie z
niego dobra książka. Dlatego najważniejszym kryterium jakości jest **poprawna, naturalna
polszczyzna** — bez AI-slopu i bez polsko-angielskich potworków typu „competence porn”, „hook”,
„worldbuilding”, „found family”.

To nie jest etap kosmetyczny na końcu — to wbudowana faza roju **oraz** obowiązkowy przebieg
`/humanizer:humanizer` w głównej sesji. Pełne reguły i słownik zamian:
**`${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`** (czytaj zanim zbudujesz raport).

## Krok 1 — zebranie wejścia (zawsze interaktywnie)

Wejście zbieraj przez `AskUserQuestion`, nawet jeśli coś podano w argumencie (argument traktuj
jako podpowiedź domyślną). To **serce tego skilla**: w odróżnieniu od `market-report`, gdzie
autor zakreśla tylko ramy, tutaj autor **szczegółowo projektuje trzon powieści**. `AskUserQuestion`
pozwala na maks. 4 pytania na wywołanie, więc kwestionariusz ma **siedem wywołań** (ekranów).
Kolejność jest celowa: **gatunek musi być znany, zanim zbudujesz opcje warstwy adaptacyjnej i
tematycznej** — czytelnik, nurt, konwencje, pytanie dramatyczne, świat itd. wynikają z gatunku.

Trzon dzieli się na trzy obszary **STAŁE** we wszystkich 5 propozycjach: **kierunek/temat**,
**bohaterowie**, **świat**. Czwarty obszar — **ramy fabuły** — to preferencje, w których rój
generuje 5 RÓŻNYCH fabuł (nie ustalasz tu gotowej fabuły).

> **Zasada przewodnia:** każde pytanie poza gatunkiem/czytelnikiem ma opcję **„Niech rój
> zaproponuje"**. Autor z pełną wizją wypełnia trzon szczegółowo; autor, który czegoś jeszcze
> nie wie, oddaje to rojowi i idzie dalej — skill zadziała w obu trybach. Gdy autor wybiera
> konkretną wartość, staje się ona **twardym, niezmiennym elementem trzonu** w prompcie każdego
> agenta. Gdy oddaje pole rojowi, rój dobiera JEDEN wariant i trzyma go we wszystkich 5 fabułach
> (osie trzonu) albo różnicuje (osie fabuły) — patrz `references/workflow-swarm.md`.

**Wywołanie 1 — fundament (2 pytania niezależne od gatunku):**

- **P1 Gatunek / specjalizacja** (`Gatunek`) — np. science fiction, kryminał, fantasy, romans,
  literatura piękna, non-fiction. Napędza całą generację; nic tu nie hardkoduj. Bez gatunku rój przerywa.
- **P2 Format** (`Format`, WYMAGANE) — **`Pojedyncza`** (rekomendowane dla debiutu) / `Trylogia`
  / `Dłuższa seria` / `Niech rój doradzi`. Zmienia ocenę „potencjału serii" i sposób budowy haczyka.

**Wywołanie 2 — nisza (warstwa adaptacyjna, WSZYSTKIE opcje WYPROWADZONE z gatunku z Wywołania 1):**

Opcje budujesz dopiero teraz, znając gatunek. Każda MUSI należeć do wybranego gatunku (klasyczny
błąd: autor wybiera fantasy, a opcje proponują kotwice z obcej niszy). Przykłady to **ilustracje
kształtu** — wygeneruj świeże dla faktycznego gatunku.

- **P3 Docelowy czytelnik** (`Czytelnik`) — opisany przez tytuły/serie kotwiczne gatunku. Np.
  fantasy: „fani Sandersona i Sapkowskiego", „fani romantasy (Maas, Yarros)"; SF: „fani Diuny,
  Projektu Hail Mary". Dołącz **„Niech rój dobierze niszę"**. Definiuje niszę.
- **P4 Podgatunek / nurt** (`Nurt`) — 3–4 żywe podgatunki gatunku, każdy jednozdaniowo, +
  **„Bez preferencji"**. Przykłady: kryminał → przytulny / noir / procedural / psychologiczny;
  fantasy → epicka / grimdark / romantasy / przytulna. **Najsilniejszy sterownik różnicujący nurt.**
- **P5 Konwencje gatunkowe** (`Konwencje`, **multiSelect**) — 4–6 najczęściej poszukiwanych
  obietnic gatunku + **„Niech rój dobierze"**. Przykłady: romans → gwarantowane szczęśliwe
  zakończenie, „wrogowie→kochankowie", powolne zbliżenie; kryminał → zamknięty pokój, narrator
  niewiarygodny, śledztwo proceduralne. Pusty wybór = bez wymagań. Te konwencje stają się
  obietnicami, które fabuły MUSZĄ dowieźć.

**Wywołanie 3 — kierunek i temat (obszar trzonu, 4 pytania):**

Serce autorskiej wizji — „po co" tej powieści. Opcje dopasuj do gatunku/nurtu.

- **P6 Centralne pytanie dramatyczne** (`Pytanie`) — „Wokół jakiego pytania ma krążyć cała
  powieść?". 3 propozycje dopasowane do gatunku (SF → „Co jesteśmy winni obcemu?"; kryminał →
  „Czy prawda jest warta swojej ceny?"; romans → „Czy można pokochać, nie tracąc siebie?") +
  **„Niech rój zaproponuje"** (rekomendowane); pozwól dopisać własne.
- **P7 Przesłanie / teza** (`Przesłanie`) — „Co czytelnik ma poczuć/zrozumieć na ostatniej
  stronie?". 3 propozycje (mroczne „cena władzy zawsze rośnie", pokrzepiające „więź ratuje",
  ambiwalentne „nie ma czystych wyborów") + **„Bez tezy — niech rój dobierze"**.
- **P8 Emocja docelowa** (`Emocja`) — „Jakie doznanie ma dominować?". Dopasuj do gatunku
  (thriller → napięcie / niepokój / adrenalina; romans → tęsknota / ciepło / katharsis;
  literatura piękna → melancholia / olśnienie / żal) + **„Niech rój dobierze"**.
- **P9 Intencja autora** (`Intencja`) — „Po co piszesz tę książkę?": `Sprzedać się na rynku` /
  `Powiedzieć coś ważnego` / `Czysta rozrywka` / **`Niech rój wyważy`** (rekomendowane). Steruje
  wagą sędziów przy ocenie fabuł (rynek → haczyk; przesłanie → wierność tezie; rozrywka → tempo).
  Do `args.intent` przekaż dokładnie jeden z tokenów `rynek` / `przeslanie` / `rozrywka` / `wywaz`
  (inna wartość cicho wpadnie w wagę wyważoną — patrz `WAGA_INTENT` w `references/workflow-swarm.md`).

**Wywołanie 4 — bohaterowie (obszar trzonu, 4 pytania):**

- **P10 Profil protagonisty / forma** (`Bohater`, WYMAGANE) — **dla fikcji:** `Kobieta` /
  `Mężczyzna` / `Zróżnicuj` / `Niech rój wybierze`; przy `Kobieta`/`Mężczyzna` dopytaj opcjonalnie
  o przedział wieku (`młody dorosły 18–25` / `30–45` / `50+` / `bez preferencji`) oraz pozwól
  dopisać typ/rolę (np. „była śledcza"). **Dla non-fiction** zamień na **`Forma`**: `Poradnik` /
  `Reportaż` / `Esej` / `Pamiętnik/wspomnienia` / `Niech rój doradzi`. **Gdy autor wybiera
  konkretną płeć/typ — bohater staje się STAŁY i rój różnicuje wtedy tylko fabułę; gdy wybiera
  `Zróżnicuj`/`Niech rój wybierze` — bohater nie jest ustalony i wraca twardy guard różnorodności
  profilu** (lek na monokulturę „90% jedna bohaterka").
- **P11 Antagonista / siła przeciwna** (`Antagonista`) — „Co stoi protagoniście na drodze?":
  `Konkretna osoba` / `System / instytucja` / `On sam (wewnętrzny)` / `Siła natury lub świata` +
  **„Niech rój dobierze"** (rekomendowane); pozwól dopisać. Dopasuj przykłady do gatunku.
- **P12 Kluczowa relacja** (`Relacja`) — „Która więź jest emocjonalnym sercem książki?". Dopasuj:
  romans → para kochanków; poza romansem → rodzic–dziecko / mentor–uczeń / rywale / przyjaźń na
  śmierć i życie + **„Niech rój dobierze"**.
- **P13 Łuk przemiany** (`Łuk`) — „Jak protagonista ma się zmienić?": `Pozytywny wzrost` /
  `Upadek (tragiczny)` / `Płaski — zmienia świat, nie siebie` / **„Niech rój dobierze"**. Dla
  `Format = seria` rekomenduj „płaski/testujący". Dla non-fiction → łuk czytelnika.

**Wywołanie 5 — świat (obszar trzonu, 4 pytania):**

- **P14 Miejsce i czas** (`Świat`) — „Gdzie i kiedy?". Dopasuj: SF → daleka / bliska przyszłość /
  alternatywna teraźniejszość / kosmos; fantasy → świat wtórny / historyczny z magią / urban
  fantasy; kryminał → mała miejscowość / metropolia / prowincja + **„Niech rój zaproponuje"**;
  pozwól dopisać.
- **P15 Zasady / poziom realizmu** (`Realizm`) — „Jak bardzo świat odbiega od naszego?":
  `Realistyczny` / `Jeden element fantastyczny` / `W pełni fantastyczny (rozbudowany system)` +
  **„Niech rój dobierze"**. Dla literatury pięknej/kryminału domyślnie realistyczny.
- **P16 Atmosfera** (`Atmosfera`) — „Jaki klimat ma oddychać ze stron?". Dopasuj: noir → duszny,
  deszczowy, moralnie szary; cozy → ciepły, bezpieczny; grimdark → brutalny + **„Niech rój
  dobierze"**. Jeśli pokrywa się z P8 (emocja) — nie dubluj, dopytaj o niuans.
- **P17 Skala** (`Skala`) — „Jak duża jest stawka świata?": `Kameralna (jedna osoba/rodzina)` /
  `Lokalna (społeczność/miasto)` / `Wielka (naród/świat/kosmos)` + **„Niech rój dobierze"**.

**Wywołanie 6 — ramy fabuły (4 pytania; preferencje, NIE gotowa fabuła):**

To, w czym rój generuje 5 RÓŻNYCH fabuł. Ustalona wartość obowiązuje wszystkie 5, ale droga do
niej jest różna.

- **P18 Typ głównego konfliktu** (`Konflikt`) — `Człowiek vs człowiek` / `Człowiek vs system/świat`
  / `Człowiek vs samego siebie` + **„Niech rój dobierze"**. To fabularna projekcja antagonisty (P11).
- **P19 Typ zakończenia** (`Zakończenie`) — `Szczęśliwe / domknięte` / `Gorzko-słodkie` /
  `Otwarte / niejednoznaczne` + **„Niech rój dobierze"**. Romans → domyślnie obietnica
  szczęśliwego zakończenia; literatura piękna → dopuść otwarte.
- **P20 Tempo** (`Tempo`) — `Wartkie / akcyjne` / `Wyważone` / `Powolne / immersyjne` +
  **„Niech rój dobierze"**.
- **P21 Punkt wyjścia** (`Zaczyn`) — „Masz iskrę otwarcia? (opcjonalnie)" — pozwól wpisać jedno
  zdanie/obraz startowy lub wybrać **„Nie mam — niech rój wymyśli"**. To ziarno, które rój może
  wpleść, NIE gotowy scenariusz.

**Wywołanie 7 — ton i ograniczenia (4 pytania):**

- **P22 Ton** (`Ton`) — `Mroczny` / `Wyważony` / `Lekki` / **`Bez preferencji`**. Jeśli wynika
  jednoznacznie z P8/P16 — możesz go ustawić bez pytania i zaznaczyć to autorowi.
- **P23 Intensywność** (`Intensywność`) — **oś właściwa dla gatunku**: romans/romantasy → poziom
  scen intymnych (`łagodny` / `umiarkowany` / `wysoki/explicit`); kryminał/thriller/horror →
  poziom przemocy/grozy (`stonowany` / `umiarkowany` / `mocny/drastyczny`); pozostałe → ogólna
  lub `nie dotyczy`. Zawsze dołącz **`Niech rój dobierze`**.
- **P24 Tabu / no-go** (`Tabu`, **multiSelect**) — lista do odznaczenia (przemoc wobec dzieci,
  przemoc seksualna, samobójstwo/autoagresja, tematy religijne/polityczne, +własne) lub
  `Brak — wszystko dozwolone`. Pusty wybór = brak ograniczeń.
- **P25 Rynek** (`Rynek`) — **`PL + ENG`** (rekomendowane, domyślne) / `Głównie PL` /
  `Głównie anglojęzyczny`. Wpływa na dobór orientacyjnych tytułów porównawczych i konwencję
  pakietu wydawniczego (etap 12).

> **POV/czas/długość świadomie NIE pytamy tu** — `book-bible` (etap 3) już je zbiera; dublowanie
> groziłoby rozjazdem. Tu zbieramy trzon i ramy fabuły, które wpływają na dobór fabuły, nie pełną
> biblię ani świat/postacie do kanonu.

> **Tempo wypełniania:** autor w pośpiechu może przeklikać „Niech rój zaproponuje" w większości
> pytań — skill zadziała wtedy jak lekki generator. Autor z wizją wypełnia trzon szczegółowo i
> dostaje 5 fabuł ściśle pod swoją wizję. Oba tryby są poprawne.

**Args do roju (Krok 2)** dzielą się na dwie grupy:

1. **Pola briefu** — trafiają do `DATA.brief` i `pomysl.json`; **kontrakt IDENTYCZNY jak w
   `market-report`** (nie dodawaj ani nie usuwaj kluczy): `genre, reader, subgenre, conventions[],
   protagonist (kobieta|mezczyzna|zroznicuj|dowolny), protAge, protType, form (non-fiction),
   format (pojedyncza|trylogia|seria|doradz), tone, spice (intensywność), taboo[], market, year`.
   Stąd dziedziczą decyzje autora outline i book-bible.
2. **Pola trzonu i ramy fabuły** — nowe, sterują rojem, ale **NIE trafiają do `brief` ani
   `pomysl.json`** (wsiąkają w treść zwycięskiej fabuły): `dramaticQ, theme, emotion, intent,
   antagonist, relation, arc, setting, realism, mood, scale` (trzon) oraz `conflictType, ending,
   pace, seed` (ramy fabuły). Puste = `''` (rój dobiera).

Twarda bramka wejścia roju to wyłącznie `genre` + `reader` — reszta ma miękki fallback.

**Rola ekspercka jest stała:** starszy redaktor do spraw zakupów w dużym wydawnictwie, 20 lat
doświadczenia w wyłapywaniu bestsellerów. Tak ustawiaj wszystkich agentów.

## Krok 2 — rój agentów (Workflow)

Uruchom rój narzędziem **Workflow** według skryptu w **`references/workflow-swarm.md`** (skopiuj
go i podstaw brief i trzon z Kroku 1 do `args` — obie grupy pól). Skrypt parsuje `args` odpornie
i przerywa z błędem przy braku gatunku/czytelnika. Trzon (kierunek/temat, bohaterowie, świat)
trafia do bloku `TRZON` jako **stała wspólna**; ramy fabuły jako ograniczenia. Fazy:

1. **Fabuły** — kilku agentów (różne typy zalążka fabuły × rotowane **soczewki twórcze**) + synteza,
   która **podkręca finalistów** (reguła „wzmacniaj, nie podmieniaj") → **5 różnych fabuł wokół STAŁEGO
   trzonu**, każda z **silnikiem premisy** wiążącym konflikt fabuły z pytaniem dramatycznym. Audyt
   różnorodności jest dwugałęziowy: gdy bohater ustalony — pilnuje różnorodności **fabuł**; gdy
   nieustalony — różnorodności **profilu bohatera**.
2. **Ocena (bez WebSearch)** — panel 4 sędziów na fabułę (redaktor prowadzący, marketing,
   czytelnik docelowy, **adwokat innowacji**) → średnia 1–10. Sędziowie oceniają, **jak fabuła
   realizuje trzon** (z wagą zależną od `intent`), z rzemiosła, **nie researchują rynku**; adwokat
   innowacji premiuje odwagę i działający silnik, nie karze ryzyka.
3. **Werdykt** — wybór zwycięskiej fabuły z uzasadnieniem, „dlaczego teraz”, krokami i wicemistrzem.
4. **Redakcja językowa** — agenci przepisują CAŁĄ prozę na poprawną, naturalną polszczyznę
   (słownik z `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`), usuwają anglicyzmy i AI-slop.

> **Brak faz „Analiza rynku" i „Luki" oraz brak WebSearch/agent-browser to cecha tego wariantu,
> nie brak.** Fabuły powstają z trzonu autora i wiedzy gatunkowej modelu. Nie zmyślaj konkretnych
> liczb sprzedaży ani cytatów ze źródeł — opieraj się na rozpoznaniu rzemieślniczym.

## Krok 3 — humanizer (główna sesja)

Po powrocie roju na złożonej prozie polskiej **wywołaj skill `/humanizer:humanizer`** (przez
narzędzie `Skill`) i nanieś jego poprawki na pola tekstowe raportu. Humanizer czyści wzorce AI;
słownik z `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` pilnuje polskości słownictwa — stosuj oba.

## Krok 4 — budowa raportu HTML

Zbuduj raport z gotowego szablonu `${CLAUDE_PLUGIN_ROOT}/skills/idea-spark/assets/idea-spark-template.html`:
podstaw placeholdery (`{{GENRE}}`, `{{READER}}`, `{{YEAR}}`) i wstrzyknij obiekt `DATA` w miejsce
`/*__INJECT_DATA__*/`. `DATA` niesie sekcje `trzon` (stały trzon autora — tylko do panelu „Trzon
wizji"), `ideas` (5 fabuł), `brief` (cały brief autora z Kroku 1) i `verdict`. Pole `protagonista`
w każdej fabule oraz `DATA.brief` to kanał, którym decyzje (profil bohatera, format, ton, spice,
tabu, rynek) dziedziczą outline i book-bible; pozostałe decyzje trzonu (kierunek, antagonista,
świat…) płyną dalej **wtopione w treść** zwycięskiej fabuły (`op`, `silnik`, `protagonista`).
Dokładny kształt `DATA`, procedura wstrzyknięcia i **walidacja** (`node --check` + podgląd
w agent-browser ze zrzutem ekranu): **`references/build-and-verify.md`**.

## Krok 5 — zapis i podsumowanie

Zapisz do **bieżącego katalogu** jako `idea-spark-<slug-gatunku>.html` (np.
`idea-spark-science-fiction.html`). Pokaż autorowi: ścieżkę pliku, trzon (skrótowo) i zwycięską
fabułę z oceną, oraz krótką notę, że tekst przeszedł redakcję PL + humanizer **oraz że to tryb
bez badania rynku** (wybór warto potwierdzić pełnym `market-report`).

**Zapisz też deterministyczny artefakt danych `.book-forge/pomysl.json`** w folderze roboczym
(utwórz `.book-forge/`, jeśli nie istnieje): `{ "idea": <zwycięska fabuła: t, en, silnik, op, hook,
comps, protagonista>, "brief": DATA.brief, "verdict": DATA.verdict, "genre": "...", "reader": "..." }`.
**Kontrakt jest IDENTYCZNY jak w `market-report` — nie dodawaj klucza `trzon` ani nowych pól
`brief`** (decyzje trzonu są już wtopione w `idea.op/silnik/protagonista` zwycięzcy). To
**kanoniczny most** do etapów 2–3: outline i book-bible czytają najpierw `.book-forge/pomysl.json`
(deterministycznie), a HTML traktują jako fallback. Etapy 2–3 nie widzą różnicy (nie wymagają pola `gap`).

## Ściąga

| Aspekt | Reguła |
| --- | --- |
| Wynik | `./idea-spark-<gatunek>.html` (interaktywny, 3 zakładki: trzon / 5 fabuł / werdykt) + `.book-forge/pomysl.json` |
| Silnik | Rój przez Workflow: trzon (stały) → 5 fabuł (`references/workflow-swarm.md`) |
| Wejście | Zawsze interaktywne (`AskUserQuestion`): gatunek + czytelnik + szczegółowy trzon (7 ekranów) |
| Rola agentów | Starszy redaktor ds. zakupów, 20 lat |
| Dane | Z wiedzy gatunkowej modelu — **bez WebSearch/agent-browser** |
| Język | Poprawna, naturalna polszczyzna — kryterium #1 |
| Redakcja | Faza roju + `/humanizer:humanizer` w głównej sesji |
| Walidacja | `node --check` na JS + podgląd/zrzut w agent-browser |

## Najczęstsze błędy

- **Anglicyzmy i kalki** w polskim tekście („hook”, „found family”, „plot armor”). Naprawa:
  słownik zamian z `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` + humanizer.
- **AI-slop** (nadęcia „stanowi/podkreśla”, triady, nadmiar myślników). Naprawa: humanizer i
  krótsze, konkretne zdania.
- **Zepsuty JS** przez prosty `"` zamiast `”` wewnątrz stringów. Naprawa: trzymaj cudzysłowy
  treści jako `„ ”`, waliduj `node --check` (patrz build-and-verify.md).
- **Zmyślone twarde dane.** To tryb bez badania rynku — NIE podawaj konkretnych liczb
  sprzedaży, zaliczek ani cytatów ze źródeł, których nie znasz na pewno. Tytuły porównawcze
  podawaj orientacyjnie, z wiedzy.
- **Rój zmienił trzon między fabułami zamiast tylko fabuły.** Trzon (świat, bohater, pytanie
  dramatyczne, antagonista-typ, przesłanie) jest STAŁY — różnić ma się tylko fabuła. Naprawa: twarda
  instrukcja „TRZON STAŁY, różnicuj TYLKO fabułę" w prompcie generowania i syntezy + audyt
  różnorodności fabuł (gałąź dla ustalonego bohatera w `references/workflow-swarm.md`).
- **Monokultura — zależnie od trzonu.** Gdy bohater ustalony (trzon) — pilnuj różnorodności **fabuł**
  (5 zalążków nie może dzielić jednego szkieletu zdarzeń). Gdy bohater nieustalony (P10 = `Zróżnicuj`/
  `Niech rój wybierze`) — pilnuj różnorodności **profilu bohatera** (np. nie „90% bohaterka 50–60 lat").
  Naprawa: dwugałęziowy audyt różnorodności w `references/workflow-swarm.md`.
- **Fabuła bez silnika premisy** (płaska sytuacja, konflikt doklejony z zewnątrz). Naprawa: każda
  fabuła ma pole `silnik` — strukturalną sprzeczność wiążącą konflikt fabuły z pytaniem dramatycznym
  trzonu (jak „idealna żona, która zaplanowała własne morderstwo"). Wymóg jest w prompcie generowania
  i u adwokata innowacji.
- **Przewidywalność nagradzana zamiast karana.** Bezpieczna, poprawna fabuła nie jest celem. Adwokat
  innowacji premiuje świeżość; synteza podkręca finalistów regułą „wzmacniaj, nie podmieniaj" (surowa
  fabuła zostaje rozpoznawalna). Soczewki twórcze rozbijają jednolitość poznawczą generatorów.
- **Hardkodowanie SF.** To skill ogólny — wszystko wynika z podanego gatunku i czytelnika.
- **`args` jako string JSON.** Workflow bywa, że podaje `args` jako tekst, nie obiekt —
  `args.genre` wychodzi `undefined`. Naprawa: skrypt parsuje `args` odpornie w `try/catch` i
  przerywa z czytelnym błędem przy braku gatunku/czytelnika (guard w `references/workflow-swarm.md`).
- **Pominięcie humanizera.** Obowiązkowy przebieg w głównej sesji, nie opcja.
