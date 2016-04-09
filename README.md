Right,
<br>
<br>
<br>

The modules needed to run Locomotive are(BTW, not sure about pip names of these, so please google):<br>
1.bcrypt(hashing passwords)<br>
2.Flask<br>
3.GoogleMaps python API<br>
4.flask-googlemaps<br>
5.flask_mail<br>
6.requests<br>
7.random<br>
8.string<br>

<br><br><br>
You'll also need two python files locally that are:<br>
1.key.py<br>
which should have a variable key='YOUR GOOGLE MAPS API KEY' which you can get from console.developers.google.com.<br> 
Enable all APIs under the MapsAPI section except the Android,iOS,SDK. and after enabling, generate credentials which should give you a key.<br><br>
2.mail_server_pass.py<br>
which should have two variables:<br>
email = 'your email id'<br>
password = 'your email's password'<br>
This is for auto email sending. BTW, Gmail disables this feature, it doesn't let external apps send auto emails from your email ID.<br>
Inorder to change that, go to https://myaccount.google.com/security and scroll all the way down and enable Allow less secure apps.<br>
Both of these files should be stored alongside webserver.py and DB.py
<br><br><br>
To get started running it<br>
Run DB.py<br>
run webserver.py<br>
(host = 0.0.0.0 and port = 5000 as configured in the web server)<br>
go to localhost:5000/create <br>
create a user<br>
Go to your email, get the URL and paste it, on the new tab. Alas! you're created a user. Login and everything's straight forward from there.




