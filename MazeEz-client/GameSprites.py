import pygame
import gui
from os import path
SCALE = (40, 34)

WALL_HEIGHT = 50
WALL_WIDTH = 50
SPEED = 6


class MovingSprite(pygame.sprite.Sprite):
    def __init__(self, x=0, y=0, game_fps=30, num=0, nametag=None):
        pygame.sprite.Sprite.__init__(self)
        self.num = num
        self.nametag = nametag
        self.animation_fps = 6
        self.next_frame = game_fps/self.animation_fps
        self.current_frame = 0
        self.current_call = 0
        self.statechanged = False
        self.frames_dict = {'walk':     # TODO: blit name surface on images
            [
                pygame.transform.scale(pygame.image.load(path.join("resources", "kitty", "frame_0.png")), SCALE).convert(),
                pygame.transform.scale(pygame.image.load(path.join("resources", "kitty", "frame_1.png")), SCALE).convert(),
                pygame.transform.scale(pygame.image.load(path.join("resources", "kitty", "frame_2.png")), SCALE).convert(),
                pygame.transform.scale(pygame.image.load(path.join("resources", "kitty", "frame_3.png")), SCALE).convert(),
                pygame.transform.scale(pygame.image.load(path.join("resources", "kitty", "frame_4.png")), SCALE).convert(),
                pygame.transform.scale(pygame.image.load(path.join("resources", "kitty", "frame_5.png")), SCALE).convert(),
            ],
            'idle': [pygame.transform.scale(pygame.image.load(path.join("resources", "kitty", "frame_4.png")), SCALE).convert()]
        }
        self.current_state = 'idle'
        self.image = pygame.transform.scale(self.frames_dict[self.current_state][0], SCALE)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.image_flip = True  # should the image be flipped

    def set_loc(self, x=None, y=None):
        self.current_state = 'walk'
        self.statechanged = True
        if x:
            if x < self.rect.centerx:
                self.image_flip = False
            elif x > self.rect.centerx:
                self.image_flip = True
            self.rect.centerx = x

        if y:
            self.rect.centery = y
        self.nametag.rect.x, self.nametag.rect.y = self.rect.topleft
        self.nametag.rect.y -= 5

    def update(self):

        if not self.statechanged:
            self.current_state = 'idle'
            self.current_frame = 0

        self.current_call += 1
        if self.current_call == self.next_frame:
            self.current_call = 0
            self.current_frame += 1
            if len(self.frames_dict[self.current_state]) == self.current_frame:
                self.current_frame = 0
            self.image = self.frames_dict[self.current_state][self.current_frame]
            if self.image_flip:
                self.image = pygame.transform.flip(self.image, True, False)

        self.statechanged = False


class ControlledSprite(MovingSprite):
    def __init__(self,x=0, y=0, game_fps=30, num=0, nametag=None):
        super().__init__(x, y, game_fps, num, nametag)
        self.blocks = pygame.sprite.Group()  # group of sprites this sprite is not allowed to touch.
        self.direction_dict = {'up': False, 'down': False, 'left': False, 'right': False}
        self.speed = 6

    def collidegroup(self, direction):
        if direction == 'up':
            self.rect.y -= self.speed
        if direction == 'down':
            self.rect.y += self.speed
        if direction == 'right':
            self.rect.x += self.speed
        if direction == 'left':
            self.rect.x -= self.speed

        collision = pygame.sprite.spritecollideany(self, self.blocks)

        if direction == 'up':
            self.rect.y += self.speed
        if direction == 'down':
            self.rect.y -= self.speed
        if direction == 'right':
            self.rect.x -= self.speed
        if direction == 'left':
            self.rect.x += self.speed

        return collision

    def move_sprite(self, direction, moving=False):
        self.direction_dict[direction] = moving

    def update(self):
        if True in self.direction_dict.values():
            self.current_state = 'walk'
            if self.direction_dict['up']:
                if not self.collidegroup('up'):
                    self.rect.y -= self.speed
            if self.direction_dict['down']:
                if not self.collidegroup('down'):
                    self.rect.y += self.speed
            if self.direction_dict['right']:
                if not self.collidegroup('right'):
                    self.rect.x += self.speed
                self.image_flip = True
            if self.direction_dict['left']:
                if not self.collidegroup('left'):
                    self.rect.x -= self.speed
                self.image_flip = False
        else:
            self.current_state = 'idle'
            self.current_frame = 0

        self.current_call += 1
        if self.current_call == self.next_frame:
            self.current_call = 0
            self.current_frame += 1
            if len(self.frames_dict[self.current_state]) == self.current_frame:
                self.current_frame = 0
            self.image = self.frames_dict[self.current_state][self.current_frame]
            if self.image_flip:
                self.image = pygame.transform.flip(self.image, True, False)

        self.nametag.rect.x, self.nametag.rect.y = self.rect.topleft
        self.nametag.rect.y -= 5


class Point(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.transform.scale(pygame.image.load(path.join("resources", "fish_point.png")), (20, 20))
        self.rect = self.image.get_rect(center=(x+25, y+25))
        self.num = 2

    def set_loc(self, x=None, y=None):
        if x:
            self.rect.x = x
        if y:
            self.rect.y = y



class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(pygame.image.load(path.join("resources", "walltile.png")).convert(), (WALL_WIDTH, WALL_HEIGHT))
        self.rect = self.image.get_rect(topleft=(x, y))

    #def move(self, direction):
    #    if direction == 'right':
    #        self.rect.x += self.speed
    #    if direction == 'left':
    #        self.rect.x -= self.speed
    #    if direction == 'down':
    #        self.rect.y += self.speed
    #    if direction == 'up':
    #        self.rect.y -= self.speed
