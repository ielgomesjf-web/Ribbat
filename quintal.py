"""Desenhos do Quintal (Fase 4): churrasco de gente gigante, casa, cerca branca, flores, abelhas e a mão."""
import math
import random

import pygame

from config import *  # noqa: F401,F403
from entidades import R

GRAMA_Q = (104, 190, 76)
GRAMA_Q_CLARA = (160, 222, 110)
GRAMA_Q_ESC = (66, 140, 54)
TERRA_Q = (126, 92, 62)
PELE = (232, 182, 146)
PELE_ESC = (196, 140, 106)


PELES = ((232, 182, 146), (196, 140, 100), (150, 100, 70), (110, 72, 50), (240, 200, 170))


def _perna(sf, x, base, k, cor, pele, curta, sapato, lado):
    """Uma perna: coxa, joelho, canela e o pé (com chinelo ou tênis)."""
    quadril, joelho, tornozelo = (x, base - 300 * k), (x + lado * 6 * k, base - 160 * k), (x + lado * 2 * k, base - 22 * k)
    if curta:                                                       # bermuda: só a coxa coberta
        pygame.draw.polygon(sf, pele, [(joelho[0] - 26 * k, joelho[1]), (joelho[0] + 26 * k, joelho[1]),
                                       (tornozelo[0] + 16 * k, tornozelo[1]), (tornozelo[0] - 16 * k, tornozelo[1])])
        pygame.draw.circle(sf, pele, (int(joelho[0]), int(joelho[1] + 6 * k)), int(26 * k))
        pygame.draw.polygon(sf, cor, [(quadril[0] - 38 * k, quadril[1]), (quadril[0] + 38 * k, quadril[1]),
                                      (joelho[0] + 32 * k, joelho[1] - 14 * k), (joelho[0] - 32 * k, joelho[1] - 14 * k)])
        pygame.draw.line(sf, [max(0, c - 30) for c in cor], (joelho[0] - 32 * k, joelho[1] - 14 * k),
                         (joelho[0] + 32 * k, joelho[1] - 14 * k), int(5 * k))
    else:                                                           # calça comprida
        pygame.draw.polygon(sf, cor, [(quadril[0] - 38 * k, quadril[1]), (quadril[0] + 38 * k, quadril[1]),
                                      (joelho[0] + 28 * k, joelho[1]), (tornozelo[0] + 22 * k, tornozelo[1]),
                                      (tornozelo[0] - 22 * k, tornozelo[1]), (joelho[0] - 28 * k, joelho[1])])
        pygame.draw.line(sf, [max(0, c - 25) for c in cor], (joelho[0] - 10 * k, joelho[1] - 40 * k), (joelho[0], joelho[1] + 30 * k),
                         int(3 * k))
    if sapato == "chinelo":
        pygame.draw.ellipse(sf, (60, 120, 200), R(tornozelo[0] - 24 * k + lado * 12 * k, base - 12 * k, 64 * k, 14 * k))
        pygame.draw.ellipse(sf, pele, R(tornozelo[0] - 18 * k + lado * 12 * k, base - 24 * k, 54 * k, 18 * k))
        pygame.draw.line(sf, (60, 120, 200), (tornozelo[0] + lado * 14 * k, base - 22 * k), (tornozelo[0] + lado * 24 * k, base - 8 * k), int(4 * k))
    else:
        pygame.draw.ellipse(sf, (240, 240, 244), R(tornozelo[0] - 26 * k + lado * 14 * k, base - 30 * k, 72 * k, 32 * k))
        pygame.draw.rect(sf, (220, 70, 60), R(tornozelo[0] - 26 * k + lado * 14 * k, base - 8 * k, 72 * k, 8 * k), border_radius=int(4 * k))
        for j in range(3):
            pygame.draw.line(sf, (90, 90, 110), (tornozelo[0] - 4 * k + lado * 14 * k + j * 8 * k, base - 28 * k),
                             (tornozelo[0] + 2 * k + lado * 14 * k + j * 8 * k, base - 20 * k), int(2 * k))


def pessoa(sf, x, base, rnd, k=1.0, segura="nada", avental=False):
    """Pessoa gigante vista do chão: pernas, roupa e os braços caídos segurando alguma coisa."""
    pele = rnd.choice(PELES)
    curta = rnd.random() < 0.6
    calca = rnd.choice([(60, 80, 140), (90, 70, 56), (200, 170, 120), (50, 50, 60), (120, 150, 90)])
    camisa = rnd.choice([(220, 80, 70), (80, 160, 210), (240, 200, 80), (120, 190, 110), (240, 240, 240), (170, 110, 200)])
    sapato = rnd.choice(["chinelo", "tenis"])
    for lado in (-1, 1):
        _perna(sf, x + lado * 44 * k, base, k, calca, pele, curta, sapato, lado)
    topo = base - 300 * k
    pygame.draw.rect(sf, calca, R(x - 84 * k, topo - 40 * k, 168 * k, 60 * k), border_radius=int(14 * k))          # quadril
    pygame.draw.rect(sf, (70, 50, 36), R(x - 84 * k, topo - 46 * k, 168 * k, 12 * k))                            # cinto
    pygame.draw.rect(sf, (220, 190, 80), R(x - 10 * k, topo - 46 * k, 20 * k, 12 * k))
    pygame.draw.rect(sf, camisa, R(x - 90 * k, topo - 300 * k, 180 * k, 262 * k), border_radius=int(30 * k))      # camiseta
    pygame.draw.line(sf, [max(0, c - 30) for c in camisa], (x - 40 * k, topo - 100 * k), (x - 20 * k, topo - 50 * k), int(3 * k))
    if avental:
        pygame.draw.polygon(sf, (250, 250, 246), [(x - 70 * k, topo - 260 * k), (x + 70 * k, topo - 260 * k), (x + 80 * k, topo + 40 * k),
                                                  (x - 80 * k, topo + 40 * k)])
        pygame.draw.rect(sf, (220, 60, 60), R(x - 40 * k, topo - 150 * k, 80 * k, 50 * k), border_radius=int(8 * k))
    for lado in (-1, 1):                                                                                     # braços
        ombro = (x + lado * 92 * k, topo - 280 * k)
        mao = (x + lado * 120 * k, topo - 40 * k)
        pygame.draw.line(sf, camisa, ombro, (x + lado * 108 * k, topo - 200 * k), int(52 * k))
        pygame.draw.line(sf, pele, (x + lado * 108 * k, topo - 200 * k), mao, int(40 * k))
        pygame.draw.circle(sf, pele, (int(mao[0]), int(mao[1])), int(24 * k))
    hx, hy = x + 120 * k, topo - 40 * k
    if segura == "copo":
        pygame.draw.rect(sf, (230, 60, 50), R(hx - 18 * k, hy - 60 * k, 36 * k, 60 * k), border_radius=int(6 * k))
        pygame.draw.rect(sf, (250, 250, 250), R(hx - 18 * k, hy - 50 * k, 36 * k, 10 * k))
    elif segura == "prato":
        pygame.draw.ellipse(sf, (250, 250, 250), R(hx - 60 * k, hy - 30 * k, 120 * k, 26 * k))
        pygame.draw.ellipse(sf, (190, 90, 60), R(hx - 30 * k, hy - 40 * k, 50 * k, 20 * k))
    elif segura == "espeto":
        pygame.draw.line(sf, (190, 190, 200), (hx, hy), (hx + 10 * k, hy - 120 * k), int(4 * k))
        for j in range(3):
            pygame.draw.ellipse(sf, (170, 80, 50), R(hx - 10 * k + j * 3 * k, hy - 100 * k + j * 26 * k, 26 * k, 22 * k))


def criar_fundo():
    ceu = pygame.Surface((LARGURA, ALTURA))
    for y in range(ALTURA):
        k = y / ALTURA
        ceu.fill([int(a + (b - a) * k) for a, b in zip((120, 190, 245), (214, 238, 250))], R(0, y, LARGURA, 1))
    pygame.draw.circle(ceu, (255, 244, 180), (150, 80), 44)
    pygame.draw.circle(ceu, (255, 252, 220), (150, 80), 34)
    # casa (fica longe, se mexe pouquinho)
    casa = pygame.Surface((LARGURA * 2, 330), pygame.SRCALPHA)
    for i in range(2):
        x0 = 120 + i * 980
        pygame.draw.rect(casa, (238, 220, 190), R(x0, 70, 640, 260))
        pygame.draw.polygon(casa, (176, 80, 60), [(x0 - 30, 74), (x0 + 320, -40), (x0 + 670, 74)])
        for j in range(3):
            jx = x0 + 60 + j * 200
            pygame.draw.rect(casa, (130, 170, 210), R(jx, 120, 110, 90))
            pygame.draw.rect(casa, BRANCO, R(jx, 120, 110, 90), 6)
            pygame.draw.line(casa, BRANCO, (jx + 55, 120), (jx + 55, 210), 4)
    # cerca branca (de ripas)
    cerca = pygame.Surface((LARGURA, 140), pygame.SRCALPHA)
    pygame.draw.rect(cerca, (236, 236, 230), R(0, 50, LARGURA, 10))
    pygame.draw.rect(cerca, (236, 236, 230), R(0, 100, LARGURA, 10))
    for x in range(0, LARGURA, 32):
        pygame.draw.polygon(cerca, (246, 246, 240), [(x + 4, 140), (x + 4, 18), (x + 14, 6), (x + 24, 18), (x + 24, 140)])
        pygame.draw.polygon(cerca, (200, 200, 196), [(x + 4, 140), (x + 4, 18), (x + 14, 6), (x + 24, 18), (x + 24, 140)], 2)
    # pessoas gigantes do churrasco (só aparece da barriga pra baixo: o Ribbat é pequeninho)
    gente = pygame.Surface((LARGURA * 2 * 2, 480 * 2), pygame.SRCALPHA)
    rnd = random.Random(8)
    for i in range(5):
        pessoa(gente, 240 + i * 760, 960, rnd, 1.7, segura=("copo", "prato", "nada", "espeto", "copo")[i])
    gente = pygame.transform.smoothscale(gente, (LARGURA * 2, 480))
    return {"ceu": ceu, "casa": casa, "cerca": cerca, "gente": gente}


def desenhar_fundo(tela, f, cam, t):
    tela.blit(f["ceu"], (0, 0))
    x = -((cam * 0.08) % (LARGURA * 2 * 0.5))
    tela.blit(f["casa"], (x, 60))
    for i in range(5):                                       # nuvenzinhas
        nx = (i * 260 - cam * 0.04 + t * 6) % (LARGURA + 200) - 100
        for dx, r in ((0, 26), (24, 20), (-24, 18)):
            pygame.draw.circle(tela, (250, 252, 255), (int(nx + dx), 60 + (i % 2) * 30), r)
    x = -((cam * 0.25) % (LARGURA * 2 * 0.5))
    tela.blit(f["gente"], (x, 0))
    x = -((cam * 0.4) % LARGURA)
    tela.blit(f["cerca"], (x, 330))
    tela.blit(f["cerca"], (x + LARGURA, 330))


def criar_tiles():
    rnd = random.Random(17)

    def terra():
        s = pygame.Surface((TILE, TILE))
        s.fill(TERRA_Q)
        for _ in range(5):
            pygame.draw.circle(s, (100, 72, 48), (rnd.randint(3, 28), rnd.randint(3, 28)), rnd.randint(1, 3))
        return s

    grama = terra()
    pygame.draw.rect(grama, GRAMA_Q, (0, 0, TILE, 11))
    for i in range(0, TILE, 3):                              # grama aparadinha de quintal
        pygame.draw.line(grama, GRAMA_Q_ESC, (i, 11), (i + 1, 14), 1)
        pygame.draw.line(grama, GRAMA_Q_CLARA, (i, 0), (i + 1, -3 + (i * 7) % 4), 1)
    pygame.draw.line(grama, GRAMA_Q_CLARA, (0, 1), (TILE, 1), 2)
    toalha = pygame.Surface((TILE, TILE), pygame.SRCALPHA)  # tampo da mesa com toalha xadrez
    pygame.draw.rect(toalha, (160, 110, 70), (0, 10, TILE, 8))
    for i in range(4):
        cor = (220, 50, 50) if i % 2 == 0 else (250, 250, 250)
        pygame.draw.rect(toalha, cor, (i * 8, 0, 8, 6))
        pygame.draw.rect(toalha, (250, 250, 250) if i % 2 == 0 else (220, 50, 50), (i * 8, 6, 8, 5))
    caixa = pygame.Surface((TILE, TILE))                     # caixa térmica azul
    caixa.fill((70, 130, 200))
    pygame.draw.rect(caixa, (40, 90, 160), (0, 0, TILE, TILE), 2)
    pygame.draw.rect(caixa, (240, 240, 240), (0, 0, TILE, 6))
    pygame.draw.line(caixa, (110, 170, 230), (4, 10), (28, 10), 2)
    boia = pygame.Surface((TILE, TILE), pygame.SRCALPHA)     # boia (atravessa por baixo)
    pygame.draw.ellipse(boia, (240, 120, 40), (0, 0, TILE, 12))
    pygame.draw.ellipse(boia, (255, 230, 90), (6, 2, 20, 6))
    return {"grama": grama, "terra": [terra() for _ in range(3)], "madeira": toalha, "caixa": caixa, "boia": boia}


def desenhar_flores(tela, flor, ox, oy, t):
    """Canteiro de flores (margarida, tulipa e girassolzinho) com folhas. É onde mora a abelha."""
    rnd = random.Random(flor.ini * 13)
    for cx in range(flor.ini, flor.fim + 1):
        for k in range(2):
            x = cx * TILE + 8 + k * 16 - ox + rnd.randint(-3, 3)
            base = flor.chao - oy
            alt = 22 + rnd.randint(0, 16)
            bal = math.sin(t * 2 + x * 0.1) * 2
            topo = (x + bal, base - alt)
            pygame.draw.line(tela, (56, 130, 48), (x, base), topo, 2)
            for lado, h in ((-1, 0.35), (1, 0.6)):                         # folhas
                fx, fy = x + bal * h, base - alt * h
                pygame.draw.polygon(tela, (80, 160, 60), [(fx, fy), (fx + lado * 10, fy - 6), (fx + lado * 3, fy + 2)])
            tipo = rnd.choice(("margarida", "tulipa", "girassol"))
            if tipo == "margarida":
                for p in range(8):
                    a = p / 8 * math.tau
                    pygame.draw.ellipse(tela, (250, 250, 250), R(topo[0] + math.cos(a) * 5 - 3, topo[1] + math.sin(a) * 5 - 3, 6, 6))
                pygame.draw.circle(tela, (250, 200, 40), (int(topo[0]), int(topo[1])), 3)
            elif tipo == "tulipa":
                cor = rnd.choice(((236, 70, 100), (250, 140, 60), (200, 110, 230)))
                pygame.draw.polygon(tela, cor, [(topo[0] - 6, topo[1] - 2), (topo[0] - 6, topo[1] - 12), (topo[0] - 2, topo[1] - 7),
                                                (topo[0], topo[1] - 13), (topo[0] + 2, topo[1] - 7), (topo[0] + 6, topo[1] - 12),
                                                (topo[0] + 6, topo[1] - 2), (topo[0], topo[1] + 2)])
                pygame.draw.line(tela, [min(255, c + 40) for c in cor], (topo[0] - 3, topo[1] - 8), (topo[0] - 3, topo[1] - 2), 1)
            else:
                for p in range(10):
                    a = p / 10 * math.tau + 0.2
                    pygame.draw.circle(tela, (250, 206, 40), (int(topo[0] + math.cos(a) * 6), int(topo[1] + math.sin(a) * 6)), 3)
                pygame.draw.circle(tela, (120, 70, 30), (int(topo[0]), int(topo[1])), 4)


_abelhas = {}


def _sprite_abelha(bate, aviso):
    """Abelha de verdade: peluda, tórax laranja, listras pretas, olhões, antena dobrada e cestinho de pólen."""
    import formigas as FA
    from chefe import ESC, _Pincel, _pts_elipse
    chave = (round(bate, 1), aviso)
    if chave in _abelhas:
        return _abelhas[chave]
    w, h = 60, 46
    sf = pygame.Surface((w * ESC, h * ESC), pygame.SRCALPHA)
    p = _Pincel(sf, 30, 24)
    for i, (comp, larg) in enumerate(((24, 9), (17, 7))):                              # 2 pares de asas
        FA._asa(p, (2 + i * 2, -7), comp, larg, math.pi + 0.6 - bate * 0.9 + i * 0.25, (226, 238, 250, 140), (130, 150, 170, 190))
    for lado in (1, 0):                                                                 # perninhas
        cor = (50, 36, 24) if lado else (70, 50, 34)
        for i in range(3):
            raiz = (6 - i * 5 - lado * 2, 5)
            joelho = (raiz[0] - 3, raiz[1] + 7)
            pe = (raiz[0] - 1 - i * 2, raiz[1] + 13)
            p.osso(raiz, joelho, 1.4, 1.1, cor)
            p.osso(joelho, pe, 1.1, 0.8, cor)
        if lado == 0:
            p.pol(_pts_elipse(-7, 16, 3.5, 2.6), (250, 200, 60))                        # cestinho de pólen
    p.pol(_pts_elipse(-11, 3, 13, 9, 0.15), (50, 34, 20))                               # abdômen listrado
    p.pol(_pts_elipse(-11, 3, 12, 8, 0.15), (240, 186, 54))
    for dx in (-17, -11, -5):
        p.pol([(dx - 2, -4), (dx + 2, -4), (dx + 2.5, 10), (dx - 1.5, 10)], (40, 28, 18))
    p.pol([(-23, 4), (-29, 6), (-23, 7)], (40, 28, 18))                                  # ferrão
    p.pol(_pts_elipse(3, -1, 8, 7), (176, 110, 44))                                       # tórax peludo
    for i in range(14):
        a = i / 14 * math.tau
        p.circ(3 + math.cos(a) * 7.5, -1 + math.sin(a) * 6.5, 1.3, (210, 150, 70))
    p.pol(_pts_elipse(12, 0, 5.5, 5), (60, 40, 26))                                      # cabeça
    p.pol(_pts_elipse(13, -1, 3.2, 4, 0.2), (255, 80, 40) if aviso else (20, 14, 10))    # olhão
    p.circ(12, -3, 1, (220, 220, 220))
    p.linha([(14, -4), (15, -10), (20, -12)], (40, 28, 18), 1.2)                         # antena dobrada
    img = pygame.transform.smoothscale(sf, (w, h))
    _abelhas[chave] = img
    return img


def desenhar_abelha(tela, a, ox, oy, t):
    x, y, d = a.x - ox, a.y - oy, a.dir
    s = _sprite_abelha(abs(math.sin(t * 50)), a.estado == "alerta" and int(t * 14) % 2 == 0)
    if d < 0:
        s = pygame.transform.flip(s, True, False)
    tela.blit(s, s.get_rect(center=(x, y)))
    if a.estado == "alerta":
        pygame.draw.circle(tela, PRETO, (int(x), int(y - 28)), 9)
        pygame.draw.circle(tela, AMARELO, (int(x), int(y - 28)), 7)
        pygame.draw.rect(tela, PRETO, R(x - 1.5, y - 33, 3, 7))
        pygame.draw.circle(tela, PRETO, (int(x), int(y - 23)), 2)


_moco = {}


def desenhar_moco(tela, mao, ox, oy):
    """O moço do churrasco (de avental, gigante) e a churrasqueira com linguiça, brasa e fumaça."""
    x = mao.x0 - ox
    base = 15 * TILE - oy
    if "img" not in _moco:
        sf = pygame.Surface((600 * 2, 560 * 2), pygame.SRCALPHA)
        pessoa(sf, 300 * 2 - 120, 560 * 2, random.Random(3), 2.0 * 0.62, avental=True)
        _moco["img"] = pygame.transform.smoothscale(sf, (600, 560))
    tela.blit(_moco["img"], (x - 300 + 60, base - 560))
    gx = x + 140                                                   # churrasqueira
    pygame.draw.line(tela, (50, 50, 54), (gx + 10, base), (gx + 26, base - 200), 6)
    pygame.draw.line(tela, (50, 50, 54), (gx + 150, base), (gx + 134, base - 200), 6)
    pygame.draw.polygon(tela, (60, 60, 66), [(gx, base - 226), (gx + 160, base - 226), (gx + 146, base - 196), (gx + 14, base - 196)])
    pygame.draw.rect(tela, (90, 90, 96), R(gx - 6, base - 232, 172, 8), border_radius=3)
    t = pygame.time.get_ticks() / 1000
    for i in range(7):                                             # brasa
        brilho = 180 + int(60 * math.sin(t * 6 + i))
        pygame.draw.circle(tela, (brilho, 90, 30), (gx + 20 + i * 20, base - 230), 6)
    for i in range(4):                                             # linguiças e carne
        pygame.draw.ellipse(tela, (150, 60, 40), R(gx + 14 + i * 36, base - 248, 30, 12))
        pygame.draw.line(tela, (110, 40, 26), (gx + 20 + i * 36, base - 244), (gx + 36 + i * 36, base - 240), 2)
    fumaca = pygame.Surface((200, 240), pygame.SRCALPHA)
    for i in range(7):
        k = (t * 0.35 + i / 7) % 1
        pygame.draw.circle(fumaca, (236, 236, 236, int(110 * (1 - k))), (int(100 + math.sin(k * 6 + i) * 34), int(230 - k * 220)),
                           int(14 + k * 34))
    tela.blit(fumaca, (gx - 20, base - 470))


_mao_img = {}


def _sprite_mao():
    """Mão gigante vista de cima (costas da mão): dedos com dobrinhas, dedão do lado, unhas e o punho."""
    if "img" in _mao_img:
        return _mao_img["img"]
    k = 2
    w, h = 130, 120
    sf = pygame.Surface((w * k, h * k), pygame.SRCALPHA)
    cx = 65 * k
    escura, pele, clara = (190, 132, 98), PELE, (246, 210, 180)
    pygame.draw.rect(sf, (220, 80, 70), R(cx - 34 * k, 0, 68 * k, 26 * k))                       # punho da manga
    pygame.draw.rect(sf, (190, 60, 56), R(cx - 34 * k, 20 * k, 68 * k, 8 * k))
    pygame.draw.rect(sf, pele, R(cx - 26 * k, 24 * k, 52 * k, 26 * k))                            # pulso
    pygame.draw.ellipse(sf, escura, R(cx - 44 * k, 38 * k, 88 * k, 56 * k))                         # costas da mão
    pygame.draw.ellipse(sf, pele, R(cx - 42 * k, 40 * k, 84 * k, 52 * k))
    for i, (dx, comp, larg) in enumerate(((-30, 30, 15), (-11, 38, 16), (8, 40, 16), (26, 34, 15))):  # 4 dedos
        x0 = cx + dx * k
        pygame.draw.rect(sf, escura, R(x0 - larg / 2 * k - 1 * k, 76 * k, (larg + 2) * k, comp * k + 2 * k), border_radius=int(8 * k))
        pygame.draw.rect(sf, pele, R(x0 - larg / 2 * k, 76 * k, larg * k, comp * k), border_radius=int(8 * k))
        for dobra in (0.35, 0.7):
            y = 76 * k + comp * dobra * k
            pygame.draw.arc(sf, escura, R(x0 - 5 * k, y - 3 * k, 10 * k, 6 * k), 0, math.pi, max(1, k))
        pygame.draw.ellipse(sf, clara, R(x0 - 5 * k, 76 * k + (comp - 11) * k, 10 * k, 9 * k))       # unha
        pygame.draw.circle(sf, clara, (int(x0), int(64 * k)), int(4 * k))                             # nó do dedo
    pygame.draw.polygon(sf, escura, [(cx - 40 * k, 56 * k), (cx - 62 * k, 82 * k), (cx - 54 * k, 92 * k), (cx - 30 * k, 72 * k)])  # dedão
    pygame.draw.polygon(sf, pele, [(cx - 40 * k, 58 * k), (cx - 60 * k, 82 * k), (cx - 54 * k, 89 * k), (cx - 32 * k, 72 * k)])
    pygame.draw.ellipse(sf, clara, R(cx - 60 * k, 80 * k, 8 * k, 8 * k))
    img = pygame.transform.smoothscale(sf, (w, h))
    _mao_img["img"] = img
    return img


def desenhar_mao(tela, mao, ox, oy, t, superficie):
    """A mão gigante + o braço vindo lá de cima + a sombra onde ela vai bater."""
    x, y = mao.x - ox, mao.y - oy
    if y < -60:
        return
    chao = (mao.alvo_y if mao.estado in ("mirando", "batendo", "no_chao") else superficie) - oy
    perto = max(0.2, min(1.0, 1 - (chao - y) / 400))              # sombra: mais escura quanto mais perto
    sombra = pygame.Surface((120, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(sombra, (20, 20, 20, int(170 * perto)), sombra.get_rect())
    tela.blit(sombra, (x - 60, chao - 12))
    tremor = math.sin(t * 60) * 3 if mao.estado == "mirando" else 0
    x += tremor
    pygame.draw.polygon(tela, (220, 80, 70), [(x - 36, -10), (x + 36, -10), (x + 34, y - 112), (x - 34, y - 112)])   # manga
    pygame.draw.line(tela, (190, 60, 56), (x - 10, -10), (x - 8, y - 112), 3)
    img = _sprite_mao()
    tela.blit(img, (x - img.get_width() / 2, y - img.get_height() + 8))


def desenhar_vaso(tela, r, semente):
    """Vaso de planta tampando o caminho (quebra com a investida)."""
    pygame.draw.polygon(tela, (150, 70, 40), [(r.left, r.top + 10), (r.right, r.top + 10), (r.right - 8, r.bottom), (r.left + 8, r.bottom)])
    pygame.draw.rect(tela, (180, 90, 52), R(r.left - 4, r.top + 4, r.width + 8, 14), border_radius=4)
    pygame.draw.line(tela, (120, 54, 30), (r.left + 10, r.top + 30), (r.right - 10, r.top + 30), 2)
    for i in range(5):                                        # plantinha
        a = -math.pi / 2 + (i - 2) * 0.45
        pygame.draw.line(tela, (60, 150, 60), (r.centerx, r.top + 6), (r.centerx + math.cos(a) * 34, r.top + 6 + math.sin(a) * 34), 4)
        pygame.draw.ellipse(tela, (80, 170, 70), R(r.centerx + math.cos(a) * 34 - 8, r.top + 6 + math.sin(a) * 34 - 5, 16, 10))


def desenhar_piscina(tela, r, t):
    camada = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
    camada.fill((90, 180, 230, 220))
    pts = [(x, 3 + math.sin(x / 20 + t * 2) * 2) for x in range(0, r.width + 8, 8)]
    pygame.draw.lines(camada, (220, 245, 255), False, pts, 3)
    for i in range(r.width // 50):
        bx = (i * 50 + t * 20) % r.width
        pygame.draw.line(camada, (180, 230, 250), (bx, 16 + i % 3 * 8), (bx + 16, 16 + i % 3 * 8), 2)
    tela.blit(camada, r.topleft)


def desenhar_porta(tela, x, base, t, k=1.0):
    """Porta dos fundos da casa, com a PORTINHA DE GATO embaixo... e dois olhos amarelos lá dentro."""
    pygame.draw.rect(tela, (238, 220, 190), R(x - 170 * k, base - 330 * k, 340 * k, 330 * k))
    pygame.draw.rect(tela, (150, 100, 60), R(x - 90 * k, base - 300 * k, 180 * k, 300 * k))
    pygame.draw.rect(tela, (120, 76, 44), R(x - 90 * k, base - 300 * k, 180 * k, 300 * k), max(2, int(6 * k)))
    pygame.draw.circle(tela, (240, 200, 70), (int(x + 64 * k), int(base - 150 * k)), int(8 * k))
    pygame.draw.rect(tela, (90, 60, 34), R(x - 36 * k, base - 70 * k, 72 * k, 70 * k), border_radius=int(10 * k))
    pygame.draw.rect(tela, (20, 14, 10), R(x - 30 * k, base - 64 * k, 60 * k, 64 * k), border_radius=int(8 * k))
    if int(t * 10) % 41 != 0:
        for ox in (-12, 12):
            pygame.draw.ellipse(tela, (250, 210, 60), R(x + ox * k - 7 * k, base - 44 * k, 14 * k, 10 * k))
            pygame.draw.ellipse(tela, PRETO, R(x + ox * k - 1.5 * k, base - 43 * k, 3 * k, 8 * k))
    pygame.draw.rect(tela, (200, 200, 196), R(x - 130 * k, base - 280 * k, 26 * k, 26 * k))
