# Evidence and maintenance

**Primary sources rechecked 2026-09-30.** Vendor positioning, comparative
measurements, and local routing policy are separate. Agreement between
reviewers is not performance evidence.

## Current vendor positioning

OpenAI's GPT-6 guide positions Luna for focused, high-volume work, GPT-6.1 Sol
for near-Astra complex work at lower cost, and Astra for the highest intelligence.
Its selection guide suggests Sol medium for revisable complex technical work,
Sol xhigh for demanding polished deliverables, and comparing Sol against Astra
on the same task. These are vendor starting points, not universal optima.

Sources: [GPT-6 guide](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md),
[selection guide](https://developers.openai.com/api/docs/guides/model-selection),
[GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

Anthropic now recommends Opus 5.5 for most workloads and Fable 5.1 for
demanding reasoning or long-horizon work where Opus falls short. Opus 5.5
defaults to medium; Sonnet 5.5 retains high as its API default while recommending
medium for well-specified agentic work and low/medium for chat. Both vendors
require workload comparisons to establish cost or completion-time savings.

Sources: [Claude overview](https://platform.claude.com/docs/en/models/overview),
[Claude effort](https://platform.claude.com/docs/en/build-with-claude/effort).

**Local policy:** independent gates, Frontier for consequential decisions,
and bounded pilots before scaling are this skill's choices. Band labels
are role groupings, not benchmark equivalences across providers.

## Economics changed; old benchmarks did not

GPT-6.1 Sol has the same $2/$10 input/output rates as GPT-6 Sol and half
its cache-read price. Opus 5.5 is $4/$20 rather than Opus 5's $5/$25, with
$0.20 cache reads rather than $0.50. Those are unit-price changes, not measured
cost per accepted result. Sources and full rates live in [model-map.md](model-map.md).

The earlier Artificial Analysis Luna/Sol cost frontier compared the GPT-5.6
family. It does not establish dominance for GPT-6 Luna, GPT-6.1 Sol,
Sonnet/Opus 5.5, or latency. Retain it only as historical context; re-evaluate
current models before claiming a ranking.

Historical source: [GPT-5.6 cost comparison](https://artificialanalysis.ai/articles/gpt-5-6-intelligence-vs-cost-across-sol-terra-luna).

## Latency mechanisms

OpenAI's guide suggests output reduction can reduce generation time, while its
small-input-trimming heuristic exempts massive contexts. For agentic workflows,
measure prefill, generation, queues, tools, retries, and validation separately.
Streaming and progress display can improve perceived waiting without shortening
the accepted-result time.

Source: [OpenAI latency guide](https://developers.openai.com/api/docs/guides/latency-optimization).

No same-host, same-task eight-model timing comparison was run for this refresh.
Vendor labels such as fastest/moderate/slower are not a completion-time SLA.

## Refresh procedure

1. Check vendor model, price, effort, caching, and migration pages alongside
   Copilot billing/entitlements. Record dates and unresolved claims in the map.
2. Check the actual dispatch schema, account access, and host-managed defaults.
   Revalidate every fallback's tools, context, efforts, and quality gate.
3. Compare cost per accepted result and p50/p95 completion time using the same
   representative tasks, acceptance gate, host, and cache/concurrency conditions.
4. Update current candidates and affected fixtures; preserve explicit legacy
   choices and label local policy separately from vendor guidance.
5. Run the repository structural validator and affected behavioral scenarios.
   Schema validity, an injected-context eval, and an actual skill-discovery run
   establish different things; report which was performed.

Remaining unknowns here: Astra's omitted API effort default, internal Sol Fast
economics, account-specific availability, and comparative success/time metrics
for this user's workflows.
