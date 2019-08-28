'use strict';

let currentData = [];

$(document).ready(() => {
    getPatients();
});

function getPatients() {
    $.ajax({
        type: 'GET',
        url: '/get_patients'
    }).done(function(resp) {
        if (sameArrays(currentData, resp['patients'])) {
            return;
        } else {
            currentData = resp['patients'];
        }

        let source;
        let status;
        let $patient;
        let lastname;
        let firstname;
        let patientId;
        let destination;
        let patients = resp['patients'];
        let $virView = $('<div>', { id: 'view' });

        let $table = $('<table>');
        let $tr = $('<tr>');

        $tr.append($('<th>').append('Firstname'));
        $tr.append($('<th>').append('Lastname'));
        $tr.append($('<th>').append('Source'));
        $tr.append($('<th>').append('Destination'));
        $tr.append($('<th>').append('Status'));
        $table.append($tr);

        for (let i = 0; i < patients.length; i++) {
            patientId = patients[i]['id'];
            firstname = patients[i]['firstname'];
            lastname = patients[i]['lastname'];
            source = patients[i]['source'];
            destination = patients[i]['destination'];
            status = patients[i]['status'];

            $patient = $('<tr>');
            $patient.append($('<td>').append(firstname));
            $patient.append($('<td>').append(lastname));
            $patient.append($('<td>').append(source));
            $patient.append($('<td>').append(destination));
            $patient.append($('<td>').append(status));

            $table.append($patient);
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
    getPatients();
}
