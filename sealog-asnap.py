#!/usr/bin/env python3
'''
This service submits ASNAP events to Sealog at the specified interval so long
as Sealog says ASNAPs be created.
'''

import argparse
import logging
import time

import requests

from python_sealog.settings import apiServerURL, customVarAPIPath, \
                                   eventsAPIPath, headers


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


ASNAP_STATUS_VAR_NAME = 'asnapStatus'

EVENT_TEMPLATE = {
    'event_value': 'ASNAP',
    'event_options': [],
    'event_free_text': '',
}


def is_asnap_enabled():
    response = requests.get(
        f'{apiServerURL}{customVarAPIPath}',
        params={'name': ASNAP_STATUS_VAR_NAME},
        headers=headers,
    )#.json()
    print(response)
    response = response.json()
    assert type(response) == type([])
    return response[0]['custom_var_value'] == 'On'


def post_asnap_event():
    requests.post(
        f'{apiServerURL}{eventsAPIPath}',
        headers=headers,
        json=EVENT_TEMPLATE,
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--interval', type=int, default=10,
                        help='ASNAP interval in seconds')
    args = parser.parse_args()

    while True:
        try:
            if is_asnap_enabled():
                post_asnap_event()
        except KeyboardInterrupt:
            quit()
        except:
            logger.exception('An error occurred while performing ASNAP')
        finally:
            time.sleep(args.interval)
