'use strict'

const url = new URL(document.URL)
const address = `ws://${url.hostname}:8765`

const socket = new WebSocket(address);

const dom_min = document.getElementById('min');
const dom_sec = document.getElementById('sec');
const dom_toggle = document.getElementById('toggle');

let state = {
    running: false,
    time: {
        min: null,
        sec: null,
    }
}

function update() {
    dom_min.value = state.time.min;
    dom_sec.value = state.time.sec;
    dom_min.disabled = state.running;
    dom_sec.disabled = state.running;
    dom_toggle.value = (state.running ? 'Stanna' : 'Starta') + ' klockan';
}

socket.addEventListener('message', event => {
    const payload = JSON.parse(event.data);
    state.running = payload.running;
    state.time.min = Math.floor(payload.time / 60);
    state.time.sec = payload.time % 60;
    update();
});

dom_toggle.addEventListener('click', event => {
    const action = {
        'action': state.running ? 'stop' : 'start',
        'time': parseInt(dom_min.value) * 60 + parseInt(dom_sec.value)
    };
    socket.send(JSON.stringify(action));
});
