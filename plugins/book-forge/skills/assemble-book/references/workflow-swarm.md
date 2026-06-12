# Skrypt roju (Workflow) — przeglądy całości książki

Skopiuj do narzędzia **Workflow**. `args`: `{ sceny, kanon }`, gdzie `sceny` to lista `{id, rozdzial, words, value, streszczenie}` (STRESZCZENIA, nie pełna proza — chroni okno kontekstu), a `kanon` to `{ beaty, setup_payoff, os_czasu, luki_postaci, motyw }` z biblii. Audyt pracuje na streszczeniach i strukturze, nie na pełnym tekście.

```javascript
export const meta = {
  name: 'book-forge-assemble-book',
  description: 'Roj przeglada calosc: luk fabularny i postaci, zasiewy, tempo, motyw, os czasu -> werdykt gotowosci',
  phases: [ { title: 'Przeglady' }, { title: 'Synteza' } ],
}

// Workflow bywa, że podaje `args` jako string JSON, nie jako obiekt — parsuj odpornie
let A
try { A = typeof args === 'string' ? JSON.parse(args) : (args || {}) }
catch (e) { throw new Error('args podane jako string, ale to nie poprawny JSON ('+e.message+'). Przekaż obiekt albo poprawny JSON.') }
const SCENY = A.sceny || [], K = A.kanon || {}

const ROLE = `Jesteś redaktorem prowadzącym oceniającym CAŁĄ książkę (nie pojedynczą scenę). Pracujesz na streszczeniach scen i strukturze kanonu. KANON:\n${JSON.stringify(K)}\n\nSCENY (streszczenia, kolejność):\n${JSON.stringify(SCENY)}\n\nPisz po polsku.`

const AUDYT = { type:'object', required:['wymiar','werdykt','problemy'], properties:{
  wymiar:{type:'string'}, werdykt:{type:'string'},
  problemy:{type:'array',items:{type:'object',required:['opis'],properties:{opis:{type:'string'},gdzie:{type:'string'},waga:{type:'string'}}}} } }

const SYNT = { type:'object', required:['werdykt_gotowosci','problemy','zasiewy_otwarte','luki_luku'], properties:{
  werdykt_gotowosci:{type:'string'},
  problemy:{type:'array',items:{type:'object',required:['typ','opis'],properties:{typ:{type:'string'},opis:{type:'string'},gdzie:{type:'string'},waga:{type:'string'}}}},
  zasiewy_otwarte:{type:'array',items:{type:'string'}},
  luki_luku:{type:'array',items:{type:'string'}},
  setup_payoff_finalny:{type:'array',items:{type:'object',properties:{id:{type:'string'},status:{type:'string'}}}} } }

phase('Przeglady')
// beaty z kanonu wybranej struktury (kishōtenketsu, 7 punktów…) — trójakt to tylko fallback, nie norma
const BEATY = (Array.isArray(K.beaty) && K.beaty.length) ? K.beaty
  : ['incydent inicjujący','próg I aktu','środek','czarna chwila','kulminacja','rozwiązanie']
const WYMIARY = [
  `Łuk fabularny: czy beaty WYBRANEJ struktury są domknięte (${BEATY.join(' → ')}), brak urwanych wątków. Oceniaj wobec tej struktury, nie wciskaj trójaktu.`,
  'Łuk postaci: czy przemiana protagonisty się realizuje (rana → kłamstwo → zmiana); czy poboczni mają domknięcia.',
  'Zasiewy: przejdź setup_payoff i streszczenia; wskaż KAŻDY zasiew bez wypłaty (strzelba, która nie wypaliła).',
  'Tempo: rozkład wartości +/– i długości scen; wskaż miejsca, gdzie za długo na jednym rejestrze, zapadnięcia napięcia, zbyt nagłe skoki.',
  'Motyw: czy temat i motywy przewijają się spójnie przez całość, bez dydaktyzmu i bez zniknięcia w środku.',
  'Oś czasu: spójność chronologii całości — brak cofnięć, dziur i sprzecznych odstępów.',
]
const audyty = (await parallel(WYMIARY.map((w,i)=>()=>
  agent(`${ROLE}\n\nWYMIAR PRZEGLĄDU: ${w}\n\nZwróć wymiar, werdykt (OK|PROBLEM) i problemy (opis, gdzie, waga).`,
    {label:`przeglad:${i+1}`,phase:'Przeglady',schema:AUDYT})))).filter(Boolean)

phase('Synteza')
const synt = await agent(
  `${ROLE}\n\nPrzeglądy zespołu:\n${JSON.stringify(audyty)}\n\nZbuduj werdykt gotowości książki: werdykt_gotowosci ("gotowa do zamrożenia" / "do poprawy"), problemy (typ, opis, gdzie, waga), zasiewy_otwarte (lista id/opisów bez wypłaty), luki_luku (niedomknięcia łuku), setup_payoff_finalny (id → status domkniety/otwarty). Krytyczne problemy (otwarty główny zasiew, niedomknięty łuk protagonisty) blokują zamrożenie kanonu.`,
  {label:'synteza',phase:'Synteza',schema:SYNT})

return { audyty, synteza: synt }
```

## Po powrocie roju (główna sesja)

1. **Złożenie** `ksiazka.md` (deterministycznie, skrypt): sceny w kolejności rozdział→scena, nagłówki rozdziałów, liczby słów.
2. **Aktualizacja biblii** (przez `bible.py`): `setup_payoff` finalne statusy (z `setup_payoff_finalny`) przez `bible.append_record('setup_payoff', ...)`, oznaczenie domknięcia łuków/rozdziałów; na końcu `bible.render_index()`. **Promocja `working` → `published`** przez `bible.freeze_canon(True)` tylko gdy `werdykt_gotowosci` = „gotowa do zamrożenia”, brak krytycznych problemów i autor potwierdzi.
3. **Artefakty** `ksiazka-<slug>.html` (przegląd) i podsumowanie. Szczegóły: `build-and-verify.md`.

## Wariant awaryjny
Brak Workflow → audytorzy jako równoległe agenty `Task`, potem agent-synteza; złożenie i zapis robi skrypt główny.
