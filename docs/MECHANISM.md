# Materialized Task Runner: mechanism

[MaterializedTaskRunner](../materialized_task_runner/runner.py) owns authorization, unique run roots, child-process execution and the retained JSON evidence. [Materialization](../materialized_task_runner/task_runner_materializer.py) writes the explicitly supplied Python source into the run directory. `cleanup_runtime=False` keeps those generated modules for inspection. Each runâ€™s source and payload hashes identify what was executed.

## Limits that matter

This executes arbitrary trusted Python. A fresh process is not a filesystem/network security boundary, and timeout handling does not establish isolation of descendant processes. There is no model connector or dependency solver.

## Demonstration contract

Input: A formatter package, run_workflow function and {"name":"avery"}.

Expected observation: A fresh interpreter returns {"greeting":"Hello Avery"}; source and result hashes remain in evidence.

The bundled example uses synthetic material. Its observed output establishes that bounded path, not every possible integration.

## Author, run and inspect one task

The [task JSON](../examples/task.json) is the executable unit: `name`, a
`packages` array, and a `workflow` object. Each package has a name and
`logic.logic_source`; the workflow supplies `workflow_source` defining
`run_workflow(payload)`. That function returns JSON-serializable data. Package
names are normalized into Python module names; import those resulting names in
the workflow. Duplicate normalized names (including case-only differences) and
reserved `workflow` / `_runner` names are rejected instead of silently omitting
or overwriting source.

Load the reviewed task and payload, construct `MaterializedTaskRunner(root)`,
and explicitly pass `authorize=True`. Denial and invalid JSON payloads happen
before a run directory is created. Runtime materialization, import, execution,
serialization and timeout failures write a failed record and then raise
`RuntimeError`. Run `python -m examples.failure_walkthrough` for a deliberate
failure whose request/source hashes remain after runtime cleanup; see its
[captured projection](../examples/failure-result.json).

Each execution uses a unique `runs/<run-id>` directory. Generated modules,
`workflow.py`, `payload.json`, `_runner.py` and (on success) `result.json` live
there. `evidence/<run-id>.json` retains status, duration, return code, file hashes,
result and error; the returned mapping also identifies that evidence path.
`cleanup_runtime=False` preserves the generated files for inspection. Retain the
original task/payload too: hashes identify bytes but cannot reconstruct them.

The child uses the same Python executable in isolated mode. Required third-party
packages must already be installed where that interpreter's isolated mode can
import them; user-site packages and `PYTHONPATH` are not dependency injection.
The task still has normal filesystem/network access. Error text may include
paths or values from the workflow, so inspect local evidence before sharing it.
