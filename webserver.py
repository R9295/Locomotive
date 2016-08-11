'''
Yowza!
This is Locomotive's backend.
Queries? Email aarnavbos@gmail.com
In order to understand this, thoroughly learn:
Flask syntax
Pymongo syntax
'''

#web framework
from flask import *

import time
#Python driver for DB(MongoDB)
from pymongo import *
from pymongo import MongoClient

from datetime import datetime
import datetime

import os
import os.path

#Handles uploading of images for events
from flask_uploads import UploadSet, configure_uploads, IMAGES


#To spawn threads to run scripts alongside the server
from threading import *

#Hash and salt passwords
from bcrypt import hashpw, gensalt

#Auto email sending module. the file emaildata contains email and pass of the Locomotive mail address.
from emaildata import *
from flask_mail import Mail, Message

#To generate random URLs
import random
import string

 #Data validation script.
from Data_validation import *

import threading
#to query OSM(Open Street Maps) to find Location of events.
import geocoder
#to query collections by their Id
from bson.objectid import ObjectId


#creating Flask app
app = Flask(__name__)


#configuring Mail server
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = email
app.config['MAIL_PASSWORD'] = password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True


#creating instance of flask-mail
mail = Mail(app)

#Connecting to DB
client = MongoClient()
db = client.users


#To generate random characters to add to URL
def url_gen(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))


def key_gen(size=26, chars=string.ascii_uppercase + string.digits+string.punctuation):
        return ''.join(random.choice(chars) for _ in range(size))





'''
Configuring where photos should be uploaded.
With Flask, the folder Static should contain scripts and images and templates should contain websites
'''
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'

#Setting up data collection for admin interface



#Routing starts here. lets say it's locmotive.com. This here handles if user goes to locomotive.com
@app.route('/')
def locomotive():
        return render_template('locomotive.html')

@app.route('/locomotive/contact-us')
def contact_us():
    return render_template('contact_us.html')

@app.route('/locomotive/docs')
def tf_are_we():
    return render_template('docs.html')


#Home page of any user. The URL here will be Locomotive.com/username
@app.route('/<user>', methods=['GET','POST'])
def home_of_user(user):
    key = request.cookies.get('key')
    #check if logged in otherwise redirect to login
    if db.active.find({'key' : key}).count() != 0:

        #queries the DB to findout user data
        user = db.users.find_one({"name":user})

        #queries DB to find what events the user has made.
        what_events_i_own = db.events.find({"who_made_me":user})
        events = db.events.find({'who_is_coming':user['name']})
        going_to = []
        for i in events:
            going_to.append({
                'name'  : i['name'],
                'id'   : i['_id']
            })


        if user['notifications'] != 0:
            notifications  = db.notifications.find({'user_to'  :  user['name']})



        #After all the queries are done it returns the website home.html with the data queried as parameters to be used in the HTML file.
    else:
        return redirect(url_for('login'))
    return render_template('home.html',user=user,going_to=going_to)


#Creating user here the URL will be locmotive.com/create
@app.route('/create', methods =['GET','POST'])
def create_user():
    error = None
    add_user = False
    #if it receives a POST with data:
    if request.method == 'POST':
        #Sends it to the Datavalidation script to validate input Data
        validates =validate_create_user_input(password=request.form['create_password'],username=request.form['create_username'],password_again=request.form['password_re_enter'],phone=request.form['phone_number'],email=request.form['email'])
        #if the validate script returns something then there is an error; it will return that error to be rectified.
        if validates != None:
            error = validates


        #If no errors, then create user
        else:
            #try to add user and send email but if it doesnt work, that means email is incorrect.

                #hashes the password to store
                hashed_password = hashpw(request.form['create_password'].encode('utf-8'),gensalt())

                community_geocode = geocoder.osm(request.form['community']+' Auroville India')
                #The user data is stored in a dict as MongoDB's collections are stored in a JSON-like format. The request.forms are inputs on the website. It refers to the data posted from the form.
                url = url_gen()
                add_user = {
                    'name' : request.form['create_username'],
                    'password' : hashed_password,
                    'phone_number' : request.form['phone_number'],
                    'email' : request.form['email'],
                    'community' : request.form['community'],
                    'going_to' : [],
                    'events_attended': [],
                    'community_lat': community_geocode.json['lat'],
                    'community_lng': community_geocode.json['lng'],
                    'key' : url,
                    'notifications'  :  0

                            }

                #adding the user
                added = db.user_auth.insert_one(add_user)

                #Creating a random part of URL to use


                #Sending a verification email to the user,the random numbers for the url are to prevent shortcuts
                msg = Message('Thanks for creating a user @ Locomotive!', sender = email, recipients = [request.form['email']])
                msg.body = "Hello, Thanks for creating a user @ Locomotive! click this URL to activate your account!   "+"locomotive.auroville.org.in"+'/adduser/'+url+'/'+request.form['create_username']
                mail.send(msg)
                add_user = True

    return render_template('create_user.html', error=error,add_user=add_user)


#If the user verifies, it moves data from user_auth to user.
@app.route('/adduser/<url>/<user_name>')
def add_user(url,user_name):


    #finding the user from user_auth

    user = db.user_auth.find({'name':user_name}).count()

    if user != 0:
        user  = db.user_auth.find_one({'name': user_name})
        if url == user['key']:

            #makuing a dict of the data
            adding_user = {
                'name': user['name'],
                'password': user['password'],
                'email': user['email'],
                'phone_number': user['phone_number'],
                'community': user['community'],
                'going_to': [],
                'events_attended': [],
                'community_lat': user['community_lat'],
                'community_lng': user['community_lng'],
                'notifications'  :  0
            }

            #add to users. Verified!
            add_to_db = db.users.insert_one(adding_user)
            return "User verified    "+user_name + "    login@"+"   locomotive.auroville.org.in/login"
        else:
            return 'Incorrect URL'
    else:
        return "User doesn't exist"

#Login page,need to add forgot password option. The URL will be locomotive.com/login
@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    #If data is posted
    if request.method == 'POST':

        # check if  user exists
        look_for = db.users.find({'name':request.form['username']}).count()

        if look_for != 0:

            look_for = db.users.find_one({'name':request.form['username']})

            passwd = request.form['password'].encode('utf-8')
            #hash password and check the has with user's password

            if hashpw(passwd,look_for['password'].encode('utf-8')) == look_for['password']:

                #generating key to hash and store in cookies to verify user.
                key = key_gen()
                hashed_key = hashpw(key,gensalt())
                active_user = {
                    'name' : request.form['username'],
                    'key'  : hashed_key,
                }
                db.active.insert_one(active_user)
                resp = make_response(redirect('/%s'%(request.form['username'])))
                resp.set_cookie('key', hashed_key)
                return resp

            else:
                   error = 'Incorrect Password'
        else:
            error = "Username doesn't exist"

    return render_template('login.html', error=error)


#Edit user profile. The URL will be locomotive.com/username/edit
@app.route('/<edit_user>/edit', methods=['GET','POST'])
def edit_user(edit_user):
    key = request.cookies.get('key')

    #if key in cookies
    if db.active.find({'key' : key}).count() != 0:

        active_user = db.active.find_one({'key' : key})

        #Gets name of user logged in to pass on to the webpage
        user_in_use = active_user['name']
        user = db.users.find_one({'name'  :  user_in_use})
        #The events the user owns to pass on to the webpage
        events = db.events.find({"who_made_me": user_in_use})

        error = None

        #Find the data of the user currently logged in to edit
        k = db.users.find_one({'name': user_in_use})

        #Checks if the person logged in is trying to edit their profile and not somebody else's
        if k['name'] == edit_user:

            #If data is posted
            if request.method == 'POST':

                #Confirms user by asking for old password before changing it
                passwd = request.form['old_password'].encode('utf-8')
                if hashpw(passwd,k['password'].encode('utf-8')) != k['password']:
                    error="Passwords don't match"

                #Checks if the new passwords match
                elif request.form['password'] != request.form['new_password']:
                    error = "New passwords don't match"

                #Updates user
                else:
                    passwd = request.form['password'].encode('utf-8')
                    k['password'] = hashpw(passwd,gensalt())
                    k['email'] = request.form['email']
                    k['phone_number'] = request.form['phone_number']
                    k['community'] = request.form['community']
                    db.users.save(k)

                    return 'Please login again, to commit changes    '+'<html><body><a href="/login"><button style="color:green;">logout</button></a></body></html>'
        else:
            return redirect('/'+user_in_use)

        return render_template('edit_users.html', var=k,error=error,user=user)




#Views all events. The URL will be locomotive.com/events/view
@app.route('/events/view',methods=['GET','POST'])
def view_all_events():
    key = request.cookies.get('key')
    #if key in cookies
    if db.active.find({'key' : key}).count() != 0:

        active_user = db.active.find_one({'key' : key})
        user_in_use = active_user['name']
        user = db.users.find_one({'name'  :  user_in_use})


        #Gets the user's events
        events = db.events.find({'who_made_me':user_in_use})


        #Grabs all the events
        all_events = db.events.find({'private'  :  False})

        what_event = None
        results = []
        #If data is posted, redirect to the search page where the query will take place and will display data. This should be real time instead of the redirects
        if request.method == 'POST':
            search_term = request.json['search']
            search_results = db.events.find({'name': {'$regex': search_term}})
            for i in search_results:
                results.append(i['name'])
            return jsonify(results=results)

        return render_template('view_events.html',all_events=all_events,user=user)
    else:
        return redirect(url_for('login'))


#Create an event. The URL will be locomotive.com/events/create
@app.route('/events/create',methods=['GET','POST'])
def create_event():
    key = request.cookies.get('key')
    #If logged in
    if db.active.find({'key' : key}).count() != 0:
        error =  None

        active_user = db.active.find_one({'key' : key})
        user_in_use = active_user['name']
        user = db.users.find_one({'name'  :  user_in_use})

        #Gets the user's events
        events = db.events.find({'who_made_me':user_in_use})

        #If data is posted
        if request.method == 'POST':

            #Check if data given is valid. The function is in data_validation.py
            validates =  validate_event_input(phone=request.form['phone_number'],y=request.form['year'],m=request.form['month'],d=request.form['day'],name=request.form['name'])

            #If the function returns something, then return error
            if validates != None:
                error = validates

            #If photo is uploaded, check if the name exists if not, upload
            elif os.path.isfile("static/img/%s" %(request.files['photo'].filename)):
                error = "Filename already exists please rename file"

            #if all the conditions are satisfied add event
            else:

                #Image filename
                filename = None

                #Gets data from the fields called year month day and converts them to int to save as a date.
                year = int(request.form['year'])
                month = int(request.form['month'])
                day = int(request.form['day'])
                geocode = geocoder.osm(request.form['address'])

                #If a photo is uploaded, save it
                if request.files['photo'].filename != '':
                    filename = photos.save(request.files['photo'])


                if request.form.get('private'):
                    private = True
                else:
                    private = False
                #Event data. request.form fields are fields on the webpage
                event_data =  {
                    'name': request.form['name'],
                    'email': request.form['email'],
                    'phone_number' : request.form['phone_number'],
                    'venue' : request.form['venue'],
                    'address' : request.form['address'],
                    'description' : request.form['description'],
                    'time' : request.form['time'],
                    'duration' : request.form['duration'],
                    'date' : '%s-%s-%s'%(year,month,day),
                    'image' : filename,
                    'who_is_coming': [],
                    'who_made_me': user_in_use,
                    'when_made' : '%s'%(datetime.date.today()),
                    'lat':geocode.json['lat'],
                    'lng':geocode.json['lng'],
                    'private' : private
                }

                #Add event
                insert = db.events.insert(event_data)
                id = db.events.find_one({'name'  : request.form['name']})

                #Send an email stating that the event has been added
                msg = Message('Hello %s, You just created an event!' %(user_in_use), sender = email, recipients = [request.form['email']])
                msg.body ='Your event %s was successfully added! Check it out here:locomotive.auroville.org.in/events/%s' %(request.form['name'],id['_id'])
                mail.send(msg)

                created_event = db.events.find_one({'name'  :  request.form['name']})
                return redirect('/events/%s' %(created_event['_id']))
        return render_template('create_event.html',error=error,user = user)


#edit a particular event.The URL will be locomotive.com/events/edit/eventname
@app.route('/events/edit/<event_id>',methods=['GET','POST'])
def edit_event(event_id):

    key = request.cookies.get('key')
    #Check if logged in
    if db.active.find({'key' : key}).count() != 0:

        active_user = db.active.find_one({'key'  :  key})
        #Gets the name of the user logged in
        user_in_use = active_user['name']
        user = db.users.find_one({'name'  : user_in_use})

        #gets the user's events
        events = db.events.find({'who_made_me':user_in_use})

        error = None

        #Checks if the user who is trying to edit the event actually owns it
        var = db.events.find({'who_made_me':user_in_use, '_id': ObjectId(event_id)}).count()

        #If the user doesn't own it, then GTFO
        if var == 0:
            return redirect('/'+{{user_in_use}})

        var = db.events.find_one({'who_made_me' : user_in_use, '_id'  : ObjectId(event_id)})


        #verify and update event
        if request.method == 'POST':
            try:
                #Verifies the data using function in data_validation.py
                validates =validate_event_edit_input(phone=request.form['phone_number'],y=request.form['year'],m=request.form['month'],d=request.form['day'])

                #If the function returns something, return the error
                if validates != None:
                        error = validates

                #Checks if image that needs to be uploaded is not already there
                elif os.path.isfile("static/img/%s" %(request.files['photo'].filename)):
                    error = "Filename already exists please rename file"

                #Update if all satisfied
                else:

                    #If image is uploaded, store it
                    if request.files['photo'].filename != '':
                        filename = photos.save(request.files['photo'])
                        var['image'] = filename
                        db.events.save(var)

                #The dict that stores changes, and then emails them
                changes = {'name':'Not changed', 'email':'Not changed', 'venue':'Not changed', 'address':'Not changed', 'description':'Not changed', 'phone_number': 'Not changed', 'time':'Not changed', 'duration':'Not changed' ,'date':'Not changed','private':'Not changed' }

                #Gets the year month and day from event and converts it to int for it to be stored as a date
                year = int(request.form['year'])
                month = int(request.form['month'])
                day = int(request.form['day'])

                #compares data input to existing values, and if they are different, updates it and adds the changes to the change dict
                #This looks very ugly right now and needs a for loop to clean it.
                if var['name']  != request.form['name']:
                    var['name'] = request.form['name']
                    changes['name'] = request.form['name']
                    db.events.save(var)


                if  var['email'] !=request.form['email']:
                    var['email'] = request.form['email']
                    changes['email'] = request.form['email']
                    db.events.save(var)

                if var['venue'] != request.form['venue']:
                    var['venue'] = request.form['venue']
                    changes['venue'] = request.form['venue']
                    db.events.save(var)

                if var['address'] != request.form['address']:
                    var['address'] = request.form['address']
                    geocode = geocoder.osm(request.form['address'])
                    var['lat'] = geocode.json['lat']
                    var['lng'] = geocode.json['lng']
                    changes['address'] = request.form['address']
                    db.events.save(var)

                if var['description'] != request.form['description']:
                    var['description'] = request.form['description']
                    changes['description'] = request.form['description']
                    db.events.save(var)

                if var['phone_number'] != request.form['phone_number']:
                    var['phone_number'] = request.form['phone_number']
                    changes['phone_number'] = request.form['phone_number']
                    db.events.save(var)


                if var['time']  != request.form['time']:
                    var['time'] = request.form['time']
                    changes['time'] = request.form['time']
                    db.events.save(var)

                if var['duration']  != request.form['duration']:
                    var['duration'] = request.form['duration']
                    changes['duration'] = request.form['duration']
                    db.events.save(var)

                if var['date']  != '%s-%s-%s'%(year,month,day):
                    var['date'] ='%s-%s-%s'%(year,month,day)
                    changes['date'] = '%s-%s-%s'%(year,month,day)
                    changes['date'].encode('utf-8')
                    db.events.save(var)

                if request.form.get('private'):
                    var['private'] = True
                    changes['private'] = 'Yes'
                    db.events.save(var)
                else:
                    var['private'] = False
                    changes['private'] =  'No'
                    db.events.save(var)

                #Emails the stuff that has been edited to the user
                    msg = Message('Hello %s, You just edited an event: %s!' % (user_in_use,var['name']), sender=email,recipients=[request.form['email']])
                    msg.body ='Your changes: '
                    for key,values in changes.iteritems():
                        if values != 'Not changed':
                            msg.body += key +': '+values+'  '

                    mail.send(msg)
                    return redirect('/events/%s' %(var['_id']))
            except:
                error = 'Incorrect Email'



    else:
        return redirect(url_for('login'))
    return render_template('edit_event.html',var=var,error=error,user=user)


#Each individual event's page auto generated. The URL will be locmotive.com/events/eventname
@app.route('/events/<event_id>',methods=['GET','POST'])
def view_event(event_id):
    key = request.cookies.get('key')
    if db.active.find({'key'  :  key}).count() != 0:
        active_user = db.active.find_one({'key'  :  key})
        #Sets the event value to not past
        past = False
        #Gets the name of the user logged in
        user_in_use = active_user['name']
        #getting data of the user_logged in
        user_data = db.users.find_one({'name':user_in_use})
        #Gets the user's events
        events = db.events.find({'who_made_me':user_in_use})
        my_events = []
        for i in events:
            my_events.append(i['name'])

        event = []


        #Check if past_event:
        if db.events.find({'_id': ObjectId(event_id)}).count() != 0:
            event = db.events.find_one({'_id': ObjectId(event_id)})
            lat_of_event = event['lat']
            lng_of_event = event['lng']

        if db.past_events.find({'_id': ObjectId(event_id)}).count() != 0:
             event = db.past_events.find_one({'_id':ObjectId(event_id)})
             lat_of_event = event['lat']
             lng_of_event = event['lng']
             past = True


        user_community_lat = user_data['community_lat']
        user_community_lng = user_data['community_lng']

        #Real time search for users that are attending the event, will be implemented for events also
        results = []
        search_results = None
        search_term = None


        if request.method == 'POST' :

            search_term = request.json['search']
            search_results = db.users.find({'going_to':event['name'], 'name':{'$regex': search_term}})
            for i in search_results:
                results.append(i['name'])
            return  jsonify(results=results)

        #if request.method == 'POST' and








        return render_template('event.html', var=event,my_events=my_events,user_in_use =user_in_use,lat=lat_of_event,lng=lng_of_event,search_results=search_results,past=past,results=results,user_lat=user_community_lat,user_lng=user_community_lng,key=mapbox_key)
    else:
        return redirect(url_for('login'))

#Deletion of an event/user
#Deletion of an event/user
@app.route('/delete/<name>',methods=['GET','POST'])
def deleteion(name):
    key = request.cookies.get('key')
    if db.active.find({'key'  :  key}).count() != 0:
        active_user = db.active.find_one({'key'  :  key})

    #Find the event
    delete_event = db.events.find_one({'name':name})

    #if the event is found, delete it
    if delete_event != None:
         k = db.users.find()
         for i in k:
             if delete_event['name'] in i['going_to']:
                 i['going_to'].remove(delete_event['name'])
                 db.users.save(i)

         db.events.remove({'name':delete_event['name']})
         return redirect('/'+active_user['name'])

    #if the event is not found, then it has to be a user. Find and delete user
    else:
        k = db.events.find()
        user_to_delete = db.users.find_one({'name':name})
        for i in k:
            if user_to_delete['name'] in i['who_is_coming']:
                i['who_is_coming'].remove(user_to_delete['name'])
                db.events.save(i)

        db.users.remove({'name':name})
        return redirect('/login')


#If you wanna get in touch with someone going to the events, you can email them. The URL here will be locomotive.com/email/usertoemail
@app.route('/email/<name>', methods=['GET','POST'])
def email_request(name):
    key = request.cookies.get('key')
    if db.active.find({'key'  :  key}).count() != 0:

        active_user = db.active.find_one({'key'  :  key})
        user_in_use = active_user['name']

        error = None

        #The user to whom you're trying to contact
        user_to = db.users.find_one({'name':name})

        #The user logged in
        who_am_i = db.users.find_one({'name':user_in_use})

        #The user's events
        events = db.events.find({'who_made_me': user_in_use})
        my_events = []
        for i in events:
            my_events.append(i['name'])

        #If data is sent, then email the person.
        if request.method == 'POST':
            msg = Message('Hello,%s has emailed you regarding an event,please contact them back' %(user_in_use), sender = email, recipients = [user_to['email']] )
            msg.body =request.form['message']
            mail.send(msg)

            # Data to append to log
            log_data = {
                'from': user_in_use,
                'to': user_to['name'],
                'when': datetime.datetime.now(),
                'message': request.form['message']
            }
            # add to log
            db.transaction_log.insert_one(log_data)

            #add to user notifications
            user = db.users.find_one({'name'  : user_in_use})
            user['notifications'] = user['notifications'] +1
            db.users.save(user)


            #add to notification database
            notify_data = {
                    'user_from'  :  user_to['name'],
                    'user_to'  :  user_in_use,
                    'when'  :  datetime.datetime.now()
            }
            db.notifications.insert_one(notify_data)


            return redirect('/'+user_in_use)

    else:
        return redirect(url_for('login'))
    return render_template('email_request.html',user_to=user_to,user_in_use=user_in_use,my_events=my_events,error=error)

#This script add to the users attending event list
@app.route('/goto/<name>')
def go_to(name):
    key = request.cookies.get('key')
    if db.active.find({'key'  :  key}).count() != 0:
        active_user = db.active.find_one({'key'  :  key})
        user_in_use = active_user['name']
        #Appending to the event's who_is_coming list
        event = db.events.find_one({'name'  :  name})
        if user_in_use in event['who_is_coming']:
            pass
        else:
            db.events.update({'name': name}, {'$push': {'who_is_coming': user_in_use}})
            db.users.update({'name': user_in_use}, {'$push': {'going_to': user_in_use}})
         #Appending to the user's going_to list


    return redirect('/'+user_in_use)

@app.route('/events/all/past' ,methods =['GET','POST'])
def view_past_events():
    key = request.cookies.get('key')
    if db.active.find({'key'  :  key}).count() != 0:
        active_user = db.active.find_one({'key'  :  key})
        user_in_use = active_user['name']
        error = None
        past_events =db.past_events.find({'private'  : False})

        user = db.users.find_one({'name'  :  user_in_use})

        #If data is posted, redirect to the search page where the query will take place and will display data. This should be real time instead of the redirects
        if request.method == 'POST':
            results = []
            search_term = request.json['search']
            search_results = db.past_events.find({'name': {'$regex': search_term}})
            for i in search_results:
                results.append(i['name'])
            return jsonify(results=results)

    else:
        return redirect('/login')
    return render_template('view_past_events.html',error=error,past_events=past_events,user=user)

#To do
@app.route('/events/search/advanced/<event>',methods=['GET','POST'])
def advanced_search(event):
    pass

@app.route('/user/admin', methods =['GET','POST'])
def admin_interface():
    key = request.cookies.get('key')
    if key == None:
            return  'Xd nice try'
    else:
        if db.active.find({'key'  :  key}).count() != 0:
            active_user = db.active.find_one({'key'  :  key})
            if active_user['name'] != 'Aarnav':
                return  "Xd you ain't admin"
            else:


                #admin user
                db.events.find_one({'name' : 'Aarnav'})

                #getting total amount of events
                total_events = db.events.find().count()
                users_logged_in = db.active.count()

                #getting total amount of users

                total_users = db.users.find().count()

                #getting total amount of past_events

                total_past_events = db.past_events.find().count()

                recent_events = []
                k = 0
                for i in db.events.find():
                    recent_events.append(i['name'])
                    k = k+1
                    if k == 4:
                        break

                if request.method == 'POST':
                    return jsonify(results={'total_past_events':total_past_events,'total_events':total_events,'total_users':total_users, 'users_logged_in':users_logged_in,'recent_events':recent_events})

        return render_template('admin_interface.html')

#Views all events. The URL will be locomotive.com/events/view
@app.route('/events-of/<name>',methods=['GET','POST'])
def view_my_events(name):

    #check if logged in
    key = request.cookies.get('key')
    if db.active.find({'key'  :  key}).count() != 0:
        active_user = db.active.find_one({'key'  :  key})

        #Gets the name of the user logged in
        user_in_use = active_user['name']
        user = db.users.find_one({'name'  :  user_in_use})
        #Gets the user's events
        events = db.events.find({'who_made_me':user_in_use})
        my_events = []
        for i in events:
            my_events.append({
                'name'  : i['name'],
                'id'   : i['_id']


            })


        return render_template('events_of_user.html',my_events=my_events,user=user)
    else:
        return redirect(url_for('login'))


@app.route('/ungo/<event>')
def un_go_to(event):
    #check if logged in
    key = request.cookies.get('key')
    if db.active.find({'key'  :  key}).count() != 0:
        active_user = db.active.find_one({'key'  :  key})
        user_in_use = active_user['name']

        un_go = db.events.find_one({'name':event})
        user_un_go = db.users.find_one({'name':user_in_use})
        if user_in_use in un_go['who_is_coming']:
            un_go['who_is_coming'].remove(user_in_use)
            db.events.save(un_go)

        if un_go['name'] in user_un_go['going_to']:
            user_un_go['going_to'].remove(un_go['name'])
            db.users.save(user_un_go)
        return redirect('/'+user_in_use)
    else:
        return 'You are not logged in!'


@app.route('/forgot', methods=['GET','POST'])
def forgot_password():
    error = None
    if request.method == 'POST':
        user = db.users.find({'name': request.form['username']}).count()

        if user == 0:
            error = 'Incorrect Username'

        if validate_email(request.form['email']) != True:
            error = 'Invalid email'

        if user != 0:
            user_data = db.users.find_one({'name' : request.form['username']})
            if user_data['email'] != request.form['email']:
                error = 'Incorrect email'
        else:
            verify = {
                'user': request.form['username'],
                'key' : url_gen(),
                'email': request.form['email']
            }

            db.reset_password_key.insert_one(verify)

            msg = Message('Reset Password', sender=email, recipients=[request.form['email']])
            msg.body = "Reset your password at:"+"locomotive.auroville.org.in/forgot/"+verify['key']+'/'+verify['user']
            mail.send(msg)
            return redirect('/')

    return render_template('forgot_password.html', error=error)

@app.route('/forgot/<url>/<name>', methods=['GET','POST'])
def reset_password(url, name):
    if db.reset_password_key.find({'user': name,'key' : url}).count() != 0:
        error = None

        if request.method == 'POST':
            if request.form['password'] != request.form['password_again']:
                error = "Passwords don't match"
            else:
                hashed_password = hashpw(request.form['create_password'].encode('utf-8'), gensalt())
                print 'xd'
                db.users.update({'name' : name}, {'$push': {'password' : hashed_password}})
                print 'lul'

        return render_template('reset_password.html', error = error)

@app.route('/notifications/<user>')
def notifications(user):
    key = request.cookies.get('key')
    if db.active.find({'key'  :  key}).count() != 0:
        active_user = db.active.find_one({'key'  :  key})
        user_in_use = active_user['name']

        notifications_of_user = db.notifications.find({'user_to'  :  user_in_use})

        rm_notifications =db.users.find_one({'name'  :  user_in_use})

        rm_notifications['notifications'] = 0
        db.users.save(rm_notifications)

    return render_template('notifications.html', notifications=notifications_of_user,user=rm_notifications)




@app.route('/logout/<name>')
def logout(name):
    remove = db.active.remove({'name':name})
    db.active_users.save(remove)
    resp = make_response(redirect('/'))
    resp.set_cookie('key','',expires=0)
    return resp



#A script I'm particularly proud of. This checks all events every 24 hours to see if they have been done or not, if they have, then it adds them to past_events
def check_if_past():

    #Gets today's date
    w = datetime.datetime.today()

    #Queries all events
    events = db.events.find()
    print 'checking for past events'

    #For all the events that haven't past in db.events, check the event's date to today's. If it's samller then it has past, if it has past add to the
    #DB past events and remove from DB.events
    for i in events:
        if datetime.datetime.strptime(i['date'].encode('utf-8'),'%Y-%m-%d') < w:
           query_it = db.events.find_one({'name':i['name']})
           add_to_past =  {
               'name': query_it['name'],
               'email': query_it['email'],
               'phone_number': query_it['phone_number'],
               'venue': query_it['venue'],
               'address': query_it['address'],
               'description': query_it['description'],
               'time': query_it['time'],
               'duration': query_it['duration'],
               'date':query_it['date'],
               'image': query_it['image'],
               'who_is_coming': query_it['who_is_coming'],
               'when_made': query_it['when_made']

           }
           db.past_events.insert_one(add_to_past)
           db.events.remove({'name':query_it['name']})

        #Do it every 24 hours. It spawns a differnet thread to run along side the server
        threading.Timer(86400, check_if_past).start()



#Run the if_past script
check_if_past()




#RUN IT GUT
if __name__ == '__main__':
    app.debug = True
    app.secret_key=os.urandom(25)
    configure_uploads(app, photos)


    app.run(host='0.0.0.0', port=5000,threaded=True)
