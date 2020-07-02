import csv 
import os


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