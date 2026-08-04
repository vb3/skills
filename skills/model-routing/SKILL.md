---
name: model-routing
description: Choose the right model and reasoning effort for a task. Use this skill before spawning subagents, delegating with the task tool, configuring an Agents SDK agent or Codex profile, or whenever asked which model or reasoning level to use for something. Also use it when a run is too slow, too expensive, or the answer quality is worse than expected and the fix might be a different model or effort level.
---

# Model Routing

Two independent choices, made in this order:

1. **Model tier** is set by how much *judgment* the task needs. Judgment means
   deciding what should be done when the request is ambiguous, incomplete, or
   has competing valid answers.
2. **Reasoning effort** is set by how much *deliberation* the task needs. That
   means steps to plan, branches to consider, and self-verification to perform
   before answering.

These are not substitutes. Raising effort gives a weaker model more time to
explore; it does not give it better taste. A cheap model at max effort will
still confidently execute the wrong plan. Conversely, a frontier model at low
effort still brings its judgment but may skip verification steps.

Resolve `<skill-directory>` to the directory containing this `SKILL.md`.

- Concrete model IDs, prices, context limits, and per-harness syntax:
  [references/model-map.md](references/model-map.md). That file is dated and is
  the only file that needs updating when a new model ships.
- Benchmarks, citations, and known conflicts behind these recommendations:
  [references/evidence.md](references/evidence.md).

## Pick a tier

| Tier | Use when | Current model (2026-08) |
|---|---|---|
| **Frontier** | The task requires judgment, the request is ambiguous, or a wrong answer is expensive to discover later | `gpt-5.6-sol` |
| **Efficient** | The task is well specified and the output is cheap to verify | `gpt-5.6-luna` |
| **Balanced** | Rarely. Only when a measured eval shows it beats both, or a harness offers no efficient tier | `gpt-5.6-terra` |

The middle tier is deliberately discouraged. After the July 2026 price cut,
Luna costs about 4% of Sol and about 10% of Terra per token while scoring within
a few points of Terra on coding and agentic benchmarks. Luna at high effort is
usually cheaper *and* stronger than Terra at low effort. Reach for the barbell:
Sol where judgment matters, Luna everywhere else. See
[references/evidence.md](references/evidence.md#terra-is-pareto-dominated).

## Pick an effort

| Effort | Use for | Tokens vs medium |
|---|---|---|
| `low` | Execution against a clear spec, mechanical edits, tool calls, retrieval, routing, classification | ~0.35x |
| `medium` | Default. Planning, judgment, ordinary agentic coding, research | 1x |
| `high` | Hard debugging, deep planning, consequential review, anything where a missed edge case is costly | ~1.75x |
| `xhigh` | Async work with no latency budget: security review, deep research, genuinely hard coding. Only after evidence it beats `high` on your task | ~2.5x |
| `max` | Rarely. The hardest quality-first single-agent work, after `xhigh` has been shown insufficient | ~4x |

Start at `medium` and move in one direction based on observed failure. Do not
start at `xhigh`.

Copilot CLI does not expose `none` for OpenAI models; `low` is the floor there.
The API does expose `none`, which is for latency-critical, non-reasoning work
only, such as classification and voice. Test `low` before dropping to `none`.

## Default routing table

Apply the modifiers in the next section on top of this. Cost is expressed as a
multiple of Luna medium, combining token price and effort token burn.

| Task | Model | Effort | Cost | Why |
|---|---|---|---|---|
| Read-only exploration, codebase search, "where is X" | Luna | `medium` | 1x | Retrieval and summarization, verifiable by reading the files it cites |
| Trivial ops: commit messages, PR descriptions, renames, lookups | Luna | `low` | 0.35x | Output is inspected immediately; failure is free |
| Well-scoped implementation, clear spec, tests exist | Luna | `high` | 1.75x | Tests are the verification gate, so buy deliberation rather than judgment |
| Test generation | Luna | `high` | 1.75x | Mechanical once behavior is defined; tests either run or they don't |
| Data, SQL, and analysis against a known schema | Luna | `high` | 1.75x | Verifiable by running the query; needs care, not taste |
| Ambiguous or underspecified implementation | Sol | `low` | 9x | Judgment picks the right thing to build; low effort is enough to build it |
| Long-context synthesis across a large repo or doc set | Sol | `medium` | 25x | Weaker models lose the thread; see context_tier below |
| Research and web synthesis | Sol | `medium` | 25x | Source quality and contradiction handling are judgment calls |
| Planning, task decomposition, orchestration | Sol | `medium` | 25x | A bad plan is the most expensive failure in an agent pipeline |
| Architecture, system design, ADRs | Sol | `high` | 44x | Ambiguous, consequential, and hard to reverse |
| Hard debugging and root-cause analysis | Sol | `high` | 44x | Requires holding competing hypotheses and rejecting the easy local fix |
| Code review | Sol | `high` | 44x | The value of review is catching what the author missed |
| Design docs and customer-facing technical writing | Sol | `medium` | 25x | Audience judgment and framing; you will read every word anyway |
| Security review and threat modeling | Sol | `xhigh` | 62x | Async, adversarial, and exhaustive search genuinely pays here |
| Long-running autonomous agentic runs | Sol | `medium` | 25x | See the long-session rules below; do not raise effort to fix drift |

## Modifiers

Apply in order. Each shifts one step along the tier or effort ladder.

**Role in the workflow**

- **Orchestrator or planner**: never downshift. The plan is the highest-leverage
  artifact in the run, and every worker inherits its errors.
- **Fan-out worker** (one of several parallel agents doing bounded work): one
  tier down, but only if the verification gate below is satisfied. Waste
  multiplies across parallel agents, and so does a bad model choice.
- **Final reviewer or synthesizer**: never downshift. This is the last chance to
  catch an error, so it needs judgment, not throughput.
- **Router or triage** (deciding which agent handles this): Luna `low`. Pattern
  matching, not reasoning.

**Stakes and blast radius**

- Output ships to a customer, or lands in a durable artifact such as an ADR or a
  design doc: one effort step up.
- Change is hard to reverse: schema migration, public API shape, infrastructure,
  anything touching production data: one effort step up, and require an approval
  gate before the write.
- Throwaway prototype, spike, or scratch script: one tier down.
- You will read and verify the output yourself in the next minute: one tier
  down. Your review is the verification gate.

## The verification gate

Downshifting is only safe when a mechanism other than the model catches its
mistakes. Before dropping a tier, name the gate:

- A test suite that actually covers the change
- A compiler, type checker, or linter that fails on the error class
- A schema or contract the output must satisfy
- A stronger reviewer model that reads the output before it is used
- You, reading it immediately

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
| Model is correct but too slow for an interactive turn | Effort down one step before tier down. Effort dominates latency. |
| Cheap model failed twice on the same task | Tier up once. Do not retry a third time at the same setting. |

De-escalate when the same task class has succeeded repeatedly at the current
setting with the gate never firing. That is evidence the gate, not the model, is
doing the work.

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
- **Starting at `xhigh` or `max`.** These are destinations reached by evidence,
  not starting points. They cost 2.5x to 4x medium and are frequently worse on
  simple tasks because the model adds unnecessary steps.
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
- **Treating the middle tier as the safe default.** It is dominated on both
  axes. Pick a side.
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

Model facts go stale in weeks. Everything above is written in tiers so it
survives releases; only [references/model-map.md](references/model-map.md) and
[references/evidence.md](references/evidence.md) need updating.

1. Check the vendor model and pricing pages for new IDs, price changes, and
   changes to the supported effort range.
2. Check the harness release notes for newly selectable models and effort levels
   (Copilot CLI model list, Codex, Agents SDK).
3. Re-check whether the current efficient tier still dominates the middle tier.
   That is the single assumption this skill leans on hardest, and a price change
   on any tier can invert it.
4. Update the model map, restamp its date, and adjust the tier table in this
   file only if a tier's occupant changed.
5. Leave the task table, modifiers, gate, and anti-patterns alone unless the
   underlying behavior changed. They are model-independent.
