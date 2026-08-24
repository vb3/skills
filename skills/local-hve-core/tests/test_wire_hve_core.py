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
ROOT_AGENT_FILES = ["dependency-reviewer.agent.md", "issue-triage.agent.md"]


def build_source(root: Path) -> Path:
    source = root / "hve-core"
    for component, names in PACKAGES.items():
        for name in names:
            package = source / ".github" / component / name
            package.mkdir(parents=True)
            (package / "SKILL.md").write_text("stub\n", encoding="utf-8")
            if name in SUBAGENTS.get(component, []):
                (package / "subagents").mkdir()
    agents_root = source / ".github" / "agents"
    for name in ROOT_AGENT_FILES:
        (agents_root / name).write_text("stub\n", encoding="utf-8")
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
        self.copilot_agents = self.root / "copilot-agents"
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
            "--copilot-agents",
            str(self.copilot_agents),
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

    def test_experimental_is_excluded_from_links_and_locations(self) -> None:
        _, state = self.run_mode("check")
        skills = state["vscode_locations"]["chat.agentSkillsLocations"]
        agents = state["vscode_locations"]["chat.agentFilesLocations"]
        self.assertNotIn(".hve-core/.github/skills/experimental", skills)
        self.assertNotIn(".hve-core/.github/agents/experimental", agents)
        self.assertNotIn(".hve-core/.github/agents/experimental/subagents", agents)
        self.assertNotIn("experimental", state["project_skill_links"]["expected"])

    def test_skill_links_target_packages_relatively_through_the_symlink(self) -> None:
        _, state = self.run_mode("check")
        expected = state["project_skill_links"]["expected"]
        self.assertEqual(expected["rpi"], "../../.hve-core/.github/skills/rpi")
        self.assertTrue(all(t.startswith("../../.hve-core/") for t in expected.values()))
        self.assertNotIn("installer", expected)
        self.assertNotIn("experimental", expected)


class CollisionTests(Harness):
    def assert_no_mutation(self) -> None:
        self.assertFalse((self.project / ".vscode").exists())
        self.assertFalse((self.project / ".github" / "skills").exists())
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

    def test_preexisting_exclude_rule_is_not_claimed_or_removed(self) -> None:
        exclude = self.project / ".git" / "info" / "exclude"
        with exclude.open("a", encoding="utf-8") as handle:
            handle.write("/.github/skills/rpi\n")

        self.run_mode("apply")
        self.run_mode("unwire")

        lines = exclude.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines.count("/.github/skills/rpi"), 1)

    def test_malformed_managed_exclude_block_blocks_before_mutation(self) -> None:
        exclude = self.project / ".git" / "info" / "exclude"
        with exclude.open("a", encoding="utf-8") as handle:
            handle.write(f"{wire.EXCLUDE_BLOCK_START}\n.hve-core\n")

        code, state = self.run_mode("apply")

        self.assertEqual(code, wire.EXIT_COLLISION)
        self.assertIn("managed exclude block is malformed", state["error"])
        self.assertFalse((self.project / ".hve-core").exists())
        self.assertFalse((self.project / ".github").exists())

    def test_exclude_append_preserves_file_lacking_trailing_newline(self) -> None:
        exclude = self.project / ".git" / "info" / "exclude"
        exclude.parent.mkdir(parents=True, exist_ok=True)
        exclude.write_text("*.log\nbuild", encoding="utf-8")
        self.run_mode("apply")
        lines = exclude.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[:3], ["*.log", "build", wire.EXCLUDE_BLOCK_START])
        self.assertEqual(
            lines[3:-1],
            [
                ".hve-core",
                "/.github/skills/hve-core",
                "/.github/skills/rpi",
                "/.github/agents/accessibility",
                "/.github/agents/hve-core",
                "/.github/agents/dependency-reviewer.agent.md",
                "/.github/agents/issue-triage.agent.md",
            ],
        )
        self.assertEqual(lines[-1], wire.EXCLUDE_BLOCK_END)

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
        exclude = self.project / ".git" / "info" / "exclude"
        exclude_before = exclude.read_bytes()
        (vscode / "settings.json").write_text(original, encoding="utf-8")
        code, state = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_MANUAL_SETTINGS)
        self.assertEqual(state["status"], "needs-manual-settings-merge")
        self.assertEqual((vscode / "settings.json").read_text(encoding="utf-8"), original)
        self.assertIn("chat.agentSkillsLocations", state["vscode_settings"]["missing_entries"])
        self.assertFalse((self.project / ".hve-core").exists())
        self.assertFalse((self.project / ".github").exists())
        self.assertEqual(exclude.read_bytes(), exclude_before)

    def test_tracked_settings_require_explicit_approval_before_any_mutation(self) -> None:
        vscode = self.project / ".vscode"
        vscode.mkdir()
        settings = vscode / "settings.json"
        settings.write_text('{"editor.tabSize": 2}\n', encoding="utf-8")
        subprocess.run(["git", "add", ".vscode/settings.json"], cwd=self.project, check=True)
        exclude = self.project / ".git" / "info" / "exclude"
        exclude_before = exclude.read_bytes()

        code, state = self.run_mode("apply")

        self.assertEqual(code, wire.EXIT_MANUAL_SETTINGS)
        self.assertEqual(state["status"], "needs-tracked-settings-approval")
        self.assertTrue(state["vscode_settings"]["tracked"])
        self.assertFalse((self.project / ".hve-core").exists())
        self.assertFalse((self.project / ".github").exists())
        self.assertEqual(exclude.read_bytes(), exclude_before)
        self.assertEqual(settings.read_text(encoding="utf-8"), '{"editor.tabSize": 2}\n')

    def test_tracked_settings_can_be_updated_with_explicit_approval(self) -> None:
        vscode = self.project / ".vscode"
        vscode.mkdir()
        settings = vscode / "settings.json"
        settings.write_text('{"editor.tabSize": 2}\n', encoding="utf-8")
        subprocess.run(["git", "add", ".vscode/settings.json"], cwd=self.project, check=True)

        code, state = self.run_mode("apply", "--allow-tracked-settings")

        self.assertEqual(code, wire.EXIT_OK)
        self.assertEqual(state["status"], "applied")
        self.assertTrue((self.project / ".hve-core").is_symlink())
        self.assertEqual(self.settings()["editor.tabSize"], 2)

    def test_jsonc_missing_entries_name_only_what_is_absent(self) -> None:
        self.run_mode("apply")
        path = self.project / ".vscode" / "settings.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        dropped = data.pop("chat.agentSkillsLocations")
        path.write_text(
            "// keep this comment\n" + json.dumps(data, indent=2), encoding="utf-8"
        )
        code, state = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_MANUAL_SETTINGS)
        missing = state["vscode_settings"]["missing_entries"]
        self.assertEqual(sorted(missing), ["chat.agentSkillsLocations"])
        self.assertEqual(missing["chat.agentSkillsLocations"], dropped)

    def test_complete_jsonc_settings_apply_cleanly_and_are_untouched(self) -> None:
        self.run_mode("apply")
        path = self.project / ".vscode" / "settings.json"
        commented = "// keep this comment\n" + path.read_text(encoding="utf-8")
        path.write_text(commented, encoding="utf-8")
        code, state = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_OK)
        self.assertEqual(state["status"], "applied")
        self.assertEqual(state["vscode_settings"]["state"], "jsonc")
        self.assertEqual(state["vscode_settings"]["missing_entries"], {})
        self.assertEqual(path.read_text(encoding="utf-8"), commented)

    def test_complete_jsonc_with_inline_comments_and_trailing_comma_is_accepted(self) -> None:
        self.run_mode("apply")
        path = self.project / ".vscode" / "settings.json"
        jsonc = path.read_text(encoding="utf-8").rstrip()
        jsonc = jsonc[:-1] + ",\n} // keep this inline comment\n"
        path.write_text(jsonc, encoding="utf-8")

        code, state = self.run_mode("apply")

        self.assertEqual(code, wire.EXIT_OK)
        self.assertEqual(state["status"], "applied")
        self.assertEqual(state["vscode_settings"]["state"], "jsonc")
        self.assertEqual(state["vscode_settings"]["missing_entries"], {})
        self.assertEqual(path.read_text(encoding="utf-8"), jsonc)

    def test_complete_strict_json_is_not_reformatted(self) -> None:
        self.run_mode("apply")
        path = self.project / ".vscode" / "settings.json"
        compact = json.dumps(json.loads(path.read_text(encoding="utf-8"))) + "\n"
        path.write_text(compact, encoding="utf-8")

        code, state = self.run_mode("apply")

        self.assertEqual(code, wire.EXIT_OK)
        self.assertEqual(state["actions"], [])
        self.assertEqual(path.read_text(encoding="utf-8"), compact)

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

    def test_apply_restores_missing_root_symlink_behind_managed_links(self) -> None:
        self.run_mode("apply")
        (self.project / ".hve-core").unlink()

        code, state = self.run_mode("apply")

        self.assertEqual(code, wire.EXIT_OK)
        self.assertEqual(state["status"], "applied")
        self.assertTrue((self.project / ".hve-core").is_symlink())
        self.assertTrue((self.project / ".github" / "skills" / "rpi").is_dir())

    def test_apply_reenables_disabled_required_location(self) -> None:
        self.run_mode("apply")
        path = self.project / ".vscode" / "settings.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        location = ".hve-core/.github/skills/rpi"
        data["chat.agentSkillsLocations"][location] = False
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        code, _ = self.run_mode("apply")

        self.assertEqual(code, wire.EXIT_OK)
        self.assertIs(self.settings()["chat.agentSkillsLocations"][location], True)


class ProjectSkillLinkTests(Harness):
    def links_dir(self) -> Path:
        return self.project / ".github" / "skills"

    def test_apply_creates_one_relative_symlink_per_package(self) -> None:
        self.run_mode("apply")
        rpi = self.links_dir() / "rpi"
        self.assertTrue(rpi.is_symlink())
        self.assertEqual(os.readlink(rpi), "../../.hve-core/.github/skills/rpi")
        self.assertTrue(rpi.is_dir(), "link must resolve through the .hve-core symlink")
        self.assertFalse((self.links_dir() / "installer").exists())
        self.assertFalse((self.links_dir() / "experimental").exists())

    def test_links_are_excluded_from_git(self) -> None:
        self.run_mode("apply")
        exclude = self.project / ".git" / "info" / "exclude"
        lines = [line.strip() for line in exclude.read_text(encoding="utf-8").splitlines()]
        self.assertIn("/.github/skills/rpi", lines)
        self.assertEqual(lines.count("/.github/skills/rpi"), 1)
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.project,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertNotIn(".github/skills", status.stdout)

    def test_existing_real_package_directory_blocks_apply(self) -> None:
        own = self.links_dir() / "rpi"
        own.mkdir(parents=True)
        (own / "SKILL.md").write_text("mine", encoding="utf-8")
        code, state = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_COLLISION)
        self.assertIn(".github/skills/rpi is a directory", state["error"])
        self.assertEqual((own / "SKILL.md").read_text(encoding="utf-8"), "mine")

    def test_unrelated_project_skills_are_left_alone(self) -> None:
        mine = self.links_dir() / "my-own-skill"
        mine.mkdir(parents=True)
        (mine / "SKILL.md").write_text("mine", encoding="utf-8")
        code, _ = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_OK)
        self.assertTrue((mine / "SKILL.md").is_file())
        exclude = self.project / ".git" / "info" / "exclude"
        self.assertNotIn(
            "/.github/skills/my-own-skill",
            exclude.read_text(encoding="utf-8").splitlines(),
        )

    def test_stale_global_registration_is_reported_not_created(self) -> None:
        skills = self.source / ".github" / "skills"
        self.register(str(skills / "rpi"), "/unrelated/other-skills")
        _, state = self.run_mode("check")
        self.assertEqual(state["stale_cli_registrations"], [str(skills / "rpi")])

    def test_apply_never_writes_copilot_settings(self) -> None:
        before = self.copilot_settings.read_bytes()
        self.run_mode("apply")
        self.assertEqual(self.copilot_settings.read_bytes(), before)

    def test_tolerates_comment_header_in_copilot_settings(self) -> None:
        rpi = str(self.source / ".github" / "skills" / "rpi")
        self.copilot_settings.write_text(
            "// managed automatically\n" + json.dumps({"skillDirectories": [rpi]}),
            encoding="utf-8",
        )
        _, state = self.run_mode("check")
        self.assertIn(rpi, state["stale_cli_registrations"])


class ProjectAgentLinkTests(Harness):
    def links_dir(self) -> Path:
        return self.project / ".github" / "agents"

    def test_apply_creates_one_relative_symlink_per_package(self) -> None:
        self.run_mode("apply")
        package = self.links_dir() / "accessibility"
        self.assertTrue(package.is_symlink())
        self.assertEqual(
            os.readlink(package), "../../.hve-core/.github/agents/accessibility"
        )
        self.assertTrue(package.is_dir(), "link must resolve through the .hve-core symlink")
        self.assertFalse((self.links_dir() / "experimental").exists())

    def test_apply_links_root_agent_files_individually(self) -> None:
        self.run_mode("apply")
        link = self.links_dir() / "dependency-reviewer.agent.md"
        self.assertTrue(link.is_symlink())
        self.assertEqual(
            os.readlink(link),
            "../../.hve-core/.github/agents/dependency-reviewer.agent.md",
        )
        self.assertTrue(link.is_file())

    def test_links_are_excluded_from_git(self) -> None:
        self.run_mode("apply")
        exclude = self.project / ".git" / "info" / "exclude"
        lines = [line.strip() for line in exclude.read_text(encoding="utf-8").splitlines()]
        self.assertIn("/.github/agents/accessibility", lines)
        self.assertIn("/.github/agents/dependency-reviewer.agent.md", lines)
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.project,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertNotIn(".github/agents", status.stdout)

    def test_existing_real_package_directory_blocks_apply(self) -> None:
        own = self.links_dir() / "hve-core"
        own.mkdir(parents=True)
        (own / "mine.agent.md").write_text("mine", encoding="utf-8")
        code, state = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_COLLISION)
        self.assertIn(".github/agents/hve-core is a directory", state["error"])
        self.assertEqual((own / "mine.agent.md").read_text(encoding="utf-8"), "mine")

    def test_existing_root_agent_file_blocks_apply(self) -> None:
        own = self.links_dir() / "dependency-reviewer.agent.md"
        own.parent.mkdir(parents=True)
        own.write_text("mine", encoding="utf-8")
        code, state = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_COLLISION)
        self.assertIn(
            ".github/agents/dependency-reviewer.agent.md is a file",
            state["error"],
        )
        self.assertEqual(own.read_text(encoding="utf-8"), "mine")

    def test_project_owned_agent_files_are_left_alone(self) -> None:
        mine = self.links_dir() / "vertex-scribe.agent.md"
        mine.parent.mkdir(parents=True)
        mine.write_text("mine", encoding="utf-8")
        code, _ = self.run_mode("apply")
        self.assertEqual(code, wire.EXIT_OK)
        self.assertEqual(mine.read_text(encoding="utf-8"), "mine")
        exclude = self.project / ".git" / "info" / "exclude"
        self.assertNotIn(
            "/.github/agents/vertex-scribe.agent.md",
            exclude.read_text(encoding="utf-8").splitlines(),
        )

    def test_global_agent_link_is_reported_not_created(self) -> None:
        self.run_mode("apply")
        self.assertFalse(self.copilot_agents.exists(), "apply must never write global agents")
        self.copilot_agents.mkdir()
        link = self.copilot_agents / "hve-core"
        link.symlink_to(self.source / ".github" / "agents" / "hve-core")
        (self.copilot_agents / "unrelated").symlink_to(self.root)
        _, state = self.run_mode("check")
        self.assertEqual(state["stale_global_agent_links"], [str(link)])


class ReconciliationTests(Harness):
    def test_apply_removes_stale_managed_links_settings_and_excludes(self) -> None:
        self.run_mode("apply")
        removed = self.source / ".github" / "skills" / "rpi"
        removed.rename(self.root / "removed-rpi")

        code, state = self.run_mode("apply")

        self.assertEqual(code, wire.EXIT_OK)
        self.assertEqual(state["status"], "applied")
        self.assertFalse((self.project / ".github" / "skills" / "rpi").exists())
        self.assertNotIn(
            "/.github/skills/rpi",
            (self.project / ".git" / "info" / "exclude")
            .read_text(encoding="utf-8")
            .splitlines(),
        )
        self.assertNotIn(
            ".hve-core/.github/skills/rpi",
            self.settings()["chat.agentSkillsLocations"],
        )
        verify_code, verify_state = self.run_mode("verify")
        self.assertEqual(verify_code, wire.EXIT_OK)
        self.assertEqual(verify_state["failures"], [])


class UnwireTests(Harness):
    def test_unwire_removes_only_hve_core_wiring(self) -> None:
        own_skill = self.project / ".github" / "skills" / "mine"
        own_skill.mkdir(parents=True)
        (own_skill / "SKILL.md").write_text("mine\n", encoding="utf-8")
        own_agent = self.project / ".github" / "agents" / "mine.agent.md"
        own_agent.parent.mkdir(parents=True)
        own_agent.write_text("mine\n", encoding="utf-8")
        self.run_mode("apply")
        settings_path = self.project / ".vscode" / "settings.json"
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        settings["editor.tabSize"] = 2
        settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        exclude = self.project / ".git" / "info" / "exclude"
        with exclude.open("a", encoding="utf-8") as handle:
            handle.write("*.local\n")

        code, state = self.run_mode("unwire")

        self.assertEqual(code, wire.EXIT_OK)
        self.assertEqual(state["status"], "unwired")
        self.assertFalse((self.project / ".hve-core").exists())
        self.assertTrue((own_skill / "SKILL.md").is_file())
        self.assertEqual(own_agent.read_text(encoding="utf-8"), "mine\n")
        remaining = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(remaining, {"editor.tabSize": 2})
        self.assertEqual(exclude.read_text(encoding="utf-8").splitlines()[-1], "*.local")
        self.assertFalse(
            any(
                line == ".hve-core" or line.startswith("/.github/skills/")
                or line.startswith("/.github/agents/")
                for line in exclude.read_text(encoding="utf-8").splitlines()
            )
        )

    def test_unwire_jsonc_gate_makes_no_changes(self) -> None:
        self.run_mode("apply")
        settings_path = self.project / ".vscode" / "settings.json"
        settings_path.write_text(
            "// preserve\n" + settings_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        before = {
            "settings": settings_path.read_bytes(),
            "exclude": (self.project / ".git" / "info" / "exclude").read_bytes(),
            "skill": os.readlink(self.project / ".github" / "skills" / "rpi"),
        }

        code, state = self.run_mode("unwire")

        self.assertEqual(code, wire.EXIT_MANUAL_SETTINGS)
        self.assertEqual(state["status"], "needs-manual-settings-merge")
        self.assertEqual(settings_path.read_bytes(), before["settings"])
        self.assertEqual(
            (self.project / ".git" / "info" / "exclude").read_bytes(),
            before["exclude"],
        )
        self.assertEqual(
            os.readlink(self.project / ".github" / "skills" / "rpi"),
            before["skill"],
        )
        self.assertTrue((self.project / ".hve-core").is_symlink())


class VerifyTests(Harness):
    def test_verify_passes_after_apply(self) -> None:
        self.run_mode("apply")
        code, state = self.run_mode("verify")
        self.assertEqual(state["failures"], [])
        self.assertEqual(code, wire.EXIT_OK)
        self.assertGreater(state["configured_location_count"], 0)
        self.assertGreater(state["linked_skill_package_count"], 0)
        self.assertGreater(state["linked_agent_package_count"], 0)

    def test_verify_reports_unlinked_agent_package(self) -> None:
        self.run_mode("apply")
        (self.project / ".github" / "agents" / "hve-core").unlink()
        code, state = self.run_mode("verify")
        self.assertEqual(code, wire.EXIT_VERIFY_FAILED)
        self.assertIn(
            "agents package not linked: .github/agents/hve-core", state["failures"]
        )

    def test_verify_reports_global_agent_link_with_remedy(self) -> None:
        self.run_mode("apply")
        self.copilot_agents.mkdir()
        link = self.copilot_agents / "prd-builder.agent.md"
        link.symlink_to(self.source / ".github" / "agents" / "hve-core" / "SKILL.md")
        code, state = self.run_mode("verify")
        self.assertEqual(code, wire.EXIT_VERIFY_FAILED)
        joined = " ".join(state["failures"])
        self.assertIn("linked machine-wide instead of per project", joined)
        self.assertIn(f"rm {link}", joined)

    def test_verify_fails_when_symlink_absent(self) -> None:
        code, state = self.run_mode("verify")
        self.assertEqual(code, wire.EXIT_VERIFY_FAILED)
        self.assertTrue(any("does not resolve" in f for f in state["failures"]))

    def test_verify_rejects_array_shaped_locations(self) -> None:
        self.run_mode("apply")
        path = self.project / ".vscode" / "settings.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["chat.agentFilesLocations"] = [{"path": "x", "enabled": True}]
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        code, state = self.run_mode("verify")
        self.assertEqual(code, wire.EXIT_VERIFY_FAILED)
        self.assertTrue(any("not an object map" in f for f in state["failures"]))

    def test_verify_rejects_skills_root_and_excluded_packages(self) -> None:
        self.run_mode("apply")
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

    def test_verify_reports_stale_global_registrations_with_remedy(self) -> None:
        self.run_mode("apply")
        skills = self.source / ".github" / "skills"
        self.register(str(skills / "rpi"), "/unrelated/other-skills")
        code, state = self.run_mode("verify")
        self.assertEqual(code, wire.EXIT_VERIFY_FAILED)
        joined = " ".join(state["failures"])
        self.assertIn("copilot skill remove", joined)
        self.assertIn(str(skills / "rpi"), joined)
        self.assertNotIn("/unrelated/other-skills", joined)

    def test_verify_reports_unlinked_package(self) -> None:
        self.run_mode("apply")
        (self.project / ".github" / "skills" / "rpi").unlink()
        code, state = self.run_mode("verify")
        self.assertEqual(code, wire.EXIT_VERIFY_FAILED)
        self.assertTrue(any("not linked" in f for f in state["failures"]))

    def test_verify_reports_experimental_link(self) -> None:
        self.run_mode("apply")
        link = self.project / ".github" / "skills" / "experimental"
        link.symlink_to("../../.hve-core/.github/skills/experimental")
        _, state = self.run_mode("verify")
        self.assertTrue(any("experimental package is linked" in f for f in state["failures"]))

    def test_verify_detects_stale_location_pointing_at_missing_directory(self) -> None:
        self.run_mode("apply")
        path = self.project / ".vscode" / "settings.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["chat.promptFilesLocations"][".hve-core/.github/prompts/gone"] = True
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _, state = self.run_mode("verify")
        self.assertTrue(any("not a directory" in f for f in state["failures"]))

    def test_verify_detects_stale_setting_when_component_becomes_empty(self) -> None:
        self.run_mode("apply")
        prompts = self.source / ".github" / "prompts"
        (prompts / "hve-core").rename(self.root / "removed-prompts")

        code, state = self.run_mode("verify")

        self.assertEqual(code, wire.EXIT_VERIFY_FAILED)
        self.assertTrue(
            any("stale HVE-Core entry" in failure for failure in state["failures"])
        )


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
