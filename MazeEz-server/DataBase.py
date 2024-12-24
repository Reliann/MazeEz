import sqlite3
import uuid

def initialize_database():
    conn = sqlite3.connect('mazeez.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    email TEXT,
                    password TEXT,
                    user_id TEXT,
                    verified BOOLEAN,
                    wins INTEGER,
                    friends_list TEXT
                )''')
    conn.commit()
    conn.close()

def signup_user(username, password, email):
    conn = sqlite3.connect('mazeez.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users WHERE username = ?', (username,))
    if c.fetchone():
        conn.close()
        return {'error': 'name taken'}
    user_id = str(uuid.uuid4())
    c.execute('INSERT INTO users (username, email, password, user_id, verified, wins, friends_list) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (username, email, password, user_id, False, 0, ''))
    conn.commit()
    conn.close()
    return {'username': username, 'user_id': user_id, 'verified': False, 'wins': 0, 'friends_list': False}

def add_friend(user, friend):
    conn = sqlite3.connect('mazeez.db')
    c = conn.cursor()
    c.execute('SELECT username FROM users WHERE username = ?', (friend,))
    if not c.fetchone():
        conn.close()
        return "The name does not exist"
    c.execute('SELECT friends_list FROM users WHERE username = ?', (friend,))
    friends_list = c.fetchone()[0]
    if user['username'] in friends_list.split(','):
        conn.close()
        return "you are friends already!"
    new_friends_list = friends_list + ',' + user['username'] if friends_list else user['username']
    c.execute('UPDATE users SET friends_list = ? WHERE username = ?', (new_friends_list, friend))
    conn.commit()
    conn.close()
    return "Friend request sent"

def set_friend(user, new_friend, status):
    conn = sqlite3.connect('mazeez.db')
    c = conn.cursor()
    if status:
        c.execute('SELECT friends_list FROM users WHERE username = ?', (new_friend,))
        friends_list = c.fetchone()[0]
        new_friends_list = friends_list + ',' + user['username'] if friends_list else user['username']
        c.execute('UPDATE users SET friends_list = ? WHERE username = ?', (new_friends_list, new_friend))
        c.execute('SELECT friends_list FROM users WHERE username = ?', (user['username'],))
        friends_list = c.fetchone()[0]
        new_friends_list = friends_list + ',' + new_friend if friends_list else new_friend
        c.execute('UPDATE users SET friends_list = ? WHERE username = ?', (new_friends_list, user['username']))
    else:
        c.execute('SELECT friends_list FROM users WHERE username = ?', (user['username'],))
        friends_list = c.fetchone()[0]
        friends_list = friends_list.split(',') if friends_list else []
        friends_list.remove(new_friend)
        c.execute('UPDATE users SET friends_list = ? WHERE username = ?', (','.join(friends_list), user['username']))
    conn.commit()
    conn.close()

def get_friends_list(user):
    conn = sqlite3.connect('mazeez.db')
    c = conn.cursor()
    c.execute('SELECT friends_list FROM users WHERE username = ?', (user['username'],))
    friends_list = c.fetchone()[0]
    conn.close()
    return [{'username': friend} for friend in friends_list.split(',')] if friends_list else []

def login_user_via_username(username, password):
    conn = sqlite3.connect('mazeez.db')
    c = conn.cursor()
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    if result and result[0] == password:
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        user_dict = {
            'username': user[0],
            'user_id': user[3],
            'verified': user[4],
            'wins': user[5],
            'friends_list': user[6].split(',') if user[6] else []
        }
        conn.close()
        return user_dict
    else:
        conn.close()
        return {'error': 'Wrong username or password'}