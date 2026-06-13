# Skrypt roju (Workflow) — idea-spark (autorski trzon + 5 wariantów fabuły)

Skopiuj ten skrypt do narzędzia **Workflow** i podstaw dane wejściowe przez `args`
(pełny brief autora + szczegółowy trzon — patrz sekcja parsowania). To **autorski wariant**
etapu 1: **nie ma faz „Analiza rynku" i „Luki", nie ma WebSearch** — ale w odróżnieniu od
samego briefu, autor podaje tu szczegółowy **TRZON** powieści (kierunek/temat, bohaterowie,
świat). Trzon jest **STAŁY** we wszystkich 5 pomysłach; rój różnicuje **tylko fabułę** —
generuje 5 różnych zalążków fabuły w ramach trzonu, ocenia je i wybiera zwycięzcę. Pomysły
powstają z wiedzy gatunkowej modelu i z trzonu, nie ze świeżych danych rynkowych. Skrypt
działa dla każdego gatunku — nie wpisuj na sztywno science fiction.

> **Uwaga o `args` (częsta pułapka).** Narzędzie Workflow bywa, że podaje `args` do skryptu
> jako **string JSON**, nie jako gotowy obiekt — wtedy `args.genre` zwróci `undefined`, a puste
> pole wpłynie do promptu każdego agenta (cały rój zwróci „gatunek: undefined” i odmówi pracy).
> Skrypt poniżej parsuje `args` odpornie i **przerywa z błędem**, gdy brakuje gatunku lub
> czytelnika — to celowa bramka wejścia (zasada „fail loud”).

Zasady wbudowane w prompty:
- **brief autora** (`subgenre, conventions, protagonist, protAge, protType, form, format, tone, spice, taboo`)
  wstrzyknięty do `ROLE`/`BRIEF` jako twarde wymagania; przy „dowolny/zróżnicuj" rój nie narzuca persony,
- **TRZON autora** (`dramaticQ, theme, emotion, antagonist, relation, arc, setting, realism, mood, scale`)
  wstrzyknięty do `ROLE`/`TRZON` jako **stała wspólna dla wszystkich 5 fabuł** — rój NIE różnicuje
  tych osi, różnicuje TYLKO fabułę; puste pola (`''`) rój dobiera sam,
- **ramy fabuły** (`conflictType, ending, pace, seed`) to ograniczenia, w których rój generuje
  RÓŻNE fabuły — wartości ustalone obowiązują wszystkie pomysły, ale droga do nich jest różna,
- **warstwa adaptacyjna**: `subgenre` zawęża pomysły do nurtu; `conventions` to obietnice
  gatunkowe, które 5 fabuł MUSI dowieźć; `form` obsługuje non-fiction (wtedy machineria
  persony bohatera nie działa),
- **anty-monokultura (dwugałęziowa)**: gdy autor NIE ustalił bohatera — audyt różnorodności
  profilu bohatera (≥3 osie, ≤2 ten sam profil); gdy bohater jest USTALONY (trzon) — audyt
  różnorodności **podejść fabularnych** (5 zalążków nie może dzielić jednego szkieletu zdarzeń),
- rola: starszy redaktor do spraw zakupów z 20-letnim doświadczeniem,
- **bez WebSearch i bez agent-browser**: oceny i pomysły opierają się na wiedzy o gatunku
  i rzemiośle, nie na świeżych danych rynkowych (to świadomy kompromis „light" — zaznacz to autorowi),
- ostatni etap to **redakcja na poprawną, naturalną polszczyznę** (bez anglicyzmów i AI-slopu)
  — patrz `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`,
- proza wraca już po polsku, w polach zgodnych z kształtem `DATA` (patrz `build-and-verify.md`).

```javascript
export const meta = {
  name: 'book-forge-idea-spark',
  description: 'Roj agentów: autorski trzon + 5 wariantów fabuły w jego ramach, ocena bez WebSearch, werdykt, redakcja PL',
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

// TRZON autora (Wywołania 3-5 kwestionariusza) — STAŁY we wszystkich 5 pomysłach; '' = rój dobiera. NIE trafia do brief/pomysl.json — wsiąka w treść op/silnik/protagonista.
const DRAMATICQ = A.dramaticQ || ''       // centralne pytanie dramatyczne
const THEME     = A.theme || ''           // przesłanie/teza
const EMOTION   = A.emotion || ''         // emocja docelowa
const INTENT    = A.intent || 'wywaz'     // 'rynek'|'przeslanie'|'rozrywka'|'wywaz' — steruje wagą sędziów
const ANTAG     = A.antagonist || ''      // antagonista/siła przeciwna: osoba|system|wewnetrzny|natura/swiat lub opis
const RELATION  = A.relation || ''        // kluczowa relacja (emocjonalne serce)
const ARC       = A.arc || ''             // łuk przemiany: 'wzrost'|'upadek'|'plaski'
const SETTING   = A.setting || ''         // świat: miejsce i czas
const REALISM   = A.realism || ''         // 'realistyczny'|'jeden-element'|'pelny'
const MOOD      = A.mood || ''            // atmosfera/nastrój świata
const SCALE     = A.scale || ''           // 'kameralna'|'lokalna'|'wielka'
// Ramy fabuły (Wywołanie 6) — ograniczenia, w których rój generuje RÓŻNE fabuły
const CONFLICT  = A.conflictType || ''    // typ głównego konfliktu
const ENDING    = A.ending || ''          // 'szczesliwe'|'gorzko-slodkie'|'otwarte'
const PACE      = A.pace || ''            // 'wartkie'|'wywazone'|'powolne'
const SEED      = A.seed || ''            // opcjonalny punkt wyjścia (zaczyn) — ziarno, nie scenariusz

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

// TRZON autora — STAŁA wspólna dla wszystkich 5 fabuł (kierunek/temat, bohaterowie, świat). Puste pole = miękki fallback (dobierz JEDEN wariant i trzymaj go wszędzie). RAMY FABUŁY = ograniczenia, w których rój generuje RÓŻNE fabuły.
const dv = (x, d) => x ? x : d
const TRZON = `

TRZON WIZJI AUTORA (STAŁY we wszystkich 5 pomysłach — NIE różnicuj tych osi między pomysłami; zmienia się TYLKO konkretna fabuła):
- Kierunek/temat: centralne pytanie dramatyczne: ${dv(DRAMATICQ, 'dobierz pod gatunek i nurt')}; przesłanie/teza: ${dv(THEME, 'dobierz')}; emocja docelowa: ${dv(EMOTION, 'dobierz')}.
- Bohaterowie: antagonista/siła przeciwna: ${dv(ANTAG, 'dobierz')}; kluczowa relacja (emocjonalne serce): ${dv(RELATION, 'dobierz')}; łuk przemiany protagonisty: ${dv(ARC, 'dobierz')}.
- Świat: ${dv(SETTING, 'dobierz miejsce i czas')}; realizm: ${dv(REALISM, 'dobierz')}; atmosfera: ${dv(MOOD, 'dobierz')}; skala: ${dv(SCALE, 'dobierz')}.
Gdy pole jest ustalone — każdy pomysł MUSI je trzymać; gdy puste — dobierz JEDEN wariant i trzymaj go we wszystkich 5. NIE rozwijaj świata ani postaci do biblii — to robi book-bible (etap 3); tu wystarczy zarys niesiony przez op/silnik/protagonista.

RAMY FABUŁY (ograniczenia, w których generujesz RÓŻNE fabuły — wartość ustalona obowiązuje wszystkie pomysły, ale droga do niej jest różna):
- typ głównego konfliktu: ${dv(CONFLICT, 'dobierz, ale różnicuj jego rozegranie między pomysłami')}; typ zakończenia: ${dv(ENDING, 'dobierz')}; tempo: ${dv(PACE, 'dobierz')}.
- punkt wyjścia (zaczyn): ${SEED ? `${SEED} — możesz go wpleść jako ziarno, NIE jako gotowy scenariusz` : 'brak — wymyśl świeże wydarzenie inicjujące dla każdej z 5 fabuł'}.`

const ROLE = `Jesteś starszym redaktorem do spraw zakupów z 20-letnim doświadczeniem w wyłapywaniu bestsellerów. Gatunek: ${G}${SUBG ? `, podgatunek/nurt: ${SUBG} (trzymaj się tego nurtu)` : ''}. Docelowy czytelnik: ${R}. Rynek: ${M}. BLOKADA GATUNKU: pracujesz WYŁĄCZNIE w obrębie gatunku ${G}${SUBG ? ` (a konkretnie nurtu ${SUBG})` : ''} i celujesz w czytelnika ${R}. Każdy pomysł MUSI należeć do tego gatunku. NIE używaj WebSearch ani CLI agent-browser — to lekki tryb: pracuj z własnej, aktualnej wiedzy o gatunku, jego konwencjach i czytelniku (${Y}). Nie zmyślaj konkretnych liczb sprzedaży ani cytatów ze źródeł, których nie znasz na pewno; opieraj się na rozpoznaniu rzemieślniczym. Pisz po polsku.${BRIEF}${TRZON}`

// --- schematy ---
const POMYSLY = { type:'object', required:['ideas'], properties:{ ideas:{type:'array',items:{
  type:'object',required:['t','en','log','silnik','op','hook','comps','protagonista'],properties:{
    t:{type:'string'},en:{type:'string'},log:{type:'string'},
    silnik:{type:'string'},                 // silnik premisy — strukturalna sprzeczność/pytanie dramatyczne, które samo napędza konflikt
    op:{type:'string'},
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
// KATY = typy ZALĄŻKA FABUŁY dla TEGO SAMEGO trzonu (różne szkielety zdarzeń, nie różne pomysły). Trzon (świat/bohater/pytanie dramatyczne) jest wspólny — zmienia się tylko sposób rozegrania.
const KATY = [
  'Fabuła startująca od nagłego wydarzenia, które rozbija status quo bohatera (incydent inicjujący z zewnątrz).',
  'Fabuła, w której bohater sam podejmuje decyzję uruchamiającą lawinę (sprawczy wybór, nie wypadek).',
  'Fabuła narastającego śledztwa/odkrywania prawdy — napięcie z tego, co bohater stopniowo poznaje.',
  'Fabuła presji czasu lub pościgu — odliczanie, które z definicji samo się zacieśnia.',
  'Fabuła intrygi i gry sił — konflikt rozgrywa się przez sojusze, zdrady i ukryte cele.',
  'Fabuła podróży/przemiany przez kolejne progi — bohater zmienia się wraz z przebytą drogą.',
  'Fabuła oblężenia/zamknięcia — zagrożenie napiera z zewnątrz na ograniczoną przestrzeń lub grupę.',
  'Ciemny koń — nieoczywista struktura fabuły, której konkurencja nie odważyłaby się rozegrać.',
]
// Soczewki twórcze — rotowane NA AGENTACH obok KATY; operują na poziomie ZDARZEŃ FABUŁY, nie trzonu (świat/bohater/pytanie dramatyczne pozostają stałe)
const SOCZEWKI = [
  'CO JEŚLI: zmień jedno założenie sytuacji startowej fabuły i wyciągnij konsekwencje — bez ruszania trzonu (świata/bohatera).',
  'ZDERZENIE DOMEN: wstrzyknij mechanizm z obcej dziedziny (nauka, zawód, rytuał, historia) jako silnik wydarzeń fabuły.',
  'INWERSJA: odwróć układ sił w fabule (kto poluje, kto ucieka, kto wie, kto płaci) przy stałym antagoniście-typie.',
  'ESKALACJA: sytuacja startowa, która z definicji sama się pogarsza, krok po kroku.',
  'KOLIZJA Z MOMENTEM: rozegraj fabułę przez dzisiejszy lęk lub napięcie kulturowe.',
  'IRONIA WBUDOWANA: bohater jest sprawcą własnego problemu (jak „idealna żona, która zaplanowała własne morderstwo”).',
  'PYTANIE NAPIĘCIA: zbuduj fabułę wokół jednego pytania „co dalej”, na które czytelnik MUSI poznać odpowiedź (lokalne wobec pytania dramatycznego trzonu).',
  'STAWKA OSOBISTA: sprowadź zagrożenie do jednej konkretnej osoby do uratowania albo zniszczenia.',
]
// Reguła silnika premisy — dla non-fiction (FORM) reinterpretowana, nie wyłączona
const SILNIK_REGULA = FORM
  ? 'centralne napięcie lub pytanie, które trzyma czytelnika (sprzeczność w temacie, mit do obalenia) — NIE wymuszaj fabularnego konfliktu'
  : 'strukturalna sprzeczność lub ironia, która SAMA generuje konflikt — napięcie wpisane w sytuację startową, nie doklejony z zewnątrz złoczyńca'
const propozycje = (await parallel(KATY.map((a,i)=>()=>
  agent(`${ROLE}\n\nTRZON jest STAŁY (podany wyżej w TRZON WIZJI) — NIE zmieniaj świata, bohatera-typu, antagonisty, relacji, łuku ani pytania dramatycznego. Wymyśl KONKRETNĄ fabułę realizującą ten trzon.\nTyp zalążka fabuły (framing): ${a}\nSOCZEWKA TWÓRCZA (narzędzie myślowe na poziomie zdarzeń, nie ozdoba): ${SOCZEWKI[i % SOCZEWKI.length]}\n\nTrzymaj się briefu i trzonu (gatunek ${G}${SUBG?`, nurt ${SUBG}`:''}, czytelnik ${R}${CONV.length?`, konwencje: ${CONV.join(', ')}`:''}). Każda fabuła MUSI mieć działający SILNIK PREMISY: ${SILNIK_REGULA}; silnik ma wiązać konkretny konflikt fabuły z pytaniem dramatycznym trzonu. Zaproponuj 1-2 fabuły. Dla każdej: t (POLSKI roboczy tytuł), en (oryginalny tytuł roboczy po angielsku), log (logline 1 zdanie po polsku), silnik (1-2 zdania — ${SILNIK_REGULA}), op (streszczenie 3-4 zdania po polsku — OPOWIEDZ TĘ KONKRETNĄ FABUŁĘ: wydarzenie inicjujące, oś napięcia, kulminacja), hook (haczyk sprzedażowy po polsku, może mieć <b>), comps (3-4 orientacyjne tytuły porównawcze z gatunku — z Twojej wiedzy, nie weryfikuj w sieci), protagonista (zwięzły profil bohatera: płeć, wiek, typ — np. „mężczyzna, ~35, były żołnierz"; ZGODNY z trzonem i BRIEF AUTORA, nie wymyślaj nowego, gdy autor go ustalił).`,
    {label:`fabula:${i+1}`,phase:'Pomysly',schema:POMYSLY})))).filter(Boolean).flatMap(r=>r.ideas)

// Czy bohater jest STAŁĄ trzonu? Jeśli tak — różnicujemy FABUŁĘ; jeśli nie (dowolny/zróżnicuj) — pilnujemy też profilu bohatera.
// 'zroznicuj' = autor JAWNIE chce różnych bohaterów, więc nigdy nie traktuj go jako stałego, nawet gdy przypadkiem przyszedł też protType.
const STALY_BOHATER = PROT === 'zroznicuj' ? false : (PROT === 'kobieta' || PROT === 'mezczyzna' || !!PTYPE)
// Operacyjna definicja „zróżnicowania" — w hybrydzie trzon jest stały, więc różnicujemy fabułę; gdy bohater nieustalony, dodatkowo pilnujemy profilu
const DYWERSYFIKACJA = STALY_BOHATER
  ? `Profil bohatera i cały TRZON są USTALONE — wszystkie 5 pomysłów je trzymają (bohater: ${PROT}${PAGE?', '+PAGE:''}${PTYPE?', '+PTYPE:''}). RÓŻNICUJ FABUŁĘ: wydarzenie inicjujące, oś konfliktu, strukturę zdarzeń, charakter kulminacji. To 5 wariantów fabuły JEDNEJ wizji, nie 5 różnych pomysłów.`
  : (PROT === 'zroznicuj'
      ? 'Autor zażądał RÓŻNYCH bohaterów — to wymóg twardy: 5 pomysłów MUSI mieć wyraźnie różne profile protagonisty (wiek/płeć/typ), a do tego różne fabuły.'
      : 'Profil bohatera nie jest ustalony — nie więcej niż 2 z 5 mogą dzielić ten sam profil; różnicuj też fabułę i setting.')
const GUARD = STALY_BOHATER
  ? 'GUARD RÓŻNORODNOŚCI FABUŁY: 5 fabuł MUSI różnić się na co najmniej 3 osiach fabularnych (wydarzenie inicjujące, oś konfliktu, struktura zdarzeń, źródło napięcia, charakter kulminacji). Trzon (świat, bohater, pytanie dramatyczne) pozostaje WSPÓLNY — nie różnicuj go.'
  : 'GUARD RÓŻNORODNOŚCI: 5 pomysłów MUSI różnić się na co najmniej 3 osiach (profil bohatera, setting, ton, podgatunek, fabuła).'
const finalisci = await agent(
  `${ROLE}\n\nFabuły zespołu:\n${JSON.stringify(propozycje)}\n\nWybierz 5 najsilniejszych i PODKRĘĆ każdą. PODKRĘCENIE = wyostrz silnik premisy (mocniejsza sprzeczność wiążąca fabułę z pytaniem dramatycznym trzonu), podnieś stawkę, dodaj jeden nieoczywisty zwrot. ŻELAZNA REGUŁA „WZMACNIAJ, NIE PODMIENIAJ": surowa fabuła musi pozostać rozpoznawalna — wzmacniasz, nie zastępujesz jej inną. NIE zmieniaj TRZONU (świat/bohater/pytanie dramatyczne pozostają wspólne dla wszystkich 5). Dopracuj pola (t, en, log, silnik, op, hook, comps, protagonista). Fabuły mają być wyraziste, świeże i sprzedawalne.\n\n${GUARD} ${DYWERSYFIKACJA}`,
  {label:'synteza:5fabul',phase:'Pomysly',schema:POMYSLY})
let ideas = finalisci.ideas.slice(0,5)

// Audyt różnorodności (zanim ruszy ocena) — dwugałęziowy:
// - bohater NIEUSTALONY → łap monokulturę profilu bohatera (jak dotąd),
// - bohater USTALONY (trzon) → monokultura bohatera jest POŻĄDANA; łap monokulturę PODEJŚĆ FABULARNYCH.
// Non-fiction (FORM): protagonista nie istnieje, więc audyt profilu bohatera jest bezprzedmiotowy — pomiń go (PERSONA już wyłącza machinerię bohatera).
if (!STALY_BOHATER && !FORM) {
  const audyt = await agent(
    `${ROLE}\n\n5 pomysłów (profile bohaterów):\n${JSON.stringify(ideas.map(s=>({t:s.t,protagonista:s.protagonista})))}\n\nSprawdź rozkład profili protagonisty. Monokultura = >60% pomysłów ma ZBLIŻONY profil (ten sam wiek/płeć/typ). Zwróć: monokultura (bool), dominujacy (opis), uwaga (1 zdanie).`,
    {label:'audyt:bohater',phase:'Pomysly',schema:{type:'object',required:['monokultura','uwaga'],properties:{monokultura:{type:'boolean'},dominujacy:{type:'string'},uwaga:{type:'string'}}}})
  if (audyt && audyt.monokultura) {
    log('Audyt różnorodności: monokultura profili bohatera — przerabiam stawkę')
    const poprawione = await agent(
      `${ROLE}\n\nStawka jest zdominowana przez jeden profil bohatera (${audyt.dominujacy||''}). Przebuduj 5 pomysłów tak, by NIE WIĘCEJ niż 2 dzieliły ten profil — zastąp nadmiarowe duplikaty pomysłami z INNYM profilem protagonisty, trzymając gatunek ${G}. Zachowaj najsilniejsze pomysły, podmień tylko duplikaty. Pola: t, en, log, silnik, op, hook, comps, protagonista.\n\nDotychczasowe:\n${JSON.stringify(ideas)}`,
      {label:'synteza:bohater',phase:'Pomysly',schema:POMYSLY})
    if (poprawione && poprawione.ideas && poprawione.ideas.length) ideas = poprawione.ideas.slice(0,5)
  }
} else {
  const audyt = await agent(
    `${ROLE}\n\n5 fabuł (ten sam trzon, różne fabuły):\n${JSON.stringify(ideas.map(s=>({t:s.t,log:s.log,silnik:s.silnik,op:s.op})))}\n\nBohater i trzon są USTALONE i wspólne — to OK i ZAMIERZONE. Sprawdź różnorodność FABUŁ. Monokultura fabularna = >60% fabuł dzieli ten sam szkielet zdarzeń (zbliżone wydarzenie inicjujące, ta sama oś konfliktu, ta sama struktura, podobna kulminacja). Zwróć: monokultura (bool), dominujacy (opis wspólnego szkieletu), uwaga (1 zdanie).`,
    {label:'audyt:fabula',phase:'Pomysly',schema:{type:'object',required:['monokultura','uwaga'],properties:{monokultura:{type:'boolean'},dominujacy:{type:'string'},uwaga:{type:'string'}}}})
  if (audyt && audyt.monokultura) {
    log('Audyt różnorodności: monokultura fabuł (ten sam szkielet) — przerabiam stawkę')
    const poprawione = await agent(
      `${ROLE}\n\nFabuły za bardzo dzielą jeden szkielet zdarzeń (${audyt.dominujacy||''}). Przebuduj nadmiarowe duplikaty NOWĄ fabułą — inne wydarzenie inicjujące, inna oś konfliktu, inna struktura — TRZYMAJĄC TEN SAM TRZON (świat, bohater, pytanie dramatyczne, antagonista-typ). Zachowaj najsilniejsze fabuły, podmień tylko duplikaty. Pola: t, en, log, silnik, op, hook, comps, protagonista.\n\nDotychczasowe:\n${JSON.stringify(ideas)}`,
      {label:'synteza:fabula',phase:'Pomysly',schema:POMYSLY})
    if (poprawione && poprawione.ideas && poprawione.ideas.length) ideas = poprawione.ideas.slice(0,5)
  }
}

// --- FAZA 2: ocena (bez WebSearch) ---
phase('Ocena')
const SEDZIOWIE = [
  {n:'Redaktor prowadzący',l:'Oceń, jak mocno FABUŁA realizuje TRZON: czy faktycznie ROZGRYWA pytanie dramatyczne, czy przesłanie wynika z wydarzeń (a nie jest doklejone), siłę silnika premisy i dopasowanie do briefu.'},
  {n:'Marketing',l:'Oceń siłę haczyka i „wiralowy" potencjał tej fabuły — z wiedzy o gatunku, NIE z badania social mediów.'},
  {n:'Czytelnik docelowy',l:'Oceń, czy KUPIŁBYŚ to i polecił; czy haczyk budzi głód.'},
  {n:'Adwokat innowacji',l:'Oceń ODWAGĘ i świeżość: czy SILNIK wiąże fabułę z trzonem (pytaniem dramatycznym i antagonistą) w nieoczywisty sposób? Tu RYZYKO i nieoczywistość to PREMIA, nie kara — fabuła będąca tylko generycznym wypełnieniem trzonu albo powieleniem zgranego schematu — oceń NIŻEJ.'},
]
const WAGA_INTENT = INTENT === 'rynek' ? 'Intencja autora: RYNEK — siła haczyka i sprzedawalność ważą więcej.'
  : INTENT === 'przeslanie' ? 'Intencja autora: PRZESŁANIE — wierność pytaniu dramatycznemu i tezie waży więcej niż sprzedawalność.'
  : INTENT === 'rozrywka' ? 'Intencja autora: ROZRYWKA — haczyk, tempo i frajda z czytania ważą więcej.'
  : 'Intencja autora: wyważona — równo waż rzemiosło, świeżość i sprzedawalność.'
const ocenione = await parallel(ideas.map((idea)=>async()=>{
  const votes=(await parallel(SEDZIOWIE.map((s)=>()=>
    agent(`${ROLE}\n\nWcielasz się w rolę: ${s.n}. ${s.l}\n${WAGA_INTENT}\n\nFabuła:\n${JSON.stringify(idea)}\n\nNIE używaj WebSearch ani agent-browser — oceniaj z wiedzy o gatunku i rzemiośle. Zwróć szczególną uwagę na pole „silnik" — fabuła bez działającego silnika premisy (płaska sytuacja, konflikt doklejony z zewnątrz) oceń niżej. Oceń też ODRÓŻNIALNOŚĆ od oczywistych klisz gatunku: fabuła, która tylko powiela zgrany schemat, dostaje KARĘ do oceny, nie premię — świeżość ma wartość. Wystaw ocenę 1-10 (może być ułamkowa) z uzasadnieniem, mocnymi stronami i ryzykami.`,
      {label:`ocena:${idea.t.slice(0,16)}`,phase:'Ocena',schema:OCENA})))).filter(Boolean)
  const avg=votes.reduce((s,v)=>s+v.score,0)/(votes.length||1)
  return {...idea, votes, avgScore:Math.round(avg*10)/10}
}))
const scoredIdeas = ocenione.filter(Boolean).sort((a,b)=>b.avgScore-a.avgScore)

// --- FAZA 3: werdykt ---
phase('Werdykt')
const WARN_MONO = STALY_BOHATER
  ? 'JEŚLI 5 fabuł jest do siebie zbyt podobnych (ten sam szkielet zdarzeń), ZGŁOŚ to jako ryzyko monokultury fabularnej i wskaż, jakiego rozegrania w stawce zabrakło'
  : 'JEŚLI wszystkie 5 pomysłów dzieli ten sam profil bohatera, ZGŁOŚ to jako ryzyko monokultury i wskaż, czego w stawce zabrakło'
const werdykt = await agent(
  `${ROLE}\n\n5 fabuł z ocenami (wspólny trzon, różne fabuły):\n${JSON.stringify(scoredIdeas.map(s=>({t:s.t,log:s.log,protagonista:s.protagonista,avgScore:s.avgScore,votes:s.votes})))}\n\nWskaż JEDNĄ fabułę do rozwijania. Podaj: winnerTitle, rationale (dlaczego ta fabuła najlepiej ROZGRYWA trzon autora), warning (uczciwe ostrzeżenie o ryzykach — fail loud; ${WARN_MONO}; przypomnij też, że to lekki tryb bez weryfikacji rynkowej — wybór warto potwierdzić pełnym market-report), whyNow (dlaczego teraz), positioning (jak pozycjonować), nextSteps (kroki dla autora), runnerTitle (tytuł wicemistrza), runnerWhy (dlaczego wicemistrz).`,
  {label:'werdykt',phase:'Werdykt',schema:WERDYKT})

// --- FAZA 4: redakcja na poprawną, naturalną polszczyznę ---
phase('Redakcja PL')
const REDAKCJA = `Jesteś redaktorem języka polskiego w wydawnictwie. Przepisz CAŁY przekazany tekst na poprawną, naturalną polszczyznę. ŻELAZNE zasady: (1) usuń anglicyzmy i kalki — tłumacz żargon (np. competence porn → frajda z patrzenia, jak bohater kompetentnie rozwiązuje problemy; hook → haczyk; found family → rodzina z wyboru; worldbuilding → świat przedstawiony; plot armor → fabularny immunitet); (2) usuń AI-slop (nadęcia „stanowi/podkreśla”, triady, nadmiar myślników, puste konkluzje); (3) krótkie, konkretne zdania, zmienny rytm; (4) zachowaj sens, liczby i źródła; (5) cudzysłowy „ ”, przecinki dziesiętne. Zwróć tekst w tej samej strukturze pól.`

const [redIdeasProse, redWerdykt] = await parallel([
  ()=>agent(`${REDAKCJA}\n\nZredaguj TYLKO pola tekstowe tych 5 fabuł (NIE oceniaj, NIE dodawaj głosów ani ocen). Zwróć obiekt {ideas:[{t,en,log,silnik,op,hook,comps,protagonista}, ...]} z DOKŁADNIE 5 pozycjami w tej SAMEJ kolejności co wejście. Nie zmieniaj kolejności ani liczby fabuł.\n${JSON.stringify({ideas:scoredIdeas.map(s=>({t:s.t,en:s.en,log:s.log,silnik:s.silnik,op:s.op,hook:s.hook,comps:s.comps,protagonista:s.protagonista}))})}`,{label:'red:fabuly',phase:'Redakcja PL',schema:POMYSLY}),
  ()=>agent(`${REDAKCJA}\n\nDane (werdykt):\n${JSON.stringify(werdykt)}`,{label:'red:werdykt',phase:'Redakcja PL',schema:WERDYKT}),
])

const mergedIdeas = scoredIdeas.map((s,i)=>{
  const r=(redIdeasProse && redIdeasProse.ideas && redIdeasProse.ideas[i]) || {}
  return {...s, t:r.t||s.t, en:r.en||s.en, log:r.log||s.log, silnik:r.silnik||s.silnik, op:r.op||s.op, hook:r.hook||s.hook, comps:(Array.isArray(r.comps)&&r.comps.length)?r.comps:s.comps, protagonista:r.protagonista||s.protagonista}
})

return {
  ideas: mergedIdeas,
  winner: redWerdykt || werdykt,
  // Brief autora — dane sterujące (NIE redagowane), dziedziczone przez outline/book-bible przez DATA.brief. BEZ ZMIAN — kontrakt identyczny z market-report.
  brief: { subgenre: SUBG, conventions: CONV, protagonist: PROT, protAge: PAGE, protType: PTYPE, form: FORM, format: FORMAT, tone: TONE, spice: SPICE, taboo: TABOO, market: M },
  // Trzon autora — TYLKO prezentacyjny dla HTML (DATA.trzon). NIE trafia do pomysl.json (kontrakt!); decyzje trzonu już wsiąkły w op/silnik/protagonista zwycięzcy.
  trzon: { dramaticQ: DRAMATICQ, theme: THEME, emotion: EMOTION, antagonist: ANTAG, relation: RELATION, arc: ARC, setting: SETTING, realism: REALISM, mood: MOOD, scale: SCALE, ramy: { conflictType: CONFLICT, ending: ENDING, pace: PACE, seed: SEED } },
}
```

## Po powrocie roju agentów (główna sesja)

1. **Humanizer** — wywołaj `/humanizer:humanizer` i nanieś poprawki na prozę (patrz
   `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`). Rój już redagował, ale humanizer to
   obowiązkowy, drugi przebieg.
2. **Mapowanie do `DATA`** i budowa HTML — `build-and-verify.md`.

## Skalowanie i wariant zapasowy

- Niszowy lub lokalny gatunek → zmniejsz liczby (np. 6 typów zalążka fabuły, 5 fabuł).
- Brak narzędzia Workflow → odtwórz te same etapy równoległymi agentami `Task` (ta sama
  logika: generuj → oceń → synteza → redakcja), wolniej i w kontekście.
- Potrzebujesz twardych danych rynkowych (10 bestsellerów, 3 luki, ocena z WebSearch)?
  To pełny `market-report` (etap 1), nie ten autorski wariant bez badania rynku.
