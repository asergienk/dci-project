def check_if_task_is_in_tasklist(jobstates, task_name):
    flag = 0
    for jobstate in jobstates:
        if jobstate['status'] != 'failure':
            if not jobstate['files']:
                    continue
            for file in jobstate['files']:
                flag = 1
                if file['name'] == task_name:
                    return 1
        if flag == 1:
           return 0
