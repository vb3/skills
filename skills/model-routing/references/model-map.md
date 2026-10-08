# Model map

**Primary sources checked 2026-10-08.** Facts below are a dated reference;
the live host schema and account policy decide availability. Routing policy
lives in [SKILL.md](../SKILL.md); exact encoding lives in [harnesses.md](harnesses.md).

## OpenAI API Standard pricing

USD per million tokens, at base context rates:

| Candidate / API ID | Input | Cache read | Cache write | Output |
|---|---:|---:|---:|---:|
| Luna: `gpt-6-luna` | 0.10 | 0.01 | 0.125 | 0.50 |
| Sol: `gpt-6.1-sol` | 2.00 | 0.10 | 2.50 | 10.00 |
| Astra: `gpt-6-astra` | 10.00 | 1.00 | 12.50 | 50.00 |
| Legacy Sol: `gpt-6-sol` | 2.00 | 0.20 | 2.50 | 10.00 |
| Legacy Terra: `gpt-5.6-terra` | 2.00 | 0.20 | 2.50 | 12.00 |
| Legacy Sol: `gpt-5.6-sol` | 4.00 | 0.40 | 5.00 | 20.00 |
| Legacy Luna: `gpt-5.6-luna` | 0.20 | 0.02 | 0.25 | 1.20 |

GPT-6.1 Sol replaces GPT-6 Sol as the preferred Sol candidate. Input/output
prices are unchanged from GPT-6 Sol; cache reads halve to 5% of input.
Compared with GPT-5.6 Sol, input/output prices halve. Terra's input price
equals current Sol's, but its output and cache reads cost more. Retain Terra
only for explicit legacy choices, a validated workload result, or the
access-constrained fallback below, rather than as a new balanced default.

`gpt-5.6` still aliases the legacy GPT-5.6 Sol, not GPT-6.1 Sol. Its promotion
runs at least through 2026-11-21, with no guaranteed expiry or reversion price.
Use explicit versioned IDs.

GPT-6 Luna, GPT-6.1 Sol, and Astra have 1,050,000 context, 922,000 maximum input,
and 128,000 maximum output. Above 272K input, input/cache rates double and output
rates increase 1.5x for the whole API request. Host limits can be smaller.

Sources: [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol),
[GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna),
[Astra](https://developers.openai.com/api/docs/models/gpt-6-astra),
[GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol),
[API pricing](https://developers.openai.com/api/docs/pricing).

## Claude API Standard pricing

USD per million tokens; cache-write rates depend on duration:

| Candidate / API ID | Input | 5m write | 1h write | Cache read | Output |
|---|---:|---:|---:|---:|---:|
| Haiku: `claude-haiku-5-5`, prompt <=100K | 0.10 | 0.125 | 0.20 | 0.01 | 0.50 |
| Haiku: `claude-haiku-5-5`, prompt >100K | 0.50 | 0.625 | 1.00 | 0.05 | 2.50 |
| Sonnet: `claude-sonnet-5-5` | 2.00 | 2.50 | 4.00 | 0.10 | 10.00 |
| Opus: `claude-opus-5-5` | 4.00 | 5.00 | 8.00 | 0.20 | 20.00 |
| Fable: `claude-fable-5-1` | 10.00 | 12.50 | 20.00 | 0.25 | 50.00 |
| Legacy Haiku: `claude-haiku-4-5-20251001` | 1.00 | 1.25 | 2.00 | 0.10 | 5.00 |

Haiku 5.5 was released October 7. A request whose prompt exceeds 100K tokens
pays the higher row for every category, including output; other current
Claude candidates keep one rate across 1M context. Below the threshold, Haiku
5.5's unit prices are one tenth of Haiku 4.5's; above it, one half.

Opus 5.5 was released September 22 and Sonnet 5.5 September 28. On October 7,
Sonnet 5.5 cache reads fell from $0.20 to $0.10; its other rates are unchanged
from Sonnet 5. Opus's input/output prices fell 20% from Opus 5, while cache
reads fell from $0.50 to $0.20. Cache-read ratios are model-specific: Opus 5.5
and Sonnet 5.5 use 0.05x input, Fable 5.1 uses 0.025x, and Haiku 5.5/4.5 use 0.1x.

`claude-haiku-5-5` is a fixed ID with no dated snapshot; the CLI uses
`claude-haiku-5.5`. Haiku 4.5's alias is `claude-haiku-4-5`. It is still
active, with a tentative API retirement not sooner than 2026-10-15 and no
deprecation notice yet. Haiku 5.5, Sonnet, Opus, and Fable have 1M context and
128K synchronous maximum output. Some batch beta limits differ. Haiku 4.5 has
200K context and 64K output. Haiku 5.5 produces about 30% more tokens than
Haiku 4.5 for the same text; compare actual usage, not equal-token assumptions
across versions or vendors.

Sources: [Claude overview](https://platform.claude.com/docs/en/models/overview),
[Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview),
[Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview),
[Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview),
[Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing),
[Claude deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations).

## Host billing

Copilot usage-based billing converts model token charges into AI credits
(one credit = $0.01); legacy request-based plans use their own allowances.
Use the account's current meter, negotiated rates, and model policy rather
than converting an API table into a Copilot bill. Paid-plan Auto has a 10%
model-cost discount; it does not pin a particular model.

The checked Copilot input, output, cache-read, and listed cache-write rates
match the corresponding base API rates. API-only cache-duration and service
options do not automatically transfer. GPT-6 Luna and GPT-6.1 Sol use a 272K
input threshold with whole-request input/cache/write rates x2 and output x1.5.
Claude Haiku 5.5 uses a 100K input threshold on Copilot, with every rate x5
above it. Legacy GPT-5.6 Luna uses 200K on Copilot, versus 272K on its API.
A `long_context` flag alone does not establish the price.

For token billing:

```text
request cost = sum(disjoint category tokens * applicable rate / 1,000,000)
               + separately billed tools and services
cost per accepted result = total bill of all attempts and reviewers / accepted results
```

Cache-write rates replace ordinary input rates for those tokens. Reasoning
already counted in output is not charged again. Apply context, service-tier,
cache-duration, and regional premiums. With no accepted results, report failure.

Sources: [Copilot pricing](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing),
[individual billing](https://docs.github.com/en/copilot/concepts/billing-and-usage/individuals/billing).

## Access and fallbacks

Published support, schema membership, entitlement, and administrator enablement
are separate. GPT-6.1 Sol is eligible on Pro+, Max, Business, and Enterprise,
not base Pro. The GPT-6 Sol/Astra and legacy GPT-5.6 Sol announcements list
the same paid plans; GPT-6 Luna, Claude Haiku 5.5, and legacy Terra/Luna
include Pro. Free/Student use Auto only. Confirm the actual picker and policy.

For a base-Pro judgment task without Sol/Astra, consider eligible Terra only
with an adequate quality gate. If it cannot meet the requirement, report the
limit rather than substituting Luna or requiring an upgrade.

Read each chain left to right, choosing the first available, compatible route:

| Role | Availability chain |
|---|---|
| Sol | `gpt-6.1-sol` -> `gpt-6-sol` -> `gpt-5.6-sol` |
| Luna | `gpt-6-luna` -> `gpt-5.6-luna` |
| Astra | `gpt-6-astra` -> the Sol chain |
| Sol Fast | `gpt-5.6-sol-fast` -> the Sol chain |
| Opus | `claude-opus-5.5` -> `claude-opus-5` |
| Sonnet | `claude-sonnet-5.5` -> `claude-sonnet-5` |
| Haiku | `claude-haiku-5.5` -> `claude-haiku-4.5` |

These are CLI IDs, not API names or quality equivalence. The base-Pro branch
precedes repeated attempts at unavailable Sol generations. Preserve the gate,
tools, input capacity, deadline, and supported effort on every fallback.
`claude-haiku-4.5` lacks task effort and `long_context` in this schema.
Chain membership does not make an incompatible candidate usable.
Use an available stronger candidate when it meets the constraints, or report
the blocker. An access error is not a reasoning failure; a rate limit needs
service-specific recovery.

GitHub retires `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, and `gpt-5-mini` from
Copilot on 2026-10-19, suggesting GPT-5.6 Sol or Luna instead. They are no
longer chain entries; move pinned configurations to a current chain and rerun
the gate. Claude Opus 4.7 left Copilot on 2026-10-02.

Sources: [Haiku 5.5 announcement](https://github.blog/changelog/2026-10-07-claude-haiku-5-5-in-github-copilot/),
[October retirements](https://github.blog/changelog/2026-09-18-upcoming-deprecation-of-selected-github-copilot-models-in-mid-october/),
[October 2 deprecations](https://github.blog/changelog/2026-10-02-selected-models-in-github-copilot-deprecated/),
[GPT-6.1 announcement](https://github.blog/changelog/2026-09-29-gpt-6-1-sol-in-github-copilot/),
[GPT-6 announcement](https://github.blog/changelog/2026-09-22-openais-gpt-6-sol-and-gpt-6-luna-now-available/),
[Astra announcement](https://github.blog/changelog/2026-09-04-gpt-6-astra-is-generally-available-in-github-copilot/),
[GPT-5.6 announcement](https://github.blog/changelog/2026-07-09-openais-gpt-5-6-sol-terra-and-luna-are-now-available-in-github-copilot/),
[Copilot availability](https://docs.github.com/en/copilot/reference/ai-models/supported-models).

## API effort controls

| Model | Supported values | Default |
|---|---|---|
| GPT-6 Luna, GPT-6 Sol, GPT-5.6 family | `none`, `low`, `medium`, `high`, `xhigh`, `max` | `medium` |
| GPT-6.1 Sol | `low`, `medium`, `high`, `xhigh`, `max` | `medium` |
| Astra | `low`, `medium`, `high`, `xhigh`, `max` | Not verified |
| Opus 5.5, Haiku 5.5 | `low`, `medium`, `high`, `xhigh`, `max` | `medium` |
| Sonnet 5.5, Fable 5.1 | `low`, `medium`, `high`, `xhigh`, `max` | `high` |
| Legacy Haiku 4.5 | Effort parameter unsupported | Not applicable |

GPT-6.1 Sol supports neither `none` nor `minimal`, unlike GPT-6 Sol's `none`.
Opus 5.5 changed from Opus 5's high default to medium, but can think more at
the same label. Sonnet 5.5 recalibrated its levels: medium for well-specified
agentic work, low/medium for chat, high for harder reasoning. Haiku 5.5 is the
first Haiku with effort: medium for most work including agentic coding, low for
chat, short tool tasks, and simple high-volume requests, and high for longer
agent tasks or strict instruction following. Anthropic suggests comparing
Haiku xhigh/max with Sonnet 5.5. Repeat effort sweeps after upgrades rather
than carrying settings over.

Effort is adaptive, not a fixed token or time multiplier. Leave budget room
for thinking and visible output. Haiku 4.5's manual thinking budget is a
different parameter, which Haiku 5.5 rejects.

Sources: [OpenAI selection](https://developers.openai.com/api/docs/guides/model-selection),
[Claude effort](https://platform.claude.com/docs/en/build-with-claude/effort).

## Speed and scheduling controls

Vendor labels Luna cost-efficient and fast; Claude labels Haiku 5.5 fastest,
Sonnet fast, Opus moderate, Fable slower. These are not a standardized
eight-model completion-time comparison or SLA.

| Control | Scope | Price or constraint |
|---|---|---|
| OpenAI Fast | API `service_tier="fast"` or `"priority"` on supported GPT-6/5.6 | 2x Standard rates; check returned tier |
| OpenAI Ultrafast | API `service_tier="ultrafast"` on Astra and GPT-6.1 Sol | 6x Standard; separate rate limits; Astra global or US processing only, GPT-6.1 Sol also EU |
| Claude Fast preview | Opus 5.5, Opus 5, Opus 4.8 on Claude API | Access, `speed="fast"`, and documented beta header required; check premium |

Fast is unavailable for GPT-6.1 Sol and Astra with EU residency. API tiers
are not Copilot task arguments. Claude Priority Tier does not support Haiku
5.5; plan Haiku 4.5 commitments separately. The exposed internal
`gpt-5.6-sol-fast` is a valid legacy latency candidate when workload
quality/time supports it, with the compatible Sol fallback. Its Copilot
price/backend remain unverified; do not invent `gpt-6.1-sol-fast` or treat an
API multiplier as its bill.

For predicate, choice, or score answers, OpenAI's Decisions API beta
(`/v1/decisions`, `gpt-6-luna` only) claims about 10x faster responses than
Responses. Use Responses for custom schemas or tool calls.

Both providers discount supported API batches 50%. Allow for the 24-hour
window, failed/expired items, result handling, and retries. Independent
requests fit; dependent client-tool loops still require orchestration.
Copilot background work is not an API batch job.

Sources: [OpenAI Fast](https://developers.openai.com/api/docs/guides/fast-mode),
[Ultrafast](https://developers.openai.com/api/docs/guides/ultrafast-mode),
[Decisions](https://developers.openai.com/api/docs/guides/decisions),
[Claude Fast](https://platform.claude.com/docs/en/build-with-claude/fast-mode),
[OpenAI Batch](https://developers.openai.com/api/docs/guides/batch),
[Claude batches](https://platform.claude.com/docs/en/build-with-claude/batch-processing).

## Prompt caching

GPT-5.6 and later support implicit/explicit caching, 1.25x writes, and a
documented `"30m"` TTL. Reads are 0.05x input on GPT-6.1 Sol and 0.1x on the
other OpenAI candidates above.

Implicit mode can reuse up to 20 earlier eligible message endings, the initial
developer block, and explicit breakpoints. A changing suffix does not prove
there are no cache hits.

For explicit-only control, use `prompt_cache_options.mode="explicit"` and
`prompt_cache_breakpoint: {"mode": "explicit"}` on a supported content block
ending the stable prefix. Later content uses ordinary input pricing.
Without breakpoints, explicit-only creates no writes/reuse. A stable cache
key helps routing but does not guarantee a hit.

Inspect input/read/write/output usage, retries, and tiers before attributing
a bill. A 25% write premium alone cannot produce a 3x total bill against
otherwise identical uncached-input pricing. These are API controls, not
invented Copilot task arguments.

Source: [OpenAI caching](https://developers.openai.com/api/docs/guides/prompt-caching).

## Version-specific integration constraints

GPT-6.1 Sol and Astra require Responses for tools; Chat Completions is
supported without tools. GPT-6 Luna/Sol permit Chat Completions function
calling only at `none`. Async tools require application/host support too.

Opus 5.5 and Fable 5.1 always use adaptive thinking; disabled thinking and
manual budgets are invalid. Sonnet 5.5 uses `between_tools` at low/medium/high
to skip up-front thinking; disabled/manual budgets are invalid. At xhigh/max
use adaptive thinking.

Opus 5.5, Fable 5.1, and Sonnet 5.5 reject forced any/named `tool_choice`; use
supported auto/none and strict tools or structured outputs for schemas.
Thinking blocks on these and Haiku 5.5 bind to model/history. Switching can
drop reasoning; editing earlier turns can invalidate blocks. Use supported
compaction and migration.

Haiku 5.5 thinks adaptively by default; `thinking: {"type": "disabled"}` is
valid only at high or below, and manual budgets are invalid. It accepts forced
`tool_choice`, but the response then skips thinking. Unlike Haiku 4.5, it
rejects assistant prefill and non-default `temperature`/`top_p`/`top_k`; use
structured outputs or enum tools for formats. Handle `stop_reason: "refusal"`.

Opus/Sonnet 5.5 progress can arrive as thinking blocks, omitted by default
display. Configure documented display when needed. On Claude API and Google
Cloud they use the newer computer-use toolset, not `computer_20251124`.
Before sensitive Fable work, check enablement and retention requirements;
GitHub describes conditional enterprise arrangements, not universal access.

Sources: [GPT-6 guide](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md),
[Opus changes](https://platform.claude.com/docs/en/models/opus-5-5/whats-new-opus-5-5),
[Sonnet changes](https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5),
[Haiku migration](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide),
[Fable changes](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1).
