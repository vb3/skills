---
name: local-hve-core
description: Wire a project to a local HVE-Core clone through a .hve-core symlink, VS Code chat component locations, and project-local Copilot CLI skill links. Use when the user asks to use, link, wire, develop against, or test a local HVE-Core checkout instead of installing the marketplace extension.
---

# Local HVE-Core

Connect a project to a local HVE-Core checkout without copying HVE-Core
artifacts into the project. Default the source clone to
`~/repos/forks/microsoft-hve-core` when the user does not provide a path.
Expand `~` to the current user's home directory before comparing or creating
symlinks.

## Setup

All deterministic work lives in [scripts/wire_hve_core.py](scripts/wire_hve_core.py).
Run it rather than performing the symlink, exclude, settings, or skill-linking
steps by hand. Your job is to resolve inputs, handle the gates it reports, and
report the outcome.

### Script contract

```bash
python3 "<skill-directory>/scripts/wire_hve_core.py" <check|apply|verify> \
  --project-root <project> [--source <clone>]
```

| Mode | Effect |
| --- | --- |
| `check` | Read-only. Reports current state and everything still pending |
| `apply` | Creates the symlinks, appends the exclude rules, and merges `.vscode/settings.json` |
| `verify` | Read-only. Asserts the finished state and lists every failure |

Every mode prints a JSON state object on stdout. Exit codes are gates:

| Code | Meaning | Your response |
| --- | --- | --- |
| 0 | Success | Continue |
| 2 | Source clone missing | Offer to clone; see step 2 |
| 3 | Symlink collision | Stop and ask the user; see step 3 |
| 4 | `.vscode/settings.json` is not strict JSON | Merge by hand; see step 5 |
| 5 | Verification failed | Report `failures` verbatim; do not paper over them |

Defaults: source `~/repos/forks/microsoft-hve-core`. The `installer` and
`experimental` packages are always excluded and cannot be enabled. The script
expands `~`, resolves the project Git root, and generates locations from the
clone as it exists now, so fork-specific packages are picked up automatically.

Two mechanisms surface the components, both scoped to the project:

- VS Code reads `chat.*Locations` in `.vscode/settings.json`, pointing at
  `.hve-core/.github/<component>/<package>`.
- Copilot CLI auto-discovers `.github/skills/`, so the script links each skill
  package there as `.github/skills/<package>` and git-excludes the links. No
  registration command is involved.

### Steps

1. Read the target repository's instructions, confirm the source clone path,
   then run `check`. If the user asks for experimental components, tell them
   this skill does not support them and continue without them.

2. If `check` exits 2, the source clone is missing. Stop and offer to work with
   the user to clone `https://github.com/microsoft/hve-core.git` into
   `~/repos/forks/microsoft-hve-core`. Do not clone silently or choose another
   destination.

3. If `check` exits 3, either `.hve-core` or a `.github/skills/<package>` path
   already exists as a directory, regular file, broken symlink, or symlink to
   another target. This is a hard stop. Report
   the `error` field, which names the conflicting type and, for a mismatched
   symlink, both the current and requested targets. Ask the user for an
   explicit disposition. In non-interactive execution, report that approval is
   required and exit. Do not remove, move, rename, overwrite, or write inside
   the conflicting path, and do not run `apply` until the user chooses.

4. Run `apply` with the same arguments. It is idempotent, so a second run is a
   no-op that leaves every byte unchanged.

5. If `apply` exits 4, it completed everything except the VS Code settings
   merge, because the file carries JSONC comments or a non-object
   `chat.*Locations` value. It left the file untouched. Merge
   `vscode_settings.missing_entries` from the JSON output by hand with a
   surgical edit that preserves comments and formatting. Each setting is a JSON
   object mapping each project-relative `.hve-core/` path to boolean `true`:

   ```json
   {
     "chat.agentFilesLocations": {
       ".hve-core/.github/agents/hve-core": true
     }
   }
   ```

   Never convert a setting to an array of `{ "path": ..., "enabled": ... }`
   objects, and never drop an unrelated setting or existing location.

6. Run `verify`. Resolve any reported failure before claiming success.

7. Report the resolved source, `configured_location_count`,
   `linked_skill_package_count`, and the required reload actions: VS Code must
   reload its window, and an active Copilot CLI session must run
   `/skills reload`.

## Boundaries

- Use the local clone and symlink path only. Leave marketplace extensions
  unchanged unless the user explicitly requests extension cleanup.
- Preserve user changes in `.vscode/settings.json` and the working tree.
- Never register skills globally with `copilot skill add`. That writes to
  `~/.copilot/settings.json`, which loads the skills into every project on the
  machine. `verify` reports leftovers from older runs so the user can remove
  them.
- Leave the project's own skills in `.github/skills/` untouched.
- Never replace an existing file, directory, broken symlink, or mismatched
  symlink without explicit approval. Collision detection happens before every
  mutation.
- Do not reimplement the script's logic in prose or ad hoc shell. If its
  behavior is wrong, change the script and its tests.
- The `installer` and `experimental` packages are out of scope. Never configure
  or link them, even on request.

## Development

The script is unit tested. From the skill directory:

```bash
python3 -m unittest discover -s tests -q
```
