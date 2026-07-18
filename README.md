# skills

Personal AI agent skills.

Each skill lives in its own directory under `skills/`, containing a `SKILL.md`
that describes when and how the agent should use it, plus any supporting files
(scripts, templates, references).

## Structure

```
skills/
  <skill-name>/
    SKILL.md        # name, description, and instructions
    ...             # optional supporting files
```

## Adding a skill

1. Create a directory under `skills/` named for the skill (kebab-case).
2. Add a `SKILL.md` with a clear name, a description of when to use it, and steps.
3. Add `evals/evals.json` with realistic prompts, expected outputs, and
   objective expectations. Include representative success cases and difficult
   edge cases, then compare runs with and without the skill using
   `skill-creator`.
4. Keep skills tool-agnostic where possible so they work across agents.
