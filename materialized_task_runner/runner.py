from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from .task_runner_materializer import (
    write_package_scripts_from_child_data,
    write_workflow_script_from_child_data,
)
from .task_runner_payloads import validate_runtime_payload


WRAPPER_SOURCE = '''from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

runtime = Path(sys.argv[1]).resolve()
payload_path = Path(sys.argv[2]).resolve()
result_path = Path(sys.argv[3]).resolve()
sys.path.insert(0, str(runtime))
spec = importlib.util.spec_from_file_location("materialized_workflow", runtime / "workflow.py")
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load materialized workflow")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
run_workflow = getattr(module, "run_workflow", None)
if not callable(run_workflow):
    raise ValueError("workflow.py must define callable run_workflow(payload)")
payload = json.loads(payload_path.read_text(encoding="utf-8"))
result = run_workflow(payload)
result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
'''


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class MaterializedTaskRunner:
    def __init__(self, root: str | Path, *, timeout_seconds: float = 30.0) -> None:
        self.root = Path(root).expanduser().resolve()
        self.timeout_seconds = float(timeout_seconds)
        if self.timeout_seconds <= 0 or self.timeout_seconds > 3600:
            raise ValueError("timeout_seconds must be between 0 and 3600")
        self.runs_dir = self.root / "runs"
        self.evidence_dir = self.root / "evidence"

    def run(
        self,
        task: dict[str, Any],
        payload: Any,
        *,
        authorize: bool,
        cleanup_runtime: bool = True,
    ) -> dict[str, Any]:
        if authorize is not True:
            raise PermissionError("Execution requires authorize=True")
        validate_runtime_payload(payload)
        task_name = str(task.get("name") or "task").strip()
        run_id = f"run-{uuid.uuid4().hex}"
        runtime = (self.runs_dir / run_id).resolve()
        if self.runs_dir.resolve() not in runtime.parents:
            raise ValueError("Runtime escaped configured root")
        runtime.mkdir(parents=True, exist_ok=False)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        started = time.monotonic()
        status = "failed"
        return_code: int | None = None
        error = ""
        result: Any = None
        try:
            package_paths = write_package_scripts_from_child_data(task, task_name, runtime)
            workflow_path = Path(write_workflow_script_from_child_data(task, task_name, runtime / "workflow.py"))
            payload_path = runtime / "payload.json"
            result_path = runtime / "result.json"
            wrapper_path = runtime / "_runner.py"
            payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            wrapper_path.write_text(WRAPPER_SOURCE, encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-I", str(wrapper_path), str(runtime), str(payload_path), str(result_path)],
                cwd=runtime,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
            return_code = completed.returncode
            if completed.returncode != 0:
                error = (completed.stderr or completed.stdout)[-4000:]
                raise RuntimeError(f"Materialized workflow exited {completed.returncode}")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            status = "complete"
            file_hashes = {
                Path(path).name: _sha256(Path(path)) for path in [*package_paths, workflow_path, payload_path, result_path]
            }
        except Exception as exc:
            error = error or f"{type(exc).__name__}: {exc}"
            file_hashes = {
                path.name: _sha256(path)
                for path in runtime.iterdir()
                if path.is_file()
            }
        evidence = {
            "schema_version": "materialized-task-runner.evidence.v1",
            "run_id": run_id,
            "task_name": task_name,
            "status": status,
            "return_code": return_code,
            "duration_ms": round((time.monotonic() - started) * 1000, 3),
            "runtime_retained": not cleanup_runtime,
            "file_sha256": dict(sorted(file_hashes.items())),
            "result": result,
            "error": error,
        }
        evidence_path = self.evidence_dir / f"{run_id}.json"
        evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        evidence["evidence_path"] = str(evidence_path)
        if cleanup_runtime:
            shutil.rmtree(runtime)
        if status != "complete":
            raise RuntimeError(error)
        return evidence
