from queue import *
import MazeGenerator
import threading
import uuid


class RoomsManager(object):
    def __init__(self, lock, maxrooms=2, maxplayers=2):
        self.lock = lock
        self.rooms = {}
        self.waiting = Queue()
        self.removed_from_queue = []
        self.maxrooms = maxrooms
        self.maxplayers = maxplayers
        self.waiting_pairs = Queue()
        self.removed_from_pairs_queue = []
        self.waiting_pairs_len = 0
        self.waiting_len = 0

    def put_event(self, event, room_id):    # event: {'player': id, 'action': (key, hit_pos)}
        self.rooms[room_id].players_events.put(event)

    def queue_player(self, player):
        if len(self.rooms) == self.maxrooms:
            return "server full"

        self.waiting.put(player)
        self.waiting_len += 1
        if self.waiting_len + self.waiting_pairs_len >= self.maxplayers:
            self.create_room()

    def queue_due(self, players):        # tuple of client and mate
        if len(self.rooms) == self.maxrooms:
            return "server full"

        self.waiting_pairs.put(players)
        self.waiting_pairs_len += 2
        if self.waiting_len + self.waiting_pairs_len >= self.maxplayers:
            self.create_room()

    def remove_from_pair_queue(self,clients):       # recive a tuple of client and mate
        self.removed_from_pairs_queue.append(clients)
        self.waiting_pairs_len -= 2

    def remove_from_queue(self, client):
        self.removed_from_queue.append(client)
        self.waiting_len -= 1

    def create_room(self):

        new_room_id = str(uuid.uuid4())
        players =[]
        max = self.maxplayers
        if not self.waiting_pairs.empty():
            pair = self.waiting_pairs.get()
            while pair in self.removed_from_pairs_queue:
                self.removed_from_pairs_queue.remove(pair)
                if not self.waiting_pairs.empty():
                    pair = self.waiting_pairs.get()
            if 2 == max:
                max -= 2
                for i in range(2):
                    players.append((pair[i], i%2))
                for player in players:
                    player[0].room_id = new_room_id
                self.rooms[new_room_id] = GameRoom(players, self.lock, self, new_room_id)
                self.rooms[new_room_id].start()
                self.waiting_len = 0
                return
            elif self.waiting_pairs.empty():
                max -= 2
                for client in pair:
                    players.append((client, 0))
            else:
                max -= 2
                for client in pair:
                    players.append((client, 0))
                pair = self.waiting_pairs.get()
                m = True
                while pair in self.removed_from_pairs_queue:
                    self.removed_from_pairs_queue.remove(pair)
                    if not self.waiting_pairs.empty():
                        pair = self.waiting_pairs.get()
                    else:
                        m = False
                        break
                if m:
                    for client in pair:
                        players.append((client, 0))


        i = 0
        while i < max:
            client = self.waiting.get()
            if client in self.removed_from_queue:
                self.removed_from_queue.remove(client)
            else:
                players.append((client, i % 2))
                i += 1

        for player in players:
            player[0].room_id = new_room_id
            player[0].queued = False
        self.rooms[new_room_id] = GameRoom(players, self.lock, self, new_room_id)
        self.rooms[new_room_id].start()
        self.waiting_len = 0

    def close_room(self, id):
        print('room: ' + id + ' closed')
        del self.rooms[id]


class GameRoom(threading.Thread):
    def __init__(self, clients, lock, rm, ide):
        super().__init__()
        self.daemon = True
        self.room_id =ide
        self.rm = rm
        self.lock = lock
        self.players = []
        i = 3
        for client in clients:
            self.players.append(Player(client[0], client[1], i))
            i += 1
        self.players_events = Queue()
        self.game_board = MazeGenerator.Maze(9, 9)
        for player in self.players:
            player.x, player.y = self.game_board.random_location()
            self.game_board.change_value(player.x, player.y, player.num)
        for i in range(3):
            pointx, pointy = self.game_board.random_location()
            self.game_board.change_value(pointx, pointy, 2)
        self.max_points = 10
        self.running = False

    def run(self):
        print('room: "'+self.room_id+ '" started')
        p_list = []
        for player in self.players:
            p_list.append((player.num, player.team, player.client.user['username']))
        for player in self.players:
            player.client.send_gamedata({'model': self.game_board.maze.tolist(), 'player_list':p_list, 'your_num': player.num})
        for player in self.players:
            self.game_board.clear_cell(player.x, player.y)

        self.running = True

        red_players_points = 0
        blue_players_points = 0

        while self.running:
            if not self.players_events.empty():
                event = self.players_events.get()
                try:
                    for player in self.players:
                        player.send_location_update(event['location_update'])
                        if event['location_update'][2] == player.num:

                                player.x, player.y = event['location_update'][0], event['location_update'][1]
                        else:
                            player.send_location_update(event['location_update'])
                except KeyError:
                    pass

                try:

                    while True:
                        available = True
                        pointx, pointy = self.game_board.random_location()
                        for player in self.players:
                            if player.x//50 == pointx and player.y//50 == pointy:
                                available = False
                        if available:
                            break

                    self.game_board.clear_cell(event['point_update'][0] // 50, event['point_update'][1] // 50)
                    self.game_board.change_value(pointx, pointy, 2)

                    for player in self.players:
                        if player.num == event['point_update'][2]:
                            if player.team == 0:
                                blue_players_points += 1
                            else:
                                red_players_points += 1
                        player.send_point_update(event['point_update'][2])
                        player.send_location_update((pointx * 50, pointy * 50, 2))
                except KeyError:
                    pass

                if red_players_points == self.max_points or blue_players_points == self.max_points:
                    winning_team = 0
                    if red_players_points > blue_players_points:
                        winning_team = 1
                    for player in self.players:
                        player.game_results(winning_team)
                        self.running = False

                if red_players_points == self.max_points and blue_players_points == self.max_points:
                    for player in self.players:
                        player.game_results(3)
                        self.running = False

        self.rm.close_room(self.room_id)


class Player(object):

    def __init__(self, player, team, num):
        self.num = num
        self.client = player
        self.points_owned = 0
        self.team = team
        self.x = 0
        self.y = 0

    def send_location_update(self, loc):
        #if loc[2] != self.num:
        self.client.send_gamedata({'location_update': loc})

    def send_point_update(self, num):
        if num == self.num:
            self.points_owned += 1
        self.client.send_gamedata({'add_points': num})

    def game_results(self, team):
        if team == self.team:
            self.client.send_gamedata({'game_result': 'victory'})
        elif team == 3:
            self.client.send_gamedata({'game_result': 'draw'})
        else:
            self.client.send_gamedata({'game_result': 'defeat'})
