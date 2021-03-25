#!/usr/bin/env python3

# TODOS
#
# - Use computers clock instead of decreasing counter based on waiting, to
#   increase precision

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=20)

state_changed = asyncio.Event()

users = set()
state = {
    'running': False,
    'time': 5,
}

async def set_state(k, v):
    state[k] = v
    state_changed.set()
    await send_state()


async def update():
    logging.info('update started')
    while True:
        if state['running']:
            await set_state('time', state['time'] - 1)
        await asyncio.sleep(1)


async def osd(size, color, outline, delay):
    cmd = f"osd_cat --pos=top --align=right --font='-*-latin modern sans-*-r-*-*-*-{size}-*-*-*-*-*-*' --color={color} --delay={delay} --outline={outline} --indent={int(size/70)} -l 1 -s 3"

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdin=asyncio.subprocess.PIPE,
    )

    return proc


async def clock(queue):
    logging.info('clock task started')
    proc = await osd(500, 'white', 2, 2)
    while True:
        time_string = await queue.get()
        proc.stdin.write(f'{time_string}\n'.encode('utf-8'))


async def draw():
    logging.info('draw started')
    q = asyncio.Queue()
    c = asyncio.create_task(clock(q))
    logging.info('clock spawned')
    while True:
        await state_changed.wait()
        state_changed.clear()
        if state['running']:
            secs = state['time']
            if secs < 0:
                secs = -secs
                sign = '-'

            else:
                sign = ''
            time_string = f'{sign}{secs // 60 :02}:{secs % 60 :02}'
            await q.put(time_string)


async def send_state(user=None):
    receivers = [user] if user is not None else users
    if receivers:
        message = json.dumps(state)
        await asyncio.wait([receiver.send(message) for receiver in receivers])


async def handle_message(websocket, message):
    logging.info(f'{websocket.remote_address} sent: {message}')
    try:
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

    updater = asyncio.get_event_loop().create_task(update())
    drawer = asyncio.get_event_loop().create_task(draw())
    asyncio.gather(updater, drawer)

    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    print('\r', end='')
    logging.info('server stopping')
