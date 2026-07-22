---
name: forge-scenes
description: >
  Użyj, gdy autor ma siatkę scen w biblii i chce napisać KILKA kolejnych scen jednym poleceniem, bez powtarzania pytań przy każdej — wyzwalacze: "taśma scen", "napisz kolejne sceny", "napisz następne N scen", "napisz rozdział", "forge scenes", "book-forge taśma". Orkiestrator sekwencyjnie prowadzi pełny łańcuch jakości per scena: write-scene → revise-scene → continuity-check → polish-pl, zadając wszystkie pytania RAZ na początku (zakres, długość, limit rewizji, polityka eskalacji) i zatrzymując się TYLKO na zdarzeniach wymagających decyzji autora (konflikt RO, wyczerpany limit prób). Po każdej scenie pokazuje postęp z bible.py status. Etap 7–10 pipeline'u book-forge w trybie taśmowym.
argument-hint: "(opcjonalnie zakres, np. 'kolejne 3' / 'rozdział 4' / R2S1,R2S2 — skill i tak dopyta)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Taśma scen — pętla write → revise → continuity → polish (orkiestrator)

Przy powieści z 60+ scenami pojedyncze uruchamianie czterech skilli per scena oznacza setki powtarzanych pytań i ręcznych handoffów. Ten skill to **sekwencyjny orkiestrator**: pyta o wszystko RAZ, potem prowadzi scenę za sceną przez pełny łańcuch jakości, przerywając tylko tam, gdzie decyzja należy do autora.

Najpierw przeczytaj `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` (kolejność redakcji per scena, limit iteracji) — orkiestrator egzekwuje dokładnie tę kolejność.

## Zasada nadrzędna

Orkiestrator **nie ma własnego roju ani własnych reguł prozy** — roje, bramki i uprawnienia zapisu żyją w wołanych skillach i pozostają nienaruszone (continuity-check nadal jest jedyną bramką zapisu w pętli prozy). Tu jest tylko pętla, pamięć odpowiedzi autora i twarde punkty zatrzymania. Proza powstaje **sekwencyjnie** — scena N widzi streszczenia scen do N-1 (anty-amnezja przez agregat `streszczenia`).

## Krok 1 — pytania RAZ, na początku

1. **Preflight:** `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bible.py check-stage write-scene` — bez biblii, siatki lub z dziurawymi kartami scen przerwij od razu (pokaż `braki`).
2. Pokaż stan: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bible.py status` (sceny wg statusu, słowa vs budżet).
3. Dopytaj `AskUserQuestion` (wszystko teraz, nic w pętli):
   - **Zakres:** kolejne N scen bez prozy (domyślnie 3) / cały wskazany rozdział / jawna lista id.
   - **Długość scen:** pomiń, jeśli `meta.budzet_slow` i `meta.liczba_scen` ustawione (liczy się z budżetu); inaczej zapytaj raz i stosuj do wszystkich.
   - **Limit prób rewizji** per scena (domyślnie 3) i **polityka po wyczerpaniu**: pytaj autora przy każdej scenie / automatycznie `accept-with-debt` z wpisem QA.
   - **Uwagi autora** wspólne dla całej taśmy (np. „pilnuj tempa").

## Krok 2 — pętla per scena (sekwencyjnie, w kolejności siatki)

Dla każdego id z zakresu:

1. `bible.py check-stage write-scene` (karty mogły się zmienić) → **`/book-forge:write-scene <id>`** z zapamiętanymi odpowiedziami; przekaż instrukcję **pominięcia auto-handoffu** — bramki prowadzi orkiestrator (patrz adnotacja w write-scene, Krok 5).
2. **`/book-forge:revise-scene <id>`** z limitem prób i uwagami z Kroku 1 (bez ponownych pytań).
3. **`/book-forge:continuity-check <id>`** z obiektem `propozycje` z kroków 1–2. **PASS** → dalej. **CONFLICT RO** → twardy stop: pokaż konflikt autorowi (`AskUserQuestion`), zgodnie z regułami bramki — taśma nie kanonizuje niczego „na ślepo".
4. **`/book-forge:polish-pl <id>`** (unslop → korekta PL, powstaje `korekta-<id>.md`).
5. Linia postępu: `bible.py status` → pokaż „scena X/N gotowa · słowa Y / budżet (Z%)".

**Punkty zatrzymania (jedyne):** konflikt RO bramki; wyczerpany limit rewizji przy polityce „pytaj"; nieprzechodzący preflight. Wszystko inne płynie bez pytań.

## Krok 3 — podsumowanie taśmy

Po ostatniej scenie pokaż: listę napisanych scen z werdyktami bramki, sumę słów i procent budżetu, zaciągnięte długi (`accept-with-debt` z notatek QA), otwarte zasiewy dotknięte w taśmie oraz sugestię następnego kroku (kolejna taśma albo `assemble-book`, gdy siatka domknięta).

> **Tryb serii** (istnieje `.book-forge/seria.md`): ustaw `BOOK_DIR`/`WORK`/`BIBLE_DIR` raz, przed pętlą — wszystkie wołane skille dziedziczą je z sesji (id scen z prefiksem tomu, np. `T2R1S1`).

## Quick reference

| Aspekt | Reguła |
| --- | --- |
| Wejście | siatka scen w biblii (preflight `check-stage write-scene`) + zakres od autora |
| Silnik | pętla po skillach `write-scene` → `revise-scene` → `continuity-check` → `polish-pl` |
| Pytania | RAZ na początku; w pętli tylko twarde stopy |
| Stopy | CONFLICT RO · wyczerpany limit rewizji (przy polityce „pytaj") · zły preflight |
| Zapis do kanonu | wyłącznie przez bramkę `continuity-check` (jak poza taśmą) |
| Postęp | `bible.py status` po każdej scenie (X/N, słowa vs budżet) |
| Wynik | N scen po pełnym łańcuchu jakości + podsumowanie taśmy |

## Najczęstsze błędy

- **Równoległe pisanie scen zależnych.** Naprawa: pętla jest sekwencyjna — scena N czyta streszczenia poprzednich z kanonu.
- **Przejechanie po konflikcie RO.** Naprawa: CONFLICT to twardy stop; decyzja należy do autora, nie do taśmy.
- **Powtarzanie pytań w pętli.** Naprawa: wszystkie odpowiedzi zbierane raz; wołane skille dostają je jako wejście.
- **Cicha akceptacja długu.** Naprawa: `accept-with-debt` zawsze ląduje w QA i w podsumowaniu taśmy.
- **Taśma zamiast bramek.** Naprawa: orkiestrator niczego nie zapisuje do biblii — to robią wołane etapy wg własnych reguł.
