from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_workflows.py"
SPEC = importlib.util.spec_from_file_location("check_workflows", SCRIPT)
assert SPEC and SPEC.loader
check_workflows = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_workflows)


VALID_SKILL = """---
name: make-note
description: Make a personalized note when explicitly requested.
catalog_summary: Make one personalized note.
---

# Make note

## Dependencies

| Skill | Source | Requirement | Purpose |
| --- | --- | --- | --- |
| `$summarize` | repository | required | Summarize the input. |

## Defaults

Use the personal vault.

## Workflow

1. Invoke the dependency.

## Approval gates

Approve substitutions.

## Completion criteria

The note exists.

## Failure handling

Report blockers.
"""


class WorkflowValidationTests(unittest.TestCase):
    def make_root(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        workflows = root / "workflows"
        workflows.mkdir()
        (workflows / "README.md").write_text(
            "# Personal workflows\n\n## Workflow catalog\n\n"
            "| Workflow | What it automates |\n| --- | --- |\n",
            encoding="utf-8",
        )
        return root

    def add_valid_workflow(self, root: Path) -> Path:
        workflow = root / "workflows" / "make-note"
        workflow.mkdir()
        (workflow / "SKILL.md").write_text(VALID_SKILL, encoding="utf-8")
        readme = root / "workflows" / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8")
            + "| [Make note](./make-note/) | Make one personalized note. |\n",
            encoding="utf-8",
        )
        return workflow

    def test_empty_initialized_state_is_valid(self) -> None:
        self.assertEqual(check_workflows.validate(self.make_root()), [])

    def test_valid_workflow_is_valid(self) -> None:
        root = self.make_root()
        self.add_valid_workflow(root)
        self.assertEqual(check_workflows.validate(root), [])

    def test_malformed_dependency_is_rejected(self) -> None:
        root = self.make_root()
        workflow = self.add_valid_workflow(root)
        path = workflow / "SKILL.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("required |", "sometimes |"),
            encoding="utf-8",
        )
        self.assertTrue(any("requirement must be" in error for error in check_workflows.validate(root)))

    def test_missing_section_is_rejected(self) -> None:
        root = self.make_root()
        workflow = self.add_valid_workflow(root)
        path = workflow / "SKILL.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("## Approval gates", "## Reviews"),
            encoding="utf-8",
        )
        self.assertTrue(any("Approval gates" in error for error in check_workflows.validate(root)))

    def test_catalog_drift_is_rejected(self) -> None:
        root = self.make_root()
        self.add_valid_workflow(root)
        readme = root / "workflows" / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace(
                "Make one personalized note.", "Different summary."
            ),
            encoding="utf-8",
        )
        self.assertTrue(any("catalog text" in error for error in check_workflows.validate(root)))

    def test_template_directory_is_ignored(self) -> None:
        root = self.make_root()
        template = root / "workflows" / "_template"
        template.mkdir()
        (template / "SKILL.md.template").write_text("placeholders", encoding="utf-8")
        self.assertEqual(check_workflows.validate(root), [])


if __name__ == "__main__":
    unittest.main()
