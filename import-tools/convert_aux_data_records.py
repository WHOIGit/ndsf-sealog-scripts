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

alvinCoordDataFields = ['alvin_x', 'alvin_y']
navDataFields = ['latitude', 'longitude', 'depth', 'altitude', 'heading', 'pitch', 'roll']

oldImageNames = {
    "Jason": [
        'Framegrabber 1',
        'Framegrabber 2',
        'Framegrabber 3',
        'Framegrabber 4',
        'Sci',
        'Brow',
        'Pilot',
        'Aft',
        'Medea',
        'Deck'
    ],
    "Alvin": [
        'Framegrabber 1',
        'Framegrabber 2',
        'Framegrabber 3'
    ]
}

oldImageSources = {
    "Jason": [
        'framegrab01',
        'framegrab02',
        'framegrab03',
        'framegrab04',
        'Sci',
        'Brow',
        'Pilot',
        'Aft',
        'Medea',
        'Deck'
    ],
    "Alvin": [
        'framegrab01',
        'framegrab02',
        'framegrab03'
    ]
}

newImageSources = {
    "Jason": [
        'SciCam',
        'BrowCam',
        'PilotCam',
        'AftCam',
        'PilotCam',
        'BrowCam',
        'SciCam',
        'AftCam',
        'MedeaCam',
        'DeckCam'
    ],
    "Alvin": [
        'SubSea1',
        'SubSea2',
        'SubSea3'
    ]
}

def fixFramegrabImage(loweringID, data, vehicle):

    new_data = copy.copy(data)
    if data['data_name'] == 'filename':

        ext = data['data_value'].split('.')[-1]
        source = data['data_value'].split('.')[-2]
        timestamp = data['data_value'].split('/')[-1].split('.')[-3]
        try:
            index = oldImageSources[vehicle].index(source)
            new_data['data_value'] = os.path.join('/', loweringID, newImageSources[vehicle][index], '.'.join([newImageSources[vehicle][index],timestamp,ext]))
        except:
            logger.info("Camera name: " + source + " not found in lookup table.")
            new_data['data_value'] = os.path.join('/', loweringID, source, '.'.join([source,timestamp,ext]))

        logger.debug("new image fn: " + new_data['data_value'])

    elif data['data_name'] == 'camera_name':

        try:
            index = oldImageNames[vehicle].index(data['data_value'])
            new_data['data_value'] = newImageSources[vehicle][index]
        except:
            logger.info("Camera name: " + data['data_value'] + " not found in lookup table.")
            new_data['data_value'] = data['data_value']

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

                if new_data['data_source'] == "alvinRealtimeNavData":

                    new_alvin_data = copy.deepcopy(new_data)
                    new_alvin_data['data_source'] = "vehicleRealtimeAlvinCoordData"
                    new_alvin_data['data_array'] = [data for data in new_data['data_array'] if data['data_name'] in alvinCoordDataFields]

                    if len(new_alvin_data['data_array']) > 0:
                        del new_alvin_data['_id']
                        # logger.error(json.dumps(new_alvin_data['data_array']))
                        return_aux_data.append(new_alvin_data)
                    else:
                        logger.error("no realtime alvin coords data, skipping")

                    new_data['data_source'] = "vehicleRealtimeNavData"
                    new_data['data_array'] = [data for data in new_data['data_array'] if data['data_name'] in navDataFields]
                    if len(new_data['data_array']) == 0:
                        continue

                elif new_data['data_source'] == "vehicleRealtimeNavData":

                    new_alvin_data = copy.deepcopy(new_data)
                    new_alvin_data['data_source'] = "vehicleRealtimeAlvinCoordData"
                    new_alvin_data['data_array'] = [data for data in new_data['data_array'] if data['data_name'] in alvinCoordDataFields]

                    if len(new_alvin_data['data_array']) > 0:
                        del new_alvin_data['_id']
                        # logger.error(json.dumps(new_alvin_data['data_array']))
                        return_aux_data.append(new_alvin_data)
                    else:
                        logger.warn("no realtime alvin coords data, skipping")

                    new_data['data_source'] = "vehicleRealtimeNavData"
                    new_data['data_array'] = [data for data in new_data['data_array'] if data['data_name'] in navDataFields]
                    if len(new_data['data_array']) == 0:
                        continue

                elif new_data['data_source'] == "renavData":

                    new_alvin_data = copy.deepcopy(new_data)
                    new_alvin_data['data_source'] = "vehicleReNavAlvinCoordData"
                    new_alvin_data['data_array'] = [data for data in new_data['data_array'] if data['data_name'] in alvinCoordDataFields]

                    if len(new_alvin_data['data_array']) > 0:
                        del new_alvin_data['_id']
                        # logger.error(json.dumps(new_alvin_data['data_array']))
                        return_aux_data.append(new_alvin_data)
                    else:
                        logger.warn("no renav alvin coords data, skipping")

                    new_data['data_source'] = "vehicleReNavData"
                    new_data['data_array'] = [data for data in new_data['data_array'] if data['data_name'] in navDataFields]
                    if len(new_data['data_array']) == 0:
                        continue

                elif new_data['data_source'] == "framegrabber":
                    new_data['data_source'] = "vehicleRealtimeFramegrabberData"
                    new_data['data_array'] = list(map(lambda data: fixFramegrabImage(loweringID, data, vehicle), new_data['data_array']))

                elif new_data['data_source'] == "vehicleRealtimeFramegrabberData":
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
