# Budowa początku (HTML + .book-forge/poczatek.md) i walidacja

Dwa artefakty:
1. `poczatek-<slug>.html` — interaktywny widok ze szablonu `${CLAUDE_PLUGIN_ROOT}/skills/opening/assets/opening-template.html`.
2. `.book-forge/poczatek.md` — polecany wariant jako tekst do dalszej pracy.

`<slug>` z tytułu książki (małe litery, bez znaków diakrytycznych, spacje zamieniane na „-”).

## Kształt obiektu DATA (HTML)

```javascript
const DATA = {
  meta: { title:"", en:"", genre:"", scene:"", recommended:"filmowa" },
  variants: [ {
    key:"filmowa",            // filmowa | zdanie | spowiedz
    nazwa:"Filmowa scena",
    opis_techniki:"",
    text:"akapit 1\n\nakapit 2",   // proza; puste linie dzielą akapity
    words: 360,
    hook:"",
    recommended:false,
    critique:{ scores:{hook:5,glos:4,immersja:5,pov:5,tempo:4}, mocne:[""], slabe:[""], verdict:"PASS" },
    ciaglosc:{ ok:true, konflikty:[] }
  } ],
  werdykt: { recommended:"filmowa", uzasadnienie:"", jak_polaczyc:"" }
};
```

## Mapowanie z wyniku roju

Rój zwraca `{ variants:[...], werdykt:{...} }`. Ustaw `recommended:true` na wariancie, którego `key === werdykt.recommended`; `meta.recommended` ← `werdykt.recommended`. `meta.title/en/genre` ← z biblii/raportu; `meta.scene` ← obietnica pierwszej sceny. Tekst wariantów to wersja **po unslopie i korekcie PL** (kolejność: unslop najpierw, korekta PL ostatnia).

## Placeholdery i wstrzyknięcie

`{{TITLE}}`, `{{GENRE}}` oraz `const DATA = /*__INJECT_DATA__*/ null;`.

```bash
python3 - "$TEMPLATE" "$DATA_JSON" "$OUT" "$TITLE" "$GENRE" << 'PY'
import sys, json
tpl,dataf,out,title,genre=sys.argv[1:6]
s=open(tpl,encoding='utf-8').read()
data=json.load(open(dataf,encoding='utf-8'))     # plik JSON (nie literał JS) — json.dumps eskejpuje
js=json.dumps(data,ensure_ascii=False).replace('</','<\\/')   # zabezpiecz przed </script>
s=s.replace('const DATA = /*__INJECT_DATA__*/ null;','const DATA = '+js+';').replace('{{TITLE}}',title).replace('{{GENRE}}',genre)
open(out,'w',encoding='utf-8').write(s)
print('zapisano',out,len(s))
PY
```

Zapisz `DATA` jako plik JSON (`$DATA_JSON`) — `json.dumps` eskejpuje cudzysłowy automatycznie (prosty `"` w prozie już nie psuje strony). W prozie i tak zachowaj polską interpunkcję dialogową (myślnik) i cudzysłowy `„ ”`.

## Walidacja (obowiązkowa)

```bash
python3 -c "import re,sys;s=open('$OUT').read();m=re.findall(r'<script[^>]*>(.*?)</script>',s,re.S);open('/tmp/p.js','w').write('\n;\n'.join(m)) if m else sys.exit('BŁĄD: brak <script> w '+'$OUT')"
node --check /tmp/p.js && echo "JS OK"
agent-browser open "file://$PWD/$OUT"
agent-browser eval "JSON.stringify({warianty:document.querySelectorAll('.tab[data-v]').length, rekomendowany:!!document.querySelector('.variant.rec'), title:document.querySelector('h1').innerText})"
```
Oczekiwane: `warianty` = 3, `rekomendowany` = true, tytuł zgodny. Zrób zrzut polecanego wariantu, przeczytaj prozę (czy brzmi po polsku, czy nazwy zgodne z glosariuszem), potem `agent-browser close`.

## `.book-forge/poczatek.md`

Zapisz polecany wariant: nagłówek z tytułem i nazwą techniki, potem proza, na końcu krótka nota werdyktu (dlaczego ten wariant) i ewentualne konflikty z kanonem do rozstrzygnięcia.
