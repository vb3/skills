# Model map

**Model and pricing facts last verified: 2026-08-04. VS Code runSubagent labels
last verified: 2026-08-19.** This is the volatile half of the skill. When
anything here changes, update the affected verification date. The tier logic in
`SKILL.md` is designed to survive without edits.

## OpenAI GPT-5.6 family

Launched 2026-07-09. The tier names (Sol, Terra, Luna) are generation
independent and are intended to persist across future releases, so
"frontier / balanced / efficient" maps onto them stably.

| Tier | Model ID | Input $/1M | Cached input $/1M | Output $/1M |
|---|---|---|---|---|
| Frontier | `gpt-5.6-sol` | 5.00 | 0.50 | 30.00 |
| Balanced | `gpt-5.6-terra` | 2.00 | 0.20 | 12.00 |
| Efficient | `gpt-5.6-luna` | 0.20 | 0.02 | 1.20 |

`gpt-5.6` is an alias that resolves to Sol. Do not use it in production code,
because it silently bills at frontier rates.

**Prices changed on 2026-07-30.** Terra dropped about 20% from $2.50/$15, and
Luna dropped about 80% from $1.00/$6.00. Any advice written before that date
undervalues Luna badly. Sources:
[OpenAI price-performance post](https://openai.com/index/advancing-the-price-performance-frontier-with-gpt-5-6/),
[BenchLM API pricing](https://benchlm.ai/openai/api-pricing),
[explainX](https://www.explainx.ai/blog/openai-gpt-5-6-luna-terra-price-cuts-july-2026).

Relative per-token cost: Terra is 10x Luna, Sol is 25x Luna and 2.5x Terra.

**Context and limits** (identical across all three): 1,050,000 token context
window, 128,000 max output tokens, knowledge cutoff 2026-02-16.
Source: [OpenAI GPT-5.6 launch](https://openai.com/index/gpt-5-6/).

Codex applies a lower effective context limit than the API, reported as reduced
from 372K to 272K tokens. This is a product limit, not an API limit, and it is a
contributing factor in long-session drift.
Source: [InfoWorld](https://www.infoworld.com/article/4198811/openais-codex-context-reduction-for-gpt-5-6-sparks-dissatisfaction-among-developers.html).

## Reasoning effort

All three GPT-5.6 models support the full range. Default is `medium` everywhere
when the parameter is omitted.

| Effort | API value | Available in Copilot CLI | Official positioning |
|---|---|---|---|
| None | `none` | No | Latency-critical, no benefit from reasoning: classification, voice |
| Low | `low` | Yes | Tool use, planning, search, execution-oriented coding |
| Medium | `medium` | Yes | Default. Planning, complex reasoning, judgment, agentic coding |
| High | `high` | Yes | Complex debugging, deep planning, quality over latency |
| Extra high | `xhigh` | Yes | Deep research, async, security and code review. Only when evals show a gain |
| Max | `max` | Yes | Maximum single-agent reasoning. Compare against `xhigh` |

Source: [OpenAI reasoning guide](https://developers.openai.com/api/docs/guides/reasoning).

Two things that are **not** effort levels:

- **Pro mode** is `reasoning.mode: "pro"`, settable on any GPT-5.6 model,
  orthogonal to effort. It adds work before returning a single answer. In
  ChatGPT it is gated to Pro and Enterprise.
- **Ultra** is a multi-agent mode in ChatGPT Work and Codex that coordinates
  several agents in parallel. It trades total tokens for wall-clock time and is
  not available as an API effort value.

There is also a Sol "fast mode", roughly 2.5x faster at double the price, for
latency-sensitive frontier work.

## Approximate effort cost multipliers

Community and third-party measurements, not official OpenAI figures. Treat as
directional. Actual reasoning tokens are visible in
`output_tokens_details.reasoning_tokens`, and models reason adaptively, so
simple tasks cost less than these multipliers imply.

| Effort | Tokens vs medium | Latency vs medium |
|---|---|---|
| `none` | 0.1x to 0.2x | 0.3x |
| `low` | 0.3x to 0.4x | 0.5x |
| `medium` | 1x | 1x |
| `high` | 1.5x to 2x | 1.5x to 2x |
| `xhigh` | 2x to 3x | 2x |
| `max` | 3x to 5x | 2.5x to 3x |

Source: [Artificial Analysis](https://artificialanalysis.ai/articles/gpt-5-6-has-landed).

### Effective cost grid

Model price multiplied by effort token burn, normalized so Luna medium is 1x.
This is the table that makes the barbell argument concrete: Luna `xhigh` is
cheaper than Terra `low`.

| | `low` | `medium` | `high` | `xhigh` | `max` |
|---|---|---|---|---|---|
| **Luna** | 0.35x | 1x | 1.75x | 2.5x | 4x |
| **Terra** | 3.5x | 10x | 17.5x | 25x | 40x |
| **Sol** | 8.75x | 25x | 43.75x | 62.5x | 100x |

**Method and its limits.** Effort multipliers are the midpoints of the ranges
above, so `low` is 0.35x and `high` is 1.75x. The cross-model ratio is 1:10:25
for Luna:Terra:Sol, which holds whether you normalize on input or output price,
because the three models share the same input-to-output price ratio.

The effort axis is the weak part. Effort mostly inflates reasoning and output
tokens while input cost stays roughly fixed, so these behave as
output-normalized figures rather than true end-to-end cost multipliers. A
request with a large prompt and a short answer will show a much flatter effort
curve than this grid implies. Treat the model axis as solid and the effort axis
as directional.

`SKILL.md` rounds these to whole numbers (9x, 44x, 62x). Do not read precision
into any of them.

## Older OpenAI models

| Model | Still worth routing to when |
|---|---|
| `gpt-5.5` | You need a well-characterized production model, or 24-hour extended prompt cache retention, which GPT-5.6 does not offer. OpenAI positions Terra as the successor, but that is vendor positioning; this skill routes to Sol or Luna instead. |
| `gpt-5.5-pro` | Low-frequency, large-context batch jobs where the 30-minute GPT-5.6 cache TTL is not enough. |
| `gpt-5.4` | Validated legacy production deployments, including Bedrock and Azure, that were tuned against it. |
| `gpt-5.3-codex` | Legacy integrations built on Codex-specific APIs. Superseded by Luna for new work, which is both cheaper and stronger on agentic coding. |
| `gpt-5.4-mini`, `gpt-5-mini` | Nothing new. Luna is cheaper than both at the current price and substantially more capable. |

## Prompt caching

GPT-5.6 changed caching in ways that matter for agent loops.

- Cache **writes** now cost 1.25x the uncached input rate. On earlier models
  they were free.
- Cache **reads** keep the 90% discount.
- Minimum TTL is 30 minutes (`prompt_cache_options.ttl: "30m"`, the only
  supported value). Earlier models offered up to 24 hours on some snapshots.
- The service no longer falls back automatically to the longest matching
  unmarked prefix.
- Mark the end of the stable prefix with
  `prompt_cache_breakpoint: { "mode": "explicit" }`, set
  `prompt_cache_options.mode: "explicit"` to suppress the implicit breakpoint,
  and set a stable `prompt_cache_key`. Up to four new breakpoints per request,
  up to 50 read-eligible per conversation.

The failure mode to watch for: leaving implicit caching on with a dynamic
suffix, which writes a fresh expensive cache entry every turn that is never
read. Monitor the ratio of `cache_write_tokens` to `cached_tokens`.

Source: [OpenAI prompt caching guide](https://developers.openai.com/api/docs/guides/prompt-caching).

**Programmatic tool calling** lets the model coordinate tools in code rather
than through round trips. OpenAI reports leaner system prompts plus PTC
improving eval scores 10% to 15% while cutting tokens 41% to 66%. Worth using
for bounded, tool-heavy workflows with predictable output schemas.
Source: [OpenAI migration guide](https://developers.openai.com/api/docs/guides/latest-model).

## Harness syntax

### VS Code runSubagent

The VS Code `runSubagent` tool uses exact model display names in its `model`
field, not API or Copilot CLI IDs. Translate the routed tier before dispatch:

| Tier | API or CLI model ID | `runSubagent` model value |
|---|---|---|
| Frontier | `gpt-5.6-sol` | `GPT-5.6 Sol (copilot)` |
| Balanced | `gpt-5.6-terra` | `GPT-5.6 Terra (copilot)` |
| Efficient | `gpt-5.6-luna` | `GPT-5.6 Luna (copilot)` |

Use the exact available-model labels returned by the tool when they differ from
this table. The current `runSubagent` schema exposes `model` but not reasoning
effort or context tier. Still choose all three routing axes (tier, effort, and
context tier) before dispatch, but encode only the controls the host supports
and state that effort or context is not host-enforced. Putting an effort request
in the worker prompt is task guidance, not a substitute for a harness control.

### Copilot CLI

The `task` tool takes `model`, `reasoning_effort`, and `context_tier`. Selectable
models and their supported efforts, as exposed by the CLI:

| Model | context_tier | Efforts |
|---|---|---|
| `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` | default, long_context | low, medium, high, xhigh, max |
| `gpt-5.5`, `gpt-5.4` | default, long_context | low, medium, high, xhigh |
| `gpt-5.3-codex`, `gpt-5.4-mini` | default | low, medium, high, xhigh |
| `gpt-5-mini` | default | low, medium, high |
| `claude-opus-5`, `claude-opus-4.8`, `claude-opus-4.7` | default, long_context | low, medium, high, xhigh, max |
| `claude-opus-4.6`, `claude-sonnet-4.6` | default, long_context | low, medium, high, max |
| `claude-sonnet-5` | default, long_context | low, medium, high, xhigh, max |
| `gemini-3.1-pro-preview` | default, long_context | low, medium, high |
| `gemini-3.6-flash`, `gemini-3.5-flash` | default, long_context | minimal, low, medium, high |
| `grok-4.5` | default, long_context | low, medium, high |

Note that `none` is not selectable here; `low` is the floor for OpenAI models.

### OpenAI API and Agents SDK

```python
Agent(
    name="Implementation worker",
    model="gpt-5.6-luna",
    model_settings=ModelSettings(reasoning={"effort": "high"}),
)
```

A run-level default can be set with `RunConfig(model=...)`, which agents inherit
unless they declare their own. Official guidance is to start at `gpt-5.6` and
move to a smaller variant only when latency or cost justifies it; this skill is
more aggressive about downshifting because it pairs downshifts with an explicit
verification gate.
Source: [Agents SDK models guide](https://developers.openai.com/api/docs/guides/agents/models).

### Codex CLI

Model and effort are set per profile, or with `-c` overrides for
`model` and `model_reasoning_effort`. Codex applies its own context limit
(see above) and its own usage allowances, which `xhigh` and ultra consume
quickly.

## Non-OpenAI models

Approximate figures for the models selectable in Copilot CLI. Verify prices
before quoting them to anyone.

| Model | Input / Output $/1M | Context | Pick it for |
|---|---|---|---|
| Claude Opus 5 | ~5 / ~25 | 1M | Classic repo-editing benchmarks; leads SWE-Bench Pro at ~80% |
| Claude Sonnet 5 | ~2 / ~10 | 1M | Strongest middle tier; good default under Claude Code |
| Gemini 3.1 Pro | ~2 / ~12 | 1M to 2M | Very large inputs, multimodal, abstract reasoning |
| Gemini 3.5 / 3.6 Flash | ~1.50 / ~7.50 | 1M | High-volume multimodal. Not for deep code logic |
| Grok 4.5 | ~2 / ~6 | 500K | Interactive single-file coding at low cost per turn |
