---
name: plain
description: >-
  This skill should be used when the user asks to simplify a Polish text into plain language: "uprość ten tekst", "napisz prościej", "prosty język", "przetłumacz z urzędniczego na ludzki", "uprość ten urzędowy tekst", "simplify this Polish text", "rewrite in plain Polish". Deliberately changes the register of public-facing, instructional, civic, or UX Polish from bureaucratic to plain. Edits files in place.
argument-hint: "<file path(s) to simplify, or a directory>"
allowed-tools: Read, Edit, Glob
---

# plain — prosty język for Polish documents

Rewrite the Polish document(s) in `$ARGUMENTS` **in place** into plain language (prosty język): the register deliberately shifts from bureaucratic or heavy to direct and reader-first. This is the opposite contract to `/unslop:unslop`, which preserves the register — use this skill only when the user explicitly wants simplification.

## Workflow

1. **Resolve targets.** `$ARGUMENTS` may hold one or more file paths or a directory (expand with `Glob` patterns `**/*.md` and `**/*.txt`; other extensions inside a directory are skipped — name them explicitly to include them). Empty → take the file the user points at in their message; if none, ask in one sentence which file to simplify.
2. **Read each file whole** and identify its job and reader. Then `Read` `${CLAUDE_PLUGIN_ROOT}/skills/unslop/references/polish-patterns.md` — its officialese, nominalization, passive-fog, genitive-chain, and participle patterns are the core of this pass, applied here without the register restraint (naming the actor and addressing the reader directly is the point, not a risk).
3. **Simplify with surgical `Edit` calls**, sentence by sentence. Principles:
   - Start with what the reader needs to know or do; legal basis and background move below the action.
   - Address the reader directly (`złóż wniosek`, `możesz odwołać się`) where the text instructs; name the actor (`urząd wyda decyzję`) where it informs.
   - Verbs over noun constructions, active over passive, one thought per sentence, roughly 15–20 words for broad-audience text.
   - Concrete, familiar words; a necessary specialist or legal term stays and gets a plain-words explanation on first use.
4. **Summarize in chat**: per file, what got simpler and one or two before → after examples, in the conversation language.

## Safety — never simplify away

Deadlines, eligibility requirements, legal basis, required documents, exceptions, warnings, rights and obligations, and procedural steps all survive the rewrite. Never move a legal obligation onto an unnamed reader: `Przedsiębiorca składa oświadczenie w terminie 14 dni` is plain and correct; `Masz 14 dni, żeby złożyć` quietly drops who is bound. Never invent facts, and never replace a precise term with a looser synonym — explain it instead. Don't touch code blocks, URLs, quoted material, proper names, or data in tables.

## When NOT to use

- Removing signs of AI writing without changing the register → `/unslop:unslop`.
- Legal or academic text where the formal register is a requirement — simplify only explanatory passages around it, never the operative wording.
- Non-Polish text; this pass is built on Polish plain-language rules.

---

Plain-language rules adapted from [miodkuj](https://github.com/bartekpucek/miodkuj) by Bartek Pucek (MIT).
