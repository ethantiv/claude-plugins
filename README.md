# claude-plugins

Publiczny **marketplace wtyczek do [Claude Code](https://claude.com/claude-code)**. Dodajesz go raz, a potem instalujesz wtyczki jedną komendą — działają w terminalu, aplikacji desktopowej i rozszerzeniach IDE.

## Wtyczki

| Wtyczka | Język | Co robi |
| --- | --- | --- |
| **book-forge** | polski | Kompletny, 12-etapowy pipeline do pisania powieści rojem agentów: od luki rynkowej i pomysłu, przez konspekt i „biblię książki", po pisanie, redakcję i pakiet wydawniczy. Każdy etap kończy obowiązkowa redakcja na naturalną polszczyznę (anty-AI-slop). |
| **babysit-pr** | uniwersalna | Lokalny odpowiednik `autofix-pr`: monitoruje bieżący pull request i naprawia go w sesji Claude Code — błędy CI, komentarze z review proszące o zmiany i konflikty scalania. |

## Instalacja

W sesji Claude Code uruchom komendy (`/plugin` to wbudowana komenda Claude Code):

```text
/plugin marketplace add ethantiv/claude-plugins
/plugin install book-forge@claude-plugins
/plugin install babysit-pr@claude-plugins
```

Albo z terminala, przez CLI:

```bash
claude plugin marketplace add ethantiv/claude-plugins
claude plugin install book-forge@claude-plugins
claude plugin install babysit-pr@claude-plugins
```

Instaluj tylko to, czego potrzebujesz — wtyczki są od siebie niezależne. Po instalacji sprawdź stan:

```bash
claude plugin marketplace list
```

### Aktualizacje

Marketplace jest dodawany przez `git clone`, więc wtyczki aktualizują się przy odświeżeniu marketplace'u — nie wymagają ponownej instalacji:

```bash
claude plugin marketplace update claude-plugins
```

## Wymagania

Obie wtyczki potrzebują działającego Claude Code. Dodatkowo:

**book-forge**
- **Python 3** — tylko biblioteka standardowa (bez `pip install`).
- **Node.js** — walidacja generowanych artefaktów HTML (`node --check`).
- Narzędzie **Workflow** (rój agentów); bez niego skille mają zapasowe wywołanie agentów `Task`.
- Skill **`/humanizer:humanizer`** — obowiązkowy przebieg redakcji językowej.
- CLI **agent-browser** (`npm i -g agent-browser && agent-browser install`) — research i weryfikacja realiów.

**babysit-pr**
- **`gh`** (GitHub CLI, zalogowane), **`jq`**, **`git`** — dostępne w `PATH`.

## Użycie

Po instalacji każda wtyczka udostępnia swoje skille jako komendy `/<wtyczka>:<skill>`.

- **book-forge** — pełny pipeline opisany w [`plugins/book-forge/README.md`](plugins/book-forge/README.md); wizualny przewodnik po 12 etapach: [`przewodnik.html`](plugins/book-forge/przewodnik.html). Start: `/book-forge:market-report` (lub lekki `/book-forge:idea-spark`).
- **babysit-pr** — wywołaj `/babysit-pr` na gałęzi z otwartym PR, by monitorować i naprawiać CI/review/konflikty lokalnie.

## Licencja

[MIT](LICENSE) — możesz swobodnie używać, modyfikować i rozpowszechniać.
