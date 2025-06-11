#!/usr/bin/env python
# -*- coding: utf-8 -*-
import yaml
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait


from astarmiko.base import (
    ActivkaBackup,
    TimeMeasure,
    setup_config,
)

config_path = os.path.expanduser("~/astarmiko/YAML/confbackup.yaml")
if os.path.exists(config_path):
    setup_config(config_path)
else:
    print("The config_backup requires a configuration file confbackup.yaml in ~/astarmiko/YAML/")
    sys.exit()


from astarmiko.base import ac

with TimeMeasure() as tm:
    max_workers = 20
    mb = ActivkaBackup("activka_byname.yaml")

    with open(os.path.expanduser(ac.localpath) + "YAML/" + "config_backup.yaml") as fyaml:
        wholedict = yaml.safe_load(fyaml)

    todo = [(key, item) for key in wholedict.keys() for item in wholedict[key]]

    def config_save(mb, what):
        mb.save_config_backup(*what)

    with ThreadPoolExecutor(max_workers) as executor:
        futures = [executor.submit(config_save, mb, what) for what in todo]
        wait(futures)
