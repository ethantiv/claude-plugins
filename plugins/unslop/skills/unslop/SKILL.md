---
name: unslop
description: >-
  This skill should be used when the user asks to "unslop" a document, "remove AI slop", "fix AI-generated text", "make this sound human", "remove signs of AI writing", "humanize this text", "this reads like ChatGPT", "usuń AI-slop", "odslopuj", "popraw tekst po LLM", "zredaguj tekst wygenerowany przez AI", "ten tekst brzmi jak AI", or wants a document edited according to Wikipedia's "Signs of AI writing". Edits Polish and English documents in place.
argument-hint: "<file path(s) to fix, or a directory>"
allowed-tools: Read, Edit, Grep, Glob
---

# unslop — remove signs of AI writing

Edit the document(s) in `$ARGUMENTS` **in place**, removing the telltale signs of AI-generated writing catalogued by Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). Preserve the meaning, the facts, and the order of the argument; change only wording, style, and formatting.

## Workflow

1. **Resolve targets.** `$ARGUMENTS` may hold one or more file paths (any text format) or a directory (take its `.md` and `.txt` files). Empty → if another skill loaded this one as an editing pass, or a drafting task is already in progress in the conversation, skip the workflow and apply the pattern catalog below to all prose produced from that point on; otherwise ask in one sentence which file to fix — don't guess.
2. **Read each file whole** (long files in sequential chunks) and detect its language. Apply the shared patterns below plus the matching vocabulary table. For mixed-language files, apply each language's rules to its own passages.
3. **Fix with surgical `Edit` calls** — sentence-level replacements, not a wholesale rewrite. The author's voice and structure stay; the slop goes.
4. **Summarize in chat** when done: per file, fix counts for the main categories touched and one or two before → after examples. Write the summary in the conversation language.

Hard rules:

- **Never invent facts.** Slop like "experts argue" is fixed by deleting or hedging honestly ("this is unverified"), never by fabricating a source, number, or name. If a vague claim carries real weight, leave it and flag it in the summary.
- **Don't touch:** code blocks and inline code, URLs, quoted material, proper names, YAML frontmatter keys, data in tables. Match the file's existing quote style (straight vs typographic) instead of imposing one.
- **Keep the register.** Formal stays formal, casual stays casual — unslopping is not informalizing.
- **Prefer deletion over substitution.** Most slop sentences add nothing; the best fix is usually cutting, not rephrasing. The document should get shorter.
- **Preserve document structure** (heading hierarchy, section order), except where the structure itself is a slop pattern listed below.

## Structural patterns (any language)

1. **Inflated significance.** "stands as a testament", "pivotal moment", "underscores its enduring legacy" / "stanowi świadectwo", "kluczowy moment", "odcisnęło trwały ślad" → state the plain fact; cut the grandeur.
2. **Negative parallelisms.** "not just X, but Y", "It's not about X — it's about Y" / "to nie tylko X, ale (także) Y", "nie chodzi o X, chodzi o Y" → keep the half that matters, drop the scaffolding.
3. **Rule of three.** Forced triads of adjectives, phrases, or examples ("fast, reliable, and scalable") → keep the one or two that carry real information.
4. **Superficial participle analyses.** Trailing "-ing" clauses attributing unsupported significance: "…, highlighting the importance of…", "…, ensuring long-term success" / "…, podkreślając znaczenie…", "…, co pokazuje, jak ważne…" → delete, or turn into a concrete supported claim.
5. **Vague attributions.** "Experts argue", "Industry reports suggest", "Some critics note" / "Eksperci wskazują", "Wielu obserwatorów uważa", "Branżowe raporty sugerują" → name the actual source or drop the claim (see the never-invent rule).
6. **Promotional tone.** "vibrant", "nestled", "rich heritage", "must-see" / "tętniący życiem", "malowniczo położony", "bogate dziedzictwo" → neutral description; a document is not a brochure.
7. **Formulaic endings.** "Challenges and Future Prospects" sections, "Despite these challenges…", hollow-optimism closers / "Podsumowując, …", "Przyszłość rysuje się obiecująco" → end when the content ends; delete conclusions that only restate.
8. **Copula avoidance.** "serves as", "functions as", "boasts", "features" / "stanowi", "pełni funkcję", "może poszczycić się", "oferuje" (for mere possession) → plain "is" / "has" ("jest" / "ma").
9. **Elegant variation.** Cycling synonyms for one referent (the city → the metropolis → the urban hub) → repeat the ordinary word; repetition is fine.
10. **Chat artifacts.** "I hope this helps", "Let's dive in", "Certainly!", knowledge-cutoff disclaimers, "As an AI…", leftover placeholders ("[insert X]") / "Mam nadzieję, że to pomoże", "Zanurzmy się" → delete outright.

## Formatting patterns

- **Bold overuse** — mechanical bolding of "key terms" throughout prose → unbold; keep at most genuinely load-bearing emphasis.
- **List-itis** — bullet lists of `**Header:** description` where flowing prose belongs → merge into sentences; keep lists only for genuinely enumerable items.
- **Em-dash overuse** — more than an occasional `—` → commas, periods, or parentheses. In Polish use the en dash (–) sparingly and correctly.
- **Emoji as decoration** — 🚀 in headings or bullets of a serious document → remove.
- **Title Case Headings** in English documents → sentence case (match the file's dominant convention if it already has one).
- **Skipped heading levels** (H2 → H4) → restore the hierarchy.
- **Horizontal rules before headings** → remove; the heading is the break.
- **Tables for prose** — tables holding sentences instead of data → convert to prose.

## AI vocabulary

Replace with the plain equivalent, or delete the phrase when it carries no content. A single occurrence can be innocent — density is the signal; when several of these cluster, rewrite the passage.

**English:** delve, tapestry, landscape (figurative), testament, pivotal, crucial, vibrant, showcase, underscore, highlight (verb, figurative), leverage, robust, seamless, foster, garner, boast, intricate, interplay, comprehensive, holistic, transformative, game-changer, cutting-edge, "it's important to note", "in today's fast-paced world", sentence-starting "Additionally," / "Moreover," / "Furthermore," in long chains.

**Polish:** kluczowy, istotny (nadużywane), niezwykle, innowacyjny, kompleksowy, holistyczny, dynamiczny rozwój, szeroko pojęty, "w dzisiejszym świecie", "w dobie…", "warto podkreślić / zauważyć", "należy zaznaczyć", "co więcej" / "ponadto" w łańcuchach, "niewątpliwie" / "bez wątpienia", "krajobraz" (przenośnie: medialny, biznesowy), "serce miasta", "prawdziwa gratka", "pełni kluczową rolę", "w kontekście" (jako wytrych), "swoisty", "niejako".

## Success check

Re-read each edited file once after the pass. It should read like a competent human wrote it: varied sentence rhythm, plain verbs, no pattern from the lists above left in bulk, and no changed meaning. If a paragraph still smells like AI but no listed pattern matches, apply the general test — does the sentence say something a knowledgeable human would bother to write? If not, cut it.
