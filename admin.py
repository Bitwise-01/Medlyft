# Date: 04/05/2019
# Author: Mohamed
# Description: Admin

from scripts.fake import Fake
from lib.database import Medlyft
from random import choice, randint
from lib.const import EmployeeConst, PatientConst

# const
DRIVER = EmployeeConst.DRIVER.value['id']
DISPATCHER = EmployeeConst.DISPATCHER.value['id']


class AccountManager:

    '''Manage the accounts
    '''

    def __init__(self):
        self.database = Medlyft()

    def register_account(self, name, username, password, employee_type):
        return self.database.register(username, password, employee_type, name)

    def delete_account(self, username):

        username = username.strip().lower()

        if not self.database.username_exists(username):
            return 'Account does not exist'

        user_id = self.database.get_user_id(username)

        return self.database.delete_account(user_id)

    def display_accounts(self):
        for row in self.database.db_query('SELECT user_id, username, employee_type FROM tbl_account;', fetchone=False):
            user_id = row[0][:8]
            username = row[1].title()

            employee_type = ''.join(
                [_.value['name']
                    for _ in EmployeeConst if _.value['id'] == row[2]]
            ).title()

            print(
                f'UserId: {user_id}\nUsername: {username}\nEmployeeType: {employee_type}\n')

# wrappers


def create_account(name, username, password, employee_type):

    # connect to the database
    account_manager = AccountManager()

    # acreate an account
    print(account_manager.register_account(
        name, username, password, employee_type))

    # disconnect from the database
    account_manager.database.db_close()


def create_accounts(names):
    account_manager = AccountManager()

    for name in names:
        username = f'{name}01'
        password = 'TumblrFuckingSucks123!@#'
        employee_type = DRIVER if randint(0, 1) else DISPATCHER
        print(account_manager.register_account(
            name, username, password, employee_type))

    account_manager.database.db_close()


def delete_account(username):

    # connect to the database
    account_manager = AccountManager()

    # delete an account
    print(account_manager.delete_account(username))

    # disconnect from the database
    account_manager.database.db_close()


def display_accounts():

    # connect to the database
    account_manager = AccountManager()

    # display accounts
    account_manager.display_accounts()

    # disconnect from the database
    account_manager.database.db_close()


def add_patient(firstname, lastname, source, destin):

    # connect to the database
    account_manager = AccountManager()

    # add patient
    account_manager.database.add_patient(firstname, lastname, source, destin)

    # disconnect from the database
    account_manager.database.db_close()


def add_patients(amount=5):

    # collect info
    patients = Fake().get(amount)

    # connect to the database
    account_manager = AccountManager()

    # add patient
    for patient in patients:
        account_manager.database.add_patient(
            firstname=patient['firstname'],
            lastname=patient['lastname'],
            source=patient['address'],
            destin=choice(PatientConst.HOSPITALS.value)
        )

    # disconnect from the database
    account_manager.database.db_close()


def add_task(driver_id, patient_id, dispatcher_id):
    # connect to the database
    account_manager = AccountManager()

    # add task
    account_manager.database.add_task(driver_id, patient_id, dispatcher_id)

    # disconnect from the database
    account_manager.database.db_close()


def exe(cmd):
     # connect to the database
    account_manager = AccountManager()

    # execute command
    account_manager.database.db_execute(cmd)

    # disconnect from the database
    account_manager.database.db_close()


if __name__ == '__main__':

    '''Database management
    '''

    # uncomment the lines below to create a new account
    # create_accounts(names)
    # create_account(
    #     name='Mohamed',
    #     username='Mohamed01',
    #     password='TumblrFuckingSucks123!@#',
    #     employee_type=DRIVER
    # )
