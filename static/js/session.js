'use strict';

const SessionDelay = 7;
let mouseMoved = false;
let isLoggedOut = false;
let updatingSession = false;
let lastUpdated = new Date();
const sessionUpdateDelay = 5 * 1000; // 5 Seconds
const sessionCheckDelay = (60 * SessionDelay + 5) * 1000; // (Session's TTL + a few seconds) 7 minutes + 5 seconds

$(document).ready(() => {
    $(document).mousemove(() => {
        mouseMoved = true;
    });

    setInterval(() => {
        if (mouseMoved) {
            sessionCheck();
        }
    }, sessionUpdateDelay);

    setInterval(sessionCheck, sessionCheckDelay);
});

function sessionCheck() {
    if (isLoggedOut || updatingSession) {
        return;
    }

    if (new Date().getTime() - lastUpdated.getTime() <= sessionUpdateDelay) {
        return;
    }

    updatingSession = true;

    let req = $.ajax({
        type: 'POST',
        url: '/session_check'
    });

    req.done(function(resp) {
        let respCode = resp['resp'];

        mouseMoved = false;
        updatingSession = false;
        lastUpdated = new Date();

        if (respCode != 0) {
            logout();
        } else {
            updateView();
        }
    });

    req.fail(() => {
        logout();
    });
}

function logout() {
    isLoggedOut = true;
    window.location.href = '/';
}
