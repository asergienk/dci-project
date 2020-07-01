import argparse
import csv
import json
import os
from dciclient.v1.api.context import build_signature_context
from dciclient.v1.api import job as dci_job
from dciclient.v1.api import file as dci_file
from dciclient.v1.api import topic as dci_topic
from dciclient.v1.api import product as dci_product
from dciclient.v1.api import jobstate as dci_jobstate
from datetime import datetime
from sort import sort_by_created_at
from jobstates import get_first_jobstate_failure
from printer import append_job_to_csv


context = build_signature_context()

def get_product_id_by_name(product_name):
   r = dci_product.list(context, where=f"name:{product_name}")
   product_id = r.json()["products"][0]["id"]
   return product_id


def get_files_for_jobstate(jobstate_id):
    r = dci_jobstate.get(context, id=jobstate_id, embed="files")
    r.raise_for_status()
    return r.json()["jobstate"]["files"]


def get_failed_jobs_for_product(product_id):
    num_of_jobs = dci_job.list(context,where=f"product_id:{product_id},status:failure", limit=1, offset=0).json()[
        "_meta"
    ]["count"]
    offset = 0
    limit = 100
    jobs = []
    while offset < num_of_jobs:
        jobs_list = dci_job.list(context,
            where=f"product_id:{product_id},status:failure",
            limit=limit,
            offset=offset,
            embed="remoteci,jobstates",
        ).json()["jobs"]
        jobs = jobs + jobs_list
        offset += limit
    return jobs


def get_content_for_file(file_id):
    r = dci_file.content(context, id=file_id)
    r.raise_for_status()
    return r.text


def enhance_job(job):
    first_jobstate_failure = get_first_jobstate_failure(job["jobstates"])
    #print(first_jobstate_failure)
    # if(first_jobstate_failure is None):
    #     print(job['jobstates'])
    job['stage_of_failure'] = first_jobstate_failure['comment']
    first_jobstate_failure_id = first_jobstate_failure["id"]
    files = get_files_for_jobstate(first_jobstate_failure_id)
    if not files:
        job["content_first_failure"] = "None"
    else:
        files_sorted = sort_by_created_at(files)
        first_file = files_sorted[0]
        content = get_content_for_file(first_file["id"])
        content_truncated = (
            (content[:186])
            if len(content) > 186
            else content
            )
        job["content_first_failure"] = content_truncated
    job['task_is_present'] = task_is_in_tasklist(job['id'], "include_tasks: {{ dci_config_dir }}/hooks/user-tests.yml")
    return job


def get_values(job):
   values = []
   values.append(job["id"])
   values.append(job['content_first_failure'])
   values.append(str(round((job["duration"] / 60), 2)))
   #values.append(job['duration'])
   values.append(job['stage_of_failure'])
   values.append(job["remoteci"]["name"])
   values.append(job['task_is_present'])
   values.append((job["created_at"])[:4])
   values.append("https://www.distributed-ci.io/jobs/" + job["id"])
   return values


def task_is_in_tasklist(job_id, task_name):
   r = dci_job.list_jobstates(context, id=job_id, limit=1000, offset=0, embed="files")
   jobstates = r.json()["jobstates"]
   for jobstate in jobstates:
       for item_file in jobstate["files"]:
           if item_file["name"] == task_name:
               return 1
   return 0


def remove_current_csv(file_name):
   os.remove(file_name)
 

def create_csv_file_with_headers(file_name, headers):
   with open(file_name, "w", newline="") as f:
       csvwriter = csv.writer(f)
       csvwriter.writerow(headers)


if __name__ == "__main__":
    csv_file_name = './jobs_7_1_2020.csv'

    remove_current_csv(csv_file_name)
    headers = ["Job ID", "Content", "Duration", "Stage of failure", "Remoteci name", "Is user-tests.yml present", "Year of creation", "Dashboard link"]
    
    create_csv_file_with_headers(csv_file_name, headers)
    product_id = get_product_id_by_name("RHEL")
    jobs = get_failed_jobs_for_product(product_id)

    for job in jobs:
        print(job['id'])
        job = enhance_job(job)
        job_values = get_values(job)
        append_job_to_csv(csv_file_name, job_values)
