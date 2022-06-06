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

imageBaseDir = {
    "Jason": "/home/sealog/sealog-files-jason/images",
    "Alvin": "/home/sealog/sealog-files-alvin/images"
}

oldImageSources = {
    "Jason": [
        'framegrab01',
        'framegrab02',
        'framegrab03',
        'framegrab04'
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
        'AftCam'
    ],
    "Alvin": [
        'SubSea1',
        'SubSea2',
        'SubSea3'
    ]
}

def modifyCopyScript(loweringID, copy_script_fn, vehicle):

    newCopyScript = ''
    with open(copy_script_fn) as copy_script_fp:
        for line in copy_script_fp:

            if line.startswith('cp'):
                copy, verbose, sourceFilePath, destDir = line.split(' ')
                sourceFileName = sourceFilePath.split('/')[-1]
                ext = sourceFileName.split('.')[-1]
                source = sourceFileName.split('.')[-2]
                timestamp = sourceFileName.split('/')[-1].split('.')[-3]
                index = oldImageSources[vehicle].index(source)

                new_destFilePath = os.path.join(loweringID, newImageSources[vehicle][index], ".".join([newImageSources[vehicle][index],timestamp,ext]))
                newCopyScript += ' '.join([copy, verbose, '${SOURCE_DIR}/' + sourceFileName, '${DEST_DIR}/' + new_destFilePath, '\n'])

    return newCopyScript



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

    new_copyScript = modifyCopyScript(loweringID, args.framegrabCopyScript, args.vehicle)

    if(new_copyScript):
        print("#!/bin/bash")
        if args.vehicle == "Alvin":
            print("SOURCE_DIR=../framegrabs")
        else:
            print("SOURCE_DIR=../images")

        print("DEST_DIR=" + imageBaseDir[args.vehicle])
        for dirname in newImageSources[args.vehicle]:
            print('mkdir -p ${DEST_DIR}/' + loweringID + '/' + dirname)

        print(new_copyScript)
    else:
        logger.error("Nothing to return")
