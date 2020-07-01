import csv 

def append_job_to_csv(file_name, values):
   with open(file_name, "a", newline="") as f:
       csvwriter = csv.writer(f)
       csvwriter.writerow(values)