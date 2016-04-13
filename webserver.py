from flask import * #web framework
from DB import * #SQLalchemy database.py file

import os
from flask_uploads import UploadSet, configure_uploads, IMAGES
import os.path

import datetime

from key import key # key for GoogleMaps API
from mail_server_pass import email,password #mail server password info

from flask_uploads import UploadSet,IMAGES,configure_uploads

from bcrypt import hashpw, gensalt #module to hash passwords
from validate_email import validate_email

from sqlalchemy.orm import sessionmaker # SQL API
from sqlalchemy import create_engine # SQL API

from flask_googlemaps import GoogleMaps#GoogleMaps API
import googlemaps #GoogleMaps API

import requests#To ping GoogleMaps API for maps
from flask_mail import Mail, Message#Auto email sending module

import random#To generate random URLs
import string#To generate random URLs

#GoogleMaps API URLs that I need to request
search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
details_url = "https://maps.googleapis.com/maps/api/place/details/json"


#creating Flask app
app = Flask(__name__)
GoogleMaps(app)






#configuring Mail server
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = email #Email is stored on different file due to github
app.config['MAIL_PASSWORD'] = password#password of that email is also stored on a different file
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

#creating instance of flask-mail
mail = Mail(app)


#DB connection and creating session
engine = create_engine('sqlite:///users.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
con = DBSession()

#To generate random characters to add to URL
def url_gen(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

#Check if status 'I am logged in as USERNAME' exists before proceeding to any route
@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']

'''
@app.before_request
def after_event():
    w = datetime.date.today()
    print w.strftime("We are the %d,%m,%Y")
    events = con.query(Events).all()
    for past in events:
        if past.date < w:
            query_it = con.query(Events).filter_by(name=past.name).first()
            add_to_past = Past_Events(name=query_it.name,email=query_it.email,phone_number=query_it.phone_number,venue=query_it.venue,description=query_it.description,date=query_it.date,time=query_it.time,duration=query_it.duration,who_made_me=query_it.who_made_me,address=query_it.address,image=query_it.image,who_came=query_it.who_is_coming)
            con.add(add_to_past)
            con.commit()
            con.delete(query_it)
            con.commit()
'''
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

        user = con.query(Users).filter_by(name=g.user).first()
        user_name = user.name
        what_events_i_own =con.query(Events).filter_by(who_made_me=g.user).all()
        if request.method == 'POST':
            pass


        return render_template('home.html',user=user,user_name=user_name,what_events_i_own=what_events_i_own,date=date)

    else:
        return redirect(url_for('login'))


#Creating user
@app.route('/create', methods =['GET','POST'])
def create_user():
    error = None
    if request.method == 'POST':

        #if passwords entered didn't match
        if request.form['create_password'] != request.form['password_re_enter']:
            error = "Passwords don't match, re enter!"

        #checks if a user with the same username exists
        elif con.query(Users).filter_by(name = request.form['create_username']).first() or con.query(AUTH).filter_by(name=request.form['create_username']).first():
             error = "Username already exists"

        #If phone number is an integer or if it isn't 10 raise error
        elif request.form['phone_number'].isdigit() != True or len(str(request.form['phone_number'])) != 10 :
             error = 'Invalid phone number'

        #calls the password from the form, hashes it and appends it to the Database. and finally, creates user
        else:
            #to generate random url for creating user
            try:
                hashed_password = hashpw(request.form['create_password'].encode('utf-8'),gensalt())
                adding_user = AUTH(name=request.form['create_username'], password=hashed_password, email=request.form['email'],community=request.form['community'],phone_number=request.form['phone_number'])
                con.add(adding_user)
                con.commit()
                usr_name = con.query(AUTH).filter_by(name=request.form['create_username']).first()
                url = url_gen()#Creating a random part of URL to use
                msg = Message('Hello, Thanks for creating a user @ Locomotive!', sender = email, recipients = [request.form['email']])
                msg.body = "Hello, Thanks for creating a user @ Locomotive! click this URL to activate your account!   "+"localhost:5000"+'/adduser/'+url+'/'+usr_name.name
                mail.send(msg)
                return redirect(url_for('login'))

            except:
                error='Invalid email!'

    return render_template('create_user.html', error=error)

@app.route('/adduser/<url>/<user_name>',methods=['GET'])
def add_user(url,user_name):

    #move data from auth to the registered user DB
    w = con.query(AUTH).filter_by(name=user_name).first()
    e = Users(name=w.name,password=w.password,email=w.email,phone_number=w.phone_number,community=w.community)
    con.add(e)
    con.commit()
    #delete the data in AUTH
    con.query(AUTH).filter_by(name=user_name).delete()
    con.commit()
    return "User verified    "+user_name + "    login@"+"   localhost:5000/login"

#Login page,need to add forgot password option
@app.route('/login', methods=['GET','POST'])
def login():
    session.pop('user',None) # kills the already logged in session cookie
    querying = con.query(Users).all()
    error = None
    if request.method == 'POST':
        look_for = con.query(Users).filter_by(name = request.form['username']).first()
        if look_for : #if user exists then check password
            passwd = request.form['password'].encode('utf-8')
            if hashpw(passwd,look_for.password) == look_for.password:
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
    my_events = con.query(Events).filter_by(who_made_me=g.user).all()
    error = ""
    if g.user:
        if con.query(Users).filter_by(name=g.user).first().name == edit_user:
            edit_user= con.query(Users).filter_by(name=g.user).first()
            if request.method == 'POST':
                if hashpw(request.form['old_password'].encode('utf-8'),edit_user.password) != edit_user.password:
                    error="Old password and New one don't match"
                elif request.form['password'] != request.form['new_password']:
                    error = "New passwords don't match"
                else:
                    edit_user.name = request.form['name']
                    edit_user.password = hashpw(request.form['password'].encode('utf-8'),gensalt())
                    edit_user.email = request.form['email']
                    edit_user.phone_number = request.form['phone_number']
                    edit_user.community = request.form['community']
                    con.commit()

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
        my_events = con.query(Events).filter_by(who_made_me=g.user).all()
        user_in_use = g.user
        search_results= con.query(Events).filter(Events.name.like('%'+'%s'%(queries)+'%' )).all()
        #for stuff in search_results:
         #   return stuff.name
                #search_results= con.query(Events).filter(Events.name.like("y%")).all()
        return render_template('search_results.html',events=search_results,error=error,my_events=my_events,user_in_use =user_in_use )
    else:
        return redirect(url_for('login'))



#Views all events
@app.route('/events/view',methods=['GET','POST'])
def view_events():
    user_in_use = g.user
    my_events = con.query(Events).filter_by(who_made_me=g.user).all()
    #check if logged in
    if g.user:
        all_events = con.query(Events).all()
        what_event = ""
        if request.method == 'POST':
            what_event = request.form['search_events'].encode('utf-8')
            return redirect('/search'+'/'+what_event)

        return render_template('view_events.html',all_events=all_events,my_events=my_events,user_in_use =user_in_use )
    else:
        return redirect(url_for('login'))



#creates an event and registers it. need to add which user did made it
@app.route('/events/create',methods=['GET','POST'])
def create_event():
    user_in_use = g.user
    my_events = con.query(Events).filter_by(who_made_me=g.user).all()
    if g.user:
        error = None
        if request.method == 'POST':
            year = int(request.form['year'])
            month = int(request.form['month'])
            day = int(request.form['day'])

            #check if event exists
            it_exists = con.query(Events).filter_by(name=request.form['name']).first()
            if it_exists:
                error = 'Event exists!!!!'
            #Check if phone number is an INT and is 10 digits
            elif request.form['phone_number'].isdigit() != True or len(str(request.form['phone_number'])) != 10 :
                error = 'Invalid phone number'


            elif os.path.isfile("static/img/%s" %(request.files['photo'].filename)):
                error = "Filename already exists please rename file"



            elif 'photo' in request.files:

                filename = photos.save(request.files['photo'])
                print filename
                add_event = Events(name= request.form['name'],email=request.form['email'],phone_number=request.form['phone_number'],venue=request.form['venue'],description=request.form['description'],time = request.form['time'],date =datetime.date(year,month,day),duration =request.form['duration'],who_made_me=g.user,address=request.form['address'],image=filename)
                con.add(add_event)
                con.commit()
                msg = Message('Hello %s, You just created an event!' %(g.user), sender = email, recipients = [request.form['email']])
                msg.body ='Your event %s was successfully added! Check it out here:locahost:5000/events/%s' %(request.form['name'],request.form['name'])
                mail.send(msg)

                return redirect('/events/%s' %(request.form['name']))



            else:

                add_event = Events(name= request.form['name'],email=request.form['email'],phone_number=request.form['phone_number'],venue=request.form['venue'],description=request.form['description'],time = request.form['time'],date =datetime.date(year,month,day),duration =request.form['duration'],who_made_me=g.user,address=request.form['address'],image=None)
                con.add(add_event)
                con.commit()
                msg = Message('Hello %s, You just created an event!' %(g.user), sender = email, recipients = [request.form['email']])
                msg.body ='Your event %s was successfully added! Check it out here: localhost:5000/events/%s' %(request.form['name'],request.form['name'])
                mail.send(msg)


                return redirect('/events/%s' %(request.form['name']))

        return render_template('create_event.html',error=error,my_events=my_events,user_in_use =user_in_use )
    else:
        return redirect(url_for('login'))





#edit a particular event
@app.route('/events/edit/<event_name>',methods=['GET','POST'])
def edit_particular_event(event_name):
    user_in_use = g.user
    my_events = con.query(Events).filter_by(who_made_me=g.user).all()
    if g.user:
        error = None
        var = con.query(Events).filter_by(who_made_me=g.user,name=event_name).first()
        if not var:
            return redirect('/')
        #updating all the entries
        if request.method == 'POST':
            year = int(request.form['year'])
            month = int(request.form['month'])
            day = int(request.form['day'])

            #Check if phone number is an INT and is 10 digits
            if request.form['phone_number'].isdigit() != True or len(str(request.form['phone_number'])) != 10 :
                error = 'Invalid phone number'

            elif os.path.isfile("static/img/%s" %(request.files['photo'].filename)):
                error = "Filename already exists please rename file"

            if 'photo' in request.files:
                filename = photos.save(request.files['photo'])
                var.image = filename
                print var.image
                con.commit()

                changes = {'name':'Not changed', 'email':'Not changed', 'venue':'Not changed', 'address':'Not changed', 'description':'Not changed', 'phone_number': 'Not changed', 'time':'Not changed', 'duration':'Not changed' ,'date':'Not changed' }
                if var.name  != request.form['name']:
                    var.name = request.form['name']
                    changes['name'] = request.form['name']
                try:
                    datetime.date(year,month,day)
                except ValueError:
                    error = 'Incorrect Dates'

                if  var.email !=request.form['email']:
                    var.email = request.form['email']
                    changes['email'] = request.form['email']

                if var.venue != request.form['venue']:
                    var.venue = request.form['venue']
                    changes['venue'] = request.form['venue']

                if var.address != request.form['address']:
                    var.address = request.form['address']
                    changes['address'] = request.form['address']
                if var.description != request.form['description']:
                    var.description = request.form['description']
                    changes['description'] = request.form['description']

                if var.phone_number != request.form['phone_number']:
                    var.phone_number = request.form['phone_number']
                    changes['phone_number'] = request.form['phone_number']


                if var.time  != request.form['time']:
                    var.time = request.form['time']
                    changes['time'] = request.form['time']

                if var.duration  != request.form['duration']:
                    var.duration = request.form['duration']
                    changes['duration'] = request.form['duration']

                if var.date  != datetime.date(year,month,day):
                    var.date = datetime.date(year,month,day)
                    changes['date'] = var.date
                msg = Message('Hello %s, You just created an event!' %(g.user), sender = email, recipients = [request.form['email']])
                msg.body = ""
                for key,values in changes.iteritems():

                    if values != 'Not changed':
                        msg.body += key+'  :  '+values+'  '


                mail.send(msg)
                print changes


                con.commit()

                return redirect('/events/%s' %(var.name))

            else:
                if var.name  != request.form['name']:
                    var.name = request.form['name']
                try:
                    datetime.date(year,month,day)
                except ValueError:
                    error = 'Incorrect Dates'

                else:
                    var.email = request.form['email']
                    var.venue = request.form['venue']
                    var.address = request.form['address']
                    var.description = request.form['description']
                    var.phone_number = request.form['phone_number']
                    var.time = request.form['time']
                    var.duration = request.form['duration']
                    var.date = datetime.date(year,month,day)
                    var.image = None
                    con.commit()
                    return redirect('/events/%s'%(var.name))
                '''
                else:
                    var.email = request.form['email']
                    var.venue = request.form['venue']
                    var.address = request.form['address']
                    var.description = request.form['description']
                    var.phone_number = request.form['phone_number']
                    var.time = request.form['time']
                    var.duration = request.form['duration']
                    var.date = datetime.date(year,month,day)
                    con.commit()
                    return redirect('/')

                '''



    else:
        return redirect(url_for('login'))
    return render_template('editing_html.html',var=var,error=error,my_events=my_events,user_in_use =user_in_use )


#Each individual event's page auto generated
@app.route('/events/<event_name>',methods=['GET','POST'])
def view_particular_event(event_name):
    user_in_use = g.user
    my_events = con.query(Events).filter_by(who_made_me=g.user).all()
    #check if logged in
    if g.user:
        #querying the map from GoogleMap API. It takes the Address of the location as GoogleMap search and spits out a link
        event=con.query(Events).filter_by(name=event_name).first()
        var = event
        i_am_coming = con.query(Users).filter_by(name=g.user).first()
        search_payload = {"key":key, "query":var.address}
        search_req = requests.get(search_url, params=search_payload)
        search_json = search_req.json()

        place_id = search_json["results"][0]["place_id"]

        details_payload = {"key":key, "placeid":place_id}
        details_resp = requests.get(details_url, params=details_payload)
        details_json = details_resp.json()

        wololo=details_json["result"]["url"]


        if request.method == 'POST':
            event.who_is_coming.append(i_am_coming)
            con.commit()
            return redirect(url_for('home'))

        return render_template('one_event.html', var=var,wololo=wololo,my_events=my_events,user_in_use =user_in_use,keys=key )
    else:
        return redirect(url_for('login'))

@app.route('/delete/<name>',methods=['GET','POST'])
def deleteion(name):
    delete_event = con.query(Events).filter_by(name=name).first()
    if delete_event:
         con.delete(delete_event)
         con.commit()
         return redirect('/')
    else:
        user_to_delete = con.query(Users).filter_by(name=name).first()

        events_of_user = con.query(Events).filter_by(who_made_me=user_to_delete.name).all()
        con.delete(user_to_delete)
        for events in events_of_user:
            con.delete(events.name)
        con.commit()
        con.delete(user_to_delete)
        con.commit()
        return redirect('/login')

@app.route('/email/<name>', methods=['GET','POST'])
def email_request(name):
    error = None
    if g.user:
        user_to = con.query(Users).filter_by(name=name).first()
        who_am_i = con.query(Users).filter_by(name=g.user).first()
        my_events = con.query(Events).filter_by(who_made_me=g.user).all()
        if request.method == 'POST':
            msg = Message('Hello,%s has emailed you regarding an event,please contact them back' %(g.user), sender = email, recipients = [user_to.email] )
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
        user_to = con.query(Users).filter_by(name=who).first()
        who_am_i = con.query(Users).filter_by(name=g.user).first()
        my_events = con.query(Events).filter_by(who_made_me=g.user).all()
        if request.method == 'POST':
            msg = Message('Hello,%s has emailed you regarding an event,please contact them back' %(g.user), sender = email, recipients = [user_to.email] )
            msg.body =request.form['message']
            mail.send(msg)
            return redirect('/')
    else:
        return redirect(url_for('login'))
    return render_template('phone_request.html',user_to=user_to,user_in_use=who_am_i,my_events=my_events,error=error)

#RUN IT GUT
if __name__ == '__main__':
    app.debug = True
    app.secret_key='gnejrgbejberjekg'
    configure_uploads(app, photos)

    app.run(host='0.0.0.0', port=5000)