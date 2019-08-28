'use strict';

let currentData = [];

$(document).ready(() => {
    getDrivers();
});

function getDrivers() {
    $.ajax({
        type: 'GET',
        url: '/get_drivers'
    }).done(function(resp) {
        if (sameArrays(currentData, resp['drivers'])) {
            return;
        } else {
            currentData = resp['drivers'];
        }

        let $driver;
        let $infoId;
        let driverId;
        let isOnline;
        let $infoName;
        let driverName;
        let $statusColor;
        let $statusPhrase;
        let $infoContainer;
        let $onelineStatus;
        let drivers = resp['drivers'];
        let $virView = $('<div>', { id: 'view' });

        for (let i = 0; i < drivers.length; i++) {
            driverId = drivers[i]['id'];
            driverName = drivers[i]['name'];
            isOnline = drivers[i]['is_online'];

            $infoId = $('<p>', { class: 'info id' });
            $infoName = $('<p>', { class: 'info name' });
            $infoContainer = $('<div>', { class: 'info-container' });
            $driver = $('<div>', {
                class: 'driver',
                onClick: `location.href='/driver?driver_id=${driverId}'`
            });

            $infoName.append(driverName);
            $infoId.append(driverId.slice(0, 12));

            $infoContainer.append($infoName);
            $infoContainer.append($infoId);
            $driver.append($infoContainer);

            $onelineStatus = $('<div>', { class: 'online-status' });
            $statusPhrase = $('<span>', { class: 'status-phrase' });
            $statusColor = $('<div>', {
                class: isOnline ? 'status-color-online' : 'status-color-offline'
            });

            $statusPhrase.append(isOnline ? 'Online' : 'Offline');

            $onelineStatus.append($statusColor);
            $onelineStatus.append($statusPhrase);

            $driver.append($onelineStatus);
            $virView.append($driver);
        }

        $('#view').replaceWith($virView);
    });
}

function sameArrays(array1, array2) {
    if (array1.length != array2.length) {
        return false;
    }

    for (let i = 0; i < array1.length; i++) {
        if (array1[i]['id'] != array2[i]['id'] || array1[i]['is_online'] != array2[i]['is_online']) {
            return false;
        }
    }

    return true;
}

function updateView() {
    getDrivers();
}
