#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Purpose: This script converts the lowering record exported by the at-sea
#          instance of Sealog so that it can be quickly ingested by the
#          Shoreside Sealog Server 
#
#   Usage: convert_lowering_records.py [-d] --vehicle <Alvin|Jason> <original lowering record>
#
#  Author: Webb Pinner webbpinner@gmail.com
# Created: 2019-05-22

import json
import logging
import os
import sys

vehicles = ["Alvin", "Jason"]

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

def convertLoweringRecord(lowering_record_fn, vehicle):
    with open(lowering_record_fn) as lowering_record_fp:
        lowering = json.load(lowering_record_fp)
        assert not isinstance(lowering, list)  # support for a list of lowerings is removed

        # Convert fields to native Mongo types
        lowering['_id'] = { "$oid": lowering['id'] }
        del lowering['id']

        for ts in ['start_ts', 'stop_ts']:
            lowering[ts] = { "$date": lowering[ts] }

        # Reset the access control and hide by default
        lowering['lowering_access_list'] = []
        lowering['lowering_hidden'] = True

        if vehicle == "Alvin":
            lowering['lowering_id'] = lowering['lowering_id'].replace('AL', 'Alvin-D')

        return lowering


if __name__ == '__main__':

    import argparse

#    global vehicles

    parser = argparse.ArgumentParser(description='lowering record reformatter')
    parser.add_argument('-d', '--debug', action='store_true', help=' display debug messages')
    parser.add_argument('--vehicle', choices=['Alvin','Jason'], help='the vehicle used (Alvin or Jason)')
    parser.add_argument('lowering_record_file', help=' original lowering record to reformat')


    args = parser.parse_args()

    # Turn on debug mode
    if args.debug:
        logger.info("Setting log level to DEBUG")
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    if not os.path.isfile(args.lowering_record_file):
        logger.error(args.lowering_record_file + " does not exist.")
        sys.exit(os.EX_DATAERR)

    if args.vehicle not in vehicles:
        logger.error("Vehicle must be one of: " + ', '.join(vehicles))
        sys.exit(os.EX_DATAERR)

    new_lowering_record = convertLoweringRecord(args.lowering_record_file, args.vehicle)

    if new_lowering_record:
        print(json.dumps(new_lowering_record, indent=2))
    else:
        logger.error("Nothing to return")
