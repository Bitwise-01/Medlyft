# Date: 04/01/2019
# Author: Mohamed
# Description: MedLyft

import os
import sys
from time import time
from datetime import timedelta
from lib.database import Medlyft
from lib.const import SessionConst, CredentialConst
from flask import Flask, flash, render_template, request, session, jsonify, redirect, url_for

# app
if getattr(sys, 'frozen', False):
    path = os.path.abspath('.')

    if not os.path.exists('database'):
        os.mkdir(os.path.join(path, 'database'))

    static_folder = os.path.join(path, 'static')
    template_folder = os.path.join(path, 'templates')

    app = Flask(__name__, template_folder=template_folder,
                static_folder=static_folder)
else:
    app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(0x20)
app.permanent_session_lifetime = timedelta(
    minutes=SessionConst.SESSION_TTL.value)

# database
database = Medlyft()


def login_required(func):
    def wrapper(*args, **kwargs):
        if not 'logged_in' in session:
            return redirect(url_for('index'))
        elif not session['logged_in']:
            return redirect(url_for('index'))
        else:
            return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


def get_driver_info(driver_id):
    return {
        'logs': database.get_logs(driver_id),
        'tasks': database.get_tasks(driver_id),
        'driver': database.get_driver(driver_id),
        'patients': database.get_waiting_patients(),
        'current_task': database.get_current_task(driver_id)
    }

# endpoints
@app.before_request
def single_browser():

    if not 'logged_in' in session:
        return

    if not session['logged_in']:
        return

    if (time() - session['last_checked']) < 5:
        return

    user_id = session['user_id']
    session_token = session['token']
    session['last_checked'] = time()

    if not database.is_logged_in(user_id, session_token):
        logout()


@app.route('/session_check', methods=['POST'])
@login_required
def session_check():
    database.update_online_status(session['user_id'])
    return jsonify({'resp': 0})


@app.route('/')
def index():
    if not 'logged_in' in session:
        session['logged_in'] = False
        return render_template('index.html')

    if not session['logged_in']:
        username = session.get('username')
        username = username if username else ''

        if username:
            session.pop('username')

        return render_template('index.html', username=username)

    flash(session['last_active'])
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not 'logged_in' in session:
        return redirect(url_for('index'))

    if not session['logged_in']:
        if not ('username' in request.form, 'password' in request.form):
            return redirect(url_for('index'))

        username = request.form['username'].strip().lower()
        password = request.form['password'].strip()

        if ((len(password) > CredentialConst.MAX_PASSWORD_LENGTH.value) or
                (len(username) > CredentialConst.MAX_USERNAME_LENGTH.value) or
                (len(username) < CredentialConst.MIN_USERNAME_LENGTH.value)
                ):
            return redirect(url_for('index'))

        session['username'] = username
        account_data = database.authenticate(
            username, password, request.remote_addr)

        if account_data:
            user_id, token, last_active = account_data

            session['token'] = token
            session.permanent = True
            session['logged_in'] = True
            session['user_id'] = user_id
            session['last_checked'] = time()
            session['last_active'] = last_active
            session['username'] = username.title()

            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/get_drivers', methods=['GET'])
@login_required
def get_drivers():
    resp = {
        'drivers': database.get_drivers()
    }

    return jsonify(resp)


@app.route('/get_driver', methods=['POST'])
@login_required
def get_driver():

    resp = {'driver_info': ''}

    if not 'driver_id' in request.form:
        return jsonify(resp)

    driver_id = request.form['driver_id'].strip()

    if not driver_id:
        return jsonify(resp)

    return jsonify({
        'driver_info': get_driver_info(driver_id)
    })


@app.route('/driver', methods=['GET'])
@login_required
def driver():
    driver_id = request.args.get('driver_id')

    if not driver_id:
        return render_template(url_for('index'))

    data = database.driver_exists(driver_id)

    if not data:
        return render_template(url_for('index'))

    flash(session['last_active'])
    return render_template('driver.html', driver_id=driver_id)


@app.route('/patients')
@login_required
def patients():
    flash(session['last_active'])
    return render_template('patients.html')


@app.route('/get_patients', methods=['GET'])
@login_required
def get_patients():
    resp = {
        'patients': database.get_patients()
    }

    return jsonify(resp)


@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    resp = {'resp': 0}

    if not ('driver_id' in request.form and 'patient_id' in request.form):
        return jsonify(resp)

    dispatcher_id = session['user_id']
    driver_id = request.form['driver_id'].strip()
    patient_id = request.form['patient_id'].strip()

    if not (database.driver_exists(driver_id) and database.patient_exists(patient_id) and database.dispatcher_exists(dispatcher_id)):
        return jsonify(resp)

    database.add_task(driver_id, patient_id, dispatcher_id)

    return jsonify({'resp': 1})


@app.route('/remove_task', methods=['POST'])
@login_required
def remove_task():
    resp = {'resp': 0}

    if not 'task_id' in request.form:
        return jsonify(resp)

    task_id = request.form['task_id']
    dispatcher_id = session['user_id']

    if not database.task_exists(task_id) or not database.dispatcher_exists(dispatcher_id):
        return jsonify(resp)

    database.remove_task(task_id, dispatcher_id)

    return jsonify({'resp': 1})


@app.route('/get_all_tasks', methods=['GET'])
@login_required
def get_all_tasks():
    return jsonify({'tasks': database.get_all_tasks()})


@app.route('/tasks')
@login_required
def tasks():
    flash(session['last_active'])
    return render_template('tasks.html')


if __name__ == '__main__':
    app.run(debug=True)
    database.db_close()
