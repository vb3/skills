---
name: skill-authoring
description: Author, review, and debug agent skills (SKILL.md files and their bundled scripts, references, and evals). Use this skill when creating a new skill, editing or refactoring an existing one, deciding whether a procedure belongs in prose or in a bundled script, writing or tightening a description so the skill actually triggers, splitting a long SKILL.md into references, writing evals, or reviewing someone else's skill.
---

# Skill Authoring

A skill is not documentation. It is a context-budget instrument that competes
with the user's actual conversation for the model's attention, and it is loaded
on a trigger you wrote. That produces two failure modes worth more than all
other style concerns combined: the skill never loads because the description
was vague, or it loads and reliably does the wrong thing because a
deterministic procedure was written as prose for the model to re-derive on
every run.

Most authoring effort should go into the description and into deciding what
becomes code. The prose is the easy part.

- Verified sources, exact quotes, and what could not be confirmed:
  [references/evidence.md](references/evidence.md). Read this before repeating
  a claim from this skill to someone else.
- Frontmatter fields, file discovery, install paths, and what is portable
  across Copilot CLI, Claude Code, and the open spec:
  [references/platform-notes.md](references/platform-notes.md).

## The first decision: script or prose

Anthropic frames this as **degrees of freedom**, and it is the most useful rule
in skill authoring. Their analogy: a "narrow bridge with cliffs on both sides"
has only one safe way forward, so give exact instructions; an "open field with
no hazards" has many paths, so give direction and trust the model.

| Signal | Freedom | Form |
|---|---|---|
| One correct sequence, failure is silent or expensive, result must be byte-identical every run | Low | Bundled script, invoked with exact flags |
| Rules are fixed but which rule applies depends on inspecting the situation | Medium | Prose plus an explicit decision table |
| Several approaches are valid, context or the user decides | High | Prose stating goals and constraints, not steps |

Low-freedom signals, quoting the best-practices doc directly: "operations are
fragile and error-prone," "consistency is critical," "a specific sequence must
be followed." High-freedom signals: "multiple approaches are valid," "decisions
depend on context," "heuristics guide the approach."

Concretely, low freedom covers symlink and file mutation, JSON and config
merging, idempotency checks, and validation assertions. High freedom covers
asking the user to resolve a collision, choosing between valid designs, and
writing the final report.

Do not resolve this per skill. Resolve it per step. Most real skills are mixed,
and the mixed case has a standard shape (see The hybrid split).

## Progressive disclosure

Three levels, with different costs. Budget accordingly.

| Level | Content | When loaded |
|---|---|---|
| 1 | `name` and `description` frontmatter | Always, for every skill installed |
| 2 | Body of `SKILL.md` | On trigger |
| 3 | `references/`, `assets/`, `scripts/` | Only when read, or never if executed |

Level 1 is charged against every session whether or not your skill is relevant,
so keep the description dense with triggers and free of prose. Level 2 should
stay under roughly 5000 tokens; once loaded, every token competes with the
conversation. Level 3 is where volatile detail, long tables, and platform
specifics belong.

A script at level 3 is the cheapest content in a skill, because an executed
script never enters the context window at all. Only its output does.

Split into references when a section is long, volatile, or mutually exclusive
with another path through the skill. Do not split a short skill into fragments
for tidiness; the indirection costs a read.

## The description is the whole trigger

First rule out the mechanical causes. A skill that is not installed in a
discovered location, is disabled, or was added after the session started will
never load no matter how good its description is. Confirm it is present and
enabled, and reload if the host requires it, before touching a word. See
[references/platform-notes.md](references/platform-notes.md).

Once the skill is provably available, retrieval is a text match against the
description. Nothing else in the skill influences whether it loads. Write it to
be matched, not to read well.

- Lead with what the skill does, then an explicit "Use this skill when..."
  clause enumerating concrete triggering situations. That fragment is the
  established convention and is not an exception to the rule below.
- Include the vocabulary a user would actually type, including tool names, file
  names, error strings, and synonyms.
- Add a "Do not use for" clause when a sibling skill is a plausible confusion.
- Describe the situation and the work, never the reader. No "you", no "I can
  help you", no conversational framing.

For an available skill that still does not fire, the description is the first
thing to fix and usually the only thing that needs fixing.

## Writing the procedure

**State every rule exactly once.** A rule repeated in two sections will drift,
and the two copies will contradict each other after the third edit. If a
constraint governs several steps, state it once and reference it. Contradiction
between two statements of one rule is a recurring defect in mature skills; both
sibling-skill bugs recorded in
[references/evidence.md](references/evidence.md) are instances of it.

**Verify tool output shapes empirically before asserting them.** If a step says
a command reports something, run the command and look. A plausible but wrong
assumption about output shape produces a validation step that can never pass,
and prose review will not catch it because the text reads correctly. This is a
repo-local lesson rather than published guidance; see
[references/evidence.md](references/evidence.md).

**Make validation checks executable.** "Verify the config is correct" is not a
check. Name the command, the expected exit code, and the specific field or path
compared against what.

**Write for the agent, not the reader.** Imperative, second person, no
narration of intent, no motivational framing.

## Bundled scripts

Any file in the skill directory is available to the agent; `scripts/` is a
convention with no special loading behavior. Path and dependency rules for
bundled files live in
[references/platform-notes.md](references/platform-notes.md).

Contract worth holding to:

- One purpose per script, an `argparse` interface, no interactive prompting.
- Distinct exit codes per failure gate so the agent can branch without parsing
  prose.
- Structured output, normally JSON on stdout, and human-readable errors on
  stderr.
- Idempotent. Re-running a completed setup must be a no-op, not a duplicate.
- Portable, per the dependency rule in
  [references/platform-notes.md](references/platform-notes.md).
- Unit tests alongside it. Determinism, repeatability, and context efficiency
  are the published arguments for scripting; testability is the one that pays
  off during maintenance, because a script can be verified against known inputs
  whereas a prose procedure can only be tested end to end through the model.

Tell the agent to run the script, do not make it reconstruct the command:

> Run `scripts/wire.py --check --source <abs-path>`. Exit 0 means ready, exit 3
> means a collision needs a user decision, exit 4 means the source is missing.

## The hybrid split

The common shape for a real skill: the script performs all deterministic
inspection and mutation and emits structured state; the agent keeps user
interaction, judgment, and reporting.

1. Script inspects and emits JSON describing current state and what it would do.
2. Agent interprets, and asks the user about anything genuinely undecidable.
3. Script applies the change, taking the decision as a flag.
4. Script verifies and emits assertions with pass or fail per check.
5. Agent writes the human report from that output.

This is not a formally named pattern, but it is what Anthropic's own PDF skill
does with an intermediate `fields.json` between its analyze and fill scripts.

## Evals

Every skill in this repo carries `evals/evals.json`: `skill_name` plus an
`evals` array of `{id, prompt, expected_output, files, expectations}`.

Expectations must be objectively checkable by an independent reviewer.
"Handles the error well" is not an expectation. "Exits without creating
`.hve-core` and reports that approval is required" is. Every expectation must
be mandatory; an expectation hedged with "may" cannot fail and therefore tests
nothing.

Each eval must be self-contained. If an expectation requires the agent to
inspect a file or a command's output, supply it in `files` or inline it in the
prompt. An eval that names a command the agent cannot run rewards a fabricated
answer.

Cover the boring success path, each branch the skill claims to handle, the
collision and refusal cases, and idempotency on a second run. Cover triggering
in both directions: a phrasing that must load the skill, and a near-miss that
must not. When a bug is found in a skill, add the eval that would have caught
it in the same change.

Evals measure behavior, not recall. Compare a run with the skill against the
same prompt without it; if the outputs match, the skill earned nothing.

## Validating structure

Run the bundled validator before committing any skill in this repo:

```bash
python3 scripts/validate_skill.py <skill-directory>...
```

Exit 0 means clean, exit 2 means structural findings on stdout as JSON, exit 1
means the path is not a skill directory. It checks frontmatter presence and
`name` format, `name` against the directory, a non-empty description, relative
links resolving, and the evals schema including unique ids and non-empty
expectations. It deliberately judges nothing else; everything above this
section is the agent's job.

## Anti-patterns

- **Prose that re-derives a deterministic procedure on every run.** The model
  will get it right most of the time, which is worse than a script failing
  loudly, because the failures are silent and non-reproducible.
- **A vague description with a meticulous body.** The body is never read.
  Once a skill is confirmed installed and enabled, this is the usual reason it
  appears not to work.
- **Restating a constraint in three places for emphasis.** You have created
  three things to keep in sync and a future contradiction.
- **A script with no tests and no exit-code contract.** You traded a prose
  procedure the model can adapt for an opaque binary it cannot debug, and kept
  none of the verifiability that justified the trade.
- **Platform-specific syntax in a skill intended to be portable.** Claude
  Code's `!` command-injection syntax is not in the open spec and does not work
  in Copilot CLI. See [references/platform-notes.md](references/platform-notes.md).
- **Pre-approving `shell` or `bash` in `allowed-tools` for a skill you have not
  read end to end**, including its scripts.
- **Splitting a 60-line skill into five reference files.** Progressive
  disclosure is a budget tool, not an organizing aesthetic.

## Reviewing an existing skill

In order, because the early checks invalidate the later ones:

1. Is the skill installed in a discovered location and enabled? Nothing else
   matters until it loads.
2. Would the description match how a user actually phrases this request, and
   would it wrongly match neighbouring requests it should not serve?
3. Run `scripts/validate_skill.py` on it and clear anything it reports.
4. Does any step describe a deterministic procedure the model must re-derive?
5. Is any rule stated in two places, and do the copies still agree?
6. Does every claim about a command's behavior or output match what that
   command actually does? Run it.
7. Is every validation step executable, with a named command and expected
   result?
8. Do the evals cover the failure branches and the negative trigger case, or
   only the happy path?

Report findings as defects with severity, not as a rewrite. Fix the description
and the script-versus-prose split first; wording is last and usually optional.

## Refreshing this skill

Durable (leave alone unless the underlying reasoning changed): the degrees of
freedom decision, progressive disclosure, description-as-trigger, the
one-rule-one-place rule, the script contract, the hybrid split, and the review
order.

Volatile (recheck): everything in
[references/platform-notes.md](references/platform-notes.md), since frontmatter
fields, `allowed-tools` support, and CLI subcommands change; and the token
budget figure in Progressive disclosure, which is published guidance rather
than a hard limit.
