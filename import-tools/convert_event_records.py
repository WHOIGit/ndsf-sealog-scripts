#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Purpose: This script converts the lowering event records exported by the at-
#          sea instance of Sealog so that they can be quickly ingested by the
#          Shoreside Sealog Server 
#
#   Usage: convert_event_records.py [-d] --vehicle <Alvin|Jason> <original event record>
#
#  Author: Webb Pinner webbpinner@gmail.com
# Created: 2019-05-22

import json
import logging
import os
import sys
import copy
import datetime
import time

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

def convertEventRecords(event_records_fn):

    loweringID = event_records_fn.split("/")[-1].split('_')[0].replace("AL", "Alvin-D")
    with open(event_records_fn) as event_records_fp:
        events = json.load(event_records_fp)

        return_events = []
        if "statusCode" in events:
          logger.error("Something went wrong in the shipboard data export")
          logger.error("Please take a look at file: " + event_records_fn)

        else:
            for event in events:

                try:
                    new_event = copy.deepcopy(event)

                    logger.debug(json.dumps(new_event, indent=2))

                    if new_event['event_value'] == "SuliusCam" or new_event['event_value'] == "SulisCam" :
                        new_event['event_options'][0]['event_option_value'] = os.path.join('/', loweringID, 'SulisCam', 'SulisCam.' + new_event['event_options'][0]['event_option_value'].split('_')[-1][:8] + "_" + new_event['event_options'][0]['event_option_value'].split('_')[-1][8:14] + '000' + new_event['event_options'][0]['event_option_value'].split('_')[-1][14:])
                        logger.debug(new_event['event_options'][0]['event_option_value'])

                    new_event['_id'] = {"$oid": new_event['id']}
                    del new_event['id']

                    new_event['ts'] = {"$date": new_event['ts']}
                    return_events.append(new_event)
                except:
                    logger.error("Could not parse event:" + json.dumps(event))

        return return_events

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='event record reformatter')
    parser.add_argument('-d', '--debug', action='store_true', help=' display debug messages')
    parser.add_argument('--vehicle', help='the vehicle used (Alvin or Jason)')
    parser.add_argument('event_record_file', help=' original event record to reformat')

    args = parser.parse_args()

    # Turn on debug mode
    if args.debug:
        logger.info("Setting log level to DEBUG")
        logger.setLevel(logging.DEBUG)
    
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    if args.vehicle not in vehicles:
        logger.error("Vehicle must be one of: " + ', '.join(vehicles))
        sys.exit(os.EX_DATAERR)

    if not os.path.isfile(args.event_record_file):
        logger.error(args.event_record_file + " does not exist.")
        sys.exit(os.EX_DATAERR)

    new_event_record = convertEventRecords(args.event_record_file)

    if(new_event_record):
        print(json.dumps(new_event_record, indent=2))
    else:
        logger.error("No events to return")
