from socket import*
from json import dumps, loads
import uuid
from threading import Thread, Lock
from queue import *
import DataBase as db
import select
import Rooms


MAX_CLIENTS = 4

TCP_SERVER_ADDRESS = ('127.0.0.1', 3000)

RESPOND_CONNECTION = "001"
REFUSE_TCP_CONNECTION = "002"
REQUEST_LOGIN = "003"
RESPOND_LOGIN = "004"
REQUEST_SIGUP = "006"
RESPOND_SIGNUP = "005"
GAMEDATA = "020"
REQUEST_GAME = "019"
LOGOUT = "007"
ADD_FRIEND = "008"
RESPOND_ADD_FRIEND = "009"
REQUEST_FRIEND_LIST = "010"
RESPOND_FRIEND_LIST = "011"
INVITE_FRIEND_TO_PARTY = "012"
RESPOND_INVITE_FRIEND_TO_PARTY = "015"
RESPOND_FRIEND_REQUEST = "013"
KICK_FROM_PARTY = '014'
GOT_PARTY_INVITE = '016'
CONSENT_PARTY_INVITE = '022'
JOIN_PARTY = '017'
GOT_KICKED_FROM_PARTY = '018'
REQUEST_LEAVE_QUEUE = '023'
RESPOND_LEAVE_QUEUE = '024'


class TcpServer(Thread):
    def __init__(self, addr, lock, rooms_manager):
        super().__init__()
        self.daemon = True
        self.address = addr
        self.lock = lock
        self.rooms_manager = rooms_manager
        self.is_running = True
        self.server = socket(AF_INET, SOCK_STREAM)
        self.online_clients = {}
        self.online = 0

    def run(self):
        self.server.bind(self.address)
        self.server.setblocking(False)
        self.server.settimeout(5)
        self.server.listen(3)
        inputs = [self.server]
        outputs = []
        data_queues = {}

        while inputs and self.is_running:
            """ 
            handles one request at a cycle, clients are not allowed to send big data (max 99999 bits)
            because the only data they should send is bound to be under that limit.
            """
            readable, writable, exceptional = select.select(
                inputs, outputs, inputs)
            for s in readable:

                if s is self.server:
                    connection, client_address = s.accept()
                    if self.online == MAX_CLIENTS:
                        self.send_refuse(connection, "server is full.")
                    else:
                        self.online += 1
                        connection.setblocking(0)
                        inputs.append(connection)
                        self.online_clients[connection] = ClientHandler(connection, client_address,
                                                                           str(uuid.uuid4()), self.rooms_manager)
                        data_queues[connection] = Queue()
                        print("connected from: " + str(client_address))
                else:
                    try:
                        message_length = s.recv(5)
                    except ConnectionResetError:
                        inputs.remove(s)
                        if s in outputs:
                            outputs.remove(s)
                        s.close()
                        print('disconnected from: ' + str(self.online_clients[s].address))
                        self.online_clients[s].logout()
                        del data_queues[s]
                        del self.online_clients[s]
                        continue
                    try:
                        message_length = int(message_length)
                    except ValueError:
                        data = ""
                    else:
                        data = loads(s.recv(message_length).decode())

                    if data:
                        data_queues[s].put(data)
                        if s not in outputs:
                            outputs.append(s)
                    else:
                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        s.close()
                        print('disconnected from: ' + self.online_clients[s].address)
                        self.online_clients[s].logout()
                        del data_queues[s]
                        del self.online_clients[s]

            for s in writable:
                try:
                    new_data = data_queues[s].get_nowait()
                except Empty:
                    outputs.remove(s)
                else:
                    self.online_clients[s].handle_new_data(new_data)

            for s in exceptional:
                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                s.close()
                self.online_clients[s].logout()
                del data_queues[s]
                del self.online_clients[s]

    def server_shutdown(self):
        self.is_running = False
        # self.online_clients.clear()   # a way around this?

    def send_refuse(self, conn, err):
        m = dumps({'type': REFUSE_TCP_CONNECTION, 'payload': err})
        m_length = str(len(m))
        while len(m_length) < 5:
            m_length = "0" + m_length
        conn.send((m_length + m).encode())
        conn.close()


class ClientHandler(object):
    online_users = []
    def __init__(self, connection, address, identifier, rm):
        self.sock = connection
        self.address = address
        self.identifier = identifier
        self.rooms_manager = rm
        self.send_TCP(RESPOND_CONNECTION,
                      {"identifier": self.identifier})
        self.user = None
        self.room_id = None
        self.mate = None
        self.mate_ready = False
        self.queued = False

    def handle_new_data(self, data):
        """
        handles client's requests
        """

        try:
            typ = data['type']
        except KeyError:
            return

        if typ == REQUEST_LOGIN:
            try:
                self.login_request(data['payload'])
            except KeyError:
                return

        if typ == REQUEST_SIGUP:
            try:
                self.signup_request(data['payload'])
            except KeyError:
                return

        if typ == REQUEST_GAME:
            try:
                self.game_request()
            except KeyError:
                return

        if typ == GAMEDATA:
            try:
                self.rooms_manager.put_event(data['payload'], self.room_id)
            except KeyError:
                return

        if typ == LOGOUT:
            self.logout()
            return

        if typ == ADD_FRIEND:
            try:
                self.add_friend(data['payload'])
            except KeyError:
                return
        if typ == REQUEST_FRIEND_LIST:
            try:
                self.friend_list_request()
            except KeyError:
                return

        if typ == RESPOND_FRIEND_REQUEST:
            try:
                self.respond_friend(data['payload'])
            except KeyError:
                return
        if typ == INVITE_FRIEND_TO_PARTY:
            try:
                self.request_invite(data['payload'])
            except KeyError:
                return
        if typ == CONSENT_PARTY_INVITE:
            self.respond_invite(data['payload'])

        if typ == REQUEST_LEAVE_QUEUE:
            self.leavequeue(requested=True)

    def request_invite(self, data):
        if self.mate:
            self.leaveparty()
        if self.user:
            online = False
            for client in ClientHandler.online_users:
                if client.user and client.user['username'] == data['friend_name']:
                    client.send_invite(self.user['username'])
                    online = True
                    self.send_TCP(RESPOND_INVITE_FRIEND_TO_PARTY, {'message': "friend invite sent"})
            if not online:
                self.send_TCP(RESPOND_INVITE_FRIEND_TO_PARTY, {'error': "friend is not online"})


    def send_invite(self, friend):
        self.send_TCP(GOT_PARTY_INVITE, {'username': friend})

    def respond_invite(self, data):
        for client in ClientHandler.online_users:
            if client.user and client.user['username'] == data['friend_name']:
                if data['consent']:
                    if client.agreejoin(self, True):
                        self.mate = client
                        self.send_TCP(JOIN_PARTY, {'username':client.user['username'],'consent': True})
                else:
                    client.agreejoin(self, False)
                    self.send_TCP(JOIN_PARTY, {'username': client.user['username'], 'consent': False})

    def agreejoin(self, friend, consent):
        if consent:
            self.mate = friend
            self.send_TCP(JOIN_PARTY, {'username':friend.user['username'],'consent': True})
            return True
        else:
            self.send_TCP(JOIN_PARTY, {'username':friend.user['username'], 'consent': False})
            return False

    def respond_friend(self, data):
        if self.user:
            db.set_friend(self.user,data['friend_name'], data['response'])
        if data['response']:
            print("sent")
            self.send_TCP(RESPOND_FRIEND_REQUEST, {'message':data['friend_name'] + " was successfully added to your friend list"})
        else:
            self.send_TCP(RESPOND_FRIEND_REQUEST,
                          {'message': data['friend_name'] + " was declined"})

    def game_request(self):
        if self.user and not self.mate:
            error = self.rooms_manager.queue_player(self)
            if error:
                self.send_TCP(GAMEDATA, {'error': error})
            else:
                self.queued = True
            return

        elif self.user and self.mate:
            if self.mate_ready:
                error = self.rooms_manager.queue_due((self, self.mate))
                if error:
                    self.send_TCP(GAMEDATA, {'error': error})
                    self.mate.send_TCP(GAMEDATA, {'error': error})
                else:
                    self.queued = True
                    self.mate.queued = True
                self.mate_ready = False
            else:
                self.mate.mate_ready = True

    def friend_list_request(self):
        if self.user:
            friend_list = db.get_friends_list(self.user)
            self.send_TCP(RESPOND_FRIEND_LIST, friend_list)
        else:
            self.send_TCP(RESPOND_FRIEND_LIST, {'error': 'you are not authorized'})

    def add_friend(self, friend_name):
        if self.user and self.user['username'] != friend_name:
            data = db.add_friend(self.user, friend_name)
            self.send_TCP(RESPOND_ADD_FRIEND, {'message': data})
        else:
            self.send_TCP(RESPOND_ADD_FRIEND, {'message': "you can't add yourself"})

    def login_request(self, user):

        auth = db.login_user_via_username(user["username"], user["password"])
        if not 'error' in auth.keys():
            if ClientHandler.online_users:
                for client in ClientHandler.online_users:
                    if client.user and client.user['username'] == auth['username']:
                        self.send_TCP(RESPOND_LOGIN, {'error':"This user is logged in somewhere else"})
                        return
            self.user = auth
            ClientHandler.online_users.append(self)
            self.send_TCP(RESPOND_LOGIN, self.user)
        else:
            self.send_TCP(RESPOND_LOGIN, auth)

    def signup_request(self, new_user):
        auth = db.signup_user(new_user["username"], new_user["password"], new_user['email'])
        if 'error' not in auth.keys():
            self.user = auth
            ClientHandler.online_users.append(self)
            self.send_TCP(RESPOND_SIGNUP, self.user)
        else:
            self.send_TCP(RESPOND_SIGNUP, auth)

    def send_gamedata(self, maze):
        self.send_TCP(GAMEDATA, maze)

    def send_TCP(self, t, payload):
        m = {'type': t, 'payload': payload}
        m = dumps(m)
        m_length = str(len(m))
        while len(m_length) < 5:
            m_length = "0" + m_length
        try:
            self.sock.send((m_length + m).encode())
        except OSError:
            pass            # passing. eventually all refrences to a dead socket will be deleted and it will gc.

    def leaveparty(self):
        if self.queued:
            self.leavequeue()
        self.mate.send_TCP(GOT_KICKED_FROM_PARTY, {'error':'party disassembled'})
        self.mate.mate = None
        self.mate = None


    def logout(self):
        if self.queued:
            self.leavequeue()
        if self.user:
            ClientHandler.online_users.remove(self)
            self.user = None
        if self.mate:
            self.leaveparty()
            self.mate = None

    def leavequeue(self, requested=False):
        if self.mate:
            self.mate.mate_ready = False
        if self.queued:
            if self.mate:
                self.mate.queued = False
                self.rooms_manager.remove_from_pair_queue((self, self.mate))
            else:
                self.rooms_manager.remove_from_queue(self)
            self.queued = False
            if requested:
                self.send_TCP(RESPOND_LEAVE_QUEUE,{'message':'you left the queue'})

    def __del__(self):
        self.sock.close()


def main_loop():
    db.initialize_database()
    lock = Lock()
    rm = Rooms.RoomsManager(lock)
    tcp_server = TcpServer(TCP_SERVER_ADDRESS, lock, rm)
    tcp_server.start()

    print("type quit to shutdown server"
          ,"view to see online users")
    while True:
        command = input()
        if command == "quit":
            tcp_server.server_shutdown()
            break
        if command == "view":
            if ClientHandler.online_users:
                for client in ClientHandler.online_users:
                    if client.user:
                        print("user: '"+client.user['username']+"' logged in from: " + client.address[0])

            else:
                print("no online users at the moment")


if __name__ == '__main__':
    main_loop()
