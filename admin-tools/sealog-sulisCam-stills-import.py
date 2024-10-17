#!/usr/bin/env python3
#
#  Purpose: This script inserts events for each SulisCam framegrab image
#           listed within the SulisCam ppx file.  It also creates/associates
#           and aux_data record containing the renav position data for the
#           moment image was taken.
#
#    Usage: Type python3 sealog-sulisCam0stills-import.py -? for full usage
#           information.
#
#           The typical way to call this script is:
#           python3 sealog-sulisCam0stills-import.py <source_dir> <ppfx_file>
#           Where <source_dir> is the location of the image files and
#           <ppfx_file> is the file path to the corresponding ppx file.
#
#
#   Author: Webb Pinner webbpinner@gmail.com
#  Created: 2018-09-26
# Modified: 2019-02-11

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
                                   eventAuxDataAPIPath, headers


DEST_IMAGE_DIRECTORY = '/home/jason/sealog-files/images/SulisCam'

auxDataTemplate = {
    'event_id': None,
    'data_source': None,
    'data_array': []
}

eventTemplate = {
  "event_value": "SulisCam",
  "event_free_text": ""
}

def translate_file_to_events(ppfx_file, source_dir):

    with open(ppfx_file) as f:
        reader = csv.reader(f, delimiter=" ", skipinitialspace=True)
        header = next(reader)

        for row in reader:

            imagePath = os.path.join(source_dir, row[3])
            if not os.path.isfile(imagePath):
                print("Could not locate", imagePath)
                continue
            else:
                print("Copying", row[3], "to", DEST_IMAGE_DIRECTORY)
                try:
                    shutil.copy2(imagePath, DEST_IMAGE_DIRECTORY)
                except Exception as error:
                    print(error)

            event = eventTemplate
            event['event_options'] = [
                {
                    'event_option_name': 'filename',
                    'event_option_value': row[3]
                }
            ]
            event['ts'] = datetime.strptime(row[0] + ' ' + row[1], '%Y/%m/%d %H:%M:%S.%f').strftime('%Y-%m-%dT%H:%M:%S.000Z')
            print("Adding Event Record")

            try:
                r = requests.post(f'{apiServerURL}/{eventsAPIPath}', headers=headers, data = json.dumps(event))
                responseObj = json.loads(r.text)

                print(f'{apiServerURL}/{eventsAPIPath}')
                print(json.dumps(event))
                print(responseObj)

                # Add renav aux data entry
                renavData = auxDataTemplate

                renavData['event_id'] = responseObj['insertedId']
                renavData['data_source'] = "vehicleReNavData"
                renavData['data_array'] = []

                renavData['data_array'].append({ 'data_name': "latitude",'data_value': row[4], 'data_uom': 'ddeg' })
                renavData['data_array'].append({ 'data_name': "longitude",'data_value': row[5], 'data_uom': 'ddeg' })
                renavData['data_array'].append({ 'data_name': "heading",'data_value': row[6], 'data_uom': 'deg' })
                renavData['data_array'].append({ 'data_name': "depth",'data_value': row[7], 'data_uom': 'meters' })
                renavData['data_array'].append({ 'data_name': "altitude",'data_value': row[8], 'data_uom': 'meters' })
                renavData['data_array'].append({ 'data_name': "pitch",'data_value': row[9], 'data_uom': 'deg' })
                renavData['data_array'].append({ 'data_name': "roll",'data_value': row[10], 'data_uom': 'deg' })

                print("Adding Renav Aux Data Record")

                try:
                    r = requests.post(f'{apiServerURL}/{eventAuxDataAPIPath}', headers=headers, data = json.dumps(renavData))
                except Exception as error:
                    print(error)
                    print(event)

                # Add framegrabber aux data entry
                framegrabberData = auxDataTemplate
                framegrabberData['event_id'] = responseObj['insertedId']
                framegrabberData['data_source'] = "vehicleRealtimeFramegrabberData"
                framegrabberData['data_array'] = []
                framegrabberData['data_array'].append({ 'data_name': "camera_name", 'data_value': "SulisCam" })
                framegrabberData['data_array'].append({ 'data_name': "filename", 'data_value': row[3] })

                print("Adding framegrabber Aux Data Record")

                try:
                    r = requests.post(f'{apiServerURL}/{eventAuxDataAPIPath}', headers=headers, data = json.dumps(framegrabberData))
                except Exception as error:
                    print(error)
                    print(event)


            except Exception as error:
                print(error)
                print(event)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='SulisCam Still Sealog Event Inserter 2000')
    parser.add_argument('source_dir', help='The directory containing the stills')
    parser.add_argument('ppfx_file', help='The ppfx file containing the timestamps and postions for the stills')

    args = parser.parse_args()

    if not os.path.isdir(DEST_IMAGE_DIRECTORY):
        print("Destination directory:", DEST_IMAGE_DIRECTORY, "does not exist")
        confirm = input('Create it? (y/n): ')
        if confirm != "y" and confirm != "Y":
            sys.exit(1)
        else:
            try:
                os.makedirs(DEST_IMAGE_DIRECTORY)
            except OSError: print ('Error: Creating directory.')

    if os.path.isdir(args.source_dir):
        translate_file_to_events(args.ppfx_file, args.source_dir)
    else:
        print("Source directory:", args.source_dir, "does not exist")
