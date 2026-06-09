---
name: assemble-book
description: >
  Użyj, gdy sceny są napisane, zweryfikowane i wygładzone, by złożyć je w całą książkę i sprawdzić całość — wyzwalacze: "złóż książkę", "scal sceny", "cała książka", "assemble book", "przegląd całości", "book-forge złożenie". Rój składa sceny w rozdziały i przegląda CAŁOŚĆ: domknięcie łuku fabularnego i łuku postaci, wypłata wszystkich zasiewów, tempo, motyw, oś czasu. Aktualizuje biblię (finalny status zasiewów i łuków) i może zamrozić kanon working→published. Wynik: ksiazka.md + interaktywny przegląd HTML. Etap 11 pipeline'u book-forge.
argument-hint: "(opcjonalnie zakres rozdziałów — domyślnie cała książka)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Złożenie książki + przeglądy całości (rój agentów)

Bierze gotowe sceny i składa je w rozdziały i pełny maszynopis, a potem patrzy na **całość**: czy historia się domyka, czy żaden zasiew nie wisi bez wypłaty, czy tempo działa. To etap nad pojedynczą sceną — łapie dryf, którego nie widać scena po scenie.

Najpierw przeczytaj `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` (kanon fabularny, zasiew/wypłata, oś czasu, working vs published canon) i `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` (język podsumowań).

## Zasada nadrzędna

Ten etap **nie przepisuje prozy** (sceny są już po `polish-pl`). Składa i **audytuje całość**, raportuje luki i — gdy czysto — zamraża kanon. Podział na rozdziały następuje PO napisaniu scen, według `kanon_fabularny.sceny[].rozdzial`.

## Krok 1 — wejście

1. Zbierz sceny z katalogu `.book-forge/sceny/` (pliki `*.md` po `polish-pl`). Z kanonu-wiki przez `bible.load_all()` weź: `kanon_fabularny` (sceny + beaty + rozdziały), `setup_payoff`, `os_czasu`, łuki postaci, motyw, kartę głosu. Z konspektu — tytuły rozdziałów.
2. Sprawdź kompletność: które sceny są napisane i `zweryfikowana`/wygładzone, a których brak. Brakujące zgłoś — nie składaj książki z dziurami po cichu.
3. Dopytaj `AskUserQuestion`: czy składamy całość czy zakres, oraz czy po czystym przeglądzie **zamrozić kanon** (`working` → `published`).

**Rola ekspercka:** redaktor prowadzący patrzący na książkę jako całość.

## Krok 2 — rój agentów (Workflow)

Uruchom rój według **`references/workflow-swarm.md`**. Przeglądy nad całością (równolegle), każdy jeden wymiar:

1. **Łuk fabularny** — czy beaty są domknięte (incydent → kulminacja → rozwiązanie), brak urwanych wątków.
2. **Łuk postaci** — czy przemiana protagonisty się realizuje (rana → kłamstwo → zmiana); czy poboczni mają domknięcia.
3. **Zasiewy** — czy każdy `setup_payoff` ma wypłatę; lista otwartych (strzelby Czechowa, które nie wypaliły).
4. **Tempo** — rozkład wartości +/– i długości scen; gdzie zwalnia/przyspiesza za bardzo.
5. **Motyw** — czy temat przewija się spójnie, bez dydaktyzmu.
6. **Oś czasu** — spójność chronologii całości (brak cofnięć i dziur).

Synteza zbiera audyty w **werdykt gotowości** + listę problemów (otwarte zasiewy, luki łuku, zapadnięcia tempa).

## Krok 3 — złożenie maszynopisu

Złóż sceny w kolejności (rozdział, potem scena) w **`ksiazka.md`**: nagłówki rozdziałów (tytuły z konspektu), sceny pod nimi, liczby słów. To deterministyczne (skrypt), nie agent. Szczegóły: **`references/build-and-verify.md`**.

## Krok 4 — aktualizacja biblii i zamrożenie kanonu

Zapisz do biblii finalne statusy (przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`): `setup_payoff` (domknięte/otwarte) przez `bible.append_record('setup_payoff', {'id':..,'status':..,'scena_splaty':..})` — agregat RUNTIME aktualizowany po `id`. **Promocja `working` → `published`** przez `bible.freeze_canon(True)` tylko gdy przegląd czysty (brak otwartych krytycznych zasiewów i luk łuku) **i** autor potwierdzi (`AskUserQuestion`) — po zamrożeniu fakty są nienaruszalne dla kolejnego tomu. Na końcu `bible.render_index()`.

**Tryb serii** (gdy istnieje `.book-forge/seria.md` — pełny model w `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md`): w audycie gotowości **rozróżnij dwa rodzaje zasiewów**. *Zasiew tomu* (`setup_payoff` w bibli) MUSI domknąć się w tym tomie — otwarty = problem (jak dziś). *Zasiew serii* (`zasiewy_miedzytomowe` z `.book-forge/seria.md`, `bible.read_series()`) wolno zostawić otwarty, jeśli jego `tom_splaty > tom_aktywny` — raportuj go jako „celowo otwarty wątek serii", **nie** jako lukę gotowości (inaczej tom 1 trylogii dostałby fałszywy błąd). Po zamrożeniu tomu N, jeśli powstaje kolejny tom, przygotuj dziedziczenie: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bible.py import-published tom-NN/.book-forge/biblia` wniesie ten kanon do `tom-(N+1)/.book-forge/biblia/_dziedziczone/` jako RO.

## Krok 5 — artefakty i podsumowanie

`ksiazka.md` + interaktywny `ksiazka-<slug>.html` (ze szablonu `${CLAUDE_PLUGIN_ROOT}/skills/assemble-book/assets/book-template.html`): rozdziały i sceny, krzywa wartości całości, macierz zasiewów, przeglądy. Pokaż autorowi: łączną liczbę słów, werdykt gotowości, otwarte zasiewy i luki łuku do domknięcia, oraz czy kanon zamrożono.

## Quick reference

| Aspekt | Reguła |
| --- | --- |
| Wejście | `.book-forge/sceny/*.md` (po `polish-pl`) + biblia (kanon, zasiewy/wypłaty, oś, łuki) |
| Silnik | Rój przeglądów całości (`references/workflow-swarm.md`) |
| Proza | NIE przepisywana — tylko składana i audytowana |
| Audyty | Łuk fabularny i postaci, zasiewy, tempo, motyw, oś czasu |
| Biblia | Finalne statusy; promocja `working`→`published` (czysto + zgoda) |
| Wynik | `ksiazka.md` + `ksiazka-<slug>.html` |
| Walidacja | Kompletność scen, każdy zasiew z wypłatą, `bible.py validate`, JS HTML |

## Najczęstsze błędy

- **Składanie z dziurami.** Naprawa: zgłoś brakujące/niewygładzone sceny, nie scalaj po cichu.
- **Otwarty zasiew (strzelba, która nie wypaliła).** Naprawa: macierz zasiewów wymusza wypłatę.
- **Niedomknięty łuk postaci.** Naprawa: audyt łuku; brak zmiany = sygnał do poprawy wcześniejszych scen.
- **Przedwczesne zamrożenie kanonu.** Naprawa: promuj `published` tylko po czystym przeglądzie i za zgodą autora.
- **Przepisywanie prozy tutaj.** Naprawa: to etap składania i audytu; poprawki prozy wracają do `revise-scene`/`polish-pl`.
