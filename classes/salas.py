import pygame
import random
import json
import os

from classes.config import *
from classes.collectibles import *

from classes.enemies import MulaSemCabeca, Iara, Curupira, Cacador

diretorio_atual = os.path.dirname(__file__)

# Volta uma pasta ('..') e procura o arquivo JSON
caminho_arquivo = os.path.join(
    diretorio_atual, '..', 'assetes', 'dict_geral', 'rooms_assetes.json')

with open(caminho_arquivo, 'r') as file:
    ROOMS_ASSETS = json.load(file)


class RoomNode:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vizinho = {'N': None, 'S': None, 'E': None, 'O': None}

        self.foi_visitada = False
        self.sala_limpa = False

        self.chefe_spaw = False

        self.tipo = 'normal'  # Pode ser: 'normal', 'chefe', 'tesouro', 'inicial'

        self.room_asset_id = "sala"

        self.item_nome = None
        self.item_dados = None
        self.item_coletado = False


class MapGenerator:
    def __init__(self, num_rooms, game):
        self.num_rooms = num_rooms
        self.game = game

        self.grid = {}
        self.mapa = []

        self.largura_sala = 21
        self.altura_sala = 15

        self.pools_de_salas = {}
        self.separar_salas_por_tipo()

    def separar_salas_por_tipo(self):
        for salas_id, dados in ROOMS_ASSETS.items():
            tipo = dados.get("tipo", "normal")

            if tipo not in self.pools_de_salas:
                self.pools_de_salas[tipo] = []

            self.pools_de_salas[tipo].append(salas_id)

    def gerador(self):
        sala_inicial = RoomNode(0, 0)

        sala_inicial.tipo = "inicial"
        sala_inicial.room_asset_id = 'sala_inicial'

        self.grid[(0, 0)] = sala_inicial
        salas_criadas = 1

        while salas_criadas <= self.num_rooms:
            rx, ry = random.choice(list(self.grid.keys()))

            direcao = [
                ("N", 0, -1, "S"),
                ('S', 0, 1, 'N'),
                ('E', 1, 0, 'O'),
                ('O', -1, 0, 'E')
            ]

            d_nome, dx, dy, op_nome = random.choice(direcao)

            novo_x, novo_y = rx + dx, ry + dy

            if (novo_x, novo_y) not in self.grid:
                nova_sala = RoomNode(novo_x, novo_y)
                self.grid[(novo_x, novo_y)] = nova_sala

                self.grid[(rx, ry)].vizinho[d_nome] = nova_sala
                nova_sala.vizinho[op_nome] = self.grid[(rx, ry)]

                salas_criadas += 1

        for coords, sala in self.grid.items():
            if coords != (0, 0):
                sala.tipo = "normal"
                sala.room_asset_id = "sala"
            self.mapa.append(sala)

        # Algoritmo BFS para definir as salas do chefe por distancia
        distancia = {}
        fila = [sala_inicial]
        distancia[sala_inicial] = 0

        while fila:
            sala_atual = fila.pop(0)
            dist_atual = distancia[sala_atual]

            for vizinha in sala_atual.vizinho.values():
                if vizinha and vizinha not in distancia:
                    distancia[vizinha] = dist_atual + 1
                    fila.append(vizinha)

        salas_ordenadas = sorted(
            distancia.items(), key=lambda x: x[1], reverse=True)

        # Sala dos chefes

        salas_chefe = []

        for sala, dist in salas_ordenadas:
            if sala == sala_inicial:
                continue

            muito_perto = False
            for chefe in salas_chefe:
                distancia_abs = abs(sala.x - chefe.x) + abs(sala.y - chefe.y)
                qtd_vizinhos = sum(
                    1 for v in sala.vizinho.values() if v is not None)

                if distancia_abs <= 2 or qtd_vizinhos != 1:
                    muito_perto = True
                    break

            if not muito_perto:
                sala.tipo = "chefe"
                sala.room_asset_id = 'sala_chefe'  # Mapeia para a sala de chefe do JSON
                salas_chefe.append(sala)

            if len(salas_chefe) >= 3:
                break

        # Filtro de salas do tesouro
        candidata_tesouro = []

        for sala in self.mapa:
            if sala == sala_inicial or sala in salas_chefe:
                continue

            qtd_vizinhos = sum(
                1 for v in sala.vizinho.values() if v is not None)
            if qtd_vizinhos == 1:
                candidata_tesouro.append(sala)

        # Garantia de duas salas
        sala_tesouro = random.sample(
            candidata_tesouro, min(2, len(candidata_tesouro)))

        for sala in sala_tesouro:
            sala.tipo = 'tesouro'
            sala.room_asset_id = 'sala_tesouro'  # Mapeia para a sala do tesouro do json

        for sala in self.grid.values():
            tipo_da_sala = sala.tipo

            # Se o tipo da sala existir no JSON, escolhe uma aleatória daquele tipo
            if tipo_da_sala in self.pools_de_salas:
                sala.room_asset_id = random.choice(
                    self.pools_de_salas[tipo_da_sala])
            else:
                sala.room_asset_id = random.choice(
                    self.pools_de_salas.get("normal", ["sala1"]))

        # Filtro de sala do chefão
        cantidata_final = []

        for sala in self.mapa:
            if sala == sala_inicial or sala in salas_chefe or sala in sala_tesouro:
                continue
            qtd_vizinhos = sum(1 for v in sala.vizinho.values() if v is None)

            if qtd_vizinhos == 2 or qtd_vizinhos == 3:
                cantidata_final.append(sala)

        sala_final = random.sample(
            cantidata_final, min(1, len(cantidata_final)))

        for sala in sala_final:
            sala.tipo = 'chefe final'
            sala.room_asset_id = 'sala_chefe_final'

        return self.mapa, sala_inicial

    def limpar_sala_atual(self):
        # Limpa a tela ao trocar de sala
        for sprite in list(self.game.all_sprites):
            if sprite != self.game.player and sprite.__class__.__name__ != 'PlayerHead':
                sprite.kill()

    def construir_sala(self, room_node):
        # Usa o Json para construir a sala por elemento
        self.limpar_sala_atual()

        dados_sala = ROOMS_ASSETS[room_node.room_asset_id]

        # Contrução das paredes externas e portas
        for y in range(self.altura_sala):
            for x in range(self.largura_sala):
                if x == 0 or x == self.largura_sala - 1 or y == 0 or y == self.altura_sala - 1:
                    # Pergunta sobre a existência da porta por vizinho
                    e_porta = False

                    # Respota se tiver ao Norte (cima)
                    if y == 0 and x == self.largura_sala // 2 and room_node.vizinho["N"]:
                        Door(self.game, x, y, 'N')
                        e_porta = True
                    # Respota se tiver ao Sul (baixo)
                    elif y == self.altura_sala - 1 and x == self.largura_sala // 2 and room_node.vizinho['S']:
                        Door(self.game, x, y, 'S')
                        e_porta = True
                    # Respota se tiver ao Oeste (esquerda)
                    elif x == 0 and y == self.altura_sala // 2 and room_node.vizinho['O']:
                        Door(self.game, x, y, 'O')
                        e_porta = True
                    # Respota se tiver ao Leste (direita)
                    elif x == self.largura_sala - 1 and y == self.altura_sala // 2 and room_node.vizinho['E']:
                        Door(self.game, x, y, 'E')
                        e_porta = True

                    if not e_porta:
                        Wall(self.game, x, y)

        # Carregar pedras
        if "pedra" in dados_sala:
            for pos in dados_sala["pedra"]:
                Block(self.game, pos[0], pos[1])

        # Carregar buracos
        if "buraco" in dados_sala:
            for pos in dados_sala["buraco"]:
                Block(self.game, pos[0], pos[1])

        # Carregar paredes além dos que limitam
        if "parede" in dados_sala:
            for pos in dados_sala["parede"]:
                Wall(self.game, pos[0], pos[1])

        # Carrega o alçapão se a condição das chaves for verdadeira
        if "alcapao" in dados_sala:
            pos = dados_sala["alcapao"]

            if self.game.player.chaves == self.game.max_chaves:
                Alcapao(self.game, pos[0], pos[1])

        # Para a sala do tessouro e chefe depois de vencé-lo
        if "pedestal" in dados_sala:
            pos = dados_sala["pedestal"]  # Formato [10, 7] do JSON
            Pedestal(self.game, pos[0], pos[1])

            if room_node.tipo == 'tesouro' and not room_node.item_coletado:
                # Sorteia o item apenas uma vez que entrar
                if room_node.item_nome is None:
                    item_sorteado = self.game.sortear_item('tesouro')
                    if item_sorteado:
                        room_node.item_nome, room_node.item_dados = item_sorteado[0]

                # Carrega o item na tela
                if room_node.item_nome:
                    ItemPassivo(
                        self.game, pos[0], pos[1], room_node.item_nome, room_node.item_dados, room_node)

            # Criação do pedestal assim que o chefe for derrotado
            if room_node.tipo == 'chefe' and room_node.sala_limpa:
                Pedestal(self.game, pos[0], pos[1])

                if not room_node.item_coletado and room_node.item_nome:
                    ItemPassivo(
                        self.game, pos[0], pos[1], room_node.item_nome, room_node.item_dados, room_node)

        # Posicionar o jogador se for a sala inicial:
        if room_node.tipo == "inicial" and "player" in dados_sala:
            pos = dados_sala["player"]
            self.game.player.rect.x = pos[0] * TILESIZE
            self.game.player.rect.y = pos[1] * TILESIZE

        # Geração de inimigo, se for sala de chefe, o inimigo tem mais vida (4x mais)
        if 'inimigo' in dados_sala and not room_node.sala_limpa:
            inimigo_pos = dados_sala['inimigo']

            # Caso tenha mais de um inimigo no dicionário do Json
            if inimigo_pos and not isinstance(inimigo_pos[0], list):
                inimigo_pos = [inimigo_pos]

            for pos in inimigo_pos:
                classe_inimigo = random.choice([MulaSemCabeca, Iara, Curupira])
                inimigo_intanciado = classe_inimigo(self.game, pos[0], pos[1])

                if room_node.tipo == 'chefe':
                    inimigo_intanciado.hp = inimigo_intanciado.hp * 4

        # Geração do caçador e inicio da batalha final
        if room_node.tipo == 'chefe final':
            # Verifica os fragmentos da chave
            if (self.game.player.chaves >= self.game.max_chaves and not room_node.chefe_spaw and not self.game.cacador_derrotado):
                Cacador(self.game, 10, 7)
                self.chefe_spaw = True
                self.game.em_batalha_final = True  # Trava as portas


class Minimap:
    def __init__(self, game):
        self.game = game

        caminho_sprite = os.path.join(os.path.dirname(
            __file__), '..', 'assetes', 'sprites', 'tileset_mapa.png')

        try:
            self.spritesheet = pygame.image.load(
                caminho_sprite).convert_alpha()
            self.spritesheet.set_alpha(OPACIDADE)
        except pygame.error:
            self.spritesheet = pygame.Surface((32, 32))
            self.spritesheet.fill((255, 0, 255))

        # Recorta os quadrantes da imagem original (16x16 pixels cada)
        self.sala_escura = pygame.transform.scale(
            self.spritesheet.subsurface(pygame.Rect(0, 0, 16, 16)), (16, 16))

        self.sala_clara = pygame.transform.scale(
            self.spritesheet.subsurface(pygame.Rect(16, 0, 16, 16)), (16, 16))

        self.caveira = pygame.transform.scale(
            self.spritesheet.subsurface(pygame.Rect(0, 16, 16, 16)), (16, 16))

        self.diamante = pygame.transform.scale(
            self.spritesheet.subsurface(pygame.Rect(16, 16, 16, 16)), (16, 16))

        # Posição central de renderização do mini mapa na tela (Canto superior direito)
        self.centro_hud_x = 80
        self.centro_hud_y = 60

        self.tamanho_sala = 16

    def draw(self, screen):
        sala_atual = self.game.sala_atual
        if not sala_atual:
            return

        # Só exibe salas já visitadas ou salas adjacentes a uma visitada
        salas_visiveis = set()
        for sala in self.game.map:
            if sala.foi_visitada:
                salas_visiveis.add(sala)
                for vizinha in sala.vizinho.values():
                    if vizinha:
                        salas_visiveis.add(vizinha)

        # Renderiza a malha de salas mapeadas
        for sala in self.game.map:
            if sala not in salas_visiveis:
                continue

            # Calcula o deslocamento (offset) baseado na posição estrutural em relação à sala atual
            dx = sala.x - sala_atual.x
            dy = sala.y - sala_atual.y

            pos_x = self.centro_hud_x + (dx * self.tamanho_sala)
            pos_y = self.centro_hud_y + (dy * self.tamanho_sala)

            # Desenha o fundo da sala correspondente (Visitada vs Não Visitada)
            if sala.foi_visitada:
                screen.blit(self.sala_clara, (pos_x, pos_y))
            else:
                screen.blit(self.sala_escura, (pos_x, pos_y))

            # Insere os marcadores por cima (Apenas se a sala for do tipo especial correspondente)
            if sala.tipo == 'chefe':
                screen.blit(self.caveira, (pos_x, pos_y))
            elif sala.tipo == 'tesouro':
                screen.blit(self.diamante, (pos_x, pos_y))

        # Desenha uma borda branca sutil piscando/fixa na sala atual onde o jogador se encontra
        pygame.draw.rect(screen, (255, 255, 255), (self.centro_hud_x,
                         self.centro_hud_y, self.tamanho_sala, self.tamanho_sala), 1)


class Pedestal(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self.has_item = True

        self._layer = DETAILS_LAYER
        self.groups = (self.game.all_sprites, self.game.pedestal)

        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        # Correção de bug: ao entrar na sala do tesouro o jogo fecha
        caminho_sprite = os.path.join(os.path.dirname(
            __file__), '..', 'assetes', 'sprites', 'pedestal_placeholder.png')

        self.image = pygame.image.load(caminho_sprite).convert_alpha()

        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x, self.y)

        if not self.has_item:
            self.kill()


class Wall(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = PLAYER_LAYER
        self.groups = (self.game.all_sprites, self.game.walls)

        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        self.width = TILESIZE
        self.height = TILESIZE

        self.image = pygame.Surface([self.width, self.height])
        # Marrom em RGB
        self.image.fill((150, 75, 00))

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y


class Block(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = PLAYER_LAYER
        self.group = self.game.all_sprites, self.game.blocks

        pygame.sprite.Sprite.__init__(self, self.group)

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        self.width = TILESIZE
        self.height = TILESIZE

        self.image = pygame.Surface([self.width, self.height])
        # Marrom em RGB
        self.image.fill((146, 142, 133))

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y


class Hole(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = PLAYER_LAYER
        self.group = self.game.all_sprites, self.game.holes

        pygame.sprite.Sprite.__init__(self, self.group)

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        self.width = TILESIZE
        self.height = TILESIZE

        self.image = pygame.Surface([self.width, self.height])
        # Cinza em RGB
        self.image.fill((50, 50, 50))

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y


class Door(pygame.sprite.Sprite):
    def __init__(self, game, x, y, direcao):
        self.game = game
        self._layer = DOOR_LAYER
        self.group = self.game.all_sprites, self.game.doors

        pygame.sprite.Sprite.__init__(self, self.group)

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        self.direcao = direcao

        if self.direcao in ['O', 'E']:
            self.width = 32
            self.height = 48
        else:
            self.width = 48
            self.height = 32

        self.image = pygame.Surface([self.width, self.height])
        # Cinza em RGB
        self.image.fill((139, 139, 139))

        self.rect = self.image.get_rect()

        if self.direcao == 'O':
            self.rect.midleft = (self.x, self.y + TILESIZE // 2)

        elif self.direcao == 'E':
            self.rect.midright = (self.x + TILESIZE, self.y + TILESIZE // 2)

        elif self.direcao == 'N':
            self.rect.midtop = (self.x + TILESIZE // 2, self.y)

        elif self.direcao == 'S':
            self.rect.midbottom = (self.x + TILESIZE // 2, self.y + TILESIZE)


class Alcapao(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = PLAYER_LAYER
        self.group = self.game.all_sprites, self.game.alcapao

        pygame.sprite.Sprite.__init__(self, self.group)

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        self.width = TILESIZE
        self.height = TILESIZE

        self.image = pygame.Surface([self.width, self.height])
        # Marrom em RGB
        self.image.fill((108, 60, 12))

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
