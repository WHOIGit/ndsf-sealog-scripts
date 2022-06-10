#!/usr/bin/env python3
#
# Purpose: This script queries the sealog-server API and returns the
#          uid for the given lowering ID
#
#   Usage: Type python3 getLoweringId.py -? for full usage information.
#
#          The typical way to call this script is:
#          python3 getLoweringId.py <lowering_id>
#          Where <lowering_id> is the common lowering id (i.e. J2-1107)
#
#          This will return the 24-character UID for the give lowering ID.
#          The lowering UID is used throughout the sealog-server API to
#          set, get and delete lowering records and accompanying events.
#          If the lowering ID is invalid then the script will return nothing. 
#
#  Author: Webb Pinner webbpinner@gmail.com
# Created: 2018-11-07

import requests
import json
import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from python_sealog.settings import apiServerURL, headers, loweringsAPIPath


if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='Sealog Lowering ID retriever 2000')
  parser.add_argument('lowering_id', help='lowering number (i.e. J2-1042)')

  args = parser.parse_args()

  r = requests.get(f'{apiServerURL}/{loweringsAPIPath}', headers=headers)

  lowerings = json.loads(r.text)
  for lowering in lowerings:
    if lowering['lowering_id'] == args.lowering_id:
      print(lowering['id'])
      break
