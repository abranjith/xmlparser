import os
import json
import csv
from datetime import datetime

def path_exists(p):
    if not p:
        return False
    if os.path.isdir(p):
        return True
    return file_exists(p)

def file_exists(f):
    if not f:
        return False
    if os.path.isfile(f):
        return True
    #handle filename without extensions
    d = os.path.dirname(f)
    b = os.path.basename(f)
    if not(d and b):
        return False
    for fname in serve_files_in_dir(d, ext=False):
        if fname == b:
            return True
    return False

def serve_files_in_dir(p, ext=True):
    if not os.path.isdir(p):
        return
    for f in os.listdir(p):
        if os.path.isfile(os.path.join(p, f)):
            if ext:
                yield f
            else:
                yield os.path.splitext(f)[0]

def load_json_from_path(file_path):
    with open(file_path) as fd:
        json_ = json.load(fd)
    return json_

def get_current_timestamp_as_str(pattern=None):
    if pattern is None:
        pattern = "%m%d%Y%H%M%S%f"
    ts = datetime.now()
    return ts.strftime(pattern)

def write_to_csv(records, header, output_file_path):
    with open(output_file_path, "w", newline="") as fd:
        writer = csv.DictWriter(fd, fieldnames=header)
        writer.writeheader()
        writer.writerows(records)

def pretty_print_records(records):
    if not records:
        return
    results = []
    for r in records:
        rec = None
        if isinstance(r, dict):
            rec_list = [(str(k) + "=" + str(v)) for k,v in r.items()]
            rec = ",".join(rec_list)
        if rec is None:
            rec = str(r)
        results.append(rec)
    res_str = (os.linesep).join(results)
    print(res_str)
