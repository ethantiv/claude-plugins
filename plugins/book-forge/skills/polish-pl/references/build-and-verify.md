# Zapis korekty i walidacja

Ten etap produkuje **prozę** i raport, nie HTML. Pliki w roboczym katalogu `.book-forge/`:
1. `.book-forge/sceny/<id>.md` — nadpisany wygładzoną wersją (opcjonalnie kopia `.book-forge/sceny/<id>.v2.md`).
2. `.book-forge/korekta-<id>.md` — raport zmian (kategorie, przywrócone nazwy, propozycje AI-izmów).

## Kolejność (krytyczna)

1. **Unslop NAJPIERW** — w głównej sesji, na prozie po `continuity-check`, zakotwiczony kartą stylu i ochroną nazw z glosariusza.
2. **Rój: korekta PL → walidacja nazw** — na tekście po unslopie.

Nigdy odwrotnie: korekta PL przed unslopem zostałaby częściowo cofnięta przez jego poprawki.

## Zapis

```bash
python3 - "$RESULT_JSON" "$ID" "$PLUGIN_ROOT" << 'PY'
import json, sys, os
sys.path.insert(0, os.path.join(sys.argv[3], 'scripts')); import bible
r = json.load(open(sys.argv[1], encoding='utf-8')); sid = sys.argv[2]
p = bible.work_path('sceny', f"{sid}.md")
if os.path.exists(p):
    open(bible.work_path('sceny', f"{sid}.v2.md"),'w',encoding='utf-8').write(open(p,encoding='utf-8').read())
open(p,'w',encoding='utf-8').write(r['text'].rstrip()+'\n')

rap = [f"# Korekta językowa — scena {sid}", '', '## Zmiany']
for z in r.get('zmiany', []): rap.append(f"- {z.get('kategoria','')}: {z.get('przyklad','')}")
rap += ['', '## Przywrócone nazwy (po unslopie)']
for n in r.get('przywrocone_nazwy', []): rap.append(f"- {n.get('bylo','')} → {n.get('jest','')}")
rap += ['', '## Propozycje nowych AI-izmów do czarnej listy']
for a in r.get('nowe_aiizmy', []): rap.append(f"- {a}")
open(bible.work_path(f"korekta-{sid}.md"),'w',encoding='utf-8').write('\n'.join(rap)+'\n')
print('zapisano scenę i korektę:', sid)
PY
```

## Walidacja (obowiązkowa)

- **Nazwy własne**: każda nazwa z glosariusza występuje w poprawnej, kanonicznej odmianie; brak wariantów zakazanych. Sprawdź, czy unslop żadnej nie „poprawił” (lista `przywrocone_nazwy` pokazuje, co naprawiono).
- **Interpunkcja dialogowa**: dialogi myślnikiem, bez cudzysłowu angielskiego; szybki audyt:
  ```bash
  : "${ID:?ustaw ID sceny w powłoce, np. ID=R3S2}"   # fail loud — bez tego grep celowałby w .md i fałszywie raportował OK
  grep -nE '^"' ".book-forge/sceny/$ID.md" && echo "UWAGA: dialog cudzysłowem ang." || echo "dialogi OK"
  ```
- **Brak prostych cudzysłowów i kropki dziesiętnej** w treści (powinny być „ ” i przecinek).
- **Rejestr**: wyrywkowo porównaj z kartą stylu (czy głos się nie spłaszczył).
- **Propozycje AI-izmów**: jeśli niepuste, pokaż autorowi do ewentualnego dopisania w `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` — nie edytuj wspólnego pliku automatycznie.

Po tym etapie scena jest gotowa do złożenia w `assemble-book`.
