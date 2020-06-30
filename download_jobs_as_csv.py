import argparse
import csv
import json
import os
from dciclient.v1.api.context import build_signature_context
from dciclient.v1.api import job as dci_job
from dciclient.v1.api import file as dci_file
from dciclient.v1.api import topic as dci_topic
from dciclient.v1.api import product as dci_product
 
 
context = build_signature_context()
 
 
# # positional: 'job_id', 'file_name'. Pass the values separated by spaces
# # optional: all that start with --. Pass name of the parameter ('--col1') and value ('content') separated by spaces, except for '--task_name' pass the actual task_name from dashboard
# parser = argparse.ArgumentParser()
 
# parser.add_argument("product_name", help="Product name")
# parser.add_argument("file_name", help="Csv file name")
# parser.add_argument("--col1", help="content")
# parser.add_argument("--col2", help="duration")
# parser.add_argument("--col3", help="comment")
# parser.add_argument("--col4", help="remoteci")
# parser.add_argument("--task_name", help="task name")
 
# args = parser.parse_args()
 
 
 
def main():
   print('main')
 
 
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
  
 
#if the job has no tasks returns None
def get_first_failed_bucket(job_id):
   r = dci_job.list_jobstates(
       context, id=job_id, where="status:failure", limit=1000, offset=0, embed="files"
   )
   try:
       bucket = r.json()["jobstates"][-1]
   except IndexError:
       return "None"
   return bucket
 
 
#if the job has no files returns None
def get_first_failed_task_id(bucket):
   if bucket == "None":
       return "None"
   try:
       #sorting task by created_at
       first_bucket_task = bucket['files'][0]
       earliest_time = first_bucket_task['created_at']
       earliest_task_id = first_bucket_task['id']
       for task in bucket['files']:
           if task['created_at'] < earliest_time:
               earliest_time = task['created_at']
               earliest_task_id = task['id']
   except IndexError:
       return "None"
   return earliest_task_id
 
 
def get_failed_task_contents(task_id):
   if task_id == "None":
       return "None"
   res = dci_file.content(context, id=task_id)
   file_contents = res.text
   return file_contents
 
 
def get_comment(bucket):
   if bucket == "None":
       return "None"
   comment = bucket["comment"]
   return comment

 
def get_jobs(where, limit, offset, embed):
   return dci_job.list(
       context, where=where, limit=limit, offset=offset, embed=embed
   ).json()
 

def get_jobs_for_product(product_id):
   num_of_jobs = get_jobs(
       where=f"product_id:{product_id}", limit=1, offset=0, embed="remoteci"
   )["_meta"]["count"]
   offset = 0
   limit = 100
   jobs = []
   while offset < num_of_jobs:
       jobs_list = get_jobs(
           where=f"product_id:{product_id}",
           limit=limit,
           offset=offset,
           embed="remoteci"
       )["jobs"]
       jobs = jobs + jobs_list
       offset += limit
   return jobs      
 
 
def get_values(job):
   values = []
   values.append(job["id"])
   values.append(job['task_content'])
   values.append(str(round((job["duration"] / 60), 2)))
   values.append(job['bucket_comment'])
   values.append(job["remoteci"]["name"])
   values.append(job['task_is_present'])
   values.append((job["created_at"])[:4])
   values.append("https://www.distributed-ci.io/jobs/" + job["id"])
   return values
 
 
def append_job_to_csv(file_name, values):
   with open(file_name, "a", newline="") as f:
       csvwriter = csv.writer(f)
       csvwriter.writerow(values)
 
 
def remove_current_csv(file_name):
   os.remove(file_name)
 

def create_csv_file_with_headers(file_name, headers):
   with open(file_name, "w", newline="") as f:
       csvwriter = csv.writer(f)
       csvwriter.writerow(headers)
 

def enhance_job(job):
   task_id = get_first_failed_task_id(get_first_failed_bucket(job['id']))
   task_contents = get_failed_task_contents(task_id)
   task_contents_truncated = (
       (task_contents[:186])
       if len(task_contents) > 186
       else task_contents
       )
   job['task_content'] = task_contents_truncated
   job['bucket_comment'] = get_comment(get_first_failed_bucket(job['id']))
   job['task_is_present'] = task_is_in_tasklist(job['id'], "include_tasks: {{ dci_config_dir }}/hooks/user-tests.yml")
   return job

 
 
if __name__ == "__main__":
   csv_file_name = './jobs_6_30_2020.csv'
 
   remove_current_csv(csv_file_name)
   headers = ["Job ID", "Content", "Duration", "Stage of failure", "Remoteci name", "Is user-tests.yml present", "Year of creation", "Dashboard link"]
   create_csv_file_with_headers(csv_file_name, headers)
 
   product_id = get_product_id_by_name("RHEL")
 
   # job = get_jobs(
   #             where=f"product_id:{product_id}",
   #             limit=1,
   #             offset=0,
   #             embed="remoteci,files"
   #         )["jobs"][0]
 
   for job in get_jobs_for_product(product_id):
       if job['status'] != 'failure':
           continue
 
       job = enhance_job(job)
       job_values = get_values(job)
       assert len(job_values) == len(headers)
       append_job_to_csv(csv_file_name, job_values)
 
 


# headers = []
# rows = []
# if args.col1:
#     add_header_and_row("Log content", task_contents_truncated)
# if args.col2:
#     add_header_and_row("Duration", job_duration)
# if args.col3:
#     add_header_and_row("Stage of failure", comment)
# if args.col4:
#     add_header_and_row("Remoteci name", remoteci_name)
# if args.task_name:
#     add_header_and_row("Task is present", task_is_present)
 
 
# with open(args.file_name, "w", newline="") as f:
#     csvwriter = csv.writer(f)
#     csvwriter.writerow(headers)
#     csvwriter.writerow(rows)
