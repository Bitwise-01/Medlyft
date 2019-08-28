'use strict';

let driverId = null;
let currentLogs = [];
let currentDriver = [];
let currentPatients = [];
let currentTaskQueue = [];

$(document).ready(() => {
    driverId = $('#driver-id').text();
    getDriver();
});

function getDriver() {
    $.ajax({
        type: 'POST',
        url: '/get_driver',
        data: { driver_id: driverId }
    }).done(function(resp) {
        let driverInfo = resp['driver_info'];

        setLogs(driverInfo['logs']);
        setDriver(driverInfo['driver']);
        setTaskQueue(driverInfo['tasks']);
        setPatients(driverInfo['patients']);
        setCurrentTask(driverInfo['current_task']);
    });
}

function setDriver(driver) {
    let $driverName = $('<span>', { id: 'driver-name' });
    let $onelineStatus = $('<div>', { class: 'online-status' });
    let $statusPhrase = $('<span>', { class: 'status-phrase' });
    let $statusColor = $('<div>', {
        class: driver['is_online'] ? 'status-color-online' : 'status-color-offline'
    });

    $statusPhrase.append(driver['is_online'] ? 'Online' : 'Offline');
    $driverName.append(driver['name']);
    $onelineStatus.append($statusColor);
    $onelineStatus.append($statusPhrase);

    let $virDriverInfo = $('<div>', { id: 'driver-info' });

    $virDriverInfo.append($driverName);
    $virDriverInfo.append($onelineStatus);

    $('#driver-info').replaceWith($virDriverInfo);
}

function setCurrentTask(currentTask) {
    let $virCurrentTask = $('<div>', { id: 'current-task' });
    let $data = $('<p>');
    let patientName = currentTask['patient_firstname'] + ' ' + currentTask['patient_lastname'];
    let source = currentTask['route_source'];
    let destination = currentTask['route_destination'];

    if (patientName.trim().length) {
        $data.append(`Transport ${patientName} from ${source} to ${destination}`);
    }

    $virCurrentTask.append($data);
    $('#current-task').replaceWith($virCurrentTask);
}

function setLogs(logs) {
    if (sameArrays(currentLogs, logs)) {
        return;
    } else {
        currentLogs = logs;
    }

    let $logMsg;
    let $logData;
    let $timeCreated;
    let $virLog = $('<div>', { id: 'log' });

    for (let n = 0; n < logs.length; n++) {
        $logMsg = $('<span>', { class: 'log-msg' });
        $logData = $('<div>', { class: 'log-data' });
        $timeCreated = $('<span>', { class: 'time-created' });

        $logMsg.append(logs[n]['log']);
        $timeCreated.append(logs[n]['time_created']);

        $logData.append($timeCreated);
        $logData.append($logMsg);

        $virLog.append($logData);
    }

    $('#log').replaceWith($virLog);
}

function setPatients(patients) {
    if (sameArrays(currentPatients, patients)) {
        return;
    } else {
        currentPatients = patients;
    }

    let patientId;
    let firstname;
    let lastname;
    let source;
    let destination;

    let $table = $('<table>');
    let $tr = $('<tr>');
    let $patient;
    let $virNewTask = $('<div>', { id: 'new-task' });

    $tr.append($('<th>').append('Name'));
    $tr.append($('<th>').append('Source'));
    $tr.append($('<th>').append('Destination'));
    $table.append($tr);

    for (let i = 0; i < patients.length; i++) {
        patientId = patients[i]['patient_id'];
        firstname = patients[i]['firstname'];
        lastname = patients[i]['lastname'];
        source = patients[i]['source'];
        destination = patients[i]['destination'];

        $patient = $('<tr>', {
            class: 'patient',
            onClick: `addTask('${patientId}')`,
            title: 'Assign task'
        });
        $patient.append($('<td>').append(firstname + ' ' + lastname));
        $patient.append($('<td>').append(source));
        $patient.append($('<td>').append(destination));

        $table.append($patient);
    }

    $virNewTask.append($table);
    $('#new-task').replaceWith($virNewTask);
}

function addTask(patientId) {
    $.ajax({
        type: 'POST',
        url: '/add_task',
        data: { driver_id: driverId, patient_id: patientId }
    }).done(function(resp) {
        if (resp['resp']) {
            updateView();
        }
    });
}

function setTaskQueue(patients) {
    if (sameArrays(currentTaskQueue, patients)) {
        return;
    } else {
        currentTaskQueue = patients;
    }

    let firstname;
    let lastname;
    let source;
    let destination;
    let taskId;

    let $patient;
    let $tr = $('<tr>');
    let $table = $('<table>');
    let $virTasksQueue = $('<div>', { id: 'tasks-queue' });

    $tr.append($('<th>').append('Name'));
    $tr.append($('<th>').append('Source'));
    $tr.append($('<th>').append('Destination'));
    $table.append($tr);

    for (let i = 0; i < patients.length; i++) {
        taskId = patients[i]['task_id'];
        firstname = patients[i]['patient_firstname'];
        lastname = patients[i]['patient_lastname'];
        source = patients[i]['route_source'];
        destination = patients[i]['route_destination'];

        $patient = $('<tr>', {
            class: 'patient',
            onClick: `removeTask('${taskId}')`,
            title: 'Unassign task'
        });

        $patient.append($('<td>').append(firstname + ' ' + lastname));
        $patient.append($('<td>').append(source));
        $patient.append($('<td>').append(destination));

        $table.append($patient);
    }

    $virTasksQueue.append($table);
    $('#tasks-queue').replaceWith($virTasksQueue);
}

function removeTask(taskId) {
    $.ajax({
        type: 'POST',
        url: '/remove_task',
        data: { task_id: taskId }
    }).done(function(resp) {
        if (resp['resp']) {
            updateView();
        }
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
    getDriver();
}
