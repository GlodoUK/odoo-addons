import datetime
import re
import glob
import os
import logging


def scan_for_files(process_path, done_path, append_date_to_done_path=True):
    result = []

    if append_date_to_done_path:
        now = datetime.datetime.now()

        done_path = os.path.join(
            done_path, now.strftime("%Y"), now.strftime("%m"), now.strftime("%d")
        )

    create_path = not os.path.exists(done_path)

    for current_file in glob.glob(process_path):
        if create_path:
            os.makedirs(done_path, exist_ok=True)
            create_path = False

        # rename file
        basename = os.path.basename(current_file)
        process_file = os.path.join(done_path, basename)

        try:
            os.rename(current_file, process_file)
            result.append(process_file)
        except Exception:
            logging.info("Failed to rename file: %s", current_file)

    return result


def is_valid_glob(pattern):
    """
    Rudimentary glob pattern sanity checking.
    """
    if not pattern:
        return (False, ["Not pattern supplied"])

    regex_at_least_one_pattern = r"((?<!\\)\[\w\-\w(?<!\\)\]|\*)"

    tests = [
        (
            not re.search(regex_at_least_one_pattern, pattern),
            "No wildcard or range specified. This will only match a single"
            " file/directory. This is not supported.",
        )
    ]

    matched_tests = [t[1] for t in tests if t[0]]

    if matched_tests:
        return (False, ",".join(matched_tests))

    return (True, [])
