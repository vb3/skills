from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_SKILLS = SKILL_ROOT.parent


def load_script(name: str):
    path = SKILL_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_skill = load_script("validate_skill")


VALID_EVALS = {
    "skill_name": "demo-skill",
    "evals": [
        {
            "id": 1,
            "prompt": "p",
            "expected_output": "o",
            "files": [],
            "expectations": ["e"],
        }
    ],
}


def build_skill(root: Path, *, name: str = "demo-skill", body: str = "", evals=VALID_EVALS):
    skill_dir = root / name
    (skill_dir / "evals").mkdir(parents=True)
    frontmatter = f"---\nname: {name}\ndescription: A demo skill for tests.\n---\n"
    (skill_dir / "SKILL.md").write_text(frontmatter + body, encoding="utf-8")
    if evals is not None:
        (skill_dir / "evals" / "evals.json").write_text(json.dumps(evals), encoding="utf-8")
    return skill_dir


class FrontmatterTests(unittest.TestCase):
    def test_parses_scalar_fields(self):
        fields, errors = validate_skill.parse_frontmatter(
            "---\nname: a-skill\ndescription: Does a thing.\n---\n# Body\n"
        )
        self.assertEqual(errors, [])
        self.assertEqual(fields["name"], "a-skill")
        self.assertEqual(fields["description"], "Does a thing.")

    def test_parses_folded_block_scalar(self):
        fields, errors = validate_skill.parse_frontmatter(
            "---\nname: a-skill\ndescription: >-\n    First line\n    second line\n---\n"
        )
        self.assertEqual(errors, [])
        self.assertEqual(fields["description"], "First line second line")

    def test_reports_missing_block(self):
        _, errors = validate_skill.parse_frontmatter("# No frontmatter\n")
        self.assertIn("does not open", errors[0])

    def test_reports_unclosed_block(self):
        _, errors = validate_skill.parse_frontmatter("---\nname: a\n")
        self.assertIn("never closed", errors[0])


class ValidationTests(unittest.TestCase):
    def test_valid_skill_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_skill.validate(build_skill(Path(tmp)))
        self.assertTrue(result["ok"], result["findings"])

    def test_name_directory_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = build_skill(Path(tmp))
            skill.joinpath("SKILL.md").write_text(
                "---\nname: other-name\ndescription: d\n---\n", encoding="utf-8"
            )
            result = validate_skill.validate(skill)
        self.assertFalse(result["ok"])
        self.assertTrue(any("does not match directory" in f["message"] for f in result["findings"]))

    def test_non_kebab_name_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "Bad--Name"
            (skill / "evals").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: Bad--Name\ndescription: d\n---\n", encoding="utf-8"
            )
            (skill / "evals" / "evals.json").write_text(json.dumps(VALID_EVALS), encoding="utf-8")
            result = validate_skill.validate(skill)
        self.assertTrue(any("kebab-case" in f["message"] for f in result["findings"]))

    def test_empty_description_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = build_skill(Path(tmp))
            skill.joinpath("SKILL.md").write_text(
                "---\nname: demo-skill\ndescription:\n---\n", encoding="utf-8"
            )
            result = validate_skill.validate(skill)
        self.assertTrue(any("description" in f["check"] for f in result["findings"]))

    def test_broken_relative_link_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = build_skill(Path(tmp), body="See [gone](references/gone.md).\n")
            result = validate_skill.validate(skill)
        self.assertTrue(any(f["check"] == "links" for f in result["findings"]))

    def test_external_and_anchor_links_are_ignored(self):
        body = "[web](https://example.com) [anchor](#section)\n"
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_skill.validate(build_skill(Path(tmp), body=body))
        self.assertTrue(result["ok"], result["findings"])

    def test_missing_evals_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_skill.validate(build_skill(Path(tmp), evals=None))
        self.assertTrue(any("evals/evals.json is missing" == f["message"] for f in result["findings"]))

    def test_duplicate_eval_ids_are_reported(self):
        case = dict(VALID_EVALS["evals"][0])
        evals = {"skill_name": "demo-skill", "evals": [case, dict(case)]}
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_skill.validate(build_skill(Path(tmp), evals=evals))
        self.assertTrue(any("repeats id" in f["message"] for f in result["findings"]))

    def test_empty_expectations_are_reported(self):
        case = dict(VALID_EVALS["evals"][0], expectations=[])
        evals = {"skill_name": "demo-skill", "evals": [case]}
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_skill.validate(build_skill(Path(tmp), evals=evals))
        self.assertTrue(any("no expectations" in f["message"] for f in result["findings"]))

    def test_missing_eval_keys_are_reported(self):
        evals = {"skill_name": "demo-skill", "evals": [{"id": 1, "expectations": ["e"]}]}
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_skill.validate(build_skill(Path(tmp), evals=evals))
        self.assertTrue(any("is missing" in f["message"] for f in result["findings"]))

    def test_skill_name_mismatch_is_reported(self):
        evals = {"skill_name": "wrong", "evals": VALID_EVALS["evals"]}
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_skill.validate(build_skill(Path(tmp), evals=evals))
        self.assertTrue(any("does not match" in f["message"] for f in result["findings"]))

    def test_unparseable_evals_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = build_skill(Path(tmp))
            skill.joinpath("evals", "evals.json").write_text("{nope", encoding="utf-8")
            result = validate_skill.validate(skill)
        self.assertTrue(any("does not parse" in f["message"] for f in result["findings"]))


class ExitCodeTests(unittest.TestCase):
    def test_returns_zero_for_valid_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = build_skill(Path(tmp))
            self.assertEqual(validate_skill.main([str(skill)]), 0)

    def test_returns_two_for_defects(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = build_skill(Path(tmp), evals=None)
            self.assertEqual(validate_skill.main([str(skill)]), 2)

    def test_returns_one_when_not_a_skill_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(validate_skill.main([tmp]), 1)


class RepositoryTests(unittest.TestCase):
    def test_every_skill_in_this_repo_is_structurally_valid(self):
        for skill_md in sorted(REPO_SKILLS.glob("*/SKILL.md")):
            with self.subTest(skill=skill_md.parent.name):
                result = validate_skill.validate(skill_md.parent)
                self.assertTrue(result["ok"], result["findings"])


if __name__ == "__main__":
    unittest.main()
