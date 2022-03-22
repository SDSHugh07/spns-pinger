#!/usr/bin/python

import datetime
import json

from core import probe_system_health, probe_system_disk, probe_system_memory

def evaluate_system_health():
    now = datetime.datetime.now()
    str_fname_out_root = 'spns_status_' + str(now).replace(' ', '_').replace('-', '').split('.')[0]
    str_fname_error_out_root = str_fname_out_root + "_ERROR"

    spns_health, dct_spns_probe_result, dct_spns_errors = probe_system_health()

    with open(str_fname_out_root + '.txt', 'w') as f_std_out:
        json.dump(dct_spns_probe_result, f_std_out, indent=4, sort_keys=True)

    if dct_spns_errors:
        with open(str_fname_error_out_root + '.txt', 'w') as f_std_out:
            json.dump(dct_spns_errors, f_std_out, indent=4, sort_keys=True)

    return spns_health, dct_spns_errors

def evaluate_system_disk():
    return probe_system_disk()

def evaluate_system_memory():
    return probe_system_memory()