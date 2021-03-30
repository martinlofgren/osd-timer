'use strict'

const dom_min = document.getElementById('min');
const dom_sec = document.getElementById('sec');
const dom_toggle = document.getElementById('toggle');

const dom_time_div = document.getElementById('time');
const dom_offline_div = document.getElementById('offline');

const url = new URL(document.URL)
const address = `ws://192.168.1.33:8765`
// var socket;

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

function connect() {
    const socket = new WebSocket(address);

    socket.addEventListener('message', event => {
        const payload = JSON.parse(event.data);
        state.running = payload.running;
        min = payload.time / 60;
        state.time.min = (min > 0) ? Math.floor(min) : Math.ceil(min);
        state.time.sec = payload.time % 60;
        update();
    });

    socket.addEventListener('open' , event => {
        dom_offline_div.style.opacity = 0;
        dom_time_div.style.opacity = 100;
    });

    const shit = e => {
        dom_offline_div.style.opacity = 100;
        dom_time_div.style.opacity = 0;
    }

    socket.addEventListener('error' , e => {
        shit();
        window.setTimeout(connect, 2000);
    });
    socket.addEventListener('close' , shit);

    dom_toggle.addEventListener('click', event => {
        const action = {
            'action': state.running ? 'stop' : 'start',
            'time': parseInt(dom_min.value) * 60 + parseInt(dom_sec.value)
        };
        socket.send(JSON.stringify(action));
        dom_toggle.blur();
    });
}

connect()
