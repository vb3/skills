---
name: model-routing
description: Choose an OpenAI or Claude model and reasoning effort for cost or latency. Use before delegating to an AI agent, configuring an agent harness, selecting Luna, Terra, Sol, Astra, Haiku, Sonnet, Opus, or Fable, or diagnosing a run that is too slow, expensive, or unreliable.
---

# Model Routing

## Inputs

For a routing decision, accept two preferences:

| Input | Values | Objective |
|---|---|---|
| `family` | `openai`, `claude` | Stay within this provider family |
| `optimize_for` | `cost`, `latency` | Minimize cost or time per accepted result |

Accept named values or ordinary language, such as `openai cost` or
`claude latency`. Infer the task, acceptance criteria, host, and deadline from
the surrounding request.

Ask for a missing preference only when it changes a user-facing recommendation.
If both are material and missing, ask family first, then optimization goal on
the next turn. For autonomous routing, use the family already selected,
otherwise the current model's family when it is OpenAI or Claude, otherwise
OpenAI. Default the objective to cost. State applied defaults.

An explicit user model choice overrides the local starting policies below.
State unmet requirements or missing verification without claiming the choice is
validated. Model selection does not authorize delegation, external writes, or
additional spending.

## Route

1. **Constrain.** Resolve the two inputs, quality floor, verification gate,
   deadline, host controls, and billing regime. The step is complete when every
   constraint is known or explicitly marked unknown.
2. **Select.** Choose a capability band and effort from the tables below, then
   apply the selected objective. Treat unmeasured choices as provisional. The
   step is complete when one in-family configuration clears the known floor.
3. **Encode.** Before emitting configuration or dispatching, read
   [harnesses.md](references/harnesses.md) and check the live host schema. Use
   only supported IDs and controls. The step is complete when the exact host
   representation is verified.
4. **Report.** State family, objective, model, effort, and one reason. Include
   the gate, blocker, or material uncertainty. Dispatch only when already
   authorized.

For a running workflow that is unexpectedly expensive, slow, or unreliable,
read [optimization.md](references/optimization.md) before rerouting. Before
quoting volatile prices, limits, defaults, caching behavior, or host controls,
read [model-map.md](references/model-map.md). For benchmark provenance or skill
maintenance, read [evidence.md](references/evidence.md).

## Capability

| Band | OpenAI | Claude | Starting use |
|---|---|---|---|
| **Efficient** | GPT-5.6 Luna | Claude Haiku 4.5 | Bounded, independently verifiable work |
| **Balanced** | GPT-5.6 Terra | Claude Sonnet 5 | Everyday work after Efficient misses the floor |
| **Frontier** | GPT-5.6 Sol | Claude Opus 5 | Ambiguity, consequential judgment, or final review |
| **Advanced** | GPT-6 Astra | Claude Fable 5.1 | Demanding reasoning or sustained agency when it improves the objective |

The pairs are role counterparts, not claims of equal quality, cost, token use,
or speed. Duration alone does not require Advanced; Sol and Opus also support
long-running work.

Apply these local starting policies:

- Start bounded workers on Efficient only when an independent gate catches the
  relevant error class.
- Start owners of consequential plans and final reviewers on Frontier.
- Keep specialists at the capability their individual work requires; fan-out
  changes total cost, not the worker's quality floor.
- Compare Frontier and Advanced for demanding reasoning or agency. When neither
  is ruled out and no measurements exist, run a bounded Frontier pilot and
  evaluate Advanced before scaling.

A gate can be an existing behavioral test, independently derived expected
value, reconciliation total, reference implementation, or qualified reviewer.
A gate must catch the failure being risked: compilation does not prove correct
requirements, and model-written tests can preserve the model's misunderstanding.
If an explicit model choice has no qualifying gate, state what remains
unverified. Preserve approval and rollback requirements for production data,
public contracts, destructive actions, and other high-blast-radius work.

## Effort

| Model | Provisional start when supported |
|---|---|
| Luna, Terra, Sol | `low` for simple execution; `medium` for ordinary reasoning; `high` for complex or consequential work |
| Astra | `high` for demanding reasoning or agency |
| Sonnet 5, Opus 5, Fable 5.1 | `high`; trial `medium` or `low` when the gate shows quality holds |
| Haiku 4.5 | No effort parameter; omit it |

Claude's API defaults to `high` for Sonnet, Opus, and Fable; GPT-5.6 defaults
to `medium`; Astra's omitted-effort default was not verified. Set effort
explicitly when the host supports it. Effort labels are not equivalent across
families. Use `xhigh` or `max` when representative evaluations justify the
additional cost or time. Prompt wording is not a substitute for an unavailable
host control.

## Objective

| Optimize for | Decision rule |
|---|---|
| **Cost** | Choose the lowest measured total bill per accepted result above the quality floor. Include failed attempts, cache operations, tools, and reviewers under the caller's actual billing regime. |
| **Latency** | Choose the lowest measured end-to-end time per accepted result above the quality floor. Include queueing, model calls, tools, retries, and validation; track tail latency and failures. |

Without measurements, use the capability and effort policies as provisional
priors. Luna for verified work and Sol for judgment is an OpenAI aggregate cost
prior, not a ban on Terra. Haiku can lose to Sonnet on successful-task cost.
Astra or Fable can offset higher unit prices through fewer tokens, retries, or
recovery loops. For latency, throughput and time to first token are diagnostics,
not substitutes for full-workflow completion time.

If the preferred model is unavailable, choose another in-family model only when
it still satisfies required capability and integration constraints. A
lower-band fallback needs a qualifying gate. Otherwise report the blocker and
the minimum change that would make a valid route possible.

## Answer

Give one concise decision:

> OpenAI + cost: Sol at high effort for the public API redesign. Contract
> review and compatibility tests are the gate; trial medium only if they hold.

Offer an alternative only when it resolves a real tradeoff, and state its
precondition. Mark provisional recommendations and unenforced effort controls.
