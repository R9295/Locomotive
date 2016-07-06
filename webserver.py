'''
Yowza!
This is Locomotive's backend. The modules that are not explained are self explanatory
Queries? Email aarnavbos@gmail.com
In order to understand this thoroughly learn:
Flask syntax
Pymongo syntax

and the rest is self explanatory.
This code is very inefficient as I'm querying the DB for the same thing every time it loads the page.
I need to be able to cache it so I can take it from the cookies, but I don't how to do it ATM

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

#Check if user is logged in  before proceeding to any route
@app.before_request
def before_request():
    g.user = None
    #when you login it adds a hashed cookie to validate that you are logged in. This checks if 'user' exists in the cookie.
    if 'user' in session:
        g.user = session['user']





'''
Configuring where photos should be uploaded.
With Flask, the folder Static should contain scripts and images and templates should contain websites
'''
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'


#Routing starts here. lets say it's locmotive.com. This here handles if user goes to locomotive.com
@app.route('/')
def home():
    #check if logged in. If so, redirects to the user's homepage otherwise redirects to login.
    if g.user:
            return redirect('/'+g.user)
    else:
        return redirect(url_for('login'))


#Home page of any user. The URL here will be Locomotive.com/username
@app.route('/<user>', methods=['GET','POST'])
def homeof_user(user):
    #check if logged in otherwise redirect to login
    if g.user:
        #queries the DB to findout user data
        user = db.users.find_one({"name":g.user})

        #queries DB to find what events the user has made.
        what_events_i_own = db.events.find({"who_made_me":g.user})
        my_events = []
        for i in what_events_i_own:
            my_events.append(i['name'])

        #After all the queries are done it returns the website home.html with the data queried as parameters to be used in the HTML file.
        return render_template('home.html',user=user,events=my_events)

    else:
        return redirect(url_for('login'))



#Creating user here the URL will be locmotive.com/create
@app.route('/create', methods =['GET','POST'])
def create_user():
    error = None
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

                #The user data is stored in a dict as MongoDB's collections are stored in a JSON-like format. The request.forms are inputs on the website. It refers to the data posted from the form.
                add_user = {
                    'name' : request.form['create_username'],
                    'password' : hashed_password,
                    'phone_number' : request.form['phone_number'],
                    'email' : request.form['email'],
                    'community' : request.form['community'],
                    'going_to' : []
                            }

                #adding the user
                added = db.user_auth.insert_one(add_user)

                #Creating a random part of URL to use
                url = url_gen()

                #Sending a verification email to the user,the random numbers for the url are to prevent shortcuts
                msg = Message('Thanks for creating a user @ Locomotive!', sender = email, recipients = [request.form['email']])
                msg.body = "Hello, Thanks for creating a user @ Locomotive! click this URL to activate your account!   "+"localhost:5000"+'/adduser/'+url+'/'+request.form['create_username']
                mail.send(msg)
                return redirect(url_for('login'))

    return render_template('create_user.html', error=error)


#If the user verifies, it moves data from user_auth to user.
@app.route('/adduser/<url>/<user_name>',methods=['GET'])
def add_user(url,user_name):

    #finding the user from user_auth
    user = db.user_auth.find_one({'name':user_name})

    #makuing a dict of the data
    adding_user = {
        'name': user['name'],
        'password': user['password'],
        'email': user['email'],
        'phone_number': user['phone_number'],
        'community': user['community'],
        'going_to': []
    }
    print adding_user
    #add to users. Verified!
    add_to_db = db.users.insert_one(adding_user)
    print 'k'
    return "User verified    "+user_name + "    login@"+"   localhost:5000/login"

#Login page,need to add forgot password option. The URL will be locomotive.com/login
@app.route('/login', methods=['GET','POST'])
def login():

    #kills the already logged in session cookie
    session.pop('user',None)

    error = None

    #If data is posted
    if request.method == 'POST':

        # check if  user exists
        look_for = db.users.find_one({'name':request.form['username']})
        if look_for :

            passwd = request.form['password'].encode('utf-8')

            #hash password and check the has with user's password
            if hashpw(passwd,look_for['password'].encode('utf-8')) == look_for['password']:

                # adds  status 'I am logged in as USERNAME' to the cookies
                session['user'] = request.form['username']
                return redirect(url_for('home'))

            else:
                   error = 'Incorrect Password'
        else:
            error = "Username doesn't exist"

    return render_template('login.html', error=error,)


#Edit user profile. The URL will be locomotive.com/username/edit
@app.route('/<edit_user>/edit', methods=['GET','POST'])
def edit_user(edit_user):
    #Gets name of user logged in to pass on to the webpage
    user_in_use = g.user

    #The events the user owns to pass on to the webpage
    events = db.events.find({"who_made_me": g.user})
    my_events = []
    for i in events:
        my_events.append(i['name'])

    error = ""

    #if logged in
    if g.user:

        #Find the data of the user currently logged in to edit
        k = db.users.find_one({'name': g.user})

        #Checks if the person logged in is trying to edit their profile and not somebody else's
        if k['name'] == edit_user:

            #If data is posted
            if request.method == 'POST':

                #Confirms user by asking for old password before changing it
                if hashpw(request.form['old_password'].encode('utf-8'),k['password']) != edit_user.password:
                    error="Passwords don't match"

                #Checks if the new passwords match
                elif request.form['password'] != request.form['new_password']:
                    error = "New passwords don't match"

                #Updates user
                else:
                    k['password'] = hashpw(request.form['password'].encode('utf-8'),gensalt())
                    k['email'] = request.form['email']
                    k['phone_number'] = request.form['phone_number']
                    k['community'] = request.form['community']
                    db.users.save(k)

                    return 'Please login again, to commit changes    '+'<html><body><a href="/login"><button style="color:green;">logout</button></a></body></html>'
        else:
            return redirect('/')
    return render_template('edit_users.html', var=k,error=error,my_events=my_events,user_in_use =user_in_use )





#Event page that returns seach queries
@app.route('/search/<queries>', methods=['GET','POST'])
def search_events(queries):

    error = None

    #check if logged in
    if g.user:

        #Checks the user's events to display on the webpage
        events = db.events.find({'who_made_me':g.user})
        my_events = []
        for i in events:
            my_events.append(i['name'])

        #Gets the name of the user logged in
        user_in_use = g.user

        #Search results of the query are built on the URL. This function if the search DB for results 'like' query
        search_results= db.events.find({'name':{'$regex': queries}})

        #Return data and load page
        return render_template('search_results.html',events=search_results,error=error,my_events=my_events,user_in_use =user_in_use )

    else:
        return redirect(url_for('login'))


#Views all events. The URL will be locomotive.com/events/view
@app.route('/events/view',methods=['GET','POST'])
def view_events():

    #Gets the name of the user logged in
    user_in_use = g.user

    #Gets the user's events
    events = db.events.find({'who_made_me':g.user})
    my_events = []
    for i in events:
        my_events.append(i['name'])

    #check if logged in
    if g.user:

        #Grabs all the events
        all_events = db.events.find()

        what_event = ""
        results = []
        #If data is posted, redirect to the search page where the query will take place and will display data. This should be real time instead of the redirects
        if request.method == 'POST':
            search_term = request.json['search']
            search_results = db.events.find({'name': {'$regex': search_term}})
            for i in search_results:
                results.append(i['name'])
            print results
            return jsonify(results=results)

        return render_template('view_events.html',all_events=all_events,my_events=my_events,user_in_use =user_in_use )
    else:
        return redirect(url_for('login'))


#Create an event. The URL will be locomotive.com/events/create
@app.route('/events/create',methods=['GET','POST'])
def create_event():

    #Gets the name of the user logged in
    user_in_use = g.user

    #Gets the user's events
    events = db.events.find({'who_made_me':g.user})
    my_events = []
    for i in events:
        my_events.append(i['name'])

    #If logged in
    if g.user:
        error = None

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


                #If a photo is uploaded, save it
                if request.files['photo'].filename != '':
                    filename = photos.save(request.files['photo'])

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
                    'who_made_me': g.user,
                    'when_made' : datetime.datetime.today()

                }

                #Add event
                insert = db.events.insert(event_data)

                #Send an email stating that the event has been added
                msg = Message('Hello %s, You just created an event!' %(g.user), sender = email, recipients = [request.form['email']])
                msg.body ='Your event %s was successfully added! Check it out here:locahost:5000/events/%s' %(request.form['name'],request.form['name'])
                mail.send(msg)

                return redirect('/events/%s' %(request.form['name']))
        return render_template('create_event.html',user_in_use=user_in_use,error=error,my_events=my_events)


#edit a particular event.The URL will be locomotive.com/events/edit/eventname
@app.route('/events/edit/<event_name>',methods=['GET','POST'])
def edit_particular_event(event_name):

    #Gets the name of the user logged in
    user_in_use = g.user

    #gets the user's events
    events = db.events.find({'who_made_me':g.user})
    my_events = []
    for i in events:
        my_events.append(i['name'])


    #Check if logged in
    if g.user:

        error = None

        #Checks if the user who is trying to edit the event actually owns it
        var = db.events.find_one({'who_made_me':g.user,'name': event_name})

        #If the user doesn't own it, then GTFO
        if not var:
            return redirect('/')


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
                changes = {'name':'Not changed', 'email':'Not changed', 'venue':'Not changed', 'address':'Not changed', 'description':'Not changed', 'phone_number': 'Not changed', 'time':'Not changed', 'duration':'Not changed' ,'date':'Not changed' }

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

                if var['date']  != datetime.date(year,month,day):
                    var['date'] ='%s-%s-%s'%(year,month,day)
                    changes['date'] = '%s-%s-%s'%(year,month,day)
                    changes['date'].encode('utf-8')
                    db.events.save(var)

                #Emails the stuff that has been edited to the user
                    msg = Message('Hello %s, You just edited an event: %s!' % (g.user,var['name']), sender=email,recipients=[request.form['email']])
                    msg.body ='Your changes: '
                    for key,values in changes.iteritems():
                        if values != 'Not changed':
                            msg.body += key +': '+values+'  '

                    mail.send(msg)
                    return redirect('/events/%s' %(var['name']))
            except:
                error = 'Incorrect Email'



    else:
        return redirect(url_for('login'))
    return render_template('editing_html.html',var=var,error=error,my_events=my_events,user_in_use =user_in_use )


#Each individual event's page auto generated. The URL will be locmotive.com/events/eventname
@app.route('/events/<event_name>',methods=['GET','POST'])
def view_particular_event(event_name):

    #Sets the event value to not past
    past = False

    #Gets the name of the user logged in
    user_in_use = g.user

    #Gets the user's events
    events = db.events.find({'who_made_me':g.user})
    my_events = []
    for i in events:
        my_events.append(i['name'])


    #If logged in
    if g.user:


        #Check if past_event:

        if db.events.find_one({'name':event_name}) != None:
            event = db.events.find_one({'name': event_name})
        elif db.past_events.find_one({'name':event_name}) != None:
             event = db.past_events.find_one({'name':event_name})
             past = True





        #querying the map from OSM API. It takes the Address of the location as OSM search and spits out a lat and lng


        var = event

        geocode = geocoder.osm(var['address'])
        lat_of_event = geocode.json["lat"]
        lng_of_event = geocode.json["lng"]

        #Real time search for users that are attending the event, will be implemented for events also
        results = []
        search_results = None
        search_term = None
        if request.method == 'POST' :

            search_term = request.json['search']
            search_results = db.users.find({'going_to':var['name'], 'name':{'$regex': search_term}})
            for i in search_results:
                results.append(i['name'])
            print results
            return  jsonify(results=results)









        return render_template('one_event.html', var=var,my_events=my_events,user_in_use =user_in_use,lat=lat_of_event,lng=lng_of_event,search_results=search_results,past=past,results=results)
    else:
        return redirect(url_for('login'))

#Deletion of an event/user
@app.route('/delete/<name>',methods=['GET','POST'])
def deleteion(name):

    #Find the event
    delete_event = db.events.find_one({'name':name})

    #if the event is found, delete it
    if delete_event:
         db.events.remove({'name':delete_event['name']})
         return redirect('/')

    #if the event is not found, then it has to be a user. Find and delete user
    else:
        user_to_delete = db.users.find_one({'name':name})
        db.events.remove({'name':name})
        return redirect('/login')


#If you wanna get in touch with someone going to the events, you can email them. The URL here will be locomotive.com/email/usertoemail
@app.route('/email/<name>', methods=['GET','POST'])
def email_request(name):

    error = None

    #If logged in
    if g.user:

        #The user to whom you're trying to contact
        user_to = db.users.find_one({'name':name})

        #The user logged in
        who_am_i = db.users.find_one({'name':g.user})

        #The user's events
        events = db.events.find({'who_made_me': g.user})
        my_events = []
        for i in events:
            my_events.append(i['name'])

        #If data is sent, then email the person.
        if request.method == 'POST':
            msg = Message('Hello,%s has emailed you regarding an event,please contact them back' %(g.user), sender = email, recipients = [user_to['email']] )
            msg.body =request.form['message']
            mail.send(msg)

            # Data to append to log
            log_data = {
                'from': g.user,
                'to': user_to['name'],
                'when': time.asctime(time.localtime(time.time)),
                'message': request.form['message']
            }
            # add to log
            db.transaction_log.insert_one(log_data)

            return redirect('/')

    else:
        return redirect(url_for('login'))
    return render_template('email_request.html',user_to=user_to,user_in_use=who_am_i,my_events=my_events,error=error)

@app.route('/request/phone_number/<who>',methods=['GET','POST'])
def phone_number_response(who):
    if g.user:
        error = None
        user_to = db.users.find_one({'name':who})
        who_am_i = db.users.find_one({'name':g.user})

        events = db.events.find({'who_made_me': g.user})
        my_events = []
        for i in events:
            my_events.append(i['name'])

        if request.method == 'POST':
            msg = Message('Hello,%s has emailed you regarding an event,please contact them back' %(g.user), sender = email, recipients = [user_to['email']] )
            msg.body =request.form['message']
            mail.send(msg)
            return redirect('/')
    else:
        return redirect(url_for('login'))
    return render_template('phone_request.html',user_to=user_to,user_in_use=who_am_i,my_events=my_events,error=error)

#This here is not valid, this is supposed to be when you wanna contact them via text.Which is incomplete as I dont have a GSM server
@app.route('/events/all/past' ,methods =['GET','POST'])
def view_past_events():
    if g.user:
        error = None
        past_events =db.past_events.find()

        events = db.events.find({'who_made_me': g.user})
        my_events = []
        for i in events:
            my_events.append(i['name'])

        if request.method == 'POST':
            what_event = request.form['search_events'].encode('utf-8')
            return redirect('/search'+'/past''/'+what_event)

    else:
        return redirect('/login')
    return render_template('view_past_events.html',user_in_use = g.user,my_events=my_events,error=error,past_events=past_events)


#This script add to the users attending event list
@app.route('/goto/<name>')
def goto(name):

    #Appending to the event's who_is_coming list
     db.events.update({'name': name}, {'$push': {'who_is_coming': g.user}})

     #Appending to the user's going_to list
     db.users.update({'name': g.user}, {'$push': {'going_to': name}})
     return redirect('/')



#This feature is the same as search events but is for searching past events. Which also needs to be real time
@app.route('/search/past/<queries>', methods=['GET','POST'])
def search_past_events(queries):
    error = None
    #check if logged in
    if g.user:
        my_events = db.events.find({'who_made_me':g.user})
        user_in_use = g.user
        search_results= db.past_events.find({'name':{'$regex': queries}})

        return render_template('search_results.html',events=search_results,error=error,my_events=my_events,user_in_use =user_in_use )
    else:
        return redirect(url_for('login'))

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
    app.secret_key='gnejrgbejberjekg'
    configure_uploads(app, photos)


    app.run(host='0.0.0.0', port=5000,threaded=True)
