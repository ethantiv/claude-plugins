# Budowa raportu HTML i walidacja — idea-spark

Szablon: `${CLAUDE_PLUGIN_ROOT}/skills/idea-spark/assets/idea-spark-template.html`. Ma 3
placeholdery tekstowe i jeden punkt wstrzyknięcia danych. Trzy zakładki: **„Trzon wizji"**
(stały fundament autora — kierunek, bohaterowie, świat), **„5 fabuł"** (warianty fabuły w ramach
trzonu) i **„Werdykt"** — bez bestsellerów i luk rynkowych (to wariant bez badania rynku).

## Placeholdery tekstowe

- `{{GENRE}}` — gatunek (np. „science fiction”), występuje kilka razy.
- `{{READER}}` — opis docelowego czytelnika.
- `{{YEAR}}` — rok danych (np. „2026”).

## Punkt wstrzyknięcia danych

W szablonie jest punkt: `const DATA = /*__INJECT_DATA__*/ null;`. Dane `DATA` (po polsku, po
redakcji i humanizerze) zapisz jako **plik JSON** i wstrzyknij skryptem z sekcji „Wstrzyknięcie”
(przez `json.dumps`) — nie sklejaj literału ręcznie.

## Kształt obiektu DATA (dokładnie taki — JS render tego oczekuje)

```javascript
const DATA = {
  ideas: [ {
    t:"",            // POLSKI tytuł roboczy
    en:"",           // oryginał roboczy (podtytuł „oryg. …”)
    score:7.3,       // średnia ocena (kropka — JS sam zamieni na przecinek)
    winner:true,     // dokładnie jeden true
    runner:true,     // dokładnie jeden true (wicemistrz); pozostałe pomiń pole
    log:"",          // logline (kursywa)
    silnik:"",       // silnik premisy — strukturalna sprzeczność napędzająca konflikt
    op:"",           // streszczenie
    hook:"",         // haczyk (może mieć <b>…</b>)
    comps:["",""],   // orientacyjne tytuły porównawcze (z wiedzy, nie weryfikowane w sieci)
    protagonista:"", // profil bohatera (np. „kobieta, ~40, była śledcza") — niesie decyzję do outline/book-bible
    votes:[ ["Redaktor prowadzący",7.4], ["Marketing",7.5], ["Czytelnik docelowy",7.4], ["Adwokat innowacji",7.6] ]
  } ],                                                // 5 fabuł (wspólny trzon, różne fabuły)
  trzon: {           // STAŁY trzon autora — TYLKO do panelu „Trzon wizji" w HTML; NIE trafia do pomysl.json (kontrakt!)
    dramaticQ:"", theme:"", emotion:"",          // kierunek i temat
    antagonist:"", relation:"", arc:"",          // bohaterowie (poza profilem protagonisty — ten jest w brief)
    setting:"", realism:"", mood:"", scale:"",   // świat
    ramy:{ conflictType:"", ending:"", pace:"", seed:"" }  // ramy fabuły (preferencje, nie gotowa fabuła)
  },
  brief: {           // brief autora z Kroku 1 — dziedziczony przez outline (etap 2) i book-bible (etap 3)
    subgenre:"",     // podgatunek/nurt (warstwa adaptacyjna) lub '' (bez preferencji)
    conventions:[],  // konwencje/obietnice gatunkowe (multiSelect) lub []
    protagonist:"",  // 'kobieta' | 'mezczyzna' | 'zroznicuj' | 'dowolny'
    protAge:"",      // np. '30-45' lub '' (bez preferencji)
    protType:"",     // opcjonalny typ/rola bohatera lub ''
    form:"",         // non-fiction: 'poradnik'|'reportaz'|'esej'|'pamietnik'; '' = fikcja
    format:"",       // 'pojedyncza' | 'trylogia' | 'seria'
    tone:"", spice:"", taboo:[], market:""
  },
  verdict: {
    title:"",        // = winnerTitle (po polsku)
    titleEn:"",      // = en zwycięskiego pomysłu
    score:"Średnia 7,5 &bull; najwyższa w stawce (7,4 / 7,5 / 7,4 / 7,6)",
    rationale:"", warn:"", whyNow:"",
    steps:["",""],   // kroki dla autora
    runner:"",       // tytuł wicemistrza (po polsku)
    runnerEn:"",     // oryginał wicemistrza
    runnerWhy:""
  }
};
```

> Brak `books`, `obs`, `gaps` — to świadoma różnica względem `market-report`. Pomysły **nie
> mają** pola `gap` (nie ma luk rynkowych do których celują), więc go nie dodawaj.

## Mapowanie z wyniku roju

Rój zwraca `{ ideas:[...], winner:{...}, brief:{...}, trzon:{...} }`.

- `DATA.ideas` ← `ideas` (każdy): `score` ← `avgScore`; `silnik` ← `silnik` (przepisz 1:1);
  `protagonista` ← `protagonista`
  (przepisz 1:1); `votes` ← sparuj oceny z nazwami sędziów **w kolejności**:
  `["Redaktor prowadzący","Marketing","Czytelnik docelowy","Adwokat innowacji"]`. Ustaw `winner:true` na pozycji,
  której `t` odpowiada `winner.winnerTitle` (fallback: najwyższe `avgScore`); ustaw `runner:true`
  tam, gdzie `t` = `winner.runnerTitle`. Kolejność tablicy `ideas` ustala „kolejność roboczą"
  w UI (sortowanie domyślne jest po ocenie).
- `DATA.trzon` ← `trzon` (przepisz 1:1). To **tylko** materiał na panel „Trzon wizji" — puste
  pola pomiń (render je opuszcza). **NIE kopiuj `trzon` do `pomysl.json`** (Krok 5 SKILL.md) —
  jego treść jest już wtopiona w `idea.op/silnik/protagonista` zwycięzcy.
- `DATA.brief` ← `brief` (przepisz 1:1 — to dane sterujące, NIE redaguj). To kanał
  dziedziczenia decyzji autora do outline i book-bible.
- `DATA.verdict`: `title`←`winner.winnerTitle`, `titleEn`← `en` zwycięskiego pomysłu,
  `rationale`←`winner.rationale`, `warn`←`winner.warning`, `whyNow`←`winner.whyNow`,
  `steps`←`winner.nextSteps`, `runner`←`winner.runnerTitle`, `runnerEn`← `en` wicemistrza,
  `runnerWhy`←`winner.runnerWhy`. Pole `score` złóż ręcznie z oceny zwycięzcy.

## Wstrzyknięcie (rzetelna metoda — przez plik, nie ręczne sklejanie)

Zapisz `DATA` jako **plik JSON** (`$DATA_JSON`) — strict JSON: klucze i napisy w cudzysłowie
prostym, bez przecinków na końcu, bez komentarzy. Python wstrzykuje go przez `json.dumps`, więc
cudzysłowy i znaki specjalne w treści są eskejpowane automatycznie. Przykład:

```bash
python3 - "$TEMPLATE" "$DATA_JSON" "$OUT" "$GENRE" "$READER" "$YEAR" << 'PY'
import sys, json
tpl, dataf, out, genre, reader, year = sys.argv[1:7]
s = open(tpl, encoding='utf-8').read()
data = json.load(open(dataf, encoding='utf-8'))      # plik JSON (nie literał JS) — json.dumps zadba o eskejpowanie
js = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')   # zabezpiecz przed </script> w treści
s = s.replace('const DATA = /*__INJECT_DATA__*/ null;', 'const DATA = ' + js + ';')
s = s.replace('{{GENRE}}', genre).replace('{{READER}}', reader).replace('{{YEAR}}', year)
open(out, 'w', encoding='utf-8').write(s)
print('zapisano', out, len(s), 'znaków')
PY
```

W prozie i tak trzymaj cudzysłowy typograficzne `„ ”` (U+201E/U+201D) — ze względów językowych,
nie technicznych. Najpierw zwaliduj sam JSON: `python3 -m json.tool "$DATA_JSON" >/dev/null && echo "DATA JSON OK"`.

## Walidacja (obowiązkowa)

1. **Składnia JS** — wytnij `<script>` i sprawdź:
   ```bash
   python3 -c "import re,sys;s=open('$OUT').read();m=re.findall(r'<script[^>]*>(.*?)</script>',s,re.S);open('/tmp/r.js','w').write('\n;\n'.join(m)) if m else sys.exit('BŁĄD: brak <script> w '+'$OUT')"
   node --check /tmp/r.js && echo "JS OK"
   ```
Gdy `node --check` zgłasza błąd, sprawdź najpierw, czy `$DATA_JSON` to poprawny JSON.
2. **Render** — otwórz w agent-browser i policz elementy:
   ```bash
   agent-browser open "file://$PWD/$OUT"
   agent-browser eval "JSON.stringify({ideas:document.querySelectorAll('#idealist .idea').length, winner:!!document.querySelector('.idea.winner'), tabs:document.querySelectorAll('nav.contents .tab').length, trzon:document.querySelector('#trzonwrap').children.length})"
   ```
Oczekiwane: ideas 5, winner true, tabs 3, trzon ≥ 1 (panel „Trzon wizji" niepusty).
3. **Zrzut ekranu** — zrób zrzut zakładek „Trzon wizji”, „5 fabuł” i „Werdykt”, przeczytaj tekst
   (czy brzmi po polsku, bez anglicyzmów; czy trzon jest wspólny dla fabuł), potem `agent-browser close`.

## Interaktywność (jest w szablonie — nie usuwaj)

Trzy zakładki (trzon wizji / 5 fabuł / werdykt), sortowanie fabuł (wg oceny / kolejności
roboczej), animowane paski ocen sędziów, podświetlony zwycięzca, podtytuły „oryg. …”, przecinki
dziesiętne. Logika renderująca czyta `DATA` — wystarczy poprawne dane.
