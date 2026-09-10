# Harness encoding

Read this reference immediately before emitting configuration or dispatching.
The live host schema is authoritative; this file records verified differences
that are easy to miss.

## Copilot CLI task tool

Snapshot checked 2026-09-09:

| `model` | `reasoning_effort` | `context_tier` |
|---|---|---|
| `gpt-5.6-luna`, `gpt-5.6-terra`, `gpt-5.6-sol`, `gpt-6-astra` | `low`, `medium`, `high`, `xhigh`, `max` | `default`, `long_context` |
| `gpt-5.6-sol-fast` (internal only) | `low`, `medium`, `high`, `xhigh`, `max` | `default`, `long_context` |
| `claude-sonnet-5`, `claude-opus-5` | `low`, `medium`, `high`, `xhigh`, `max` | `default`, `long_context` |
| `claude-haiku-4.5` | Omit; not exposed | `default` |

Fable 5 and 5.1 appear in public GitHub documentation but were absent from this
snapshot. Select another in-family model only under the quality-preserving
fallback rule in [`SKILL.md`](../SKILL.md). `none` was also absent from this
task schema.

Emit only supported fields. A verified bounded-worker route can encode:

```json
{"model": "gpt-5.6-luna", "reasoning_effort": "medium", "context_tier": "default"}
```

## VS Code runSubagent

Use exact labels from the live available-model list rather than API IDs. A
previously observed Luna label was `GPT-5.6 Luna (copilot)` on 2026-08-19.

When the schema exposes only a model selector, omit effort and context fields
and report the intended effort as unenforced. Prompt wording does not create a
missing control.

## OpenAI API and Agents SDK

Responses uses `model` with `reasoning: {"effort": "high"}`. The Agents SDK
uses per-agent `model` and `ModelSettings(reasoning={"effort": "high"})`; a run
configuration can supply defaults. Confirm override precedence in the installed
SDK.

Source: [Agents SDK models](https://developers.openai.com/api/docs/guides/agents/models).

## Codex

Profiles use `model` and `model_reasoning_effort`, including through `-c`
overrides. Check the installed host's accepted values and limits.

Source: [Codex configuration](https://developers.openai.com/codex/config-reference/).

## Claude API

Use the IDs in [model-map.md](model-map.md) and set
`output_config: {"effort": "high"}` where supported. Omit effort for Haiku.
Thinking configuration and effort are separate controls.

Source: [Claude effort](https://platform.claude.com/docs/en/build-with-claude/effort).
