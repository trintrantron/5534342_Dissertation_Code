# 635dff

# <form id="finishButton" action="/confirm_enter_students" method="post">
#     <button type="submit">Finish</button>
# </form>

from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_socketio import SocketIO, emit, join_room
from db import Task
import logging

from logging.handlers import RotatingFileHandler

app = Flask(__name__)
socketio = SocketIO(app)
rooms = {}
print("ROOMS RESET:", rooms)

###################################################################################################################
# Logger
###################################################################################################################

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = RotatingFileHandler('login.log', maxBytes=1024 * 1024, backupCount=10)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
app.logger.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.propagate = False

terminalLog = logging.getLogger('terminal')
server_handler = logging.StreamHandler()
server_handler.setFormatter(formatter)
server_handler.setLevel(logging.DEBUG) 
terminalLog.addHandler(server_handler)
terminalLog.setLevel(logging.DEBUG)

###################################################################################################################
# Session Key
###################################################################################################################

f = open("session_key", "r")
app.secret_key = f.readline()
f.close()

class Resource:
    def __init__(self, name, role):
        self.name = name
        self.role = role

class RBACSystem:
    def __init__(self):
        self.resources = []

    def add_resource(self, res_name, role):
        resource = Resource(res_name, role)
        self.resources.append(resource)
    
    def grant_access(self, username, resource_name):
        user = Task.user_exists(username)
        if user != 0:
            role = user.user_type
            for reasource in self.resources:
                if reasource.name == resource_name and (reasource.role == role or role == "adm"):
                    return(True)
        return(False)

###################################################################################################################
# Role based access control
###################################################################################################################

access = RBACSystem()
access.add_resource("student_homepage", "s")

access.add_resource("teacher_homepage", "t")
access.add_resource("create_class", "t")
access.add_resource("view_classes", "t")
access.add_resource("start_game", "t")
access.add_resource("build_class", "t")
access.add_resource("enter_names", "t")
access.add_resource("generate_names", "t")
access.add_resource("generate_class_names", "t")
access.add_resource("enter_names_success", "t")
access.add_resource("view_classes", "t")
access.add_resource("start_game", "t")

@app.before_request
def make_session_permanent():
    session.permanent = True

###################################################################################################################
# Pages
###################################################################################################################

@app.route('/', methods=['GET', 'POST'])
def login_page():
    if not("message" in session):
        message = ""
    else:
        message = session["message"]
    if "message" in session:
        session.pop("message")
    session["logged_in"] = False
    return render_template('login.html', message=message)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    attempt = Task.login(username, password)
    if attempt[0] == True:
        user = Task.user_exists(username)
        session["user_id"] = user.user_id
        session["logged_in"] = True
        session["user_type"] = user.user_type
        if user.user_type == "t":
            session["username"] = username
            app.logger.info(f"Successful teacher login attempt: User '{username}' from IP {request.remote_addr}")
            return redirect('/teacher_homepage') 
        session["class_id"] = user.class_id
        session["name"] = user.name
        session["username"] = username
        session["flags"] = ""
        app.logger.info(f"Successful student login attempt: User '{username}' from IP {request.remote_addr}")
        return redirect('/student_homepage') 
    else:
        app.logger.warning(f"Failed login attempt: User '{username}' from IP {request.remote_addr}")
        session["message"] = attempt[1]
        return redirect("/")

###################################################################################################################
# Teacher Pages
###################################################################################################################

@app.route('/signup', methods=['GET', 'POST']) 
def signup():
    if not("message" in session):
        message = ""
    else:
        message = session["message"]
    if "message" in session:
        session.pop("message")
    return render_template('signUp.html', message=message)

@app.route('/signup_confirm', methods=['GET', 'POST']) 
def signup_confirm():
    username = request.form.get('username')
    password = request.form.get('password')
    passwordConf = request.form.get('confirm_password')
    if password == passwordConf:
        add = Task.add_teacher(username, password)
        if add == 0: 
            app.logger.info(f"New user created: '{username}'")
            return redirect('/signup_success')
        if add == 2: 
            session["message"] = "That username is already taken."
            return redirect('/signup')
        session["message"] = add
        return redirect('/signup')
    session["message"] = "The passwords entered do not match."    
    return redirect('/signup')

@app.route('/signup_success', methods=['GET', 'POST'])
def signup_success():
    return render_template('signupSuccess.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    return render_template('forgotPassword.html')

@app.route('/teacher_homepage', methods=['GET', 'POST'])
def admin_homepage():
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "teacher_homepage")):
            username = session["username"]
            return render_template('teacherHomepage.html', username=username)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/create_class', methods=['GET', 'POST'])
def create_class():
    if not("message" in session):
        message = ""
    else:
        message = session["message"]
    if "message" in session:
        session.pop("message")
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "create_class")):
            username = session["username"]
            return render_template('createClass.html', username=username, message=message)
        else:
            return redirect("/")
    else:
        return redirect("/")
    
@app.route('/create_class_confirm', methods=['GET', 'POST'])
def create_class_confirm():
    class_name = request.form.get('class_name')
    username = session["username"]
    attempt = Task.add_class(class_name, username)
    if attempt[0] == True:
        if session.get("logged_in") == True:
            if(access.grant_access(session["username"], "build_class")):
                session["class_id"] = attempt[1]
                return redirect("/build_class")
            else:
                return redirect("/")
        else:
            return redirect("/")
    else:
        session["message"] = attempt[1]
        return redirect("/create_class")

@app.route('/build_class', methods=['GET', 'POST'])
def build_class():
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "build_class")):
            username = session["username"]
            return render_template('buildClass.html', username=username)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/generate_names', methods=['GET', 'POST'])
def generate_names():
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "generate_names")):
            username = session["username"]
            return render_template('generateNames.html', username=username)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/generate_class_names', methods=['GET', 'POST'])
def generate_class_names():
    class_size = request.form.get('class_size')
    username = session["username"]
    class_id = session["class_id"]
    Task.generate_class(class_size, class_id)
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "generate_class_names")):
            return render_template('generateClassNames.html', username=username)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/loading_page', methods=['GET', 'POST'])
def loading_page():
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "generate_names")):
            username = session["username"]
            return render_template('loadingPage.html', username=username)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/enter_names', methods=['GET', 'POST'])
def enter_names():
    if not("message" in session):
        message = ""
    else:
        message = session["message"]
    if "message" in session:
        session.pop("message")
    class_id = session["class_id"]
    class_temp = Task.temp_students(class_id)
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "enter_names")):
            username = session["username"]
            return render_template('enterNames.html', username=username, message=message, class_temp=class_temp)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/manually_add_students', methods=['GET', 'POST'])
def manually_add_students():
    if session.get("logged_in") == True:
        name = request.form.get('name')
        class_id = session["class_id"]
        class_temp = Task.temp_students(class_id)
        attempt = Task.add_named_students(name, class_id, class_temp) 
        if attempt[0] == True:
            return redirect("/enter_names")
        else:
            session["message"] = attempt[1]
            return redirect("/enter_names")
    else:
        return redirect("/")

@app.route('/confirm_enter_students', methods=['GET', 'POST'])
def confirm_enter_students():
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "enter_names_success")):
            username = session["username"]
            return render_template('enterNamesSuccess.html', username=username)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/delete_student', methods=['GET', 'POST'])
def delete_student():
    if session.get("logged_in") == True:
        name = request.form.get('studentName')
        class_id = session["class_id"]
        temp_class = Task.temp_students(class_id)
        attempt = Task.delete_student(name, temp_class) 
        if attempt[0] == True:
            return redirect("/enter_names")
        else:
            session["message"] = attempt[1]
            return redirect("/enter_names")
    else:
        return redirect("/")

@app.route('/view_classes', methods=['GET', 'POST']) # UNFINISHED!!!
def view_classes():    
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "view_classes")):
            username = session["username"]
            class_temp = Task.get_classes(username)
            return render_template('viewClasses.html', username=username, class_temp=class_temp)
        else:
            return redirect("/")
    else:
        return redirect("/")
    
@app.route('/edit_class', methods=['GET', 'POST'])
def edit_class():
    if not("message" in session):
        message = ""
    else:
        message = session["message"]
    if "message" in session:
        session.pop("message")
    class_id = request.form.get('classID')
    session["class_id"] = class_id
    class_temp = Task.temp_students(class_id)
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "enter_names")):
            username = session["username"]
            return render_template('editClass.html', username=username, message=message, class_temp=class_temp, class_id=class_id)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/edit_class_repeat', methods=['GET', 'POST'])
def edit_class_repeat():
    if not("message" in session):
        message = ""
    else:
        message = session["message"]
    if "message" in session:
        session.pop("message")
    class_id = request.form.get('classID')
    class_id = session["class_id"]
    class_temp = Task.temp_students(class_id)
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "enter_names")):
            username = session["username"]
            return render_template('editClass.html', username=username, message=message, class_temp=class_temp, class_id=class_id)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/manually_add_students_1', methods=['GET', 'POST'])
def manually_add_students_1():
    if session.get("logged_in") == True:
        name = request.form.get('name')
        class_id = session["class_id"]
        class_temp = Task.temp_students(class_id)
        attempt = Task.add_named_students(name, class_id, class_temp)
        if attempt[0] == True:
            return redirect("/edit_class_repeat")
        else:
            session["message"] = attempt[1]
            return redirect("/edit_class_repeat")
    else:
        return redirect("/")

@app.route('/confirm_enter_students_1', methods=['GET', 'POST'])
def confirm_enter_students_1():
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "enter_names_success")):
            return redirect("/view_classes")
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/delete_student_edit', methods=['GET', 'POST'])
def delete_student_edit():
    if session.get("logged_in") == True:
        name = request.form.get('studentName')
        class_id = session["class_id"]
        temp_class = Task.temp_students(class_id)
        attempt = Task.delete_student(name, temp_class) 
        if attempt[0] == True:
            return redirect("/edit_class_repeat")
        else:
            session["message"] = attempt[1]
            return redirect("/edit_class_repeat")
    else:
        return redirect("/")

@app.route('/delete_class', methods=['GET', 'POST'])
def delete_class():
    if session.get("logged_in") == True:
        class_id = request.form.get('classID')
        Task.delete_class(class_id) 
        return redirect("/view_classes")
    else:
        return redirect("/")
    
@app.route('/start_game', methods=['GET', 'POST']) # unfinished!!!
def start_game():
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "create_class")):
            username = session["username"]
            class_temp = Task.get_classes(username)
            return render_template('startGame.html', username=username, class_temp=class_temp)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/starting_game', methods=['GET', 'POST']) # THIS NEEDS A LIST OF STUDENTS IN THE ROOM!!! AND NEEDS TO UPDATE PERIODICALLY, AND SHOW NUMBER OF STUDENTS IN ROOM
def starting_game():
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "create_class")):
            username = session["username"]
            print(username)
            class_id = request.form.get('classID')
            session["class_id"] = class_id
            return render_template('startingGame.html', username=username, class_id=class_id)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/leaderboard', methods=['GET', 'POST']) # THIS NEEDS THE CURRENT STUDENTS IN THE ROOM TO BE ORDERED, AND NEEDS TO UPDATE PERIODICALLY 
def leaderboard():
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "create_class")):
            username = session["username"]
            class_id = session["class_id"]
            return render_template('leaderboard.html', username=username, class_id=class_id)
        else:
            return redirect("/")
    else:
        return redirect("/")
    
@app.route('/results', methods=['GET', 'POST']) # THIS NEEDS 
def results():
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "create_class")):
            username = session["username"]
            class_id = session["class_id"]
            leaderboard = []
            students = Task.students_in_class(class_id)
            for student in students:
                leaderboard.append({
                    "name": student.name,
                    "score": student.score
                })
            leaderboard.sort(key=lambda x: x["score"], reverse=True)
            top_3 = leaderboard[:3]
            return render_template('results.html', top_3=top_3, username=username, class_id=class_id)
        else:
            return redirect("/")
    else:
        return redirect("/")

@socketio.on("start_game")
def start_game():
    class_id = session["class_id"]
    socketio.emit("start_game", room=class_id)

@socketio.on("end_game")
def end_game():
    class_id = session["class_id"]
    socketio.emit("game_over", room=class_id)
    rooms[class_id] = []
    socketio.emit("user_list", [], room=class_id)

@app.route("/download_pdf", methods=['GET', 'POST'])
def download_pdf():
    class_id = request.form.get('classID')
    pdf_buffer = Task.make_pdf(class_id)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="cyber_quack_logins.pdf",
        mimetype="application/pdf"
    )




















###################################################################################################################
# Student Pages
###################################################################################################################

@socketio.on("join_class")
def join_class():
    print("SID:", request.sid)
    print("USER AGENT:", request.headers.get("User-Agent"))
    print("REFERER:", request.headers.get("Referer"))
    class_id = session["class_id"]
    user_type = session["user_type"]
    user_id = session["user_id"]
    if user_type == "t":
        name = session["username"]
    else: 
        name = session["name"]

    join_room(class_id)

    if class_id not in rooms:
        rooms[class_id] = []

    if user_type == "s":
        rooms[class_id] = [
            user for user in rooms[class_id]
            if user["name"] != name
        ]

        rooms[class_id].append({
            "sid": request.sid,
            "name": name,
            "user_id": user_id
        })
    
    if user_type == "t":
        leaderboard = []
        students = Task.students_in_class(class_id)
        for student in students:
            leaderboard.append({
                "name": student.name,
                "score": student.score
            })
        socketio.emit("score_change", leaderboard, room=class_id)

    print(name, " joined room: ", rooms[class_id])
    emit("user_list", rooms[class_id], room=class_id)
    

@socketio.on("disconnect")
def disconnect():
    sid = request.sid

    for class_id in list(rooms.keys()):

        rooms[class_id] = [
            user for user in rooms[class_id]
            if user["sid"] != sid
        ]

        emit("user_list", rooms[class_id], room=class_id)

        if len(rooms[class_id]) == 0:
            del rooms[class_id]

@app.route('/student_homepage', methods=['GET', 'POST']) # unfinished!!!
def student_homepage():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            return render_template('studentHomepage.html', username=username, class_id=class_id)
        else:
            return redirect("/")
    else:
        return redirect("/")
    
@app.route('/tutorial', methods=['GET', 'POST']) # unfinished!!!
def tutorial():
    if not("message1" in session):
        message1 = ""
    else:
        message1 = session["message1"]
    if "message1" in session:
        session.pop("message1")
    if session["flags"] == "":
        session["flags"] = [False, False, False, False, False, False]
    print("they are redirected correctly!!")
    print("\n\nLogged in:", session.get("logged_in"))
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            return render_template('tutorial.html', username=username, class_id=class_id, message1=message1)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/challenge_page', methods=['GET', 'POST']) # unfinished!!!
def challenge_page():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            flags = session["flags"]
            return render_template('challengePage.html', username=username, class_id=class_id, score=score, flags=flags)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/tutorial_flag', methods=['GET', 'POST']) # unfinished!!!
def tutorial_flag():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            session["message1"] = "We'll tell you if you're right..."
            return redirect("/tutorial")
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/practice', methods=['GET', 'POST']) # unfinished!!!
def practice():
    if not("message1" in session):
        message1 = ""
    else:
        message1 = session["message1"]
    if "message1" in session:
        session.pop("message1")
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            flags = session["flags"]
            if flags[0] == True:
                return redirect("/completed")
            return render_template('practice.html', message1 = message1, username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/challenge_1', methods=['GET', 'POST']) # unfinished!!!
def challenge_1():
    if not("message" in session):
        message = ""
    else:
        message = session["message"]
    if "message" in session:
        session.pop("message")
    if not("message1" in session):
        message1 = ""
    else:
        message1 = session["message1"]
    if "message1" in session:
        session.pop("message1")
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            flags = session["flags"]
            if flags[1] == True:
                return redirect("/completed")
            return render_template('challenge1.html', message=message, message1=message1, username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/challenge_2', methods=['GET', 'POST']) # unfinished!!!
def challenge_2():
    if not("message1" in session):
        message1 = ""
    else:
        message1 = session["message1"]
    if "message1" in session:
        session.pop("message1")
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            flags = session["flags"]
            if flags[2] == True:
                return redirect("/completed")
            return render_template('challenge2.html', message1 = message1, username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/challenge_3', methods=['GET', 'POST']) # unfinished!!!
def challenge_3():
    if not("message1" in session):
        message1 = ""
    else:
        message1 = session["message1"]
    if "message1" in session:
        session.pop("message1")
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            flags = session["flags"]
            if flags[3] == True:
                return redirect("/completed")
            return render_template('challenge3.html', message1 = message1, username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/challenge_4', methods=['GET', 'POST']) # unfinished!!!
def challenge_4():
    if not("message" in session):
        message = ""
    else:
        message = session["message"]
    if "message" in session:
        session.pop("message")
    if not("message1" in session):
        message1 = ""
    else:
        message1 = session["message1"]
    if "message1" in session:
        session.pop("message1")
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            flags = session["flags"]
            if flags[4] == True:
                return redirect("/completed")
            return render_template('challenge4.html', message=message, message1=message1, username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/challenge_5', methods=['GET', 'POST']) # unfinished!!!
def challenge_5():
    if not("message1" in session):
        message1 = ""
    else:
        message1 = session["message1"]
    if "message1" in session:
        session.pop("message1")
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            flags = session["flags"]
            if flags[5] == True:
                return redirect("/completed")
            return render_template('challenge5.html', message1 = message1, username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/flag_0', methods=['GET', 'POST']) # unfinished!!!
def flag_0():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            flag_input = request.form.get('flag')
            flag = Task.get_flag("practice")
            if flag_input.lower() == flag:
                user_id = session["user_id"]
                user = Task.user_exists(user_id)
                Task.update_score(user, "practice")
                flags = session["flags"]
                flags[0] = True
                session["flags"] = flags
                class_id = session["class_id"]

                leaderboard = []
                students = Task.students_in_class(class_id)
                for student in students:
                    leaderboard.append({
                        "name": student.name,
                        "score": student.score
                    })
                leaderboard.sort(key=lambda x: x["score"], reverse=True)
                socketio.emit("score_change", leaderboard, room=class_id)

                return redirect("/completed")
            else:
                session["message1"] = "Thats not quite right..."
            return redirect("/practice")
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/flag_1', methods=['GET', 'POST']) # unfinished!!!
def flag_1():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            flag_input = request.form.get('flag')
            flag = Task.get_flag("challenge_1")
            if flag_input.lower() == flag:
                user_id = session["user_id"]
                user = Task.user_exists(user_id)
                Task.update_score(user, "challenge_1")
                flags = session["flags"]
                flags[1] = True
                session["flags"] = flags
                class_id = session["class_id"]

                leaderboard = []
                students = Task.students_in_class(class_id)
                for student in students:
                    leaderboard.append({
                        "name": student.name,
                        "score": student.score
                    })
                leaderboard.sort(key=lambda x: x["score"], reverse=True)
                socketio.emit("score_change", leaderboard, room=class_id)

                return redirect("/completed")
            else:
                session["message1"] = "Thats not quite right..."
            return redirect("/challenge_1")
        else:
            return redirect("/")
    else:
        return redirect("/")
    
@app.route('/flag_2', methods=['GET', 'POST']) # unfinished!!!
def flag_2():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            flag_input = request.form.get('flag')
            flag = Task.get_flag("challenge_2")
            if flag_input.lower() == flag:
                user_id = session["user_id"]
                user = Task.user_exists(user_id)
                Task.update_score(user, "challenge_2")
                flags = session["flags"]
                flags[2] = True
                session["flags"] = flags
                class_id = session["class_id"]

                leaderboard = []
                students = Task.students_in_class(class_id)
                for student in students:
                    leaderboard.append({
                        "name": student.name,
                        "score": student.score
                    })
                leaderboard.sort(key=lambda x: x["score"], reverse=True)
                socketio.emit("score_change", leaderboard, room=class_id)

                return redirect("/completed")
            else:
                session["message1"] = "Thats not quite right..."
            return redirect("/challenge_2")
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/flag_3', methods=['GET', 'POST']) # unfinished!!!
def flag_3():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            flag_input = request.form.get('flag')
            flag = Task.get_flag("challenge_3")
            if flag_input.lower() == flag:
                user_id = session["user_id"]
                user = Task.user_exists(user_id)
                Task.update_score(user, "challenge_3")
                flags = session["flags"]
                flags[3] = True
                session["flags"] = flags
                class_id = session["class_id"]

                leaderboard = []
                students = Task.students_in_class(class_id)
                for student in students:
                    leaderboard.append({
                        "name": student.name,
                        "score": student.score
                    })
                leaderboard.sort(key=lambda x: x["score"], reverse=True)
                socketio.emit("score_change", leaderboard, room=class_id)

                return redirect("/completed")
            else:
                session["message1"] = "Thats not quite right..."
            return redirect("/challenge_3")
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/flag_4', methods=['GET', 'POST']) # unfinished!!!
def flag_4():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            flag_input = request.form.get('flag')
            flag = Task.get_flag("challenge_4")
            if flag_input.lower() == flag:
                user_id = session["user_id"]
                user = Task.user_exists(user_id)
                Task.update_score(user, "challenge_4")
                flags = session["flags"]
                flags[4] = True
                session["flags"] = flags
                class_id = session["class_id"]

                leaderboard = []
                students = Task.students_in_class(class_id)
                for student in students:
                    leaderboard.append({
                        "name": student.name,
                        "score": student.score
                    })
                leaderboard.sort(key=lambda x: x["score"], reverse=True)
                socketio.emit("score_change", leaderboard, room=class_id)

                return redirect("/completed")
            else:
                session["message1"] = "Thats not quite right..."
            return redirect("/challenge_4")
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/flag_5', methods=['GET', 'POST']) # unfinished!!!
def flag_5():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            flag_input = request.form.get('flag')
            flag = Task.get_flag("challenge_5")
            if flag_input.lower() == flag:
                user_id = session["user_id"]
                user = Task.user_exists(user_id)
                Task.update_score(user, "challenge_5")
                flags = session["flags"]
                flags[5] = True
                session["flags"] = flags
                class_id = session["class_id"]

                leaderboard = []
                students = Task.students_in_class(class_id)
                for student in students:
                    leaderboard.append({
                        "name": student.name,
                        "score": student.score
                    })
                leaderboard.sort(key=lambda x: x["score"], reverse=True)
                socketio.emit("score_change", leaderboard, room=class_id)

                return redirect("/completed")
            else:
                session["message1"] = "Thats not quite right..."
            return redirect("/challenge_5")
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/login_challenge_1', methods=['GET', 'POST']) # unfinished!!!
def login_challenge_1():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            password = request.form.get('password')
            if password.lower() == "secret":
                session["message"] = "Password correct!"
            else:
                session["message"] = "Password incorrect."
            return redirect("/challenge_1")
        else:
            return redirect("/")
    else:
        return redirect("/")
    
@app.route('/login_challenge_4', methods=['GET', 'POST']) # unfinished!!!
def login_challenge_4():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            password = request.form.get('password')
            if password.lower() == "stella2007":
                session["message"] = "Password correct!"
            else:
                session["message"] = "Password incorrect."
            return redirect("/challenge_4")
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/packet_1', methods=['GET', 'POST']) # unfinished!!!
def packet_1():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('packet1.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/packet_2', methods=['GET', 'POST']) # unfinished!!!
def packet_2():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('packet2.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")
    
@app.route('/packet_3', methods=['GET', 'POST']) # unfinished!!!
def packet_3():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('packet3.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")
    
@app.route('/packet_4', methods=['GET', 'POST']) # unfinished!!!
def packet_4():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('packet4.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")
    
@app.route('/packet_5', methods=['GET', 'POST']) # unfinished!!!
def packet_5():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('packet5.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/packet_6', methods=['GET', 'POST']) # unfinished!!!
def packet_6():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('packet6.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/images', methods=['GET', 'POST']) # unfinished!!!
def images():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('images.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")
    
@app.route('/meetings', methods=['GET', 'POST']) # unfinished!!!
def meetings():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('meetings.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/research', methods=['GET', 'POST']) # unfinished!!!
def research():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('research.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/work', methods=['GET', 'POST']) # unfinished!!!
def work():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('work.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/geese', methods=['GET', 'POST']) # unfinished!!!
def geese():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('geese.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/goose', methods=['GET', 'POST']) # unfinished!!!
def goose():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('goose.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/hat_goose', methods=['GET', 'POST']) # unfinished!!!
def hat_goose():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('hat_goose.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/shoes_goose', methods=['GET', 'POST']) # unfinished!!!
def shoes_goose():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('shoes_goose.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/meeting_1', methods=['GET', 'POST']) # unfinished!!!
def meeting_1():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('meeting_1.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/meeting_2', methods=['GET', 'POST']) # unfinished!!!
def meeting_2():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('meeting_2.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/meeting_3', methods=['GET', 'POST']) # unfinished!!!
def meeting_3():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('meeting_3.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/notes', methods=['GET', 'POST']) # unfinished!!!
def notes():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('notes.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")
    
@app.route('/password', methods=['GET', 'POST']) # unfinished!!!
def password():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('password.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/cyber', methods=['GET', 'POST']) # unfinished!!!
def cyber():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('cyber.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/goose_txt', methods=['GET', 'POST']) # unfinished!!!
def goose_txt():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('goose_txt.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")
    
@app.route('/security', methods=['GET', 'POST']) # unfinished!!!
def security():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('security.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/cyber_quack', methods=['GET', 'POST']) # unfinished!!!
def cyber_quack():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('cyber_quack.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/file_guide', methods=['GET', 'POST']) # unfinished!!!
def file_guide():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('file_guide.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/completed', methods=['GET', 'POST']) # unfinished!!!
def completed():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            user = Task.user_exists(user_id)
            score = user.score
            return render_template('completed.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")












@app.route('/student_results', methods=['GET', 'POST']) # unfinished!!!
def student_results():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "student_homepage")):
            username = session["name"]
            class_id = session["class_id"]
            user_id = session["user_id"]
            student = Task.user_exists(user_id)
            score = student.score
            return render_template('studentResults.html', username=username, class_id=class_id, score=score)
        else:
            return redirect("/")
    else:
        return redirect("/")
















@app.route('/logout', methods=['POST']) 
def logout():
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "logout")):
            session["logged_in"] = False
            return redirect(url_for('login_page'))
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/logout_student', methods=['POST']) 
def logout_student():
    if session.get("logged_in") == True:
        if(access.grant_access(session["user_id"], "logout")):
            session["logged_in"] = False
            return redirect("/")
        else:
            return redirect("/")
    else:
        return redirect("/")

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8080, use_reloader=False, allow_unsafe_werkzeug=True)
