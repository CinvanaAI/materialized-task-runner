# Security

- `authorize=True` is mandatory.
- Package names must be valid contained Python module names.
- Payload and result must be JSON serializable.
- Execution occurs in a child Python process with a timeout and unique directory.
- Evidence stores hashes, status, result, and a bounded error tail.
- The runner does not provide syscall, filesystem, network, memory, or CPU isolation.

Only execute trusted embedded source, or place this runner inside an operating-system/container sandbox you control.
