def check_if_file_is_in_files(files_for_jobstate_before_failure, file_name):
    for file in files_for_jobstate_before_failure:
        if file['name'] == file_name:
            return True
    return False


