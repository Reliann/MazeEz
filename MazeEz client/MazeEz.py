import pygame as pygame
import gui
import client
import ctypes
from game import Game
from time import sleep


pygame.init()
pygame.font.init()

user32 = ctypes.windll.user32

LOGO = gui.MenuSprite(135, 60, pygame.image.load(r"resources\coollogo_com-9162951.png"), name="logo")
BACKGROUND = pygame.image.load(r"resources\sprite_northWindShrineBG.png")


WIDTH_SCALE = user32.GetSystemMetrics(0)//1280
HEIGHT_SCALE = user32.GetSystemMetrics(1)//720

CANCEL_BUTTON = gui.Button(text="Leave Queue", x=400, y=400, width=100, height=45, name="cancel")
UNREADY_BUTTON = gui.Button(text="Unready", x=400, y=400, width=100, height=45, name="cancel")

LABELS_FOR_STARTUP_MENU = [LOGO, gui.Button(text="Log In", x=205, y=180, width=100, height=40, name="LogIn"),
                           gui.Button(text="Sign Up", x=205, y=240, width=100, height=40, name="SignUp")]

LABELS_FOR_LOGIN_MENU = [LOGO, gui.Button(text="Back", x=20, y=20, width=50, height=30, name="Back"),
                         gui.Button(text="Log In", x=205, y=340, width=100, height=40, name="MainMenu"),
                         gui.InputBox(x=215, y=210, width=150, height=30, name='username'),
                         gui.InputBox(x=215, y=250, width=150, height=30, name='password', secret='True'),
                         gui.Label(x=145, y=215, width=65, height=20, text="Username:"),
                         gui.Label(x=145, y=255, width=65, height=20, text="Password:")]

LABELS_FOR_SIGNUP_MENU = [LOGO, gui.Button(text="Back", x=20, y=20, width=50, height=30, name='Back'),
                          gui.Button(text="Sign Up", x=205, y=340, width=100, height=40, name='MainMenu'),
                          gui.InputBox(x=215, y=180, width=150, height=30, name='username'),
                          gui.InputBox(x=215, y=220, width=150, height=30, name='email'),
                          gui.InputBox(x=215, y=260, width=150, height=30, name='password', secret='True'),
                          gui.Label(x=137, y=175, width=65, height=30, text="Username:"),
                          gui.Label(x=155, y=215, width=45, height=30, text="Email:"),
                          gui.Label(x=140, y=255, width=65, height=30, text="Password:")]

LABELS_FOR_MAIN_MENU = buttons = [LOGO, gui.Button(text="Play", x=205, y=180, width=115, height=40, name='Play'),
                                  gui.Button(text="Invite Friend", x=205, y=230, width=115, height=40,
                                             name='InviteFriend'),
                                  gui.Button(text="Add Friend", x=205, y=280, width=115, height=40, name='AddFriend'),
                                  gui.Button(text="Log Out", x=20, y=10, width=100, height=40, name="StartUp"),
                                  ]

VICTORY_LABELS = [LOGO, gui.MenuSprite(50, 175, pygame.image.load(r"resources\victoryimage.png")),
                  gui.Button(text="continue", x=400, y=400, width=100, height=40, name="MainMenu")]
DEFEAT_LABELS = [LOGO, gui.MenuSprite(100, 200, pygame.image.load(r"resources\defeatimage.png"))
                 ,gui.Button(text="continue", x=400, y=400, width=100, height=40, name="MainMenu")]
DRAW_LABELS = [LOGO,
               gui.Button(text="continue", x=400, y=400, width=100, height=40, name="MainMenu")]

LABELS_FOR_ADD_MENU = [LOGO, gui.Button(text="Add", x=210, y=260, width=100, height=40, name="MainMenu"),
                       gui.InputBox(x=215, y=180, width=150, height=30, name='FriendName'),
                       gui.Button(text="Back", x=20, y=20, width=50, height=30, name='Back'),
                       gui.Label(x=110, y=180, width=100, height=20, text="friend name:")]

LABELS_FOR_INVITE_MENU = [LOGO, gui.Button(text="Back", x=20, y=20, width=50, height=30, name='Back'),
                          gui.Label(x=110, y=180, width=-1, height=20, text="sadly, you have no friends :(")]


def initialize():
    myclient = client.TcpClient()
    message_box = ctypes.windll.user32.MessageBoxW
    if not myclient.ui_queue.empty():
        error = myclient.ui_queue.get()
        message_box(None, error, 'Error', 0)
        quit()
    screen = pygame.display.set_mode((500, 500))
    logo = pygame.image.load(r"resources\kitty\frame_0.png").convert_alpha()
    logo = pygame.transform.scale(logo, (32, 32))
    pygame.display.set_icon(logo)
    pygame.display.set_caption(r"MazeEz")
    pygame.key.set_repeat(50, 50)  # set repeat for menus.
    myclient.start()
    return screen, myclient, message_box


def main():
    screen, client, message_box = initialize()
    startup_menu = gui.Menu(screen, LABELS_FOR_STARTUP_MENU, BACKGROUND)
    login_menu = gui.Menu(screen, LABELS_FOR_LOGIN_MENU, BACKGROUND)
    #main_menu = gui.Menu(screen, LABELS_FOR_MAIN_MENU, BACKGROUND)
    signup_menu = gui.Menu(screen, LABELS_FOR_SIGNUP_MENU, BACKGROUND)
    add_friend_menu = gui.Menu(screen, LABELS_FOR_ADD_MENU, BACKGROUND)
    invite_friend_menu_false = gui.Menu(screen, LABELS_FOR_INVITE_MENU, BACKGROUND)
    victory_screen = gui.Menu(screen, VICTORY_LABELS, BACKGROUND)
    defeat_screen = gui.Menu(screen, DEFEAT_LABELS, BACKGROUND)
    draw_screen = gui.Menu(screen, DRAW_LABELS, BACKGROUND)

    # loading_images = []
    # for i in range(5):
    #     loading_images.append(pygame.transform.scale
    #                           (pygame.image.load(r"resources\loading\my loading " + str(i) + ".png"), (200, 40)))

    mygame = Game(client)
    m = None
    back = ""
    next_action = "StartUp"
    while next_action != "quit" and client.is_connected:

        if next_action == "LogIn":
            client.logout()
            next_action, required_data = login_menu.run()
            if next_action == "MainMenu":
                if required_data['username'] and required_data['password']:
                    client.login(required_data['username'], required_data['password'])

                    while client.ui_queue.empty():
                        pass
                    typ, data = client.ui_queue.get()
                    try:
                        error_msg = data['error']
                        message_box(None, error_msg, 'Error', 0)
                        next_action = 'LogIn'
                    except KeyError:
                        back = 'LogIn'
                        next_action = 'MainMenu'
                else:
                    message_box(None, 'Please fill in all details, they are necessary.', 'Error', 0)
                    next_action = "LogIn"
            sleep(0.2)
        if next_action == "StartUp":
            client.logout()
            next_action, required_data = startup_menu.run()
            back = "StartUp"
            sleep(0.2)
        if next_action == "Back":
            next_action = back
        if next_action == 'MainMenu':
            main_menu = gui.Menu(screen, LABELS_FOR_MAIN_MENU, BACKGROUND)
            main_menu.addlabel(gui.Label(x=20, y=400, width=120, height=45, text="Username: " + client.user['username']))

            if client.mate:
                m = gui.Label(x=160, y=400, width=120, height=45, text="party: " + client.mate)
                main_menu.addlabel(m)
            next_action, required_data = main_menu.run()
            if m:
                main_menu.removelabel(m)
                m = None
            back = 'MainMenu'
            sleep(0.2)
        if next_action == 'SignUp':
            next_action, required_data = signup_menu.run()

            if next_action == 'MainMenu':
                if required_data['username'] and required_data['password'] and required_data['email']:
                    client.signup(required_data['username'], required_data['password'], required_data['email'])
                    while client.ui_queue.empty():
                        pass
                    typ, data = client.ui_queue.get()
                    try:
                        error_msg = data['error']
                        message_box(None, error_msg, 'Error', 0)
                        next_action = 'SignUp'
                    except KeyError:
                        back = 'LogIn'
                        next_action = 'MainMenu'
                else:
                    message_box(None, 'Please fill in all details, they are necessary.', 'Error', 0)
                    next_action = "SingUp"
            sleep(0.2)
        if next_action == 'Play':
            client.request_game()
            leave, ex = cancel_queue(screen, client)
            if ex:
                next_action = 'quit'
            elif leave:
                client.request_leave_queue()
                next_action = 'MainMenu'
            else:
                next_action = mygame.playgame()
        if next_action == 'AddFriend':
            next_action, required_data = add_friend_menu.run()
            if next_action == 'MainMenu':
                    if required_data['FriendName']:
                        client.add_friend(required_data['FriendName'])
                        while client.ui_queue.empty():
                            pass
                        typ, data = client.ui_queue.get()
                        try:
                            message = data['message']
                            message_box(None, message, 'message from server', 0)
                        except KeyError:
                            message_box(None, "unexpected respond from server", 'Error', 0)

                    else:
                        message_box(None, 'please enter a username to be added', 'Error', 0)
                        next_action = 'AddFriend'
            sleep(0.2)  # prevents useres from ninja clicking
        if next_action == 'victory':
            next_action, required_data = victory_screen.run()
        if next_action == 'defeat':
            next_action, required_data = defeat_screen.run()
        if next_action == 'draw':
            next_action, required_data = draw_screen.run()
        if next_action == 'InviteFriend':
            client.request_friend_list()
            while client.ui_queue.empty():
                pass
            typ, friend_list = client.ui_queue.get()
            if friend_list:
                friends = create_friends_labels(friend_list)
                invite_friend_menu_true = gui.Menu(screen,friends, BACKGROUND)
                next_action, required_data = invite_friend_menu_true.run()
                if next_action[:6] != "Invite" and required_data:
                    for key in required_data:
                        client.reply_friend_request(key, required_data[key])
                        while client.ui_queue.empty():
                            pass
                        typ, data = client.ui_queue.get()

                        try:
                            message = data['message']
                            message_box(None, message, 'message from server', 0)
                        except KeyError:
                            message_box(None, "unexpected respones from server", 'Error', 0)
                    next_action = 'InviteFriend'

                elif next_action[:6] == "Invite":
                    client.invitefriend(next_action[6:])

                    while client.ui_queue.empty():
                        pass
                    typ, data = client.ui_queue.get()

                    if 'error' in data.keys():
                        message_box(None, data['error'], 'Error', 0)
                    elif 'message' in data.keys():
                        message_box(None, data['message'], 'Error', 0)
                    else:
                        message_box(None, "unexpected respones from server", 'Error', 0)

                    next_action = 'MainMenu'
            else:
                next_action, required_data = invite_friend_menu_false.run()
            sleep(0.2)

    if not client.is_connected:
        message_box(None, "The server was shut down", 'Connection Reset', 0)

def create_friends_labels(friend_list):
    labels = [LOGO, gui.Button(text="Back", x=20, y=20, width=50, height=30, name='Back')]
    y = 200
    for key in friend_list:
        l = gui.Label(50, y, height=30, text=key, name=key)
        labels.append(l)
        if friend_list[key]:
            labels.append(gui.Button(l.rect.topright[0], y, 40,30, text="invite", name="Invite" + key))
        else:
            labels.append(gui.BinariButton(l.rect.topright[0], y, 30, 30, name=key))
        y = y + 50

    return labels


def cancel_queue(screen, myclient):
    clock = pygame.time.Clock()

    if myclient.mate:
        ren = pygame.sprite.RenderUpdates(UNREADY_BUTTON)
        leb = UNREADY_BUTTON
    else:
        ren = pygame.sprite.RenderUpdates(CANCEL_BUTTON)
        leb = CANCEL_BUTTON
    while myclient.game_updates.empty():
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return True, True

        ren.update()
        ren.clear(screen, BACKGROUND)
        DirtyRects = ren.draw(screen)
        pygame.display.update(DirtyRects)

        if leb.clicked:
            leb.reset()
            return True, False
        if gui.Menu.refresh:
            gui.Menu.refresh = False
            return True, False
        clock.tick(30)

    return False, False




if __name__ == '__main__':
    main()
