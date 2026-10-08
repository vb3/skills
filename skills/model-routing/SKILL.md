---
name: model-routing
description: Choose OpenAI or Claude models and effort for cost or latency, with access-aware fallbacks and an OpenAI-first Copilot default. Use for model recommendations, subagent assignments, agent harness configuration, or runs that are too slow, expensive, or unreliable. Do not use for ordinary coding or model-name mentions without a routing decision.
---

# Model Routing

## Inputs

For a routing decision, accept two preferences:

| Input | Values | Objective |
|---|---|---|
| `family` | `openai`, `claude` | Stay within this provider family |
| `optimize_for` | `cost`, `latency` | Minimize cost or time per accepted result |

Accept named values or ordinary language, such as `openai cost` or
`claude latency`. Infer the task, acceptance criteria, host, and deadline.

Ask for a missing preference only when it changes a user-facing recommendation.
If both are material and missing, ask family first, then optimization goal on
the next turn. For autonomous routing, preserve an already selected family;
otherwise prefer OpenAI under Copilot, or the current OpenAI/Claude family on
other hosts. Default to OpenAI if neither applies, and to cost. State defaults.

Explicit user model choices override local starting policies. State unmet
requirements without claiming the choice is validated. Model selection does
not authorize delegation, external writes, or additional spending.

For ordinary Copilot CLI delegation, leave model, effort, and context overrides
unset unless the current request or persistent instructions require them.
`/subagents` owns those defaults; advisory routing is not configuration.

## Route

1. **Constrain.** Resolve the inputs, quality floor, independent gate, deadline,
   host controls, access, and billing regime. Finish with each constraint known
   or explicitly marked unknown.
2. **Select.** Choose a capability band and effort below, then apply the objective.
   Treat unmeasured choices as provisional. Finish with a compatible route or
   an explicit blocker.
3. **Encode.** Before configuration or dispatch, read
   [harnesses.md](references/harnesses.md) and check the live schema. Finish with
   verified IDs and supported controls, or omitted host-managed overrides.
4. **Report.** State family, objective, model, effort, and one reason. Include
   material uncertainty, the gate, and an access fallback when needed. Dispatch
   only when authorized.

For access-sensitive recommendations, read the fallback and plan guidance in
[model-map.md](references/model-map.md#access-and-fallbacks). For unexpectedly
expensive, slow, or unreliable runs, read [optimization.md](references/optimization.md).
Before quoting prices, limits, defaults, caching, or migration constraints,
read [model-map.md](references/model-map.md). For benchmark provenance or skill
maintenance, read [evidence.md](references/evidence.md).

## Capability

| Band | OpenAI | Claude | Starting use |
|---|---|---|---|
| **Efficient** | GPT-6 Luna | Claude Haiku 5.5 | Bounded, independently verifiable work |
| **Balanced** | GPT-6 Luna or GPT-6.1 Sol | Claude Sonnet 5.5 | Everyday work, selecting the lightest route that clears the floor |
| **Frontier** | GPT-6.1 Sol | Claude Opus 5.5 | Ambiguity, consequential judgment, or final review |
| **Advanced** | GPT-6 Astra | Claude Fable 5.1 | Demanding reasoning or sustained agency |

These are role counterparts, not equal quality, price, token use, or speed.
Balanced is a task route, not a separate OpenAI model: choose Luna for bounded,
independently checkable work and Sol for nuance or judgment beyond Luna's floor.
Duration alone does not require Advanced. Preserve validated legacy routes and
explicit versions; repeat quality/effort checks on upgrades.

Apply these local starting policies:

- Start bounded workers on Efficient only with a gate for the relevant errors.
- Start consequential planning owners and final reviewers on Frontier; keep
  each specialist at the capability its work requires.
- Compare Frontier and Advanced for demanding reasoning or agency. Without
  measurements, begin a bounded Frontier pilot before scaling. For explicitly
  quality-first hardest work, Advanced is a valid provisional starting route;
  include an available, compatible fallback rather than requiring it everywhere.

A gate can be existing behavioral tests, independent expected values,
reconciliation totals, a reference implementation, or qualified review.
Compilation does not prove correct requirements; model-written tests can
preserve a misunderstanding. If an explicit model choice has no qualifying gate,
state what remains unverified. Preserve approval and rollback requirements for
production data, public contracts, and destructive actions.

## Effort

| Model | Provisional start when supported |
|---|---|
| Luna, Sol, Opus 5.5 | `low` for simple execution; `medium` for ordinary reasoning; `high` for complex or consequential work |
| Astra | `high` for demanding reasoning or agency |
| Sonnet 5.5 | `medium` for specified agentic work; `low`/`medium` for chat; `high` for harder reasoning |
| Haiku 5.5 | `low` for chat, short tool tasks, or simple high-volume work; `medium` for ordinary work, including agentic coding; `high` for longer agent tasks or strict instruction following |
| Fable 5.1 | `high`; trial lower effort when the gate holds |
| Legacy Haiku 4.5 | No effort parameter; omit it |

These are policies, not inherited API settings. Set effort only when authorized
and supported; otherwise mark it unenforced. Version defaults and thinking
controls differ. Use `xhigh`/`max` when evaluations justify the additional cost
or time. Account for a risk once, rather than stacking overlapping stakes;
quality/approval requirements remain independent of effort.

## Objective

| Optimize for | Decision rule |
|---|---|
| **Cost** | Lowest measured total bill per accepted result above the quality floor, including failed attempts, cache operations, tools, workers, and reviewers under the actual billing regime |
| **Latency** | Lowest measured end-to-end time to an accepted result above the floor, including queues, model calls, tools, retries, and validation; track tails and failures |

Without measurements, the tables are provisional priors, not cross-generation
benchmark rankings. Worker-plus-reviewer is not automatically cheaper.
Astra/Fable can offset unit prices through fewer failures or recovery loops.
Sol Fast is an allowed host-specific latency candidate when a comparison supports
it; its name proves neither current-Sol quality nor API-tier pricing.

Honor a selected family. When none is selected, Copilot's OpenAI preference
yields to required capabilities or a representative workload result favoring
another provider. Compare actual provider charges, not API prices imported into
Copilot or fixed effort multipliers. Throughput is not full-workflow latency.

If the preferred model is unavailable, follow the map only while preserving
quality, tools, context, and supported effort. A lower-band fallback needs a
qualifying gate; otherwise report the blocker and the minimum enabling change.

## Answer

> OpenAI + cost: GPT-6.1 Sol at high for the public API redesign. Contract review
> and compatibility tests are the gate; trial medium only if they hold.

Give one concise decision. Mark provisional routes and unenforced controls.
Include a compatible access fallback for sensitive choices such as Astra or
Sol Fast; an unavailable or unqualified fallback is a blocker, not a solution.
Offer other alternatives only when they resolve a real tradeoff.
