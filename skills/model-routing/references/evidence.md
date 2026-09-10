# Evidence and maintenance

**Rechecked 2026-09-09.** Distinguish vendor facts, benchmark observations, and
local policy. Two reviewers agreeing establishes neither measured performance
nor factual truth; primary sources and workload evidence remain necessary.

## Vendor positioning

OpenAI recommends Astra for most reasoning workloads and describes gains on
complex end-to-end work, including fewer output tokens and lower estimated API
cost per task on several evaluations despite higher unit prices. These are
vendor results on specific workloads, not proof that Astra is always cheaper
or faster.

Sources: [Astra guide](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md),
[Astra model page](https://developers.openai.com/api/docs/models/gpt-6-astra).

Anthropic's choosing guide supports efficiency-first routing with Haiku or
capability-first routing with Opus. It positions Fable for the most demanding
reasoning and long-horizon work. Opus also supports multihour autonomous work,
so duration alone does not distinguish them. Anthropic's relative latency
labels are Haiku fastest, Sonnet fast, Opus moderate, and Fable slower.

Sources: [choosing a model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model),
[model overview](https://platform.claude.com/docs/en/models/overview),
[Fable guide](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1).

**Local policy:** the four role bands, Frontier starting point for consequential
judgment, independent gates, and bounded pilots before scaling are this skill's
routing choices. They are not claims that vendors prescribe the same ladder.
In particular, retaining Sol as a cost-conscious starting candidate is not a
restatement of OpenAI's Astra-first recommendation.

## Cost evidence has a defined scope

Artificial Analysis reports a Luna/Sol frontier ahead of Terra across effort
levels on its Intelligence Index versus cost-per-task evaluation. That supports
trying Luna for verifiable work and Sol for judgment as an **aggregate cost
prior**.

Source: [GPT-5.6 intelligence versus cost](https://artificialanalysis.ai/articles/gpt-5-6-intelligence-vs-cost-across-sol-terra-luna).

It does not establish that Terra loses on every workload, that the same result
holds for Claude, or that cost dominance implies latency dominance. It also
does not compare Astra. A task-specific result at the required quality floor
overrides this prior.

Published token prices are not task costs. Different tokenizers, reasoning,
cache behavior, tool use, and failure rates change the bill. This revision
removes the old synthetic effort-cost grids: uniform effort multipliers were
not supported across these models, particularly Astra and Claude.

## Latency mechanisms, not universal rankings

OpenAI's latency guide says halving output tokens *may* roughly halve generation
latency. Its 1-5% benefit example for halving input explicitly excepts massive
contexts. Neither heuristic establishes total time for a tool-using workflow.
Select the optimization that targets the measured bottleneck.

Source: [OpenAI latency optimization](https://developers.openai.com/api/docs/guides/latency-optimization).

Reasoning can interleave with visible output. Streaming, a short preamble, and
progress updates can reduce perceived waiting, though they do not necessarily
shorten completion time. Effort is adaptive and model-dependent; it is not a
fixed token or time multiplier.

Sources: [OpenAI reasoning](https://developers.openai.com/api/docs/guides/reasoning),
[Claude effort](https://platform.claude.com/docs/en/build-with-claude/effort).

**Inference to measure:** a smaller model can take longer if it generates more
tokens or requires retries; a stronger model can reduce full-workflow time
despite slower generation. This is not a measured ranking of the eight models.
The prior TTFT table mixed unverified measurements and percentiles; it has been
removed rather than used to promise a latency ladder.

The roughly ten-second human-attention heuristic is UX background, not a model
SLA and not evidence for a universal `medium` effort ceiling.

Source: [Nielsen response-time limits](https://www.nngroup.com/articles/response-times-3-important-limits/).

## Operational corrections

The source-backed details live in [model-map.md](model-map.md), including:

- Sol's promotion runs at least through the published date; no automatic price
  reversion is established.
- OpenAI implicit caching can reuse earlier eligible prefixes despite a changing
  suffix. Usage evidence is needed before attributing an unexpected bill.
- Model effort support and API defaults differ, and Haiku has no effort
  parameter.
- API pricing, Copilot billing, context capacity, and host context controls
  are separate.
- Astra async tools and Fable thinking/history constraints need application
  support; a model selection alone cannot supply it.

## Refreshing the skill

1. Read current vendor model, pricing, effort, caching, and integration pages.
   Verify both API and host-specific billing. Recheck Sol's promotion around
   2026-11-21 rather than scheduling an assumed price change.
2. Inspect the live dispatch schema for exact IDs and supported controls.
   Separate public product availability from availability in this host.
3. Re-evaluate cost per accepted result and end-to-end latency independently.
   Use the same representative tasks and acceptance gate, record model/version,
   effort, host, concurrency, cache state, prices, and failure/timeout rates.
4. Update facts and dates in the model map. Revise policy only when its premises
   changed, labeling local choices separately from vendor guidance.
5. Update affected behavioral fixtures in `../evals/evals.json`. Run the existing
   structural validator, then review or execute the scenarios. JSON/schema
   validity is not evidence that routing behavior passed.

## Remaining uncertainties

No controlled workload comparison was run for all eight counterparts in this
repository. Astra's omitted-effort default, the internal Copilot Sol Fast
entry's price, and current VS Code display labels remain unverified here.
Public model catalogs and live host availability can differ. Treat numerical
performance promises without a matching workload measurement as unsupported.
