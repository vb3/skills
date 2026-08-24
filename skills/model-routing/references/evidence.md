# Evidence

**Compiled 2026-08-04. Speed and latency sections added 2026-08-24.** Each
claim is tagged by confidence:

- **[V]** Vendor-documented.
- **[B]** Third-party benchmark or measurement.
- **[A]** Anecdotal practitioner report.

## Terra is off the cost frontier, and the speed axis does not rescue it

This is the single finding the routing table leans on hardest, and it is the one
most likely to invert on a price change.

**State it precisely.** Terra is *not* strictly dominated by either sibling on
its own: it scores higher than Luna (55 vs 51) and costs less than Sol. The
claim is that the frontier traced jointly by Sol and Luna *across effort levels*
lies outside Terra **on the cost axis**, so for a given Terra configuration
there is usually a Luna or Sol configuration that is better on one axis without
being worse on the other. Saying "Terra is dominated on both axes" is wrong and
should not be repeated.

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
between them without owning either end, which is the whole of the argument
against it on cost. Note that Terra beats Luna on score here; the case against
Terra is positional, not that it is bad.

**[V]** The dominance is a consequence of the 2026-07-30 price cut, which left
Sol unchanged, cut Terra ~20%, and cut Luna ~80%. Before that date, Terra was a
defensible default and most published routing advice recommends it. Treat any
routing guidance written before 2026-07-30 as stale on this specific point.
Source: [OpenAI price-performance post](https://openai.com/index/advancing-the-price-performance-frontier-with-gpt-5-6/).

### Does the speed axis change the conclusion? No.

This was the obvious objection to the barbell, and it was investigated
specifically. It does not hold up.

**[B]** Measured output speed, at a fixed effort level:

| Model | Output TPS | Intelligence |
|---|---|---|
| Luna | 140-149 | 51-52 |
| Terra | 105-121 | 55-57 |
| Sol | 72-110 | 59-61 |

Read naively, this puts all three on a speed-versus-intelligence frontier, since
none dominates another on both. **That reading is wrong, because it holds effort
fixed while this skill treats effort as a free variable.**

End-to-end generation time is roughly `tokens / rate`. Effort multiplies the
token count several-fold; the model sets the rate. So exactly as with cost,
varying effort lets the endpoints enclose the middle. Using the midpoint rates
above and the effort multipliers from the model map, seconds per 1,000-token
medium-effort baseline:

| | `low` | `medium` | `high` | `xhigh` | `max` |
|---|---|---|---|---|---|
| **Luna** | 2.4 | 6.9 | 12.1 | 17.2 | 27.6 |
| **Terra** | 3.1 | 8.8 | 15.5 | 22.1 | 35.4 |
| **Sol** | 3.8 | 11.0 | 19.2 | 27.5 | 44.0 |

Now apply the one published quality head-to-head between these two models, from
the section below: **Sol at `medium` beats Terra at `xhigh`** on both the
Intelligence Index and the Coding Agent Index. Sol `medium` takes ~11.0 s
against Terra `xhigh` at ~22.1 s. Sol is simultaneously faster *and* better, so
Terra `xhigh` is dominated on both axes at once. The same enclosure argument
that removes Terra from the cost frontier removes it from the latency frontier.

**Conclusion: the barbell survives on both frontiers, for the same structural
reason.** The latency answer inside the OpenAI family is Sol at lower effort
when judgment is needed and Luna when it is not. It is not Terra.

**Where the argument genuinely runs out.** At the `low` end the three models are
within about 1.4 seconds of each other, and no published data establishes
quality at matched low effort, so nothing here proves Terra is dominated at
`low`. The claim is that Terra has no *demonstrated* latency slot, not that one
is impossible. A measured eval on a specific workload still outranks this file.

Note also that time to first token does not separate these three models: all are
reported under a second and within ~0.1 s of each other. TTFT differences matter
between *vendors*, not within the GPT-5.6 family.

**Conflict flagged.** Two independent research passes over the same source
returned different TPS figures: 140/121/72 and 149/105-120/90-110 for
Luna/Terra/Sol. The ordering and the rough 2x spread between Luna and Sol are
consistent across both; the individual numbers are not. Do not quote a specific
TPS figure. The conclusion above depends only on the ordering and on the
published Sol-medium-beats-Terra-xhigh result, both of which are robust to the
disagreement.

**Caveat.** Both Pareto claims are measured on aggregate benchmark indices, not
on any specific workload. If a measured eval on your own task shows Terra
winning, believe the eval over this file.

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

## Latency mechanics

**[V]** OpenAI's latency guidance gives the load-bearing asymmetry: "cutting
50% of your output tokens may cut ~50% of your latency", while "cutting 50% of
your prompt may only result in a 1-5% latency improvement". Reasoning tokens
are generated at the output rate, so effort is a latency control and prompt
size essentially is not.
Source: [latency optimization guide](https://developers.openai.com/api/docs/guides/latency-optimization).

**[V]** OpenAI positions the effort ladder explicitly against latency: `none`
for "latency-critical tasks that do not benefit from any reasoning" such as
voice and classification, `low` for "efficient reasoning with a modest latency
increase", `medium` as the "well-balanced point on the pareto curve of latency,
performance and cost", and `high` and above for cases where "quality and
intelligence matter more than latency".
Source: [reasoning guide](https://developers.openai.com/api/docs/guides/reasoning).

**[V]** Anthropic's production multi-agent system reports that parallelizing
subagents and tool calls "cut research time by up to 90%" on complex queries.
This is the largest single latency win documented anywhere in this file, and it
is an orchestration change rather than a model change.
Source: [Anthropic multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system).

**[V]** From the same source, an important limit on fan-out: token usage alone
explained 80% of performance variance on their evaluation, and spawning large
numbers of subagents for simple queries was a recorded failure mode. Fan-out
buys wall clock only to the extent the work is genuinely independent.

**[B]** Human response-time thresholds, unchanged since Miller (1968) and Card
et al. (1991): 0.1 s feels instantaneous, 1 s is the limit for uninterrupted
flow of thought, 10 s is the limit for holding attention, after which users
reorient on return.
Source: [Nielsen](https://www.nngroup.com/articles/response-times-3-important-limits/).

**[B]** Speculative decoding yields a measured 2x to 3x latency improvement
with identical outputs, implemented provider-side and therefore already
reflected in published TPS figures rather than available as a lever.
Source: Leviathan et al., [arXiv:2211.17192](https://arxiv.org/abs/2211.17192).

**Derived, not measured.** The claim that a small model at high effort can
finish later in wall clock than a large model at low effort follows from two
verified facts (reasoning tokens are clocked at the output rate; effort
multiplies reasoning tokens several-fold) but **no published experiment
measuring this crossover was found**. It is stated in the skill as a mechanism,
not as a benchmark result, and should not be quoted as one.

**Not found.** No published study measures the latency at which a developer
abandons or rejects an AI coding suggestion. The widely repeated "300 ms for
inline completions" figure is practitioner lore. The GitHub Copilot
productivity study (Peng et al., [arXiv:2302.06590](https://arxiv.org/abs/2302.06590))
measures task completion time, not latency sensitivity.

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
  figures. A targeted search for a primary source found only qualitative
  language in the OpenAI docs.
- Output TPS figures for Sol, Terra, and Luna differ between research passes;
  only the ordering is reliable. See the conflict note above.
- All TTFT figures in the model map are secondary estimates. Artificial
  Analysis renders its TTFT provider pages in JavaScript and they could not be
  fetched directly.
- Gemini 3.7 Flash TTFT is reported as both ~0.4 s and ~10-12 s by different
  sources. The likely reconciliation is first *thinking* token versus first
  *answer* token, but this is inference, not confirmation.
- Grok 4.5 and 4.6 output TPS is contradicted across sources by two orders of
  magnitude; treat as a data gap rather than an estimate.
- Non-OpenAI pricing in the model map is approximate and moves frequently.
- Claude model naming in benchmark write-ups is inconsistent across sources for
  the current Opus-class flagship. Verify the exact model ID before quoting a
  head-to-head number.
