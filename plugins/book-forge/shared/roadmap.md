# book-forge — pipeline i planowane etapy

Plugin prowadzi autora od pomysłu do gotowego maszynopisu, etap po etapie. Każdy etap wykonuje rój agentów, z obowiązkową redakcją na naturalną polszczyznę (humanizer), a od momentu pisania prozy ze wspólnym fundamentem — **biblią książki** (`${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md`).

Status: ✅ gotowe · 🔜 planowane.

| # | Polecenie | Status | Cel | Rola biblii |
| --- | --- | --- | --- | --- |
| 1 | `market-report` | ✅ | Luki rynkowe + zwycięski pomysł (raport HTML) | — |
| 1L | `idea-spark` | ✅ | Lekki wariant etapu 1: 5 pomysłów z kwestionariusza, bez badania rynku (ten sam `.book-forge/pomysl.json`) | — |
| 2 | `outline` | ✅ | Konspekt rozdział po rozdziale (`.book-forge/konspekt.md`) | — |
| 3 | `book-bible` | ✅ | Jedno źródło prawdy ZANIM padnie pierwsze zdanie prozy | **tworzy** całość |
| 4 | `opening` | ✅ | Mocny początek: 3 warianty pierwszej sceny | czyta wszystko; proponuje runtime |
| 5 | `outline-to-scenes` | ✅ | Przepisać konspekt na siatkę scen (cel→konflikt→zwrot) | czyta postacie/POV/świat; pisze siatkę, oś czasu, zasiewy i wypłaty |
| 6 | `world-research` | ✅ | Doprecyzować realia przez agent-browser, na żądanie z luk scen | czyta świat/glosariusz; pisze zweryfikowane fakty z cytowaniem |
| 7 | `write-scene` | ✅ | Napisać pojedynczą scenę wg karty (sekwencyjnie) | czyta głosy/świat/zasiewy; tylko proponuje |
| 8 | `revise-scene` | ✅ | Pogłębienie prozą + redakcja developmentalna (generuj→oceń) | czyta kanon fabularny, stawkę, łuki; notatka QA |
| 9 | `continuity-check` | ✅ | Bramka spójności (jedyny write-back do kanonu) | czyta wszystko; **pisze** runtime |
| 10 | `polish-pl` | ✅ | Humanizer (zakotwiczony stylem) → korekta PL + walidacja nazw | czyta kartę stylu i glosariusz |
| 11 | `assemble-book` | ✅ | Złożyć sceny w rozdziały i książkę; przeglądy całości (domknięcie łuku, wypłata zasiewów, tempo) | czyta zasiewy i wypłaty, oś czasu, motyw |
| 12 | `publishing-package` | ✅ | Pakiet sprzedażowy: logline, pitch, synopsis, list do agenta | czyta meta/postacie/stawkę |

## Zasady projektowe etapów pisania

Wynikają z analizy wielu perspektyw (pisarz, redaktor prowadzący, redaktor językowy, czytelnik, agent literacki, strażnik kanonu, architekt narzędzia) i z przebiegu adwersaryjnego:

- **Jednostką jest SCENA, nie rozdział-esej:** cel postaci → konflikt → zwrot (zmiana wartości). Przemianę przechodzi **bohater** (rana → kłamstwo → zmiana), nie „czytelnik”.
- **Głos = narrator + idiolekty postaci**, nie „głos autora”. Jeden ton dla wszystkich spłaszcza obsadę.
- **Bez wstrzykiwania anegdot/statystyk i zwrotów „stop and think”** — to wytrąca czytelnika z lektury. Scenę wzmacnia się środkami prozy (podtekst, charakteryzacja przez działanie, detal sensoryczny, mikrozwrot, zasiew). Research świata trafia do biblii z cytowaniem, nie do prozy.
- **Bez sztywnych metryk** („co N słów”, „cliffhanger co rozdział”, reguła trójki) — generują schematyczność, którą humanizer ma usuwać.
- **Pola RO i RUNTIME** w biblii — bramka ciągłości waliduje ustalenia (CONFLICT), a zapisuje tylko stan bieżący. To jedyne miejsce zapisu do kanonu.
- **Proza sekwencyjna** (scena N widzi N-1); rój do researchu, krytyki i wariantów. Równolegle pisze się tylko sceny niezależne („frozen prefix”).
- **Mikrokolejność redakcji:** humanizer NAJPIERW (zakotwiczony kartą stylu), potem korekta polonistyczna i walidacja glosariusza oraz nazw OSTATNIA (humanizer nie psuje odmiany nazw ani interpunkcji dialogowej).
- **Limit iteracji i eskalacja:** po N nieudanych próbach — eskalacja do autora albo `accept-with-debt` z wpisem w logu QA (nigdy cicha, nieskończona pętla).

## Kryteria bramki redakcyjnej (fabularne, nie eseistyczne)

Cel i zwrot sceny, rosnąca stawka, sprawczość bohatera (działa, nie tylko reaguje), podtekst dialogu, spójność punktu widzenia i czasu, „pokazuj, nie opowiadaj”, brak przeładowania informacjami, rozróżnialność głosów postaci, tempo. Bramka działa jako PASS/FIX, nie jako luźna porada.
