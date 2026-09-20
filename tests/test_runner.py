from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from materialized_task_runner import MaterializedTaskRunner


def task() -> dict:
    return {
        "name": "Greeting",
        "packages": [
            {
                "name": "formatter",
                "logic": {"logic_source": "def format_name(value):\n    return value.strip().title()"},
            }
        ],
        "workflow": {
            "workflow_source": "from formatter import format_name\n\ndef run_workflow(payload):\n    return {'greeting': 'Hello ' + format_name(payload['name'])}"
        },
    }


class RunnerTests(unittest.TestCase):
    def test_authorization_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError):
                MaterializedTaskRunner(tmp).run(task(), {"name": "avery"}, authorize=False)

    def test_materializes_executes_records_and_cleans(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence = MaterializedTaskRunner(tmp).run(task(), {"name": "avery"}, authorize=True)
            self.assertEqual(evidence["status"], "complete")
            self.assertEqual(evidence["result"], {"greeting": "Hello Avery"})
            self.assertFalse(any((Path(tmp) / "runs").iterdir()))
            stored = json.loads(Path(evidence["evidence_path"]).read_text(encoding="utf-8"))
            self.assertIn("workflow.py", stored["file_sha256"])

    def test_runtime_can_be_retained_for_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            evidence = MaterializedTaskRunner(tmp).run(
                task(), {"name": "river"}, authorize=True, cleanup_runtime=False
            )
            self.assertTrue((Path(tmp) / "runs" / evidence["run_id"] / "result.json").exists())

    def test_invalid_module_name_fails(self) -> None:
        broken = task()
        broken["packages"][0]["name"] = "../escape"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                MaterializedTaskRunner(tmp).run(broken, {}, authorize=True)

    def test_ambiguous_and_reserved_modules_fail_before_execution(self) -> None:
        for names in (("format-ter", "formatter"), ("Formatter", "formatter"), ("workflow",), ("_runner",)):
            with self.subTest(names=names), tempfile.TemporaryDirectory() as tmp:
                candidate = task()
                candidate["packages"] = [{"name": name, "logic": {"logic_source": "VALUE = 1"}} for name in names]
                candidate["workflow"]["workflow_source"] = "from pathlib import Path\ndef run_workflow(payload):\n    Path('executed.txt').write_text('unexpected')\n"
                with self.assertRaisesRegex(RuntimeError, "collision|reserved"):
                    MaterializedTaskRunner(tmp).run(candidate, {}, authorize=True, cleanup_runtime=False)
                self.assertFalse(list(Path(tmp).rglob("executed.txt")))
                record = json.loads(next((Path(tmp) / "evidence").glob("*.json")).read_text())
                self.assertEqual(record["status"], "failed")

    def test_payload_must_be_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                MaterializedTaskRunner(tmp).run(task(), {"bad": object()}, authorize=True)


if __name__ == "__main__":
    unittest.main()
