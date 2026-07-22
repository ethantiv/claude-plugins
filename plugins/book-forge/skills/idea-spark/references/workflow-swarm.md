# Skrypt roju (Workflow) — idea-spark (lekka iskra: 5 zaskakująco nieoczywistych fabuł)

Skopiuj ten skrypt do narzędzia **Workflow** i podstaw dane wejściowe przez `args`
(rdzeń + opcjonalne zawężenie z Kroku 1 — patrz sekcja parsowania). To **lekki wariant**
etapu 1: **nie ma faz „Analiza rynku" i „Luki", nie ma WebSearch, nie ma osobnej fazy redakcji**.
Autor podaje minimum (gatunek, czytelnik, poziom dziwności, tabu + opcjonalne zawężenie), a rój
generuje **5 zaskakująco nieoczywistych fabuł**, ocenia je pod kątem świeżości i wykonalności,
i wybiera zwycięzcę. Pomysły powstają z wiedzy gatunkowej modelu, nie ze świeżych danych
rynkowych. Skrypt działa dla każdego gatunku — nie wpisuj na sztywno science fiction.

> **Uwaga o `args` (częsta pułapka).** Narzędzie Workflow bywa, że podaje `args` do skryptu
> jako **string JSON**, nie jako gotowy obiekt — wtedy `args.genre` zwróci `undefined`, a puste
> pole wpłynie do promptu każdego agenta (cały rój zwróci „gatunek: undefined” i odmówi pracy).
> Skrypt poniżej parsuje `args` odpornie i **przerywa z błędem**, gdy brakuje gatunku lub
> czytelnika — to celowa bramka wejścia (zasada „fail loud”).

Zasady wbudowane w prompty:
- **rdzeń** (`genre, reader, weird, taboo`) + **opcjonalne zawężenie** (`subgenre, tone,
  protagonist, protAge, protType, format, conventions, form`) wstrzyknięte do `ROLE`/`BRIEF`
  jako miękkie wymagania; przy „dowolny/zróżnicuj" rój nie narzuca persony,
- **suwak dziwności** (`weird` = `bezpieczne`|`smiale`|`dzikie`, domyślnie `smiale`) skaluje
  **twardą bramkę anty-klisza** — im wyżej, tym mocniejszy nacisk na nieoczywistość; ale
  **rzemiosło to zawsze twarda podłoga** (nawet „dzikie" musi dać się napisać),
- **anty-monokultura (dwugałęziowa)**: gdy autor NIE ustalił bohatera — różnorodność profilu
  bohatera (≥3 osie, ≤2 ten sam profil); gdy bohater USTALONY — różnorodność **podejść
  fabularnych** (5 zalążków nie może dzielić jednego szkieletu zdarzeń). Egzekwowana **w prompcie
  syntezy**, bez osobnego agenta-audytora (lekki tryb),
- rola: starszy redaktor do spraw zakupów z 20-letnim doświadczeniem,
- **bez WebSearch i bez agent-browser**: oceny i pomysły opierają się na wiedzy o gatunku
  i rzemiośle, nie na świeżych danych rynkowych (to świadomy kompromis „light" — zaznacz to autorowi),
- **bez osobnej fazy redakcji PL**: zasady polszczyzny (zakaz anglicyzmów i AI-slopu) są wbite
  w `ROLE`, więc proza wraca już czysta; finalny szlif robi obowiązkowy `/unslop:unslop`
  w głównej sesji (patrz `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`),
- proza wraca już po polsku, w polach zgodnych z kształtem `DATA` (patrz `build-and-verify.md`).

```javascript
export const meta = {
  name: 'book-forge-idea-spark',
  description: 'Lekki rój: 5 zaskakująco nieoczywistych fabuł (bramka anty-klisza), ocena świeżości i wykonalności, werdykt — bez WebSearch i bez fazy redakcji',
  phases: [
    { title: 'Pomysly' }, { title: 'Ocena' }, { title: 'Werdykt' },
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
// Rdzeń (ekran 1) + opcjonalne zawężenie (ekran 2). Defaulty miękkie — tylko genre/reader to twarda bramka.
const PROT  = A.protagonist || 'dowolny'   // 'kobieta' | 'mezczyzna' | 'zroznicuj' | 'dowolny'
const PAGE  = A.protAge || ''              // np. '30-45' lub '' (bez preferencji)
const FORMAT= A.format || 'pojedyncza'     // 'pojedyncza' | 'trylogia' | 'seria' | 'doradz'
const TONE  = A.tone || 'dowolny'          // 'mroczny' | 'wywazony' | 'lekki' | 'dowolny'
const SPICE = A.spice || 'dobierz'         // 'lagodny' | 'umiarkowany' | 'explicit' | 'dobierz'
const TABOO = Array.isArray(A.taboo) ? A.taboo : []   // lista no-go (ekran 1)
const SUBG  = A.subgenre || ''            // podgatunek/nurt; '' = bez preferencji
const CONV  = Array.isArray(A.conventions) ? A.conventions : []  // konwencje/obietnice gatunkowe
const FORM  = A.form || ''                // non-fiction: 'poradnik'|'reportaz'|'esej'|'pamietnik'; '' = fikcja
const PTYPE = A.protType || ''            // opcjonalny typ/rola bohatera, np. 'była śledcza'

// Suwak dziwności (ekran 1) — skaluje TWARDĄ BRAMKĘ ANTY-KLISZA. Rzemiosło jest ZAWSZE twardą podłogą.
const WEIRD = (A.weird === 'bezpieczne' || A.weird === 'dzikie') ? A.weird : 'smiale'
const WEIRD_LABEL = WEIRD === 'bezpieczne' ? 'bezpieczne' : WEIRD === 'dzikie' ? 'dzikie' : 'śmiałe'
const ANTYKLISZA = WEIRD === 'bezpieczne'
  ? 'Trzymaj się sprawdzonych, satysfakcjonujących schematów gatunku, ale świeżość znajdź w konkretnym detalu i kącie ujęcia — omijaj najbardziej zgrane klisze.'
  : WEIRD === 'dzikie'
    ? 'TWARDA BRAMKA ANTY-KLISZA: odrzuć wszystko, co czytelnik tego gatunku mógłby przewidzieć. Sięgaj po nieoczywiste zderzenia i wywrócone założenia. ALE każdy pomysł MUSI mieć spójny silnik premisy i dać się z niego napisać książkę — rzemiosło to twarda podłoga, nie zdejmuj jej nawet dla najdzikszego konceptu.'
    : 'TWARDA BRAMKA ANTY-KLISZA: odrzuć 3 pierwsze oczywiste pomysły, które przychodzą do głowy dla tego gatunku — to są klisze. Szukaj nieoczywistego kąta. Klisza = kara, nie pomysł.'

// Linia persony: dla non-fiction (FORM) machineria bohatera nie obowiązuje; inaczej konkret = twarde wymaganie, 'dowolny'/'zroznicuj' = nie narzucaj (lek na monokulturę)
const PERSONA = FORM
  ? `- Forma (non-fiction): ${FORM} — dobierz pomysły do tej formy; machineria różnorodności bohatera NIE dotyczy.`
  : `- Bohater: ${PROT === 'dowolny' ? 'profil dobierasz pod pomysł'
      : PROT === 'zroznicuj' ? 'NIE narzucaj jednego profilu — w 5 pomysłach protagoniści MUSZĄ się różnić wiekiem/płcią/typem'
      : `protagonista to ${PROT}${PAGE ? `, wiek ${PAGE}` : ''}${PTYPE ? `, typ: ${PTYPE}` : ''} — trzymaj się tego we WSZYSTKICH pomysłach`}.`

const BRIEF = `
BRIEF AUTORA (miękkie preferencje — puste pola dobierasz sam):
${PERSONA}
- Format: ${FORMAT} (przy ocenie: ${FORMAT === 'pojedyncza' ? 'oceniaj samodzielny, domknięty łuk; NIE premiuj potencjału serii' : 'uwzględnij potencjał serii i zasiewy międzytomowe'}).
- Ton: ${TONE === 'dowolny' ? 'dobierz pod niszę' : `utrzymaj ton: ${TONE}`}.
- Intensywność (spice/przemoc/groza wg gatunku): ${SPICE === 'dobierz' ? 'typowa dla niszy' : SPICE}.
${CONV.length ? `- Konwencje/obietnice gatunkowe, które pomysły MUSZĄ dowieźć: ${CONV.join(', ')}.` : ''}
${TABOO.length ? `- TABU (NIGDY nie proponuj tych tematów): ${TABOO.join(', ')}.` : ''}`

const ROLE = `Jesteś starszym redaktorem do spraw zakupów z 20-letnim doświadczeniem w wyłapywaniu bestsellerów. Gatunek: ${G}${SUBG ? `, podgatunek/nurt: ${SUBG} (trzymaj się tego nurtu)` : ''}. Docelowy czytelnik: ${R}. Rynek: ${M}. BLOKADA GATUNKU: pracujesz WYŁĄCZNIE w obrębie gatunku ${G}${SUBG ? ` (a konkretnie nurtu ${SUBG})` : ''} i celujesz w czytelnika ${R}. Każdy pomysł MUSI należeć do tego gatunku. NIE używaj WebSearch ani CLI agent-browser — to lekki tryb: pracuj z własnej, aktualnej wiedzy o gatunku, jego konwencjach i czytelniku (${Y}). Nie zmyślaj konkretnych liczb sprzedaży ani cytatów ze źródeł. Pisz po polsku — czystą, naturalną polszczyzną, BEZ anglicyzmów (hook→haczyk, found family→rodzina z wyboru, worldbuilding→świat przedstawiony, plot armor→fabularny immunitet) i BEZ AI-slopu (nadęcia „stanowi/podkreśla", triady, nadmiar myślników); krótkie, konkretne zdania.${BRIEF}`

// --- schematy ---
const POMYSLY = { type:'object', required:['ideas'], properties:{ ideas:{type:'array',items:{
  type:'object',required:['t','en','log','silnik','op','hook','comps','protagonista'],properties:{
    t:{type:'string'},en:{type:'string'},log:{type:'string'},
    silnik:{type:'string'},                 // silnik premisy — strukturalna sprzeczność/pytanie dramatyczne, które samo napędza konflikt
    op:{type:'string'},
    hook:{type:'string'},comps:{type:'array',items:{type:'string'}},
    protagonista:{type:'string'}}}} } }   // profil bohatera, np. "kobieta, ~40, była śledcza" — niesie decyzję dalej (outline/book-bible)
// Ocena: jeden krytyk świeżości na pomysł zwraca 3 wymiary 1-10. Łączną ocenę liczymy deterministycznie w JS (rzemiosło = twarda podłoga), nie ufamy arytmetyce modelu.
const OCENA = { type:'object', required:['breakdown','rationale'], properties:{
  breakdown:{type:'object',required:['swiezosc','silnik','rzemioslo'],properties:{swiezosc:{type:'number'},silnik:{type:'number'},rzemioslo:{type:'number'}}},
  rationale:{type:'string'},strengths:{type:'array',items:{type:'string'}},risks:{type:'array',items:{type:'string'}} } }
const WERDYKT = { type:'object', required:['winnerTitle','rationale','warning','whyNow','nextSteps','runnerTitle','runnerWhy'], properties:{
  winnerTitle:{type:'string'},rationale:{type:'string'},warning:{type:'string'},whyNow:{type:'string'},
  positioning:{type:'string'},nextSteps:{type:'array',items:{type:'string'}},
  runnerTitle:{type:'string'},runnerWhy:{type:'string'} } }

// --- FAZA 1: pomysly (4 generatory + 1 synteza, audyt różnorodności WTOPIONY w syntezę) ---
phase('Pomysly')
// 4 zróżnicowane typy ZALĄŻKA FABUŁY (różne szkielety zdarzeń) × rotowane SOCZEWKI TWÓRCZE
const KATY = [
  'Fabuła startująca od nagłego wydarzenia, które rozbija status quo bohatera (incydent inicjujący z zewnątrz).',
  'Fabuła, w której bohater sam podejmuje decyzję uruchamiającą lawinę (sprawczy wybór, nie wypadek).',
  'Fabuła narastającego śledztwa/odkrywania prawdy — napięcie z tego, co bohater stopniowo poznaje.',
  'Ciemny koń — nieoczywista struktura fabuły, której konkurencja nie odważyłaby się rozegrać.',
]
const SOCZEWKI = [
  'ZDERZENIE DOMEN: wstrzyknij mechanizm z obcej dziedziny (nauka, zawód, rytuał, historia) jako silnik wydarzeń fabuły.',
  'INWERSJA: odwróć układ sił w fabule (kto poluje, kto ucieka, kto wie, kto płaci).',
  'CO JEŚLI: zmień jedno założenie sytuacji startowej i wyciągnij bezlitosne konsekwencje.',
  'IRONIA WBUDOWANA: bohater jest sprawcą własnego problemu (jak „idealna żona, która zaplanowała własne morderstwo”).',
]
// Reguła silnika premisy — dla non-fiction (FORM) reinterpretowana, nie wyłączona
const SILNIK_REGULA = FORM
  ? 'centralne napięcie lub pytanie, które trzyma czytelnika (sprzeczność w temacie, mit do obalenia) — NIE wymuszaj fabularnego konfliktu'
  : 'strukturalna sprzeczność lub ironia, która SAMA generuje konflikt — napięcie wpisane w sytuację startową, nie doklejony z zewnątrz złoczyńca'
const propozycje = (await parallel(KATY.map((a,i)=>()=>
  agent(`${ROLE}\n\n${ANTYKLISZA}\n\nWymyśl KONKRETNĄ, zaskakująco nieoczywistą fabułę dla gatunku ${G}${SUBG?`, nurt ${SUBG}`:''}, celując w czytelnika ${R}.\nTyp zalążka fabuły (framing): ${a}\nSOCZEWKA TWÓRCZA (narzędzie myślowe, nie ozdoba): ${SOCZEWKI[i % SOCZEWKI.length]}\n\n${CONV.length?`Dowieź obietnice gatunkowe: ${CONV.join(', ')}. `:''}Każda fabuła MUSI mieć działający SILNIK PREMISY: ${SILNIK_REGULA}. Zaproponuj 1-2 fabuły. Dla każdej: t (POLSKI roboczy tytuł), en (oryginalny tytuł roboczy po angielsku), log (logline 1 zdanie po polsku), silnik (1-2 zdania — ${SILNIK_REGULA}), op (streszczenie 3-4 zdania po polsku — wydarzenie inicjujące, oś napięcia, kulminacja), hook (haczyk sprzedażowy po polsku, może mieć <b>), comps (3-4 orientacyjne tytuły porównawcze z gatunku — z Twojej wiedzy, nie weryfikuj w sieci), protagonista (zwięzły profil bohatera: płeć, wiek, typ — np. „mężczyzna, ~35, były żołnierz"; ZGODNY z BRIEF AUTORA, gdy autor go ustalił).`,
    {label:`fabula:${i+1}`,phase:'Pomysly',schema:POMYSLY})))).filter(Boolean).flatMap(r=>r.ideas)

// Czy bohater jest USTALONY? Jeśli tak — różnicujemy FABUŁĘ; jeśli nie (dowolny/zróżnicuj) — pilnujemy też profilu bohatera.
// 'zroznicuj' = autor JAWNIE chce różnych bohaterów, więc nigdy nie traktuj go jako ustalonego, nawet gdy przypadkiem przyszedł też protType.
const STALY_BOHATER = PROT === 'zroznicuj' ? false : (PROT === 'kobieta' || PROT === 'mezczyzna' || !!PTYPE)
const DYWERSYFIKACJA = STALY_BOHATER
  ? `Profil bohatera jest USTALONY i wspólny dla wszystkich 5 (bohater: ${PROT}${PAGE?', '+PAGE:''}${PTYPE?', '+PTYPE:''}). RÓŻNICUJ FABUŁĘ: wydarzenie inicjujące, oś konfliktu, strukturę zdarzeń, charakter kulminacji — oraz setting i ton. To 5 wariantów fabuły jednej obsady, nie 5 klonów.`
  : (PROT === 'zroznicuj'
      ? 'Autor zażądał RÓŻNYCH bohaterów — to wymóg twardy: 5 pomysłów MUSI mieć wyraźnie różne profile protagonisty (wiek/płeć/typ), a do tego różne fabuły.'
      : 'Profil bohatera nie jest ustalony — nie więcej niż 2 z 5 mogą dzielić ten sam profil; różnicuj też fabułę i setting.')
const GUARD = STALY_BOHATER
  ? 'GUARD RÓŻNORODNOŚCI FABUŁY: 5 fabuł MUSI różnić się na co najmniej 3 osiach fabularnych (wydarzenie inicjujące, oś konfliktu, struktura zdarzeń, źródło napięcia, charakter kulminacji).'
  : 'GUARD RÓŻNORODNOŚCI: 5 pomysłów MUSI różnić się na co najmniej 3 osiach (profil bohatera, setting, ton, podgatunek, fabuła).'
const finalisci = await agent(
  `${ROLE}\n\n${ANTYKLISZA}\n\nSurowe fabuły zespołu:\n${JSON.stringify(propozycje)}\n\nWybierz 5 NAJ-bardziej nieoczywistych i mocnych, i PODKRĘĆ każdą. PODKRĘCENIE = wyostrz silnik premisy (mocniejsza, czystsza sprzeczność), podnieś stawkę, dodaj jeden nieoczywisty zwrot. ŻELAZNA REGUŁA „WZMACNIAJ, NIE PODMIENIAJ": surowa fabuła musi pozostać rozpoznawalna — wzmacniasz, nie zastępujesz jej inną. ODRZUĆ fabuły banalne lub powielające zgrany schemat gatunku. Dopracuj pola (t, en, log, silnik, op, hook, comps, protagonista). Fabuły mają być wyraziste, świeże i wykonalne.\n\n${GUARD} ${DYWERSYFIKACJA}`,
  {label:'synteza:5fabul',phase:'Pomysly',schema:POMYSLY})
const ideas = finalisci.ideas.slice(0,5)

// --- FAZA 2: ocena (1 krytyk świeżości na pomysł, bez WebSearch) ---
phase('Ocena')
const ocenione = await parallel(ideas.map((idea)=>async()=>{
  const o = await agent(
    `${ROLE}\n\nWcielasz się w KRYTYKA ŚWIEŻOŚCI I RZEMIOSŁA — jedynego sędziego tej fabuły. NIE oceniasz trendów social mediów ani sprzedawalności; oceniasz, czy pomysł jest naprawdę NIEOCZYWISTY i czy da się z niego napisać dobrą książkę gatunku ${G}.\n\nFabuła:\n${JSON.stringify(idea)}\n\nNIE używaj WebSearch ani agent-browser. Wystaw trzy oceny 1-10 (mogą być ułamkowe) w polu breakdown:\n- swiezosc: jak bardzo pomysł odchodzi od oczywistych klisz gatunku (klisza = niska, świeżość = wysoka),\n- silnik: czy SILNIK PREMISY działa — strukturalna sprzeczność SAMA napędza konflikt (doklejony z zewnątrz = niska),\n- rzemioslo: czy z tego DA SIĘ napisać spójną, satysfakcjonującą książkę (to twarda podłoga — najdziksza fabuła bez wykonalności dostaje tu niską ocenę).\nDodaj rationale (1-2 zdania), strengths, risks.`,
    {label:`ocena:${idea.t.slice(0,16)}`,phase:'Ocena',schema:OCENA})
  if (!o) return {...idea, votes:[], avgScore:0}
  const b = o.breakdown || {}
  const sw=Number(b.swiezosc)||0, si=Number(b.silnik)||0, rz=Number(b.rzemioslo)||0
  // świeżość i silnik ważą najwięcej; rzemiosło to TWARDA PODŁOGA: rz<5 dociska łączną ocenę do rz
  let comp = sw*0.4 + si*0.35 + rz*0.25
  if (rz < 5) comp = Math.min(comp, rz)
  return {...idea, votes:[['Świeżość',sw],['Silnik premisy',si],['Rzemiosło',rz]], avgScore:Math.round(comp*10)/10, rationale:o.rationale, strengths:o.strengths, risks:o.risks}
}))
const scoredIdeas = ocenione.filter(Boolean).sort((a,b)=>b.avgScore-a.avgScore)

// --- FAZA 3: werdykt ---
phase('Werdykt')
const WARN_MONO = STALY_BOHATER
  ? 'JEŚLI 5 fabuł jest do siebie zbyt podobnych (ten sam szkielet zdarzeń), ZGŁOŚ to jako ryzyko monokultury fabularnej i wskaż, jakiego rozegrania w stawce zabrakło'
  : 'JEŚLI wszystkie 5 pomysłów dzieli ten sam profil bohatera, ZGŁOŚ to jako ryzyko monokultury i wskaż, czego w stawce zabrakło'
const werdykt = await agent(
  `${ROLE}\n\n5 fabuł z ocenami świeżości:\n${JSON.stringify(scoredIdeas.map(s=>({t:s.t,log:s.log,protagonista:s.protagonista,avgScore:s.avgScore,votes:s.votes})))}\n\nWskaż JEDNĄ fabułę do rozwijania — tę, która najlepiej łączy NIEOCZYWISTOŚĆ z wykonalnością. Podaj: winnerTitle, rationale (dlaczego ta), warning (uczciwe ostrzeżenie o ryzykach — fail loud; ${WARN_MONO}; przypomnij też, że to lekki tryb bez weryfikacji rynkowej — wybór warto potwierdzić pełnym market-report), whyNow (dlaczego teraz), positioning (jak pozycjonować), nextSteps (kroki dla autora), runnerTitle (tytuł wicemistrza), runnerWhy (dlaczego wicemistrz).`,
  {label:'werdykt',phase:'Werdykt',schema:WERDYKT})

return {
  ideas: scoredIdeas,
  winner: werdykt,
  weird: WEIRD_LABEL,
  // Brief autora — dane sterujące (NIE redagowane), dziedziczone przez outline/book-bible przez DATA.brief. Kontrakt IDENTYCZNY z market-report.
  brief: { subgenre: SUBG, conventions: CONV, protagonist: PROT, protAge: PAGE, protType: PTYPE, form: FORM, format: FORMAT, tone: TONE, spice: SPICE, taboo: TABOO, market: M },
}
```

## Po powrocie roju agentów (główna sesja)

1. **Unslop** — wywołaj `/unslop:unslop` i nanieś poprawki na prozę (patrz
   `${CLAUDE_PLUGIN_ROOT}/shared/polish-style.md`). To jedyny przebieg redakcji (faza w roju
   została usunięta, bo proza wraca już po polsku z `ROLE`) — **obowiązkowy**.
2. **Mapowanie do `DATA`** i budowa HTML — `build-and-verify.md`.

## Skalowanie i wariant zapasowy

- Niszowy lub lokalny gatunek → możesz dodać 5. generator (rotacja KATY/SOCZEWKI starczy).
- Brak narzędzia Workflow → odtwórz te same etapy równoległymi agentami `Task` (ta sama
  logika: generuj → oceń → werdykt), wolniej i w kontekście.
- Potrzebujesz twardych danych rynkowych (10 bestsellerów, 3 luki, ocena z WebSearch)?
  To pełny `market-report` (etap 1), nie ten lekki wariant bez badania rynku.
```
