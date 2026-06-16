# Skrypt roju (Workflow) — biblia książki

Skopiuj do narzędzia **Workflow**. `args`: `{ idea, genre, reader, pov, czas, subgenre, tomy, form, outline, existing }`, gdzie `idea` to zwycięski pomysł z etapu 1, `form` to forma z briefu (`''` = fikcja; `poradnik`/`reportaz`/`esej`/`pamietnik` = non-fiction — wyłącza profil chaosu postaci), `outline` to streszczenie konspektu, a `existing` to już istniejąca biblia (lub null przy pierwszym uruchomieniu — idempotencja). Kształt zwracanego obiektu odpowiada `${CLAUDE_PLUGIN_ROOT}/shared/biblia-spec.md`.

```javascript
export const meta = {
  name: 'book-forge-bible',
  description: 'Roj buduje biblie: swiat, postacie, glosy, glosariusz, kanon, motyw + synteza spojnosci',
  phases: [ { title: 'Sekcje' }, { title: 'Synteza spojnosci' } ],
}

// Workflow bywa, że podaje `args` jako string JSON, nie jako obiekt — parsuj odpornie
let A
try { A = typeof args === 'string' ? JSON.parse(args) : (args || {}) }
catch (e) { throw new Error('args podane jako string, ale to nie poprawny JSON ('+e.message+'). Przekaż obiekt albo poprawny JSON.') }
const I = A.idea, G = A.genre, R = A.reader
const POV = A.pov || 'trzecioosobowa ograniczona', CZAS = A.czas || 'przeszły'
const SUB = A.subgenre || G, TOMY = A.tomy || 1
const FORM = A.form || ''   // non-fiction: poradnik/reportaz/esej/pamietnik; '' = fikcja (guard profilu chaosu)
const OUT = A.outline || '', EX = A.existing || null

const SERIA = TOMY > 1 ? `\nTo SERIA ${TOMY}-tomowa: projektuj łuki postaci i zasiewy z rozpiętością wielotomową (co domyka się w tomie 1, co dojrzewa w kolejnych — spójnie z luk_nadrzedny/zasiewy_miedzytomowe z seria.md), a zasady świata tak, by uniosły całą serię, nie jeden tom.` : ''
const ROLE = `Jesteś showrunnerem powieści i strażnikiem kanonu. Gatunek: ${G} (${SUB}). Czytelnik: ${R}. POV: ${POV}, czas: ${CZAS}. Pomysł: ${JSON.stringify(I)}. Konspekt (skrót): ${OUT}. Buduj świat logiczny i spójny; nazwy własne podawaj z PEŁNĄ polską odmianą. Gdy trzeba zweryfikować twardy filar świata, użyj WebSearch/agent-browser (lekko, tylko fundamenty). Pisz po polsku — czystą, naturalną polszczyzną, BEZ anglicyzmów (hook→haczyk, found family→rodzina z wyboru, worldbuilding→świat przedstawiony) i BEZ AI-slopu (nadęcia „stanowi/podkreśla", triady, nadmiar myślników); krótkie, konkretne zdania, cudzysłowy „ ". NIE ruszaj nazw własnych z glosariusza ani ich odmiany.${SERIA}${EX ? '\\nISTNIEJĄCA BIBLIA (pola RO traktuj jako ustalone, tylko uzupełniaj braki):\\n'+JSON.stringify(EX) : ''}`

// schematy sekcji (skrocone; rozszerz pola wg biblia-spec.md)
const S_SWIAT = { type:'object', required:['lokacje','zasady'], properties:{
  lokacje:{type:'array',items:{type:'object',properties:{nazwa:{type:'string'},opis:{type:'string'}}}},
  zasady:{type:'array',items:{type:'object',required:['zasada','koszt','ograniczenie'],properties:{zasada:{type:'string'},koszt:{type:'string'},ograniczenie:{type:'string'}}}},
  technologia:{type:'array',items:{type:'string'}}, konsekwencje:{type:'string'} } }
const S_POST = { type:'object', required:['postacie','antagonista','stawka'], properties:{
  postacie:{type:'array',items:{type:'object',required:['imie','rola','want','need','rana','klamstwo','luk'],properties:{
    imie:{type:'string'},odmiana:{type:'string'},rola:{type:'string'},opis_fizyczny:{type:'string'},maniery:{type:'string'},
    want:{type:'string'},need:{type:'string'},rana:{type:'string'},klamstwo:{type:'string'},luk:{type:'string'},relacje:{type:'array',items:{type:'string'}},glos_ref:{type:'string'},
    chaos:{type:'object',properties:{obsesja:{type:'string'},znieksztalcenie:{type:'string'},wspomnienie:{type:'string'},kontrola:{type:'string'}}}}}},  // opcjonalne markery nieprzewidywalności (pomijane dla non-fiction); konsumuje je Disruptor w revise-scene
  antagonista:{type:'object',required:['profil','cel','motywacja','plan'],properties:{profil:{type:'string'},cel:{type:'string'},motywacja:{type:'string'},plan:{type:'array',items:{type:'string'}},przewaga:{type:'string'}}},
  stawka:{type:'object',required:['osobista','globalna'],properties:{osobista:{type:'string'},globalna:{type:'string'},zegar:{type:'string'}}} } }
const S_GLOS = { type:'object', required:['glos_narratora','glosy_postaci'], properties:{
  glos_narratora:{type:'object',required:['pov','czas','rytm','rejestr'],properties:{pov:{type:'string'},czas:{type:'string'},rytm:{type:'string'},rejestr:{type:'string'},zwroty:{type:'array',items:{type:'string'}},metafory:{type:'string'},czego_unikac:{type:'array',items:{type:'string'}}}},
  glosy_postaci:{type:'array',items:{type:'object',required:['postac','rejestr','tiki'],properties:{postac:{type:'string'},rejestr:{type:'string'},tiki:{type:'array',items:{type:'string'}},rytm:{type:'string'},slownictwo:{type:'string'}}}} } }
const S_GLOSAR = { type:'object', required:['glosariusz'], properties:{ glosariusz:{type:'array',items:{
  type:'object',required:['nazwa','kategoria','odmiana'],properties:{nazwa:{type:'string'},kategoria:{type:'string'},
  odmiana:{type:'object',properties:{M:{type:'string'},D:{type:'string'},C:{type:'string'},B:{type:'string'},N:{type:'string'},Ms:{type:'string'},W:{type:'string'}}},
  warianty_zakazane:{type:'array',items:{type:'string'}},opis:{type:'string'}}}} } }
const S_TEMAT = { type:'object', required:['temat','pytanie_dramatyczne','motywy'], properties:{
  temat:{type:'string'},pytanie_dramatyczne:{type:'string'},motywy:{type:'array',items:{type:'string'}} } }

phase('Sekcje')
const [swiat, post, glos, glosar, temat] = await parallel([
  ()=>agent(`${ROLE}\n\nROLA: architekt świata. Zbuduj sekcję ŚWIAT: lokacje, zasady (KAŻDA z kosztem i ograniczeniem — co niemożliwe i czemu), technologia, konsekwencje.`,{label:'swiat',phase:'Sekcje',schema:S_SWIAT}),
  ()=>agent(`${ROLE}\n\nROLA: twórca postaci. Zbuduj POSTACIE (want/need/rana/kłamstwo/łuk, opis fizyczny, relacje, odmiana imienia), ANTAGONISTĘ (cel, motywacja „ma rację z własnej perspektywy”, plan, przewaga) i STAWKĘ (osobista, globalna, zegar).${FORM ? '' : ' Dla KAŻDEJ ważnej postaci dodaj `chaos` — cztery markery ludzkiej nieprzewidywalności: obsesja (nieistotna dla fabuły fiksacja, która wraca bez uzasadnienia), znieksztalcenie (codzienne zniekształcenie poznawcze: katastrofizacja, czarno-białe myślenie, czytanie w myślach), wspomnienie (konkretne, zmysłowe, niechciane wspomnienie wracające w złych momentach), kontrola (typowy moment, gdy postać próbuje opanować emocję i jej się to nie udaje). Skaluj gatunkiem: literatura piękna — bogato i wszystkie cztery; proza komercyjna — 2-3 najmocniejsze; te markery to materiał dla późniejszej fazy anty-przewidywalności (Disruptor).'}`,{label:'postacie',phase:'Sekcje',schema:S_POST}),
  ()=>agent(`${ROLE}\n\nROLA: projektant głosów. Zbuduj GŁOS NARRATORA (pov, czas, rytm, rejestr, charakterystyczne zwroty, typ metafor, czego unikać) oraz osobne GŁOSY POSTACI (idiolekty: rejestr, 3-5 tików językowych, rytm, słownictwo).`,{label:'glosy',phase:'Sekcje',schema:S_GLOS}),
  ()=>agent(`${ROLE}\n\nROLA: redaktor nazewnictwa. Zbuduj GLOSARIUSZ nazw własnych: dla każdej nazwa kanoniczna, kategoria, PEŁNA polska odmiana przez 7 przypadków, warianty zakazane, krótki opis.`,{label:'glosariusz',phase:'Sekcje',schema:S_GLOSAR}),
  ()=>agent(`${ROLE}\n\nROLA: strażnik motywu. Zbuduj TEMAT: czym powieść „jest pod spodem”, pytanie dramatyczne książki, powracające motywy/obrazy.`,{label:'temat',phase:'Sekcje',schema:S_TEMAT}),
])

phase('Synteza spojnosci')
const spojna = await agent(
  `${ROLE}\n\nZebrane sekcje:\nŚWIAT:${JSON.stringify(swiat)}\nPOSTACIE:${JSON.stringify(post)}\nGŁOSY:${JSON.stringify(glos)}\nGLOSARIUSZ:${JSON.stringify(glosar)}\nTEMAT:${JSON.stringify(temat)}\n\nROLA: strażnik kanonu. Scal w spójną całość, usuń sprzeczności (np. zasada świata kontra plan antagonisty), upewnij się, że każda nazwa z postaci/świata jest w glosariuszu z odmianą, a każda postać ma łuk. Zwróć finalne, scalone sekcje.`,
  {label:'synteza-spojnosci',phase:'Synteza spojnosci',
   schema:{type:'object',required:['swiat','postacie','antagonista','stawka','glos_narratora','glosy_postaci','glosariusz','temat'],properties:{
     swiat:S_SWIAT.properties?S_SWIAT:{type:'object'}, postacie:{type:'array'}, antagonista:{type:'object'}, stawka:{type:'object'},
     glos_narratora:{type:'object'}, glosy_postaci:{type:'array'}, glosariusz:{type:'array'}, temat:{type:'object'}}}})

// Redakcja PL nie jest osobną fazą roju — zasady polszczyzny są w ROLE (proza wraca czysta);
// finalny szlif robi obowiązkowy /humanizer:humanizer w głównej sesji (patrz „Po powrocie roju").
return spojna
```

## Po powrocie roju (główna sesja)

1. **Humanizer** na partiach opisowych (`/humanizer:humanizer`), z pominięciem nazw własnych. To **jedyny** przebieg redakcji (osobna faza w roju została usunięta — proza wraca po polsku z `ROLE`).
2. **Złożenie kanonu-wiki** przez `${CLAUDE_PLUGIN_ROOT}/scripts/bible.py` (`write_section`/`write_entity` dla sekcji RO + `write_scene_grid` z beatami/scenami z konspektu; sekcje RUNTIME `os_czasu`/`setup_payoff`/`fakty`/`log_ciaglosci` zostają puste) i **`render_index()`**. Na koniec dopisz wpis ingestu do kroniki: `append_log({"werdykt":"INGEST","decyzja":"Zbudowano kanon z pomysl.json + konspekt.md: N postaci, M zasad świata, K haseł glosariusza"})` (operacja „ingest" wzorca LLM-wiki — patrz `build-and-verify.md`). Szczegóły: `build-and-verify.md`.

## Wariant awaryjny
Brak narzędzia Workflow → te same role jako równoległe agenty `Task`, potem synteza.
