#!/usr/bin/env python3
"""Copy the bundled FastAPI on Functions Flex starter into a project."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCAFFOLD_ROOT = SKILL_ROOT / "assets" / "scaffold"
CANONICAL_EASY_AUTH = SKILL_ROOT / "assets" / "bicep" / "easy-auth.bicep"
SCAFFOLD_FILES = (
    Path("azure.yaml"),
    Path("function_app.py"),
    Path("host.json"),
    Path("local.settings.json"),
    Path("requirements.txt"),
    Path("app/__init__.py"),
    Path("app/main.py"),
    Path("infra/main.bicep"),
    Path("infra/app.bicep"),
    Path("infra/main.parameters.json"),
)


def scaffold_project(target: Path) -> list[Path]:
    target = target.expanduser().resolve()
    if target.exists() and not target.is_dir():
        raise NotADirectoryError(f"Target is not a directory: {target}")

    destinations = [target / relative for relative in SCAFFOLD_FILES]
    destinations.append(target / "infra" / "easy-auth.bicep")
    conflicts = [path for path in destinations if path.exists()]
    if conflicts:
        names = ", ".join(str(path.relative_to(target)) for path in conflicts)
        raise FileExistsError(
            f"Refusing to overwrite existing scaffold files: {names}"
        )

    sources = [SCAFFOLD_ROOT / relative for relative in SCAFFOLD_FILES]
    sources.append(CANONICAL_EASY_AUTH)
    missing = [path for path in sources if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Bundled scaffold is incomplete: {missing[0]}")

    created: list[Path] = []
    for source, destination in zip(sources, destinations, strict=True):
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        created.append(destination)
    return created


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=Path.cwd(),
        help="Project directory to populate",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        created = scaffold_project(args.target)
    except (FileExistsError, FileNotFoundError, NotADirectoryError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    json.dump(
        {"created": [str(path) for path in created]},
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
