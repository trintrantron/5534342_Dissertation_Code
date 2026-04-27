# 635dff

# <form id="finishButton" action="/confirm_enter_students" method="post">
#     <button type="submit">Finish</button>
# </form>

from flask import Flask, render_template, request, redirect, url_for, session
from db import Task
import logging

from logging.handlers import RotatingFileHandler

app = Flask(__name__)

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
access.add_resource("student_homepage", "t")

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
        session["username"] = user.username
        session["user_id"] = user.user_id
        session["logged_in"] = True
        if user.user_type == "t":
            app.logger.info(f"Successful login attempt: User '{username}' from IP {request.remote_addr}")
            return redirect('/teacher_homepage') 
        app.logger.info(f"Successful login attempt: User '{username}' from IP {request.remote_addr}")
        return redirect('/student_homepage') 
    else:
        app.logger.warning(f"Failed login attempt: User '{username}' from IP {request.remote_addr}")
        session["message"] = attempt[1]
        return redirect("/")

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
    













    
@app.route('/start_game', methods=['GET', 'POST']) # unfinished!!!
def start_game():
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "create_class")):
            username = session["username"]
            return render_template('startGame.html', username=username)
        else:
            return redirect("/")
    else:
        return redirect("/")

@app.route('/student_homepage', methods=['GET', 'POST']) # unfinished!!!
def user_homepage():
    if session.get("logged_in") == True:
        if(access.grant_access(session["username"], "user_homepage")):
            username = session["username"]
            return render_template('userhomepage.html', username=username)
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

if __name__ == '__main__':
    app.run(debug=True, port=8080)
