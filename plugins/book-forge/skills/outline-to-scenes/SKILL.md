---
name: outline-to-scenes
description: >
  Użyj, gdy autor ma konspekt i biblię i chce przejść od rozdziałów do siatki scen gotowej do pisania — wyzwalacze: "siatka scen", "podziel na sceny", "rozpisz sceny", "outline to scenes", "book-forge sceny". Rój agentów przepisuje konspekt na sceny (cel → konflikt → zwrot, zmiana wartości), osadza je na beatach łuku protagonisty, buduje oś czasu i rejestr zasiewów, i zapisuje to do biblii. Wynik: siatka scen w biblii + scalenie do `konspekt-<slug>.html` jako zakładka „Sceny" (osobny plik scen nie powstaje). Etap 5 pipeline'u book-forge — most między konspektem a pisaniem prozy.
argument-hint: "(opcjonalnie ścieżki do konspektu/biblii — skill i tak dopyta)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Konspekt → siatka scen (rój agentów)

Przekłada konspekt rozdział po rozdziale na **siatkę scen** gotową do pisania. To brakujące ogniwo między planem a prozą: rozdział mierzony „obietnicą i punktami” rodzi prozę ekspozycyjną, w której postacie odhaczają punkty zamiast pragnąć i działać. Scena z celem, przeszkodą i zwrotem to silnik napięcia i przyczynowości („a więc / ale” zamiast „i potem”).

To **etap planowania**: buduje planowaną siatkę scen w biblii (jak `kanon_fabularny`), więc wolno mu pisać do kanonu (w odróżnieniu od etapów prozy, które tylko czytają i proponują). Najpierw przeczytaj `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` (pola RO/RUNTIME, kanon fabularny) i `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` (język).

## Zasada nadrzędna

Każda scena musi mieć **cel postaci → konflikt/przeszkodę → zwrot (zmiana wartości +/–)** i zasługiwać na swoje miejsce. Oś całości to **łuk protagonisty**, osadzony na beatach (incydent inicjujący, próg I aktu, środek, czarna chwila, kulminacja, rozwiązanie). Spójność z biblią (POV, postacie, świat, nazwy) i naturalna polszczyzna obowiązują jak w pozostałych etapach.

## Krok 1 — wejście

1. Wczytaj `.book-forge/konspekt.md` (rozdziały) oraz kanon-wiki z `.book-forge/biblia/` przez `bible.load_all()` (wymagany — bez niego brak kontekstu postaci/świata/POV). Jeśli konspektu brak lub jest kilka kandydatów, zapytaj o ścieżki (`AskUserQuestion`).
2. Z biblii weź: POV/czas, postacie z łukami, stawkę, motyw, zasady świata, glosariusz. Z konspektu — listę rozdziałów (obietnica, kluczowe punkty, emocja, a jeśli są — `subwersja` i `kotwica`). Pola `subwersja`/`kotwica` przekaż w `args.chapters`, by rój zaszył je na scenie otwierającej rozdziału (honoruje je `write-scene`).
3. Dopytaj `AskUserQuestion`: ile scen średnio na rozdział (domyślnie rój dobiera 1–3 wg potrzeby) i czy autor chce trzymać liczbę scen w ryzach (np. limit całkowity). Jeśli `meta.budzet_slow` jest puste/0, zapytaj też o **docelowy budżet słów całej książki** (zaproponuj wartość z docelowej długości w konspekcie albo normę subgatunku) — zapiszesz go w Kroku 4 i od tej pory `write-scene` liczy z niego sugerowaną długość scen.

**Rola ekspercka:** architekt struktury powieści, który myśli scenami i przyczynowością, nie streszczeniem.

## Krok 2 — rój agentów (Workflow)

Uruchom rój według **`references/workflow-swarm.md`**. Fazy:

1. **Mapa łuku** — z łuku protagonisty, stawki i beatów powstaje krzywa wartości całości (który fragment trafia w który beat, jak emocja rośnie i opada).
2. **Siatka scen** — każdy rozdział rozpisany na sceny: id, POV, miejsce i czas, cel, konflikt, zwrot, wartość (+/–), pozycja w łuku, co zasiewa i co spłaca.
3. **Oś czasu i zasiewy** — z wszystkich scen powstaje rejestr zasiewów (każdy zasiew ma wypłatę) oraz oś czasu (dzień fabularny, kolejność chronologiczna a narracyjna).
4. **Krytyka** — panel sprawdza: czy każda scena ma cel i zwrot, czy wartość naprawdę się zmienia, czy działa przyczynowość, czy nie ma wypełniaczy, czy łuk jest ciągły → rewizja (łączenie/cięcie scen).
5. **Redakcja PL** — opisy scen na naturalną polszczyznę.

Sceny mogą oznaczać **luki badawcze** (realia wymagające weryfikacji) — trafiają na listę dla etapu `world-research` (research na żądanie, nie na zapas).

## Krok 3 — humanizer (główna sesja)

Na opisach scen uruchom `/humanizer:humanizer` i nanieś poprawki (nazwy własne z glosariusza chronione).

## Krok 4 — zapis do biblii + artefakty

1. **Zapis do biblii** (przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`): wpisz planowaną siatkę scen przez `bible.write_scene_grid(rozdzialy, beaty, sceny, force=...)` (status `"planowana"`), zainicjuj `setup_payoff` (zasiewy planowane) i `os_czasu` (planowana kolejność) pętlą `bible.append_record(...)` (dedup chroni przed duplikatem przy ponownym uruchomieniu). To planowanie, więc te pola powstają tu; późniejsze etapy prozy ich nie nadpisują. Po udanym `write_scene_grid` **domknij łańcuch budżetu słów**: `bible.update_meta("liczba_scen", len(sceny))` oraz — jeśli autor podał budżet w Kroku 1 — `bible.update_meta("budzet_slow", <wartość>)` (to jedyny producent tych pól; bez nich budżet w `write-scene` nigdy się nie włącza). Na końcu `bible.render_index()`.
2. **Dowiązanie otwarcia:** jeśli w folderze roboczym istnieje `.book-forge/poczatek.md` (proza otwarcia z etapu `opening`), ustaw na karcie sceny otwierającej (domyślnie pierwsza, `sceny[0]`) twardy wskaźnik przez `bible.set_scene_field(<id_sceny_1>, "proza_zrodlo", ".book-forge/poczatek.md")`. Dzięki temu `write-scene` rozwinie gotowe otwarcie zamiast pisać scenę 1 od zera (zob. `proza_zrodlo` w `shared/biblia-spec.md`). Jeśli openingu jeszcze nie ma, pomiń — dowiązanie powstanie, gdy uruchomisz `outline-to-scenes` po `opening` (zachowaj właściwą kolejność etapów 4→5).
3. **Scalenie do konspektu (bez osobnego pliku scen):** nie buduj ani `sceny-<slug>.html`, ani `sceny.md`. Zamiast tego wczytaj istniejący `konspekt-<slug>.html`, wyłuskaj z niego obiekt `DATA`, dodaj pole `DATA.scenes` (lista scen: `id, rozdzial, pov, miejsce, czas, cel, konflikt, zwrot, value, luk`) i ponownie wstrzyknij `DATA` w szablon `${CLAUDE_PLUGIN_ROOT}/skills/outline/assets/outline-template.html`, nadpisując `konspekt-<slug>.html`. Szablon pokaże wtedy zakładkę „Sceny" (03) z siatką scena po scenie. Łuk, beaty, zasiewy i research zostają **tylko w biblii** — nie trafiają do HTML. Jeśli `konspekt-<slug>.html` nie istnieje, pomiń scalenie HTML (kanon i tak jest w biblii) i powiedz to autorowi. Szczegóły i walidacja: **`references/build-and-verify.md`** (`node --check` + podgląd w agent-browser).

Jeśli siatka scen już istnieje (`bible.load_all()['kanon_fabularny'].sceny` niepuste, lub `write_scene_grid` zwróci `{"status":"GUARD"}`), zapytaj o nadpisanie (`AskUserQuestion`) i ponów z `force=True`.

**Tryb serii** (gdy istnieje `.book-forge/seria.md` — pełny model w `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md`): przed rojem odczytaj `bible.read_series()` i przekaż do `args` aktywny tom (`tom`) oraz `seria` (`obietnica_serii` + `zasiewy_miedzytomowe`). Rój nada ID scen z prefiksem `T<tom>` (np. `T2R1S1`) i może oznaczyć sceny realizujące zasiewy międzytomowe. Ustaw `BOOK_DIR=tom-NN/`, `WORK=tom-NN/.book-forge/`, `BIBLE_DIR=tom-NN/.book-forge/biblia` przed zapisem. Pojedyncza książka: pomiń — ID bez prefiksu, ścieżki płaskie.

## Krok 5 — podsumowanie

Pokaż autorowi: liczbę scen, mapę beatów, ostrzeżenia (zasiew bez wypłaty, scena bez zwrotu, płaski odcinek łuku) oraz listę luk badawczych do etapu `world-research`. Jeśli dowiązano otwarcie, odnotuj, na której scenie ustawiono `proza_zrodlo` (lub ostrzeż, że brak `.book-forge/poczatek.md` — wtedy scenę 1 napisze `write-scene` od zera).

## Quick reference

| Aspekt | Reguła |
| --- | --- |
| Wejście | `.book-forge/konspekt.md` + kanon-wiki `.book-forge/biblia/` przez `bible.load_all()` (wymagany) |
| Silnik | Rój agentów (`references/workflow-swarm.md`) |
| Jednostka | Scena: cel → konflikt → zwrot, wartość +/– |
| Oś | Łuk protagonisty na beatach |
| Zapis do kanonu | Tak (etap planowania): siatka scen, oś czasu, zasiewy i wypłaty |
| Wynik | siatka scen w biblii + zakładka „Sceny" scalona do `konspekt-<slug>.html`; luki badawcze dla `world-research` |
| Język | Naturalna polszczyzna + `/humanizer:humanizer` |
| Walidacja | `node --check` na JS + podgląd w agent-browser |

## Najczęstsze błędy

- **Streszczenie zamiast sceny.** Naprawa: każda scena ma cel, konflikt i zwrot, nie zdanie fabuły.
- **„I potem” zamiast „a więc/ale”.** Naprawa: wymuś przyczynowość między scenami.
- **Zasiew bez wypłaty.** Naprawa: rejestr zasiewów sprawdza domknięcia.
- **Płaski łuk.** Naprawa: krzywa wartości musi się zmieniać; sceny bez zmiany wartości to kandydaci do cięcia.
- **Złamanie kanonu** (POV, nazwy). Naprawa: kotwicz w biblii; nazwy z glosariusza.
