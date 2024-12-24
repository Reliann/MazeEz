# original firebaseDB code from 2019-2018
# UNUSED CODE by the current version of the server.
# To use: replace the current firebaseDb.py with this code.
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import uuid


# server identifies users with 'username' key in the dictionary, database does not.
def signup_user(username, password, email):
    if db.reference().child('users/' + username + "/user_id").get(shallow=True):
        return {'error': 'name taken'}
    user = {
        #'online': True,
        'email': email,
        'password': password,
        'user_id': str(uuid.uuid4()),
        'verified': False,
        'wins': 0,
        'friends_list': False
        # 'friends_list': None  ,  should be list of users ID true= friends false = pending
    }
    db.reference().child('users/' + username).set(user)
    user.update({'username': username})
    user.pop('password', None)
    user.pop('email', None)
    return user


# def logout(username):
#     db.reference().child('users/' + username + '/online').set(False)


def add_friend(user, friend):
    if db.reference().child('users/' + friend).get():
        if db.reference().child('users/' + friend + '/friends_list/' + user['username']).get(shallow=True):
            return "you are friends already!"
        db.reference().child('users/' + friend + '/friends_list/' + user['username']).set(False)
        return "Friend request sent"
    else:
        return "The name does not exist"


def set_friend(user, new_friend, status):       # TODO: IF FRIEND SENT REQUEST ADD INSTEAD OF SETTING
    if status:
        db.reference().child('users/' + new_friend + '/friends_list/' + user['username']).set(status)
        db.reference().child('users/' + user['username'] + '/friends_list/' + new_friend).set(status)
    else:
        db.reference('users/' + user['username'] + '/friends_list/' + new_friend).delete()


def get_friends_list(user):
    return db.reference().child('users/' + user['username'] + '/friends_list').get()


def login_user_via_username(username, password):
    if db.reference().child('users/' + username + '/password').get() == password:
        user = db.reference().child('users/' + username).get()
        user.update({'username': username})
        del user['password']
        del user['email']
        # db.reference().child('users/' + username + '/online').set(True)
        return user
    else:
        return {'error': 'Wrong username or password'}


# def get_requests(user):
#     requsets = db.reference().child('users/' + user['username'] + '/friends_list/' ).get(False)
#     requsets += db.reference().child('users/' + user['username'] + '/invites/' ).get(False)
#     return requsets
#
#
# def send_invite(user, friend):
#     db.reference().child('users/' +friend + '/invites/' + user).get(False)


def initialize_database():
    cred = credentials.Certificate(r"mykey.json")
    firebase_admin.initialize_app(cred, {'databaseURL': "https://mazeez-2903a.firebaseio.com"})

    # db.reference().delete()