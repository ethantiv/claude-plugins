#!/usr/bin/env python3
"""book-forge — echo-hunter: detektor powtórzeń frazowych w maszynopisie.

Proza generowana scena po scenie w osobnych sesjach nieuchronnie powiela frazy —
to najbardziej rozpoznawalny ślad maszynopisu AI i pierwsza rzecz, którą wyłapie
redaktor wydawnictwa. Skrypt skanuje całość deterministycznie (zero kosztu LLM):

- n-gramy 3-5 słów powtórzone między scenami (lub ≥3× w jednej),
- słowa-ulubieńce (częstość na 10 tys. słów ponad próg),
- powtórzone otwarcia akapitów (pierwsze 4 słowa).

Standalone, tylko biblioteka standardowa. Wejście: katalog scen
(`.book-forge/sceny/`, pliki po id z siatki) albo `ksiazka.md` (cięta po
nagłówkach `##`). Wyjście: raport tekstowy albo JSON z kluczem `per_scena`
(zasila `redakcja-todo.md` w assemble-book). Exit 0 = czysto, 1 = są znaleziska.
"""

import argparse
import json
import os
import re
import sys

# ~80 najczęstszych polskich słów funkcyjnych — n-gram złożony wyłącznie z nich
# ("i to nie jest") to szum językowy, nie echo autorskie
STOPWORDS = {
    "a", "aby", "ale", "ani", "az", "aż", "bardzo", "bez", "bo", "by", "byc", "być",
    "byl", "był", "byla", "była", "bylo", "było", "co", "cos", "coś", "czy", "dla",
    "do", "gdy", "gdzie", "go", "i", "ich", "im", "ja", "jak", "jakby", "jako", "je",
    "jego", "jej", "jest", "jeszcze", "jesli", "jeśli", "juz", "już", "kiedy", "kto",
    "ktora", "która", "ktore", "które", "ktory", "który", "lecz", "lub", "ma", "mi",
    "mial", "miał", "miala", "miała", "mnie", "moze", "może", "mu", "na", "nad", "nawet",
    "nic", "nie", "niz", "niż", "o", "od", "ona", "one", "oni", "ono", "po", "pod",
    "potem", "przed", "przez", "przy", "sie", "się", "swoje", "ta", "tak", "takze",
    "także", "tam", "te", "tego", "tej", "ten", "teraz", "to", "tu", "tylko", "tym",
    "u", "w", "we", "wiec", "więc", "wszystko", "z", "za", "ze", "że", "zeby", "żeby",
}


def tokenize(text):
    return re.findall(r"[a-ząćęłńóśźż0-9]+", text.lower())


def _glossary_forms():
    """Wszystkie formy odmiany nazw z glosariusza biblii (fail-soft: brak biblii
    lub bible.py ⇒ pusty zbiór — ulubieńcy po prostu nie są filtrowani)."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import bible
        forms = set()
        for slug in bible.list_entities("glosariusz"):
            fm, _ = bible.read_entity("glosariusz", slug)
            for v in (fm.get("odmiana") or {}).values():
                if v:
                    forms.update(tokenize(v))
            if fm.get("nazwa"):
                forms.update(tokenize(fm["nazwa"]))
        return forms
    except Exception:  # noqa: BLE001 — diagnostyka, nie bramka
        return set()


def segment(sceny_dir=None, ksiazka=None):
    """→ [(id, text)]. Katalog scen: pliki <id>.md bez .qa/.v* (notatki QA i stare
    wersje zawyżyłyby liczniki). ksiazka.md: cięcie po nagłówkach ##/###."""
    if sceny_dir:
        out = []
        for name in sorted(os.listdir(sceny_dir)):
            if not name.endswith(".md") or re.search(r"\.(qa|v\d+)\.md$", name):
                continue
            with open(os.path.join(sceny_dir, name), encoding="utf-8") as f:
                out.append((name[:-3], f.read()))
        return out
    with open(ksiazka, encoding="utf-8") as f:
        text = f.read()
    parts = re.split(r"^(#{2,3} .+)$", text, flags=re.MULTILINE)
    if len(parts) == 1:
        return [("ksiazka", text)]
    out, head = [], "poczatek"
    if parts[0].strip():
        out.append((head, parts[0]))
    for i in range(1, len(parts) - 1, 2):
        out.append((parts[i].lstrip("# ").strip()[:40], parts[i + 1]))
    return out


def ngram_repeats(scenes, nmin, nmax):
    """N-gramy obecne w ≥2 scenach albo ≥3× w jednej; od najdłuższych, bez
    fraz zawartych w już zgłoszonej dłuższej; bez fraz z samych stopwords."""
    toks = {sid: tokenize(t) for sid, t in scenes}
    found, reported = [], []
    for n in range(nmax, nmin - 1, -1):
        counts = {}
        for sid, tk in toks.items():
            for i in range(len(tk) - n + 1):
                g = " ".join(tk[i:i + n])
                counts.setdefault(g, {}).setdefault(sid, 0)
                counts[g][sid] += 1
        for g, per in counts.items():
            total = sum(per.values())
            if not (len(per) >= 2 or total >= 3):
                continue
            if all(w in STOPWORDS for w in g.split()):
                continue
            if any(g in longer for longer in reported):
                continue
            reported.append(g)
            found.append({"fraza": g, "n": n, "razem": total,
                          "gdzie": [{"scena": s, "ile": c} for s, c in sorted(per.items())]})
    found.sort(key=lambda x: (-x["razem"], -x["n"]))
    return found


def favorite_words(scenes, prog, glossary):
    """Słowa ≥5 znaków (poza stopwords i glosariuszem) z częstością na 10 tys.
    słów powyżej progu — kandydaci na słowa-ulubieńce („spojrzała", „cień")."""
    counts, per_scene, total = {}, {}, 0
    for sid, t in scenes:
        for w in tokenize(t):
            total += 1
            if len(w) < 5 or w in STOPWORDS or w in glossary:
                continue
            counts[w] = counts.get(w, 0) + 1
            per_scene.setdefault(w, set()).add(sid)
    if not total:
        return []
    out = []
    for w, c in counts.items():
        na_10k = round(c * 10000 / total, 1)
        if na_10k > prog and c >= 3:
            out.append({"slowo": w, "na_10k": na_10k, "prog": prog, "razem": c,
                        "sceny": sorted(per_scene[w])})
    out.sort(key=lambda x: -x["na_10k"])
    return out


def paragraph_openings(scenes, k=4, min_count=3):
    """Identyczne otwarcia akapitów (pierwsze k słów) ≥ min_count razy w całości."""
    counts = {}
    for sid, t in scenes:
        for par in re.split(r"\n\s*\n", t):
            tk = tokenize(par)
            if len(tk) < k:
                continue
            op = " ".join(tk[:k])
            counts.setdefault(op, []).append(sid)
    out = []
    for op, sids in counts.items():
        if len(sids) >= min_count and not all(w in STOPWORDS for w in op.split()):
            out.append({"otwarcie": op, "ile": len(sids), "sceny": sorted(set(sids))})
    out.sort(key=lambda x: -x["ile"])
    return out


def build_report(scenes, nmin, nmax, prog, top):
    glossary = _glossary_forms()
    ngramy = ngram_repeats(scenes, nmin, nmax)[:top]
    ulubience = favorite_words(scenes, prog, glossary)[:top]
    otwarcia = paragraph_openings(scenes)

    per_scena = {}
    for f in ngramy:
        for g in f["gdzie"]:
            per_scena.setdefault(g["scena"], {"ngramy": [], "ulubience": [], "otwarcia": 0})
            per_scena[g["scena"]]["ngramy"].append(f["fraza"])
    for u in ulubience:
        for sid in u["sceny"]:
            per_scena.setdefault(sid, {"ngramy": [], "ulubience": [], "otwarcia": 0})
            per_scena[sid]["ulubience"].append(u["slowo"])
    for o in otwarcia:
        for sid in set(o["sceny"]):
            per_scena.setdefault(sid, {"ngramy": [], "ulubience": [], "otwarcia": 0})
            per_scena[sid]["otwarcia"] += 1

    return {
        "sceny": len(scenes),
        "slowa": sum(len(tokenize(t)) for _, t in scenes),
        "ngramy": ngramy,
        "ulubience": ulubience,
        "otwarcia": otwarcia,
        "per_scena": per_scena,
    }


def render_text(r):
    lines = [f"echo-hunter: {r['sceny']} scen, {r['slowa']} słów"]
    if r["ngramy"]:
        lines.append(f"\nPowtórzone frazy ({len(r['ngramy'])}):")
        for f in r["ngramy"]:
            gdzie = ", ".join(f"{g['scena']}×{g['ile']}" for g in f["gdzie"])
            lines.append(f"  „{f['fraza']}” — {f['razem']}× ({gdzie})")
    if r["ulubience"]:
        lines.append(f"\nSłowa-ulubieńcy ({len(r['ulubience'])}):")
        for u in r["ulubience"]:
            lines.append(f"  {u['slowo']} — {u['na_10k']}/10k słów ({u['razem']}×, próg {u['prog']})")
    if r["otwarcia"]:
        lines.append(f"\nPowtórzone otwarcia akapitów ({len(r['otwarcia'])}):")
        for o in r["otwarcia"]:
            lines.append(f"  „{o['otwarcie']}…” — {o['ile']}× ({', '.join(o['sceny'])})")
    if not (r["ngramy"] or r["ulubience"] or r["otwarcia"]):
        lines.append("Czysto — brak ech wartych uwagi.")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Detektor powtórzeń frazowych w maszynopisie")
    ap.add_argument("--sceny", help="katalog z prozą scen (domyślnie .book-forge/sceny, jeśli istnieje)")
    ap.add_argument("--ksiazka", help="złożony maszynopis (fallback: ksiazka.md)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-ngram", type=int, default=3)
    ap.add_argument("--max-ngram", type=int, default=5)
    ap.add_argument("--prog-ulubieniec", type=float, default=4.0,
                    help="próg częstości na 10 tys. słów")
    ap.add_argument("--top", type=int, default=25)
    a = ap.parse_args(argv)

    sceny_dir, ksiazka = a.sceny, a.ksiazka
    if not sceny_dir and not ksiazka:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import bible
            kandydat_sceny, kandydat_ksiazka = bible.work_path("sceny"), bible.book_path("ksiazka.md")
        except Exception:  # noqa: BLE001
            kandydat_sceny, kandydat_ksiazka = os.path.join(".book-forge", "sceny"), "ksiazka.md"
        if os.path.isdir(kandydat_sceny):
            sceny_dir = kandydat_sceny
        elif os.path.exists(kandydat_ksiazka):
            ksiazka = kandydat_ksiazka
        else:
            print("brak wejścia: ani katalogu scen, ani ksiazka.md (użyj --sceny/--ksiazka)")
            return 2

    scenes = segment(sceny_dir=sceny_dir, ksiazka=ksiazka)
    if not scenes:
        print("brak tekstu do analizy")
        return 2

    report = build_report(scenes, a.min_ngram, a.max_ngram, a.prog_ulubieniec, a.top)
    print(json.dumps(report, ensure_ascii=False, indent=2) if a.json else render_text(report))
    return 1 if (report["ngramy"] or report["ulubience"] or report["otwarcia"]) else 0


if __name__ == "__main__":
    sys.exit(main())
