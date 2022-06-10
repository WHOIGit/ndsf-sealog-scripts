#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Purpose: This script converts the framegrab copy script exported by the at-
#          sea instance of Sealog so that it can be used to copy the framegrab
#          images to the appropriate location on the Shoreside Sealog Server 
#
#   Usage: convert_framegrab_copy_script.py [-d] <loweringID> <original framegrab copy script>
#
#  Author: Webb Pinner webbpinner@gmail.com
# Created: 2019-05-22

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


# FIXME: This is really hacky
if "harmonyhill" in os.getenv("HOSTNAME", ""):
    imageBaseDir = {
        "Jason": "/home/sealog/sealog-files-jason/images",
        "Alvin": "/home/sealog/sealog-files-alvin/images",
    }
else:
    imageBaseDir = {
        "Jason": "/home/sealog/sealog-files/images",
        "Alvin": "/home/sealog/sealog-files/images",
    }

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

def modifyCopyScript(loweringID, copy_script_fn, vehicle):
    sources = set()

    newCopyScript = ''
    with open(copy_script_fn) as copy_script_fp:
        for line in copy_script_fp:

            if line.startswith('cp'):
                copy, verbose, sourceFilePath, destDir = line.split(' ')
                sourceFileName = os.path.basename(sourceFilePath)

                # Parse the filename
                name, ext = os.path.splitext(sourceFileName)

                # Detect whether the order is <source>.<timestamp> or <timestamp>.<source>
                if re.match(r'^\d+_\d+$', name.split(".")[0]):
                    timestamp, source = name.split(".", maxsplit=1)
                else:
                    source, timestamp = os.path.splitext(name)

                source = imageSourceMap.get(vehicle, {}).get(source, source)
                sources.add(source)

                new_destFilePath = os.path.join(loweringID, source, f'{source}.{timestamp}{ext}')
                newCopyScript += ' '.join([copy, verbose, '${SOURCE_DIR}/' + sourceFileName, '${DEST_DIR}/' + new_destFilePath, '\n'])

    return newCopyScript, sources



if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='framegrab copy script tweaker')
    parser.add_argument('-d', '--debug', action='store_true', help=' display debug messages')
    parser.add_argument('--vehicle', choices=vehicles, help='the vehicle used (Alvin or Jason)')
    parser.add_argument('loweringID', help='lowering ID')
    parser.add_argument('framegrabCopyScript', help=' original framegrab copy script to modify')

    args = parser.parse_args()

    # Turn on debug mode
    if args.debug:
        logger.info("Setting log level to DEBUG")
        logger.setLevel(logging.DEBUG)

        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)

    if not os.path.isfile(args.framegrabCopyScript):
        logger.error(args.framegrabCopyScript + " does not exist.")
        sys.exit(0)

    if args.vehicle not in vehicles:
        logger.error("Vehicle must be one of: " + ', '.join(vehicles))
        sys.exit(0)

    loweringID = args.loweringID
    if args.vehicle == "Alvin":
        loweringID = args.loweringID.replace("AL", "Alvin-D")

    new_copyScript, sources = modifyCopyScript(loweringID, args.framegrabCopyScript, args.vehicle)

    if(new_copyScript):
        print("#!/bin/bash")
        print("SOURCE_DIR=../images")

        print("DEST_DIR=" + imageBaseDir[args.vehicle])
        for dirname in sources:
            print('mkdir -p ${DEST_DIR}/' + loweringID + '/' + dirname)

        print(new_copyScript)
    else:
        logger.error("Nothing to return")
