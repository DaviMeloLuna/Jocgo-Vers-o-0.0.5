import pygame
import math

from classes.config import *


class Projetil(pygame.sprite.Sprite):  # classe para os projeteis
    def __init__(self, game, x, y, dx, dy):
        self.game = game

        self._layer = PROJ_LAYER
        self.group = self.game.all_sprites

        pygame.sprite.Sprite.__init__(self, self.group)

        # quadrado laranja da bola de fogo
        self.image = pygame.Surface((16, 16))
        self.image.fill((255, 120, 0))

        self.rect = self.image.get_rect()

        # onde a bola de fogo nasce
        self.rect.centerx = x
        self.rect.centery = y

        self.dx = dx
        self.dy = dy

        self.speed = 5

    def update(self):
        self.rect.x += self.dx * self.speed
        self.rect.y += self.dy * self.speed

        if self.rect.colliderect(self.game.player.rect):
            self.game.player.hp = max(
                0, self.game.player.hp - 5)  # dá dano ao jogador
            self.kill()  # destrói o projétil ao colidir com o jogador

        if pygame.sprite.spritecollide(self, self.game.walls, False):
            self.kill()


# Inimigo perseguidor e atirador
class PerseguidorA(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game

        self._layer = PLAYER_LAYER
        self.group = self.game.all_sprites, self.game.enemies

        pygame.sprite.Sprite.__init__(self, self.group)

        # aparencia do quadrado laranja representando a mula sem cabeça
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill((255, 100, 0))

        self.rect = self.image.get_rect()

        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)

        self.hitbox = self.rect.copy()

        self.speed = 1.5
        self.hp = 20.0

        self.cooldown_tiro = FPS

    # a mula é um inimigo para testes
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.kill()

    def update(self):
        player = self.game.player

        if self.rect.colliderect(self.game.player.rect):
            self.game.player.hp = max(
                0, self.game.player.hp - 5)

        if player is None:
            return

        # Melhoria de movimentação
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery - 8

        # Normalização do vetor direção
        distancia = math.sqrt(dx**2 + dy**2)

        if distancia != 0:
            dx /= distancia
            dy /= distancia

            # Implementação de colisões
            self.pos_x += dx * self.speed
            self.rect.x = int(self.pos_x)

            obstaculo = [self.game.walls, self.game.holes, self.game.blocks]

            for grupo in obstaculo:
                colisao = pygame.sprite.spritecollide(self, grupo, False)

                for obstaculo in colisao:
                    if dx > 0:  # Colisão a direita
                        self.rect.right = obstaculo.rect.left
                    elif dx < 0:
                        self.rect.left = obstaculo.rect.right

                    self.pos_x = self.rect.x

            self.pos_y += dy * self.speed
            self.rect.y = int(self.pos_y)

            for grupo in obstaculo:
                colisao = pygame.sprite.spritecollide(self, grupo, False)

                for obstaculo in colisao:
                    if dy > 0:
                        self.rect.bottom = obstaculo.rect.top
                    elif dy < 0:
                        self.rect.top = obstaculo.rect.bottom

                    self.pos_y = self.rect.y

        self.hitbox = self.rect.copy()

        if self.cooldown_tiro > 0:
            self.cooldown_tiro -= 1

        if self.cooldown_tiro == 0:
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery

            distancia = math.sqrt(dx**2 + dy**2)

            dx /= distancia  # normalização do vetor direção
            dy /= distancia

            Projetil(
                self.game, self.rect.centerx, self.rect.centery, dx, dy)

            # espera um tempo de 2 segundos antes de atirar novamente
            self.cooldown_tiro = 2 * FPS


# Inimigo Estático
class Iara(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game

        # Ajeitar a imagem e as informações principais da iara
        self.x = x*TILESIZE
        self.y = y*TILESIZE

        self._layer = PLAYER_LAYER
        self.group = self.game.all_sprites, self.game.enemies

        pygame.sprite.Sprite.__init__(self, self.group)

        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill((0, 0, 255))

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.cooldown_tiro = FPS
        self.hp = 30.0

        self.hitbox = self.rect.copy()

    def take_damage(self, damage):  # Só para não dar erro
        self.hp -= damage

        if self.hp <= 0:
            self.kill()

    def update(self):
        player = self.game.player

        # Calculando a distância para ajeitar o alcance:
        distancia = math.sqrt((self.rect.x - player.rect.x) **
                              2 + (self.rect.y - player.rect.y)**2)

        if self.cooldown_tiro == 0:
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery - 8

            distancia = math.sqrt(dx**2 + dy**2)

            if distancia != 0:
                dx /= distancia
                dy /= distancia

            Projetil(
                self.game, self.rect.centerx, self.rect.centery, dx, dy)

            self.cooldown_tiro = 2 * FPS


class Perseguidor(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = PLAYER_LAYER
        self.group = self.game.all_sprites, self.game.enemies

        pygame.sprite.Sprite.__init__(self, self.group)

        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill((0, 180, 0))  # quadrado verde

        self.rect = self.image.get_rect()

        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)

        self.hitbox = self.rect.copy()

        self.speed = 1.5
        self.hp = 25.0

    def take_damage(self, damage):
        self.hp -= damage

        if self.hp <= 0:
            self.kill()

    def update(self):
        # saber se o jogador encostou no curupira
        if self.rect.colliderect(self.game.player.rect):
            self.game.player.hp = max(
                0, self.game.player.hp - 5)

        player = self.game.player

        if player is None:
            return

        # Melhoria de movimentação
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery - 8

        # Normalização do vetor direção
        distancia = math.sqrt(dx**2 + dy**2)

        if distancia != 0:
            dx /= distancia
            dy /= distancia

            self.pos_x += dx * self.speed

            self.rect.x = int(self.pos_x)

            obstaculo = [self.game.walls, self.game.holes, self.game.blocks]

            for grupo in obstaculo:
                colisao = pygame.sprite.spritecollide(self, grupo, False)

                for obstaculo in colisao:
                    if dx > 0:  # Colisão a direita
                        self.rect.right = obstaculo.rect.left
                    elif dx < 0:
                        self.rect.left = obstaculo.rect.right

                    self.pos_x = self.rect.x

            self.pos_y += dy * self.speed

            self.rect.y = int(self.pos_y)

            for grupo in obstaculo:
                colisao = pygame.sprite.spritecollide(self, grupo, False)

                for obstaculo in colisao:
                    if dy > 0:
                        self.rect.bottom = obstaculo.rect.top
                    elif dy < 0:
                        self.rect.top = obstaculo.rect.bottom

                    self.rect.y = self.rect.y

        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        self.hitbox = self.rect.copy()


# Chefe final
class Cacador(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = PLAYER_LAYER
        self.group = self.game.all_sprites, self.game.enemies

        pygame.sprite.Sprite.__init__(self, self.group)

        self.facing = "face_baixo"

        # Objeto Pai
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill((5, 52, 246))  # Azul Custumizado

        self.rect = self.image.get_rect()

        self.rect.x = x * TILESIZE * 2.5
        self.rect.y = y * TILESIZE * 2.5

        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)

        self.hitbox = self.rect.copy()

        self.head = CacadorHead(self.game, self)

        self.speed_mov = 2.5
        self.hp = 350.0

        self.cooldown_tiro = 5.0 * FPS  # Tempo para o jogador perceber o chefão
        self.estado = "NEUTRO"  # Formas do chefão: NEUTRO, PERSEGUINDO, ATACAR

        self.irritado = False  # Mudança de fase

    def take_damage(self, damage):
        self.hp -= damage

        if self.hp <= 0:
            self.game.cacador_derrotado = True
            self.kill()

        elif self.hp > 0 and self.hp <= 125.0:
            self.irritado = True

    def update(self):
        player = self.game.player

        vel = self.speed_mov * (1.2 if self.self.irritado else 1)

        if player is None:
            return

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery - 8

        distancia = math.sqrt(dx**2 + dy**2)

        # Normalização de vetor
        if distancia != 0:
            dx /= distancia
            dy /= distancia

        if self.estado == "PERSEGUINDO":
            if distancia >= 128:
                # Melhoria de movimentação 2.0
                obstaculo = [self.game.walls,
                             self.game.holes, self.game.blocks]

                self.rect.x += dx * vel

                for groupo in obstaculo:
                    colisao = pygame.sprite.spritecollide(
                        self, groupo, False)
                    for obstaculo in colisao:
                        if dx > 0:
                            self.rect.right = self.obstaculo.rect.left
                        elif dx < 0:
                            self.rect.left = self.obstaculo.rect.right

                self.rect.y += dy * vel

                for groupo in obstaculo:
                    colisao = pygame.sprite.spritecollide(
                        self, groupo, False)
                    for obstaculo in colisao:
                        if dy > 0:
                            self.rect.bottom = self.obstaculo.rect.top
                        elif dy < 0:
                            self.rect.top = self.obstaculo.rect.bottom

            else:
                self.estado = "ATACAR"

        elif self.estado == "ATACAR":
            qtd_proj = 8 if self.irritado else 5

            angulo_base = math.atan2(dy, dx)
            angulo_total_rad = math.radians(45.0)

            angulo_inicial = angulo_base - (angulo_total_rad / 2)

            passo_angular = angulo_total_rad / (qtd_proj - 1)

            # Intância dos projetéis
            for i in range(qtd_proj):
                angulo_total = angulo_inicial + (i * passo_angular)

                # Conversão de angulo em vetor
                dir_x = math.cos(angulo_total)
                dir_y = math.sin(angulo_total)

                ProjetilChefe(self.game, self.rect.centerx,
                              self.rect.centery, dir_x, dir_y)

            self.estado = "NEUTRO"
            self.cooldown_tiro = 2.5 * FPS

        elif self.estado == "NEUTRO":
            if self.cooldown_tiro > 0:
                self.cooldown_tiro -= 1
            else:
                self.estado = "PERSEGUINDO"

        if abs(dx) > abs(dy):
            if dx > 0:
                self.facing = "face_direita"
            else:
                self.facing = "face_esquerda"
        else:
            if dy > 0:
                self.facing = "face_baixo"
            else:
                self.facing = "face_cima"

        self.hitbox = self.rect.copy()


class CacadorHead(pygame.sprite.Sprite):
    def __init__(self, game, cacador, facing):
        self.game = game
        self.cacador = cacador
        self.cabeça_posicao = facing

        self._layer = PLAYER_HEAD_LAYER
        self.group = self.game.all_sprites

        # Objeto filho
        pygame.sprite.Sprite.__init__(self, self.group)

        self.width = TILESIZE
        self.height = TILESIZE

        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(GREEN)

        self.rect = self.image.get_rect()

    def update(self):
        self.rect.centerx = self.cacador.rect.centerx

        self.rect.centery = self.cacador.rect.centery - TILESIZE


class ProjetilChefe(pygame.sprite.Sprite):
    def __init__(self, game, chefe_x, chefe_y, dir_x, dir_y):
        self.game = game
        self._layer = PLAYER_LAYER
        self.group = self.game.all_sprites

        pygame.sprite.Sprite.__init__(self, self.group)

        self.image = pygame.Surface((16, 16))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect()

        self.pos_x = float(chefe_x)
        self.pos_y = float(chefe_y)
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)

        # Direção e velocidade
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.speed_proj = 8

        self.distance_traveled = 0
        self.max_dist = TILESIZE * 10

    def update(self):
        self.pos_x += self.dir_x * self.speed_proj
        self.pos_y += self.dir_y * self.speed_proj

        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)

        self.distance_traveled += self.speed_proj

        if self.distance_traveled >= self.max_dist:
            self.kill()

        if pygame.sprite.spritecollide(self, self.game.walls, False):
            self.kill()
