# to do

- init a git repo 
- ignore remoteci.rc & job.json git ignore
- create commit 
- from Shub's document: duration, status, look at jos states
- for each job we need list of the job states(new, running, pre-run, post-run, success, failure, killed, error)
- ignore vscode venv folders, json

- create download_jobs_as_csv.py
- grab the product_id by name https://github.com/redhat-cip/dci-downloader/blob/master/dci_downloader/api.py#L18-L27
- commit and push 
- call and print jobs in csv file
- argparse: add name of csv file as a parameter
- save and use csv file from argparse instead of hardcoding it
- add parameters in CLI to choose the columns insteads of hardcoding them (python download_jobs_as_csv.py output.csv id duration)









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
