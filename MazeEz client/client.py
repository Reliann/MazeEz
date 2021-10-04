from socket import*
from json import dumps, loads
from threading import Thread, Lock
from queue import Queue
import gui
import game

REQUEST_GAME = "019"
SERVER_ADDRESS = ('127.0.0.1', 5030)
REFUSE_TCP_CONNECTION = "002"
RESPOND_CONNECTION = "001"
REQUEST_LOGIN = "003"
RESPOND_LOGIN = "004"
REQUEST_SIGUP = "006"
RESPOND_SIGNUP = "005"
GAMEDATA = '020'
LOGOUT = "007"
ADD_FRIEND = "008"
RESPOND_ADD_FRIEND = "009"
REQUEST_FRIEND_LIST = "010"
RESPOND_FRIEND_LIST = "011"
RESPOND_FRIEND_REQUEST = "013"
INVITE_FRIEND_TO_PARTY = "012"      # i to server
REQUEST_LEAVE_QUEUE = '023'
RESPOND_LEAVE_QUEUE = '024'

RESPOND_INVITE_FRIEND_TO_PARTY = "015" #server to me
KICK_FROM_PARTY = '014'
GOT_PARTY_INVITE = '016'    # server to me (friend)
JOIN_PARTY = '017'    # server to me
GOT_KICKED_FROM_PARTY = '018'
CONSENT_PARTY_INVITE = '022'



class TcpClient(Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True  # close after ur done :)
        self.TCPsock = socket(AF_INET, SOCK_STREAM)
        self.is_connected = True
        self.identifier = None
        self.ui_queue = Queue()
        self.game_updates = Queue()
        try:
            self.TCPsock.connect(SERVER_ADDRESS)
        except ConnectionRefusedError:
            self.ui_queue.put("Can't connect server. check your internet connection or try again later."
                              "\n(server may be offline)")
        self.user = None
        self.mate = ""
        gui.Menu.myclient = self

    def run(self):
        while self.is_connected:

                try:
                    data_length = self.TCPsock.recv(5)
                except ConnectionResetError:
                    self.disconnection()
                    continue

                if not data_length:
                    continue
                try:
                    data_length = int(data_length)
                except ValueError:
                    continue

                data = loads(self.TCPsock.recv(data_length).decode())

                try:
                    typ = data['type']
                except KeyError:
                    continue

                if typ == GAMEDATA:
                    self.game_updates.put(data['payload'])
                    continue

                if typ == RESPOND_CONNECTION:
                    try:
                        self.identifier = data['payload']['identifier']
                        continue

                    except KeyError:
                        continue

                if typ == REFUSE_TCP_CONNECTION:
                    self.TCPsock.close()
                    self.ui_queue.put(data['type'], data['payload'])
                    break

                if typ == RESPOND_LOGIN or typ == RESPOND_SIGNUP:
                    try:    # if there is no error key in 'payload', it's the user.
                        data['payload']['error']
                    except KeyError:
                        self.user = data['payload']

                if typ == GOT_PARTY_INVITE:
                    try:
                        friendname = data['payload']['username']
                        if len(gui.Menu.popups) < 3:
                            gui.Menu.popups.append(friendname)
                            gui.Menu.popupcounter += 1
                            gui.Menu.activate = True

                        continue
                    except KeyError:
                        continue

                if typ == JOIN_PARTY:
                    try:
                        if data['payload']['consent']:
                            self.mate = data['payload']['username']
                            gui.Menu.refresh = True
                        continue
                    except KeyError:
                        continue

                if typ == GOT_KICKED_FROM_PARTY:
                    self.mate = ""
                    gui.Menu.refresh = True
                    continue

                if typ == RESPOND_LEAVE_QUEUE:
                    gui.Menu.refresh = True
                    continue

                self.ui_queue.put((data['type'], data['payload']))

    def login(self, username, password):
        self.send_server(REQUEST_LOGIN, {
                                         'username': username, 'password': password
                                        })

    def signup(self, username, password, email):
        self.send_server(REQUEST_SIGUP,
                         {
                              'username': username,
                              'password': password,
                              'email': email
                         })

    def request_game(self):
        self.send_server(REQUEST_GAME, None)

    def send_server(self, t, payload):
        m = {'type': t, 'payload': payload, 'identifier': self.identifier}
        m = dumps(m)
        m_length = str(len(m))
        while len(m_length) < 5:
            m_length = "0" + m_length
        try:
            self.TCPsock.send((m_length + m).encode())
        except OSError:
            self.ui_queue.put(('error',{'error': 'Oops! something went wrong!'}))
            self.disconnection()

    def disconnection(self):
        self.is_connected = False
        gui.Menu.refresh = True
        game.Game.online = False

    def send_event(self, data):
        self.send_server(GAMEDATA, data)

    def request_leave_queue(self):
        if self.user:
            self.send_server(REQUEST_LEAVE_QUEUE, {})

    def logout(self):
        if self.user:
            self.send_server(LOGOUT, "")
            self.user = None
        self.mate = ""

    def add_friend(self, friend_name):
        if self.user and self.user['username'] != friend_name:
            self.send_server(ADD_FRIEND, friend_name)
        else:
            self.ui_queue.put(("Client Error", {'message': "you can't add yourself"}))

    def request_friend_list(self):
        if self.user:
            self.send_server(REQUEST_FRIEND_LIST, "")
        else:
            self.ui_queue.put(("Client Error", {'message': "no user authorized"}))

    def disconnect(self):   # ToDo: properly close connection
        self.is_connected = False
        # self.TCPsock.close()

    def reply_friend_request(self, friend_name, response):
        if self.user:
            self.send_server(RESPOND_FRIEND_REQUEST,{'friend_name':friend_name,'response':response})

    def invitefriend(self, friend_name):
        if self.user:
            self.mate = ""
            self.send_server(INVITE_FRIEND_TO_PARTY, {'friend_name':friend_name})

    def kick_from_party(self, friend_name):
        if self.user:
            self.send_server(KICK_FROM_PARTY, friend_name)

    def send_invite_consent(self, name, consent):
        self.send_server(CONSENT_PARTY_INVITE, {'friend_name': name, 'consent': consent})