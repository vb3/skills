# Evidence

**Verified 2026-09-23.** This refresh uses directly inspected primary
documentation and the benchmark publisher's own pages, not search summaries.
Separate three kinds of evidence:

- **[V]** Vendor documentation or official product announcements.
- **[B]** Third-party measurements published by the benchmark owner.
- **[H]** The authoring session's live harness, not universal availability.

The task/effort recommendations in `SKILL.md` are routing policy informed by
these sources. They are not measured optima for every repository.

## Model roles and what changed

**[V]** OpenAI describes [GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol)
as built for complex coding and agentic workflows,
[GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) as its
efficient model for focused, high-volume tasks, and
[GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra) as its
most capable model for the hardest end-to-end work.

**[V]** GitHub's [September 22 Sol/Luna announcement](https://github.blog/changelog/2026-09-22-openais-gpt-6-sol-and-gpt-6-luna-now-available/)
positions Sol as the balanced choice for interactive and agentic coding and
Luna for smaller, faster work. Its
[September 4 Astra announcement](https://github.blog/changelog/2026-09-04-gpt-6-astra-is-generally-available-in-github-copilot/)
reports stronger long-horizon coding in GitHub's internal testing, with fewer
steps and independent validation. This supports recommending Astra for
difficult autonomous work, but does not quantify a universal win over Sol.

**Policy consequence:** Luna remains the checked-worker default; Sol is the
general judgment/ownership default, not the highest-capability model by
definition. Astra is a legitimate quality-first route with a Sol fallback.
An intermediate tier is not inherently off the frontier: the new Sol is
itself positioned as balanced.

## Copilot access

**[V]** Plan eligibility from the linked GitHub release announcements:

| Model | Eligible paid plans |
|---|---|
| GPT-6 Astra, GPT-6 Sol | Pro+, Max, Business, Enterprise |
| GPT-6 Luna | Pro, Pro+, Max, Business, Enterprise |
| GPT-5.6 Sol | Pro+, Max, Business, Enterprise |
| GPT-5.6 Terra, GPT-5.6 Luna | Pro, Pro+, Max, Business, Enterprise |

Sources: the two GPT-6 announcements above and the
[GPT-5.6 announcement](https://github.blog/changelog/2026-07-09-openais-gpt-5-6-sol-terra-and-luna-are-now-available-in-github-copilot/).
Rollout and administrator policy can still prevent access. The newer GPT-6
announcements say default model enablement enables new models automatically
unless the administrator disables that default or the model. Do not repeat
the July GPT-5.6 post's historical "off by default" as current universal policy.

**[V]** [Individual billing documentation](https://docs.github.com/en/copilot/concepts/billing-and-usage/individuals/billing)
says Free and Student plans access models through Auto selection only.

**Policy consequence:** "No Astra" does not always mean "use Sol": base Pro
lacks both. GPT-5.6 Terra is an eligible general-purpose fallback candidate
for that plan, subject to the task's quality gate. Check the actual picker
before proposing another paid-plan-only model or assuming a plan upgrade.

## Copilot pricing

**[V]** [GitHub's model pricing table](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing)
is the authority for Copilot charges. Snapshot in USD per million tokens,
default context, before any applicable discount:

| Model | Input | Cached input | Cache write | Output |
|---|---:|---:|---:|---:|
| GPT-6 Luna | 0.10 | 0.01 | 0.125 | 0.50 |
| GPT-6 Sol | 2.00 | 0.20 | 2.50 | 10.00 |
| GPT-6 Astra | 10.00 | 1.00 | 12.50 | 50.00 |
| GPT-5.6 Luna | 0.20 | 0.02 | 0.25 | 1.20 |
| GPT-5.6 Sol | 4.00 | 0.40 | 5.00 | 20.00 |
| GPT-5.6 Terra | 2.00 | 0.20 | 2.50 | 12.00 |
| Claude Sonnet 5 | 2.00 | 0.20 | 2.50 | 10.00 |
| Claude Opus 5 | 5.00 | 0.50 | 6.25 | 25.00 |
| Claude Opus 5.5 | 4.00 | 0.20 | 5.00 | 20.00 |

GitHub lists no separate GPT-5.6 Sol Fast rate in this table. Its rate remains
unknown here; do not substitute the direct API Fast-mode price.

For GPT-6 models, GitHub's long-context threshold is more than 272K input
tokens, with 2x input/cache/cache-write and 1.5x output rates. The older
GPT-5.6 Luna threshold is **200K**, not 272K. Model-specific thresholds
matter; `long_context` is not a free quality setting.

**Derived, same usage mix and default tier:** GPT-6 Sol has half GPT-5.6 Sol's
listed rates; GPT-6 Luna halves GPT-5.6 Luna's input/cache rates and reduces
output from $1.20 to $0.50. Sol is cheaper than either listed Opus, but equals
Sonnet 5's rates. Astra is more expensive than those Claude models.
Sol's rates are 20x Luna's and Astra's are 5x Sol's. These are **token-rate
ratios, not total task-cost ratios**; reasoning, cache reuse, retries, and
review can change the latter substantially.

**[V]** [Current individual billing](https://docs.github.com/en/copilot/concepts/billing-and-usage/individuals/billing)
meters token usage in AI credits, with **1 credit = $0.01**. Paid-plan Auto
selection receives a 10% model-cost discount. This does not make Auto a way
to enforce a specific selected model.

**[V]** [Legacy annual-plan documentation](https://docs.github.com/en/copilot/reference/copilot-billing/request-based-billing-legacy/what-changed-with-billing)
limits premium-request multipliers to existing annual Pro/Pro+ subscribers
who remained on request billing after June 1, 2026, until their plan ends.
Do not apply that billing model to all Copilot users.

**Policy consequence:** OpenAI-first is well supported for Sol/Luna versus
Opus on these rates, not a universal vendor discount. Use total measured
Copilot cost per accepted result; don't import an API-only price or multiply
an assumed effort-token factor by an output price.

## API capabilities are not harness guarantees

**[V]** The three GPT-6 model pages linked above document text/image input,
text output, a 1,050,000-token API context window, maximum 922,000 input and
128,000 output. That does not establish Copilot's effective usable window.
Their API base token rates match the GPT-6 rows of the Copilot snapshot.

| Model | Documented API `reasoning.effort` |
|---|---|
| GPT-6 Sol, GPT-6 Luna | `none`, `low`, `medium` (default), `high`, `xhigh`, `max` |
| GPT-6 Astra | `low`, `medium`, `high`, `xhigh`, `max`; no `none` |

**[V]** Sol/Luna model pages recommend Responses for tool calling; Chat
Completions supports function calling only at `none` effort. The
[reasoning guide](https://developers.openai.com/api/docs/guides/reasoning)
says Astra does not support Chat Completions function calling, and requesting
`none` effort returns HTTP 400. Use Responses for reasoning/tool workflows.

**[V]** The reasoning guide describes adaptive deliberation, names
medium/high as useful comparison points, and says to use `xhigh` only when
evals show a clear benefit. It publishes no fixed effort-to-token multiplier.
Reasoning tokens count toward the context window and API output billing.
`reasoning.mode: pro` is a separate API control; it is not a Copilot effort.

The guide's introductory cheaper-model examples still name GPT-5.6 rather
than the newly released Sol/Luna. Prefer the current model pages and rates for
those choices, not an assumption that every guide updated simultaneously.

## Fast mode and the local Sol Fast ID

**[V]** [OpenAI Fast mode](https://developers.openai.com/api/docs/guides/fast-mode)
uses `service_tier: fast` (or `priority`) on a normal API model ID. The guide
describes up to 2.5x faster processing and gives GPT-5.6 Sol Fast processing a
2x rate. The GPT-6 model pages also list a 2x Fast-mode rate. This is not
evidence that a Copilot `-fast` ID uses that route, pricing, or speed.

**[H]** `gpt-5.6-sol-fast` is a valid `task.model` value in the authoring
session, with `xhigh`, `max`, and `long_context` exposed. It is therefore an
allowed host-specific recommendation, not a fictional model inferred from a
web search. Its backend mechanism, Copilot rate, and relative quality/speed
were not established by the inspected public sources.

**Policy consequence:** recommend this exposed candidate for an appropriate
latency-sensitive task, clearly identifying what is unmeasured. Compare it
against GPT-6 Sol and give the Sol fallback. Do not invent `gpt-6-sol-fast`,
deny the observed local ID because a public catalog omits it, or advertise an
API Fast-mode multiplier as a measured Copilot result.

## Independent measurements and their limits

**[B]** Same-day snapshots from Artificial Analysis's model pages, each
labelled `max` effort:

| Model | Intelligence Index | Output tokens/s | Reported average evaluation cost/task |
|---|---:|---:|---:|
| [GPT-6 Astra](https://artificialanalysis.ai/models/gpt-6-astra) | 53 | 52 | $3.26 |
| [GPT-6 Sol](https://artificialanalysis.ai/models/gpt-6-sol) | 48 | 113 | $1.06 |
| [GPT-6 Luna](https://artificialanalysis.ai/models/gpt-6-luna) | 37 | 131 | $0.07 |

These are publisher measurements, not Copilot measurements or an effort
ladder. They support considering Astra for quality, Sol for a cheaper/faster
judgment route, and Luna for checked volume. They do not prove the same
ranking at medium effort or on a particular repository.

The retrieved page summaries do not state the index version; do not compare
these scores with the older skill's GPT-5.6 numbers. Their cohort medians also
differ. The Sol page reports an 872K context window versus OpenAI's 1,050,000;
the cause is not established. Prefer vendor docs for API limits and the live
host for its effective limit, not a merged or guessed value.

Output throughput is not time to first useful output or full agent completion.
No same-harness Copilot TTFT, p95, or cost-per-accepted-result comparison was
performed in this refresh. No fresh SWE-Bench comparison here supports
automatically preferring Claude for repository issue fixes.

## Caching, batch work, and latency

**[V]** The current [OpenAI caching guide](https://developers.openai.com/api/docs/guides/prompt-caching)
documents a 1,024-token minimum cacheable prefix for GPT-5.6 and later,
implicit and explicit caching, 1.25x cache-write and 0.1x cache-read rates,
and a 30-minute minimum lifetime refreshed on reuse.

Cache-write pricing is **not additive** to the ordinary input rate: input
tokens use the uncached, cached, or write rate. Explicit-only mode uses
`prompt_cache_options.mode: explicit` plus explicit breakpoints; without any
breakpoints it creates no cache writes. Implicit mode can look back to earlier
eligible message endings. The old claim that a changing suffix necessarily
prevents any reusable-prefix read is therefore too strong.

These are API controls, not documented Copilot task arguments. Diagnose usage
and cache reuse before changing models; do not prescribe API breakpoints in
a host that does not expose them.

**[V]** The [Batch API guide](https://developers.openai.com/api/docs/guides/batch)
documents a 50% discount and turnaround within 24 hours for supported API
jobs. This is not a Copilot background-task discount or a guarantee of
finishing an eight-hour overnight deadline.

**[V]** [Nielsen's response-time guidance](https://www.nngroup.com/articles/response-times-3-important-limits/)
identifies roughly ten seconds as an attention threshold and recommends
feedback for longer waits. It is general UX guidance, not evidence for a
universal `medium` effort ceiling or a coding-model latency SLA.

## Live harness evidence and remaining uncertainty

**[H]** Copilot CLI 1.0.88's authoring-session `task` schema includes all
four requested IDs and exposes `xhigh`, `max`, and `long_context` for each.
`copilot --help` exposes model, effort, and context flags; the help tool
documents `/model`, `/usage`, and `/subagents`. The per-model matrix and
override semantics are recorded in [model-map.md](model-map.md#harness-syntax).

These observations establish local control syntax, not every user's access
or actual run cost. No user-specific billing logs or model performance runs
were collected. The routing remains conditional on actual entitlement,
independent task verification, and the provider's current rates.
