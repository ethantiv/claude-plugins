---
name: market-report
description: >
  Użyj, gdy autor chce znaleźć lukę rynkową i pomysł na książkę ZANIM napisze pierwsze słowo — wyzwalacze: "raport rynku", "luka rynkowa", "pomysł na książkę", "market report", "co się sprzedaje w moim gatunku", "book-forge raport". Rój agentów (Workflow) analizuje 10 bestsellerów niszy, wskazuje 3 niedoceniane luki, proponuje 5 pomysłów z roboczymi tytułami, ocenia każdy 1–10 i wybiera zwycięzcę. Wynik to interaktywny raport HTML po polsku. Działa dla DOWOLNEGO gatunku — zawsze pyta o gatunek/pasję i docelowego czytelnika. To etap 1 pipeline'u book-forge.
argument-hint: "(opcjonalnie gatunek i czytelnik — skill i tak dopyta interaktywnie)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Raport rynku → pomysł na książkę (rój agentów)

Generuje **interaktywny raport HTML** dla autora, który chce znaleźć lukę na rynku i najlepszy pomysł na książkę, zanim zacznie pisać. Napędza go **rój agentów** przez narzędzie **Workflow**: pięć faz analizy plus faza redakcji językowej, a potem główna sesja domyka raport (humanizer, lokalizacja tytułów, budowa HTML).

Wynik odpowiada na pięć pytań z briefu autora:
1. 10 najlepiej sprzedających się książek w niszy,
2. 3 niedoceniane aspekty (luki), których brakuje konkurencji,
3. 5 pomysłów z roboczymi tytułami,
4. ocena każdego pod kątem potencjału komercyjnego (1–10),
5. który pomysł rozwijać i dlaczego.

## Zasada nadrzędna: polszczyzna (czytaj najpierw)

Mówimy o **literaturze**. Jeśli konspekt brzmi sztucznie albo niezrozumiale, nie powstanie z niego dobra książka. Dlatego najważniejszym kryterium jakości jest **poprawna, naturalna polszczyzna** — bez AI-slopu i bez polsko-angielskich potworków typu „competence porn”, „hook”, „worldbuilding”, „found family”.

To nie jest etap kosmetyczny na końcu — to wbudowana faza roju **oraz** obowiązkowy przebieg `/humanizer:humanizer` w głównej sesji. Pełne reguły, słownik zamian i zasady lokalizacji tytułów: **`${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`** (czytaj zanim zbudujesz raport).

## Krok 1 — zebranie wejścia (zawsze interaktywnie)

Wejście zbieraj przez `AskUserQuestion`, nawet jeśli coś podano w argumencie (argument traktuj jako podpowiedź domyślną). Zbierasz **brief autora**, który steruje całym rojem i jest dziedziczony przez kolejne etapy (outline, book-bible) — patrz Krok 5/6. `AskUserQuestion` pozwala na maks. 4 pytania na wywołanie, więc **trzy wywołania**. Kolejność jest celowa: **gatunek musi być znany, zanim zbudujesz opcje warstwy adaptacyjnej** (P2 czytelnik, P9 podgatunek, P10 konwencje), bo wszystkie te opcje wynikają z gatunku — dlatego cała warstwa adaptacyjna jest w osobnym, drugim wywołaniu. Kwestionariusz ma trzy warstwy: **fundament** (niezależny od gatunku), **warstwa adaptacyjna** (opcje generowane z gatunku — to ona różnicuje profil między gatunkami) i **ton/ograniczenia**.

> **Zasada przewodnia:** każde pytanie poza gatunkiem/czytelnikiem ma opcję **„Bez preferencji — niech rój zaproponuje"**. Market-report służy autorowi, który jeszcze nie wie; brak tej opcji zmuszałby do zgadywania. Gdy autor wybiera „bez preferencji", rój dobiera sam, ALE w syntezie działa twardy warunek różnorodności (5 pomysłów nie może dzielić jednego profilu bohatera — patrz `references/workflow-swarm.md`). Gdy autor wybiera konkretną wartość — staje się ona twardym wymaganiem w prompcie każdego agenta.

**Wywołanie 1 — fundament (2 pytania niezależne od gatunku):**

- **P1 Gatunek / specjalizacja** (`Gatunek`) — np. science fiction, kryminał, fantasy, romans, literatura piękna, non-fiction. Napędza całą analizę; nic tu nie hardkoduj. Bez gatunku rój przerywa.
- **P4 Format** (`Format`, WYMAGANE) — **`Pojedyncza`** (rekomendowane dla debiutu) / `Trylogia` / `Dłuższa seria` / `Niech rój doradzi`. Zmienia ocenę „potencjału serii" u sędziego finansowego i sposób budowy haczyka.

**Wywołanie 2 — warstwa adaptacyjna (do 4 pytań, WSZYSTKIE opcje WYPROWADZONE z gatunku z Wywołania 1):**

To serce profilowania — bez niej kwestionariusz daje ten sam profil dla każdego gatunku. **Opcje budujesz dopiero teraz, znając gatunek.** Każda opcja MUSI należeć do wybranego gatunku (klasyczny błąd: autor wybiera fantasy, a opcje proponują kotwice/nurty z obcej niszy). Podane niżej przykłady to **ilustracje kształtu** — wygeneruj świeże dla faktycznego gatunku.

- **P2 Docelowy czytelnik** (`Czytelnik`) — opisany przez tytuły/serie kotwiczne wybranego gatunku. Np. fantasy: „fani Sandersona i Sapkowskiego", „fani romantasy (Maas, Yarros)", „fani grimdark (Abercrombie, Martin)"; science fiction: „fani Diuny, Projektu Hail Mary". Dołącz **„Bez preferencji — niech rój dobierze niszę"**. Definiuje niszę.
- **P9 Podgatunek / nurt** (`Nurt`) — 3–5 żywych podgatunków wybranego gatunku, każdy z jednozdaniowym opisem, + **„Bez preferencji"**. Przykłady kształtu: kryminał → przytulny / noir / procedural / psychologiczny; fantasy → epicka / grimdark / romantasy / przytulna; SF → twarda / space opera / cyberpunk / dystopia. **Najsilniejszy sterownik różnicujący gatunki** — zawęża wyszukiwanie bestsellerów i luk w roju.
- **P10 Konwencje gatunkowe** (`Konwencje`, **multiSelect**) — 4–6 najczęściej poszukiwanych przez czytelników tego gatunku obietnic/konwencji + **„Niech rój dobierze"**. To, na co czytelnik realnie kupuje (Goodreads/BookTok). Przykłady kształtu: romans → gwarantowane szczęśliwe zakończenie, „wrogowie→kochankowie", powolne zbliżenie; kryminał → zamknięty pokój, narrator niewiarygodny, śledztwo proceduralne; fantasy → twardy system magii, rodzina z wyboru, wybraniec kontra antybohater. Pusty wybór = bez wymagań. Te konwencje stają się obietnicami, które 5 pomysłów MUSI dowieźć.
- **P3 Profil bohatera / forma** (`Bohater`, WYMAGANE) — **dla fikcji:** `Kobieta` / `Mężczyzna` / **`Zróżnicuj`** (rekomendowane — wymusza różne profile bohaterów w 5 pomysłach) / `Niech rój wybierze`; przy `Kobieta`/`Mężczyzna` dopytaj opcjonalnie o przedział wieku (`młody dorosły 18–25` / `30–45` / `50+` / `bez preferencji`) oraz pozwól dopisać typ/rolę (np. „była śledcza", „antybohater"). **Dla non-fiction** (gdzie nie ma bohatera) zamień to pytanie na **`Forma`**: `Poradnik` / `Reportaż` / `Esej` / `Pamiętnik/wspomnienia` / `Niech rój doradzi`. To pytanie **bezpośrednio łamie monokulturę** „90% bohaterka 50–60 lat": gdy autor nie narzuca profilu, rój dawniej konwergował na jednej niszy demograficznej.

**Wywołanie 3 — ton i ograniczenia (4 pytania):**

- **P5 Ton** (`Ton`) — `Mroczny` / `Wyważony` / `Lekki` / **`Bez preferencji`** (rekomendowane). Jeśli „lekki/przytulny" pokrywa się z wybranym w P9 nurtem — nie dubluj, dopytaj tylko o natężenie.
- **P6 Intensywność** (`Intensywność`) — **pytaj o oś właściwą dla gatunku** (dawne „treści 18+" było romansocentryczne): romans/romantasy → poziom scen intymnych (`łagodny` / `umiarkowany` / `wysoki/explicit`); kryminał/thriller/horror → poziom przemocy/grozy (`stonowany` / `umiarkowany` / `mocny/drastyczny`); pozostałe → ogólna intensywność lub `nie dotyczy`. Zawsze dołącz **`Niech rój dobierze`** (rekomendowane). Twarda zmienna rynkowa.
- **P7 Tabu / no-go** (`Tabu`, **multiSelect**) — lista do odznaczenia (przemoc wobec dzieci, przemoc seksualna, samobójstwo/autoagresja, tematy religijne/polityczne, +własne) lub `Brak — wszystko dozwolone`. Pusty wybór = brak ograniczeń.
- **P8 Rynek** (`Rynek`) — **`PL + ENG`** (rekomendowane, domyślne, najszerszy ogląd) / `Głównie PL` / `Głównie anglojęzyczny`. Wpływa na comps i konwencję pakietu wydawniczego (etap 12).

> **POV/czas/długość świadomie NIE pytamy tu** — `book-bible` (etap 3) już je zbiera; dublowanie groziłoby rozjazdem. Market-report zbiera tylko to, co wpływa na dobór pomysłu i ocenę rynkową.

Zebrane odpowiedzi przekazujesz do roju w `args` jako: `genre, reader, subgenre, conventions[], protagonist (kobieta|mezczyzna|zroznicuj|dowolny), protAge, protType, form (non-fiction), format (pojedyncza|trylogia|seria|doradz), tone, spice (intensywność), taboo[], market, year` (Krok 2). Brief trafia też do `DATA.brief` w raporcie (Krok 5), skąd dziedziczą go outline i book-bible.

**Rola ekspercka jest stała:** starszy redaktor do spraw zakupów w dużym wydawnictwie, 20 lat doświadczenia w wyłapywaniu bestsellerów. Tak ustawiaj wszystkich agentów.

## Krok 2 — rój agentów (Workflow)

Uruchom rój narzędziem **Workflow** według skryptu w **`references/workflow-swarm.md`** (skopiuj go i podstaw cały brief z Kroku 1 do `args`: `genre, reader, subgenre, conventions, protagonist, protAge, protType, form, format, tone, spice, taboo, market, year`). Skrypt rozprasza wektor demografii, a w syntezie luk i pomysłów egzekwuje **twarde guardy różnorodności** (to lek na monokulturę „90% jedna bohaterka"). Fazy:

> **Pułapka `args`.** Workflow potrafi przekazać `args` do skryptu jako **string JSON**, a nie obiekt — wtedy `args.genre` jest `undefined` i puste pole zatruwa prompt każdego agenta (rój zwraca „gatunek: undefined” i odmawia pracy). Skrypt w `references/workflow-swarm.md` parsuje `args` odpornie i przerywa z błędem przy braku gatunku/czytelnika. Jeśli kopiujesz skrypt własnoręcznie, zachowaj ten guard. Po fazie 1 i tak zweryfikuj, że pierwsze tytuły są z właściwego gatunku — nie dopuszczaj „undefined” dalej.

1. **Analiza rynku** — kilkunastu agentów z różnych perspektyw → 10 bestsellerów.
2. **Luki** — kilku agentów + synteza → 3 niedoceniane luki.
3. **Pomysły** — kilku agentów (różne kategorie × rotowane **soczewki twórcze**) + synteza, która **podkręca finalistów** (reguła „wzmacniaj, nie podmieniaj") → 5 pomysłów z roboczymi tytułami, każdy z **silnikiem premisy** (wbudowaną sprzecznością napędzającą konflikt).
4. **Ocena** — panel 5 sędziów na pomysł (redaktor/finanse, marketing, czytelnik docelowy, analityk sprzedaży, **adwokat innowacji**) → średnia 1–10. Adwokat innowacji premiuje odwagę i działający silnik, nie karze ryzyka.
5. **Werdykt** — wybór zwycięzcy z uzasadnieniem, „dlaczego teraz”, krokami i wicemistrzem.
6. **Redakcja językowa** — agenci przepisują CAŁĄ prozę na poprawną, naturalną polszczyznę (słownik z `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`), usuwają anglicyzmy i AI-slop.

**Świeże dane z rynku są obowiązkowe.** Agenci sięgają po nie przez **WebSearch / WebFetch** oraz CLI **agent-browser** (uruchamiane z `Bash`) — listy bestsellerów, Goodreads/lubimyczytać, Reddit, BookTok, nagrody gatunku, transakcje wydawnicze. Nie zmyślaj liczb; każdą opieraj na źródle. Sterowania realną przeglądarką nie odpalaj w dziesiątkach kopii naraz (bywa zawodne) — używaj go celowo.

## Krok 3 — humanizer (główna sesja)

Po powrocie roju na złożonej prozie polskiej **wywołaj skill `/humanizer:humanizer`** (przez narzędzie `Skill`) i nanieś jego poprawki na pola tekstowe raportu. Humanizer czyści wzorce AI; słownik z `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` pilnuje polskości słownictwa — stosuj oba.

## Krok 4 — lokalizacja tytułów (agent-browser)

Tytuły istniejących książek (10 bestsellerów + tytuły porównawcze) podawaj po **polsku, jeśli mają polskie wydanie** — zweryfikuj to przez agent-browser na lubimyczytac.pl (wchodź na stronę książki, sprawdź pole „Wydawnictwo”/„Tłumacz”, nie ufaj samemu podglądowi wyszukiwarki). Brak polskiego wydania → zostaw oryginał. Tytuły **propozycji** są polskie (robocze), z oryginałem w podtytule. Procedura i pułapki: **`${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`**.

## Krok 5 — budowa raportu HTML

Zbuduj raport z gotowego szablonu `${CLAUDE_PLUGIN_ROOT}/skills/market-report/assets/report-template.html`: podstaw placeholdery (`{{GENRE}}`, `{{READER}}`, `{{YEAR}}`) i wstrzyknij obiekt `DATA` w miejsce `/*__INJECT_DATA__*/`. `DATA` niesie też sekcję **`DATA.brief`** (cały brief autora z Kroku 1) oraz pole `protagonista` w każdym pomyśle — to kanał, którym decyzje (profil bohatera, format, ton, spice, tabu, rynek) dziedziczą outline i book-bible. Dokładny kształt `DATA`, procedura wstrzyknięcia i **walidacja** (`node --check` + podgląd w agent-browser ze zrzutem ekranu): **`references/build-and-verify.md`**. To jest krok krytyczny technicznie; `DATA` wstrzykujemy jako plik JSON przez `json.dumps`, więc eskejpowanie cudzysłowów jest automatyczne — i tak zwaliduj wynik (`node --check`).

## Krok 6 — zapis i podsumowanie

Zapisz do **bieżącego katalogu** jako `market-report-<slug-gatunku>.html` (np. `market-report-science-fiction.html`). Pokaż autorowi: ścieżkę pliku, zwycięski pomysł z oceną, 3 luki i krótką notę, że tekst przeszedł redakcję PL + humanizer. Surowo zgłaszaj, czego nie udało się zweryfikować (np. brak danych rynkowych dla niszowego gatunku).

**Zapisz też deterministyczny artefakt danych `.book-forge/pomysl.json`** w folderze roboczym (utwórz `.book-forge/`, jeśli nie istnieje): `{ "idea": <zwycięski pomysł: t, en, silnik, op, hook, gap, comps, protagonista>, "brief": DATA.brief, "verdict": DATA.verdict, "genre": "...", "reader": "..." }`. To **kanoniczny most** do etapów 2–3: outline i book-bible czytają najpierw `.book-forge/pomysl.json` (deterministycznie), a HTML traktują jako fallback. HTML jest formatem prezentacyjnym — nie zmuszaj kolejnych etapów do wyłuskiwania `DATA` z `<script>` (kruche przy wielu raportach i zmianie szablonu).

## Ściąga

| Aspekt | Reguła |
| --- | --- |
| Wynik | `./market-report-<gatunek>.html` (interaktywny) |
| Silnik | Rój agentów przez Workflow (`references/workflow-swarm.md`) |
| Wejście | Zawsze interaktywne (`AskUserQuestion`): gatunek + czytelnik |
| Rola agentów | Starszy redaktor ds. zakupów, 20 lat |
| Dane | Świeże, przez agent-browser + WebSearch; cytuj źródła |
| Język | Poprawna, naturalna polszczyzna — kryterium #1 |
| Redakcja | Faza roju + `/humanizer:humanizer` w głównej sesji |
| Tytuły | PL gdy jest wydanie (weryfikacja agent-browser); inaczej oryginał |
| Walidacja | `node --check` na JS + podgląd/zrzut w agent-browser |

## Najczęstsze błędy

- **Anglicyzmy i kalki** w polskim tekście („hook”, „found family”, „plot armor”). Naprawa: słownik zamian z `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` + humanizer.
- **AI-slop** (nadęcia „stanowi/podkreśla”, triady, nadmiar myślników). Naprawa: humanizer i krótsze, konkretne zdania.
- **Zepsuty JS** przez prosty `"` zamiast `”` wewnątrz stringów. Naprawa: trzymaj cudzysłowy treści jako `„ ”`, waliduj `node --check` (patrz build-and-verify.md).
- **Zmyślone liczby/daty.** Naprawa: każdą daną opieraj na źródle z sieci.
- **Dryf gatunkowy.** Rój sięga po listy ogólne (NYT, Amazon, Empik), gdzie dominują inne gatunki, i podaje romantasy/poradniki zamiast pozycji z niszy. Szczególnie groźne dla gatunków spoza ścisłej czołówki sprzedaży (np. hard SF). Naprawa: twarda blokada gatunku w `ROLE` + bramka walidacyjna po fazie 1 (oba w `references/workflow-swarm.md`); sięgaj po listy i nagrody gatunkowe.
- **Hardkodowanie SF.** To skill ogólny — wszystko wynika z podanego gatunku i czytelnika.
- **Monokultura pomysłów (np. „90% bohaterka 50–60 lat").** Bias nie jest zaszyty w kodzie — jest emergentny: rój szukający „niedoobsługiwanej" niszy konwerguje na jednej demografii. Naprawa: pytanie P3 (profil bohatera) daje autorowi kontrolę, a rozproszony wektor demografii + twarde guardy różnorodności w syntezie (max 1 luka persony, ≥3 osie różnicy między 5 pomysłami) i audytor różnorodności przed werdyktem łamią monokulturę (wszystko w `references/workflow-swarm.md`). Gdy autor jawnie ustalił profil — monokultura jest OK i audytor ją przepuszcza.
- **`args` jako string JSON.** Workflow bywa, że podaje `args` jako tekst, nie obiekt — `args.genre` wychodzi `undefined` i całe wejście roju jest puste. Naprawa: skrypt parsuje `args` odpornie w `try/catch` (`typeof args === 'string' ? JSON.parse(args) : (args || {})`) i przerywa z czytelnym błędem przy braku gatunku/czytelnika lub niepoprawnym JSON (guard w `references/workflow-swarm.md`); w fazie 1 (Analiza rynku) działa bramka gatunku — po niej sprawdź, czy tytuły są z gatunku, a nie „undefined”.
- **Pomysł bez silnika premisy** (płaska sytuacja, konflikt doklejony z zewnątrz). Naprawa: każdy pomysł ma pole `silnik` — strukturalną sprzeczność, która sama generuje fabułę; wymóg w prompcie generowania i u adwokata innowacji, który premiuje odwagę zamiast karać ryzyko.
- **Pominięcie humanizera.** Obowiązkowy przebieg w głównej sesji, nie opcja.
