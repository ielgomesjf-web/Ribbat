"""Desenhos do pântano: fundo com folhas gigantes, taboas, água, vitória-régia, peixe, vagalume."""
import math
import random

import pygame

from config import *  # noqa: F401,F403
from entidades import R


def _folha_gigante(larg, cor, angulo, caule=1.0):
    """Folha de orelha-de-elefante: coração caído, pendurado num caule curvo."""
    alt = int(larg * 1.9)
    s = pygame.Surface((int(larg * 1.6), alt), pygame.SRCALPHA)
    cx, topo = s.get_width() / 2, larg * 0.15
    escura = [max(0, c - 34) for c in cor]
    clara = [min(255, c + 26) for c in cor]
    ca, sa = math.cos(angulo), math.sin(angulo)
    k = larg / 34

    def gira(x, y):
        return cx + (x * ca - y * sa) * k, topo + larg * 0.25 + (x * sa + y * ca) * k

    pts = []
    for i in range(40):
        a = i / 40 * math.tau
        x = 16 * math.sin(a) ** 3
        y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append(gira(x, y))
    entalhe = gira(0, -5)
    ponta = gira(0, 17)
    base = (cx + larg * 0.1 * caule, alt)
    meio = (cx - larg * 0.15, (alt + entalhe[1]) / 2)
    pygame.draw.lines(s, escura, False, [base, meio, entalhe], max(3, int(larg * 0.06)))
    pygame.draw.polygon(s, cor, pts)
    pygame.draw.polygon(s, escura, pts, 2)
    pygame.draw.line(s, clara, entalhe, ponta, max(2, int(larg * 0.025)))
    for i in range(1, 5):
        f = i / 5
        mx, my = entalhe[0] + (ponta[0] - entalhe[0]) * f, entalhe[1] + (ponta[1] - entalhe[1]) * f
        for lado in (-1, 1):
            pygame.draw.line(s, clara, (mx, my), gira(lado * (14 - i * 2), -3 + i * 4), 1)
    return s


def criar_fundo():
    ceu = pygame.Surface((LARGURA, ALTURA))
    for y in range(ALTURA):
        k = y / ALTURA
        cor = [int(a + (b - a) * k) for a, b in zip((120, 168, 160), (214, 226, 186))]
        pygame.draw.line(ceu, cor, (0, y), (LARGURA, y))
    rnd = random.Random(11)
    longe = [_folha_gigante(rnd.randint(90, 130), (118, 166, 128), rnd.uniform(-0.5, 0.5), rnd.uniform(-1, 1))
             for _ in range(5)]
    perto = [_folha_gigante(rnd.randint(150, 210), rnd.choice([(70, 132, 74), (62, 120, 80), (84, 142, 70)]),
                            rnd.uniform(-0.6, 0.6), rnd.uniform(-1, 1)) for _ in range(6)]
    neblina = pygame.Surface((LARGURA, 140), pygame.SRCALPHA)
    for y in range(140):
        pygame.draw.line(neblina, (230, 240, 225, int(70 * math.sin(y / 140 * math.pi))), (0, y), (LARGURA, y))
    return {"ceu": ceu, "longe": longe, "perto": perto, "neblina": neblina}


def _arvore_brejo(tela, x, base, alt, t, i):
    cor, musgo = (96, 132, 118), (150, 172, 140)
    pygame.draw.polygon(tela, cor, [(x - 22, base), (x - 7, base - alt * 0.5), (x - 5, base - alt),
                                    (x + 5, base - alt), (x + 7, base - alt * 0.5), (x + 22, base)])
    for dx, dy, r in ((-30, -alt, 40), (25, -alt - 10, 44), (0, -alt - 40, 46),
                      (-50, -alt + 20, 30), (50, -alt + 15, 32)):
        pygame.draw.circle(tela, cor, (int(x + dx), int(base + dy)), r)
    for j in range(6):
        mx = x - 50 + j * 20
        comp = 30 + (i * 7 + j * 13) % 40
        bal = math.sin(t * 0.8 + j + i) * 3
        pygame.draw.lines(tela, musgo, False, [(mx, base - alt + 10), (mx + bal, base - alt + 10 + comp / 2),
                                               (mx - bal, base - alt + 10 + comp)], 2)


def desenhar_fundo(tela, fundo, cam, t):
    tela.blit(fundo["ceu"], (0, 0))
    passo = 260   # árvores de brejo lá no fundo
    x0 = -((cam * 0.12) % passo) - passo
    i0 = int((cam * 0.12) // passo)
    for i in range(LARGURA // passo + 3):
        n = i0 + i
        _arvore_brejo(tela, x0 + i * passo + (n * 97 % 80), 400, 210 + (n * 53 % 70), t, n)
    tela.blit(fundo["neblina"], (0, 300))
    for camada, fator, passo, base in ((fundo["longe"], 0.3, 120, 470), (fundo["perto"], 0.55, 210, 500)):
        x0 = -((cam * fator) % passo) - passo
        i0 = int((cam * fator) // passo)
        for i in range(LARGURA // passo + 3):
            n = i0 + i
            img = camada[n * 7 % len(camada)]
            x = x0 + i * passo + (n * 41 % 50) - img.get_width() / 2
            tela.blit(img, (x, base - img.get_height() + (n * 29 % 40)))


def desenhar_taboas(tela, x, base, t, semente):
    """Taboas (planta de brejo com a ponta marrom) balançando."""
    for j in range(2 + semente % 2):
        alt = 40 + (semente * 13 + j * 17) % 30
        bal = math.sin(t * 1.6 + semente + j) * 4
        bx = x + j * 7 - 6
        topo = (bx + bal, base - alt)
        pygame.draw.line(tela, (70, 120, 60), (bx, base), topo, 2)
        pygame.draw.ellipse(tela, (110, 70, 40), R(topo[0] - 3, topo[1] + 2, 7, 16))
        pygame.draw.line(tela, (70, 120, 60), (topo[0], topo[1] + 2), (topo[0] + bal * 0.3, topo[1] - 6), 1)
        pygame.draw.line(tela, (84, 140, 70), (bx + 2, base), (bx + 12 + bal, base - alt * 0.6), 2)


def desenhar_agua(tela, r, t):
    camada = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
    camada.fill((52, 104, 96, 205))
    pygame.draw.rect(camada, (34, 76, 72, 230), R(0, 40, r.width, r.height))
    pts = [(x, 3 + math.sin(x / 22 + t * 2.5) * 2) for x in range(0, r.width + 8, 8)]
    pygame.draw.lines(camada, (170, 214, 200, 255), False, pts, 2)
    for i in range(r.width // 70):
        bx = (i * 70 + t * 14) % r.width
        pygame.draw.line(camada, (120, 170, 160, 180), (bx, 14 + i % 3 * 6), (bx + 18, 14 + i % 3 * 6), 1)
    tela.blit(camada, r.topleft)


def desenhar_vitoria(tela, r, peso, afundada, aguenta, t):
    """r = retângulo da folha (o topo é onde o Ribbat pisa)."""
    if afundada > 0:
        for i in range(3):
            sobe = (t * 2 + i * 0.7) % 1.5
            pygame.draw.circle(tela, (180, 220, 210), (int(r.left + 10 + i * r.width / 3), int(r.top + 8 - sobe * 6)),
                               2 + i % 2, 1)
        return
    desce = peso / aguenta * 7 + math.sin(t * 2 + r.x) * 1.2
    tremida = math.sin(t * 50) * 1.5 if peso > aguenta * 0.5 else 0
    folha = R(r.left - 6 + tremida, r.top - 3 + desce, r.width + 12, 12)
    pygame.draw.ellipse(tela, (40, 96, 50), folha.move(0, 2))
    pygame.draw.ellipse(tela, (82, 160, 76), folha)
    pygame.draw.polygon(tela, (52, 104, 96), [folha.center, (folha.right, folha.centery - 3),
                                              (folha.right, folha.centery + 3)])
    pygame.draw.line(tela, (124, 196, 104), (folha.left + 6, folha.centery - 1), (folha.centerx, folha.centery - 1), 1)
    if (r.x // TILE) % 3 == 0:  # florzinha
        fx, fy = folha.left + 12, folha.top
        for a in range(5):
            ang = a / 5 * math.tau
            pygame.draw.circle(tela, (246, 180, 200), (int(fx + math.cos(ang) * 4), int(fy + math.sin(ang) * 2)), 3)
        pygame.draw.circle(tela, AMARELO, (int(fx), int(fy)), 2)


def desenhar_peixe(tela, x, y, vx, vy):
    s = pygame.Surface((40, 24), pygame.SRCALPHA)
    pygame.draw.polygon(s, (200, 100, 50), [(6, 12), (0, 4), (0, 20)])
    pygame.draw.ellipse(s, (232, 130, 60), R(5, 4, 30, 16))
    pygame.draw.ellipse(s, (250, 200, 130), R(12, 12, 18, 7))
    pygame.draw.polygon(s, (200, 100, 50), [(16, 5), (22, 0), (26, 5)])
    pygame.draw.circle(s, BRANCO, (29, 10), 4)
    pygame.draw.circle(s, PRETO, (30, 10), 2)
    pygame.draw.line(s, (120, 50, 30), (34, 14), (31, 15), 2)
    pygame.draw.ellipse(s, PRETO, R(5, 4, 30, 16), 1)
    ang = -math.degrees(math.atan2(vy, abs(vx) + 1))
    if vx < 0:
        s = pygame.transform.flip(s, True, False)
        ang = -ang
    img = pygame.transform.rotate(s, ang)
    tela.blit(img, (x - img.get_width() / 2, y - img.get_height() / 2))


def desenhar_vagalume(tela, x, y, t):
    brilho = (math.sin(t * 3) + 1) / 2
    if brilho > 0.3:
        halo = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(halo, (250, 240, 120, int(90 * brilho)), (8, 8), 8)
        tela.blit(halo, (x - 8, y - 8))
        pygame.draw.circle(tela, (255, 250, 170), (int(x), int(y)), 2)


def desenhar_aviso_peixe(tela, x, y, t):
    """Borbulhas e anelzinho na água: o peixe vai pular aqui!"""
    for i in range(2):
        k = (t * 1.8 + i * 0.5) % 1
        pygame.draw.ellipse(tela, (190, 230, 220), R(x - 6 - k * 18, y - 2 - k * 3, 12 + k * 36, 6 + k * 6), 1)
    for i in range(3):
        sobe = (t * 3 + i * 0.33) % 1
        pygame.draw.circle(tela, (210, 240, 235), (int(x - 8 + i * 8), int(y - 2 - sobe * 14)), 2 + i % 2, 1)
