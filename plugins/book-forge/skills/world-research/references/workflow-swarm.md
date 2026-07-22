# Skrypt roju (Workflow) — research świata → kanon

Skopiuj do narzędzia **Workflow**. `args`: `{ needs, bible, rygor }`, gdzie `needs` to zebrane luki badawcze (z `sceny[].research`, zasad bez ugruntowania, listy autora), `bible` to WYCIĄG (subgatunek, tytuły porównawcze, zasady świata, glosariusz), a `rygor` to wymóg weryfikacji (np. „2 niezależne źródła dla faktu twardego”).

```javascript
export const meta = {
  name: 'book-forge-world-research',
  description: 'Roj: plan pytan -> research (agent-browser/WebSearch) -> weryfikacja adwersaryjna -> integracja do kanonu',
  phases: [ { title: 'Plan pytan' }, { title: 'Research' }, { title: 'Weryfikacja' }, { title: 'Integracja' }, { title: 'Redakcja PL' } ],
}

// Workflow bywa, że podaje `args` jako string JSON, nie jako obiekt — parsuj odpornie
let A
try { A = typeof args === 'string' ? JSON.parse(args) : (args || {}) }
catch (e) { throw new Error('args podane jako string, ale to nie poprawny JSON ('+e.message+'). Przekaż obiekt albo poprawny JSON.') }
const NEEDS = A.needs || [], B = A.bible, RYGOR = A.rygor || '1 wiarygodne zrodlo; dla faktow twardych 2 niezalezne'

const ROLE = `Jesteś researcherem i konsultantem merytorycznym (science / fact-checker) dla powieści. Subgatunek i kontekst świata: ${JSON.stringify(B)}. Szukasz przez WebSearch/WebFetch, a gdy trzeba wejść na konkretną stronę — przez agent-browser (Bash). Odróżniaj źródło wiarygodne od przypadkowego. NIGDY nie zmyślaj: brak wiarygodnego źródła = "nie ustalono". Rygor weryfikacji: ${RYGOR}. Pisz po polsku.`

const QPLAN = { type:'object', required:['pytania'], properties:{ pytania:{type:'array',items:{
  type:'object',required:['q','typ'],properties:{q:{type:'string'},typ:{type:'string'},kontekst:{type:'string'}}}} } }
const FIND = { type:'object', required:['q','ustalono'], properties:{
  q:{type:'string'}, ustalono:{type:'boolean'}, odpowiedz:{type:'string'}, pewnosc:{type:'string'},
  zrodla:{type:'array',items:{type:'object',required:['zrodlo'],properties:{zrodlo:{type:'string'},url:{type:'string'},data:{type:'string'}}}} } }
const VERD = { type:'object', required:['q','keep'], properties:{
  q:{type:'string'}, keep:{type:'boolean'}, drugie_zrodlo:{type:'boolean'}, powod:{type:'string'} } }
const INTEGR = { type:'object', required:['fakty','zrodla'], properties:{
  zasady:{type:'array',items:{type:'object',required:['zasada','koszt','ograniczenie'],properties:{zasada:{type:'string'},koszt:{type:'string'},ograniczenie:{type:'string'}}}},
  fakty:{type:'array',items:{type:'object',required:['tresc','typ','pewnosc'],properties:{tresc:{type:'string'},typ:{type:'string'},pewnosc:{type:'string'},zrodlo_ref:{type:'string'}}}},
  zrodla:{type:'array',items:{type:'object',required:['id','dotyczy','zrodlo'],properties:{id:{type:'string'},dotyczy:{type:'string'},zrodlo:{type:'string'},url:{type:'string'},data:{type:'string'},notatka:{type:'string'}}}} } }

phase('Plan pytan')
const plan = await agent(
  `${ROLE}\n\nLuki badawcze do rozpracowania:\n${JSON.stringify(NEEDS)}\n\nZamień je w precyzyjne, odpowiadalne pytania. Każde oznacz typ="fakt" (konkret do zweryfikowania) lub typ="zasada" (reguła świata do ugruntowania w realiach). Połącz duplikaty, odrzuć pytania bez znaczenia dla fabuły. Jeśli żadne nie wymaga researchu, zwróć pustą listę.`,
  {label:'plan-pytan',phase:'Plan pytan',schema:QPLAN})
const pytania = (plan && plan.pytania) || []

phase('Research')
const findings = pytania.length ? (await parallel(pytania.map((p,i)=>()=>
  agent(`${ROLE}\n\nPytanie (${p.typ}): ${p.q}\nKontekst: ${p.kontekst||''}\n\nZnajdź odpowiedź w wiarygodnych źródłach (WebSearch/WebFetch; agent-browser dla konkretnej strony). Zwróć: q, ustalono (true/false), odpowiedz (zwięzła), pewnosc (wysoka/średnia/niska), zrodla[{zrodlo,url,data}]. Jeśli brak wiarygodnego źródła: ustalono=false.`,
    {label:`research:${i+1}`,phase:'Research',schema:FIND})))).filter(Boolean) : []

phase('Weryfikacja')
const ustalone = findings.filter(f=>f.ustalono)
const werdykty = ustalone.length ? (await parallel(ustalone.map((f,i)=>()=>
  agent(`Jesteś sceptycznym fact-checkerem. Sprawdź to ustalenie: czy źródło jest wiarygodne, czy potwierdza je drugie niezależne źródło, czy nie ma sprzeczności. Rygor: ${RYGOR}.\n\nUSTALENIE:\n${JSON.stringify(f)}\n\nZwróć q, keep (true tylko gdy wiarygodne i spełnia rygor), drugie_zrodlo (bool), powod.`,
    {label:`weryfikacja:${i+1}`,phase:'Weryfikacja',schema:VERD})))).filter(Boolean) : []
const potwierdzone = ustalone.filter(f=>{ const v=werdykty.find(w=>w.q===f.q); return v && v.keep })

phase('Integracja')
const integr = potwierdzone.length ? await agent(
  `${ROLE}\n\nPotwierdzone ustalenia:\n${JSON.stringify(potwierdzone)}\n\nIstniejące zasady świata:\n${JSON.stringify((B&&B.zasady)||[])}\n\nZintegruj w kanon: (1) zasady — doprecyzowane reguły świata z REALNYM kosztem i ograniczeniem (tylko tam, gdzie research to uzasadnia); (2) fakty — wpisy {tresc, typ:"swiat", pewnosc:"kanon", zrodlo_ref:"Zxx"}; (3) zrodla — rejestr {id:"Z01"..., dotyczy (id faktu lub nazwa zasady), zrodlo, url, data, notatka}. Powiąż każdy fakt z wpisem w zrodla przez zrodlo_ref.`,
  {label:'integracja',phase:'Integracja',schema:INTEGR}) : { zasady:[], fakty:[], zrodla:[] }

phase('Redakcja PL')
const red = (integr.fakty && integr.fakty.length) ? await agent(
  `Jesteś redaktorem języka polskiego. Przepisz opisy zasad i faktów na naturalną polszczyznę (bez anglicyzmów, AI-slopu; cudzysłowy „ ”). NIE ruszaj nazw własnych, URL-i ani dat. Zwróć tę samą strukturę.\n\n${JSON.stringify(integr)}`,
  {label:'redakcja',phase:'Redakcja PL',schema:INTEGR}) : integr

return {
  pytania,
  findings,
  nieustalone: findings.filter(f=>!f.ustalono).map(f=>f.q),
  oflagowane: ustalone.filter(f=>{ const v=werdykty.find(w=>w.q===f.q); return !(v&&v.keep) }).map(f=>f.q),
  integracja: red && red.fakty ? red : integr,
}
```

## Po powrocie roju (główna sesja)

1. **Unslop** na opisowych partiach ustaleń.
2. **Zapis do biblii** (przez `bible.py`): dopisz `fakty` i `zrodla` pętlą `bible.append_record(...)`; doprecyzowanie istniejących `swiat.zasady` (RO) tylko po potwierdzeniu autora (`bible.write_section('swiat', ...)`); na końcu `bible.render_index()`. Szczegóły: `build-and-verify.md`.
3. **Bez osobnych artefaktów** (`research.md`/`.html` nie powstają) — wynik żyje w biblii; pokaż autorowi nieustalone i oflagowane pytania.

## Fallback
Brak Workflow → te same fazy równoległymi agentami `Task` (plan → research → weryfikacja → integracja → redakcja).
