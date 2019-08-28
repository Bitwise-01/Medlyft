# Date: 04/01/2019
# Author: Mohamed
# Description: Const

from enum import Enum


class DatabaseConst(Enum):

    # login info
    USER = 'root'
    HOST = '127.0.0.1'
    PASSWORD = 'TumblrFuckingSucks123!@#'

    # database
    DATABASE_NAME = 'medlyft'

    # login security
    LOCK_TIME = 60 * 60  # (secs) 60 * 60 => 1 hour
    MAX_FAILED_ATTEMPTS = 7  # attempts before locking


class SessionConst(Enum):

    # (mins) 7 => 7 minutes; this must also be changed in session.js(SessionDelay)
    SESSION_TTL = 7

    # the account is consider logged out if it doesn't ping the server within this amount of time
    MIN_SILENCE_TIME = 30  # (seconds)


class CredentialConst(Enum):

    MIN_USERNAME_LENGTH = 4
    MAX_USERNAME_LENGTH = 32

    MIN_PASSWORD_LENGTH = 12
    MAX_PASSWORD_LENGTH = 64


class EmployeeConst(Enum):

    DRIVER = {'id': 0, 'name': 'Driver'}
    DISPATCHER = {'id': 1, 'name': 'Dispatcher'}


class PatientConst(Enum):

    STATUS = {
        0: 'Waiting',
        1: 'In route',
        2: 'Dropped off'
    }

    _STATUS = {
        'Waiting': 0,
        'In route': 1,
        'Dropped off': 2
    }

    HOSPITALS = ['322 Lake Ave', '1000 South Ave',
                 '601 Elmwood Ave', '1425 Portland Ave']
