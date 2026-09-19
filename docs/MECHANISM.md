# Materialized Task Runner: mechanism

[MaterializedTaskRunner](../materialized_task_runner/runner.py) owns authorization, unique run roots, child-process execution and the retained JSON evidence. [Materialization](../materialized_task_runner/task_runner_materializer.py) writes the explicitly supplied Python source into the run directory. `cleanup_runtime=False` keeps those generated modules for inspection. Each run’s source and payload hashes identify what was executed.

## Limits that matter

This executes arbitrary trusted Python. A fresh process is not a filesystem/network security boundary, and timeout handling does not establish isolation of descendant processes. There is no model connector or dependency solver.

## Demonstration contract

Input: A formatter package, run_workflow function and {"name":"avery"}.

Expected observation: A fresh interpreter returns {"greeting":"Hello Avery"}; source and result hashes remain in evidence.

The bundled example uses synthetic material. Its observed output establishes that bounded path, not every possible integration.
