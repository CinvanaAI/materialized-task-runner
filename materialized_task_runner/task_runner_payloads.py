from __future__ import annotations


def validate_runtime_payload(runtime_payload: object) -> object:
    import json

    try:
        json.dumps(runtime_payload, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("Runtime payload must be JSON serializable.") from exc
    return runtime_payload
