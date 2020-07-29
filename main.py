import json
import logging
import traceback
import sys
from dciclient.v1.api.context import build_dci_context
from dciclient.v1.api import job as dci_job
from dciclient.v1.api import file as dci_file
from dciclient.v1.api import product as dci_product
from dciclient.v1.api import jobstate as dci_jobstate
from datetime import datetime
from sort import sort_by_created_at
from jobstates import get_first_jobstate_failure, get_jobstate_before_failure
from csv_manipulations import (
    remove_current_csv,
    create_csv_file_name,
    create_csv_file_with_headers,
    append_job_to_csv,
)
from file_is_in_files import check_if_file_is_in_files


headers = [
    "Job_link",
    "Job_ID",
    "Error_Message",
    "Stage_of_Failure",
    "Is_user_text.yml",
    "Is_SUT.yml",
    "Is_install.yml",
    "Is_logs.yml",
    "Is_dci-rhel-cki",
]

context = build_dci_context()
LOG = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)


def get_product_id_by_name(product_name):
    r = dci_product.list(context, where=f"name:{product_name}")
    product_id = r.json()["products"][0]["id"]
    return product_id


def get_files_for_jobstate(jobstate_id):
    r = dci_jobstate.get(context, id=jobstate_id, embed="files")
    r.raise_for_status()
    return r.json()["jobstate"]["files"]


def get_jobstates_with_files(job_id):
    r = dci_job.list_jobstates(context, id=job_id, embed="files")
    r.raise_for_status()
    return r.json()["jobstates"]


def get_failed_jobs_for_product(product_id):
    num_of_jobs = dci_job.list(
        context, where=f"product_id:{product_id},status:failure", limit=1, offset=0
    ).json()["_meta"]["count"]
    offset = 0
    limit = 100
    jobs = []
    while offset < num_of_jobs:
        jobs_list = dci_job.list(
            context,
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


def change_content_to_wait_system_to_be_installed(
    job, files_for_jobstate_before_failure
):
    for file in files_for_jobstate_before_failure:
        if file["name"] == "Wait system to be installed":
            job["content"] = get_content_for_file(file["id"])
            return job["content"]
    return None


def enhance_job(job, first_jobstate_failure, files):
    files_sorted = sort_by_created_at(files)
    first_file = files_sorted[0]
    content = get_content_for_file(first_file["id"])
    job["content"] = content

    jobstate_before_failure = get_jobstate_before_failure(
        get_jobstates_with_files(job["id"])
    )
    files_for_jobstate_before_failure = get_files_for_jobstate(
        jobstate_before_failure["id"]
    )

    job["stage_of_failure"] = first_jobstate_failure["comment"]
    if job["stage_of_failure"] == "Gathering Facts":
        job["content"] = change_content_to_wait_system_to_be_installed(
            job, files_for_jobstate_before_failure
        )
        if job["content"] is None:
            job["content"] = content

    job["is_user_text"] = check_if_file_is_in_files(
        files_for_jobstate_before_failure, "/hooks/user-tests.yml",
    )
    job["is_sut"] = check_if_file_is_in_files(
        files_for_jobstate_before_failure, "include_tasks: sut.yml"
    )
    job["is_install"] = check_if_file_is_in_files(
        files_for_jobstate_before_failure, "include_tasks: install.yml"
    )
    job["is_logs"] = check_if_file_is_in_files(
        files_for_jobstate_before_failure, "include_tasks: logs.yml"
    )

    if "dci-rhel-cki" in files_sorted[0]["name"]:
        job["is_dci-rhel-cki"] = True
    else:
        job["is_dci-rhel-cki"] = False

    return job


def get_values(job):
    values = []
    values.append("https://www.distributed-ci.io/jobs/" + job["id"])
    values.append(job["id"])
    values.append(job["content"])
    values.append(job["stage_of_failure"])
    if job["is_user_text"]:
        values.append("1")
    else:
        values.append("0")
    if job["is_sut"]:
        values.append("1")
    else:
        values.append("0")
    if job["is_install"]:
        values.append("1")
    else:
        values.append("0")
    if job["is_logs"]:
        values.append("1")
    else:
        values.append("0")
    if job["is_dci-rhel-cki"]:
        values.append("1")
    else:
        values.append("0")
    return values


def test_data(job_id):
    csv_file_name = create_csv_file_name()
    create_csv_file_with_headers(csv_file_name, headers)
    try:
        r = dci_job.get(
            context, id=job_id, limit=1, offset=0, embed="remoteci,jobstates"
        )
        job = r.json()["job"]
        first_jobstate_failure = get_first_jobstate_failure(job["jobstates"])
        first_jobstate_failure_id = first_jobstate_failure["id"]
        files = get_files_for_jobstate(first_jobstate_failure_id)
        job = enhance_job(job, first_jobstate_failure, files)
        job_values = get_values(job)
        append_job_to_csv(csv_file_name, job_values)
    except Exception:
        # LOG.error(traceback.format_exc())
        sys.exit(1)


def api_main():
    csv_file_name = create_csv_file_name()
    create_csv_file_with_headers(csv_file_name, headers)

    product_id = get_product_id_by_name("RHEL")
    jobs = get_failed_jobs_for_product(product_id)

    for job in jobs:
        created_at = datetime.strptime(job["created_at"], "%Y-%m-%dT%H:%M:%S.%f")
        if created_at.year < 2020:
            continue

        if (
            job["remoteci"]["name"] == "westford-lab"
            or job["remoteci"]["name"] == "dci-rhel-agent-ci"
            or job["remoteci"]["name"] == "pctt-fdaencar"
            or job["remoteci"]["name"] == "p3ck-lab"
            or job["remoteci"]["name"] == "pctt-thomas-1"
        ):
            continue

        first_jobstate_failure = get_first_jobstate_failure(job["jobstates"])
        first_jobstate_failure_id = first_jobstate_failure["id"]
        files = get_files_for_jobstate(first_jobstate_failure_id)
        if not files:
            continue
        job = enhance_job(job, first_jobstate_failure, files)
        job_values = get_values(job)
        append_job_to_csv(csv_file_name, job_values)


if __name__ == "__main__":
    api_main()
