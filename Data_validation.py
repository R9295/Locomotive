from pymongo import *
import datetime

client = MongoClient()
db = client.events
def validate_event_input(phone,y,m,d,name):
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
    it_exists = db.events.find_one({'name':name})
    if it_exists:
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

def validate_create_user_input(password,username,password_again,phone):
    error = None
    if password != password_again:
        error = "Passwords don't mach"
    elif db.users.find_one({'name':username}) or db.user_auth.find_one({'name':username}) != None:
        error = 'User already exists. Please rename'
    elif phone.isdigit() != True or len(str(phone)) != 10 :
        error = 'Invalid phone number'
    else:
        error= ''
    if error:
        return error