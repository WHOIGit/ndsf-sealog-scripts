#!/usr/bin/env python3
#
#  Purpose: This script processes the provided event export and returns a
#           list of all SulisCam image filename added to a specified
#           source path.
#
#    Usage: Type python3 getSulisCamList.py -? for full usage information.
#
#           The typical way to call this script is:
#           python3 getSulisCamList.py <event_data_file>
#           Where <event_data_file> is the json-formatted Event Export from
#           the sealog client.
#
#           The output is sent to stdout so that it can be redriected to a
#           file or subsequent processing step.
#
#   Author: Webb Pinner webbpinner@gmail.com
#  Created: 2018-09-26
# Modified: 2019-05-11

import json
import argparse
import os

IMAGE_SOURCE_DIR = '/home/jason/sealog-files/images/SulisCam'

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='Sealog SulisCam file list retriever 2000')
  parser.add_argument('-s', metavar='source_dir', help='The source directory to prepend to the SulisCam file names')
  parser.add_argument('events_file', help='The events-only export from Sealog')

  args = parser.parse_args()

  if args.s:
    IMAGE_SOURCE_DIR = args.s

  f = open(args.events_file)
  r = json.loads(f.read())

  for event in r:
    if event['event_value'] == "SulisCam":
      for option in event['event_options']:
        if option['event_option_name'] == 'filename':
          print(os.path.join(IMAGE_SOURCE_DIR, option['event_option_value']))

