# to do

6/25/2020
- create download_jobs_as_csv.py
- grab the product_id by name https://github.com/redhat-cip/dci-downloader/blob/master/dci_downloader/api.py#L18-L27
- commit and push 
- call and print jobs in csv file
- argparse: add name of csv file as a parameter
- save and use csv file from argparse instead of hardcoding it
- add parameters in CLI to choose the columns instead of hardcoding them (python download_jobs_as_csv.py output.csv id duration)


7/1/2020
- use embed jobstates on get jobs - done
- get first failed jobstate - done
- use first failed file - done
- fix tests for jobstate error - done
- add printer in printer.py or in csv.py
- clean your methods, files names, structure code correctly
- check if we get the proper jobs for RHEL (why do we have jobs for OCP)
- commit and push
- creating document (README.md) How to install, requirements (python version), how to run test




