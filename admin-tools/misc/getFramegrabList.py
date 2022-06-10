#!/usr/bin/env python3
#
# Purpose: This script processes the provided aux_data export and returns
#          a list of all framegrab image filepaths
#
#   Usage: Type python3 getFramegrabList.py -? for full usage information.
#
#          The typical way to call this script is:
#          python3 getFramegrabList.py <aux_data_file>
#          Where <aux_data_file> is the json-formatted Aux Data Export from
#          the sealog client.
#
#          The output is sent to stdout so that it can be redriected to a
#          file or subsequent processing step.
#
#  Author: Webb Pinner webbpinner@gmail.com
# Created: 2018-09-26

import json
import argparse

if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='Sealog framegrab file list retriever 2000')
  parser.add_argument('aux_data_file', help='sealog_aux_data_file')

  args = parser.parse_args()

  f = open(args.aux_data_file)
  r = json.loads(f.read())

  for data in r:
    if data['data_source'] == "vehicleRealtimeFramegrabberData":
      for framegrab in data['data_array']:
        if framegrab['data_name'] == 'filename':
          print(framegrab['data_value'])

