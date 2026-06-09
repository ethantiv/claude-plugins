# Zapis researchu do biblii i walidacja

Research **nie tworzy osobnych plików** (`research.md`/`.html`). Jedyny wynik to wpis do biblii (`fakty` + `zrodla`, ewentualnie doprecyzowane `swiat.zasady`). Kolejne etapy czytają realia z biblii, nie z raportu.

## Zapis do biblii (przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py`)

Dopisz nowe `fakty` (z `zrodlo_ref`) i `zrodla` (rejestr cytowań) przez `bible.append_record` (auto-id `F`/`Z`, dedup). Doprecyzowanie istniejących `swiat.zasady` (pole RO) tylko po potwierdzeniu autora — w skrypcie poniżej zakomentowane; włącz po `AskUserQuestion` (`bible.write_section('swiat', {...})`).

```bash
python3 - "$RESULT_JSON" "$PLUGIN_ROOT" << 'PY'
import json, sys, os
sys.path.insert(0, os.path.join(sys.argv[2], 'scripts'))
import bible
res = json.load(open(sys.argv[1], encoding='utf-8'))['integracja']
for f in res.get('fakty', []):  bible.append_record('fakty', f)
for z in res.get('zrodla', []): bible.append_record('zrodla', z)
# zasady RO — tylko za zgodą autora (AskUserQuestion); scal z istniejącymi swiat.zasady:
# sw = bible.load_all().get('swiat', {})
# sw['zasady'] = merge(sw.get('zasady', []), res.get('zasady', []))
# bible.write_section('swiat', sw)
bible.render_index()
print('dopisano faktów:', len(res.get('fakty',[])), 'źródeł:', len(res.get('zrodla',[])))
PY
```

`render_index()` regeneruje widok (`index.md`) po zapisie. `append_record('fakty')` deduplikuje po `(tresc, zrodlo_scena)`, więc ponowny przebieg nie dubluje ustaleń.

## Domknięcie pętli zwrotnej

Jeśli research obalił lub istotnie zmienił realia, na których opierała się któraś scena (`kanon_fabularny.sceny[].research`), oznacz ją do rewizji: `bible.set_scene_field(<id>, "status", "do-rewizji")` i wypisz autorowi. Sceny niedotknięte zostaw bez zmian.

## Walidacja (obowiązkowa)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/bible.py validate
```

Walidator zgłosi luki kanonu (`OK, brak luk` / `LUKI:`). Sprawdź dodatkowo na `bible.load_all()`, że każdy fakt ma `zrodlo_ref` wskazujący istniejący wpis w `zrodla` i że nie ma faktu bez źródła.
