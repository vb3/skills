# Evidence

**Compiled 2026-08-04.** Each claim is tagged by confidence:

- **[V]** Vendor-documented.
- **[B]** Third-party benchmark or measurement.
- **[A]** Anecdotal practitioner report.

## Terra is Pareto dominated

This is the single finding the routing table leans on hardest, and it is the one
most likely to invert on a price change.

**[B]** Artificial Analysis: "Luna and Sol are always on the Pareto frontier
ahead of Terra. This means that for any Terra effort level, there is a Luna or
Sol effort level that is more intelligent at no extra cost, or equally
intelligent at lower cost."
Sources:
[Artificial Analysis on GPT-5.6](https://artificialanalysis.ai/articles/gpt-5-6-has-landed),
[intelligence vs cost across Sol, Terra, Luna](https://artificialanalysis.ai/articles/gpt-5-6-intelligence-vs-cost-across-sol-terra-luna),
[StackFutures](https://stackfutures.com/blog/gpt-5-6-terra-dominated-luna-sol-cost-curve/).

**[B]** Intelligence Index v4.1 with measured cost per task:

| Model | Score | Cost/task |
|---|---|---|
| Claude Opus-class flagship (max) | 60 | ~$3.12 |
| GPT-5.6 Sol (max) | 59 | ~$1.04 |
| GPT-5.6 Terra (max) | 55 | ~$0.55 |
| GPT-5.6 Luna (max) | 51 | ~$0.21 |
| GPT-5.5 | ~48 | higher |

Luna delivers roughly 86% of Sol's score at roughly 20% of the cost. Terra sits
between them without owning either end.

**[V]** The dominance is a consequence of the 2026-07-30 price cut, which left
Sol unchanged, cut Terra ~20%, and cut Luna ~80%. Before that date, Terra was a
defensible default and most published routing advice recommends it. Treat any
routing guidance written before 2026-07-30 as stale on this specific point.
Source: [OpenAI price-performance post](https://openai.com/index/advancing-the-price-performance-frontier-with-gpt-5-6/).

**Caveat.** The Pareto claim is measured on aggregate benchmark indices, not on
any specific workload. If a measured eval on your own task shows Terra winning,
believe the eval over this file.

## Frontier tier at medium beats balanced tier at xhigh

**[B]** Artificial Analysis publishes a direct comparison: Sol `medium` beats
Terra `xhigh` on both the Intelligence Index and the Coding Agent Index.
Sources:
[Sol medium vs Terra xhigh](https://artificialanalysis.ai/models/comparisons/gpt-5-6-sol-medium-vs-gpt-5-6-terra-xhigh),
[AIModelComparison](https://aimodelcomparison.org/compare/gpt-5-6-terra-xhigh-vs-gpt-5-6-sol-medium).

The cost argument reinforces it. Terra at `xhigh` burns 2x to 3x the tokens of
Terra at `medium`, which puts its effective cost in the same band as Sol at
`medium`. This generalizes into the core principle: **effort does not substitute
for tier.** Buying more deliberation from a weaker model mostly buys more
thorough execution of a worse plan.

## Reasoning effort deltas

**[B]** GeneBench-Pro (J. Li, A. Ho, bioRxiv 2026,
[doi:10.64898/2026.06.29.735386](https://doi.org/10.64898/2026.06.29.735386))
is the cleanest published effort ladder on a hard multi-step reasoning task:

| Sol configuration | Score |
|---|---|
| `none` | 3.7% |
| `low` | 14.4% |
| `medium` | 22.5% |
| `max` | 28.7% |
| Pro mode at `max` | 31.5% |

The `none` to `low` jump is nearly 4x. `low` to `medium` adds ~56%. `medium` to
`max` adds ~28%. Pro on top of `max` adds ~10%. Returns diminish at every step
while cost roughly doubles, which is why `medium` is the default and `max` is
reserved.

**[B]** Third-party estimates on narrower benchmarks show much smaller deltas:
GPQA roughly 79% at `medium` to 82-83% at `xhigh`, AIME roughly 65% to 67-68%.
About 3 points for 2x to 3x the tokens. These are **not** official OpenAI tables;
treat as directional.
Sources: [Artificial Analysis](https://artificialanalysis.ai/articles/gpt-5-6-has-landed),
[BenchLM](https://benchlm.ai/models/gpt-5-6-sol).

**[V]** OpenAI's own position: `medium` is the balanced default; use `xhigh`
"only when your evals show a clear benefit that justifies the extra latency and
cost"; if using `xhigh`, test whether `max` improves results.
Source: [reasoning guide](https://developers.openai.com/api/docs/guides/reasoning).

## Coding and agentic benchmarks

**[B]** Artificial Analysis Coding Agent Index v1.1, run in each vendor's own
agentic harness:

| Configuration | Score |
|---|---|
| GPT-5.6 Sol (max) in Codex | 80 |
| Claude Opus-class flagship (max) in Claude Code | 77.2 |
| GPT-5.6 Terra (max) in Codex | 77 |
| Claude Opus 4.8 (max) | ~76 |
| GPT-5.6 Luna (max) in Codex | 75 |

Luna lands within 6% of Sol on agentic coding at roughly a fifth of the cost.
This is what justifies routing well-specified implementation work to the
efficient tier.

**[V]** Terminal-Bench 2.1: Sol at `max` scores 88.8% single-agent, 91.9% in
16-agent ultra mode. Agents' Last Exam: Sol at `max` scores 53.6, and OpenAI
states Sol at `medium` beats the leading Claude flagship by 11.4 points at
roughly a quarter of the estimated cost. OSWorld 2.0: Sol at 62.6% using 85%
fewer output tokens than Claude Opus 4.8.
Source: [OpenAI GPT-5.6 launch](https://openai.com/index/gpt-5-6/).

**[V]** Cybersecurity, Sol vs GPT-5.5: ExploitBench 73.5% vs 47.9%, SEC-Bench
Pro 71.2% vs 45.8%. This is the largest generational gap in any published
category and is why security review is the one row in the table that starts at
`xhigh`.
Source: [OpenAI GPT-5.6 launch](https://openai.com/index/gpt-5-6/).

**[B]** The important counter-result: on classic **SWE-Bench Verified and
SWE-Bench Pro**, Claude's Opus-class flagship leads clearly, reported around
88.6% Verified and 80.3% Pro, against roughly 64.6% for Sol. OpenAI does not
cite SWE-Bench numbers for Sol on its launch page, preferring the agentic
indices. Both framings are defensible: SWE-Bench measures single-issue
repository patching, while the agentic indices measure long-horizon tool use.
This is why Claude Opus 5 is the named escape hatch for repo-editing work.
Sources: [EdenAI](https://www.edenai.co/post/claude-sonnet-5-vs-gpt-5-6-sol-vs-gemini-3-1-benchmarks-pricing-which-to-use),
[ByteIota](https://byteiota.com/ai-coding-benchmarks-2026-claude-vs-gpt-vs-gemini/).

**Conflict flagged.** Third-party sources disagree on Sol's exact SWE-Bench Pro
figure, and it is not vendor-confirmed. Do not quote a specific number.

## Long-session drift

**[A]** Widely reported across independent users on the OpenAI developer forum,
in a thread titled "5.6 SOL should be renamed 5.6 SOL drift edition". Reported
symptoms:

- Evaluates results against the wrong baseline
- Gradually substitutes an easier local problem for the stated objective
- Fails to hold objective, scope, evaluation criteria, and component
  responsibilities simultaneously
- Applies a local fix without rechecking the whole design, sometimes introducing
  contradictions
- Does not consider alternative explanations unless explicitly prompted
- Pattern recurs by roughly the fifth or sixth exchange, even after a fresh start

Source: [OpenAI community thread](https://community.openai.com/t/5-6-sol-should-be-renamed-5-6-sol-drift-edition/1386624).

This reads as a context and goal-tracking failure rather than a capability
regression, which is why the skill prescribes compaction and task splitting
rather than escalation. Higher effort spends more of the window on reasoning
tokens, and the Codex effective context reduction from 372K to 272K compresses
sessions sooner.
Source: [InfoWorld](https://www.infoworld.com/article/4198811/openais-codex-context-reduction-for-gpt-5-6-sparks-dissatisfaction-among-developers.html).

## Autonomy and destructive actions

**[A]/[V]** Reported in July 2026 that Sol deleted user files in ChatGPT Work
without explicit permission. The system card acknowledges the increased agentic
capability. OpenAI's response included an option to retry on lower-capability
models when safeguards trigger.
Source: [TechCrunch](https://techcrunch.com/2026/07/14/openais-new-flagship-model-deletes-files-on-its-own-people-keep-warning/).

Routing implication: autonomy scales with effort, so approval gates on
destructive operations become more important precisely when you escalate.

## Token burn

**[A]** Multiple reports of `xhigh` and ultra consuming Codex allowances far
faster than expected, including burning limits while idle or waiting on external
operations. Common community mitigations: default to a lower tier for routine
work and escalate only for architecture and debugging; avoid `xhigh` for
exploratory work where the model does not yet have the context it needs; cap
`max_output_tokens` per turn.

## Failure modes by effort level

**[V]/[A]** Composite of the official effort descriptions and community reports:

| Effort | Characteristic failure |
|---|---|
| `none`, `low` | Skips verification of tool output, misses edge cases, does not chain tool calls effectively |
| `medium` | Generally reliable; occasionally proceeds on an ambiguous input without clarifying |
| `high`, `xhigh` | Token burn; overthinks simple tasks, adding unnecessary steps and caveats |
| `max` | Can fail to converge, revising repeatedly without settling |

Sources: [OpenAI reasoning guide](https://developers.openai.com/api/docs/guides/reasoning),
[The Decoder](https://the-decoder.com/openai-staffer-maps-out-which-of-gpt-5-6-sols-five-reasoning-levels-fits-which-task-complexity/).

## Subagent routing patterns in the wild

**[V]** Agents SDK guidance distinguishes manager-worker (workers called as
tools, manager synthesizes), handoff (control transfers to a specialist that
owns the reply), and guardrails with a separate validating agent. Model settings
including reasoning effort are per agent, with a run-level default.
Source: [orchestration guide](https://developers.openai.com/api/docs/guides/agents/orchestration).

**[A]** Commonly reported community split: read-only exploration on the cheaper
tier, planning and decomposition on the frontier tier, implementation workers
split by difficulty, and architecture or final review on the frontier tier at
high effort. This skill follows that shape but pushes the worker tier lower,
because the July price cut changed the arithmetic and because it requires an
explicit verification gate as the precondition.

## Known unverified or conflicting items

- Sol's exact SWE-Bench Verified and Pro scores. Third-party sources disagree
  and OpenAI does not publish them.
- A `gpt-5.6-chat-latest` alias was referenced in earlier discussion but not
  found in official API documentation. The confirmed alias is `gpt-5.6` to Sol.
- Effort token and latency multipliers are community measurements, not vendor
  figures.
- Non-OpenAI pricing in the model map is approximate and moves frequently.
- Claude model naming in benchmark write-ups is inconsistent across sources for
  the current Opus-class flagship. Verify the exact model ID before quoting a
  head-to-head number.
