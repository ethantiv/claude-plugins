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
    for sec in ("os_czasu", "streszczenia", "setup_payoff", "fakty", "zrodla"):
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
        # work_path/book_path liczą ścieżki względem CWD — w teście kieruj je do tempdir,
        # żeby check_stage/book_status nie czytały (ani nie śmieciły) w katalogu repo
        bible.BOOK_DIR = work
        bible.WORK_DIR = os.path.join(work, ".book-forge/")

        original = json.load(open(os.path.join(HERE, "fixture-biblia.json"), encoding="utf-8"))

        # 2. zbuduj kanon przez publiczne API (tą samą drogą co skill book-bible)
        _populate(bible, original)
        check("setup: layout postacie", len(bible.list_entities("postac")) == 2)
        check("setup: layout glosariusz", len(bible.list_entities("glosariusz")) == 3)

        # 3. round-trip kształtu (NAJWAŻNIEJSZY)
        loaded = bible.load_all()
        check("round-trip kształtu == fixture", _norm(loaded) == _norm(original),
              "load_all() różni się od oryginału")
        check("round-trip: 17 sekcji", set(loaded) == set(original))
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

        # 5c'. streszczenia: update-or-append po (scena,) — ponowna bramka aktualizuje, nie dubluje
        s1 = bible.append_record("streszczenia", {"RUNTIME": True, "scena": "R1S2",
                                                  "streszczenie": "Eron gubi trop.", "slowa": 900, "hash": "h1"})
        check("streszczenia: append nowej sceny", s1["action"] == "append", str(s1))
        s2 = bible.append_record("streszczenia", {"RUNTIME": True, "scena": "R1S2",
                                                  "streszczenie": "Eron gubi trop, ale znajduje mapę.", "slowa": 1050, "hash": "h2"})
        check("streszczenia: update po rewizji (ta sama scena)", s2["action"] == "update", str(s2))
        st = bible.load_all()["streszczenia"]
        check("streszczenia: brak duplikatu sceny", len([x for x in st if x["scena"] == "R1S2"]) == 1)
        check("streszczenia: treść zaktualizowana",
              [x for x in st if x["scena"] == "R1S2"][0]["hash"] == "h2")

        # 5c''. update_meta: whitelist RUNTIME singletonu meta
        m1 = bible.update_meta("liczba_scen", 4)
        check("update_meta liczba_scen = WRITE", m1["status"] == "WRITE", str(m1))
        m2 = bible.update_meta("budzet_slow", 90000)
        check("update_meta budzet_slow = WRITE", m2["status"] == "WRITE", str(m2))
        meta_po = bible.load_all()["meta"]
        check("update_meta zapisał oba pola", meta_po.get("liczba_scen") == 4 and meta_po.get("budzet_slow") == 90000)
        check("update_meta nie clobberuje reszty meta", meta_po.get("tytul") == "Pył i Pamięć")
        m3 = bible.update_meta("tytul", "Nowy tytuł")
        check("update_meta pole RO → CONFLICT", m3["status"] == "CONFLICT", str(m3))
        check("update_meta RO niezmienione", bible.load_all()["meta"]["tytul"] == "Pył i Pamięć")

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

        check("update_meta MISS bez meta.md", bible.update_meta("liczba_scen", 1)["status"] == "MISS")

        imp = bible.import_published(tom1_dir)
        check("seria: import_published OK", imp["status"] == "OK" and imp["stron"] > 0, str(imp))
        names = [p["imie"] for p in bible.load_all().get("postacie", [])]
        check("seria: tom 2 widzi postać dziedziczoną", "Kalina" in names, str(names))
        check("seria: dziedziczone encje oznaczone _inherited",
              all(p.get("_inherited") for p in bible.load_all()["postacie"]))
        r = bible.write_entity("postac", {"imie": "Kalina", "opis_fizyczny": "inna"})
        check("seria: write_entity na dziedziczonej → INHERITED_RO", r.get("status") == "INHERITED_RO", str(r))

        # regresja: index tomu 2 linkuje encje dziedziczone — walidator nie może
        # zgłaszać wiszących wikilinków (strony żyją w _dziedziczone/)
        bible.render_index()
        braki_t2 = bible.validate_canon()
        check("seria: walidator czysty w tomie 2 po render_index", braki_t2 == [], "; ".join(braki_t2))

        # copy-on-write: RUNTIME dziedziczonej postaci materializuje stronę własną,
        # RO zostaje verbatim, a warstwa _dziedziczone/ jest nietknięta
        u = bible.update_runtime("postac", "Kalina", "_stan.lokalizacja", "Pas Łomów II")
        check("seria: update_runtime copy-on-write → WRITE", u.get("status") == "WRITE" and u.get("zmaterializowano"), str(u))
        own_kalina = os.path.join(tom2_dir, "postacie", "kalina.md")
        check("seria: strona własna zmaterializowana", os.path.exists(own_kalina))
        kalina2 = [p for p in bible.load_all()["postacie"] if p["imie"] == "Kalina"][0]
        check("seria: RUNTIME spatchowany po materializacji", kalina2["_stan"]["lokalizacja"] == "Pas Łomów II")
        check("seria: RO dziedziczonej Kaliny niezmienione", kalina2["opis_fizyczny"] == "drobna, blizna na dłoni")
        check("seria: zmaterializowana strona bez _inherited", not kalina2.get("_inherited"))
        inh_fm, _ = bible._read_page(os.path.join("_dziedziczone", "postacie", "kalina.md"))
        check("seria: warstwa _dziedziczone nietknięta",
              inh_fm["_stan"]["lokalizacja"] == "Cytadela" and inh_fm.get("_inherited") is True, str(inh_fm))
        check("seria: walidator czysty po materializacji", bible.validate_canon() == [])
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

        # 6a. book_path/work_path — układ katalogów trybu serii
        old_book, old_work = bible.BOOK_DIR, bible.WORK_DIR
        bible.BOOK_DIR, bible.WORK_DIR = "tom-02/", "tom-02/.book-forge/"
        check("book_path w trybie serii", bible.book_path("ksiazka.md") == os.path.join("tom-02/", "ksiazka.md"))
        check("work_path w trybie serii",
              bible.work_path("sceny", "T2R1S1.md") == os.path.join("tom-02/.book-forge/", "sceny", "T2R1S1.md"))
        bible.BOOK_DIR = ""
        check("book_path pojedynczej książki", bible.book_path("ksiazka.md") == "ksiazka.md")
        bible.BOOK_DIR, bible.WORK_DIR = old_book, old_work

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

        # 6b. check_stage: preflight wejścia etapów (na kanonie z fixture, bez plików prozy)
        cs = bible.check_stage("write-scene")
        check("check_stage write-scene OK (siatka kompletna)", cs["ok"], "; ".join(cs["braki"]))
        cs = bible.check_stage("revise-scene")
        check("check_stage revise-scene bez id → brak", not cs["ok"] and any("podaj id" in x for x in cs["braki"]), str(cs))
        cs = bible.check_stage("revise-scene", "R1S1")
        check("check_stage revise-scene bez prozy → brak", not cs["ok"], str(cs))
        cs = bible.check_stage("outline")
        check("check_stage outline bez pomysl.json → brak", not cs["ok"], str(cs))
        cs = bible.check_stage("publishing-package")
        check("check_stage publishing bez ksiazka.md → brak", not cs["ok"], str(cs))
        raised_cs = False
        try:
            bible.check_stage("nieznany-etap")
        except ValueError:
            raised_cs = True
        check("check_stage nieznany etap → ValueError", raised_cs)

        # napisz prozę R1S1 → preflight revise-scene przechodzi, a status ją widzi
        sc_dir = bible.work_path("sceny")
        os.makedirs(sc_dir, exist_ok=True)
        with open(os.path.join(sc_dir, "R1S1.md"), "w", encoding="utf-8") as f:
            f.write("Kalina weszła do archiwum portu. " * 50)
        check("check_stage revise-scene z prozą OK", bible.check_stage("revise-scene", "R1S1")["ok"])

        # 6c. book_status: dashboard
        st = bible.book_status()
        check("status: tytuł i kanon", st["tytul"] == "Pył i Pamięć" and st["kanon"] in ("working", "published"))
        check("status: sceny razem", st["sceny"]["razem"] == 4, str(st["sceny"]))
        check("status: słowa policzone i budżet z meta",
              st["slowa"]["per_scena"].get("R1S1", 0) > 0 and st["slowa"]["budzet"] == 90000)
        check("status: procent budżetu", isinstance(st["slowa"]["procent"], int))
        check("status: otwarte zasiewy nie zawierają domkniętych",
              all(z["id"] != "SP01" for z in st["zasiewy_otwarte"]), str(st["zasiewy_otwarte"]))
        with open(bible.work_path("korekta-R1S1.md"), "w", encoding="utf-8") as f:
            f.write("# korekta\n")
        st2 = bible.book_status()
        check("status: korekta-<id>.md ⇒ wygladzona", st2["sceny"]["wg_statusu"].get("wygladzona", 0) == 1,
              str(st2["sceny"]["wg_statusu"]))

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

        # 7c. urwany frontmatter (--- bez domknięcia) → ValueError, walidator raportuje
        with open(bad, "w", encoding="utf-8") as f:
            f.write('---\n{"imie": "Kalina"}\n')
        braki3 = bible.validate_canon()
        check("walidator wykrywa urwany frontmatter", any("bez domknięcia" in x for x in braki3), "; ".join(braki3))
        raised_fm = False
        try:
            bible._split_frontmatter('---\n{"a": 1}\n')
        except ValueError:
            raised_fm = True
        check("_split_frontmatter rzuca na urwanej stronie", raised_fm)

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
