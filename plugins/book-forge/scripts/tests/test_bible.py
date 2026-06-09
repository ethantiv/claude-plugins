#!/usr/bin/env python3
"""Test E2E biblioteki kanonu-wiki (scripts/bible.py). Bez pisania powieści.

Uruchom: python3 scripts/tests/test_bible.py
Pracuje w katalogu tymczasowym (BIBLE_DIR), nie dotyka realnych projektów.
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
sys.path.insert(0, SCRIPTS)

FAILS = []


def check(name, cond, detail=""):
    print(("OK  " if cond else "FAIL") + "  " + name + (f"  — {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def _norm(b):
    """Normalizuje obiekt do porównania: sortuje listy-encje po kluczu naturalnym."""
    b = json.loads(json.dumps(b))  # głęboka kopia
    keymap = {"postacie": "imie", "glosy_postaci": "postac", "glosariusz": "nazwa"}
    for sec, key in keymap.items():
        if sec in b:
            b[sec] = sorted(b[sec], key=lambda x: x.get(key, ""))
    if "swiat" in b and "lokacje" in b["swiat"]:
        b["swiat"]["lokacje"] = sorted(b["swiat"]["lokacje"], key=lambda x: x.get("nazwa", ""))
    return b


def _populate(bible, b):
    """Buduje kanon-wiki z pełnego obiektu przez publiczne API biblioteki —
    ta sama sekwencja, którą stosuje skill book-bible (build-and-verify.md)."""
    for sec in ("meta", "temat", "stawka", "antagonista", "glos_narratora"):
        if b.get(sec):
            bible.write_section(sec, b[sec])
    if "swiat" in b:
        sw = dict(b["swiat"])
        for lok in sw.pop("lokacje", []):
            bible.write_entity("lokacja", lok, ro_guard=False)
        bible.write_section("swiat", sw)
    for p in b.get("postacie", []):
        bible.write_entity("postac", p, ro_guard=False)
    for g in b.get("glosy_postaci", []):
        bible.write_entity("glos", g, ro_guard=False)
    for g in b.get("glosariusz", []):
        bible.write_entity("glosariusz", g, ro_guard=False)
    kf = b.get("kanon_fabularny", {})
    bible.write_scene_grid(kf.get("rozdzialy", []), kf.get("beaty", []), kf.get("sceny", []), force=True)
    for sec in ("os_czasu", "setup_payoff", "fakty", "zrodla"):
        for rec in b.get(sec, []):
            bible.append_record(sec, rec)
    for e in b.get("log_ciaglosci", []):
        bible.append_log(e)
    bible.render_index()


def main():
    import bible

    work = tempfile.mkdtemp(prefix="biblia-test-")
    try:
        os.environ["BIBLE_DIR"] = os.path.join(work, "biblia")
        bible.BIBLE_DIR = os.environ["BIBLE_DIR"]
        os.makedirs(bible.BIBLE_DIR, exist_ok=True)

        original = json.load(open(os.path.join(HERE, "fixture-biblia.json"), encoding="utf-8"))

        # 2. zbuduj kanon przez publiczne API (tą samą drogą co skill book-bible)
        _populate(bible, original)
        check("setup: layout postacie", len(bible.list_entities("postac")) == 2)
        check("setup: layout glosariusz", len(bible.list_entities("glosariusz")) == 3)

        # 3. round-trip kształtu (NAJWAŻNIEJSZY)
        loaded = bible.load_all()
        check("round-trip kształtu == fixture", _norm(loaded) == _norm(original),
              "load_all() różni się od oryginału")
        check("round-trip: 16 sekcji", set(loaded) == set(original))
        check("round-trip: _stan zachowany",
              any(p.get("_stan", {}).get("lokalizacja") == "Pas Łomów" for p in loaded["postacie"]))
        check("round-trip: kolejność scen", [s["id"] for s in loaded["kanon_fabularny"]["sceny"]]
              == ["R1S1", "R1S2", "R2S1", "R2S2"])

        # 4. round-trip zapisu (zapis encji bez zmian → load identyczny)
        fm, _ = bible.read_entity("postac", "Kalina")
        bible.write_entity("postac", fm)
        check("round-trip zapisu", _norm(bible.load_all()) == _norm(original))

        # 5a. append_record + dedup + auto-id
        r1 = bible.append_record("fakty", {"tresc": "Eron zna mapę", "typ": "zdarzenie",
                                            "zrodlo_scena": "R2S1", "pewnosc": "roboczy", "zrodlo_ref": ""})
        check("append_record auto-id F02", r1["id"] == "F02" and r1["action"] == "append", str(r1))
        r2 = bible.append_record("fakty", {"tresc": "Eron zna mapę", "typ": "zdarzenie",
                                           "zrodlo_scena": "R2S1", "pewnosc": "roboczy", "zrodlo_ref": ""})
        check("append_record dedup skip", r2["action"] == "skip", str(r2))
        check("fakty: 2 rekordy po dedup", len(bible.load_all()["fakty"]) == 2)

        # 5b. update_runtime RUNTIME OK + RO→CONFLICT
        w = bible.update_runtime("postac", "Kalina", "_stan.lokalizacja", "Cytadela")
        check("update_runtime _stan = WRITE", w["status"] == "WRITE", str(w))
        check("update_runtime zmienił stan",
              [p for p in bible.load_all()["postacie"] if p["imie"] == "Kalina"][0]["_stan"]["lokalizacja"] == "Cytadela")
        c = bible.update_runtime("postac", "Kalina", "opis_fizyczny", "wysoka blondynka")
        check("update_runtime RO → CONFLICT", c["status"] == "CONFLICT", str(c))
        check("RO niezmienione po CONFLICT",
              [p for p in bible.load_all()["postacie"] if p["imie"] == "Kalina"][0]["opis_fizyczny"] == "drobna, blizna na dłoni")

        # 5c. idempotencja: setup_payoff update-or-append (status) dwukrotnie
        bible.append_record("setup_payoff", {"id": "SP01", "status": "domkniety", "scena_splaty": "R2S2"})
        bible.append_record("setup_payoff", {"id": "SP01", "status": "domkniety", "scena_splaty": "R2S2"})
        sp = bible.load_all()["setup_payoff"]
        check("setup_payoff: brak duplikatu (idempotencja)", len([x for x in sp if x["id"] == "SP01"]) == 1)
        check("setup_payoff: status zaktualizowany",
              [x for x in sp if x["id"] == "SP01"][0]["status"] == "domkniety")

        # 5d. set_scene_status + log
        bible.set_scene_status("R1S1", "zweryfikowana")
        check("set_scene_status",
              [s for s in bible.load_all()["kanon_fabularny"]["sceny"] if s["id"] == "R1S1"][0]["status"] == "zweryfikowana")

        # 5d'. set_scene_field: dowiązanie prozy otwarcia trwa na karcie sceny
        w = bible.set_scene_field("R1S1", "proza_zrodlo", "poczatek.md")
        check("set_scene_field WRITE", w["status"] == "WRITE" and w["pole"] == "proza_zrodlo", str(w))
        check("set_scene_field round-trip",
              [s for s in bible.load_all()["kanon_fabularny"]["sceny"] if s["id"] == "R1S1"][0].get("proza_zrodlo") == "poczatek.md")
        check("set_scene_field MISS na nieznanej scenie",
              bible.set_scene_field("BRAK", "proza_zrodlo", "x")["status"] == "MISS")
        bible.append_log({"scena": "R1S1", "werdykt": "PASS", "sprzecznosci": "", "decyzja": "zapis RUNTIME"})
        check("append_log → log_ciaglosci",
              len(bible.load_all()["log_ciaglosci"]) == 1 and bible.load_all()["log_ciaglosci"][0]["werdykt"] == "PASS")

        # 5e. write_scene_grid guard (siatka istnieje)
        g = bible.write_scene_grid([], [], [{"id": "X", "status": "planowana"}])
        check("write_scene_grid guard", g["status"] == "GUARD", str(g))

        # 5f. freeze_canon (i powrót published→working)
        bible.freeze_canon(True)
        check("freeze_canon published", bible.load_all()["kanon"] == "published")
        bible.freeze_canon(False)
        check("freeze_canon working (powrót)", bible.load_all()["kanon"] == "working")
        bible.freeze_canon(True)  # zostaw published — potrzebne do dziedziczenia w teście serii

        # 6. SERIA: tom 2 dziedziczy published-kanon tomu 1 jako RO
        tom1_dir = bible.BIBLE_DIR
        tom2_dir = os.path.join(work, "tom-02", "biblia")
        os.makedirs(tom2_dir, exist_ok=True)
        os.environ["BIBLE_DIR"] = tom2_dir
        bible.BIBLE_DIR = tom2_dir

        imp = bible.import_published(tom1_dir)
        check("seria: import_published OK", imp["status"] == "OK" and imp["stron"] > 0, str(imp))
        names = [p["imie"] for p in bible.load_all().get("postacie", [])]
        check("seria: tom 2 widzi postać dziedziczoną", "Kalina" in names, str(names))
        check("seria: dziedziczone encje oznaczone _inherited",
              all(p.get("_inherited") for p in bible.load_all()["postacie"]))
        r = bible.write_entity("postac", {"imie": "Kalina", "opis_fizyczny": "inna"})
        check("seria: write_entity na dziedziczonej → INHERITED_RO", r.get("status") == "INHERITED_RO", str(r))
        u = bible.update_runtime("postac", "Kalina", "_stan.lokalizacja", "X")
        check("seria: update_runtime na dziedziczonej → INHERITED_RO", u.get("status") == "INHERITED_RO", str(u))
        check("seria: dziedziczona Kalina niezmieniona",
              [p for p in bible.load_all()["postacie"] if p["imie"] == "Kalina"][0]["opis_fizyczny"] == "drobna, blizna na dłoni")
        bible.write_entity("postac", {"imie": "Norn", "rola": "nowy", "luk": "plan", "opis_fizyczny": "y"}, ro_guard=False)
        names2 = sorted(p["imie"] for p in bible.load_all()["postacie"])
        check("seria: nowa postać tomu 2 współistnieje z dziedziczoną", "Norn" in names2 and "Kalina" in names2, str(names2))
        err = bible.import_published(tom2_dir)  # tom 2 nie jest published (brak index.md)
        check("seria: import z nie-published → ERROR", err.get("status") == "ERROR", str(err))

        os.environ["SERIA_FILE"] = os.path.join(work, "seria.md")
        bible.SERIA_FILE = os.environ["SERIA_FILE"]
        check("seria: read_series None gdy brak pliku", bible.read_series() is None)
        bible.write_series({"RO": True, "tytul_serii": "Cykl", "tomy": 3, "tom_aktywny": 2})
        check("seria: write/read_series round-trip", (bible.read_series() or {}).get("tomy") == 3)

        os.environ["BIBLE_DIR"] = tom1_dir  # przywróć tom 1 do dalszych testów walidatora
        bible.BIBLE_DIR = tom1_dir

        # 5g. write_entity z realnym konfliktem RO: zgłoszony w conflicts, RO niezmienione na dysku
        ro_snap = bible.ro_snapshot()
        rc = bible.write_entity("postac", {"imie": "Kalina", "opis_fizyczny": "wysoka blondynka"})
        check("write_entity RO konflikt zgłoszony", any(c.get("pole") == "opis_fizyczny" for c in rc.get("conflicts", [])), str(rc))
        check("write_entity RO niezmienione na dysku",
              [p for p in bible.load_all()["postacie"] if p["imie"] == "Kalina"][0]["opis_fizyczny"] == "drobna, blizna na dłoni")
        check("assert_ro_unchanged po konflikcie przechodzi", bible.assert_ro_unchanged(ro_snap) is True)

        # 5h. kolizja slugu: inna nazwa transliterująca się do istniejącego slugu → SLUG_COLLISION
        sc = bible.write_entity("postac", {"imie": "Kálina", "rola": "x", "luk": "y", "opis_fizyczny": "z"})
        check("write_entity kolizja slugu", sc.get("status") == "SLUG_COLLISION", str(sc))

        # 5i. new_id kontynuuje numerację (po wcześniejszym F02)
        check("new_id fakty kolejne (F03)", bible.new_id("fakty") == "F03", bible.new_id("fakty"))

        # 7. walidator: czysto, potem zepsuty frontmatter
        braki = bible.validate_canon()
        check("walidator czysty", braki == [], "; ".join(braki))

        # 7a. assert_ro_unchanged WYKRYWA forsowaną zmianę RO (ro_guard=False to świadomy override)
        ro_snap2 = bible.ro_snapshot()
        bible.write_entity("postac", {"imie": "Kalina", "opis_fizyczny": "INNA"}, ro_guard=False)
        raised = False
        try:
            bible.assert_ro_unchanged(ro_snap2)
        except AssertionError:
            raised = True
        check("assert_ro_unchanged wykrywa zmianę RO", raised)

        # 7b. walidator wykrywa postać bez łuku i wiszący wikilink
        bible.write_entity("postac", {"imie": "Bezluku", "rola": "x", "opis_fizyczny": "y"}, ro_guard=False)
        with open(os.path.join(bible.BIBLE_DIR, "notatka.md"), "w", encoding="utf-8") as f:
            f.write("zob. [[nieistnieje/cos|Coś]]\n")
        braki_gap = bible.validate_canon()
        check("walidator: postać bez łuku", any("bez łuku" in x for x in braki_gap), "; ".join(braki_gap))
        check("walidator: wiszący wikilink", any("wiszący wikilink" in x for x in braki_gap))
        bad = os.path.join(bible.BIBLE_DIR, "postacie", "kalina.md")
        with open(bad, "w", encoding="utf-8") as f:
            f.write("---\n{zepsuty json}\n---\nproza\n")
        braki2 = bible.validate_canon()
        check("walidator wykrywa zepsuty frontmatter", any("zepsuty frontmatter" in x for x in braki2))

    finally:
        shutil.rmtree(work, ignore_errors=True)

    print()
    if FAILS:
        print(f"NIEPOWODZENIA ({len(FAILS)}): " + ", ".join(FAILS))
        return 1
    print("Wszystkie testy OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
