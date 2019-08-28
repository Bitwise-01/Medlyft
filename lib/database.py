# Date: 02/08/2019
# Author: Mohamed
# Description: DBMS

import bcrypt
from sys import exit
from time import time
from os import urandom
from hashlib import sha256
from datetime import datetime
import mysql.connector as mysql
from base64 import b64encode, b64decode
from lib.const import DatabaseConst, SessionConst, CredentialConst, EmployeeConst, PatientConst


class DatabaseWrapper:

    def __init__(self, db_name):
        self.db_name = db_name
        self.database = self.db_connect(db_name)

    def db_connect(self, db_name):
        try:
            return mysql.connect(
                database=db_name,
                host=DatabaseConst.HOST.value,
                user=DatabaseConst.USER.value,
                password=DatabaseConst.PASSWORD.value
            )
        except mysql.errors.InterfaceError:
            exit('[!] Error: Failed to connect to SQL server')

    def reconnect(self):
        self.database = self.db_connect(self.db_name)

    def db_close(self):
        if self.database:
            self.database.close()

    def db_query(self, cmd, args=[], fetchone=True, tries=3):

        try:
            cursor = self.database.cursor()
        except mysql.errors.OperationalError:
            if tries:
                self.reconnect()
                return self.db_query(cmd, args, fetchone, tries-1)
            else:
                raise mysql.errors.OperationalError

        cursor.execute(cmd, args)
        data = cursor.fetchone()[0] if fetchone else cursor.fetchall()
        return data

    def db_execute(self, cmd, args=[], tries=3):
        try:
            self.database.cursor().execute(cmd, args)
        except mysql.errors.OperationalError:
            if tries:
                self.reconnect()
                self.db_execute(cmd, args, tries-1)
            else:
                raise mysql.errors.OperationalError

        self.database.commit()


class Medlyft(DatabaseWrapper):

    def __init__(self):
        super().__init__(DatabaseConst.DATABASE_NAME.value)
        self.create_tables()

    def create_tables(self):

        # account
        self.db_execute('''
        CREATE TABLE IF NOT EXISTS
        tbl_account(
            user_id VARCHAR(64),
            username VARCHAR(32),
            password BLOB,
            employee_type INTEGER,

            PRIMARY KEY(user_id)
        );
        ''')

        self.db_execute('''
        CREATE TABLE IF NOT EXISTS
        tbl_status(
            last_online BIGINT,
            time_created BIGINT,
            ip_address VARCHAR(15),
            session_token VARCHAR(64),
            stat_id VARCHAR(64) NOT NULL,

            FOREIGN KEY(stat_id) REFERENCES tbl_account(user_id),
            PRIMARY KEY(stat_id)
        );
        ''')

        self.db_execute('''
        CREATE TABLE IF NOT EXISTS
        tbl_attempt(
            last_attempt BIGINT,
            attempts_made INT DEFAULT 0,
            ampt_id VARCHAR(64) NOT NULL,

            FOREIGN KEY(ampt_id) REFERENCES tbl_account(user_id),
            PRIMARY KEY(ampt_id)
        );
        ''')

        self.db_execute('''
        CREATE TABLE IF NOT EXISTS
        tbl_lock(
            lock_id VARCHAR(64) NOT NULL,
            time_locked BIGINT DEFAULT 0,
            
            FOREIGN KEY(lock_id) REFERENCES tbl_account(user_id),
            PRIMARY KEY(lock_id)
        );
        ''')

        # log
        self.db_execute('''
        CREATE TABLE IF NOT EXISTS
        tbl_log(
            log_id INT AUTO_INCREMENT,
            time_created BIGINT,
            account_id VARCHAR(64),
            log TEXT,

            FOREIGN KEY(account_id) REFERENCES tbl_account(user_id),
            PRIMARY KEY(log_id)
        );
        ''')

        # dispatcher
        self.db_execute('''
        CREATE TABLE IF NOT EXISTS
        tbl_dispatcher(
            name VARCHAR(32),
            dispatcher_id VARCHAR(64),

            FOREIGN KEY(dispatcher_id) REFERENCES tbl_account(user_id), 
            PRIMARY KEY(dispatcher_id)
        );
        ''')

        # driver
        self.db_execute(''' 
        CREATE TABLE IF NOT EXISTS
        tbl_driver(
            name VARCHAR(32),
            driver_id VARCHAR(64),
            current_task_id INT,

            FOREIGN KEY(driver_id) REFERENCES tbl_account(user_id),
            FOREIGN KEY(current_task_id) REFERENCES tbl_task(task_id),
            PRIMARY KEY(driver_id)
        );
        ''')

        # car
        self.db_execute('''
        CREATE TABLE IF NOT EXISTS
        tbl_car(
            car_id INT AUTO_INCREMENT,
            driver_id VARCHAR(64),

            FOREIGN KEY(driver_id) REFERENCES tbl_driver(driver_id),
            PRIMARY KEY(car_id)
        );
        ''')

        # route
        self.db_execute('''
        CREATE TABLE IF NOT EXISTS
        tbl_route(
            route_id VARCHAR(64),
            source VARCHAR(64),
            status TINYINT(1),
            destination VARCHAR(64),

            PRIMARY KEY(route_id)
        );
        ''')

        # patient
        self.db_execute('''
        CREATE TABLE IF NOT EXISTS
        tbl_patient(
            patient_id VARCHAR(64),
            firstname VARCHAR(64),
            lastname VARCHAR(64),
            route_id VARCHAR(64),

            FOREIGN KEY(route_id) REFERENCES tbl_route(route_id),
            PRIMARY KEY(patient_id)
        );
        ''')

        # task
        self.db_execute('''
        CREATE TABLE IF NOT EXISTS
        tbl_task(
            task_id INT AUTO_INCREMENT,
            time_created BIGINT,
            driver_id VARCHAR(64),
            patient_id VARCHAR(64),
            dispatcher_id VARCHAR(64),

            FOREIGN KEY(driver_id) REFERENCES tbl_account(user_id),
            FOREIGN KEY(patient_id) REFERENCES tbl_patient(patient_id),
            FOREIGN KEY(dispatcher_id) REFERENCES tbl_dispatcher(dispatcher_id),
            PRIMARY KEY(task_id)
        );
        ''')

    def register(self, username, password, employee_type, name):

        username = username.strip().lower()
        password = password.strip()
        time_created = time()
        name = name.strip()

        if not len(username) or not len(password) or not len(name):
            return 'All field must be supplied'

        # username
        if len(username) < CredentialConst.MIN_USERNAME_LENGTH.value:
            return f'Username must have at least {CredentialConst.MIN_USERNAME_LENGTH.value}'

        if len(username) > CredentialConst.MAX_USERNAME_LENGTH.value:
            return f'Username must have no more than {CredentialConst.MAX_USERNAME_LENGTH.value}'

        if self.username_exists(username):
            return 'Account already exists'

        # password
        if len(password) < CredentialConst.MIN_PASSWORD_LENGTH.value:
            return f'Password must have at least {CredentialConst.MIN_PASSWORD_LENGTH.value}'

        if len(password) > CredentialConst.MAX_PASSWORD_LENGTH.value:
            return f'Password must have no more than {CredentialConst.MAX_PASSWORD_LENGTH.value}'

        # employee
        if not [_.value for _ in EmployeeConst if _.value['id'] == employee_type]:
            return f'Employee type is unknown'

        hashed_password = self.hash_password(password)
        user_id = self.generate_user_id(username, password)

        # account
        self.db_execute('''
        INSERT INTO tbl_account(user_id, username, password, employee_type)
        VALUES(%s, %s, %s, %s);
        ''', [user_id, username, hashed_password, employee_type]
        )

        self.db_execute('''
        INSERT INTO tbl_status(last_online, time_created, stat_id)
        VALUES(%s, %s, %s);
        ''', [time_created, time_created, user_id]
        )

        self.db_execute('''
        INSERT INTO tbl_attempt(last_attempt, ampt_id)
        VALUES(%s, %s);
        ''', [time_created, user_id]
        )

        self.db_execute('''
        INSERT INTO tbl_lock(lock_id)
        VALUES(%s);
        ''', [user_id]
        )

        # driver
        if EmployeeConst.DRIVER.value['id'] == employee_type:
            self.db_execute('''
            INSERT INTO tbl_driver(driver_id, name)
            VALUES(%s, %s);
            ''', [user_id, name])

            self.db_execute('''
            INSERT INTO tbl_car(driver_id)
            VALUES(%s);
            ''', [user_id])

        # dispatcher
        if EmployeeConst.DISPATCHER.value['id'] == employee_type:
            self.db_execute('''
            INSERT INTO tbl_dispatcher(dispatcher_id, name)
            VALUES(%s, %s);
            ''', [user_id, name])

        self.log(user_id, 'Account created')

        return 'Account created successfully'

    def log(self, user_id, log):
        self.db_execute('''
        INSERT INTO tbl_log(time_created, account_id, log)
        VALUES(%s, %s, %s);
        ''', [time(), user_id, log])

    def delete_account(self, user_id):
        self.db_execute('DELETE FROM tbl_lock WHERE lock_id=%s;', [user_id])
        self.db_execute('DELETE FROM tbl_status WHERE stat_id=%s;', [user_id])
        self.db_execute('DELETE FROM tbl_attempt WHERE ampt_id=%s;', [user_id])
        self.db_execute('DELETE FROM tbl_account WHERE user_id=%s;', [user_id])
        return 'Account deleted successfully'

    # -------- Authenticate -------- #

    def account_exists(self, username):
        data = self.db_query(
            'SELECT * FROM tbl_account WHERE username=%s;', [username], False)
        return True if len(data) else False

    def compare_passwords(self, user_id, password):
        hashed_password = self.db_query(
            'SELECT password FROM tbl_account WHERE user_id=%s;', [user_id])
        return True if bcrypt.hashpw(password.encode(), hashed_password) == hashed_password.encode else False

    def check_password(self, username, password):
        hashed_password = self.db_query(
            'SELECT password FROM tbl_account WHERE username=%s;', [username])     
        return True if bcrypt.hashpw(password.encode(), hashed_password.encode()) == hashed_password.encode() else False

    def authenticate(self, username, password, ip_address):
        if self.account_exists(username):
            user_id = self.get_user_id(username)

            if not self.is_locked(user_id):
                if self.check_password(username, password):

                    # Remove commented sections if you do not want the drivers to login through the web api
                    # is_dispatcher = True if self.db_query('''
                    # SELECT employee_type
                    # FROM tbl_account
                    # WHERE user_id = %s;
                    # ''', [user_id]) == EmployeeConst.DISPATCHER.value['id'] else False

                    # if not is_dispatcher:
                    #     return None

                    token = self.generate_session_token(user_id)
                    last_active = self.get_last_active(user_id)
                    self.login(user_id, token, ip_address)

                    return user_id, token, last_active
                else:
                    self.failed_attempt(user_id)
        return None

    def login(self, user_id, token, ip_address):
        self.db_execute(
            'UPDATE tbl_attempt SET attempts_made=%s WHERE ampt_id=%s;', [0, user_id])
        self.db_execute('UPDATE tbl_status SET session_token=%s WHERE stat_id=%s;',
                        [token, user_id])
        self.db_execute('UPDATE tbl_status SET ip_address=%s WHERE stat_id=%s;',
                        [ip_address, user_id])

        self.log(user_id, f'Logged in from {ip_address}')

    def update_online_status(self, user_id):
        self.db_execute('UPDATE tbl_status SET last_online=%s WHERE stat_id=%s;', [
            time(), user_id])

    def logout(self, user_id):
        token = self.generate_session_token(user_id)
        self.db_execute('UPDATE tbl_status SET session_token=%s WHERE stat_id=%s;',
                        [token, user_id])

    def is_logged_in(self, user_id, session_token):

        token = self.db_query(
            'SELECT session_token FROM tbl_status WHERE stat_id=%s;', [user_id])

        if token != session_token:
            return False
        return True

    # -------- Attempts -------- #

    def lock_account(self, user_id):
        self.log(user_id, 'Account locked')
        self.db_execute('UPDATE tbl_lock SET time_locked=%s WHERE lock_id=%s;',
                        [time(), user_id])

    def failed_attempt(self, user_id):
        current_value = self.failed_attempts_counts(user_id)

        if current_value >= DatabaseConst.MAX_FAILED_ATTEMPTS.value-1:
            if not self.is_locked(user_id):
                self.lock_account(user_id)
        else:
            self.db_execute('UPDATE tbl_attempt SET attempts_made=%s WHERE ampt_id=%s;',
                            [current_value + 1, user_id])

    def failed_attempts_counts(self, user_id):
        return self.db_query('SELECT attempts_made FROM tbl_attempt WHERE ampt_id=%s;', [user_id])

    def is_locked(self, user_id):
        time_locked = self.locked(user_id)

        if time_locked:

            if (time() - time_locked) >= DatabaseConst.LOCK_TIME.value:
                self.remove_locked_account(user_id)
                return False
            else:
                return True
        else:
            return False

    def locked(self, user_id):
        return self.db_query('''
            SELECT time_locked
            FROM tbl_lock
            INNER JOIN tbl_account ON tbl_account.user_id = tbl_lock.lock_id
            WHERE tbl_lock.lock_id=%s;
            ''', [user_id]
        )

    def remove_locked_account(self, user_id):
        self.log(user_id, 'Account unlocked')
        self.db_execute(
            'UPDATE tbl_attempt SET attempts_made=%s WHERE ampt_id=%s;', [0, user_id])

    # -------- Misc -------- #

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    def generate_user_id(self, username, password, n=2):
        a = b64encode(username.encode() + password.encode() +
                      urandom(64 * 64)).hex()
        b = b64encode(username.encode() + password.encode() +
                      urandom(64 * 64)).hex()

        c = sha256(a.encode() + b.encode()).digest().hex()

        return self.generate_user_id(a, b, n-1) if n else c

    def generate_session_token(self, user_id):
        return sha256(user_id.encode() + urandom(64 * 64) + str(time()).encode()).digest().hex()

    def get_last_active(self, user_id):
        epoch = self.db_query(
            'SELECT last_online FROM tbl_status WHERE stat_id=%s;', [user_id])

        self.update_online_status(user_id)
        return datetime.fromtimestamp(epoch).strftime('%b %d, %Y at %I:%M %p')

    def get_user_id(self, username):
        return self.db_query('SELECT user_id FROM tbl_account WHERE username=%s;', [username])

    def user_id_exists(self, user_id):
        return self.db_query('SELECT COUNT(*) FROM tbl_account WHERE user_id=%s;', [user_id])

    def username_exists(self, username):
        return self.db_query('SELECT COUNT(*) FROM tbl_account WHERE username=%s;', [username])

    # -------- API's -------- #

    # dispatcher

    def dispatcher_exists(self, dispatcher_id):
        return True if self.db_query('''
        SELECT * 
        FROM tbl_dispatcher 
        WHERE dispatcher_id = %s;
        ''', [dispatcher_id], fetchone=False) else False

    # drivers

    def get_drivers(self):
        drivers = []

        for driver in self.db_query('''
            SELECT tbl_driver.driver_id, tbl_driver.name, tbl_status.last_online
            FROM tbl_status
            INNER JOIN tbl_driver ON tbl_driver.driver_id = tbl_status.stat_id
            ORDER BY tbl_status.last_online DESC, tbl_driver.name ASC;
            ''', fetchone=False):

            last_online = self.db_query(
                'SELECT last_online FROM tbl_status WHERE stat_id=%s;', [driver[0]])

            is_online = False if (
                time() - last_online) > SessionConst.MIN_SILENCE_TIME.value else True

            drivers.append(
                {
                    'id': driver[0],
                    'name': driver[1],
                    'is_online': is_online
                }
            )

        return drivers

    def get_driver(self, driver_id):
        name, last_online = self.db_query('''
        SELECT tbl_driver.name, tbl_status.last_online
        from tbl_driver
        INNER JOIN tbl_status on tbl_driver.driver_id = tbl_status.stat_id
        WHERE tbl_driver.driver_id = %s;
        ''', [driver_id], fetchone=False)[0]

        return {
            'driver_id': driver_id,
            'name': name,
            'is_online': False if (time() - last_online) > SessionConst.MIN_SILENCE_TIME.value else True
        }

    def driver_exists(self, driver_id):
        return True if self.db_query('''
        SELECT name
        FROM tbl_driver
        WHERE driver_id = %s;
        ''', [driver_id], fetchone=False) else False

    # route

    def add_route(self, pick_time, source, destin):
        route_id = self.generate_user_id(source, destin)
        self.db_execute('''
        INSERT INTO tbl_route(route_id, pick_time, source, destination, status)
        VALUES(%s, %s, %s, %s, %s);''', [route_id, pick_time, source, destin, 0])
        return route_id

    # patients

    def add_patient(self, firstname, lastname, source, destin):
        firstname, lastname = firstname.lower(), lastname.lower()
        patient_id = self.generate_user_id(firstname, lastname)
        route_id = self.add_route(time(), source, destin)

        self.db_execute('''
        INSERT INTO tbl_patient(patient_id, firstname, lastname, route_id)
        VALUES(%s, %s, %s, %s);
        ''', [patient_id, firstname, lastname, route_id])

    def get_patients(self):
        patients = []

        for patient in self.db_query('''
        SELECT tbl_patient.patient_id, tbl_patient.firstname, tbl_patient.lastname, tbl_route.source, tbl_route.destination, tbl_route.status
        FROM tbl_patient
        INNER JOIN tbl_route ON tbl_patient.route_id = tbl_route.route_id
        ORDER BY tbl_patient.firstname ASC, tbl_patient.lastname ASC;
        ''', fetchone=False):

            patients.append({
                'patient_id': patient[0],
                'firstname': patient[1].title(),
                'lastname': patient[2].title(),
                'source': patient[3].title(),
                'destination': patient[4].title(),
                'status':  PatientConst.STATUS.value[patient[5]]
            })

        return patients

    def get_waiting_patients(self):
        patients = []

        for patient in self.db_query('''
        SELECT tbl_patient.patient_id, tbl_patient.firstname, tbl_patient.lastname, tbl_route.source, tbl_route.destination
        FROM tbl_patient
        INNER JOIN tbl_route ON tbl_patient.route_id = tbl_route.route_id
        WHERE tbl_route.status = %s AND tbl_patient.patient_id NOT  IN (SELECT tbl_task.patient_id FROM tbl_task)
        ORDER BY tbl_patient.firstname ASC, tbl_patient.lastname ASC;
        ''', [PatientConst._STATUS.value['Waiting']], fetchone=False):

            patients.append({
                'patient_id': patient[0],
                'firstname': patient[1].title(),
                'lastname': patient[2].title(),
                'source': patient[3].title(),
                'destination': patient[4].title()
            })

        return patients

    def patient_exists(self, patient_id):
        return True if self.db_query('''
        SELECT * 
        FROM tbl_patient
        WHERE patient_id = %s;
        ''', [patient_id], fetchone=False) else False

    # tasks

    def add_task(self, driver_id, patient_id, dispatcher_id):
        self.db_execute('''
        INSERT INTO tbl_task(time_created, driver_id, patient_id, dispatcher_id)
        VALUES(%s, %s, %s, %s);
        ''', [time(), driver_id, patient_id, dispatcher_id])

        patient_firstname, patient_lastname, source, destin = self.db_query('''
        SELECT tbl_patient.firstname, tbl_patient.lastname, tbl_route.source, tbl_route.destination
        FROM tbl_patient
        INNER JOIN tbl_route ON tbl_patient.route_id = tbl_route.route_id
        WHERE tbl_patient.patient_id = %s;
        ''', [patient_id], fetchone=False)[0]

        dispatcher_name = self.db_query('''
        SELECT name 
        from tbl_dispatcher
        WHERE dispatcher_id = %s;
        ''', [dispatcher_id])

        log1 = 'Requested by {} to pick {} {} from {} to {}'.format(
            dispatcher_name.title(),
            patient_firstname.title(), patient_lastname.title(),
            source.title(), destin.title()
        )

        log2 = 'Requested {} to pick {} {} from {} to {}'.format(
            self.db_query('''
            SELECT name 
            FROM tbl_driver
            WHERE tbl_driver.driver_id = %s;
            ''', [driver_id]).title(),

            patient_firstname.title(), patient_lastname.title(),
            source.title(), destin.title()
        )

        self.log(driver_id, log1)
        self.log(dispatcher_id, log2)

    def remove_task(self, task_id, dispatcher_id):
        task_info = self.get_task_info(task_id)

        driver_id = task_info['driver_id']
        driver_name = task_info['driver_name']

        dispatcher_name = self.db_query('''
        SELECT name 
        FROM tbl_dispatcher
        WHERE dispatcher_id = %s;
        ''', [dispatcher_id])

        patient_name = task_info['patient_firstname'] + \
            ' ' + task_info['patient_lastname']

        route_source = task_info['route_source']
        route_destination = task_info['route_destination']

        log1 = '{} removed the task for transporting {} from {} to {}'.format(
            dispatcher_name, patient_name, route_source, route_destination)

        log2 = 'Removed task from {} for transporting {} from {} to {}'.format(
            driver_name, patient_name, route_source, route_destination)

        self.log(driver_id, log1)
        self.log(dispatcher_id, log2)

        self.db_execute('''
        DELETE FROM tbl_task
        WHERE task_id = %s;
        ''', [task_id])

    def get_tasks(self, driver_id):
        tasks = []

        for task in self.db_query('''
        SELECT tbl_task.task_id, tbl_patient.firstname, tbl_patient.lastname, 
        tbl_route.source, tbl_route.destination
        FROM tbl_task
        JOIN tbl_patient ON tbl_task.patient_id = tbl_patient.patient_id
        JOIN tbl_route ON tbl_patient.route_id = tbl_route.route_id
        WHERE tbl_task.driver_id = %s
        ORDER BY tbl_task.time_created ASC;
        ''', [driver_id], fetchone=False):

            tasks.append({
                'task_id': task[0],
                'patient_firstname': task[1].title(),
                'patient_lastname': task[2].title(),
                'route_source': task[3].title(),
                'route_destination': task[4].title()
            })

        return tasks

    def get_all_tasks(self):
        tasks = []

        for task in self.db_query('''
        SELECT tbl_patient.firstname, tbl_patient.lastname, 
        tbl_route.source, tbl_route.destination, tbl_driver.name
        FROM tbl_task
        JOIN tbl_patient ON tbl_task.patient_id = tbl_patient.patient_id
        JOIN tbl_route ON tbl_patient.route_id = tbl_route.route_id
        JOIN tbl_driver ON tbl_task.driver_id = tbl_driver.driver_id
        ORDER BY tbl_task.time_created ASC;
        ''', fetchone=False):

            tasks.append({
                'patient_firstname': task[0].title(),
                'patient_lastname': task[1].title(),
                'route_source': task[2].title(),
                'route_destination': task[3].title(),
                'driver_name': task[4].title()
            })

        return tasks

    def task_exists(self, task_id):
        return self.db_query('''
        SELECT *
        FROM tbl_task
        WHERE task_id = %s;
        ''', [task_id])

    def get_task_info(self, task_id):
        sql = self.db_query('''
        SELECT tbl_dispatcher.dispatcher_id, tbl_dispatcher.name, 
        tbl_driver.driver_id, tbl_driver.name,
        tbl_patient.firstname, tbl_patient.lastname,
        tbl_route.source, tbl_route.destination
        FROM tbl_task
        INNER JOIN tbl_dispatcher ON tbl_task.dispatcher_id = tbl_dispatcher.dispatcher_id
        INNER JOIN tbl_patient ON tbl_task.patient_id = tbl_patient.patient_id
        INNER JOIN tbl_driver ON tbl_task.driver_id = tbl_driver.driver_id
        INNER JOIN tbl_route ON tbl_patient.route_id = tbl_route.route_id
        WHERE task_id = %s;
        ''', [task_id], fetchone=False)[0]

        return {
            'dispatcher_id': sql[0],
            'dispatcher_name': sql[1].title(),
            'driver_id': sql[2],
            'driver_name': sql[3].title(),
            'patient_firstname': sql[4].title(),
            'patient_lastname': sql[5].title(),
            'route_source': sql[6].title(),
            'route_destination': sql[7].title()
        }

    def get_current_task(self, driver_id):
        task = self.db_query('''
        SELECT tbl_patient.firstname, tbl_patient.lastname, 
        tbl_route.source, tbl_route.destination
        FROM tbl_task
        JOIN tbl_patient ON tbl_task.patient_id = tbl_patient.patient_id
        JOIN tbl_route ON tbl_patient.route_id = tbl_route.route_id
        WHERE tbl_task.driver_id = %s
        ORDER BY tbl_task.time_created ASC
        LIMIT 1;
        ''', [driver_id], fetchone=False)

        if task:
            task = task[0]

            return {
                'patient_firstname': task[0].title(),
                'patient_lastname': task[1].title(),
                'route_source': task[2].title(),
                'route_destination': task[3].title()
            }

        else:
            return {
                'patient_firstname': '',
                'patient_lastname': '',
                'route_source': '',
                'route_destination': ''
            }

    # log

    def format_log_time(self, epoch):
        return datetime.fromtimestamp(epoch).strftime('%d/%b/%Y  %H:%M:%S')

    def get_logs(self, account_id):
        logs = []

        for log in self.db_query('''
            SELECT time_created, log
            FROM tbl_log
            WHERE account_id = %s
            ORDER BY time_created DESC;
            ''', [account_id], fetchone=False):
            logs.append({
                'time_created': self.format_log_time(log[0]),
                'log': log[1]
            })

        return logs
