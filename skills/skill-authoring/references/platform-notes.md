# Platform Notes

Dated 2026-08-19. Volatile. Frontmatter fields, discovery rules, and CLI
subcommands change between releases. Recheck against `copilot skill --help` and
the vendor docs before relying on anything here.

## Frontmatter

Only `name` and `description` are required, and only those two are portable
across every runtime. Everything else is host-specific and is ignored rather
than rejected by hosts that do not implement it.

Fields observed in use, tallied across installed skills on this machine:

| Field | Notes |
|---|---|
| `name` | Required. Kebab-case, matches the directory name. |
| `description` | Required. The entire retrieval surface. |
| `license` | Common in published skills. |
| `metadata` | Common in published skills; free-form host data. |
| `compatibility` | Used in this repo to declare runtime and tool prerequisites. |
| `user-invocable` | Copilot CLI. Set `false` on the two bundled built-in skills, which are agent-triggered only. |
| `argument-hint` | Rare. Slash-command style hint. |
| `allowed-tools` | Open-spec experimental. Space-separated, e.g. `Bash(git:*) Bash(jq:*) Read`. Not observed in any installed `SKILL.md` frontmatter here. Do not depend on it for security. |

Treat `allowed-tools` as advisory. Enforcement varies by host, and Copilot CLI
warns that pre-approving `shell` or `bash` "removes the confirmation step for
running terminal commands and can allow attacker-controlled skills or prompt
injections to execute arbitrary commands in your environment."

## Copilot CLI

Discovery sources, from `copilot skill --help`:

| Source | Location |
|---|---|
| Project | `.github/skills/`, `.agents/skills/`, or `.claude/skills/` |
| Personal | `~/.copilot/skills/` or `~/.agents/skills/` |
| Plugin | Installed plugins that bundle skills |
| Custom | Directories added with `copilot skill add <directory>` |

Multi-file skills need no manifest. Per the docs, "Copilot automatically
discovers all of the files in the skill's directory and makes them available
alongside the skill's instructions."

Subcommands, verified on 1.0.81-4:

```bash
copilot skill list [--json]
copilot skill add <file | url | directory> [--project]
copilot skill remove <name-or-directory>
```

`add` resolves by argument type: a directory is registered as a custom skill
directory, while a file or HTTPS URL is materialized into
`~/.copilot/skills/<name>/SKILL.md`, or into the project's `.github/skills`
with `--project`. `add` on an already-registered directory is idempotent and
leaves settings byte-identical.

In-session equivalents are `/skills list`, `/skills add`, `/skills remove`, and
`/skills reload`. Registering a directory from outside the session requires
`/skills reload` before the running session sees it.

### Two traps in the CLI surface

**A registered directory is not a skill directory.** `copilot skill add` takes
the parent directory that *contains* skill directories. Registering
`<pkg>/.github/skills` exposes every package beneath it, including any you meant
to exclude.

**`copilot skill list --json` does not report registered directories.** It
reports resolved skills, one object per skill, with `path` pointing at the leaf
skill directory. The authoritative registry is the `skillDirectories` array in
`~/.copilot/settings.json`. To confirm a registered directory resolved
anything, match listed `path` values by prefix against it.

Shape of a `list --json` entry:

```json
{
  "name": "rpi-plan",
  "description": "...",
  "source": "custom",
  "path": "/abs/path/.github/skills/rpi/rpi-plan",
  "enabled": true
}
```

`source` is one of `builtin`, `personal-copilot`, `personal-agents`, `project`,
`plugin`, or `custom`.

## Claude Code

Supports the base format plus extensions that are **not** in the open spec and
do not work elsewhere. The notable one is dynamic context injection: a line of
the form

```markdown
!`git diff HEAD`
```

is executed at skill-load time and replaced with its output before the model
sees the skill body. There is no Copilot CLI equivalent. A skill that depends
on it is not portable; if the skill must run in both, have the agent run the
command as a normal step instead.

## Writing for portability

- Keep `name` and `description` doing all the load-bearing work.
- Reference bundled files by path relative to the skill root, never by absolute
  path or host-specific skills directory.
- **Dependency rule.** A script must be self-contained or declare its
  dependencies explicitly, and should prefer the standard library. A dependency
  absent on a clean machine turns the whole skill into a failure. Verified
  example: on this machine neither Python's stdlib nor the Node install can
  parse JSONC, and PyYAML is not present, so a skill assuming either would
  break. `scripts/validate_skill.py` parses frontmatter with a deliberately
  minimal scalar reader for exactly this reason.
- Do not assume a host enforces `allowed-tools`.

## External validators

`skills-ref` on npm (0.1.5 as of this date, "Reference library for Agent
Skills") offers `skills-ref validate <dir>` against the open spec. It is early,
was not installed or exercised here, and its provenance was not confirmed.
Treat it as optional. The bundled `scripts/validate_skill.py` covers this
repo's invariants with no dependencies.
