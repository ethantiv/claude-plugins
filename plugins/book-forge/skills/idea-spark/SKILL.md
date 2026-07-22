---
name: idea-spark
description: >
  Użyj, gdy autor chce SZYBKO dostać 5 zaskakująco nieoczywistych pomysłów na fabułę powieści — bez badania rynku, po krótkim wejściu. Wyzwalacze: "iskra pomysłu", "idea spark", "szybki pomysł na książkę", "zaskakujący pomysł", "nieoczywista fabuła", "5 wariantów fabuły", "book-forge pomysły". Lekki wariant etapu 1 (zamiast market-report z badaniem rynku): autor podaje minimum (gatunek, czytelnik, poziom dziwności, tabu + opcjonalne zawężenie), a rój generuje 5 RÓŻNYCH, celowo nieoczywistych fabuł z twardą bramką anty-klisza, ocenia je pod kątem świeżości i wykonalności (bez WebSearch) i wybiera zwycięzcę. Wynik: interaktywny HTML po polsku (5 fabuł + werdykt) + .book-forge/pomysl.json (ten sam most do outline i book-bible co market-report). Działa dla DOWOLNEGO gatunku — zawsze pyta o gatunek i docelowego czytelnika.
argument-hint: "(opcjonalnie gatunek i czytelnik — skill i tak dopyta interaktywnie)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit
---

# Iskra pomysłu → 5 zaskakująco nieoczywistych fabuł

Generuje **interaktywny raport HTML** dla autora, który chce **szybko** dostać świeże, nieoczywiste pomysły na fabułę — bez badania rynku i bez długiego kwestionariusza. To **lekki wariant etapu 1**: zamiast roju z `market-report` (10 bestsellerów, 3 luki, ocena z WebSearch) autor podaje **minimum**, a rój przez narzędzie **Workflow** generuje **5 różnych fabuł** z **twardą bramką anty-klisza**: pomysły → ocena świeżości (bez WebSearch) → werdykt.

> **idea-spark daje zarys 5 fabuł i zwycięzcę, NIE gotową biblię ani konspekt.** Rozwinięcie
> świata i postaci to `book-bible` (etap 3), rozpisanie fabuły to `outline` (etap 2).

Wynik odpowiada na trzy pytania:
1. **5 wariantów fabuły** z roboczymi tytułami, celowo nieoczywistych,
2. ocena każdej pod kątem **świeżości, silnika premisy i wykonalności** (1–10),
3. którą fabułę rozwijać i dlaczego.

> **Kiedy `market-report`, a kiedy `idea-spark`?** `market-report` = pomysł **ugruntowany w
> danych rynkowych** (WebSearch, agent-browser — wolny, dokładny). `idea-spark` = **czysta iskra
> twórcza** — szybka, bez sieci, celowo zaskakująca; jego pomysły i oceny opierają się na
> **wiedzy gatunkowej modelu**, nie na rynku. Zaznacz tę różnicę autorowi (Rule 10 — fail loud).

## Zasada nadrzędna: polszczyzna (czytaj najpierw)

Mówimy o **literaturze**. Jeśli pomysł brzmi sztucznie albo niezrozumiale, nie powstanie z niego dobra książka. Najważniejszym kryterium jakości jest **poprawna, naturalna polszczyzna** — bez AI-slopu i bez polsko-angielskich potworków typu „competence porn”, „hook”, „worldbuilding”, „found family”.

W tym lekkim wariancie **nie ma osobnej fazy redakcji w roju** — zasady polszczyzny są wbite w prompty roju (proza wraca już po polsku), a finalny szlif robi **obowiązkowy** przebieg `/unslop:unslop` w głównej sesji. Pełne reguły i słownik zamian: **`${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`** (czytaj zanim zbudujesz raport).

## Krok 1 — zebranie wejścia (zawsze interaktywnie, 2 ekrany)

Wejście zbieraj przez `AskUserQuestion`, nawet jeśli coś podano w argumencie (argument traktuj jako podpowiedź domyślną). Kwestionariusz jest **lekki — dwa wywołania (ekrany)**. Kolejność jest celowa: **gatunek musi być znany, zanim zbudujesz opcje ekranu 2** (nurt, ton, profil bohatera wynikają z gatunku).

**Ekran 1 — rdzeń (WYMAGANY, 4 pytania):**

- **P1 Gatunek / specjalizacja** (`Gatunek`) — np. science fiction, kryminał, fantasy, romans, literatura piękna, non-fiction. Napędza całą generację; nic tu nie hardkoduj. Bez gatunku rój przerywa.
- **P2 Docelowy czytelnik** (`Czytelnik`) — opisany przez tytuły/serie kotwiczne gatunku (np. fantasy: „fani Sandersona i Sapkowskiego”; SF: „fani Diuny, Projektu Hail Mary”). Dołącz **„Niech rój dobierze niszę"**. Definiuje niszę.
- **P3 Poziom dziwności** (`Dziwność`) — „Jak bardzo nieoczywiste mają być pomysły?": `Bezpieczne` (sprawdzone schematy, świeżość w detalu) / **`Śmiałe`** (rekomendowane — omija oczywiste klisze) / `Dzikie` (maksimum zaskoczenia, ale **rzemiosło zostaje twardą podłogą** — pomysł i tak musi dać się napisać). Do `args.weird` przekaż token `bezpieczne` / `smiale` / `dzikie`.
- **P4 Tabu / no-go** (`Tabu`, **multiSelect**) — lista do odznaczenia (przemoc wobec dzieci, przemoc seksualna, samobójstwo/autoagresja, tematy religijne/polityczne, +własne) lub `Brak — wszystko dozwolone`. **Zostaje na ekranie 1**, bo zaskakujący generator bez no-go może trafić w temat, którego autor nie chce. Pusty wybór = brak ograniczeń.

**Ekran 2 — opcjonalne zawężenie (4 pytania; każde z opcją „Niech rój dobierze"):**

Dla autora z wizją. Autor w pośpiechu przeklikuje „Niech rój dobierze" we wszystkich — skill zadziała jak najlżejszy generator. Opcje budujesz **dopiero teraz**, znając gatunek z ekranu 1.

- **P5 Podgatunek / nurt** (`Nurt`) — 3–4 żywe podgatunki gatunku, każdy jednozdaniowo, + **„Niech rój dobierze"**. Zawęża pomysły do nurtu. → `args.subgenre`.
- **P6 Profil protagonisty / forma** (`Bohater`) — **dla fikcji:** `Kobieta` / `Mężczyzna` / `Zróżnicuj` / **`Niech rój wybierze`**; przy `Kobieta`/`Mężczyzna` pozwól dopisać wiek/typ. **Dla non-fiction** zamień na **`Forma`**: `Poradnik` / `Reportaż` / `Esej` / `Pamiętnik` / `Niech rój doradzi`. Konkret = bohater STAŁY (rój różnicuje tylko fabułę); `Zróżnicuj`/`Niech rój wybierze` = wraca guard różnorodności profilu. → `args.protagonist` (+`protAge`/`protType`/`form`).
- **P7 Ton** (`Ton`) — `Mroczny` / `Wyważony` / `Lekki` / **`Niech rój dobierze`**. → `args.tone`.
- **P8 Format** (`Format`) — **`Pojedyncza`** (rekomendowane dla debiutu) / `Trylogia` / `Dłuższa seria` / **`Niech rój doradzi`**. Zmienia ocenę potencjału serii. → `args.format`.

> **POV/czas/długość, konwencje gatunkowe, intensywność, rynek — świadomie NIE pytamy.**
> `book-bible` (etap 3) i tak je zbiera; w lekkim wariancie schodzą do miękkich domyślnych
> (rój dobiera). Tu zbieramy minimum, które steruje doborem i poziomem zaskoczenia.

**Args do roju (Krok 2)** dzielą się na dwie grupy:

1. **Pola briefu** — trafiają do `DATA.brief` i `pomysl.json`; **kontrakt IDENTYCZNY jak w `market-report`** (nie dodawaj ani nie usuwaj kluczy): `genre, reader, subgenre, conventions[], protagonist (kobieta|mezczyzna|zroznicuj|dowolny), protAge, protType, form (non-fiction), format (pojedyncza|trylogia|seria|doradz), tone, spice (intensywność), taboo[], market, year`. Pola, o które nie pytamy, przekaż jako miękkie domyślne (`''` / `[]` / `'dobierz'`). Stąd dziedziczą decyzje autora outline i book-bible.
2. **Pole sterujące kreatywnością** — `weird` (`bezpieczne|smiale|dzikie`). NIE trafia do `brief` ani `pomysl.json` (wsiąka w treść pomysłów) — pokazujemy je tylko w belce nagłówka HTML.

Twarda bramka wejścia roju to wyłącznie `genre` + `reader` — reszta ma miękki fallback.

**Rola ekspercka jest stała:** starszy redaktor do spraw zakupów w dużym wydawnictwie, 20 lat doświadczenia w wyłapywaniu bestsellerów. Tak ustawiaj wszystkich agentów.

## Krok 2 — rój agentów (Workflow)

Uruchom rój narzędziem **Workflow** według skryptu w **`references/workflow-swarm.md`** (skopiuj go i podstaw brief + `weird` z Kroku 1 do `args`). Skrypt parsuje `args` odpornie i przerywa z błędem przy braku gatunku/czytelnika. **11 agentów, 3 fazy, bez WebSearch:**

1. **Pomysły** — 4 generatory (różne typy zalążka fabuły × rotowane **soczewki twórcze**) z **twardą bramką anty-klisza** skalowaną suwakiem dziwności + 1 synteza, która podkręca finalistów (reguła „wzmacniaj, nie podmieniaj") i pilnuje różnorodności (audyt **wtopiony** w prompt, bez osobnego agenta) → **5 różnych, nieoczywistych fabuł**, każda z **silnikiem premisy**.
2. **Ocena (bez WebSearch)** — **1 krytyk świeżości na fabułę** (5 agentów) ocenia trzy wymiary 1–10: świeżość, silnik premisy, rzemiosło (twarda podłoga). Łączną ocenę liczymy deterministycznie w JS. Bez marketingu i czytelnika docelowego — oni ścierali dziwność.
3. **Werdykt** — wybór zwycięzcy łączącego nieoczywistość z wykonalnością, „dlaczego teraz”, krokami i wicemistrzem.

> **Brak faz „Analiza rynku" i „Luki", brak WebSearch/agent-browser oraz brak osobnej fazy
> redakcji to cechy tego wariantu, nie braki.** Fabuły powstają z wiedzy gatunkowej modelu. Nie
> zmyślaj liczb sprzedaży ani cytatów ze źródeł.

## Krok 3 — unslop (główna sesja)

Po powrocie roju na prozie polskiej **wywołaj skill `/unslop:unslop`** (przez narzędzie `Skill`) i nanieś jego poprawki na pola tekstowe raportu. To **jedyny** przebieg redakcji (faza w roju została usunięta) — obowiązkowy, nie opcja. Słownik z `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` pilnuje polskości słownictwa — stosuj oba.

## Krok 4 — budowa raportu HTML

Zbuduj raport z gotowego szablonu `${CLAUDE_PLUGIN_ROOT}/skills/idea-spark/assets/idea-spark-template.html`: podstaw placeholdery (`{{GENRE}}`, `{{READER}}`, `{{YEAR}}`) i wstrzyknij obiekt `DATA` w miejsce `/*__INJECT_DATA__*/`. `DATA` niesie sekcje `ideas` (5 fabuł), `brief` (cały brief autora), `weird` (poziom dziwności — do belki nagłówka) i `verdict`. **Dwie zakładki: „5 fabuł" i „Werdykt"** (zakładka „Trzon wizji" została usunięta). Pole `protagonista` w każdej fabule oraz `DATA.brief` to kanał, którym decyzje (profil bohatera, format, ton, tabu…) dziedziczą outline i book-bible. Dokładny kształt `DATA`, procedura wstrzyknięcia i **walidacja** (`node --check` + podgląd w agent-browser ze zrzutem ekranu): **`references/build-and-verify.md`**.

## Krok 5 — zapis i podsumowanie

Zapisz do **bieżącego katalogu** jako `idea-spark-<slug-gatunku>.html` (np. `idea-spark-science-fiction.html`). Pokaż autorowi: ścieżkę pliku, zwycięską fabułę z oceną, oraz krótką notę, że tekst przeszedł unslop **oraz że to lekki tryb bez badania rynku** (wybór warto potwierdzić pełnym `market-report`).

**Zapisz też deterministyczny artefakt danych `.book-forge/pomysl.json`** w folderze roboczym (utwórz `.book-forge/`, jeśli nie istnieje): `{ "idea": <zwycięska fabuła: t, en, silnik, op, hook, comps, protagonista>, "brief": DATA.brief, "verdict": DATA.verdict, "genre": "...", "reader": "..." }`. **Kontrakt jest IDENTYCZNY jak w `market-report` — nie dodawaj klucza `weird` ani nowych pól `brief`.** To **kanoniczny most** do etapów 2–3: outline i book-bible czytają najpierw `.book-forge/pomysl.json` (deterministycznie), a HTML traktują jako fallback. Etapy 2–3 nie widzą różnicy (nie wymagają pola `gap`).

## Ściąga

| Aspekt | Reguła |
| --- | --- |
| Wynik | `./idea-spark-<gatunek>.html` (interaktywny, 2 zakładki: 5 fabuł / werdykt) + `.book-forge/pomysl.json` |
| Silnik | Rój przez Workflow: 11 agentów, 3 fazy (`references/workflow-swarm.md`) |
| Wejście | Zawsze interaktywne (`AskUserQuestion`): 2 ekrany — rdzeń (gatunek, czytelnik, dziwność, tabu) + opcjonalne zawężenie |
| Kreatywność | Twarda bramka anty-klisza skalowana suwakiem dziwności; rzemiosło = twarda podłoga |
| Rola agentów | Starszy redaktor ds. zakupów, 20 lat |
| Dane | Z wiedzy gatunkowej modelu — **bez WebSearch/agent-browser** |
| Język | Poprawna, naturalna polszczyzna — kryterium #1 |
| Redakcja | Wbita w prompty roju + `/unslop:unslop` w głównej sesji (brak osobnej fazy w roju) |
| Walidacja | `node --check` na JS + podgląd/zrzut w agent-browser |

## Najczęstsze błędy

- **Anglicyzmy i kalki** w polskim tekście („hook”, „found family”, „plot armor”). Naprawa: słownik zamian z `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` + unslop.
- **AI-slop** (nadęcia „stanowi/podkreśla”, triady, nadmiar myślników). Naprawa: unslop i krótsze, konkretne zdania.
- **Zepsuty JS** przez prosty `"` zamiast `”` wewnątrz stringów. Naprawa: trzymaj cudzysłowy treści jako `„ ”`, waliduj `node --check` (patrz build-and-verify.md).
- **Zmyślone twarde dane.** To tryb bez badania rynku — NIE podawaj konkretnych liczb sprzedaży, zaliczek ani cytatów ze źródeł. Tytuły porównawcze podawaj orientacyjnie, z wiedzy.
- **Przewidywalność nagradzana zamiast karana.** Bezpieczna, poprawna fabuła nie jest celem. Bramka anty-klisza (skalowana suwakiem dziwności) i krytyk świeżości premiują nieoczywistość; synteza podkręca finalistów regułą „wzmacniaj, nie podmieniaj". Klisza = kara.
- **„Dzikie" bez rzemiosła.** Nawet na poziomie `dzikie` rzemiosło zostaje twardą podłogą — krytyk dociska łączną ocenę, gdy z fabuły nie da się napisać książki. Naprawa: wymiar `rzemioslo` w ocenie i logika podłogi w `references/workflow-swarm.md`.
- **Monokultura — zależnie od profilu.** Gdy bohater ustalony (ekran 2) — pilnuj różnorodności **fabuł**; gdy nieustalony — różnorodności **profilu bohatera**. Naprawa: dwugałęziowy guard wtopiony w prompt syntezy w `references/workflow-swarm.md`.
- **Fabuła bez silnika premisy** (płaska sytuacja, konflikt doklejony z zewnątrz). Naprawa: pole `silnik` w każdej fabule + wymiar `silnik` w ocenie.
- **Hardkodowanie SF.** To skill ogólny — wszystko wynika z podanego gatunku i czytelnika.
- **`args` jako string JSON.** Workflow bywa, że podaje `args` jako tekst, nie obiekt — `args.genre` wychodzi `undefined`. Naprawa: skrypt parsuje `args` odpornie w `try/catch` i przerywa z czytelnym błędem przy braku gatunku/czytelnika.
- **Pominięcie unslopa.** Obowiązkowy przebieg w głównej sesji, nie opcja (zwłaszcza że faza redakcji w roju została usunięta).
