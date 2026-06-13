---
name: book-bible
description: >
  Użyj, gdy autor zaczyna pisać powieść i potrzebuje wspólnego, usystematyzowanego fundamentu, żeby całość była spójna — wyzwalacze: "biblia książki", "book bible", "story bible", "świat i postacie", "ustal kanon", "book-forge biblia". Rój agentów buduje jedno źródło prawdy (świat, postacie, głosy, glosariusz z polską odmianą, kanon fabularny, fakty) z raportu i konspektu. Wynik: zdekomponowany kanon-wiki .book-forge/biblia/**/*.md + .book-forge/biblia/index.md (katalog). Idempotentne. To fundament etapów pisania w pipeline'u book-forge.
argument-hint: "(opcjonalnie ścieżki do raportu/konspektu — skill i tak dopyta)"
allowed-tools: Workflow, AskUserQuestion, Skill, Bash, Read, Write, Edit, WebSearch, WebFetch
---

# Biblia książki — wspólny stan projektu (rój agentów)

Buduje i utrzymuje **biblię** powieści: jedno źródło prawdy, które każdy kolejny etap czyta, dzięki czemu agent ma pełny kontekst, a świat, postacie, nazwy, głos i fakty są spójne od pierwszej do ostatniej strony. To fundament, na którym stoją wszystkie etapy pisania.

**Najpierw przeczytaj specyfikację:** **`${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md`** — zdekomponowany kanon-wiki (markdown źródłem prawdy, całe I/O przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`), pola RO vs RUNTIME, glosariusz z odmianą, anty-dryf. Reguły języka: **`${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`**.

## Zasada nadrzędna: spójność + polszczyzna

Dwa kryteria równorzędne. **Spójność:** nic nie może sobie przeczyć (to po to jest biblia). **Polszczyzna:** opisy w biblii mają brzmieć naturalnie, bez anglicyzmów i AI-slopu (faza redakcji + `/humanizer:humanizer` na partiach opisowych).

## Krok 1 — wejście

1. Znajdź artefakty wcześniejszych etapów: **najpierw** `.book-forge/pomysl.json` (deterministyczny artefakt z etapu 1: `idea`, `brief`, `verdict`, `reader`), z fallbackiem na `market-report-*.html` (obiekt `DATA`), oraz `.book-forge/konspekt.md`. Jeśli brak lub jest kilka — zapytaj o ścieżki (`AskUserQuestion`). Biblia może powstać już po etapie 1 (sam pomysł), ale najlepiej po etapie 2.
2. Wczytaj je (`Read`) i wyciągnij: gatunek, czytelnika, zwycięski pomysł (`t`, `en`, `silnik`, `op`, `hook`, `comps`, `protagonista`), **brief autora** (`DATA.brief`: `format`, `form`, `tone`, `spice`, `protagonist`, `protAge`, `taboo`, `market`), a z konspektu — fundament, strukturę, rozdziały. Brief zasila budowaną sekcję `meta` (Krok 5): `format`→`meta.tomy`/tryb serii, `form`→`meta.forma` (guard non-fiction dla prozy) i sterowanie profilem chaosu postaci, `tone`→`meta.ton`, `protagonista`→seed postaci; nie dubluj POV/czasu z briefu (ich tu nie ma — to decyzja tego etapu). `form` przekaż też do roju w `args.form`.
3. Zbierz decyzje autora przez `AskUserQuestion`: **POV** (np. trzecioosobowa ograniczona), **czas** (przeszły/teraźniejszy), **subgatunek**, **liczba tomów** (domyślnie z `brief.format`: pojedyncza→1, trylogia→3, seria→pytaj ile).

**Rola ekspercka:** showrunner powieści i strażnik kanonu — ktoś, kto pilnuje, by świat i postacie były logiczne, a nazwy odmieniały się tak samo w całej książce.

## Krok 2 — idempotencja (czytaj, nie nadpisuj)

Rozpoznaj stan katalogu `.book-forge/biblia/`:
- **Kanon-wiki istnieje** (`.book-forge/biblia/index.md`) → **wczytaj go** `bible.load_all()` i traktuj pola **RO** jako ustalone: rój uzupełnia puste, ale nie zmienia bez zgody autora (o realnej zmianie RO pytaj `AskUserQuestion` → wtedy jawny `write_entity`). Pola RUNTIME zostają nietknięte (rosną dopiero przez bramkę ciągłości).
- **Pusto** → świeża budowa z roju.

## Krok 3 — rój agentów (Workflow)

Uruchom rój według **`references/workflow-swarm.md`**. Agenci wypełniają sekcje z różnych ról: architekt świata (zasady z KOSZTEM), twórca postaci (want/need/rana/kłamstwo/łuk + **profil chaosu**: obsesja, zniekształcenie poznawcze, niechciane wspomnienie, nieudana kontrola emocji — skalowany gatunkiem, pomijany dla non-fiction), projektant głosów (narrator + osobne idiolekty postaci), redaktor nazewnictwa (glosariusz z pełną polską odmianą i wariantami zakazanymi), strażnik motywu. Potem synteza spójności scala i usuwa sprzeczności. **Lekki research** realiów (agent-browser) tylko dla twardych filarów świata koniecznych do planowania — właściwy, ukierunkowany research zostaw na później (etap `world-research`).

## Krok 4 — humanizer (główna sesja)

Na partiach **opisowych** (opisy świata, postaci, motyw) uruchom `/humanizer:humanizer` i nanieś poprawki. Nie ruszaj nim nazw własnych z glosariusza (chronione).

## Krok 5 — zapis (kanon-wiki) i walidacja

Zapisz kanon przez **`${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`** (singletony → `write_entity`/`write_section`, encje postaci/lokacji/głosów/glosariusza → pętla `write_entity`, siatka scen z konspektu → `write_scene_grid`), na końcu `render_index()`. Szczegóły kształtu, merge idempotentny i walidacja: **`references/build-and-verify.md`**. Waliduj: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bible.py validate` — raport potwierdza poprawne frontmattery, wypełnione sekcje RO i pełną odmianę każdej nazwy w glosariuszu.

## Krok 6 — podsumowanie

Pokaż autorowi: ścieżki obu plików, liczbę postaci, zasad świata i haseł glosariusza, oraz **luki do uzupełnienia** (np. brak kosztu przy zasadzie świata, postać bez łuku). Surowo zgłaszaj braki — pusta biblia gorzej trzyma kanon.

## Quick reference

| Aspekt | Reguła |
| --- | --- |
| Wejście | `.book-forge/pomysl.json` (fallback: HTML etapu 1) + `.book-forge/konspekt.md` + decyzje (POV, czas, tomy) |
| Silnik | Rój agentów (`references/workflow-swarm.md`) |
| Wynik | zdekomponowany kanon-wiki `.book-forge/biblia/**/*.md` + `.book-forge/biblia/index.md` (katalog) |
| Warstwy | Frontmatter stron = prawda; treść stron i `index.md` = pochodna, generowane przez `bible.py` |
| Pola | RO (ustalenia) vs RUNTIME (stan; rośnie tylko przez bramkę ciągłości) |
| Nazwy | Glosariusz z pełną polską odmianą + warianty zakazane |
| Idempotencja | Ponowne uruchomienie uzupełnia, nie nadpisuje RO bez zgody |
| Język | Naturalna polszczyzna + `/humanizer:humanizer` na opisach |

## Najczęstsze błędy

- **Zasada świata bez kosztu/ograniczenia.** Naprawa: każda zasada mówi, co jest niemożliwe i dlaczego (inaczej świat traci napięcie).
- **Jeden głos dla wszystkich.** Naprawa: osobne idiolekty postaci obok głosu narratora.
- **Nazwy bez odmiany.** Naprawa: pełna deklinacja w glosariuszu + warianty zakazane (ochrona przed dryfem i przed „poprawkami” humanizera).
- **Nadpisanie ustaleń.** Naprawa: pola RO zmieniaj tylko za zgodą autora.
- **Ręczna edycja treści/indeksu.** Naprawa: zmieniaj frontmatter stron przez `bible.py`; treść stron i `index.md` regeneruj (`render_index`).
