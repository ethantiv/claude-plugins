---
name: polish-pl
description: >
  Użyj na scenie po kontroli ciągłości, by ją finalnie wygładzić językowo — wyzwalacze: "wygładź scenę", "korekta językowa", "humanizer sceny", "finalna polszczyzna", "polish pl", "book-forge korekta". Najpierw uruchamia /humanizer:humanizer (zakotwiczony kartą stylu z biblii), potem rój agentów robi finalną korektę polonistyczną i walidację nazw z glosariusza. Ta mikrokolejność jest krytyczna: humanizer bazuje na wzorcach angielskich, więc korekta PL musi być ostatnia. Wynik: wygładzona .book-forge/sceny/<id>.md + raport zmian. Etap 10 pipeline'u book-forge.
argument-hint: "(opcjonalnie id sceny, np. R3S2 — skill i tak dopyta)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Finalna polszczyzna sceny (humanizer → korekta PL)

Ostatni szlif języka: usuwa znamiona pisania AI i doprowadza prozę do naturalnej, poprawnej polszczyzny. Uruchamiany na scenie **po kontroli ciągłości** — to tutaj, a nie wcześniej, odpala się humanizer.

Najpierw przeczytaj `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` (słownik kalk, kalki składniowe, interpunkcja dialogowa) i `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` (karta stylu/głosu, glosariusz, kolejność redakcji).

## Zasada nadrzędna: mikrokolejność (humanizer NAJPIERW, korekta PL OSTATNIA)

To najważniejsza decyzja tego etapu. `/humanizer:humanizer` opiera się na angielskich „signs of AI writing” i potrafi pchać tekst ku angielskiej składni oraz „poprawiać” nazwy własne i interpunkcję. Dlatego:

1. **Humanizer NAJPIERW** — zakotwiczony **kartą stylu/głosu z biblii** (rejestr, rytm, charakterystyczne zwroty) i z **ochroną nazw** z glosariusza.
2. **Korekta polonistyczna OSTATNIA** — naprawia to, co humanizer mógł zepsuć: interpunkcja dialogowa (myślnik, nie cudzysłów angielski), aspekt czasowników, szyk, kalki składniowe, redukcja przysłówków przy czasownikach mówienia („powiedział cicho”).
3. **Walidacja nazw** — każda nazwa z glosariusza w poprawnej, kanonicznej odmianie; przywróć każdą, którą humanizer zmienił.

Odwrotna kolejność (korekta PL przed humanizerem) jest błędem — humanizer cofnąłby część pracy.

## Krok 1 — wejście

1. Wczytaj prozę `.book-forge/sceny/<id>.md` (najlepiej po `continuity-check`). Wczytaj kanon: `b = bible.load_all()` (przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`) i weź **kartę głosu narratora** (rejestr, rytm, zwroty, czego unikać) i **glosariusz** (nazwy + odmiana + warianty zakazane). Domyślnie ostatnia scena zweryfikowana, jeszcze niewygładzona; pozwól wskazać id (`AskUserQuestion`).
2. Sprawdź w logu, że scena przeszła `continuity-check` (PASS). Jeśli ma otwarty CONFLICT — ostrzeż; wygładzanie nieuzgodnionej sceny jest przedwczesne.

**Rola ekspercka:** korektor i redaktor języka polskiego z uchem do prozy.

## Krok 2 — humanizer (główna sesja, NAJPIERW)

Uruchom skill **`/humanizer:humanizer`** na prozie sceny. W poleceniu zakotwicz: zachowaj rejestr i rytm z karty głosu; **nie zmieniaj** nazw własnych z glosariusza; zachowaj polską interpunkcję dialogową i przecinek dziesiętny. Wynik humanizera to wejście do kroku 3 — nie zapisuj go jeszcze jako finalny.

## Krok 3 — rój agentów: korekta PL + walidacja nazw

Uruchom rój według **`references/workflow-swarm.md`** na **tekście po humanizerze**. Fazy:

1. **Korekta polonistyczna** — interpunkcja dialogowa myślnikiem, aspekt (dok./niedok.), naturalny szyk, eliminacja kalk składniowych i AI-izmów (słownik z `polish-style.md`), redukcja przysłówków przy czasownikach mówienia; zachowanie rejestru z karty stylu.
2. **Walidacja nazw** — sprawdzenie każdej nazwy z glosariusza: poprawna forma i odmiana, brak wariantów zakazanych; przywrócenie nazw zmienionych przez humanizer.

Rój może też **zgłosić nowe AI-izmy** wykryte w tekście — jako propozycję do czarnej listy w `polish-style.md` (autor decyduje o dopisaniu; nie edytuj wspólnego pliku automatycznie).

## Krok 4 — zapis i walidacja

Nadpisz `.book-forge/sceny/<id>.md` wygładzoną wersją (opcjonalnie kopia `.book-forge/sceny/<id>.v2.md`). Zapisz raport `.book-forge/korekta-<id>.md` (kategorie zmian, przywrócone nazwy, propozycje AI-izmów). Szczegóły i walidacja (kolejność, sprawdzenie nazw): **`references/build-and-verify.md`**. Ten etap nie generuje HTML — to korekta prozy; widok całości powstaje w `assemble-book`.

## Krok 5 — podsumowanie

Pokaż autorowi: co poprawiono (kategorie), które nazwy przywrócono po humanizerze oraz propozycje nowych AI-izmów do czarnej listy.

## Quick reference

| Aspekt | Reguła |
| --- | --- |
| Wejście | `.book-forge/sceny/<id>.md` (po `continuity-check`) + karta stylu + glosariusz |
| Kolejność | Humanizer NAJPIERW (zakotwiczony) → korekta PL → walidacja nazw OSTATNIA |
| Humanizer | `/humanizer:humanizer` w głównej sesji, z ochroną nazw i rejestru |
| Korekta | Interpunkcja dialogowa, aspekt, szyk, kalki, przysłówki mówienia |
| Nazwy | Glosariusz: poprawna odmiana; przywróć zmienione przez humanizer |
| Wynik | wygładzona `.book-forge/sceny/<id>.md` + `.book-forge/korekta-<id>.md` (+ propozycje AI-izmów) |

## Najczęstsze błędy

- **Korekta PL przed humanizerem.** Naprawa: humanizer najpierw, korekta PL ostatnia.
- **Humanizer psujący nazwy własne.** Naprawa: ochrona glosariusza + walidacja nazw na końcu.
- **Utrata głosu/rejestru.** Naprawa: zakotwicz humanizer i korektę w karcie stylu z biblii.
- **Cudzysłów angielski w dialogu.** Naprawa: polska interpunkcja dialogowa (myślnik).
- **Przysłówki przy „powiedział”.** Naprawa: mocniejszy czasownik lub akcja zamiast „powiedział cicho”.
