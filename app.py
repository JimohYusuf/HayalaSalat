###################################################################################################################
from flask import Flask, render_template, request, redirect , jsonify 
from flask_mysqldb import MySQL

import datetime  
import yaml 
import mysql.connector 
import os 
import pygal
import json
import MySQLdb      

from datetime import datetime, date, timedelta 

#####################################################################################
#G Constants
SUCCESS = "POST Success"
FAIL    = "POST Failed"
SALAT_INT = 3600
SIGN_IN_INT = 300  

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


###########################################################################################
@app.route('/', methods=['POST', 'GET'])  
def root():
    return redirect("/home", code=302) 


#############################################################################################
@app.route('/home', methods=['POST', 'GET'])  
def home():
    return render_template("home.html") 


##############################################################################################
@app.route('/newuser', methods=['POST', 'GET'])  
def newuser():
    if request.method == 'POST': 
        data            = request.values
        name            = data['name'].upper()
        password        = data['pass'] 

        cur = dbConn.connection.cursor() 

        addNewUser(name, password, cur)
    return render_template("newuser.html") 


###############################################################################################    
@app.route('/create_user', methods=['POST', 'GET'])  
def create_user():
    return render_template("create_user.html") 


################################################################################################
@app.route('/<username>/<upassword>', methods=['POST', 'GET'])  
def signin(username, upassword):  
    name            = username.upper()  
    password        = upassword
    datte           = str(date.today().strftime("%d/%m/%Y")) 
    arrival_time    = str(datetime.now().strftime("%H:%M:%S")) 
    
    cur = dbConn.connection.cursor() 
    ################################################
    FMT             = '%H:%M:%S'

    #################################################

    salat_dict = getSalatTimes(cur) 

    salat_timings = [salat_dict['FAJR'],salat_dict['ZUHR'],salat_dict['ASR'],salat_dict['MAGHRIB'],salat_dict['ISHA']] 

    
    ###################################################
    for salat in salat_timings:
        time_diff_forward = datetime.strptime(arrival_time, FMT) - datetime.strptime(salat, FMT) 
        time_diff_backward = datetime.strptime(salat, FMT) - datetime.strptime(arrival_time, FMT) 

        # print(abs(time_diff_forward.seconds)) 
        # print(abs(time_diff_backward.seconds)) 

        if ((abs(time_diff_forward.seconds) <= SALAT_INT) or (abs(time_diff_backward.seconds) <= SALAT_INT)):   
            for key, value in salat_dict.items():
                if salat == value:
                    curr_salat = key
                    break 
            break 
        else:
            curr_salat = 'no-salat' 
    
    ####################################################

    if curr_salat == 'no-salat':
        return "<h3 style='font-size: 3em; color: maroon; margin: auto;'>NO SALAT AVAILABLE NOW.</h3><br><h3 style='font-size: 1.5em;'> SIGN IN ONLY ALLOWED WITHIN AN HOUR OF EACH SALAT<h3/>" 

    all_masjid_users = getUsers(cur)

    if curr_salat == 'FAJR':
        previous_salat = 'ISHA'
    elif curr_salat == 'ZUHR':
        previous_salat = 'FAJR'
    elif curr_salat == 'ASR':
        previous_salat = 'ZUHR'
    elif curr_salat == 'MAGHRIB':
        previous_salat = 'ASR'
    elif curr_salat == 'ISHA':
        previous_salat = 'MAGHRIB' 

    ######################################################
    if name in all_masjid_users:
        user_password = getUserPassword(name, cur)
        if password == user_password: 
            if (curr_salat=='FAJR'): 
                tdelta = datetime.strptime(salat_dict['FAJR'], FMT) - datetime.strptime(arrival_time, FMT) 
                if tdelta.days < 0:
                    tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(salat_dict['FAJR'], FMT) 
                    points = int((tdelta.seconds/-60)) 
                    state = "late"
                else:
                    if tdelta.seconds > SIGN_IN_INT: 
                        return "<p style='font-size: 3em; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % curr_salat.upper()
                    else:
                        state = "on-time"
                        points = 10.0 
            elif (curr_salat=='ZUHR'): 
                tdelta = datetime.strptime(salat_dict['ZUHR'], FMT) - datetime.strptime(arrival_time, FMT) 
                if tdelta.days < 0: 
                    tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(salat_dict['ZUHR'], FMT) 
                    points = int((tdelta.seconds/-60)) 
                    state = "late"
                else:
                    if tdelta.seconds > SIGN_IN_INT:
                        return "<p style='font-size: 3em; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % curr_salat.upper()
                    else:
                        state = "on-time"
                        points = 10.0
            elif (curr_salat=='ASR'): 
                tdelta = datetime.strptime(salat_dict['ASR'], FMT) - datetime.strptime(arrival_time, FMT) 
                if tdelta.days < 0:
                    tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(salat_dict['ASR'], FMT) 
                    points = int((tdelta.seconds/-60))
                    state = "late" 
                else:
                    if tdelta.seconds > SIGN_IN_INT:
                        return "<p style='font-size: 3em; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % curr_salat.upper() 
                    else:
                        state = "on-time"
                        points = 10.0 
            elif (curr_salat=='MAGHRIB'): 
                tdelta = datetime.strptime(salat_dict['MAGHRIB'], FMT) - datetime.strptime(arrival_time, FMT) 
                if tdelta.days < 0:
                    tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(salat_dict['MAGHRIB'], FMT)  
                    points = int((tdelta.seconds/-60)) 
                    state = "late"
                else:
                    if tdelta.seconds > SIGN_IN_INT:
                        return "<p style='font-size: 3em; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % curr_salat.upper() 
                    else:
                        state = "on-time"
                        points = 10.0 
            elif (curr_salat=='ISHA'): 
                tdelta = datetime.strptime(salat_dict['ISHA'], FMT) - datetime.strptime(arrival_time, FMT) 
                if tdelta.days < 0:
                    tdelta = datetime.strptime(arrival_time, FMT) - datetime.strptime(salat_dict['ISHA'], FMT)   
                    points = (tdelta.seconds/-120) 
                    state = "late" 
                else:
                    if tdelta.seconds > SIGN_IN_INT:
                        return "<p style='font-size: 3em; color: maroon; margin: auto;'>NOT YET TIME TO SIGN IN FOR %s<p/>" % curr_salat.upper()  
                    else:
                        state = "on-time"
                        points = 10.0
            else:
                return "<p style='font-size: 3em; color: maroon; margin: auto;'>NO SALAT WITH NAME %s<p/>" % curr_salat.upper() 

        else:
            return "<p style='font-size: 3em; color: maroon; margin: auto;'>WRONG PASSWORD. GO BACK TO HOME PAGE AND RETRY<p/>"


        ############################################################################## 
        if points < -15:
            points = -15 

        ######################################################
        user_last_salat = getLastSalat(cur, name)  
        print(user_last_salat) 
        print(previous_salat) 
        print(curr_salat)
        if user_last_salat != previous_salat:
            try:
                local_point = -10 
                cur.execute("INSERT INTO " + name + "(date, time, salat, point, state, signer) VALUES(%s, %s, %s, %s, %s, %s)", (datte, arrival_time, previous_salat, local_point, state, name))  
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
            except MySQLdb.Error as err: 
                print(err) 
                return "<p style='font-size: 3em; color: maroon; margin: auto;'>REQUESTED SALAT ENTRY ALREADY EXISTS IN THE DATABASE<p/>"   

        ###############################################################################
        try:
            cur.execute("INSERT INTO " + name + "(date, time, salat, point, state, signer) VALUES(%s, %s, %s, %s, %s, %s)", (datte, arrival_time, curr_salat, points, state, name))  
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
        except MySQLdb.Error as err: 
            print(err) 
            return ("<p style='font-size: 3em; color: maroon; margin: auto;'>YOU HAVE ALREADY SIGNED IN FOR " + curr_salat + " <p/>")    
            
    else: 
        return render_template("create_user.html") 

    return render_template("welcome.html", curr_salat=curr_salat.upper(), username=username.upper())    


####################################################################################################
@app.route('/absentee', methods=['POST', 'GET'])  
def absentee():
    return render_template("absentee.html") 


@app.route('/absent', methods=['POST', 'GET'])  
def absent(): 
    if request.method == 'POST':  
        data            = request.values  
        abs_name        = data['aname'].upper() 
        sig_name        = data['sname'].upper()
        special_case    = data['sp_case']   
        password        = data['pass'] 
        datte           = str(date.today().strftime("%d/%m/%Y")) 
        arrival_time    = str(datetime.now().strftime("%H:%M:%S")) 
    
        cur = dbConn.connection.cursor() 
        ################################################
        FMT             = '%H:%M:%S'

        #################################################

        salat_dict = getSalatTimes(cur) 

        salat_timings = [salat_dict['FAJR'],salat_dict['ZUHR'],salat_dict['ASR'],salat_dict['MAGHRIB'],salat_dict['ISHA']] 

    
        ###################################################
        for salat in salat_timings:
            time_diff_forward = datetime.strptime(arrival_time, FMT) - datetime.strptime(salat, FMT) 
            time_diff_backward = datetime.strptime(salat, FMT) - datetime.strptime(arrival_time, FMT) 

            # print(abs(time_diff_forward.seconds)) 
            # print(abs(time_diff_backward.seconds)) 

            if ((abs(time_diff_forward.seconds) <= SALAT_INT) or (abs(time_diff_backward.seconds) <= SALAT_INT)):    
                for key, value in salat_dict.items():
                    if salat == value:
                        curr_salat = key
                        break 
                break
            else:
                curr_salat = 'no-salat' 
                
        
        ####################################################

        if curr_salat == 'no-salat':
            return "<p style='font-size: 1.5em; color: maroon; margin: auto;'>NO SALAT AVAILABLE NOW. SIGN IN ONLY ALLOWED WITHIN AN HOUR OF EACH SALAT<p/>" 

        all_masjid_users = getUsers(cur)


        ######################################################
        if abs_name in all_masjid_users: 
            if password == "tafadal":
                if special_case == 'lateness': 
                    state = 'late'
                    points = 5 
                elif special_case == 'absence':
                    state = 'absent'
                    points = -2 
            else:
                return "<p style='font-size: 3em; color: maroon; margin: auto;'>WRONG PASSWORD. ONLY ADMIN CAN SIGN IN AN ABSENTEE<p/>"

        ###############################################################################
            try:
                if special_case == 'absence':
                    cur.execute("INSERT INTO " + abs_name + "(date, time, salat, point, state, signer) VALUES(%s, %s, %s, %s, %s, %s)", (datte, arrival_time, curr_salat, points, state, sig_name)) 
                    dbConn.connection.commit()
                elif special_case == 'lateness':
                    former_point = getAUserPoint(cur, abs_name)
                    points = points + former_point
                    cur.execute("DELETE FROM " + abs_name + " ORDER BY date DESC LIMIT 1")  
                    cur.execute("INSERT INTO " + abs_name + "(date, time, salat, point, state, signer) VALUES(%s, %s, %s, %s, %s, %s)", (datte, arrival_time, curr_salat, points, state, sig_name)) 
                    dbConn.connection.commit()
                else:
                    return "<p style='font-size: 3em; color: maroon; margin: auto;'>SOMETHING IS NOT RIGHT. TRY AGAIN<p/>" 
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
            return "NO USER WITH NAME %s" % abs_name 

        return render_template("absent.html", curr_salat=curr_salat.upper(), username=abs_name.upper())


#####################################################################################################
@app.route('/stats', methods=['POST', 'GET'])  
def stats(): 
    cur = dbConn.connection.cursor() 
    all_users = getUsers(cur) 

    all_user_stats_points = pygal.Bar() 
    all_user_stats_late = pygal.Bar()
    all_user_stats_absent = pygal.Bar()  

    all_user_stats_points.title = "SALAT STATISTICS" 
    all_user_stats_late.title = "NO OF TIMES EACH USER HAS ARRIVED LATE"
    all_user_stats_absent.title = "NO OF TIMES EACH USER HAS BEEN ABSENT" 
    for user in all_users: 
        total = 0
        no_late = 0
        no_absent = 0
        cur.execute("SELECT * FROM " + user) 
        user_stat = cur.fetchall() 

        for row in user_stat:
            total += row[3] 
            if row[4] == "late":
                no_late += 1
            elif row[4] == "absent":
                no_absent += 1 


        all_user_stats_points.add(user, total) 
        all_user_stats_late.add(user, no_late)
        all_user_stats_absent.add(user, no_absent) 
    
    users_statistics_points = all_user_stats_points.render_data_uri() 
    users_statistics_late   = all_user_stats_late.render_data_uri()
    users_statistics_absent = all_user_stats_absent.render_data_uri() 

    users_statistics = [users_statistics_points, users_statistics_late, users_statistics_absent] 

    return render_template("stats.html", users_statistics=users_statistics) 

#####################################################################################
@app.route('/curr_salat_status', methods=['POST', 'GET'])  
def curr_salat_status():  
    cur = dbConn.connection.cursor() 
    curr_salat_users_status = seeSignedInUsers(cur) 

    all_users_status = jsonify(curr_salat_users_status)  
    return  all_users_status 

@app.route('/get_curr_status', methods=['POST', 'GET'])  
def get_curr_status():  
    return render_template("curr_salat_users_status.html")   

#####################################################################################
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


#########################################################################################
@app.route('/users', methods=['POST', 'GET'])  
def users():  
    cur = dbConn.connection.cursor() 
    all_users = getUsers(cur)   

    return render_template("users.html", users=all_users) 


#########################################################################################
@app.route('/update_salat_time', methods=['POST', 'GET'])  
def update_salat_time():
    if request.method == 'POST': 
        data            = request.values 
        salat           = data['salat'].upper()
        timme           = data['time']  
          
        cur = dbConn.connection.cursor() 

        updateSalatTime(cur, salat, timme) 
    
    return render_template("update_success.html", salat=salat, time=timme) 


############################################################################################
@app.route('/update_time', methods=['POST', 'GET'])  
def update_time():
    return render_template("update_time.html")  


#########################################################################################
@app.route('/salat_times', methods=['POST', 'GET'])  
def salat_times():
    cur = dbConn.connection.cursor() 
    salat_times_dict = getSalatTimes(cur) 

    fajr = salat_times_dict['FAJR']
    zuhr = salat_times_dict['ZUHR']
    asr = salat_times_dict['ASR']
    maghrib = salat_times_dict['MAGHRIB']
    isha = salat_times_dict['ISHA'] 

    return render_template("salat_times.html", fajr=fajr, zuhr=zuhr, asr=asr, maghrib=maghrib, isha=isha)

##########################################################################################
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
    except MySQLdb.Error as err: 
        print(err) 
        return "<p style='font-size: 3em; color: maroon; margin: auto;'>NO MASJID USER CURRENTLY<p/>"

    users = []

    for row in all_users:
        users.append(row[0]) 
    
    return users 

################################################################################################
def seeSignedInUsers(cursor_object):
    ################################################
    datte           = str(date.today().strftime("%d/%m/%Y")) 
    arrival_time    = str(datetime.now().strftime("%H:%M:%S"))  
    FMT             = '%H:%M:%S'

    #################################################

    salat_dict = getSalatTimes(cursor_object) 

    salat_timings = [salat_dict['FAJR'],salat_dict['ZUHR'],salat_dict['ASR'],salat_dict['MAGHRIB'],salat_dict['ISHA']] 


    ###################################################
    for salat in salat_timings:
        time_diff_forward = datetime.strptime(arrival_time, FMT) - datetime.strptime(salat, FMT) 
        time_diff_backward = datetime.strptime(salat, FMT) - datetime.strptime(arrival_time, FMT) 

        if ((abs(time_diff_forward.seconds) <= SALAT_INT) or (abs(time_diff_backward.seconds) <= SALAT_INT)):   
            for key, value in salat_dict.items():
                if salat == value:
                    curr_salat = key
                    break 
            break 
        else:
            curr_salat = 'no-salat' 
        
        ####################################################

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
    except MySQLdb.Error as err: 
        print(err) 
        return "<p style='font-size: 3em; color: maroon; margin: auto;'>NO MASJID USER CURRENTLY<p/>" 

    users = []
    for row in all_users:
        users.append(row[0]) 

    curr_salat_users_status = []

    for user in users:
        try:
            cursor_object.execute("SELECT * FROM " + user) 
            user_data = cursor_object.fetchall()
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
        except MySQLdb.Error as err: 
            print(err) 
            return "<p style='font-size: 3em; color: maroon; margin: auto;'>NO ENTRY IN REQUESTED USER'S TABLE<p/>"

        signed_in = False 
        if curr_salat == 'no-salat':
            status = "NO SALAT NOW. CHECK BACK LATER" 
            curr_salat_users_status.append({"status": status})
            break 
        else:
            for row in user_data:
                if ((row[0] == datte) and (row[2] == curr_salat)):
                    signed_in = True 
                    if row[4] == "on-time":
                        status = user + " HAS SIGNED IN FOR " + curr_salat + " : CAME ON TIME" 
                        curr_salat_users_status.append({"status": status})  
                    elif row[4] == "late":
                        status = user + " HAS SIGNED IN FOR " + curr_salat + " : CAME LATE" 
                        curr_salat_users_status.append({"status": status})
                    elif row[4] == "absent":
                        status = user + " WAS SIGNED IN FOR ABSENCE/EXCUSED BY " + row[5] 
                        curr_salat_users_status.append({"status": status})
            
            if signed_in == False:
                status = user + " HAS NOT YET SIGNED IN FOR " + curr_salat 
                curr_salat_users_status.append({"status": status})
    
    return curr_salat_users_status 

            
################################################################################################
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
    except MySQLdb.Error as err: 
        print(err) 
        return "<p style='font-size: 3em; color: maroon; margin: auto;'>NO REGISTERED MASJID USER AT THE MOMENT<p/>"

    users = []
    for row in all_users:
        users.append(row[0]) 
    return users 


################################################################################################
def getAUserPoint(cursor_object, name): 
    try:
        cursor_object.execute("SELECT * FROM " + name + " ORDER BY date DESC LIMIT 1")  
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
    except MySQLdb.Error as err: 
        print(err) 
        return "<p style='font-size: 3em; color: maroon; margin: auto;'>USER TABLE IS EMPTY<p/>" 

    for row in all_users:
        point = row[3] 
    return point


################################################################################################
def getLastSalat(cursor_object, name): 
    try:
        cursor_object.execute("SELECT * FROM " + name + " ORDER BY date DESC LIMIT 1")  
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
    except MySQLdb.Error as err: 
        print(err) 
        return "<p style='font-size: 3em; color: maroon; margin: auto;'>USER TABLE IS EMPTY<p/>"

    for row in all_users:
        salat = row[2]
      
    return salat   



#################################################################################################
def addNewUser(username, password, cursor_object):
    try:
        add_user = """INSERT INTO masjid_users(username, password) VALUES (%s, %s)"""
        cursor_object.execute(add_user, (username, password)) 

        cursor_object.execute("CREATE TABLE " + username + "(date varchar(30), time varchar(30), salat varchar(30), point float, state varchar(30), signer varchar(30), UNIQUE(date, salat))")  
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
    except MySQLdb.Error as err: 
        print(err) 
        return "<p style='font-size: 3em; color: maroon; margin: auto;'>USERNAME ALREADY EXIST OR CANNOT REGISTER USER AT THE MOMENT<p/>"

##################################################################################################
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
    except MySQLdb.Error as err: 
        print(err) 
        return "<p style='font-size: 3em; color: maroon; margin: auto;'>USER DOES NOT EXIST<p/>" 

    for row in user:
        password = row[1]
    

    return password

def getSalatTimes(cursor_object):
    try:
        cursor_object.execute("SELECT * FROM salat_times")   
        timings = cursor_object.fetchall() 
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
    except MySQLdb.Error as err: 
        print(err) 
        return "<p style='font-size: 3em; color: maroon; margin: auto;'>SALAT TIMES HAVE NOT BEEN SET YET<p/>"

    times_dict = {}

    for row in timings:
        times_dict[row[0]] = row[1] 
    
    return times_dict 

def updateSalatTime(cursor_object, salat, time): 
    try:
        cursor_object.execute("DELETE FROM salat_times WHERE salat='MAGHRIB'") 
        cursor_object.execute("INSERT INTO salat_times VALUES ('MAGHRIB', '19:24:00')")     
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
    except MySQLdb.Error as err: 
        print(err) 
        return "<p style='font-size: 3em; color: maroon; margin: auto;'>THAT SALAT WAS NOT BROUGHT BY THE PROPHET HENCE DOES NOT EXIST<p/>" 

######################################################################################################
if __name__ == '__main__':
    #port = int(os.environ.get('PORT', 80)) 
    app.run(host='ec2-15-185-71-112.me-south-1.compute.amazonaws.com', port=5000, debug=True)  