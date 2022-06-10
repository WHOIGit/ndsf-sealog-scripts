#!/usr/bin/env python3
#
# Purpose: This script queries the sealog-server API and returns the
#          uid for the given cruise ID
#
#   Usage: Type python3 getCruiseId.py -? for full usage information.
#
#          The typical way to call this script is:
#          python3 getCruiseId.py <cruise_id>
#          Where <cruise_id> is the common cruise id (i.e. AT42-01)
#
#          This will return the 24-character UID for the give cruise ID.
#          The cruise UID is used throughout the sealog-server API to set,
#          get and delete cruise records and accompanying events.  If the
#          cruise ID is invalid then the script will return nothing. 
#
#  Author: Webb Pinner webbpinner@gmail.com
# Created: 2018-09-26

import requests
import json
import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.realpath(__file__)))))

from python_sealog.settings import apiServerURL, cruisesAPIPath, headers

# FIXME: Override apiServerURL because we're outside of Docker
apiServerURL = "https://localhost/sealog/server"


if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='Sealog Cruise ID retriever 2000')
  parser.add_argument('cruise_id', help='cruise number (i.e. AT4201)')

  args = parser.parse_args()

  r = requests.get(f'{apiServerURL}/{cruisesAPIPath}', headers=headers)

  cruises = json.loads(r.text)
  for cruise in cruises:
    if cruise['cruise_id'] == args.cruise_id:
      print(cruise['id'])
      break
