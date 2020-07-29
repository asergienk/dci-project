import csv 
import os
import time


def remove_current_csv(file_name):
   os.remove(file_name)


def create_csv_file_with_headers(file_name, headers):
   with open(file_name, "w", newline="") as f:
       csvwriter = csv.writer(f)
       csvwriter.writerow(headers)


def append_job_to_csv(file_name, values):
   with open(file_name, "a", newline="") as f:
       csvwriter = csv.writer(f)
       csvwriter.writerow(values)

def create_csv_file_name():
   timestr = time.strftime("%Y%m%d-%H%M%S")
   csv_file_name = "jobs_" + timestr + ".csv"
   if os.path.exists(csv_file_name):
        remove_current_csv(csv_file_name)
   return csv_file_name