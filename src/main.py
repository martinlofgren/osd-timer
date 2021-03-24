#!/usr/bin/env python3

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=20)

users = set()
state = {
    'running': False,
    'time': 60,
}

q = asyncio.Queue()

async def set_state(k, v):
    state[k] = v
    await send_state()


async def events_handler():
    logging.info('events_handler started')
    while True:
        event = await q.get()
        print(f'got event: {event}')


async def update():
    logging.info('update started')
    while True:
        if state['running']:
            await set_state('time', state['time'] - 1)
        await asyncio.sleep(1)


def osd(size, color, outline, delay):
    cmd = f"""osd_cat \
        --pos=top \
        --align=right \
        --font='-*-latin modern sans-*-r-*-*-*-{size}-*-*-*-*-*-*' \
        --color={color} \
        --delay={delay} \
        --outline={outline} \
        --indent={int(size/70)}
        """
    proc = asyncio.create_subprocess_shell(
        cmd,
        stdin=asyncio.subprocess.PIPE)

    return proc

async def clock(queue):
    logging.info('clock started')
    c = osd('', 150, 'white', 2, 1)
    print(c)
    logging.info('clock process started')
    await c.communicate('fisk')
    logging.info('clock stdin written')


async def draw():
    logging.info('draw started')
    q = asyncio.Queue()
    c = asyncio.create_task(clock(q))
    while True:
        if state['running']:
            secs = state['time']
            time_string = f'{secs // 60 :02}:{secs % 60 :02}'
            print(time_string)
        await asyncio.sleep(1)


async def send_state(user=None):
    receivers = [user] if user is not None else users
    if receivers:
        message = json.dumps(state)
        await asyncio.wait([receiver.send(message) for receiver in receivers])


async def handle_message(websocket, message):
    logging.info(f'{websocket.remote_address} sent: {message}')
    try:
        # await q.put('start')
        data = json.loads(message)
        if 'action' in data:
            cmd = data['action']
            if cmd == 'start':
                await set_state('time', data['time'])
                await set_state('running', True)
            elif cmd == 'stop':
                await set_state('running', False)
            elif cmd == 'reset':
                await set_state('time', 0)

    except:
        await websocket.send(json.dumps({'error': f'malformed data: {message}'}))


async def handler(websocket, path):
    users.add(websocket)
    logging.info(f'{websocket.remote_address} connected')
    await send_state(websocket)
    try:
        async for message in websocket:
            await handle_message(websocket, message)
    finally:
        users.remove(websocket)
        logging.info(f'{websocket.remote_address} disconnected')


start_server = websockets.serve(handler, "localhost", 8765)
logging.info('server starting')


try:
    asyncio.get_event_loop().run_until_complete(start_server)

    c1 = asyncio.get_event_loop().create_task(update())
    c2 = asyncio.get_event_loop().create_task(events_handler())
    c3 = asyncio.get_event_loop().create_task(draw())
    asyncio.gather(c1, c2, c3)

    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    print('\r', end='')
    logging.info('server stopping')
