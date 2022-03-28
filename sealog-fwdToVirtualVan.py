#!/usr/bin/env python3
#
# Purpose: This service listens for new events submitted to Sealog
#          and repeats those events on to VirtualVan so long as
#          the timestamp on the event is within 120 seconds of the
#          current time.

import argparse
import asyncio
import datetime
import json
import logging
import re
import socket
import urllib.request

import websockets

from python_sealog.settings import apiServerURL, eventTemplatesAPIPath, \
                                   headers, wsServerURL


# Parse command-line arguments
parser = argparse.ArgumentParser(
    description='Sealog to VirtualVan event bridge',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument('--time-limit', default=120,
                    help='Discard events from more than this many seconds ago')
parser.add_argument('--virtualvan', default='198.17.154.221:10502',
                    help='Address of the VirtualVan DAQ server')
args = parser.parse_args()


# Convert the VirtualVan address to a (host, port) tuple
if ':' in args.virtualvan:
    host, _, port = args.virtualvan.partition(':')
    args.virtualvan = (host, int(port))
else:
    args.virtualvan = (args.virtualvan, 10502)


EXCLUDE_SET = {'ASNAP'}


CLIENT_WSID = 'sealog2VirtualVan'

HELLO = {
    'type': 'hello',
    'id': CLIENT_WSID,
    'auth': {'headers': headers},
    'version': '2',
    'subs': ['/ws/status/newEvents'],
}

PING = {
    'type': 'ping',
    'id': CLIENT_WSID,
}


LOG_LEVEL = logging.DEBUG

# create logger
logger = logging.getLogger(__file__)
logger.setLevel(LOG_LEVEL)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(LOG_LEVEL)

# create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


event_templates = {}

def get_event_templates():
    req = urllib.request.Request(
        f'{apiServerURL}{eventTemplatesAPIPath}',
        headers=headers
    )
    with urllib.request.urlopen(req) as r:
        j = json.loads(r.read().decode())

    for template in j:
        event_templates[template['event_value']] = template

    # Put in a bogus event template for free form events
    event_templates['FREE_FORM'] = {
        'event_free_text_required': True
    }


async def handle_event(event):
    event_value = event['message']['event_value']

    if event_value in EXCLUDE_SET:
        logger.debug('Skipping because event value is in the exclude set')
        return

    # Because event templates can change, we do not cache the result of this
    # API call, but it makes us a little sad
    get_event_templates()
    event_template = event_templates[event_value]

    req_free_text = event_template['event_free_text_required']
    if req_free_text and not event['message'].get('event_free_text'):
        logger.debug('Ignoring event because required free text is missing')
        return

    for eto in event_template.get('event_options', []):
        eto_name = eto['event_option_name']
        eto_required = eto['event_option_required']
        if not eto_required:
            continue

        # The event template option names are normalized when they appear in an event
        eto_name = re.sub('\s+', '_', eto_name.lower())

        for opt in event['message']['event_options']:
            opt_name = opt['event_option_name']
            opt_value = opt['event_option_value']
            if opt_name == eto_name and opt_value:
                break
        else:
            logger.debug('Ignoring event because required field %s is missing', eto_name)
            return

    # Requires Python 3.7. We need to explicitly expand the timezone
    timestamp = datetime.datetime.fromisoformat(
        event['message']['ts'].replace('Z', '+00:00'))

    now = datetime.datetime.now(datetime.timezone.utc)
    if (now - timestamp).total_seconds() > args.time_limit:
        logger.debug('Ignored because the user took too long to submit')
        return

    event_name = 'TXT'
    if event_value != 'FREE_FORM':
        event_name = event_value

    event_options = ''
    if len(event['message']['event_options']) > 0:
        options = []
        for option in event['message']['event_options']:
            options.append(option['event_option_name'])
            options.append(option['event_option_value'])

        event_options = ' '.join(options)

    line = ' '.join([
        'EVT', datetime.datetime.strftime(timestamp, '%Y/%m/%d %H:%M:%S'),
        'DLG', event_name + ':', event['message'].get('event_free_text', ''),
        event_options
    ])

    logger.debug('Adding Record: ' + line)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(line.encode(), args.virtualvan)


async def event_listener():
    async with websockets.connect(wsServerURL) as websocket:
        await websocket.send(json.dumps(HELLO))

        while True:
            try:
                msg = json.loads(await websocket.recv())

                if msg.get('type') == 'ping':
                    logger.debug('Acknowledging ping from server')
                    await websocket.send(json.dumps(PING))
                elif msg.get('type') == 'pub':
                    await handle_event(msg)
                else:
                    logger.debug(f'Ignoring message of type {msg.get("type")}')
            except websockets.exceptions.ConnectionClosedError:
                logger.error('The connection to the server was lost')
                break
            except:
                logger.exception(
                    'An exception occurred while processing a message')


async def main():
    # Call this once just so we fail early instead of doing so when the first
    # event arrives.
    get_event_templates()

    await event_listener()


if __name__ == '__main__':
    asyncio.run(main())
