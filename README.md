# Materialized Task Runner

Execute a saved trusted Python task without opening an authoring workbench. The runner writes package modules and a workflow into a fresh run directory, launches a separate interpreter, then retains the request, result and source hashes.

## Try it

Python 3.11 or newer.

```sh
python -m pip install -e .
python -m examples.demo
```

The complete [task](examples/task.json) contains a formatter module plus `run_workflow`; the [payload](examples/payload.json) contains `{"name":"avery"}`. The example proves that an unauthorized call is refused, then runs the authorized task and returns `{"greeting":"Hello Avery"}`. Temporary runtime files are removed; the printed evidence path remains.

## How it works

Separating task materialization from the authoring workbench makes saved work independently executable and reviewable. Read the [mechanism and implementation notes](docs/MECHANISM.md) for the specific boundaries and source links.

## Scope

This executes arbitrary trusted Python. A fresh process is not a filesystem/network security boundary, and timeout handling does not establish isolation of descendant processes. There is no model connector or dependency solver.

## Verify

`python -m pytest` runs the behavior tests (install `pytest` first). The runnable example above provides a separate first-use check.

MIT licensed; see [LICENSE.md](LICENSE.md). Origin and release boundaries are documented in [ORIGIN.md](ORIGIN.md) and [SECURITY.md](SECURITY.md).
## Inspect the example result

Open the [saved synthetic result](examples/captured-result.json) alongside its [input and demonstration](examples/demo.py). The result is from the bundled synthetic example; local machine paths and temporary run identifiers are excluded from public projections.
