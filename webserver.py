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
@app.route('/', methods=['GET','POST'])
def locomotive():

    if request.method == 'POST':
        msg = Message('%s contacted you regarding Locomotive'%(request.form['name']), sender = email, recipients = ['aarnavbos@gmail.com'])
        msg.body = request.form['message']
        mail.send(msg)
    return render_template('locomotive.html')

@app.route('/locomotive/docs')
def tf_are_we():
    return render_template('docs.html')


#Home page of any user. The URL here will be Locomotive.com/username
@app.route('/<id>', methods=['GET','POST'])
def home_of_user(id):
    key = request.cookies.get('key')
    #check if logged in otherwise redirect to login
    if db.active.find({'key' : key}).count() != 0:

        #queries the DB to findout user data
        user = db.users.find_one({'_id'  : ObjectId(id)  })

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

        if request.form['create_password'] != request.form['password_re_enter']:
            error = "Passwords don't mach"

        if db.users.find({'name':request.form['create_username']}).count() > 0:
            error = 'User already exists. Please rename'

        if  db.user_auth.find({'name':request.form['create_username']}).count() > 0:
            error = 'User exists,Please rename'

        if request.form['phone_number'].isdigit() != True or len(str(request.form['phone_number'])) != 10 :
            error = 'Invalid phone number'

        if validate_email(request.form['email']) != True:
            error = 'Incorrect Email!'

        community_geocode = geocoder.osm(request.form['community']+' Auroville India')
        if community_geocode.json['status'] != 'OK':
            error = "Locomotive cannot serve this community due to technical reasons, please choose another one that is closeby "

        #If no errors, then create user
        if error == None:
            #try to add user and send email but if it doesnt work, that means email is incorrect.

                #hashes the password to store
            hashed_password = hashpw(request.form['create_password'].encode('utf-8'),gensalt())



            #The user data is stored in a dict as MongoDB's collections are stored in a JSON-like format. The request.forms are inputs on the website. It refers to the data posted from the form.
            #Creating a random part of URL to use
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
            user = db.user_auth.find_one({'name'  :  add_user['name']})



            #Sending a verification email to the user,the random numbers for the url are to prevent shortcuts
            msg = Message('Thanks for creating a user @ Locomotive!', sender = email, recipients = [request.form['email']])
            msg.body = "Hello, Thanks for creating a user @ Locomotive! click this URL to activate your account!   "+"locomotive.auroville.org.in"+'/adduser/'+url+'/'+'%s'%(user['_id'])
            mail.send(msg)
            add_user = True

    return render_template('create_user.html', error=error,add_user=add_user)


#If the user verifies, it moves data from user_auth to user.
@app.route('/adduser/<url>/<id>')
def add_user(url,id):


    #finding the user from user_auth

    user = db.user_auth.find({'_id':ObjectId(id)}).count()
    if user != 0:
        user  = db.user_auth.find_one({'_id': ObjectId(id)})
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
            rm = db.user_auth.find_one({'name'  :  user['name']})
            db.user_auth.remove(rm)
            db.user_auth.save(rm)
            return "User verified    "+adding_user['name']+ "<html><body><a href='/login'>Login!</a></body></html>"   
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
                user = db.users.find_one({'name'  : request.form['username']})
                resp = make_response(redirect('/%s'%(user['_id'])))
                resp.set_cookie('key', hashed_key)
                return resp

            else:
                   error = 'Incorrect Password'
        else:
            error = "Username doesn't exist"

    return render_template('login.html', error=error)


#Edit user profile. The URL will be locomotive.com/username/edit
@app.route('/<id>/edit', methods=['GET','POST'])
def edit_user(id):
    key = request.cookies.get('key')
    error = None

    #if key in cookies
    if db.active.find({'key' : key}).count() != 0:

        active_user = db.active.find_one({'key' : key})

        #Gets name of user logged in to pass on to the webpage
        user_in_use = active_user['name']
        user = db.users.find_one({'_id'  :  ObjectId(id)})
        #The events the user owns to pass on to the webpage
        events = db.events.find({"who_made_me": user_in_use})


        #Find the data of the user currently logged in to edit
        k = db.users.find_one({'_id': ObjectId(id)})

        #Checks if the person logged in is trying to edit their profile and not somebody else's
        if k['name'] == user_in_use:

            #If data is posted
            if request.method == 'POST':

                #Confirms user by asking for old password before changing it
                if request.form['password'] and request.form['new_password'] != None:
                    passwd = request.form['old_password'].encode('utf-8')
                    if hashpw(passwd,k['password'].encode('utf-8')) != k['password']:
                        error="Passwords don't match"


                community_geocode = geocoder.osm(request.form['community']+' Auroville India')
                if community_geocode.json['status'] != 'OK':
                    error = "Locomotive cannot serve this community due to technical reasons, please choose another one that is closeby "

                #Checks if the new passwords match
                elif request.form['password'] != request.form['new_password']:
                    error = "New passwords don't match"



                #Updates user
                if error == None:
                    if request.form['password'] != None:
                        passwd = request.form['password'].encode('utf-8')
                        k['password'] = hashpw(passwd,gensalt())
                    k['email'] = request.form['email']
                    k['phone_number'] = request.form['phone_number']
                    k['community'] = request.form['community']
                    k['community_lat'] = community_geocode.json['lat']
                    k['community_lng'] = community_geocode.json['lng']
                    db.users.save(k)

                    return 'Please login again, to commit changes    '+'<html><body><a href="/login"><button style="color:green;">logout</button></a></body></html>'
        else:
            return redirect('/'+'%s'%(user['_id']))

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
        all_events = db.events.find({'private'  :  False,'when_made'  :  {'$regex'  : '%s'%(datetime.date.today())}}).sort([("when" , -1)])

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

            year  = int(request.form['year'])
            month = int(request.form['month'])
            day = int(request.form['day'])
            
            try:
                if datetime.date(year, month, day) < datetime.date.today():
                    error = "Can't create events in the past"
            except ValueError or NameError:
                error = "Incorrect dates"

            if request.form['phone_number'].isdigit() != True or len(str(request.form['phone_number'])) != 10 :
                error = 'Invalid phone number'

            if  db.events.find({'name':request.form['name']}).count() > 0:
                error = 'Event name already exists'
         
            geocode = geocoder.osm(request.form['address'])
            if geocode.json['status'] != 'OK':
                error = "Locomotive cannot serve this community due to technical reasons, please choose another one that is closeby "

            #If photo is uploaded, check if the name exists if not, upload
            if os.path.isfile("static/img/%s" %(request.files['photo'].filename)):
                error = "Filename already exists please rename file"

            

            #if all the conditions are satisfied add event
            if error == None:
                
                #Image filename
                filename = None

                #Gets data from the fields called year month day and converts them to int to save as a date.
                year = int(request.form['year'])
                month = int(request.form['month'])
                day = int(request.form['day'])

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
                    'contact' : request.form['contact']
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
            return redirect('/'+user['_id'])

        var = db.events.find_one({'who_made_me' : user_in_use, '_id'  : ObjectId(event_id)})


        #verify and update event
        if request.method == 'POST':
            try:

                year  = int(request.form['year'])
                month = int(request.form['month'])
                day = int(request.form['day'])
            
                try:
                    datetime.date(year,month,day)
                except ValueError or NameError:
                    error = 'Wrong dates'
                try:
                    if datetime.date(year, month, day) < datetime.date.today():
                        error = "Can't create events in the past"
                except ValueError or NameError:
                    error = "Incorrect dates"


                if request.form['phone_number'].isdigit() != True or len(str(request.form['phone_number'])) != 10 :
                    error = 'Invalid phone number'

                if  db.events.find({'name':name}).count() > 0:
                    error = 'Event name already exists'

                geocode = geocoder.osm(request.form['address'])
                if geocode.json['status'] != 'OK':
                    error = "Locomotive cannot serve this community due to technical reasons, please choose another one that is closeby "

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
                changes = {'name':'Not changed','venue':'Not changed', 'address':'Not changed', 'description':'Not changed', 'contact': 'Not changed', 'time':'Not changed', 'duration':'Not changed' ,'date':'Not changed','private':'Not changed' }

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


                if  var['contact'] !=request.form['contact']:
                    var['contact'] = request.form['contact']
                    changes['contact'] = request.form['contact']
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


        if request.method == 'POST':
            user_to = db.users.find_one({'name'  :  request.form['user_to']})
            user_from = user_in_use
            message = request.form['message']

            msg = Message('Hello,%s has emailed you regarding an event,please contact them back' %(user_in_use), sender = email, recipients = [user_to['email']] )
            msg.body =message
            mail.send(msg)
            # Data to append to log
            log_data = {
                'from': user_in_use,
                'to': user_to['name'],
                'when': datetime.datetime.now(),
                'message': message
            }
            # add to log
            db.transaction_log.insert_one(log_data)

            #add to user notifications
            user_to['notifications'] = user_to['notifications'] +1
            db.users.save(user_to)


            #add to notification database
            notify_data = {
                    'user_from'  :  user_from,
                    'user_to'  :  user_to['name'],
                    'when'  :  '%s' %(datetime.datetime.now()),
                    'what_event'  :  event['name']
            }
            db.notifications.insert_one(notify_data)

        return render_template('event.html',var=event,user_in_use =user_in_use,lat=lat_of_event,lng=lng_of_event,past=past,user_lat=user_community_lat,user_lng=user_community_lng,user=user_data,key=mapbox_key)
    else:
        return redirect(url_for('login'))

@app.route('/search/user', methods=['GET','POST'])
def realtime_user_search():
    if request.method == 'POST':
        results = []
        search_term = request.json['search']
        event = request.json['event']
        search_results = db.users.find({'going_to'  :  event , 'name'  :  {'$regex'  :  search_term}})
        for i in search_results:
            results.append(i['name'])
        return jsonify(results=results)


#Deletion of an event/user
#Deletion of an event/user
@app.route('/delete/<name>',methods=['GET','POST'])
def deleteion(name):
    key = request.cookies.get('key')
    if db.active.find({'key'  :  key}).count() != 0:
        active_user = db.active.find_one({'key'  :  key})

    #Find the event
    delete_event = db.events.find({'name':name}).count()

    #if the event is found, delete it
    if delete_event != 0:
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


#This script add to the users attending event list
@app.route('/goto/<name>')
def go_to(name):
    key = request.cookies.get('key')
    if db.active.find({'key'  :  key}).count() != 0:
        active_user = db.active.find_one({'key'  :  key})
        user_in_use = active_user['name']
        user = db.users.find_one({'name'  :  user_in_use})
        #Appending to the event's who_is_coming list
        event = db.events.find_one({'name'  :  name})
        if user_in_use in event['who_is_coming']:
            pass
        else:
            db.events.update({'name': name}, {'$push': {'who_is_coming': user_in_use}})
            db.users.update({'name': user_in_use}, {'$push': {'going_to': event['name']}})
         #Appending to the user's going_to list


    return redirect('/'+'%s'%(user['_id']))

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
@app.route('/events-of/<id>',methods=['GET','POST'])
def view_my_events(id):

    #check if logged in
    key = request.cookies.get('key')
    if db.active.find({'key'  :  key}).count() != 0:
        active_user = db.active.find_one({'key'  :  key})
        user = db.users.find_one({'_id'  : ObjectId(id)})
        if user['name'] != active_user['name']:
            return "You don't own these events."

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
        user = db.users.find_one({'name'  : active_user})

        un_go = db.events.find_one({'name':event})
        user_un_go = db.users.find_one({'name':user_in_use})
        if user_in_use in un_go['who_is_coming']:
            un_go['who_is_coming'].remove(user_in_use)
            db.events.save(un_go)

        if un_go['name'] in user_un_go['going_to']:
            user_un_go['going_to'].remove(un_go['name'])
            db.users.save(user_un_go)
        return redirect('/'+user['_id'])
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

        notifications_of_user = db.notifications.find({'user_to'  :  user_in_use ,'when'  :  {'$regex'  : '%s'%(datetime.date.today())}}).sort([("when" , -1)])

        rm_notifications =db.users.find_one({'name'  :  user_in_use})

        rm_notifications['notifications'] = 0
        db.users.save(rm_notifications)

    return render_template('notifications.html', notifications=notifications_of_user,user=rm_notifications)




@app.route('/logout/<id>')
def logout(id):
    user = db.users.find_one({'_id'  : ObjectId(id)})
    remove = db.active.remove({'name':user['name']})
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
