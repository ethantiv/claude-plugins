# Zapis sceny i walidacja

Ten etap produkuje **prozę** (tekst), nie HTML. Jeden plik w roboczym katalogu `.book-forge/sceny/`:
1. `.book-forge/sceny/<id>.md` — proza sceny (np. `.book-forge/sceny/R3S2.md`).

Propozycje dopisów do kanonu **nie są zapisywane do pliku** — rój zwraca je jako obiekt `propozycje`, który przekazujesz w handoffie do `continuity-check` (Krok 5 w `SKILL.md`).

Widok całej książki (złożenie scen w rozdziały, HTML) powstaje dopiero w `assemble-book` — tu nie generujemy szablonu.

## Zapis prozy

```bash
python3 - "$RESULT_JSON" "$PLUGIN_ROOT" << 'PY'
import json, sys, os
sys.path.insert(0, os.path.join(sys.argv[2], 'scripts')); import bible
r = json.load(open(sys.argv[1], encoding='utf-8'))
p = bible.work_path('sceny', f"{r['id']}.md")
os.makedirs(os.path.dirname(p), exist_ok=True)
open(p, 'w', encoding='utf-8').write(r['text'].rstrip()+'\n')
print('zapisano', p, r.get('words','?'), 'słów')
PY
```

## Propozycje do kanonu (w pamięci, NIE do biblii, NIE do pliku)

Rój zwraca `propozycje` jako obiekt (nowe fakty, nowe nazwy z kategorią, zmiany `_stan` postaci, dotknięte zasiewy). Nie zapisuj ich do pliku ani do kanonu — przekaż jako wejście do bramki `continuity-check` (jedyny etap z prawem zapisu przez `bible.py`). Kształt obiektu zgodny z `args.propozycje` w `${CLAUDE_PLUGIN_ROOT}/skills/continuity-check/references/workflow-swarm.md`.

## Bez humanizera na tym etapie

Nie uruchamiaj `/humanizer:humanizer`. Kolejność redakcji prozy (patrz `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md`): treść (tu) → pogłębienie + dev-edit (`revise-scene`) → kontrola ciągłości (`continuity-check`) → humanizer → korekta PL (`polish-pl`). Humanizer przed kontrolą ciągłości mógłby złamać fakt, głos lub odmianę nazw.

## Walidacja (obowiązkowa)

- **Długość** zgodna z zamówioną (policz słowa; ostrzeż przy dużym odchyleniu).
- **Zgodność z kartą** (z wyniku roju): `pov_ok`, `glos_ok`, `nazwy_ok`, `cel_realizowany`, `zwrot_obecny`, `value_shift_ok` — wszystkie `true`. Każde `false` zgłoś autorowi jako blokadę (scena nie realizuje karty lub łamie biblię).
- **Nazwy własne**: szybki audyt, czy nazwy użyte w scenie są w glosariuszu i odmienione zgodnie z nim:
  ```bash
  : "${ID:?ustaw ID sceny w powłoce, np. ID=R3S2}"
  python3 - "$ID" "$PLUGIN_ROOT" << 'PY'
  import json, sys, os
  sys.path.insert(0, os.path.join(sys.argv[2], 'scripts')); import bible
  sid=sys.argv[1]
  b=bible.load_all()
  formy=set()
  for g in b.get('glosariusz',[]):
      for v in (g.get('odmiana') or {}).values():
          if v: formy.add(v)
  txt=open(bible.work_path('sceny', sid+'.md'),encoding='utf-8').read()
  # heurystyka: zgłoś kanoniczne nazwy uzyte w formie spoza odmiany
  print('Sprawdź ręcznie nazwy z glosariusza w tekście; formy kanoniczne:', len(formy))
  PY
  ```
- **Brak zapisu do kanonu**: potwierdź, że kanon `.book-forge/biblia/` nie został zmieniony przez ten etap — `git status --porcelain .book-forge/biblia/` ma być puste (zmienia go dopiero `continuity-check`).

Scena niezgodna z kartą wraca do poprawy; po N próbach (np. 3) eskaluj do autora albo zapisz z adnotacją „do poprawy” (nie wpuszczaj cichej, nieskończonej pętli).
