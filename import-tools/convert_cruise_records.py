#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import sys

# logging level
LOG_LEVEL = logging.INFO

# create logger
logger = logging.getLogger(__file__ )
logger.setLevel(LOG_LEVEL)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(LOG_LEVEL)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

def convertCruiseRecord(cruise_record_fn):
    with open(cruise_record_fn) as cruise_record_fp:
        cruise = json.load(cruise_record_fp)
        assert not isinstance(cruise, list)  # support for a list of cruises is removed

        # Convert fields to native Mongo types
        cruise['_id'] = { "$oid": cruise['id'] }
        del cruise['id']

        for ts in ['start_ts', 'stop_ts']:
            cruise[ts] = { "$date": cruise[ts] }

        # Reset the access control and hide by default
        cruise['cruise_access_list'] = []
        cruise['cruise_hidden'] = True
        return cruise


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='cruise record reformatter')
    parser.add_argument('-d', '--debug', action='store_true', help=' display debug messages')
    parser.add_argument('cruise_record_file', help=' original cruise record to reformat')

    args = parser.parse_args()

    # Turn on debug mode
    if args.debug:
        logger.info("Setting log level to DEBUG")
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    if not os.path.isfile(args.cruise_record_file):
        logger.error(args.cruise_record_file + " does not exist.")
        sys.exit(0)

    new_cruise_record = convertCruiseRecord(args.cruise_record_file)

    if new_cruise_record:
        print(json.dumps(new_cruise_record, indent=2))
    else:
        logger.error("Nothing to return")
