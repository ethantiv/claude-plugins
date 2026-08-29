# Polish officialese and heaviness patterns

Load this file when the target text contains Polish. These patterns cover Polish-specific slop the main catalog does not: bureaucratic phrasing, nominalizations, impersonal fog, and grammatical heaviness typical of both AI-generated and officialese Polish. The "Keep" guards and the register restraint below apply to the unslop pass; `/unslop:plain` deliberately overrides them, since its whole job is the register change.

## Cluster rule (overrides everything below)

These are cluster-sensitive signals, not absolute bans. One `kluczowy`, one triad, one passive sentence proves nothing — a competent human writes all of these occasionally. Act when several items cluster in a passage, and check each pattern's "keep" guard before editing. When in doubt, leave the sentence alone; a false positive that flattens correct formal Polish is worse than a missed hit.

## Officialese

Watchlist and plain replacements:

- `niniejszy` → `ten`
- `w celu` / `celem` → `aby`, `żeby`
- `w dniu dzisiejszym` → `dzisiaj`
- `w miesiącu maju` → `w maju`
- `dokonać zakupu` → `kupić`; `dokonać zgłoszenia` → `zgłosić` (any `dokonać` + noun → the plain verb)
- `ulec poprawie` / `ulec pogorszeniu` → `poprawić się` / `pogorszyć się`
- `posiadać możliwość` → `może`
- `w związku z powyższym` → `dlatego`
- `w zakresie` / `w ramach` / `z uwagi na` → rephrase with a plain preposition or drop

Keep: statutory phrases, document names, definitions, and required procedural language in legal or official text — there `niniejsza umowa` is a term, not slop.

## Nominalizations

Signals: verbal nouns in `-anie`, `-enie`, `-cie` carrying the action — `przeprowadzenie analizy`, `podjęcie decyzji`, `wdrożenie rozwiązania`, `zapewnienie możliwości`.

Fix: actor plus finite verb — `przeprowadzenie analizy danych` → `zespół przeanalizował dane`; `podjęcie decyzji nastąpiło` → `rada zdecydowała`.

Keep: terms of art, legal labels, official procedure names, scientific terms, and headings where the noun form is natural.

## Passive and impersonal fog

Watchlist: `zostało wykonane`, `jest realizowane`, `dokonano`, `ustalono`, `przyjęto`, `wskazano`, `należy`, `powinno się`, `można zauważyć`.

Fix: name the actor when it is known and useful — `zostało opracowane narzędzie` → `zespół opracował narzędzie`; in instructions address the reader — `należy złożyć wniosek` → `złóż wniosek` (only where the register already allows direct address; unslopping never informalizes).

Keep: legal text, official notices, academic methods sections, and cases where the actor is unknown or irrelevant.

## Genitive chains

Signals: stacked nouns in the genitive with unclear relations — `w przypadku braku możliwości uruchomienia pojazdu`.

Fix: convert the chain into a clause — `jeśli nie można uruchomić pojazdu`; `analiza wyników badania satysfakcji klientów` → `analiza tego, jak klienci ocenili usługę`.

## Participial heaviness

Watchlist: `mając na uwadze`, `biorąc pod uwagę`, `uwzględniając`, `dotyczący`, `obejmujący`, `stanowiący`, `umożliwiający`, `pozwalający`.

Fix: shorter clauses with a finite verb — `system umożliwiający generowanie raportów` → `system, który generuje raporty` or `system generuje raporty`.

Keep: single participles that read naturally; the problem is stacking, not the form itself.

---

Patterns adapted from [miodkuj](https://github.com/bartekpucek/miodkuj) by Bartek Pucek (MIT).
