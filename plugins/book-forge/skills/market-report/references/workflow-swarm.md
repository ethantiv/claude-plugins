# Skrypt roju agentów (Workflow) — ogólny

Skopiuj ten skrypt do narzędzia **Workflow** i podstaw dane wejściowe przez `args` (`{ genre, reader, subgenre, conventions, market, year, ... }` — pełny brief w sekcji parsowania). Skrypt działa dla każdego gatunku — nie wpisuj na sztywno science fiction. Liczby agentów dostosuj do gatunku (niszowy → mniej).

> **Uwaga o `args` (częsta pułapka).** Narzędzie Workflow bywa, że podaje `args` do skryptu jako **string JSON**, nie jako gotowy obiekt — wtedy `args.genre` zwróci `undefined`, a puste pole wpłynie do promptu każdego agenta (cały rój zwróci „gatunek: undefined” i odmówi pracy). Skrypt poniżej parsuje `args` odpornie i **przerywa z błędem**, gdy brakuje gatunku lub czytelnika — to celowa bramka wejścia (zasada „fail loud”). Jeśli widzisz ten błąd, sprawdź, czy w wywołaniu Workflow faktycznie przekazujesz `genre` i `reader`.

Zasady wbudowane w prompty:
- **brief autora** (`subgenre, conventions, protagonist, protAge, protType, form, format, tone, spice, taboo`) wstrzyknięty do `ROLE`/`BRIEF` jako twarde wymagania; przy „dowolny/zróżnicuj" rój nie narzuca persony,
- **warstwa adaptacyjna**: `subgenre` zawęża wyszukiwanie bestsellerów i luk do nurtu; `conventions` to obietnice gatunkowe, które 5 pomysłów MUSI dowieźć; `form` obsługuje non-fiction (wtedy machineria persony bohatera nie działa),
- **anty-monokultura**: wektor demografii rozbity na rozłączne osie, twarde guardy różnorodności w syntezie luk (max 1 demograficzna) i pomysłów (≥3 osie, ≤2 ten sam profil), kryterium anty-trend u sędziów, audytor różnorodności przed oceną,
- rola: starszy redaktor do spraw zakupów z 20-letnim doświadczeniem,
- **twarda blokada gatunku**: każdy tytuł, każda luka i każdy pomysł MUSI być w podanym gatunku; po fazie 1 działa bramka walidacyjna, która odrzuca pozycje spoza gatunku i uzupełnia je z list gatunkowych (bez tego rój dryfuje ku temu, co dominuje listy ogólne — np. romantasy — zamiast trzymać niszę),
- świeże dane przez **WebSearch** oraz **agent-browser** (z `Bash`); cytuj źródła,
- ostatni etap to **redakcja na poprawną, naturalną polszczyznę** (bez anglicyzmów i AI-slopu) — patrz `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`,
- proza wraca już po polsku, w polach zgodnych z kształtem `DATA` (patrz `build-and-verify.md`).

```javascript
export const meta = {
  name: 'book-forge-market-report',
  description: 'Roj agentów: 10 bestsellerów, 3 luki, 5 pomysłów, ocena 1-10, werdykt, redakcja PL',
  phases: [
    { title: 'Analiza rynku' }, { title: 'Luki' }, { title: 'Pomysly' },
    { title: 'Ocena' }, { title: 'Werdykt' }, { title: 'Redakcja PL' },
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
  : `- Bohater: ${PROT === 'dowolny' ? 'profil dobierasz pod lukę rynkową'
      : PROT === 'zroznicuj' ? 'NIE narzucaj jednego profilu — w 5 pomysłach protagoniści MUSZĄ się różnić wiekiem/płcią/typem'
      : `protagonista to ${PROT}${PAGE ? `, wiek ${PAGE}` : ''}${PTYPE ? `, typ: ${PTYPE}` : ''} — trzymaj się tego we WSZYSTKICH pomysłach`}.`

const BRIEF = `
BRIEF AUTORA (twarde wymagania — nadrzędne nad domysłami):
${PERSONA}
- Format: ${FORMAT} (ocena finansowa: ${FORMAT === 'pojedyncza' ? 'oceniaj samodzielny, domknięty łuk; NIE premiuj potencjału serii' : 'uwzględnij potencjał serii i zasiewy międzytomowe'}).
- Ton: ${TONE === 'dowolny' ? 'dobierz pod niszę' : `utrzymaj ton: ${TONE}`}.
- Intensywność (spice/przemoc/groza wg gatunku): ${SPICE === 'dobierz' ? 'typowa dla niszy' : SPICE}.
${CONV.length ? `- Konwencje/obietnice gatunkowe, które pomysły MUSZĄ dowieźć: ${CONV.join(', ')}.` : ''}
${TABOO.length ? `- TABU (NIGDY nie proponuj tych tematów): ${TABOO.join(', ')}.` : ''}`

const ROLE = `Jesteś starszym redaktorem do spraw zakupów z 20-letnim doświadczeniem w wyłapywaniu bestsellerów. Gatunek: ${G}${SUBG ? `, podgatunek/nurt: ${SUBG} (trzymaj się tego nurtu)` : ''}. Docelowy czytelnik: ${R}. Rynek: ${M}. BLOKADA GATUNKU: pracujesz WYŁĄCZNIE w obrębie gatunku ${G}${SUBG ? ` (a konkretnie nurtu ${SUBG})` : ''} i celujesz w czytelnika ${R}. Każdy tytuł, każda luka i każdy pomysł MUSI należeć do tego gatunku. Ogólne listy sprzedaży (NYT, Amazon, Empik, lubimyczytac) bywają zdominowane przez inne gatunki (romans, romantasy, poradniki) — filtruj je i bierz wyłącznie pozycje z ${G}, a brakujące uzupełniaj z list i nagród gatunkowych, tematycznych półek Goodreads/lubimyczytac oraz gatunkowych społeczności (Reddit). Pozycje spoza gatunku są POZA ZAKRESEM — odrzucaj je, nie podawaj jako trafienia. Korzystaj z NAJŚWIEŻSZYCH danych (${Y}) przez WebSearch oraz CLI agent-browser uruchamiane z Bash (listy bestsellerów, Goodreads/lubimyczytac, Reddit, BookTok, nagrody gatunku, transakcje wydawnicze). Cytuj źródła, nie zmyślaj liczb. Pisz po polsku.${BRIEF}`

// --- schematy (skrócone; rozszerz pola opisowe wg potrzeb) ---
const ANALIZA = { type:'object', required:['perspektywa','ustalenia','topKsiazki','luki'], properties:{
  perspektywa:{type:'string'}, ustalenia:{type:'array',items:{type:'string'}},
  topKsiazki:{type:'array',items:{type:'string'}}, luki:{type:'array',items:{type:'string'}} } }
const BEST = { type:'object', required:['books','observations'], properties:{
  books:{type:'array',items:{type:'object',required:['t','a','g','why','love'],properties:{
    t:{type:'string'},a:{type:'string'},g:{type:'string'},why:{type:'string'},love:{type:'string'}}}},
  observations:{type:'array',items:{type:'object',required:['b','t'],properties:{b:{type:'string'},t:{type:'string'}}}} } }
const LUKI = { type:'object', required:['gaps'], properties:{ gaps:{type:'array',items:{
  type:'object',required:['n','h','p','e'],properties:{n:{type:'number'},h:{type:'string'},p:{type:'string'},
  e:{type:'object',required:['proof'],properties:{                          // dowód i okazja — STRUKTURA, nie jeden akapit
    proof:{type:'array',items:{type:'string'}},                            // 3-5 osobnych dowodów (każdy z URL źródła, jeśli jest)
    notes:{type:'array',items:{type:'object',required:['k','t'],properties:{ // wyróżnione plakietki
      k:{type:'string'},                                                    // 'Luka' | 'Ryzyko' | 'Pozycjonowanie'
      t:{type:'string'}}}}}}}}} } }
const POMYSLY = { type:'object', required:['ideas'], properties:{ ideas:{type:'array',items:{
  type:'object',required:['t','en','gap','log','silnik','op','hook','comps','protagonista'],properties:{
    t:{type:'string'},en:{type:'string'},gap:{type:'string'},log:{type:'string'},
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

// --- FAZA 1: rynek ---
phase('Analiza rynku')
const PERSPEKTYWY = [
  'Fenomen 1-2 czołowych tytułów kotwicznych gatunku — co je dziś realnie sprzedaje.',
  'Aktualne listy bestsellerów, ale WYŁĄCZNIE pozycje z gatunku: przefiltruj listy ogólne (NYT, Amazon, Empik) i sięgnij po listy oraz kategorie gatunkowe (np. Amazon w kategorii gatunku, Locus, tematyczne zestawienia) — co z TEGO gatunku sprzedaje się teraz.',
  'Nastroje czytelników: Reddit, fora, grupy — czego łakną, na co narzekają.',
  'Goodreads/lubimyczytać: najwyżej oceniane i najczęściej dodawane premiery gatunku.',
  'BookTok/TikTok/Bookstagram: które tytuły wybuchają wiralowo i jakie tropy je niosą.',
  'Comp titles i zaliczki: na co wydawcy stawiają duże pieniądze w tym gatunku.',
  'Mapa podgatunków: które rosną, które są nasycone.',
  'Nagrody gatunku — co docenia branża, a czego brak masowemu czytelnikowi.',
  'Audiobook i ekranizacje — jak adaptacje napędzają sprzedaż książek.',
  // Wektor demografii rozbity na rozłączne osie — inaczej rój konwerguje na jednej „białej plamie" (monokultura bohaterów)
  'Luki w typie/profilu protagonisty — kto prowadzi te historie i jakiego bohatera brakuje.',
  'Luki w settingu i realiach — gdzie i kiedy dzieją się historie, a gdzie jest pustka.',
]
const analizy = (await parallel(PERSPEKTYWY.map((p,i)=>()=>
  agent(`${ROLE}\n\nTwoja perspektywa: ${p}\n\nZbadaj rynek (WebSearch/agent-browser) i podaj ustalenia oparte na faktach, konkretne tytuły i zauważone luki.`,
    {label:`analiza:${i+1}`,phase:'Analiza rynku',schema:ANALIZA})))).filter(Boolean)

const bestKandydaci = await agent(
  `${ROLE}\n\nOto analizy zespołu:\n${JSON.stringify(analizy)}\n\nSkonsoliduj w 10 najlepiej sprzedających się książek NISZY (gatunek ${G}, czytelnik ${R}). Dla każdej: t (tytuł), a (autor), g (krótki podgatunek), why (dlaczego się sprzedaje), love (co kocha czytelnik). Dodaj observations: 6-8 obserwacji {b: pogrubione zdanie, t: rozwinięcie}.`,
  {label:'synteza:top10',phase:'Analiza rynku',schema:BEST})

// BRAMKA GATUNKU: bez niej rój dryfuje ku temu, co dominuje listy ogólne (np. romantasy), zamiast trzymać niszę
const bestsellers = await agent(
  `${ROLE}\n\nKANDYDACI NA 10 BESTSELLERÓW:\n${JSON.stringify(bestKandydaci)}\n\nAUDYT GATUNKU. Sprawdź każdą pozycję: czy to powieść z gatunku ${G} dla czytelnika ${R}? Usuń KAŻDĄ, która nią nie jest (inny gatunek, poradnik, romans/romantasy doklejone „bo się sprzedaje” — POZA ZAKRESEM). Jeśli zostało mniej niż 10, UZUPEŁNIJ realnymi tytułami Z GATUNKU (WebSearch/agent-browser: nagrody i listy gatunkowe, tematyczne półki Goodreads/lubimyczytac, gatunkowe wątki na Reddicie); nie zmyślaj. Zwróć DOKŁADNIE 10 pozycji z gatunku (t, a, g, why, love) oraz 6-8 observations {b,t} dotyczących tego gatunku.`,
  {label:'bramka:gatunek',phase:'Analiza rynku',schema:BEST})

// --- FAZA 2: luki ---
phase('Luki')
const OBIEKTYWY = [
  'Luki tematyczne i światotwórcze.','Luki w profilu bohatera (kto prowadzi historię — wiek/płeć/typ).',
  'Luki w settingu i realiach (gdzie/kiedy).','Luki tonalne i w tempie/formacie.',
  'Skrzyżowania gatunkowe, gdzie jest pieniądz.','Luki zgrane z momentem kulturowym/kalendarzem.',
]
const kandydaci = (await parallel(OBIEKTYWY.map((l,i)=>()=>
  agent(`${ROLE}\n\nBestsellery:\n${JSON.stringify(bestsellers)}\n\nObiektyw: ${l}\n\nWskaż 2-3 NIEDOCENIANE aspekty, których brak konkurencji, z potencjałem komercyjnym. Poprzyj dowodami z rynku.`,
    {label:`luki:${i+1}`,phase:'Luki',schema:LUKI})))).filter(Boolean).flatMap(r=>r.gaps)

const luki = await agent(
  `${ROLE}\n\nKandydujące luki:\n${JSON.stringify(kandydaci)}\n\nWybierz DOKŁADNIE 3 najsilniejsze. Dla każdej: n (numer 1-3), h (nagłówek), p (opis), e (dowód i okazja jako STRUKTURA: e.proof = 3-5 osobnych, zwięzłych dowodów, każdy z URL źródła gdy istnieje; e.notes = plakietki o k ∈ {Luka, Ryzyko, Pozycjonowanie} i treści t — NIE pisz jednego długiego akapitu). Połącz pokrewne, odrzuć słabe.\n\nGUARD RÓŻNORODNOŚCI: MAKSYMALNIE JEDNA z 3 luk może dotyczyć profilu/persony bohatera (wiek/płeć/typ protagonisty). Pozostałe dwie MUSZĄ dotyczyć innych osi (setting, koncept, tempo/format, skrzyżowanie gatunkowe, temat). Jeśli kandydaci są zdominowani przez demografię — świadomie wybierz różnorodność, nie powielaj jednej „białej plamy".`,
  {label:'synteza:3luki',phase:'Luki',schema:LUKI})

// --- FAZA 3: pomysly ---
phase('Pomysly')
const KATY = [
  'Pomysł w duchu czołowego tytułu kotwicznego, ale z JEDNYM złamanym założeniem nurtu, celujący w luki.',
  'Pomysł „jeden bohater vs świat”, gdzie bohater pragnie czegoś, co go zniszczy, celujący w luki.',
  'Pomysł, w którym sam świat lub jego zasada jest źródłem nieuniknionego konfliktu, celujący w luki.',
  'Odważne skrzyżowanie gatunkowe — mechanizm z OBCEJ dziedziny (nauka, zawód, rytuał, historia), celujący w luki.',
  'Pomysł oparty na momencie kulturowym zderzonym z osobistą stawką bohatera, celujący w luki.',
  'Pomysł z niedoreprezentowaną perspektywą kulturową, która NAPĘDZA fabułę, celujący w luki.',
  'Pomysł z premisą, którą da się streścić w jednym zdaniu i opowiedzieć dalej, celujący w luki.',
  'Ciemny koń — premisa tak nieoczywista, że konkurencja nie odważyłaby się jej kupić.',
]
// Soczewki twórcze — narzędzia myślowe rotowane NA AGENTACH obok KATY (różnorodność poznawcza, nie tylko zmiana framingu)
const SOCZEWKI = [
  'CO JEŚLI: zmień jedno twarde założenie gatunku i wyciągnij z tego konsekwencje.',
  'ZDERZENIE DOMEN: wstrzyknij mechanizm z obcej dziedziny (nauka, zawód, rytuał, historia) jako silnik fabuły.',
  'INWERSJA: odwróć główną konwencję nurtu (kto poluje, kto ucieka, kto wie, kto płaci).',
  'ESKALACJA: sytuacja startowa, która z definicji sama się pogarsza, krok po kroku.',
  'KOLIZJA Z MOMENTEM: zderz premisę z dzisiejszym lękiem lub napięciem kulturowym.',
  'IRONIA WBUDOWANA: bohater jest sprawcą własnego problemu (jak „idealna żona, która zaplanowała własne morderstwo”).',
  'PYTANIE DRAMATYCZNE: zacznij od jednego pytania, na które czytelnik MUSI poznać odpowiedź.',
  'STAWKA OSOBISTA: sprowadź globalne zagrożenie do jednej konkretnej osoby do uratowania albo zniszczenia.',
]
// Reguła silnika premisy — dla non-fiction (FORM) reinterpretowana, nie wyłączona
const SILNIK_REGULA = FORM
  ? 'centralne napięcie lub pytanie, które trzyma czytelnika (sprzeczność w temacie, mit do obalenia) — NIE wymuszaj fabularnego konfliktu'
  : 'strukturalna sprzeczność lub ironia, która SAMA generuje konflikt — napięcie wpisane w sytuację startową, nie doklejony z zewnątrz złoczyńca'
const propozycje = (await parallel(KATY.map((a,i)=>()=>
  agent(`${ROLE}\n\nLuki:\n${JSON.stringify(luki.gaps)}\n\nZadanie (framing): ${a}\nSOCZEWKA TWÓRCZA (użyj jej jako narzędzia myślowego, nie ozdoby): ${SOCZEWKI[i % SOCZEWKI.length]}\n\nKażdy pomysł MUSI mieć działający SILNIK PREMISY: ${SILNIK_REGULA}. Zaproponuj 1-2 pomysły. Dla każdego: t (POLSKI roboczy tytuł), en (oryginalny tytuł roboczy po angielsku), gap (która luka), log (logline 1 zdanie po polsku), silnik (1-2 zdania — ${SILNIK_REGULA}), op (streszczenie 3-4 zdania po polsku), hook (haczyk sprzedażowy po polsku, może mieć <b>), comps (3-4 tytuły porównawcze), protagonista (zwięzły profil bohatera: płeć, wiek, typ — np. „mężczyzna, ~35, były żołnierz"; zgodny z BRIEF AUTORA powyżej).`,
    {label:`pomysl:${i+1}`,phase:'Pomysly',schema:POMYSLY})))).filter(Boolean).flatMap(r=>r.ideas)

// Operacyjna definicja „zróżnicowania" — inaczej rój daje 5 wariantów jednego pomysłu (efekt kuli śnieżnej z jednej luki)
const DYWERSYFIKACJA = PROT === 'zroznicuj'
  ? 'Autor zażądał RÓŻNYCH bohaterów — to wymóg twardy: 5 pomysłów MUSI mieć wyraźnie różne profile protagonisty (wiek/płeć/typ).'
  : (PROT !== 'dowolny'
      ? `Profil bohatera jest USTALONY przez autora (${PROT}${PAGE?', '+PAGE:''}) — wszystkie pomysły go trzymają; różnicuj POZOSTAŁE osie (setting, ton, koncept, podgatunek).`
      : 'Nie więcej niż 2 z 5 pomysłów mogą dzielić ten sam profil protagonisty; reszta musi się różnić.')
const finalisci = await agent(
  `${ROLE}\n\nPomysły zespołu:\n${JSON.stringify(propozycje)}\n\nWybierz 5 najsilniejszych i PODKRĘĆ każdy z nich. PODKRĘCENIE = wyostrz silnik premisy (mocniejsza sprzeczność), podnieś stawkę, dodaj jeden nieoczywisty zwrot. ŻELAZNA REGUŁA „WZMACNIAJ, NIE PODMIENIAJ": surowy pomysł musi pozostać rozpoznawalny — wzmacniasz, nie zastępujesz go innym. Dopracuj pola (t, en, gap, log, silnik, op, hook, comps, protagonista). Pomysły mają być wyraziste, świeże i sprzedawalne.\n\nGUARD RÓŻNORODNOŚCI: 5 pomysłów MUSI różnić się na co najmniej 3 osiach (profil bohatera, setting, ton, podgatunek, format). ${DYWERSYFIKACJA}`,
  {label:'synteza:5pomyslow',phase:'Pomysly',schema:POMYSLY})
let ideas = finalisci.ideas.slice(0,5)

// Audyt różnorodności (zanim ruszy ocena — poprawiona stawka płynnie wejdzie do scoringu).
// Łapie monokulturę profilu bohatera, której guardy syntezy nie złapały. Pomijany, gdy autor JAWNIE ustalił profil.
if (PROT === 'dowolny' || PROT === 'zroznicuj') {
  const audyt = await agent(
    `${ROLE}\n\n5 pomysłów (profile bohaterów):\n${JSON.stringify(ideas.map(s=>({t:s.t,protagonista:s.protagonista,gap:s.gap})))}\n\nSprawdź rozkład profili protagonisty. Monokultura = >60% pomysłów ma ZBLIŻONY profil (ten sam wiek/płeć/typ). Zwróć: monokultura (bool), dominujacy (opis), uwaga (1 zdanie).`,
    {label:'audyt:roznorodnosc',phase:'Pomysly',schema:{type:'object',required:['monokultura','uwaga'],properties:{monokultura:{type:'boolean'},dominujacy:{type:'string'},uwaga:{type:'string'}}}})
  if (audyt && audyt.monokultura) {
    log('Audyt różnorodności: monokultura profili bohatera — przerabiam stawkę')
    const poprawione = await agent(
      `${ROLE}\n\nStawka jest zdominowana przez jeden profil bohatera (${audyt.dominujacy||''}). Przebuduj 5 pomysłów tak, by NIE WIĘCEJ niż 2 dzieliły ten profil — zastąp nadmiarowe duplikaty pomysłami z INNYM profilem protagonisty, trzymając gatunek ${G} i te same luki. Zachowaj najsilniejsze pomysły, podmień tylko duplikaty. Pola: t, en, gap, log, silnik, op, hook, comps, protagonista.\n\nDotychczasowe:\n${JSON.stringify(ideas)}`,
      {label:'synteza:roznorodnosc',phase:'Pomysly',schema:POMYSLY})
    if (poprawione && poprawione.ideas && poprawione.ideas.length) ideas = poprawione.ideas.slice(0,5)
  }
}

// --- FAZA 4: ocena ---
phase('Ocena')
const SEDZIOWIE = [
  {n:'Redaktor (finanse)',l:'Oceń zwrot: rynek, ryzyko, zaliczka, potencjał serii.'},
  {n:'Marketing',l:'Oceń wiralowość, łatwość pozycjonowania, siłę haczyka (BookTok/social).'},
  {n:'Czytelnik docelowy',l:'Oceń, czy KUPIŁBYŚ to i polecił; czy haczyk budzi głód.'},
  {n:'Analityk sprzedaży',l:'Oceń na podstawie realnych wyników podobnych tytułów (WebSearch).'},
  {n:'Adwokat innowacji',l:'Oceń ODWAGĘ i świeżość: czy SILNIK premisy to realna, samonapędzająca się sprzeczność? Czy pomysł otwiera nową półkę, zamiast dosiadać przegrzanego trendu? Tu RYZYKO i nieoczywistość to PREMIA, nie kara; pomysł poprawny, lecz przewidywalny oceń NIŻEJ.'},
]
const ocenione = await parallel(ideas.map((idea)=>async()=>{
  const votes=(await parallel(SEDZIOWIE.map((s)=>()=>
    agent(`${ROLE}\n\nWcielasz się w rolę: ${s.n}. ${s.l}\n\nPomysł:\n${JSON.stringify(idea)}\n\nLuki:\n${JSON.stringify(luki.gaps)}\n\nZweryfikuj realia rynku (WebSearch). Zwróć szczególną uwagę na pole „silnik" — pomysł bez działającego silnika premisy (płaska sytuacja, konflikt doklejony z zewnątrz) oceń niżej. Oceń też ODRÓŻNIALNOŚĆ od obecnej fali: pomysł, który tylko dosiada przegrzanego trendu (np. kolejna starsza bohaterka przy rynku już nimi nasyconym), dostaje KARĘ do oceny, nie premię — świeżość ma wartość. Wystaw ocenę 1-10 (może być ułamkowa) z uzasadnieniem, mocnymi stronami i ryzykami.`,
      {label:`ocena:${s.n.slice(0,12)}:${idea.t.slice(0,12)}`,phase:'Ocena',schema:OCENA})))).filter(Boolean)
  const avg=votes.reduce((s,v)=>s+v.score,0)/(votes.length||1)
  return {...idea, votes, avgScore:Math.round(avg*10)/10}
}))
const scoredIdeas = ocenione.filter(Boolean).sort((a,b)=>b.avgScore-a.avgScore)

// --- FAZA 5: werdykt ---
phase('Werdykt')
const werdykt = await agent(
  `${ROLE}\n\n5 pomysłów z ocenami:\n${JSON.stringify(scoredIdeas.map(s=>({t:s.t,log:s.log,protagonista:s.protagonista,avgScore:s.avgScore,votes:s.votes})))}\n\nLuki:\n${JSON.stringify(luki.gaps)}\n\nWskaż JEDEN pomysł do rozwijania. Podaj: winnerTitle, rationale (dlaczego), warning (uczciwe ostrzeżenie o ryzykach — fail loud; JEŚLI wszystkie 5 pomysłów dzieli ten sam profil bohatera, ZGŁOŚ to jako ryzyko monokultury i wskaż, czego w stawce zabrakło), whyNow (dlaczego teraz), positioning (jak pozycjonować), nextSteps (kroki dla autora), runnerTitle (tytuł wicemistrza), runnerWhy (dlaczego wicemistrz).`,
  {label:'werdykt',phase:'Werdykt',schema:WERDYKT})

// --- FAZA 6: redakcja na poprawną, naturalną polszczyznę ---
phase('Redakcja PL')
const REDAKCJA = `Jesteś redaktorem języka polskiego w wydawnictwie. Przepisz CAŁY przekazany tekst na poprawną, naturalną polszczyznę. ŻELAZNE zasady: (1) usuń anglicyzmy i kalki — tłumacz żargon (np. competence porn → frajda z patrzenia, jak bohater kompetentnie rozwiązuje problemy; hook → haczyk; found family → rodzina z wyboru; worldbuilding → świat przedstawiony; plot armor → fabularny immunitet); (2) usuń AI-slop (nadęcia „stanowi/podkreśla”, triady, nadmiar myślników, puste konkluzje); (3) krótkie, konkretne zdania, zmienny rytm; (4) zachowaj sens, liczby i źródła; (5) cudzysłowy „ ”, przecinki dziesiętne. Zwróć tekst w tej samej strukturze pól.`

const [redBest, redLuki, redIdeasProse, redWerdykt] = await parallel([
  ()=>agent(`${REDAKCJA}\n\nDane (10 bestsellerów):\n${JSON.stringify(bestsellers)}`,{label:'red:bestsellery',phase:'Redakcja PL',schema:BEST}),
  ()=>agent(`${REDAKCJA}\n\nDane (3 luki):\n${JSON.stringify(luki)}`,{label:'red:luki',phase:'Redakcja PL',schema:LUKI}),
  ()=>agent(`${REDAKCJA}\n\nZredaguj TYLKO pola tekstowe tych 5 pomysłów (NIE oceniaj, NIE dodawaj głosów ani ocen). Zwróć obiekt {ideas:[{t,en,gap,log,silnik,op,hook,comps,protagonista}, ...]} z DOKŁADNIE 5 pozycjami w tej SAMEJ kolejności co wejście. Pole gap zachowaj w formacie zaczynającym się od numeru luki (np. „Luka 2 — …”). Nie zmieniaj kolejności ani liczby pomysłów.\n${JSON.stringify({ideas:scoredIdeas.map(s=>({t:s.t,en:s.en,gap:s.gap,log:s.log,silnik:s.silnik,op:s.op,hook:s.hook,comps:s.comps,protagonista:s.protagonista}))})}`,{label:'red:pomysly',phase:'Redakcja PL',schema:POMYSLY}),
  ()=>agent(`${REDAKCJA}\n\nDane (werdykt):\n${JSON.stringify(werdykt)}`,{label:'red:werdykt',phase:'Redakcja PL',schema:WERDYKT}),
])

const mergedIdeas = scoredIdeas.map((s,i)=>{
  const r=(redIdeasProse && redIdeasProse.ideas && redIdeasProse.ideas[i]) || {}
  return {...s, t:r.t||s.t, en:r.en||s.en, gap:r.gap||s.gap, log:r.log||s.log, silnik:r.silnik||s.silnik, op:r.op||s.op, hook:r.hook||s.hook, comps:(Array.isArray(r.comps)&&r.comps.length)?r.comps:s.comps, protagonista:r.protagonista||s.protagonista}
})

return {
  bestsellers: redBest || bestsellers,
  gaps: (redLuki && redLuki.gaps) || luki.gaps,
  ideas: mergedIdeas,
  winner: redWerdykt || werdykt,
  // Brief autora — dane sterujące (NIE redagowane), dziedziczone przez outline/book-bible przez DATA.brief
  brief: { subgenre: SUBG, conventions: CONV, protagonist: PROT, protAge: PAGE, protType: PTYPE, form: FORM, format: FORMAT, tone: TONE, spice: SPICE, taboo: TABOO, market: M },
}
```

## Po powrocie roju agentów (główna sesja)

1. **Humanizer** — wywołaj `/humanizer:humanizer` i nanieś poprawki na prozę (patrz `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`). Rój już redagował, ale humanizer to obowiązkowy, drugi przebieg.
2. **Lokalizacja tytułów** — zweryfikuj polskie wydania przez agent-browser (`${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`).
3. **Mapowanie do `DATA`** i budowa HTML — `build-and-verify.md`.

## Skalowanie i wariant zapasowy

- Niszowy lub lokalny gatunek → zmniejsz liczby (np. 6 perspektyw, 5 pomysłów).
- Brak narzędzia Workflow → odtwórz te same etapy równoległymi agentami `Task` (ta sama logika: generuj → oceń → synteza → redakcja), wolniej i w kontekście.
