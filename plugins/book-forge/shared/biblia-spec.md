# Biblia książki — wspólny stan projektu (spec)

Biblia to **jedno źródło prawdy** o powieści. Każdy etap pisania ją czyta, dzięki czemu agent zawsze ma pełny kontekst, a całość „trzyma się kupy”: świat, postacie, nazewnictwo, głos i fakty są spójne od pierwszej do ostatniej strony (i między tomami).

## Zdekomponowany kanon-wiki (źródło prawdy = markdown)

Kanon to **drzewo plików `.book-forge/biblia/**/*.md`** — wzorzec „LLM wiki”: jedna encja (postać, lokacja, nazwa własna, głos) = jeden plik, listy rekordów (sceny, oś czasu, fakty, zasiewy, źródła) = jeden agregat. Strony encji i sekcji są **frontmatter-only**: cała treść siedzi w **kompaktowym JSON** między liniami `---`, a edytory (Obsidian, VS Code) renderują ten frontmatter jako tabelę właściwości. Pełną treść markdown mają tylko dwie strony: `.book-forge/biblia/index.md` (katalog wszystkich stron, generowany) i `.book-forge/biblia/log.md` (kronika ciągłości, tylko dopisy).

- **Źródłem prawdy jest frontmatter stron `.md`**, nie żaden pojedynczy plik.
- **Całe I/O przechodzi przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`** (stdlib-only, bez pyyaml). Żaden skill nie czyta/pisze plików `.book-forge/biblia/` inline — to gwarantuje, że reguła RO→CONFLICT nie ma dziur. `bible.load_all()` skleja drzewo w jeden obiekt (17 sekcji, kształt niżej), więc skille czytające biorą cały kanon jednym wywołaniem, a logika wyciągów zostaje bez zmian.
- **Frontmatter zapisywany jest jako `json.dumps(..., ensure_ascii=False, indent=2, sort_keys=True)`** — wieloliniowy i deterministyczny, więc git-diff pokazuje zmianę pojedynczego pola jako jedną linię.

## Zasada uprawnień (klucz do spójności)

Rozdziel pola jak w bazie danych:

- **RO (ustalone z góry, tylko do odczytu)** — zapisane na etapie biblii: POV, czas gramatyczny, opis fizyczny postaci, łuki, zasady świata, motyw, kanoniczne nazwy i ich odmiana. Bramka ciągłości przy rozbieżności **zgłasza CONFLICT, a NIE nadpisuje**. Gwarancja RO stoi na trzech filarach bibliotecznych (nie na dyscyplinie skryptu): (1) `bible.update_runtime` — próba zmiany pola spoza whitelisty RUNTIME zwraca `CONFLICT` i niczego nie zapisuje; (2) encje `_inherited` z zamkniętych tomów serii → `write_entity` zwraca `INHERITED_RO` (pola RO twardo nietykalne; pola RUNTIME idą przez copy-on-write w `update_runtime` — patrz „Tryb serii”); (3) `bible.ro_snapshot()` + `bible.assert_ro_unchanged(before)` — bramka ciągłości robi snapshot pól RO przed write-backiem i po nim rzuca, gdyby cokolwiek RO drgnęło. `write_entity(ro_guard=False)` i `write_section` to świadomy autorski override (np. seedowanie kanonu w `book-bible`), nie luka — każde przypadkowe ruszenie RO wychwytuje filar (3).
- **RUNTIME (rośnie w trakcie pisania)** — stan bieżący: lokalizacja postaci (`_stan` postaci), oś czasu, status zasiewów, nowe fakty, nowe nazwy, log ciągłości. Tu dozwolony jest zapis (write-back) — **w pętli prozy wyłącznie przez bramkę ciągłości** (jedyny etap prozy z prawem zapisu; etapy planowania/przeglądu — book-bible, outline-to-scenes, world-research, assemble-book — mają własne, wąskie uprawnienia zapisu poza pętlą prozy).

Etapy pisania (write-scene, revise-scene, opening) **tylko czytają i proponują** dopisy. Nie zapisują same — inaczej błąd surowej sceny natychmiast stałby się „prawdą”.

## Kanon working a kanon published

- `kanon: "working"` — notatki robocze w trakcie pisania tomu.
- `kanon: "published"` — zamrożony, przenośny do kolejnego tomu. Fakty z tomu 1 są wtedy nienaruszalne dla tomu 2 (czytelnik fantastyki naukowej wyłapie sprzeczność między tomami).

## Tryb serii / wiele tomów

**Inwariant:** projekt z jednym tomem (brak `.book-forge/seria.md`) działa płasko — pliki robocze (proza, JSON, biblia) chowają się do ukrytego `.book-forge/`, a w korzeniu zostaje tylko to, co dla człowieka (prezentacyjne `*.html` + finalny `ksiazka.md`/`pakiet.md`); ID scen `R1S1`. Tryb serii włącza się TYLKO, gdy istnieje `.book-forge/seria.md`. Wszystkie poniższe mechanizmy są dla `meta.tomy==1` (lub braku `.book-forge/seria.md`) wyłączone — zero zmian dla pojedynczej książki.

**Stan serii — `.book-forge/seria.md` w korzeniu projektu** (PONAD biblią tomu, bo łuk serii musi być widoczny z każdego tomu). Frontmatter-only, RO poza `tom_aktywny`; I/O przez `bible.read_series()` / `bible.write_series()`:

```json
{ "RO": true, "tytul_serii": "", "tomy": 3, "tom_aktywny": 1,
  "obietnica_serii": "", "luk_nadrzedny": { "want_serii": "", "need_serii": "", "etapy_po_tomach": [] },
  "zasiewy_miedzytomowe": [ { "id": "SS01", "opis": "", "tom_zasiewu": 1, "tom_splaty": 3, "status": "otwarty" } ],
  "tomy_meta": [ { "nr": 1, "logline": "", "rola_w_serii": "" } ] }
```

`tom_aktywny` to jedyne pole RUNTIME (przełącza je autor, zaczynając nowy tom).

**Układ katalogu i namespace per tom.** Artefakty dzielą się na trzy warstwy:
- **dla człowieka** — korzeń tomu (`BOOK_DIR`): prezentacyjne `*.html` + finalny `ksiazka.md` i `pakiet.md`;
- **robocze** — ukryty `WORK = ${BOOK_DIR}.book-forge/`: `pomysl.json`, `konspekt.md`, `poczatek.md`, `sceny/<id>.md`, `*.qa.md`, `korekta-<id>.md` oraz pliki pośrednie (`*_JSON` wstrzykiwane do HTML — trzymaj je w `.book-forge/` lub `$TMPDIR`, nigdy w korzeniu);
- **kanon** — `BIBLE_DIR = ${WORK}biblia`.

Pojedyncza książka (wartości domyślne, zero eksportów): `BOOK_DIR=""`, `WORK=.book-forge/`, `BIBLE_DIR=.book-forge/biblia`. Tryb serii: każdy skill ustawia `BOOK_DIR=tom-NN/`, `WORK=tom-NN/.book-forge/`, `BIBLE_DIR=tom-NN/.book-forge/biblia` (z `tom_aktywny`); `.book-forge/seria.md` zostaje jeden, w korzeniu projektu (ponad tomami). Skrypty liczą ścieżki przez helpery `bible.book_path(...)` / `bible.work_path(...)`, więc reagują na te zmienne automatycznie.

**ID scen unikalne między tomami.** Tom 1 / pojedyncza książka: `R1S1` (bez prefiksu — wstecznie zgodne). Tom N>1: `T<N>R<r>S<s>` (np. `T2R1S1`). ID nadaje `outline-to-scenes`; wszyscy konsumenci (`os_czasu.scena`, `setup_payoff.scena_*`, `log_ciaglosci.scena`, `set_scene_field`) używają pełnego stringa, więc działają bez zmian.

**Dziedziczenie kanonu (`_dziedziczone/`).** Po zamrożeniu tomu N (`freeze_canon(True)`) kolejny tom woła `bible.import_published(<biblia_tomu_N>)`, co kopiuje published-strony poprzednika do `tom-(N+1)/.book-forge/biblia/_dziedziczone/` z flagą `"_inherited": true`. `load_all()` tomu N+1 nakłada tę warstwę pod spód (own-wins: encja własna przesłania dziedziczoną; brakujące fakty świata/postaci/glosariusza są widoczne dla wyciągów do prozy). `import_published` odmawia, gdy poprzednik nie jest `published` (fail loud — nie dziedziczymy roboczego kanonu).

**RO zamkniętego tomu, RUNTIME przez copy-on-write.** Pola RO encji z `"_inherited": true` są twardo nietykalne: `write_entity` na dziedziczonej encji zwraca `{"status": "INHERITED_RO"}` i nic nie zapisuje (gwarancja w bibliotece, nie w dyscyplinie skryptu). Tom N+1 może odwołać się do postaci z tomu N, ale nie zmieni jej `opis_fizyczny`/`luk`/`odmiana`. Pola RUNTIME (`_stan`) podlegają natomiast **copy-on-write**: `update_runtime` materializuje stronę do warstwy własnej tomu (pola RO skopiowane verbatim, bez `_inherited`) i dopiero wtedy patchuje — bohater kontynuujący serię może zmienić lokalizację czy postęp łuku, a own-wins z `load_all()` przesłania warstwę dziedziczoną. Warstwa `_dziedziczone/` zostaje nietknięta (snapshot poprzedniego tomu).

**Łuk serii vs łuk tomu.** `luk_nadrzedny` i `zasiewy_miedzytomowe` żyją w `.book-forge/seria.md`, nie w bibli tomu. Etapy narracyjne rozróżniają **zasiew tomu** (`setup_payoff` w bibli — MUSI domknąć się w tomie) od **zasiewu serii** (`.book-forge/seria.md` — wolno zostawić otwarty, jeśli `tom_splaty > tom_aktywny`). `assemble-book` nie raportuje otwartego zasiewu serii jako luki gotowości.

## Kształt kanonu (17 sekcji)

Poniższy obiekt to **kształt w pamięci**, jaki odtwarza `bible.load_all()`. Fizycznie kanon jest rozłożony na pliki wg tabeli „Mapowanie sekcja → plik”.

```json
{
  "kanon": "working",
  "meta":        { "RO": true, "tytul":"", "subgatunek":"", "logline":"", "target":"", "comps":[], "pov":"", "czas":"", "tomy":1, "ton":"", "format":"pojedyncza", "forma":"", "budzet_slow":0, "liczba_scen":0 },
  "swiat":       { "RO": true, "lokacje":[{"nazwa":"","opis":""}], "zasady":[{"zasada":"","koszt":"","ograniczenie":""}], "technologia":[], "konsekwencje":"" },
  "postacie":    [ { "imie":"", "odmiana":"(RO) D./C./B./N./Ms.", "rola":"", "opis_fizyczny":"(RO)", "maniery":"", "want":"", "need":"", "rana":"", "klamstwo":"", "luk":"(RO) plan przemiany", "relacje":[], "glos_ref":"",
                     "chaos": { "obsesja":"", "znieksztalcenie":"", "wspomnienie":"", "kontrola":"" },
                     "_stan": { "RUNTIME": true, "lokalizacja":"", "stan":"", "postep_luku":"" } } ],
  "antagonista": { "RO": true, "profil":"", "cel":"", "motywacja":"", "plan":[], "przewaga":"" },
  "stawka":      { "RO": true, "osobista":"", "globalna":"", "zegar":"" },
  "glos_narratora": { "RO": true, "pov":"", "czas":"", "rytm":"", "rejestr":"", "zwroty":[], "metafory":"", "czego_unikac":[] },
  "glosy_postaci":  [ { "postac":"", "rejestr":"", "tiki":[], "rytm":"", "slownictwo":"" } ],
  "glosariusz":  [ { "nazwa":"", "kategoria":"planeta|frakcja|technologia|tytul|imie", "odmiana":{"M":"","D":"","C":"","B":"","N":"","Ms":"","W":""}, "warianty_zakazane":[], "opis":"" } ],
  "kanon_fabularny": { "RO": true, "rozdzialy":[{"nr":1,"tytul":""}], "beaty":["incydent inicjujacy","prog I aktu","midpoint","czarna chwila","kulminacja","rozwiazanie"], "sceny":[{"id":"R1S1","rozdzial":1,"pov":"","cel":"","konflikt":"","zwrot":"","value":"+/-","typ":"kluczowa|pomostowa|sekwel","research":[],"status":"planowana"}] },
  "os_czasu":    [ { "RUNTIME": true, "scena":"R1S1", "dzien_fabularny":"", "kolejnosc":1 } ],
  "streszczenia":[ { "RUNTIME": true, "scena":"R1S1", "streszczenie":"3-5 zdań: fakty fabularne + stan postaci na koniec sceny", "slowa":0, "hash":"sha256[:12] prozy" } ],
  "setup_payoff":[ { "RUNTIME": true, "id":"SP01", "opis":"", "typ":"glowny|poboczny|strzelba", "scena_zasiewu":"", "scena_splaty":"", "status":"otwarty|domkniety" } ],
  "fakty":       [ { "RUNTIME": true, "id":"F01", "tresc":"", "typ":"swiat|postac|relacja|zdarzenie", "zrodlo_scena":"", "pewnosc":"kanon|roboczy", "zrodlo_ref":"" } ],
  "zrodla":      [ { "RUNTIME": true, "id":"Z01", "dotyczy":"F01 lub nazwa zasady", "zrodlo":"", "url":"", "data":"", "notatka":"" } ],
  "temat":       { "RO": true, "temat":"", "pytanie_dramatyczne":"", "motywy":[] },
  "log_ciaglosci":[ { "RUNTIME": true, "scena":"", "werdykt":"PASS|CONFLICT|FIX", "sprzecznosci":"", "decyzja":"" } ]
}
```

> **`meta` jest RO z dwoma wyjątkami RUNTIME:** `budzet_slow` i `liczba_scen` pisze `outline-to-scenes` po `write_scene_grid` przez `update_meta` (patrz API) — to producent budżetu słów konsumowanego przez `write-scene`. `meta.forma` (non-fiction: poradnik/reportaż/esej/pamiętnik; `""` = fikcja) jest RO — seeduje ją `book-bible` z briefu i czytają etapy prozy jako guard non-fiction.

> **`chaos` postaci jest opcjonalny i RO** — cztery markery ludzkiej nieprzewidywalności (`obsesja` = nieistotna obsesja; `znieksztalcenie` = zniekształcenie poznawcze; `wspomnienie` = niechciane wspomnienie; `kontrola` = nieudana kontrola emocji). Seeduje je `book-bible` (skalowane gatunkiem; non-fiction pomija), a konsumuje je `revise-scene` (faza Disruption) i opcjonalnie `write-scene`. Jako pole RO (poza `_stan`) jest objęte `ro_snapshot`/`assert_ro_unchanged` jak `luk` — proza go nie nadpisuje.

> **`beaty` to lista OTWARTA, zależna od wybranej struktury narracyjnej** (trójakt, struktura 7 punktów, Save the Cat, kishōtenketsu…), nie sztywny trójakt. Powyższy trójaktowy zestaw to tylko domyślny przykład. Strukturę wybiera `outline` (pole `structureName`), `book-bible` zapisuje `rozdzialy`+`beaty` z konspektu, a `outline-to-scenes` mapuje sceny na beaty TEJ struktury (nie wciska trójaktu w kishōtenketsu). `typ` sceny (`kluczowa|pomostowa|sekwel`) steruje kryteriami dev-edit (scena pomostowa nie wymaga pełnego zwrotu wartości).

## Mapowanie sekcja → plik

Encja (ma nazwę, tożsamość, prozę, jest celem wikilinku `[[slug]]`) dostaje osobny plik (czysty diff/blame, tani odczyt). Lista jednorodnych rekordów zostaje zagregowana w jednym pliku (czytana i modyfikowana hurtem).

| Sekcja | Plik(i) | Typ |
| --- | --- | --- |
| `kanon` (working/published) | `index.md` (frontmatter) | skalar |
| `meta`, `temat`, `stawka`, `antagonista`, `glos_narratora` | `meta.md`, `temat.md`, `stawka.md`, `antagonista.md`, `glos_narratora.md` | singletony RO |
| `swiat` (zasady/technologia/konsekwencje) | `swiat/_swiat.md` | agregat RO |
| `swiat.lokacje[]` | `swiat/<slug>.md` | encje RO |
| `postacie[]` (RO + zagnieżdżony `_stan` RUNTIME) | `postacie/<slug>.md` | encje |
| `glosy_postaci[]` | `glosy/<slug>.md` | encje RO |
| `glosariusz[]` | `glosariusz/<slug>.md` | encje RO |
| `kanon_fabularny` (rozdzialy, beaty, sceny[]) | `fabula/sceny.md` | agregat RO (status sceny = RUNTIME) |
| `os_czasu[]`, `streszczenia[]`, `setup_payoff[]`, `fakty[]`, `zrodla[]` | `fabula/os-czasu.md`, `fabula/streszczenia.md`, `fabula/zasiewy.md`, `fabula/fakty.md`, `fabula/zrodla.md` | agregaty RUNTIME |
| `log_ciaglosci[]` | `log.md` | kronika (tylko dopisy) |

Slug liczony jest z **mianownika** nazwy (transliteracja: ł→l, ż→z, ą→a…), więc jest stabilny mimo polskiej odmiany. Wikilinki: `[[postacie/kalina|Kalinę]]` — target to slug, etykieta może być odmieniona. **Uwaga:** `.book-forge/biblia/fabula/sceny.md` to KARTY scen (kanon); katalog `.book-forge/sceny/<id>.md` to PROZA robocza — to dwa różne miejsca.

**Dowiązanie otwarcia (`proza_zrodlo`).** Karta sceny może mieć opcjonalne pole `proza_zrodlo` (np. `".book-forge/poczatek.md"`) wskazujące gotową prozę otwarcia napisaną na etapie `opening`. Ustawia je etap planowania `outline-to-scenes` (biegnie po `opening`, więc `.book-forge/poczatek.md` już istnieje) na karcie sceny otwierającej. `write-scene` traktuje je jako **obowiązkowy materiał do rozwinięcia** (rozwija otwarcie do docelowej długości w tym samym głosie, nie pisze sceny od zera) — i tylko CZYTA, zgodnie z zasadą „etapy prozy nie zapisują kanonu”. To pole karty (jak `status`), więc patchuje je `set_scene_field` (wyjątek od RO-guarda agregatu).

## API `scripts/bible.py` (jedyne wejście do kanonu)

- `load_all()` → obiekt kanonu (kształt jak wyżej). Skille czytające: `b = bible.load_all()`. **Zwraca tylko sekcje fizycznie obecne** (na wczesnych etapach kanon bywa częściowy) — konsument ZAWSZE używa `b.get('sekcja', domyślne)`, nie zakłada obecności klucza. W trybie serii skleja też warstwę `_dziedziczone/` (own-wins). Uszkodzona/urwana strona → `load_all` rzuca (fail loud), nie zwraca cichej pustki.
- `read_section(name)`, `read_entity(kind, name_or_slug)`, `list_entities(kind)` — odczyt granularny do wyciągów.
- `write_entity(kind, data, body=None, ro_guard=True)` — atomowy zapis encji; scala bez nadpisywania pól RO, realny konflikt → `conflicts`. Dwie różne nazwy mapujące się na ten sam slug → `{"status":"SLUG_COLLISION"}` (cicha utrata danych zablokowana; nadaj `_slug`). Encja `_inherited` → `INHERITED_RO`.
- `ro_snapshot()` / `assert_ro_unchanged(before)` — audyt pól RO przed/po write-backu (filar 3 gwarancji RO); woła je bramka ciągłości.
- `update_runtime(kind, name, field, value)` — patch tylko pól RUNTIME (np. `_stan.lokalizacja`); pole RO → `{"status":"CONFLICT"}` bez zapisu. Encja `_inherited` → copy-on-write (materializacja strony własnej, w wyniku `"zmaterializowano": true`).
- `append_record(section, record, dedup_keys=None)` — append do agregatu z dedup + auto-id (`new_id`): `fakty`→F, `zrodla`→Z, `setup_payoff`→SP. `streszczenia` deduplikują po `scena` (update-or-append — ponowna bramka po rewizji aktualizuje wpis, nie dubluje); `hash` to `sha256(prozy)[:12]` — konsument porównuje go z aktualną prozą i przy rozjeździe (np. po `polish-pl`) traktuje streszczenie jako nieaktualne.
- `update_meta(field, value)` — patch pojedynczego pola RUNTIME singletonu `meta` (whitelist: `budzet_slow`, `liczba_scen`; producent: `outline-to-scenes` po `write_scene_grid`). Pole RO → `{"status":"CONFLICT"}`; brak `meta.md` → `MISS`. Read-modify-write — nie clobberuje reszty meta (w przeciwieństwie do `write_section`).
- `set_scene_field(scene_id, field, value)` / `set_scene_status(scene_id, status)`, `write_scene_grid(rozdzialy, beaty, sceny, force=False)` — maszyna stanu scen (`set_scene_field` patchuje dowolne pole karty, np. `proza_zrodlo`; `set_scene_status` to jego skrót dla `status`).
- `append_log(entry)` — dopisuje wpis do `log.md` (nigdy nie przepisuje historii).
- `render_index()` — regeneruje `index.md` (następca regeneracji `biblia.md`; wołaj po każdym zapisie).
- `freeze_canon(published=True)` — working→published (i z powrotem). Dla pojedynczej książki to jeden skalar w `index.md`.
- `read_series()` / `write_series(data)` — stan serii z `.book-forge/seria.md` (brak pliku ⇒ `None` ⇒ tryb pojedynczy).
- `import_published(prev_bible_dir)` — kopiuje published-kanon poprzedniego tomu do `BIBLE_DIR/_dziedziczone/` jako warstwę RO (`_inherited`); odmawia, gdy poprzednik nie jest `published`. Patrz „Tryb serii".
- `check_stage(etap, scena=None)` — deterministyczny preflight WEJŚCIA etapu (czy artefakty poprzednich etapów istnieją i są kompletne) — skill woła go ZANIM uruchomi drogi rój. Zwraca `{"ok", "etap", "braki"}`.
- `book_status()` — dashboard projektu (czysty odczyt): sceny wg statusu (w tym de facto „wygładzona" = istnieje `korekta-<id>.md`), słowa vs `meta.budzet_slow`, otwarte zasiewy, sceny bez wpisu w logu, ostatnie werdykty.
- CLI: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bible.py {validate|render-index|dump|freeze|import-published <kat>|series|check-stage <etap> [<id>]|status [--json]}` — `validate` zwraca raport `OK, brak luk` / `LUKI:`; `check-stage` zwraca JSON i exit 1 przy brakach (bramka); `status` to dashboard (exit zawsze 0).

## Anty-dryf (przy 90–120 tys. słów)

1. **Wstrzykiwanie ważone trafnością** — do promptu sceny NIE wklejaj całego tekstu, tylko wyciąg: karta POV, głosy obecnych postaci, zasady świata istotne dla scenerii, glosariusz, otwarte zasiewy, streszczenia 2–3 poprzednich scen. Streszczenia bierz z agregatu `streszczenia` w kanonie (pisze je bramka ciągłości po werdykcie), nie streszczaj prozy od nowa — to ten sam tekst widziany przez wszystkich konsumentów i zero powtórnego kosztu.
2. **Sekwencyjność prozy** — proza powstaje SEKWENCYJNIE (scena N widzi wynik N-1). Rój agentów służy do researchu, krytyki i wariantów, nie do równoległego pisania sprzecznych scen. Równolegle wolno pisać tylko sceny niezależne (bez wspólnych otwartych zasiewów i faktów — na „zamrożonym wstępie”).
3. **Audyt zbiorczy** co 10–15 tys. słów ponad pojedynczą sceną — wychwytuje kumulujący się dryf chronologii i osierocone wątki.

## Glosariusz: ochrona nazw własnych

Każda nazwa ma gotową **polską odmianę przez przypadki** i listę **wariantów zakazanych**. To najtańsza ochrona przed tym, że „Arrakis” odmieni się inaczej w rozdziale 1 i 12, oraz przed tym, że humanizer „poprawi” nazwę własną. Glosariusz i czarna lista AI-izmów (z `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`) są wspólne dla wszystkich agentów i dla humanizera.

## Kolejność redakcji per scena (ważne)

1. treść → 2. pogłębienie → 3. redakcja developmentalna → 3b. **disruption** (anty-przewidywalność, po PASS dev-edit, na zaakceptowanej prozie — poza zasięgiem dev-edit; wyłączona dla non-fiction) → 4. **kontrola ciągłości** (jedyny zapis do kanonu) → 5. **humanizer** (zakotwiczony kartą stylu/głosu) → 6. **finalna korekta polonistyczna + walidacja glosariusza/nazw** (ostatnia, by humanizer nie zepsuł odmiany nazw ani interpunkcji dialogowej).

Faza disruption (3b) zwraca listę `celowe_odstepstwa` — fragmenty celowej szorstkości, niesione przez `.book-forge/sceny/<id>.qa.md` aż do kroków 5–6, by humanizer i korekta ich NIE cofnęły (mają przeciwny wektor: wygładzają, a disruption celowo wprowadza tarcie).

Twardy **limit iteracji**: jeśli scena nie przechodzi po N próbach (np. 3) → eskalacja do autora albo `accept-with-debt` z wpisem w `log_ciaglosci` (nigdy cicha, nieskończona pętla).
