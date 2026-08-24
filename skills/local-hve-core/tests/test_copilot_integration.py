from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "wire_hve_core.py"
SOURCE = Path(
    os.environ.get("HVE_CORE_SOURCE", "~/repos/forks/microsoft-hve-core")
).expanduser()


@unittest.skipUnless(
    os.environ.get("RUN_COPILOT_INTEGRATION") == "1",
    "set RUN_COPILOT_INTEGRATION=1 to test Copilot CLI discovery",
)
class CopilotDiscoveryTests(unittest.TestCase):
    def test_project_links_expose_hve_skills_and_agents(self) -> None:
        self.assertIsNotNone(shutil.which("copilot"))
        self.assertTrue(SOURCE.is_dir(), SOURCE)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=project, check=True)
            subprocess.run(
                [
                    "python3",
                    str(SCRIPT),
                    "apply",
                    "--project-root",
                    str(project),
                    "--source",
                    str(SOURCE),
                    "--copilot-settings",
                    str(root / "copilot-settings.json"),
                    "--copilot-agents",
                    str(root / "copilot-agents"),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            skills = subprocess.run(
                [
                    "copilot",
                    "-C",
                    str(project),
                    "-p",
                    "/skills list",
                    "--silent",
                    "--allow-all-tools",
                    "--no-color",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("rpi-plan", skills.stdout)

            agent = subprocess.run(
                [
                    "copilot",
                    "-C",
                    str(project),
                    "--agent",
                    "Dependency Reviewer",
                    "-p",
                    "/env",
                    "--silent",
                    "--allow-all-tools",
                    "--no-color",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertNotIn("No such agent", agent.stdout + agent.stderr)


if __name__ == "__main__":
    unittest.main()
