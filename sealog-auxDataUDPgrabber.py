#!/usr/bin/env python3
'''
This service listens for new events submitted to Sealog and associates an
aux_data record containing the real-time data received from UDP packets.
'''

import argparse
import asyncio
import bisect
import collections
import datetime
import json
import logging
import socket

import requests
import websockets

from python_sealog.settings import apiServerURL, eventAuxDataAPIPath, headers, \
                                   wsServerURL


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


CLIENT_WSID = 'alvinUDPgrabber'

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

CacheEntry = collections.namedtuple('CacheEntry', 'timestamp aux_data')
AUX_DATA_CACHE = []


def add_cache_entry(aux_data, timestamp=None):
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    timestamp = timestamp or now

    # Ignore entries that are too old
    if (now - timestamp).total_seconds() > ARGS.max_age:
        return

    # Purge cache entries that have expired
    while AUX_DATA_CACHE:
        if (now - AUX_DATA_CACHE[0].timestamp).total_seconds() > ARGS.max_age:
            del AUX_DATA_CACHE[0]
        else:
            break  # early exit since we are in sorted order

    # Insert the entry into the cache maintaining sorted order 
    timestamps = [x.timestamp for x in AUX_DATA_CACHE]
    AUX_DATA_CACHE.insert(
        bisect.bisect_left(timestamps, timestamp),
        CacheEntry(timestamp, aux_data)
    )


# Looks through our aux_data cache and finds the entry that arrived closest to
# the target timestamp.
def get_cache_entry(target_ts):
    bestidx = best = -1
    for i, (aux_data_ts, aux_data) in enumerate(AUX_DATA_CACHE):
        delta = abs((aux_data_ts - target_ts).total_seconds())
        if bestidx == -1 or delta < best:
            bestidx, best = i, delta
    return AUX_DATA_CACHE[bestidx]


# Parse DSL's timestamp format based on the implementation of
# rov_convert_dsl_time_string() from the Alvin codebase.
def parse_dsl_timestamp(str):
    return datetime.datetime.strptime(str, '%Y/%m/%d %H:%M:%S.%f')\
                            .replace(tzinfo=datetime.timezone.utc)


def handle_csv_packet(packet):
    # An example packet, see sprintfAlvinDataRecords() in alvinDataThread.cpp:
    #
    # CSV,2021/08/13 21:28:04.332,ALVI,38.95180555,-77.14555556,3.14,6.28,19.84,180.00,0.00,0.00,1609.34

    data = packet.decode().rstrip('\n').split(',')

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

    timestamp = parse_dsl_timestamp(data[1])

    # Record this packet to our cache.
    #
    # Note: As in the original Sealog script, we do not convert any data types;
    # everything is passed to Sealog as a string. :(
    add_cache_entry(
        timestamp=timestamp,
        aux_data={
            'data_source': 'vehicleRealtimeNavData',
            'data_array': [
                { 'data_name': name, 'data_value': value, 'data_uom': unit }
                for value, (name, unit) in zip(data[3:], fields)
            ]
        }
    )


def handle_ctm_packet(packet):
    # Not entirely sure where this is generated but here's an example:
    #
    # CTM 2020/09/12 10:00:00.316 CTM !SWT 4 F 3.12 3.08 -999.99 -999.99 C
    #
    # The interface board provides 4 ports. Typically one probe is attached.
    # Unoccupied ports will fill in with -999.99.

    data = packet.decode().rstrip('\n').split(' ')

    if not data or data[0] != 'CTM':
        return

    fields = (
        (f'probe{i+1}_temperature', 'degC')
        for i in range(4)
    )

    timestamp = parse_dsl_timestamp(f'{data[1]} {data[2]}')

    # Record this packet to our cache.
    #
    # Note: As in the original Sealog script, we do not convert any data types;
    # everything is passed to Sealog as a string. :(
    add_cache_entry(
        timestamp=timestamp,
        aux_data={
            'data_source': 'vehicleTemperatureProbe',
            'data_array': [
                { 'data_name': name, 'data_value': value, 'data_uom': unit }
                for value, (name, unit) in zip(data[7:], fields)
            ]
        }
    )


def handle_icl_packet(packet):
    # Not entirely sure where this is generated but here's an example:
    #
    # ICL 2021/02/12 16:51:40.704 013.4 014.5 C
    #
    # First temperature is tip, second is housing.

    data = packet.decode().rstrip('\n').split(' ')

    if not data or data[0] != 'ICL':
        return

    fields = (
        ('tip_temp', 'degC'),
        ('housing_temp', 'degC'),
    )

    timestamp = parse_dsl_timestamp(f'{data[1]} {data[2]}')

    # Remove leading zeroes
    data[3] = data[3].lstrip('0')
    data[4] = data[4].lstrip('0')

    # Record this packet to our cache.
    #
    # Note: As in the original Sealog script, we do not convert any data types;
    # everything is passed to Sealog as a string. :(
    add_cache_entry(
        timestamp=timestamp,
        aux_data={
            'data_source': 'ICLTemperatureProbe',
            'data_array': [
                { 'data_name': name, 'data_value': value, 'data_uom': unit }
                for value, (name, unit) in zip(data[3:], fields)
            ]
        }
    )


def handle_jds_packet(packet):
    # An example packet, see sprintf_data_records() in
    # jason-rov/data_thread.cpp:
    #
    # JDS 2021/08/13 21:28:04.332 JAS2 38.9518055 -77.1455566 101.33 101.33 4.5 4.5 4.55 9.66 5.55 8841941.2 31.2

    data = packet.decode().rstrip('\n').split(' ')

    if not data or data[0] != 'JDS':
        return

    fields = (
        ('latitude', 'ddeg'),
        ('longitude', 'ddeg'),
        ('local_x', 'meters'),
        ('local_y', 'meters'),
        ('roll', 'deg'),
        ('pitch', 'deg'),
        ('heading', 'deg'),
        ('depth', 'meters'),
        ('altitude', 'meters'),
        # ignoring runtime, wraps
    )

    timestamp = parse_dsl_timestamp(f'{data[1]} {data[2]}')

    # Record this packet to our cache.
    #
    # Note: As in the original Sealog script, we do not convert any data types;
    # everything is passed to Sealog as a string. :(
    add_cache_entry(
        timestamp=timestamp,
        aux_data={
            'data_source': 'vehicleRealtimeNavData',
            'data_array': [
                { 'data_name': name, 'data_value': value, 'data_uom': unit }
                for value, (name, unit) in zip(data[4:], fields)
            ]
        }
    )


def handle_odr_packet(packet):
    # An example packet, see data_thread() in jason-rov/data_thread.cpp:
    #
    # ODR 2021/08/13 21:28:04.332 JAS2 38.95180 -77.14555 17 AT42-01 4444

    data = packet.decode().rstrip('\n').split(' ')

    if not data or data[0] != 'ODR':
        return

    fields = (
        ('latitude', 'ddeg'),
        ('longitude', 'ddeg'),
        ('utm_zone', ''),
        ('cruise_id', ''),
        ('dive_id', ''),
    )

    timestamp = parse_dsl_timestamp(f'{data[1]} {data[2]}')

    # Record this packet to our cache.
    #
    # Note: As in the original Sealog script, we do not convert any data types;
    # everything is passed to Sealog as a string. :(
    add_cache_entry(
        timestamp=timestamp,
        aux_data={
            'data_source': 'vehicleOrigin',
            'data_array': [
                { 'data_name': name, 'data_value': value, 'data_uom': unit }
                for value, (name, unit) in zip(data[4:], fields)
            ]
        }
    )


async def udp_listener(handler):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    s.setblocking(False)
    s.bind(('', ARGS.port))

    while True:
        packet = await asyncio.get_event_loop().sock_recv(s, 1024)
        try:
            handler(packet)
        except:
            logger.exception('An exception occurred while parsing a packet')


async def handle_event(event):
    event_ts = datetime.datetime.strptime(event['message']['ts'],
                                          '%Y-%m-%dT%H:%M:%S.%fZ')\
                                .replace(tzinfo=datetime.timezone.utc)

    aux_data_ts, aux_data = get_cache_entry(event_ts)

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
        udp_listener(ARGS.parser),
    )


if __name__ == '__main__':
    parsers =  {
        'CSV': handle_csv_packet,
        'CTM': handle_ctm_packet,
        'ICL': handle_icl_packet,
        'JDS': handle_jds_packet,
        'ODR': handle_odr_packet,
    }

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--max-age', type=int, default=120,
                        help='Maximum age of an event that will be annotated')
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--type', dest='parser', choices=parsers, required=True)

    ARGS = parser.parse_args()
    ARGS.parser = parsers[ARGS.parser]

    asyncio.run(main())
