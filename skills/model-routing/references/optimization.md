# Optimization and diagnosis

Read this reference when a running workflow is unexpectedly expensive, slow,
or unreliable. The routing procedure and model bands remain authoritative in
[`SKILL.md`](../SKILL.md); volatile rates and host controls live in
[`model-map.md`](model-map.md).

## Cost per accepted result

1. Identify the billing regime: API tokens, Copilot AI credits, request-based
   allowances, or another host plan.
2. Inspect actual usage for every attempt. Include cache reads and writes,
   billed reasoning/output, tools, reviewers, service tiers, and long-context
   rates. Keep token categories disjoint.
3. Compare viable configurations on representative tasks with the same
   acceptance gate. Divide the total bill, including failed attempts, by
   accepted results. Report acceptance rate separately.
4. Trial one cheaper change at a time while retaining the gate. When the
   workflow permits, evaluate supported caching and API batch discounts.

A cheap failed attempt is not a saving. When there are no accepted results,
report failure rather than a finite successful-task cost.

## End-to-end latency

Measure request start through accepted result. Record median and tail completion
time, failure or timeout rate, and these components when available:

- queueing and service tier
- prompt prefill and cache lookup
- reasoning and answer generation
- tool execution and serial round trips
- retries and final validation

Change the component that dominates:

| Dominant wait | Candidate change |
|---|---|
| Independent serial tool calls | Batch or parallelize them while preserving dependencies |
| Excess generation or reasoning | Request concise output; trial lower effort through the quality gate |
| Prefill or cache misses | Reuse a stable prefix; trim irrelevant input, especially at massive context |
| Model inference or queueing | Compare qualified model/effort configurations or a supported paid speed tier |
| Failed attempts | Repair context or tools, or trial stronger capability |

There is no universal lever order. Streaming or progress output can improve
perceived waiting without reducing completion time. Background execution frees
the user but does not itself shorten the task. If the quality floor and deadline
conflict, report the conflict and propose narrower scope or a changed budget.

## Diagnose before changing the route

| Observation | Inspect first |
|---|---|
| Correct-looking answer to the wrong problem | Objective, requirements, and supplied context |
| Right approach with missed edge cases | Independent gate, then effort or capability |
| Repeated failure at one configuration | Failure evidence; change a relevant variable rather than blindly retrying |
| Contradictions in a long session | Goals, constraints, compaction, and bounded fresh subtasks |
| Unexpected bill | Usage categories, cache behavior, retries, service tier, and context rates |
| Insufficient context window | Irrelevant material, coherent task splits, then larger supported capacity |

Context capacity, a host's `context_tier`, and a billing threshold are distinct.
Select capacity for the input; calculate price from actual usage and host rules.
