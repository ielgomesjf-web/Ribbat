"""Desenhos do Formigueiro (a Colônia): túneis, ovos, jardim de fungo, melado, buracos, formiga guerreira."""
import math
import random

import pygame

from config import *  # noqa: F401,F403
from entidades import R

TERRA_F = (92, 64, 44)
TERRA_F_ESC = (62, 42, 28)
TERRA_F_CLARA = (140, 104, 72)
MEL = (226, 150, 40)


def criar_fundo():
    fundo = pygame.Surface((LARGURA, ALTURA))
    for y in range(ALTURA):
        k = y / ALTURA
        fundo.fill([int(a + (b - a) * k) for a, b in zip((46, 31, 22), (78, 54, 38))], R(0, y, LARGURA, 1))
    rnd = random.Random(31)
    for _ in range(40):                              # textura de terra
        pygame.draw.circle(fundo, (58, 40, 28), (rnd.randint(0, LARGURA), rnd.randint(0, ALTURA)), rnd.randint(4, 14))
    # camada do fundo: túneis e câmaras (mais escuros, mas sem exagero)
    tuneis = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    for _ in range(6):
        x, y = rnd.randint(40, LARGURA - 40), rnd.randint(140, 400)
        pts = [(x + i * 46, y + math.sin(i * 0.8 + x) * 24) for i in range(-3, 4)]
        pygame.draw.lines(tuneis, (30, 20, 14, 150), False, pts, 20)
        pygame.draw.ellipse(tuneis, (30, 20, 14, 170), R(x - 40, y - 22, 80, 46))
        if rnd.random() < 0.6:                       # montinho de ovos na câmara
            for k, (ex, ey) in enumerate(((-12, 8), (0, 8), (12, 8), (-6, 0), (6, 0), (0, -8))):
                pygame.draw.ellipse(tuneis, (220, 212, 190, 200), R(x + ex - 5, y + ey - 4, 10, 13))
                pygame.draw.ellipse(tuneis, (250, 246, 232, 200), R(x + ex - 3, y + ey - 3, 4, 4))
    # camada do meio: jardins de fungo (as formigas plantam fungo de verdade!)
    fungos = pygame.Surface((LARGURA, 200), pygame.SRCALPHA)
    for _ in range(6):
        x = rnd.randint(30, LARGURA - 30)
        for k in range(22):
            fx, fy = x + rnd.randint(-26, 26), 150 + rnd.randint(-22, 10)
            pygame.draw.circle(fungos, (210, 206, 178, 90), (fx, fy), rnd.randint(2, 5))
        pygame.draw.ellipse(fungos, (230, 226, 200, 25), R(x - 46, 110, 92, 60))
    return {"fundo": fundo, "tuneis": tuneis, "fungos": fungos}


def desenhar_fundo(tela, f, cam, t):
    tela.blit(f["fundo"], (0, 0))
    x = -((cam * 0.15) % LARGURA)
    tela.blit(f["tuneis"], (x, 0))
    tela.blit(f["tuneis"], (x + LARGURA, 0))
    x = -((cam * 0.4) % LARGURA)
    tela.blit(f["fungos"], (x, 260))
    tela.blit(f["fungos"], (x + LARGURA, 260))


def criar_tiles():
    rnd = random.Random(13)

    def dentro():
        s = pygame.Surface((TILE, TILE))
        s.fill(TERRA_F)
        for _ in range(8):                          # grãozinhos de terra
            pygame.draw.circle(s, rnd.choice([TERRA_F_ESC, TERRA_F_CLARA]), (rnd.randint(2, 29), rnd.randint(2, 29)),
                               rnd.randint(1, 2))
        return s

    topo = dentro()
    pygame.draw.rect(topo, TERRA_F_CLARA, (0, 0, TILE, 4))
    pygame.draw.line(topo, (170, 132, 96), (0, 0), (TILE, 0), 2)
    for x in (6, 17, 26):
        pygame.draw.circle(topo, (180, 150, 110), (x, 2), 2)   # grão de areia carregado pelas formigas
    raiz = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    pygame.draw.rect(raiz, (70, 46, 28), (0, 2, TILE, 13), border_radius=6)
    pygame.draw.rect(raiz, (120, 84, 52), (0, 1, TILE, 10), border_radius=5)
    pygame.draw.line(raiz, (90, 62, 38), (4, 6), (20, 7), 2)
    pygame.draw.line(raiz, (150, 110, 70), (2, 2), (28, 2), 1)
    return {"grama": topo, "terra": [dentro() for _ in range(3)], "madeira": raiz}


def desenhar_melado(tela, r, t, semente):
    """Melado (o 'mel' que as formigas guardam): gruda e deixa lento."""
    pygame.draw.ellipse(tela, (160, 96, 20), R(r.x - 4, r.y + 2, r.width + 8, r.height + 4))
    pygame.draw.ellipse(tela, MEL, R(r.x - 2, r.y, r.width + 4, r.height))
    pygame.draw.ellipse(tela, (255, 220, 140), R(r.x + 6 + math.sin(t * 2 + semente) * 2, r.y + 2, 10, 4))
    if semente % 2 == 0:                       # gota pingando
        k = (t * 0.7 + semente * 0.3) % 1
        pygame.draw.circle(tela, MEL, (int(r.centerx), int(r.bottom + k * 10)), 3)


def desenhar_buraco(tela, x, chao, t):
    pygame.draw.ellipse(tela, TERRA_F_CLARA, R(x - 30, chao - 14, 60, 18))
    pygame.draw.ellipse(tela, (16, 10, 6), R(x - 20, chao - 10, 40, 12))
    for i in range(6):                         # grãozinhos em volta
        a = i / 6 * math.tau
        pygame.draw.circle(tela, (170, 130, 90), (int(x + math.cos(a) * 30), int(chao - 6 + math.sin(a) * 6)), 2)
    if int(t * 3 + x) % 4 == 0:                # anteninha aparecendo
        pygame.draw.line(tela, (70, 24, 14), (x - 4, chao - 6), (x - 8, chao - 14), 2)
        pygame.draw.line(tela, (70, 24, 14), (x + 4, chao - 6), (x + 8, chao - 14), 2)


def desenhar_tampado(tela, x, chao):
    pygame.draw.ellipse(tela, (120, 88, 60), R(x - 26, chao - 10, 52, 14))


def desenhar_guerreira(tela, g, ox, oy, t):
    """Formiga guerreira (soldado alado): desenhada pelo formigas.py com a anatomia certa."""
    import formigas as FA
    x, y, d = g.x - ox, g.y - oy, g.dir
    mirando = g.estado == "mirando"
    bate = abs(math.sin(t * (42 if g.estado != "voltando" else 26)))
    olho = (255, 70, 40) if mirando and int(t * 16) % 2 == 0 else None
    abre = 0.9 if g.estado in ("mirando", "investindo") else 0.3
    s = FA.sprite_guerreira(t, bate=bate, abre=abre, olho=olho)
    if d < 0:
        s = pygame.transform.flip(s, True, False)
    if g.estado == "investindo":
        ang = -math.degrees(math.atan2(g.vy, abs(g.vx) + 0.01)) * (1 if d > 0 else -1)
        s = pygame.transform.rotate(s, ang)
        for i in range(3):                                               # rastro de velocidade
            pygame.draw.line(tela, (255, 230, 200), (x - g.vx * 0.03 * (i + 1), y - g.vy * 0.03 * (i + 1) - 4 + i * 4),
                             (x - g.vx * 0.06 * (i + 1), y - g.vy * 0.06 * (i + 1) - 4 + i * 4), 2)
    tremor = math.sin(t * 60) * 2 if mirando else 0
    tela.blit(s, s.get_rect(center=(x + tremor, y)))
    if mirando:                                                          # aviso: "!" em cima
        pygame.draw.circle(tela, PRETO, (int(x), int(y - 36)), 9)
        pygame.draw.circle(tela, (255, 90, 60), (int(x), int(y - 36)), 7)
        pygame.draw.rect(tela, BRANCO, R(x - 1.5, y - 41, 3, 7))
        pygame.draw.circle(tela, BRANCO, (int(x), int(y - 31)), 2)


def desenhar_torrao(tela, r, semente):
    """Torrão de terra socada tampando o túnel (quebra com a investida)."""
    rnd = random.Random(semente)
    pygame.draw.rect(tela, TERRA_F_ESC, r.inflate(6, 2), border_radius=12)
    pygame.draw.rect(tela, (120, 86, 58), r, border_radius=10)
    for _ in range(14):
        pygame.draw.circle(tela, rnd.choice([TERRA_F_ESC, TERRA_F_CLARA, (160, 124, 88)]),
                           (rnd.randint(r.left + 6, r.right - 6), rnd.randint(r.top + 6, r.bottom - 6)), rnd.randint(2, 5))
    pygame.draw.lines(tela, TERRA_F_ESC, False, [(r.centerx - 8, r.top + 4), (r.centerx + 2, r.centery), (r.centerx - 4, r.bottom - 4)], 2)


def desenhar_camara_real(tela, x, base, t, k=1.0):
    """Entrada da câmara real: arco enfeitado com grãos e folhas, e alguém ENORME lá dentro..."""
    bw, bh = 170 * k, 150 * k
    arco = [(x - bw / 2, base)] + [(x + math.cos(math.pi - i / 18 * math.pi) * bw / 2,
                                    base - math.sin(math.pi - i / 18 * math.pi) * bh) for i in range(1, 18)] + [(x + bw / 2, base)]
    pygame.draw.polygon(tela, (140, 104, 72), [(px * 1.0 + (px - x) * 0.18, py - (base - py) * 0.12) for px, py in arco])
    pygame.draw.polygon(tela, (12, 8, 6), arco)
    for i, (px, py) in enumerate(arco[1:-1]):                # enfeite de folhinhas e sementes
        if i % 2 == 0:
            pygame.draw.ellipse(tela, (90, 140, 60), R(px - 8 * k, py - 14 * k, 14 * k, 9 * k))
        else:
            pygame.draw.ellipse(tela, (220, 190, 120), R(px - 5 * k, py - 12 * k, 10 * k, 7 * k))
    balanco = math.sin(t * 1.5) * 6 * k                      # antenas gigantes lá dentro
    for s in (-1, 1):
        pygame.draw.lines(tela, (60, 30, 20), False, [(x + s * 18 * k, base - 60 * k), (x + s * 40 * k + balanco, base - 120 * k),
                                                      (x + s * 60 * k + balanco, base - 128 * k)], max(2, int(4 * k)))
    if int(t * 10) % 37 != 0:
        for s in (-1, 1):
            pygame.draw.ellipse(tela, (255, 200, 60), R(x + s * 22 * k - 8 * k, base - 56 * k, 16 * k, 10 * k))
