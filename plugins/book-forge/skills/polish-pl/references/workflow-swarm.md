# Skrypt roju agentów (Workflow) — korekta PL + walidacja nazw

Uruchamiany na **tekście PO unslopie** (unslop uruchamia się wcześniej, w głównej sesji). `args`: `{ proza, karta_stylu, glosariusz, celowe_odstepstwa }`, gdzie `proza` to scena po unslopie, `karta_stylu` to karta głosu narratora z biblii, `glosariusz` to nazwy własne z odmianą i wariantami zakazanymi, a `celowe_odstepstwa` to lista fragmentów z fazy Disruption (revise-scene), których korekta NIE ma wygładzać.

```javascript
export const meta = {
  name: 'book-forge-polish-pl',
  description: 'Korekta polonistyczna na tekscie po unslopie + walidacja nazw z glosariusza',
  phases: [ { title: 'Korekta PL' }, { title: 'Kontrola' }, { title: 'Walidacja nazw' } ],
}

// Workflow bywa, że podaje `args` jako string JSON, nie jako obiekt — parsuj odpornie
let A
try { A = typeof args === 'string' ? JSON.parse(args) : (args || {}) }
catch (e) { throw new Error('args podane jako string, ale to nie poprawny JSON ('+e.message+'). Przekaż obiekt albo poprawny JSON.') }
const STYL = A.karta_stylu, GLOS = A.glosariusz || []
const ODST = Array.isArray(A.celowe_odstepstwa) ? A.celowe_odstepstwa : []   // chronione fragmenty z fazy Disruption
let proza = A.proza

const OCHRONA = ODST.length ? `\n\nCHRONIONE ODSTĘPSTWA (z fazy disruption — to CELOWA szorstkość/zaburzenie; NIE wygładzaj ich, NIE „naprawiaj” rytmu ani składni; wolno tylko poprawić ewidentny błąd ortografii lub odmianę nazwy własnej): ${JSON.stringify(ODST)}.` : ''
const ROLE = `Jesteś korektorem i redaktorem języka polskiego z uchem do prozy. Pracujesz na tekście, który właśnie przeszedł przez unslop (narzędzie oparte na ANGIELSKICH wzorcach), więc twoim zadaniem jest naprawić to, co unslop mógł zepsuć, i doprowadzić tekst do naturalnej, poprawnej polszczyzny. Zachowaj rejestr i rytm z karty stylu. KARTA STYLU/GŁOSU:\n${JSON.stringify(STYL)}${OCHRONA}`

const KOREKTA = { type:'object', required:['text','zmiany'], properties:{
  text:{type:'string'}, words:{type:'number'},
  zmiany:{type:'array',items:{type:'object',required:['kategoria','przyklad'],properties:{kategoria:{type:'string'},przyklad:{type:'string'}}}},
  nowe_aiizmy:{type:'array',items:{type:'string'}} } }
const NAZWY = { type:'object', required:['text','przywrocone'], properties:{
  text:{type:'string'},
  przywrocone:{type:'array',items:{type:'object',required:['bylo','jest'],properties:{bylo:{type:'string'},jest:{type:'string'}}}},
  uwagi:{type:'array',items:{type:'string'}} } }

phase('Korekta PL')
const kor = await agent(
  `${ROLE}\n\nPopraw tekst: (1) INTERPUNKCJA DIALOGOWA PO POLSKU (nie cudzysłów angielski) — twarde reguły: każda kwestia od nowego akapitu zaczyna się od pauzy „— ” (U+2014) i spacji; didaskalia z czasownikiem mowy po pauzie i MAŁĄ literą („— Nie pójdę — powiedziała.”, „— Już?! — krzyknął.”); gdy po kwestii jest samodzielne zdanie narracji BEZ czasownika mowy — kwestię domknij kropką, narrację od WIELKIEJ litery („— Nie pójdę. — Odwróciła się do okna.”); wtrącenie w środku kwestii: „— Wejdź — rzucił — i zamknij drzwi.”; akapit na każdą zmianę mówiącego; myśli kursywą/cudzysłowem, bez pauzy. (2) aspekt czasowników (dok./niedok.); (3) naturalny szyk (usuń kalkowany SVO, nadmiar zaimków ja/mój); (4) eliminacja kalk składniowych i AI-izmów (np. „wydaje się być” → „wydaje się”, „w oparciu o” → „na podstawie”); (5) redukcja przysłówków przy czasownikach mowienia („powiedział cicho” → mocniejszy czasownik lub akcja). NIE zmieniaj zdarzeń ani nazw własnych. Zwróć text, words, zmiany (kategorie z przykładem) i nowe_aiizmy (wykryte do czarnej listy).\n\nTEKST:\n${proza}`,
  {label:'korekta-pl',phase:'Korekta PL',schema:KOREKTA})
proza = kor.text

phase('Kontrola')
const kon = await agent(
  `${ROLE}\n\nNiezależna kontrola: przeczytaj tekst świeżym okiem i wyłap resztki — anglicyzmy, kalki, sztywne zdania, miejsca, gdzie zgubiono rejestr z karty stylu. Popraw je zachowując sens i zdarzenia. Zwróć text, words, zmiany (co jeszcze poprawiono), nowe_aiizmy.\n\nTEKST:\n${proza}`,
  {label:'kontrola',phase:'Kontrola',schema:KOREKTA})
if (kon && kon.text) proza = kon.text

phase('Walidacja nazw')
const naz = await agent(
  `Jesteś redaktorem nazewnictwa. Sprawdź każdą nazwę własną w tekście wobec glosariusza i przywróć poprawną formę/odmianę, jeśli unslop lub korekta ją zmieniły. Pilnuj wariantów zakazanych. NIE zmieniaj niczego poza nazwami.\n\nGLOSARIUSZ:\n${JSON.stringify(GLOS)}\n\nTEKST:\n${proza}\n\nZwróć text (z poprawnymi nazwami), przywrocone (lista bylo→jest) i uwagi.`,
  {label:'walidacja-nazw',phase:'Walidacja nazw',schema:NAZWY})
if (naz && naz.text) proza = naz.text

return {
  text: proza,
  zmiany: [...(kor.zmiany||[]), ...(kon&&kon.zmiany||[])],
  nowe_aiizmy: [...new Set([...(kor.nowe_aiizmy||[]), ...(kon&&kon.nowe_aiizmy||[])])],
  przywrocone_nazwy: (naz&&naz.przywrocone)||[],
}
```

## Przed rojem agentów (główna sesja): unslop NAJPIERW

Zanim uruchomisz ten rój agentów, uruchom `/unslop:unslop` na surowej (po `continuity-check`) prozie sceny — z poleceniem: zachowaj rejestr z karty stylu, nie ruszaj nazw z glosariusza, zachowaj polską interpunkcję dialogową i przecinek dziesiętny. **Jeśli istnieje `.book-forge/sceny/<id>.qa.md` z listą `celowe_odstepstwa` (z fazy Disruption), dołącz ją do polecenia unslopa: te fragmenty to celowa szorstkość — nie wygładzaj ich.** Dopiero wynik unslopa podaj jako `args.proza` (a `celowe_odstepstwa` przekaż też do `args`).

## Po powrocie roju agentów

1. Nadpisz `.book-forge/sceny/<id>.md` wygładzoną wersją (opcjonalnie kopia `.book-forge/sceny/<id>.v2.md`).
2. Zapisz `.book-forge/korekta-<id>.md` (kategorie zmian, przywrócone nazwy, propozycje AI-izmów do czarnej listy w `polish-style.md` — autor decyduje o dopisaniu).
3. Pokaż autorowi podsumowanie. Szczegóły: `build-and-verify.md`.

## Postępowanie awaryjne
Brak Workflow → korektor i walidator nazw jako agenty `Task` (po unslopie w głównej sesji).
