# Budowa konspektu (dwa pliki) i walidacja

Etap 2 zapisuje **dwa** artefakty:
1. `.book-forge/konspekt.md` — kanoniczny, dla etapu 3 (pisanie początku).
2. `konspekt-<slug>.html` — interaktywny widok ze szablonu `${CLAUDE_PLUGIN_ROOT}/skills/outline/assets/outline-template.html`.

`<slug>` zrób z tytułu książki (małe litery, bez znaków diakrytycznych, spacje → „-”).

## Kształt obiektu DATA (HTML)

```javascript
const DATA = {
  meta: {
    title:"",          // polski tytuł roboczy (= idea.t)
    en:"",             // oryginał roboczy (= idea.en)
    genre:"", reader:"", length:"", chaptersCount: 0,   // ← chapters.length (nie hardkoduj — wynika z gatunku)
    structure:"",      // nazwa zastosowanej struktury
    premise:"", transformation:"", theme:"", conflict:"", ending:"", arc:""
  },
  chapters: [ {
    n:1, title:"", promise:"",
    beats:["",""],     // 3-5 kluczowych punktów
    hook:"",           // haczyk otwierający
    twist:"",          // zwrot akcji na końcu
    emotion:"",        // przejście emocjonalne, np. „nadzieja → strata”
    value:"+"          // "+" albo "-" (na czym kończy się rozdział dla bohatera)
  } ],
  cut: [ {n:0, powod:""} ]   // wycięte wypełniacze (informacyjnie; może być [])
};
```

Pole `DATA.scenes` **nie powstaje na tym etapie** — dopisuje je później `outline-to-scenes` (scalenie siatki scen). Gdy istnieje i jest niepuste, szablon sam pokazuje zakładkę „Sceny" (03); gdy go brak, zakładka jest ukryta. Etap 2 zostawia więc dwie zakładki: Fundament i Rozdziały.

## Mapowanie z wyniku roju

Rój zwraca `{ fundament:{premise,theme,transformation,centralConflict,ending,arc}, structureName, chapters:[...], cut:[...] }`.

- `meta.title` ← `idea.t`, `meta.en` ← `idea.en` (z etapu 1)
- `meta.genre/reader/length` ← parametry wejścia; `meta.chaptersCount` ← `chapters.length`
- `meta.structure` ← `structureName`
- `meta.premise/transformation/theme/arc/ending` ← odpowiednie pola `fundament`
- `meta.conflict` ← `fundament.centralConflict`
- `DATA.chapters` ← `chapters`; `DATA.cut` ← `cut`

## Placeholdery szablonu

`{{TITLE}}`, `{{GENRE}}` oraz punkt wstrzyknięcia `const DATA = /*__INJECT_DATA__*/ null;`.

## Wstrzyknięcie (przez plik, nie ręczne sklejanie)

```bash
python3 - "$TEMPLATE" "$DATA_JSON" "$OUT" "$TITLE" "$GENRE" << 'PY'
import sys, json
tpl, dataf, out, title, genre = sys.argv[1:6]
s = open(tpl, encoding='utf-8').read()
data = json.load(open(dataf, encoding='utf-8'))  # plik JSON (nie literał JS) — json.dumps zadba o eskejpowanie
js = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')   # zabezpiecz przed </script>
s = s.replace('const DATA = /*__INJECT_DATA__*/ null;', 'const DATA = ' + js + ';')
s = s.replace('{{TITLE}}', title).replace('{{GENRE}}', genre)
open(out, 'w', encoding='utf-8').write(s)
print('zapisano', out, len(s))
PY
```

Zapisz `DATA` jako plik JSON (`$DATA_JSON`) — `json.dumps` eskejpuje cudzysłowy automatycznie (prosty `"` w prozie już nie psuje strony). W treści i tak trzymaj cudzysłowy `„ ”` (U+201E/U+201D).

## Format `.book-forge/konspekt.md` (kanon dla etapu 3)

```markdown
# {title} ({en})

- Gatunek: {genre}
- Czytelnik: {reader}
- Długość: {length}
- Struktura: {structure}

## Fundament
**Przesłanka:** {premise}
**Motyw:** {theme}
**Transformacja:** {transformation}
**Konflikt:** {conflict}
**Zakończenie:** {ending}
**Łuk emocjonalny:** {arc}

## Rozdziały

### Rozdział {n} — {title}
**Obietnica:** {promise}
**Kluczowe punkty:**
- {beat}
**Haczyk:** {hook}
**Zwrot akcji:** {twist}
**Emocja:** {emotion} ({value})

## Wycięte wypełniacze
- Rozdział {n}: {powod}
```

## Walidacja (obowiązkowa)

1. **Składnia JS:**
   ```bash
   python3 -c "import re,sys;s=open('$OUT').read();m=re.findall(r'<script[^>]*>(.*?)</script>',s,re.S);open('/tmp/o.js','w').write('\n;\n'.join(m)) if m else sys.exit('BŁĄD: brak <script> w '+'$OUT')"
   node --check /tmp/o.js && echo "JS OK"
   ```
2. **Render:**
   ```bash
   agent-browser open "file://$PWD/$OUT"
   agent-browser eval "JSON.stringify({chapters:document.querySelectorAll('#chapters .chap').length, title:document.querySelector('h1').innerText})"
   ```
Oczekiwane: `chapters` = liczba rozdziałów, tytuł zgodny.
3. **Zrzut ekranu** zakładek „fundament” i „rozdziały”; przeczytaj tekst (czy brzmi po polsku, bez anglicyzmów), potem `agent-browser close`.
4. Sprawdź `.book-forge/konspekt.md` — czy każdy rozdział ma obietnicę, punkty, haczyk i zwrot.
