# Skrypt roju (Workflow) — pakiet wydawniczy

Skopiuj do narzędzia **Workflow**. `args`: `{ fabula, biblia, words, rynek, bio }`, gdzie `fabula` to streszczenie całości (z beatów/streszczeń scen i setup_payoff — NIE pełny maszynopis), `biblia` to `{ meta, protagonista, stawka, motyw, comps }`, `words` to liczba słów książki, `rynek` i `bio` z dopytania (bio może być puste).

```javascript
export const meta = {
  name: 'book-forge-publishing-package',
  description: 'Roj tworzy pakiet sprzedazowy: logline, pitch, blurb, synopsis, list do agenta, comps',
  phases: [ { title: 'Komponenty' }, { title: 'Ocena' }, { title: 'Redakcja PL' } ],
}

// Workflow bywa, że podaje `args` jako string JSON, nie jako obiekt — parsuj odpornie
let A
try { A = typeof args === 'string' ? JSON.parse(args) : (args || {}) }
catch (e) { throw new Error('args podane jako string, ale to nie poprawny JSON ('+e.message+'). Przekaż obiekt albo poprawny JSON.') }
const F = A.fabula, B = A.biblia, WORDS = A.words || 0, RYNEK = A.rynek || 'rynek polski', BIO = A.bio || ''

const ROLE = `Jesteś agentem literackim / redaktorem ds. zakupów piszącym materiały sprzedażowe. Rynek: ${RYNEK}. Liczba słów: ${WORDS}. DANE Z BIBLII (meta, protagonista, stawka, motyw, comps):\n${JSON.stringify(B)}\n\nSTRESZCZENIE FABUŁY:\n${JSON.stringify(F)}\n\nŻELAZNE zasady: comp titles ujmuj jako „dla czytelników X i Y” (NIE „w stylu autora Z” — ochrona przed zarzutem imitacji); ZERO zmyślonych nagród, sprzedaży, cytatów czy referencji; bio autora zostaw jako pole do uzupełnienia (${BIO?('podane: '+BIO):'puste'}). Pisz po polsku, naturalnie.`

const CMP = { type:'object', required:['klucz','tekst'], properties:{ klucz:{type:'string'}, tekst:{type:'string'} } }
const COMPS = { type:'object', required:['comps'], properties:{ comps:{type:'array',items:{
  type:'object',required:['tytul','dla_czytelnikow'],properties:{tytul:{type:'string'},dla_czytelnikow:{type:'string'}}}} } }
const PAKIET = { type:'object', required:['logline','pitch','blurb','synopsis','query','comps'], properties:{
  logline:{type:'string'}, pitch:{type:'string'}, blurb:{type:'string'}, synopsis:{type:'string'}, query:{type:'string'},
  comps:{type:'array',items:{type:'object',properties:{tytul:{type:'string'},dla_czytelnikow:{type:'string'}}}},
  uwagi:{type:'array',items:{type:'string'}} } }

phase('Komponenty')
const ZADANIA = [
  {klucz:'logline', opis:'Logline w JEDNYM zdaniu: protagonista pragnie Y, ale Z stoi na drodze; stawka jasna.'},
  {klucz:'pitch', opis:'Elevator pitch (2-3 zdania): haczyk + świat + stawka, tak by zatrzymać agenta.'},
  {klucz:'blurb', opis:'Opis z okładki (~150 słów): kusi, buduje napięcie, BEZ zdradzania zakończenia.'},
  {klucz:'synopsis', opis:'Synopsis 1-2 strony: cała fabuła PO KOLEI, z ujawnionym zakończeniem i łukiem protagonisty (dla agenta).'},
  {klucz:'query', opis:'List do agenta: hak (1 akapit), krótkie przedstawienie książki (gatunek, liczba słów), comp titles, miejsce na bio i dane kontaktowe jako pola do uzupełnienia.'},
]
const czesci = (await parallel(ZADANIA.map(z=>()=>
  agent(`${ROLE}\n\nNapisz komponent: ${z.opis}\nZwróć klucz="${z.klucz}" i tekst.`,
    {label:`cz:${z.klucz}`,phase:'Komponenty',schema:CMP})))).filter(Boolean)
const comps = await agent(
  `${ROLE}\n\nDobierz 3-5 comp titles (książki/serie), KAŻDY ujęty jako „dla czytelników X i Y” — opis przez odbiorcę i półkę, nie przez naśladowanie autora. Zwróć comps[{tytul, dla_czytelnikow}].`,
  {label:'comps',phase:'Komponenty',schema:COMPS})

const get = k => (czesci.find(c=>c.klucz===k)||{}).tekst || ''
const pakiet0 = { logline:get('logline'), pitch:get('pitch'), blurb:get('blurb'), synopsis:get('synopsis'), query:get('query'), comps:(comps&&comps.comps)||[] }

phase('Ocena')
const oceniony = await agent(
  `${ROLE}\n\nOto pakiet:\n${JSON.stringify(pakiet0)}\n\nOceń i POPRAW jako agent, który musi to sprzedać: czy logline/pitch chwytają; czy blurb kusi BEZ spoilera; czy synopsis jest kompletny z zakończeniem; czy comps są „dla czytelników X i Y” (popraw, jeśli któryś jest „w stylu autora”); czy nigdzie nie ma zmyślonych referencji/nagród (usuń). Zwróć poprawiony pakiet (logline, pitch, blurb, synopsis, query, comps) i uwagi (co zmieniono / o czym pamiętać).`,
  {label:'ocena',phase:'Ocena',schema:PAKIET})

phase('Redakcja PL')
const red = await agent(
  `Jesteś redaktorem języka polskiego. Wyczyść pakiet z anglicyzmów, kalk i AI-slopu; naturalna polszczyzna, cudzysłowy „ ”. Nie zmieniaj sensu, comp titles ani pól do uzupełnienia (bio/kontakt). Zwróć ten sam pakiet.\n\n${JSON.stringify(oceniony)}`,
  {label:'redakcja',phase:'Redakcja PL',schema:PAKIET})

return red && red.logline ? red : oceniony
```

## Po powrocie roju (główna sesja)

1. **Unslop** na prozie pakietu (pitch, blurb, synopsis, list); nie zniekształcaj nazw ani comp titles.
2. Zapisz `pakiet.md` (wszystkie komponenty) + `pakiet-<slug>.html`. Szczegóły: `build-and-verify.md`.
3. Przypomnij autorowi o uzupełnieniu bio i danych kontaktowych w liście (pola zostawione puste).

## Wariant awaryjny
Brak narzędzia Workflow → komponenty równoległymi agentami `Task`, potem agent-ocena i redakcja.
