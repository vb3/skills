#!/usr/bin/env python3
"""Validate the structural invariants of a skill directory.

Checks only what is mechanically decidable. Judgment about whether a skill is
well written stays with the agent.

Exit codes:
    0  all checks passed
    1  usage error, or the path is not a skill directory
    2  structural defects found
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RELATIVE_LINK_PATTERN = re.compile(r"\[[^\]]*\]\((?!https?:|mailto:|#)([^)]+)\)")
SCALAR_PATTERN = re.compile(r"^(?P<key>[A-Za-z][A-Za-z0-9_-]*):\s*(?P<value>.*)$")
EVAL_KEYS = {"id", "prompt", "expected_output", "files", "expectations"}


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    """Extract top-level scalar frontmatter keys.

    Deliberately not a YAML parser: PyYAML is not guaranteed present, and the
    structural checks here only need top-level scalars. Nested structures are
    ignored rather than rejected.
    """
    findings: list[str] = []
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        findings.append("SKILL.md does not open with a --- frontmatter block")
        return {}, findings

    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        findings.append("frontmatter block is never closed with ---")
        return {}, findings

    fields: dict[str, str] = {}
    pending_key: str | None = None
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1].isspace():
            if pending_key is not None:
                fields[pending_key] = f"{fields[pending_key]} {line.strip()}".strip()
            continue
        match = SCALAR_PATTERN.match(line)
        if not match:
            continue
        key = match.group("key")
        value = match.group("value").strip()
        if value in {">-", ">", "|", "|-", ""}:
            fields[key] = ""
            pending_key = key
        else:
            fields[key] = value.strip("'\"")
            pending_key = None
    return fields, findings


def check_frontmatter(skill_dir: Path, fields: dict[str, str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    name = fields.get("name", "").strip()
    if not name:
        findings.append({"check": "frontmatter.name", "message": "name is missing or empty"})
    else:
        if not NAME_PATTERN.match(name):
            findings.append({
                "check": "frontmatter.name",
                "message": f"name {name!r} is not kebab-case without consecutive hyphens",
            })
        if name != skill_dir.name:
            findings.append({
                "check": "frontmatter.name",
                "message": f"name {name!r} does not match directory {skill_dir.name!r}",
            })
    if not fields.get("description", "").strip():
        findings.append({
            "check": "frontmatter.description",
            "message": "description is missing or empty; it is the entire retrieval surface",
        })
    return findings


def check_links(skill_dir: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for markdown in sorted(skill_dir.rglob("*.md")):
        for target in RELATIVE_LINK_PATTERN.findall(markdown.read_text(encoding="utf-8")):
            resolved = (markdown.parent / target.split("#", 1)[0]).resolve()
            if not resolved.exists():
                findings.append({
                    "check": "links",
                    "message": f"{markdown.relative_to(skill_dir)} links to missing {target}",
                })
    return findings


def check_evals(skill_dir: Path, name: str) -> list[dict[str, str]]:
    path = skill_dir / "evals" / "evals.json"
    if not path.exists():
        return [{"check": "evals", "message": "evals/evals.json is missing"}]

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [{"check": "evals", "message": f"evals/evals.json does not parse: {error}"}]

    findings: list[dict[str, str]] = []
    if not isinstance(document, dict):
        return [{"check": "evals", "message": "evals/evals.json must be a JSON object"}]
    if name and document.get("skill_name") != name:
        findings.append({
            "check": "evals",
            "message": f"skill_name {document.get('skill_name')!r} does not match {name!r}",
        })

    cases = document.get("evals")
    if not isinstance(cases, list) or not cases:
        return findings + [{"check": "evals", "message": "evals must be a non-empty array"}]

    seen: set[Any] = set()
    for index, case in enumerate(cases):
        label = f"eval[{index}]"
        if not isinstance(case, dict):
            findings.append({"check": "evals", "message": f"{label} is not an object"})
            continue
        missing = EVAL_KEYS - set(case)
        if missing:
            findings.append({
                "check": "evals",
                "message": f"{label} is missing {', '.join(sorted(missing))}",
            })
        identifier = case.get("id")
        if identifier in seen:
            findings.append({"check": "evals", "message": f"{label} repeats id {identifier!r}"})
        seen.add(identifier)
        expectations = case.get("expectations")
        if not isinstance(expectations, list) or not expectations:
            findings.append({"check": "evals", "message": f"{label} has no expectations"})
    return findings


def validate(skill_dir: Path) -> dict[str, Any]:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    fields, frontmatter_errors = parse_frontmatter(text)

    findings: list[dict[str, str]] = [
        {"check": "frontmatter", "message": message} for message in frontmatter_errors
    ]
    findings.extend(check_frontmatter(skill_dir, fields))
    findings.extend(check_links(skill_dir))
    findings.extend(check_evals(skill_dir, fields.get("name", "").strip()))

    return {
        "skill": str(skill_dir),
        "name": fields.get("name", ""),
        "ok": not findings,
        "findings": findings,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate skill directory structure.")
    parser.add_argument("skill", nargs="+", help="skill directory containing SKILL.md")
    arguments = parser.parse_args(argv)

    results = []
    for raw in arguments.skill:
        skill_dir = Path(raw).resolve()
        if not (skill_dir / "SKILL.md").is_file():
            print(f"{skill_dir}: no SKILL.md", file=sys.stderr)
            return 1
        results.append(validate(skill_dir))

    print(json.dumps(results, indent=2))
    total = sum(len(result["findings"]) for result in results)
    if total:
        print(f"{total} structural finding(s)", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
