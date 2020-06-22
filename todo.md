# to do

- init a git repo 
- ignore remoteci.rc & job.json git ignore
- create commit 
- from Shub's document: duration, status, look at jos states
- for each job we need list of the job states(new, running, pre-run, post-run, success, failure, killed, error)

- ignore vscode venv folders, json










# Notes
1. To filter all the jobs based on the product name (we need only RHEL) I need to access 'topic' key to get to the 'name' key. But in the list of valid keys there are no such keys
{"valid_keys":
["comment",
"status",
"topic_id_secondary",
"remoteci_id",
"state",
"previous_job_id",
"created_at",
"tag",
"updated_at",
"update_previous_job_id
team_id",
"etag",
"user_agent",
"topic_id",
"duration",
"client_version",
"id",
"product_id"]}

2. Listing endpoints: sort, limit, offset, where, embed

3. from dciclient.v1.api import job as dci_job

r = dci_job.list_jobstates(context, id="cfe77482-d424-49f3-bff7-d0ca46937d02", limit=1000, offset=0)

jobs = r.json()

print(jobs)

for list_jobstates method for the particular job the output is: list_jobstates_all.json
if we want to limit to some particular status, need to have where="status:failure"
