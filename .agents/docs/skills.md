# Skills kept in this repo

Three skills are vendored under `.agents/skills/` so the repo carries the
conventions it was written to, rather than depending on whatever is installed
globally. They are documentation, not code: nothing in the build reads them.

| Skill | Reach for it when |
|---|---|
| [`writing-for-agents`](../skills/writing-for-agents/SKILL.md) | writing or editing any of these docs, or an `AGENTS.md` — context pointers, information hierarchy, pruning, leading words |
| [`agent-md-refactor`](../skills/agent-md-refactor/SKILL.md) | an agent file has outgrown its top: splitting it, finding contradictions, deciding what belongs at the root |
| [`create-agentsmd`](../skills/create-agentsmd/SKILL.md) | starting an `AGENTS.md` from nothing, or checking this one covers setup, workflow, tests and build |

The two longer ones carry their own companions — `writing-for-agents` ships
`SKILL-MECHANICS.md` (frontmatter, invocation, router skills) next to it, and
`agent-md-refactor` ships a worked before/after `README.md`.

The one rule that outranks a skill's own defaults: **this repo's docs are the
authority on this repo.** A skill describes how to write; the numbers, the layer
list and the traps here describe what is true. Where they disagree, the docs win
and the skill is what gets left alone.
