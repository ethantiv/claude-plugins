---
name: write-scene
description: >
  Użyj, gdy autor ma siatkę scen w biblii i chce napisać prozę pojedynczej sceny — wyzwalacze: "napisz scenę", "rozpisz scenę", "proza sceny", "write scene", "book-forge scena". Rój agentów pisze JEDNĄ scenę według karty z siatki, sekwencyjnie, w zafiksowanym POV/czasie, głosem narratora i idiolektami postaci z biblii, na podstawie wyciągu z biblii (świat, glosariusz, otwarte zasiewy) i streszczeń poprzednich scen. Tylko czyta i PROPONUJE dopisy do kanonu — nie zapisuje sam, lecz po napisaniu robi handoff do kontroli ciągłości. Wynik: .book-forge/sceny/<id>.md + automatyczny handoff do continuity-check (zapis do biblii). Etap 7 pipeline'u book-forge.
argument-hint: "(opcjonalnie id sceny, np. R3S2 — skill i tak dopyta)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Napisz scenę (rój agentów)

Pisze prozę jednej sceny z siatki scen. To pierwszy etap, w którym powstaje właściwy tekst powieści. Jednostką jest **scena** (cel postaci → konflikt → zwrot), nie rozdział-esej; głos to **narrator i postacie z biblii**, nigdy „głos autora”.

Najpierw przeczytaj `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` (sekcja „kolejność redakcji per scena”, pola RO/RUNTIME, anty-dryf) i `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` (język).

## Zasada nadrzędna

Trzy reguły wbudowane: (1) jednostką jest scena z celem, konfliktem i zwrotem — bez „głosu autora”, bez wstrzykiwanych osobistych historii, bez „stop and think” co N słów, bez wymuszonego cliffhangera (haczyk wynika ze sceny); (2) proza w głosie z biblii — narrator + osobne idiolekty postaci; pokazuj, nie mów; dialog z podtekstem; świat dawkowany przez akcję; (3) ten etap **tylko czyta i proponuje** — nie zapisuje do kanonu (inaczej błąd surowej sceny stałby się „prawdą”).

## Kolejność redakcji — gdzie jesteśmy

To jest etap **„treść”**. Zgodnie ze specyfikacją: treść (tu) → pogłębienie + redakcja developmentalna (`revise-scene`) → kontrola ciągłości (`continuity-check`, jedyny zapis do kanonu) → **humanizer → korekta PL** (`polish-pl`). Dlatego **nie uruchamiaj tu `/humanizer:humanizer`** — to surowa wersja robocza. Pisz od razu dobrą polszczyzną (słownik z `polish-style.md`), ale właściwy przebieg humanizera jest później, by jego wygładzanie nie złamało faktu, głosu ani odmiany nazw przed kontrolą ciągłości.

## Krok 1 — wejście (sekwencyjnie)

1. Wczytaj kanon: `b = bible.load_all()` (przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`). Z `b['kanon_fabularny']['sceny']` weź **kartę sceny** do napisania. Domyślnie pierwsza scena bez gotowej prozy; pozwól wskazać id (`AskUserQuestion`). Bez biblii i siatki scen — przerwij i skieruj do `book-bible` / `outline-to-scenes`.
2. Zbuduj **wyciąg** (nie całą biblię): karta głosu narratora; głosy tylko tych postaci, które są w scenie; zasady świata istotne dla scenerii; hasła glosariusza, które mogą paść (z odmianą); otwarte zasiewy dotyczące tej sceny (z `setup_payoff`); pozycja na osi czasu.
3. **Anty-amnezja:** dołącz streszczenia 2–3 poprzednich scen (z już napisanych `.book-forge/sceny/*.md`), żeby zachować ciągłość. Pisz sekwencyjnie — scena widzi to, co przed nią.
4. **Gotowe otwarcie (`proza_zrodlo`):** jeśli karta wybranej sceny ma pole `proza_zrodlo` i wskazany plik istnieje — albo (fallback) pola brak, ale to pierwsza scena siatki (`sceny[0]`) i w folderze roboczym istnieje `.book-forge/poczatek.md` — wczytaj tę prozę jako **obowiązkowy materiał otwarcia**: rój ma ją zachować i ROZWINĄĆ do docelowej długości w tym samym głosie i POV, nie pisać sceny od nowa ani nie zastępować pierwszych akapitów. To tylko ODCZYT (zgodnie z zasadą „etapy prozy nie zapisują kanonu” — wskaźnik ustawia `outline-to-scenes`). Zob. `proza_zrodlo` w `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md`.
5. **Budżet słów:** jeśli `meta.budzet_slow` i `meta.liczba_scen` są ustawione, policz sugerowaną długość sceny = `budzet_slow / liczba_scen` (z korektą na wagę: scena kluczowa dłuższa, pomostowa krótsza) i przekaż ją jako `dlugosc` do roju. Policz też skumulowaną sumę słów już napisanych scen (`.book-forge/sceny/*.md`) i pokaż autorowi „X / cel" — to chroni przed maszynopisem, który puchnie do 200 tys. słów (agent/wydawca odrzuca). Bez budżetu w `meta` zapytaj o długość jak niżej.
6. Dopytaj `AskUserQuestion`: docelowa długość sceny (np. 800–1500 słów) i czy autor ma uwagi do tej sceny.

**Rola ekspercka:** powieściopisarz piszący w cudzym (ustalonym) głosie — narratora i postaci z biblii.

## Krok 2 — rój agentów (Workflow)

Uruchom rój według **`references/workflow-swarm.md`**. Fazy:

1. **Plan sceny** — mikropunkty w obrębie sceny (jak realizuje cel → konflikt → zwrot, gdzie zmienia się wartość).
2. **Wersja robocza** — dwa warianty prozy z różnym naciskiem (np. mocniej na podtekst dialogu albo mocniej na warstwę zmysłową i akcję), oba zakotwiczone w głosie z biblii. Jeśli z Kroku 1 jest gotowe otwarcie (`proza_zrodlo`/`.book-forge/poczatek.md`), oba warianty muszą z niego WYRASTAĆ (zachować jego początek i głos), a nie pisać sceny od zera.
3. **Wybór/scalenie** — wybór mocniejszego wariantu lub połączenie ich atutów w jedną wersję roboczą.
4. **Zgodność** — niezależny sprawdzający: czy proza jest zgodna z POV/czasem, głosem (karta), nazwami z glosariusza; czy scena realizuje swój cel i ma zwrot ze zmianą wartości. Jeśli FIX — jedna rewizja.
5. **Redakcja PL (lekka)** — czysta polszczyzna (bez anglicyzmów i AI-slopu), bez humanizera.

## Krok 3 — propozycje do kanonu (w pamięci, nie zapis)

Z gotowej sceny wyodrębnij **propozycje** dopisów RUNTIME dla bramki `continuity-check`: nowe fakty, nowe nazwy (do glosariusza), zmiany stanu postaci (lokalizacja/relacje), dotknięte zasiewy. **Nie zapisuj ich do kanonu ani do pliku** — to obiekt w pamięci, ładunek handoffu do bramki (Krok 5). Zapis do biblii robi dopiero kontrola ciągłości (jedyny etap z prawem zapisu przez `bible.py`).

## Krok 4 — zapis i walidacja

Zapisz prozę do **`.book-forge/sceny/<id>.md`** (tylko proza — żadnego pliku propozycji). Szczegóły i walidacja (długość, zgodność, brak humanizera na tym etapie): **`references/build-and-verify.md`**. Ten etap nie generuje HTML — proza jest tekstem; widok całości powstaje w `assemble-book`.

> **Tryb serii** (gdy istnieje `.book-forge/seria.md` — `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` → „Tryb serii"): ustaw `BOOK_DIR=tom-NN/`, `WORK=tom-NN/.book-forge/`, `BIBLE_DIR=tom-NN/.book-forge/biblia`, a prozę zapisuj do `${WORK}sceny/<id>.md` (ID scen mają wtedy prefiks tomu, np. `T2R1S1`). Wyciąg z `bible.load_all()` automatycznie zawiera dziedziczony, zamrożony kanon poprzednich tomów (warstwa `_dziedziczone`, RO). Pojedyncza książka: ścieżki płaskie, bez zmian.

## Krok 5 — handoff do continuity-check

Po zapisie sceny **od razu uruchom `/book-forge:continuity-check`** dla tego `<id>`, przekazując obiekt `propozycje` z roju (Krok 3) jako wejście bramki — kanon aktualizuje się natychmiast, bez ręcznego uruchamiania dwa etapy dalej. To **nie** łamie zasady „tylko continuity-check pisze do biblii”: handoff jedynie wyzwala bramkę, a sam zapis i audyt RO robi ona. Jeśli bramka wykryje konflikt RO, **zapyta autora** (kanon nie aktualizuje się „na ślepo”). W trybie serii handoff dziedziczy `BOOK_DIR`/`WORK`/`BIBLE_DIR` z tej sesji.

Na koniec pokaż autorowi: ścieżkę sceny, liczbę słów, wynik kontroli zgodności (POV/głos/nazwy/cel/zwrot) oraz werdykt bramki ciągłości. Surowo zgłaszaj, jeśli scena nie realizuje celu albo łamie POV.

## Quick reference

| Aspekt | Reguła |
| --- | --- |
| Wejście | Karta sceny z biblii + wyciąg + streszczenia 2–3 poprzednich scen |
| Silnik | Rój agentów (`references/workflow-swarm.md`) |
| Jednostka | Scena: cel → konflikt → zwrot; głos narratora + idiolekty |
| Tryb | Sekwencyjny; tylko czyta i PROPONUJE (bez zapisu do kanonu) |
| Humanizer | NIE tutaj — dopiero `polish-pl` (po kontroli ciągłości) |
| Wynik | `.book-forge/sceny/<id>.md` + handoff do `continuity-check` (zapis do biblii) |
| Walidacja | Długość, zgodność POV/głos/nazwy, cel i zwrot obecne |

## Najczęstsze błędy

- **Głos autora albo jeden ton dla wszystkich.** Naprawa: kotwicz w karcie głosu i idiolektach z biblii.
- **Streszczenie zamiast sceny.** Naprawa: realny cel, konflikt i zwrot ze zmianą wartości.
- **Przeładowanie informacjami (wykład).** Naprawa: świat dawkuj przez akcję i zmysły.
- **Zapis do kanonu z surowej sceny.** Naprawa: tylko propozycje; zapis robi `continuity-check`.
- **Humanizer za wcześnie.** Naprawa: nie tutaj; po kontroli ciągłości w `polish-pl`.
- **Amnezja między scenami.** Naprawa: streszczenia poprzednich scen w wyciągu; pisz sekwencyjnie.
