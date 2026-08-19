---
name: model-routing
description: Choose the right model and reasoning effort for a task. Use this skill before spawning subagents, delegating with the task tool, configuring an Agents SDK agent or Codex profile, or whenever asked which model or reasoning level to use for something. Also use it when a run is too slow, too expensive, or the answer quality is worse than expected and the fix might be a different model or effort level.
---

# Model Routing

Two independent routing choices, then an encoding step:

1. **Model tier** is set primarily by how much *judgment* the task needs.
   Judgment means deciding what should be done when the request is ambiguous,
   incomplete, or has competing valid answers. Tier is then floored by risk: a
   task whose errors are expensive and whose output has no reliable check stays
   on the frontier tier even when its judgment demand is low.
2. **Reasoning effort** is set by how much *deliberation* the task needs. That
   means steps to plan, branches to consider, and self-verification to perform
   before answering.
3. **Host encoding** translates those choices into the active harness. Before
   dispatch, identify the harness and use its exact model namespace and exposed
   controls from [references/model-map.md](references/model-map.md#harness-syntax).
   Model IDs and display names are not portable between harnesses. When the host
   does not expose effort or context controls, keep the routing choice in the
   rationale, state that the axis is not enforced, and do not represent prompt
   wording as an equivalent control.

The first two choices are not substitutes. Raising effort gives a weaker model
more time to explore; it does not give it better taste. A cheap model at max
effort will still confidently execute the wrong plan. Conversely, a frontier
model at low effort still brings its judgment but may skip verification steps.

Because these two axes are independent, ask two separate questions and do not
let the answer to one bias the other. "This request is ambiguous" argues for the
frontier tier and says nothing about effort. "This has many steps and edge
cases" argues for higher effort and says nothing about tier. An ambiguous but
mechanically simple change is correctly routed to a frontier model at low
effort, and a fully specified but intricate change is correctly routed to an
efficient model at high effort. Those pairings look inverted only if the two
questions are collapsed into one.

Resolve `<skill-directory>` to the directory containing this `SKILL.md`.

- Concrete model IDs, prices, context limits, and per-harness syntax:
  [references/model-map.md](references/model-map.md). Dated, and the file that
  changes most often when a new model ships.
- Benchmarks, citations, and known conflicts behind these recommendations:
  [references/evidence.md](references/evidence.md).

See "Refreshing this skill" at the end for which parts of *this* file are also
volatile.

## Pick a tier

**The ladder has exactly two rungs: Frontier and Efficient.** Every "tier up"
or "tier down" instruction in this skill moves between those two and nowhere
else. The balanced tier sits off the ladder entirely and is never reached by a
modifier.

| Tier | Use when | Current model (2026-08) |
|---|---|---|
| **Frontier** | The task requires judgment, the request is ambiguous, or a wrong answer is expensive to discover later | `gpt-5.6-sol` |
| **Efficient** | The task is well specified and the output is cheap to verify | `gpt-5.6-luna` |
| *(off-ladder)* **Balanced** | Only when a measured eval on your own workload shows it beats both, or the harness offers no efficient tier | `gpt-5.6-terra` |

The middle tier is deliberately skipped. On aggregate coding and agentic
benchmark indices, the frontier and efficient tiers jointly form the
cost-quality frontier, and the balanced tier sits inside it: for a given
balanced-tier configuration there is usually an efficient-tier configuration
that is cheaper at similar quality, or a frontier-tier one that is better for
a comparable effective cost. Concretely, Luna at `xhigh` costs less than Terra
at `low`.

Note the precise claim. Terra is not worse than Luna on quality, and it is not
more expensive than Sol. It is off the frontier those two jointly define, which
is why the eval escape hatch above is coherent rather than self-refuting: the
dominance is measured on aggregate indices, so a specific workload can still
land in Terra's favor. If your own eval says Terra wins, believe the eval. See
[references/evidence.md](references/evidence.md#terra-is-off-the-joint-frontier).

## Pick an effort

| Effort | Use for | Tokens vs medium |
|---|---|---|
| `low` | Execution against a clear spec, mechanical edits, tool calls, retrieval, routing, classification | ~0.35x |
| `medium` | Default. Planning, judgment, ordinary agentic coding, research | 1x |
| `high` | Hard debugging, deep planning, consequential review, anything where a missed edge case is costly | ~1.75x |
| `xhigh` | Async work with no latency budget: security review, deep research, genuinely hard coding. For task classes the routing table names, `xhigh` is the documented starting point. For anything else, adopt it only after evidence it beats `high` on your task | ~2.5x |
| `max` | Rarely. The hardest quality-first single-agent work, after `xhigh` has been shown insufficient | ~4x |

For a task class **not** covered by the routing table below, start at `medium`
and move in one direction based on observed failure. The routing table overrides
this generic default, because its rows already encode a starting point chosen
for that task class. Never treat `xhigh` or `max` as a starting point for an
uncovered task.

Copilot CLI does not expose `none` for OpenAI models; `low` is the floor there.
The API does expose `none`, which is for latency-critical, non-reasoning work
only, such as classification and voice. Test `low` before dropping to `none`.

## Default routing table

These rows are the starting point for each task class. **Each row already
prices in the stakes typical of that task**, so do not apply a stakes modifier
for a property already named in the row. Apply role modifiers, and apply stakes
modifiers only for properties the row does not mention.

Cost is expressed as a multiple of Luna medium, combining per-token price with
effort token burn. The figures are approximate; see
[references/model-map.md](references/model-map.md#effective-cost-grid) for the
method and its assumptions.

| Task | Model | Effort | Cost | Why |
|---|---|---|---|---|
| Read-only exploration, codebase search, "where is X" | Luna | `medium` | 1x | Retrieval and summarization, verifiable by reading the files it cites |
| Trivial ops: commit messages, PR descriptions, renames, lookups | Luna | `low` | 0.35x | Output is inspected immediately; failure is free |
| Well-scoped implementation, clear spec, tests exist | Luna | `high` | 1.75x | Spec supplies the judgment, so buy deliberation instead. Drop to `medium` if the change is also mechanically simple |
| Test generation | Luna | `high` | 1.75x | Mechanical once behavior is defined. Review the assertions, not just that the suite runs |
| Data, SQL, and analysis against a known schema | Luna | `high` | 1.75x | Needs care, not taste. Check results against a known total or invariant |
| Ambiguous or underspecified implementation | Sol | `low` | 9x | Tier buys the judgment to pick the right thing to build; if building it is also intricate, raise effort independently |
| Long-context synthesis across a large repo or doc set | Sol | `medium` | 25x | Weaker models lose the thread; see context_tier below |
| Research and web synthesis | Sol | `medium` | 25x | Source quality and contradiction handling are judgment calls |
| Planning, task decomposition, orchestration | Sol | `medium` | 25x | A bad plan is the most expensive failure in an agent pipeline |
| Architecture, system design, ADRs | Sol | `high` | 44x | Ambiguous, consequential, and hard to reverse. Durability and irreversibility are already priced in |
| Hard debugging and root-cause analysis | Sol | `high` | 44x | Requires holding competing hypotheses and rejecting the easy local fix |
| Code review | Sol | `high` | 44x | The value of review is catching what the author missed |
| Design docs and customer-facing technical writing | Sol | `medium` | 25x | Audience judgment and framing. Customer-facing is already priced in |
| Security review and threat modeling | Sol | `xhigh` | 62x | Documented exception to the start-at-medium rule, on the strength of the cybersecurity results in evidence.md. Async and adversarial, so exhaustive search pays. Customer exposure and severity of the system under review are already priced in |
| Long-running autonomous agentic runs | Sol | `medium` | 25x | See the long-session rules below; do not raise effort to fix drift |

## Modifiers

Resolve the tier axis and the effort axis separately, applying these rules in
order to each axis. Within one axis, stop at the first rule that settles it.

1. **Role prohibitions win.** If a role says "never downshift", no later
   modifier may lower its tier. A throwaway orchestrator stays on the frontier
   tier.
2. **Skip anything already priced in.** If the routing table row already names
   the property, do not apply it again. A routing table row also overrides the
   generic effort guidance: where the table names a starting effort, that is the
   starting effort.
3. **Apply at most one tier shift and at most one effort shift** per routing
   decision. Modifiers do not compound. If several apply to the same axis, take
   the single strongest, meaning the one whose stated reason survives the
   others: a modifier grounded in the cost of being wrong outranks one grounded
   in the cost of the run.
4. **Clamp.** Tier is bounded by Frontier and Efficient. Effort is bounded by
   `low` and `max`. A shift that would move past either end is dropped, not
   carried over into the other axis.
5. **Every tier downshift still requires a named verification gate**, with no
   exceptions, including throwaway work.

**Role in the workflow**

Classify role by decision authority, not by the agent's name or the task noun.
A worker named "Planner" is still a worker when it owns only a bounded section
and a parent evaluates its return.

- **Orchestrator or planning owner**: never downshift. This role owns
  decomposition, cross-task decisions, or final plan synthesis, and every worker
  inherits its errors.
- **Fan-out or bounded worker**: use the efficient tier if a verification gate
  exists. This includes bounded planning assignments that cannot revise the
  overall plan without parent approval. If the row already routes to the
  efficient tier, leave it there. Waste multiplies across parallel agents, and
  so does a bad model choice.
- **Final reviewer or synthesizer**: never downshift. This is the last chance to
  catch an error, so it needs judgment, not throughput. Route a reviewer by the
  artifact it is reviewing: reviewing a design document uses the design document
  row, not a generic review effort. Use that row's effort unchanged, and step up
  exactly one level if no human inspects the artifact after this agent. That
  step counts as the one effort shift allowed by rule 3.
- **Router or triage** (deciding which agent handles this): Luna `low`. Pattern
  matching, not reasoning.

**Stakes and blast radius**

- Output ships to a customer, or lands in a durable artifact such as an ADR or a
  design doc: one effort step up.
- Change is hard to reverse: schema migration, public API shape, infrastructure,
  anything touching production data: one effort step up, and require an approval
  gate before the write. This applies when the agent *makes* the change. An
  agent that only reads and reports on such a system is not covered, since its
  own output is reversible; the approval gate still applies to whoever acts on
  the report.
- Throwaway prototype, spike, or scratch script: use the efficient tier, subject
  to rules 1 and 5 above.
- You will read and verify the output yourself in the next minute, **and the
  errors that matter for this task are ones you would actually catch on
  reading**: use the efficient tier. Your review is the verification gate. This
  does not apply when the failure mode is subtle enough to survive a read, such
  as audience misjudgment in a document or a plausible-looking wrong number.

## The verification gate

Downshifting is only safe when a mechanism other than the model catches its
mistakes. Before dropping a tier, name the gate:

- A test suite that actually covers the change
- A compiler, type checker, or linter that fails on the error class
- A schema or contract the output must satisfy
- A stronger reviewer model that reads the output before it is used
- You, reading it immediately, for error classes a read would actually catch

A gate has to catch the error class you are worried about. Two ways this fails
quietly:

- **Execution is not correctness.** A vacuous or wrong test passes. Syntactically
  valid SQL returns a plausible wrong number. If the model wrote both the code
  and the check, the check inherits its misunderstanding.
- **The gate is unqualified for the failure mode.** Reading a document catches
  typos and obvious errors, not a misjudged audience or a subtly wrong framing.

So prefer a gate with an independent source of truth: expected values derived
separately, an invariant or reconciliation total, a reference implementation, or
a reviewer that did not write the artifact.

If you cannot name one, do not downshift. "It's probably fine" is not a gate.

The corollary: adding a gate is usually cheaper than upgrading the model. Luna
`high` plus a Sol `medium` reviewer costs less than Sol `high` on the whole
task and catches a different, often larger, class of error.

## Escalation and de-escalation

Escalate when you observe a specific failure, not preemptively.

| Observed failure | Fix |
|---|---|
| Output is well reasoned but solves the wrong problem | Tier up. This is a judgment failure, and effort will not fix it. |
| Output is directionally right but misses edge cases or skips verification | Effort up one step. |
| Model asks for clarification it should have inferred | Tier up. |
| Model contradicts itself across a long session | Do not escalate. Compact the context or split the task. See below. |
| Model is correct but too slow for an interactive turn | Effort down one step before tier down. Effort is the cheapest latency lever, and unlike a tier change it does not give up judgment. If quality must be preserved exactly, consider Sol fast mode instead, which buys speed with price rather than deliberation. |
| Cheap model failed twice on the same task | Tier up once. Do not retry a third time at the same setting. |

De-escalate when the same task class has succeeded repeatedly at the current
setting and the gate has been catching nothing. That is grounds for a monitored
trial one step cheaper on a single axis, effort before tier, not proof that the
cheaper setting is safe: a silent gate is
ambiguous evidence, since it is equally consistent with the model succeeding, the
task being easy, and the gate being ineffective. Confirm the gate actually works
before relying on it, by checking that it has caught real failures before or by
feeding it a known-bad input.

Escalate at most one step at a time, and only after the prompt is known to be
good. Most apparent model failures are missing context.

## context_tier

Copilot CLI exposes `context_tier: default | long_context` on most models. Use
`long_context` only when the input genuinely exceeds the default window:
whole-repo synthesis, large document sets, or a long transcript. It is not a
quality setting, and using it by default wastes budget and can dilute attention
across irrelevant material.

If a task needs `long_context`, first ask whether it should instead be split
into bounded subtasks with a synthesis step. Narrower context usually beats
larger context on the same budget.

## Anti-patterns

- **Raising effort to compensate for a bad prompt.** A missing spec, absent
  acceptance criteria, or unstated constraints will not be reasoned into
  existence. Fix the prompt first, then re-measure.
- **Starting at `xhigh` or `max` for an uncovered task.** These are destinations
  reached by evidence, not starting points. They cost 2.5x to 4x medium and are
  frequently worse on simple tasks because the model adds unnecessary steps. The
  one documented exception is security review, which the routing table starts at
  `xhigh`; a table row beats this rule, an intuition does not.
- **Using `max` on tasks with deterministic validation.** If a test suite or
  compiler decides correctness, extra deliberation is largely wasted. Spend that
  budget on more attempts or a better gate instead.
- **Using the frontier tier for fan-out.** Parallel agents multiply cost. If
  eight workers each need frontier judgment, the decomposition is wrong; the
  judgment belongs in the orchestrator.
- **Downshifting the reviewer.** The cheapest place to save money is also the
  worst, because the reviewer is the gate.
- **Raising effort to fix long-session drift.** Drift is a context problem.
  Higher effort consumes more of the window with reasoning tokens and can make
  it worse.
- **Treating the middle tier as the safe default.** It is off the frontier that
  the other two jointly define. Pick a side, or produce an eval that justifies
  it.
- **Re-running the same failure at a higher setting more than once.** Two
  escalations without progress means the task, the context, or the tooling is
  the problem.

## Long-session and autonomy rules

- Frontier models drift in long sessions, typically after five or six
  substantial exchanges: substituting an easier problem for the original one,
  applying local fixes without rechecking the design, and losing track of the
  original acceptance criteria. Mitigate by compacting history, restating the
  objective and constraints, or splitting into fresh subtasks. Do not mitigate
  by raising effort.
- Higher effort increases autonomy and persistence. At `high` and above, require
  an explicit approval gate before destructive or external-write operations, and
  state the autonomy boundary in the prompt rather than assuming it.
- For agent loops on the API, structure the stable system prompt and tool
  definitions as a cached prefix. GPT-5.6 charges for cache writes, so an
  unmarked dynamic suffix silently pays the write premium on every turn without
  ever reading the cache. See
  [references/model-map.md](references/model-map.md#prompt-caching).

## Non-OpenAI escape hatches

Default to OpenAI. Switch when one of these specific conditions holds, not on
general preference.

- **Claude Opus 5**: classic repository-editing work of the "fix this issue in
  this real codebase" shape, where it leads by a wide margin on SWE-Bench Pro.
  Costs meaningfully more per agentic task.
- **Claude Sonnet 5**: the strongest middle tier available; a reasonable
  substitute for the discouraged Terra slot when running under Claude Code.
- **Gemini 3.1 Pro**: input larger than the OpenAI window, heavy multimodal or
  UI-screenshot work, or abstract-reasoning puzzles where it leads.
- **Grok 4.5**: interactive single-file coding where cost per turn dominates.
  Not for complex agentic pipelines.
- Whatever model is already running the session: switching harnesses has its own
  cost. If the current model is within one tier of the recommendation, staying
  put is usually right.

## Answering "what model should I use"

State the pick, the effort, and the single reason in one line. Then offer one
cheaper alternative with the condition under which it is sufficient. Do not
present a matrix unless asked. Example:

> Sol at high effort, because root-cause analysis needs to hold competing
> hypotheses. Luna at high is fine instead if you already have a failing test
> that isolates the bug.

When picking models for subagents, do not ask permission. Pick, spawn, and state
what was chosen and why in one line.

## Refreshing this skill

Model facts go stale in weeks. The reasoning here is written in tiers so it
survives releases, but this file is not purely durable: it names the current
occupant of each tier, quotes cost multiples, and asserts that the middle tier
is off the joint frontier. Those are volatile and must be rechecked.

Durable (leave alone unless the underlying behavior changed): the
judgment-versus-deliberation split, the modifier precedence and clamping rules,
the verification gate, the escalation table, and the anti-patterns.

Volatile (recheck every time): everything in
[references/model-map.md](references/model-map.md), the tier occupants and cost
column here, and the joint-frontier claim.

1. Check the vendor model and pricing pages for new IDs, price changes, and
   changes to the supported effort range.
2. Check the harness release notes for newly selectable models and effort levels
   (Copilot CLI model list, Codex, Agents SDK).
3. Re-check whether the efficient and frontier tiers still jointly dominate the
   middle tier. This is the assumption the skill leans on hardest, and a price
   move on any tier can invert it. If it inverts, the barbell becomes wrong and
   the two-rung ladder needs a third rung.
4. Update the model map and restamp its date. Update the tier table, the cost
   column, and the concrete cross-over example in "Pick a tier" if the numbers
   moved.
5. Re-run the evals. Several assert specific model names and will need updating
   whenever a tier occupant changes.
