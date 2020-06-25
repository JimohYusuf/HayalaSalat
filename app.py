from flask import Flask, render_template, request, redirect 
from flask_mysqldb import MySQL

import datetime  
import yaml 
import mysql.connector 
import os 
import pygal    

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
    #return redirect("/home", code=302)  


@app.route('/signin', methods=['POST', 'GET'])  
def signin(): 
    if request.method == 'POST': 
        data            = request.values
        name            = data['name'] 
        password        = data['pass'] 
        salat           = data['salat'] 
        datte           = str(date.today().strftime("%d/%m/%Y")) 
        arrival_time    = str(datetime.now().strftime("%H:%M:%S")) 
        
        fajr_time       = '04:31:00'
        zuhr_time       = '12:51:00'
        asr_time        = '16:11:00'
        maghrib_time    = '19:23:00'   
        isha_time       = '21:01:00' 
        FMT             = '%H:%M:%S'

        cur = dbConn.connection.cursor() 

        all_masjid_users = getUsers(cur)

        if name in all_masjid_users:
            user_password = getUserPassword(name, cur)
            if password == user_password: 
                if (salat=='fajr'): 
                    tdelta = datetime.strptime(fajr_time, FMT) - datetime.strptime(arrival_time, FMT) 
                    if tdelta.days < 0:
                        tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(fajr_time, FMT) 
                        points = int((tdelta.seconds/-60)) 
                    else:
                        if tdelta.seconds > 600:
                            return "<p style='font-size: 18dp; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % salat.upper()
                        else:
                            points = 10.0 
                elif (salat=='zuhr'): 
                    tdelta = datetime.strptime(zuhr_time, FMT) - datetime.strptime(arrival_time, FMT) 
                    if tdelta.days < 0: 
                        tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(zuhr_time, FMT) 
                        points = int((tdelta.seconds/-60)) 
                    else:
                        if tdelta.seconds > 600:
                            return "<p style='font-size: 18dp; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % salat.upper()
                        else:
                            points = 10.0
                elif (salat=='asr'): 
                    tdelta = datetime.strptime(asr_time, FMT) - datetime.strptime(arrival_time, FMT) 
                    if tdelta.days < 0:
                        tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(asr_time, FMT) 
                        points = int((tdelta.seconds/-60)) 
                    else:
                        if tdelta.seconds > 600:
                            return "<p style='font-size: 18dp; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % salat.upper() 
                        else:
                            points = 10.0 
                elif (salat=='maghrib'): 
                    tdelta = datetime.strptime(maghrib_time, FMT) - datetime.strptime(arrival_time, FMT) 
                    if tdelta.days < 0:
                        tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(maghrib_time, FMT)  
                        points = int((tdelta.seconds/-60)) 
                    else:
                        if tdelta.seconds > 600:
                            return "<p style='font-size: 18dp; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % salat.upper() 
                        else:
                            points = 10.0 
                elif (salat=='isha'): 
                    tdelta = datetime.strptime(isha_time, FMT) - datetime.strptime(arrival_time, FMT) 
                    if tdelta.days < 0:
                        tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(isha_time, FMT) 
                        points = int((tdelta.seconds/-60)) 
                    else:
                        if tdelta.seconds > 600:
                            return "<p style='font-size: 18dp; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % salat.upper()  
                        else:
                            points = 10.0
                else:
                    return "<p style='font-size: 18dp; color: maroon; margin: auto;'>NO SALAT WITH NAME %s<p/>" % salat.upper() 
            

            else:
                return "<p style='font-size: 18dp; color: maroon; margin: auto;'>WRONG PASSWORD. GO BACK TO HOME PAGE AND RETRY<p/>"

            if points < -30:
                points = -30 

            try:
                cur.execute("INSERT INTO " + name + "(date, time, salat, point) VALUES(%s, %s, %s, %s)", (datte, arrival_time, salat, points)) 
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

    return render_template("welcome.html") 

@app.route('/stats', methods=['POST', 'GET'])  
def stats(): 
    cur = dbConn.connection.cursor() 
    all_users = getUsers(cur) 

    all_user_stats = pygal.Bar() 

    all_user_stats.title = "Salat Statisitics"
    for user in all_users: 
        total = 0
        cur.execute("SELECT * FROM " + user) 
        user_stat = cur.fetchall() 

        for row in user_stat:
            total += row[3] 

        all_user_stats.add(user, total) 
    
    users_statistics = all_user_stats.render_data_uri() 

    return render_template("stats.html", users_statistics=users_statistics) 
        
      

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

def addNewUser(username, password, cursor_object):
    try:
        add_user = """INSERT INTO masjid_users(username, password) VALUES (%s, %s)"""
        cursor_object.execute(add_user, (username, password)) 

        cursor_object.execute("CREATE TABLE " + username + "(date varchar(30), time varchar(30), salat varchar(30), point float, UNIQUE(date, salat))")  
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)  