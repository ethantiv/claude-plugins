---
name: outline
description: >
  Użyj, gdy autor ma już wybrany pomysł na książkę (z raportu etapu 1) i chce konspekt rozdział po rozdziale — wyzwalacze: "konspekt", "konspekt rozdziałów", "outline książki", "rozpisz rozdziały", "book-forge konspekt", "architektura książki". Rój agentów (Workflow) buduje fundament (przesłanka, motyw, łuk), dobiera strukturę, rozpisuje rozdziały dobrane do gatunku (obietnica, kluczowe punkty, haczyk, zwrot akcji, przejście emocjonalne) i tnie wypełniacze. Opiera się na raporcie HTML z etapu 1. Wynik: .book-forge/konspekt.md + interaktywny konspekt HTML po polsku. To etap 2 pipeline'u book-forge.
argument-hint: "(opcjonalnie ścieżka do raportu z etapu 1 — skill i tak dopyta)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Konspekt rozdział po rozdziale (rój agentów)

Buduje **szczegółowy konspekt** powieści na podstawie zwycięskiego pomysłu z etapu 1. Napędza go **rój agentów** przez narzędzie **Workflow**: fundament → struktura → rozdziały → cięcie wypełniaczy → redakcja językowa. Książka bez konspektu to miesiące błądzenia — ten etap ma temu zapobiec.

Dla każdego rozdziału powstaje: jednozdaniowa **obietnica**, 3–5 **kluczowych punktów**, **haczyk** na początku i **zwrot akcji** na końcu, **przejście emocjonalne**, a do tego **subwersja** standardowego beatu (strukturalne zaskoczenie zamiast przewidywalnej wypłaty) i **kotwica** (konkretny zapamiętywalny obraz). Całość spina jeden **łuk emocjonalny**, a każdy rozdział musi zasłużyć na swoje miejsce — wypełniacze wycinamy.

## Zasada nadrzędna: polszczyzna (czytaj najpierw)

Tak jak w etapie 1: liczy się **poprawna, naturalna polszczyzna**, bez AI-slopu i bez polsko-angielskich potworków (żargon narracyjny tłumacz — „plot twist” → „zwrot akcji”, „cliffhanger” → „urwanie akcji”, „foreshadowing” → „zapowiadanie wydarzeń”). Pełne reguły i słownik: **`${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`**. Redakcja to wbudowana faza roju **oraz** obowiązkowy przebieg `/unslop:unslop` w głównej sesji.

## Krok 1 — wczytaj raport z etapu 1

1. Znajdź wejście z etapu 1. **Najpierw** szukaj `.book-forge/pomysl.json` (deterministyczny artefakt danych — `idea`, `brief`, `verdict`, `genre`, `reader`); jeśli istnieje, czytaj z niego. **Fallback:** `market-report-*.html` i wyłuskanie obiektu `DATA`. Jeśli jest kilka raportów albo żadnego — zapytaj o ścieżkę przez `AskUserQuestion` (argument traktuj jako podpowiedź).
2. Z `.book-forge/pomysl.json` (lub z obiektu `DATA` w HTML) wyciągnij:
- **gatunek** i **docelowego czytelnika** (placeholdery/nagłówek),
- **zwycięski pomysł** — w `pomysl.json` to pojedynczy obiekt `idea`; w HTML to element `ideas[]` z `winner:true`. Pola: `t`, `en`, `op` (streszczenie), `hook`, `gap` (brak w wariancie idea-spark), `comps`, `protagonista`,
- **brief autora** (`DATA.brief`): `subgenre`, `conventions`, `protagonist`, `protAge`, `protType`, `form`, `format`, `tone`, `spice`, `taboo`, `market` — decyzje z etapu 1, które konspekt ma respektować. **Cały brief przekazujesz do roju** (Krok 3) — bez tego rój pisze konspekt na ślepo wobec tych decyzji. `subgenre` steruje długością, strukturą i `comps`; `conventions` to obietnice, które rozdziały MUSZĄ dowieźć; `format` (`pojedyncza` vs `trylogia`/`seria`) wpływa na łuk: w trybie serii tom 1 zostawia celowo otwarte zasiewy nadrzędne i nie domyka łuku serii (patrz `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md`); `form` (non-fiction) zmienia ramę (łuk czytelnika, nie bohatera); `protagonista`/`tone` zakotwicz w fundamencie i rozdziałach.
- **werdykt** (`verdict`): `rationale`, `whyNow`, `positioning`.
3. Potwierdź interaktywnie (`AskUserQuestion`), który pomysł rozwijać — domyślnie zwycięzca; pozwól wybrać wicemistrza lub wskazać inny.

## Krok 2 — dopytaj o parametry konspektu (interaktywnie)

Przez `AskUserQuestion`. **Długość i liczbę rozdziałów wyprowadź z gatunku i podgatunku** (`brief.subgenre`) — nie podawaj stałej. Najpierw ustal typowy zakres dla niszy (w razie potrzeby przez WebSearch / `comps`), zaproponuj go jako **rekomendowany default**, ale pozwól nadpisać:
- **Docelowa długość** — rekomendacja z gatunku/podgatunku (np. epicka fantasy ~120 000 słów, kryminał ~80 000, romans ~70 000, literatura piękna ~90 000, YA ~75 000). **Nie hardkoduj 60 000** — to długość zbliżona do krótkiej powieści i pasuje do mniejszości gatunków.
- **Liczba rozdziałów** — wyprowadzona z długości i tempa gatunku (thriller: wiele krótkich rozdziałów; epicka fantasy: więcej dłuższych), a nie stałe 14. Dobierz tak, by długość rozdziału była typowa dla niszy.
- **Transformacja** — skąd bohater/czytelnik zaczyna, dokąd dochodzi. Jeśli autor nie wie, niech rój zaproponuje na podstawie pomysłu (zaznacz to). Dla non-fiction (`brief.form`) to transformacja **czytelnika**, nie bohatera.

Konwencji gatunkowych i tabu z etapu 1 (`brief.conventions`, `brief.taboo`) **nie pytaj tu ponownie** — przekazujesz je do roju (Krok 3), gdzie rozdziały muszą je dowieźć (konwencje) lub ich unikać (tabu).

**Rola ekspercka jest stała:** mistrz architektury książek, autor konspektów ponad pięćdziesięciu bestsellerów. Tak ustawiaj agentów.

## Krok 3 — rój agentów (Workflow)

Uruchom rój według skryptu w **`references/workflow-swarm.md`** (podstaw pomysł z polem `protagonista`, gatunek, czytelnika, **cały brief autora** (`subgenre`, `conventions`, `protagonist`, `tone`, `taboo`, `format`, `form`…), werdykt i parametry do `args`). Fazy:

1. **Fundament** — kilku agentów z różnych stron (motyw, łuk bohatera, obietnica rynkowa, zakończenie) proponuje kręgosłup książki → synteza.
2. **Struktura** — kilku agentów proponuje różne szkielety (np. trójakt, podróż bohatera, struktura siedmiu punktów, kishōtenketsu) dopasowane do gatunku → panel sędziów ocenia dopasowanie i **oryginalność** (z realną wagą) oraz subwersję konwencji → wybór/scalenie najlepszego.
3. **Rozdziały** — rozpisanie każdego rozdziału: obietnica, 3–5 kluczowych punktów, haczyk, zwrot akcji, przejście emocjonalne, **subwersja beatu i kotwica emocjonalna**.
4. **Cięcie wypełniaczy** — panel krytyków sprawdza każdy rozdział: czy posuwa łuk, czy ma haczyk i zwrot, **czy nie jest przewidywalny / czy ma realną subwersję**, czy nie jest wypełniaczem → rewizja (łączenie/cięcie).
5. **Redakcja PL** — przepisanie całości na poprawną, naturalną polszczyznę.

**Research strukturalny** (opcjonalny, ale zalecany): agenci sprawdzają przez **WebSearch / agent-browser** konwencje budowy i tempa w tym gatunku oraz to, jak zbudowane są tytuły porównawcze (`comps`) — żeby struktura pasowała do oczekiwań czytelnika, a nie była teoretyczna.

## Krok 4 — unslop (główna sesja)

Po powrocie roju **wywołaj `/unslop:unslop`** na całej prozie konspektu (obietnice, punkty, opisy łuku) i nanieś poprawki. To drugi, obowiązkowy przebieg.

## Krok 5 — zapis (dwa pliki) i walidacja

Zbuduj dwa artefakty (szczegóły: **`references/build-and-verify.md`**):

1. **`.book-forge/konspekt.md`** — kanoniczny plik dla kolejnych etapów (3: `book-bible`, 4: `opening`, 5: `outline-to-scenes`). Markdown: tytuł, przesłanka, transformacja, motyw, struktura, łuk emocjonalny, a potem rozdziały (obietnica, kluczowe punkty, haczyk, zwrot, emocja).
2. **`konspekt-<slug>.html`** — interaktywny widok ze szablonu `${CLAUDE_PLUGIN_ROOT}/skills/outline/assets/outline-template.html` (zakładki: fundament — z łukiem emocjonalnym jako kartą — i rozdziały; rozwijane karty rozdziałów). Wstrzyknij `DATA` i podstaw placeholdery; **zwaliduj** `node --check` + podgląd w agent-browser.

Jeśli istnieje już `.book-forge/konspekt.md`, zapytaj o nadpisanie (`AskUserQuestion`).

## Krok 6 — podsumowanie

Pokaż autorowi: ścieżki obu plików, tytuł książki, liczbę rozdziałów, łuk w jednym zdaniu i które rozdziały rój wyciął jako wypełniacze (i dlaczego). Surowo zgłaszaj braki (np. luki w łuku, których nie udało się domknąć).

## Quick reference

| Aspekt | Reguła |
| --- | --- |
| Wejście | `.book-forge/pomysl.json` z etapu 1 (fallback: `market-report-*.html` / `idea-spark-*.html`) |
| Parametry | Interaktywnie: długość i liczba rozdziałów (rekomendacja z gatunku/podgatunku, nie stała), transformacja |
| Silnik | Rój agentów przez Workflow (`references/workflow-swarm.md`) |
| Rola agentów | Mistrz architektury książek, 50+ bestsellerów |
| Na rozdział | Obietnica + 3–5 punktów + haczyk + zwrot + emocja + subwersja + kotwica |
| Spójność | Jeden łuk emocjonalny; każdy rozdział zasługuje na miejsce |
| Język | Poprawna, naturalna polszczyzna — kryterium #1 |
| Redakcja | Faza roju + `/unslop:unslop` w głównej sesji |
| Wynik | `.book-forge/konspekt.md` (kanon) + `konspekt-<slug>.html` (interaktywny) |
| Walidacja | `node --check` na JS + podgląd/zrzut w agent-browser |

## Najczęstsze błędy

- **Wypełniacze.** Rozdział, który nie posuwa łuku ani fabuły. Naprawa: panel krytyków tnie i łączy; każdy rozdział musi mieć obietnicę, haczyk i zwrot.
- **Płaski łuk.** Te same emocje rozdział po rozdziale. Naprawa: wymuś przejście emocjonalne (wartość +/–) i sprawdź ciągłość między rozdziałami.
- **Przewidywalny beat.** Kompetentnie napisany standard gatunku, którego czytelnik się spodziewa. Naprawa: pole `subwersja` wymusza strukturalne zaskoczenie; krytyk oznacza `przewidywalny` bez `maSubwersje` do rewizji. Dla non-fiction subwersja = kontrintuicja, nie łamanie beatu.
- **Anglicyzmy/AI-slop** w opisach. Naprawa: słownik z `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` + unslop.
- **Ignorowanie etapu 1.** Konspekt ma realizować zwycięski pomysł i jego haczyk, nie własną, nową historię. Dotyczy to też **całego briefu** (ton, profil bohatera, format, konwencje, tabu) — przekaż go do roju, inaczej silnik go nie zobaczy.
- **Zahardkodowana długość/liczba rozdziałów.** 60 000 słów i 14 rozdziałów pasują do mniejszości gatunków. Naprawa: wyprowadź jedno i drugie z gatunku/podgatunku jako rekomendację, z możliwością nadpisania.
- **Zepsuty JS** przez prosty `"` zamiast `”` w stringach. Naprawa: `node --check` (patrz build-and-verify.md).
- **Pominięcie unslopa.** Obowiązkowy przebieg w głównej sesji.
