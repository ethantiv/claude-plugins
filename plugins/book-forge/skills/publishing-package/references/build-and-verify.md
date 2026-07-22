# Budowa pakietu i walidacja

Dwa rezultaty: `pakiet.md` (wszystkie komponenty) i `pakiet-<slug>.html` (interaktywny widok ze szablonu `${CLAUDE_PLUGIN_ROOT}/skills/publishing-package/assets/package-template.html`). `<slug>` z tytułu (małe litery, bez znaków diakrytycznych, spacje → „-”).

## DATA dla HTML

```javascript
const DATA = {
  meta: { title:"", en:"", genre:"", words:0, target:"" },
  logline: "", pitch: "", blurb: "",
  synopsis: "",   // 1-2 strony, z zakończeniem (akapity oddzielone pustą linią)
  query: "",      // list do agenta; pola bio/kontakt zostawione do uzupełnienia
  comps: [ {tytul:"", dla_czytelnikow:""} ],
  uwagi: []
};
```

`meta.words` z `ksiazka.md`; reszta z wyniku roju (po unslopie). Placeholdery `{{TITLE}}`, `{{GENRE}}`; wstrzyknięcie jak w pozostałych szablonach — `DATA` zapisz jako plik JSON i wstrzyknij przez `json.dumps` (wzorzec w `outline-to-scenes`/`market-report`).

## Format `pakiet.md`

Sekcje pod nagłówkami: Logline, Elevator pitch, Opis z okładki (bez spoilerów), Synopsis (z zakończeniem), List do agenta, Tytuły porównawcze (każdy jako „dla czytelników …”), Metadane (gatunek, liczba słów, grupa docelowa). W liście zostaw widoczne pola `[Bio autora — do uzupełnienia]` i `[Dane kontaktowe — do uzupełnienia]`.

## Walidacja (obowiązkowa)

```bash
python3 -c "import re,sys;s=open('$OUT').read();m=re.findall(r'<script[^>]*>(.*?)</script>',s,re.S);open('/tmp/pk.js','w').write('\n;\n'.join(m)) if m else sys.exit('BŁĄD: brak <script> w '+'$OUT')"
node --check /tmp/pk.js && echo "JS OK"
agent-browser open "file://$PWD/$OUT"
agent-browser eval "JSON.stringify({comps:document.querySelectorAll('#comps .comp').length, title:document.querySelector('h1').innerText, sekcje:document.querySelectorAll('.panel').length})"
```

Sprawdź ręcznie:
- **Tytuły porównawcze** każdy ujęty jako „dla czytelników X i Y” — żadnego „w stylu autora Z”.
- **Opis z okładki** nie zdradza zakończenia; **synopsis** je zawiera.
- **Brak zmyślonych** nagród/sprzedaży/cytatów; bio i kontakt to pola do uzupełnienia.
- **Język** naturalny, bez anglicyzmów (po unslopie i redakcji).

To finalny etap pipeline'u — po nim autor ma maszynopis (`ksiazka.md`) i komplet materiałów do wysyłki.
