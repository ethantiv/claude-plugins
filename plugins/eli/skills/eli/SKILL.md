---
name: eli
description: >-
  Explain like I'm an intern — explain any concept, term, acronym, or piece of code to a smart, mature person who simply has zero knowledge of that domain. NOT baby-talk (no "imagine you're 5"): treat the user as an intelligent adult, just unfamiliar. Always short, concrete, and visual — built on examples and analogies, no fluff, no padding. Triggers: "/eli", "eli", "wytłumacz jak stażyście", "wytłumacz prosto", "wyjaśnij obrazowo", "explain like I'm an intern", "ELI intern", "co to jest <X>", "wytłumacz mi <X> krótko".
argument-hint: "<concept / term / file path / code snippet to explain>"
allowed-tools: Read, Grep, Glob, Bash
---

# eli — explain like I'm an intern

Explain the subject in `$ARGUMENTS` to **a smart, mature adult who just doesn't know this
domain yet** — a sharp new intern on day one. Not a child. Assume general intelligence and
life experience; assume **zero** field-specific knowledge and zero jargon.

**Speak Polish** to the user (the explanation, headings, examples). These instructions stay
in English.

## Resolve the subject

- **Empty `$ARGUMENTS`** → ask in one Polish sentence what to explain. Don't guess.
- **A file path / something that looks like code in this repo** → read it (and only what you
  need to understand it) before explaining. Explain *that* code, not the abstract concept.
- **Anything else** → an abstract concept, term, or acronym. Explain from your own knowledge.
  Only run a tool if you genuinely need to check a repo-specific fact.

## How to explain

The whole point is **short, vivid, concrete**. A senior engineer skimming it should think
"yes, that's the cleanest way to say it" — not "this is padded".

1. **One-line core first.** Open with a single plain-language sentence: what it *is* and what
   it's *for*. If the reader stops here, they still got the gist.
2. **A concrete example or analogy.** Always. Anchor the idea to something the reader already
   knows from everyday life or from a domain they do have. Prefer a real, specific example
   over a generic description. Show a tiny code snippet / number / before-after when it lands
   the point faster than prose.
3. **Why it matters.** One or two sentences: what problem it solves, what breaks without it.
4. **One gotcha (optional).** The single most common misunderstanding or trap — only if it's
   genuinely useful. Skip it rather than pad.

## Hard rules

- **Mature, not childish.** No "imagine you're five", no cutesy tone, no talking down. Plain
  words, full respect for the reader's intelligence.
- **No jargon without paying for it.** If a term is unavoidable, define it in the same breath,
  in plain words. Don't explain one unknown with three more.
- **Length matches the subject, and stays tight.** A term → a few sentences. A gnarly system →
  still compact, no walls of text. Every sentence earns its place; if a line only restates the
  previous one, cut it.
- **Show, don't pad.** A good example beats a paragraph of qualifiers. Reach for an analogy,
  a number, or a 3-line snippet before reaching for more sentences.
- **One pass, done.** This is a one-shot explanation, not a tutoring session. If the user wants
  to go deeper or be quizzed, point them to `/teach-me`.

After explaining, offer in one line: deeper dive, a different analogy, or `/teach-me` for an
interactive session — then stop.
