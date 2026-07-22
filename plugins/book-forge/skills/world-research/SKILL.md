---
name: world-research
description: >
  Użyj, gdy siatka scen albo zasady świata zgłaszają luki wymagające weryfikacji realiów (nauka, technologia, historia, geografia, prawo, konwencje gatunku) — wyzwalacze: "research świata", "zweryfikuj realia", "uwiarygodnij świat", "world research", "book-forge research". Rój agentów odpowiada na pytania badawcze przez agent-browser/WebSearch, adwersaryjnie weryfikuje ustalenia i zapisuje je do biblii (doprecyzowane zasady, fakty, rejestr źródeł z URL i datą). Research zasila KANON, nigdy nie wchodzi wprost do prozy. Etap 6 pipeline'u book-forge, na żądanie z luk scen.
argument-hint: "(opcjonalnie ścieżka do biblii/listy pytań — skill i tak dopyta)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Research świata → kanon (rój agentów)

Uwiarygadnia świat powieści: odpowiada na konkretne pytania badawcze wynikające z siatki scen i zasad świata, a wynik zapisuje **do biblii**, nie do prozy. To chroni przed dwoma grzechami: halucynowanym „faktem” wpisanym w tekst i pastiszem cudzych zdań przeniesionych żywcem do prozy.

Najpierw przeczytaj `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` (sekcje `swiat`, `fakty`, `zrodla`, pola RO/RUNTIME) i `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` (język).

## Zasada nadrzędna: research na żądanie, do kanonu, z cytowaniem

Trzy reguły: (1) badamy tylko to, czego **realnie żąda fabuła** (luki z siatki scen), nie wszystko na zapas; (2) każdy ustalony fakt ma **cytowanie** (źródło, URL, data) w rejestrze `zrodla` — audytowalność; (3) wynik trafia do biblii (`swiat`, `fakty`, `zrodla`), a do prozy nigdy bezpośrednio.

## Krok 1 — wejście i zebranie pytań

1. Wczytaj kanon-wiki z `.book-forge/biblia/` przez `bible.load_all()`. Zbierz luki badawcze z: `kanon_fabularny.sceny[].research`, zasad świata bez ugruntowania (`swiat.zasady` bez realnego kosztu/ograniczenia) oraz ewentualnej listy `research_needs` przekazanej z etapu `outline-to-scenes`. Jeśli kanonu brak — przerwij i poproś o `book-bible`.
2. Jeśli pytań brak (np. czysta fantastyka bez potrzeby weryfikacji), powiedz to wprost i zaproponuj zakończenie — nie wymyślaj pytań na siłę.
3. Dopytaj `AskUserQuestion`: czy autor chce dorzucić własne pytania badawcze i jak rygorystyczna ma być weryfikacja (np. wymagane 2 niezależne źródła dla faktu twardego).

**Rola ekspercka:** researcher i konsultant merytoryczny (science/fact-checker), który odróżnia źródło wiarygodne od przypadkowego i zawsze podaje cytat.

## Krok 2 — rój agentów (Workflow)

Uruchom rój według **`references/workflow-swarm.md`**. Fazy:

1. **Plan pytań** — luki zamienione na precyzyjne, odpowiadalne pytania; każde oznaczone jako „fakt do weryfikacji” albo „zasada do ugruntowania”.
2. **Research** — na pytanie agent szuka przez **WebSearch/WebFetch** (a gdy trzeba wejść na konkretną stronę — **agent-browser** z `Bash`), zwraca odpowiedź ze źródłami (zrodlo, URL, data) i poziomem pewności. Nie zmyśla; brak wiarygodnego źródła = „nie ustalono”.
3. **Weryfikacja adwersaryjna** — sceptyk sprawdza każde ustalenie: wiarygodność źródła, potwierdzenie w drugim źródle, sprzeczności. Oznacza keep / flaga. To bramka przeciw halucynacjom.
4. **Integracja** — z potwierdzonych ustaleń powstają: doprecyzowane `swiat.zasady` (z realnym kosztem/ograniczeniem), wpisy `fakty` (typ świat, pewność kanon, z `zrodlo_ref`) i rejestr `zrodla`.
5. **Redakcja PL** — opisy na naturalną polszczyznę.

Nie odpalaj agent-browsera w dziesiątkach kopii naraz (bywa zawodne) — WebSearch jest podstawą, agent-browser celowo.

## Krok 3 — unslop (główna sesja)

Na opisowych partiach ustaleń uruchom `/unslop:unslop`. Nazw własnych i cytowań nie ruszaj.

## Krok 4 — zapis do biblii + artefakty

1. **Zapis do biblii** (przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`): dopisz `fakty` (nowe, z `zrodlo_ref`) i `zrodla` (rejestr cytowań) pętlą `bible.append_record('fakty', ...)` / `bible.append_record('zrodla', ...)` (auto-id `F`/`Z`, dedup). Doprecyzowanie istniejących `swiat.zasady` (pole RO) wykonaj tylko po potwierdzeniu autora (`AskUserQuestion`) — `bible.write_section('swiat', {...})` — to mogłoby zmienić ustalony świat. Na końcu `bible.render_index()`.
2. **Domknięcie pętli zwrotnej:** jeśli research **obalił lub istotnie zmienił** realia, na których opierała się któraś scena (z `kanon_fabularny.sceny[].research`), oznacz te sceny do rewizji — ustaw na karcie `bible.set_scene_field(<id>, "status", "do-rewizji")` i wypisz je autorowi. Inaczej scena zostałaby napisana na realiach, które właśnie upadły. Sceny niedotknięte zostaw bez zmian.
3. **Bez osobnych artefaktów.** Research nie tworzy plików `research.md` ani `research-<slug>.html` — całość (fakty, źródła, ewentualne doprecyzowania zasad) żyje w biblii i to ona jest źródłem prawdy dla kolejnych etapów. Po zapisie zweryfikuj kanon: `bible.py validate`.

## Krok 5 — podsumowanie

Pokaż autorowi: ile pytań rozstrzygnięto, ile faktów dopisano (z liczbą źródeł), które ustalenia **oflagowano jako niepewne** lub „nie ustalono”, oraz które zasady świata czekają na jego decyzję o doprecyzowaniu. Surowo zgłaszaj braki — lepiej „nie ustalono” niż zmyślony fakt.

## Quick reference

| Aspekt | Reguła |
| --- | --- |
| Wejście | kanon-wiki `.book-forge/biblia/` przez `bible.load_all()` (luki z `sceny[].research`, zasady bez ugruntowania) |
| Silnik | Rój agentów (`references/workflow-swarm.md`) |
| Źródła | WebSearch/WebFetch (podstawa) + agent-browser (celowo) |
| Weryfikacja | Adwersaryjny sceptyk; brak źródła = „nie ustalono” |
| Zapis | `fakty` + `zrodla` (cytowania); `swiat.zasady` tylko za zgodą autora |
| Granica | Do kanonu, NIGDY wprost do prozy |
| Wynik | aktualizacja biblii (fakty, źródła, ew. zasady) — bez osobnych plików |
| Walidacja | `bible.py validate` (kanon) |

## Najczęstsze błędy

- **Research na zapas.** Naprawa: badaj tylko luki, których żąda fabuła.
- **Fakt bez źródła.** Naprawa: każdy fakt z cytowaniem; brak źródła = „nie ustalono”.
- **Halucynacja udająca fakt.** Naprawa: adwersaryjna weryfikacja, wymóg drugiego źródła dla twardych faktów.
- **Cudze zdania w prozie.** Naprawa: research idzie do kanonu; prozę pisze się później z faktów, nie z cytatów.
- **Nadpisanie zasady świata.** Naprawa: doprecyzowanie RO tylko za zgodą autora.
