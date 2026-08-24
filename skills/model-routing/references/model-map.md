# Model map

**Model, pricing, and speed facts last verified: 2026-08-24. VS Code
runSubagent labels last verified: 2026-08-19.** This is the volatile half of the
skill. When anything here changes, update the affected verification date. The
tier logic in `SKILL.md` is designed to survive without edits.

## OpenAI GPT-5.6 family

Launched 2026-07-09. The tier names (Sol, Terra, Luna) are generation
independent and are intended to persist across future releases, so
"frontier / balanced / efficient" maps onto them stably.

| Tier | Model ID | Input $/1M | Cached input $/1M | Output $/1M |
|---|---|---|---|---|
| Frontier | `gpt-5.6-sol` | 4.00 | 0.40 | 20.00 |
| Balanced | `gpt-5.6-terra` | 2.00 | 0.20 | 12.00 |
| Efficient | `gpt-5.6-luna` | 0.20 | 0.02 | 1.20 |

`gpt-5.6` is an alias that resolves to Sol. Do not use it in production code,
because it silently bills at frontier rates.

**Sol's $4/$20 is promotional and expires 2026-11-21**, reverting to the list
price of $5/$30. Every Sol cost figure in this skill uses the promotional rate.
When it lapses, Sol's relative cost rises from ~17x Luna to ~25x Luna and the
cost grid below must be recomputed. Sources:
[OpenAI pricing](https://developers.openai.com/api/docs/pricing),
[CometAPI](https://www.cometapi.com/gpt-5-6-pricing/).

**Prices changed on 2026-07-30.** Terra dropped about 20% from $2.50/$15, and
Luna dropped about 80% from $1.00/$6.00. Any advice written before that date
undervalues Luna badly. Sources:
[OpenAI price-performance post](https://openai.com/index/advancing-the-price-performance-frontier-with-gpt-5-6/),
[BenchLM API pricing](https://benchlm.ai/openai/api-pricing),
[explainX](https://www.explainx.ai/blog/openai-gpt-5-6-luna-terra-price-cuts-july-2026).

Relative per-token cost, normalized on output price: Terra is 10x Luna, Sol is
~17x Luna and ~1.7x Terra. Note that the promotional rate breaks the previously
clean 1:10:25 ratio, and Sol's input-to-output ratio (1:5) now differs from
Terra's and Luna's (1:6), so input-normalized and output-normalized figures no
longer agree. The grid below is output-normalized.

## Speed and latency

The axis that the cost tables above say nothing about. Output speed is measured
in tokens per second (TPS) at `max` effort; time to first token (TTFT) is
measured to the first *answer* token, after any thinking phase.

| Model | Output TPS | Intelligence index | TTFT |
|---|---|---|---|
| `gpt-5.6-luna` | 140-149 | 51 | <0.4 s |
| `gpt-5.6-terra` | 105-121 | 55 | ~0.4 s |
| `gpt-5.6-sol` | 72-110 | 59 | ~0.5 s |

**Sources disagree on the exact TPS figures.** Two independent passes over
Artificial Analysis returned 140/121/72 and 149/105-120/90-110 for
Luna/Terra/Sol. Treat the ranges as directional. What both agree on, and what
the routing rule actually depends on, is the *ordering and rough spacing*: Luna
is fastest, Terra is close behind, and Sol is roughly half Luna's rate.
Sources: [Sol](https://artificialanalysis.ai/models/gpt-5-6-sol),
[Terra](https://artificialanalysis.ai/models/gpt-5-6-terra),
[Luna](https://artificialanalysis.ai/models/gpt-5-6-luna).

**The consequence that matters is narrower than it looks.** At a *fixed* effort
level no model here dominates another on both speed and intelligence, so Terra
is on the speed-intelligence frontier in that frozen sense. But effort is not
fixed, and once it varies the enclosure returns: latency is roughly output
tokens divided by this rate, and effort moves the token count several-fold.
Sol at `medium` ends up both faster and better than Terra at `xhigh`. See
[evidence.md](evidence.md#terra-is-off-the-cost-frontier-and-the-speed-axis-does-not-rescue-it).

TTFT figures are the weakest numbers in this file; Artificial Analysis renders
its TTFT provider pages in JavaScript and they could not be fetched directly.
Do not quote them to anyone without rechecking in a browser.

### Unavailable speed controls

Recorded so they are not rediscovered and recommended. **None of these are
reachable from the harnesses this skill covers. Never route to them.**

| Control | What it offers | Why it is out of scope |
|---|---|---|
| **Fast mode** | 2x price for up to 2.5x speed, quality unchanged | API-only `service_tier: "fast"`. Not available to this user |
| **Ultrafast** | Cerebras-hosted Sol at ~750 TPS, ~14x standard Sol | Limited API preview, no published price |
| **Claude fast mode** | 2x price for up to 2.5x speed | Research preview, API-only, not in Copilot CLI |

Sources: [OpenAI fast mode](https://developers.openai.com/api/docs/guides/fast-mode),
[OpenAI Ultrafast preview](https://openai.com/index/previewing-ultrafast/),
[Anthropic fast mode](https://platform.claude.com/docs/en/build-with-claude/fast-mode).

The consequence for routing: latency has to be bought with round trips, output
length, or caching. There is no lever that buys speed with money alone, so a
turn that is too slow at a given quality bar is a signal to move the work off
the interactive path, not to pay for it.

### Batch API

The correct destination for work with no latency budget at all: a 50% discount
against synchronous pricing, a 24-hour turnaround ceiling, and substantially
higher rate limits. Route evals, bulk classification, embedding jobs, and
overnight analysis here rather than reaching for a cheaper model.
Source: [OpenAI batch guide](https://developers.openai.com/api/docs/guides/batch).

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

**Effort is a ceiling, not a fixed cost.** OpenAI states the models reason
adaptively, spending fewer tokens on simple tasks and more on complex ones. A
high effort setting on an easy task does not automatically burn the full
multiplier. This cuts both ways for latency: raising effort does not reliably
slow down easy work, and lowering it does not reliably speed up hard work.

Two things that are **not** effort levels:

- **Pro mode** is `reasoning.mode: "pro"`, settable on any GPT-5.6 model,
  orthogonal to effort, defaulting to `medium` effort. It adds work before
  returning a single answer, and bills at standard token rates, so its cost
  comes from generating more tokens rather than a price premium. No wall-clock
  figures are published; expect higher latency.
- **Ultra** is a multi-agent mode, exposed on the API as
  `multi_agent: { enabled: true, max_concurrent_subagents: N }` behind the
  `responses_multi_agent=v1` beta, defaulting to 3 concurrent subagents. It
  trades total tokens for wall-clock time and is not an effort value. It
  *reduces* wall clock on genuinely parallelizable work and *adds* overhead on
  sequential work.
  Source: [multi-agent guide](https://developers.openai.com/api/docs/guides/responses-multi-agent).

## Approximate effort cost multipliers

Community and third-party measurements. **No primary OpenAI source publishes
these numbers**; a targeted search for one found only qualitative language in
the vendor docs. Treat as directional and do not quote them as vendor figures.
Actual reasoning tokens are visible in
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

The tokens and latency columns track each other closely, and that is the
mechanism behind the whole latency section of `SKILL.md`: reasoning tokens are
generated at the model's output rate, so anything that changes token count
changes wall clock roughly proportionally. OpenAI's own latency guidance puts
it as "cutting 50% of your output tokens may cut ~50% of your latency", against
only 1% to 5% for halving the *input*.
Source: [latency optimization guide](https://developers.openai.com/api/docs/guides/latency-optimization).

### Effective cost grid

Model price multiplied by effort token burn, normalized so Luna medium is 1x.
This is the table that makes the barbell argument concrete: Luna `xhigh` is
cheaper than Terra `low`.

| | `low` | `medium` | `high` | `xhigh` | `max` |
|---|---|---|---|---|---|
| **Luna** | 0.35x | 1x | 1.75x | 2.5x | 4x |
| **Terra** | 3.5x | 10x | 17.5x | 25x | 40x |
| **Sol** | 5.8x | 16.7x | 29x | 42x | 67x |

**Method and its limits.** Effort multipliers are the midpoints of the ranges
above, so `low` is 0.35x and `high` is 1.75x. The cross-model ratio is
1:10:16.7 for Luna:Terra:Sol, output-normalized, using Sol's promotional price.
Under Sol's $5/$30 list price the ratio returns to 1:10:25 and every Sol figure
in this row rises by about 50%.

The effort axis is the weak part. Effort mostly inflates reasoning and output
tokens while input cost stays roughly fixed, so these behave as
output-normalized figures rather than true end-to-end cost multipliers. A
request with a large prompt and a short answer will show a much flatter effort
curve than this grid implies. Treat the model axis as solid and the effort axis
as directional.

`SKILL.md` rounds these to whole numbers (6x, 17x, 29x, 42x). Do not read
precision into any of them.

Note that the Luna `xhigh` versus Terra `low` crossover (2.5x against 3.5x)
survives the price correction, so the barbell argument does not depend on which
Sol price is in effect.

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

Caching is also a **latency** lever, not only a cost lever: a cache hit skips
prefill on the cached prefix and so reduces TTFT. OpenAI confirms the direction
but publishes no figures, and no controlled measurement was found. Practitioner
reports of 30% to 70% TTFT reduction on large static prefixes are consensus
rather than measurement.

**Programmatic tool calling** lets the model coordinate tools in code rather
than through round trips. OpenAI reports leaner system prompts plus PTC
improving eval scores 10% to 15% while cutting tokens 41% to 66%. Worth using
for bounded, tool-heavy workflows with predictable output schemas.
Source: [OpenAI migration guide](https://developers.openai.com/api/docs/guides/latest-model).

## Latency levers: measured gains

Evidence for the lever ordering in `SKILL.md`, which is the single normative
list. This table is evidentiary; do not read it as a second procedure, and note
that two of its rows are not levers you can pull.

| Lever | Claimed gain | Confidence |
|---|---|---|
| Parallel tool calls and parallel subagents | Up to 90% cut in wall clock on tool-heavy research | Anthropic production engineering blog |
| Generate fewer output tokens (lower effort, cap `max_output_tokens`, demand concision) | Roughly proportional: 50% fewer tokens, ~50% less latency | OpenAI latency guide |
| Prompt caching | 30% to 70% of TTFT | Practitioner consensus, no published figure |
| Predicted outputs, for edits where most output is unchanged | "Significantly reduce latency"; rejected tokens still billed | [OpenAI predicted outputs](https://developers.openai.com/api/docs/guides/predicted-outputs) |
| *(not a lever)* Speculative decoding | 2x to 3x | Provider-side and already inside the published TPS figures |
| *(not a lever)* Reduce input tokens | 1% to 5% only | OpenAI latency guide. Use this for cost and context quality, not for latency |

Sources: [Anthropic multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system),
[OpenAI latency optimization](https://developers.openai.com/api/docs/guides/latency-optimization),
Leviathan et al., [arXiv:2211.17192](https://arxiv.org/abs/2211.17192).

Two findings worth stating explicitly because they contradict intuition:

- **Shrinking the prompt is nearly useless for latency.** Halving input buys 1%
  to 5%. Halving output buys ~50%. People reach for the wrong one.
- **Streaming does not help reasoning models the way it helps chat models.**
  The model emits thinking tokens before any answer token, so there is a "dark
  period" during which streaming has nothing to show. OpenAI's recommended
  mitigations are progress indication and asking for a short preamble before
  deeper reasoning, which improves time to first *visible* token without
  changing time to first answer token.

## Human latency thresholds

The thresholds behind the interactive budget in `SKILL.md`, unchanged since
Miller 1968 and Card et al. 1991, popularized by Nielsen:

| Threshold | Meaning |
|---|---|
| 0.1 s | Feels instantaneous |
| 1 s | Upper limit for uninterrupted flow of thought |
| 10 s | Upper limit for holding attention; beyond this the user context-switches and must reorient on return |

Source: [Nielsen, response time limits](https://www.nngroup.com/articles/response-times-3-important-limits/).

No published study was found measuring the latency at which a developer
abandons or rejects an AI coding suggestion. The widely repeated "300 ms for
inline completion" figure is practitioner lore, not a citable measurement.

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
| `claude-sonnet-5` | default, long_context | low, medium, high, xhigh, max |
| `claude-opus-4.6`, `claude-sonnet-4.6` | default, long_context | low, medium, high, max |
| `claude-haiku-4.5` | default | low, medium, high |
| `gemini-3.1-pro-preview` | default, long_context | low, medium, high |
| `gemini-3.7-flash` | default, long_context | low, medium, high |
| `gemini-3.6-flash`, `gemini-3.5-flash` | default, long_context | minimal, low, medium, high |
| `grok-4.6` | default, long_context | low, medium, high, xhigh |
| `grok-4.5` | default, long_context | low, medium, high |
| `mai-code-1.1-flash`, `mai-code-1-flash-picker` | default | low, medium, high |

Note that `none` is not selectable here; `low` is the floor for OpenAI models.
`minimal` is exposed **only** on Gemini 3.5 and 3.6 Flash. It is not available
on Gemini 3.7 Flash, which is a common wrong assumption given the naming.

Read this table as volatile even by the standards of this file. It is derived
from the live tool schema, and models appear and disappear between releases:
`claude-haiku-4.5`, `gemini-3.7-flash`, `grok-4.6`, and the `mai-code-1` family
were all absent at the previous verification on 2026-08-04. Re-derive it from
the schema rather than trusting this copy.

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
before quoting them to anyone. Speed figures are third-party and provider
dependent; Copilot CLI does not publish which provider it routes to.

| Model | In / Out $/1M | Context | Output TPS | TTFT | Pick it for |
|---|---|---|---|---|---|
| Claude Opus 5 | 5 / 25 | 1M | 56-62 | ~0.75 s | Classic repo-editing benchmarks; highest measured intelligence index (63) |
| Claude Sonnet 5 | 2 / 10 | 1M | not found | p95 ~20 s | Strongest middle tier; good default under Claude Code |
| Claude Haiku 4.5 | 1 / 5 | **200K** | 94-139 | **~0.6 s** | The only non-OpenAI model with sub-second TTFT. SWE-Bench Verified 73.3% |
| Claude Sonnet 4.6 | 3 / 15 | 1M | 44-55 | ~1.1 s | Superseded by Sonnet 5 |
| Claude Opus 4.6 / 4.7 / 4.8 | 5 / 25 | 1M | not found | not found | Superseded by Opus 5 at the same price |
| Gemini 3.1 Pro | 2 / 12 (4 / 18 above 200K) | 1M | 121-126 | 23-35 s | Very large inputs, multimodal, abstract reasoning. Not for interactive work |
| Gemini 3.7 Flash | 0.75 / 3.75 (intro) | 1M | **340-357** | ~10-12 s | Highest throughput available. Intelligence index 56, above Luna |
| Gemini 3.6 Flash | 1.50 / 7.50 | 1M | 225-304 | 13-19 s | High-volume multimodal. Not for deep code logic |
| Gemini 3.5 Flash | 1.50 / 9 | 1M | 170-225 | 17-19 s | Superseded by 3.6 on both price and speed |
| Grok 4.6 | 2 / 6 | 500K | ~61 (disputed) | p95 ~6 s | Intelligence index 61, near Sol, at a third of the price. SWE-Bench 95.6% |
| Grok 4.5 | 2 / 6 | 500K | ~61 (disputed) | p95 ~6 s | Superseded by 4.6 |
| GPT-5.4-mini | 0.75 / 4.50 | 400K | 163-201 | 0.7-3.8 s | Nothing new. Luna is cheaper and stronger |

**The Gemini Flash trap.** Flash models have the highest tokens per second and
some of the worst time to first token, because they think before emitting an
answer token. High TPS does not mean low latency. Worked example against Luna
at 149 TPS and <0.4 s TTFT:

| Response length | Luna | Gemini 3.7 Flash | Winner |
|---|---|---|---|
| 500 tokens | ~4.1 s | ~13.5 s | Luna, by 3x |
| 5,000 tokens | ~34 s | ~27 s | Flash, by ~20% |

So Flash is a **throughput** pick for long generations and batch pipelines, and
a bad **latency** pick for short interactive turns. One source reports 0.4-0.5 s
TTFT for Flash in agentic pipelines against Artificial Analysis's 10-12 s; the
likely reconciliation is that the low figure measures the first *thinking*
token. Copilot CLI does not surface thinking tokens, so assume the high figure.

**Grok 4.6 caveat.** It gained sharply on single-issue patching (SWE-Bench 86%
to 95.6%) while slightly *regressing* on multi-step agentic coding (LiveBench
56.5 to 54.2). Marketing emphasizes the first. For long-horizon agent loops the
gain may not be real. Its TPS figure is contradicted across sources and should
be rechecked before it is relied on.
