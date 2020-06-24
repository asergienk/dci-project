import json
import csv
from dciclient.v1.api.context import build_signature_context
from dciclient.v1.api import job as dci_job
from dciclient.v1.api import file as dci_file


context = build_signature_context()


def get_jobstates_object(job_id):
    r = dci_job.list_jobstates(context, id=job_id, where='status:failure', limit=1000, offset=0, embed='files')
    return r


#from the list of failed tasks returns the id of a task that failed first
def get_failed_task_id(jobstates_object):
    task_id = jobstates_object.json()['jobstates'][-1]['files'][0]['id']
    return task_id


def get_failed_task_contents(task_id):
    res = dci_file.content(context, id=task_id)
    file_contents = res.text
    return file_contents


def get_comment(jobstates_object):
    comment = jobstates_object.json()['jobstates'][-1]['comment']
    return comment


def get_duration(job_id):
    sec_in_min = 60
    r = dci_job.get(context, id=job_id)
    duration_in_min = r.json()['job']['duration'] / sec_in_min
    return duration_in_min


def get_remoteci_name(job_id):
    r = dci_job.get(context, id=job_id, embed='remoteci')
    remoteci_name = r.json()['job']['remoteci']['name']
    return remoteci_name


failed_task_contents_truncated = (failed_task_contents[:186]) if len(failed_task_contents) > 186 else failed_task_contents


fields = ['Log content', 'Duration', 'Stage of failure', 'Remoteci name']
rows = [failed_task_contents_truncated, failed_job_duration, failed_comment, failed_remoteci_name]

with open('records.csv', 'w', newline='') as f:
    csvwriter = csv.writer(f)
    csvwriter.writerow(fields)
    csvwriter.writerow(rows)




