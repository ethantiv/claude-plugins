# Skrypt roju (Workflow) — konspekt → siatka scen

Skopiuj do narzędzia **Workflow**. `args`: `{ chapters, bible, scenesHint }`, gdzie `chapters` to lista rozdziałów z konspektu (obietnica, kluczowe punkty, emocja), a `bible` to wyciąg z biblii (POV/czas, postacie z łukami, stawka, motyw, zasady świata, glosariusz). Nie wklejaj całej biblii, tylko wyciąg.

```javascript
export const meta = {
  name: 'book-forge-outline-to-scenes',
  description: 'Roj: mapa luku -> siatka scen -> os czasu i zasiewy -> krytyka -> redakcja PL',
  phases: [ { title: 'Mapa luku' }, { title: 'Siatka scen' }, { title: 'Os i zasiewy' }, { title: 'Krytyka' }, { title: 'Redakcja PL' } ],
}

// Workflow bywa, że podaje `args` jako string JSON, nie jako obiekt — parsuj odpornie
let A
try { A = typeof args === 'string' ? JSON.parse(args) : (args || {}) }
catch (e) { throw new Error('args podane jako string, ale to nie poprawny JSON ('+e.message+'). Przekaż obiekt albo poprawny JSON.') }
const CH = A.chapters, B = A.bible, HINT = A.scenesHint || '1-3 sceny na rozdział, wedle potrzeby'
// Beaty zależą od WYBRANEJ struktury (z konspektu), nie zawsze trójakt. A.beaty (z konspektu/biblii) ma pierwszeństwo.
const STRUKTURA = A.struktura || 'trójaktowa'
const BEATY = Array.isArray(A.beaty) && A.beaty.length ? A.beaty
  : (B && B.kanon_fabularny && Array.isArray(B.kanon_fabularny.beaty) && B.kanon_fabularny.beaty.length ? B.kanon_fabularny.beaty
    : ['incydent inicjujący','próg I aktu','środek','czarna chwila','kulminacja','rozwiązanie'])
// Tryb serii: aktywny tom (z .book-forge/seria.md → tom_aktywny). Tom 1 / pojedyncza książka bez prefiksu (wstecznie zgodne).
const TOM = A.tom || 1
const TP  = TOM > 1 ? `T${TOM}` : ''      // prefiks ID scen: '' dla tomu 1, 'T2' dla tomu 2…
const SERIA = A.seria || null             // { obietnica_serii, zasiewy_miedzytomowe[] } lub null (pojedyncza książka)

const ROLE = `Jesteś architektem struktury powieści, który myśli SCENAMI i przyczynowością, nie streszczeniem. Trzymaj się biblii: POV/czas, łuki postaci, stawka, zasady świata, nazwy z glosariusza (z odmianą). WYCIĄG Z BIBLII:\n${JSON.stringify(B)}${SERIA ? `\n\nKONTEKST SERII (tom ${TOM}): obietnica serii i zasiewy międzytomowe — niektóre zasiewy MOGĄ celowo zostać otwarte, jeśli ich tom wypłaty > ${TOM}:\n${JSON.stringify(SERIA)}` : ''}\n\nPisz po polsku, naturalnie.`

const ARC = { type:'object', required:['krzywa','podsumowanie'], properties:{
  krzywa:{type:'array',items:{type:'object',required:['beat','gdzie','opis'],properties:{beat:{type:'string'},gdzie:{type:'string'},opis:{type:'string'}}}},
  podsumowanie:{type:'string'} } }
const SCENE = { type:'object', required:['id','rozdzial','pov','cel','konflikt','zwrot','value','typ'], properties:{
  id:{type:'string'}, rozdzial:{type:'number'}, pov:{type:'string'}, miejsce:{type:'string'}, czas:{type:'string'},
  typ:{type:'string'},   // kluczowa | pomostowa | sekwel — steruje kryteriami dev-edit (pomost nie wymaga pełnego value_shift)
  cel:{type:'string'}, konflikt:{type:'string'}, zwrot:{type:'string'}, value:{type:'string'}, luk:{type:'string'},
  subwersja:{type:'string'}, kotwica:{type:'string'},   // opcjonalne — przeniesione z rozdziału konspektu na scenę otwierającą; honoruje je write-scene
  zasiewa:{type:'array',items:{type:'string'}}, splaca:{type:'array',items:{type:'string'}}, research:{type:'array',items:{type:'string'}} } }
const SCENESET = { type:'object', required:['sceny'], properties:{ sceny:{type:'array',items:SCENE} } }
const SP = { type:'object', required:['setup_payoff','os_czasu'], properties:{
  setup_payoff:{type:'array',items:{type:'object',required:['id','opis','typ','status'],properties:{id:{type:'string'},opis:{type:'string'},typ:{type:'string'},scena_zasiewu:{type:'string'},scena_splaty:{type:'string'},status:{type:'string'}}}},
  os_czasu:{type:'array',items:{type:'object',required:['scena','kolejnosc'],properties:{scena:{type:'string'},dzien_fabularny:{type:'string'},kolejnosc:{type:'number'}}}} } }
const CRIT = { type:'object', required:['id','ma_cel','ma_zwrot','wartosc_sie_zmienia','filler'], properties:{
  id:{type:'string'}, ma_cel:{type:'boolean'}, ma_zwrot:{type:'boolean'}, wartosc_sie_zmienia:{type:'boolean'},
  przyczynowosc:{type:'boolean'}, filler:{type:'boolean'}, uwaga:{type:'string'}, fix:{type:'string'} } }

phase('Mapa luku')
const arc = await agent(
  `${ROLE}\n\nRozdziały z konspektu:\n${JSON.stringify(CH)}\n\nStruktura narracyjna: ${STRUKTURA}. Zbuduj mapę łuku protagonisty: przypisz beaty TEJ struktury (${BEATY.join(', ')}) do rozdziałów/fragmentów i opisz krzywą wartości (jak emocja rośnie i opada). Trzymaj się beatów struktury — nie wciskaj trójaktu, jeśli wybrano kishōtenketsu czy strukturę 7 punktów. Zwróć krzywa[] i podsumowanie.`,
  {label:'mapa-luku',phase:'Mapa luku',schema:ARC})

phase('Siatka scen')
const zestawy = (await parallel(CH.map((c,i)=>()=>
  agent(`${ROLE}\n\nMapa łuku:\n${JSON.stringify(arc)}\n\nRozdział ${i+1}:\n${JSON.stringify(c)}\n\nRozpisz ten rozdział na sceny (${HINT}). Każda scena: id (DOKŁADNIE w formacie "${TP}R${i+1}S<n>", np. "${TP}R${i+1}S1" — prefiks tomu "${TP}" jest OBOWIĄZKOWY, jeśli niepusty), rozdzial=${i+1}, pov, miejsce, czas, typ ("kluczowa" — pełna scena z celem i zwrotem; "pomostowa" — krótkie przejście/oddech/sumariusz bez pełnego zwrotu wartości; "sekwel" — reakcja po kulminacji; większość scen jest kluczowa, ale wpleć pomostowe dla rytmu, by proza nie była jednostajnie napięta), cel (czego chce postać), konflikt (co stoi na drodze), zwrot (jak kończy się scena, zmiana wartości; dla pomostowej może być drobny), value ("+" lub "-"), luk (jak posuwa łuk protagonisty), zasiewa (co zapowiada — w tym zasiewy międzytomowe serii, jeśli scena je realizuje), splaca (jaki wcześniejszy zasiew domyka), research (realia wymagające weryfikacji — może być puste). Jeśli rozdział niesie pola „subwersja"/„kotwica" (z konspektu), PRZENIEŚ je na PIERWSZĄ (otwierającą) scenę tego rozdziału jako pola subwersja/kotwica — nie powielaj ich na pozostałe sceny. Bez wypełniaczy; każda scena ma cel i zwrot.`,
    {label:`sceny:${TP}R${i+1}`,phase:'Siatka scen',schema:SCENESET})))).filter(Boolean)
let sceny = zestawy.flatMap(z=>z.sceny)

phase('Os i zasiewy')
const sp = await agent(
  `${ROLE}\n\nWszystkie sceny:\n${JSON.stringify(sceny)}\n\nZbuduj: (1) setup_payoff — rejestr zasiewów i wypłat (id, opis, typ: glowny|poboczny|strzelba, scena_zasiewu, scena_splaty, status: otwarty|domkniety); upewnij się, że każdy istotny zasiew ma wypłatę. (2) os_czasu — dla każdej sceny dzień fabularny i kolejność chronologiczna (vs narracyjna). Zgłoś w opisie zasiewy bez wypłaty.`,
  {label:'os-i-zasiewy',phase:'Os i zasiewy',schema:SP})

phase('Krytyka')
const krytyka = (await parallel(sceny.map(s=>()=>
  agent(`${ROLE}\n\nOceń KRYTYCZNIE scenę pod kątem struktury (nie prozy). Scena:\n${JSON.stringify(s)}\n\nCzy ma cel? Czy ma zwrot? Czy wartość naprawdę się zmienia? Czy wynika przyczynowo z poprzednich („a więc/ale”, nie „i potem”)? Czy to wypełniacz? Zwróć id, ma_cel, ma_zwrot, wartosc_sie_zmienia, przyczynowosc, filler, uwaga, fix.`,
    {label:`krytyk:${s.id}`,phase:'Krytyka',schema:CRIT})))).filter(Boolean)

const doNaprawy = krytyka.filter(k=>k.filler || !k.ma_cel || !k.ma_zwrot || !k.wartosc_sie_zmienia)
if (doNaprawy.length) {
  const rew = await agent(
    `${ROLE}\n\nSiatka scen:\n${JSON.stringify(sceny)}\n\nUwagi krytyków:\n${JSON.stringify(doNaprawy)}\n\nPopraw siatkę: wytnij lub połącz wypełniacze, dodaj brakujące cele/zwroty, wyrównaj krzywą wartości i przyczynowość. Przenumeruj id po cięciach. Zwróć finalną listę scen.`,
    {label:'rewizja-scen',phase:'Krytyka',schema:SCENESET})
  if (rew && rew.sceny) sceny = rew.sceny
}

phase('Redakcja PL')
const red = await agent(
  `Jesteś redaktorem języka polskiego. Przepisz opisy scen na naturalną polszczyznę (bez anglicyzmów: plot twist → zwrot akcji, stakes → stawka; bez AI-slopu; cudzysłowy „ ”). Nie ruszaj nazw własnych z glosariusza. Zwróć tę samą strukturę.\n\n${JSON.stringify(sceny)}`,
  {label:'redakcja',phase:'Redakcja PL',schema:SCENESET})
if (red && red.sceny) sceny = red.sceny

return {
  arc,
  scenes: sceny,
  rozdzialy: (CH||[]).map((c,i)=>({nr:i+1, tytul:(c && c.title) || ''})),  // nr zgodne ze scene.rozdzial (=i+1), tytuły do nagłówków w assemble-book
  setup_payoff: sp.setup_payoff || [],
  os_czasu: sp.os_czasu || [],
  research_needs: [...new Set(sceny.flatMap(s=>s.research||[]))],
}
```

## Po powrocie roju (główna sesja)

1. **Humanizer** na opisach scen (`/humanizer:humanizer`), nazwy własne chronione.
2. **Zapis do biblii** (przez `bible.py`): siatka scen przez `bible.write_scene_grid(...)` (status `"planowana"`), `setup_payoff` i `os_czasu` pętlą `bible.append_record(...)`; na końcu `bible.render_index()`.
3. **Scalenie** siatki scen do `konspekt-<slug>.html` jako zakładka „Sceny" (osobny plik scen ani `sceny.md` nie powstają) i walidacja — `build-and-verify.md`.
4. Lista `research_needs` przekazana autorowi jako wejście do etapu `world-research`.

## Awaryjnie
Brak narzędzia Workflow → te same fazy równoległymi agentami `Task` (mapa łuku → sceny w podziale na rozdziały → oś i zasiewy → krytyka → redakcja).
