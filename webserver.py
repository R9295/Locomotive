from flask import * #web framework
from pymongo import *
from datetime import datetime
import os
from flask_uploads import UploadSet, configure_uploads, IMAGES
import os.path
import threading
import datetime


from flask_uploads import UploadSet,IMAGES,configure_uploads

from bcrypt import hashpw, gensalt

from pymongo import MongoClient


from emaildata import *
from flask_mail import Mail, Message

import random#To generate random URLs
import string#To generate random URLs

from Data_validation import *
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

#Check if status 'I am logged in as USERNAME' exists before proceeding to any route
@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']






photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'



@app.route('/')
def home():
    if g.user:
            return redirect('/'+g.user)
    else:
        return redirect(url_for('login'))

#Home page of any user
@app.route('/<user>', methods=['GET','POST'])
def homeof_user(user):
    if g.user:
        date = datetime.date.today()

        user = db.users.find_one({"name":g.user})

        what_events_i_own = db.events.find({"who_made_me":g.user})

        if request.method == 'POST':
            pass


        return render_template('home.html',user=user,what_events_i_own=what_events_i_own,date=date)

    else:
        return redirect(url_for('login'))


#Creating user
@app.route('/create', methods =['GET','POST'])
def create_user():
    error = None
    if request.method == 'POST':
        validates =validate_create_user_input(password=request.form['create_password'],username=request.form['create_username'],password_again=request.form['password_re_enter'],phone=request.form['phone_number'])


        if validates != None:
            error = validates

        #calls the password from the form, hashes it and appends it to the Database. and finally, creates user
        else:
            #to generate random url for creating user
            try:
                hashed_password = hashpw(request.form['create_password'].encode('utf-8'),gensalt())
                add_user = {
                    'name' : request.form['create_username'],
                    'password' : hashed_password,
                    'phone_number' : request.form['phone_number'],
                    'email' : request.form['email'],
                    'community' : request.form['community'],
                    'going_to' : []


                }
                added = db.user_auth.insert_one(add_user)
                url = url_gen()#Creating a random part of URL to use
                msg = Message('Thanks for creating a user @ Locomotive!', sender = email, recipients = [request.form['email']])
                msg.body = "Hello, Thanks for creating a user @ Locomotive! click this URL to activate your account!   "+"localhost:5000"+'/adduser/'+url+'/'+request.form['create_username']
                mail.send(msg)
                return redirect(url_for('login'))

            except:
                error='Invalid email!'

    return render_template('create_user.html', error=error)

@app.route('/adduser/<url>/<user_name>',methods=['GET'])
def add_user(url,user_name):
    user = db.user_auth.find_one({'name':user_name})
    adding_user = {
        'name': user['name'],
        'password': user['password'],
        'email': user['email'],
        'phone_number': user['phone_number'],
        'community': user['community'],
        'going_to': []
    }
    add_to_db = db.users.insert_one(adding_user)
    return "User verified    "+user_name + "    login@"+"   localhost:5000/login"

#Login page,need to add forgot password option
@app.route('/login', methods=['GET','POST'])
def login():
    session.pop('user',None) # kills the already logged in session cookie
    error = None
    if request.method == 'POST':
        look_for = db.users.find_one({'name':request.form['username']})
        if look_for : #if user exists then check password
            passwd = request.form['password'].encode('utf-8')
            if hashpw(passwd,look_for['password'].encode('utf-8')) == look_for['password']:
                session['user'] = request.form['username'] #adds  status 'I am logged in as USERNAME' to the cookies
                return redirect(url_for('home')) #Might wanna change the page it redirects to if login is successful

            else:
                   error = 'Incorrect Password'
        else:
            error = "Username doesn't exist"

    return render_template('login.html', error=error,)



@app.route('/<edit_user>/edit', methods=['GET','POST'])
def edit_user(edit_user):
    user_in_use = g.user
    my_events = db.events.find({'who_made_me':g.user})
    error = ""
    if g.user:
        k = db.events.find({'name': g.user})
        if k['name'] == edit_user:
            if request.method == 'POST':
                if hashpw(request.form['old_password'].encode('utf-8'),k['password']) != edit_user.password:
                    error="Old password and New one don't match"
                elif request.form['password'] != request.form['new_password']:
                    error = "New passwords don't match"
                else:
                    k['password'] = hashpw(request.form['password'].encode('utf-8'),gensalt())
                    k['email'] = request.form['email']
                    k['phone_number'] = request.form['phone_number']
                    k['community'] = request.form['community']
                    db.users.save(k)

                    return 'Please login again, to commit changes    '+'<html><body><a href="/login"><button style="color:green;">logout</button></a></body></html>'
        else:
            return redirect('/')
    return render_template('edit_users.html', var=edit_user,error=error,my_events=my_events,user_in_use =user_in_use )





#Main event page, only shows the most recent ones
@app.route('/search/<queries>', methods=['GET','POST'])
def search_events(queries):
    error = None
    #check if logged in
    if g.user:
        my_events = db.events.find({'who_made_me':g.user})
        user_in_use = g.user
        search_results= db.events.find({'name':{'$regex': queries}})
        return render_template('search_results.html',events=search_results,error=error,my_events=my_events,user_in_use =user_in_use )
    else:
        return redirect(url_for('login'))


#Views all events
@app.route('/events/view',methods=['GET','POST'])
def view_events():
    user_in_use = g.user
    my_events = db.events.find({'who_made_me':g.user})
    #check if logged in
    if g.user:
        all_events = db.events.find()
        what_event = ""
        if request.method == 'POST':
            what_event = request.form['search_events'].encode('utf-8')
            return redirect('/search'+'/'+what_event)

        return render_template('view_events.html',all_events=all_events,my_events=my_events,user_in_use =user_in_use )
    else:
        return redirect(url_for('login'))



@app.route('/events/create',methods=['GET','POST'])
def create_event():
    user_in_use = g.user
    my_events = db.events.find({'who_made_me':g.user})
    if g.user:
        error = None
        if request.method == 'POST':

            validates =  validate_event_input(phone=request.form['phone_number'],y=request.form['year'],m=request.form['month'],d=request.form['day'],name=request.form['name'])
            if validates != None:
                error = validates


            elif os.path.isfile("static/img/%s" %(request.files['photo'].filename)):
                error = "Filename already exists please rename file"


            else:
                filename = None

                year = int(request.form['year'])
                month = int(request.form['month'])
                day = int(request.form['day'])

                if request.files['photo'].filename != '':
                    filename = photos.save(request.files['photo'])
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
                insert = db.events.insert(event_data)
                msg = Message('Hello %s, You just created an event!' %(g.user), sender = email, recipients = [request.form['email']])
                msg.body ='Your event %s was successfully added! Check it out here:locahost:5000/events/%s' %(request.form['name'],request.form['name'])
                mail.send(msg)

                return redirect('/events/%s' %(request.form['name']))
        return render_template('create_event.html',user_in_use=user_in_use,error=error,my_events=my_events)


#edit a particular event
@app.route('/events/edit/<event_name>',methods=['GET','POST'])
def edit_particular_event(event_name):
    user_in_use = g.user
    my_events = db.events.find({'who_made_me':g.user})
    if g.user:
        error = None
        var = db.events.find_one({'who_made_me':g.user,'name': event_name})
        if not var:
            return redirect('/')
        #updating all the entries
        if request.method == 'POST':
            try:
                validates =validate_event_edit_input(phone=request.form['phone_number'],y=request.form['year'],m=request.form['month'],d=request.form['day'])
                if validates != None:
                        error = validates


                elif os.path.isfile("static/img/%s" %(request.files['photo'].filename)):
                    error = "Filename already exists please rename file"

                else:
                    if request.files['photo'].filename != '':
                        filename = photos.save(request.files['photo'])
                        var['image'] = filename
                        db.events.save(var)
                changes = {'name':'Not changed', 'email':'Not changed', 'venue':'Not changed', 'address':'Not changed', 'description':'Not changed', 'phone_number': 'Not changed', 'time':'Not changed', 'duration':'Not changed' ,'date':'Not changed' }

                year = int(request.form['year'])
                month = int(request.form['month'])
                day = int(request.form['day'])

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


#Each individual event's page auto generated
@app.route('/events/<event_name>',methods=['GET','POST'])
def view_particular_event(event_name):
    past = False
    user_in_use = g.user
    my_events = db.events.find({'who_made_me':g.user})
    if g.user:
        #querying the map from OSM API. It takes the Address of the location as OSM search and spits out a lat and lng
        event=db.events.find_one({'name':event_name})
        var = event
        try:
            geocode = geocoder.osm(var['address'])
            lat_of_event = geocode.json["lat"]
            lng_of_event = geocode.json["lng"]
        except AttributeError:
            past = True
            event = db.past_events.find_one({'name':event_name})
            var = event
            geocode = geocoder.osm(var['address'])
            lat_of_event = geocode.json["lat"]
            lng_of_event = geocode.json["lng"]



        search_results = None
        search_term = None
        if request.method == 'POST' :

            search_term = request.json['search']
            print search_term
            search_results = db.users.find({'going_to':var['name'], 'name':{'$regex': search_term}})
            for k in search_results:
                print k['going_to']






        return render_template('one_event.html', var=var,my_events=my_events,user_in_use =user_in_use,lat=lat_of_event,lng=lng_of_event,search_results=search_results,past=past)
    else:
        return redirect(url_for('login'))

@app.route('/delete/<name>',methods=['GET','POST'])
def deleteion(name):
    delete_event = db.events.find_one({'name':name})
    if delete_event:
         db.events.remove({'name':delete_event['name']})
         return redirect('/')
    else:
        user_to_delete = db.users.find_one({'name':name})
        db.events.remove({'name':name})
        return redirect('/login')

@app.route('/email/<name>', methods=['GET','POST'])
def email_request(name):
    error = None
    if g.user:
        user_to = db.users.find_one({'name':name})
        who_am_i = db.users.find_one({'name':g.user})
        my_events = db.events.find({'who_made_me':g.user})
        if request.method == 'POST':
            msg = Message('Hello,%s has emailed you regarding an event,please contact them back' %(g.user), sender = email, recipients = [user_to['email']] )
            msg.body =request.form['message']
            mail.send(msg)
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
        my_events = db.events.find({'who_made_me':g.user})
        if request.method == 'POST':
            msg = Message('Hello,%s has emailed you regarding an event,please contact them back' %(g.user), sender = email, recipients = [user_to['email']] )
            msg.body =request.form['message']
            mail.send(msg)
            return redirect('/')
    else:
        return redirect(url_for('login'))
    return render_template('phone_request.html',user_to=user_to,user_in_use=who_am_i,my_events=my_events,error=error)


@app.route('/events/all/past' ,methods =['GET','POST'])
def view_past_events():
    if g.user:
        error = None
        past_events =db.past_events.find()
        my_events = db.events.find({'who_made_me':g.user})
        if request.method == 'POST':
            what_event = request.form['search_events'].encode('utf-8')
            return redirect('/search'+'/past''/'+what_event)

    else:
        return redirect('/login')
    return render_template('view_past_events.html',user_in_use = g.user,my_events=my_events,error=error,past_events=past_events)



@app.route('/search/users/<name>',methods=['GET','POST'])
def search_user(name):
    if request.method == 'POST':
        search_results = db.events.find_one({'who_is_coming':{'$regex': name}})
        print search_results


@app.route('/goto/<name>')
def goto(name):
     db.events.update({'name': name}, {'$push': {'who_is_coming': g.user}})
     db.users.update({'name': g.user}, {'$push': {'going_to': name}})
     return redirect('/')




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

def check_if_past():
    w = datetime.datetime.today()
    events = db.events.find()
    print 'checking for past events'
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


        threading.Timer(86400, check_if_past).start()


check_if_past()

#RUN IT GUT
if __name__ == '__main__':
    app.debug = True
    app.secret_key='gnejrgbejberjekg'
    configure_uploads(app, photos)


    app.run(host='0.0.0.0', port=5000,threaded=True)
