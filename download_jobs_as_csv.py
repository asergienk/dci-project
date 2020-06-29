import argparse
import csv
import json
from dciclient.v1.api.context import build_signature_context
from dciclient.v1.api import job as dci_job
from dciclient.v1.api import file as dci_file
from dciclient.v1.api import topic as dci_topic
from dciclient.v1.api import product as dci_product


context = build_signature_context()


# positional: 'job_id', 'file_name'. Pass the values separated by spaces
# optional: all that start with --. Pass name of the parameter ('--col1') and value ('content') separated by spaces, except for '--task_name' pass the actual task_name from dashboard
parser = argparse.ArgumentParser()

parser.add_argument("product_name", help="Product name")
parser.add_argument("job_id", help="Failed Job ID")
parser.add_argument("file_name", help="Csv file name")
parser.add_argument("--col1", help="content")
parser.add_argument("--col2", help="duration")
parser.add_argument("--col3", help="comment")
parser.add_argument("--col4", help="remoteci")
parser.add_argument("--task_name", help="task name")

args = parser.parse_args()


def task_is_in_tasklist(job_id, task_name):
    r = dci_job.list_jobstates(context, id=job_id, limit=1000, offset=0, embed="files")
    jobstates = r.json()["jobstates"]
    for jobstate in jobstates:
        for item_file in jobstate["files"]:
            if item_file["name"] == task_name:
                return 1
    return 0


def get_product_id_by_name(product_name):
    r = dci_product.list(context, where=f"name:{product_name}")
    product_id = r.json()["products"][0]["id"]
    return product_id


def get_failed_job_ids(callback, product_id):
    num_of_failed_jobs = dci_job.list(
        context, where=f"product_id:{product_id},status:failure", limit=1, offset=0
    ).json()["_meta"]["count"]
    offset = 0
    limit = 100
    mode = "w"
    while offset < num_of_failed_jobs:
        jobs_list = dci_job.list(
            context,
            where=f"product_id:{product_id},status:failure",
            limit=limit,
            offset=offset,
        ).json()["jobs"]
        for job in jobs_list:
            callback(job, mode)
            mode = "a"
        offset += limit
        


def print_to_csv(job, mode):
    job_id = job["id"]
    with open("job_ids.csv", mode, newline="") as f:
        csvwriter = csv.writer(f)
        csvwriter.writerow([job_id])


def get_first_failed_jobstate(job_id):
    r = dci_job.list_jobstates(
        context, id=job_id, where="status:failure", limit=1000, offset=0, embed="files"
    )
    jobstate = r.json()["jobstates"][-1]
    return jobstate


def get_first_failed_task_id(jobstate):
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


def add_header_and_row(header, row):
    headers.append(header)
    rows.append(row)


product_id = get_product_id_by_name(args.product_name)
get_failed_job_ids(print_to_csv, product_id)


first_failed_jobstate = get_first_failed_jobstate(args.job_id)
task_id = get_first_failed_task_id(first_failed_jobstate)
task_contents = get_failed_task_contents(task_id)
comment = get_comment(first_failed_jobstate)
job_duration = get_duration(args.job_id)
remoteci_name = get_remoteci_name(args.job_id)
task_is_present = task_is_in_tasklist(args.job_id, args.task_name)

task_contents_truncated = (
    (task_contents[:186])
    if len(task_contents) > 186
    else task_contents
)


headers = []
rows = []
if args.col1:
    add_header_and_row("Log content", task_contents_truncated)
if args.col2:
    add_header_and_row("Duration", job_duration)
if args.col3:
    add_header_and_row("Stage of failure", comment)
if args.col4:
    add_header_and_row("Remoteci name", remoteci_name)
if args.task_name:
    add_header_and_row("Task is present", task_is_present)


with open(args.file_name, "w", newline="") as f:
    csvwriter = csv.writer(f)
    csvwriter.writerow(headers)
    csvwriter.writerow(rows)

