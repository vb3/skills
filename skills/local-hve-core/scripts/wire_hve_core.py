#!/usr/bin/env python3
"""Wire a project to a local HVE-Core clone: check, apply, unwire, or verify."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = "~/repos/forks/microsoft-hve-core"
SYMLINK_NAME = ".hve-core"
EXCLUDE_RULE = ".hve-core"
EXCLUDE_BLOCK_START = "# local-hve-core:start"
EXCLUDE_BLOCK_END = "# local-hve-core:end"
PROJECT_SKILLS_SUBPATH = ".github/skills"
PROJECT_AGENTS_SUBPATH = ".github/agents"
COMPONENT_ROOTS = ("agents", "prompts", "instructions", "skills", "hooks")
SKILL_ONLY_EXCLUDES = ("installer",)
EXPERIMENTAL = "experimental"

# Copilot CLI auto-discovers these two roots in the project and recurses into
# package directories. Everything else is VS Code only.
CLI_LINK_SUBPATHS = {
    "skills": PROJECT_SKILLS_SUBPATH,
    "agents": PROJECT_AGENTS_SUBPATH,
}
CLI_LINK_STATE_KEYS = {
    "skills": "project_skill_links",
    "agents": "project_agent_links",
}
DEFAULT_COPILOT_AGENTS = "~/.copilot/agents"

# settings.json states the script may rewrite. A JSONC file is readable but not
# writable here, because json.dumps would drop its comments.
MERGEABLE_SETTINGS_STATES = ("absent", "strict-json")

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_SOURCE_MISSING = 2
EXIT_COLLISION = 3
EXIT_MANUAL_SETTINGS = 4
EXIT_VERIFY_FAILED = 5

LOCATION_SETTINGS = {
    "agents": "chat.agentFilesLocations",
    "prompts": "chat.promptFilesLocations",
    "instructions": "chat.instructionsFilesLocations",
    "skills": "chat.agentSkillsLocations",
    "hooks": "chat.hookFilesLocations",
}

class SetupError(Exception):
    """A gate failure that maps to a specific exit code."""

    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code


def run_git(arguments: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SetupError(
            f"git {' '.join(arguments)} failed: {completed.stderr.strip()}",
            EXIT_USAGE,
        )
    return completed.stdout.strip()


def resolve_project_root(candidate: str | None) -> Path:
    start = Path(candidate).expanduser() if candidate else Path.cwd()
    if not start.is_dir():
        raise SetupError(f"project root is not a directory: {start}", EXIT_USAGE)
    return Path(run_git(["rev-parse", "--show-toplevel"], start)).resolve()


def resolve_source(candidate: str | None) -> Path:
    raw = candidate or DEFAULT_SOURCE
    source = Path(raw).expanduser()
    if not source.is_absolute():
        source = (Path.cwd() / source).resolve()
    return source


def check_source(source: Path) -> list[str]:
    """Return the component roots that exist under the source clone."""
    if not source.is_dir():
        raise SetupError(
            f"source clone not found: {source}. Offer to clone "
            "https://github.com/microsoft/hve-core.git into that path.",
            EXIT_SOURCE_MISSING,
        )
    present = [name for name in COMPONENT_ROOTS if (source / ".github" / name).is_dir()]
    if not present:
        raise SetupError(
            f"source clone has no .github component roots: {source}",
            EXIT_SOURCE_MISSING,
        )
    return present


def classify_symlink(project_root: Path, source: Path) -> dict[str, Any]:
    path = project_root / SYMLINK_NAME
    info: dict[str, Any] = {"path": str(path), "requested": str(source)}
    if not path.is_symlink() and not path.exists():
        info["state"] = "absent"
        return info
    if path.is_symlink():
        target = os.readlink(path)
        resolved = Path(target)
        if not resolved.is_absolute():
            resolved = (path.parent / resolved).resolve()
        info["resolved"] = str(resolved)
        if resolved == source and path.exists():
            info["state"] = "reuse"
            return info
        info["state"] = "broken-symlink" if not path.exists() else "symlink-mismatch"
        return info
    info["state"] = "directory" if path.is_dir() else "file"
    return info


def guard_symlink(info: dict[str, Any]) -> None:
    if info["state"] in ("absent", "reuse"):
        return
    detail = f"{SYMLINK_NAME} is a {info['state']}"
    if "resolved" in info:
        detail += f" resolving to {info['resolved']}, not {info['requested']}"
    raise SetupError(
        f"{detail}. Stop and ask the user how to handle the collision.",
        EXIT_COLLISION,
    )


def subdirectories(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted((p for p in root.iterdir() if p.is_dir()), key=lambda p: p.name)


def relative_location(path: Path, source: Path) -> str:
    return f"{SYMLINK_NAME}/{path.relative_to(source).as_posix()}"


def compute_locations(source: Path) -> dict[str, dict[str, bool]]:
    """Build the chat.*Locations map from the clone as it exists now."""
    locations: dict[str, dict[str, bool]] = {}
    for component, setting in LOCATION_SETTINGS.items():
        root = source / ".github" / component
        entries: dict[str, bool] = {}
        for directory in subdirectories(root):
            if directory.name == EXPERIMENTAL:
                continue
            if component == "skills" and directory.name in SKILL_ONLY_EXCLUDES:
                continue
            entries[relative_location(directory, source)] = True
            if component == "agents":
                subagents = directory / "subagents"
                if subagents.is_dir():
                    entries[relative_location(subagents, source)] = True
        if entries:
            locations[setting] = entries
    return locations


def expected_project_links(source: Path, component: str) -> dict[str, str]:
    """Map each linkable package or root agent file to its relative symlink target."""
    subpath = CLI_LINK_SUBPATHS[component]
    links: dict[str, str] = {}
    root = source / ".github" / component
    for directory in subdirectories(root):
        if component == "skills" and directory.name in SKILL_ONLY_EXCLUDES:
            continue
        if directory.name == EXPERIMENTAL:
            continue
        links[directory.name] = f"../../{SYMLINK_NAME}/{subpath}/{directory.name}"
    if component == "agents" and root.is_dir():
        for agent_file in sorted(root.glob("*.agent.md"), key=lambda path: path.name):
            links[agent_file.name] = (
                f"../../{SYMLINK_NAME}/{subpath}/{agent_file.name}"
            )
    return links


def classify_project_links(
    project_root: Path, expected: dict[str, str], component: str
) -> dict[str, Any]:
    """Classify expected links and obsolete symlinks previously managed here."""
    subpath = CLI_LINK_SUBPATHS[component]
    root = project_root / subpath
    present: list[str] = []
    missing: list[str] = []
    collisions: list[dict[str, str]] = []
    stale: list[dict[str, str]] = []
    for name, target in expected.items():
        path = root / name
        if not path.is_symlink() and not path.exists():
            missing.append(name)
            continue
        if not path.is_symlink():
            collisions.append(
                {"name": name, "state": "directory" if path.is_dir() else "file"}
            )
            continue
        actual = os.readlink(path)
        if actual == target:
            present.append(name)
        else:
            collisions.append(
                {
                    "name": name,
                    "state": "broken-symlink" if not path.exists() else "symlink-mismatch",
                    "resolved": actual,
                }
            )
    prefix = f"../../{SYMLINK_NAME}/{subpath}/"
    if root.is_dir():
        for entry in sorted(root.iterdir(), key=lambda path: path.name):
            if entry.name in expected or not entry.is_symlink():
                continue
            target = os.readlink(entry)
            if target.startswith(prefix):
                stale.append({"name": entry.name, "target": target})
    return {
        "component": component,
        "subpath": subpath,
        "path": str(root),
        "expected": expected,
        "present": present,
        "missing": missing,
        "collisions": collisions,
        "stale": stale,
    }


def guard_project_links(info: dict[str, Any]) -> None:
    if not info["collisions"]:
        return
    detail = ", ".join(
        f"{info['subpath']}/{item['name']} is a {item['state']}"
        for item in info["collisions"]
    )
    raise SetupError(
        f"{detail}. Stop and ask the user how to handle the collision.",
        EXIT_COLLISION,
    )


def create_project_links(project_root: Path, info: dict[str, Any]) -> list[str]:
    root = project_root / info["subpath"]
    if info["missing"]:
        root.mkdir(parents=True, exist_ok=True)
    actions = []
    for name in info["missing"]:
        (root / name).symlink_to(info["expected"][name])
        actions.append(f"{info['component']}: linked {info['subpath']}/{name}")
    return actions


def remove_project_links(project_root: Path, info: dict[str, Any]) -> list[str]:
    root = project_root / info["subpath"]
    actions: list[str] = []
    for item in info["stale"]:
        path = root / item["name"]
        path.unlink()
        actions.append(f"{info['component']}: removed stale {info['subpath']}/{item['name']}")
    return actions


def strip_jsonc_comments(text: str) -> str:
    """Remove line and block comments without changing quoted JSON strings."""
    result: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if text.startswith("//", index):
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue
        if text.startswith("/*", index):
            index += 2
            while index < len(text) and not text.startswith("*/", index):
                if text[index] in "\r\n":
                    result.append(text[index])
                index += 1
            index += 2 if index < len(text) else 0
            continue
        result.append(char)
        index += 1
    return "".join(result)


def strip_jsonc_trailing_commas(text: str) -> str:
    """Remove commas immediately before closing object or array delimiters."""
    result: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if char == ",":
            lookahead = index + 1
            while lookahead < len(text) and text[lookahead].isspace():
                lookahead += 1
            if lookahead < len(text) and text[lookahead] in "}]":
                index += 1
                continue
        result.append(char)
        index += 1
    return "".join(result)


def load_json_tolerant(path: Path) -> Any:
    """Parse JSONC comments and trailing commas. Raises on invalid content."""
    text = path.read_text(encoding="utf-8")
    return json.loads(strip_jsonc_trailing_commas(strip_jsonc_comments(text)))


def read_registered_dirs(settings_path: Path) -> list[str]:
    """Legacy Copilot CLI registrations this skill used to create."""
    if not settings_path.is_file():
        return []
    try:
        data = load_json_tolerant(settings_path)
    except json.JSONDecodeError:
        return []
    value = data.get("skillDirectories", []) if isinstance(data, dict) else []
    return [str(item) for item in value] if isinstance(value, list) else []


def stale_cli_registrations(settings_path: Path, source: Path) -> list[str]:
    """Global registrations pointing into the clone, left by older runs."""
    skills_root = source / ".github" / "skills"
    return [
        directory
        for directory in read_registered_dirs(settings_path)
        if Path(directory) == skills_root or Path(directory).parent == skills_root
    ]


def stale_global_agent_links(agents_dir: Path, source: Path) -> list[str]:
    """Machine-wide ~/.copilot/agents links into the clone: loads them everywhere."""
    if not agents_dir.is_dir():
        return []
    agents_root = os.path.realpath(source / ".github" / "agents")
    stale: list[str] = []
    for entry in sorted(agents_dir.iterdir(), key=lambda p: p.name):
        if not entry.is_symlink():
            continue
        resolved = os.path.realpath(entry)
        if resolved == agents_root or resolved.startswith(agents_root + os.sep):
            stale.append(str(entry))
    return stale


def inspect_vscode_settings(
    project_root: Path, locations: dict[str, dict[str, bool]]
) -> dict[str, Any]:
    """Classify settings.json and compute the entries still missing.

    A JSONC file is parsed tolerantly so `missing_entries` names only what is
    genuinely absent. It is still never rewritten: `json.dumps` would drop the
    comments, so those merges stay manual.
    """
    path = project_root / ".vscode" / "settings.json"
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", ".vscode/settings.json"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
    ).returncode == 0
    info: dict[str, Any] = {"path": str(path), "tracked": tracked}
    if not path.is_file():
        info["state"] = "absent"
        info["missing_entries"] = locations
        info["stale_entries"] = {}
        return info
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        state = "strict-json"
    except json.JSONDecodeError:
        try:
            data = load_json_tolerant(path)
            state = "jsonc"
        except json.JSONDecodeError:
            info["state"] = "unparseable"
            info["missing_entries"] = locations
            info["stale_entries"] = {}
            info["reason"] = "not strict JSON (JSONC comments or trailing commas)"
            return info
    if not isinstance(data, dict):
        info["state"] = "unparseable"
        info["missing_entries"] = locations
        info["stale_entries"] = {}
        info["reason"] = "top-level value is not an object"
        return info

    missing: dict[str, dict[str, bool]] = {}
    stale: dict[str, list[str]] = {}
    for setting in LOCATION_SETTINGS.values():
        entries = locations.get(setting, {})
        existing = data.get(setting)
        if existing is None:
            if entries:
                missing[setting] = dict(entries)
            continue
        if not isinstance(existing, dict):
            info["state"] = "unparseable"
            info["missing_entries"] = locations
            info["stale_entries"] = {}
            info["reason"] = f"{setting} is not an object map from path to boolean"
            return info
        absent = {
            location: True
            for location in entries
            if existing.get(location) is not True
        }
        if absent:
            missing[setting] = absent
        obsolete = [
            location
            for location in existing
            if location.startswith(f"{SYMLINK_NAME}/.github/") and location not in entries
        ]
        if obsolete:
            stale[setting] = obsolete
    info["state"] = state
    info["missing_entries"] = missing
    info["stale_entries"] = stale
    if state == "jsonc":
        info["reason"] = "JSONC comments; merge by hand to preserve them"
    return info


def reconcile_vscode_settings(
    project_root: Path,
    missing: dict[str, dict[str, bool]],
    stale: dict[str, list[str]],
) -> list[str]:
    path = project_root / ".vscode" / "settings.json"
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
    actions: list[str] = []
    for setting, locations in stale.items():
        existing = data[setting]
        for location in locations:
            del existing[location]
            actions.append(f"settings: removed {setting}[{location}]")
        if not existing:
            del data[setting]
    for setting, entries in missing.items():
        existing = data.setdefault(setting, {})
        for location in entries:
            if existing.get(location) is not True:
                existing[location] = True
                actions.append(f"settings: enabled {setting}[{location}]")
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return actions


def exclude_path(project_root: Path) -> Path:
    relative = run_git(["rev-parse", "--git-path", "info/exclude"], project_root)
    candidate = Path(relative)
    if not candidate.is_absolute():
        candidate = (project_root / candidate).resolve()
    return candidate


def expected_exclude_rules(links_by_component: dict[str, dict[str, str]]) -> list[str]:
    rules = [EXCLUDE_RULE]
    for component, expected in links_by_component.items():
        subpath = CLI_LINK_SUBPATHS[component]
        rules += [f"/{subpath}/{name}" for name in expected]
    return rules


def present_exclude_rules(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines()}


def read_exclude_block(path: Path) -> tuple[str, str, list[str], str]:
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    lines = existing.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line.strip() == EXCLUDE_BLOCK_START]
    ends = [index for index, line in enumerate(lines) if line.strip() == EXCLUDE_BLOCK_END]
    if len(starts) != len(ends) or len(starts) > 1 or (
        starts and starts[0] >= ends[0]
    ):
        raise SetupError(
            f"managed exclude block is malformed in {path}",
            EXIT_COLLISION,
        )

    if starts:
        start, end = starts[0], ends[0]
        prefix = "".join(lines[:start])
        suffix = "".join(lines[end + 1 :])
        owned = [line.strip() for line in lines[start + 1 : end] if line.strip()]
    else:
        prefix = existing
        suffix = ""
        owned = []
    return prefix, suffix, owned, existing


def reconcile_exclude_rules(path: Path, desired: Sequence[str]) -> list[str]:
    """Own only a delimited block, leaving identical pre-existing rules untouched."""
    prefix, suffix, owned, existing = read_exclude_block(path)

    unmanaged = {
        line.strip()
        for line in (prefix + suffix).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    wanted = [rule for rule in desired if rule not in unmanaged]
    block = ""
    if wanted:
        if prefix and not prefix.endswith("\n"):
            prefix += "\n"
        block = (
            f"{EXCLUDE_BLOCK_START}\n"
            + "".join(f"{rule}\n" for rule in wanted)
            + f"{EXCLUDE_BLOCK_END}\n"
        )
    updated = prefix + block + suffix
    if updated != existing:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated, encoding="utf-8")

    actions = [f"exclude: removed {rule} from {path}" for rule in owned if rule not in wanted]
    actions += [f"exclude: added {rule} to {path}" for rule in wanted if rule not in owned]
    return actions


def build_state(args: argparse.Namespace) -> dict[str, Any]:
    project_root = resolve_project_root(args.project_root)
    source = resolve_source(args.source)
    present_roots = check_source(source)
    symlink = classify_symlink(project_root, source)
    locations = compute_locations(source)
    expected_links = {
        component: expected_project_links(source, component) for component in CLI_LINK_SUBPATHS
    }
    rules = expected_exclude_rules(expected_links)
    read_exclude_block(exclude := exclude_path(project_root))
    present_rules = present_exclude_rules(exclude)
    settings_path = Path(args.copilot_settings).expanduser()
    agents_dir = Path(args.copilot_agents).expanduser()
    state = {
        "project_root": str(project_root),
        "source": str(source),
        "component_roots_present": present_roots,
        "symlink": symlink,
        "vscode_locations": locations,
        "git_exclude": {
            "path": str(exclude),
            "rules": rules,
            "missing": [rule for rule in rules if rule not in present_rules],
        },
        "stale_cli_registrations": stale_cli_registrations(settings_path, source),
        "stale_global_agent_links": stale_global_agent_links(agents_dir, source),
    }
    for component, key in CLI_LINK_STATE_KEYS.items():
        state[key] = classify_project_links(project_root, expected_links[component], component)
    return state


def command_check(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    state = build_state(args)
    guard_symlink(state["symlink"])
    for key in CLI_LINK_STATE_KEYS.values():
        guard_project_links(state[key])
    settings = inspect_vscode_settings(Path(state["project_root"]), state["vscode_locations"])
    state["vscode_settings"] = settings
    state["mode"] = "check"
    pending = (
        state["symlink"]["state"] == "absent"
        or bool(state["git_exclude"]["missing"])
        or bool(settings.get("missing_entries"))
        or bool(settings.get("stale_entries"))
        or any(state[key]["missing"] for key in CLI_LINK_STATE_KEYS.values())
        or any(state[key]["stale"] for key in CLI_LINK_STATE_KEYS.values())
    )
    state["status"] = "pending" if pending else "already-applied"
    return state, EXIT_OK


def command_apply(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    state = build_state(args)
    guard_symlink(state["symlink"])
    for key in CLI_LINK_STATE_KEYS.values():
        guard_project_links(state[key])
    project_root = Path(state["project_root"])
    source = Path(state["source"])
    actions: list[str] = []
    settings = inspect_vscode_settings(project_root, state["vscode_locations"])
    state["vscode_settings"] = settings
    state["mode"] = "apply"
    state["failures"] = []
    settings_changes = bool(settings["missing_entries"] or settings["stale_entries"])

    if settings["state"] not in MERGEABLE_SETTINGS_STATES and settings_changes:
        state["actions"] = []
        state["status"] = "needs-manual-settings-merge"
        state["next_steps"] = [
            f"Merge vscode_settings.missing_entries and remove "
            f"vscode_settings.stale_entries in {settings['path']} by hand, "
            "preserving comments and formatting."
        ]
        return state, EXIT_MANUAL_SETTINGS
    if settings["tracked"] and settings_changes and not args.allow_tracked_settings:
        state["actions"] = []
        state["status"] = "needs-tracked-settings-approval"
        state["next_steps"] = [
            f"Re-run with --allow-tracked-settings to update {settings['path']}, "
            "or merge the reported entries by hand."
        ]
        return state, EXIT_MANUAL_SETTINGS

    if state["symlink"]["state"] == "absent":
        (project_root / SYMLINK_NAME).symlink_to(source)
        actions.append(f"symlink: created {SYMLINK_NAME} -> {source}")
        state["symlink"] = classify_symlink(project_root, source)

    for component, key in CLI_LINK_STATE_KEYS.items():
        actions += remove_project_links(project_root, state[key])
        actions += create_project_links(project_root, state[key])
        state[key] = classify_project_links(project_root, state[key]["expected"], component)

    actions += reconcile_exclude_rules(
        Path(state["git_exclude"]["path"]), state["git_exclude"]["rules"]
    )
    state["git_exclude"]["missing"] = []

    if settings["state"] in MERGEABLE_SETTINGS_STATES and settings_changes:
        actions += reconcile_vscode_settings(
            project_root,
            settings["missing_entries"],
            settings["stale_entries"],
        )
    state["actions"] = actions
    state["status"] = "applied"
    return state, EXIT_OK


def command_unwire(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    project_root = resolve_project_root(args.project_root)
    source = resolve_source(args.source)
    symlink = classify_symlink(project_root, source)
    removable_symlink = symlink["state"] in ("absent", "reuse") or (
        symlink["state"] == "broken-symlink"
        and symlink.get("resolved") == str(source)
    )
    if not removable_symlink:
        guard_symlink(symlink)

    links = {
        component: classify_project_links(project_root, {}, component)
        for component in CLI_LINK_SUBPATHS
    }
    exclude = exclude_path(project_root)
    read_exclude_block(exclude)
    settings = inspect_vscode_settings(project_root, {})
    state: dict[str, Any] = {
        "mode": "unwire",
        "project_root": str(project_root),
        "source": str(source),
        "symlink": symlink,
        "vscode_settings": settings,
        "actions": [],
    }
    for component, key in CLI_LINK_STATE_KEYS.items():
        state[key] = links[component]

    settings_changes = bool(settings["stale_entries"])
    if settings["state"] == "unparseable" or (
        settings["state"] == "jsonc" and settings_changes
    ):
        state["status"] = "needs-manual-settings-merge"
        state["next_steps"] = [
            f"Remove vscode_settings.stale_entries from {settings['path']} by hand, "
            "preserving comments and formatting."
        ]
        return state, EXIT_MANUAL_SETTINGS
    if settings["tracked"] and settings_changes and not args.allow_tracked_settings:
        state["status"] = "needs-tracked-settings-approval"
        state["next_steps"] = [
            f"Re-run with --allow-tracked-settings to update {settings['path']}, "
            "or remove the reported entries by hand."
        ]
        return state, EXIT_MANUAL_SETTINGS

    actions: list[str] = []
    if settings["state"] == "strict-json" and settings_changes:
        actions += reconcile_vscode_settings(project_root, {}, settings["stale_entries"])

    for info in links.values():
        actions += remove_project_links(project_root, info)
    actions += reconcile_exclude_rules(exclude, [])

    symlink_path = project_root / SYMLINK_NAME
    if symlink_path.is_symlink():
        symlink_path.unlink()
        actions.append(f"symlink: removed {SYMLINK_NAME}")

    state["actions"] = actions
    state["status"] = "unwired"
    return state, EXIT_OK


def forbidden_location(setting: str, location: str) -> list[str]:
    parts = location.split("/")
    if EXPERIMENTAL in parts:
        return [f"{setting} includes an experimental path: {location}"]
    if setting != LOCATION_SETTINGS["skills"]:
        return []
    if parts[-1] == "skills":
        return [f"{setting} includes the skills root: {location}"]
    if parts[-1] in SKILL_ONLY_EXCLUDES:
        return [f"{setting} includes an excluded package: {location}"]
    return []


def check_ignore_attribution(project_root: Path, expected: Path, target: str) -> list[str]:
    completed = subprocess.run(
        ["git", "check-ignore", "-v", "--no-index", target],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return [f"git check-ignore did not match {target}"]
    source_file = completed.stdout.split(":", 1)[0].strip()
    resolved = Path(source_file)
    if not resolved.is_absolute():
        resolved = (project_root / resolved).resolve()
    if resolved != expected:
        return [f"{target} rule attributed to {resolved}, expected {expected}"]
    return []


def verify_vscode(state: dict[str, Any]) -> tuple[list[str], int]:
    project_root = Path(state["project_root"])
    path = project_root / ".vscode" / "settings.json"
    failures: list[str] = []
    if not path.is_file():
        return [f"missing {path}"], 0
    try:
        data = load_json_tolerant(path)
    except json.JSONDecodeError:
        return [f"cannot parse {path}"], 0
    if not isinstance(data, dict):
        return [f"top-level value in {path} is not an object"], 0

    configured = 0
    for setting in LOCATION_SETTINGS.values():
        entries = state["vscode_locations"].get(setting, {})
        actual = data.get(setting)
        if entries and not isinstance(actual, dict):
            failures.append(f"{setting} is missing or not an object map from path to boolean")
            continue
        if not isinstance(actual, dict):
            continue
        for location in entries:
            if actual.get(location) is not True:
                failures.append(f"{setting} missing enabled entry {location}")
        for location, enabled in actual.items():
            if (
                location.startswith(f"{SYMLINK_NAME}/.github/")
                and location not in entries
            ):
                failures.append(f"{setting} has stale HVE-Core entry {location}")
            if enabled is not True:
                continue
            configured += 1
            if not (project_root / location).is_dir():
                failures.append(f"{setting} enabled path is not a directory: {location}")
            if location.startswith(f"{SYMLINK_NAME}/"):
                failures += forbidden_location(setting, location)
    return failures, configured


def verify_project_links(state: dict[str, Any], key: str) -> tuple[list[str], int]:
    project_root = Path(state["project_root"])
    info = state[key]
    component = info["component"]
    subpath = info["subpath"]
    failures = [f"{component} package not linked: {subpath}/{name}" for name in info["missing"]]
    failures += [
        f"{subpath}/{item['name']} is a {item['state']}" for item in info["collisions"]
    ]
    failures += [
        f"stale {component} link: {subpath}/{item['name']}" for item in info["stale"]
    ]

    prefix = f"../../{SYMLINK_NAME}/"
    root = project_root / subpath
    for entry in sorted(root.iterdir(), key=lambda p: p.name) if root.is_dir() else []:
        if not entry.is_symlink():
            continue
        target = os.readlink(entry)
        if not target.startswith(prefix):
            continue
        if EXPERIMENTAL in target.split("/"):
            failures.append(f"an experimental package is linked: {entry.name}")
        elif component == "skills" and entry.name in SKILL_ONLY_EXCLUDES:
            failures.append(f"an excluded package is linked: {entry.name}")
        if not entry.exists():
            failures.append(f"linked {component} package is broken: {entry.name}")
    return failures, len(info["present"])


def command_verify(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    state = build_state(args)
    failures: list[str] = []

    if state["symlink"]["state"] != "reuse":
        failures.append(
            f"{SYMLINK_NAME} does not resolve to {state['source']} "
            f"(state: {state['symlink']['state']})"
        )

    vscode_failures, configured = verify_vscode(state)
    failures += vscode_failures
    skill_failures, linked_skills = verify_project_links(state, CLI_LINK_STATE_KEYS["skills"])
    failures += skill_failures
    agent_failures, linked_agents = verify_project_links(state, CLI_LINK_STATE_KEYS["agents"])
    failures += agent_failures
    failures += [
        f"stale global CLI registration, run: copilot skill remove {directory}"
        for directory in state["stale_cli_registrations"]
    ]
    failures += [
        f"agent linked machine-wide instead of per project, run: rm {path}"
        for path in state["stale_global_agent_links"]
    ]

    missing_rules = state["git_exclude"]["missing"]
    failures += [
        f"{rule} rule absent from {state['git_exclude']['path']}" for rule in missing_rules
    ]
    for rule in state["git_exclude"]["rules"]:
        if rule in missing_rules:
            continue
        failures += check_ignore_attribution(
            Path(state["project_root"]),
            Path(state["git_exclude"]["path"]),
            rule.lstrip("/"),
        )

    state["mode"] = "verify"
    state["configured_location_count"] = configured
    state["linked_skill_package_count"] = linked_skills
    state["linked_agent_package_count"] = linked_agents
    state["failures"] = failures
    state["status"] = "verified" if not failures else "verification-failed"
    return state, EXIT_OK if not failures else EXIT_VERIFY_FAILED


COMMANDS = {
    "check": command_check,
    "apply": command_apply,
    "unwire": command_unwire,
    "verify": command_verify,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=sorted(COMMANDS))
    parser.add_argument("--project-root", default=None, help="target project path (default: cwd)")
    parser.add_argument(
        "--source", default=None, help=f"HVE-Core clone path (default: {DEFAULT_SOURCE})"
    )
    parser.add_argument("--copilot-settings", default="~/.copilot/settings.json")
    parser.add_argument("--copilot-agents", default=DEFAULT_COPILOT_AGENTS)
    parser.add_argument(
        "--allow-tracked-settings",
        action="store_true",
        help="allow apply or unwire to edit tracked .vscode/settings.json",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        state, code = COMMANDS[args.mode](args)
    except SetupError as error:
        json.dump({"mode": args.mode, "status": "blocked", "error": str(error)}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return error.code
    json.dump(state, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
