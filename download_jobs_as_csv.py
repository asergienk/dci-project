import argparse
import csv
import json
from dciclient.v1.api.context import build_signature_context
from dciclient.v1.api import job as dci_job
from dciclient.v1.api import file as dci_file
from dciclient.v1.api import topic as dci_topic


context = build_signature_context()

#positional: just pass the values separated by spaces
#optional: name of the parameter and value in 'help' separated by spaces
parser = argparse.ArgumentParser()

parser.add_argument('job_id', help="Failed Job ID")
parser.add_argument('file_name', help="Csv file name")
parser.add_argument('--col1', help="content")
parser.add_argument('--col2', help="duration")
parser.add_argument('--col3', help="comment")
parser.add_argument('--col4', help="remoteci")

args = parser.parse_args()


def get_product_id_by_name(product_name):
    r = dci_topic.list(context, where=f"name:{product_name}")
    product_id = r.json()["topics"][0]["product_id"]
    return product_id

 
def get_failed_job_ids(callback, product_id):
    num_of_failed_jobs = dci_job.list(
        context, where=f"product_id:{product_id},status:failure", limit=1, offset=0
    ).json()["_meta"]["count"]
    offset = 0
    limit = 100
    while offset < num_of_failed_jobs:
        jobs_list = dci_job.list(
            context,
            where=f"product_id:{product_id},status:failure",
            limit=limit,
            offset=offset,
        ).json()["jobs"]
        for job in jobs_list:
            callback(job)
        offset += limit
 
 
def print_to_csv(job):
    job_id = job["id"]
    with open("job_ids.csv", "a", newline="") as f:
        csvwriter = csv.writer(f)
        csvwriter.writerow([job_id])


def get_first_failed_jobstate(job_id):
    r = dci_job.list_jobstates(
        context, id=job_id, where="status:failure", limit=1000, offset=0, embed="files"
    )
    jobstate = r.json()["jobstates"][-1]
    return jobstate


# from the list of failed tasks returns the id of a task that failed first
def get_failed_task_id(jobstate):
    task_id = jobstate["files"][0]["id"]
    return task_id


def get_failed_task_contents(task_id):
    res = dci_file.content(context, id=task_id)
    file_contents = res.text
    return file_contents


def get_comment(jobstate):
    comment = jobstate["comment"]
    return comment


def get_duration(job_id):
    sec_in_min = 60
    r = dci_job.get(context, id=job_id)
    duration_in_min = r.json()["job"]["duration"] / sec_in_min
    return duration_in_min


def get_remoteci_name(job_id):
    r = dci_job.get(context, id=job_id, embed="remoteci")
    remoteci_name = r.json()["job"]["remoteci"]["name"]
    return remoteci_name


product_name = "RHEL-8.2"
product_id = get_product_id_by_name(product_name)
get_failed_job_ids(print_to_csv, product_id)


first_failed_jobstate = get_first_failed_jobstate(args.job_id)
failed_task_id = get_failed_task_id(first_failed_jobstate)
failed_task_contents = get_failed_task_contents(failed_task_id)
failed_comment = get_comment(first_failed_jobstate)
failed_job_duration = get_duration(args.job_id)
failed_remoteci_name = get_remoteci_name(args.job_id)

failed_task_contents_truncated = (
    (failed_task_contents[:186])
    if len(failed_task_contents) > 186
    else failed_task_contents
)


headers = []
rows = []
if args.col1:
    headers.append("Log content")
    rows.append(failed_task_contents_truncated)
if args.col2:
    headers.append("Duration")
    rows.append(failed_job_duration)
if args.col3:
    headers.append("Stage of failure")
    rows.append(failed_comment)
if args.col4:
    headers.append("Remoteci name")
    rows.append(failed_remoteci_name)
with open(args.file_name, "w", newline="") as f:
    csvwriter = csv.writer(f)
    csvwriter.writerow(headers)
    csvwriter.writerow(rows)
    


