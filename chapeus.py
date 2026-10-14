"""
Chapéus do Ribbat: comprados na loja com as moscas que ele junta nas fases.

Cada chapéu é desenhado em cima da cabeça. As coordenadas são "do sapo": (0, 0) = topo da cabeça,
x pra frente (pra onde ele olha), y pra baixo. Tudo é multiplicado pela escala do sapo.
"""
import math

import pygame

from config import *  # noqa: F401,F403

# (nome, preço em moscas)
CHAPEUS = (
    ("nenhum", 0),
    ("bone", 10),
    ("folha", 15),
    ("gato", 25),
    ("besouro", 35),
    ("coroa", 50),
    ("pena", 70),
    ("cartola", 100),
)
PRECO = dict(CHAPEUS)
TOPO = (27, 12.5)           # onde o chapéu senta: atrás do olho, na rampa da cabeça (sistema das orelhinhas de coelho)
INCLINA = 0.4               # tomba pra trás seguindo a curva das costas (~23°), pedido do Gomes


def desenhar(tela, nome, cx, base, d, escala, sq=1.0, pose="parado", inclina=INCLINA):
    """Desenha o chapéu no sapo que está com os pés em `base` e o meio em `cx`."""
    if not nome or nome == "nenhum":
        return
    hx = cx + d * (TOPO[0] - 30) * escala
    hy = base - (46 - TOPO[1]) * escala * sq
    k = escala
    ca, sa = math.cos(inclina), math.sin(inclina)

    def P(x, y):
        x, y = x * ca + y * sa, -x * sa + y * ca        # gira: o topo tomba pras costas
        return hx + d * x * k, hy + y * k

    def pol(pts, cor, borda=True):
        q = [P(*p) for p in pts]
        if borda:
            pygame.draw.polygon(tela, PRETO, q, max(1, int(2 * k)))
        pygame.draw.polygon(tela, cor, q)
        if borda:
            pygame.draw.polygon(tela, PRETO, q, max(1, int(1.4 * k)))

    def elip(x, y, rx, ry, cor):
        r = pygame.Rect(0, 0, rx * 2 * k, ry * 2 * k)
        r.center = P(x, y)
        pygame.draw.ellipse(tela, PRETO, r.inflate(3 * k, 3 * k))
        pygame.draw.ellipse(tela, cor, r)

    if nome == "bone":                                           # boné vermelho com aba pra frente
        pol([(-11, 1), (-10, -6), (-4, -10), (4, -10), (10, -6), (11, 1)], (210, 50, 50))
        pol([(8, 1), (22, 2), (20, 4), (8, 3)], (170, 30, 30))
        elip(0, -10, 2, 1.5, (250, 240, 230))
    elif nome == "folha":                                        # folhinha de vitória-régia
        pts = [(math.cos(a) * 15, -2 + math.sin(a) * 4) for a in [i / 16 * math.tau for i in range(17)]]
        pol(pts[:15] + [(0, -2)], (80, 160, 80))
        pygame.draw.line(tela, (50, 110, 50), P(0, -2), P(-10, -3), max(1, int(1.5 * k)))
        pygame.draw.line(tela, (60, 120, 50), P(2, -4), P(4, -11), max(1, int(2 * k)))   # cabinho
    elif nome == "gato":                                         # orelhas de gato preto
        for x0 in (-9, 5):
            pol([(x0 - 4, 0), (x0, -13), (x0 + 5, 0)], (30, 28, 34))
            pol([(x0 - 1.5, -1), (x0 + 0.3, -8), (x0 + 2.5, -1)], (240, 150, 170), borda=False)
    elif nome == "besouro":                                      # capacete de besouro com chifre
        pol([(-12, 2), (-11, -6), (-5, -10), (5, -10), (11, -6), (12, 2)], (110, 54, 26))
        pol([(-4, -9), (0, -10), (4, -9), (10, -18), (14, -24), (12, -16), (6, -7)], (70, 32, 14))
        pygame.draw.line(tela, (200, 130, 80), P(-7, -6), P(-2, -8), max(1, int(2 * k)))
    elif nome == "coroa":                                        # coroa da Rainha
        pol([(-10, 1), (-11, -10), (-6, -5), (0, -13), (6, -5), (11, -10), (10, 1)], (246, 200, 70))
        for x, cor in ((-6, (200, 40, 60)), (0, (60, 120, 220)), (6, (200, 40, 60))):
            elip(x, -2, 1.6, 1.6, cor)
    elif nome == "pena":                                         # faixa com a pena da Águia
        pol([(-11, 0), (11, 0), (11, -4), (-11, -4)], (190, 40, 40))
        pol([(-6, -3), (-14, -22), (-10, -26), (-4, -16), (-3, -3)], (248, 246, 240))
        pygame.draw.line(tela, (120, 110, 100), P(-4, -3), P(-11, -23), max(1, int(1.2 * k)))
        pol([(-11, -22), (-14, -22), (-10, -26)], (60, 44, 30), borda=False)
    elif nome == "cartola":                                      # cartola chique
        pol([(-14, 1), (14, 1), (14, -2), (-14, -2)], (30, 28, 34))
        pol([(-9, -1), (-9, -22), (9, -22), (9, -1)], (30, 28, 34))
        pol([(-9, -5), (9, -5), (9, -9), (-9, -9)], (200, 40, 50), borda=False)


def icone(tela, nome, x, y, k=1.6):
    """O chapéu sozinho (pra loja)."""
    if nome == "nenhum":
        pygame.draw.circle(tela, (200, 60, 60), (int(x), int(y - 6)), int(10 * k / 1.6), 3)
        pygame.draw.line(tela, (200, 60, 60), (x - 7 * k / 1.6, y + 1), (x + 7 * k / 1.6, y - 13), 3)
        return
    desenhar(tela, nome, x - (TOPO[0] - 30) * k, y + (46 - TOPO[1]) * k, 1, k, inclina=0)
