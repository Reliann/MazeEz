import pygame


class MenuSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, img, name="default"):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False
        self.name = name

    def reset(self):
        self.clicked = False


class RawText(MenuSprite):
    def __init__(self, x, y, text="", name="default", size=50):
        self.text = text
        self.size = size
        self.textsurf = pygame.font.SysFont('Ariel', self.size)
        self.image = self.textsurf.render(self.text, False, (0, 0, 0))
        super().__init__(x, y, self.image, name)

    def update(self, *args):
        self.textsurf = pygame.font.SysFont('Ariel', self.size)
        self.image = self.textsurf.render(self.text, False, (0, 0, 0))


class Label(MenuSprite):
    def __init__(self, x, y, width=-1, height=10, text="", color=(173, 204, 255), name="default"):
        self.textsurf = pygame.font.SysFont('Ariel', 20)
        if width == -1:     # default width is text size
            width = self.textsurf.size(text)[0] + 4
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.color = color
        self.text = text
        self.image.blit(self.textsurf.render(self.text, False, (0, 0, 0)), (0, 0))     # change this to center text
        super().__init__(x, y, self.image, name)

    def update(self, *args):
        self.image.fill(self.color)
        self.textsurf = pygame.font.SysFont('Ariel', 20)
        self.image.blit(self.textsurf.render(self.text, False, (0, 0, 0)), (0, 0))  # change this to center text


class Button(Label):
    def __init__(self, x, y, width, height, text="", color=(173, 204, 255), name="default"):
        super().__init__(x, y, width, height, text, color, name)
        self.on_color = (255, 163, 228)
        self.og_color = self.color

    def update(self, *args):
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos):
            self.color = self.on_color
            mouse_buttons = pygame.mouse.get_pressed()
            self.clicked = mouse_buttons[0]
        else:
            self.color = self.og_color
        super().update()

    def reset(self):
        super().reset()
        self.color = self.og_color


class InputBox(Button):
    def __init__(self, x, y, width, height, text="", color=(173, 204, 255), name="default", secret=False):
        super().__init__(x, y, width, height, text, color, name)
        self.selected = False
        self.hidden_text = ""
        self.secret = secret
        self.actualtext = ""

    def update(self, events):
        pos = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()
        self.clicked = mouse_buttons[0]

        if self.rect.collidepoint(pos):
            self.color = self.on_color
            mouse_buttons = pygame.mouse.get_pressed()
            self.clicked = mouse_buttons[0]
            if self.clicked:
                self.selected = True
        elif self.clicked:
            self.selected = False
            self.color = self.og_color
        else:
            if self.selected:
                self.color = self.on_color
            else:
                self.color = self.og_color

        if self.selected:
            for event in events[:1]:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        self.text = self.text[:-1]
                        if self.secret:
                            self.actualtext = self.actualtext[:-1]
                        if self.textsurf.size(self.text)[0] < self.rect.width:
                            self.text = self.hidden_text[-1:] + self.text
                            self.hidden_text = self.hidden_text[:-1]
                    else:
                        if self.secret:
                            self.text += "*"
                            self.actualtext += event.unicode
                        else:
                            self.text += event.unicode
                        if self.textsurf.size(self.text)[0] > self.rect.width:
                            self.hidden_text = self.hidden_text + self.text[0]
                            self.text = self.text[1:]

        self.clicked = False
        Label.update(self)

    def get_text(self):
        if self.secret:
            return self.actualtext
        return self.hidden_text + self.text


class BinariButton(MenuSprite):
    def __init__(self, x, y, width, height, name):
        self.red_color = (252, 70, 76)
        self.green_color = (182, 252, 121)
        img = pygame.Surface((width, height))
        img.fill(self.green_color)
        img.fill(self.red_color, pygame.Rect((x+width//2, y), (width//2, height)))
        self.true_img = pygame.transform.scale(pygame.image.load(r"resources\green_v.png"), (width//2, height)).convert()
        self.false_img = pygame.transform.scale(pygame.image.load(r"resources\red_x.png"), (width//2, height)).convert()
        img.blit(self.false_img, (1, 1))
        img.blit(self.true_img, (1+width//2, 1))
        self.status = None
        super().__init__(x, y, img, name)

    def update(self, *args):
        mouse_buttons = pygame.mouse.get_pressed()
        pos = pygame.mouse.get_pos()
        spot = self.rect.collidepoint(pos)
        if mouse_buttons[0] and spot and pos[0] <= self.rect.center[0]:
            self.image.fill(self.red_color)
            self.image.blit(self.false_img, (1, 1))
            self.status = False
            self.clicked = True

        elif mouse_buttons[0] and spot and pos[0] > self.rect.center[0]:
            self.image.fill(self.green_color)
            self.image.blit(self.true_img, (1, 1))
            self.status = True
            self.clicked = True

    def get_status(self):
        return self.status


class Menu(object):
    activate = False
    popupcounter = 0
    popups = []
    myclient = None
    refresh = False

    def __init__(self, screen, sprites, background):
        try:
            iter(sprites)
            self.labels = sprites
        except TypeError:
            self.labels = [sprites]

        self.background = background
        self.screen = screen
        self.popuplabels = []
        self.fps_clock = pygame.time.Clock()

    def addlabel(self, label):
        self.labels.append(label)

    def removelabel(self, label):
        self.labels.remove(label)

    def run(self):
        renderlabels = pygame.sprite.RenderUpdates(self.labels)

        for Label in self.labels:
            Label.reset()
        self.screen.blit(self.background, (0, 0))
        renderlabels.draw(self.screen)
        pygame.display.flip()

        nextdo = None

        if Menu.activate:

            for i in range(len(Menu.popups)):
                img = pygame.Surface((110, 60))
                img.fill((216, 138, 226))
                x = 390
                y = Menu.popupcounter * 30 + 1

                popuplabels = [MenuSprite(x, y, img), BinariButton(x+15, y+30, 40, 30, 'popup' + Menu.popups[i]),
                               RawText(x, y, Menu.popups[i], size=25)]
                self.popuplabels.append((Menu.popups[i], popuplabels))
                renderlabels.add(popuplabels)
                Menu.activate = False

        m = None
        while not nextdo:
            if Menu.refresh:
                Menu.refresh = False
                nextdo = 'MainMenu'
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    nextdo = "quit"
            renderlabels.update(events)
            for label in renderlabels:
                if label.clicked:
                    if type(label) is BinariButton and label.name[:5] == 'popup':

                        Menu.myclient.send_invite_consent(label.name[5:], label.status)

                        for i in self.popuplabels:
                            if i[0] == label.name[5:]:
                                m = i
                        self.popuplabels.remove(m)
                        m = m[1]
                        Menu.popups.remove(label.name[5:])
                        Menu.popupcounter -= 1

                        if label.status:
                            nextdo = 'MainMenu'

                    else:
                        nextdo = label.name
            if m:
                for sprite in m:
                    renderlabels.remove(sprite)

                m = None


            renderlabels.clear(self.screen, self.background)
            DirtyRects = renderlabels.draw(self.screen)
            pygame.display.update(DirtyRects)

            if Menu.activate:
                img = pygame.Surface((110, 60))
                img.fill((216, 138, 226))
                x = 390
                y = Menu.popupcounter * 30 + 1

                popuplabels = [MenuSprite(x, y, img), BinariButton(x + 15, y + 30, 40, 30, 'popup' + Menu.popups[Menu.popupcounter-1]),
                               RawText(x+2, y, Menu.popups[Menu.popupcounter-1], size=25)]
                self.popuplabels.append((Menu.popups[Menu.popupcounter-1], popuplabels))
                renderlabels.add(popuplabels)
                Menu.activate = False

            self.fps_clock.tick(30)

        returned_input = {}

        for sprite in self.labels:
            if type(sprite) is InputBox:
                returned_input.update({sprite.name: sprite.get_text()})
            if type(sprite) is BinariButton:
                if sprite.get_status() is not None:
                    returned_input.update({sprite.name: sprite.get_status()})

        if Menu.popupcounter != 0:
            Menu.activate = True

        if returned_input:
            return nextdo, returned_input
        else:
            return nextdo, None

    def run_nonauto(self):
        pass

