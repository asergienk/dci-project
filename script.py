import json
from dciclient.v1.api.context import build_signature_context
from dciclient.v1.api import job as dci_job

context = build_signature_context()


r = dci_job.list(context, where="status:failure", limit=20, offset=0, embed='topic,remoteci')
print(r.text)

jobs = r.json()['jobs']
print(r.json()['_meta']['count'])

print(len(jobs))

print(json.dumps(jobs[0], indent=4, sort_keys=True))

