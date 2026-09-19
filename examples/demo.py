import json
import tempfile
from pathlib import Path
from materialized_task_runner import MaterializedTaskRunner

examples=Path(__file__).parent
task=json.loads((examples/'task.json').read_text())
payload=json.loads((examples/'payload.json').read_text())
root=Path(tempfile.mkdtemp(prefix='materialized-demo-'))
runner=MaterializedTaskRunner(root)
try:
    runner.run(task,payload,authorize=False)
except PermissionError:
    refused=True
else:
    raise AssertionError('Unauthorized task ran')
evidence=runner.run(task,payload,authorize=True)
assert evidence['result']=={'greeting':'Hello Avery'}
assert not any((root/'runs').iterdir())
print(json.dumps({'unauthorized_refused':refused,'status':evidence['status'],'result':evidence['result'],'runtime_cleaned':True,'evidence_path':evidence['evidence_path']},indent=2))
