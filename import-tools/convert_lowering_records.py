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
        lowerings = json.load(lowering_record_fp)

        return_lowerings = []

        if isinstance(lowerings, (list,)):

            for lowering in lowerings:
                logger.debug("Processing Lowering: " + lowering['lowering_id'])
                logger.debug(json.dumps(lowering, indent=2))
                if vehicle == "Jason":
                    try:
                        loweringOBJ = {
                            '_id': {"$oid": lowering['id']},
                            'lowering_id': lowering['lowering_id'],
                            'start_ts': { "$date": lowering['start_ts']},
                            'stop_ts': { "$date": lowering['stop_ts']},
                            'lowering_location': lowering['lowering_location'],
                            'lowering_tags': lowering['lowering_tags'],
                            'lowering_hidden': True,
                            'lowering_access_list': []
                        }

                        if 'lowering_additional_meta' in lowering:
                            loweringOBJ['lowering_additional_meta'] = lowering['lowering_additional_meta']
                        elif 'lowering_additional_meta' not in loweringOBJ:
                            loweringOBJ['lowering_additional_meta'] = {}

                        if 'lowering_description' in lowering:
                            loweringOBJ['lowering_additional_meta']['lowering_description'] = lowering['lowering_description']
                        elif 'lowering_description' not in loweringOBJ['lowering_additional_meta']:
                            loweringOBJ['lowering_additional_meta']['lowering_description'] = ""

                        loweringOBJ['lowering_additional_meta']['lowering_files'] = []

                        return_lowerings.append(loweringOBJ)
                    except Exception as e:
                        logger.error("Issue with lowering: " + lowering['lowering_id'])
                        logger.error(e)
                        sys.exit(os.EX_DATAERR)
                elif vehicle == "Alvin":
                    try:
                        logger.debug("Processing Lowering: " + lowering['lowering_id'])
                        loweringOBJ = {
                            '_id': {"$oid": lowering['id']},
                            'lowering_id': lowering['lowering_id'].replace("AL", "Alvin-D"),
                            'start_ts': { "$date": lowering['start_ts']},
                            'stop_ts': { "$date": lowering['stop_ts']},
                            'lowering_location': lowering['lowering_location'],
                            'lowering_tags': lowering['lowering_tags'],
                            'lowering_hidden': True,
                            'lowering_access_list': []
                        }

                        if 'lowering_additional_meta' in lowering:
                            loweringOBJ['lowering_additional_meta'] = lowering['lowering_additional_meta']
                        elif 'lowering_additional_meta' not in loweringOBJ:
                            loweringOBJ['lowering_additional_meta'] = {}

                        if 'lowering_description' in lowering:
                            loweringOBJ['lowering_additional_meta']['lowering_description'] = lowering['lowering_description']
                        elif 'lowering_description' not in loweringOBJ['lowering_additional_meta']:
                            loweringOBJ['lowering_additional_meta']['lowering_description'] = ""

                        if 'lowering_pilot' in lowering:
                            loweringOBJ['lowering_additional_meta']['lowering_pilot'] = lowering['lowering_pilot']
                        elif 'lowering_pilot' not in loweringOBJ['lowering_additional_meta']:
                            loweringOBJ['lowering_additional_meta']['lowering_pilot'] = ""

                        if 'lowering_observers' in lowering:
                            loweringOBJ['lowering_additional_meta']['lowering_observers'] = lowering['lowering_observers']
                        elif 'lowering_observers' not in loweringOBJ['lowering_additional_meta']:
                            loweringOBJ['lowering_additional_meta']['lowering_observers'] = []

                        loweringOBJ['lowering_additional_meta']['lowering_files'] = []

                        return_lowerings.append(loweringOBJ)

                    except Exception as e:
                        logger.error("Issue with: " + lowering['lowering_id'])
                        logger.error(e)
                        sys.exit(os.EX_DATAERR)
        else:

            lowering = lowerings

            logger.debug("Processing Lowering: " + lowering['lowering_id'])
            logger.debug(json.dumps(lowering,indent=2))
            if vehicle == "Jason":
                try:
                    loweringOBJ = {
                        '_id': {"$oid": lowering['id']},
                        'lowering_id': lowering['lowering_id'],
                        'start_ts': { "$date": lowering['start_ts']},
                        'stop_ts': { "$date": lowering['stop_ts']},
                        'lowering_location': lowering['lowering_location'],
                        'lowering_tags': lowering['lowering_tags'],
                        'lowering_hidden': True,
                        'lowering_access_list': []
                    }

                    if 'lowering_additional_meta' in lowering:
                        loweringOBJ['lowering_additional_meta'] = lowering['lowering_additional_meta']
                    elif 'lowering_additional_meta' not in loweringOBJ:
                        loweringOBJ['lowering_additional_meta'] = {}

                    if 'lowering_description' in lowering:
                        loweringOBJ['lowering_additional_meta']['lowering_description'] = lowering['lowering_description']
                    elif 'lowering_description' not in loweringOBJ['lowering_additional_meta']:
                        loweringOBJ['lowering_additional_meta']['lowering_description'] = ""

                    loweringOBJ['lowering_additional_meta']['lowering_files'] = []

                    return_lowerings.append(loweringOBJ)

                except Exception as e:
                    logger.error("Issue with lowering: " + lowering['lowering_id'])
                    logger.error(e)
                    sys.exit(os.EX_DATAERR)

            elif vehicle == "Alvin":
                try:
                    logger.debug("Processing Lowering: " + lowering['lowering_id'])
                    loweringOBJ = {
                        '_id': {"$oid": lowering['id']},
                        'lowering_id': lowering['lowering_id'].replace("AL", "Alvin-D"),
                        'start_ts': { "$date": lowering['start_ts']},
                        'stop_ts': { "$date": lowering['stop_ts']},
                        'lowering_location': lowering['lowering_location'],
                        'lowering_tags': lowering['lowering_tags'],
                        'lowering_hidden': True,
                        'lowering_access_list': []
                    }

                    if 'lowering_additional_meta' in lowering:
                        loweringOBJ['lowering_additional_meta'] = lowering['lowering_additional_meta']
                    elif 'lowering_additional_meta' not in loweringOBJ:
                        loweringOBJ['lowering_additional_meta'] = {}

                    if 'lowering_description' in lowering:
                        loweringOBJ['lowering_additional_meta']['lowering_description'] = lowering['lowering_description']
                    elif 'lowering_description' not in loweringOBJ['lowering_additional_meta']:
                        loweringOBJ['lowering_additional_meta']['lowering_description'] = ""

                    if 'lowering_pilot' in lowering:
                        loweringOBJ['lowering_additional_meta']['lowering_pilot'] = lowering['lowering_pilot']
                    elif 'lowering_pilot' not in loweringOBJ['lowering_additional_meta']:
                        loweringOBJ['lowering_additional_meta']['lowering_pilot'] = ""

                    if 'lowering_observers' in lowering:
                        loweringOBJ['lowering_additional_meta']['lowering_observers'] = lowering['lowering_observers']
                    elif 'lowering_observers' not in loweringOBJ['lowering_additional_meta']:
                        loweringOBJ['lowering_additional_meta']['lowering_observers'] = []

                    loweringOBJ['lowering_additional_meta']['lowering_files'] = []

                    return_lowerings.append(loweringOBJ)
                except Exception as e:
                    logger.error("Issue with: " + lowering['lowering_id'])
                    logger.error(e)
                    sys.exit(os.EX_DATAERR)

        return return_lowerings

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

    if(new_lowering_record):
        print(json.dumps(new_lowering_record, indent=2))
    else:
        logger.error("Nothing to return")
