from flask import * #web framework
from DB import * #SQLalchemy database.py file

from key import key # key for GoogleMaps API
from mail_server_pass import email,password #mail server password info

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

        user = con.query(Users).filter_by(name=g.user).first()
        user_name = user.name
        what_events_i_own =con.query(Events).filter_by(who_made_me=g.user).all()
        return render_template('home.html',user=user,user_name=user_name,what_events_i_own=what_events_i_own)

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
    error = ""
    if g.user:
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
                return 'Please login again, to commit changes    '+'<html><body><a href="/login"><button>logout</button></a></body></html>'
    return render_template('edit_users.html', var=edit_user,error=error)




#Main event page, only shows the most recent ones
@app.route('/search/<queries>', methods=['GET','POST'])
def search_events(queries):
    #check if logged in
    if g.user:
        y = '%s'%(queries)
        search_results= con.query(Events).filter(Events.name.like('%'+'%s'%(queries)+'%' )).all()
        print y
        #for stuff in search_results:
         #   return stuff.name
                #search_results= con.query(Events).filter(Events.name.like("y%")).all()
        return render_template('events.html',events=search_results )
    else:
        return redirect(url_for('login'))



#Views all events
@app.route('/events/view',methods=['GET','POST'])
def view_events():
    #check if logged in
    if g.user:
        all_events = con.query(Events).all()
        what_event = ""
        if request.method == 'POST':
            what_event = request.form['search_events'].encode('utf-8')
            return redirect('/search'+'/'+what_event)

        return render_template('view_events.html',all_events=all_events)
    else:
        return redirect(url_for('login'))




#creates an event and registers it. need to add which user did made it
@app.route('/events/create',methods=['GET','POST'])
def create_event():
    if g.user:
        error = None
        if request.method == 'POST':
            #check if event exists
            it_exists = con.query(Events).filter_by(name=request.form['name']).first()
            if it_exists:
                error = 'Event exists!!!!'
            #Check if phone number is an INT and is 10 digits
            elif request.form['phone_number'].isdigit() != True or len(str(request.form['phone_number'])) != 10 :
                error = 'Invalid phone number'
            #if all conditions are satisfied adds it to the DB
            else:
                add_event = Events(name= request.form['name'],email=request.form['email'],phone_number=request.form['phone_number'],venue=request.form['venue'],description=request.form['description'],time = request.form['time'],date =request.form['date'],duration =request.form['duration'],who_made_me=g.user,address=request.form['address'])
                con.add(add_event)
                con.commit()

        return render_template('create_event.html',error=error)
    else:
        return redirect(url_for('login'))




#Views events you can edit
@app.route('/events/edit/',methods=['GET','POST'])
def view_events_for_edit():
    #check if logged in
    if g.user:

        event = con.query(Events).filter_by(who_made_me=g.user).all()
        #urls = var.name
        return render_template('edit_events.html', var=event)

    else:
        return redirect(url_for('login'))

#edit a particular event
@app.route('/events/edit/<event_name>',methods=['GET','POST'])
def edit_particular_event(event_name):
    if g.user:
        error = None
        var = con.query(Events).filter_by(who_made_me=g.user,name=event_name).first()
        #updating all the entries
        if request.method == 'POST':
            var.name = request.form['name']
            var.email = request.form['email']
            var.venue = request.form['venue']
            var.address = request.form['address']
            var.description = request.form['description']
            var.phone_number = request.form['phone_number']
            var.time = request.form['time']
            var.duration = request.form['duration']
            var.date = request.form['date']
            con.commit()
            return redirect(url_for('/events/%s'%(event_name)))
    else:
        return redirect(url_for('login'))
    return render_template('editing_html.html',var=var,error=error)


#Each individual event's page auto generated
@app.route('/events/<event_name>',methods=['GET','POST'])
def view_particular_event(event_name):
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

        return render_template('one_event.html', var=var,wololo=wololo)
    else:
        return redirect(url_for('login'))

@app.route('/delete/<name_of_thing>',methods=['GET','POST'])
def deleteion(name_of_thing):
    pass



#RUN IT GUT
if __name__ == '__main__':
    app.debug = True
    app.secret_key='gnejrgbejberjekg'
    app.run(host='0.0.0.0', port=5000)