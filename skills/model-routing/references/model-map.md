# Model map

**Vendor facts and Copilot CLI task snapshot checked 2026-09-09.** This is a
dated reference, not a substitute for the live host schema or current prices.
The role bands and routing procedure live in [SKILL.md](../SKILL.md).

## OpenAI API models and Standard pricing

USD per million tokens, at the base context rate:

| Model / API ID | Input | Cache read | Cache write | Output |
|---|---:|---:|---:|---:|
| Luna: `gpt-5.6-luna` | 0.20 | 0.02 | 0.25 | 1.20 |
| Terra: `gpt-5.6-terra` | 2.00 | 0.20 | 2.50 | 12.00 |
| Sol: `gpt-5.6-sol` | 4.00 | 0.40 | 5.00 | 20.00 |
| Astra: `gpt-6-astra` | 10.00 | 1.00 | 12.50 | 50.00 |

`gpt-5.6` aliases Sol. Prefer the explicit model ID when communicating a route.
Sol's promotional pricing is available **at least through 2026-11-21**.
Recheck the price; that wording does not establish an exact expiry or a
guaranteed post-promotion rate.

All four model pages list a 1,050,000-token context window, 922,000 maximum input,
and 128,000 maximum output. For API prompts above 272K input tokens, input and
cache rates are doubled and output rates are multiplied by 1.5 for the
**entire request**, not only the excess. Copilot uses a different Luna threshold
described below. Host limits can be smaller than model capacity.

Sources: OpenAI model pages for
[Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna),
[Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra),
[Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol),
[Astra](https://developers.openai.com/api/docs/models/gpt-6-astra),
and [pricing](https://developers.openai.com/api/docs/pricing).

## Claude API models and Standard pricing

USD per million tokens; write prices depend on cache duration:

| Model / API ID | Input | 5m write | 1h write | Cache read | Output |
|---|---:|---:|---:|---:|---:|
| Haiku: `claude-haiku-4-5-20251001` | 1.00 | 1.25 | 2.00 | 0.10 | 5.00 |
| Sonnet: `claude-sonnet-5` | 2.00 | 2.50 | 4.00 | 0.20 | 10.00 |
| Opus: `claude-opus-5` | 5.00 | 6.25 | 10.00 | 0.50 | 25.00 |
| Fable: `claude-fable-5-1` | 10.00 | 12.50 | 20.00 | 0.25 | 50.00 |

Haiku's API alias is `claude-haiku-4-5`; its Copilot CLI ID uses a dot instead.
Sonnet's $2/$10 is standard pricing, not an expired introductory offer.
Sonnet, Opus, and Fable support 1M context at standard context pricing, explicitly
confirmed by the checked
[context-window guide](https://platform.claude.com/docs/en/build-with-claude/context-windows#context-window-sizes-by-model).
Their synchronous maximum output is 128K; some batch beta modes have different
limits. Haiku supports 200K context and 64K maximum output.

Fable 5.1's $0.25 cache read is intentionally **0.025x** its input rate, unlike
the 0.1x read rate for the other three models.

Newer Claude tokenizers can use approximately 30% more tokens for the same text
than older generations. Equal-token price comparisons across models or vendors
are not equal-work comparisons.

Sources: [model overview](https://platform.claude.com/docs/en/models/overview),
[pricing](https://platform.claude.com/docs/en/about-claude/pricing),
and [choosing a model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model).

## Host billing is a separate input

GitHub documents usage-based Copilot AI credits, with one credit equal to
$0.01, as well as legacy request-based billing. Inspect the caller's plan and
actual usage meter; neither API token rates nor request multipliers describe
every Copilot subscription.

For usage-based Copilot billing, use the current GitHub model-rate table rather
than assuming API rates transfer. In the checked table, OpenAI long-context
pricing starts above **200K input for Luna**, and above **272K for Terra, Sol,
and Astra**. Input/cache/write rates increase 2x and output 1.5x for the full
request. A `long_context` flag does not alone tell you the billed token count.

For token billing, calculate cost from disjoint billed categories:

```text
request cost = sum(category tokens * applicable category rate / 1,000,000)
               + separately billed tools and services
cost per accepted result = total cost of all attempts and reviewers / accepted results
```

Apply service-tier, cache-duration, and context pricing to the relevant request.
Reasoning tokens already counted in output must not be charged twice. With no
accepted results, report failure, not a finite successful-task cost. For
request-based allowances, replace token arithmetic with that host's metering.

Source: [GitHub models and pricing](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing).

## Effort controls

| Model | API effort values | API default |
|---|---|---|
| Luna, Terra, Sol | `none`, `low`, `medium`, `high`, `xhigh`, `max` | `medium` |
| Astra | `low`, `medium`, `high`, `xhigh`, `max` | Not verified; set explicitly |
| Sonnet 5, Opus 5, Fable 5.1 | `low`, `medium`, `high`, `xhigh`, `max` | `high` |
| Haiku 4.5 | Effort parameter unsupported | Not applicable |

`none` is invalid for Astra. API support does not establish that a particular
host exposes a value. Haiku's manual extended-thinking budget on supporting
APIs is not the effort parameter.

Anthropic recommends beginning Opus and Fable at `high`, then tuning against
quality, cost, and latency. Effort affects token usage adaptively, not by a
fixed multiplier. On Opus 5, lower effort is not a reliable way to shorten
visible prose; request the desired response length separately.

Sources: [OpenAI reasoning](https://developers.openai.com/api/docs/guides/reasoning),
[Astra guide](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md),
[Claude effort](https://platform.claude.com/docs/en/build-with-claude/effort).

## Latency evidence and speed controls

Anthropic's overview uses these comparative labels: Haiku **fastest**, Sonnet
**fast**, Opus **moderate**, Fable **slower**. These describe relative positioning,
not an end-to-end SLA. This reference does not maintain a standardized measured
TTFT/TPS ranking for the eight models. Measure the actual workload, effort,
provider, concurrency, and warm/cold cache conditions before claiming a winner.

Paid speed is host-specific:

| Control | Verified scope | Caveat |
|---|---|---|
| GPT-5.6 / Astra fast mode | API `service_tier="fast"` or `"priority"`; 2x corresponding Standard price | Sol advertises up to 2.5x speed; this is not a universal model or task guarantee |
| Astra fast mode | Supported at premium rates | No latency SLA; unavailable with EU data residency |
| Claude fast mode | Opus 5 and Opus 4.8 research preview on Claude API, including Managed Agents | Requires access, `speed="fast"`, and the documented beta header; not generally available on other cloud hosts |

Check the returned service tier or speed because a request can run at standard
speed. Read current fast-mode pricing before estimating a bill. Copilot's
internal `gpt-5.6-sol-fast` entry is a distinct host selection: this review did
not establish its price or equivalence to API fast mode.

Sources: [OpenAI fast mode](https://developers.openai.com/api/docs/guides/fast-mode),
[Claude fast mode](https://platform.claude.com/docs/en/build-with-claude/fast-mode).

## Batch processing

OpenAI Batch and Claude Message Batches offer 50% discounts on supported API
requests. They are API workflow options, not automatic discounts on Copilot
`task` calls. Establish the actual deadline and allow for the 24-hour processing
window, expired or failed requests, result collection, and retries. "Overnight"
alone does not establish enough slack.

Use batches for independent requests. A sequential tool-using agent loop still
needs client orchestration between dependent rounds; submitting its first
request does not batch the whole task. Claude batches do not stream or use fast
mode. When evaluating production behavior, preserve the configuration under
test rather than downshifting it to make the evaluation cheaper.

Sources: [OpenAI Batch](https://developers.openai.com/api/docs/guides/batch),
[Claude Message Batches](https://platform.claude.com/docs/en/build-with-claude/batch-processing).

## Prompt caching

GPT-5.6 and Astra support implicit and explicit caching. Writes cost 1.25x the
uncached input rate, reads cost 0.1x, and the documented TTL is `"30m"`.

In implicit mode, the service can look back to up to 20 earlier eligible message
endings, plus the initial developer block and explicit breakpoints. A changing
suffix does **not** prove the stable prefix is never reused.

For explicit-only control, set `prompt_cache_options.mode="explicit"` and put
`prompt_cache_breakpoint: {"mode": "explicit"}` on a supported content block at
the end of the stable prefix. Dynamic content after the last breakpoint is
ordinary uncached input rather than a cache write. Explicit-only mode with no
breakpoints has no writes or reuse. A stable cache key can help routing but
does not guarantee a hit.

Diagnose using actual input, cached-read, cache-write, and billed-output usage,
plus retries and service/context tiers. A 25% write premium alone cannot explain
a 3x total bill against an otherwise identical uncached-input baseline. Cache
hits can reduce prefill latency; their effect depends on the cached share and
the rest of the workflow.

Source: [OpenAI prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching).

## Advanced-model integration constraints

Astra tool calling requires the **Responses API**, even though Chat Completions
supports other uses of the model. Async tool calling also requires host or
application support; selecting Astra alone does not parallelize a serial loop.

Fable 5.1 uses always-on adaptive thinking. Forced tool use (`any` or a named
tool) is unsupported; `auto` and `none` are supported. Earlier Claude models
cannot consume its thinking blocks, and history edits can invalidate bound
thinking blocks. Use supported compaction and migration mechanisms; switching
models mid-session is not necessarily a lossless operation.

Check organization enablement and data-retention requirements before sensitive
Fable workflows. GitHub documents conditional enterprise arrangements, not
universal availability or a universal prohibition.

Sources: [Astra guide](https://developers.openai.com/api/docs/guides/latest-model/gpt-6-astra.md),
[Fable 5.1 changes](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1),
[GitHub supported models](https://docs.github.com/en/copilot/reference/ai-models/supported-models).

Exact host encoding is isolated in [harnesses.md](harnesses.md), which must be
checked against the live schema before dispatch.
