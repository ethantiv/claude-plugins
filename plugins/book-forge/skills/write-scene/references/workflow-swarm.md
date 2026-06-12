# Skrypt roju (Workflow) — napisz scenę

Skopiuj do narzędzia **Workflow**. `args`: `{ scena, wyciag, prev, dlugosc, prozaZrodlo }`, gdzie `scena` to karta sceny z biblii (id, pov, miejsce, czas, cel, konflikt, zwrot, value, luk, zasiewa, splaca), `wyciag` to WYCIĄG z biblii (karta głosu narratora, głosy obecnych postaci, zasady świata istotne, glosariusz z odmianą, otwarte zasiewy), `prev` to streszczenia 2–3 poprzednich scen, a `prozaZrodlo` to **treść** pliku otwarcia (gdy karta ma `proza_zrodlo` lub to scena 1 z `.book-forge/poczatek.md` — patrz Krok 1 SKILL.md). Nie wklejaj całej biblii ani całego dotychczasowego tekstu — tylko wyciąg i streszczenia.

```javascript
export const meta = {
  name: 'book-forge-write-scene',
  description: 'Roj: plan sceny -> draft (2 warianty) -> wybor -> adherencja -> redakcja PL -> propozycje do kanonu',
  phases: [ { title: 'Plan sceny' }, { title: 'Draft' }, { title: 'Wybor' }, { title: 'Adherencja' }, { title: 'Redakcja PL' }, { title: 'Propozycje' } ],
}

// Workflow bywa, że podaje `args` jako string JSON, nie jako obiekt — parsuj odpornie
let A
try { A = typeof args === 'string' ? JSON.parse(args) : (args || {}) }
catch (e) { throw new Error('args podane jako string, ale to nie poprawny JSON ('+e.message+'). Przekaż obiekt albo poprawny JSON.') }
const SC = A.scena, W = A.wyciag, PREV = A.prev || [], DL = A.dlugosc || '800-1500 słów'
const PZ = A.prozaZrodlo || ''   // tekst .book-forge/poczatek.md, gdy karta sceny ma proza_zrodlo (scena otwierająca)

// Kontrakt narracji jako jawne, nienaruszalne wymaganie (nie tylko „trzymaj się POV z biblii")
const POVK = `${SC.pov || (W.glos_narratora&&W.glos_narratora.pov) || ''}`.trim()
const CZASK = `${(W.glos_narratora&&W.glos_narratora.czas) || (W.meta&&W.meta.czas) || ''}`.trim()
const KONTRAKT = `\n\nKONTRAKT NARRACJI (zafiksowany — NIE łam): POV: ${POVK||'jak w karcie .book-forge/sceny/głosu'}; czas gramatyczny: ${CZASK||'jak w karcie głosu'}. Pozostań w głowie fokalizatora POV — ZERO head-hoppingu (nie wchodź do myśli innych postaci).`
// Zasiewy z karty sceny jako TWARDE zadanie (nie giną w ogólnym JSON karty)
const ZAS = `${(SC.zasiewa&&SC.zasiewa.length)?`\n- ZASIEJ w tej scenie (z karty): ${SC.zasiewa.join(', ')}.`:''}${(SC.splaca&&SC.splaca.length)?`\n- SPŁAĆ w tej scenie (z karty): ${SC.splaca.join(', ')}.`:''}`
const ZADANIA = ZAS ? `\n\nZADANIA SCENY (obowiązkowe):${ZAS}` : ''
const OTWARCIE = PZ ? `\n\nMATERIAŁ OTWARCIA (proza z etapu opening) — to scena otwierająca: ROZWIŃ poniższy tekst do docelowej długości, ZACHOWUJĄC jego pierwsze akapity, obrazy i głos. NIE pisz sceny od zera, nie podmieniaj otwarcia:\n${PZ}` : ''

const ROLE = `Jesteś powieściopisarzem piszącym w USTALONYM głosie z biblii — głosie narratora i idiolektach postaci, nie we własnym. Trzymaj się ściśle: POV i czas z biblii, karta głosu, zasady świata, nazwy własne i ich odmiana z glosariusza. Pisz immersyjnie: pokazuj nie mów, konkret sensoryczny, dialog z podtekstem, świat dawkowany przez akcję. Dialog zapisuj polską interpunkcją dialogową (pauza „— ”, didaskalia małą literą — patrz shared/polish-style.md). Bez „głosu autora”, bez osobistych anegdot, bez zwrotów do czytelnika, bez „stop and think”, bez wymuszonego cliffhangera — haczyk i napięcie wynikają ze sceny. Pisz po polsku (słownik z polish-style).${KONTRAKT}${ZADANIA}${OTWARCIE}\n\nWYCIĄG Z BIBLII:\n${JSON.stringify(W)}\n\nKARTA SCENY:\n${JSON.stringify(SC)}\n\nCO BYŁO WCZEŚNIEJ (streszczenia poprzednich scen):\n${JSON.stringify(PREV)}`

const PLAN = { type:'object', required:['mikrobeaty','wejscie','wyjscie'], properties:{
  mikrobeaty:{type:'array',items:{type:'string'}}, wejscie:{type:'string'}, wyjscie:{type:'string'}, uwagi_glos:{type:'string'} } }
const DRAFT = { type:'object', required:['text','words'], properties:{ text:{type:'string'}, words:{type:'number'} } }
const ADHER = { type:'object', required:['pov_ok','glos_ok','glosy_rozroznialne','sensoryka_ok','nazwy_ok','cel_realizowany','zwrot_obecny','value_shift_ok','zasiewy_zrealizowane'], properties:{
  pov_ok:{type:'boolean'},                 // zgodny POV/czas, brak head-hoppingu
  glos_ok:{type:'boolean'},
  glosy_rozroznialne:{type:'boolean'},     // idiolekty: postacie mówią różnie (gdy >1 mówiąca)
  sensoryka_ok:{type:'boolean'},           // konkret zmysłowy, nie ogólniki
  nazwy_ok:{type:'boolean'}, cel_realizowany:{type:'boolean'},
  zwrot_obecny:{type:'boolean'}, value_shift_ok:{type:'boolean'},
  zasiewy_zrealizowane:{type:'boolean'},   // zasiewy/payoffy z karty faktycznie obecne w prozie
  otwarcie_zachowane:{type:'boolean'},     // (gdy scena ma proza_zrodlo) pierwsze akapity to rozwinięcie, nie podmiana
  naprawic:{type:'array',items:{type:'string'}} } }
const PROP = { type:'object', required:['fakty','nazwy','stan','zasiewy_dotkniete'], properties:{
  fakty:{type:'array',items:{type:'object',required:['tresc','typ'],properties:{tresc:{type:'string'},typ:{type:'string'}}}},
  nazwy:{type:'array',items:{type:'object',required:['nazwa'],properties:{nazwa:{type:'string'},kategoria:{type:'string'}}}},
  stan:{type:'array',items:{type:'object',required:['postac','zmiana'],properties:{postac:{type:'string'},zmiana:{type:'string'}}}},
  zasiewy_dotkniete:{type:'array',items:{type:'string'}} } }

phase('Plan sceny')
const plan = await agent(
  `${ROLE}\n\nZaplanuj tę scenę: rozpisz mikrobeaty (jak realizuje cel → konflikt → zwrot), na czym scena się zaczyna (wejscie) i kończy (wyjscie, ze zmianą wartości), oraz uwagi o głosie postaci obecnych w scenie. Bez pisania prozy.`,
  {label:'plan-sceny',phase:'Plan sceny',schema:PLAN})

phase('Draft')
const NACISK = [
  'Połóż nacisk na podtekst dialogu i relacje — to, co postacie przemilczają.',
  'Połóż nacisk na sensorykę, ruch i napięcie fizyczne sceny.',
]
const drafty = (await parallel(NACISK.map((n,i)=>()=>
  agent(`${ROLE}\n\nPlan sceny:\n${JSON.stringify(plan)}\n\n${n}\n\nNapisz pełną scenę (${DL}). Realizuj cel, konflikt i zwrot z karty; zachowaj POV/czas i głos. Zwróć text i words.`,
    {label:`draft:${i+1}`,phase:'Draft',schema:DRAFT})))).filter(Boolean)

phase('Wybor')
const wybrany = drafty.length>1 ? await agent(
  `${ROLE}\n\nDwa warianty tej samej sceny:\n${JSON.stringify(drafty)}\n\nWybierz mocniejszy lub połącz ich atuty w jeden spójny draft (jeden głos, jedno tempo). Zwróć text i words.`,
  {label:'wybor',phase:'Wybor',schema:DRAFT}) : drafty[0]

phase('Adherencja')
// niezalezny sprawdzajacy: czyta karte sceny + wyciag + tekst (nie wie, jak powstal)
const adher = await agent(
  `Jesteś redaktorem pilnującym zgodności sceny z planem i biblią. Sprawdź TEN tekst wobec karty sceny i wyciągu z biblii.\n\nKARTA SCENY:\n${JSON.stringify(SC)}\n\nWYCIĄG:\n${JSON.stringify(W)}\n\nTEKST:\n${wybrany.text}\n\nOceń (true/false): pov_ok (zgodny POV/czas, brak head-hoppingu — narracja tylko w głowie fokalizatora), glos_ok (zgodny z kartą głosu), glosy_rozroznialne (gdy mówi >1 postać — czy idiolekty są różne; przy jednej postaci ⇒ true), sensoryka_ok (konkret zmysłowy zakotwiczony w świecie, nie ogólniki), nazwy_ok (nazwy i odmiana z glosariusza), cel_realizowany, zwrot_obecny, value_shift_ok (wartość naprawdę się zmienia), zasiewy_zrealizowane (zasiewy/payoffy z pól ZADANIA SCENY faktycznie obecne — true, gdy karta ich nie wymaga)${PZ?', otwarcie_zachowane (pierwsze akapity to ROZWINIĘCIE materiału otwarcia, nie napisana od zera podmiana)':''}. Wypisz naprawic[] (konkretne usterki, w tym brakujące zasiewy${PZ?' i porzucone otwarcie':''}) — pusta lista, gdy wszystko gra.`,
  {label:'adherencja',phase:'Adherencja',schema:ADHER})

let final = wybrany
if (adher.naprawic && adher.naprawic.length) {
  final = await agent(
    `${ROLE}\n\nTekst sceny:\n${wybrany.text}\n\nUsterki do naprawienia (zgodność z kartą/biblią):\n${JSON.stringify(adher.naprawic)}\n\nPopraw scenę zachowując jej zalety; nie dopisuj nowych zdarzeń poza karta sceny. Zwróć text i words.`,
    {label:'rewizja',phase:'Adherencja',schema:DRAFT})
}

phase('Redakcja PL')
const red = await agent(
  `Jesteś redaktorem języka polskiego. Wyczyść tekst sceny: usuń anglicyzmy i kalki, AI-slop, popraw interpunkcję dialogową (myślnik, nie cudzysłów angielski), zadbaj o aspekt czasowników i naturalny szyk. NIE wygładzaj „pod humanizer” (to później) i NIE ruszaj nazw własnych z glosariusza ani zdarzeń. Zwróć text i words.\n\nTEKST:\n${final.text}`,
  {label:'redakcja-pl',phase:'Redakcja PL',schema:DRAFT})
// guard: przyjmij redakcję tylko, gdy zwróciła pełnoprawny tekst (nie skrót/halucynację)
if (red && red.text && red.text.length >= final.text.length * 0.7) final = red

phase('Propozycje')
const prop = await agent(
  `${ROLE}\n\nNa podstawie napisanej sceny wyodrębnij PROPOZYCJE dopisów do kanonu (do zatwierdzenia przez kontrolę ciągłości — NIE zapisuj sam): fakty (nowe ustalenia świat/postać/relacja/zdarzenie), nazwy (nowe nazwy własne do glosariusza z kategorią), stan (zmiany stanu/lokalizacji/relacji postaci), zasiewy_dotkniete (id zasiewów zasianych lub spłaconych w tej scenie).\n\nTEKST:\n${final.text}`,
  {label:'propozycje',phase:'Propozycje',schema:PROP})

return { id: SC.id, text: final.text, words: final.words, adherencja: adher, propozycje: prop }
```

## Po powrocie roju (główna sesja)

1. **Bez humanizera** na tym etapie (kolejność redakcji — patrz `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md`).
2. Zapisz `.book-forge/sceny/<id>.md` (sama proza). Obiekt `propozycje` z roju trzymaj w pamięci — **nie** zapisuj pliku propozycji ani kanonu `.book-forge/biblia/`. Szczegóły: `build-and-verify.md`.
3. **Handoff:** uruchom `/book-forge:continuity-check` dla `<id>`, przekazując `propozycje` jako wejście bramki (to ona zapisuje do biblii i pyta autora o konflikty RO).
4. Pokaż autorowi długość, wynik adherencji i werdykt bramki ciągłości.

## Fallback
Brak Workflow → te same fazy równoległymi agentami `Task` (plan → 2 drafty → wybór → adherencja → redakcja → propozycje).
