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
import collections
import datetime
import json
import logging
import os
import urllib.parse

import requests
import socketio
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

# Incoming Sealog events get added to this queue and processed by a worker
Event = collections.namedtuple('Event', 'id timestamp frames')
EVENT_QUEUE = None  # see https://stackoverflow.com/a/55918049/145504

# Records the last heartbeat timestamp from the imaging control server
LAST_HEARTBEAT = None


def download_url(url):
    logger.info('Downloading frame from %s', url)
    data = bytearray()
    with requests.get(url, stream=True, timeout=ARGS.timeout) as r:
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=8192):
            data += chunk
    return data


def attach_framegrabs(event, grabs):
    aux_data = {
        'event_id': event.id,
        'data_source': 'vehicleRealtimeFramegrabberData',
        'data_array': [],
    }

    for label, file in grabs:
        aux_data['data_array'].extend([
            { 'data_name': 'camera_name', 'data_value': label },

            # XXX
            # The filename provided here will be processed by get_image_url()
            # defined in client_config.js. This currently means that we need to
            # insert a /.
            { 'data_name': 'filename',    'data_value': f'/{file}' },
        ])

    # Post the new auxiliary data
    logger.info('Associating grabbed frames with event %s', event.id)
    requests.post(
        f'{apiServerURL}{eventAuxDataAPIPath}',
        headers=headers,
        json=aux_data,
    )


# Handle an incoming Sealog events by contacting all known framegrabbers and
# saving the resulting images to the event queue.
async def handle_event(event):
    ts = datetime.datetime.strptime(event['message']['ts'],
                                    '%Y-%m-%dT%H:%M:%S.%fZ')
    if (datetime.datetime.utcnow() - ts).total_seconds() > ARGS.max_age:
         logger.info('Ignoring event older than maximum age')
         return

    # Download an image from each framegrabber to memory
    frames = await asyncio.gather(*(
        asyncio.to_thread(download_url, url)
        for _, url, _ in ARGS.grabbers
    ), return_exceptions=True)

    frames = [None if isinstance(f, Exception) else f for f in frames]
    if not any(frames):
        logger.warn('Could not contact any framegrabbers')
        return

    # Enqueue event for future processing
    EVENT_QUEUE.put_nowait(Event(
        id=event['message']['id'],
        timestamp=ts,
        frames=frames,
    ))


# This worker pops events with frames off the queue, and submits them to
# Sealog with the appropriate camera labels attached.
async def auxdata_worker():
    while True:
        event = await EVENT_QUEUE.get()
        logger.info('Worker popped event %s', event.id)

        # If there hasn't been an imaging control heartbeat since this event
        # was received, place it back in the queue.
        if ARGS.imaging_control is not None:
            dt = None if LAST_HEARTBEAT is None else \
                 (event.timestamp - LAST_HEARTBEAT).total_seconds()
            if dt is not None and dt >= 3:
                logger.info('No heartbeat, doing event %s anyway', event.id)
            elif dt is None or dt >= 0:
                logger.info('Re-queuing event %s until heartbeat', event.id)
                EVENT_QUEUE.put_nowait(event)
                EVENT_QUEUE.task_done()
                await asyncio.sleep(0.5)
                continue

        # Now that we finally know labels for the grabbers, write frames to
        # disk and attach them to the original Sealog event.
        grabs = []
        for grabber, frame in zip(ARGS.grabbers, event.frames):
            if frame is None:
                continue
            label, _, pattern = grabber

            out_name = pattern.replace('{}',
                event.timestamp.strftime('%Y%m%d_%H%M%S%f')[:-3])
            out_path = os.path.join(ARGS.dest, out_name)
            grabs.append((label, out_name))

            with open(out_path, 'wb') as f:
                f.write(frame)

        attach_framegrabs(event, grabs)

        EVENT_QUEUE.task_done()


# Listens for new events coming from Sealog
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


# When an imaging control server is in play, this listener updates the list
# of grabbers whenever the configuration changes.
async def imaging_control_listener():
    if ARGS.imaging_control is None:
        return

    # Perhaps one of the dumbest things I've ever seen: python-socketio just
    # silently ignores anything other than the server address that you pass
    # to `url`, so we need to split it up ourselves.
    #
    # https://github.com/miguelgrinberg/python-socketio/issues/818
    u = urllib.parse.urlparse(ARGS.imaging_control)

    sio = socketio.AsyncClient()

    @sio.on('SealogHeartbeat', namespace='/sealog')
    async def on_heartbeat(hb):
        global LAST_HEARTBEAT
        LAST_HEARTBEAT = datetime.datetime.utcnow()

        ARGS.grabbers = []
        for i, grabber_info in enumerate(hb.get('framegrabbers', [])):
            ARGS.grabbers.append((
                f'{grabber_info["camera_name"]} (Framegrabber {i+1})',
                grabber_info['url'],
                f'{{}}.{grabber_info["camera_name"]}.framegrab{i+1:02}.jpg',
            ))

    await sio.connect(f'{u.scheme}://{u.netloc}',
                      socketio_path=f'{u.path}/socket.io',
                      namespaces=['/sealog'])
    await sio.wait()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', required=True)
    parser.add_argument('--max-age', type=int, default=10,
                        help='Maximum age of an event that will be annotated')
    parser.add_argument('--timeout', type=float, default=1.0,
                        help='Maximum amount of time to wait for a grabber')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--grabber', nargs=3, action='append', dest='grabbers',
                       metavar=('LABEL', 'URL', 'FILENAME_PATTERN'))
    group.add_argument('--imaging-control', type=str, metavar='URL')

    ARGS = parser.parse_args()

    async def start():
        global EVENT_QUEUE
        EVENT_QUEUE = asyncio.Queue()

        await asyncio.gather(
            event_listener(),
            imaging_control_listener(),
            auxdata_worker(),
        )

    asyncio.run(start())
