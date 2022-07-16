#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Purpose: This script converts the lowering aux data records exported by the
#          at-sea instance of Sealog so that they can be quickly ingested by 
#          the Shoreside Sealog Server 
#
#   Usage: convert_aux_data_records.py [-d] --vehicle <Alvin|Jason> <original aux data record>
#
#  Author: Webb Pinner webbpinner@gmail.com
# Created: 2019-05-22
#
#   Modified: 2021-05-14 Scott McCue smccue@whoi.edu 
#   Corrected typo MedaCam -> MedeaCam in 'newImageSources' dict.


import json
import logging
import os
import re
import sys
import copy

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

imageSourceMap = {
    "Jason": {
        'framegrab01': 'SciCam',
        'framegrab02': 'BrowCam',
        'framegrab03': 'PilotCam',
        'framegrab04': 'AftCam',
    },
    "Alvin": {
        'framegrab01': 'SubSea1',
        'framegrab02': 'SubSea2',
        'framegrab03': 'SubSea3',
    },
}

def fixFramegrabImage(loweringID, data, vehicle):

    new_data = copy.copy(data)
    if data['data_name'] == 'filename':
        # Parse the filename
        name, ext = os.path.splitext(os.path.basename(data['data_value']))

        # Detect whether the order is <source>.<timestamp> or <timestamp>.<source>
        if re.match(r'^\d+_\d+$', name.split(".")[0]):
            timestamp, source = name.split(".", maxsplit=1)
        else:
            source, timestamp = os.path.splitext(name)

        source = imageSourceMap.get(vehicle, {}).get(source, source)

        new_data['data_value'] = os.path.join('/', loweringID, source, f'{source}.{timestamp}{ext}')
        logger.debug("new image fn: " + new_data['data_value'])

    elif data['data_name'] == 'camera_name':

        source = new_data['data_value']
        new_data['data_value'] = imageSourceMap.get(vehicle, {}).get(source, source)

        logger.debug("new image source: " + new_data['data_value'])

#    logger.debug(new_data)
#    new_data['_id'] = { "$oid": new_data['id'] }
#    del new_data['id']
    return new_data


def convertAuxDataRecords(aux_data_records_fn, vehicle):

    loweringID = aux_data_records_fn.split("/")[-1].split('_')[0]
    if vehicle == "Alvin":
        loweringID = loweringID.replace("AL", "Alvin-D")

    with open(aux_data_records_fn) as aux_data_records_fp:
        aux_data = json.load(aux_data_records_fp)

        return_aux_data = []

        if "statusCode" in aux_data:
            logger.error("Something went wrong in the shipboard data export")
            logger.error("Please take a look at file: " + aux_data_records_fn)

        else:
           for data in aux_data:

                new_data = copy.deepcopy(data)
                new_data['event_id'] = { "$oid": data['event_id'] }
                new_data['_id'] = { "$oid": data['id'] }
                del new_data['id']

                if new_data['data_source'] == "vehicleRealtimeFramegrabberData":
                    new_data['data_array'] = list(map(lambda data: fixFramegrabImage(loweringID, data, vehicle), new_data['data_array']))

                return_aux_data.append(new_data)

        return return_aux_data


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='aux_data record reformatter')
    parser.add_argument('-d', '--debug', action='store_true', help=' display debug messages')
    parser.add_argument('--vehicle', help='the vehicle used (Alvin or Jason)')
    parser.add_argument('aux_data_record_file', help=' original aux_data record to reformat')

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

    if not os.path.isfile(args.aux_data_record_file):
        logger.error(args.aux_data_record_file + " does not exist.")
        sys.exit(os.EX_DATAERR)

    new_aux_data_record = convertAuxDataRecords(args.aux_data_record_file, args.vehicle)

    if(new_aux_data_record):
        print(json.dumps(new_aux_data_record, indent=2))
    else:
        logger.error("Nothing to return")
