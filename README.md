# skills

Personal AI agent skills.

Each skill lives in its own directory under `skills/`, containing a `SKILL.md`
that describes when and how the agent should use it, plus any supporting files
(scripts, templates, references).

## Skills

| Skill | What it does |
| --- | --- |
| [`azure-fastapi-easy-auth`](skills/azure-fastapi-easy-auth/) | Scaffold, secure, deploy, and troubleshoot FastAPI on Azure Functions or App Service behind Microsoft Entra Easy Auth. Covers authsettingsV2 Bicep, azd deployment, delegated vs app-only access, and 401 or 403 triage. |
| [`local-hve-core`](skills/local-hve-core/) | Wire or unwire a project-local HVE-Core clone for VS Code and Copilot CLI without installing the marketplace extension or registering components globally. |
| [`model-routing`](skills/model-routing/) | Pick the model and reasoning effort for a task, including for subagents about to be spawned. Also the first thing to check when a run is too slow, too expensive, or worse than expected. |
| [`skill-authoring`](skills/skill-authoring/) | Author, review, and debug the skills in this repo. Decides what belongs in a bundled script versus prose, keeps descriptions triggerable, and validates structure. |
| [`tdd-with-agents`](skills/tdd-with-agents/) | Decide whether test-first work is worth it when an agent writes the code, and run the workflow that replaces it. Covers where the human checkpoint goes and how to tell if agent-written tests are a real safety net. |

`azure-fastapi-easy-auth`, `local-hve-core`, and `skill-authoring` bundle
executable scripts with unit tests, because their work is deterministic.
`model-routing` and `tdd-with-agents` are judgment skills and stay prose.

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
5. Run the structural validator before committing:

   ```bash
   python3 skills/skill-authoring/scripts/validate_skill.py skills/*/
   ```

See [`skill-authoring`](skills/skill-authoring/) for the guidance behind these
steps, including when a procedure should become a script instead of prose.
