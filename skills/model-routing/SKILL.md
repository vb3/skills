---
name: model-routing
description: Choose models and reasoning effort with access-aware fallbacks and an OpenAI-first Copilot preference. Use when recommending a model, considering subagent assignments, configuring an Agents SDK agent or Codex profile, or diagnosing model cost, latency, or answer quality. Covers GPT-6 Sol, Luna, Astra, and GPT-5.6 Sol Fast. Do not use for ordinary coding or model-name mentions without a routing decision.
---

# Model Routing

Prefer OpenAI for Copilot routing. Choose for task quality first, then optimize
the actual provider bill and elapsed time. A vendor API price is not a Copilot
rate, and a selectable model is not proof that every account can use it.

Read [the model map](references/model-map.md) for current candidates, fallback
chains, and host controls. Read [the evidence](references/evidence.md) before
quoting prices, benchmarks, or release-specific capabilities. Recommendations
are policy; call out where comparative evidence is missing.

## Resolve the route

1. **Identify the host and constraints.** Record provider, available models,
   required tools/modalities, context requirement, and who is waiting. Preserve
   explicit user choices and host-managed defaults. For ordinary Copilot CLI
   delegation, omit model, effort, and context overrides unless the current
   request or applicable persistent instructions explicitly require them;
   `/subagents` resolves the defaults. A recommendation is not authorization
   to rewrite configuration or override those defaults.
2. **Choose judgment capacity.** Use Sol for ambiguous work, plan ownership,
   consequential decisions, and final review. Use Luna for bounded work with
   an independent correctness gate. These are starting roles, not a claim
   that every intermediate or older model is dominated.
3. **Choose deliberation separately.** Use the task table below. More effort
   buys additional reasoning, not a missing specification or guaranteed better
   judgment. Resolve missing intent before retrying at a higher setting.
4. **Check access and fallbacks.** Follow the model-map chain while preserving
   the task's quality, tool, and context requirements. Re-check the fallback's
   effort controls rather than copying unsupported parameters. Report an
   unavailable model and the substitution. If no compatible candidate exists,
   report the blocker rather than silently lowering the quality bar.
5. **Encode only supported controls.** Read the live tool schema or model
   picker, not a model name reconstructed from branding. State when the host
   cannot enforce the recommended effort or context setting.

Completion: one compatible model, an effort choice where supported, a named
verification gate for a worker/downshift, and a fallback when access varies.
For host-default delegation, completion is the advisory route plus omitted
overrides, not an invented claim about which model the host actually ran.

## Starting routes

These are workload heuristics, not benchmark-optimal settings. Sol and Luna
refer to the current candidates in the model map. The table assumes background
work; the latency section governs a human-blocking interaction.

| Task | Candidate | Effort | Gate or reason |
|---|---|---|---|
| Retrieval, codebase search, summaries of specified files | Luna | `medium` | Check cited files and coverage |
| Renames, lookups, commit messages, mechanical edits | Luna | `low` | Inspect the diff or exact expected result |
| Scoped implementation with acceptance tests | Luna | `high` | Existing tests cover behavior; `medium` for simple changes |
| Test generation or SQL against a known schema | Luna | `high` | Independently specified assertions, expected totals, or invariants |
| Ambiguous implementation | Sol | `medium` | Resolve intent first; lower effort for a simple execution step |
| Research, cross-file synthesis, technical writing | Sol | `medium` | Judge source quality, contradictions, and audience |
| Planning owner, orchestrator, final synthesis | Sol | `medium` | Planning errors propagate to workers |
| Architecture, hard debugging, consequential code review | Sol | `high` | Competing hypotheses and expensive missed edge cases |
| Security review, threat modeling | Sol | `high` | Adversarial coverage; trial `xhigh` when deeper review improves results |
| Long autonomous work | Sol | `medium` | Explicit checkpoints and independently checked acceptance criteria |
| Hardest long-horizon coding or synthesis, quality first | Astra if accessible; otherwise Sol | `high` | Stronger-capability route; retain independent verification on the fallback |

**Astra is an allowed quality-first recommendation**, especially for difficult
synthesis, architecture, or persistent failures on Sol. Current vendor
positioning and independent measurements support this role, not a universal
advantage on every task. Always check access and pair it with the Sol fallback
from the model map. Base Copilot Pro lacks both Astra and Sol; use the map's
plan-aware branch rather than promising an unavailable fallback. Preserve the
review gate and choose effort for the task on either model.

**Sol Fast is an allowed latency-oriented recommendation** for a Sol-class
workflow when the exposed model meets its quality requirements. Compare it
with current-generation Sol at the required effort; an older `-fast` model is
not automatically faster end to end or equivalent to GPT-6 Sol. Use its
documented provider rate or observed usage, not an assumed fast-mode premium.

## Effort, role, and stakes

Start at `medium` for an uncovered task. Use `low` for clear mechanical work,
`high` for intricate reasoning and verification, and trial `xhigh` or `max`
only when the additional deliberation addresses an observed gap. Effort levels
are model/host controls, not universal token, cost, or latency multipliers.

Assign bounded workers to Luna only if their return can be checked. Keep plan
owners and final reviewers on a judgment-capable candidate. A worker drafting
one section of a plan is not the planning owner; a worker deciding the overall
architecture is not mechanical just because it runs in parallel.

Raise effort one supported step for extra stakes not already represented by
the selected row, such as an unsupervised final decision. Apply at most one
stakes increase, rather than stacking "customer-facing", "durable", and
"hard to reverse" for the same risk. The architecture and security rows
already account for their usual durability, irreversibility, and customer
exposure; human sign-off is not an additional stakes increase. Keep existing
authorization and rollback requirements independent of model choice or effort.

## Verification gates

Name what catches the error before recommending a cheaper/weaker candidate:
acceptance tests, a type checker for type errors, independent reconciliation
totals for data, an expert reviewing the artifact, or a stronger independent
reviewer. Immediate human reading is sufficient only for errors that reading
would actually reveal.

A passing test written from the same mistaken interpretation is not independent
evidence. SQL execution is not proof of a correct answer. A reviewer that never
flags anything might be ineffective; check it with a known-bad example before
removing it or relying on a lower-cost route.

A worker plus reviewer can improve cost per accepted result, but is not
automatically cheaper than one stronger agent. Count review calls, retries,
tool loops, and the provider's actual billing unit.

## Latency

Distinguish human-blocking interaction, background work with a deadline, and
bulk work with genuine scheduling slack. About ten seconds is a useful UX
attention guideline, not a model SLA or a universal effort ceiling.

For an interactive turn, start with `low` or `medium`, measure time to useful
output and task completion, and keep the required quality. If adequate review
cannot fit the interaction budget, move it to background work and show progress
rather than shipping a shallower review.

Find the bottleneck before changing models:

- Parallelize independent tool calls when serial round trips dominate; avoid
  adding subagents to a small task that can be finished directly.
- When generation dominates, shorten unnecessary output and trial lower effort
  against the same quality gate. Higher effort does not have a fixed time cost.
- Reuse a stable prompt prefix where the provider supports caching. Measure
  cache hits; use only that provider's documented controls.
- Compare compatible models, including Sol Fast, using the same inputs, tools,
  effort, and output requirements. Provider queues and time to first useful
  output matter as well as token throughput.

Streaming helps perceived progress, not completion time. Reducing irrelevant
context can help quality, cost, and sometimes latency; do not discard needed
evidence to meet an arbitrary prompt length. Published throughput alone cannot
rank short interactive turns.

Use an API's batch discount only when that API, endpoint, model, and turnaround
meet the deadline. A Copilot background task is not an OpenAI Batch API job.
An overnight deadline is not automatically compatible with a 24-hour window.
When an eval measures production behavior, preserve the production model and
effort instead of changing what is being measured to save money.

## Cost and vendor choice

Under Copilot, use current Copilot rates and observed usage, including any
account discounts. Under a direct API, use that API's token/cache/tool rates.
For a plan that still uses request multipliers, use those instead. The model
map separates these regimes; never convert API prices to Copilot charges by
assumption.

Compare **cost per accepted result**, including failed attempts and review,
alongside quality and p50/p95 elapsed time. Prefer OpenAI when it meets the
requirements. This is a provider-aware default, not a claim that every OpenAI
model costs less than every Claude model.

Use Claude or another family when explicitly requested, required by the host
or a capability, useful for an explicitly required independent-family critique,
or demonstrably better on the user's workload enough to justify its actual
cost. Repository issue fixing alone is not an automatic Claude override.
Allow an older or intermediate model to win a representative comparison.

## Failures and escalation

| Observation | Next action |
|---|---|
| Correctly executes the wrong intent | Repair the specification; trial Sol if the prompt was already adequate |
| Correct direction, missing edge cases | Increase effort one supported step and repeat the relevant check |
| Sol still fails a well-specified hard task | Compare Astra if available, otherwise improve decomposition or use a justified alternate model |
| Access denied, unsupported model, or missing capability | Use the compatible availability fallback; do not mislabel it a quality failure |
| Rate limit or transient service error | Respect retry guidance; distinguish service recovery from a model capability decision |
| Decisions drift during a long session | Restate constraints, compact, or split into bounded fresh contexts |
| Same failure twice without new evidence | Stop identical retries; inspect the task, context, and tools |
| Repeated success with a proven gate | Trial one cheaper setting at a time while keeping the gate |

Do not retry a possibly completed external write just because a model call
failed. Verify the existing action's state before redispatch. If it completed,
report that result; fallback alone does not authorize another write or comment.

## Context and host encoding

Use `long_context` only when needed and supported by the selected model.
It is a capacity option, not a quality boost or a known numeric window.
Check product limits separately from vendor API limits. Prefer bounded inputs
and a synthesis step when that preserves the cross-file relationships.

For API code, validate the model ID and reasoning settings against the API's
own registry/docs. For VS Code, use the exact available model label. Copilot
CLI IDs are not evidence of API availability or VS Code display names.
The [harness reference](references/model-map.md#harness-syntax) shows the
verified controls and the limits of the current snapshot.

## Answer format

State the model, effort, and task-specific reason briefly. Include the access
fallback for Astra or another availability-sensitive recommendation; add a
cheaper alternative only when it is distinct and has an adequate gate. Mark an
unmeasured recommendation as provisional rather than quoting invented savings.

> GPT-6 Sol at high effort for root-cause analysis. GPT-6 Luna at high is
> sufficient if a reproducer isolates the bug and independently checks the fix.

## Refreshing

Refresh when a model, provider rate, entitlement, or harness control changes:

1. Inspect primary sources and the live host schema separately. Record source
   dates, supported claims, conflicts, and unknowns in the evidence file.
2. Update candidates and fallback chains in the model map. Re-check tools,
   context, effort support, and the billing regime for each fallback.
3. Revisit task routes only where new evidence changes them. Do not carry
   generational benchmark rankings or fixed effort-cost ratios forward.
4. Update the behavioral evals, including access failure, host defaults, exact
   IDs, provider economics, and the negative trigger case.
5. Run the structural validator documented in the repository README. Review
   the eval responses against their mandatory expectations; structural
   validation alone says nothing about routing quality.
