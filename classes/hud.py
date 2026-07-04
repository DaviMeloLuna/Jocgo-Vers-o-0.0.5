import math
import pygame

from classes.config import *
from collections import Counter


class HUD:
    def __init__(self, game):
        self.game = game
        self.fonte_tempo = pygame.font.SysFont('Arial', 26, bold=True)
        self.fonte_pequena = pygame.font.SysFont('Arial', 16, bold=True)
        self.fonte_letra_item = pygame.font.SysFont('Arial', 14, bold=True)

        self.altura_hud = 44
        self.margem = 10

        self.tamanho_coracao = 22
        self.espaco_coracao = 4
        self.vida_por_coracao = 10

        self.tamanho_icone_item = 16
        self.espaco_icone_item = 4

        self.max_colunas = 5
        self.max_linhas = 8

    def draw(self, screen):
        player = self.game.player
        if player is None:
            return

        self._desenhar_fundo(screen)
        self._desenhar_vida(screen, player)
        self._desenhar_tempo(screen, player)
        self._desenhar_inventario(screen, player)

    # Deixa o fundo da barra do hud quase transparente
    def _desenhar_fundo(self, screen):
        fundo = pygame.Surface((WIDTH_TELA, self.altura_hud))
        fundo.set_alpha(180)
        fundo.fill(DARK_GRAY)
        screen.blit(fundo, (0, 0))

        # Linha para separar o HUD do resto do jogo
        pygame.draw.line(
            screen, GRAY,
            (0, self.altura_hud), (WIDTH_TELA, self.altura_hud), 1
        )

    def _desenhar_vida(self, screen, player):
        x = self.margem
        y = (self.altura_hud - self.tamanho_coracao) // 2

        hp = max(0, player.hp)
        hp_max = max(player.hp_max, self.vida_por_coracao)

        total_coracoes = max(1, math.ceil(hp_max / self.vida_por_coracao))

        for i in range(total_coracoes):
            vida_neste_coracao = hp - (i * self.vida_por_coracao)

            if vida_neste_coracao >= self.vida_por_coracao:
                estado = 'cheio'
            elif vida_neste_coracao > 0:
                estado = 'meio'
            else:
                estado = 'vazio'

            pos_x = x + i * (self.tamanho_coracao + self.espaco_coracao)
            self._desenhar_coracao(screen, pos_x, y, estado)

    def _desenhar_coracao(self, screen, x, y, estado):
        tam = self.tamanho_coracao
        raio = tam // 4

        centro_esq = (x + raio, y + raio)
        centro_dir = (x + tam - raio, y + raio)
        pontos_triangulo = [
            (x + 1, y + raio),
            (x + tam - 1, y + raio),
            (x + tam // 2, y + tam - 1),
        ]

        def desenhar_forma(cor):
            pygame.draw.circle(screen, cor, centro_esq, raio)
            pygame.draw.circle(screen, cor, centro_dir, raio)
            pygame.draw.polygon(screen, cor, pontos_triangulo)

        cor_vazio = (70, 70, 70)
        cor_cheio = RED

        desenhar_forma(cor_vazio)

        if estado == 'cheio':
            desenhar_forma(cor_cheio)
        elif estado == 'meio':
            clip_anterior = screen.get_clip()
            screen.set_clip(pygame.Rect(x, y, tam // 2, tam))
            desenhar_forma(cor_cheio)
            screen.set_clip(clip_anterior)

        contorno = (20, 20, 20)
        pygame.draw.circle(screen, contorno, centro_esq, raio, 1)
        pygame.draw.circle(screen, contorno, centro_dir, raio, 1)
        pygame.draw.polygon(screen, contorno, pontos_triangulo, 1)

    # Mostra o tempo restante
    def _desenhar_tempo(self, screen, player):
        tempo = max(0, player.tempo)
        minutos = tempo // 60
        segundos = tempo % 60
        texto_tempo = f"{minutos:02}:{segundos:02}"

        if tempo > 30:
            cor = WHITE
        elif tempo > 10:
            cor = YELLOW
        else:
            cor = RED

        texto_render = self.fonte_tempo.render(texto_tempo, True, cor)
        rect_texto = texto_render.get_rect(
            center=(WIDTH_TELA // 2, self.altura_hud // 2)
        )
        screen.blit(texto_render, rect_texto)

    def _desenhar_inventario(self, screen, player):
        inventario = player.inventario

        x_direita = WIDTH_TELA - self.margem
        y = self.margem

        tem_chave = inventario.busca_chave()
        fragmentos = inventario.contar_fragmentos()

        if tem_chave:
            texto, cor = "Chave completa!", GOLD
        elif fragmentos > 0:
            texto, cor = f"Fragmentos: {fragmentos}/3", GRAY
        else:
            texto, cor = None, None

        if texto:
            texto_render = self.fonte_pequena.render(texto, True, cor)
            rect_texto = texto_render.get_rect(topright=(x_direita, y))
            screen.blit(texto_render, rect_texto)

        itens_passivos = [
            item for item in inventario.coisas if item.get('tipo') == 'passivo'
        ]

        contagem_itens = Counter(item.get('nome', '?')
                                 for item in itens_passivos)

        y_icones = self.margem + \
            (self.fonte_pequena.get_height() if texto else 0) + 4
        x_icone = x_direita

        contadores_fixos = [
            ('V', RED, inventario.contagem_vida),
            ('T', YELLOW, inventario.contagem_tempo),
        ]

        for letra, cor_icone, quantidade in contadores_fixos:
            if quantidade <= 0:
                continue

            x_icone -= self.tamanho_icone_item + self.espaco_icone_item
            if x_icone < self.margem:
                break

            rect_icone = pygame.Rect(
                x_icone, y_icones, self.tamanho_icone_item, self.tamanho_icone_item
            )
            self._desenhar_icone_fixo(
                screen, rect_icone, letra, cor_icone, quantidade)

        for nome, quantidade in reversed(list(contagem_itens.items())):
            x_icone -= self.tamanho_icone_item + self.espaco_icone_item

            if x_icone < self.margem:
                break

            rect_icone = pygame.Rect(
                x_icone, y_icones, self.tamanho_icone_item, self.tamanho_icone_item
            )

            self._desenhar_icone_item(screen, rect_icone, nome, quantidade)

            # Melhoria no HUD
            largura_matriz = self.max_colunas * \
                (self.tamanho_icone_item + self.espaco_icone_item)

            x_inicial_matriz = WIDTH_TELA - self.margem - largura_matriz

            coluna = 0
            linha = 0

            for nome, quantidade in reversed(list(contagem_itens.items())):
                if linha >= self.max_linhas:
                    break

                x_icone = x_inicial_matriz + coluna * \
                    (self.tamanho_icone_item + self.espaco_icone_item)
                y_icone = y_icones + linha * \
                    (self.tamanho_icone_item + self.espaco_icone_item)

                rect_icone = pygame.Rect(
                    x_icone, y_icone, self.tamanho_icone_item, self.tamanho_icone_item)
                self._desenhar_icone_item(screen, rect_icone, nome, quantidade)

                coluna += 1

                if coluna >= self.max_colunas:
                    coluna = 0
                    linha += 1

    def _desenhar_icone_item(self, screen, rect_icone, nome, quantidade):
        # Reworke no desenhar icone
        icone_surface = pygame.Surface(
            (rect_icone.width, rect_icone.height), pygame.SRCALPHA)

        icone_surface.fill((0, 255, 255, 100))

        screen.blit(icone_surface, rect_icone.topleft)

        letra = nome[0].upper() if nome else '?'

        letra_render = self.fonte_letra_item.render(letra, True, BLACK)
        letra_rect = letra_render.get_rect(center=rect_icone.center)
        screen.blit(letra_render, letra_rect)

        if quantidade > 1:
            texto_qtd = str(quantidade) if quantidade < 10 else "9+"
            qtd_render = self.fonte_letra_item.render(texto_qtd, True, WHITE)

            raio_badge = 8
            centro_badge = (rect_icone.right - 2, rect_icone.bottom - 2)

            pygame.draw.circle(screen, BLACK, centro_badge, raio_badge)
            pygame.draw.circle(screen, WHITE, centro_badge, raio_badge, 1)

            qtd_rect = qtd_render.get_rect(center=centro_badge)
            screen.blit(qtd_render, qtd_rect)

    def _desenhar_icone_fixo(self, screen, rect_icone, letra, cor_icone, quantidade):
        pygame.draw.rect(screen, cor_icone, rect_icone)
        pygame.draw.rect(screen, WHITE, rect_icone, 1)

        letra_render = self.fonte_letra_item.render(letra, True, BLACK)
        letra_rect = letra_render.get_rect(center=rect_icone.center)
        screen.blit(letra_render, letra_rect)

        texto_qtd = str(quantidade) if quantidade < 100 else "99+"
        qtd_render = self.fonte_letra_item.render(texto_qtd, True, WHITE)

        raio_badge = 8
        centro_badge = (rect_icone.right - 2, rect_icone.bottom - 2)

        pygame.draw.circle(screen, BLACK, centro_badge, raio_badge)
        pygame.draw.circle(screen, WHITE, centro_badge, raio_badge, 1)

        qtd_rect = qtd_render.get_rect(center=centro_badge)
        screen.blit(qtd_render, qtd_rect)
