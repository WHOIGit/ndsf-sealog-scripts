#!/usr/bin/env python3
#
#  Purpose: This script takes a lowering ID and renav ppi file and 
#           creates new renav aux_data records within Seaplay
#
#    Usage: Type python3 sealog-renav-to-events.py <lowering_id> <ppi_file> to run the script.
#            - <lowering_id>: the lowering ID (J2-1042)
#            - <ppi_file>: the ppi file name with absolute/relative path (./J2-1042_ppi.txt)
#
#   Author: Webb Pinner webbpinner@gmail.com
#  Created: 2018-11-07
# Modified: 2019-05-11

import requests
import json
import argparse
import csv
import sys
import os
import shutil
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from python_sealog.settings import apiServerURL, eventsAPIPath, \
                                   eventAuxDataAPIPath, headers, \
                                   loweringsAPIPath

auxDataTemplate = {
    'event_id': None,
    'data_source': None,
    'data_array': []
}

def get_events(lowering_uid):
    try:
        r = requests.get(f'{apiServerURL}/{eventsAPIPath}/bylowering/{lowering_uid}', headers=headers)
        return json.loads(r.text)
    except Exception as error:
        print(error)
        return None

def get_lowering_uid(lowering_id):
    try:
        r = requests.get(f'{apiServerURL}/{loweringsAPIPath}?lowering_id={lowering_id}', headers=headers)
        response = json.loads(r.text)

        if response[0]['lowering_id']:
            return response[0]['id']
        else:
            return None
    except Exception as error:
        print(error)
        return None

def match_ppi_to_event(ppi_file, events):

    # print(json.dumps(events, indent=2))
    for event in events:
        event['ts'] = datetime.strptime(event['ts'], '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y-%m-%dT%H:%M:%S.000Z')

    ppi_data_array = []

    with open(ppi_file) as f:
        reader = csv.reader(f, delimiter=" ", skipinitialspace=True)
        # header = next(reader) # skip header

        for row in reader:
            
            ppi_ts = datetime.strptime(row[0] + ' ' + row[1], '%Y/%m/%d %H:%M:%S.%f').strftime('%Y-%m-%dT%H:%M:%S.000Z')
            eventIDArray = filter(lambda event: event['ts'] == ppi_ts, events)

            for event in eventIDArray:
                # print("event:", json.dumps(event))
                ppi_data = {}
                ppi_data['event_id'] = event['id']
                ppi_data['data_source'] = "vehicleReNavData"
                ppi_data['data_array'] = []
                ppi_data['data_array'].append({ 'data_name': "latitude",'data_value': row[2], 'data_uom': 'ddeg' })
                ppi_data['data_array'].append({ 'data_name': "longitude",'data_value': row[3], 'data_uom': 'ddeg' })
                ppi_data['data_array'].append({ 'data_name': "heading",'data_value': row[5], 'data_uom': 'deg' })
                ppi_data['data_array'].append({ 'data_name': "depth",'data_value': row[4], 'data_uom': 'meters' })
                ppi_data['data_array'].append({ 'data_name': "altitude",'data_value': row[8], 'data_uom': 'meters' })

                # ppi_data_array.append(ppi_data)
                print("Adding Aux Data Record to event:", event['ts'], '-->', event['event_value'])

                try:
                    r = requests.post(f'{apiServerURL}/{eventAuxDataAPIPath}', headers=headers, data = json.dumps(ppi_data))
                    #Copy file
                except Exception as error:
                    print("Error:", error)
                    print("Event:", event)

                # print("event:", json.dumps(event))
                # ppi_data = {}
                # ppi_data['event_id'] = event['id']
                # ppi_data['data_source'] = "vehicleReNavAlvinCoordData"
                # ppi_data['data_array'] = []
                # ppi_data['data_array'].append({ 'data_name': "alvin_x",'data_value': row[6], 'data_uom': 'meters' })
                # ppi_data['data_array'].append({ 'data_name': "alvin_y",'data_value': row[7], 'data_uom': 'meters' })

                # # ppi_data_array.append(ppi_data)
                # print("Adding Aux Data Record to event:", event['ts'], '-->', event['event_value'])

                # try:
                #     r = requests.post(f'{apiServerURL}/{eventAuxDataAPIPath}', headers=headers, data = json.dumps(ppi_data))
                #     #Copy file
                # except Exception as error:
                #     print("Error:", error)
                #     print("Event:", event)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Sealog ReNav Inserter 2000')
    parser.add_argument('lowering_id', help='The lowering to process (i.e. 5001)')
    parser.add_argument('ppi_file', help='The ppi file containing the timestamps and postions for the stills')

    args = parser.parse_args()

    if not os.path.isfile(args.ppi_file):
        print("ERROR: ppi file", args.ppi_file, " not found")
        sys.exit(1)

    lowering_uid = get_lowering_uid(args.lowering_id)

    if not lowering_uid:
        print("ERROR: lowering", args.lowering_id , "not found")
        sys.exit(1)

    print("lowering_uid:", lowering_uid)
    lowering_events = get_events(lowering_uid)

    match_ppi_to_event(args.ppi_file, lowering_events)
