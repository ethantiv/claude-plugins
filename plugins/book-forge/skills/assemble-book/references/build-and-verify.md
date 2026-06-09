# Złożenie książki, aktualizacja biblii i walidacja

Wyniki: `ksiazka.md` (pełny maszynopis), aktualizacja kanonu-wiki w `.book-forge/biblia/` (finalne statusy i ewentualna promocja kanonu, przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`) oraz `ksiazka-<slug>.html` (przegląd). `<slug>` z tytułu (małe litery, bez znaków diakrytycznych, spacje → „-”).

## Złożenie `ksiazka.md` (deterministyczne)

Składamy sceny w kolejności rozdział → scena, z nagłówkami rozdziałów. Tytuły rozdziałów bierzemy z `kanon_fabularny` (jeśli są) lub z konspektu.

```bash
python3 - "$PLUGIN_ROOT" << 'PY'
import sys, os, re
sys.path.insert(0, os.path.join(sys.argv[1], 'scripts'))
import bible
b = bible.load_all()
sceny = b.get('kanon_fabularny', {}).get('sceny', [])
# kolejnosc: (tom, rozdzial, scena) wyłuskane z ID. Obsługuje oba formaty:
# R1S2 (pojedyncza książka / tom 1) i T2R1S2 (seria, tom>1).
def klucz(s):
    m = re.fullmatch(r'T?(\d+)?R(\d+)S(\d+)', s.get('id','') or '')
    if not m:
        return (0, s.get('rozdzial', 0), 0)
    tom, roz, sc = m.groups()
    return (int(tom) if tom else 1, int(roz), int(sc))
sceny = sorted(sceny, key=klucz)
out, last_ch, total = [], None, 0
tytuly = {c.get('nr'): c.get('tytul') for c in b.get('kanon_fabularny',{}).get('rozdzialy',[])} if isinstance(b.get('kanon_fabularny',{}).get('rozdzialy'),list) else {}
for s in sceny:
    ch = s.get('rozdzial')
    if ch != last_ch:
        t = tytuly.get(ch, '')
        out.append(f"\n\n## Rozdział {ch}{(' — '+t) if t else ''}\n")
        last_ch = ch
    p = bible.work_path('sceny', f"{s['id']}.md")
    if os.path.exists(p):
        txt = open(p, encoding='utf-8').read().strip()
        total += len(txt.split())
        out.append(txt+'\n')
    else:
        out.append(f"_[BRAK SCENY {s['id']}]_\n")
title = b.get('meta',{}).get('tytul','Książka')
gatunek = b.get('meta',{}).get('subgatunek') or b.get('meta',{}).get('gatunek','')
naglowek = f"# {title}\n\n> Maszynopis: {total} słów · {len(set(s.get('rozdzial') for s in sceny))} rozdziałów · {len(sceny)} scen{(' · '+gatunek) if gatunek else ''}\n"
open(bible.book_path('ksiazka.md'),'w',encoding='utf-8').write(naglowek+''.join(out))
print('złożono', bible.book_path('ksiazka.md'), '—', total, 'słów,', len(sceny), 'scen')
PY
```

Brakujące sceny zostają jako widoczne `[BRAK SCENY ...]` — nie scalaj dziur po cichu, lecz zgłoś je autorowi.

## Aktualizacja biblii + promocja kanonu

Na podstawie `synteza.setup_payoff_finalny` ustaw statusy zasiewów i oznacz domknięcia przez `bible.append_record('setup_payoff', ...)` (agregat RUNTIME aktualizowany po `id`). **Promocja `working` → `published`** przez `bible.freeze_canon(True)` następuje tylko wtedy, gdy `werdykt_gotowosci` = „gotowa do zamrożenia”, nie ma krytycznych problemów, a autor potwierdził (`AskUserQuestion`).

```bash
python3 - "$SYNT_JSON" "$ZAMROZ" "$PLUGIN_ROOT" << 'PY'
import json, sys, os
sys.path.insert(0, os.path.join(sys.argv[3], 'scripts'))
import bible
synt = json.load(open(sys.argv[1], encoding='utf-8'))
zamroz = sys.argv[2] == 'tak'        # decyzja autora
for sp in synt.get('setup_payoff_finalny', []):
    if sp.get('id'): bible.append_record('setup_payoff', sp)   # dedup po id → update statusu/scena_splaty
krytyczne = [p for p in synt.get('problemy',[]) if p.get('waga')=='krytyczna'] + synt.get('luki_luku',[])
if zamroz and synt.get('werdykt_gotowosci','').startswith('gotowa') and not krytyczne:
    bible.freeze_canon(True)
    print('kanon zamrożony: published')
else:
    print('kanon pozostaje working (niegotowy lub bez zgody)')
bible.render_index()
PY
```

`freeze_canon`/`render_index` regenerują widok (`index.md`) po zapisie.

## DATA dla HTML

```javascript
const DATA = {
  meta: { title:"", en:"", genre:"", rozdzialy:0, sceny:0, words:0, werdykt:"", kanon:"working" },
  rozdzialy: [ {nr:1, tytul:"", sceny:[{id:"R1S1", words:0, value:"+"}], words:0} ],
  arc: [ {id:"R1S1", value:"+"} ],
  zasiewy: [ {id:"SP01", opis:"", typ:"", scena_zasiewu:"R1S1", scena_splaty:"R8S2", status:"domkniety"} ],
  audyty: [ {wymiar:"Łuk fabularny", werdykt:"OK", problemy:[]} ],
  problemy: [ {typ:"", opis:"", gdzie:"", waga:""} ]
};
```

Mapowanie: `rozdzialy/arc` z `kanon_fabularny.sceny` plus policzone słowa; `zasiewy` z `setup_payoff` (w tym `scena_zasiewu`/`scena_splaty` — szablon pokazuje, GDZIE strzelbę powieszono i gdzie wypaliła, czyli rozpiętość zasiewu); `audyty/problemy/werdykt` z `synteza`. Pole `kanon` z biblii po promocji. Wypełniacze `{{TITLE}}`, `{{GENRE}}`; wstrzyknięcie jak w pozostałych szablonach — `DATA` zapisz jako plik JSON i wstrzyknij przez `json.dumps` (wzorzec w `outline-to-scenes`/`market-report`).

## Walidacja (obowiązkowa)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bible.py validate
test -f ksiazka.md && grep -c 'BRAK SCENY' ksiazka.md   # 0 = komplet
python3 -c "import re,sys;s=open('$OUT').read();m=re.findall(r'<script[^>]*>(.*?)</script>',s,re.S);open('/tmp/k.js','w').write('\n;\n'.join(m)) if m else sys.exit('BŁĄD: brak <script> w '+'$OUT')"
node --check /tmp/k.js && echo "JS OK"
agent-browser open "file://$PWD/$OUT"
agent-browser eval "JSON.stringify({rozdzialy:document.querySelectorAll('#rozdzialy .rozdzial').length, zasiewy:document.querySelectorAll('#zasiewy tr').length, werdykt:document.querySelector('#werdykt').innerText})"
```

Potwierdź: w `ksiazka.md` nie ma `BRAK SCENY`, każdy zasiew ma status (otwarte zgłoś), a werdykt gotowości jest widoczny. Kanon zamrażaj tylko po czystym przeglądzie.
