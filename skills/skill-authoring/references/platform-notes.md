# Platform Notes

Dated 2026-08-24. Volatile. Frontmatter fields, discovery rules, and CLI
subcommands change between releases. Recheck against `copilot skill --help` and
the vendor docs before relying on anything here.

## Frontmatter

Only `name` and `description` are required. The open specification also defines
the optional `license`, `compatibility`, `metadata`, and experimental
`allowed-tools` fields. Invocation controls and command presentation fields are
host extensions; unsupported hosts may ignore them.

Fields verified in the open specification or supported hosts:

| Field | Notes |
|---|---|
| `name` | Required. Kebab-case, matches the directory name. |
| `description` | Required. The entire retrieval surface. |
| `license` | Optional open-spec field. |
| `metadata` | Optional open-spec field for free-form host data. |
| `compatibility` | Optional open-spec field for runtime and tool prerequisites. |
| `user-invocable` | Copilot CLI, GitHub Copilot in VS Code, and Claude Code. Defaults to `true`; `false` hides direct user invocation while preserving automatic agent loading. |
| `disable-model-invocation` | Copilot CLI, GitHub Copilot in VS Code, and Claude Code. Defaults to `false`; `true` prevents automatic agent loading and requires direct user invocation. |
| `argument-hint` | Copilot CLI, GitHub Copilot in VS Code, and Claude Code. Slash-command style hint. |
| `allowed-tools` | Open-spec experimental and supported by Copilot CLI. Space-separated, e.g. `Bash(git:*) Bash(jq:*) Read`. Do not depend on it for security. |

Treat `allowed-tools` as advisory. Enforcement varies by host, and Copilot CLI
warns that pre-approving `shell` or `bash` "removes the confirmation step for
running terminal commands and can allow attacker-controlled skills or prompt
injections to execute arbitrary commands in your environment."

### Invocation controls

`user-invocable` and `disable-model-invocation` control separate paths:

| `user-invocable` | `disable-model-invocation` | Result |
|---|---|---|
| omitted or `true` | omitted or `false` | Agent and user can invoke |
| `false` | omitted or `false` | Agent only |
| omitted or `true` | `true` | User only |
| `false` | `true` | No normal invocation path; avoid |

They are host extensions, not fields in the open Agent Skills specification.
Do not use either as a security boundary: another host may ignore unknown
frontmatter, and a host that honors them still applies its own tool permission
and approval model.

GitHub Copilot in VS Code documents both fields. Copilot CLI 1.0.81-8 also
implements both: its bundled `customize-cloud-agent` and `github-pr-media`
skills use `user-invocable: false`, and its packaged changelog records support
for and full enforcement of `disable-model-invocation`. The current
CLI-specific authoring page describes automatic and `/name` invocation but
does not list either field, so verify behavior again when the CLI version
changes. Claude Code documents both as extensions to the open specification.

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
- Treat invocation controls as optional host behavior; make the skill safe if
  an unsupported host ignores them.
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
