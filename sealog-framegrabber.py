#!/usr/bin/env python3
'''
This service listens for new events submitted to Sealog. When one is received,
a frame is downloaded from each framegrabber and saved to disk. The event aux
data is updated to reference the files on disk.
'''

# TODO
# Rather than handling multiple framegrabbers in one instance, we could just
# run multiple instances pointed at different devices. However this assumes that
# the API allows attaching multiple vehicleRealtimeFramegrabberData fragments.

import argparse
import asyncio
import datetime
import json
import logging
import os

import requests
import websockets

from python_sealog.settings import apiServerURL, eventAuxDataAPIPath, headers, \
                                   wsServerURL


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


CLIENT_WSID = 'framegrabber'

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

ARGS = None


def download_url(url, f):
    with requests.get(url, stream=True, timeout=ARGS.timeout) as r:
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=8192): 
            f.write(chunk)


async def handle_event(event):
    ts = datetime.datetime.strptime(event['message']['ts'],
                                    '%Y-%m-%dT%H:%M:%S.%fZ')
    if (datetime.datetime.utcnow() - ts).total_seconds() > ARGS.max_age:
         logger.info('Ignoring event older than maximum age')
         return
    
    aux_data = {
        'event_id': event['message']['id'],
        'data_source': 'vehicleRealtimeFramegrabberData',
        'data_array': [],
    }

    # Download an image from each framegrabber
    for (label, url, pattern) in ARGS.grabbers:
        out_name = pattern.format(ts.strftime("%Y%m%d_%H%M%S%f")[:-3])
        out_path = os.path.join(ARGS.dest, out_name)

        try:
            with open(out_path, 'wb') as f:
                download_url(url, f)
        except:
            logger.exception(f'Failed to fetch frame from {label}')
            continue
        
        aux_data['data_array'].extend([
            { 'data_name': 'camera_name', 'data_value': label },

            # XXX
            # The filename provided here will be processed by get_image_url()
            # defined in client_config.js. This currently means that we need to
            # insert a /.
            { 'data_name': 'filename',    'data_value': f'/{out_name}' },
        ])

    # Post the new auxiliary data
    if aux_data['data_array']:
        logger.info('Associating grabbed frames with event')
        requests.post(
            f'{apiServerURL}{eventAuxDataAPIPath}',
            headers=headers,
            json=aux_data,
        )
    else:
        logger.warning('Handled event, but could not contact any grabbers')


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', required=True)
    parser.add_argument('--max-age', type=int, default=10,
                        help='Maximum age of an event that will be annotated')
    parser.add_argument('--timeout', type=float, default=1.0,
                        help='Maximum amount of time to wait for a grabber')
    parser.add_argument('--grabber', nargs=3, action='append', dest='grabbers',
                        metavar=('LABEL', 'URL', 'FILENAME_PATTERN'))

    ARGS = parser.parse_args()

    asyncio.run(event_listener())
