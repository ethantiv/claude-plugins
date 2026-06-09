#!/usr/bin/env python3
"""book-forge — biblioteka kanonu „biblii książki” (zdekomponowany kanon-wiki).

Źródłem prawdy jest frontmatter w kompaktowym JSON (między liniami `---`). Strony
encji/sekcji są frontmatter-only; pełną treść markdown mają tylko `index.md`
(katalog) i `log.md` (kronika). `load_all()` skleja to drzewo w jeden obiekt
(16 sekcji wg `shared/biblia-spec.md`), z którego czytają skille.

Standalone, tylko biblioteka standardowa (brak pyyaml). Wołane z poziomu skilli
przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py` (CLI) albo importowane.
"""

import glob
import json
import os
import re
import sys
import tempfile
import unicodedata

# Układ katalogu książki: pliki dla człowieka (HTML + finalny ksiazka.md/pakiet.md) leżą
# w korzeniu (BOOK_DIR), a cała mechanika robocza chowa się do ukrytego .book-forge/ (WORK_DIR).
# Kanon to .book-forge/biblia (BIBLE_DIR). W trybie serii wszystko zagnieżdża się pod tom-NN/.
BOOK_DIR = os.environ.get("BOOK_DIR", "")            # root dla człowieka: "" lub "tom-NN/"
WORK_DIR = os.environ.get("WORK", ".book-forge/")    # pliki robocze: ${BOOK_DIR}.book-forge/
BIBLE_DIR = os.environ.get("BIBLE_DIR", os.path.join(".book-forge", "biblia"))


def book_path(*parts):
    """Ścieżka do pliku przeznaczonego dla człowieka (korzeń książki/tomu)."""
    return os.path.join(BOOK_DIR, *parts)


def work_path(*parts):
    """Ścieżka do pliku roboczego (ukryty .book-forge/)."""
    return os.path.join(WORK_DIR, *parts)

# Kolejność sekcji jak w shared/biblia-spec.md (kształt odtwarzany przez load_all).
SECTION_ORDER = [
    "kanon", "meta", "swiat", "postacie", "antagonista", "stawka",
    "glos_narratora", "glosy_postaci", "glosariusz", "kanon_fabularny",
    "os_czasu", "setup_payoff", "fakty", "zrodla", "temat", "log_ciaglosci",
]

# Singletony: jedna sekcja = jeden plik (frontmatter = obiekt sekcji verbatim).
SINGLETONS = {
    "meta": "meta.md",
    "temat": "temat.md",
    "stawka": "stawka.md",
    "antagonista": "antagonista.md",
    "glos_narratora": "glos_narratora.md",
}
# Świat: zasady/technologia/konsekwencje w _swiat.md; lokacje to encje.
SWIAT_FILE = os.path.join("swiat", "_swiat.md")
# Agregaty list RUNTIME: frontmatter = {"items": [...]}.
AGGREGATES = {
    "os_czasu": os.path.join("fabula", "os-czasu.md"),
    "setup_payoff": os.path.join("fabula", "zasiewy.md"),
    "fakty": os.path.join("fabula", "fakty.md"),
    "zrodla": os.path.join("fabula", "zrodla.md"),
}
SCENY_FILE = os.path.join("fabula", "sceny.md")  # kanon_fabularny (agregat)
INDEX_FILE = "index.md"
LOG_FILE = "log.md"

# Seria / wiele tomów. seria.md leży w projekt-rootowym .book-forge/ (PONAD biblią tomu), bo łuk
# serii musi być widoczny z każdego tomu. _dziedziczone/ to snapshot published-kanonu
# poprzedniego tomu (RO) nakładany pod spód przy load_all. Brak obu ⇒ tryb pojedynczy.
SERIA_FILE = os.environ.get("SERIA_FILE", os.path.join(".book-forge", "seria.md"))
INHERIT_DIR = "_dziedziczone"

# Encje kolekcyjne: katalog + pole-nazwa (do slugu i rekonstrukcji).
ENTITY_KINDS = {
    "postac": {"dir": "postacie", "name": "imie", "section": "postacie"},
    "lokacja": {"dir": "swiat", "name": "nazwa", "section": None},  # do swiat.lokacje
    "glos": {"dir": "glosy", "name": "postac", "section": "glosy_postaci"},
    "glosariusz": {"dir": "glosariusz", "name": "nazwa", "section": "glosariusz"},
}

# Prefiks auto-id per agregat (jak dawne nid()).
ID_PREFIX = {"fakty": "F", "zrodla": "Z", "setup_payoff": "SP"}

# Pola RUNTIME (jedyne, które update_runtime wolno tknąć) per rodzaj encji.
RUNTIME_FIELDS = {"postac": {"_stan"}}


# --------------------------------------------------------------------------- #
# Prymitywy: frontmatter, atomowy zapis, slug
# --------------------------------------------------------------------------- #
def _split_frontmatter(text):
    """Zwraca (frontmatter_dict, body). Body może swobodnie zawierać `---`
    (dopasowujemy tylko PIERWSZE zamknięcie). Strona zaczynająca się od `---`
    bez domykającego `---` to uszkodzenie — rzucamy, by walidacja i load_all
    głośno zgłaszały urwaną stronę, a nie traktowały jej jak pustą (Rule 10)."""
    if not text.startswith("---"):
        return {}, text
    lines = text.split("\n")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("otwarty blok frontmatter `---` bez domknięcia (urwana strona)")
    fm_text = "\n".join(lines[1:end]).strip()
    body = "\n".join(lines[end + 1:]).lstrip("\n")
    fm = json.loads(fm_text) if fm_text else {}
    return fm, body


def _join_frontmatter(fm, body=""):
    fm_text = json.dumps(fm, ensure_ascii=False, indent=2, sort_keys=True)
    out = "---\n" + fm_text + "\n---\n"
    if body:
        out += "\n" + body.rstrip() + "\n"
    return out


def _atomic_write(path, text):
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())  # bez fsync os.replace daje atomowość nazwy, ale nie trwałość treści (karta SD na RPi)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def slugify(s):
    s = s or ""
    s = "".join({"ł": "l", "Ł": "l"}.get(c, c) for c in s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "x"


def _read_page(rel, base=None):
    path = os.path.join(base or BIBLE_DIR, rel)
    if not os.path.exists(path):
        return None, None
    with open(path, encoding="utf-8") as f:
        return _split_frontmatter(f.read())


# --------------------------------------------------------------------------- #
# Warstwa dziedziczenia serii (_dziedziczone/ = published-kanon poprzedniego tomu, RO)
# --------------------------------------------------------------------------- #
def _inherit_dir():
    return os.path.join(BIBLE_DIR, INHERIT_DIR)


def _has_inherit():
    return os.path.isdir(_inherit_dir())


def _read_page_merged(rel):
    """Czyta stronę własną; jeśli brak, a istnieje warstwa dziedziczona — czyta z niej.
    Dla tomu 1 / pojedynczej książki (brak _dziedziczone/) zachowuje się jak _read_page."""
    fm, body = _read_page(rel)
    if fm is None and _has_inherit():
        return _read_page(rel, base=_inherit_dir())
    return fm, body


def _is_inherited(rel):
    """True, gdy strona istnieje WYŁĄCZNIE w warstwie dziedziczonej (RO poprzedniego tomu)."""
    if not _has_inherit():
        return False
    own, _ = _read_page(rel)
    if own is not None:
        return False
    inh, _ = _read_page(rel, base=_inherit_dir())
    return bool(inh and inh.get("_inherited"))


def _write_page(rel, fm, body=""):
    _atomic_write(os.path.join(BIBLE_DIR, rel), _join_frontmatter(fm, body))


# --------------------------------------------------------------------------- #
# Body stron encji/sekcji: frontmatter-only (puste); por. shared/biblia-spec.md
# --------------------------------------------------------------------------- #
def _render_entity_body(kind, data):
    return ""


def _render_section_body(name, data):
    return ""


# --------------------------------------------------------------------------- #
# Odczyt
# --------------------------------------------------------------------------- #
def list_entities(kind, include_inherited=True):
    """Slugi encji danego rodzaju. W trybie serii dołącza encje dziedziczone
    (own-wins: encja własna o tym samym slugu przesłania dziedziczoną)."""
    slugs = {}

    def scan(root):
        dd = os.path.join(root, ENTITY_KINDS[kind]["dir"])
        if not os.path.isdir(dd):
            return
        for path in sorted(glob.glob(os.path.join(dd, "*.md"))):
            base = os.path.basename(path)
            if base.startswith("_"):  # _swiat.md to nie encja
                continue
            slugs.setdefault(base[:-3], True)  # własne skanowane pierwsze → wygrywają

    scan(BIBLE_DIR)
    if include_inherited and _has_inherit():
        scan(_inherit_dir())
    return list(slugs.keys())


def read_entity(kind, name_or_slug):
    slug = name_or_slug if _looks_like_slug(name_or_slug) else slugify(name_or_slug)
    rel = os.path.join(ENTITY_KINDS[kind]["dir"], slug + ".md")
    fm, body = _read_page_merged(rel)
    if fm is None:
        raise KeyError(f"brak encji {kind}:{name_or_slug} ({rel})")
    return fm, body


def _looks_like_slug(s):
    return bool(re.fullmatch(r"[a-z0-9-]+", s or ""))


def read_section(name):
    return load_all().get(name)


def _read_kanon_scalar():
    fm, _ = _read_page(INDEX_FILE)
    if fm and "kanon" in fm:
        return fm["kanon"]
    return "working"


def load_all():
    """Skleja drzewo `biblia/**/*.md` w jeden obiekt (16 sekcji wg biblia-spec.md)."""
    b = {}
    b["kanon"] = _read_kanon_scalar()

    for sec in ("meta", "temat", "stawka", "antagonista", "glos_narratora"):
        fm, _ = _read_page_merged(SINGLETONS[sec])
        if fm is not None:
            b[sec] = fm

    # swiat: bazowa sekcja + lokacje (encje)
    fm, _ = _read_page_merged(SWIAT_FILE)
    if fm is not None or list_entities("lokacja"):
        swiat = dict(fm or {})
        swiat["lokacje"] = [read_entity("lokacja", s)[0] for s in list_entities("lokacja")]
        b["swiat"] = swiat

    if list_entities("postac"):
        b["postacie"] = [read_entity("postac", s)[0] for s in list_entities("postac")]
    if list_entities("glos"):
        b["glosy_postaci"] = [read_entity("glos", s)[0] for s in list_entities("glos")]
    if list_entities("glosariusz"):
        b["glosariusz"] = [read_entity("glosariusz", s)[0] for s in list_entities("glosariusz")]

    fm, _ = _read_page_merged(SCENY_FILE)
    if fm is not None:
        b["kanon_fabularny"] = fm

    for sec, rel in AGGREGATES.items():
        items = _merge_aggregate(rel)
        if items is not None:
            b[sec] = items

    b["log_ciaglosci"] = _read_log()

    return {k: b[k] for k in SECTION_ORDER if k in b}


def _merge_aggregate(rel):
    """Items agregatu RUNTIME: rekordy dziedziczone (RO) pod spodem, własne na wierzchu
    (own-wins po `id`). Brak własnego i dziedziczonego pliku ⇒ None (sekcja nieobecna)."""
    own_fm, _ = _read_page(rel)
    inh_items = []
    if _has_inherit():
        inh_fm, _ = _read_page(rel, base=_inherit_dir())
        if inh_fm is not None:
            inh_items = inh_fm.get("items", [])
    if own_fm is None and not inh_items:
        return None
    own = own_fm.get("items", []) if own_fm is not None else []
    if not inh_items:
        return own
    own_ids = {it.get("id") for it in own if it.get("id")}
    return [it for it in inh_items if it.get("id") not in own_ids] + own


# --------------------------------------------------------------------------- #
# Zapis: encje, sekcje, RUNTIME
# --------------------------------------------------------------------------- #
def write_section(name, data, body=None):
    if name == "swiat":
        rel = SWIAT_FILE
    elif name in SINGLETONS:
        rel = SINGLETONS[name]
    else:
        raise ValueError(f"nieznana sekcja-singleton: {name}")
    _write_page(rel, data, body if body is not None else _render_section_body(name, data))


def write_entity(kind, data, body=None, ro_guard=True):
    """Tworzy/aktualizuje plik encji. Przy ro_guard i istniejącym pliku:
    niepuste pola RO zostają (merge-not-clobber), realny konflikt → CONFLICT.

    UWAGA o gwarancji RO: twarda, bibliotekowa gwarancja „nie nadpiszesz RO" dotyczy
    `update_runtime` (whitelist RUNTIME) oraz encji `_inherited` (zamknięte tomy serii).
    `ro_guard=False` to ŚWIADOMY autorski override (np. seedowanie kanonu w book-bible) —
    pomija merge i nadpisuje. Bramka ciągłości po write-backu woła `assert_ro_unchanged`,
    co wychwytuje każde przypadkowe ruszenie RO niezależnie od tej ścieżki."""
    spec = ENTITY_KINDS[kind]
    name = data.get(spec["name"], "")
    slug = data.get("_slug") or slugify(name)
    rel = os.path.join(spec["dir"], slug + ".md")
    if _is_inherited(rel):  # encja zamkniętego tomu jest nietykalna — nie pozwól jej przesłonić
        return {"slug": slug, "created": False, "conflicts": [],
                "status": "INHERITED_RO", "powod": f"{kind}:{name} pochodzi z zamkniętego tomu (RO)"}
    conflicts = []
    existing, _ = _read_page(rel)
    created = existing is None
    if existing is not None:  # kolizja slugu: dwie różne nazwy mapują się na ten sam plik (np. „Wena”/„Węna”)
        existing_name = existing.get(spec["name"])
        if existing_name and name and existing_name != name:
            return {"slug": slug, "created": False, "conflicts": [],
                    "status": "SLUG_COLLISION",
                    "powod": f"slug '{slug}' należy już do {spec['name']}='{existing_name}', nie '{name}' — nadaj inny slug (_slug)"}
    if existing is not None and ro_guard:
        merged = dict(existing)
        for k, v in data.items():
            old = existing.get(k)
            if old in (None, "", [], {}):
                merged[k] = v
            elif v not in (None, "", [], {}) and v != old:
                conflicts.append({"pole": k, "biblia_mowi": old, "nowe": v})
            # niepuste i zgodne → zostaw
        data = merged
    _write_page(rel, data, body if body is not None else _render_entity_body(kind, data))
    return {"slug": slug, "created": created, "conflicts": conflicts}


def update_runtime(kind, name, field, value):
    """Patch pola RUNTIME encji. Pole spoza whitelisty RUNTIME → CONFLICT
    (nic nie zapisuje). Nieistniejąca encja → MISS (nic nie zapisuje, nie rzuca —
    żeby zła nazwa w propozycji nie wysadziła całego write-backu bramki).
    Obsługuje ścieżkę kropkową w obrębie _stan."""
    root = field.split(".", 1)[0]
    if root not in RUNTIME_FIELDS.get(kind, set()):
        return {"status": "CONFLICT", "pole": field,
                "powod": f"pole {field} nie jest RUNTIME dla {kind}"}
    try:
        fm, body = read_entity(kind, name)
    except KeyError:
        return {"status": "MISS", "pole": field,
                "powod": f"brak encji {kind}:{name}"}
    if fm.get("_inherited"):  # encja dziedziczona z zamkniętego tomu — RUNTIME też zablokowany
        return {"status": "INHERITED_RO", "pole": field,
                "powod": f"{kind}:{name} pochodzi z zamkniętego tomu (RO)"}
    if "." in field:
        sub = field.split(".", 1)[1]
        fm.setdefault(root, {})[sub] = value
    else:
        fm[root] = value
    spec = ENTITY_KINDS[kind]
    slug = fm.get("_slug") or slugify(fm.get(spec["name"], ""))
    _write_page(os.path.join(spec["dir"], slug + ".md"), fm,
                _render_entity_body(kind, fm))
    return {"status": "WRITE", "pole": field}


def new_id(section):
    prefix = ID_PREFIX[section]
    items = load_all().get(section, [])
    mx = 0
    for it in items:
        m = re.match(rf"{prefix}(\d+)$", str(it.get("id", "")))
        if m:
            mx = max(mx, int(m.group(1)))
    return f"{prefix}{mx + 1:02d}"


def append_record(section, record, dedup_keys=None):
    """Append do agregatu RUNTIME z dedup + auto-id. Domyślny dedup:
    fakty=(tresc,zrodlo_scena); os_czasu=(scena,) update-or-append;
    setup_payoff=(id,) update-or-append; zrodla=(id,) lub brak."""
    rel = AGGREGATES[section]
    fm, _ = _read_page(rel)
    items = list((fm or {}).get("items", []))
    defaults = {
        "fakty": ("tresc", "zrodlo_scena"),
        "os_czasu": ("scena",),
        "setup_payoff": ("id",),
        "zrodla": ("id",),
    }
    keys = dedup_keys if dedup_keys is not None else defaults.get(section, ())

    record = dict(record)
    # Rekord z auto-id bez wskazanego id: świeżo nadane id nigdy nie zrówna się
    # z istniejącym, więc dedup po samym 'id' by nie zadziałał — deduplikuj po treści.
    auto_id = section in ID_PREFIX and not record.get("id")
    if auto_id and keys in ((), ("id",)):
        keys = tuple(k for k in record if k not in ("id", "RUNTIME"))
    if auto_id:
        record["id"] = new_id(section)

    action = "append"
    if keys:
        def sig(r):
            return tuple(r.get(k) for k in keys)
        for i, it in enumerate(items):
            if sig(it) == sig(record):
                if section in ("os_czasu", "setup_payoff"):
                    items[i] = {**it, **record}
                    action = "update"
                else:
                    action = "skip"
                break
        else:
            items.append(record)
    else:
        items.append(record)
    _write_page(rel, {"items": items}, _render_aggregate_body(section, items))
    return {"id": record.get("id"), "action": action}


def _render_aggregate_body(section, items):
    return ""


# --------------------------------------------------------------------------- #
# Sceny (maszyna stanu — wyjątek od RO-guarda)
# --------------------------------------------------------------------------- #
def write_scene_grid(rozdzialy, beaty, sceny, force=False):
    fm, _ = _read_page(SCENY_FILE)
    if fm is not None and fm.get("sceny") and not force:
        return {"status": "GUARD", "powod": "siatka scen już istnieje (force=True by nadpisać)"}
    data = {"RO": True, "rozdzialy": rozdzialy, "beaty": beaty, "sceny": sceny}
    _write_page(SCENY_FILE, data, _render_section_body("kanon_fabularny", data))
    return {"status": "WRITE", "scen": len(sceny)}


def set_scene_field(scene_id, field, value):
    """Patch pojedynczego pola karty sceny (maszyna stanu — wyjątek od RO-guarda
    agregatu, jak status). MISS, gdy nie ma takiej sceny. Używane m.in. do
    `proza_zrodlo` (dowiązanie gotowej prozy otwarcia z etapu opening)."""
    fm, _ = _read_page(SCENY_FILE)
    if fm is None:
        raise KeyError("brak fabula/sceny.md")
    for s in fm.get("sceny", []):
        if s.get("id") == scene_id:
            s[field] = value
            _write_page(SCENY_FILE, fm, _render_section_body("kanon_fabularny", fm))
            return {"status": "WRITE", "scena": scene_id, "pole": field}
    return {"status": "MISS", "scena": scene_id}


def set_scene_status(scene_id, status):
    return set_scene_field(scene_id, "status", status)


# --------------------------------------------------------------------------- #
# Log (append-only kronika)
# --------------------------------------------------------------------------- #
def append_log(entry):
    path = os.path.join(BIBLE_DIR, LOG_FILE)
    if entry in _read_log():  # idempotencja: powtórzenie bramki nie dubluje identycznego wpisu
        return
    head = " · ".join(str(entry.get(k, "")) for k in ("scena", "werdykt") if entry.get(k))
    block = []
    if head:
        block.append(f"## {head}")
    block.append(f"<!-- {json.dumps(entry, ensure_ascii=False)} -->")
    proza = entry.get("decyzja") or entry.get("sprzecznosci") or ""
    if proza:
        block.append(proza)
    block.append("\n---\n")
    text = "\n".join(block) + "\n"
    os.makedirs(BIBLE_DIR, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)


def _read_log():
    path = os.path.join(BIBLE_DIR, LOG_FILE)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        text = f.read()
    out = []
    for m in re.finditer(r"<!--\s*(\{.*?\})\s*-->", text, re.DOTALL):
        try:
            out.append(json.loads(m.group(1)))
        except json.JSONDecodeError:
            pass
    return out


# --------------------------------------------------------------------------- #
# Indeks i zamrożenie kanonu
# --------------------------------------------------------------------------- #
def render_index():
    b = load_all()
    lines = ["<!-- GENEROWANE przez scripts/bible.py — NIE EDYTUJ RĘCZNIE -->"]
    tytul = (b.get("meta") or {}).get("tytul", "")
    lines.append(f"# Indeks biblii — „{tytul}”" if tytul else "# Indeks biblii")
    lines.append(f"kanon: **{b.get('kanon', 'working')}**")
    lines.append("")

    def row(link, status, opis):
        return f"| [[{link}]] | {status} | {opis} |"

    # Encje bierzemy z jednego snapshotu load_all (bez drugiego skanu dysku);
    # slug odtwarzamy tak samo jak nazwa pliku: _slug albo slugify(nazwa).
    groups = [
        ("Postacie", "postac", "RO+RT", b.get("postacie", [])),
        ("Świat / lokacje", "lokacja", "RO", (b.get("swiat") or {}).get("lokacje", [])),
        ("Głosy postaci", "glos", "RO", b.get("glosy_postaci", [])),
        ("Glosariusz", "glosariusz", "RO", b.get("glosariusz", [])),
    ]
    for title, kind, status, ents in groups:
        if not ents:
            continue
        name_field = ENTITY_KINDS[kind]["name"]
        lines += [f"## {title}", "| Strona | Status | Opis |", "|---|---|---|"]
        for fm in ents:
            slug = fm.get("_slug") or slugify(fm.get(name_field, ""))
            opis = fm.get("opis") or fm.get("rola") or fm.get("kategoria") or ""
            lines.append(row(f"{ENTITY_KINDS[kind]['dir']}/{slug}", status, str(opis)[:80]))
        lines.append("")

    aggr = []
    if b.get("kanon_fabularny"):
        kf = b["kanon_fabularny"]
        aggr.append(("fabula/sceny", "RO", f"{len(kf.get('sceny', []))} scen, {len(kf.get('rozdzialy', []))} rozdz."))
    for sec, label in (("setup_payoff", "fabula/zasiewy"), ("os_czasu", "fabula/os-czasu"),
                       ("fakty", "fabula/fakty"), ("zrodla", "fabula/zrodla")):
        if sec in b:
            aggr.append((label, "RT", f"{len(b[sec])} rekordów"))
    if aggr:
        lines += ["## Fabuła i stan (agregaty)", "| Strona | Status | Opis |", "|---|---|---|"]
        for link, status, opis in aggr:
            lines.append(row(link, status, opis))
        lines.append("")

    body = "\n".join(lines).rstrip() + "\n"
    _write_page(INDEX_FILE, {"kanon": b.get("kanon", "working")}, body)


def freeze_canon(published=True):
    fm, _ = _read_page(INDEX_FILE)
    fm = fm or {}
    fm["kanon"] = "published" if published else "working"
    _write_page(INDEX_FILE, fm)  # utrwal kanon; render_index niżej regeneruje całe body
    render_index()


# --------------------------------------------------------------------------- #
# Seria: stan serii + dziedziczenie published-kanonu poprzedniego tomu
# --------------------------------------------------------------------------- #
def read_series():
    """Stan serii z seria.md (frontmatter). Brak pliku ⇒ None ⇒ tryb pojedynczy."""
    if not os.path.exists(SERIA_FILE):
        return None
    with open(SERIA_FILE, encoding="utf-8") as f:
        fm, _ = _split_frontmatter(f.read())
    return fm


def write_series(data):
    _atomic_write(SERIA_FILE, _join_frontmatter(data))
    return {"status": "WRITE", "plik": SERIA_FILE}


def import_published(prev_bible_dir):
    """Kopiuje published-kanon poprzedniego tomu do BIBLE_DIR/_dziedziczone/ jako warstwę RO
    (każda strona dostaje `_inherited: true`). Odmawia, gdy poprzednik nie jest published
    (nie dziedziczymy roboczego kanonu — fail loud). Idempotentne (nadpisuje snapshot)."""
    if not os.path.isdir(prev_bible_dir):
        return {"status": "ERROR", "powod": f"brak katalogu biblii poprzedniego tomu: {prev_bible_dir}"}
    idx, _ = _read_page(INDEX_FILE, base=prev_bible_dir)
    if (idx or {}).get("kanon") != "published":
        return {"status": "ERROR",
                "powod": "poprzedni tom nie jest 'published' — zamroź go (freeze_canon) przed dziedziczeniem"}
    dest = _inherit_dir()
    n = 0
    for path in glob.glob(os.path.join(prev_bible_dir, "**", "*.md"), recursive=True):
        rel = os.path.relpath(path, prev_bible_dir)
        if rel in (INDEX_FILE, LOG_FILE):      # index regenerujemy; log ciągłości jest per-tom
            continue
        if rel.split(os.sep, 1)[0] == INHERIT_DIR:  # nie dziedzicz rekurencyjnie cudzego _dziedziczone/
            continue
        with open(path, encoding="utf-8") as f:
            fm, body = _split_frontmatter(f.read())
        fm = dict(fm or {})
        fm["_inherited"] = True
        _atomic_write(os.path.join(dest, rel), _join_frontmatter(fm, body))
        n += 1
    return {"status": "OK", "stron": n, "dest": dest}


# --------------------------------------------------------------------------- #
# Audyt RO (gwarancja w bibliotece, nie w dyscyplinie skryptu) — używa go bramka ciągłości
# --------------------------------------------------------------------------- #
RO_SINGLETONS = ("meta", "swiat", "antagonista", "stawka", "glos_narratora", "temat")
RO_POSTAC_POLA = ("opis_fizyczny", "luk", "odmiana", "want", "need", "rana", "klamstwo")
RO_GLOS_POLA = ("odmiana", "kategoria")


def ro_snapshot():
    """Hash pól RO całego kanonu (singletony RO + RO-pola postaci i glosariusza).
    Porównanie before/after wykrywa, że write-back tknął RO — patrz assert_ro_unchanged."""
    b = load_all()
    snap = {}
    for sec in RO_SINGLETONS:
        if sec in b:
            snap[sec] = json.dumps(b[sec], sort_keys=True, ensure_ascii=False)
    snap["postacie_RO"] = {p.get("imie"): json.dumps({k: p.get(k) for k in RO_POSTAC_POLA}, sort_keys=True, ensure_ascii=False)
                           for p in b.get("postacie", [])}
    snap["glosariusz_RO"] = {g.get("nazwa"): json.dumps({k: g.get(k) for k in RO_GLOS_POLA}, sort_keys=True, ensure_ascii=False)
                             for g in b.get("glosariusz", [])}
    return snap


def assert_ro_unchanged(before):
    """Rzuca AssertionError, jeśli którekolwiek pole RO zmieniło się od snapshotu `before`.
    Wołane przez bramkę ciągłości po write-backu — domyka obietnicę „RO nie do ruszenia"."""
    after = ro_snapshot()
    if after != before:
        diffs = [k for k in set(before) | set(after) if before.get(k) != after.get(k)]
        raise AssertionError(f"BŁĄD AUDYTU RO: write-back zmienił pola RO: {diffs}")
    return True


# --------------------------------------------------------------------------- #
# Walidacja
# --------------------------------------------------------------------------- #
def validate_canon():
    braki = []
    for path in glob.glob(os.path.join(BIBLE_DIR, "**", "*.md"), recursive=True):
        if os.path.basename(path) in (INDEX_FILE, LOG_FILE):
            continue
        with open(path, encoding="utf-8") as f:
            try:
                _split_frontmatter(f.read())
            except (json.JSONDecodeError, ValueError) as e:
                braki.append(f"zepsuty frontmatter: {path} ({e})")
    if braki:  # brama: bez poprawnych frontmatterów load_all i tak by rzucił
        return braki

    try:
        b = load_all()
    except Exception as e:  # noqa: BLE001 — raport, nie crash
        return [f"load_all() rzucił: {e}"]

    for s in ("meta", "swiat", "postacie", "glos_narratora", "glosariusz", "temat"):
        if not b.get(s):
            braki.append(f"pusta sekcja RO: {s}")
    for p in b.get("postacie", []):
        if not p.get("luk"):
            braki.append(f"postać bez łuku: {p.get('imie', '?')}")
    for z in b.get("swiat", {}).get("zasady", []):
        if not z.get("koszt"):
            braki.append(f"zasada bez kosztu: {str(z.get('zasada', '?'))[:40]}")
    for g in b.get("glosariusz", []):
        od = g.get("odmiana") or {}
        miss = [k for k in ("M", "D", "C", "B", "N", "Ms", "W") if not od.get(k)]
        if miss:
            braki.append(f"nazwa bez pełnej odmiany ({','.join(miss)}): {g.get('nazwa', '?')}")

    seen = {}
    for sec in ("fakty", "zrodla", "setup_payoff"):
        for it in b.get(sec, []):
            i = it.get("id")
            if i and i in seen:
                braki.append(f"duplikat id {i} w {sec}")
            seen[i] = sec

    for path in glob.glob(os.path.join(BIBLE_DIR, "**", "*.md"), recursive=True):
        with open(path, encoding="utf-8") as f:
            for link in re.findall(r"\[\[([a-z0-9/_-]+?)(?:\|[^\]]*)?\]\]", f.read()):
                target = os.path.join(BIBLE_DIR, link + ".md")
                if not os.path.exists(target):
                    braki.append(f"wiszący wikilink [[{link}]] w {os.path.basename(path)}")
    return braki


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _cli(argv):
    if not argv:
        print("użycie: bible.py {validate|render-index|dump|freeze|import-published <kat>|series}")
        return 2
    cmd = argv[0]
    if cmd == "import-published":
        if len(argv) < 2:
            print("użycie: bible.py import-published <katalog_biblii_poprzedniego_tomu>")
            return 2
        res = import_published(argv[1])
        print(json.dumps(res, ensure_ascii=False))
        return 0 if res.get("status") == "OK" else 1
    if cmd == "series":
        print(json.dumps(read_series(), ensure_ascii=False, indent=2))
        return 0
    if cmd == "validate":
        braki = validate_canon()
        print("OK, brak luk" if not braki else "LUKI:\n- " + "\n- ".join(braki))
        return 1 if braki else 0
    if cmd == "render-index":
        render_index()
        print("zregenerowano index.md")
        return 0
    if cmd == "dump":
        print(json.dumps(load_all(), ensure_ascii=False, indent=2))
        return 0
    if cmd == "freeze":
        freeze_canon(True)
        print("kanon: published")
        return 0
    print(f"nieznana komenda: {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
