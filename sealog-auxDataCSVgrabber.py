#!/usr/bin/env python3
'''
This service listens for new events submitted to Sealog and associates an
aux_data record containing the real-time data received from UDP packets.
'''

import argparse
import asyncio
import datetime
import json
import logging
import socket
import time

import requests
import websockets

from python_sealog.settings import apiServerURL, eventAuxDataAPIPath, headers, \
                                   wsServerURL


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


CLIENT_WSID = 'alvinCSVgrabber'

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


AUX_DATA_CACHE = []


# Only keep enough messages around to associate events that arrive within our
# timeout argument. This assumes that we receive packets in order.
def discard_old_aux_data():
    while AUX_DATA_CACHE:
        age = AUX_DATA_CACHE[-1][0] - AUX_DATA_CACHE[0][0]
        if age.total_seconds() > ARGS.max_age:
            del AUX_DATA_CACHE[0]
        else:
            break


# Looks through our aux_data cache and finds the entry that arrived closest to
# the target timestamp.
def get_nearest_aux_data(target_ts):
    if not AUX_DATA_CACHE:
        raise ValueError('Aux data cache is empty')

    bestidx = best = -1
    for i, (aux_data_ts, aux_data) in enumerate(AUX_DATA_CACHE):
        delta = abs((aux_data_ts - target_ts).total_seconds())
        if bestidx == -1 or delta < best:
            bestidx, best = i, delta
    return AUX_DATA_CACHE[bestidx]


async def handle_packet(packet):
    # An example packet, see sprintfAlvinDataRecords() in alvinDataThread.cpp:
    #
    # CSV,2021/08/13 21:28:04.332,ALVI,38.95180555,-77.14555556,3.14,6.28,19.84,180.00,0.00,0.00,1609.34

    data = packet.decode('utf-8').split(',')

    if not data or data[0] != 'CSV':
        return

    fields = (
        ('latitude', 'ddeg'),
        ('longitude', 'ddeg'),
        ('local_x', 'meters'),
        ('local_y', 'meters'),
        ('depth', 'meters'),
        ('heading', 'deg'),
        ('pitch', 'deg'),
        ('roll', 'deg'),
        ('altitude', 'meters'),
    )

    # Parse the timestamp of this record, based on the implementation of
    # rov_convert_dsl_time_string() from the Alvin codebase.
    timestamp = datetime.datetime.strptime(data[1], '%Y/%m/%d %H:%M:%S.%f')\
                                 .replace(tzinfo=datetime.timezone.utc)

    # We assume that timestamps of incoming packets are well-ordered
    if AUX_DATA_CACHE and not timestamp > AUX_DATA_CACHE[-1][0]:
        logger.error('Timestamp of CSV packet is not monotonically increasing')

    # Record this packet to our cache.
    #
    # Note: As in the original Sealog script, we do not convert any data types;
    # everything is passed to Sealog as a string. :(
    AUX_DATA_CACHE.append((
        timestamp,
        {
            'data_source': 'vehicleRealtimeNavData',
            'data_array': [
                { 'data_name': name, 'data_value': value, 'data_uom': unit }
                for value, (name, unit) in zip(data[3:], fields)
            ]
        }
    ))
    discard_old_aux_data()


async def udp_listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    s.setblocking(False)
    s.bind(('', ARGS.port))

    while True:
        packet = await asyncio.get_event_loop().sock_recv(s, 1024)
        try:
            await handle_packet(packet)
        except:
            logger.exception('An exception occurred while parsing a packet')


async def handle_event(event):
    event_ts = datetime.datetime.strptime(event['message']['ts'],
                                          '%Y-%m-%dT%H:%M:%S.%fZ')\
                                .replace(tzinfo=datetime.timezone.utc)

    aux_data_ts, aux_data = get_nearest_aux_data(event_ts)

    # Do not associate with the event if the aux_data we found is too old
    if abs((event_ts - aux_data_ts).total_seconds()) > ARGS.max_age:
        logger.info('Ignoring event older than maximum age')
        return

    # Associate the aux_data with this event
    aux_data['event_id'] = event['message']['id']
    requests.post(
        f'{apiServerURL}{eventAuxDataAPIPath}',
        headers=headers,
        json=aux_data,
    )


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
    await asyncio.gather(
        event_listener(),
        udp_listener()
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-age', type=int, default=120,
                        help='Maximum age of an event that will be annotated')
    parser.add_argument('--port', type=int, default=10600)

    ARGS = parser.parse_args()

    asyncio.run(main())
