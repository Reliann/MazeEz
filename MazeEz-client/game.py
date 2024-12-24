import pygame
from GameSprites import *
import gui
import client
import ctypes
from os import path

SW = 500
SH = 500


class Game(object):
    online = True
    def __init__(self, client):
        self.client = client
        self.screen = None
        self.fps_c = pygame.time.Clock()
        self.running = False
        self.screensize = 700, 450
        self.floor = pygame.transform.scale(pygame.image.load(path.join("resources", "grassfloor.jpg")), self.screensize)

    def playgame(self):
        result = None
        enemiesnum = []
        initdata = self.client.game_updates.get()
        try:
            gamemodle = initdata['model']
        except(KeyError, TypeError):
            return 'MainMenu'

        self.screen = pygame.display.set_mode(self.screensize)  # self.screensize
        mynum = initdata['your_num']
        enemiesnum_team = initdata['player_list']
        scores = {'redteam': {}, 'blueteam': {}}
        for player_num in enemiesnum_team:
            if player_num[1] == 0:
                scores['blueteam'].update({str(player_num[0]): 0})
            else:
                scores['redteam'].update({str(player_num[0]): 0})
        for enemy in enemiesnum_team:
            enemiesnum.append(enemy[0])
        enemiesnum.remove(mynum)

        enemies = pygame.sprite.Group()
        points = pygame.sprite.Group()
        self.screen.blit(self.floor, (0, 0))
        mysprite = None
        walls = pygame.sprite.Group()
        nametags = pygame.sprite.Group()
        for i in range(len(gamemodle)):
            for j in range(len(gamemodle[i])):
                if gamemodle[i][j] == 1:
                    walls.add(Wall(j * 50, i * 50))
                elif gamemodle[i][j] == mynum:
                    n = gui.RawText(j*50, i*50 + 3, self.client.user["username"], size=25)
                    mysprite = ControlledSprite(num=mynum, x=j*50, y=i*50, nametag=n)
                    nametags.add(n)
                elif gamemodle[i][j] in enemiesnum:
                    for enemy in enemiesnum_team:
                        if enemy[0] == gamemodle[i][j]:
                            n = gui.RawText(j*50, i*50 + 3, enemy[2], size=25)
                            enemies.add(MovingSprite(num=gamemodle[i][j], x=j*50, y=i*50, nametag=n))
                            nametags.add(n)
                elif gamemodle[i][j] == 2:
                    points.add(Point(j*50, i*50))


        all_sprites = pygame.sprite.RenderUpdates()
        all_sprites.add(walls)
        all_sprites.add(enemies)
        all_sprites.add(mysprite)
        all_sprites.add(nametags)
        all_sprites.add(points)


        self.screen.blit(pygame.transform.scale(pygame.image.load(path.join("resources", "scores.png")), (150, 120)), (505, 10))
        self.screen.blit(pygame.transform.scale(pygame.image.load(path.join("resources", "redteam.png")), (140, 80)), (480, 110))
        self.screen.blit(pygame.transform.scale(pygame.image.load(path.join("resources", "blueteam.png")), (140, 80)), (480, 200))
        redteam_scores = gui.RawText(650, 140, "0")
        blueteam_scores = gui.RawText(650, 230, "0")

        all_sprites.add(redteam_scores)
        all_sprites.add(blueteam_scores)

        all_sprites.draw(self.screen)
        for enemy in enemies:
            if enemiesnum_team[0] == enemy.num:
                enemy.name = enemiesnum_team[2]
            if enemiesnum_team[0] == mynum:
                mysprite.name = enemiesnum_team[2]

        mysprite.blocks = walls         # set forbidden sprites

        pygame.display.flip()
        print("starting game session")
        pygame.key.set_repeat()

        self.running = True
        while self.running and Game.online:
            while not self.client.game_updates.empty():
                data = self.client.game_updates.get()  # tuple :x, y , num
                try:
                    # if data['location_update'][2] == mynum:
                    #     mysprite.set_loc(data['location_update'][0], data['location_update'][1])
                    #     continue

                    for enemy in enemies:
                        if data['location_update'][2] == enemy.num:
                                enemy.set_loc(data['location_update'][0], data['location_update'][1])
                    if data['location_update'][2] == 2:
                        p = Point(data['location_update'][0], data['location_update'][1])
                        points.add(p)
                        all_sprites.add(p)
                    continue
                except (KeyError,TypeError):
                    pass

                try:
                    for enemy in enemiesnum_team:
                        if enemy[1] == 0 and data['add_points'] == enemy[0]:
                            scores['blueteam'][str(data['add_points'])] += 1
                            blueteam_scores.text = str(sum(scores['blueteam'].values()))

                        elif enemy[1] == 1 and data['add_points'] == enemy[0]:
                            scores['redteam'][str(data['add_points'])] += 1
                            redteam_scores.text = str(sum(scores['redteam'].values()))
                except (KeyError, TypeError):
                    pass

                try:
                    if data['game_result']:
                        result = data['game_result']
                        self.running = False
                except (KeyError, TypeError):
                    pass

            myloc = (mysprite.rect.x,mysprite.rect.y)

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    result = 'quit'
                    self.running = False

                elif event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_w:
                        mysprite.move_sprite('up', True)
                    if event.key == pygame.K_d:
                        mysprite.move_sprite('right', True)
                    if event.key == pygame.K_a:
                        mysprite.move_sprite('left', True)
                    if event.key == pygame.K_s:
                        mysprite.move_sprite('down', True)

                elif event.type == pygame.KEYUP:

                    if event.key == pygame.K_w:
                        mysprite.move_sprite('up', False)
                    if event.key == pygame.K_d:
                        mysprite.move_sprite('right', False)
                    if event.key == pygame.K_a:
                        mysprite.move_sprite('left', False)
                    if event.key == pygame.K_s:
                        mysprite.move_sprite('down', False)

            all_sprites.update()

            if not myloc == (mysprite.rect.x, mysprite.rect.y):
                self.client.send_event({'location_update': (mysprite.rect.centerx,
                                                            mysprite.rect.centery,
                                                            mysprite.num)})

            point = pygame.sprite.spritecollideany(mysprite, points)
            if point:
                point.kill()
                self.client.send_event({'point_update': (point.rect.x, point.rect.y, mysprite.num)})
            else:
                for sprite in enemies:
                    point = pygame.sprite.spritecollideany(sprite, points)
                    if point:
                        point.kill()

            all_sprites.clear(self.screen, self.floor)
            dirty_rects = all_sprites.draw(self.screen)
            pygame.display.update(dirty_rects)

            self.fps_c.tick(30)

        pygame.key.set_repeat(50, 50)
        pygame.display.set_mode((500, 500))
        return result
