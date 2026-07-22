# Zapis rewizji i walidacja

Ten etap produkuje **prozę** i notatkę QA, nie HTML. Pliki w roboczym katalogu `.book-forge/sceny/`:
1. `.book-forge/sceny/<id>.md` — nadpisany poprawioną sceną (opcjonalnie kopia `.book-forge/sceny/<id>.v1.md`).
2. `.book-forge/sceny/<id>.qa.md` — notatka QA (werdykt, oceny, log rund, ewentualny dług).

Nowe propozycje do kanonu (jeśli pogłębienie coś dodało) **nie idą do pliku** — rój zwraca je jako obiekt `propozycje`, który przekazujesz w handoffie do `continuity-check` (Krok 5 w `SKILL.md`).

## Zapis prozy i QA

```bash
python3 - "$RESULT_JSON" "$PLUGIN_ROOT" << 'PY'
import json, sys, os
sys.path.insert(0, os.path.join(sys.argv[2], 'scripts')); import bible
r = json.load(open(sys.argv[1], encoding='utf-8'))
p = bible.work_path('sceny', f"{r['id']}.md")
os.makedirs(os.path.dirname(p), exist_ok=True)
if os.path.exists(p):                       # kopia poprzedniej wersji
    open(bible.work_path('sceny', f"{r['id']}.v1.md"),'w',encoding='utf-8').write(open(p,encoding='utf-8').read())
open(p,'w',encoding='utf-8').write(r['text'].rstrip()+'\n')

qa = [f"# QA — scena {r['id']}", '', f"Werdykt: {r['verdict']}"]
if r.get('dlug'): qa += ['', f"Dług: {r['dlug']}"]
qa += ['', '## Rundy']
for rd in r.get('rundy', []):
    qa.append(f"- runda {rd['runda']}: {rd['verdict']} — oceny {rd.get('scores',{})}")
    for f in rd.get('top_fixy', []): qa.append(f"  - {f}")
open(bible.work_path('sceny', f"{r['id']}.qa.md"),'w',encoding='utf-8').write('\n'.join(qa)+'\n')
print('zapisano scenę i QA:', r['id'], '| werdykt:', r['verdict'])
PY
```

## Notatka QA — nie do kanonu

QA to plik, **nie** wpis do kanonu `.book-forge/biblia/`. Kanonu fabularnego ten etap nie zmienia; `log_ciaglosci` w biblii aktualizuje dopiero `continuity-check`.

## Bez unslopa na tym etapie

Nie uruchamiaj `/unslop:unslop`. Kolejność: treść (`write-scene`) → pogłębienie + dev-edit (tu) → kontrola ciągłości (`continuity-check`) → unslop → korekta PL (`polish-pl`).

## Walidacja (obowiązkowa)

- **Werdykt** z pętli: `PASS` albo `FIX` z `accept-with-debt`. Każdy dług zgłoś autorowi (to świadomy kompromis, nie cicha porażka — zasada „fail loud”).
- **Oceny** dev-edit: pokaż wynik per kryterium; oznacz słabe (np. < 3) jako ryzyka.
- **Zgodność z kartą sceny**: po rewizji scena nadal realizuje cel i zwrot z karty (pogłębienie nie powinno dodać zdarzeń spoza karty).
- **Brak zapisu do kanonu**: potwierdź, że kanon `.book-forge/biblia/` nie został zmieniony. Nie używaj gita (katalog książki nie musi być repo); porównaj snapshot sprzed roju: `find .book-forge/biblia -name '*.md' -exec md5sum {} + | sort | md5sum` — suma przed i po ma być identyczna.
- **Nazwy własne**: szybki audyt zgodności z glosariuszem (jak w `write-scene`).

Jeśli wyczerpano limit prób bez PASS, scena zostaje z adnotacją `accept-with-debt` w QA — to wejście do decyzji autora lub do ponownej rewizji z jego uwagami.
