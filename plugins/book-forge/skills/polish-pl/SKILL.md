---
name: polish-pl
description: >
  Użyj na scenie po kontroli ciągłości, by ją finalnie wygładzić językowo — wyzwalacze: "wygładź scenę", "korekta językowa", "unslop sceny", "finalna polszczyzna", "polish pl", "book-forge korekta". Najpierw uruchamia /unslop:unslop (zakotwiczony kartą stylu z biblii), potem rój agentów robi finalną korektę polonistyczną i walidację nazw z glosariusza. Ta mikrokolejność jest krytyczna: korekta PL musi mieć ostatnie słowo po ingerencjach unslopa. Wynik: wygładzona .book-forge/sceny/<id>.md + raport zmian. Etap 10 pipeline'u book-forge.
argument-hint: "(opcjonalnie id sceny, np. R3S2 — skill i tak dopyta)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Finalna polszczyzna sceny (unslop → korekta PL)

Ostatni szlif języka: usuwa znamiona pisania AI i doprowadza prozę do naturalnej, poprawnej polszczyzny. Uruchamiany na scenie **po kontroli ciągłości** — to tutaj, a nie wcześniej, odpala się unslop.

Najpierw przeczytaj `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` (słownik kalk, kalki składniowe, interpunkcja dialogowa) i `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` (karta stylu/głosu, glosariusz, kolejność redakcji).

## Zasada nadrzędna: mikrokolejność (unslop NAJPIERW, korekta PL OSTATNIA)

To najważniejsza decyzja tego etapu. `/unslop:unslop` wywodzi się z katalogu „signs of AI writing” i mimo polskich wzorców potrafi „poprawiać” nazwy własne i interpunkcję. Dlatego:

1. **Unslop NAJPIERW** — zakotwiczony **kartą stylu/głosu z biblii** (rejestr, rytm, charakterystyczne zwroty) i z **ochroną nazw** z glosariusza.
2. **Korekta polonistyczna OSTATNIA** — naprawia to, co unslop mógł zepsuć: interpunkcja dialogowa (myślnik, nie cudzysłów angielski), aspekt czasowników, szyk, kalki składniowe, redukcja przysłówków przy czasownikach mówienia („powiedział cicho”).
3. **Walidacja nazw** — każda nazwa z glosariusza w poprawnej, kanonicznej odmianie; przywróć każdą, którą unslop zmienił.

Odwrotna kolejność (korekta PL przed unslopem) jest błędem — unslop cofnąłby część pracy.

## Krok 1 — wejście

1. **Preflight:** `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bible.py check-stage polish-pl <id>`. Potem wczytaj prozę `.book-forge/sceny/<id>.md` (najlepiej po `continuity-check`). Wczytaj kanon: `b = bible.load_all()` i weź **kartę głosu narratora** (rejestr, rytm, zwroty, czego unikać) i **glosariusz** (nazwy + odmiana + warianty zakazane). Jeśli istnieje `.book-forge/sceny/<id>.qa.md` z listą **`celowe_odstepstwa`** (z fazy Disruption w `revise-scene`), wczytaj ją — to fragmenty celowej szorstkości, których ani unslop, ani korekta NIE mają wygładzać; przekażesz ją do unslopa (Krok 2) i do roju (`args.celowe_odstepstwa`). Jeśli istnieje `.book-forge/redakcja-todo.md`, sprawdź sekcję `## <id>` — pozycje `[echo]` (powtórzone frazy, słowa-ulubieńcy) to konkretne cele tej korekty. Domyślnie ostatnia scena zweryfikowana, jeszcze niewygładzona — „niewygładzona" znaczy: **brak pliku `.book-forge/korekta-<id>.md`** (raport korekty jest de facto markerem wygładzenia; kanon nie ma osobnego statusu „wygładzona"). Pozwól wskazać id (`AskUserQuestion`).
2. Sprawdź w logu, że scena przeszła `continuity-check` (PASS). Jeśli ma otwarty CONFLICT — ostrzeż; wygładzanie nieuzgodnionej sceny jest przedwczesne.

**Rola ekspercka:** korektor i redaktor języka polskiego z uchem do prozy.

## Krok 2 — unslop (główna sesja, NAJPIERW)

Uruchom skill **`/unslop:unslop`** na prozie sceny. W poleceniu zakotwicz: zachowaj rejestr i rytm z karty głosu; **nie zmieniaj** nazw własnych z glosariusza; zachowaj polską interpunkcję dialogową i przecinek dziesiętny; **jeśli wczytano `celowe_odstepstwa` (Krok 1), nie wygładzaj tych fragmentów — to celowa szorstkość z fazy Disruption**. Wynik unslopa to wejście do kroku 3 — nie zapisuj go jeszcze jako finalny.

## Krok 3 — rój agentów: korekta PL + walidacja nazw

Uruchom rój według **`references/workflow-swarm.md`** na **tekście po unslopie**. Fazy:

1. **Korekta polonistyczna** — interpunkcja dialogowa myślnikiem, aspekt (dok./niedok.), naturalny szyk, eliminacja kalk składniowych i AI-izmów (słownik z `polish-style.md`), redukcja przysłówków przy czasownikach mówienia; zachowanie rejestru z karty stylu.
2. **Walidacja nazw** — sprawdzenie każdej nazwy z glosariusza: poprawna forma i odmiana, brak wariantów zakazanych; przywrócenie nazw zmienionych przez unslop.

Rój może też **zgłosić nowe AI-izmy** wykryte w tekście — jako propozycję do czarnej listy w `polish-style.md` (autor decyduje o dopisaniu; nie edytuj wspólnego pliku automatycznie).

## Krok 4 — zapis i walidacja

Nadpisz `.book-forge/sceny/<id>.md` wygładzoną wersją (opcjonalnie kopia `.book-forge/sceny/<id>.v2.md`). Zapisz raport `.book-forge/korekta-<id>.md` (kategorie zmian, przywrócone nazwy, propozycje AI-izmów). Szczegóły i walidacja (kolejność, sprawdzenie nazw): **`references/build-and-verify.md`**. Ten etap nie generuje HTML — to korekta prozy; widok całości powstaje w `assemble-book`.

## Krok 5 — podsumowanie

Pokaż autorowi: co poprawiono (kategorie), które nazwy przywrócono po unslopie oraz propozycje nowych AI-izmów do czarnej listy.

## Quick reference

| Aspekt | Reguła |
| --- | --- |
| Wejście | `.book-forge/sceny/<id>.md` (po `continuity-check`) + karta stylu + glosariusz |
| Kolejność | Unslop NAJPIERW (zakotwiczony) → korekta PL → walidacja nazw OSTATNIA |
| Unslop | `/unslop:unslop` w głównej sesji, z ochroną nazw i rejestru |
| Korekta | Interpunkcja dialogowa, aspekt, szyk, kalki, przysłówki mówienia |
| Nazwy | Glosariusz: poprawna odmiana; przywróć zmienione przez unslop |
| Wynik | wygładzona `.book-forge/sceny/<id>.md` + `.book-forge/korekta-<id>.md` (+ propozycje AI-izmów) |

## Najczęstsze błędy

- **Korekta PL przed unslopem.** Naprawa: unslop najpierw, korekta PL ostatnia.
- **Unslop psujący nazwy własne.** Naprawa: ochrona glosariusza + walidacja nazw na końcu.
- **Utrata głosu/rejestru.** Naprawa: zakotwicz unslop i korektę w karcie stylu z biblii.
- **Cudzysłów angielski w dialogu.** Naprawa: polska interpunkcja dialogowa (myślnik).
- **Przysłówki przy „powiedział”.** Naprawa: mocniejszy czasownik lub akcja zamiast „powiedział cicho”.
