# Skrypt roju (Workflow) — kontrola ciągłości

Skopiuj do narzędzia **Workflow**. `args`: `{ scena, proza, propozycje, biblia }`, gdzie `biblia` to istotny kontekst kanonu (meta pov/czas, postacie obecne z opisem RO i `_stan`, glosariusz, swiat.zasady, setup_payoff, os_czasu). `propozycje` pochodzą z **handoffu** `write-scene`/`revise-scene` i są **opcjonalne** — przy samodzielnym audycie zostają puste (`A.propozycje || {}`), bo audytorzy wyłuskują ustalenia wprost z prozy. Rój tylko **audytuje i tworzy plan** — zapis do biblii wykonuje główna sesja skryptem.

```javascript
export const meta = {
  name: 'book-forge-continuity-check',
  description: 'Roj audytorow porownuje scene z biblia, synteza klasyfikuje: CONFLICT (RO) vs WRITE (RUNTIME) + plan zapisu',
  phases: [ { title: 'Audyt' }, { title: 'Klasyfikacja' } ],
}

// Workflow bywa, że podaje `args` jako string JSON, nie jako obiekt — parsuj odpornie
let A
try { A = typeof args === 'string' ? JSON.parse(args) : (args || {}) }
catch (e) { throw new Error('args podane jako string, ale to nie poprawny JSON ('+e.message+'). Przekaż obiekt albo poprawny JSON.') }
const SC = A.scena, PROZA = A.proza, PROP = A.propozycje || {}, B = A.biblia

const ROLE = `Jesteś strażnikiem kanonu (continuity editor). Twoje jedyne zmartwienie to spójność. Porównujesz scenę i jej propozycje z biblią. KANON (istotny fragment):\n${JSON.stringify(B)}\n\nKARTA SCENY:\n${JSON.stringify(SC)}\n\nPROPOZYCJE z etapu pisania:\n${JSON.stringify(PROP)}\n\nPisz po polsku.`

const AUDYT = { type:'object', required:['dziedzina','sprzecznosci','ustalenia'], properties:{
  dziedzina:{type:'string'},
  sprzecznosci:{type:'array',items:{type:'object',required:['pole','scena_mowi','biblia_mowi'],properties:{pole:{type:'string'},scena_mowi:{type:'string'},biblia_mowi:{type:'string'},waga:{type:'string'}}}},
  ustalenia:{type:'array',items:{type:'object',required:['typ','tresc'],properties:{typ:{type:'string'},tresc:{type:'string'}}}} } }

const PLAN = { type:'object', required:['werdykt','konflikty','zapis','log'], properties:{
  werdykt:{type:'string'},
  konflikty:{type:'array',items:{type:'object',required:['pole','opis'],properties:{pole:{type:'string'},opis:{type:'string'},scena_mowi:{type:'string'},biblia_mowi:{type:'string'},rekomendacja:{type:'string'}}}},
  zapis:{type:'object',required:['fakty','nazwy','stan','os_czasu','setup_payoff'],properties:{
    fakty:{type:'array',items:{type:'object',required:['tresc','typ','zrodlo_scena'],properties:{tresc:{type:'string'},typ:{type:'string'},pewnosc:{type:'string'},zrodlo_scena:{type:'string'}}}},
    nazwy:{type:'array',items:{type:'object',required:['nazwa','kategoria','odmiana'],properties:{nazwa:{type:'string'},kategoria:{type:'string'},odmiana:{type:'object',required:['M','D','B'],properties:{M:{type:'string'},D:{type:'string'},C:{type:'string'},B:{type:'string'},N:{type:'string'},Ms:{type:'string'},W:{type:'string'}}}}}},
    stan:{type:'array',items:{type:'object',required:['postac','pole','wartosc'],properties:{postac:{type:'string'},pole:{type:'string'},wartosc:{type:'string'}}}},
    os_czasu:{type:'array',items:{type:'object',required:['scena','kolejnosc'],properties:{scena:{type:'string'},dzien_fabularny:{type:'string'},kolejnosc:{type:'number'}}}},
    setup_payoff:{type:'array',items:{type:'object',required:['id','status'],properties:{id:{type:'string'},status:{type:'string'},opis:{type:'string'},scena_splaty:{type:'string'}}}}}},
  log:{type:'object',required:['scena','werdykt'],properties:{scena:{type:'string'},werdykt:{type:'string'},sprzecznosci:{type:'string'},decyzja:{type:'string'}}} } }

phase('Audyt')
const WYMIARY = [
  'Opisy i stan postaci: czy wygląd/maniery zgodne z opisem RO; czy zmiany stanu/relacji są spójne z dotychczasowym.',
  'Chronologia i oś czasu: czy kolejność i upływ czasu się zgadzają; brak cofnięć i dziur.',
  'Nazwy i odmiana: czy każda nazwa własna jest z glosariusza i odmieniona zgodnie z nim; brak wariantów zakazanych.',
  'Zasady świata: czy scena nie łamie zasad (z kosztem/ograniczeniem) ani konsekwencji świata.',
  'POV i czas gramatyczny: czy scena trzyma zadeklarowany POV i czas.',
  'Zasiewy (setup/payoff): co scena zasiewa, co spłaca; czy nie zostawia otwartych bez planu wypłaty.',
]
const audyty = (await parallel(WYMIARY.map((w,i)=>()=>
  agent(`${ROLE}\n\nWYMIAR AUDYTU: ${w}\n\nTEKST SCENY:\n${PROZA}\n\nZgłoś sprzecznosci (pole, co mówi scena, co mówi biblia, waga) i ustalenia (nowe fakty/nazwy/zmiany — typ, treść). Tylko w swoim wymiarze.`,
    {label:`audyt:${i+1}`,phase:'Audyt',schema:AUDYT})))).filter(Boolean)

phase('Klasyfikacja')
const plan = await agent(
  `${ROLE}\n\nAudyty zespołu:\n${JSON.stringify(audyty)}\n\nZbuduj plan. KLUCZOWE rozróżnienie:\n- pola RO (POV, czas, opis fizyczny postaci, łuki, zasady świata, motyw, kanoniczne nazwy i odmiana) → jeśli scena im przeczy, to KONFLIKT: zgłoś w konflikty[] (pole, opis, scena_mowi, biblia_mowi, rekomendacja). NIE wpisuj zmian RO do zapis.\n- pola RUNTIME (nowe fakty, nowe nazwy z odmianą, zmiany _stan postaci, oś czasu, status setup/payoff) → wpisz do zapis (tylko to, co spójne i nowe).\nUstal werdykt: PASS (brak konfliktów) lub CONFLICT. Dodaj log {scena:"${SC.id}", werdykt, sprzecznosci (skrót), decyzja (np. „do rozstrzygnięcia przez autora”)}. Pewność nowych faktów ustaw "roboczy", chyba że poparte researchem.`,
  {label:'klasyfikacja',phase:'Klasyfikacja',schema:PLAN})

return { id: SC.id, plan, audyty }
```

## Po powrocie roju (główna sesja)

1. **Konflikty** (jeśli są): pokaż autorowi (`AskUserQuestion`); RO zmieniaj tylko za zgodą. Bez zgody — nie zapisuj RO, zostaw w logu jako „do rozstrzygnięcia”.
2. **Write-back deterministyczny** (skrypt przez `bible.py`): zastosuj `plan.zapis` (RUNTIME) — `append_record`/`update_runtime`, oznacz scenę `set_scene_status(...,'zweryfikowana')`, `append_log(plan.log)` jako ostatni, `render_index()`. Pól RO skrypt nie tyka (RO→CONFLICT + snapshot). Szczegóły: `build-and-verify.md`.
3. **Podsumowanie dla autora** (werdykt, dopisane fakty/nazwy, otwarte zasiewy); bez plików — jedyny wynik to aktualizacja biblii.

## Fallback
Brak Workflow → audytorzy jako równoległe agenty `Task`, potem agent-synteza tworzy plan; zapis i tak wykonuje skrypt główny.
