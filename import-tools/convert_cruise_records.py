#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Modified: SJM 5/12/21 If vessel is not in metadata and vehicle is Alvin, define it as the Atlantis.

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

def convertCruiseRecord(vehicle, cruise_record_fn):
    with open(cruise_record_fn) as cruise_record_fp:
        cruises = json.load(cruise_record_fp)

        return_cruises = []

        if isinstance(cruises, (list,)):

            for cruise in cruises:
                logger.debug("Processing Cruise: " + cruise['cruise_id'])
                logger.debug(json.dumps(cruise, indent=2))
                try:

                    cruiseOBJ = {
                        '_id': {"$oid": cruise['id']},
                        'cruise_id': cruise['cruise_id'],
                        'start_ts': {"$date": cruise['start_ts']},
                        'stop_ts': {"$date": cruise['stop_ts']},
                        'cruise_location': cruise['cruise_location'],
                        'cruise_tags': cruise['cruise_tags'],
                        'cruise_hidden': True,
                        'cruise_access_list': []
                    }

                    if 'cruise_additional_meta' in cruise:
                       cruiseOBJ['cruise_additional_meta'] = cruise['cruise_additional_meta']
                    elif 'cruise_additional_meta' not in cruiseOBJ:
                        cruiseOBJ['cruise_additional_meta'] = {}

                    if 'cruise_name' in cruise:
                        cruiseOBJ['cruise_additional_meta']['cruise_name'] = cruise['cruise_name']
                    elif 'cruise_name' not in cruiseOBJ['cruise_additional_meta']:
                        cruiseOBJ['cruise_additional_meta']['cruise_name'] = ""

                    if 'cruise_pi' in cruise:
                        cruiseOBJ['cruise_additional_meta']['cruise_pi'] = cruise['cruise_pi']
                    elif 'cruise_pi' not in cruiseOBJ['cruise_additional_meta']:
                        cruiseOBJ['cruise_additional_meta']['cruise_pi'] = ""

                    if 'cruise_vessel' in cruise:
                        cruiseOBJ['cruise_additional_meta']['cruise_vessel'] = cruise['cruise_vessel']
                    elif 'cruise_vessel' not in cruiseOBJ['cruise_additional_meta']:
                        if vehicle == 'Alvin':
                            logger.warning("cruise_vessel not in metadata and vehicle is Alvin- Assigning vessel as the Atlantis")
                            print("cruise_vessel not in metadata and vehicle is Alvin- Assigning vessel as the Atlantis")
                            cruiseOBJ['cruise_additional_meta']['cruise_vessel'] = "RV Atlantis"
                        else:
                            cruiseOBJ['cruise_additional_meta']['cruise_vessel'] = ""

                    if 'cruise_description' in cruise:
                        cruiseOBJ['cruise_additional_meta']['cruise_description'] = cruise['cruise_description']
                    elif 'cruise_description' not in cruiseOBJ['cruise_additional_meta']:
                        cruiseOBJ['cruise_additional_meta']['cruise_description'] = ""

                    if 'cruise_participants' in cruise:
                       cruiseOBJ['cruise_additional_meta']['cruise_participants'] = cruise['cruise_participants']
                    elif 'cruise_participants' not in cruiseOBJ['cruise_additional_meta']:
                        cruiseOBJ['cruise_additional_meta']['cruise_participants'] = []

                    cruiseOBJ['cruise_additional_meta']['cruise_files'] = []
                    cruiseOBJ['cruise_additional_meta']['cruise_linkToR2R'] = ""

                    return_cruises.append(cruiseOBJ)
                except Exception as e:
                    logger.error("issue at: " + cruise['cruise_id'])
                    logger.error(e)
                    return None
        else:

            cruise = cruises

            logger.debug("Processing Cruise: " + cruise['cruise_id'])
            logger.debug(json.dumps(cruise, indent=2))

            try:
                cruiseOBJ = {
                    '_id': {"$oid": cruise['id']},
                    'cruise_id': cruise['cruise_id'],
                    'start_ts': {"$date": cruise['start_ts']},
                    'stop_ts': {"$date": cruise['stop_ts']},
                    'cruise_location': cruise['cruise_location'],
                    'cruise_tags': cruise['cruise_tags'],
                    'cruise_hidden': cruise['cruise_hidden'],
                    'cruise_access_list': [],
                    'cruise_additional_meta': {}
                }

                if 'cruise_additional_meta' in cruise:
                    cruiseOBJ['cruise_additional_meta'] = cruise['cruise_additional_meta']
                elif 'cruise_additional_meta' not in cruiseOBJ:
                    cruiseOBJ['cruise_additional_meta'] = {}

                if 'cruise_name' in cruise:
                    cruiseOBJ['cruise_additional_meta']['cruise_name'] = cruise['cruise_name']
                elif 'cruise_name' not in cruiseOBJ['cruise_additional_meta']:
                    cruiseOBJ['cruise_additional_meta']['cruise_name'] = ""

                if 'cruise_pi' in cruise:
                    cruiseOBJ['cruise_additional_meta']['cruise_pi'] = cruise['cruise_pi']
                elif 'cruise_pi' not in cruiseOBJ['cruise_additional_meta']:
                    cruiseOBJ['cruise_additional_meta']['cruise_pi'] = ""

                if 'cruise_vessel' in cruise:
                    cruiseOBJ['cruise_additional_meta']['cruise_vessel'] = cruise['cruise_vessel']
                elif 'cruise_vessel' not in cruiseOBJ['cruise_additional_meta']:
                    if vehicle == 'Alvin':
                        logger.warning("cruise_vessel not in metadata and vehicle is Alvin- Assigning vessel as the Atlantis")
                        cruiseOBJ['cruise_additional_meta']['cruise_vessel'] = "RV Atlantis"
                    else:
                        cruiseOBJ['cruise_additional_meta']['cruise_vessel'] = ""

                if 'cruise_description' in cruise:
                    cruiseOBJ['cruise_additional_meta']['cruise_description'] = cruise['cruise_description']
                elif 'cruise_description' not in cruiseOBJ['cruise_additional_meta']:
                    cruiseOBJ['cruise_additional_meta']['cruise_description'] = ""

                if 'cruise_participants' in cruise:
                    cruiseOBJ['cruise_additional_meta']['cruise_participants'] = cruise['cruise_participants']
                elif 'cruise_participants' not in cruiseOBJ['cruise_additional_meta']:
                    cruiseOBJ['cruise_additional_meta']['cruise_participants'] = []

                cruiseOBJ['cruise_additional_meta']['cruise_files'] = []
                cruiseOBJ['cruise_additional_meta']['cruise_linkToR2R'] = ""

                return_cruises.append(cruiseOBJ)

            except Exception as e:
                logger.error("issue at: " + cruise['cruise_id'])
                logger.error(e)
                return None

        return return_cruises

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='cruise record reformatter')
    parser.add_argument('-d', '--debug', action='store_true', help=' display debug messages')
    parser.add_argument('--vehicle', choices=['Alvin','Jason'], help=' vehicle used')
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

    new_cruise_record = convertCruiseRecord(args.vehicle, args.cruise_record_file)

    if(new_cruise_record):
        print(json.dumps(new_cruise_record, indent=2))
    else:
        logger.error("Nothing to return")
