# book-forge — pipeline i planowane etapy

Plugin prowadzi autora od pomysłu do gotowego maszynopisu, etap po etapie. Każdy etap wykonuje rój agentów, z obowiązkową redakcją na naturalną polszczyznę (unslop), a od momentu pisania prozy ze wspólnym fundamentem — **biblią książki** (`${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md`).

Status: ✅ gotowe · 🔜 planowane.

| # | Polecenie | Status | Cel | Rola biblii |
| --- | --- | --- | --- | --- |
| 1 | `market-report` | ✅ | Luki rynkowe + zwycięski pomysł (raport HTML) | — |
| 1L | `idea-spark` | ✅ | Autorski wariant etapu 1: autor projektuje trzon (kierunek/bohaterowie/świat), rój generuje 5 wariantów fabuły, bez badania rynku (ten sam `.book-forge/pomysl.json`) | — |
| 2 | `outline` | ✅ | Konspekt rozdział po rozdziale (`.book-forge/konspekt.md`) | — |
| 3 | `book-bible` | ✅ | Jedno źródło prawdy ZANIM padnie pierwsze zdanie prozy | **tworzy** całość |
| 4 | `opening` | ✅ | Mocny początek: 3 warianty pierwszej sceny | czyta wszystko; proponuje runtime |
| 5 | `outline-to-scenes` | ✅ | Przepisać konspekt na siatkę scen (cel→konflikt→zwrot) | czyta postacie/POV/świat; pisze siatkę, oś czasu, zasiewy i wypłaty |
| 6 | `world-research` | ✅ | Doprecyzować realia przez agent-browser, na żądanie z luk scen | czyta świat/glosariusz; pisze zweryfikowane fakty z cytowaniem |
| 7 | `write-scene` | ✅ | Napisać pojedynczą scenę wg karty (sekwencyjnie) | czyta głosy/świat/zasiewy/streszczenia; tylko proponuje |
| 7–10T | `forge-scenes` | ✅ | Tryb taśmowy pętli scen: pytania raz, potem write→revise→continuity→polish dla N scen | nie pisze sam — bramki w wołanych etapach |
| 8 | `revise-scene` | ✅ | Pogłębienie prozą + redakcja developmentalna (generuj→oceń) | czyta kanon fabularny, stawkę, łuki; notatka QA |
| 9 | `continuity-check` | ✅ | Bramka spójności (jedyny write-back do kanonu w pętli prozy) | czyta wszystko; **pisze** runtime + streszczenie sceny |
| 10 | `polish-pl` | ✅ | Unslop (zakotwiczony stylem) → korekta PL + walidacja nazw | czyta kartę stylu i glosariusz |
| 11 | `assemble-book` | ✅ | Złożyć sceny w rozdziały i książkę; przeglądy całości (domknięcie łuku, wypłata zasiewów, tempo); arkusze wydawnicze, echo-hunter, work-lista `redakcja-todo.md` | czyta zasiewy i wypłaty, oś czasu, motyw, streszczenia |
| 12 | `publishing-package` | ✅ | Pakiet sprzedażowy: logline, pitch, synopsis, list do agenta | czyta meta/postacie/stawkę |

## 🔜 Planowane (z audytu 2026-06)

Pomysły zatwierdzone kierunkowo, odłożone za czołówkę — w kolejności oceny panelu sędziów:

| Pomysł | Cel |
| --- | --- |
| Trwały ładunek handoffu (`<id>.propozycje.json`) | Propozycje kanonu odporne na utratę sesji między sceną a bramką; bramka kasuje plik po write-backu |
| `export-manuscript` | Eksport `ksiazka.md` do DOCX (standard maszynopisu wydawniczego) i EPUB przez pandoc |
| `voice-audit` | Siódmy wymiar przeglądu całości: dryf głosu narratora między scenami (odcisk statystyczny + próbki prozy) |
| `revise-chapter` | Rewizja na poziomie rozdziału sterowana raportem z `assemble-book` (mapowanie problemów całości na sceny) |
| `beta-read` | Symulacja beta-czytelników na pełnej prozie (persony, krzywa napięcia, ryzyko DNF) — etap 11.5 |
| Wersjonowanie spec kanonu + `bible.py migrate` | Migracja biblii książki w połowie pipeline'u po aktualizacji pluginu |
| `import-manuscript` | Wejście do pipeline'u z istniejącym rękopisem (dekompozycja na sceny + reverse-engineering biblii) |
| Tiering modeli w rojach | Tańsze modele dla zadań mechanicznych (ekstrakcja, walidacja), drogie tylko dla prozy |

## Zasady projektowe etapów pisania

Wynikają z analizy wielu perspektyw (pisarz, redaktor prowadzący, redaktor językowy, czytelnik, agent literacki, strażnik kanonu, architekt narzędzia) i z przebiegu adwersaryjnego:

- **Jednostką jest SCENA, nie rozdział-esej:** cel postaci → konflikt → zwrot (zmiana wartości). Przemianę przechodzi **bohater** (rana → kłamstwo → zmiana), nie „czytelnik”.
- **Głos = narrator + idiolekty postaci**, nie „głos autora”. Jeden ton dla wszystkich spłaszcza obsadę.
- **Bez wstrzykiwania anegdot/statystyk i zwrotów „stop and think”** — to wytrąca czytelnika z lektury. Scenę wzmacnia się środkami prozy (podtekst, charakteryzacja przez działanie, detal sensoryczny, mikrozwrot, zasiew). Research świata trafia do biblii z cytowaniem, nie do prozy.
- **Bez sztywnych metryk** („co N słów”, „cliffhanger co rozdział”, reguła trójki) — generują schematyczność, którą unslop ma usuwać.
- **Pola RO i RUNTIME** w biblii — bramka ciągłości waliduje ustalenia (CONFLICT), a zapisuje tylko stan bieżący. To jedyne miejsce zapisu do kanonu.
- **Proza sekwencyjna** (scena N widzi N-1); rój do researchu, krytyki i wariantów. Równolegle pisze się tylko sceny niezależne („frozen prefix”).
- **Mikrokolejność redakcji:** unslop NAJPIERW (zakotwiczony kartą stylu), potem korekta polonistyczna i walidacja glosariusza oraz nazw OSTATNIA (unslop nie psuje odmiany nazw ani interpunkcji dialogowej).
- **Limit iteracji i eskalacja:** po N nieudanych próbach — eskalacja do autora albo `accept-with-debt` z wpisem w logu QA (nigdy cicha, nieskończona pętla).

## Kryteria bramki redakcyjnej (fabularne, nie eseistyczne)

Cel i zwrot sceny, rosnąca stawka, sprawczość bohatera (działa, nie tylko reaguje), podtekst dialogu, spójność punktu widzenia i czasu, „pokazuj, nie opowiadaj”, brak przeładowania informacjami, rozróżnialność głosów postaci, tempo. Bramka działa jako PASS/FIX, nie jako luźna porada.
