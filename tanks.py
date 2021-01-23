import pygame
import pytmx
import math
import sys
import random
import datetime

FPS = 60
WIDTH, HEIGHT = 1280, 720
tile_width = tile_height = 32

# точки спавна для уровней
SPAWNPOINTS_FOR_LEVELS = [[(22, 48), (22, 22), (70, 40), (22, 48), (70, 22), (60, 60)],
                          [(22, 50), (75, 25), (22, 48), (30, 77), (22, 22), (70, 75)]]


# функция загрузки изображения
def load_image(fullname, colorkey=None):
    image = pygame.image.load(fullname)
    if colorkey is not None:
        # загрузка изображения без фона
        # если параметр colorkey равен -1,
        # то за цвет фона берется цвет левого верхнего пикселя
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


# класс игровой карты
class Map:
    def __init__(self, filename):
        # загрузка карты с использованием библиотеки pytmx
        self.map = pytmx.load_pygame(f"maps/{filename}")
        self.height = self.map.height
        self.width = self.map.width
        self.tile_size = self.map.tilewidth

    # рендеринг карты
    def render(self):
        for y in range(self.height):
            for x in range(self.width):
                # создание клетки
                # в качетсве её изображения берется изображение тайла с первого (нулевого) слоя карты
                tile_id = self.map.tiledgidmap[self.map.get_tile_gid(x, y, 0)]
                if tile_id == 1 or tile_id == 66 or tile_id == 285:
                    Tile(tiles_group, self.map.get_tile_image(x, y, 0), x, y)
                elif tile_id == 363 or tile_id == 106:
                    Tile(bonus_group, self.map.get_tile_image(x, y, 0), x, y,
                         "speed")
                elif tile_id == 364 or tile_id == 105:
                    Tile(bonus_group, self.map.get_tile_image(x, y, 0), x, y,
                         "ammo")
                else:
                    Tile(walls_group, self.map.get_tile_image(x, y, 0), x, y)


# класс тайла(клеточки)
class Tile(pygame.sprite.Sprite):
    # для инициализации необходимо передать группу, к которой эта клетка относится,
    # её изображение, координаты клетки на игровом поле и необязательный параметр bonus_type,
    # который указывет, к какому типу бонусов относится клетка
    def __init__(self, group, image, pos_x, pos_y, bonus_type=None):
        super().__init__(group, all_sprites)
        self.image = image
        self.coords = (pos_x, pos_y)
        self.bonus_type = bonus_type
        self.rect = self.image.get_rect().move(tile_width * pos_x,
                                               tile_height * pos_y)

    def get_map_coords(self):
        return self.coords

    def remove_image(self):
        # смена изображения клетки на изображение тайла с теми же координатами, но со второго слоя
        self.image = battle_map.map.get_tile_image(*self.coords, 1)
        self.remove(bonus_group)
        self.add(tiles_group)

    def get_bonus_type(self):
        return self.bonus_type


class Player(pygame.sprite.Sprite):
    def __init__(self, image, pos_x, pos_y):
        super().__init__(player_group, all_sprites)
        self.image = image
        self.rect = self.image.get_rect().move(pos_x, pos_y)  # координаты экранные
        self.angle = -90  # угол, на который повёрнут танк (в градусах)
        self.player_speed = 5  # скорость танка
        self.hp = 100  # очки здоровья
        self.max_speed = 7  # максимальаня скорость, которую может иметь танк,
        # когда соберёт бонус ускорения
        self.damage = 35  # урон от выстрела танка
        self.reload_time = 2000  # время перезарядки в миллисекундах
        self.time_of_the_shot = -1  # время, когда был произведен выстрел
        self.bullets = 10  # оставшееся количество выстрелов
        self.bonus_timer = 0  # время, когда началось действие бонуса "ускорение" (в миллисекундах)
        self.speed_bonus_time = 0  # оставшееся время действия бонуса "ускорение"
        self.is_alive = True

    def move(self, speed):
        #  перемещение танка под его углом в заданном направлении (аргумент speed)
        self.rect = self.rect.move(speed *
                                   math.cos(math.radians(self.angle)),
                                   speed *
                                   math.sin(math.radians(self.angle)))
        if pygame.sprite.spritecollideany(self, walls_group) or \
                pygame.sprite.spritecollideany(self, enemies_group):
            self.rect = self.rect.move(-speed *
                                       math.cos(math.radians(self.angle)),
                                       -speed *
                                       math.sin(math.radians(self.angle)))

    def update_bonus_timer(self):
        # проверка того, что действие ускорения ещё не кончилось
        if (pygame.time.get_ticks() - self.bonus_timer >= self.speed_bonus_time) \
                and self.speed_bonus_time != 0:
            self.bonus_timer = 0
            self.speed_bonus_time = 0
            self.player_speed = 5

    def movement(self):
        self.update_bonus_timer()

        #  проверка того, какие клавишы нажаты пользователем
        #  и перемещение танка в зависимости от этого
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.move(self.player_speed)
        if keys[pygame.K_s]:
            self.move(-self.player_speed)

        #  проверка на то, не собрал ли пользователь какой-либо бонус
        bonus_collided = pygame.sprite.spritecollide(self, bonus_group, False)
        if bonus_collided:
            for tile in bonus_collided:
                bonus = tile.get_bonus_type()
                if bonus == "ammo":
                    self.bullets += 3
                elif bonus == "speed":
                    self.bonus_timer = pygame.time.get_ticks()
                    self.speed_bonus_time = 10000
                    self.player_speed = self.player_speed + 2 if \
                        self.player_speed <= self.max_speed else self.max_speed
                tile.remove_image()

    #  вращение танка на определенный угол
    def rotate(self, angle):
        self.angle = (self.angle + angle) % 360
        rect = self.image.get_rect(center=(self.rect.x + self.rect.w // 2,
                                           self.rect.y + self.rect.h // 2))
        rot_image = pygame.transform.rotate(self.image, -angle)
        rot_rect = rot_image.get_rect(center=rect.center)
        self.image = rot_image
        self.rect = rot_rect
        if pygame.sprite.spritecollideany(self, walls_group) or \
                pygame.sprite.spritecollideany(self, enemies_group):
            self.move(-self.player_speed + 10)
            self.move(self.player_speed + 10)

    def shot(self):
        if self.time_of_the_shot == -1 and self.bullets != 0:
            AnimatedShot(r"sprites\animated_shot", self.rect.x, self.rect.y,
                         self.angle)
            Bullet(r"sprites\animated_shot", self.rect.x, self.rect.y,
                   self.angle, self.damage, enemies_group)
            sound_of_shot.play()
            self.time_of_the_shot = pygame.time.get_ticks()
            self.bullets -= 1

    def get_hp(self):
        return self.hp

    def get_bullets(self):
        return self.bullets

    #  метод, возвращающий количество прошедших миллисекунд с момента поднятия ускорения
    def get_bonus_timer(self):
        if self.speed_bonus_time == 0:
            return 0
        return pygame.time.get_ticks() - self.bonus_timer

    #  метод,  возвращающий количество прошедших миллисекунд с момента выстрела
    def get_left_reload_time(self):
        return pygame.time.get_ticks() - self.time_of_the_shot \
            if self.time_of_the_shot != -1 else self.reload_time

    def update_reload_time(self):
        if self.time_of_the_shot != -1:
            if self.get_left_reload_time() >= self.reload_time:
                self.time_of_the_shot = -1

    # метод остановки всех таймеров
    def pause_timers(self, time):
        if self.bonus_timer > 0:
            self.bonus_timer += time
        if self.time_of_the_shot != -1:
            self.time_of_the_shot += time

    #  функция нанесения урона танку от попадания снаряда
    def get_damaged(self, damage):
        if self.is_alive:
            self.hp -= damage
            # проверка того, что танк был уничтожен вытсрелом
            if self.hp <= 0:
                self.hp = 0
                self.is_alive = False
                self.image = load_image(r"textures\tanks\killed tank.png", -1)
                angle = self.angle
                self.angle = -90
                self.rotate(angle)


#  класс анимированного выстрела
class AnimatedShot(pygame.sprite.Sprite):
    def __init__(self, filepath, x, y, angle):
        super().__init__(all_sprites)
        self.angle = angle + 90
        self.frames = []
        self.load_sprites(filepath)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.counter = -1
        if self.angle == 0 or self.angle == 360:
            self.rect = self.image.get_rect().move(x - 2, y - 22)
        elif self.angle == 90:
            self.rect = self.image.get_rect().move(x + 35, y)
        elif self.angle == 180:
            self.rect = self.image.get_rect().move(x - 2, y + 35)
        elif self.angle == 270:
            self.rect = self.image.get_rect().move(x - 20, y - 2)

    def load_sprites(self, filepath):
        for i in range(1, 6):
            image = load_image(filepath + f"/Flash_A_0{i}.png")
            image = pygame.transform.rotate(image, -self.angle)
            self.frames.append(image)

    def update(self):
        self.counter += 1
        if self.counter % 4 == 0:
            if self.cur_frame != 4:
                self.cur_frame += 1
                self.image = self.frames[self.cur_frame]
            else:
                self.kill()


#  класс снаряда танка
class Bullet(pygame.sprite.Sprite):
    def __init__(self, filepath, x, y, angle, damage, group):
        super().__init__(bullets_group, all_sprites)
        self.angle = angle + 90
        self.damage = damage
        self.enemies = group  # группа спрайтов, которой снаряд будет наносить урон
        self.image = pygame.transform.rotate(
            load_image(filepath + "/Heavy_Shell.png"),
            self.angle)
        self.explosion_frames = []
        self.load_sprites(filepath)
        self.counter = -1
        self.cur_frame = 0
        if self.angle == 0 or self.angle == 360:
            self.rect = self.image.get_rect().move(x + 14, y - 22)
            self.dx, self.dy = 0, -30
        elif self.angle == 90:
            self.rect = self.image.get_rect().move(x + 35, y + 15)
            self.dx, self.dy = 30, 0
        elif self.angle == 180:
            self.rect = self.image.get_rect().move(x + 14, y + 35)
            self.dx, self.dy = 0, 30
        elif self.angle == 270:
            self.rect = self.image.get_rect().move(x - 20, y + 13)
            self.dx, self.dy = -30, 0

    def load_sprites(self, filepath):
        for i in range(1, 9):
            image = load_image(filepath + f"/Explosion_{i}.png")
            image = pygame.transform.rotate(image, -self.angle)
            self.explosion_frames.append(image)

    def detonate(self):
        explosion_sound.play()
        self.counter = 0
        center = self.rect.x + 16, self.rect.y + 16
        self.image = self.explosion_frames[self.cur_frame]
        self.rect = self.image.get_rect(center=center)

    def update(self):
        if self.counter == -1:
            self.rect = self.rect.move(self.dx, self.dy)
            if pygame.sprite.spritecollideany(self, walls_group):
                self.detonate()
            sprites = pygame.sprite.spritecollide(self, self.enemies,
                                                  dokill=False)
            # проверка снаряда на столкновение с танком
            if sprites:
                self.detonate()
                for enemy in sprites:
                    if enemy.is_alive:
                        enemy.get_damaged(self.damage)
        else:
            self.counter += 1
            if self.cur_frame != 7:
                self.cur_frame += 1
                self.image = self.explosion_frames[self.cur_frame]
            else:
                self.kill()


class Camera:
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self, target):
        global spawnpoints
        self.dx = -(target.rect.x + target.rect.w // 2 - WIDTH // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - HEIGHT // 2)
        for i in range(len(spawnpoints)):
            spawnpoints[i] = spawnpoints[i][0] + self.dx, \
                             spawnpoints[i][1] + self.dy


#  класс кнокпи
class Button:
    def __init__(self, x, y, filepath):
        self.image = pygame.image.load(filepath)  # загрузка изображение кнопки
        self.rect = self.image.get_rect().move(x, y)  # перемещение кнокпи на заданные координаты
        self.x, self.y = x, y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.draw()

    def is_clicked(self, x, y, ):
        # проверка на нажатие кнокпи
        if self.x <= x <= self.x + self.width and \
                self.y <= y <= self.y + self.height:
            btn_pressed_sound.set_volume(0.3)
            btn_pressed_sound.play()
            return True
        return False

    def draw(self):
        # отрисовка кнопки
        screen.blit(self.image, self.rect)


# класс вражеского танка
class Enemy(pygame.sprite.Sprite):
    def __init__(self, image, pos_x, pos_y):
        super().__init__(enemies_group, all_sprites)
        self.image = image
        self.rect = self.image.get_rect().move(pos_x, pos_y)
        self.angle = 270
        self.speed = 1
        self.hp = 75
        self.damage = 5
        self.reload_time = 2500
        self.time_of_the_shot = -1
        self.is_alive = True
        # координаты поля видимости танка
        self.direction_coords = (self.rect.x + 10, self.rect.y - 500,
                                 self.rect.x + 70, self.rect.y)
        self.sight = pygame.sprite.Sprite()
        self.sight.image = pygame.Surface([80, 500])
        self.sight.rect = self.sight.image.get_rect().move(self.direction_coords[0],
                                                           self.direction_coords[1])
        self.last_movement = -1

    def movement(self):
        self.rect = self.rect.move(self.speed *
                                   math.cos(math.radians(self.angle)),
                                   self.speed *
                                   math.sin(math.radians(self.angle)))
        if pygame.sprite.spritecollideany(self, walls_group) or \
                pygame.sprite.spritecollideany(self, player_group):
            self.rect = self.rect.move(-self.speed *
                                       math.cos(math.radians(self.angle)),
                                       -self.speed *
                                       math.sin(math.radians(self.angle)))
            self.rotate((self.angle + 90) % 360)

    def rotate(self, angle):
        self.angle = (self.angle + angle) % 360
        rect = self.image.get_rect(center=(self.rect.x + self.rect.w // 2,
                                           self.rect.y + self.rect.h // 2))
        rot_image = pygame.transform.rotate(self.image, -angle)
        rot_rect = rot_image.get_rect(center=rect.center)
        self.image = rot_image
        self.rect = rot_rect
        if pygame.sprite.spritecollideany(self, walls_group) or \
                pygame.sprite.spritecollideany(self, enemies_group):
            self.move(-self.speed + 10)
            self.move(self.speed + 10)
        if pygame.sprite.spritecollideany(self, walls_group) or \
                pygame.sprite.spritecollideany(self, player_group):
            return False
        return True

    def shot(self):
        if self.time_of_the_shot == -1:
            AnimatedShot(r"sprites\animated_shot", self.rect.x, self.rect.y,
                         self.angle)
            Bullet(r"sprites\animated_shot", self.rect.x, self.rect.y,
                   self.angle, self.damage, player_group)
            sound_of_shot.play()
            self.time_of_the_shot = pygame.time.get_ticks()

    def get_left_reload_time(self):
        return pygame.time.get_ticks() - self.time_of_the_shot \
            if self.time_of_the_shot != -1 else self.reload_time

    def update_reload_time(self):
        if self.time_of_the_shot != -1:
            if self.get_left_reload_time() >= self.reload_time:
                self.time_of_the_shot = -1

    def get_damaged(self, damage):
        if self.is_alive:
            self.hp -= damage
            if self.hp <= 0:
                self.hp = 0
                self.is_alive = False
                self.image = load_image(r"textures\tanks\killed tank.png", -1)
                angle = self.angle
                self.angle = 270
                while self.angle != angle:
                    self.rotate(90)
                self.add(walls_group)

    #  метод, вращающий поле видимости
    def rotate_direction(self, angle):
        if angle == 90:
            return self.rect.x + 10, self.rect.y, self.rect.x + 70, self.rect.y + 500
        elif angle == 180:
            return self.rect.x - 500, self.rect.y + 10, self.rect.x, self.rect.y + 70
        elif angle == 270:
            return self.rect.x + 10, self.rect.y - 500, self.rect.x + 70, self.rect.y
        elif angle == 0:
            return self.rect.x, self.rect.y + 10, self.rect.x + 500, self.rect.y + 70

    def player_in_sight(self, x1, y1, x2, y2):
        # проверка того, что игрок находится в поле видимости танка
        return not (x1 > player.rect.x + player.rect.width or x2 < player.rect.x or
                    y1 > player.rect.y + player.rect.height or y2 < player.rect.y)

    def check_distance(self):
        # дистанция до танка игрока
        return math.sqrt((self.rect.x - player.rect.x) * (self.rect.x - player.rect.x) +
                         (self.rect.y - player.rect.y) * (self.rect.y - player.rect.y))

    def move(self, speed):
        self.rect = self.rect.move(speed *
                                   math.cos(math.radians(self.angle)),
                                   speed *
                                   math.sin(math.radians(self.angle)))
        if pygame.sprite.spritecollideany(self, walls_group) or \
                pygame.sprite.spritecollideany(self, enemies_group):
            self.rect = self.rect.move(-speed *
                                       math.cos(math.radians(self.angle)),
                                       -speed *
                                       math.sin(math.radians(self.angle)))

    def rotate_sight(self, x1, y1, x2, y2):
        if self.angle == 0 or self.angle == 90:
            self.sight.rect.x, self.sight.rect.y = x1, y1
        else:
            self.sight.rect.x, self.sight.rect.y = x2, y2
        self.sight.rect.width = abs(x1 - x2)
        self.sight.rect.height = abs(y1 - y2)

    # метод, описывающий поведение танка
    def update(self):
        self.direction_coords = self.rotate_direction(self.angle)
        if self.is_alive:
            time = pygame.time.get_ticks()
            x1, y1, x2, y2 = self.direction_coords
            if self.time_of_the_shot == -1 or time - self.time_of_the_shot >= self.reload_time:
                if self.player_in_sight(x1, y1, x2, y2):
                    player_x, player_y = player.rect.x, player.rect.y
                    self.rotate_sight(x1, y1, player_x, player_y)
                    if not pygame.sprite.spritecollideany(self.sight, walls_group):
                        self.time_of_the_shot = -1
                        self.shot()
                    else:
                        self.move(self.speed + 5)
            if self.player_in_sight(*self.rotate_direction((self.angle + 90) % 360)) or self.player_in_sight(
                    *self.rotate_direction((self.angle + 180) % 360)) or self.player_in_sight(
                *self.rotate_direction((self.angle + 270) % 360)):
                if not self.player_in_sight(x1, y1, x2, y2) and time - self.last_movement > 1200:
                    x1, y1, x2, y2 = self.rotate_direction((self.angle + 90) % 360)
                    self.last_movement = time
                    if self.player_in_sight(x1, y1, x2, y2):
                        f = self.rotate(90)
                        if f:
                            self.direction_coords = (x1, y1, x2, y2)
                        else:
                            self.rotate(-90)
                    else:
                        x1, y1, x2, y2 = self.rotate_direction((self.angle - 90) % 360)
                        f = self.rotate(-90)
                        if f:
                            self.direction_coords = (x1, y1, x2, y2)
                        else:
                            self.rotate(90)
            elif (time - self.last_movement > 5000) or self.last_movement == -1:
                self.last_movement = time
                angle = random.choice([-90, 90])
                x1, y1, x2, y2 = self.rotate_direction(((self.angle + angle) % 360))
                f = self.rotate(angle)
                if f:
                    self.direction_coords = (x1, y1, x2, y2)
                else:
                    self.rotate(90)
            else:
                self.movement()


#  функция перезапуска игры
def restart_game(current_level):
    global all_sprites, walls_group, tiles_group, \
        player_group, clock, battle_map, camera, \
        player, sound_of_shot, engine_sound, \
        movement_sound, explosion_sound, bonus_group, \
        enemies_group, bullets_group, enemy_count, \
        spawnpoints, btn_pressed_sound, start_time

    # группы спрайтов
    all_sprites = pygame.sprite.Group()
    walls_group = pygame.sprite.Group()
    tiles_group = pygame.sprite.Group()
    player_group = pygame.sprite.Group()
    bonus_group = pygame.sprite.Group()
    enemies_group = pygame.sprite.Group()
    bullets_group = pygame.sprite.Group()

    #  точки спавна
    spawnpoints = [(x * tile_width, y * tile_height)
                   for x, y in SPAWNPOINTS_FOR_LEVELS[current_level - 1]]

    clock = pygame.time.Clock()

    start_time = datetime.datetime.now()

    x, y = spawnpoints.pop(1)
    Enemy(load_image("textures/tanks/enemy tank.png", -1), x, y)
    enemy_count = 4

    battle_map = Map(f"level{current_level}.tmx")
    battle_map.render()

    x, y = spawnpoints.pop(0)
    player = Player(load_image("textures/tanks/player tank.png", -1), x, y)
    camera = Camera()

    # звуки
    sound_of_shot = pygame.mixer.Sound("sounds/shot.wav")
    engine_sound = pygame.mixer.Sound("sounds/engine_sound.wav")
    movement_sound = pygame.mixer.Sound("sounds/movement.wav")
    explosion_sound = pygame.mixer.Sound("sounds/explosion.wav")
    btn_pressed_sound = pygame.mixer.Sound("sounds/btn_pressed.wav")
    engine_sound.play(loops=-1)


# окно с управлением
def controls_menu():
    image = pygame.image.load(r"menu\controls wndw.png")
    screen.blit(image, (0, 0))
    show_menu = True
    back_btn = Button(20, 620, r"menu\arrowBeige_left.png")
    back_btn.draw()
    while show_menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.is_clicked(*event.pos):
                    show_menu = False
        pygame.display.flip()


#  главное меню
def main_menu():
    global current_lvl
    pygame.mixer.unpause()

    current_lvl = 1

    screen.blit(main_menu_background, (0, 0))

    # кнопки
    start_btn = Button(545, 275, r"menu\start button.png")
    select_lvl_btn = Button(545, 345, r"menu\levels button.png")
    records_btn = Button(545, 415, r"menu\records_btn.png")
    controls_btn = Button(545, 485, r"menu\controls button.png")
    exit_btn = Button(545, 555, r"menu\exit button.png")

    show_menu = True
    while show_menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if controls_btn.is_clicked(*event.pos):
                    controls_menu()
                if start_btn.is_clicked(*event.pos):
                    show_menu = False
                if exit_btn.is_clicked(*event.pos):
                    pygame.quit()
                    sys.exit()
                if select_lvl_btn.is_clicked(*event.pos):
                    current_lvl = select_level()
                if records_btn.is_clicked(*event.pos):
                    records_window()
        screen.blit(main_menu_background, (0, 0))

        start_btn.draw()
        select_lvl_btn.draw()
        exit_btn.draw()
        records_btn.draw()
        controls_btn.draw()

        pygame.display.flip()
    restart_game(current_lvl)


# пауза во время игры
def pause_menu():
    continue_btn = Button(545, 260, r"menu\continue btn.png")
    main_menu_btn = Button(545, 330, r"menu\main menu btn.png")
    restart_button = Button(545, 400, r"menu\restart button.png")

    pygame.mixer.pause()

    start_pause_time = pygame.time.get_ticks()

    show_menu = True
    while show_menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if continue_btn.is_clicked(*event.pos):
                    btn_pressed_sound.play()
                    show_menu = False
                if main_menu_btn.is_clicked(*event.pos):
                    btn_pressed_sound.play()
                    pygame.mixer.stop()
                    main_menu()
                    break
                if restart_button.is_clicked(*event.pos):
                    btn_pressed_sound.play()
                    show_menu = False
                    pygame.mixer.stop()
                    restart_game(current_lvl)
        pygame.display.flip()
    player.pause_timers(pygame.time.get_ticks() - start_pause_time)
    pygame.mixer.unpause()


# функция отрисовки интерфейса во время боя
def draw_interface():
    # отрисовка очков жизней у игрока
    hp = player.get_hp()
    screen.blit(bar, (10, 10))
    pygame.draw.rect(screen, (255, 0, 0), (17, 17, 206 * (hp / 100), 26))

    # отрисовка времени перезарядки
    reload_time = player.get_left_reload_time()
    screen.blit(bar, (10, 70))
    pygame.draw.rect(screen, (0, 255, 0), (17, 77, 206 * (reload_time /
                                                          player.reload_time), 26))

    # отрисовка количества оставшихся снарядов
    bullets = font.render(str(player.get_bullets()), True, (0, 255, 0))
    screen.blit(bullet, (10, 130))
    screen.blit(bullets, (84, 140))

    if player.get_bonus_timer() != 0:
        # отрисовка количества секунд до окончания действия ускорения
        seconds = font.render(str(10 - player.get_bonus_timer() // 1000), True,
                              (255, 255, 0))
        screen.blit(bonus, (10, 204))
        screen.blit(seconds, (84, 214))


# функция, которая проверяет, остались ли живые враги на карте
def check_enemies():
    global enemy_count, new_enemy, spawnpoints
    flag = False
    for enemy in enemies_group.sprites():
        if enemy.is_alive:
            flag = True
    if enemy_count > 0 and not flag:
        enemy_count -= 1
        x, y = spawnpoints.pop(random.randint(0, len(spawnpoints) - 1))
        new_enemy = Enemy(load_image("textures/tanks/enemy tank.png", -1), x, y)
    elif enemy_count == 0:
        end_window(True)
    elif not player.is_alive:
        end_window(False)


def end_window(won):
    pygame.mixer.pause()
    time_delta = datetime.datetime.now() - start_time
    show_menu = True
    pygame.mixer.stop()
    screen.blit(inf_panel, (390, 210))
    if won:
        screen.blit(font.render("Победа!", True, (255, 0, 0)), (535, 280))
        screen.blit(font.render(f"Время: {time_delta.seconds} с",
                                True, (255, 0, 0)), (535, 330))

        f = open(r"records\records.txt", mode="r", encoding="utf8")
        level_name = "Таможня" if current_lvl == 1 else "Пустыня"
        res = f"{level_name};{datetime.datetime.now().strftime('%m/%d/%Y')};{time_delta.seconds}"
        records = f.readlines()
        f.close()
        records.append(res)
        records.sort(key=lambda x: int(x.split(";")[2]))

        f = open(r"records\records.txt", mode="w", encoding="utf8")
        f.seek(0)
        for i in range(len(records)):
            if i == 6:
                break
            f.write(records[i].strip() + "\n")
        f.close()
    else:
        screen.blit(font.render("Поражение", True, (255, 0, 0)), (535, 280))
        screen.blit(font.render(f"Время: {time_delta.seconds} с",
                                True, (255, 0, 0)), (535, 330))
    main_menu_btn = Button(545, 420, r"menu\main menu btn.png")
    while show_menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if main_menu_btn.is_clicked(*event.pos):
                    show_menu = False
                    main_menu()
        pygame.display.flip()


# окно выбора уровня
def select_level():
    screen.blit(main_menu_background, (0, 0))
    screen.blit(first_level_img, (390, 210))
    current_level = 1
    accept_button = Button(545, 570, r"menu\accept.png")
    left_button = Button(200, 310, r"menu\arrowBeige_left.png")
    right_button = Button(1080, 310, r"menu\arrowBeige_right.png")
    accept_button.draw()
    left_button.draw()
    right_button.draw()
    screen.blit(font.render("Таможня", True, (255, 0, 0)), (545, 150))
    show_menu = True
    while show_menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if accept_button.is_clicked(*event.pos):
                    show_menu = False
                if left_button.is_clicked(*event.pos):
                    current_level = 1
                if right_button.is_clicked(*event.pos):
                    current_level = 2
        screen.blit(main_menu_background, (0, 0))
        accept_button.draw()
        left_button.draw()
        right_button.draw()

        if current_level == 1:
            screen.blit(first_level_img, (390, 210))
            screen.blit(font.render("Таможня", True, (255, 0, 0)), (540, 150))
        else:
            screen.blit(second_level_img, (390, 210))
            screen.blit(font.render("Пустыня", True, (255, 0, 0)), (545, 150))
        pygame.display.flip()
    return current_level


# окно с таблицей рекордов
def records_window():
    screen.blit(records_background, (0, 0))

    f = open(r"records\records.txt", mode="r", encoding="utf8")
    records = [r.strip().split(";") for r in f.readlines()]
    screen.blit(font.render("Карта", True, (255, 0, 0)), (350, 80))
    screen.blit(font.render("Дата", True, (255, 0, 0)), (600, 80))
    screen.blit(font.render("Время", True, (255, 0, 0)), (810, 80))
    for number, record in enumerate(records):
        screen.blit(font.render(f"{number + 1})   {record[0]}   {record[1]}   {record[2]} c",
                                True, (255, 0, 0)), (250, 80 + (number + 1) * 60))
    f.close()

    back_btn = Button(50, 600, r"menu\arrowBeige_left.png")

    show_menu = True
    while show_menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.is_clicked(*event.pos):
                    show_menu = False
        pygame.display.flip()


pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2)
pygame.font.init()
font = pygame.font.Font(None, 64)

bar = pygame.image.load(r"interface\bar.png")
bullet = pygame.image.load(r"interface\Bullet.png")
bonus = pygame.image.load(r"interface\Bonus_Icon.png")
main_menu_background = pygame.image.load(r"menu\background.png")
records_background = pygame.image.load(r"menu\records_backgorund.png")
first_level_img = pygame.image.load(r"menu\level1.PNG")
second_level_img = pygame.image.load(r"menu\level2.PNG")
inf_panel = pygame.image.load(r"menu\panel.png")

btn_pressed_sound = pygame.mixer.Sound("sounds/btn_pressed.wav")

pygame.display.set_caption('Танки')
size = WIDTH, HEIGHT
screen = pygame.display.set_mode(size)

main_menu()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pause_menu()
            if event.key == pygame.K_d:
                player.rotate(90)
                if pygame.sprite.spritecollideany(player, walls_group):
                    player.rotate(-90)
            elif event.key == pygame.K_a:
                player.rotate(-90)
                if pygame.sprite.spritecollideany(player, walls_group):
                    player.rotate(90)
            if event.key == pygame.K_w or event.key == pygame.K_s:
                movement_sound.play(loops=-1)
            if event.key == pygame.K_SPACE:
                player.shot()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w or event.key == pygame.K_s:
                movement_sound.fadeout(750)

    player.movement()
    player.update_reload_time()

    enemies_group.update()

    camera.update(player)
    for sprite in all_sprites:
        camera.apply(sprite)

    check_enemies()

    screen.fill((0, 0, 0))
    all_sprites.update()
    all_sprites.draw(screen)
    enemies_group.draw(screen)
    bullets_group.draw(screen)

    draw_interface()

    clock.tick(FPS)

    pygame.display.flip()
pygame.quit()
