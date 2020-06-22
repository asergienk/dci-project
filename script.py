import json
from dciclient.v1.api.context import build_signature_context
from dciclient.v1.api import job as dci_job
from dciclient.v1.api import file as dci_file

context = build_signature_context()


#from the list of failed tasks takes the id of a task that failed first; takes job_id
def get_failed_task_id(job_id):
    r = dci_job.list_jobstates(context, id=job_id, where="status:failure", limit=1000, offset=0, embed='files')
    task_id = r.json()['jobstates'][-1]['files'][0]['id']
    return task_id


#outputs the contents of the task failure; takes task_id from get_failed_task_id function
def get_failed_task_contents(task_id):
    res = dci_file.content(context, id=task_id)
    file_contents = res.text
    print(file_contents)


#gets comment(failure stage) of the failed task
def get_comment(job_id):
    r = dci_job.list_jobstates(context, id=job_id, where="status:failure", limit=1000, offset=0, embed='files')
    comment = r.json()['jobstates'][-1]['comment']
    return comment




# #gets duration of the job
# def get_duration(job_id):






# #writing to a file
# with open('test.json', 'w') as f:
#     json.dump(jobs, f, indent=2)

