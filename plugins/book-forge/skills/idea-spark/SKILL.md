---
name: idea-spark
description: >
  Użyj, gdy autor chce SZYBKO wygenerować 5 pomysłów na książkę z samego kwestionariusza, BEZ badania rynku i nisz — wyzwalacze: "iskra pomysłu", "pomysły na książkę szybko", "5 pomysłów", "idea spark", "pomysł bez analizy rynku", "book-forge pomysły". Lekki wariant etapu 1 (zamiast pełnego market-report): rój generuje 5 pomysłów z roboczymi tytułami na podstawie briefu autora, ocenia je redaktorsko (bez WebSearch) i wybiera zwycięzcę. Wynik: interaktywny HTML po polsku + .book-forge/pomysl.json (zasila outline i book-bible). Działa dla DOWOLNEGO gatunku — zawsze pyta o gatunek/pasję i docelowego czytelnika.
argument-hint: "(opcjonalnie gatunek i czytelnik — skill i tak dopyta interaktywnie)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit
---

# Iskra pomysłu → 5 pomysłów na książkę (lekki rój)

Generuje **interaktywny raport HTML** dla autora, który chce szybko dostać garść pomysłów na
książkę, zanim zacznie pisać — **bez pełnego badania rynku i nisz**. To **lekki wariant
etapu 1**: zamiast 6-fazowego roju z `market-report` (10 bestsellerów, 3 luki rynkowe, ocena
z WebSearch) zostaje sam **kwestionariusz** i **generowanie 5 pomysłów** lekkim rojem przez
narzędzie **Workflow**: pomysły → ocena (bez WebSearch) → werdykt → redakcja językowa.

Wynik odpowiada na trzy pytania:
1. 5 pomysłów z roboczymi tytułami (zrodzonych z briefu autora),
2. ocena każdego pod kątem rzemiosła i potencjału (1–10),
3. który pomysł rozwijać i dlaczego.

> **Kiedy pełny `market-report`, a kiedy `idea-spark`?** Jeśli autor potrzebuje twardych
> danych rynkowych (co realnie się sprzedaje, gdzie są luki, ocena oparta o WebSearch) — to
> `market-report`. `idea-spark` jest szybki i tani, ale jego pomysły i oceny opierają się na
> **wiedzy gatunkowej modelu**, nie na świeżych danych z rynku. Zaznacz tę różnicę autorowi
> (Rule 10 — fail loud).

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
jako podpowiedź domyślną). Zbierasz **brief autora**, który steruje całym rojem i jest
dziedziczony przez kolejne etapy (outline, book-bible) — patrz Krok 4/5. `AskUserQuestion`
pozwala na maks. 4 pytania na wywołanie, więc **trzy wywołania**. Kolejność jest celowa:
**gatunek musi być znany, zanim zbudujesz opcje warstwy adaptacyjnej** (P2 czytelnik,
P9 podgatunek, P10 konwencje), bo wszystkie te opcje wynikają z gatunku — dlatego cała warstwa
adaptacyjna jest w osobnym, drugim wywołaniu. Kwestionariusz ma trzy warstwy: **fundament**
(niezależny od gatunku), **warstwa adaptacyjna** (opcje generowane z gatunku — to ona różnicuje
profil między gatunkami) i **ton/ograniczenia**.

> **Zasada przewodnia:** każde pytanie poza gatunkiem/czytelnikiem ma opcję **„Bez preferencji
> — niech rój zaproponuje"**. idea-spark służy autorowi, który jeszcze nie wie; brak tej opcji
> zmuszałby do zgadywania. Gdy autor wybiera „bez preferencji", rój dobiera sam, ALE w syntezie
> działa twardy warunek różnorodności (5 pomysłów nie może dzielić jednego profilu bohatera —
> patrz `references/workflow-swarm.md`). Gdy autor wybiera konkretną wartość — staje się ona
> twardym wymaganiem w prompcie każdego agenta.

**Wywołanie 1 — fundament (2 pytania niezależne od gatunku):**

- **P1 Gatunek / specjalizacja** (`Gatunek`) — np. science fiction, kryminał, fantasy, romans,
  literatura piękna, non-fiction. Napędza całą generację; nic tu nie hardkoduj. Bez gatunku rój przerywa.
- **P4 Format** (`Format`, WYMAGANE) — **`Pojedyncza`** (rekomendowane dla debiutu) / `Trylogia`
  / `Dłuższa seria` / `Niech rój doradzi`. Zmienia ocenę „potencjału serii" i sposób budowy haczyka.

**Wywołanie 2 — warstwa adaptacyjna (do 4 pytań, WSZYSTKIE opcje WYPROWADZONE z gatunku z Wywołania 1):**

To serce profilowania — bez niej kwestionariusz daje ten sam profil dla każdego gatunku. **Opcje
budujesz dopiero teraz, znając gatunek.** Każda opcja MUSI należeć do wybranego gatunku (klasyczny
błąd: autor wybiera fantasy, a opcje proponują kotwice/nurty z obcej niszy). Podane niżej przykłady
to **ilustracje kształtu** — wygeneruj świeże dla faktycznego gatunku.

- **P2 Docelowy czytelnik** (`Czytelnik`) — opisany przez tytuły/serie kotwiczne wybranego
  gatunku. Np. fantasy: „fani Sandersona i Sapkowskiego", „fani romantasy (Maas, Yarros)",
  „fani grimdark (Abercrombie, Martin)"; science fiction: „fani Diuny, Projektu Hail Mary".
  Dołącz **„Bez preferencji — niech rój dobierze niszę"**. Definiuje niszę.
- **P9 Podgatunek / nurt** (`Nurt`) — 3–5 żywych podgatunków wybranego gatunku, każdy z
  jednozdaniowym opisem, + **„Bez preferencji"**. Przykłady kształtu: kryminał → przytulny /
  noir / procedural / psychologiczny; fantasy → epicka / grimdark / romantasy / przytulna; SF →
  twarda / space opera / cyberpunk / dystopia. **Najsilniejszy sterownik różnicujący gatunki** —
  zawęża pomysły do nurtu.
- **P10 Konwencje gatunkowe** (`Konwencje`, **multiSelect**) — 4–6 najczęściej poszukiwanych
  przez czytelników tego gatunku obietnic/konwencji + **„Niech rój dobierze"**. To, na co
  czytelnik realnie kupuje. Przykłady kształtu: romans → gwarantowane szczęśliwe zakończenie,
  „wrogowie→kochankowie", powolne zbliżenie; kryminał → zamknięty pokój, narrator niewiarygodny,
  śledztwo proceduralne; fantasy → twardy system magii, rodzina z wyboru, wybraniec kontra
  antybohater. Pusty wybór = bez wymagań. Te konwencje stają się obietnicami, które 5 pomysłów
  MUSI dowieźć.
- **P3 Profil bohatera / forma** (`Bohater`, WYMAGANE) — **dla fikcji:** `Kobieta` / `Mężczyzna`
  / **`Zróżnicuj`** (rekomendowane — wymusza różne profile bohaterów w 5 pomysłach) /
  `Niech rój wybierze`; przy `Kobieta`/`Mężczyzna` dopytaj opcjonalnie o przedział wieku
  (`młody dorosły 18–25` / `30–45` / `50+` / `bez preferencji`) oraz pozwól dopisać typ/rolę
  (np. „była śledcza", „antybohater"). **Dla non-fiction** (gdzie nie ma bohatera) zamień to
  pytanie na **`Forma`**: `Poradnik` / `Reportaż` / `Esej` / `Pamiętnik/wspomnienia` /
  `Niech rój doradzi`. To pytanie **bezpośrednio łamie monokulturę** „90% bohaterka 50–60 lat":
  gdy autor nie narzuca profilu, rój dawniej konwergował na jednej niszy demograficznej.

**Wywołanie 3 — ton i ograniczenia (4 pytania):**

- **P5 Ton** (`Ton`) — `Mroczny` / `Wyważony` / `Lekki` / **`Bez preferencji`** (rekomendowane).
  Jeśli „lekki/przytulny" pokrywa się z wybranym w P9 nurtem — nie dubluj, dopytaj tylko o natężenie.
- **P6 Intensywność** (`Intensywność`) — **pytaj o oś właściwą dla gatunku**:
  romans/romantasy → poziom scen intymnych (`łagodny` / `umiarkowany` / `wysoki/explicit`);
  kryminał/thriller/horror → poziom przemocy/grozy (`stonowany` / `umiarkowany` / `mocny/drastyczny`);
  pozostałe → ogólna intensywność lub `nie dotyczy`. Zawsze dołącz **`Niech rój dobierze`**
  (rekomendowane).
- **P7 Tabu / no-go** (`Tabu`, **multiSelect**) — lista do odznaczenia (przemoc wobec dzieci,
  przemoc seksualna, samobójstwo/autoagresja, tematy religijne/polityczne, +własne) lub
  `Brak — wszystko dozwolone`. Pusty wybór = brak ograniczeń.
- **P8 Rynek** (`Rynek`) — **`PL + ENG`** (rekomendowane, domyślne, najszerszy ogląd) /
  `Głównie PL` / `Głównie anglojęzyczny`. Wpływa na dobór orientacyjnych tytułów porównawczych
  i konwencję pakietu wydawniczego (etap 12).

> **POV/czas/długość świadomie NIE pytamy tu** — `book-bible` (etap 3) już je zbiera; dublowanie
> groziłoby rozjazdem. idea-spark zbiera tylko to, co wpływa na dobór pomysłu.

Zebrane odpowiedzi przekazujesz do roju w `args` jako: `genre, reader, subgenre, conventions[],
protagonist (kobieta|mezczyzna|zroznicuj|dowolny), protAge, protType, form (non-fiction),
format (pojedyncza|trylogia|seria|doradz), tone, spice (intensywność), taboo[], market, year`
(Krok 2). Brief trafia też do `DATA.brief` w raporcie (Krok 4), skąd dziedziczą go outline i
book-bible. **Umowa pól briefu MUSI być identyczna jak w `market-report`** — to kontrakt
dziedziczenia do etapów 2–3.

**Rola ekspercka jest stała:** starszy redaktor do spraw zakupów w dużym wydawnictwie, 20 lat
doświadczenia w wyłapywaniu bestsellerów. Tak ustawiaj wszystkich agentów.

## Krok 2 — lekki rój agentów (Workflow)

Uruchom rój narzędziem **Workflow** według skryptu w **`references/workflow-swarm.md`** (skopiuj
go i podstaw cały brief z Kroku 1 do `args`). Skrypt parsuje `args` odpornie i przerywa z błędem
przy braku gatunku/czytelnika. Fazy:

1. **Pomysły** — kilku agentów (różne kategorie) + synteza → 5 pomysłów z roboczymi tytułami,
   z twardymi guardami różnorodności (lek na monokulturę „90% jedna bohaterka").
2. **Ocena (bez WebSearch)** — panel 3 sędziów na pomysł (redaktor prowadzący, marketing,
   czytelnik docelowy) → średnia 1–10. Sędziowie oceniają z rzemiosła, **nie researchują rynku**.
3. **Werdykt** — wybór zwycięzcy z uzasadnieniem, „dlaczego teraz”, krokami i wicemistrzem.
4. **Redakcja językowa** — agenci przepisują CAŁĄ prozę na poprawną, naturalną polszczyznę
   (słownik z `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`), usuwają anglicyzmy i AI-slop.

> **Brak faz „Analiza rynku" i „Luki" oraz brak WebSearch/agent-browser to cecha tego wariantu,
> nie brak.** Pomysły powstają z wiedzy gatunkowej modelu i z briefu. Nie zmyślaj konkretnych
> liczb sprzedaży ani cytatów ze źródeł — opieraj się na rozpoznaniu rzemieślniczym.

## Krok 3 — humanizer (główna sesja)

Po powrocie roju na złożonej prozie polskiej **wywołaj skill `/humanizer:humanizer`** (przez
narzędzie `Skill`) i nanieś jego poprawki na pola tekstowe raportu. Humanizer czyści wzorce AI;
słownik z `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` pilnuje polskości słownictwa — stosuj oba.

## Krok 4 — budowa raportu HTML

Zbuduj raport z gotowego szablonu `${CLAUDE_PLUGIN_ROOT}/skills/idea-spark/assets/idea-spark-template.html`:
podstaw placeholdery (`{{GENRE}}`, `{{READER}}`, `{{YEAR}}`) i wstrzyknij obiekt `DATA` w miejsce
`/*__INJECT_DATA__*/`. `DATA` niesie sekcje `ideas`, `brief` (cały brief autora z Kroku 1) i
`verdict`. Pole `protagonista` w każdym pomyśle oraz `DATA.brief` to kanał, którym decyzje
(profil bohatera, format, ton, spice, tabu, rynek) dziedziczą outline i book-bible. Dokładny
kształt `DATA`, procedura wstrzyknięcia i **walidacja** (`node --check` + podgląd w agent-browser
ze zrzutem ekranu): **`references/build-and-verify.md`**.

## Krok 5 — zapis i podsumowanie

Zapisz do **bieżącego katalogu** jako `idea-spark-<slug-gatunku>.html` (np.
`idea-spark-science-fiction.html`). Pokaż autorowi: ścieżkę pliku, zwycięski pomysł z oceną,
i krótką notę, że tekst przeszedł redakcję PL + humanizer **oraz że to lekki tryb bez badania
rynku** (wybór warto potwierdzić pełnym `market-report`).

**Zapisz też deterministyczny artefakt danych `.book-forge/pomysl.json`** w folderze roboczym
(utwórz `.book-forge/`, jeśli nie istnieje): `{ "idea": <zwycięski pomysł: t, en, op, hook,
comps, protagonista>, "brief": DATA.brief, "verdict": DATA.verdict, "genre": "...", "reader": "..." }`.
To **kanoniczny most** do etapów 2–3: outline i book-bible czytają najpierw `.book-forge/pomysl.json`
(deterministycznie), a HTML traktują jako fallback. Format jest zgodny z tym, który produkuje
`market-report` — etapy 2–3 nie widzą różnicy (nie wymagają pola `gap`).

## Ściąga

| Aspekt | Reguła |
| --- | --- |
| Wynik | `./idea-spark-<gatunek>.html` (interaktywny, 2 zakładki) + `.book-forge/pomysl.json` |
| Silnik | Lekki rój przez Workflow (`references/workflow-swarm.md`) |
| Wejście | Zawsze interaktywne (`AskUserQuestion`): gatunek + czytelnik + brief |
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
- **Zmyślone twarde dane.** To lekki tryb bez researchu — NIE podawaj konkretnych liczb
  sprzedaży, zaliczek ani cytatów ze źródeł, których nie znasz na pewno. Tytuły porównawcze
  podawaj orientacyjnie, z wiedzy.
- **Monokultura pomysłów (np. „90% bohaterka 50–60 lat").** Naprawa: pytanie P3 (profil bohatera)
  + twarde guardy różnorodności w syntezie i audytor różnorodności przed werdyktem (wszystko w
  `references/workflow-swarm.md`). Gdy autor jawnie ustalił profil — monokultura jest OK.
- **Hardkodowanie SF.** To skill ogólny — wszystko wynika z podanego gatunku i czytelnika.
- **`args` jako string JSON.** Workflow bywa, że podaje `args` jako tekst, nie obiekt —
  `args.genre` wychodzi `undefined`. Naprawa: skrypt parsuje `args` odpornie w `try/catch` i
  przerywa z czytelnym błędem przy braku gatunku/czytelnika (guard w `references/workflow-swarm.md`).
- **Pominięcie humanizera.** Obowiązkowy przebieg w głównej sesji, nie opcja.
