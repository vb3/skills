# Harness encoding

Read this reference immediately before emitting configuration or dispatching.
The live host schema is authoritative; this file records verified differences
that are easy to miss.

## Copilot CLI delegation

Apply the override-authorization rule in [`SKILL.md`](../SKILL.md). The
registry below is for explicit configuration, not a replacement for host
preferences.

Relevant IDs checked in this session's task schema on 2026-09-30:

| Candidate | CLI `model` | Direct API `model` |
|---|---|---|
| Luna | `gpt-6-luna` | `gpt-6-luna` |
| Sol | `gpt-6.1-sol` | `gpt-6.1-sol` |
| Astra | `gpt-6-astra` | `gpt-6-astra` |
| Sonnet | `claude-sonnet-5.5` | `claude-sonnet-5-5` |
| Opus | `claude-opus-5.5` | `claude-opus-5-5` |
| Haiku | `claude-haiku-4.5` | `claude-haiku-4-5-20251001` |

The current task entries above expose low through max effort, except Haiku,
which has no effort field. Fable 5/5.1 appear in public documentation but are
absent from this task snapshot. `none` is not exposed by this task tool,
even for API models that support it. Context support must be checked per
model/host; an exposed selector does not establish a numeric window.

For a user-authorized explicit bounded-worker configuration, for example:

```json
{"model": "gpt-6-luna", "reasoning_effort": "medium"}
```

## VS Code runSubagent

Use exact labels from the live available-model list rather than API or CLI
IDs. Do not reconstruct labels from branding or transfer old labels to a new
version.

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

Use the API IDs above and set `output_config: {"effort": "medium"}` for an
ordinary Opus 5.5 reasoning route. Select effort for the task, not from an
older model's default; omit effort for Haiku.
Thinking configuration and effort are separate controls.

Source: [Claude effort](https://platform.claude.com/docs/en/build-with-claude/effort).
