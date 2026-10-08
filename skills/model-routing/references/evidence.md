# Evidence and maintenance

**Primary sources rechecked 2026-10-08.** Vendor positioning, comparative
measurements, and local routing policy are separate. Reviewer agreement is
not performance evidence.

## Current vendor positioning

OpenAI positions Luna for focused high-volume work, GPT-6.1 Sol for
near-Astra complex work at lower cost, and Astra for highest intelligence.
Its guide suggests Sol medium for revisable complex work and xhigh for
demanding polished deliverables, with same-task Sol/Astra comparisons.
Those are vendor starting points, not universal optima.

The current guide focuses on Luna, Sol, and Astra rather than a separate Terra
tier. Retaining Terra as a legacy or access fallback is this skill's routing
policy.

Sources: [GPT-6 guide](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md),
[selection guide](https://developers.openai.com/api/docs/guides/model-selection),
[GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

Anthropic recommends Opus 5.5 for most workloads and Fable 5.1 for demanding
reasoning or long-horizon work where Opus falls short. Opus defaults to medium;
Sonnet 5.5's API default stays high, with medium suggested for specified agentic
work and low/medium for chat. Compare workload results rather than effort labels.

Anthropic positions Haiku 5.5 for high-volume, cost-sensitive, narrowly scoped
work: classification, extraction, summaries, compaction, subagents, and
speed-sensitive support or browser use. It states that Sonnet 5.5 and Opus 5.5
remain better for complex agentic coding. Its claim that Haiku 5.5 costs
around 75% less to run than Haiku 4.5 on average is a vendor estimate. GitHub's
report that Haiku 5.5
"matched Claude Sonnet 5 on many coding tasks" in early testing names no tasks
or method; it is not parity with Sonnet 5.5 or with this user's workloads.

Sources: [Claude overview](https://platform.claude.com/docs/en/models/overview),
[Claude effort](https://platform.claude.com/docs/en/build-with-claude/effort),
[Haiku 5.5 announcement](https://www.anthropic.com/claude-haiku-5-5),
[Copilot Haiku 5.5](https://github.blog/changelog/2026-10-07-claude-haiku-5-5-in-github-copilot/).

**Local policy:** OpenAI-first Copilot recommendations when no family is chosen,
independent gates, Frontier for consequential decisions, and bounded pilots
are this skill's choices. Explicit families and measured exceptions still win.
Role bands are not benchmark equivalences.

## Access and economics

The [September 29 Copilot announcement](https://github.blog/changelog/2026-09-29-gpt-6-1-sol-in-github-copilot/)
confirms GPT-6.1 Sol for Pro+, Max, Business, and Enterprise with gradual rollout.
The [September 22 announcement](https://github.blog/changelog/2026-09-22-openais-gpt-6-sol-and-gpt-6-luna-now-available/)
includes base Pro for Luna, not Sol. The [October 7 announcement](https://github.blog/changelog/2026-10-07-claude-haiku-5-5-in-github-copilot/)
adds Haiku 5.5 for Pro and above, enabled unless an administrator disables it.
Plan-aware fallback guidance
and exact rates live in [model-map.md](model-map.md#access-and-fallbacks).

GPT-6.1 Sol halves GPT-6 Sol's cache-read rate while input/output remain $2/$10.
Opus 5.5 falls to $4/$20 with $0.20 cache reads. Sonnet 5.5 cache reads fell
to $0.10 on October 7; Anthropic estimates about 20% lower cost on most agentic
work. Haiku 5.5's prices jump 5x above 100K prompt tokens. These are unit-price
changes, not task-cost measurements. Paid Auto's discount does not enforce a model.

No new OpenAI model IDs appeared through October 8. GPT-6.1 Sol gained
Ultrafast, and GPT-6 Luna gained the Decisions API beta. Do not plan routes
around unannounced model IDs.

## Historical benchmark boundaries

The upstream September 23 refresh recorded Artificial Analysis `max` snapshots:
Astra index 53 / 52 output tokens/s / $3.26 average evaluation cost; GPT-6 Sol
48 / 113 / $1.06; Luna 37 / 131 / $0.07. They support considering Astra
for quality and Luna for checked volume, not a ranking at medium effort,
on Copilot, or for the newer GPT-6.1 Sol and Claude 5.5. Index version was not
established; do not combine them with older generations' index scores.

Historical sources: [Astra](https://artificialanalysis.ai/models/gpt-6-astra),
[GPT-6 Sol](https://artificialanalysis.ai/models/gpt-6-sol),
[Luna](https://artificialanalysis.ai/models/gpt-6-luna).

The earlier [GPT-5.6 cost frontier](https://artificialanalysis.ai/articles/gpt-5-6-intelligence-vs-cost-across-sol-terra-luna)
also does not establish current-model or latency dominance. Re-evaluate
representative tasks before claiming a winner.

## Latency and verification

OpenAI's [latency guide](https://developers.openai.com/api/docs/guides/latency-optimization)
suggests output reduction can reduce generation time, while its small-input
heuristic exempts massive contexts. Measure prefill, generation, queues,
tools, retries, and validation separately. Streaming/progress can improve
perceived waiting without shortening completion time.

No same-host, same-task eight-model timing comparison was run for this refresh.
Vendor fastest/moderate/slower labels and historical throughput are not SLAs.
Likewise, injected-context routing fixtures test guidance, not discovery,
live model access, or workload performance.

## Refresh procedure

1. Check vendor price, effort, cache, migration, and Copilot access/billing
   sources. Record dates and unresolved claims in the map.
2. Check the dispatch schema and account access independently; preserve
   host-managed defaults and validate each fallback's tools/context/effort.
3. Compare accepted-result cost and p50/p95 time using the same tasks, gate,
   host, tools, and cache/concurrency conditions.
4. Update candidates and fixtures, retaining explicit legacy choices and
   identifying local policy separately from vendor guidance.
5. Run the repository structural validator and affected behavioral scenarios.
   Report whether discovery, injected-context guidance, or workload tests ran.

Remaining unknowns: Astra's omitted API default, internal Sol Fast economics,
Haiku 5.5 against Luna or Sonnet 5.5 on the same host and tasks,
account-specific access, and success/time metrics for this user's workflows.
