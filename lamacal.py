"""Desenhos do Terreno de Lamaçal: fim de tarde, terra rachada, lama movediça, peixe-lama."""
import math
import random

import pygame

from config import *  # noqa: F401,F403
from entidades import R

LAMA_TOPO = (86, 60, 40)
LAMA_BRILHO = (150, 118, 86)
LAMA_DENTRO = (74, 52, 36)
LAMA_ESC = (58, 40, 28)


def criar_fundo():
    ceu = pygame.Surface((LARGURA, ALTURA))
    for y in range(ALTURA):
        k = y / ALTURA
        cor = [int(a + (b - a) * k) for a, b in zip((214, 150, 110), (240, 214, 160))]
        pygame.draw.line(ceu, cor, (0, y), (LARGURA, y))
    pygame.draw.circle(ceu, (255, 220, 150), (720, 150), 60)
    pygame.draw.circle(ceu, (255, 236, 190), (720, 150), 48)
    neblina = pygame.Surface((LARGURA, 120), pygame.SRCALPHA)
    for y in range(120):
        pygame.draw.line(neblina, (240, 210, 170, int(60 * math.sin(y / 120 * math.pi))), (0, y), (LARGURA, y))
    return {"ceu": ceu, "neblina": neblina}


def _arvore_seca(tela, x, base, alt, n):
    cor = (120, 92, 76)
    pygame.draw.polygon(tela, cor, [(x - 10, base), (x - 4, base - alt), (x + 4, base - alt), (x + 10, base)])
    rnd = random.Random(n)
    for i in range(4):
        y = base - alt * (0.45 + i * 0.15)
        lado = 1 if i % 2 else -1
        comp = rnd.randint(30, 60)
        fim = (x + lado * comp, y - comp * 0.6)
        pygame.draw.line(tela, cor, (x, y), fim, 4)
        pygame.draw.line(tela, cor, fim, (fim[0] + lado * 14, fim[1] - 16), 2)


def desenhar_fundo(tela, fundo, cam, t):
    tela.blit(fundo["ceu"], (0, 0))
    # morros de terra rachada lá longe
    for cor, fator, base, amp, onda in (((176, 132, 100), 0.12, 330, 30, 210), ((150, 108, 78), 0.3, 380, 22, 120)):
        pts = [(0, ALTURA)]
        for x in range(0, LARGURA + 17, 16):
            w = x + cam * fator
            pts.append((x, base + math.sin(w / onda) * amp + math.sin(w / (onda * 0.4)) * amp * 0.35))
        pts.append((LARGURA, ALTURA))
        pygame.draw.polygon(tela, cor, pts)
    passo = 300   # árvores secas
    x0 = -((cam * 0.2) % passo) - passo
    i0 = int((cam * 0.2) // passo)
    for i in range(LARGURA // passo + 3):
        n = i0 + i
        _arvore_seca(tela, x0 + i * passo + (n * 83 % 90), 395, 150 + (n * 37 % 60), n)
    tela.blit(fundo["neblina"], (0, 330))
    passo = 140   # moitas de junco
    x0 = -((cam * 0.5) % passo) - passo
    i0 = int((cam * 0.5) // passo)
    for i in range(LARGURA // passo + 3):
        n = i0 + i
        bx = x0 + i * passo + (n * 47 % 60)
        for j in range(7):
            alt = 60 + (n * 13 + j * 29) % 70
            bal = math.sin(t * 1.2 + n + j) * 4
            pygame.draw.line(tela, (126, 128, 70), (bx + j * 6, 470), (bx + j * 6 + bal + (j - 3) * 4, 470 - alt), 3)


def criar_tiles():
    rnd = random.Random(9)

    def dentro():
        s = pygame.Surface((TILE, TILE))
        s.fill(LAMA_DENTRO)
        for _ in range(5):
            pygame.draw.circle(s, LAMA_ESC, (rnd.randint(3, 28), rnd.randint(3, 28)), rnd.randint(1, 3))
        for _ in range(2):
            pygame.draw.circle(s, (110, 90, 70), (rnd.randint(3, 28), rnd.randint(3, 28)), 2)
        return s

    topo = dentro()
    pygame.draw.rect(topo, LAMA_TOPO, (0, 0, TILE, 10))
    pygame.draw.line(topo, LAMA_BRILHO, (0, 1), (TILE, 1), 2)
    pygame.draw.ellipse(topo, (120, 96, 70), (6, 3, 14, 4))
    for x in (5, 19, 27):  # pingos escorrendo
        pygame.draw.line(topo, LAMA_TOPO, (x, 9), (x, 13 + x % 5), 3)
    return {"grama": topo, "terra": [dentro() for _ in range(3)]}


def desenhar_poca(tela, r, t):
    """Lama movediça: mais clara e amarelada que o chão firme, girando e borbulhando."""
    camada = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
    camada.fill((168, 132, 80, 245))
    pygame.draw.rect(camada, (140, 106, 64, 250), R(0, 26, r.width, r.height))
    for i in range(r.width // 46 + 1):            # redemoinhos
        cx = (i * 46 + 20 + t * 8) % (r.width + 40) - 20
        a = t * 1.5 + i
        pygame.draw.arc(camada, (196, 160, 104, 255), R(cx - 14, 8, 28, 10), a, a + 3.6, 2)
    pts = [(x, 2 + math.sin(x / 30 + t * 1.2) * 1.5) for x in range(0, r.width + 8, 8)]
    pygame.draw.lines(camada, (214, 182, 124, 255), False, pts, 3)
    for i in range(r.width // 60 + 1):
        fase = (t * 0.8 + i * 0.37) % 1
        bx = (i * 61 + 23) % max(1, r.width)
        if fase < 0.8:
            pygame.draw.circle(camada, (120, 90, 54, 255), (int(bx), 9), int(2 + fase * 7), 2)
        else:
            for k in range(4):
                a = k * math.pi / 2 + 0.6
                pygame.draw.circle(camada, (120, 90, 54, 255), (int(bx + math.cos(a) * 9), int(7 + math.sin(a) * 3)), 2)
    tela.blit(camada, r.topleft)


def desenhar_lama_grudenta(tela, r, t, semente):
    brilho = math.sin(t * 2 + semente) * 2
    pygame.draw.ellipse(tela, LAMA_ESC, R(r.x - 4, r.y + 2, r.width + 8, r.height + 4))
    pygame.draw.ellipse(tela, (70, 48, 30), R(r.x - 2, r.y, r.width + 4, r.height))
    pygame.draw.ellipse(tela, (130, 100, 70), R(r.x + 6 + brilho, r.y + 2, 10, 4))
    if semente % 3 == 0:
        fase = (t + semente * 0.3) % 2
        if fase < 1:
            pygame.draw.circle(tela, (110, 84, 58), (int(r.centerx), int(r.y + 2 - fase * 4)), int(2 + fase * 3), 1)


_PL_CORPO = (128, 112, 88)        # marrom-acinzentado
_PL_BARRIGA = (206, 194, 168)
_PL_ESC = (66, 54, 40)
_PL_AZUL = (90, 170, 230)


def _olhos_periscopio(sf, x, y, k, pisca=False):
    """Os olhos grandões, saltados e colados no alto da cabeça (igual periscópio)."""
    for dx in (-5 * k, 5 * k):
        pygame.draw.circle(sf, _PL_ESC, (int(x + dx), int(y)), int(7 * k))
        pygame.draw.circle(sf, (226, 216, 180), (int(x + dx), int(y)), int(6 * k))
        if pisca:
            pygame.draw.line(sf, _PL_ESC, (x + dx - 5 * k, y), (x + dx + 5 * k, y), max(1, int(2 * k)))
        else:
            pygame.draw.circle(sf, PRETO, (int(x + dx + 1.5 * k), int(y)), int(3.2 * k))
            pygame.draw.circle(sf, BRANCO, (int(x + dx + 2.4 * k), int(y - 1.2 * k)), max(1, int(1.2 * k)))


def _peixe_lama(sf, cx, base, alt, abre, nadadeira, t, fora):
    """Peixe-lama de lado (virado pra direita): corpo comprido, cabeção, olhos no topo, nadadeiras-bracinho."""
    k = 2
    hy = base - alt * k                                   # altura da cabeça
    # corpo comprido saindo da lama (ou deitado se estiver "fora")
    if fora:
        corpo = [(cx - 44 * k, base - 6 * k), (cx - 10 * k, base - 16 * k), (cx + 18 * k, base - 18 * k),
                 (cx + 30 * k, base - 8 * k), (cx + 20 * k, base), (cx - 40 * k, base)]
        cauda = [(cx - 42 * k, base - 6 * k), (cx - 58 * k, base - 14 * k + math.sin(t * 14) * 5 * k), (cx - 56 * k, base + 2 * k)]
        hx, hy = cx + 22 * k, base - 12 * k
    else:
        corpo = [(cx - 10 * k, base + 4 * k), (cx - 13 * k, hy + 16 * k), (cx + 2 * k, hy + 6 * k), (cx + 14 * k, hy + 14 * k),
                 (cx + 12 * k, base + 4 * k)]
        cauda = None
        hx = cx + 2 * k
    if cauda:
        pygame.draw.polygon(sf, _PL_ESC, cauda)
    pygame.draw.polygon(sf, _PL_CORPO, corpo)
    pygame.draw.polygon(sf, _PL_ESC, corpo, k)
    # nadadeira das costas alta com pintas azuis (levanta quando ataca)
    if nadadeira > 0.05:
        bx = cx - (20 * k if fora else 8 * k)
        by = base - 16 * k if fora else hy + 22 * k
        h = 22 * k * nadadeira
        fin = [(bx - 14 * k, by), (bx - 10 * k, by - h), (bx + 4 * k, by - h * 0.9), (bx + 10 * k, by)]
        pygame.draw.polygon(sf, (70, 56, 44), fin)
        pygame.draw.lines(sf, (150, 210, 240), False, fin[:3], k)
        for i in range(3):
            pygame.draw.circle(sf, _PL_AZUL, (int(bx - 8 * k + i * 6 * k), int(by - h * 0.5 + (i % 2) * 4 * k)), k * 2)
    # listras escuras nas costas e pintinhas azuis brilhantes
    if fora:
        for i in range(4):
            x = cx - 30 * k + i * 12 * k
            pygame.draw.line(sf, _PL_ESC, (x, base - 14 * k), (x - 3 * k, base - 6 * k), k + 1)
        for i in range(6):
            pygame.draw.circle(sf, _PL_AZUL, (int(cx - 34 * k + i * 10 * k), int(base - 9 * k + (i % 2) * 3 * k)), k)
        pygame.draw.polygon(sf, _PL_BARRIGA, [(cx - 30 * k, base - 1 * k), (cx + 18 * k, base - 2 * k), (cx + 12 * k, base)])
    else:
        for i in range(3):
            y = hy + 22 * k + i * 9 * k
            if y < base:
                pygame.draw.line(sf, _PL_ESC, (cx - 11 * k, y), (cx - 4 * k, y + 2 * k), k + 1)
                pygame.draw.circle(sf, _PL_AZUL, (int(cx + 4 * k), int(y + 4 * k)), k)
    # cabeção com a bocona (lábios largos)
    cab = R(hx - 14 * k, hy - 2 * k, 30 * k, 22 * k)
    pygame.draw.ellipse(sf, _PL_CORPO, cab)
    pygame.draw.ellipse(sf, _PL_ESC, cab, k)
    pygame.draw.ellipse(sf, _PL_BARRIGA, R(hx - 6 * k, hy + 10 * k, 20 * k, 9 * k))
    pygame.draw.line(sf, (110, 140, 190), (hx + 2 * k, hy + 14 * k), (hx + 12 * k, hy + 16 * k), k)   # listra azul no queixo
    if abre > 0.2:
        boca = [(hx + 16 * k, hy + 6 * k - abre * 8 * k), (hx + 4 * k, hy + 10 * k), (hx + 16 * k, hy + 12 * k + abre * 8 * k)]
        pygame.draw.polygon(sf, (150, 50, 50), boca)
        for i in range(3):
            tx = hx + 8 * k + i * 3 * k
            pygame.draw.polygon(sf, BRANCO, [(tx, hy + 8 * k - abre * 5 * k), (tx + 1.5 * k, hy + 10 * k - abre * 2 * k),
                                             (tx + 3 * k, hy + 8 * k - abre * 5 * k)])
    else:
        pygame.draw.line(sf, _PL_ESC, (hx + 4 * k, hy + 10 * k), (hx + 15 * k, hy + 9 * k), k)
    # nadadeira peitoral = "bracinho" pra andar na lama
    bx, by = (hx - 8 * k, hy + 18 * k) if fora else (cx + 8 * k, hy + 26 * k)
    pygame.draw.ellipse(sf, (100, 86, 64), R(bx, by, 14 * k, 8 * k))
    for i in range(3):
        pygame.draw.line(sf, _PL_ESC, (bx + 3 * k, by + 4 * k), (bx + (10 + i * 2) * k, by + (2 + i * 3) * k), 1)
    _olhos_periscopio(sf, hx + 4 * k, hy - 2 * k, k)


def desenhar_peixe_lama(tela, p, ox, oy, t):
    """Peixe-lama de verdade (mudskipper): escondido só com os OLHOS pra fora da lama, sobe mordendo e fica se debatendo."""
    x, chao = p.x - ox, p.chao - oy
    if p.estado == "escondido":
        sobe = 6 if p.espia < 0 else 3                      # o olho-periscópio espiando (às vezes sobe mais)
        sf = pygame.Surface((40, 30), pygame.SRCALPHA)
        _olhos_periscopio(sf, 20, 30 - sobe - 6, 1, pisca=int(t * 2 + p.x) % 7 == 0)
        tela.blit(sf, (x - 20, chao - 30 + 4))
        pygame.draw.ellipse(tela, LAMA_TOPO, R(x - 12, chao - 4, 24, 8))
        return
    if p.estado == "tremendo":
        tremor = math.sin(t * 70) * 3
        pygame.draw.ellipse(tela, LAMA_TOPO, R(x - 20 + tremor, chao - 8, 40, 14))
        sf = pygame.Surface((40, 40), pygame.SRCALPHA)
        _olhos_periscopio(sf, 20, 22, 1)
        tela.blit(sf, (x - 20 + tremor, chao - 34))
        for k_ in (-1, 1):
            pygame.draw.circle(tela, LAMA_TOPO, (int(x + k_ * 18 + tremor), int(chao - 12 - abs(tremor) * 2)), 3)
        return
    if p.estado == "mordendo":
        sobe = min(1.0, p.t / 0.12) * 22
        abre = 0.9 if p.t < 0.22 else 0.15
        fora = False
    else:
        sobe, abre, fora = 0, 0.1, True
    sf = pygame.Surface((240, 200), pygame.SRCALPHA)
    _peixe_lama(sf, 120, 190, sobe + 10, abre, 1.0 if p.estado == "mordendo" else 0.4, t, fora)
    img = pygame.transform.smoothscale(sf, (120, 100))
    if p.dir < 0:
        img = pygame.transform.flip(img, True, False)
    tela.blit(img, (x - 60, chao - 95 + 2))
    pygame.draw.ellipse(tela, LAMA_TOPO, R(x - 22, chao - 6, 44, 12))   # lama em volta


def desenhar_toca_besouro(tela, x, base, t, k=1.0):
    """Toca do Besouro-rinoceronte: monte de barro seco com um buraco e um chifre lá dentro."""
    w, h = 340 * k, 190 * k
    pts = [(x - w / 2, base)]
    for i in range(1, 20):
        a = math.pi - i / 20 * math.pi
        pts.append((x + math.cos(a) * w / 2, base - math.sin(a) * h * (0.9 + 0.1 * math.sin(i * 2.3))))
    pts.append((x + w / 2, base))
    pygame.draw.polygon(tela, (150, 108, 74), pts)
    pygame.draw.lines(tela, (176, 134, 96), False, pts[1:-1], max(2, int(6 * k)))
    rnd = random.Random(12)
    for _ in range(9):  # rachaduras
        cx, cy = x + rnd.uniform(-0.35, 0.35) * w, base - rnd.uniform(0.25, 0.75) * h
        pygame.draw.lines(tela, (110, 76, 52), False, [(cx, cy), (cx + 8 * k, cy + 10 * k), (cx + 2 * k, cy + 20 * k)], 2)
    bw, bh = 130 * k, 110 * k
    arco = [(x - bw / 2, base)] + [(x + math.cos(math.pi - i / 16 * math.pi) * bw / 2,
                                    base - math.sin(math.pi - i / 16 * math.pi) * bh) for i in range(1, 16)] + [(x + bw / 2, base)]
    pygame.draw.polygon(tela, (20, 14, 12), arco)
    # chifre aparecendo no escuro
    brilho = 70 + int(30 * math.sin(t * 1.5))
    pygame.draw.polygon(tela, (brilho, brilho - 20, brilho - 30), [(x - 6 * k, base - 30 * k), (x + 24 * k, base - 92 * k),
                                                                    (x + 12 * k, base - 34 * k)])
    if int(t * 10) % 41 != 0:
        for ox in (-22, -4):
            pygame.draw.ellipse(tela, (250, 120, 40), R(x + ox * k - 5 * k, base - 36 * k, 10 * k, 7 * k))
