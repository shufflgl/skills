from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "export_skillroom_catalog", SCRIPTS / "export_skillroom_catalog.py"
)
exporter = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(exporter)


class SkillroomCatalogExportTests(unittest.TestCase):
    def test_actual_repository_exports_every_cataloged_item(self) -> None:
        skills = exporter.skill_records(ROOT, exporter.repo_url(ROOT))
        workflows = exporter.workflow_records(ROOT)
        self.assertEqual(len(skills), len(exporter.skill_dirs(ROOT)))
        self.assertEqual(
            {workflow["name"] for workflow in workflows},
            {
                "deploy-my-private-vps-proxy",
                "download-bilibili-audio-to-apple-music",
            },
        )
        self.assertEqual(
            {skill["name"] for skill in skills},
            exporter.skill_dirs(ROOT),
        )

    def test_public_workflow_projection_excludes_private_sections(self) -> None:
        workflows = exporter.workflow_records(ROOT)
        public_workflow = json.dumps(workflows[0])
        self.assertNotIn("Defaults", public_workflow)
        self.assertNotIn("Approval gates", public_workflow)
        self.assertNotIn("/Users/", public_workflow)
        self.assertEqual(
            set(workflows[0]),
            {"kind", "name", "displayName", "summary", "category", "dependencies", "latestChange"},
        )

    def test_absolute_path_in_public_dependency_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "categories.json").write_text(
                '{"Workflow": "Workflow category."}',
                encoding="utf-8",
            )
            workflows = root / "workflows"
            workflow = workflows / "unsafe-workflow"
            workflow.mkdir(parents=True)
            (workflows / "README.md").write_text(
                "# Workflows\n\n## Workflow catalog\n\n"
                "| Workflow | What it automates |\n| --- | --- |\n"
                "| [Unsafe Workflow](./unsafe-workflow/) | Safe summary. |\n",
                encoding="utf-8",
            )
            (workflow / "SKILL.md").write_text(
                "---\nname: unsafe-workflow\ncategory: Workflow\ndescription: Unsafe.\n"
                "catalog_summary: Safe summary.\n---\n\n# Unsafe\n\n"
                "## Dependencies\n\n| Skill | Source | Requirement | Purpose |\n"
                "| --- | --- | --- | --- |\n"
                "| `$example` | `/Users/example/private` | required | Test. |\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "absolute path"):
                exporter.workflow_records(root)


if __name__ == "__main__":
    unittest.main()
