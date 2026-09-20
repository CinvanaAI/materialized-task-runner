"""A workflow failure still leaves local source and request evidence."""
import json
import tempfile
from pathlib import Path
from materialized_task_runner import MaterializedTaskRunner

with tempfile.TemporaryDirectory(prefix="task-failure-") as temporary:
    root = Path(temporary)
    task = {"name": "Synthetic failure", "packages": [], "workflow": {"workflow_source": "def run_workflow(payload):\n    raise ValueError('synthetic failure')\n"}}
    try:
        MaterializedTaskRunner(root).run(task, {"case": "failure"}, authorize=True)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Failure was not reported")
    files = list((root / "evidence").glob("*.json"))
    assert len(files) == 1
    evidence = json.loads(files[0].read_text(encoding="utf-8"))
    assert evidence["status"] == "failed" and evidence["return_code"] != 0
    assert "synthetic failure" in evidence["error"]
    assert {"workflow.py", "payload.json"} <= evidence["file_sha256"].keys()
    assert not any((root / "runs").iterdir())
    print(json.dumps({"synthetic": True, "status": evidence["status"], "error_observed": "ValueError", "hashed_files": sorted(evidence["file_sha256"]), "runtime_cleaned": True, "evidence_retained_until_example_cleanup": True}, indent=2))
