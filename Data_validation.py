from pymongo import *
import datetime
from validate_email import validate_email
client = MongoClient()
db = client.users
def validate_event_input(phone,y,m,d,name):
    error = None
    year  = int(y)
    month = int(m)
    day = int(d)
    try:
        datetime.date(year,month,day)
    except ValueError or NameError:
        error = 'Wrong dates'
    try:
        if datetime.date(year, month, day) < datetime.date.today():
            error = "Can't create events in the past"
    except ValueError or NameError:
        error = "Incorrect dates"


    if phone.isdigit() != True or len(str(phone)) != 10 :
                error = 'Invalid phone number'

    elif  db.events.find_one({'name':name})  != None:
        error = 'Event name already exists'

    if error:
        return error

def validate_event_edit_input(phone,y,m,d):
    error = None
    year  = int(y)
    month = int(m)
    day = int(d)
    try:
        datetime.date(year,month,day)
    except ValueError or NameError:
        error = 'Wrong dates'
    if phone.isdigit() != True or len(str(phone)) != 10 :
        error = 'Invalid phone number'
    try:
        if datetime.date(year,month,day) < datetime.date.today():
            error = "Can't create events in the past"
    except ValueError or NameError:
        error = "Incorrect dates"
    if error:
        return error

def validate_create_user_input(password,username,password_again,phone,email):
    error = 'None1'
    if password != password_again:
        error = "Passwords don't mach"

    elif db.users.find({'name':username}).count() > 0:
        error = 'User already exists. Please rename'

    elif  db.user_auth.find({'name':username}).count() > 0:

        error = 'User exists,Please rename'

    elif phone.isdigit() != True or len(str(phone)) != 10 :
        error = 'Invalid phone number'

    elif validate_email(email) != True:
        error = 'Incorrect Email!'
    else:
        error = None

    return error

