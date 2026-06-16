# Skrypt roju agentów (Workflow) — ogólny (wariant odchudzony)

Skopiuj ten skrypt do narzędzia **Workflow** i podstaw dane wejściowe przez `args` (`{ genre, reader, subgenre, conventions, market, year, ... }` — pełny brief w sekcji parsowania). Skrypt działa dla każdego gatunku — nie wpisuj na sztywno science fiction. Liczby agentów dostosuj do gatunku (niszowy → mniej).

> **Uwaga o `args` (częsta pułapka).** Narzędzie Workflow bywa, że podaje `args` do skryptu jako **string JSON**, nie jako gotowy obiekt — wtedy `args.genre` zwróci `undefined`, a puste pole wpłynie do promptu każdego agenta (cały rój zwróci „gatunek: undefined” i odmówi pracy). Skrypt poniżej parsuje `args` odpornie i **przerywa z błędem**, gdy brakuje gatunku lub czytelnika — to celowa bramka wejścia (zasada „fail loud”). Jeśli widzisz ten błąd, sprawdź, czy w wywołaniu Workflow faktycznie przekazujesz `genre` i `reader`.

> **Wariant odchudzony (szybszy).** Ten skrypt to lżejsza wersja: **6 perspektyw rynku** (zamiast 11), **4 obiektywy luk** (zamiast 6), **6 generatorów pomysłów** (zamiast 8) z **audytem różnorodności wtopionym w syntezę** (bez osobnego agenta), **3 sędziów na pomysł** (zamiast 5) **bez ponownego WebSearch w ocenie** (oceniają na danych z fazy 1) oraz **bez osobnej fazy redakcji PL** (zasady polszczyzny wbite w `ROLE`; finalny szlif robi obowiązkowy `/humanizer:humanizer` w głównej sesji). Core bez zmian: ugruntowanie rynkowe przez WebSearch + 10 bestsellerów, 3 luki, 5 pomysłów, oceny, werdykt.

Zasady wbudowane w prompty:
- **brief autora** (`subgenre, conventions, protagonist, protAge, protType, form, format, tone, spice, taboo`) wstrzyknięty do `ROLE`/`BRIEF` jako twarde wymagania; przy „dowolny/zróżnicuj" rój nie narzuca persony,
- **warstwa adaptacyjna**: `subgenre` zawęża wyszukiwanie bestsellerów i luk do nurtu; `conventions` to obietnice gatunkowe, które 5 pomysłów MUSI dowieźć; `form` obsługuje non-fiction (wtedy machineria persony bohatera nie działa),
- **anty-monokultura**: wektor demografii rozbity na rozłączne osie, twarde guardy różnorodności w syntezie luk (max 1 demograficzna) i pomysłów (≥3 osie, ≤2 ten sam profil) — **audyt różnorodności wtopiony w prompt syntezy pomysłów**, bez osobnego agenta,
- rola: starszy redaktor do spraw zakupów z 20-letnim doświadczeniem,
- **twarda blokada gatunku**: każdy tytuł, każda luka i każdy pomysł MUSI być w podanym gatunku; po fazie 1 działa bramka walidacyjna, która odrzuca pozycje spoza gatunku i **uzupełnia je z sieci TYLKO, gdy po filtrze zostało mniej niż 10** (bez tego rój dryfuje ku temu, co dominuje listy ogólne — np. romantasy),
- świeże dane przez **WebSearch** oraz **agent-browser** (z `Bash`) **w fazach 1-2**; **faza oceny NIE używa WebSearch** — sędziowie oceniają na danych rynkowych zebranych w fazie 1; cytuj źródła,
- proza wraca już po polsku (zasady w `ROLE`), w polach zgodnych z kształtem `DATA` (patrz `build-and-verify.md`); osobnej fazy redakcji nie ma — patrz `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md` i obowiązkowy humanizer w głównej sesji.

```javascript
export const meta = {
  name: 'book-forge-market-report',
  description: 'Roj agentów (odchudzony): 10 bestsellerów, 3 luki, 5 pomysłów, ocena 1-10 bez re-searchu, werdykt',
  phases: [
    { title: 'Analiza rynku' }, { title: 'Luki' }, { title: 'Pomysly' },
    { title: 'Ocena' }, { title: 'Werdykt' },
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

const ROLE = `Jesteś starszym redaktorem do spraw zakupów z 20-letnim doświadczeniem w wyłapywaniu bestsellerów. Gatunek: ${G}${SUBG ? `, podgatunek/nurt: ${SUBG} (trzymaj się tego nurtu)` : ''}. Docelowy czytelnik: ${R}. Rynek: ${M}. BLOKADA GATUNKU: pracujesz WYŁĄCZNIE w obrębie gatunku ${G}${SUBG ? ` (a konkretnie nurtu ${SUBG})` : ''} i celujesz w czytelnika ${R}. Każdy tytuł, każda luka i każdy pomysł MUSI należeć do tego gatunku. Ogólne listy sprzedaży (NYT, Amazon, Empik, lubimyczytac) bywają zdominowane przez inne gatunki (romans, romantasy, poradniki) — filtruj je i bierz wyłącznie pozycje z ${G}, a brakujące uzupełniaj z list i nagród gatunkowych, tematycznych półek Goodreads/lubimyczytac oraz gatunkowych społeczności (Reddit). Pozycje spoza gatunku są POZA ZAKRESEM — odrzucaj je, nie podawaj jako trafienia. Gdy zadanie tego wymaga, korzystaj z NAJŚWIEŻSZYCH danych (${Y}) przez WebSearch oraz CLI agent-browser uruchamiane z Bash. Cytuj źródła, nie zmyślaj liczb. Pisz po polsku — czystą, naturalną polszczyzną, BEZ anglicyzmów (hook→haczyk, found family→rodzina z wyboru, worldbuilding→świat przedstawiony, plot armor→fabularny immunitet) i BEZ AI-slopu (nadęcia „stanowi/podkreśla", triady, nadmiar myślników); krótkie, konkretne zdania.${BRIEF}`

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

// --- FAZA 1: rynek (6 perspektyw) ---
phase('Analiza rynku')
const PERSPEKTYWY = [
  'Fenomen 1-2 czołowych tytułów kotwicznych gatunku — co je dziś realnie sprzedaje.',
  'Aktualne listy bestsellerów, ale WYŁĄCZNIE pozycje z gatunku: przefiltruj listy ogólne (NYT, Amazon, Empik) i sięgnij po listy oraz kategorie gatunkowe (np. Amazon w kategorii gatunku, Locus, tematyczne zestawienia) — co z TEGO gatunku sprzedaje się teraz.',
  'Nastroje czytelników: Reddit, fora, grupy — czego łakną, na co narzekają.',
  'Goodreads/lubimyczytać: najwyżej oceniane i najczęściej dodawane premiery gatunku.',
  'BookTok/TikTok/Bookstagram: które tytuły wybuchają wiralowo i jakie tropy je niosą.',
  'Comp titles i zaliczki: na co wydawcy stawiają duże pieniądze w tym gatunku.',
]
const analizy = (await parallel(PERSPEKTYWY.map((p,i)=>()=>
  agent(`${ROLE}\n\nTwoja perspektywa: ${p}\n\nZbadaj rynek (WebSearch/agent-browser) i podaj ustalenia oparte na faktach, konkretne tytuły i zauważone luki.`,
    {label:`analiza:${i+1}`,phase:'Analiza rynku',schema:ANALIZA})))).filter(Boolean)

const bestKandydaci = await agent(
  `${ROLE}\n\nOto analizy zespołu:\n${JSON.stringify(analizy)}\n\nSkonsoliduj w 10 najlepiej sprzedających się książek NISZY (gatunek ${G}, czytelnik ${R}). Dla każdej: t (tytuł), a (autor), g (krótki podgatunek), why (dlaczego się sprzedaje), love (co kocha czytelnik). Dodaj observations: 6-8 obserwacji {b: pogrubione zdanie, t: rozwinięcie}.`,
  {label:'synteza:top10',phase:'Analiza rynku',schema:BEST})

// BRAMKA GATUNKU: bez niej rój dryfuje ku temu, co dominuje listy ogólne (np. romantasy). WebSearch TYLKO gdy po filtrze zostało < 10.
const bestsellers = await agent(
  `${ROLE}\n\nKANDYDACI NA 10 BESTSELLERÓW:\n${JSON.stringify(bestKandydaci)}\n\nAUDYT GATUNKU. Sprawdź każdą pozycję: czy to powieść z gatunku ${G} dla czytelnika ${R}? Usuń KAŻDĄ, która nią nie jest (inny gatunek, poradnik, romans/romantasy doklejone „bo się sprzedaje” — POZA ZAKRESEM). Jeśli po odfiltrowaniu zostało 10 trafnych pozycji — NIE używaj WebSearch, po prostu zwróć je. TYLKO jeśli zostało mniej niż 10, UZUPEŁNIJ realnymi tytułami Z GATUNKU (WebSearch/agent-browser: nagrody i listy gatunkowe, tematyczne półki Goodreads/lubimyczytac, gatunkowe wątki na Reddicie); nie zmyślaj. Zwróć DOKŁADNIE 10 pozycji z gatunku (t, a, g, why, love) oraz 6-8 observations {b,t} dotyczących tego gatunku.`,
  {label:'bramka:gatunek',phase:'Analiza rynku',schema:BEST})

// --- FAZA 2: luki (4 obiektywy) ---
phase('Luki')
const OBIEKTYWY = [
  'Luki tematyczne i światotwórcze.',
  'Luki w profilu bohatera (kto prowadzi historię — wiek/płeć/typ).',
  'Luki w settingu i realiach (gdzie/kiedy).',
  'Skrzyżowania gatunkowe i luki zgrane z momentem kulturowym/kalendarzem — gdzie jest pieniądz.',
]
const kandydaci = (await parallel(OBIEKTYWY.map((l,i)=>()=>
  agent(`${ROLE}\n\nBestsellery:\n${JSON.stringify(bestsellers)}\n\nObiektyw: ${l}\n\nWskaż 2-3 NIEDOCENIANE aspekty, których brak konkurencji, z potencjałem komercyjnym. Poprzyj dowodami z rynku.`,
    {label:`luki:${i+1}`,phase:'Luki',schema:LUKI})))).filter(Boolean).flatMap(r=>r.gaps)

const luki = await agent(
  `${ROLE}\n\nKandydujące luki:\n${JSON.stringify(kandydaci)}\n\nWybierz DOKŁADNIE 3 najsilniejsze. Dla każdej: n (numer 1-3), h (nagłówek), p (opis), e (dowód i okazja jako STRUKTURA: e.proof = 3-5 osobnych, zwięzłych dowodów, każdy z URL źródła gdy istnieje; e.notes = plakietki o k ∈ {Luka, Ryzyko, Pozycjonowanie} i treści t — NIE pisz jednego długiego akapitu). Połącz pokrewne, odrzuć słabe.\n\nGUARD RÓŻNORODNOŚCI: MAKSYMALNIE JEDNA z 3 luk może dotyczyć profilu/persony bohatera (wiek/płeć/typ protagonisty). Pozostałe dwie MUSZĄ dotyczyć innych osi (setting, koncept, tempo/format, skrzyżowanie gatunkowe, temat). Jeśli kandydaci są zdominowani przez demografię — świadomie wybierz różnorodność, nie powielaj jednej „białej plamy".`,
  {label:'synteza:3luki',phase:'Luki',schema:LUKI})

// --- FAZA 3: pomysly (6 generatorów, audyt różnorodności WTOPIONY w syntezę) ---
phase('Pomysly')
const KATY = [
  'Pomysł w duchu czołowego tytułu kotwicznego, ale z JEDNYM złamanym założeniem nurtu, celujący w luki.',
  'Pomysł „jeden bohater vs świat”, gdzie bohater pragnie czegoś, co go zniszczy, celujący w luki.',
  'Pomysł, w którym sam świat lub jego zasada jest źródłem nieuniknionego konfliktu, celujący w luki.',
  'Odważne skrzyżowanie gatunkowe — mechanizm z OBCEJ dziedziny (nauka, zawód, rytuał, historia), celujący w luki.',
  'Pomysł oparty na momencie kulturowym zderzonym z osobistą stawką bohatera, celujący w luki.',
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
// AUDYT RÓŻNORODNOŚCI WTOPIONY: synteza sama pilnuje rozkładu profili bohatera (zamiast osobnego agenta-audytora)
const ANTYMONO = (PROT === 'dowolny' || PROT === 'zroznicuj')
  ? 'AUDYT WTOPIONY: zanim zwrócisz 5 pomysłów, sprawdź rozkład profili protagonisty — jeśli >60% dzieli zbliżony profil (ten sam wiek/płeć/typ), PRZEBUDUJ nadmiarowe duplikaty pomysłami z INNYM profilem (trzymając gatunek i te same luki). Nie zwracaj monokultury.'
  : ''
const finalisci = await agent(
  `${ROLE}\n\nPomysły zespołu:\n${JSON.stringify(propozycje)}\n\nWybierz 5 najsilniejszych i PODKRĘĆ każdy z nich. PODKRĘCENIE = wyostrz silnik premisy (mocniejsza sprzeczność), podnieś stawkę, dodaj jeden nieoczywisty zwrot. ŻELAZNA REGUŁA „WZMACNIAJ, NIE PODMIENIAJ": surowy pomysł musi pozostać rozpoznawalny — wzmacniasz, nie zastępujesz go innym. Dopracuj pola (t, en, gap, log, silnik, op, hook, comps, protagonista). Pomysły mają być wyraziste, świeże i sprzedawalne.\n\nGUARD RÓŻNORODNOŚCI: 5 pomysłów MUSI różnić się na co najmniej 3 osiach (profil bohatera, setting, ton, podgatunek, format). ${DYWERSYFIKACJA} ${ANTYMONO}`,
  {label:'synteza:5pomyslow',phase:'Pomysly',schema:POMYSLY})
const ideas = finalisci.ideas.slice(0,5)

// --- FAZA 4: ocena (3 sędziów/pomysł, BEZ WebSearch — na danych z fazy 1) ---
phase('Ocena')
const SEDZIOWIE = [
  {n:'Redaktor (finanse-rynek)',l:'Oceń zwrot komercyjny na bazie zebranych danych rynkowych (bestsellery i luki w kontekście): rynek, ryzyko, zaliczka, potencjał serii, realne wyniki podobnych tytułów z TYCH danych.'},
  {n:'Marketing',l:'Oceń wiralowość, łatwość pozycjonowania, siłę haczyka i głód zakupowy czytelnika docelowego (BookTok/social) — na bazie danych z fazy 1.'},
  {n:'Adwokat innowacji',l:'Oceń ODWAGĘ i świeżość: czy SILNIK premisy to realna, samonapędzająca się sprzeczność? Czy pomysł otwiera nową półkę, zamiast dosiadać przegrzanego trendu? Tu RYZYKO i nieoczywistość to PREMIA, nie kara; pomysł poprawny, lecz przewidywalny oceń NIŻEJ.'},
]
const ocenione = await parallel(ideas.map((idea)=>async()=>{
  const votes=(await parallel(SEDZIOWIE.map((s)=>()=>
    agent(`${ROLE}\n\nWcielasz się w rolę: ${s.n}. ${s.l}\n\nPomysł:\n${JSON.stringify(idea)}\n\nBestsellery i luki (dane rynkowe z fazy 1):\n${JSON.stringify({books:bestsellers.books,gaps:luki.gaps})}\n\nNIE używaj WebSearch ani agent-browser — oceniaj WYŁĄCZNIE na powyższych danych rynkowych z fazy 1. Zwróć szczególną uwagę na pole „silnik" — pomysł bez działającego silnika premisy (płaska sytuacja, konflikt doklejony z zewnątrz) oceń niżej. Oceń też ODRÓŻNIALNOŚĆ od obecnej fali: pomysł, który tylko dosiada przegrzanego trendu (np. kolejna starsza bohaterka przy rynku już nimi nasyconym), dostaje KARĘ do oceny, nie premię — świeżość ma wartość. Wystaw ocenę 1-10 (może być ułamkowa) z uzasadnieniem, mocnymi stronami i ryzykami.`,
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

return {
  bestsellers,
  gaps: luki.gaps,
  ideas: scoredIdeas,
  winner: werdykt,
  // Brief autora — dane sterujące (NIE redagowane), dziedziczone przez outline/book-bible przez DATA.brief
  brief: { subgenre: SUBG, conventions: CONV, protagonist: PROT, protAge: PAGE, protType: PTYPE, form: FORM, format: FORMAT, tone: TONE, spice: SPICE, taboo: TABOO, market: M },
}
```

## Po powrocie roju agentów (główna sesja)

1. **Humanizer** — wywołaj `/humanizer:humanizer` i nanieś poprawki na prozę (patrz `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`). To **jedyny** przebieg redakcji (osobna faza w roju została usunięta, proza wraca po polsku z `ROLE`) — obowiązkowy.
2. **Lokalizacja tytułów** — zweryfikuj polskie wydania przez agent-browser **tylko dla 10 bestsellerów** (nie dla comps), w **równoległym batchu** sesji (best-effort: błąd/timeout → zostaw tytuł oryginalny). Procedura i pułapki: `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`.
3. **Mapowanie do `DATA`** i budowa HTML — `build-and-verify.md`.

## Skalowanie i wariant zapasowy

- Niszowy lub lokalny gatunek → zmniejsz liczby jeszcze bardziej (np. 4 perspektywy, 5 pomysłów).
- Potrzebujesz szerszego ugruntowania rynkowego → zwiększ liczbę perspektyw fazy 1 i przywróć WebSearch w ocenie (wolniej, dokładniej).
- Brak narzędzia Workflow → odtwórz te same etapy równoległymi agentami `Task` (ta sama logika: generuj → oceń → synteza), wolniej i w kontekście.
```
