#!/usr/bin/env python3
"""Wire a project to a local HVE-Core clone: check, apply, or verify."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = "~/repos/forks/microsoft-hve-core"
SYMLINK_NAME = ".hve-core"
EXCLUDE_RULE = ".hve-core"
PROJECT_SKILLS_SUBPATH = ".github/skills"
COMPONENT_ROOTS = ("agents", "prompts", "instructions", "skills", "hooks")
SKILL_ONLY_EXCLUDES = ("installer",)
EXPERIMENTAL = "experimental"

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

LINE_COMMENT = re.compile(r"^\s*//")


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


def expected_project_skill_links(source: Path) -> dict[str, str]:
    """Map each linkable skill package to its symlink target, relative to the link."""
    links: dict[str, str] = {}
    for directory in subdirectories(source / ".github" / "skills"):
        if directory.name in SKILL_ONLY_EXCLUDES:
            continue
        if directory.name == EXPERIMENTAL:
            continue
        links[directory.name] = f"../../{SYMLINK_NAME}/{PROJECT_SKILLS_SUBPATH}/{directory.name}"
    return links


def classify_project_skill_links(project_root: Path, expected: dict[str, str]) -> dict[str, Any]:
    """Classify each expected package link as present, missing, or colliding."""
    root = project_root / PROJECT_SKILLS_SUBPATH
    present: list[str] = []
    missing: list[str] = []
    collisions: list[dict[str, str]] = []
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
        if actual == target and path.exists():
            present.append(name)
        else:
            collisions.append(
                {
                    "name": name,
                    "state": "broken-symlink" if not path.exists() else "symlink-mismatch",
                    "resolved": actual,
                }
            )
    return {
        "path": str(root),
        "expected": expected,
        "present": present,
        "missing": missing,
        "collisions": collisions,
    }


def guard_project_skill_links(info: dict[str, Any]) -> None:
    if not info["collisions"]:
        return
    detail = ", ".join(
        f"{PROJECT_SKILLS_SUBPATH}/{item['name']} is a {item['state']}"
        for item in info["collisions"]
    )
    raise SetupError(
        f"{detail}. Stop and ask the user how to handle the collision.",
        EXIT_COLLISION,
    )


def create_project_skill_links(project_root: Path, info: dict[str, Any]) -> list[str]:
    root = project_root / PROJECT_SKILLS_SUBPATH
    if info["missing"]:
        root.mkdir(parents=True, exist_ok=True)
    actions = []
    for name in info["missing"]:
        (root / name).symlink_to(info["expected"][name])
        actions.append(f"skills: linked {PROJECT_SKILLS_SUBPATH}/{name}")
    return actions


def load_json_tolerant(path: Path) -> Any:
    """Parse JSON, ignoring whole-line // comments. Raises on anything else."""
    text = path.read_text(encoding="utf-8")
    stripped = "\n".join("" if LINE_COMMENT.match(line) else line for line in text.splitlines())
    return json.loads(stripped)


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


def inspect_vscode_settings(
    project_root: Path, locations: dict[str, dict[str, bool]]
) -> dict[str, Any]:
    """Classify settings.json and compute the entries still missing."""
    path = project_root / ".vscode" / "settings.json"
    info: dict[str, Any] = {"path": str(path)}
    if not path.is_file():
        info["state"] = "absent"
        info["missing_entries"] = locations
        return info
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        info["state"] = "unparseable"
        info["missing_entries"] = locations
        info["reason"] = "not strict JSON (JSONC comments or trailing commas)"
        return info
    if not isinstance(data, dict):
        info["state"] = "unparseable"
        info["missing_entries"] = locations
        info["reason"] = "top-level value is not an object"
        return info

    missing: dict[str, dict[str, bool]] = {}
    for setting, entries in locations.items():
        existing = data.get(setting)
        if existing is None:
            missing[setting] = dict(entries)
            continue
        if not isinstance(existing, dict):
            info["state"] = "unparseable"
            info["missing_entries"] = locations
            info["reason"] = f"{setting} is not an object map from path to boolean"
            return info
        absent = {location: True for location in entries if location not in existing}
        if absent:
            missing[setting] = absent
    info["state"] = "strict-json"
    info["missing_entries"] = missing
    return info


def merge_vscode_settings(project_root: Path, missing: dict[str, dict[str, bool]]) -> list[str]:
    path = project_root / ".vscode" / "settings.json"
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {}
    actions = []
    for setting, entries in missing.items():
        existing = data.setdefault(setting, {})
        for location in entries:
            if location not in existing:
                existing[location] = True
                actions.append(f"settings: added {setting}[{location}]")
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return actions


def exclude_path(project_root: Path) -> Path:
    relative = run_git(["rev-parse", "--git-path", "info/exclude"], project_root)
    candidate = Path(relative)
    if not candidate.is_absolute():
        candidate = (project_root / candidate).resolve()
    return candidate


def expected_exclude_rules(expected_links: dict[str, str]) -> list[str]:
    return [EXCLUDE_RULE] + [
        f"/{PROJECT_SKILLS_SUBPATH}/{name}" for name in expected_links
    ]


def present_exclude_rules(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines()}


def append_exclude_rules(path: Path, rules: Sequence[str]) -> list[str]:
    present = present_exclude_rules(path)
    pending = [rule for rule in rules if rule not in present]
    if not pending:
        return []
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    prefix = "" if existing == "" or existing.endswith("\n") else "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(prefix + "".join(f"{rule}\n" for rule in pending))
    return [f"exclude: appended {rule} to {path}" for rule in pending]


def build_state(args: argparse.Namespace) -> dict[str, Any]:
    project_root = resolve_project_root(args.project_root)
    source = resolve_source(args.source)
    present_roots = check_source(source)
    symlink = classify_symlink(project_root, source)
    locations = compute_locations(source)
    expected_links = expected_project_skill_links(source)
    skill_links = classify_project_skill_links(project_root, expected_links)
    rules = expected_exclude_rules(expected_links)
    present_rules = present_exclude_rules(exclude := exclude_path(project_root))
    settings_path = Path(args.copilot_settings).expanduser()
    return {
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
        "project_skill_links": skill_links,
        "stale_cli_registrations": stale_cli_registrations(settings_path, source),
    }


def command_check(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    state = build_state(args)
    guard_symlink(state["symlink"])
    guard_project_skill_links(state["project_skill_links"])
    settings = inspect_vscode_settings(Path(state["project_root"]), state["vscode_locations"])
    state["vscode_settings"] = settings
    state["mode"] = "check"
    pending = (
        state["symlink"]["state"] == "absent"
        or bool(state["git_exclude"]["missing"])
        or bool(settings.get("missing_entries"))
        or bool(state["project_skill_links"]["missing"])
    )
    state["status"] = "pending" if pending else "already-applied"
    return state, EXIT_OK


def command_apply(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    state = build_state(args)
    guard_symlink(state["symlink"])
    guard_project_skill_links(state["project_skill_links"])
    project_root = Path(state["project_root"])
    source = Path(state["source"])
    actions: list[str] = []

    if state["symlink"]["state"] == "absent":
        (project_root / SYMLINK_NAME).symlink_to(source)
        actions.append(f"symlink: created {SYMLINK_NAME} -> {source}")
        state["symlink"] = classify_symlink(project_root, source)

    actions += create_project_skill_links(project_root, state["project_skill_links"])
    state["project_skill_links"] = classify_project_skill_links(
        project_root, state["project_skill_links"]["expected"]
    )

    actions += append_exclude_rules(
        Path(state["git_exclude"]["path"]), state["git_exclude"]["rules"]
    )
    state["git_exclude"]["missing"] = []

    settings = inspect_vscode_settings(project_root, state["vscode_locations"])
    state["vscode_settings"] = settings
    state["mode"] = "apply"
    state["failures"] = []

    if settings["state"] == "unparseable":
        state["actions"] = actions
        state["status"] = "needs-manual-settings-merge"
        state["next_steps"] = [
            f"Merge vscode_settings.missing_entries into {settings['path']} by hand, "
            "preserving comments and formatting. Each setting is an object mapping "
            "each path to boolean true."
        ]
        return state, EXIT_MANUAL_SETTINGS

    actions += merge_vscode_settings(project_root, settings["missing_entries"])
    state["actions"] = actions
    state["status"] = "applied"
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
    for setting, entries in state["vscode_locations"].items():
        actual = data.get(setting)
        if not isinstance(actual, dict):
            failures.append(f"{setting} is missing or not an object map from path to boolean")
            continue
        for location in entries:
            if actual.get(location) is not True:
                failures.append(f"{setting} missing enabled entry {location}")
        for location, enabled in actual.items():
            if enabled is not True:
                continue
            configured += 1
            if not (project_root / location).is_dir():
                failures.append(f"{setting} enabled path is not a directory: {location}")
            if location.startswith(f"{SYMLINK_NAME}/"):
                failures += forbidden_location(setting, location)
    return failures, configured


def verify_project_skills(state: dict[str, Any]) -> tuple[list[str], int]:
    project_root = Path(state["project_root"])
    info = state["project_skill_links"]
    failures = [
        f"skill package not linked: {PROJECT_SKILLS_SUBPATH}/{name}" for name in info["missing"]
    ]
    failures += [
        f"{PROJECT_SKILLS_SUBPATH}/{item['name']} is a {item['state']}"
        for item in info["collisions"]
    ]

    prefix = f"../../{SYMLINK_NAME}/"
    root = project_root / PROJECT_SKILLS_SUBPATH
    for entry in sorted(root.iterdir(), key=lambda p: p.name) if root.is_dir() else []:
        if not entry.is_symlink():
            continue
        target = os.readlink(entry)
        if not target.startswith(prefix):
            continue
        if EXPERIMENTAL in target.split("/"):
            failures.append(f"an experimental package is linked: {entry.name}")
        elif entry.name in SKILL_ONLY_EXCLUDES:
            failures.append(f"an excluded package is linked: {entry.name}")
        if not entry.exists():
            failures.append(f"linked skill package is broken: {entry.name}")
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
    skill_failures, linked = verify_project_skills(state)
    failures += skill_failures
    failures += [
        f"stale global CLI registration, run: copilot skill remove {directory}"
        for directory in state["stale_cli_registrations"]
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
    state["linked_skill_package_count"] = linked
    state["failures"] = failures
    state["status"] = "verified" if not failures else "verification-failed"
    return state, EXIT_OK if not failures else EXIT_VERIFY_FAILED


COMMANDS = {"check": command_check, "apply": command_apply, "verify": command_verify}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=sorted(COMMANDS))
    parser.add_argument("--project-root", default=None, help="target project path (default: cwd)")
    parser.add_argument(
        "--source", default=None, help=f"HVE-Core clone path (default: {DEFAULT_SOURCE})"
    )
    parser.add_argument("--copilot-settings", default="~/.copilot/settings.json")
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
