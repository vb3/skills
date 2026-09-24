# Model map

**Refreshed 2026-09-23.** Copilot CLI observations below are from version
1.0.88 and the authoring session's live `task` schema. Public-source findings,
including what could not be verified, live in [evidence.md](evidence.md).
Recheck the consuming account: schema membership establishes a valid argument,
not entitlement, numeric context capacity, pricing, or measured quality.

## OpenAI-first candidates

These are routing defaults, not a benchmark leaderboard. Use the workload
rules in [SKILL.md](../SKILL.md); do not infer role or quality solely from a
model's generation or name.

| Role | Copilot CLI ID | Recommendation |
|---|---|---|
| General judgment, ownership, final review | `gpt-6-sol` | Default Sol candidate |
| Bounded, independently verifiable work | `gpt-6-luna` | Default Luna candidate; retain the correctness gate |
| Quality-first alternative | `gpt-6-astra` | Recommend for the hardest long-horizon coding, reasoning, or synthesis when quality warrants it; always include a Sol fallback |
| Latency-oriented alternative | `gpt-5.6-sol-fast` | Allowed when its observed or documented quality and latency fit the task; compare with current Sol |

The last two entries are real IDs in this host schema. Neither is a universal
entitlement. Astra need not be a prerequisite for using the skill, and Sol Fast
is not interchangeable with GPT-6 Sol or with an API `service_tier` parameter.

### Plan-aware access

GitHub's current announcements make GPT-6 Sol/Astra and GPT-5.6 Sol eligible
on Pro+, Max, Business, and Enterprise, not base Pro. GPT-6 Luna and GPT-5.6
Terra/Luna include base Pro. Free/Student use Auto selection only. Check the
actual picker and policy: plan eligibility alone does not finish the access
check. See [the access evidence](evidence.md#copilot-access).

For a **base-Pro judgment task**, consider `gpt-5.6-terra` if its quality gate
is adequate, instead of cycling through unavailable Sol generations. This is
an access fallback, not a claim that Terra matches Sol or Astra on hard work.
If it cannot meet the requirement, report the limitation; do not silently
assign Luna or require a plan upgrade.

### Availability fallback chains

Read left to right and take the first **available and compatible** candidate.
These are availability paths, not claims of identical quality, price, or speed.

| Requested route | Candidate chain |
|---|---|
| Sol | `gpt-6-sol` -> `gpt-5.6-sol` -> `gpt-5.5` |
| Luna | `gpt-6-luna` -> `gpt-5.6-luna` -> `gpt-5.4-mini` |
| Astra | `gpt-6-astra` -> the Sol chain |
| Sol Fast | `gpt-5.6-sol-fast` -> the Sol chain |

Compatibility includes the required quality gate, modalities/tools, actual
context capacity, supported effort controls, and deadline. An older model is
not proved compatible just because its ID is in a chain. In particular,
`gpt-5.5` cannot encode `max` in this snapshot and `gpt-5.4-mini` cannot encode
`max` or `long_context`. Re-evaluate those routes rather than silently clamping.

If no Luna candidate meets the gate, use an available Sol candidate if it fits
the constraints; report that this is a capacity step up, not a saving. The
base-Pro branch above takes precedence over trying unavailable Sol candidates.
If no judgment-capable candidate fits, use a task-justified available
alternative or report the blocker. A matched local eval can justify an
intermediate model such as `gpt-5.6-terra`; no universal dominance claim
excludes it.

An access failure permits a compatible fallback, not identical retries against
the unavailable model. A rate limit needs service-specific retry handling.
Neither permits repeating an external write whose completion is uncertain.
Host-managed dispatch still follows the override rules in `SKILL.md`.

## Provider economics

**Prefer OpenAI under Copilot as a routing policy, not a universal price
theorem.** Check the current account's billing regime and relevant rates.
Vendor API list prices, Copilot AI-credit charges, and legacy premium-request
multipliers are different quantities.

Use the [verified Copilot rate snapshot](evidence.md#copilot-pricing), including
cache writes and long-context thresholds. GPT-6 Sol is cheaper than the listed
Opus models but matches Sonnet 5's rates; Astra costs more than those models.
The OpenAI preference is not a reason to label Astra a cost-saving alternative
to Claude. Paid Auto has a 10% model-cost discount, but does not pin a model.

| Environment | Compare using |
|---|---|
| Copilot token/AI-credit billing | Copilot model rates, cached versus uncached usage, output/reasoning usage, account discounts, and actual tool-loop usage |
| A request-billed plan | Its documented multiplier and number of charged requests; do not import token-based effort costs |
| Direct OpenAI or another API | That endpoint's input, cached input, billable output/reasoning, tool, and service-tier rates |
| Subscription or bundled allowance | The product's usage policy, limits, and measured consumption; no invented dollar conversion |

For token billing, sum actual usage times the applicable rates over the whole
task, including retries, workers, and review. For request billing, sum charged
requests times their multipliers. Divide total charge by accepted results when
comparing routes; record acceptance criteria and elapsed time alongside cost.

This refresh does not retain the old output-normalized "Luna medium = 1x"
effort grid. Effort does not specify how many tokens a task consumes, input
and cached usage differ between workloads, and API ratios are not Copilot
prices. Unknown rates stay unknown; they are not zero and do not justify an
exact savings claim.

## Harness syntax

### Copilot CLI

Authoring-session observations, not a promise for other installations:

- `task` accepts `model`, `reasoning_effort`, and `context_tier`. Its model
  enum includes the four primary candidates above.
- The current task instructions require omitted overrides unless the current
  request or applicable persistent instructions explicitly require values.
  `/subagents` resolves default and per-agent settings.
- `/model` selects a session model; it is not the same as configuring subagent
  defaults. `/usage` reports session usage.
- `copilot --help` exposes `--model`, `--reasoning-effort`, and
  `--context default|long_context`. Its global effort parser lists `none`,
  `minimal`, `low`, `medium`, `high`, `xhigh`, and `max`. A parser-wide choice
  is not evidence that a particular model supports every value.

The task schema exposes the ordinary `low`/`medium`/`high` controls and
explicit model lists for additional efforts and long context:

| Relevant model IDs | Additional task efforts | `context_tier` |
|---|---|---|
| `gpt-6-sol`, `gpt-6-luna`, `gpt-6-astra` | `xhigh`, `max` | `default`, `long_context` |
| `gpt-5.6-sol-fast`, `gpt-5.6-sol`, `gpt-5.6-luna`, `gpt-5.6-terra` | `xhigh`, `max` | `default`, `long_context` |
| `gpt-5.5`, `gpt-5.4` | `xhigh` | `default`, `long_context` |
| `gpt-5.4-mini`, `gpt-5.3-codex` | `xhigh` | `default` |
| `gpt-5-mini` | None listed | `default` |
| `claude-opus-5.5`, `claude-opus-5`, `claude-sonnet-5` | `xhigh`, `max` | `default`, `long_context` |
| `claude-haiku-4.5` | None listed | `default` |

This is a routing-relevant subset, not the complete model catalog. The live
schema also lists other Claude, Gemini, Grok, and MAI candidates; inspect it
when one is needed rather than copying a stale vendor roundup. Do not invent
`none` or `minimal` support for these OpenAI task routes from the CLI's global
parser options.

When the user explicitly requests a CLI model and effort, the observed syntax
is, for example:

```bash
copilot --model gpt-6-sol --reasoning-effort high
```

An explicitly requested task override uses that tool's own fields instead:

```json
{
  "model": "gpt-6-sol",
  "reasoning_effort": "high"
}
```

This is a fields-only illustration, not a complete task call or a reason to
override host defaults. Add `context_tier` only when both authorized and needed.
Do not create unverified shorthand aliases such as `gpt-6`, or extrapolate a
`gpt-6-sol-fast` ID from the available GPT-5.6 fast variant.

### VS Code and other agent hosts

Inspect the active tool's accepted model values. Some hosts expose display
labels, some IDs, and some delegate selection to configuration. Use the exact
returned value; do not derive a display label by title-casing a CLI ID.

Inspect effort and context fields independently. When absent, give the
recommendation as unenforced guidance and do not invent an argument or claim
that words in a prompt implement a model reasoning control. No current
GPT-6 VS Code label is asserted by this CLI-only snapshot.

### OpenAI API, Agents SDK, and Codex

The public API documents `gpt-6-sol`, `gpt-6-luna`, and `gpt-6-astra`; still
resolve account access before setting SDK `model` or reasoning options.
A working Copilot ID alone does not establish API availability, notably for
`gpt-5.6-sol-fast`. Check the installed SDK's supported `ModelSettings` fields
rather than copying Copilot arguments.

Use Responses for GPT-6 reasoning with tools. Sol/Luna permit Chat Completions
function calling only at `none` effort; Astra does not support that endpoint's
function calling and cannot use `none`. Sol/Luna support API efforts from
`none` through `max`, excluding `minimal`; Astra supports `low` through `max`.
Those API values do not add unsupported controls to a Copilot task.
The [API evidence](evidence.md#api-capabilities-are-not-harness-guarantees)
also records numeric API windows, which must not be copied as host limits.

For Codex, inspect the installed version's model choices and profile schema.
Use its supported model and reasoning configuration, not Copilot's
`context_tier` field. Check product context and usage limits separately from
API model limits; this skill does not retain a hard-coded Codex context size.

## Measuring a route

Use representative inputs with independent acceptance criteria and keep the
host, tools, context, and effort explicit. Compare quality, p50/p95 completion
time, time to useful output, actual provider charge, and retries. Repeat enough
cases to expose failure modes; a single attractive answer is not a ranking.

Test access separately from capability. A model picker entry or successful
trivial response confirms less than a representative workload. If Astra or
Sol Fast is unavailable, exercise the advertised fallback with the same gate.
If a comparison changes generation and effort together, do not attribute its
gain to effort alone.

Prompt caching, API batch processing, and paid service tiers are
provider-specific controls. Consult the freshly verified sources in
[evidence.md](evidence.md) before generating their configuration. No cache-write
premium, explicit-breakpoint protocol, speed multiplier, or batch discount
applies merely because it appeared in an older version of this skill.
