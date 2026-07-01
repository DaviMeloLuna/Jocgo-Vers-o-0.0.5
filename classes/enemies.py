import pygame
import math

from classes.config import *


class BolaDeFogo(pygame.sprite.Sprite):  # classe para os projeteis da mula sem cabeça
    def __init__(self, game, x, y, dx, dy):
        self.game = game

        self._layer = PROJ_LAYER
        self.group = self.game.all_sprites

        pygame.sprite.Sprite.__init__(self, self.group)

        # quadrado laranja da bola de fogo
        self.image = pygame.Surface((16, 16))
        self.image.fill((255, 120, 0))

        self.rect = self.image.get_rect()
        self.rect.centerx = x  # onde a bola de fogo nasce
        self.rect.centery = y

        self.dx = dx  # direção do projétil, normalizada
        self.dy = dy

        self.speed = 5  # coloquei a velocidade 5, mas pode ser ajustada para ficar melhor

    def update(self):

        self.rect.x += self.dx * self.speed
        self.rect.y += self.dy * self.speed

        if self.rect.colliderect(self.game.player.rect):
            self.game.player.hp = max(
                0, self.game.player.hp - 5)  # dá dano ao jogador
            self.kill()  # destrói o projétil ao colidir com o jogador

        if pygame.sprite.spritecollide(self, self.game.walls, False):
            self.kill()

# Inimigo perseguidor


class MulaSemCabeca(pygame.sprite.Sprite):  # classe para a mula sem cabeça
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

        self.hitbox = self.rect.copy()

        self.speed = 2
        self.hp = 20.0

        self.cooldown_tiro = 0

    # a mula é um inimigo para testes
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.kill()

    def update(self):
        player = self.game.player

        if player is None:
            return

        # diferença de posições entre a mula sem cabeça e o jogador
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery

        distancia = math.sqrt(dx**2 + dy**2)

        # Só persegue se estiver longe
        if distancia > 120:
            # mov horizontal
            if self.rect.centerx < player.rect.centerx:
                self.rect.x += self.speed

            elif self.rect.centerx > player.rect.centerx:
                self.rect.x -= self.speed
            # mov vertical
            if self.rect.centery < player.rect.centery:
                self.rect.y += self.speed

            elif self.rect.centery > player.rect.centery:
                self.rect.y -= self.speed

        self.hitbox = self.rect.copy()

        if self.cooldown_tiro > 0:
            self.cooldown_tiro -= 1

        if self.cooldown_tiro == 0:

            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery

            distancia = math.sqrt(dx**2 + dy**2)

            # só atira a depender da distancia do jogador, para não ficar atirando a todo momento
            if distancia > 0 and distancia < 250:

                dx /= distancia  # normalização do vetor direção
                dy /= distancia

                BolaDeFogo(
                    self.game, self.rect.centerx, self.rect.centery, dx, dy)

                self.cooldown_tiro = 2 * FPS  # espera um tempo de 2 segundos antes de atirar novamente, limitando a quantidade de projéteis na tela e dando uma chance para o jogador se esquivar


# Criando a Iara:
class Poder(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game

        # Ajeitar a imagem do ataque
        self._layer = PROJ_LAYER
        self.group = self.game.all_sprites

        pygame.sprite.Sprite.__init__(self, self.group)

        self.image = pygame.Surface((16, 16))
        self.image.fill((255, 0, 0))

        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y

        # Ajeitar as distancias para ficar proporcional o quanto anda
        player = self.game.player
        distancia = ((self.rect.centerx - player.rect.centerx) **
                     2 + (self.rect.centery - player.rect.centery)**2)**0.5
        if distancia == 0:
            self.dx = 0
            self.dy = 0
        else:
            self.dx = (player.rect.centerx - self.rect.centerx)/distancia
            self.dy = (player.rect.centery - self.rect.centery)/distancia

        # Uma velocidade qualquer, podemos mudar depois qualquer coisa
        self.speed = 7

    def update(self):
        # Ele anda um pouco dependendo da velocidade
        self.rect.centerx += self.dx * self.speed
        self.rect.centery += self.dy * self.speed

        # Verifica se houve colisão ou com o jogador(para diminuir o tempo) ou com a parede (para desaparecer)
        if self.rect.colliderect(self.game.player.rect):
            # Diminui a princípio em 10 segundos, mas a gente pode mudar
            self.game.player.tempo -= 10
            self.kill()

        if pygame.sprite.spritecollide(self, self.game.walls, False):
            self.kill()


# Inimigo
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

        # Começamos com zero para poder atacar logo
        self.cooldown_tiro = 0
        self.hp = 30.0

        self.hitbox = self.rect.copy()

    def take_damage(self, damage):  # Só para não dar erro
        self.hp -= damage

        if self.hp <= 0:
            self.kill()

    def update(self):
        player = self.game.player

        # Calculando a distância para ajeitar o alcance:
        distancia = ((self.rect.x - player.rect.x) **
                     2 + (self.rect.y - player.rect.y)**2)**0.5

        # Primeiro vamos verificar se o jogador tá perto o suficiente
        if distancia < 128:  # Chutei um número qualquer para testar
            if self.cooldown_tiro == 0:  # para esperar um pouco antes de atacar
                Poder(self.game, self.rect.centerx, self.rect.centery)
                self.cooldown_tiro = 60  # Botei 1 segundo, mas podemos trocar depois
        if self.cooldown_tiro > 0:
            self.cooldown_tiro -= 1


class Curupira(pygame.sprite.Sprite):
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
            # aplica o efeito de atordoamento no jogador
            self.game.player.aplicar_atordoamento()
            self.kill()  # o curupira desaparece apos aplicar o efeito

        player = self.game.player

        if player is None:
            return

        # Irá perseguir o player, independentemente da distância do player
        # mov horizontal
        if self.rect.centerx < player.rect.centerx:
            self.rect.x += self.speed

        elif self.rect.centerx > player.rect.centerx:
            self.rect.x -= self.speed
        # mov vertical
        if self.rect.centery < player.rect.centery:
            self.rect.y += self.speed

        elif self.rect.centery > player.rect.centery:
            self.rect.y -= self.speed

        self.hitbox = self.rect.copy()


class Cacador(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = PLAYER_LAYER
        self.group = self.game.all_sprites, self.game.enemies

        pygame.sprite.Sprite.__init__(self, self.group)

        # Objeto Pai
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill((5, 52, 246))  # Azul Custumizado

        self.rect = self.image.get_rect()

        self.rect.x = x * TILESIZE * 2
        self.rect.y = y * TILESIZE * 2

        self.hitbox = self.rect.copy()

        self.head = CacadorHead(self.game, self)

        self.speed_mov = 2.5
        self.hp = 350.0

        self.cooldown_tiro = 5.0 * FPS  # Tempo para o jogador perceber o chefão
        self.estado = "NEUTRO"  # Formas do chefão: NEUTRO, PERSEGUINDO, ATACAR
        self.irritado = False

    def take_damage(self, damage):
        self.hp -= damage

        if self.hp <= 0:
            self.kill()
            self.game.cacador_derrotado = True
        elif self.hp > 0 and self.hp <= 125.0:
            self.irritado = True

    def update(self):
        player = self.game.player

        if player is None:
            return

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery

        distancia = math.sqrt(dx**2 + dy**2)

        if self.estado == "PERSEGUINDO":
            if distancia >= 128:
                # mov horizontal do chefe final
                if self.rect.centerx < player.rect.centerx:
                    if self.irritado:
                        self.rect.x += self.speed_mov * 1.2
                    else:
                        self.rect.x += self.speed_mov

                elif self.rect.centerx > player.rect.centerx:
                    if self.irritado:
                        self.rect.x -= self.speed_mov * 1.2
                    else:
                        self.rect.x -= self.speed_mov

                # mov vertical do chefe final
                if self.rect.centery < player.rect.centery:
                    if self.irritado:
                        self.rect.y += self.speed_mov * 1.2
                    else:
                        self.rect.y += self.speed_mov

                elif self.rect.centery > player.rect.centery:
                    if self.irritado:
                        self.rect.y -= self.speed_mov * 1.2
                    else:
                        self.rect.y -= self.speed_mov
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
                angulo_total = angulo_inicial + (1 * passo_angular)

                # Conversão de angulo em vetor
                dir_x = math.cos(angulo_total)
                dir_y = math.sin(angulo_total)

                Projetil_arma(self.game, self.rect.centerx,
                              self.rect.centery, dir_x, dir_y)

            self.estado = "NEUTRO"
            self.cooldown_tiro = 2.5 * FPS

        elif self.estado == "NEUTRO":
            if self.cooldown_tiro > 0:
                self.cooldown_tiro -= 1
            else:
                self.estado = "PERSEGUINDO"

        self.hitbox = self.rect.copy()


class Projetil_arma(pygame.sprite.Sprite):
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


class CacadorHead(pygame.sprite.Sprite):
    def __init__(self, game, cacador):
        self.game = game
        self.cacador = cacador

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
        self.rect.centerx = self.player.rect.centerx

        self.rect.centery = self.player.rect.centery - TILESIZE
