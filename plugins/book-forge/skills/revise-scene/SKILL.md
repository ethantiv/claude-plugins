---
name: revise-scene
description: >
  Użyj, gdy scena ma już szkic (z write-scene) i trzeba ją pogłębić oraz zredagować — wyzwalacze: "popraw scenę", "pogłęb scenę", "redakcja sceny", "revise scene", "dev-edit", "book-forge rewizja". Rój agentów w pętli generuj→oceń wzmacnia prozę środkami literackimi (podtekst, charakteryzacja przez działanie, sensoryka, mikrozwrot, zasiew), a osobny krytyk „na ślepo” ocenia ją kryteriami fabularnymi jako bramka PASS/FIX. Wynik: poprawiona .book-forge/sceny/<id>.md + notatka QA. Etap 8 pipeline'u book-forge.
argument-hint: "(opcjonalnie id sceny, np. R3S2 — skill i tak dopyta)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Rewizja sceny: pogłębienie + redakcja developmentalna (rój agentów)

Bierze surowy szkic sceny i doprowadza go do jakości publikacyjnej: najpierw **pogłębia prozą**, potem przepuszcza przez **bezlitosną redakcję developmentalną** jako bramkę. Oba kroki działają w pętli, aż scena przejdzie albo wyczerpie limit prób.

Najpierw przeczytaj `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` (kolejność redakcji, pola RO/RUNTIME, limit iteracji) i `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` (język).

## Zasada nadrzędna: rozdzielność ról (poprawiający ≠ oceniający)

Najważniejsza decyzja tego etapu: **pogłębiający i krytyk to osobne role**. Krytyk (dev-edit) czyta **tylko kartę sceny + wyciąg z biblii + sam tekst** — nie wie, „co dopisano” ani dlaczego. Inaczej bramka przepuszczałaby własne dzieło. Dev-edit jest twardą bramką **PASS/FIX**, nie luźną poradą („nie bądź miły, bądź użyteczny”).

To dwa scalone i przerobione pod prozę etapy: **pogłębienie** wzmacnia scenę środkami prozy (zero wstrzykiwanych anegdot, statystyk czy zwrotów do czytelnika), a **dev-edit** ocenia ją kryteriami fabularnymi zamiast eseistycznych.

## Kolejność redakcji — gdzie jesteśmy

Etap **„pogłębienie + dev-edit”**: po `write-scene` (treść), przed `continuity-check`. Dlatego **nadal bez `/unslop:unslop`** — unslop i finalna korekta PL przychodzą w `polish-pl`, po kontroli ciągłości. Tu pilnujemy treści, struktury i siły prozy, nie wygładzania pod wzorce AI.

## Krok 1 — wejście

1. **Preflight:** `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bible.py check-stage revise-scene <id>` — brak prozy = przerwij z czytelnym komunikatem zamiast wykładać rój. Potem wczytaj szkic `.book-forge/sceny/<id>.md`, a kanon przez `b = bible.load_all()`: kartę sceny z `b['kanon_fabularny']['sceny']` i **wyciąg** z biblii (karta głosu narratora, głosy obecnych postaci, stawka, łuk postaci, istotne zasady świata, glosariusz, **profil `chaos` obecnych postaci** i **`meta.forma`** — zasilają fazę Disruption). Domyślnie pierwsza scena ze szkicem i statusem innym niż `zweryfikowana` (priorytet: `do-rewizji` — sceny oflagowane przez `world-research`); pozwól wskazać id (`AskUserQuestion`).
2. Jeśli istnieje `.book-forge/redakcja-todo.md` (work-lista z przeglądu całości w `assemble-book`), wczytaj sekcję `## <id>` i sekcję `## CAŁOŚĆ` — pozycje dotyczące tej sceny przekaż do roju jako dodatkowe cele rewizji (to pętla zwrotna całość→scena).
3. Dopytaj `AskUserQuestion`: maksymalna liczba prób (domyślnie 3) i czego autor szczególnie pilnuje (np. tempo, podtekst).

**Rola pogłębiającego:** powieściopisarz wzmacniający scenę środkami prozy. **Rola krytyka:** redaktor prowadzący czytający na ślepo.

## Krok 2 — rój agentów (Workflow, pętla generuj→oceń)

Uruchom rój według **`references/workflow-swarm.md`**. W pętli (do `N` prób):

1. **Pogłębienie** — wzmocnij scenę: podtekst dialogu (co postać przemilcza), charakteryzacja przez działanie, detal sensoryczny osadzający w świecie, mowa pozornie zależna, podniesienie stawki, mikrozwrot, zasiew Czechowowskiej strzelby. Bez dydaktyzmu i bez wybijania czytelnika z lektury.
2. **Dev-edit (krytyk na ślepo)** — ocena kryteriami fabularnymi: cel i zwrot, rosnąca stawka, sprawczość bohatera (działa, nie tylko reaguje), podtekst dialogu, spójność punktu widzenia i czasu, „pokazuj, nie opowiadaj”, brak przeładowania informacjami, rozróżnialność głosów, tempo, słabe czasowniki, klisze i wypełniacze. Werdykt PASS/FIX + „trzy najważniejsze poprawki”.
3. Jeśli FIX — kolejna runda pogłębienia, która uwzględnia poprawki. Jeśli PASS — koniec.

**Limit iteracji + eskalacja:** po `N` próbach bez PASS — zapisz z adnotacją `accept-with-debt` w notatce QA i zgłoś autorowi (nigdy cicha, nieskończona pętla).

Po pętli (na ZAAKCEPTOWANEJ prozie) działa faza **Disruption** — anty-przewidywalność: 2–4 operacje, które usuwają gładką sztuczność, a nie „poprawiają” (nieistotna myśl z `chaos.obsesja` postaci, złamana kontrola emocji, jedno celowo chropawe zdanie, zaszumiony dialog / wycięty przewidywalny akapit). Działa POZA bramką dev-edit (która ukarałaby celową szorstkość) i jest **wyłączona dla non-fiction** (`meta.forma`). Zwraca `celowe_odstepstwa` — listę fragmentów chronionych przed korektą i unslopem w `polish-pl`.

## Krok 3 — bez unslopa, lekka redakcja PL

Po przejściu pętli zrób tylko **lekką redakcję polonistyczną** (anglicyzmy, AI-slop, interpunkcja dialogowa) — **nie** unslop (ten w `polish-pl`). Nazw własnych z glosariusza nie ruszaj.

## Krok 4 — zapis i QA

1. Nadpisz `.book-forge/sceny/<id>.md` poprawioną sceną (opcjonalnie zachowaj kopię `.book-forge/sceny/<id>.v1.md`).
2. Zapisz **`.book-forge/sceny/<id>.qa.md`** — notatka QA: werdykt, oceny, najważniejsze poprawki, dziennik rund, ewentualny dług (`accept-with-debt`) oraz **`celowe_odstepstwa`** z fazy Disruption (lista chronionych fragmentów — `polish-pl` ją stąd wczyta). To notatka, **nie** zapis do kanonu — kanonu fabuły ten etap nie zmienia (robi to `continuity-check`).
3. Jeśli pogłębienie wprowadziło nowe fakty/nazwy/zasiewy, rój zwraca je jako obiekt `propozycje` — trzymaj go w pamięci jako ładunek handoffu (Krok 5), **nie** zapisuj do pliku.

Szczegóły i walidacja: **`references/build-and-verify.md`**.

## Krok 5 — handoff do continuity-check

Po zapisie poprawionej sceny **od razu uruchom `/book-forge:continuity-check`** dla tego `<id>`, przekazując obiekt `propozycje` z roju — tak nowe ustalenia z pogłębienia od razu przechodzą przez bramkę i (po audycie) trafiają do biblii. Zasada „tylko continuity-check pisze do kanonu” zostaje: handoff jedynie wyzwala bramkę; przy konflikcie RO zapyta ona autora. W trybie serii handoff dziedziczy `BOOK_DIR`/`WORK`/`BIBLE_DIR`.

## Krok 6 — podsumowanie

Pokaż autorowi: werdykt (PASS/FIX), liczbę rund, najważniejsze poprawki, czy zaakceptowano dług, oraz werdykt bramki ciągłości z handoffu.

## Quick reference

| Aspekt | Reguła |
| --- | --- |
| Wejście | `.book-forge/sceny/<id>.md` + karta sceny + wyciąg z biblii |
| Silnik | Rój agentów: pętla pogłębienie → dev-edit (`references/workflow-swarm.md`) |
| Rozdzielność | Krytyk czyta tylko kartę + biblię + tekst (na ślepo) |
| Bramka | Dev-edit PASS/FIX, kryteria fabularne, „trzy najważniejsze poprawki” |
| Limit | N prób (domyślnie 3) → `accept-with-debt` + eskalacja |
| Unslop | NIE tutaj — w `polish-pl` |
| Wynik | poprawiona `.book-forge/sceny/<id>.md` + `.book-forge/sceny/<id>.qa.md` + handoff do `continuity-check` |

## Najczęstsze błędy

- **Poprawiający ocenia sam siebie.** Naprawa: krytyk to osobna rola, czyta na ślepo.
- **Wstrzykiwanie anegdot/statystyk.** Naprawa: wzmacniaj środkami prozy, nie wstawkami.
- **Kryteria eseistyczne.** Naprawa: oceniaj fabularnie (cel, zwrot, stawka, sprawczość, podtekst).
- **Nieskończona pętla.** Naprawa: twardy limit prób + `accept-with-debt` + eskalacja.
- **Unslop za wcześnie.** Naprawa: dopiero `polish-pl`, po kontroli ciągłości.
