#!/usr/bin/env python3
'''
This service listens for new events submitted to Sealog and performs additional 
actions depending on the recieved event.

This service listens for 'Off deck' and 'On deck' milestones and enables/
disables the ASNAP functionality and if a lowering is currently active it will
set the start/stop time to the time of the event.

This service listens for 'On bottom' and 'Off bottom' milestones and if a 
lowering is currently active it will set the lowering_on/off_bottom milestone 
time to the time of the event.
'''

import asyncio
import json
import logging
import time

import requests
import websockets

from python_sealog.custom_vars import getCustomVarUIDByName, setCustomVar
from python_sealog.lowerings import getLoweringByEvent
from python_sealog.settings import apiServerURL, headers, loweringsAPIPath, \
                                   wsServerURL


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


ASNAP_STATUS_VAR_NAME = 'asnapStatus'
ASNAP_STATUS_VAR_ID = None

CLIENT_WSID = 'autoActions'

HELLO = {
    'type': 'hello',
    'id': CLIENT_WSID,
    'auth': {'headers': headers},
    'version': '2',
    'subs': ['/ws/status/newEvents', '/ws/status/updateEvents'],
}

PING = {
    'type': 'ping',
    'id': CLIENT_WSID,
}

AUX_DATA_TEMPLATE = {
    'event_id': None,
    'data_source': None,
    'data_array': [],
}


def init_asnap_status_var_id():
    global ASNAP_STATUS_VAR_ID
    ASNAP_STATUS_VAR_ID = getCustomVarUIDByName(ASNAP_STATUS_VAR_NAME)
    logging.info(f'Got asnapStatus variable ID: {ASNAP_STATUS_VAR_ID}') 


def enable_asnap():
    logger.info('Turning ASNAP on')
    setCustomVar(ASNAP_STATUS_VAR_ID, 'On')

def disable_asnap():
    logger.info('Turning ASNAP off')
    setCustomVar(ASNAP_STATUS_VAR_ID, 'Off')


def stamp_lowering_milestone(milestone, event):
    lowering = getLoweringByEvent(event['message']['id'])
    if not lowering:
        logger.warning('Cannot stamp lowering record because there is no '
                       'active lowering')
        return
    
    logger.info(f'Setting {milestone} time for lowering '
                f'{lowering["lowering_id"]} to {event["message"]["ts"]}')

    if milestone in ('start', 'stop'):
        payload = {
            f'{milestone}_ts': event['message']['ts']
        }
    elif milestone in ('on_bottom', 'off_bottom'):
        payload = {
            'lowering_additional_meta': lowering['lowering_additional_meta'],
        }
        payload['lowering_additional_meta'].setdefault('milestones', {})\
               [f'lowering_{milestone}'] = event['message']['ts']
        del payload['lowering_additional_meta']['lowering_files']
    else:
        raise ValueError('Unexpected milestone')

    requests.patch(
        f'{apiServerURL}{loweringsAPIPath}/{lowering["lowering_id"]}',
        headers=headers,
        json=payload,
    )


async def handle_event(event):
    if event['message']['event_value'] != 'VEHICLE':
        return

    for option in event['message']['event_options']:
        option_name_val = (option['event_option_name'],
                           option['event_option_value'])
        
        if option_name_val == ('milestone', 'Alvin off deck'):
            stamp_lowering_milestone('start', event)

        elif option_name_val == ('milestone', 'On bottom'):
            enable_asnap()
            stamp_lowering_milestone('on_bottom', event)
        
        elif option_name_val == ('milestone', 'Off bottom'):
            disable_asnap()
            stamp_lowering_milestone('off_bottom', event)
        
        elif option_name_val == ('milestone', 'Alvin on deck'):
            stamp_lowering_milestone('stop', event)


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
    try:
        init_asnap_status_var_id()
    except:
        logger.exception('Could not resolve asnapStatus variable ID')
        quit()

    asyncio.run(event_listener())
