from sort import sort_by_created_at


def get_first_jobstate_failure(jobstates):
    sorted_jobstates = sort_by_created_at(jobstates)

    for jobstate in sorted_jobstates:
        if jobstate["status"] == "failure" or jobstate["status"] == "error":
            return jobstate