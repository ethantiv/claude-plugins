#!/usr/bin/env python3
"""Test detektora powtórzeń (scripts/echo.py) na syntetycznych mini-scenach.

Uruchom: python3 scripts/tests/test_echo.py
"""
import json
import os
import shutil
import subprocess
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


# wstrzyknięte echa: 4-gram „wzruszył ramionami bez słowa", ulubieniec „spojrzała",
# powtórzone otwarcie akapitu „kalina spojrzała na drzwi"
SCENA_1 = """Kalina spojrzała na drzwi archiwum. Strażnik wzruszył ramionami bez słowa.

Kurz osiadał na półkach. Spojrzała na mapę i spojrzała raz jeszcze, niepewna.

Kalina spojrzała na drzwi, zanim wyszła na targ."""

SCENA_2 = """Kalina spojrzała na drzwi Cytadeli. Eron wzruszył ramionami bez słowa i odszedł.

Wiatr niósł piasek. Spojrzała w stronę wydm, gdzie czekała karawana."""

SCENA_3 = """Burza nadciągała od wschodu. Kalina spojrzała na drzwi schronu.

Przewodnik wzruszył ramionami bez słowa. Spojrzała na zegar i policzyła godziny."""


def main():
    import echo

    check("tokenize: polskie znaki", echo.tokenize("Żółć, jaźń!") == ["żółć", "jaźń"])

    work = tempfile.mkdtemp(prefix="echo-test-")
    try:
        sc_dir = os.path.join(work, "sceny")
        os.makedirs(sc_dir)
        for sid, txt in (("R1S1", SCENA_1), ("R1S2", SCENA_2), ("R2S1", SCENA_3)):
            with open(os.path.join(sc_dir, sid + ".md"), "w", encoding="utf-8") as f:
                f.write(txt)
        # plik QA nie może wejść do analizy
        with open(os.path.join(sc_dir, "R1S1.qa.md"), "w", encoding="utf-8") as f:
            f.write("wzruszył ramionami bez słowa " * 20)

        scenes = echo.segment(sceny_dir=sc_dir)
        check("segment: 3 sceny (bez .qa.md)", [s for s, _ in scenes] == ["R1S1", "R1S2", "R2S1"],
              str([s for s, _ in scenes]))

        rep = echo.build_report(scenes, 3, 5, 4.0, 25)
        frazy = [f["fraza"] for f in rep["ngramy"]]
        check("ngram: wykryty wstrzyknięty 4-gram", any("wzruszył ramionami bez słowa" in f for f in frazy),
              str(frazy[:5]))
        check("ngram: krótsza fraza zawarta w dłuższej niezdublowana",
              not any(f == "wzruszył ramionami bez" for f in frazy), str(frazy[:8]))

        ulub = [u["slowo"] for u in rep["ulubience"]]
        check("ulubieniec: spojrzała wykryta", "spojrzała" in ulub, str(ulub))

        check("otwarcia: powtórzone otwarcie akapitu",
              any(o["otwarcie"].startswith("kalina spojrzała na drzwi") for o in rep["otwarcia"]),
              str(rep["otwarcia"]))

        check("per_scena: scena z echem ma wpis", "R1S1" in rep["per_scena"], str(rep["per_scena"].keys()))

        # segmentacja ksiazka.md po nagłówkach
        ks = os.path.join(work, "ksiazka.md")
        with open(ks, "w", encoding="utf-8") as f:
            f.write("# Tytuł\n\n## Rozdział 1\n\n" + SCENA_1 + "\n\n## Rozdział 2\n\n" + SCENA_2 + "\n")
        segs = echo.segment(ksiazka=ks)
        check("segment ksiazka.md: cięcie po ##", len(segs) >= 2, str([s for s, _ in segs]))

        # CLI: exit 1 przy znaleziskach, poprawny JSON
        proc = subprocess.run([sys.executable, os.path.join(SCRIPTS, "echo.py"),
                               "--sceny", sc_dir, "--json"],
                              capture_output=True, text=True)
        check("CLI: exit 1 przy echach", proc.returncode == 1, f"rc={proc.returncode} err={proc.stderr[:200]}")
        cli_rep = json.loads(proc.stdout)
        check("CLI: JSON z per_scena", "per_scena" in cli_rep and cli_rep["sceny"] == 3)

        # czysty tekst → exit 0
        clean = os.path.join(work, "czyste")
        os.makedirs(clean)
        with open(os.path.join(clean, "R1S1.md"), "w", encoding="utf-8") as f:
            f.write("Jedno krótkie zdanie bez powtórzeń tutaj.")
        proc2 = subprocess.run([sys.executable, os.path.join(SCRIPTS, "echo.py"), "--sceny", clean],
                               capture_output=True, text=True)
        check("CLI: exit 0 gdy czysto", proc2.returncode == 0, f"rc={proc2.returncode} out={proc2.stdout[:200]}")
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
