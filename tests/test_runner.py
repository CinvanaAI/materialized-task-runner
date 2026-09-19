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

    def test_payload_must_be_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                MaterializedTaskRunner(tmp).run(task(), {"bad": object()}, authorize=True)


if __name__ == "__main__":
    unittest.main()
