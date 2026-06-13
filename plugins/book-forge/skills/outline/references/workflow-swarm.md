# Skrypt roju agentów (Workflow) — konspekt rozdział po rozdziale

Skopiuj skrypt do narzędzia **Workflow** i podstaw dane przez `args`: `{ idea, genre, reader, brief, verdict, length, chapters, transformation }`, gdzie `idea` to zwycięski pomysł z etapu 1 (`{ t, en, op, hook, gap, comps, protagonista }`), `brief` to brief autora z etapu 1 (`{ subgenre, conventions, protagonist, protAge, protType, form, format, tone, taboo, ... }`), a `verdict` to uzasadnienie z raportu (`{ rationale, whyNow, positioning }`). **Brief MUSI tu trafić** — bez niego rój nie zna tonu, bohatera, formatu, konwencji ani tabu i pisze konspekt na ślepo. Ten sam rygor co w etapie 1: rola ekspercka, świeży research przez WebSearch/agent-browser, a ostatnia faza to redakcja na poprawną, naturalną polszczyznę (patrz `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`).

```javascript
export const meta = {
  name: 'book-forge-outline',
  description: 'Roj agentow: fundament -> struktura -> rozdzialy -> ciecie wypelniaczy -> redakcja PL',
  phases: [
    { title: 'Fundament' }, { title: 'Struktura' }, { title: 'Rozdzialy' },
    { title: 'Ciecie wypelniaczy' }, { title: 'Redakcja PL' },
  ],
}

// Workflow bywa, że podaje `args` jako string JSON, nie jako obiekt — parsuj odpornie
let A
try { A = typeof args === 'string' ? JSON.parse(args) : (args || {}) }
catch (e) { throw new Error('args podane jako string, ale to nie poprawny JSON ('+e.message+'). Przekaż obiekt albo poprawny JSON.') }
const IDEA = A.idea                          // { t, en, silnik, op, hook, gap, comps, protagonista }
const G = A.genre
const R = A.reader
if (!IDEA || !G || !R) throw new Error('Brak idea/genre/reader w args — przerwij, nie uruchamiaj roju z pustym wejściem (uruchom etap 1 albo podaj pomysł).')
const V = (A.verdict && typeof A.verdict === 'object') ? A.verdict : {}   // { rationale, whyNow, positioning }
const B = (A.brief && typeof A.brief === 'object') ? A.brief : {}          // brief autora z etapu 1
if (!Object.keys(B).length) log('UWAGA: brak briefu z etapu 1 — konspekt powstaje bez tonu, tabu i konwencji autora (degradacja, nie błąd)')
const SUBG  = B.subgenre || ''               // podgatunek/nurt
const CONV  = Array.isArray(B.conventions) ? B.conventions : []           // konwencje/obietnice gatunkowe
const FORM  = B.form || ''                   // non-fiction: 'poradnik'|'reportaz'|'esej'|'pamietnik'; '' = fikcja
const PROT  = B.protagonist || 'dowolny'
const PAGE  = B.protAge || ''
const PTYPE = B.protType || ''
const TONE  = B.tone || 'dowolny'
const TABOO = Array.isArray(B.taboo) ? B.taboo : []
const FORMAT= B.format || 'pojedyncza'
const LEN = A.length || '(długość typowa dla gatunku — dobierz przez WebSearch)'   // SKILL powinien przekazać rekomendację z gatunku/podgatunku, nie stałą
const N = A.chapters || 14                   // SKILL powinien przekazać liczbę wyprowadzoną z gatunku i długości; 14 to ostatnia deska ratunku
const TRANS = A.transformation || '(zaproponuj na podstawie pomysłu)'

// Profil bohatera: z pomysłu (etap 1) albo z briefu; przy 'dowolny'/'zroznicuj' nie narzucaj
const PROTAG = IDEA.protagonista || (PROT === 'dowolny' || PROT === 'zroznicuj' ? '' : `${PROT}${PAGE ? ', ' + PAGE : ''}${PTYPE ? ', ' + PTYPE : ''}`)

// Dla non-fiction (FORM) maszyneria fabularna jest reinterpretowana, nie wyłączona
const NONFIC = FORM
  ? `\nUWAGA — to non-fiction (forma: ${FORM}). „Łuk bohatera" czytaj jako transformację CZYTELNIKA / linię argumentu; „haczyk" = mocne otwarcie rozdziału; „zwrot akcji" = kluczowy wniosek lub przeskok myślowy; „przejście emocjonalne/value" = postęp w rozumieniu tematu. Nie wymyślaj fikcyjnej fabuły.`
  : ''

const BRIEF = `
BRIEF AUTORA (z etapu 1 — twarde wymagania, których konspekt MUSI przestrzegać):
${PROTAG ? `- Bohater: ${PROTAG} — zakotwicz łuk w tym profilu.` : '- Bohater: profil zgodny z pomysłem z etapu 1.'}
- Format: ${FORMAT}${FORMAT === 'pojedyncza' ? ' — domknij łuk w jednym tomie.' : ' — to tom serii: zostaw celowo otwarte zasiewy nadrzędne, NIE domykaj łuku całej serii.'}
- Ton: ${TONE === 'dowolny' ? 'dobierz pod niszę' : `utrzymaj ton: ${TONE}`}.
${CONV.length ? `- Konwencje/obietnice gatunkowe, które rozdziały MUSZĄ dowieźć: ${CONV.join(', ')}.` : ''}
${TABOO.length ? `- TABU (NIGDY nie wprowadzaj tych tematów): ${TABOO.join(', ')}.` : ''}${NONFIC}`

const ROLE = `Jesteś mistrzem architektury książek — autorem konspektów ponad pięćdziesięciu bestsellerów. Gatunek: ${G}${SUBG ? `, podgatunek/nurt: ${SUBG}` : ''}. Docelowy czytelnik: ${R}. Pracujesz nad książką: „${IDEA.t}”. Streszczenie pomysłu: ${IDEA.op} Silnik premisy (zachowaj jako centralny konflikt książki): ${IDEA.silnik || '(brak — wyprowadź z premisy)'} Haczyk: ${IDEA.hook}${V.positioning ? ` Pozycjonowanie: ${V.positioning}` : ''} Docelowa długość: ${LEN}. Gdy trzeba, sprawdzaj konwencje budowy i tempa gatunku${SUBG ? ` (nurt: ${SUBG})` : ''} przez WebSearch/agent-browser oraz to, jak zbudowane są tytuły porównawcze (${(IDEA.comps||[]).join(', ')}). Pisz po polsku, naturalnie, bez anglicyzmów.${BRIEF}`

// --- schematy ---
const FUND = { type:'object', required:['premise','theme','transformation','centralConflict','ending','arc'], properties:{
  premise:{type:'string'}, theme:{type:'string'}, transformation:{type:'string'},
  centralConflict:{type:'string'}, ending:{type:'string'}, arc:{type:'string'} } }
const SKELETON = { type:'object', required:['structureName','why','chapters'], properties:{
  structureName:{type:'string'}, why:{type:'string'},
  chapters:{type:'array', items:{ type:'object', required:['n','title','promise','role'], properties:{
    n:{type:'number'}, title:{type:'string'}, promise:{type:'string'}, role:{type:'string'} } } } } }
const JUDGE = { type:'object', required:['structureName','fit','promiseStrength','originality','verdict'], properties:{
  structureName:{type:'string'}, fit:{type:'number'}, promiseStrength:{type:'number'},
  originality:{type:'number'}, subverts:{type:'string'},   // jak ta struktura łamie konwencję gatunku (lub "nic — standardowy szkielet")
  verdict:{type:'string'}, why:{type:'string'} } }
const CHAPTER = { type:'object', required:['n','title','promise','beats','hook','twist','emotion','value','subwersja','kotwica'], properties:{
  n:{type:'number'}, title:{type:'string'}, promise:{type:'string'},
  beats:{type:'array', items:{type:'string'}}, hook:{type:'string'}, twist:{type:'string'},
  emotion:{type:'string'}, value:{type:'string'},          // value: "+", "-" lub etykieta przejścia
  subwersja:{type:'string'},   // jak rozdział łamie oczekiwaną wypłatę centralnego beatu (lub "beat oryginalny")
  kotwica:{type:'string'} } }  // konkretny zapamiętywalny obraz/moment; ew. odwrócona emocja
const CRIT = { type:'object', required:['n','filler','hasHook','hasTwist','advancesArc','maSubwersje','przewidywalny'], properties:{
  n:{type:'number'}, filler:{type:'boolean'}, hasHook:{type:'boolean'}, hasTwist:{type:'boolean'},
  advancesArc:{type:'boolean'}, maSubwersje:{type:'boolean'}, przewidywalny:{type:'boolean'},
  issues:{type:'string'}, fix:{type:'string'} } }

// --- FAZA 1: Fundament ---
phase('Fundament')
const KATY_F = [
  'Od MOTYWU: jaka jedna prawda o świecie/człowieku napędza tę książkę i jak wraca w fabule.',
  'Od ŁUKU BOHATERA: skąd bohater startuje wewnętrznie, dokąd dochodzi, jaki kosztuje go to wybór.',
  'Od OBIETNICY RYNKOWEJ: co dokładnie obiecuje haczyk z etapu 1 i jak fabuła ma tę obietnicę spełnić.',
  'Od ZAKOŃCZENIA: zaproponuj 2 różne finały (oczywisty-satysfakcjonujący vs nieoczywisty-rezonujący), oceń je krótko (rezonans / nieoczywistość / zgodność z premisą) i REKOMENDUJ jeden w polu ending; potem cofnij się do punktu wyjścia. Finał ma czytelnika poruszyć, nie tylko domknąć.',
]
const fundCand = (await parallel(KATY_F.map((k,i)=>()=>
  agent(`${ROLE}\n\nPomysł (z etapu 1):\n${JSON.stringify(IDEA)}\n\nObiektyw: ${k}\nTransformacja (jeśli podana): ${TRANS}\n\nZaproponuj kręgosłup książki: premise (rozszerzona przesłanka), theme (motyw), transformation (skąd → dokąd), centralConflict, ending, arc (łuk emocjonalny całości).`,
    {label:`fundament:${i+1}`,phase:'Fundament',schema:FUND})))).filter(Boolean)

const fundament = await agent(
  `${ROLE}\n\nPropozycje kręgosłupa:\n${JSON.stringify(fundCand)}\n\nScal w JEDEN spójny fundament (premise, theme, transformation, centralConflict, ending, arc). Wybierz najmocniejsze elementy, usuń sprzeczności.`,
  {label:'synteza:fundament',phase:'Fundament',schema:FUND})

// --- FAZA 2: Struktura (panel) ---
phase('Struktura')
const STRUKTURY = [
  'Trójakt z wyraźnymi punktami zwrotnymi.',
  'Podróż bohatera (monomit) dopasowana do gatunku.',
  'Struktura siedmiu punktów (Dan Wells).',
  'Save the Cat / beat sheet w wersji powieściowej.',
  'Kishōtenketsu lub inna struktura nieoparta na konflikcie (jeśli pasuje do gatunku).',
]
const szkielety = (await parallel(STRUKTURY.map((s,i)=>()=>
  agent(`${ROLE}\n\nFundament:\n${JSON.stringify(fundament)}\n\nZbuduj szkielet konspektu w oparciu o: ${s}\nDokładnie ${N} rozdziałów. Dla każdego: n, title (roboczy), promise (jednozdaniowa obietnica), role (funkcja w strukturze). Podaj structureName i why (czemu pasuje do tego gatunku i pomysłu).${FORM ? '' : ' Wskaż TEŻ, jak ta struktura SUBWERTUJE konwencję gatunku (gdzie świadomie odmawia czytelnikowi oczekiwanej kolejności beatów albo oczekiwanej wypłaty) — ujmij to w polu why.'}`,
    {label:`szkielet:${i+1}`,phase:'Struktura',schema:SKELETON})))).filter(Boolean)

const oceny = await parallel(szkielety.map((sz)=>async()=>{
  const votes=(await parallel([1,2,3].map((nr)=>()=>
    agent(`${ROLE}\n\nOceń szkielet pod kątem dopasowania do gatunku ${G} i siły obietnic rozdziałów. Szkielet:\n${JSON.stringify(sz)}\n\nDaj fit (1-5), promiseStrength (1-5), originality (1-5 — gdzie 5 = łamie schemat gatunku w sposób, który nadal dowozi obietnicę), subverts (jednozdaniowo: co konkretnie subwertuje, albo „nic — standardowy szkielet"), verdict keep|kill, why.`,
      {label:`ocena-struktury:${nr}:${sz.structureName.slice(0,14)}`,phase:'Struktura',schema:JUDGE})))).filter(Boolean)
  // originality dostaje wagę 2 (fit/promiseStrength po 1); avg służy tylko sortowaniu, więc skala nie ma znaczenia
  const avg=votes.reduce((s,v)=>s+(v.fit+v.promiseStrength+2*v.originality),0)/((votes.length||1)*4)
  return {sz, avg, keeps:votes.filter(v=>v.verdict==='keep').length, votes}
}))
const best = oceny.filter(o=>o.keeps>=2).sort((a,b)=>b.avg-a.avg)[0] || oceny.sort((a,b)=>b.avg-a.avg)[0]
const szkielet = best.sz
log(`Wybrana struktura: ${szkielet.structureName} (${szkielet.chapters.length} rozdziałów)`)

// --- FAZA 3: Rozdzialy (rownolegle, z kontekstem sasiadow) ---
phase('Rozdzialy')
const mapaObietnic = szkielet.chapters.map(c=>`R${c.n}: ${c.promise}`).join('\n')
const rozdzialy = (await parallel(szkielet.chapters.map((c)=>()=>
  agent(`${ROLE}\n\nFundament:\n${JSON.stringify(fundament)}\n\nPełna mapa obietnic rozdziałów (dla ciągłości):\n${mapaObietnic}\n\nRozpisz SZCZEGÓŁOWO rozdział ${c.n} („${c.title}”, obietnica: ${c.promise}, rola: ${c.role}). Podaj: n, title, promise (dopracowana), beats (3-5 kluczowych punktów), hook (haczyk otwierający rozdział), twist (zwrot akcji na końcu), emotion (przejście emocjonalne, np. „nadzieja → strata”), value ("+" lub "-" — czy rozdział kończy się na plusie czy minusie dla bohatera).\n${FORM
    ? 'subwersja: jak ten rozdział łamie oczekiwany schemat rozwoju argumentu (zamiast spodziewanego wniosku — kontrintuicja, odwrócenie założenia czytelnika). kotwica: jeden konkretny, zapamiętywalny przykład/obraz/zdanie, które utrwali tezę rozdziału.'
    : 'subwersja: jeśli centralny beat tego rozdziału jest standardowy dla gatunku, ZAPROJEKTUJ strukturalne zaskoczenie — odmów oczekiwanej wypłaty, odwróć kto działa, albo przenieś ciężar sceny gdzie indziej (świetnie napisany standardowy beat i tak zatrzymuje oryginalność). Jeśli beat jest z natury nieoczywisty — napisz „beat oryginalny" i uzasadnij jednym zdaniem. kotwica: zamiast mgły („czytelnik czuje niepokój") podaj JEDEN konkretny obraz/moment, który czytelnik zapamięta (np. „okulary wciąż w torebce zmarłej"); zaznacz, jeśli oczekiwana emocja jest tu celowo odwrócona.'}\nBez wypełniaczy.`,
    {label:`rozdzial:${c.n}`,phase:'Rozdzialy',schema:CHAPTER})))).filter(Boolean).sort((a,b)=>a.n-b.n)

// --- FAZA 4: Ciecie wypelniaczy ---
phase('Ciecie wypelniaczy')
const krytyka = (await parallel(rozdzialy.map((c)=>()=>
  agent(`${ROLE}\n\nCały konspekt (obietnice + emocje):\n${JSON.stringify(rozdzialy.map(x=>({n:x.n,promise:x.promise,emotion:x.emotion,value:x.value,hook:x.hook,twist:x.twist})))}\n\nOceń KRYTYCZNIE rozdział ${c.n}:\n${JSON.stringify(c)}\n\nCzy posuwa łuk i fabułę? Czy ma realny haczyk i zwrot? Czy to nie wypełniacz?${FORM ? '' : ' Czy centralny beat jest przewidywalny (czytelnik gatunku zgadnie wypłatę z góry)? Czy rozdział faktycznie subwertuje schemat, czy tylko „kompetentnie" odgrywa standard?'} Daj: n, filler (bool), hasHook, hasTwist, advancesArc, maSubwersje (bool — czy subwersja jest realna, nie pozorna), przewidywalny (bool), issues, fix (jak naprawić albo z czym połączyć).`,
    {label:`krytyk:${c.n}`,phase:'Ciecie wypelniaczy',schema:CRIT})))).filter(Boolean)

const doNaprawy = krytyka.filter(k=>k.filler || !k.hasHook || !k.hasTwist || !k.advancesArc || (!FORM && k.przewidywalny && !k.maSubwersje))
let finalneRozdzialy = rozdzialy
if (doNaprawy.length) {
  const rewizja = await agent(
    `${ROLE}\n\nKonspekt:\n${JSON.stringify(rozdzialy)}\n\nUwagi krytyków (rozdziały do poprawy/cięcia):\n${JSON.stringify(doNaprawy)}\n\nPopraw konspekt: wytnij lub połącz wypełniacze, dodaj brakujące haczyki/zwroty, wyrównaj łuk emocjonalny${FORM ? '' : ' oraz dodaj subwersje tam, gdzie beat był przewidywalny'}. Zwróć finalną, spójną listę rozdziałów (każdy: n, title, promise, beats, hook, twist, emotion, value, subwersja, kotwica). Przenumeruj po cięciach.`,
    {label:'rewizja-rozdzialow',phase:'Ciecie wypelniaczy',
     schema:{ type:'object', required:['chapters'], properties:{ chapters:{type:'array',items:CHAPTER} } }})
  if (rewizja && rewizja.chapters) finalneRozdzialy = rewizja.chapters.sort((a,b)=>a.n-b.n)
}

// --- FAZA 5: Redakcja PL ---
phase('Redakcja PL')
const REDAKCJA = `Jesteś redaktorem języka polskiego. Przepisz przekazany konspekt na poprawną, naturalną polszczyznę. Usuń anglicyzmy i kalki (plot twist → zwrot akcji, cliffhanger → urwanie akcji, foreshadowing → zapowiadanie, stakes → stawka), usuń AI-slop (nadęcia, triady, nadmiar myślników), krótkie konkretne zdania, cudzysłowy „ ”. Zachowaj strukturę pól i sens.`

const [redFund, redRozdz] = await parallel([
  ()=>agent(`${REDAKCJA}\n\nFundament:\n${JSON.stringify(fundament)}`,{label:'red:fundament',phase:'Redakcja PL',schema:FUND}),
  ()=>agent(`${REDAKCJA}\n\nRozdziały:\n${JSON.stringify(finalneRozdzialy)}`,{label:'red:rozdzialy',phase:'Redakcja PL',
       schema:{ type:'object', required:['chapters'], properties:{ chapters:{type:'array',items:CHAPTER} } }}),
])

return {
  fundament: redFund || fundament,
  structureName: szkielet.structureName,
  chapters: (redRozdz && redRozdz.chapters) ? redRozdz.chapters.sort((a,b)=>a.n-b.n) : finalneRozdzialy,
  cut: doNaprawy.filter(k=>k.filler).map(k=>({ n:k.n, powod:k.issues })),
}
```

## Po powrocie roju agentów (główna sesja)

1. **Humanizer** — `/humanizer:humanizer` na całej prozie konspektu.
2. **Budowa dwóch plików** (`.book-forge/konspekt.md` + `konspekt-<slug>.html`) i walidacja — patrz `build-and-verify.md`.

## Skalowanie i plan awaryjny

- Krótsza forma (np. 8–10 rozdziałów) → zmniejsz `N` i liczbę struktur w panelu.
- Brak narzędzia Workflow → odtwórz fazy równoległymi agentami `Task` (ta sama logika: fundament → panel struktur → rozdziały → krytyka → redakcja).
