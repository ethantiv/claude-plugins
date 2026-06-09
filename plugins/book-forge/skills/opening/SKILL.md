---
name: opening
description: >
  Użyj, gdy autor ma konspekt i biblię i chce mocny początek powieści — wyzwalacze: "początek książki", "pierwsza strona", "pierwsza scena", "mocne otwarcie", "opening", "book-forge początek". Rój agentów pisze 3 warianty pierwszej sceny (filmowa scena, mocne zdanie otwierające, intymna spowiedź bohatera), każdy zakotwiczony w głosie i świecie z biblii, po czym ocenia je kryteriami fabularnymi, sprawdza zgodność z kanonem i wygładza (humanizer → korekta PL). Wynik: .book-forge/poczatek.md + interaktywny HTML. Etap 4 pipeline'u book-forge — pierwszy etap pisania prozy.
argument-hint: "(opcjonalnie ścieżki do konspektu/biblii — skill i tak dopyta)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Mocny początek powieści — 3 warianty (rój agentów)

Pierwsza strona decyduje, czy ktoś czyta dalej. To polecenie pisze **3 warianty pierwszej sceny** powieści, każdy inną techniką otwarcia, a potem poddaje je bezlitosnej ocenie fabularnej i wskazuje, który rozwijać.

To etap **pisania prozy**, więc obowiązuje cały rygor spójności: warianty muszą zgadzać się z **biblią** (głos, świat, postacie, nazwy). Najpierw przeczytaj `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` (po co biblia, pola RO/RUNTIME) oraz `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` (język).

## Zasada nadrzędna

Trzy rzeczy naraz, równorzędnie: **wciągająca proza**, **spójność z kanonem** (nic nie przeczy biblii) i **naturalna polszczyzna** (bez anglicyzmów i AI-slopu). Głos to **narrator i bohater z biblii**, nigdy „głos autora”. Bez wstrzykiwanych anegdot, bez zwrotów typu „stop and think”, bez wymuszonego urwania akcji w punkcie napięcia (cliffhangera) — haczyk ma wynikać ze sceny.

## Krok 1 — wejście (biblia jest wymagana)

1. Wczytaj kanon: `bible.load_all()` (przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`). Jeśli kanonu nie ma — przerwij i poproś autora o uruchomienie `/book-forge:book-bible` (bez biblii nie ma spójności). Wczytaj też `.book-forge/konspekt.md`.
2. Z biblii weź **wyciąg** (nie cały obiekt): karta głosu narratora, głosy postaci obecnych w scenie 1, zasady świata istotne dla scenerii, glosariusz (nazwy + odmiana), motyw, stawka. Z konspektu — pierwszy rozdział/scena (obietnica, haczyk).
3. Dopytaj `AskUserQuestion`: którą **scenę otwierającą** rozwijamy (domyślnie pierwsza z konspektu), długość wariantu (domyślnie 300–400 słów) i czy autor ma **próbkę własnego stylu** do uwzględnienia (opcjonalnie — ale głos i tak kotwiczy karta stylu z biblii, nie „głos autora-eksperta”).

**Rola ekspercka:** powieściopisarz i ghostwriter prozy, który pisze w głosie z biblii (narrator + idiolekty), nie we własnym.

## Krok 2 — rój agentów (Workflow)

Uruchom rój według **`references/workflow-swarm.md`**. Fazy:

1. **Warianty** — trzy techniki otwarcia, każda jako pełna scena (300–400 słów), zakotwiczone w głosie i świecie z biblii:
- **Filmowa scena** — wejście w środek akcji (in medias res), konkret sensoryczny, ruch; bez ekspozycji na wejściu.
- **Mocne zdanie otwierające** — prowokacyjne, intrygujące zdanie narratora lub bohatera, z którego wynika scena (nie oderwany aforyzm).
- **Intymna spowiedź bohatera** — bliski, pierwszoosobowy (lub głęboko ograniczony) głos, który od razu buduje więź; spowiedź w roli, nie autora.
2. **Ocena fabularna (dev-edit)** — niezależny krytyk ocenia każdy wariant kryteriami PROZY: siła haczyka (pierwsze zdania), spójność głosu z kartą, POV/czas, „pokazuj, nie opowiadaj”, brak przeładowania informacjami, wciągnięcie czytelnika, tempo. Bramka PASS/FIX, „nie bądź miły, bądź użyteczny”.
3. **Kontrola ciągłości** — każdy wariant porównany z biblią: nazwy i ich odmiana, opisy postaci, zasady świata, POV/czas. Zgłoś CONFLICT, jeśli coś przeczy kanonowi.
4. **Werdykt** — który wariant rozwijać i dlaczego (lub jak je połączyć).

## Krok 3 — humanizer, potem korekta PL (kolejność!)

Na prozie wariantów: **najpierw `/humanizer:humanizer`** (zakotwiczony kartą stylu z biblii), **potem** finalna korekta polonistyczna i walidacja nazw z glosariusza (humanizer bazuje na wzorcach angielskich i mógłby zepsuć odmianę nazw lub interpunkcję dialogową — dlatego korekta PL jest ostatnia). Szczegóły: `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` (sekcja „kolejność redakcji”).

## Krok 4 — zapis i walidacja

Zbuduj (szczegóły: **`references/build-and-verify.md`**):
1. **`poczatek-<slug>.html`** — interaktywny widok ze szablonu `${CLAUDE_PLUGIN_ROOT}/skills/opening/assets/opening-template.html` (zakładki: trzy warianty; każdy z prozą, liczbą słów, haczykiem i oceną). Waliduj `node --check` + podgląd w agent-browser.
2. **`.book-forge/poczatek.md`** — wybrany (rekomendowany) wariant jako tekst do dalszej pracy.

## Krok 5 — propozycja dopisów do biblii (przez bramkę)

Jeśli warianty wprowadzają **nowe** nazwy/fakty/szczegóły postaci, **zaproponuj** je jako dopisy do pól RUNTIME biblii (`fakty`, `glosariusz`, `_stan`). Zapisuj je do kanonu (przez `bible.py`: `append_record`/`write_entity`/`update_runtime`) **dopiero po potwierdzeniu autora** (`AskUserQuestion`) — to namiastka bramki `continuity-check`, dopóki nie powstanie. Pól RO nie ruszaj.

## Krok 6 — podsumowanie

Pokaż autorowi: ścieżki plików, rekomendowany wariant z uzasadnieniem, oceny trzech wariantów i ewentualne konflikty z kanonem do rozstrzygnięcia. Zaznacz, że `.book-forge/poczatek.md` (wybrany wariant) zostanie automatycznie podchwycony przez następny etap `outline-to-scenes` (ustawi `proza_zrodlo` na karcie sceny otwierającej) i rozwinięty przez `write-scene` — autor nie musi ręcznie przenosić otwarcia do `.book-forge/sceny/`.

## Quick reference

| Aspekt | Reguła |
| --- | --- |
| Wejście | kanon `.book-forge/biblia/` (przez bible.py, wymagane) + `.book-forge/konspekt.md` |
| Silnik | Rój agentów (`references/workflow-swarm.md`) |
| Warianty | Filmowa scena · mocne zdanie · intymna spowiedź (300–400 słów) |
| Głos | Narrator + idiolekty z biblii (NIE „głos autora”) |
| Ocena | Kryteria fabularne (haczyk, głos, POV, pokazuj nie opowiadaj, tempo) |
| Spójność | Kontrola względem biblii; CONFLICT zamiast cichej zmiany |
| Redakcja | Humanizer NAJPIERW, korekta PL + walidacja nazw OSTATNIA |
| Wynik | `poczatek-<slug>.html` + `.book-forge/poczatek.md`; propozycje runtime do biblii |

## Najczęstsze błędy

- **Głos autora zamiast narratora.** Naprawa: kotwicz w karcie głosu z biblii.
- **Ekspozycja/przeładowanie informacjami na wejściu.** Naprawa: konkret sensoryczny i akcja; świat dawkuj.
- **Haczyk doklejony.** Naprawa: napięcie ma wynikać ze sceny, nie z gadżetu.
- **Złamanie kanonu** (nazwa, opis, POV). Naprawa: kontrola ciągłości + glosariusz.
- **Humanizer po korekcie PL.** Naprawa: humanizer najpierw, korekta PL ostatnia.
