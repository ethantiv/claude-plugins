# Skrypt roju (Workflow) — rewizja sceny (pętla pogłębienie → dev-edit)

Skopiuj do narzędzia **Workflow**. `args`: `{ proza, scena, wyciag, maxRund }`, gdzie `proza` to wersja robocza z `.book-forge/sceny/<id>.md`, `scena` to karta sceny, `wyciag` to wyciąg z biblii (głos narratora, stawka, łuk, świat przedstawiony, glosariusz, **`postacie` z polem `chaos` obecnych postaci** i **`meta.forma`** — zasilają fazę Disruption). Krytyk dostaje tylko kartę sceny, wyciąg i tekst — nigdy notatek pogłębiającego.

```javascript
export const meta = {
  name: 'book-forge-revise-scene',
  description: 'Petla: poglebienie proza -> dev-edit na slepo (PASS/FIX) -> kolejna runda; limit iteracji',
  phases: [ { title: 'Rewizja' }, { title: 'Disruption' }, { title: 'Redakcja PL' }, { title: 'Propozycje' } ],
}

// Workflow bywa, że podaje `args` jako string JSON, nie jako obiekt — parsuj odpornie
let A
try { A = typeof args === 'string' ? JSON.parse(args) : (args || {}) }
catch (e) { throw new Error('args podane jako string, ale to nie poprawny JSON ('+e.message+'). Przekaż obiekt albo poprawny JSON.') }
const SC = A.scena, W = A.wyciag, MAX = A.maxRund || 3
let proza = A.proza

const ROLE_DEEP = `Jesteś powieściopisarzem POGŁĘBIAJĄCYM scenę środkami PROZY (nie wstawkami). Wzmacniaj: podtekst dialogu (co postać przemilcza), charakteryzacja przez działanie, detal sensoryczny osadzony w świecie, mowa pozornie zależna, podniesienie stawki, mikro-zwrot, zasiew Czechowowskiej strzelby. ZERO anegdot, statystyk, zwrotów do czytelnika, dydaktyzmu. Trzymaj POV/czas i głos z biblii, nazwy z glosariusza. Nie dopisuj zdarzeń poza karta sceny. WYCIĄG:\n${JSON.stringify(W)}\n\nKARTA SCENY:\n${JSON.stringify(SC)}`

const TYP = SC.typ || 'kluczowa'   // pomostowa = przejście/oddech: nie wymaga pełnego celu/zwrotu, liczy się zwięzłość i funkcja
const ROLE_EDIT = `Jesteś redaktorem prowadzącym (developmental editor). „Nie bądź miły, bądź użyteczny.” Oceniasz scenę WYŁĄCZNIE na podstawie karty sceny, wyciągu z biblii i samego tekstu — nie wiesz, co i jak zostało dopisane. Kryteria FABULARNE (nie eseistyczne). TYP SCENY: ${TYP}${TYP==='pomostowa'?' — to scena POMOSTOWA: nie wymagaj pełnego zwrotu wartości ani silnej stawki; oceniaj zwięzłość, funkcję przejścia i to, czy nie puchnie (ekonomia).':''}`

const DEEP = { type:'object', required:['text','words'], properties:{ text:{type:'string'}, words:{type:'number'}, co_wzmocniono:{type:'array',items:{type:'string'}} } }
const EDIT = { type:'object', required:['verdict','scores','top_fixy'], properties:{
  verdict:{type:'string'},
  scores:{type:'object',required:['cel_zwrot','stawka','agency','podtekst','pov','show_tell','tempo','jezyk','ekonomia'],properties:{
    cel_zwrot:{type:'number'},stawka:{type:'number'},agency:{type:'number'},podtekst:{type:'number'},
    pov:{type:'number'},show_tell:{type:'number'},tempo:{type:'number'},jezyk:{type:'number'},
    ekonomia:{type:'number'}}},   // czy scena nie puchnie — pogłębienie systematycznie dodaje słowa
  top_fixy:{type:'array',items:{type:'string'}}, uwagi:{type:'array',items:{type:'string'}} } }
const PROP = { type:'object', required:['fakty','nazwy','zasiewy_dotkniete'], properties:{
  fakty:{type:'array',items:{type:'object',properties:{tresc:{type:'string'},typ:{type:'string'}}}},
  nazwy:{type:'array',items:{type:'object',properties:{nazwa:{type:'string'},kategoria:{type:'string'}}}},
  zasiewy_dotkniete:{type:'array',items:{type:'string'}} } }
const DISR = { type:'object', required:['text','operacje','celowe_odstepstwa'], properties:{
  text:{type:'string'}, operacje:{type:'array',items:{type:'string'}},
  celowe_odstepstwa:{type:'array',items:{type:'string'}} } }   // fragmenty chronione przed korektą/unslopem w polish-pl

phase('Rewizja')
// Werdykt liczymy DETERMINISTYCZNIE z ocen (nie ufamy polu `verdict` od agenta — inaczej ta sama
// scena raz dostaje PASS, raz FIX). Bramka, która może nie odrzucić niczego, nie jest bramką.
// Wymiary krytyczne PASS zależą od typu sceny: pomost nie jest karany za brak pełnego celu/zwrotu i agency.
const KRYT = TYP === 'pomostowa' ? ['pov', 'jezyk'] : ['cel_zwrot', 'pov', 'agency', 'podtekst']
const sumaScores = (s) => Object.values(s || {}).reduce((a, b) => a + (+b || 0), 0)
const liczPass = (s) => KRYT.every(k => (+s[k] || 0) >= 4) && Object.values(s).every(v => (+v || 0) >= 3)

const rundy = []
let verdict = 'FIX', fixy = [], passProza = null
let best = { proza, suma: -1, runda: 0 }   // najlepszy dotąd wariant wg sumy ocen
for (let r = 1; r <= MAX; r++) {
  const deep = await agent(
    `${ROLE_DEEP}\n\nTekst do pogłębienia:\n${proza}\n${fixy.length?('\nUwagi z poprzedniej redakcji do naprawienia:\n'+JSON.stringify(fixy)):''}\n\nZwróć pogłębiony text, words i co_wzmocniono.`,
    {label:`poglebienie:r${r}`,phase:'Rewizja',schema:DEEP})
  proza = deep.text
  const edit = await agent(
    `${ROLE_EDIT}\n\nKARTA SCENY:\n${JSON.stringify(SC)}\n\nWYCIĄG Z BIBLII:\n${JSON.stringify(W)}\n\nTEKST:\n${proza}\n\nOceń 1-5: cel_zwrot, stawka, agency (bohater działa, nie tylko reaguje), podtekst, pov (spójność POV/czasu), show_tell (pokazuj nie mów, brak info-dumpu), tempo, jezyk (mocne czasowniki, brak klisz/wypełniaczy), ekonomia (czy scena NIE jest rozwlekła — pogłębienie kusi, by dodawać; nadmiar = niska ocena, nawet jeśli reszta dobra). Podaj też orientacyjny verdict PASS|FIX (ostateczny liczymy z ocen), top_fixy (maks. 3 najważniejsze) i uwagi.`,
    {label:`dev-edit:r${r}`,phase:'Rewizja',schema:EDIT})
  const pass = liczPass(edit.scores), suma = sumaScores(edit.scores)
  verdict = pass ? 'PASS' : 'FIX'
  rundy.push({ runda:r, verdict, suma, scores:edit.scores, top_fixy:edit.top_fixy })
  if (suma > best.suma) best = { proza, suma, runda: r }
  if (pass) { passProza = proza; break }
  fixy = edit.top_fixy || []
  if (r >= 2 && suma < best.suma) { rundy[rundy.length - 1].regres = true; break }  // pętla się cofa — przerwij, weź najlepszą
}
// Zwróć NAJLEPSZĄ wersję wg ocen (gdy PASS — wersję, która przeszła bramkę), nie ostatnią.
proza = passProza || best.proza
const dlug = verdict !== 'PASS' ? `accept-with-debt (najlepsza runda ${best.runda}/${MAX})` : null

// --- Disruption: anty-przewidywalność na ZAAKCEPTOWANEJ prozie (poza zasięgiem dev-edit, który ukarałby
// celową szorstkość). Wyłączona dla non-fiction. Korzysta z profilu chaosu postaci z biblii. ---
phase('Disruption')
const FORMA = (W.meta && W.meta.forma) || ''
const CHAOS = (W.postacie || []).map(p => (p && p.chaos) ? { imie: p.imie, chaos: p.chaos } : null).filter(Boolean)
let celowe_odstepstwa = []
if (!FORMA) {
  const disr = await agent(
    `Jesteś redaktorem anty-przewidywalności. Tekst jest poprawny — Twoim zadaniem jest USUNĄĆ jego gładką sztuczność, NIE „poprawiać”. Wykonaj 2-4 operacje (więcej, im bardziej tekst jest przewidywalny):\n- wstrzyknij JEDNĄ nieistotną myśl z obsesji postaci (z profilu chaosu, bez uzasadnienia — postać nie reflektuje, czemu o tym myśli);\n- w jednym miejscu złam nadmierną kontrolę emocji (postać próbuje opanować i jej się NIE udaje — drobno, bez melodramatu, bez autorefleksji);\n- zostaw jedno celowo chropawe, niegładkie zdanie (poprawne gramatycznie, ale rytmicznie niewygodne);\n- zaszum najczystszy, „najbardziej pisany” dialog (przerwania, powtórzenia, odpowiedzi obok pytania) ALBO usuń najbardziej przewidywalny akapit lub jego puentę.\nNIE ruszaj zdarzeń, POV/czasu ani nazw z glosariusza. Zwróć text, operacje (co zrobiłeś) oraz celowe_odstepstwa[] — krótkie cytaty fragmentów, których późniejsza korekta i unslop NIE mają „naprawiać”.${CHAOS.length?`\n\nPROFILE CHAOSU OBECNYCH POSTACI:\n${JSON.stringify(CHAOS)}`:''}\n\nTEKST:\n${proza}`,
    {label:'disruption',phase:'Disruption',schema:DISR})
  if (disr && disr.text && disr.text.length >= proza.length * 0.6) proza = disr.text
  celowe_odstepstwa = (disr && disr.celowe_odstepstwa) || []
}

phase('Redakcja PL')
const red = await agent(
  `Jesteś redaktorem języka polskiego. Lekka korekta: anglicyzmy/kalki, AI-slop, interpunkcja dialogowa (myślnik), aspekt, szyk. NIE wygładzaj „pod unslop” i nie ruszaj nazw własnych ani zdarzeń.${celowe_odstepstwa.length?` CHRONIONE ODSTĘPSTWA (NIE naprawiaj — to celowa szorstkość z fazy disruption; wolno tylko poprawić ewidentny błąd ortografii/odmiany nazwy): ${JSON.stringify(celowe_odstepstwa)}.`:''} Zwróć text i words.\n\n${proza}`,
  {label:'redakcja-pl',phase:'Redakcja PL',schema:DEEP})
if (red && red.text) proza = red.text

phase('Propozycje')
const prop = await agent(
  `${ROLE_DEEP}\n\nNa podstawie pogłębionej sceny wyodrębnij NOWE propozycje do kanonu (do zatwierdzenia przez kontrolę ciągłości — NIE zapisuj): fakty, nazwy (z kategorią), zasiewy_dotkniete. Jeśli pogłębienie nic nie dodało, zwróć puste listy.\n\nTEKST:\n${proza}`,
  {label:'propozycje',phase:'Propozycje',schema:PROP})

return { id: SC.id, text: proza, verdict, dlug, rundy, celowe_odstepstwa, propozycje: prop }
```

## Po powrocie roju (główna sesja)

1. **Bez unslopa** (kolejność redakcji — `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md`).
2. Nadpisz `.book-forge/sceny/<id>.md` (opcjonalnie kopia `.book-forge/sceny/<id>.v1.md`). Zapisz `.book-forge/sceny/<id>.qa.md` (werdykt, oceny, zapis rund, dług). Obiekt `propozycje` z roju trzymaj w pamięci — **nie** zapisuj pliku propozycji ani kanonu `.book-forge/biblia/`. Szczegóły: `build-and-verify.md`.
3. **Handoff:** uruchom `/book-forge:continuity-check` dla `<id>`, przekazując `propozycje` jako wejście bramki (to ona zapisuje do biblii i pyta autora o konflikty RO).
4. Pokaż autorowi werdykt, liczbę rund, ewentualny dług i werdykt bramki ciągłości.

## Wariant zapasowy
Brak Workflow → ta sama pętla agentami `Task`: na zmianę agent pogłębiający i osobny agent-krytyk (na ślepo), aż do werdyktu PASS lub wyczerpania limitu.
