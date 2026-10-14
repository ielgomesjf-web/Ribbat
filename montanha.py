"""Desenhos da Montanha (Fase 5): céu que escurece lá em cima, serras com neve, nuvens, rocha, gelo e o gavião."""
import math
import random

import pygame

from config import *  # noqa: F401,F403
from entidades import R

ROCHA_M = (124, 112, 104)
ROCHA_M_ESC = (88, 78, 72)
ROCHA_M_CLARA = (160, 150, 140)
NEVE = (240, 246, 252)
NEVE_SOMBRA = (200, 216, 236)


def criar_fundo():
    rnd = random.Random(23)
    serras = []
    for camada, (cor, alt, passo) in enumerate((((150, 170, 200), 200, 220), ((120, 140, 170), 150, 170))):
        s = pygame.Surface((LARGURA * 2, 340), pygame.SRCALPHA)
        pts = [(0, 340)]
        x = 0
        picos = []
        while x <= LARGURA * 2:
            y = 340 - alt - rnd.randint(-40, 60)
            pts.append((x, y))
            picos.append((x, y))
            x += passo // 2
            pts.append((x, 340 - alt * 0.45 - rnd.randint(0, 40)))
            x += passo // 2
        pts.append((LARGURA * 2, 340))
        pygame.draw.polygon(s, cor, pts)
        for px, py in picos:                              # neve nos picos
            pygame.draw.polygon(s, NEVE, [(px, py), (px - 34, py + 44), (px - 12, py + 36), (px, py + 48),
                                          (px + 14, py + 34), (px + 34, py + 44)])
        serras.append(s)
    nuvens = pygame.Surface((LARGURA * 2, 160), pygame.SRCALPHA)
    for i in range(16):
        x, y = rnd.randint(0, LARGURA * 2), rnd.randint(30, 120)
        for k in range(5):
            pygame.draw.circle(nuvens, (250, 252, 255, 210), (x + k * 26 - 52, y + (k % 2) * 10), 30 + (k % 3) * 8)
    return {"serras": serras, "nuvens": nuvens}


def desenhar_fundo(tela, f, cam_x, cam_y, alt_fase, t):
    """O céu escurece quanto mais alto o Ribbat está (e as nuvens passam por ele)."""
    altura_max = max(1, alt_fase * TILE - ALTURA)
    subida = 1 - min(1.0, max(0.0, cam_y / altura_max))          # 0 = pé da montanha, 1 = topo
    baixo = [int(a + (b - a) * subida) for a, b in zip((196, 226, 244), (120, 150, 210))]
    cima = [int(a + (b - a) * subida) for a, b in zip((110, 170, 230), (40, 50, 110))]
    for y in range(0, ALTURA, 4):
        k = y / ALTURA
        tela.fill([int(a + (b - a) * k) for a, b in zip(cima, baixo)], R(0, y, LARGURA, 4))
    if subida > 0.6:                                              # estrelinhas lá no alto
        rnd = random.Random(3)
        for i in range(30):
            br = int(200 * (subida - 0.6) / 0.4 * (0.6 + 0.4 * math.sin(t * 2 + i)))
            pygame.draw.circle(tela, (br, br, br), (rnd.randint(0, LARGURA), rnd.randint(0, 200)), 1)
    for camada, (fx, fy, base) in enumerate(((0.06, 0.05, 260), (0.14, 0.1, 300))):
        s = f["serras"][camada]
        x = -((cam_x * fx) % LARGURA)
        y = base - (cam_y - (alt_fase * TILE - ALTURA)) * fy
        tela.blit(s, (x, y))
        tela.blit(s, (x + LARGURA * 2 - LARGURA * 2, y))
    # faixa de nuvens: fica numa altura da montanha (você atravessa ela subindo)
    y_nuvem = alt_fase * TILE * 0.45 - cam_y
    x = -((cam_x * 0.5 + t * 8) % LARGURA)
    tela.blit(f["nuvens"], (x, y_nuvem))
    tela.blit(f["nuvens"], (x + LARGURA, y_nuvem))


def criar_tiles():
    rnd = random.Random(29)

    def rocha():
        s = pygame.Surface((TILE, TILE))
        s.fill(ROCHA_M)
        for _ in range(3):                                         # rachadurinhas
            x, y = rnd.randint(2, 28), rnd.randint(2, 28)
            pygame.draw.line(s, ROCHA_M_ESC, (x, y), (x + rnd.randint(-8, 8), y + rnd.randint(3, 9)), 1)
        for _ in range(4):
            pygame.draw.circle(s, rnd.choice([ROCHA_M_ESC, ROCHA_M_CLARA]), (rnd.randint(3, 28), rnd.randint(3, 28)), 2)
        return s

    grama = rocha()                                                # embaixo: grama rala em cima da rocha
    pygame.draw.rect(grama, (96, 160, 80), (0, 0, TILE, 7))
    for i in range(0, TILE, 4):
        pygame.draw.line(grama, (70, 130, 60), (i, 6), (i + 2, 10), 2)
    pygame.draw.line(grama, (140, 200, 110), (0, 1), (TILE, 1), 2)
    neve = rocha()                                                 # lá no alto: neve
    pygame.draw.rect(neve, NEVE, (0, 0, TILE, 10))
    for x in (4, 13, 22, 29):
        pygame.draw.circle(neve, NEVE, (x, 10), 4)
    pygame.draw.line(neve, NEVE_SOMBRA, (0, 9), (TILE, 9), 2)
    pygame.draw.line(neve, (255, 255, 255), (0, 1), (TILE, 1), 2)
    tabua = pygame.Surface((TILE, TILE), pygame.SRCALPHA)          # bordinha de madeira presa na rocha
    pygame.draw.rect(tabua, (150, 100, 56), (0, 0, TILE, 10), border_radius=3)
    pygame.draw.rect(tabua, (110, 70, 36), (0, 0, TILE, 10), 2, border_radius=3)
    pygame.draw.line(tabua, (90, 60, 30), (4, 10), (10, 18), 3)
    return {"grama": grama, "neve": neve, "terra": [rocha() for _ in range(3)], "madeira": tabua}


def desenhar_espinho(tela, x, base, gelo):
    """Espinhos de pedra (embaixo) ou cristais de gelo (lá em cima)."""
    for i in range(3):
        px = x + 4 + i * 10
        h = 16 + (i % 2) * 4
        if gelo:
            pygame.draw.polygon(tela, (170, 220, 250), [(px, base), (px + 5, base - h), (px + 10, base)])
            pygame.draw.line(tela, (240, 250, 255), (px + 5, base - h), (px + 3, base - 4), 2)
        else:
            pygame.draw.polygon(tela, (100, 92, 88), [(px, base), (px + 5, base - h), (px + 10, base)])
            pygame.draw.line(tela, (170, 160, 150), (px + 5, base - h), (px + 4, base - 6), 1)


_gaviao = {}


def _sprite_gaviao(asa, mergulho, aviso):
    """Gavião de verdade: bico curvo escuro com a base amarela, olho amarelo, asas com as penas da ponta
    abertas, barriga clara listrada, cauda listrada e pernas amarelas com garras."""
    from chefe import ESC, _Pincel, _pts_elipse
    chave = (round(asa, 1), mergulho, aviso)
    if chave in _gaviao:
        return _gaviao[chave]
    w, h = 96, 80
    sf = pygame.Surface((w * ESC, h * ESC), pygame.SRCALPHA)
    p = _Pincel(sf, 50, 40)
    marrom, marrom_esc, clara = (122, 92, 64), (78, 56, 38), (232, 220, 196)
    # cauda listrada
    cauda = [(-20, -2), (-44, -6), (-46, 4), (-20, 6)]
    p.pol(cauda, (140, 120, 100))
    for k in range(3):
        x = -26 - k * 7
        p.linha([(x, -4), (x, 5)], (60, 46, 34), 2)
    # asa de lá (mais escura)
    def asa_pts(lado):
        ang = -0.9 + asa * 1.5 if not mergulho else -0.2
        comp = 44 if not mergulho else 30
        base = (-2 + lado * 3, -6)
        ponta = (base[0] - 8 + math.cos(ang) * 4, base[1] - math.sin(-ang) * comp)
        return base, ponta, ang
    for lado, cor in ((1, marrom_esc), (0, marrom)):
        base, ponta, ang = asa_pts(lado)
        bx, by = base
        if mergulho:                                              # asas fechadas pra trás no mergulho
            pts = [(bx + 8, by), (bx - 34, by - 8), (bx - 30, by + 4)]
            p.pol(pts, cor)
            continue
        alto = -40 * (1 - asa) + 18 * asa
        pts = [(bx + 10, by + 2), (bx + 4, by + alto * 0.6), (bx - 6, by + alto), (bx - 24, by + alto * 0.9), (bx - 18, by + 4)]
        p.pol(pts, cor)
        for k in range(4):                                        # penas da ponta abertas
            fx = bx - 4 - k * 6
            p.pol([(fx, by + alto), (fx - 3, by + alto - 9 * (1 if alto < 0 else -1)), (fx - 5, by + alto)], cor)
    # corpo: costas marrons, barriga clara com listrinhas
    p.pol(_pts_elipse(0, 0, 24, 13, 0.08), marrom)
    p.pol(_pts_elipse(2, 5, 18, 8, 0.08), clara)
    for k in range(4):
        p.linha([(-8 + k * 6, 2), (-6 + k * 6, 10)], (170, 120, 80), 1.5)
    # cabeça, olho e bico curvo
    p.pol(_pts_elipse(22, -6, 11, 10), (110, 100, 96))
    p.pol(_pts_elipse(25, -8, 4, 4), (250, 210, 60) if not aviso else (255, 90, 40))
    p.circ(26, -8, 1.8, PRETO)
    p.pol([(30, -6), (36, -4), (34, 2), (30, 0)], (40, 36, 40))     # bico
    p.pol([(29, -7), (32, -7), (31, -3)], (250, 210, 60))           # base amarela do bico
    # pernas amarelas com garras (esticadas no mergulho)
    if mergulho:
        for k in (0, 6):
            p.linha([(10 + k, 8), (22 + k, 18)], (240, 200, 70), 2.5)
            for g in (-1, 0, 1):
                p.linha([(22 + k, 18), (26 + k + g * 2, 22 + abs(g) * 2)], (30, 26, 26), 1.5)
    else:
        p.linha([(4, 10), (6, 14)], (240, 200, 70), 2.5)
    img = pygame.transform.smoothscale(sf, (w, h))
    _gaviao[chave] = img
    return img


def desenhar_gaviao(tela, g, ox, oy, t):
    x, y = g.x - ox, g.y - oy
    mergulho = g.estado == "mergulhando"
    aviso = g.estado == "mirando" and int(t * 14) % 2 == 0
    img = _sprite_gaviao((math.sin(t * 9) + 1) / 2 if not mergulho else 0, mergulho, aviso)
    if g.dir < 0:
        img = pygame.transform.flip(img, True, False)
    if mergulho:
        ang = -math.degrees(math.atan2(g.vy, abs(g.vx) + 0.01)) * (1 if g.dir > 0 else -1)
        img = pygame.transform.rotate(img, ang)
    tela.blit(img, img.get_rect(center=(x, y)))
    if g.estado == "mirando" and g.alvo:                           # o alvo travado no chão
        ax, ay = g.alvo[0] - ox, g.alvo[1] - oy
        k = 0.6 + 0.4 * abs(math.sin(t * 12))
        pygame.draw.circle(tela, (230, 50, 40), (int(ax), int(ay)), int(18 * k), 3)
        pygame.draw.line(tela, (230, 50, 40), (ax - 24, ay), (ax + 24, ay), 2)
        pygame.draw.line(tela, (230, 50, 40), (ax, ay - 24), (ax, ay + 24), 2)
        pygame.draw.circle(tela, PRETO, (int(x), int(y - 34)), 9)
        pygame.draw.circle(tela, (255, 90, 60), (int(x), int(y - 34)), 7)
        pygame.draw.rect(tela, BRANCO, R(x - 1.5, y - 39, 3, 7))
        pygame.draw.circle(tela, BRANCO, (int(x), int(y - 29)), 2)


def desenhar_cume(tela, x, base, t, k=1.0):
    """Lá no topo: a entrada de uma caverna com um brilho dourado lá dentro... e alguém esperando."""
    pygame.draw.polygon(tela, ROCHA_M_ESC, [(x - 170 * k, base), (x - 120 * k, base - 210 * k), (x - 20 * k, base - 260 * k),
                                            (x + 90 * k, base - 230 * k), (x + 170 * k, base)])
    pygame.draw.polygon(tela, NEVE, [(x - 120 * k, base - 210 * k), (x - 20 * k, base - 260 * k), (x + 90 * k, base - 230 * k),
                                     (x + 60 * k, base - 200 * k), (x - 10 * k, base - 224 * k), (x - 90 * k, base - 190 * k)])
    arco = [(x - 60 * k, base)] + [(x + math.cos(math.pi - i / 14 * math.pi) * 60 * k,
                                    base - math.sin(math.pi - i / 14 * math.pi) * 120 * k) for i in range(1, 14)] + [(x + 60 * k, base)]
    pygame.draw.polygon(tela, (30, 24, 20), arco)
    luz = pygame.Surface((int(200 * k), int(200 * k)), pygame.SRCALPHA)
    for i in range(8):
        pygame.draw.circle(luz, (255, 220, 120, 14), (int(100 * k), int(110 * k)), int((90 - i * 10) * k))
    tela.blit(luz, (x - 100 * k, base - 170 * k))
    for i in range(6):                                             # brilhinhos dourados saindo
        a = t * 1.5 + i
        pygame.draw.circle(tela, (255, 230, 140), (int(x + math.cos(a) * 30 * k), int(base - 60 * k + math.sin(a * 1.3) * 30 * k)), 2)
    if int(t * 10) % 43 != 0:
        for ox in (-16, 16):
            pygame.draw.ellipse(tela, (250, 120, 60), R(x + ox * k - 6 * k, base - 92 * k, 12 * k, 8 * k))
