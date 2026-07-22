---
name: publishing-package
description: >
  Użyj, gdy maszynopis jest gotowy i autor potrzebuje pakietu do agenta/wydawcy — wyzwalacze: "pakiet wydawniczy", "list do agenta", "blurb", "synopsis", "logline", "query letter", "publishing package", "book-forge pakiet". Rój tworzy: logline, elevator pitch, opis z okładki (bez spoilerów), synopsis 1–2 strony (z zakończeniem), list do agenta i comp titles ujęte jako „dla czytelników X i Y” (nie „w stylu autora Z”). Wynik: pakiet.md + interaktywny HTML. Etap 12 (finalny) pipeline'u book-forge.
argument-hint: "(opcjonalnie ścieżka do ksiazka.md/biblii — skill i tak dopyta)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Pakiet wydawniczy (rój agentów)

Tworzy materiały, którymi sprzedaje się gotową książkę agentowi i wydawcy. To etap okołowydawniczy — nie zmienia kanonu, korzysta z gotowego maszynopisu i biblii.

Najpierw przeczytaj `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` (język) i `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` (skąd brać logline, protagonistę, stawkę, motyw).

## Zasada nadrzędna: sprzedaj, nie skłam

Dwie reguły poza naturalną polszczyzną:

- **Comp titles jako „dla czytelników X i Y”, nie „w stylu autora Z”.** Pozycjonuj przez odbiorcę i półkę, nie przez naśladowanie żywego autora — to ochrona przed zarzutem imitacji.
- **Bez zmyślonych referencji.** Żadnego „pisałem dla znanych autorów”, zmyślonych nagród, sprzedaży czy cytatów. Bio autora zostaw jako pole do uzupełnienia, nie wymyślaj.

Dyscyplina spoilerów: **opis z okładki bez zakończenia** (ma kusić), **synopsis z zakończeniem** (agent musi znać całość).

## Krok 1 — wejście

1. Wczytaj `ksiazka.md` (gotowy maszynopis — policz słowa) i kanon przez `b = bible.load_all()` (przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`): meta (tytuł, gatunek, logline, target, comps), protagonista, stawka, motyw. Jeśli istnieje raport z etapu 1 (`market-report-*.html`), weź z niego comps i pozycjonowanie. Brak maszynopisu/biblii — przerwij i wskaż wcześniejsze etapy.
2. Dopytaj `AskUserQuestion`: rynek docelowy (agent PL / zagraniczny), ewentualne bio autora (lub zostaw puste), preferowane comp titles.

**Rola ekspercka:** agent literacki / redaktor ds. zakupów piszący materiały sprzedażowe.

## Krok 2 — rój agentów (Workflow)

Uruchom rój według **`references/workflow-swarm.md`**. Fazy:

1. **Komponenty** (równolegle): logline (1 zdanie), elevator pitch (2–3 zdania), opis z okładki (~150 słów, bez spoilerów), synopsis (1–2 strony, z zakończeniem), list do agenta, comp titles („dla czytelników X i Y”).
   - **Tryb serii** (gdy istnieje `.book-forge/seria.md`, `bible.read_series()`): dodaj **pitch serii** — 2–3 zdania o `obietnica_serii` i miejscu tego tomu w łuku nadrzędnym (`tomy`, `tom_aktywny`, `rola_w_serii`). Agent ma jasno zaznaczyć, że tom 1 broni się samodzielnie, a seria jest opcją (tak czyta to agent/wydawca). Pojedyncza książka: pomiń.
   - **Rynek docelowy.** Dla rynku PL — konwencja polskiego listu do agenta/wydawcy (luźniejszy, krótszy). Dla rynku **zagranicznego** — wygeneruj RÓWNOLEGŁĄ sekcję EN (logline, blurb, synopsis, query letter w konwencji anglojęzycznej: hook → mini-synopsis → bio → comp titles, ~300 słów, metadane: word count, genre) z wyraźnym oznaczeniem „draft do weryfikacji przez native speakera". Zapisz ją obok (zakładka „PL / EN" w HTML lub `pakiet-en.md`); nie podawaj polskiej konwencji jako gotowej do wysyłki za granicę.
2. **Ocena** — agent literacki sprawdza: czy się sprzedaje, czy comps są ujęte przez odbiorcę (nie imitację), czy opis nie zdradza zakończenia, czy synopsis jest kompletny, czy nie ma zmyślonych referencji, a w serii — czy pitch serii nie psuje samodzielności tomu 1. Poprawki.
3. **Redakcja PL** — naturalna polszczyzna.

## Krok 3 — unslop (główna sesja)

Na prozie pakietu (pitch, opis z okładki, synopsis, list) uruchom `/unslop:unslop`. Nazw własnych z glosariusza i tytułów porównawczych nie zniekształcaj.

## Krok 4 — zapis i walidacja

`pakiet.md` (wszystkie komponenty) + interaktywny `pakiet-<slug>.html` (ze szablonu `${CLAUDE_PLUGIN_ROOT}/skills/publishing-package/assets/package-template.html`): pitch, synopsis, list do agenta, comps, metadane. Szczegóły i walidacja: **`references/build-and-verify.md`** (`node --check` + podgląd).

## Krok 5 — podsumowanie

Pokaż autorowi: logline, długość książki, comp titles (ujęte przez odbiorcę), oraz przypomnienie, by uzupełnił bio i dane kontaktowe w liście (pola zostawione celowo puste).

## Quick reference

| Aspekt | Reguła |
| --- | --- |
| Wejście | `ksiazka.md` + kanon `.book-forge/biblia/` (przez bible.py) (+ market-report jeśli jest) |
| Silnik | Rój agentów (`references/workflow-swarm.md`) |
| Komponenty | logline, pitch, opis (bez spoilerów), synopsis (z końcem), list, comps |
| Comps | „dla czytelników X i Y”, nie „w stylu autora Z” |
| Uczciwość | Bez zmyślonych nagród/sprzedaży/referencji; bio = pole do uzupełnienia |
| Język | Naturalna polszczyzna + `/unslop:unslop` |
| Wynik | `pakiet.md` + `pakiet-<slug>.html` |

## Najczęstsze błędy

- **Comps przez imitację autora.** Naprawa: „dla czytelników X i Y”, nie „w stylu Z”.
- **Spoiler w opisie z okładki.** Naprawa: opis kusi, synopsis zdradza — rozdziel.
- **Zmyślone referencje/nagrody.** Naprawa: tylko fakty; bio jako pole do uzupełnienia.
- **Synopsis bez zakończenia.** Naprawa: agent musi znać całość — synopsis kompletny.
- **Anglicyzmy w materiałach.** Naprawa: słownik z `polish-style.md` + unslop.
