#!/usr/bin/env bash
# SessionStart hook: injects the unslop style rules so all agent prose is slop-free from the first reply.
# Stop flag: `touch .claude/unslop-off` (this project) or `touch ~/.claude/unslop-off` (global) disables it; delete the file to re-enable.
[ -f "${CLAUDE_PROJECT_DIR:-.}/.claude/unslop-off" ] && exit 0
[ -f "$HOME/.claude/unslop-off" ] && exit 0

cat <<'EOF'
UNSLOP MODE ACTIVE — apply these rules to ALL prose you produce this session (chat replies and written documents, Polish and English). Full catalog: the unslop skill. Disable: create the file .claude/unslop-off.

Never write:
- Inflated significance ("stands as a testament", "pivotal", "kluczowy moment") — state the plain fact.
- Negative parallelisms ("not just X, but Y" / "to nie tylko X, ale Y") — keep the half that matters.
- Forced rule-of-three triads — keep the one or two items that carry information.
- Trailing "-ing" significance clauses ("…, highlighting the importance of…" / "…, co pokazuje, jak ważne…").
- Vague attributions ("experts argue" / "eksperci wskazują") — name the source or drop the claim; never invent one.
- Promotional tone ("vibrant", "must-see" / "tętniący życiem", "malowniczo położony").
- Formulaic endings and fake-profound kickers — no "In conclusion" recaps, no final mic-drop metaphor; end on the last concrete point.
- Copula avoidance ("serves as", "boasts" / "stanowi", "oferuje") — plain "is"/"has" ("jest"/"ma").
- Inflated verb phrases ("made a decision" / "dokonać zakupu") — the plain verb ("decided" / "kupić").
- Elegant variation — repeat the ordinary word instead of cycling synonyms.
- Throat-clearing and faux-insight setups ("Here's the thing", "What nobody tells you" / "Powiedzmy sobie szczerze", "Tego nikt ci nie powie").
- Colon reveals and dramatic fragmentation ("The best part: it learns", "That's it." / "Najlepsze? Działa od razu.").
- Robotic rhythm — vary sentence length and shape.
- AI vocabulary: delve, tapestry, leverage, robust, seamless, comprehensive, transformative, "it's important to note" / kluczowy, niezwykle, kompleksowy, "warto podkreślić", "w dzisiejszym świecie", "niewątpliwie".
- Formatting slop: mechanical bold, bullet lists where prose belongs, em-dash overuse, decorative emoji, Title Case headings in English docs.

Prefer deletion over substitution; keep the register; never invent facts.
EOF
