#Locomotive
An open source community platform in Auroville for carpooling

#Requirements
* Python V2.7
* MongoDB V2.6.10
* Bcrypt
* Flask_Uploads
* Flask_Mail
* Pymongo
* Threading
* Geocoder

#Set up

Start the MongoDB process
```
sudo mongod
```

Create a file called emaildata.py, in their you need to add two variables:
```
email = your email address
password = your email's password
```
After that, go to your gmail's setttings at https://myaccount.google.com/security .
Under the section 'Connected apps & sites', switch on Allowed Less Secure Apps

After this, open up a terminal and navigate to the Locomotive directory, and then run the webserver by this command
```
python webserver.py
```
Keep the terminal open and go to your web browser and enter: 0.0.0.0:5000/

#Queries at aarnavbos@gmail.com
