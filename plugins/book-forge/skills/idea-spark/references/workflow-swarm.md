# Skrypt lekkiego roju (Workflow) — idea-spark

Skopiuj ten skrypt do narzędzia **Workflow** i podstaw dane wejściowe przez `args`
(pełny brief autora — patrz sekcja parsowania). To **lekki wariant** roju z `market-report`:
**nie ma faz „Analiza rynku" i „Luki", nie ma WebSearch** — pomysły powstają z wiedzy
gatunkowej modelu i z briefu, a nie ze świeżych danych rynkowych. Skrypt działa dla każdego
gatunku — nie wpisuj na sztywno science fiction.

> **Uwaga o `args` (częsta pułapka).** Narzędzie Workflow bywa, że podaje `args` do skryptu
> jako **string JSON**, nie jako gotowy obiekt — wtedy `args.genre` zwróci `undefined`, a puste
> pole wpłynie do promptu każdego agenta (cały rój zwróci „gatunek: undefined” i odmówi pracy).
> Skrypt poniżej parsuje `args` odpornie i **przerywa z błędem**, gdy brakuje gatunku lub
> czytelnika — to celowa bramka wejścia (zasada „fail loud”).

Zasady wbudowane w prompty:
- **brief autora** (`subgenre, conventions, protagonist, protAge, protType, form, format, tone, spice, taboo`)
  wstrzyknięty do `ROLE`/`BRIEF` jako twarde wymagania; przy „dowolny/zróżnicuj" rój nie narzuca persony,
- **warstwa adaptacyjna**: `subgenre` zawęża pomysły do nurtu; `conventions` to obietnice
  gatunkowe, które 5 pomysłów MUSI dowieźć; `form` obsługuje non-fiction (wtedy machineria
  persony bohatera nie działa),
- **anty-monokultura**: twarde guardy różnorodności w syntezie pomysłów (≥3 osie, ≤2 ten sam
  profil) i audytor różnorodności przed oceną,
- rola: starszy redaktor do spraw zakupów z 20-letnim doświadczeniem,
- **bez WebSearch i bez agent-browser**: oceny i pomysły opierają się na wiedzy o gatunku
  i rzemiośle, nie na świeżych danych rynkowych (to świadomy kompromis „light" — zaznacz to autorowi),
- ostatni etap to **redakcja na poprawną, naturalną polszczyznę** (bez anglicyzmów i AI-slopu)
  — patrz `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`,
- proza wraca już po polsku, w polach zgodnych z kształtem `DATA` (patrz `build-and-verify.md`).

```javascript
export const meta = {
  name: 'book-forge-idea-spark',
  description: 'Lekki roj agentów: 5 pomysłów na książkę z kwestionariusza, ocena bez WebSearch, werdykt, redakcja PL',
  phases: [
    { title: 'Pomysly' }, { title: 'Ocena' }, { title: 'Werdykt' }, { title: 'Redakcja PL' },
  ],
}

// Workflow potrafi podać `args` jako string JSON, nie jako obiekt — parsuj odpornie, inaczej args.genre === undefined wpłynie do KAŻDEGO promptu
let A
try { A = typeof args === 'string' ? JSON.parse(args) : (args || {}) }
catch (e) { throw new Error('args podane jako string, ale to nie poprawny JSON ('+e.message+'). Przekaż obiekt {genre, reader} albo poprawny JSON.') }
if (!A.genre || !A.reader) throw new Error('Brak gatunku lub czytelnika w args — przerwij, nie uruchamiaj roju z pustym wejściem (gatunek="'+A.genre+'", czytelnik="'+A.reader+'").')
const G = A.genre               // gatunek/pasja, np. "kryminał skandynawski"
const R = A.reader              // docelowy czytelnik (tytuły/serie kotwiczne)
const Y = A.year || '2026'      // rok danych
const M = A.market || 'rynek polski i anglojęzyczny'
// Brief autora (Krok 1). Defaulty „bez preferencji" — NIE są wymagane (tylko genre/reader są twardą bramką).
const PROT  = A.protagonist || 'dowolny'   // 'kobieta' | 'mezczyzna' | 'zroznicuj' | 'dowolny'
const PAGE  = A.protAge || ''              // np. '30-45' lub '' (bez preferencji)
const FORMAT= A.format || 'pojedyncza'     // 'pojedyncza' | 'trylogia' | 'seria' | 'doradz'
const TONE  = A.tone || 'dowolny'          // 'mroczny' | 'wywazony' | 'lekki' | 'dowolny'
const SPICE = A.spice || 'dobierz'         // 'lagodny' | 'umiarkowany' | 'explicit' | 'dobierz'
const TABOO = Array.isArray(A.taboo) ? A.taboo : []   // lista no-go
// Warstwa adaptacyjna (Wywołanie 2 kwestionariusza) — różnicuje profil między gatunkami
const SUBG  = A.subgenre || ''            // podgatunek/nurt; '' = bez preferencji
const CONV  = Array.isArray(A.conventions) ? A.conventions : []  // konwencje/obietnice gatunkowe
const FORM  = A.form || ''                // non-fiction: 'poradnik'|'reportaz'|'esej'|'pamietnik'; '' = fikcja
const PTYPE = A.protType || ''            // opcjonalny typ/rola bohatera, np. 'była śledcza'

// Linia persony: dla non-fiction (FORM) machineria bohatera nie obowiązuje; inaczej konkret = twarde wymaganie, 'dowolny'/'zroznicuj' = nie narzucaj (lek na monokulturę)
const PERSONA = FORM
  ? `- Forma (non-fiction): ${FORM} — dobierz pomysły do tej formy; machineria różnorodności bohatera NIE dotyczy.`
  : `- Bohater: ${PROT === 'dowolny' ? 'profil dobierasz pod pomysł'
      : PROT === 'zroznicuj' ? 'NIE narzucaj jednego profilu — w 5 pomysłach protagoniści MUSZĄ się różnić wiekiem/płcią/typem'
      : `protagonista to ${PROT}${PAGE ? `, wiek ${PAGE}` : ''}${PTYPE ? `, typ: ${PTYPE}` : ''} — trzymaj się tego we WSZYSTKICH pomysłach`}.`

const BRIEF = `
BRIEF AUTORA (twarde wymagania — nadrzędne nad domysłami):
${PERSONA}
- Format: ${FORMAT} (przy ocenie: ${FORMAT === 'pojedyncza' ? 'oceniaj samodzielny, domknięty łuk; NIE premiuj potencjału serii' : 'uwzględnij potencjał serii i zasiewy międzytomowe'}).
- Ton: ${TONE === 'dowolny' ? 'dobierz pod niszę' : `utrzymaj ton: ${TONE}`}.
- Intensywność (spice/przemoc/groza wg gatunku): ${SPICE === 'dobierz' ? 'typowa dla niszy' : SPICE}.
${CONV.length ? `- Konwencje/obietnice gatunkowe, które pomysły MUSZĄ dowieźć: ${CONV.join(', ')}.` : ''}
${TABOO.length ? `- TABU (NIGDY nie proponuj tych tematów): ${TABOO.join(', ')}.` : ''}`

const ROLE = `Jesteś starszym redaktorem do spraw zakupów z 20-letnim doświadczeniem w wyłapywaniu bestsellerów. Gatunek: ${G}${SUBG ? `, podgatunek/nurt: ${SUBG} (trzymaj się tego nurtu)` : ''}. Docelowy czytelnik: ${R}. Rynek: ${M}. BLOKADA GATUNKU: pracujesz WYŁĄCZNIE w obrębie gatunku ${G}${SUBG ? ` (a konkretnie nurtu ${SUBG})` : ''} i celujesz w czytelnika ${R}. Każdy pomysł MUSI należeć do tego gatunku. NIE używaj WebSearch ani CLI agent-browser — to lekki tryb: pracuj z własnej, aktualnej wiedzy o gatunku, jego konwencjach i czytelniku (${Y}). Nie zmyślaj konkretnych liczb sprzedaży ani cytatów ze źródeł, których nie znasz na pewno; opieraj się na rozpoznaniu rzemieślniczym. Pisz po polsku.${BRIEF}`

// --- schematy ---
const POMYSLY = { type:'object', required:['ideas'], properties:{ ideas:{type:'array',items:{
  type:'object',required:['t','en','log','op','hook','comps','protagonista'],properties:{
    t:{type:'string'},en:{type:'string'},log:{type:'string'},op:{type:'string'},
    hook:{type:'string'},comps:{type:'array',items:{type:'string'}},
    protagonista:{type:'string'}}}} } }   // profil bohatera, np. "kobieta, ~40, była śledcza" — niesie decyzję dalej (outline/book-bible)
const OCENA = { type:'object', required:['score','rationale'], properties:{
  score:{type:'number'},rationale:{type:'string'},strengths:{type:'array',items:{type:'string'}},risks:{type:'array',items:{type:'string'}} } }
const WERDYKT = { type:'object', required:['winnerTitle','rationale','warning','whyNow','nextSteps','runnerTitle','runnerWhy'], properties:{
  winnerTitle:{type:'string'},rationale:{type:'string'},warning:{type:'string'},whyNow:{type:'string'},
  positioning:{type:'string'},nextSteps:{type:'array',items:{type:'string'}},
  runnerTitle:{type:'string'},runnerWhy:{type:'string'} } }

// --- FAZA 1: pomysly ---
phase('Pomysly')
const KATY = [
  'Pomysł w duchu czołowego tytułu kotwicznego gatunku, mocno trzymający brief.',
  'Pomysł „jeden bohater vs świat”, mocno trzymający brief.',
  'Pomysł z głęboką budową świata, mocno trzymający brief.',
  'Odważne skrzyżowanie gatunkowe wewnątrz briefu.',
  'Pomysł oparty na nośnym, aktualnym koncepcie.',
  'Pomysł z niedoreprezentowaną perspektywą kulturową.',
  'Pomysł maksymalnie „wiralowy” z mocnym haczykiem.',
  'Ciemny koń — śmiały, nieoczywisty pomysł.',
]
const propozycje = (await parallel(KATY.map((a,i)=>()=>
  agent(`${ROLE}\n\nZadanie: ${a}\n\nTrzymaj się briefu (gatunek ${G}${SUBG?`, nurt ${SUBG}`:''}, czytelnik ${R}${CONV.length?`, konwencje: ${CONV.join(', ')}`:''}). Zaproponuj 1-2 pomysły. Dla każdego: t (POLSKI roboczy tytuł), en (oryginalny tytuł roboczy po angielsku), log (logline 1 zdanie po polsku), op (streszczenie 3-4 zdania po polsku), hook (haczyk sprzedażowy po polsku, może mieć <b>), comps (3-4 orientacyjne tytuły porównawcze z gatunku — z Twojej wiedzy, nie weryfikuj w sieci), protagonista (zwięzły profil bohatera: płeć, wiek, typ — np. „mężczyzna, ~35, były żołnierz"; zgodny z BRIEF AUTORA powyżej).`,
    {label:`pomysl:${i+1}`,phase:'Pomysly',schema:POMYSLY})))).filter(Boolean).flatMap(r=>r.ideas)

// Operacyjna definicja „zróżnicowania" — inaczej rój daje 5 wariantów jednego pomysłu
const DYWERSYFIKACJA = PROT === 'zroznicuj'
  ? 'Autor zażądał RÓŻNYCH bohaterów — to wymóg twardy: 5 pomysłów MUSI mieć wyraźnie różne profile protagonisty (wiek/płeć/typ).'
  : (PROT !== 'dowolny'
      ? `Profil bohatera jest USTALONY przez autora (${PROT}${PAGE?', '+PAGE:''}) — wszystkie pomysły go trzymają; różnicuj POZOSTAŁE osie (setting, ton, koncept, podgatunek).`
      : 'Nie więcej niż 2 z 5 pomysłów mogą dzielić ten sam profil protagonisty; reszta musi się różnić.')
const finalisci = await agent(
  `${ROLE}\n\nPomysły zespołu:\n${JSON.stringify(propozycje)}\n\nWybierz 5 najsilniejszych. Dopracuj pola (t, en, log, op, hook, comps, protagonista). Pomysły mają być wyraziste i sprzedawalne.\n\nGUARD RÓŻNORODNOŚCI: 5 pomysłów MUSI różnić się na co najmniej 3 osiach (profil bohatera, setting, ton, podgatunek, format). ${DYWERSYFIKACJA}`,
  {label:'synteza:5pomyslow',phase:'Pomysly',schema:POMYSLY})
let ideas = finalisci.ideas.slice(0,5)

// Audyt różnorodności (zanim ruszy ocena). Łapie monokulturę profilu bohatera. Pomijany, gdy autor JAWNIE ustalił profil.
if (PROT === 'dowolny' || PROT === 'zroznicuj') {
  const audyt = await agent(
    `${ROLE}\n\n5 pomysłów (profile bohaterów):\n${JSON.stringify(ideas.map(s=>({t:s.t,protagonista:s.protagonista})))}\n\nSprawdź rozkład profili protagonisty. Monokultura = >60% pomysłów ma ZBLIŻONY profil (ten sam wiek/płeć/typ). Zwróć: monokultura (bool), dominujacy (opis), uwaga (1 zdanie).`,
    {label:'audyt:roznorodnosc',phase:'Pomysly',schema:{type:'object',required:['monokultura','uwaga'],properties:{monokultura:{type:'boolean'},dominujacy:{type:'string'},uwaga:{type:'string'}}}})
  if (audyt && audyt.monokultura) {
    log('Audyt różnorodności: monokultura profili bohatera — przerabiam stawkę')
    const poprawione = await agent(
      `${ROLE}\n\nStawka jest zdominowana przez jeden profil bohatera (${audyt.dominujacy||''}). Przebuduj 5 pomysłów tak, by NIE WIĘCEJ niż 2 dzieliły ten profil — zastąp nadmiarowe duplikaty pomysłami z INNYM profilem protagonisty, trzymając gatunek ${G}. Zachowaj najsilniejsze pomysły, podmień tylko duplikaty. Pola: t, en, log, op, hook, comps, protagonista.\n\nDotychczasowe:\n${JSON.stringify(ideas)}`,
      {label:'synteza:roznorodnosc',phase:'Pomysly',schema:POMYSLY})
    if (poprawione && poprawione.ideas && poprawione.ideas.length) ideas = poprawione.ideas.slice(0,5)
  }
}

// --- FAZA 2: ocena (bez WebSearch) ---
phase('Ocena')
const SEDZIOWIE = [
  {n:'Redaktor prowadzący',l:'Oceń siłę premisy, oryginalność i dopasowanie do briefu (gatunek, konwencje, profil bohatera).'},
  {n:'Marketing',l:'Oceń siłę haczyka i „wiralowy" potencjał konceptu — z wiedzy o gatunku, NIE z badania social mediów.'},
  {n:'Czytelnik docelowy',l:'Oceń, czy KUPIŁBYŚ to i polecił; czy haczyk budzi głód.'},
]
const ocenione = await parallel(ideas.map((idea)=>async()=>{
  const votes=(await parallel(SEDZIOWIE.map((s)=>()=>
    agent(`${ROLE}\n\nWcielasz się w rolę: ${s.n}. ${s.l}\n\nPomysł:\n${JSON.stringify(idea)}\n\nNIE używaj WebSearch ani agent-browser — oceniaj z wiedzy o gatunku i rzemiośle. Oceń też ODRÓŻNIALNOŚĆ od oczywistych klisz gatunku: pomysł, który tylko powiela zgrany schemat, dostaje KARĘ do oceny, nie premię — świeżość ma wartość. Wystaw ocenę 1-10 (może być ułamkowa) z uzasadnieniem, mocnymi stronami i ryzykami.`,
      {label:`ocena:${idea.t.slice(0,16)}`,phase:'Ocena',schema:OCENA})))).filter(Boolean)
  const avg=votes.reduce((s,v)=>s+v.score,0)/(votes.length||1)
  return {...idea, votes, avgScore:Math.round(avg*10)/10}
}))
const scoredIdeas = ocenione.filter(Boolean).sort((a,b)=>b.avgScore-a.avgScore)

// --- FAZA 3: werdykt ---
phase('Werdykt')
const werdykt = await agent(
  `${ROLE}\n\n5 pomysłów z ocenami:\n${JSON.stringify(scoredIdeas.map(s=>({t:s.t,log:s.log,protagonista:s.protagonista,avgScore:s.avgScore,votes:s.votes})))}\n\nWskaż JEDEN pomysł do rozwijania. Podaj: winnerTitle, rationale (dlaczego), warning (uczciwe ostrzeżenie o ryzykach — fail loud; JEŚLI wszystkie 5 pomysłów dzieli ten sam profil bohatera, ZGŁOŚ to jako ryzyko monokultury i wskaż, czego w stawce zabrakło; przypomnij też, że to lekki tryb bez weryfikacji rynkowej — wybór warto potwierdzić pełnym market-report), whyNow (dlaczego teraz), positioning (jak pozycjonować), nextSteps (kroki dla autora), runnerTitle (tytuł wicemistrza), runnerWhy (dlaczego wicemistrz).`,
  {label:'werdykt',phase:'Werdykt',schema:WERDYKT})

// --- FAZA 4: redakcja na poprawną, naturalną polszczyznę ---
phase('Redakcja PL')
const REDAKCJA = `Jesteś redaktorem języka polskiego w wydawnictwie. Przepisz CAŁY przekazany tekst na poprawną, naturalną polszczyznę. ŻELAZNE zasady: (1) usuń anglicyzmy i kalki — tłumacz żargon (np. competence porn → frajda z patrzenia, jak bohater kompetentnie rozwiązuje problemy; hook → haczyk; found family → rodzina z wyboru; worldbuilding → świat przedstawiony; plot armor → fabularny immunitet); (2) usuń AI-slop (nadęcia „stanowi/podkreśla”, triady, nadmiar myślników, puste konkluzje); (3) krótkie, konkretne zdania, zmienny rytm; (4) zachowaj sens, liczby i źródła; (5) cudzysłowy „ ”, przecinki dziesiętne. Zwróć tekst w tej samej strukturze pól.`

const [redIdeasProse, redWerdykt] = await parallel([
  ()=>agent(`${REDAKCJA}\n\nZredaguj TYLKO pola tekstowe tych 5 pomysłów (NIE oceniaj, NIE dodawaj głosów ani ocen). Zwróć obiekt {ideas:[{t,en,log,op,hook,comps,protagonista}, ...]} z DOKŁADNIE 5 pozycjami w tej SAMEJ kolejności co wejście. Nie zmieniaj kolejności ani liczby pomysłów.\n${JSON.stringify({ideas:scoredIdeas.map(s=>({t:s.t,en:s.en,log:s.log,op:s.op,hook:s.hook,comps:s.comps,protagonista:s.protagonista}))})}`,{label:'red:pomysly',phase:'Redakcja PL',schema:POMYSLY}),
  ()=>agent(`${REDAKCJA}\n\nDane (werdykt):\n${JSON.stringify(werdykt)}`,{label:'red:werdykt',phase:'Redakcja PL',schema:WERDYKT}),
])

const mergedIdeas = scoredIdeas.map((s,i)=>{
  const r=(redIdeasProse && redIdeasProse.ideas && redIdeasProse.ideas[i]) || {}
  return {...s, t:r.t||s.t, en:r.en||s.en, log:r.log||s.log, op:r.op||s.op, hook:r.hook||s.hook, comps:(Array.isArray(r.comps)&&r.comps.length)?r.comps:s.comps, protagonista:r.protagonista||s.protagonista}
})

return {
  ideas: mergedIdeas,
  winner: redWerdykt || werdykt,
  // Brief autora — dane sterujące (NIE redagowane), dziedziczone przez outline/book-bible przez DATA.brief
  brief: { subgenre: SUBG, conventions: CONV, protagonist: PROT, protAge: PAGE, protType: PTYPE, form: FORM, format: FORMAT, tone: TONE, spice: SPICE, taboo: TABOO, market: M },
}
```

## Po powrocie roju agentów (główna sesja)

1. **Humanizer** — wywołaj `/humanizer:humanizer` i nanieś poprawki na prozę (patrz
   `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`). Rój już redagował, ale humanizer to
   obowiązkowy, drugi przebieg.
2. **Mapowanie do `DATA`** i budowa HTML — `build-and-verify.md`.

## Skalowanie i wariant zapasowy

- Niszowy lub lokalny gatunek → zmniejsz liczby (np. 6 kategorii, 5 pomysłów).
- Brak narzędzia Workflow → odtwórz te same etapy równoległymi agentami `Task` (ta sama
  logika: generuj → oceń → synteza → redakcja), wolniej i w kontekście.
- Potrzebujesz twardych danych rynkowych (10 bestsellerów, 3 luki, ocena z WebSearch)?
  To pełny `market-report` (etap 1), nie ten lekki wariant.
