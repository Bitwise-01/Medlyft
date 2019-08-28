'use strict';

let currentData = [];

$(document).ready(() => {
    getTasks();
});

function getTasks() {
    $.ajax({
        type: 'GET',
        url: '/get_all_tasks'
    }).done(function(resp) {
        if (sameArrays(currentData, resp['tasks'])) {
            return;
        } else {
            currentData = resp['tasks'];
        }

        let $task;
        let source;
        let driver;
        let firstname;
        let lastname;
        let destination;
        let tasks = resp['tasks'];
        let $virView = $('<div>', { id: 'view' });

        let $table = $('<table>');
        let $tr = $('<tr>');

        $tr.append($('<th>').append('Name'));
        $tr.append($('<th>').append('Source'));
        $tr.append($('<th>').append('Destination'));
        $tr.append($('<th>').append('Driver'));
        $table.append($tr);

        for (let i = 0; i < tasks.length; i++) {
            firstname = tasks[i]['patient_firstname'];
            lastname = tasks[i]['patient_lastname'];
            source = tasks[i]['route_source'];
            destination = tasks[i]['route_destination'];
            driver = tasks[i]['driver_name'];

            $task = $('<tr>');
            $task.append($('<td>').append(firstname + ' ' + lastname));
            $task.append($('<td>').append(source));
            $task.append($('<td>').append(destination));
            $task.append($('<td>').append(driver));

            $table.append($task);
        }

        $virView.append($table);
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
    getTasks();
}
