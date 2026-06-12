# Siatka scen: zapis do biblii + scalenie do konspektu HTML

Dwa rezultaty: wpis do biblii (kanon fabularny — źródło prawdy) oraz scalenie siatki scen do istniejącego `konspekt-<slug>.html` jako zakładka „Sceny". Osobnych `sceny.md` ani `sceny-<slug>.html` **nie tworzymy**. `<slug>` z tytułu książki (małe litery, bez znaków diakrytycznych, spacje → „-”).

## Zapis do biblii (przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`)

To etap planowania, więc tworzy on wyjściowy kanon fabularny (siatkę scen). Z wyniku roju agentów zmapuj:
- siatka scen ← `scenes` (każda: id, rozdzial, pov, miejsce, czas, cel, konflikt, zwrot, value, luk, zasiewa, splaca; status ustawiany na `"planowana"`) + `rozdzialy` (nr, tytul — do nagłówków w `assemble-book`) + `beaty` (z `arc`) → `bible.write_scene_grid(...)`.
- `setup_payoff` ← `setup_payoff`, `os_czasu` ← `os_czasu` — agregaty `RUNTIME` wg `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md`; pętla `bible.append_record(...)`, której dedup chroni przed duplikatami (`setup_payoff` po `id`, `os_czasu` po `scena` — update-or-append).

Zapisz przez bibliotekę (nie ręczne sklejanie). Najpierw zrzuć wynik roju do pliku tymczasowego, potem rozłóż przez `bible.py`; na końcu `render_index()`:

```bash
# BUDZET_SLOW: odpowiedź autora z Kroku 1 (puste = nie nadpisuj istniejącego budżetu)
python3 - "$RESULT_JSON" "$PLUGIN_ROOT" "$FORCE" "${BUDZET_SLOW:-}" << 'PY'
import json, sys, os
sys.path.insert(0, os.path.join(sys.argv[2], 'scripts'))
import bible
res = json.load(open(sys.argv[1], encoding='utf-8'))            # wynik roju
force = sys.argv[3] == 'tak'                                    # nadpisanie istniejącej siatki (po AskUserQuestion)

beaty = [k.get('beat') for k in (res.get('arc', {}).get('krzywa') or []) if k.get('beat')]
g = bible.write_scene_grid(res.get('rozdzialy', []), beaty,
                           [{**s, 'status': 'planowana'} for s in res['scenes']], force=force)
if g.get('status') == 'GUARD':
    print('GUARD: siatka scen już istnieje — zapytaj autora i ponów z FORCE=tak'); sys.exit(0)

# setup_payoff/os_czasu to agregaty RUNTIME (rozwija je continuity-check) — append z dedup, nie nadpisanie
for sp in res.get('setup_payoff', []): bible.append_record('setup_payoff', sp)
for oc in res.get('os_czasu', []):     bible.append_record('os_czasu', oc)

# łańcuch budżetu słów: jedyny producent meta.liczba_scen / meta.budzet_slow (konsumuje write-scene)
bible.update_meta('liczba_scen', len(res['scenes']))
if len(sys.argv) > 4 and sys.argv[4].isdigit():
    bible.update_meta('budzet_slow', int(sys.argv[4]))

bible.render_index()
print('zaktualizowano kanon-wiki:', len(res['scenes']), 'scen')
PY
```

Jeśli siatka scen już istnieje (pisanie ruszyło), `write_scene_grid` zwróci `{"status":"GUARD"}` — zapytaj autora o nadpisanie (`AskUserQuestion`) i ponów z `FORCE=tak`. Agregaty `setup_payoff`/`os_czasu` rosną przez `append_record` z dedup, więc ponowny przebieg nie duplikuje rekordów ani nie kasuje postępu z `continuity-check`.

## Scalenie scen do konspektu HTML (zamiast osobnego pliku)

Sceny trafiają jako zakładka „Sceny" (03) do istniejącego `konspekt-<slug>.html`. Mechanika: wczytaj konspekt, wyłuskaj z niego obiekt `DATA`, dołóż pole `DATA.scenes` i ponownie wstrzyknij `DATA` w szablon `${CLAUDE_PLUGIN_ROOT}/skills/outline/assets/outline-template.html`, nadpisując konspekt. Szablon sam pokaże zakładkę „Sceny", gdy `DATA.scenes` jest niepuste. **Łuk, beaty, zasiewy i research celowo pomijamy w HTML** — to żyje w biblii.

Kształt `DATA.scenes` (podzbiór pól sceny — bez tagów zasiewów/researchu):

```javascript
scenes: [ {id:"R1S1", rozdzial:1, pov:"", miejsce:"", czas:"", cel:"", konflikt:"", zwrot:"", value:"+", luk:""} ]
```

```bash
python3 - "$KONSPEKT_HTML" "$SCENES_JSON" "$OUTLINE_TEMPLATE" << 'PY'
import re, json, sys
kon_path, scenes_path, tpl_path = sys.argv[1:4]
html = open(kon_path, encoding='utf-8').read()
data = json.loads(re.search(r'const DATA = (\{.*?\});\nconst \$=', html, re.S).group(1))
data['scenes'] = json.load(open(scenes_path, encoding='utf-8'))   # lista scen (pola jak wyżej)
tpl = open(tpl_path, encoding='utf-8').read()
js = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')   # zabezpiecz przed </script>
tpl = tpl.replace('const DATA = /*__INJECT_DATA__*/ null;', 'const DATA = ' + js + ';')
tpl = tpl.replace('{{TITLE}}', data['meta'].get('title','')).replace('{{GENRE}}', data['meta'].get('genre','science fiction'))
open(kon_path, 'w', encoding='utf-8').write(tpl)
print('scalono scen:', len(data['scenes']))
PY
```

Cudzysłowy treści trzymaj jako `„ ”`. Jeśli `konspekt-<slug>.html` nie istnieje — pomiń scalenie HTML (kanon scen jest w biblii) i powiedz to autorowi.

## Walidacja (obowiązkowa)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bible.py validate
python3 -c "import re,sys;s=open('$KONSPEKT_HTML').read();m=re.findall(r'<script[^>]*>(.*?)</script>',s,re.S);open('/tmp/s.js','w').write('\n;\n'.join(m)) if m else sys.exit('BŁĄD: brak <script>')"
node --check /tmp/s.js && echo "JS OK"
agent-browser open "file://$PWD/$KONSPEKT_HTML"
agent-browser eval "JSON.stringify({sceny:document.querySelectorAll('#scenes-list .scene').length, tabSceny:getComputedStyle(document.getElementById('tab-scenes')).display!=='none', title:document.querySelector('h1').innerText})"
```

Oczekiwane: `validate` → `OK, brak luk` (luki zgłoś autorowi), `sceny` = liczba scen, `tabSceny` = true, tytuł zgodny. Sprawdź też w kanonie (`bible.load_all()['setup_payoff']`): czy każdy zasiew ma `scena_splaty` (status `domkniety`) lub jest świadomie otwarty; zgłoś autorowi zasiewy bez wypłaty. Zrób zrzut zakładki „Sceny", potem `agent-browser close`.
