# Budowa kanonu-wiki i walidacja

Kanon to **drzewo `.book-forge/biblia/**/*.md`** (frontmatter JSON + treść), nie pojedynczy plik. Całe I/O przez **`${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`**. Pełny kształt i mapowanie sekcja→plik: `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md`.

## Tryb serii (gdy autor pisze serię — `meta.tomy > 1`)

Pełny model: `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md` → „Tryb serii". Dla book-bible konkretnie:

Gdy `format`/`tomy` z briefu (etap 1) wskazują serię, utwórz `.book-forge/seria.md` (stan serii ponad tomami) i ustaw aktywny tom (na starcie 1), a kanon buduj w `tom-NN/.book-forge/biblia` (kod od kolumny 0 — heredoc zachowuje wcięcia):

```bash
export BOOK_DIR="tom-01/"                      # korzeń tomu (HTML + ksiazka.md/pakiet.md)
export WORK="tom-01/.book-forge/"              # pliki robocze tomu (konspekt/poczatek/sceny/biblia)
export BIBLE_DIR="tom-01/.book-forge/biblia"   # kanon tomu wg .book-forge/seria.md → tom_aktywny
python3 - "$PLUGIN_ROOT" << 'PY'
import sys, os; sys.path.insert(0, os.path.join(sys.argv[1],"scripts")); import bible
if bible.read_series() is None:
    bible.write_series({"RO": True, "tytul_serii": "", "tomy": 3, "tom_aktywny": 1,
                        "obietnica_serii": "", "luk_nadrzedny": {"want_serii":"","need_serii":"","etapy_po_tomach":[]},
                        "zasiewy_miedzytomowe": [], "tomy_meta": []})
print(".book-forge/seria.md gotowe; tom aktywny:", (bible.read_series() or {}).get("tom_aktywny"))
PY
```

Dla tomu 2+: zanim zbudujesz kanon, zaimportuj published-kanon poprzednika jako warstwę RO: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bible.py import-published tom-01/.book-forge/biblia` (wymaga, by poprzedni tom był zamrożony — `freeze` na etapie assemble-book).

**Pojedyncza książka:** pomiń tę sekcję — `BIBLE_DIR=.book-forge/biblia`, `WORK=.book-forge/`, `BOOK_DIR` pusty (wartości domyślne, zero eksportów).

## Złożenie kanonu z wyniku roju

Wynik roju (świat, postacie, antagonista, stawka, głosy, glosariusz, temat) zapisz przez bibliotekę. Najpierw zrzuć surowy obiekt roju do pliku tymczasowego (żeby nie psuć cudzysłowów), potem rozłóż go na strony.

> **Obiekt wejściowy `r` to wynik roju PLUS dane spoza roju**, które musisz dołączyć z Kroku 1: `r["idea"]` (zwycięski pomysł z etapu 1), `r["brief"]` (`DATA.brief`: format, ton, spice, protagonist…), `r["reader"]`, oraz `r["meta"]` z decyzjami autora (pov, czas, subgatunek, tomy). Rój **nie** zwraca `meta` ani scen — `meta` składamy poniżej, a `kanon_fabularny.rozdzialy/beaty` bierzemy z konspektu. To domyka lukę, w której logline/comps z etapu 1 przepadały.

```bash
python3 - "$ROJ_JSON_SRC" "$PLUGIN_ROOT" << 'PY'
import json, sys, os
sys.path.insert(0, os.path.join(sys.argv[2], "scripts"))
import bible
r = json.load(open(sys.argv[1], encoding="utf-8"))   # surowy obiekt z roju + decyzje autora

# kanon: working + meta. UWAGA: `meta` NIE pochodzi z roju — składamy ją z decyzji autora
# (pov/czas/subgatunek/tomy) + briefu i zwycięskiego pomysłu z etapu 1. Inaczej logline/comps przepadają.
m = r.get("meta") or {}
idea = r.get("idea") or {}
brief = r.get("brief") or {}
meta = {"RO": True,
        "tytul":      m.get("tytul")   or idea.get("t", ""),
        "subgatunek": m.get("subgatunek", ""),
        "logline":    m.get("logline") or idea.get("log") or idea.get("op", ""),
        "target":     m.get("target")  or r.get("reader", ""),
        "comps":      m.get("comps")   or idea.get("comps", []),
        "pov":        m.get("pov", ""), "czas": m.get("czas", ""),
        "tomy":       m.get("tomy", 1),
        "ton":        m.get("ton")    or brief.get("tone", ""),
        "format":     m.get("format") or brief.get("format", "pojedyncza"),
        "forma":      m.get("forma")  or brief.get("form", ""),   # non-fiction: poradnik/reportaz/esej/pamietnik; "" = fikcja (guard non-fiction dla prozy)
        "budzet_slow": m.get("budzet_slow", 0), "liczba_scen": m.get("liczba_scen", 0)}
if not meta["logline"] or not meta["comps"]:
    print("UWAGA: meta.logline lub meta.comps puste — uzupełnij z raportu etapu 1 (DATA.brief / zwycięski pomysł)")
bible.write_section("meta", meta)
for sec in ("temat", "stawka", "antagonista", "glos_narratora"):
    if r.get(sec): bible.write_section(sec, {"RO": True, **r[sec]})

sw = dict(r["swiat"]); lokacje = sw.pop("lokacje", [])
bible.write_section("swiat", {"RO": True, **sw})
for lok in lokacje: bible.write_entity("lokacja", lok)
for p in r.get("postacie", []):
    p.setdefault("_stan", {"RUNTIME": True, "lokalizacja": "", "stan": "", "postep_luku": ""})
    bible.write_entity("postac", p)
for g in r.get("glosy_postaci", []): bible.write_entity("glos", g)
for g in r.get("glosariusz", []):    bible.write_entity("glosariusz", g)

# kanon_fabularny: book-bible zapisuje TYLKO rozdziały i beaty z konspektu (deterministycznie, nie z roju).
# SCENY dopisuje wyłącznie outline-to-scenes (etap 5) — tu zostają puste, by nie zapisać pustej/sprzecznej siatki.
# Beaty pochodzą z WYBRANEJ STRUKTURY narracyjnej (structureName z konspektu), nie zawsze z trójaktu.
kf = r.get("kanon_fabularny", {})   # {rozdzialy, beaty} z konspektu
bible.write_scene_grid(kf.get("rozdzialy", []), kf.get("beaty", []), [], force=True)

bible.render_index()
print("zapisano kanon-wiki do .book-forge/biblia/")
PY
```

Sekcje RUNTIME zostają puste — rosną dopiero podczas pisania (przez bramkę ciągłości). Agregaty `os_czasu`/`setup_payoff`/`fakty`/`zrodla` `bible.py` tworzy leniwie przy pierwszym `append_record`; `log_ciaglosci` (plik `log.md`) powstaje przy pierwszym `append_log`.

## Idempotencja (merge bez nadpisywania RO)

`write_entity(..., ro_guard=True)` (domyślnie) **nie nadpisuje** niepustych pól RO — uzupełnia tylko puste, a realny konflikt zwraca w `conflicts`. Merge przy ponownym uruchomieniu opisuje SKILL.md (Krok 2). Realną zmianę pola RO wykonuj tylko po `AskUserQuestion` — wtedy jawny `write_entity` na konkretnej encji.

## Strony i indeks

Strony encji/sekcji są **frontmatter-only** — czyta się je jako tabelę właściwości w edytorze. Pełną treść markdown mają tylko `.book-forge/biblia/index.md` (katalog) i `.book-forge/biblia/log.md` (kronika), generowane przez `bible.py` (`render_index`/`append_log`). Nie edytuj ich ręcznie; zmieniaj frontmatter przez bibliotekę.

## Walidacja (obowiązkowa)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bible.py validate
```

Walidator (następca `json.load`) sprawdza: poprawny frontmatter każdej strony, że `load_all()` składa kanon bez błędu, wypełnione sekcje RO (każda postać ma łuk, każda zasada koszt), pełną 7-przypadkową odmianę każdej nazwy w glosariuszu, rozwiązywalność wikilinków oraz brak duplikatów id. Wynik: `OK, brak luk` albo `LUKI:\n- ...`. Luki zgłoś autorowi — to typowe źródła późniejszych sprzeczności.

## Co czytają kolejne etapy

Etapy pisania wczytują kanon przez `bible.load_all()` i wstrzykują do promptu **tylko wyciąg** (karta POV, głosy obecnych postaci, istotne zasady świata, glosariusz, otwarte zasiewy) — patrz „anty-dryf” w `biblia-spec.md`.
