---
name: continuity-check
description: >
  Użyj po napisaniu/rewizji sceny, by sprawdzić jej spójność z biblią i bezpiecznie dopisać nowe ustalenia do kanonu — wyzwalacze: "kontrola ciągłości", "sprawdź spójność", "continuity check", "bramka kanonu", "book-forge ciągłość". Rój audytorów porównuje scenę z biblią (nazwy i odmiana, opisy postaci, chronologia, POV/czas, zasady świata, zasiewy), a synteza klasyfikuje propozycje: CONFLICT (łamie pola RO — blokuje, nie nadpisuje) lub WRITE (nowy RUNTIME — zapis do kanonu). To JEDYNY etap PROZY z prawem zapisu do biblii (etapy planowania mają własne, wąskie uprawnienia). Etap 9 pipeline'u book-forge.
argument-hint: "(opcjonalnie id sceny, np. R3S2 — skill i tak dopyta)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Kontrola ciągłości — bramka kanonu (rój agentów)

Pilnuje, żeby książka „trzymała się kupy”, i jako **jedyny etap** kontrolowanie dopisuje ustalenia do biblii. Porównuje świeżą scenę i jej propozycje z całym kanonem, blokuje to, co łamie ustalenia, a bezpiecznie zapisuje to, co nowe.

Najpierw przeczytaj `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` (pola RO vs RUNTIME, uprawnienia zapisu, log ciągłości) i `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` (język).

## Zasada nadrzędna: RO blokuj, RUNTIME zapisuj

To zwornik spójności. Reguły żelazne:

- **Pola RO** (POV, czas, opis fizyczny postaci, łuki, zasady świata, motyw, kanoniczne nazwy i ich odmiana): jeśli scena im przeczy → **CONFLICT**. Bramka **zgłasza i blokuje, NIGDY nie nadpisuje**. Decyzję podejmuje autor (poprawić scenę albo świadomie zmienić kanon RO).
- **Pola RUNTIME** (lokalizacja/stan/relacje/postęp łuku, oś czasu, status zasiewów, nowe fakty, nowe nazwy): tu i tylko tu następuje **write-back** do kanonu-wiki przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py` (`update_runtime`/`append_record`/`append_log`).
- **Nowa encja RO ≠ zmiana pola RO.** Subtelność glosariusza: utworzenie NOWEJ nazwy własnej (nowa encja RO w glosariuszu) jest dozwolone automatycznie, bo niczego nie nadpisuje (`write_entity` robi merge-not-clobber). Natomiast **zmiana istniejącego** pola RO (inna odmiana, inny opis postaci) zawsze → **CONFLICT** i wymaga zgody autora. Nową nazwę zapisuj z pewnością „roboczy" (jak inne nowe fakty), żeby kanoniczna odmiana mogła zostać potwierdzona, a nie wskakiwała jako pewnik.
- To **jedyny etap prozy** zapisujący do kanonu. Etapy pisania (opening, write-scene, revise-scene, polish-pl) tylko proponowały; tu propozycje są weryfikowane i dopiero teraz stają się kanonem. Etapy planowania i przeglądu (book-bible, outline-to-scenes, world-research, assemble-book) mają własne, wąsko zakreślone uprawnienia zapisu — żaden z nich nie kanonizuje ustaleń z surowej prozy.
- **Zapis wykonuje główna sesja deterministycznie (skrypt), nie agent** — agent tworzy plan zapisu, kod go wykonuje (audytowalność, brak „kanonizacji halucynacji”).

## Krok 1 — wejście

1. Wczytaj kanon `bible.load_all()` i prozę `.book-forge/sceny/<id>.md`. **Propozycje bierz z handoffu** — gdy bramkę uruchamia `write-scene`/`revise-scene`, dostają one obiekt `propozycje` w wejściu (Krok 5 tamtych etapów). Przy uruchomieniu **samodzielnym** (np. audyt zbiorczy co 10–15 tys. słów) propozycji nie ma — audytorzy i tak wyłuskują ustalenia wprost z prozy. Domyślnie ostatnia napisana/rewidowana scena bez wpisu w `log_ciaglosci`; pozwól wskazać id albo zakres. Bez biblii — przerwij.
2. Zbuduj pełny kontekst kanonu istotny dla tej sceny (postacie obecne, nazwy, otwarte zasiewy, oś czasu do tej pory).

**Rola ekspercka:** strażnik kanonu / redaktor ds. spójności — jego jedyne zmartwienie to spójność.

## Krok 2 — rój agentów (Workflow)

Uruchom rój według **`references/workflow-swarm.md`**. Fazy:

1. **Audyt** — panel audytorów (równolegle), każdy jeden wymiar: opisy i stan postaci, chronologia/oś czasu, nazwy i odmiana z glosariusza, zasady świata, POV/czas, zasiewy (domknięcia). Każdy zwraca sprzeczności i ustalenia.
2. **Klasyfikacja** — synteza zbiera audyty i każdą propozycję/ustalenie klasyfikuje jako **CONFLICT** (łamie RO), **WRITE** (nowy RUNTIME) lub **OK** (zgodne istniejące). Tworzy **plan zapisu** (tylko RUNTIME), wpis do `log_ciaglosci` (PASS/CONFLICT/FIX) oraz **streszczenie sceny** (3-5 zdań) do agregatu `streszczenia` — z niego kolejne sceny biorą wyciąg anty-amnezji, zamiast streszczać prozę od nowa.

## Krok 3 — rozstrzygnięcie konfliktów (autor decyduje)

Jeśli są CONFLICT-y, pokaż je autorowi (`AskUserQuestion`): co mówi scena vs co mówi biblia. Opcje zwykle: (a) poprawić scenę (wróć do `revise-scene`), (b) świadomie zmienić pole RO w biblii (za wyraźną zgodą), (c) odłożyć z adnotacją. **Nie zapisuj RO bez zgody.**

## Krok 4 — write-back (deterministyczny) i log

Wykonaj plan zapisu skryptem (główna sesja) przez `bible.py`: `append_record('fakty'…)`, nowe nazwy → `write_entity('glosariusz'…)` (z odmianą), `update_runtime('postac', …, '_stan.…')`, `append_record('os_czasu'/'setup_payoff'…)`; oznacz scenę `set_scene_status(sid,'zweryfikowana')` i dopisz streszczenie `append_record('streszczenia', …)` (z hashem prozy). `append_log(...)` **jako ostatni** (znacznik domknięcia), potem `render_index()`. **Pól RO skrypt nie dotyka** — `update_runtime` egzekwuje to twardo (RO→CONFLICT), a wbudowany snapshot RO przerywa zapis przy jakiejkolwiek zmianie RO. Szczegóły: **`references/build-and-verify.md`**.

## Krok 5 — podsumowanie (w czacie, bez plików)

Ten etap **nie tworzy żadnych plików** — jedynym trwałym wynikiem jest aktualizacja biblii (kanon RUNTIME + `log_ciaglosci`). W czacie pokaż autorowi werdykt (PASS/CONFLICT), konflikty do rozstrzygnięcia, liczbę dopisanych faktów/nazw i zasiewy bez wypłaty.

## Quick reference

| Aspekt | Reguła |
| --- | --- |
| Wejście | kanon `.book-forge/biblia/` (przez `bible.load_all()`) + `.book-forge/sceny/<id>.md` + propozycje z handoffu (opcjonalne) |
| Silnik | Rój audytorów + synteza (`references/workflow-swarm.md`) |
| RO | CONFLICT — blokuj, nie nadpisuj; decyzja autora |
| RUNTIME | Write-back do kanonu (jedyny etap zapisujący) |
| Zapis | Deterministyczny skrypt, nie agent |
| Log | Wpis w `log_ciaglosci` (PASS/CONFLICT/FIX) |
| Wynik | aktualizacja biblii (kanon + `log_ciaglosci`) — bez osobnych plików |

## Najczęstsze błędy

- **Kanonizacja błędu z surowej sceny.** Naprawa: CONFLICT na RO blokuje; tylko RUNTIME jest zapisywany.
- **Nadpisanie ustalenia RO.** Naprawa: nigdy automatycznie; tylko autor.
- **Zapis przez agenta.** Naprawa: agent tworzy plan, skrypt wykonuje (audytowalność).
- **Zasiew bez wypłaty przeoczony.** Naprawa: audyt zasiewów pilnuje domknięć.
- **Dryf odmiany nazw.** Naprawa: audyt nazw vs glosariusz; nowe nazwy z pełną odmianą.
