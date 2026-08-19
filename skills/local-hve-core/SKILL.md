---
name: local-hve-core
description: Wire a project to a local HVE-Core clone through a .hve-core symlink and VS Code chat component locations. Use when the user asks to use, link, wire, develop against, or test a local HVE-Core checkout instead of installing the marketplace extension.
---

# Local HVE-Core

Connect a project to a local HVE-Core checkout without copying HVE-Core
artifacts into the project. Default the source clone to
`~/repos/forks/microsoft-hve-core` when the user does not provide a path.
Expand `~` to the current user's home directory before comparing or creating
symlinks.

## Setup

1. Resolve the target project's Git root and the absolute source clone path.
   Read the target's repository instructions before changing files. If the
   source clone does not exist, stop setup and offer to work with the user to
   clone `https://github.com/microsoft/hve-core.git` into
   `~/repos/forks/microsoft-hve-core`. Do not silently choose another location
   or clone without the user's approval.

2. Run a read-only preflight before changing **any** target file:

   - target Git status;
   - `.hve-core`;
   - `.vscode/settings.json`;
   - the repository-local exclude path from
     `git rev-parse --git-path info/exclude`;
   - source `.github/{agents,prompts,instructions,skills,hooks}` directories.

   Continue only when the source contains the expected component roots.

3. Classify `.hve-core` before making any target mutation:

   | Current state | Required action |
   | --- | --- |
   | Path is absent | Continue with setup |
   | Symlink resolves to the requested source | Reuse it and continue |
   | Directory, regular file, broken symlink, or symlink to another target | Stop and ask the user how to handle the collision |

   A collision is a hard stop. Do not remove, move, rename, overwrite, or write
   inside `.hve-core`. Do not edit VS Code settings, Git excludes, or any other
   project file before the user explicitly chooses a disposition. In
   non-interactive execution, report the existing path type and exit without
   mutation. For a mismatched symlink, report both its current resolved target
   and the requested resolved source path.

4. When `.hve-core` is absent, create the project-root symlink:

   ```bash
   ln -s <absolute-source-clone> <project-root>/.hve-core
   ```

5. Add `.hve-core` to the repository-local exclude file returned by
   `git rev-parse --git-path info/exclude`. Do not construct this path by
   appending `info/exclude` to `.git` or `git rev-parse --git-dir`; linked
   worktrees may use a common Git directory for excludes. Keep this machine-
   specific path out of the shared `.gitignore`. Append the rule only when an
   exact `.hve-core` rule is absent, and ensure it begins on a new line when
   the existing file lacks a trailing newline.

6. Merge HVE-Core locations into `.vscode/settings.json`. Preserve every
   unrelated setting and existing location. Generate entries from the current
   clone rather than caching a package list:

   | Setting | Locations |
   | --- | --- |
   | `chat.agentFilesLocations` | Each direct directory under `.hve-core/.github/agents`; include its `subagents` directory when present |
   | `chat.promptFilesLocations` | Each direct directory under `.hve-core/.github/prompts` |
   | `chat.instructionsFilesLocations` | Each direct directory under `.hve-core/.github/instructions` |
   | `chat.agentSkillsLocations` | `.hve-core/.github/skills` and each direct package directory except `installer` |
   | `chat.hookFilesLocations` | Each direct directory under `.hve-core/.github/hooks` |

   Each `chat.*Locations` setting must be a JSON object that maps each project-
   relative `.hve-core/` path to boolean `true`:

   ```json
   {
     "chat.agentFilesLocations": {
       ".hve-core/.github/agents/hve-core": true
     }
   }
   ```

   Do not use an array of `{ "path": ..., "enabled": ... }` objects. Exclude
   every directory named `experimental` by default. Include experimental
   locations only when the user explicitly opts in.

   If the settings file is JSONC, preserve its comments and formatting with a
   surgical edit. If it is strict JSON, keep it valid JSON. Create the `.vscode`
   directory and settings file when absent.

7. Validate completion:

   - `.hve-core` resolves to the requested source;
   - every enabled `chat.*Locations` path exists and is a directory;
   - `installer` and non-opted-in `experimental` skill locations are absent;
   - `git check-ignore -v --no-index .hve-core` attributes the rule to the
     path returned by `git rev-parse --git-path info/exclude`;
   - target Git status contains no unexpected changes.

8. Report the resolved source, number of configured locations, whether
   experimental components were included, and that VS Code must reload its
   window to discover the components.

## Boundaries

- Use the local clone and symlink path only. Leave marketplace extensions
  unchanged unless the user explicitly requests extension cleanup.
- Preserve user changes in `.vscode/settings.json` and the working tree.
- Never replace an existing file, directory, broken symlink, or mismatched
  symlink without explicit approval. Collision detection happens before every
  mutation.
- Configure locations from the checkout as it exists now, so fork-specific
  packages are included automatically.
