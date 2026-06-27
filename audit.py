import json
import os

AUDIT_LOG_FILE = "audit_log.json"
SUBMISSIONS_FILE = "submissions.json"


def _read_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r") as f:
        return json.load(f)


def _write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def append_log(entry: dict):
    log = _read_json(AUDIT_LOG_FILE, [])
    log.append(entry)
    _write_json(AUDIT_LOG_FILE, log)


def save_submission(record: dict):
    submissions = _read_json(SUBMISSIONS_FILE, {})
    submissions[record["content_id"]] = record
    _write_json(SUBMISSIONS_FILE, submissions)


def get_log() -> list:
    return _read_json(AUDIT_LOG_FILE, [])
