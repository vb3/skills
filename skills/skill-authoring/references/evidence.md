# Evidence

Dated 2026-08-24. Sources verified by direct fetch. This file holds the exact
quotes behind `SKILL.md`, plus everything that carries a caveat. Read it before
repeating a claim from this skill to anyone else.

## Sources

| Source | URL |
|---|---|
| Anthropic engineering, "Equipping agents for the real world with Agent Skills" | <https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills> |
| Agent Skills best practices (canonical authoring reference) | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices> |
| Agent Skills overview | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview> |
| Agent Skills open standard specification | <https://agentskills.io/specification> |
| Claude Code: skills | <https://code.claude.com/docs/en/skills> |
| GitHub Copilot CLI: adding agent skills | <https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills> |
| GitHub Copilot: about agent skills | <https://docs.github.com/en/copilot/concepts/agents/about-agent-skills> |
| GitHub Copilot in VS Code: agent skills | <https://code.visualstudio.com/docs/agent-customization/agent-skills> |
| anthropics/skills repository | <https://github.com/anthropics/skills> |
| awesome-copilot `appinsights-instrumentation` | <https://github.com/github/awesome-copilot/blob/main/skills/appinsights-instrumentation/SKILL.md> |

## Code versus prose

From the engineering blog:

> Large language models excel at many tasks, but certain operations are better
> suited for traditional code execution. For example, sorting a list via token
> generation is far more expensive than simply running a sorting algorithm.
> Beyond efficiency concerns, many applications require the deterministic
> reliability that only code can provide.

On their PDF form-extraction script:

> Claude can run this script without loading either the script or the PDF into
> context. And because code is deterministic, this workflow is consistent and
> repeatable.

That second quote is the basis for the claim in `SKILL.md` that an executed
script is the cheapest content in a skill.

On the dual role of bundled code:

> code can serve as both executable tools and as documentation. It should be
> clear whether Claude should run scripts directly or read them into context as
> reference.

## Degrees of freedom

From the best-practices doc. Low freedom is prescribed when:

> Operations are fragile and error-prone
> Consistency is critical
> A specific sequence must be followed

High freedom when:

> Multiple approaches are valid
> Decisions depend on context
> Heuristics guide the approach

The analogy quoted in `SKILL.md`:

> Narrow bridge with cliffs on both sides: There's only one safe way forward.
> Provide specific guardrails and exact instructions (low freedom). Example:
> database migrations that must run in exact sequence.
>
> Open field with no hazards: Many paths lead to success. Give general
> direction and trust Claude to find the best route (high freedom). Example:
> code reviews where context determines the best approach.

The doc's own low-freedom example is an exact command with "Do not modify the
command or add additional flags."

## Progressive disclosure and token budget

From the overview, level 3 is described as:

> Code and resources (loaded and executed when needed): Executable scripts and
> other supporting files that Claude uses to complete specific tasks.

The best-practices doc annotates a `scripts/` directory in its skill-structure
diagram with "executed, not loaded into context," distinguishing the two modes.

On budget:

> Not every token in your Skill has an immediate cost. At startup, only the
> metadata (name and description) from all Skills is pre-loaded. Claude reads
> SKILL.md only when the Skill becomes relevant, and reads additional files
> only as needed. However, being concise in SKILL.md still matters: once Claude
> loads it, every token competes with conversation history and other context.

On splitting:

> When the SKILL.md file becomes unwieldy, split its content into separate
> files and reference them. If certain contexts are mutually exclusive or
> rarely used together, keeping the paths separate will reduce the token usage.

The open spec states the three levels as metadata (~100 tokens, always loaded),
instructions (<5000 tokens recommended), and resources (loaded when required).
The 5000 figure is a recommendation, not an enforced limit.

## Invocation controls

The open Agent Skills specification does not define `user-invocable` or
`disable-model-invocation`. Its frontmatter table contains `name`,
`description`, `license`, `compatibility`, `metadata`, and the experimental
`allowed-tools` field.

GitHub Copilot in VS Code documents:

> `user-invocable`: Controls whether the skill appears as a slash command in
> the chat menu. Defaults to `true`. Set to `false` to hide the skill from the
> `/` menu while still allowing the agent to load it automatically.

and:

> `disable-model-invocation`: Controls whether the agent can automatically load
> the skill based on relevance. Defaults to `false`. Set to `true` to require
> manual invocation through the `/` slash command only.

Claude Code documents the same defaults and semantics, and explicitly labels
invocation control as an extension to the open standard.

Copilot CLI's published authoring page does not list either field, but version
1.0.81-8 provides direct implementation evidence. Its packaged changelog
contains "Skills support `disable-model-invocation` frontmatter field" and
"Fully honor the skill disable-model-invocation flag." Two packaged built-in
skills set `user-invocable: false`. Treat this as verified behavior for that
version, not a portable specification guarantee.

## Script conventions

From the open spec, on `scripts/`:

> Contains executable code that agents can run. Scripts should:
> - Be self-contained or clearly document dependencies
> - Include helpful error messages
> - Handle edge cases gracefully

The spec is explicit that any file in the skill directory is reachable and that
`scripts/` is a naming convention with no special loader behavior.

## The hybrid split

Anthropic's PDF skill runs `analyze_form.py`, which writes `fields.json`, which
the agent then reads or edits, after which `fill_form.py` consumes it. The
best-practices doc presents this as a checklist workflow. That intermediate
JSON handoff is the pattern `SKILL.md` describes, though no source names it.

`appinsights-instrumentation` in awesome-copilot is the closest real-world
analog to a setup skill: deterministic Azure resource creation lives in
`scripts/appinsights.ps1`, while framework-specific code changes and all user
interaction stay in prose references. Its SKILL.md instructs, "You must always
ask the user where the application is hosted."

## Repo-local lessons, not published guidance

These are recorded here because `SKILL.md` presents them with the same weight
as the sourced material, and they do not come from any vendor doc.

**Verify tool output shapes empirically.** In `local-hve-core`, three steps
asserted that `copilot skill list --json` reports registered skill directories.
It reports individual resolved skills, whose `path` values are leaf skill
directories. The intersection with the registered directory set is empty, so
the idempotency check never matched and the validation step could never pass.
The text read correctly and survived both an authoring session and a plan
critique. Running the command once refuted it.

**State every rule exactly once.** The same skill excluded `installer` and
`experimental` in one step while configuring the parent directory containing
both in another. Two prose statements of one rule drifted apart.

Both defects are in the class that a bundled script plus a unit test removes
structurally, which is the main reason this skill is opinionated about the
script-versus-prose split.

## Not verified, or explicitly false

| Claim | Status |
|---|---|
| A verbatim rule of the form "if the operation is deterministic, write a script" | Not found in any source. The substance is the three quotes above; the phrasing is not Anthropic's. |
| `scripts/` is a special, specially-loaded directory | False. Convention only. |
| The script-emits-JSON hybrid is a formally named pattern | Not named or given a dedicated doc page anywhere. Demonstrated by example only. |
| Quantified token cost of prose procedures versus script invocation | No published numbers. The sorting analogy is illustrative, not empirical. |
| Claude Code `!` dynamic context injection works in Copilot CLI | False. Claude Code extension, not in the open spec. |
| Source of `anthropics/skills` PDF scripts | Referenced by name across official docs, but GitHub returned 403 on the file views, so the implementations were not read. |
| Guidance comparing maintenance burden of scripts versus prose | Not addressed by any source. The tradeoff claim in `SKILL.md` is judgment. |
