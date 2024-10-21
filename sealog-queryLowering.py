#!/usr/bin/env python3
'''
This script provides a command line interface for querying for lowering and
cruise IDs given a timestamp.
'''

import argparse
import datetime
import logging
import sys

import python_sealog.settings
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


parser = argparse.ArgumentParser()
parser.add_argument('--url', default=python_sealog.settings.apiServerURL)
parser.add_argument('--get', dest='mode',
                    choices=('cruise', 'lowering', 'dive'), default='lowering')
parser.add_argument('--time', default='now')
args = parser.parse_args()


# Override python_sealog's server URL, then do late import of API
python_sealog.settings.apiServerURL = args.url

import python_sealog.cruises
import python_sealog.lowerings


# Handle synonymous dive/lowering
if args.mode == 'dive':
    args.mode = 'lowering'

# Parse the timestamp
fixzulu = lambda t: t.replace('Z', '+00:00')
if args.time == 'now':
    # Ridiculously, datetime.datetime.utcnow() is not timezone aware!
    args.time = datetime.datetime.now(datetime.timezone.utc)
else:
    args.time = datetime.datetime.fromisoformat(fixzulu(args.time))

# Find the first lowering that matches our timestamp
for lowering in python_sealog.lowerings.getLowerings() or []:
    start = datetime.datetime.fromisoformat(fixzulu(lowering['start_ts']))
    stop  = datetime.datetime.fromisoformat(fixzulu(lowering['stop_ts']))
    if start <= args.time < stop:
        break
else:
    print('null')
    sys.exit(1)

if args.mode == 'lowering':
    print(lowering['lowering_id'])
    sys.exit(0)

# Look up the cruise for this lowering
assert args.mode == 'cruise'
cruise = python_sealog.cruises.getCruiseByLowering(lowering['id'])

if cruise is None:
    print('null')
    sys.exit(1)

print(cruise['cruise_id'])
