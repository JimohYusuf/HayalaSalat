from flask import Flask, render_template, request, redirect , jsonify 
from flask_mysqldb import MySQL

import datetime  
import yaml 
import mysql.connector 
import os 
import pygal
import json      

from datetime import datetime, date, timedelta 

#G Constants
SUCCESS = "POST Success"
FAIL    = "POST Failed"

#flask handle
app = Flask(__name__) 

#db param handle
dbParam = yaml.safe_load(open('loginParams.yaml')) 


#db config variables
app.config['MYSQL_HOST']     = dbParam['mysql_host']
app.config['MYSQL_USER']     = dbParam['mysql_user']
app.config['MYSQL_PASSWORD'] = dbParam['mysql_password']
app.config['MYSQL_DB']       = dbParam['mysql_db'] 

#db handle
dbConn = MySQL(app)

@app.route('/', methods=['POST', 'GET'])  
def root():
    return redirect("/home", code=302) 

@app.route('/home', methods=['POST', 'GET'])  
def home():
    return render_template("home.html") 

@app.route('/newuser', methods=['POST', 'GET'])  
def newuser():
    if request.method == 'POST': 
        data            = request.values
        name            = data['name']
        password        = data['pass'] 

        cur = dbConn.connection.cursor() 

        addNewUser(name, password, cur)
    return render_template("newuser.html") 
     
@app.route('/create_user', methods=['POST', 'GET'])  
def create_user():
    return render_template("create_user.html") 

@app.route('/<username>/<upassword>', methods=['POST', 'GET'])  
def signin(username, upassword):  
    name            = username 
    password        = upassword  
    #curr_salat      = data['salat'] 
    datte           = str(date.today().strftime("%d/%m/%Y")) 
    arrival_time    = str(datetime.now().strftime("%H:%M:%S")) 
    
    fajr_time       = '04:31:00'
    zuhr_time       = '12:51:00'
    asr_time        = '16:11:00'
    maghrib_time    = '19:23:00'   
    isha_time       = '21:01:00' 
    FMT             = '%H:%M:%S'

    salat_timings = [fajr_time, zuhr_time, asr_time, maghrib_time, isha_time] 
    salat_timings_dict = {fajr_time: 'fajr', zuhr_time: 'zuhr', asr_time: 'asr', maghrib_time: 'maghrib', isha_time: 'isha'} 

    for salat in salat_timings:
        time_diff_forward = datetime.strptime(arrival_time, FMT) - datetime.strptime(salat, FMT) 
        time_diff_backward = datetime.strptime(salat, FMT) - datetime.strptime(arrival_time, FMT) 

        print(abs(time_diff_forward.seconds)) 
        print(abs(time_diff_backward.seconds)) 

        if ((abs(time_diff_forward.seconds) <= 7200) or (abs(time_diff_backward.seconds) <= 7200)) : 
            curr_salat =  salat_timings_dict[salat] 
            break 
        else:
            curr_salat = 'no-salat' 

    if curr_salat == 'no-salat':
        return "<p style='font-size: 18dp; color: maroon; margin: auto;'>NO SALAT AVAILABLE NOW. SIGN IN ONLY ALLOWED WITHIN AN HOUR OF EACH SALAT<p/>" 

    cur = dbConn.connection.cursor() 

    all_masjid_users = getUsers(cur)

    if name in all_masjid_users:
        user_password = getUserPassword(name, cur)
        if password == user_password: 
            if (curr_salat=='fajr'): 
                tdelta = datetime.strptime(fajr_time, FMT) - datetime.strptime(arrival_time, FMT) 
                if tdelta.days < 0:
                    tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(fajr_time, FMT) 
                    points = int((tdelta.seconds/-60)) 
                    state = "late"
                else:
                    if tdelta.seconds > 600:
                        return "<p style='font-size: 18dp; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % curr_salat.upper()
                    else:
                        state = "on-time"
                        points = 10.0 
            elif (curr_salat=='zuhr'): 
                tdelta = datetime.strptime(zuhr_time, FMT) - datetime.strptime(arrival_time, FMT) 
                if tdelta.days < 0: 
                    tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(zuhr_time, FMT) 
                    points = int((tdelta.seconds/-60)) 
                    state = "late"
                else:
                    if tdelta.seconds > 600:
                        return "<p style='font-size: 18dp; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % curr_salat.upper()
                    else:
                        state = "on-time"
                        points = 10.0
            elif (curr_salat=='asr'): 
                tdelta = datetime.strptime(asr_time, FMT) - datetime.strptime(arrival_time, FMT) 
                if tdelta.days < 0:
                    tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(asr_time, FMT) 
                    points = int((tdelta.seconds/-60))
                    state = "late" 
                else:
                    if tdelta.seconds > 600:
                        return "<p style='font-size: 18dp; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % curr_salat.upper() 
                    else:
                        state = "on-time"
                        points = 10.0 
            elif (curr_salat=='maghrib'): 
                tdelta = datetime.strptime(maghrib_time, FMT) - datetime.strptime(arrival_time, FMT) 
                if tdelta.days < 0:
                    tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(maghrib_time, FMT)  
                    points = int((tdelta.seconds/-60)) 
                    state = "late"
                else:
                    if tdelta.seconds > 600:
                        return "<p style='font-size: 18dp; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % curr_salat.upper() 
                    else:
                        state = "on-time"
                        points = 10.0 
            elif (curr_salat=='isha'): 
                tdelta = datetime.strptime(isha_time, FMT) - datetime.strptime(arrival_time, FMT) 
                if tdelta.days < 0:
                    tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(isha_time, FMT) 
                    points = (tdelta.seconds/-120) 
                    state = "late" 
                else:
                    if tdelta.seconds > 600:
                        return "<p style='font-size: 18dp; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % curr_salat.upper()  
                    else:
                        state = "on-time"
                        points = 10.0
            else:
                return "<p style='font-size: 18dp; color: maroon; margin: auto;'>NO SALAT WITH NAME %s<p/>" % curr_salat.upper() 
        

        else:
            return "<p style='font-size: 18dp; color: maroon; margin: auto;'>WRONG PASSWORD. GO BACK TO HOME PAGE AND RETRY<p/>"

        if points < -15:
            points = -15   

        try:
            cur.execute("INSERT INTO " + name + "(date, time, salat, point, state) VALUES(%s, %s, %s, %s, %s)", (datte, arrival_time, curr_salat, points,state)) 
            dbConn.connection.commit() 
        except (mysql.connector.IntegrityError, mysql.connector.DataError) as err:
            print("DataError or IntegrityError")
            print(err)
            return FAIL
        except mysql.connector.ProgrammingError as err:
            print("Programming Error")
            print(err) 
            return FAIL
        except mysql.connector.Error as err:
            print(err)
            return FAIL 
    else: 
        return render_template("create_user.html") 

    return render_template("welcome.html", curr_salat=curr_salat.upper(), username=username.upper())    

@app.route('/stats', methods=['POST', 'GET'])  
def stats(): 
    cur = dbConn.connection.cursor() 
    all_users = getUsers(cur) 

    all_user_stats_points = pygal.Bar() 
    all_user_stats_states = pygal.Bar() 

    all_user_stats_points.title = "Salat Statistics" 
    all_user_stats_states.title = "No of time each user has arrived late"
    for user in all_users: 
        total = 0
        no_late = 0
        cur.execute("SELECT * FROM " + user) 
        user_stat = cur.fetchall() 

        for row in user_stat:
            total += row[3] 
            if row[4] == "late":
                no_late += 1


        all_user_stats_points.add(user, total) 
        all_user_stats_states.add(user, no_late) 
    
    users_statistics_points = all_user_stats_points.render_data_uri() 
    users_statistics_states = all_user_stats_states.render_data_uri()

    users_statistics = [users_statistics_points, users_statistics_states] 

    return render_template("stats.html", users_statistics=users_statistics) 

@app.route('/get_users', methods=['POST', 'GET'])  
def get_users():  
    cur = dbConn.connection.cursor() 
    all_users = getAllUsers(cur) 
    users_list = [] 

    cnt = 1
    for user in all_users:
        users_list.append({"name": user}) 
        cnt += 1 
        
    all_users_json = jsonify(users_list) 
    return  all_users_json   

@app.route('/users', methods=['POST', 'GET'])  
def users():  
    cur = dbConn.connection.cursor() 
    all_users = getUsers(cur)   

    return render_template("users.html", users=all_users)      



def getUsers(cursor_object):
    try:
        cursor_object.execute("SELECT * FROM masjid_users")
        all_users = cursor_object.fetchall()
    except (mysql.connector.IntegrityError, mysql.connector.DataError) as err:
        print("DataError or IntegrityError")
        print(err)
        return FAIL
    except mysql.connector.ProgrammingError as err:
        print("Programming Error")
        print(err) 
        return FAIL
    except mysql.connector.Error as err:
        print(err)
        return FAIL

    users = []

    for row in all_users:
        users.append(row[0])
    
    return users 

def getAllUsers(cursor_object):
    try:
        cursor_object.execute("SELECT * FROM masjid_users")
        all_users = cursor_object.fetchall()
    except (mysql.connector.IntegrityError, mysql.connector.DataError) as err:
        print("DataError or IntegrityError")
        print(err)
        return FAIL
    except mysql.connector.ProgrammingError as err:
        print("Programming Error")
        print(err) 
        return FAIL
    except mysql.connector.Error as err:
        print(err)
        return FAIL

    users = []
    for row in all_users:
        users.append(row[0]) 
    return users 


def addNewUser(username, password, cursor_object):
    try:
        add_user = """INSERT INTO masjid_users(username, password) VALUES (%s, %s)"""
        cursor_object.execute(add_user, (username, password)) 

        cursor_object.execute("CREATE TABLE " + username + "(date varchar(30), time varchar(30), salat varchar(30), point float, state varchar(30), UNIQUE(date, salat))")  
    except (mysql.connector.IntegrityError, mysql.connector.DataError) as err:
        print("DataError or IntegrityError")
        print(err)
        return FAIL
    except mysql.connector.ProgrammingError as err:
        print("Programming Error")
        print(err) 
        return FAIL
    except mysql.connector.Error as err:
        print(err)
        return FAIL 

def getUserPassword(username, cursor_object):
    try:
        cursor_object.execute("SELECT * FROM masjid_users WHERE username=" + "\"" + username + "\"")  
        user = cursor_object.fetchall() 
    except (mysql.connector.IntegrityError, mysql.connector.DataError) as err:
        print("DataError or IntegrityError")
        print(err)
        return FAIL
    except mysql.connector.ProgrammingError as err:
        print("Programming Error")
        print(err) 
        return FAIL
    except mysql.connector.Error as err:
        print(err)
        return FAIL 

    for row in user:
        password = row[1]
    

    return password
        

if __name__ == '__main__':
    #port = int(os.environ.get('PORT', 80)) 
    app.run(host='192.168.0.101', port=5000, debug=True)  