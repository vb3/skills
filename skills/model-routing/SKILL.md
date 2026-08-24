---
name: model-routing
description: Choose the right model and reasoning effort for a task. Use this skill before spawning subagents, delegating with the task tool, configuring an Agents SDK agent or Codex profile, or whenever asked which model or reasoning level to use for something. Also use it when a run is too slow, too expensive, or the answer quality is worse than expected and the fix might be a different model or effort level, and when trading off latency, speed, cost, and intelligence, or deciding what to run in an interactive loop versus in the background or a batch job.
---

# Model Routing

Two independent routing choices, made inside a constraint, then an encoding
step:

1. **Latency budget** is a property of the task rather than a preference: who
   is waiting for the result, and how long will they tolerate waiting. Settle
   it first, because it clamps the other two choices instead of trading against
   them.
2. **Model tier** is set primarily by how much *judgment* the task needs.
   Judgment means deciding what should be done when the request is ambiguous,
   incomplete, or has competing valid answers. Tier is then floored by risk: a
   task whose errors are expensive and whose output has no reliable check stays
   on the frontier tier even when its judgment demand is low.
3. **Reasoning effort** is set by how much *deliberation* the task needs. That
   means steps to plan, branches to consider, and self-verification to perform
   before answering.
4. **Host encoding** translates those choices into the active harness. Before
   dispatch, identify the harness and use its exact model namespace and exposed
   controls from [references/model-map.md](references/model-map.md#harness-syntax).
   Model IDs and display names are not portable between harnesses. When the host
   does not expose effort or context controls, keep the routing choice in the
   rationale, state that the axis is not enforced, and do not represent prompt
   wording as an equivalent control.

Tier and effort are not substitutes. Raising effort gives a weaker model
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

**Cost and latency are not the same axis, and cheap does not mean fast.** An
efficient model at high effort emits a great many reasoning tokens at its own
token rate, and can finish well after a frontier model at low effort: on current
figures Luna at `high` takes roughly three times as long as Sol at `low`.
Optimizing only for cost produces slow pipelines, and optimizing only for speed
produces expensive ones. The latency budget below is what keeps the two from
being confused.

Resolve `<skill-directory>` to the directory containing this `SKILL.md`.

- Concrete model IDs, prices, context limits, and per-harness syntax:
  [references/model-map.md](references/model-map.md). Dated, and the file that
  changes most often when a new model ships.
- Benchmarks, citations, and known conflicts behind these recommendations:
  [references/evidence.md](references/evidence.md).

See "Refreshing this skill" at the end for which parts of *this* file are also
volatile.

## Latency budget

Classify by who is blocked, not by how urgent the task feels. The routing table
below assumes the background class; the other two classes adjust it.

| Class | Who is waiting | Budget | Effect on routing |
|---|---|---|---|
| **Interactive** | A human, watching, unable to proceed | Under ~10 s per turn | Ceiling of `medium` effort. Never `high`, `xhigh`, or `max` |
| **Background** | A human doing something else, checking back later | Seconds to minutes | The routing table as written |
| **Batch** | Nobody, before a known deadline | Hours | No effort ceiling. Use the Batch API for its 50% discount if the deadline is more than 24 hours out |

**The interactive ceiling is applied last and overrides everything, including a
routing table row and any modifier.** Resolve tier and effort normally, then
clamp. Do not use "the table says `high`" to exceed it.

**If a task cannot fit its latency budget, move the task, not the quality.** A
security review belongs at `xhigh`, and `xhigh` cannot run inside an interactive
turn; the answer is to run it out of band and return the result, never to ship a
degraded review to hit a latency target. The classes are a statement about where
work is allowed to run, not a licence to under-resource it.

Ten seconds is the point at which a person stops attending and has to reorient
on return, which is why it is the interactive ceiling rather than a round
number; one second is the limit for uninterrupted flow. See
[references/model-map.md](references/model-map.md#human-latency-thresholds).

Classify by who is blocked and against what deadline, not by wall-clock
duration. "It runs overnight" is not by itself the batch class: an overnight job
with a 9 a.m. deadline has a real budget, and the Batch API's 24-hour ceiling
can miss it. Conversely, treating agent work as interactive when the human has
already tabbed away spends a budget that could have bought quality.

**When something is too slow, apply these in order and stop when it is fast
enough.** The order is by measured impact, and the model change is last because
it is the only one that gives up judgment.

1. **Cut round trips.** In agent loops, serial tool calls usually dominate wall
   clock over token generation. Issue independent tool calls in parallel, fan
   out independent subtasks, and combine dependent steps into one prompt.
   Reported at up to a 90% reduction on tool-heavy work.
2. **Cut output tokens.** Drop effort one step, cap `max_output_tokens`, and
   ask for less prose. Roughly proportional: half the output tokens, half the
   latency.
3. **Cache the stable prefix.** This is the lever that attacks time to first
   token specifically.
4. **Change the model.** Only now, and only under the tier rules above. Inside
   the OpenAI family that means Sol at lower effort, or Luna. It never means the
   middle tier.

There is no "buy speed with money" lever here. Fast mode is an API-level
`service_tier` control that is not reachable from the harnesses this skill
covers, so speed has to be bought with round trips, output length, or caching.
See [references/model-map.md](references/model-map.md#unavailable-speed-controls).

Do not shrink the prompt to go faster. Halving the input buys 1% to 5%. That
lever is for context quality and cost, not for latency.

## Pick a tier

**The ladder has exactly two rungs: Frontier and Efficient.** Every "tier up"
or "tier down" instruction in this skill moves between those two and nowhere
else. The balanced tier sits off the ladder entirely and is never reached by a
modifier, a latency constraint, or any other rule in this skill.

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
land in Terra's favor. If your own eval says Terra wins, believe the eval.

**Latency does not rescue the middle tier, and this is worth knowing because it
is the obvious objection.** Terra is genuinely between its siblings on raw
tokens per second, so it looks like it should own a latency slot. It does not,
because wall clock is roughly `tokens / rate`, and effort moves the token count
several-fold while the model only sets the rate. Varying effort therefore lets
the endpoints enclose the middle on latency exactly as they do on cost: Sol at
`medium` is both **faster and better** than Terra at `xhigh`. Inside the OpenAI
family the latency answer is Sol at lower effort when judgment is needed and
Luna when it is not. See
[references/evidence.md](references/evidence.md#terra-is-off-the-cost-frontier-and-the-speed-axis-does-not-rescue-it).

## Pick an effort

| Effort | Use for | Tokens vs medium |
|---|---|---|
| `low` | Execution against a clear spec, mechanical edits, tool calls, retrieval, routing, classification | ~0.35x |
| `medium` | Default. Planning, judgment, ordinary agentic coding, research | 1x |
| `high` | Hard debugging, deep planning, consequential review, anything where a missed edge case is costly | ~1.75x |
| `xhigh` | Async work with no latency budget: security review, deep research, genuinely hard coding. For task classes the routing table names, `xhigh` is the documented starting point. For anything else, adopt it only after evidence it beats `high` on your task | ~2.5x |
| `max` | Rarely. The hardest quality-first single-agent work, after `xhigh` has been shown insufficient | ~4x |

Effort is a ceiling rather than a fixed cost: the models reason adaptively and
spend fewer tokens on easy inputs, so a high setting does not always burn the
full multiplier. The practical consequence is that raising effort is cheaper
than the table implies on simple tasks, and lowering it is a less reliable
latency fix than expected on genuinely hard ones.

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
| Ambiguous or underspecified implementation | Sol | `low` | 6x | Tier buys the judgment to pick the right thing to build; if building it is also intricate, raise effort independently |
| Long-context synthesis across a large repo or doc set | Sol | `medium` | 17x | Weaker models lose the thread; see context_tier below |
| Research and web synthesis | Sol | `medium` | 17x | Source quality and contradiction handling are judgment calls |
| Planning, task decomposition, orchestration | Sol | `medium` | 17x | A bad plan is the most expensive failure in an agent pipeline |
| Architecture, system design, ADRs | Sol | `high` | 29x | Ambiguous, consequential, and hard to reverse. Durability and irreversibility are already priced in |
| Hard debugging and root-cause analysis | Sol | `high` | 29x | Requires holding competing hypotheses and rejecting the easy local fix |
| Code review | Sol | `high` | 29x | The value of review is catching what the author missed |
| Design docs and customer-facing technical writing | Sol | `medium` | 17x | Audience judgment and framing. Customer-facing is already priced in |
| Security review and threat modeling | Sol | `xhigh` | 42x | Documented exception to the start-at-medium rule, on the strength of the cybersecurity results in evidence.md. Async and adversarial, so exhaustive search pays. Customer exposure and severity of the system under review are already priced in |
| Long-running autonomous agentic runs | Sol | `medium` | 17x | See the long-session rules below; do not raise effort to fix drift |

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
  so does a bad model choice. Wall clock across a fan-out is the slowest worker
  rather than the sum, so an uneven split costs more time than a slow model
  does.
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
| Model is correct but too slow for an interactive turn | Do not start with the model. Work the latency levers in order; the model change is step 5. |
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
  the other two jointly define, on cost and on latency alike. Pick a side, or
  produce an eval that justifies it.
- **Reaching for the middle tier to go faster.** Its higher token rate is real
  and does not survive letting effort vary: Sol at `medium` is both faster and
  better than Terra at `xhigh`.
- **Reaching for a faster model when the loop is round-trip bound.** If wall
  clock is going into serial tool calls and tool execution, a faster model
  changes a small fraction of it. Measure where the time goes before routing.
- **Reading tokens per second as latency.** A model can lead on throughput and
  still feel slow, because it spends seconds thinking before the first answer
  token. For short interactive turns, time to first token dominates; throughput
  only wins once responses run to thousands of tokens.
- **Raising effort inside an interactive loop.** Effort is the token count and
  the token count is the wall clock. An interactive turn is the one place where
  the effort ceiling is set by the human, not by the task.
- **Shrinking the prompt to reduce latency.** Halving input buys 1% to 5%.
- **Expecting streaming to fix a reasoning model's latency.** Thinking tokens
  come before any answer token, so there is nothing to stream during the wait.
  Progress indication is the mitigation; streaming is not.
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
- **Claude Sonnet 5**: the strongest middle tier available. Reach for it only
  when the harness gives you no barbell to run instead, which is the same
  exception that lets the balanced tier onto the ladder at all.
- **Claude Haiku 4.5**: the only non-OpenAI model with sub-second time to first
  token, so the pick when interactive responsiveness is the whole requirement
  and Luna is unavailable. Note the 200K context, which is far below the 1M of
  everything else here.
- **Gemini 3.1 Pro**: input larger than the OpenAI window, heavy multimodal or
  UI-screenshot work, or abstract-reasoning puzzles where it leads. Its time to
  first token is tens of seconds; never put it in an interactive loop.
- **Gemini 3.7 Flash**: highest output throughput available, and more capable
  than Luna on aggregate indices. It is a **throughput** pick for long
  generations and batch pipelines, not a latency pick, because its time to
  first token is around ten seconds.
- **Grok 4.6**: frontier-class intelligence at roughly a third of Sol's price,
  and the best non-OpenAI option when Sol's cost is the blocker but its judgment
  is not replaceable. Weigh that it regressed slightly on multi-step agentic
  coding even as it gained on single-issue patching.
- Whatever model is already running the session: switching harnesses has its own
  cost. If the current model is within one tier of the recommendation, staying
  put is usually right.

## Answering "what model should I use"

State the pick, the effort, and the single reason in one line. Then offer one
cheaper alternative with the condition under which it is sufficient. Do not
present a matrix unless asked. Name the latency budget only when it changed the
answer. Example:

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
the verification gate, the escalation table, the anti-patterns, the three
latency classes, the ordering of the latency levers, and the human latency
thresholds behind the interactive budget.

Volatile (recheck every time): everything in
[references/model-map.md](references/model-map.md), the tier occupants, the cost
column here, the speed ordering of the tiers, and both frontier claims.

1. Check the vendor model and pricing pages for new IDs, price changes, and
   changes to the supported effort range. **Sol's promotional price expires
   2026-11-21**; when it does, every Sol figure in the cost column rises by
   about 50% and must be recomputed from the grid in the model map.
2. Check the harness release notes for newly selectable models and effort levels
   (Copilot CLI model list, Codex, Agents SDK). Re-derive the Copilot CLI table
   from the live tool schema rather than editing the copy in the model map.
3. Re-check whether the efficient and frontier tiers still jointly dominate the
   middle tier **on cost**. This is the assumption the skill leans on hardest,
   and a price move on any tier can invert it. If it inverts, the barbell
   becomes wrong and the two-rung ladder needs a third rung.
4. Re-check the **speed** enclosure separately, because it moves independently
   of price. The barbell currently holds on latency because Sol at `medium` is
   both faster and better than Terra at `xhigh`. If a release changes the
   token-rate spread or overturns that head-to-head, recompute the seconds
   table in evidence.md before assuming the conclusion still holds.
5. Update the model map and restamp its date. Update the tier table, the cost
   column, and the concrete cross-over example in "Pick a tier" if the numbers
   moved.
6. Re-run the evals. Several assert specific model names and will need updating
   whenever a tier occupant changes.
