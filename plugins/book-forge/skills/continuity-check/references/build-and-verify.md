# Write-back kanonu i walidacja

Jeden wynik: aktualizacja **kanonu-wiki** `.book-forge/biblia/**/*.md` (tylko RUNTIME, przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`). Ten etap **nie tworzy plików raportu** — werdykt i historia bramki żyją w biblii (`log_ciaglosci` w `log.md`), a podsumowanie dla autora idzie do czatu.

## Najpierw konflikty (RO) — decyzja autora

Jeśli `plan.konflikty` niepuste, rozstrzygnij je z autorem PRZED zapisem. Pól RO skrypt nie tyka — zmianę RO wprowadza autor ręcznie, za swoją zgodą (jawny `bible.write_entity`/`write_section`). Nierozstrzygnięte konflikty zostają w `log_ciaglosci` jako „do rozstrzygnięcia”.

## Write-back (deterministyczny, tylko RUNTIME)

Zapis wykonuje skrypt, nie agent, i przechodzi **wyłącznie przez `bible.py`** — biblioteka egzekwuje RO→CONFLICT (`update_runtime` odmawia pól spoza listy dozwolonych pól RUNTIME) i atomowość per-plik. Kolejność: dane → **`append_log` JAKO OSTATNI** (znacznik „bramka domknięta”; przerwany przebieg bez wpisu w logu jest bezpieczny do powtórzenia — operacje są idempotentne dzięki dedup). Na końcu audyt: pola RO nie mogły się zmienić.

```bash
python3 - "$PLAN_JSON" "$PLUGIN_ROOT" << 'PY'
import hashlib, json, sys, os
sys.path.insert(0, os.path.join(sys.argv[2], "scripts"))
import bible
plan = json.load(open(sys.argv[1], encoding="utf-8"))   # obiekt {id, plan:{zapis, log, konflikty, streszczenie}}
sid = plan["id"]; z = plan["plan"]["zapis"]; log = plan["plan"]["log"]

# Audyt RO jest teraz w bibliotece (bible.ro_snapshot / assert_ro_unchanged) — gwarancja po stronie biblioteki, nie skryptu
ro_before = bible.ro_snapshot()
konflikty_ro = []

# 1. fakty — append z auto-id (F) i dedup po tresc+zrodlo_scena (ponowne przejście nie duplikuje)
for f in z.get("fakty", []):
    bible.append_record("fakty", {"RUNTIME": True, "tresc": f.get("tresc",""), "typ": f.get("typ","swiat"),
        "zrodlo_scena": f.get("zrodlo_scena", sid), "pewnosc": f.get("pewnosc","roboczy"),
        "zrodlo_ref": f.get("zrodlo_ref","")})

# 2. nowe nazwy → glosariusz (merge-not-clobber: istniejąca nazwa nie jest duplikowana);
#    rozbieżna odmiana/opis istniejącej nazwy wraca w `conflicts` — ujawnienie, nie cisza
for nz in z.get("nazwy", []):
    if nz.get("nazwa"):
        r = bible.write_entity("glosariusz", {"nazwa": nz["nazwa"], "kategoria": nz.get("kategoria",""),
            "odmiana": nz.get("odmiana", {}), "warianty_zakazane": nz.get("warianty_zakazane", []),
            "opis": nz.get("opis","")})
        for c in r.get("conflicts", []):
            konflikty_ro.append({"status": "CONFLICT", "nazwa": nz["nazwa"], **c})

# 3. stan postaci (_stan, RUNTIME) — update_runtime egzekwuje RO→CONFLICT,
#    a brak takiej postaci w kanonie → MISS (zła nazwa nie wysadza write-backu)
for s in z.get("stan", []):
    if s.get("postac") and s.get("pole"):
        r = bible.update_runtime("postac", s["postac"], "_stan." + s["pole"], s.get("wartosc",""))
        if r.get("status") in ("CONFLICT", "MISS"):
            konflikty_ro.append(r)

# 4. oś czasu — update-or-append po scena;  5. zasiewy — update-or-append po id
for o in z.get("os_czasu", []):
    bible.append_record("os_czasu", {"RUNTIME": True, **o})
for sp in z.get("setup_payoff", []):
    bible.append_record("setup_payoff", {"RUNTIME": True, **sp})

# 6. status sceny w kanonie fabularnym
bible.set_scene_status(sid, "zweryfikowana")

# 6b. streszczenie sceny → agregat (update-or-append po scenie; hash prozy pozwala
#     konsumentom wykryć nieaktualność po polish-pl). Bramka i tak czytała prozę.
streszczenie = plan["plan"].get("streszczenie", "")
proza_path = bible.work_path("sceny", sid + ".md")
if streszczenie and os.path.exists(proza_path):
    proza = open(proza_path, encoding="utf-8").read()
    bible.append_record("streszczenia", {"RUNTIME": True, "scena": sid,
        "streszczenie": streszczenie, "slowa": len(proza.split()),
        "hash": hashlib.sha256(proza.encode("utf-8")).hexdigest()[:12]})

# 7. log ciaglosci — JAKO OSTATNI (znacznik domknięcia bramki)
bible.append_log({"RUNTIME": True, **log})
bible.render_index()

bible.assert_ro_unchanged(ro_before)   # rzuca, gdyby write-back tknął jakiekolwiek pole RO
print("write-back OK:", sid, "| werdykt:", log.get("werdykt"),
      "| faktów+", len(z.get("fakty",[])), "nazw+", len(z.get("nazwy",[])),
      ("| NIEZAPISANE (RO→CONFLICT / brak encji MISS): " + str(len(konflikty_ro))) if konflikty_ro else "")
PY
```

`append_record`/`update_runtime`/`render_index` same regenerują treść stron i `index.md` — nie ma osobnej regeneracji widoku.

## Podsumowanie dla autora (czat, bez plików)

Po write-backu pokaż autorowi w czacie: werdykt (PASS/CONFLICT), konflikty RO do rozstrzygnięcia (pole — co mówi scena vs co biblia — rekomendacja), liczbę dopisanych faktów/nazw oraz zasiewy bez wypłaty. Pełna historia jest w biblii (`log_ciaglosci`); nie zapisuj osobnego raportu.

## Walidacja (obowiązkowa)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bible.py validate && echo "kanon-wiki OK"
```

Audyt RO jest **wbudowany w skrypt** (`assert ro_snapshot() == ro_before` — przerwie zapis, gdyby jakiekolwiek pole RO uległo zmianie). Dodatkowo: każdy fakt ma id i `zrodlo_scena`; każda nowa nazwa ma odmianę (sprawdza `bible.py validate`). Werdykt CONFLICT → upewnij się, że nie zapisano nic spornego, a sprawa jest w logu.
