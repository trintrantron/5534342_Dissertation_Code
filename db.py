from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base 
from sqlalchemy.orm.exc import NoResultFound
from itertools import count
import hashlib
import bcrypt
from random import randint
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
import time
import os
from password_generator import PasswordGenerator
from time import sleep
from threading import Thread


f = open("db_key", "r")
key = f.readline()
f.close()

def load_id_count(table):
    f = open("{0}_id_counter".format(table), "r")
    count = int(f.readline())
    f.close()
    return(int(count))

def save_val(table):
            count = load_id_count(table)
            f = open("{0}_id_counter".format(table), "w")
            count += 1
            f.write(str(count))
            f.close()

###################################################################################################################
# Defining tables
###################################################################################################################

Base = declarative_base()
class db:

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Teacher
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class Teachers(Base): 
        def __init__(self, username, password, salt):
            file = open("Users_id_counter", "r")
            id = file.read()
            id = int(id)
            id = id + 1
            self.user_id = str(id)
            file.close()
            file = open("Users_id_counter", "w")
            file.write(str(id))
            file.close()
            self.username = username
            self.password = password.decode("utf-8")
            self.salt = salt
            self.user_type = "t"

        __tablename__ = "Teachers"   

        user_id = Column("User ID", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'), primary_key = True)
        username = Column("Username",StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        password = Column("Password", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        salt = Column("Salt", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        user_type = Column("User Type", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))

        def getId(self):
            return self.user_id

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Student
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class Students(Base): 
        def __init__(self, name, password, salt, class_id):
            file = open("Users_id_counter", "r")
            id = file.read()
            id = int(id)
            id = id + 1
            self.user_id = str(id)
            file.close()
            file = open("Users_id_counter", "w")
            file.write(str(id))
            file.close()
            self.name = name
            self.password = password.decode("utf-8")
            self.salt = salt
            self.class_id = class_id
            self.score = 0
            self.in_game = False
            self.user_type = "s"

        __tablename__ = "Students"   

        user_id = Column("User ID", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'), primary_key = True)
        name = Column("Name",StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        password = Column("Password", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        salt = Column("Salt", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        class_id = Column("Class ID", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        score = Column("Score", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        in_game = Column("In Game", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        user_type = Column("User Type", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Class
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class Classes(Base): 
        id_counter = count(start = load_id_count("Classes"), step = 1)
        def __init__(self, teacher_id, class_name):
            self.class_id = str(next(self.id_counter))
            save_val("Classes")
            self.teacher_id = teacher_id
            self.class_name = class_name
            self.current_game = False
            self.game_started = False

        __tablename__ = "Classes"

        class_id = Column("Class ID", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'), primary_key = True)
        teacher_id = Column("Teacher ID",StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        class_name = Column("Class Name", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        current_game = Column("Current Game", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        game_started = Column("Game Started", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Challenge
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class Challenges(Base): 
        id_counter = count(start = load_id_count("Challenges"), step = 1)
        def __init__(self, name, points):
            self.challenge_id = str(next(self.id_counter))
            save_val("Challenges") 
            self.name = name
            self.points = points

        __tablename__ = "Challenges"   

        challenge_id = Column("Challenge ID", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'), primary_key = True)
        name = Column("Name",StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        points = Column("Points", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Leaderboard
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class Leaderboards(Base): 
        id_counter = count(start = load_id_count("Leaderboards"), step = 1)
        def __init__(self, class_id, ordered_students):
            self.leaderboard_id = str(next(self.id_counter))
            save_val("Leaderboards") 
            self.class_id = class_id
            self.ordered_students = ordered_students

        def order_students():
            print("order students")
        
        __tablename__ = "Leaderboards"   

        leaderboard_id = Column("User Order ID", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'), primary_key = True)
        class_id = Column("Class ID",StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        ordered_students = Column("Ordered students", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Game
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class Games(Base): 
        id_counter = count(start = load_id_count("Games"), step = 1)
        def __init__(self, current_players, class_id):
            self.game_id = str(next(self.id_counter))
            save_val("Games")
            self.current_players = current_players 
            self.class_id = class_id

        
        def start_game():
            print("Start game")

        __tablename__ = "Purchase History"

        game_id = Column("Game ID", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'), primary_key = True)
        current_players = Column("Current Players", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))
        class_id = Column("Class ID", StringEncryptedType(String(100), key, AesEngine, 'pkcs5'))

###################################################################################################################
# Creation
###################################################################################################################

engine = create_engine("sqlite:///cyberquackdb.db", echo = False)
Base.metadata.create_all(bind=engine)
   
Session = sessionmaker(bind=engine)
session = Session()

###################################################################################################################
# Defining Tasks
###################################################################################################################

class Task: 
    
    # Checks if user exists and returns the object if they do
    def user_exists(username):
        try:
            user = session.query(db.Teachers).filter(db.Teachers.username==username).one()
            return(user)
        except NoResultFound as e:
            try:
                user = session.query(db.Students).filter(db.Students.user_id==username).one()
                return(user)
            except NoResultFound as e:
                return(0)
            
    # Checks if class name is available and returns True if it is 
    def class_name_available(teacher_id, class_name):
        classes_temp = session.query(db.Classes).filter(db.Classes.teacher_id==teacher_id).all()
        for i in classes_temp:
            print(i.class_name)
        for i in classes_temp: # Checks if the list contains the proposed class name 
            if i.class_name == class_name:
                print("class name not available")
                return False # returns false if the class name already exists
        print("class is available")
        return True # Returns true if the class name is available 
    
    # Checks user does not already exist and adds them to the system 
    def add_teacher(username, password):
        if Task.user_exists(username) == 0:
            req = Task.check_password(password)
            if req[0] and len(username):
                salt = bcrypt.gensalt()
                bpass = password.encode('utf-8')
                hash = bcrypt.hashpw(bpass, salt)
                teacher = db.Teachers(username, hash, salt)
                session.add(teacher)
                session.commit()
                return(0) # Success
            return(req[1]) # Password doesnt meet requirements
        return(2) # User already exists
    
    def add_class(class_name, username):
        teacher = session.query(db.Teachers).filter(db.Teachers.username==username).one() # Identifies current user
        teacher_id = teacher.getId()
        if Task.class_name_available(teacher_id, class_name) == True:
            new_class = db.Classes(teacher_id, class_name)
            print(teacher_id)
            session.add(new_class)
            print("class exists!!!!")
            session.commit()
            return((True, new_class.class_id)) # Success
        return((False, "You have already created a class with that name")) # Class already exists
    
    def generate_class(class_size, class_id):
        thr = Thread(target=Task.generate_students, args=[class_size, class_id])
        thr.start()

    def generate_students(class_size, class_id):
        file = open("usernames.txt")
        contents = file.read()
        usernames = contents.split(',') 
        class_size = int(class_size)
        for i in range(0, class_size):
            password = Task.generate_password()
            salt = bcrypt.gensalt()
            bpass = password.encode('utf-8')
            hash = bcrypt.hashpw(bpass, salt)
            new_student = db.Students(usernames[i], hash, salt, class_id)
            session.add(new_student)
            session.commit()
            print(new_student.user_id, new_student.name, new_student.class_id, new_student.password, new_student.score, new_student.user_type)

    def generate_password():
        pwo = PasswordGenerator()
        pwo.minlen = 8 
        pwo.maxlen = 8 
        pwo.minuchars = 1 
        pwo.minlchars = 1 
        pwo.minnumbers = 1 
        pwo.minschars = 1 

        password = pwo.generate()
        print(password)
        return password

    def temp_students(class_id):
        temp_students = session.query(db.Students).filter(db.Students.class_id==class_id).all()
        return temp_students

    # def add_named_students(name, class_id, temp_class):
    #     thr = Thread(target=Task.add_named_students_thread, args=[name, class_id, temp_class])
    #     thr.start()

    def add_named_students(name, class_id, temp_class):
        for student in temp_class:
            if student.name == name:
                return((False, "You have already added a student with that name"))
        password = Task.generate_password()
        salt = bcrypt.gensalt()
        bpass = password.encode('utf-8')
        hash = bcrypt.hashpw(bpass, salt)
        new_student = db.Students(name, hash, salt, class_id)
        session.add(new_student)
        session.commit()
        print(new_student.user_id, new_student.name, new_student.class_id, new_student.password, new_student.score, new_student.user_type)
        return ((True, "woo"))
    
    def delete_student(name, temp_class):
        for student in temp_class:
            if student.name == name:
                session.delete(student)
                session.commit()
                return ((True), "yip")
        return((False), "An error occured.")
 
    def get_classes(username):
        teacher = session.query(db.Teachers).filter(db.Teachers.username==username).one()
        teacher_id = teacher.user_id
        temp_classes = session.query(db.Classes).filter(db.Classes.teacher_id==teacher_id).all()
        classes = session.query(db.Classes).all()
        for classq in classes:
            print(classq.class_name, classq.teacher_id)
        print(teacher_id)
        print("this runs wooooo")
        print(temp_classes)
        return temp_classes
    
    def delete_class(class_id):
        this_class = session.query(db.Classes).filter(db.Classes.class_id==class_id).one()
        session.delete(this_class)
        session.commit()


















    # Checks user does not already exist and adds them to the system 
    def add_student(username, password, class_id):
        if Task.user_exists(username) == 0:
            req = Task.check_password(password)
            if req[0] and len(username):
                salt = bcrypt.gensalt()
                bpass = password.encode('utf-8')
                hash = bcrypt.hashpw(bpass, salt)
                score = 0
                student = db.Students(username, hash, salt, class_id, score)
                session.add(student)
                session.commit()
                return(0) # Success
            return(req[1]) # Password doesnt meet requirements
        return(2) # User already exists

    # Checks that user exists and password is correct
    def login(username, password):
        user = Task.user_exists(username)
        if user != 0:
            bpass = password.encode('utf-8')
            result = bcrypt.checkpw(bpass, user.password.encode("utf-8"))
            if result:
                return((True, username))
        return((False, "Incorrect username or password"))

    # Retuns true if the password given meets the security requirements 
    def check_password(password): 
        if  len(password) < 8 or len(password) > 71: return (False, "Password does not meet the length requirements")
        if  not any(letter.isupper() for letter in password): return (False, "Password must contain a captial letter")
        if  not any(letter.islower() for letter in password): return (False, "Password must contain a lower case letter")
        if  not any(digit.isdigit() for digit in password): return (False, "Password must contain a number")
        special_char = "*%!@()[]$£?~#=+-/|"
        if not any(special in special_char for special in password): return (False, f"Password must contain a special character: {special_char}")
        return (True, "Valid Password")


