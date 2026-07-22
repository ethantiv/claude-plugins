# Skrypt roju (Workflow) — mocny początek (3 warianty)

Skopiuj do narzędzia **Workflow**. `args`: `{ wyciag, scena, dlugosc }`, gdzie `wyciag` to WYCIĄG z biblii (karta głosu narratora, głosy postaci sceny 1, zasady świata istotne dla scenerii, glosariusz z odmianą, motyw, stawka), a `scena` to obietnica/haczyk pierwszej sceny z konspektu. Nie wklejaj całej biblii — tylko wyciąg.

```javascript
export const meta = {
  name: 'book-forge-opening',
  description: 'Roj pisze 3 warianty pierwszej sceny, ocenia fabularnie, sprawdza ciaglosc, wybiera',
  phases: [ { title: 'Warianty' }, { title: 'Ocena' }, { title: 'Ciaglosc' }, { title: 'Werdykt' } ],
}

// Workflow bywa, że podaje `args` jako string JSON, nie jako obiekt — parsuj odpornie
let A
try { A = typeof args === 'string' ? JSON.parse(args) : (args || {}) }
catch (e) { throw new Error('args podane jako string, ale to nie poprawny JSON ('+e.message+'). Przekaż obiekt albo poprawny JSON.') }
const W = A.wyciag, SC = A.scena, DL = A.dlugosc || '300-400 słów'

// Kontrakt narracji wyłuskany z wyciągu — POV/czas jako jawne, nienaruszalne wymaganie (nie tylko „trzymaj się karty głosu")
const POVK = `${(W.glos_narratora&&W.glos_narratora.pov)||(W.meta&&W.meta.pov)||''}`.trim()
const CZASK = `${(W.glos_narratora&&W.glos_narratora.czas)||(W.meta&&W.meta.czas)||''}`.trim()
const KONTRAKT = (POVK||CZASK) ? `\n\nKONTRAKT NARRACJI (zafiksowany — NIE łam): tryb/POV: ${POVK||'jak w karcie głosu'}; czas gramatyczny: ${CZASK||'jak w karcie głosu'}. Pozostań w głowie fokalizatora — ZERO head-hoppingu (nie wchodź do myśli innych postaci).` : ''

const ROLE = `Jesteś powieściopisarzem piszącym w GŁOSIE Z BIBLII (narrator + idiolekty postaci), nie we własnym. Trzymaj się ściśle: karta głosu, zasady świata, nazwy własne i ich odmiana z glosariusza. Pisz po polsku, immersyjnie: pokazuj nie mów, konkret sensoryczny, dialog z podtekstem, świat dawkowany przez akcję. Dialog zapisuj polską interpunkcją dialogową (pauza „— ”, didaskalia małą literą — patrz shared/polish-style.md). Bez wstrzykiwanych anegdot, bez zwrotów do czytelnika, bez wymuszonego cliffhangera — haczyk wynika ze sceny.${KONTRAKT} WYCIĄG Z BIBLII:\n${JSON.stringify(W)}\n\nPierwsza scena (z konspektu): ${SC}`

const TECHNIKI = [
  { key:'filmowa', nazwa:'Filmowa scena', opis:'Wejście w środek akcji (in medias res). Ruch, konkret sensoryczny, napięcie od pierwszego zdania. Zero ekspozycji na wejściu.' },
  { key:'zdanie', nazwa:'Mocne zdanie otwierające', opis:'Prowokacyjne, intrygujące zdanie narratora lub bohatera, z którego naturalnie wynika scena. Nie oderwany aforyzm.' },
  { key:'spowiedz', nazwa:'Intymna spowiedź bohatera', opis:'Bliski, pierwszoosobowy lub głęboko ograniczony głos, który od razu buduje więź. Spowiedź w roli postaci, nie autora.' },
]

const VAR = { type:'object', required:['key','text','hook','words'], properties:{
  key:{type:'string'}, text:{type:'string'}, hook:{type:'string'}, words:{type:'number'} } }
const CRIT = { type:'object', required:['key','scores','verdict'], properties:{
  key:{type:'string'},
  scores:{type:'object',required:['hook','glos','immersja','pov','tempo','idiolekty','sensoryka'],properties:{hook:{type:'number'},glos:{type:'number'},immersja:{type:'number'},pov:{type:'number'},tempo:{type:'number'},idiolekty:{type:'number'},sensoryka:{type:'number'}}},
  mocne:{type:'array',items:{type:'string'}}, slabe:{type:'array',items:{type:'string'}}, verdict:{type:'string'} } }
const CONT = { type:'object', required:['key','ok'], properties:{
  key:{type:'string'}, ok:{type:'boolean'}, konflikty:{type:'array',items:{type:'string'}} } }
const WERD = { type:'object', required:['recommended','uzasadnienie'], properties:{
  recommended:{type:'string'}, uzasadnienie:{type:'string'}, jak_polaczyc:{type:'string'} } }

phase('Warianty')
const warianty = (await parallel(TECHNIKI.map(t=>()=>
  agent(`${ROLE}\n\nTECHNIKA OTWARCIA: ${t.nazwa} — ${t.opis}\n\nNapisz pełną pierwszą scenę tą techniką, ${DL}. Zakończ obietnicą/haczykiem, który ciągnie dalej. Zwróć: key="${t.key}", text (proza, akapity oddzielone pustą linią), hook (zdanie-obietnica), words (liczba słów).`,
    {label:`wariant:${t.key}`,phase:'Warianty',schema:VAR})))).filter(Boolean)

phase('Ocena')
// niezalezny krytyk: czyta TYLKO wyciag z biblii + tekst wariantu (nie wie, jak powstal)
const oceny = (await parallel(warianty.map(v=>()=>
  agent(`Jesteś bezlitosnym redaktorem prowadzącym. „Nie bądź miły, bądź użyteczny.” Oceń TEN wariant pierwszej sceny wyłącznie na podstawie tekstu i wyciągu z biblii.\n\nWYCIĄG:\n${JSON.stringify(W)}\n\nTEKST:\n${v.text}\n\nOceń 1-5: hook (siła pierwszych zdań), glos (spójność z kartą głosu), immersja (pokazuj-nie-mów, brak info-dumpu), pov (wierność POV/czasowi, brak head-hoppingu), tempo, idiolekty (rozróżnialność głosów — gdy mówi >1 postać, czy brzmią różnie; przy jednej postaci oceń wyrazistość głosu narratora), sensoryka (konkret zmysłowy zakotwiczony w świecie, nie ogólniki). Podaj mocne, słabe, verdict PASS|FIX. key="${v.key}".`,
    {label:`ocena:${v.key}`,phase:'Ocena',schema:CRIT})))).filter(Boolean)

phase('Ciaglosc')
const ciaglosc = (await parallel(warianty.map(v=>()=>
  agent(`Jesteś strażnikiem kanonu. Porównaj wariant z biblią i wskaż SPRZECZNOŚCI (nazwy i ich odmiana, opisy postaci, zasady świata, POV/czas). Nie poprawiaj — raportuj.\n\nWYCIĄG Z BIBLII:\n${JSON.stringify(W)}\n\nTEKST:\n${v.text}\n\nZwróć key="${v.key}", ok (true gdy brak sprzeczności), konflikty (lista).`,
    {label:`ciaglosc:${v.key}`,phase:'Ciaglosc',schema:CONT})))).filter(Boolean)

phase('Werdykt')
// Ranking wstępny liczony DETERMINISTYCZNIE z ocen (suma) z preferencją wariantów czystych w ciągłości —
// kotwiczy redaktora naczelnego, żeby nie wskazał słabego wariantu wbrew ocenom.
const suma = (s) => Object.values(s || {}).reduce((a, b) => a + (+b || 0), 0)
const ranking = oceny.map(o => {
  const c = ciaglosc.find(x => x.key === o.key) || {}
  return { key: o.key, suma: suma(o.scores), ciaglosc_ok: c.ok !== false }
}).sort((a, b) => (b.ciaglosc_ok - a.ciaglosc_ok) || (b.suma - a.suma))
const najlepszy = ranking[0] || {}
const wszystkieSlabe = oceny.length > 0 && oceny.every(o => suma(o.scores) < 25)  // 7 wymiarów × <3.6 śr. ⇒ słaba stawka

const werdykt = await agent(
  `Jesteś redaktorem naczelnym. Na podstawie ocen i kontroli ciągłości wskaż, który wariant pierwszej sceny rozwijać i dlaczego; jeśli warto, zaproponuj, jak połączyć ich mocne strony.\n\nRANKING WSTĘPNY (z sum ocen, czyste w ciągłości wyżej) — domyślnie wybierz czołowy, odejdź od niego tylko z wyraźnym uzasadnieniem:\n${JSON.stringify(ranking)}\n\nOCENY:\n${JSON.stringify(oceny)}\n\nCIĄGŁOŚĆ:\n${JSON.stringify(ciaglosc)}\n\n${wszystkieSlabe?'UWAGA (fail loud): wszystkie warianty są słabe — zaznacz to w uzasadnieniu i zaleć autorowi ponowne otwarcie zamiast rozwijania któregokolwiek.\n\n':''}Zwróć recommended (key), uzasadnienie, jak_polaczyc.`,
  {label:'werdykt',phase:'Werdykt',schema:WERD})

return {
  variants: warianty.map(v=>{
    const o=oceny.find(x=>x.key===v.key)||{}, c=ciaglosc.find(x=>x.key===v.key)||{}
    const t=TECHNIKI.find(x=>x.key===v.key)||{}
    return { ...v, nazwa:t.nazwa, opis_techniki:t.opis, critique:o, ciaglosc:c, recommended:false }
  }),
  werdykt,
}
```

## Po powrocie roju (główna sesja)

1. **Unslop NAJPIERW** (`/unslop:unslop`) na prozie wariantów, zakotwiczony kartą stylu z biblii; **potem** korekta polonistyczna + walidacja nazw z glosariusza.
2. Oznacz `recommended:true` na wariancie z `werdykt.recommended`.
3. Budowa HTML + `.book-forge/poczatek.md` (rekomendowany wariant) — `build-and-verify.md`.
4. Zaproponuj autorowi dopisy RUNTIME do biblii (nowe nazwy/fakty) — zapis dopiero po potwierdzeniu.

## Fallback
Brak Workflow → te same fazy równoległymi agentami `Task` (warianty → ocena → ciągłość → werdykt).
