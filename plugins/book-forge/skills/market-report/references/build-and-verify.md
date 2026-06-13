# Budowa raportu HTML i walidacja

Szablon: `${CLAUDE_PLUGIN_ROOT}/skills/market-report/assets/report-template.html`. Ma 3 placeholdery tekstowe i jeden punkt wstrzyknięcia danych.

## Placeholdery tekstowe

- `{{GENRE}}` — gatunek (np. „science fiction”), występuje 3×.
- `{{READER}}` — opis docelowego czytelnika.
- `{{YEAR}}` — rok danych (np. „2026”).

## Punkt wstrzyknięcia danych

W szablonie jest punkt: `const DATA = /*__INJECT_DATA__*/ null;`. Dane `DATA` (po polsku, po redakcji i humanizerze) zapisz jako **plik JSON** i wstrzyknij skryptem z sekcji „Wstrzyknięcie” (przez `json.dumps`) — nie sklejaj literału ręcznie.

## Kształt obiektu DATA (dokładnie taki — JS render tego oczekuje)

```javascript
const DATA = {
  books: [ {t:"", a:"", g:"", why:"", love:""} ],   // 10 pozycji
  obs:   [ {b:"", t:""} ],                            // 6-8 obserwacji (b = pogrubione zdanie)
  gaps:  [ {n:1, h:"", p:"",                          // 3 luki
            e:{ proof:["",""],                        //   dowód i okazja — STRUKTURA (nie jeden akapit)
                notes:[{k:"Luka",t:""},{k:"Ryzyko",t:""}] } } ],  // proof = 3-5 dowodów (URL w treści); notes k ∈ {Luka,Ryzyko,Pozycjonowanie}

  ideas: [ {
    t:"",            // POLSKI tytuł roboczy
    en:"",           // oryginał roboczy (podtytuł „oryg. …”)
    score:7.3,       // średnia ocena (kropka — JS sam zamieni na przecinek)
    winner:true,     // dokładnie jeden true
    runner:true,     // dokładnie jeden true (wicemistrz); pozostałe pomiń pole
    gap:"Luka 2",
    log:"",          // logline (kursywa)
    silnik:"",       // silnik premisy — strukturalna sprzeczność napędzająca konflikt
    op:"",           // streszczenie
    hook:"",         // haczyk (może mieć <b>…</b>)
    comps:["",""],   // tytuły porównawcze
    protagonista:"", // profil bohatera (np. „kobieta, ~40, była śledcza") — niesie decyzję do outline/book-bible
    votes:[ ["Redaktor (finanse)",7.4], ["Marketing",7.5], ["Czytelnik docelowy",7.4], ["Analityk sprzedaży",6.8], ["Adwokat innowacji",7.6] ]
  } ],                                                // 5 pomysłów
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
    score:"Średnia 7,3 &bull; najwyższa w stawce (7,4 / 7,5 / 7,4 / 6,8 / 7,6)",
    rationale:"", warn:"", whyNow:"",
    steps:["",""],   // kroki dla autora
    runner:"",       // tytuł wicemistrza (po polsku)
    runnerEn:"",     // oryginał wicemistrza
    runnerWhy:""
  }
};
```

## Mapowanie z wyniku roju

Rój zwraca `{ bestsellers:{books,observations}, gaps:[...], ideas:[...], winner:{...}, brief:{...} }`.

- `DATA.books` ← `bestsellers.books`
- `DATA.obs` ← `bestsellers.observations`
- `DATA.gaps` ← `gaps`
- `DATA.ideas` ← `ideas` (każdy): `score` ← `avgScore`; `silnik` ← `silnik` (przepisz 1:1); `protagonista` ← `protagonista` (przepisz 1:1); `votes` ← sparuj oceny z nazwami sędziów **w kolejności**: `["Redaktor (finanse)","Marketing","Czytelnik docelowy","Analityk sprzedaży","Adwokat innowacji"]`. Ustaw `winner:true` na pozycji, której `t` odpowiada `winner.winnerTitle` (fallback: najwyższe `avgScore`); ustaw `runner:true` tam, gdzie `t` = `winner.runnerTitle`. **Pole `gap` każdego pomysłu musi zaczynać się od numeru luki** (np. „Luka 2 — …”) — UI ma dwa tryby sortowania: „według oceny” (malejąco po `score`) oraz „według luki rynkowej” (rosnąco po numerze wyłuskanym z `gap`). Kolejność tablicy `ideas` ustala porządek w obrębie jednej luki (np. zwycięzca najpierw), więc grupuj ją wg luki, a nie pre-sortuj po ocenie.
- `DATA.brief` ← `brief` (przepisz 1:1 — to dane sterujące, NIE redaguj). To kanał dziedziczenia decyzji autora do outline i book-bible.
- `DATA.verdict`: `title`←`winner.winnerTitle`, `titleEn`← `en` zwycięskiego pomysłu, `rationale`←`winner.rationale`, `warn`←`winner.warning`, `whyNow`←`winner.whyNow`, `steps`←`winner.nextSteps`, `runner`←`winner.runnerTitle`, `runnerEn`← `en` wicemistrza, `runnerWhy`←`winner.runnerWhy`. Pole `score` złóż ręcznie z oceny zwycięzcy.

## Wstrzyknięcie (rzetelna metoda — przez plik, nie ręczne sklejanie)

Zapisz `DATA` jako **plik JSON** (`$DATA_JSON`) — strict JSON: klucze i napisy w cudzysłowie prostym, bez przecinków na końcu, bez komentarzy. Python wstrzykuje go przez `json.dumps`, więc cudzysłowy i znaki specjalne w treści są eskejpowane automatycznie (prosty `"` w prozie już nie psuje strony). Przykład:

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

W prozie i tak trzymaj cudzysłowy typograficzne `„ ”` (U+201E/U+201D) — ze względów językowych, nie technicznych. Najpierw zwaliduj sam JSON: `python3 -m json.tool "$DATA_JSON" >/dev/null && echo "DATA JSON OK"`.

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
   agent-browser eval "JSON.stringify({books:document.querySelectorAll('#blist .bcard').length, obs:document.querySelector('#obs').children.length, ideas:document.querySelectorAll('#ideas .idea').length, winner:!!document.querySelector('.idea.winner')})"
   ```
Oczekiwane: books 10, obs 6-8, ideas 5, winner true.
3. **Zrzut ekranu** — zrób zrzut zakładek „pomysły” i „werdykt”, przeczytaj tekst (czy brzmi po polsku, bez anglicyzmów), potem `agent-browser close`.

## Interaktywność (jest w szablonie — nie usuwaj)

Zakładki, rozwijane karty bestsellerów, animowane paski ocen sędziów, sortowanie pomysłów (wg oceny / kolejności roboczej), podświetlony zwycięzca, podtytuły „oryg. …”, przecinki dziesiętne. Logika renderująca czyta `DATA` — wystarczy poprawne dane.
