from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = SKILL_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wire = load_script("wire_hve_core")


PACKAGES = {
    "agents": ["accessibility", "experimental", "hve-core"],
    "prompts": ["hve-core", "experimental"],
    "instructions": ["hve-core"],
    "skills": ["hve-core", "rpi", "installer", "experimental"],
    "hooks": ["shared"],
}
SUBAGENTS = {"agents": ["hve-core", "experimental"]}


def build_source(root: Path) -> Path:
    source = root / "hve-core"
    for component, names in PACKAGES.items():
        for name in names:
            package = source / ".github" / component / name
            package.mkdir(parents=True)
            (package / "SKILL.md").write_text("stub\n", encoding="utf-8")
            if name in SUBAGENTS.get(component, []):
                (package / "subagents").mkdir()
    return source


def build_project(root: Path) -> Path:
    project = root / "project"
    project.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    return project


class Harness(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.source = build_source(self.root)
        self.project = build_project(self.root)
        self.copilot_settings = self.root / "copilot-settings.json"
        self.copilot_settings.write_text(json.dumps({"skillDirectories": []}), encoding="utf-8")
        self.addCleanup(self._tmp.cleanup)

    def run_mode(self, mode: str, *extra: str) -> tuple[int, dict]:
        argv = [
            mode,
            "--project-root",
            str(self.project),
            "--source",
            str(self.source),
            "--copilot-settings",
            str(self.copilot_settings),
            "--copilot-bin",
            "definitely-not-a-real-binary",
            *extra,
        ]
        import io
        from contextlib import redirect_stdout

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = wire.main(argv)
        return code, json.loads(buffer.getvalue())

    def settings(self) -> dict:
        return json.loads((self.project / ".vscode" / "settings.json").read_text(encoding="utf-8"))

    def register(self, *directories: str) -> None:
        self.copilot_settings.write_text(
            json.dumps({"skillDirectories": list(directories)}), encoding="utf-8"
        )


class LocationComputationTests(Harness):
    def test_values_are_object_maps_to_true_not_arrays(self) -> None:
        _, state = self.run_mode("check")
        for setting, entries in state["vscode_locations"].items():
            self.assertIsInstance(entries, dict, setting)
            self.assertTrue(all(value is True for value in entries.values()), setting)

    def test_excludes_installer_experimental_and_skills_root(self) -> None:
        _, state = self.run_mode("check")
        skills = state["vscode_locations"]["chat.agentSkillsLocations"]
        self.assertNotIn(".hve-core/.github/skills", skills)
        self.assertNotIn(".hve-core/.github/skills/installer", skills)
        self.assertNotIn(".hve-core/.github/skills/experimental", skills)
        self.assertIn(".hve-core/.github/skills/rpi", skills)

    def test_excludes_experimental_for_every_component(self) -> None:
        _, state = self.run_mode("check")
        for setting, entries in state["vscode_locations"].items():
            for location in entries:
                self.assertNotIn("experimental", location.split("/"), setting)

    def test_includes_subagents_directory_when_present(self) -> None:
        _, state = self.run_mode("check")
        agents = state["vscode_locations"]["chat.agentFilesLocations"]
        self.assertIn(".hve-core/.github/agents/hve-core/subagents", agents)
        self.assertIn(".hve-core/.github/agents/accessibility", agents)
        self.assertNotIn(".hve-core/.github/agents/accessibility/subagents", agents)

    def test_opting_into_experimental_is_not_supported(self) -> None:
        import contextlib
        import io

        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                self.run_mode("check", "--include-experimental")

    def test_experimental_is_excluded_from_cli_dirs_and_locations(self) -> None:
        _, state = self.run_mode("check")
        skills = state["vscode_locations"]["chat.agentSkillsLocations"]
        agents = state["vscode_locations"]["chat.agentFilesLocations"]
        self.assertNotIn(".hve-core/.github/skills/experimental", skills)
        self.assertNotIn(".hve-core/.github/agents/experimental", agents)
        self.assertNotIn(".hve-core/.github/agents/experimental/subagents", agents)

    def test_cli_dirs_are_absolute_source_packages(self) -> None:
        _, state = self.run_mode("check")
        expected = state["cli_skill_dirs"]["expected"]
        self.assertIn(str(self.source / ".github" / "skills" / "rpi"), expected)
        self.assertTrue(all(Path(d).is_absolute() for d in expected))
        self.assertNotIn(str(self.source / ".github" / "skills"), expected)
        self.assertNotIn(str(self.source / ".github" / "skills" / "installer"), expected)
        self.assertNotIn(str(self.source / ".github" / "skills" / "experimental"), expected)


class CollisionTests(Harness):
    def assert_no_mutation(self) -> None:
        self.assertFalse((self.project / ".vscode").exists())
        exclude = self.project / ".git" / "info" / "exclude"
        text = exclude.read_text(encoding="utf-8") if exclude.is_file() else ""
        self.assertNotIn(".hve-core", text)

    def test_existing_directory_blocks_before_any_mutation(self) -> None:
        (self.project / ".hve-core").mkdir()
        (self.project / ".hve-core" / "keep.txt").write_text("keep", encoding="utf-8")
        code, state = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_COLLISION)
        self.assertEqual(state["status"], "blocked")
        self.assertIn("directory", state["error"])
        self.assertEqual((self.project / ".hve-core" / "keep.txt").read_text(), "keep")
        self.assert_no_mutation()

    def test_regular_file_blocks_before_any_mutation(self) -> None:
        (self.project / ".hve-core").write_text("payload", encoding="utf-8")
        code, state = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_COLLISION)
        self.assertEqual((self.project / ".hve-core").read_text(), "payload")
        self.assert_no_mutation()

    def test_mismatched_symlink_reports_both_targets(self) -> None:
        other = self.root / "other-clone"
        other.mkdir()
        os.symlink(other, self.project / ".hve-core")
        code, state = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_COLLISION)
        self.assertIn(str(other), state["error"])
        self.assertIn(str(self.source), state["error"])
        self.assertEqual(os.readlink(self.project / ".hve-core"), str(other))
        self.assert_no_mutation()

    def test_broken_symlink_blocks(self) -> None:
        os.symlink(self.root / "missing", self.project / ".hve-core")
        code, _ = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_COLLISION)
        self.assert_no_mutation()

    def test_missing_source_blocks_without_cloning(self) -> None:
        argv_source = self.root / "absent-clone"
        import io
        from contextlib import redirect_stdout

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = wire.main(
                [
                    "apply",
                    "--project-root",
                    str(self.project),
                    "--source",
                    str(argv_source),
                    "--copilot-settings",
                    str(self.copilot_settings),
                ]
            )
        state = json.loads(buffer.getvalue())
        self.assertEqual(code, wire.EXIT_SOURCE_MISSING)
        self.assertIn("hve-core.git", state["error"])
        self.assertFalse(argv_source.exists())
        self.assertFalse((self.project / ".hve-core").exists())
        self.assert_no_mutation()


class ApplyTests(Harness):
    def test_apply_creates_symlink_exclude_and_settings(self) -> None:
        code, state = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_OK)
        self.assertEqual(state["status"], "applied")
        link = self.project / ".hve-core"
        self.assertTrue(link.is_symlink())
        self.assertEqual(Path(os.readlink(link)), self.source)
        exclude = self.project / ".git" / "info" / "exclude"
        self.assertIn(".hve-core", exclude.read_text(encoding="utf-8").splitlines())
        self.assertIn("chat.agentSkillsLocations", self.settings())

    def test_exclude_rule_written_once_and_not_to_gitignore(self) -> None:
        self.run_mode("apply")
        self.run_mode("apply")
        exclude = self.project / ".git" / "info" / "exclude"
        lines = [line.strip() for line in exclude.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(lines.count(".hve-core"), 1)
        self.assertFalse((self.project / ".gitignore").exists())

    def test_exclude_append_preserves_file_lacking_trailing_newline(self) -> None:
        exclude = self.project / ".git" / "info" / "exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_text("*.log\nbuild", encoding="utf-8")
        self.run_mode("apply")
        lines = exclude.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines, ["*.log", "build", ".hve-core"])

    def test_apply_preserves_unrelated_and_existing_settings(self) -> None:
        vscode = self.project / ".vscode"
        vscode.mkdir()
        (vscode / "settings.json").write_text(
            json.dumps(
                {
                    "python.analysis.typeCheckingMode": "strict",
                    "chat.agentFilesLocations": {"custom/agents": True},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        self.run_mode("apply")
        merged = self.settings()
        self.assertEqual(merged["python.analysis.typeCheckingMode"], "strict")
        self.assertIs(merged["chat.agentFilesLocations"]["custom/agents"], True)
        self.assertIs(merged["chat.agentFilesLocations"][".hve-core/.github/agents/hve-core"], True)

    def test_every_configured_path_exists_as_a_directory(self) -> None:
        self.run_mode("apply")
        for entries in self.settings().values():
            if not isinstance(entries, dict):
                continue
            for location, enabled in entries.items():
                if enabled is True:
                    self.assertTrue((self.project / location).is_dir(), location)

    def test_jsonc_settings_are_never_overwritten(self) -> None:
        vscode = self.project / ".vscode"
        vscode.mkdir()
        original = '{\n  // keep this comment\n  "editor.tabSize": 2\n}\n'
        (vscode / "settings.json").write_text(original, encoding="utf-8")
        code, state = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_MANUAL_SETTINGS)
        self.assertEqual(state["status"], "needs-manual-settings-merge")
        self.assertEqual((vscode / "settings.json").read_text(encoding="utf-8"), original)
        self.assertIn("chat.agentSkillsLocations", state["vscode_settings"]["missing_entries"])
        self.assertTrue((self.project / ".hve-core").is_symlink())

    def test_array_shaped_locations_are_never_overwritten(self) -> None:
        vscode = self.project / ".vscode"
        vscode.mkdir()
        original = json.dumps({"chat.agentFilesLocations": [{"path": "x", "enabled": True}]})
        (vscode / "settings.json").write_text(original, encoding="utf-8")
        code, _ = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_MANUAL_SETTINGS)
        self.assertEqual((vscode / "settings.json").read_text(encoding="utf-8"), original)

    def test_second_run_is_byte_identical(self) -> None:
        self.run_mode("apply")
        settings_path = self.project / ".vscode" / "settings.json"
        exclude = self.project / ".git" / "info" / "exclude"
        before = (
            settings_path.read_bytes(),
            exclude.read_bytes(),
            os.readlink(self.project / ".hve-core"),
        )
        code, state = self.run_mode("apply")
        after = (
            settings_path.read_bytes(),
            exclude.read_bytes(),
            os.readlink(self.project / ".hve-core"),
        )
        self.assertEqual(code, wire.EXIT_OK)
        self.assertEqual(before, after)
        self.assertEqual(state["actions"], [])

    def test_apply_reuses_matching_symlink(self) -> None:
        os.symlink(self.source, self.project / ".hve-core")
        code, state = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_OK)
        self.assertEqual(state["symlink"]["state"], "reuse")


class CliRegistrationTests(Harness):
    def test_missing_excludes_already_registered_directories(self) -> None:
        rpi = str(self.source / ".github" / "skills" / "rpi")
        self.register(rpi, "/unrelated/other-skills")
        _, state = self.run_mode("check")
        self.assertNotIn(rpi, state["cli_skill_dirs"]["missing"])
        self.assertIn(str(self.source / ".github" / "skills" / "hve-core"), state["cli_skill_dirs"]["missing"])

    def test_unrelated_registered_directories_are_preserved(self) -> None:
        self.register("/unrelated/other-skills")
        self.run_mode("apply")
        registered = json.loads(self.copilot_settings.read_text(encoding="utf-8"))
        self.assertIn("/unrelated/other-skills", registered["skillDirectories"])

    def test_tolerates_comment_header_in_copilot_settings(self) -> None:
        rpi = str(self.source / ".github" / "skills" / "rpi")
        self.copilot_settings.write_text(
            "// managed automatically\n" + json.dumps({"skillDirectories": [rpi]}),
            encoding="utf-8",
        )
        _, state = self.run_mode("check")
        self.assertIn(rpi, state["cli_skill_dirs"]["registered"])


class VerifyTests(Harness):
    def register_all(self) -> None:
        _, state = self.run_mode("check")
        self.register(*state["cli_skill_dirs"]["expected"])

    def test_verify_passes_after_apply(self) -> None:
        self.run_mode("apply")
        self.register_all()
        code, state = self.run_mode("verify")
        self.assertEqual(state["failures"], [])
        self.assertEqual(code, wire.EXIT_OK)
        self.assertGreater(state["configured_location_count"], 0)

    def test_verify_fails_when_symlink_absent(self) -> None:
        code, state = self.run_mode("verify")
        self.assertEqual(code, wire.EXIT_VERIFY_FAILED)
        self.assertTrue(any("does not resolve" in f for f in state["failures"]))

    def test_verify_rejects_array_shaped_locations(self) -> None:
        self.run_mode("apply")
        self.register_all()
        path = self.project / ".vscode" / "settings.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["chat.agentFilesLocations"] = [{"path": "x", "enabled": True}]
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        code, state = self.run_mode("verify")
        self.assertEqual(code, wire.EXIT_VERIFY_FAILED)
        self.assertTrue(any("not an object map" in f for f in state["failures"]))

    def test_verify_rejects_skills_root_and_excluded_packages(self) -> None:
        self.run_mode("apply")
        self.register_all()
        path = self.project / ".vscode" / "settings.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["chat.agentSkillsLocations"][".hve-core/.github/skills"] = True
        data["chat.agentSkillsLocations"][".hve-core/.github/skills/installer"] = True
        data["chat.agentSkillsLocations"][".hve-core/.github/skills/experimental"] = True
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _, state = self.run_mode("verify")
        joined = " ".join(state["failures"])
        self.assertIn("skills root", joined)
        self.assertIn("excluded package", joined)
        self.assertIn("experimental", joined)

    def test_verify_rejects_registered_installer_or_experimental(self) -> None:
        self.run_mode("apply")
        skills = self.source / ".github" / "skills"
        self.register(str(skills / "rpi"), str(skills / "installer"), str(skills))
        _, state = self.run_mode("verify")
        joined = " ".join(state["failures"])
        self.assertIn("excluded package is registered", joined)
        self.assertIn("skills root is registered", joined)

    def test_verify_reports_unregistered_cli_directory(self) -> None:
        self.run_mode("apply")
        code, state = self.run_mode("verify")
        self.assertEqual(code, wire.EXIT_VERIFY_FAILED)
        self.assertTrue(any("not registered" in f for f in state["failures"]))

    def test_verify_detects_stale_location_pointing_at_missing_directory(self) -> None:
        self.run_mode("apply")
        self.register_all()
        path = self.project / ".vscode" / "settings.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["chat.promptFilesLocations"][".hve-core/.github/prompts/gone"] = True
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _, state = self.run_mode("verify")
        self.assertTrue(any("not a directory" in f for f in state["failures"]))


class WorktreeTests(Harness):
    def test_exclude_path_follows_git_rev_parse_in_linked_worktree(self) -> None:
        subprocess.run(
            ["git", "-c", "user.email=t@e", "-c", "user.name=t", "commit",
             "-q", "--allow-empty", "-m", "init"],
            cwd=self.project,
            check=True,
        )
        worktree = self.root / "linked"
        subprocess.run(
            ["git", "worktree", "add", "-q", "-b", "wt", str(worktree)],
            cwd=self.project,
            check=True,
        )
        import io
        from contextlib import redirect_stdout

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = wire.main(
                [
                    "apply",
                    "--project-root",
                    str(worktree),
                    "--source",
                    str(self.source),
                    "--copilot-settings",
                    str(self.copilot_settings),
                    "--copilot-bin",
                    "definitely-not-a-real-binary",
                ]
            )
        state = json.loads(buffer.getvalue())
        self.assertEqual(code, wire.EXIT_OK)
        exclude = Path(state["git_exclude"]["path"])
        self.assertTrue(exclude.is_file())
        self.assertIn(".hve-core", exclude.read_text(encoding="utf-8").splitlines())
        attribution = subprocess.run(
            ["git", "check-ignore", "-v", "--no-index", ".hve-core"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(attribution.returncode, 0)


if __name__ == "__main__":
    unittest.main()
