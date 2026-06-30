from turtle import pos

import pygame
import sys
import json
import os

from random import choices
from classes.config import *
from classes.salas import *
from classes.character import *
from classes.enemies import *
from classes.collectibles import *
from classes.hud import HUD


class Game:
    def __init__(self):
        pygame.init()
        self.estado = "MENU"
        self.resultado = None

        self.cacador_derrotado = False

        self.screen = pygame.display.set_mode((WIDTH_TELA, HEIGTH_TELA))
        self.clock = pygame.time.Clock()
        self.runnning = True

        self.espera_porta = 0
        # Tipo de cronômetro
        self.EVENTO_RELOGIO = pygame.USEREVENT + 1
        pygame.time.set_timer(self.EVENTO_RELOGIO, 1000)

        # Sistema de leitura do json
        diretorio_atual = os.path.dirname(__file__)
        caminho_json = os.path.join(
            diretorio_atual, 'assetes', 'dict_geral', 'items_passive.json')

        with open(caminho_json, 'r', encoding='utf-8') as f:
            self.banco_dados = json.load(f)

    # Método de sorteio
    def sortear_item(self, tipo_sala):
        itens_validos = []
        pesos = []

        for nome, dados in self.banco_dados.items():
            pool = dados.get("pool", "")
            qualidade = dados.get("qualidade", 1)

            if 'Fragmento' in nome:
                continue

            if tipo_sala in pool or 'tesouro - chefe' in pool:
                itens_validos.append((nome, dados))

            peso = 1.0 / max(qualidade, 0.1)
            pesos.append(peso)

        if not itens_validos:
            return None

        item_escolhido = choices(itens_validos, weights=pesos, k=1)
        return item_escolhido

    def troca_sala(self, novo_sala):
        # Atualiza a sala atual
        self.sala_atual = novo_sala

        # Maracação de visita ao entrar
        self.sala_atual.foi_visitada = True

        # Carrega o novo layout
        self.gerador.construir_sala(self.sala_atual)

    def new(self):
        # Quando começa um novo jogo
        self.playing = True

        self.all_sprites = pygame.sprite.LayeredUpdates()

        self.walls = pygame.sprite.LayeredUpdates()
        self.blocks = pygame.sprite.LayeredUpdates()
        self.holes = pygame.sprite.LayeredUpdates()
        self.pedestal = pygame.sprite.LayeredUpdates()

        self.doors = pygame.sprite.LayeredUpdates()

        self.projectiles = pygame.sprite.LayeredUpdates()

        self.enemies = pygame.sprite.LayeredUpdates()
        self.pickup = pygame.sprite.LayeredUpdates()

        self.player_status = {
            "hp_max": 30,
            "vida_extra": 0,
            "dano": 3.5,
            "multi_dmg": 1.0,
            "alcance": 8.5,
            "atq_speed": 1.0,
            "frequencia": 0.0,
            "speed": 1.0,
            "multi_spd": 1.0,
            "qtd_proj": 1,
            "homming": False,
            "pierce": False
        }

        self.player = Player(self, 10, 7, self.player_status)

        # Define quantas salas quer no andar
        self.gerador = MapGenerator(16, self)
        self.map, self.sala_atual = self.gerador.gerador()

        # Sala inicial descoberta por padrão
        self.sala_atual.foi_visitada = True

        # Começa o gerenciador do mini mapa
        self.minimapa = Minimap(self)

        # Carrega a sala inicial (Start Room)
        self.gerador.construir_sala(self.sala_atual)

        # Criação do hud depois do player, porque ele lê dados do self.player
        self.hud = HUD(self)

    def events(self):
        # Game loop event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.playing = False
                self.runnning = False
            if event.type == self.EVENTO_RELOGIO:
                if self.player is not None:
                    if self.player.tempo > 0:
                        self.player.tempo -= 1
                    else:
                        self.resultado = "TEMPO"
                        self.playing = False

    def uptade(self):
        self.all_sprites.update()

        if self.player:
            self.check_door_collisions()

            # Verfica se o jogador morreu, se sim, termina o jogo
            if self.player.hp <= 0:
                self.resultado = "MORREU"
                self.playing = False

            if not self.sala_atual.sala_limpa:
                if len(self.enemies) == 0:
                    self.sala_atual.sala_limpa = True

        if self.espera_porta > 0:
            self.espera_porta -= 1

        self.verificar_game_over()

    def draw(self):
        self.screen.fill(BLACK)
        # Textura do cenário
        self.all_sprites.draw(self.screen)

        if hasattr(self, 'minimapa'):
            self.minimapa.draw(self.screen)

        # Desenha vida, tempo e inventário "por cima"
        self.hud.draw(self.screen)

        self.clock.tick(FPS)
        pygame.display.update()

    def main(self):
        # Loop do jogo
        while self.playing:
            self.events()
            self.uptade()
            self.draw()
        self.runnning = False

    def intro_screen(self):
        pass

    def game_over(self):
        fonte = pygame.font.SysFont(None, 72)
        fonte2 = pygame.font.SysFont(None, 36)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.runnning = False
                    return

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.new()
                        return

                    if event.key == pygame.K_ESCAPE:
                        self.menu()
                        return

            self.screen.fill(BLACK)

            if self.resultado == "MORREU":
                texto = "VOCÊ MORREU"

            elif self.resultado == "TEMPO":
                texto = "O TEMPO ACABOU"

            elif self.resultado == "FUGIU":
                texto = "VOCÊ FUGIU DO CAÇADOR"

            elif self.resultado == "VITORIA":
                texto = "VOCÊ VENCEU"

            else:
                texto = "FIM DE JOGO"

            t1 = fonte.render(texto, True, (255, 255, 255))
            t2 = fonte2.render("ENTER - Jogar novamente",
                               True, (200, 200, 200))
            t3 = fonte2.render("ESC - Menu", True, (200, 200, 200))

            self.screen.blit(t1, (WIDTH_TELA//2 - t1.get_width()//2, 150))
            self.screen.blit(t2, (WIDTH_TELA//2 - t2.get_width()//2, 300))
            self.screen.blit(t3, (WIDTH_TELA//2 - t3.get_width()//2, 350))

            pygame.display.flip()

    def menu(self):
        fonte = pygame.font.SysFont(None, 72)
        fonte2 = pygame.font.SysFont(None, 40)

        while self.runnning:

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self.runnning = False
                    return

                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_RETURN:
                        self.new()
                        return

                    if event.key == pygame.K_ESCAPE:
                        self.runnning = False
                        return

            self.screen.fill((30, 30, 30))

            titulo = fonte.render("MEU ROGUELIKE", True, (255, 255, 255))
            jogar = fonte2.render("ENTER - Jogar", True, (220, 220, 220))
            sair = fonte2.render("ESC - Sair", True, (220, 220, 220))

            self.screen.blit(
                titulo, (WIDTH_TELA//2 - titulo.get_width()//2, 150))
            self.screen.blit(
                jogar, (WIDTH_TELA//2 - jogar.get_width()//2, 300))
            self.screen.blit(sair, (WIDTH_TELA//2 - sair.get_width()//2, 350))

            pygame.display.flip()

    def verificar_game_over(self):
        # Derrota por vida
        if self.player.hp <= 0:
            self.resultado = "MORREU"
            self.playing = False
            return

        # Derrota por tempo
        if self.player.tempo <= 0:
            self.resultado = "TEMPO"
            self.playing = False
            return

        # Vitória
        if self.player.chaves >= self.player.max_chaves and self.cacador_derrotado:
            self.resultado = "VITORIA"
            self.playing = False
            return

        # Derrotou por escapar sem derrotar o caçador
        if self.player.chaves >= self.player.max_chaves and not self.cacador_derrotado:
            self.resultado = "FUGIU"
            self.playing = False
            return

    def check_door_collisions(self):
        # O 'False' significa que a porta NÃO será deletada ao ser tocada
        hits = pygame.sprite.spritecollide(self.player, self.doors, False)

        if hits and not self.espera_porta > 0:
            # Pega a primeira porta que o jogador encostou
            porta_tocada = hits[0]
            direcao = porta_tocada.direcao

            # Verifica qual é a sala vizinha nessa direção
            nova_sala = self.sala_atual.vizinho[direcao]

            # Se a sala existir, fazemos a transição
            if nova_sala:
                self.troca_sala(nova_sala)

                if direcao == 'N':
                    self.player.rect.x = 10 * TILESIZE
                    self.player.rect.y = 12 * TILESIZE
                    self.espera_porta = 20

                elif direcao == 'S':
                    self.player.rect.x = 10 * TILESIZE
                    self.player.rect.y = 2 * TILESIZE
                    self.espera_porta = 20

                elif direcao == 'E':
                    self.player.rect.x = 2 * TILESIZE
                    self.player.rect.y = 7 * TILESIZE
                    self.espera_porta = 20

                elif direcao == 'O':
                    self.player.rect.x = 18 * TILESIZE
                    self.player.rect.y = 7 * TILESIZE
                    self.espera_porta = 20


g = Game()
g.intro_screen()
g.new()

while g.runnning:
    g.main()
    g.game_over()
    g.menu()

pygame.quit()
sys.exit()
