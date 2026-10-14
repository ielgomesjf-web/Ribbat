"""A história contada em quadrinhos (sem texto: só desenho e balão com figura)."""
import math
import random

import pygame

import desenho as D
from config import *  # noqa: F401,F403
from entidades import R

PAPEL = (250, 244, 228)


def gradiente(s, topo, baixo):
    w, h = s.get_size()
    for y in range(h):
        k = y / h
        pygame.draw.line(s, [int(topo[i] + (baixo[i] - topo[i]) * k) for i in range(3)], (0, y), (w, y))


def balao(s, caixa, ponta):
    """Balão de fala branco, com rabinho apontando pra quem fala."""
    cx, cy = caixa.center
    base_l = (cx - caixa.width * 0.12, caixa.bottom - caixa.height * 0.18)
    base_r = (cx + caixa.width * 0.08, caixa.bottom - caixa.height * 0.12)
    pygame.draw.polygon(s, PRETO, [base_l, ponta, base_r])
    pygame.draw.ellipse(s, PRETO, caixa.inflate(6, 6))
    pygame.draw.ellipse(s, BRANCO, caixa)
    pygame.draw.polygon(s, BRANCO, [(base_l[0] + 3, base_l[1] - 2), (ponta[0], ponta[1] - 4),
                                    (base_r[0] - 3, base_r[1] - 2)])


def estrelas(s, t, n, semente, area_y):
    rnd = random.Random(semente)
    w = s.get_width()
    for i in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, area_y)
        brilho = 160 + int(95 * abs(math.sin(t * 2 + i)))
        pygame.draw.circle(s, (brilho, brilho, brilho), (int(x), int(y)), 1 + (i % 3 == 0))


def vitoria_regia(s, x, y, w, cor=(70, 140, 76), agua=(40, 80, 110)):
    pygame.draw.ellipse(s, cor, R(x - w / 2, y - w * 0.18, w, w * 0.36))
    pygame.draw.polygon(s, agua, [(x, y), (x + w / 2, y - w * 0.08), (x + w / 2, y + w * 0.08)])


def casinha(s, x, base, k=1.0):
    """Casinha de folha da Vila dos Sapos."""
    pygame.draw.ellipse(s, (60, 130, 66), R(x - 34 * k, base - 50 * k, 68 * k, 70 * k))
    pygame.draw.ellipse(s, (90, 170, 80), R(x - 28 * k, base - 46 * k, 50 * k, 40 * k))
    pygame.draw.rect(s, (60, 130, 66), R(x - 34 * k, base - 16 * k, 68 * k, 16 * k))
    pygame.draw.ellipse(s, (50, 34, 22), R(x - 10 * k, base - 26 * k, 20 * k, 30 * k))
    pygame.draw.line(s, (40, 100, 50), (x, base - 50 * k), (x + 6 * k, base - 60 * k), max(1, int(3 * k)))


# ---------------------------------------------------------------- painéis
def balao_mapa(s, caixa, ponta, etapa, t):
    """Balão de pensamento com o MAPA do caminho até o pergaminho (sem texto).
    etapa = quantos lugares o Ribbat já passou (1 = pântano, 2 = lamaçal, 3 = formigueiro, 4 = quintal)."""
    for i, k in enumerate((0.25, 0.5, 0.75)):        # bolinhas do pensamento
        x = ponta[0] + (caixa.centerx - ponta[0]) * k
        y = ponta[1] + (caixa.bottom - ponta[1]) * k
        pygame.draw.circle(s, PRETO, (int(x), int(y)), 5 + i * 3)
        pygame.draw.circle(s, BRANCO, (int(x), int(y)), 3 + i * 3)
    for dx, dy, rr in ((-0.32, -0.1, 0.32), (0.0, -0.2, 0.36), (0.3, -0.08, 0.3), (-0.15, 0.18, 0.3), (0.2, 0.2, 0.3)):
        pygame.draw.circle(s, PRETO, (int(caixa.centerx + dx * caixa.width), int(caixa.centery + dy * caixa.height)),
                           int(rr * caixa.height) + 3)
    for dx, dy, rr in ((-0.32, -0.1, 0.32), (0.0, -0.2, 0.36), (0.3, -0.08, 0.3), (-0.15, 0.18, 0.3), (0.2, 0.2, 0.3)):
        pygame.draw.circle(s, (252, 248, 236), (int(caixa.centerx + dx * caixa.width), int(caixa.centery + dy * caixa.height)),
                           int(rr * caixa.height))
    pygame.draw.ellipse(s, (252, 248, 236), caixa.inflate(-20, -16))
    # o caminho: 3 lugares, a névoa (o que ainda não se sabe) e o pergaminho lá no fim
    x0, x1, yb = caixa.left + 40, caixa.right - 40, caixa.centery + 6
    pontos = [(x0 + (x1 - x0) * i / 5, yb + math.sin(i * 1.7) * 14) for i in range(6)]
    for a, b in zip(pontos, pontos[1:]):
        n = int(math.dist(a, b) // 9)
        for k in range(n):
            if k % 2 == 0:
                pygame.draw.line(s, (150, 120, 80), (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n),
                                 (a[0] + (b[0] - a[0]) * (k + 1) / n, a[1] + (b[1] - a[1]) * (k + 1) / n), 3)
    (px, py), (lx, ly), (fx, fy), (qx, qy), (nx, ny), (sx, sy) = pontos
    pygame.draw.rect(s, (238, 220, 190), R(qx - 12, qy - 10, 24, 18))                       # quintal: casinha
    pygame.draw.polygon(s, (176, 80, 60), [(qx - 15, qy - 9), (qx, qy - 22), (qx + 15, qy - 9)])
    pygame.draw.ellipse(s, (82, 160, 76), R(px - 14, py - 7, 28, 14))                     # pântano: vitória-régia
    pygame.draw.polygon(s, (252, 248, 236), [(px, py), (px + 14, py - 3), (px + 14, py + 3)])
    pygame.draw.line(s, (120, 92, 76), (lx, ly + 8), (lx, ly - 14), 3)                     # lamaçal: árvore seca
    pygame.draw.line(s, (120, 92, 76), (lx, ly - 6), (lx - 9, ly - 14), 2)
    pygame.draw.line(s, (120, 92, 76), (lx, ly - 2), (lx + 8, ly - 10), 2)
    pygame.draw.polygon(s, (150, 110, 70), [(fx - 16, fy + 8), (fx, fy - 12), (fx + 16, fy + 8)])  # formigueiro
    pygame.draw.ellipse(s, (40, 26, 16), R(fx - 4, fy - 12, 8, 5))
    pygame.draw.polygon(s, (124, 112, 104), [(nx - 18, ny + 8), (nx, ny - 22), (nx + 18, ny + 8)])  # a montanha
    pygame.draw.polygon(s, (240, 246, 252), [(nx, ny - 22), (nx - 7, ny - 10), (nx + 7, ny - 10)])
    for i in range(4):                                                                       # nas nuvens (o desconhecido)
        pygame.draw.circle(s, (220, 222, 232), (int(nx - 14 + i * 9), int(ny + 4 + (i % 2) * 4)), 7)
    D.pergaminho(s, sx, sy, 0.55, brilho=t * 1.5)                                            # o PERGAMINHO
    for i, (cx, cy) in enumerate(pontos[:5]):
        if i < etapa:                                                                        # lugar vencido: bandeirinha
            pygame.draw.line(s, (120, 110, 90), (cx + 10, cy - 4), (cx + 10, cy - 24), 2)
            D.bandeirinha(s, cx + 11, cy - 24, 0.45, t)
    ox, oy = pontos[min(etapa, 5) - 1]                                                       # onde o Ribbat está
    ax, ay = pontos[min(etapa, 5)]
    pula = abs(math.sin(t * 4)) * 4
    pygame.draw.circle(s, (40, 112, 50), (int(ox), int(oy - 20 - pula)), 11)
    pygame.draw.circle(s, (112, 186, 80), (int(ox), int(oy - 20 - pula)), 9)
    for ex in (-4, 4):
        pygame.draw.circle(s, BRANCO, (int(ox + ex), int(oy - 28 - pula)), 4)
        pygame.draw.circle(s, PRETO, (int(ox + ex + 1), int(oy - 28 - pula)), 2)
    mx, my = (ox + ax) / 2, (oy + ay) / 2 - 22                                               # setinha pro próximo
    pygame.draw.polygon(s, (230, 90, 60), [(mx + 8, my), (mx - 4, my - 7), (mx - 4, my + 7)])


def painel_noite(s, t):
    """1) De noite, na beira da lagoa, o vô conta a história do pergaminho."""
    w, h = s.get_size()
    gradiente(s, (18, 26, 64), (58, 68, 120))
    estrelas(s, t, 40, 3, h * 0.55)
    pygame.draw.circle(s, (244, 242, 214), (w - 70, 52), 28)
    pygame.draw.circle(s, (218, 214, 186), (w - 78, 46), 6)
    pygame.draw.circle(s, (218, 214, 186), (w - 62, 62), 4)
    agua = (36, 72, 104)
    pygame.draw.rect(s, agua, R(0, h - 70, w, 70))
    for i in range(5):
        pygame.draw.line(s, (70, 110, 150), (40 + i * 90 + math.sin(t + i) * 6, h - 40 + i % 2 * 14),
                         (70 + i * 90 + math.sin(t + i) * 6, h - 40 + i % 2 * 14), 2)
    vitoria_regia(s, 120, h - 52, 170, agua=agua)
    vitoria_regia(s, 330, h - 48, 130, agua=agua)
    # foguinho
    fx, fy = 228, h - 60
    pygame.draw.circle(s, (90, 60, 30), (fx, fy + 4), 16)
    for i in range(3):
        a = math.sin(t * 9 + i * 2) * 3
        pygame.draw.polygon(s, [(250, 120, 40), (255, 190, 60), (255, 240, 160)][i],
                            [(fx - 10 + i * 3, fy), (fx + a, fy - 26 + i * 7), (fx + 10 - i * 3, fy)])
    D.desenhar_sapo(s, 110, h - 56, 1, "parado", escala=1.9, estilo="vovo")
    pygame.draw.line(s, MADEIRA_ESC, (162, h - 108), (176, h - 54), 4)      # bengala
    pygame.draw.arc(s, MADEIRA_ESC, R(150, h - 118, 16, 16), 0, math.pi, 4)
    D.desenhar_sapo(s, 335, h - 52, -1, "parado", escala=1.25, estilo="filhote")
    balao(s, R(160, 14, 170, 96), (150, h - 132))
    D.pergaminho(s, 245, 62, 1.2, brilho=t * 0.8)


def painel_lenda(s, t):
    """2) A lenda (em cor de foto antiga): o pergaminho no alto do morro, guardado por bichos."""
    w, h = s.get_size()
    gradiente(s, (240, 220, 178), (214, 186, 140))
    for i, (cor, base, amp) in enumerate((((206, 172, 122), 120, 50), ((176, 138, 92), 160, 34))):
        pts = [(0, h)] + [(x, base + math.sin(x / (60 + i * 30) + i) * amp) for x in range(0, w + 10, 10)] + [(w, h)]
        pygame.draw.polygon(s, cor, pts)
    pygame.draw.polygon(s, (150, 112, 70), [(w * 0.38, h), (w * 0.55, 46), (w * 0.72, h)])   # morro
    D.pergaminho(s, w * 0.55, 34, 0.9, brilho=t * 1.2)
    for x in range(0, w, 34):                                                              # floresta
        alt = 60 + (x * 37 % 40)
        pygame.draw.polygon(s, (110, 78, 48), [(x - 20, h), (x, h - alt), (x + 20, h)])
    # aranha pendurada
    pygame.draw.line(s, (90, 64, 40), (70, 0), (70, 96 + math.sin(t * 2) * 8), 1)
    ay = 100 + math.sin(t * 2) * 8
    for sx in (-1, 1):
        for i in range(4):
            pygame.draw.lines(s, (70, 48, 30), False, [(70 + sx * 5, ay - 3 + i * 3), (70 + sx * 15, ay - 10 + i * 5),
                                                       (70 + sx * 20, ay + 2 + i * 5)], 2)
    pygame.draw.circle(s, (70, 48, 30), (70, int(ay)), 11)
    # fila de formigas
    for i in range(5):
        D.desenhar_formiga(s, w - 210 + i * 34, h - 30, 26, 16, -1, t * 10 + i)
    # moldura de "lembrança"
    pygame.draw.rect(s, (120, 86, 50), s.get_rect(), 10)


def painel_manha(s, t):
    """3) De manhã, o vô dá o lenço e as 3 bandeiras da vila pro Ribbat."""
    w, h = s.get_size()
    gradiente(s, (150, 200, 240), (255, 220, 170))
    pygame.draw.circle(s, (255, 236, 150), (w - 60, 60), 30)
    pygame.draw.rect(s, (96, 170, 84), R(0, h - 54, w, 54))
    casinha(s, 60, h - 54, 0.9)
    casinha(s, w - 70, h - 54, 1.1)
    D.desenhar_sapo(s, 140, h - 50, 1, "parado", escala=1.9, estilo="vovo")
    D.desenhar_sapo(s, 320, h - 50, -1, "parado", escala=1.3, estilo="ribbat")
    for i in range(3):                                                    # as 3 bandeiras na mão do vô
        bx = 196 + i * 12
        pygame.draw.line(s, (230, 220, 190), (bx, h - 64), (bx, h - 116), 3)
        D.bandeirinha(s, bx + 1, h - 116, 0.55, t + i)
    for i in range(3):                                                    # brilhinho no olho
        a = t * 3 + i * 2.1
        pygame.draw.circle(s, AMARELO, (int(330 + math.cos(a) * 26), int(h - 120 + math.sin(a) * 10)), 3)
    balao(s, R(110, 12, 200, 80), (150, h - 118))
    for i in range(3):
        D.bandeirinha(s, 150 + i * 44, 34, 0.9, t + i)


def painel_partida(s, t):
    """4) Ribbat pula rumo à floresta. Lá atrás, o vô dá tchau."""
    w, h = s.get_size()
    gradiente(s, (255, 196, 140), (190, 224, 240))
    pygame.draw.circle(s, (255, 230, 140), (90, h - 70), 40)
    pygame.draw.rect(s, (96, 170, 84), R(0, h - 54, w, 54))
    pygame.draw.polygon(s, (186, 150, 100), [(0, h - 30), (w, h - 44), (w, h - 26), (0, h - 12)])  # trilha
    casinha(s, 40, h - 54, 0.6)
    D.desenhar_sapo(s, 96, h - 52, 1, "parado", escala=0.8, estilo="vovo")
    tchau = math.sin(t * 8) * 6
    pygame.draw.line(s, (132, 160, 104), (108, h - 70), (114 + tchau, h - 88), 4)
    for x in range(w - 150, w + 30, 30):                                  # floresta escura
        alt = 120 + (x * 53 % 50)
        pygame.draw.rect(s, (70, 50, 34), R(x - 4, h - 60, 8, 20))
        pygame.draw.polygon(s, (30, 70, 40), [(x - 26, h - 54), (x, h - alt), (x + 26, h - 54)])
    pulo = abs(math.sin(t * 2.5)) * 30
    rx = 230 + (t * 20) % 40
    for i in range(3):
        pygame.draw.line(s, BRANCO, (rx - 50 - i * 6, h - 70 - pulo + i * 8), (rx - 30, h - 70 - pulo + i * 8), 2)
    D.desenhar_sapo(s, rx, h - 40 - pulo, 1, "pulo" if pulo > 4 else "parado", escala=1.4, estilo="ribbat")


def painel_toca(s, t):
    """Fim da fase: Ribbat chega na toca do chefão... e algo olha lá de dentro."""
    w, h = s.get_size()
    gradiente(s, (40, 50, 80), (90, 80, 100))
    estrelas(s, t, 30, 9, h * 0.4)
    for x in range(-20, w + 40, 60):
        pygame.draw.polygon(s, (36, 60, 46), [(x - 40, h - 60), (x, h - 200 - (x * 31 % 60)), (x + 40, h - 60)])
    pygame.draw.rect(s, TERRA, R(0, h - 64, w, 64))
    pygame.draw.rect(s, GRAMA, R(0, h - 64, w, 10))
    D.desenhar_toca(s, w * 0.62, h - 64, t, 1.6)
    D.desenhar_sapo(s, w * 0.2, h - 64, 1, "parado", escala=2.2, estilo="ribbat")
    gota_y = h - 160 + (t * 30) % 16
    pygame.draw.polygon(s, (150, 210, 255), [(w * 0.2 - 30, gota_y - 10), (w * 0.2 - 36, gota_y + 2),
                                             (w * 0.2 - 24, gota_y + 2)])
    pygame.draw.circle(s, (150, 210, 255), (int(w * 0.2 - 30), int(gota_y + 3)), 6)
    D.desenhar_alerta(s, w * 0.2 + 30, h - 190)


def painel_vitoria(s, t):
    """Venceu a Viúva Negra: ela enrolada na própria teia, e o Ribbat pensa no caminho até o pergaminho."""
    w, h = s.get_size()
    gradiente(s, (30, 22, 26), (74, 52, 40))
    luz = pygame.Surface((w, h), pygame.SRCALPHA)
    for k in range(10):
        pygame.draw.circle(luz, (255, 236, 150, 9), (int(w * 0.32), int(h * 0.45)), 220 - k * 20)
    s.blit(luz, (0, 0))
    pygame.draw.rect(s, (54, 38, 28), R(0, h - 70, w, 70))
    pygame.draw.rect(s, (84, 62, 44), R(0, h - 70, w, 6))
    # a viúva embrulhada, de cabeça pra baixo, pendurada
    vx = w * 0.72
    balanco = math.sin(t * 1.5) * 6
    pygame.draw.line(s, (220, 220, 235), (vx, 0), (vx + balanco, 120), 2)
    casulo = R(vx + balanco - 60, 120, 120, 170)
    pygame.draw.ellipse(s, (210, 206, 220), casulo)
    for i in range(9):
        yy = casulo.top + 14 + i * 17
        pygame.draw.arc(s, (150, 146, 166), R(casulo.left + 4, yy - 8, casulo.width - 8, 22), math.pi, math.tau, 2)
    for sx in (-1, 1):  # patinhas pra fora do casulo
        for i in range(2):
            px = casulo.centerx + sx * (30 + i * 14)
            pygame.draw.lines(s, (16, 14, 22), False, [(px, casulo.top + 20), (px + sx * 20, casulo.top - 4 - i * 8),
                                                        (px + sx * 34, casulo.top + 6)], 4)
    olho_y = casulo.bottom - 34
    for ox in (-14, 14):  # olhinhos tontos
        pygame.draw.line(s, (200, 30, 40), (casulo.centerx + ox - 5, olho_y - 5), (casulo.centerx + ox + 5, olho_y + 5), 3)
        pygame.draw.line(s, (200, 30, 40), (casulo.centerx + ox + 5, olho_y - 5), (casulo.centerx + ox - 5, olho_y + 5), 3)
    for i in range(3):
        a = t * 3 + i * math.tau / 3
        x, y = casulo.centerx + math.cos(a) * 40, casulo.bottom + 16 + math.sin(a) * 8
        pygame.draw.circle(s, AMARELO, (int(x), int(y)), 5)
    # Ribbat comemorando e pensando no caminho até o pergaminho
    pulo = abs(math.sin(t * 3)) * 18
    rx = w * 0.3
    D.desenhar_sapo(s, rx, h - 70 - pulo, 1, "pulo" if pulo > 6 else "parado", escala=2.4, estilo="ribbat")
    balao_mapa(s, R(rx - 150, 16, 380, 150), (rx + 30, h - 160 - pulo), 1, t)


def painel_toca_besouro(s, t):
    """Fim do Lamaçal: Ribbat chega na toca do Besouro-rinoceronte. Um chifre enorme brilha lá dentro..."""
    import lamacal as L
    w, h = s.get_size()
    gradiente(s, (200, 120, 90), (240, 200, 150))
    pygame.draw.circle(s, (255, 210, 140), (int(w * 0.85), 90), 50)
    pygame.draw.rect(s, (86, 60, 40), R(0, h - 64, w, 64))
    pygame.draw.line(s, (150, 118, 86), (0, h - 63), (w, h - 63), 3)
    L.desenhar_toca_besouro(s, w * 0.62, h - 64, t, 1.5)
    D.desenhar_sapo(s, w * 0.2, h - 64, 1, "parado", escala=2.2, estilo="ribbat")
    gota_y = h - 160 + (t * 30) % 16
    pygame.draw.circle(s, (150, 210, 255), (int(w * 0.2 - 30), int(gota_y + 3)), 6)
    D.desenhar_alerta(s, w * 0.2 + 30, h - 190)
    if int(t * 4) % 6 == 0:    # tremidinha no chão: tem algo GRANDE lá dentro
        for i in range(5):
            pygame.draw.circle(s, (120, 90, 60), (int(w * 0.5 + i * 30), int(h - 70 - (i % 2) * 6)), 3)


def painel_vitoria_besouro(s, t):
    """Venceu o Besouro: o tatu de barriga pra cima e o Ribbat pensando no caminho (2 lugares vencidos)."""
    w, h = s.get_size()
    gradiente(s, (50, 34, 24), (110, 76, 50))
    luz = pygame.Surface((w, h), pygame.SRCALPHA)
    for k in range(10):
        pygame.draw.circle(luz, (255, 220, 150, 9), (int(w * 0.3), int(h * 0.45)), 220 - k * 20)
    s.blit(luz, (0, 0))
    pygame.draw.rect(s, (86, 60, 40), R(0, h - 70, w, 70))
    pygame.draw.line(s, (150, 118, 86), (0, h - 69), (w, h - 69), 3)
    # o tatu de barriga pra cima
    bx, by = w * 0.7, h - 70
    pygame.draw.ellipse(s, (104, 84, 66), R(bx - 104, by - 92, 208, 96))
    pygame.draw.ellipse(s, (232, 190, 178), R(bx - 96, by - 88, 192, 80))
    for i in range(5):
        pygame.draw.arc(s, (190, 160, 148), R(bx - 80 + i * 32, by - 80, 30, 60), 0, math.pi, 2)
    for i in range(6):  # patinhas pro alto, tremendo
        px = bx - 70 + i * 28
        tremor = math.sin(t * 20 + i) * 3
        pygame.draw.lines(s, (150, 118, 108), False, [(px, by - 80), (px + tremor, by - 118), (px + 8 + tremor, by - 128)], 5)
    pygame.draw.ellipse(s, (214, 168, 156), R(bx + 80, by - 56, 50, 30))     # focinho
    pygame.draw.polygon(s, (58, 26, 12), [(bx + 96, by - 30), (bx + 124, by + 6), (bx + 108, by - 32)])  # chifre (de ponta-cabeça)
    pygame.draw.line(s, PRETO, (bx + 104, by - 48), (bx + 112, by - 40), 3)  # olho de X
    pygame.draw.line(s, PRETO, (bx + 112, by - 48), (bx + 104, by - 40), 3)
    for i in range(3):
        a = t * 3 + i * math.tau / 3
        pygame.draw.circle(s, AMARELO, (int(bx + 100 + math.cos(a) * 30), int(by - 90 + math.sin(a) * 8)), 5)
    for i in range(6):  # caquinhos da armadura no chão
        pygame.draw.polygon(s, (104, 52, 28), [(bx - 160 + i * 60, by), (bx - 150 + i * 60, by - 10), (bx - 140 + i * 60, by)])
    # Ribbat comemorando e pensando no caminho até o pergaminho
    pulo = abs(math.sin(t * 3)) * 18
    rx = w * 0.27
    D.desenhar_sapo(s, rx, h - 70 - pulo, 1, "pulo" if pulo > 6 else "parado", escala=2.4, estilo="ribbat")
    balao_mapa(s, R(rx - 130, 16, 380, 150), (rx + 30, h - 160 - pulo), 2, t)


def painel_camara_real(s, t):
    """Fim do Formigueiro: a entrada da câmara real. Antenas ENORMES aparecem lá dentro..."""
    import formigueiro as FM
    w, h = s.get_size()
    gradiente(s, (30, 20, 14), (70, 48, 34))
    pygame.draw.rect(s, (92, 64, 44), R(0, 0, w, 40))
    pygame.draw.rect(s, (92, 64, 44), R(0, h - 64, w, 64))
    pygame.draw.line(s, (140, 104, 72), (0, h - 64), (w, h - 64), 3)
    FM.desenhar_camara_real(s, w * 0.64, h - 64, t, 1.6)
    for i in range(4):                       # guardas: formigas paradas dos lados
        D.desenhar_formiga(s, w * 0.42 + (i % 2) * 300 - (i // 2) * 30, h - 80, 26, 16, -1 if i % 2 else 1, 0, parada=True)
    D.desenhar_sapo(s, w * 0.17, h - 64, 1, "parado", escala=2.2, estilo="ribbat")
    gota_y = h - 160 + (t * 30) % 16
    pygame.draw.circle(s, (150, 210, 255), (int(w * 0.17 - 30), int(gota_y + 3)), 6)
    D.desenhar_alerta(s, w * 0.17 + 30, h - 190)


def painel_vitoria_rainha(s, t):
    """Venceu a Rainha: ela tonta no chão, a coroa caiu, e o Ribbat pensando no caminho (3 lugares vencidos)."""
    w, h = s.get_size()
    gradiente(s, (40, 26, 18), (90, 62, 42))
    luz = pygame.Surface((w, h), pygame.SRCALPHA)
    for k in range(10):
        pygame.draw.circle(luz, (255, 220, 150, 9), (int(w * 0.28), int(h * 0.45)), 220 - k * 20)
    s.blit(luz, (0, 0))
    pygame.draw.rect(s, (54, 38, 26), R(0, h - 70, w, 70))
    pygame.draw.line(s, (140, 104, 72), (0, h - 69), (w, h - 69), 3)
    bx, by = w * 0.72, h - 70                    # a rainha deitada, tontinha
    pygame.draw.ellipse(s, (124, 36, 22), R(bx - 110, by - 60, 110, 62))
    for k in range(3):
        pygame.draw.line(s, (46, 12, 8), (bx - 90 + k * 26, by - 58), (bx - 84 + k * 26, by), 3)
    pygame.draw.ellipse(s, (124, 36, 22), R(bx - 10, by - 44, 56, 40))
    pygame.draw.circle(s, (124, 36, 22), (int(bx + 66), int(by - 26)), 24)
    pygame.draw.ellipse(s, (220, 236, 246), R(bx - 70, by - 96, 90, 40))
    for ox in (-6, 6):                           # olhos de X
        pygame.draw.line(s, PRETO, (bx + 70 + ox - 4, by - 34), (bx + 70 + ox + 4, by - 26), 3)
        pygame.draw.line(s, PRETO, (bx + 70 + ox + 4, by - 34), (bx + 70 + ox - 4, by - 26), 3)
    for i in range(3):
        a = t * 3 + i * math.tau / 3
        pygame.draw.circle(s, AMARELO, (int(bx + 66 + math.cos(a) * 32), int(by - 64 + math.sin(a) * 8)), 5)
    cx = bx + 130                                # a coroa caída no chão
    pygame.draw.polygon(s, (246, 200, 70), [(cx - 16, by), (cx - 16, by - 18), (cx - 8, by - 8), (cx, by - 22),
                                            (cx + 8, by - 8), (cx + 16, by - 18), (cx + 16, by)])
    pygame.draw.circle(s, (220, 40, 60), (int(cx), int(by - 8)), 4)
    pulo = abs(math.sin(t * 3)) * 18
    rx = w * 0.27
    D.desenhar_sapo(s, rx, h - 70 - pulo, 1, "pulo" if pulo > 6 else "parado", escala=2.4, estilo="ribbat")
    balao_mapa(s, R(rx - 130, 16, 380, 150), (rx + 30, h - 160 - pulo), 3, t)


def painel_portinha(s, t):
    """Fim do Quintal: a portinha de gato da casa... e dois olhos amarelos lá dentro."""
    import quintal as Q
    w, h = s.get_size()
    gradiente(s, (120, 190, 245), (214, 238, 250))
    pygame.draw.rect(s, (104, 190, 76), R(0, h - 64, w, 64))
    Q.desenhar_porta(s, w * 0.62, h - 64, t, 1.3)
    D.desenhar_sapo(s, w * 0.2, h - 64, 1, "parado", escala=2.2, estilo="ribbat")
    gota_y = h - 160 + (t * 30) % 16
    pygame.draw.circle(s, (150, 210, 255), (int(w * 0.2 - 30), int(gota_y + 3)), 6)
    D.desenhar_alerta(s, w * 0.2 + 30, h - 190)


def painel_vitoria_gato(s, t):
    """Venceu o Gato: ele esparramado no tapete da sala, tontinho (o laser ainda no nariz), e o Ribbat no sofá."""
    w, h = s.get_size()
    s.fill((236, 226, 200))
    pygame.draw.rect(s, (176, 124, 78), R(0, h - 70, w, 70))
    pygame.draw.ellipse(s, (200, 90, 80), R(w * 0.32, h - 84, w * 0.6, 40))
    pygame.draw.rect(s, (90, 140, 200), R(30, h - 230, 260, 120), border_radius=24)          # sofá
    pygame.draw.rect(s, (110, 170, 220), R(60, h - 170, 200, 50), border_radius=14)
    D.desenhar_sapo(s, 170, h - 170, 1, "pulo" if int(t * 3) % 2 else "parado", escala=1.8, estilo="ribbat")
    import gato as GT                                                                           # o gato de verdade, deitado e tonto
    from chefe import ESC, _Pincel
    g = GT.Gato()
    g.modo, g.estado, g.t, g.dir = "sala", "chegando", t, -1
    k = 1.5
    sf = pygame.Surface((380 * ESC, 260 * ESC), pygame.SRCALPHA)
    GT._gato_lado(_Pincel(sf, 190, 250), g, t)
    img = pygame.transform.smoothscale(sf, (int(380 * k), int(260 * k)))
    img = pygame.transform.flip(img, True, False)
    gx, gy = w * 0.64, h - 60
    s.blit(img, img.get_rect(midbottom=(gx, gy + 14)))
    pygame.draw.circle(s, (255, 40, 40), (int(gx - 200), int(gy - 50)), 5)                     # o laser no nariz
    balao_mapa(s, R(w * 0.06, 14, 380, 150), (170, h - 230), 4, t)


def painel_cume(s, t):
    """Fim da Montanha: lá no topo, acima das nuvens, a caverna com o brilho dourado... e olhos lá dentro."""
    import montanha as MT
    w, h = s.get_size()
    gradiente(s, (40, 50, 110), (150, 170, 220))
    rnd = random.Random(5)
    for i in range(30):
        pygame.draw.circle(s, (240, 240, 255), (rnd.randint(0, w), rnd.randint(0, h // 2)), 1)
    for i in range(6):                                                                       # nuvens lá embaixo
        pygame.draw.circle(s, (240, 244, 252), (int(i * 170 + 40), h - 40), 70)
    pygame.draw.rect(s, (124, 112, 104), R(0, h - 70, w, 70))
    pygame.draw.rect(s, (240, 246, 252), R(0, h - 70, w, 12))
    MT.desenhar_cume(s, w * 0.64, h - 70, t, 1.2)
    D.desenhar_sapo(s, w * 0.2, h - 70, 1, "parado", escala=2.2, estilo="ribbat")
    gota_y = h - 166 + (t * 30) % 16
    pygame.draw.circle(s, (150, 210, 255), (int(w * 0.2 - 30), int(gota_y + 3)), 6)
    D.desenhar_alerta(s, w * 0.2 + 30, h - 196)


PAINEIS_INTRO = [painel_noite, painel_lenda, painel_manha, painel_partida]


def desenhar_pagina(tela, paineis, mostrar, alfa_ultimo, t, fonte):
    """Página de quadrinho 2x2. `mostrar` = quantos painéis já apareceram."""
    tela.fill(PAPEL)
    margem, vao = 22, 14
    w = (LARGURA - 2 * margem - vao) // 2
    h = (ALTURA - 2 * margem - vao - 26) // 2
    caixas = [R(margem + (i % 2) * (w + vao), margem + (i // 2) * (h + vao), w, h) for i in range(4)]
    for i in range(min(mostrar, len(paineis))):
        surf = pygame.Surface((w, h))
        paineis[i](surf, t)
        desliza = 0
        if i == mostrar - 1 and alfa_ultimo < 1:
            surf.set_alpha(int(255 * alfa_ultimo))
            desliza = (1 - alfa_ultimo) * 16
        tela.blit(surf, caixas[i].move(0, desliza))
        pygame.draw.rect(tela, PRETO, caixas[i].move(0, desliza), 4)
    if alfa_ultimo >= 1 and int(t * 2) % 2 == 0:
        D.tecla(tela, fonte, LARGURA - 60, ALTURA - 34, "enter", 40)


def desenhar_painel_unico(tela, painel, t, fonte):
    tela.fill(PAPEL)
    caixa = R(22, 22, LARGURA - 44, ALTURA - 72)
    surf = pygame.Surface(caixa.size)
    painel(surf, t)
    tela.blit(surf, caixa)
    pygame.draw.rect(tela, PRETO, caixa, 4)
    if int(t * 2) % 2 == 0:
        D.tecla(tela, fonte, LARGURA - 60, ALTURA - 38, "enter", 40)


# ---------------------------------------------------------------- O FINAL (venceu a corrida contra a Águia)
def _aguia(s, pose, x, y, d, k, asa=0.3, bico=False):
    import aguia as AG
    AG.blit_aguia(s, AG.sprite(pose, round(asa, 1), bico), x, y, d, k=k)


def painel_final_pergaminho(s, t):
    """1) Lá no topo: o Ribbat ergue o PERGAMINHO. A águia chega atrasada e abaixa a cabeça (respeito!)."""
    w, h = s.get_size()
    gradiente(s, (255, 196, 120), (255, 236, 190))
    for i in range(12):                                                                      # raios de sol
        a = i / 12 * math.tau + t * 0.1
        pygame.draw.line(s, (255, 230, 170), (w * 0.3, h * 0.35), (w * 0.3 + math.cos(a) * 600, h * 0.35 + math.sin(a) * 600), 6)
    for i in range(6):
        pygame.draw.circle(s, (255, 250, 244), (int(i * 90 + 20), h - 30), 50)
    pygame.draw.polygon(s, (110, 100, 96), [(w * 0.08, h), (w * 0.18, h - 70), (w * 0.44, h - 74), (w * 0.54, h)])
    pygame.draw.polygon(s, (244, 248, 252), [(w * 0.17, h - 68), (w * 0.45, h - 72), (w * 0.43, h - 62), (w * 0.19, h - 60)])
    base = h - 72
    D.desenhar_sapo(s, w * 0.3, base, 1, "parado", escala=1.6, estilo="ribbat")
    for lado in (-1, 1):                                                                      # bracinhos erguendo o pergaminho
        pygame.draw.line(s, (40, 112, 50), (w * 0.3 + lado * 14, base - 50), (w * 0.3 + lado * 22, base - 82), 7)
        pygame.draw.line(s, (112, 186, 80), (w * 0.3 + lado * 14, base - 50), (w * 0.3 + lado * 22, base - 82), 4)
    D.pergaminho(s, w * 0.3 + 4, base - 92 + math.sin(t * 3) * 3, 1.1, brilho=t * 1.5)
    for i in range(6):                                                                       # brilhinhos
        a = t * 2 + i
        pygame.draw.circle(s, (255, 250, 200), (int(w * 0.3 + math.cos(a) * 60), int(base - 92 + math.sin(a * 1.3) * 40)), 2)
    pygame.draw.polygon(s, (110, 100, 96), [(w * 0.6, h), (w * 0.66, h - 44), (w * 0.9, h - 48), (w * 0.98, h)])
    pygame.draw.polygon(s, (244, 248, 252), [(w * 0.66, h - 42), (w * 0.9, h - 46), (w * 0.88, h - 38), (w * 0.68, h - 36)])
    _aguia(s, "pousada", w * 0.78, h - 46 - 72 * 0.62, -1, 0.62, 0.0)                    # a águia chegou atrasada...
    pygame.draw.circle(s, (150, 210, 255), (int(w * 0.78 - 70), int(h - 150 + (t * 20) % 10)), 4)


def painel_final_carona(s, t):
    """2) A volta pra casa: o Ribbat de carona nas costas da águia, por cima das nuvens."""
    w, h = s.get_size()
    gradiente(s, (110, 160, 230), (220, 236, 252))
    rnd = random.Random(3)
    for i in range(10):
        x = (rnd.randint(0, w) - t * 60 * (1 + i % 3)) % (w + 120) - 60
        pygame.draw.circle(s, (252, 252, 255), (int(x), rnd.randint(h // 2, h)), rnd.randint(26, 44))
    pygame.draw.polygon(s, (90, 130, 90), [(0, h), (w * 0.15, h - 40), (w * 0.3, h)])         # lá embaixo: o pântano
    x, y = w * 0.5, h * 0.48 + math.sin(t * 2) * 8
    _aguia(s, "alto", x, y, 1, 0.62, (math.sin(t * 5) + 1) / 2)
    D.desenhar_sapo(s, x - 6, y - 14, 1, "parado", escala=1.0, estilo="ribbat")
    D.pergaminho(s, x - 24, y - 30, 0.4)
    for i in range(3):                                                                       # vento
        yy = y - 40 + i * 30
        pygame.draw.line(s, BRANCO, (x - 200 - i * 20, yy), (x - 140 - i * 20, yy), 2)


def painel_final_casa(s, t):
    """3) De noite, na lagoa: o vô e o filhote abrem o pergaminho com o Ribbat. Lá dentro: o caminho todo."""
    w, h = s.get_size()
    gradiente(s, (18, 26, 64), (58, 68, 120))
    estrelas(s, t, 40, 3, h * 0.55)
    agua = (36, 72, 104)
    pygame.draw.rect(s, agua, R(0, h - 60, w, 60))
    vitoria_regia(s, w * 0.5, h - 44, w * 0.8, agua=agua)
    luz = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(8):
        pygame.draw.circle(luz, (255, 220, 140, 14), (int(w * 0.5), int(h * 0.42)), 160 - i * 18)
    s.blit(luz, (0, 0))
    D.desenhar_sapo(s, w * 0.2, h - 50, 1, "parado", escala=1.6, estilo="vovo")
    D.desenhar_sapo(s, w * 0.8, h - 50, -1, "pulo" if int(t * 3) % 2 else "parado", escala=1.1, estilo="filhote")
    D.desenhar_sapo(s, w * 0.62, h - 50, -1, "parado", escala=1.4, estilo="ribbat")
    # o pergaminho aberto: o mapa do caminho, com as 5 bandeirinhas
    px, py, pw, ph = w * 0.5 - 110, h * 0.42 - 58, 220, 100
    pygame.draw.rect(s, (242, 224, 172), R(px, py, pw, ph))
    pygame.draw.rect(s, (150, 110, 60), R(px, py, pw, ph), 2)
    for ex in (px, px + pw):
        pygame.draw.ellipse(s, (214, 190, 130), R(ex - 7, py - 4, 14, ph + 8))
        pygame.draw.ellipse(s, (150, 110, 60), R(ex - 7, py - 4, 14, ph + 8), 2)
    pts = [(px + 24 + i * 34, py + 60 + math.sin(i * 1.7) * 14) for i in range(6)]
    for a, b in zip(pts, pts[1:]):
        pygame.draw.line(s, (150, 110, 60), a, b, 2)
    for i, (cx, cy) in enumerate(pts[:5]):
        pygame.draw.line(s, (120, 110, 90), (cx, cy), (cx, cy - 18), 2)
        D.bandeirinha(s, cx + 1, cy - 18, 0.35, t)
    pygame.draw.circle(s, (200, 40, 40), (int(pts[5][0]), int(pts[5][1])), 6)               # e o coração no fim
    pygame.draw.circle(s, (200, 40, 40), (int(pts[5][0] + 7), int(pts[5][1])), 6)
    pygame.draw.polygon(s, (200, 40, 40), [(pts[5][0] - 6, pts[5][1] + 2), (pts[5][0] + 13, pts[5][1] + 2),
                                           (pts[5][0] + 3.5, pts[5][1] + 14)])
    for i in range(10):                                                                      # vagalumes
        a = t * 0.7 + i
        pygame.draw.circle(s, (250, 240, 140), (int((i * 97 + math.sin(a) * 30) % w), int(40 + (i * 53) % 120 + math.cos(a) * 10)), 2)


_fonte_fim = None


def painel_final_titulo(s, t):
    """4) FIM: o nome do jogo, o Ribbat na vitória-régia com o pergaminho e a águia voando lá longe."""
    global _fonte_fim
    w, h = s.get_size()
    gradiente(s, (250, 160, 110), (255, 222, 170))
    pygame.draw.circle(s, (255, 240, 190), (int(w * 0.5), int(h * 0.72)), 70)
    agua = (90, 120, 150)
    pygame.draw.rect(s, agua, R(0, h - 60, w, 60))
    vitoria_regia(s, w * 0.5, h - 46, 200, agua=agua)
    D.desenhar_sapo(s, w * 0.5, h - 50, 1, "parado", escala=1.5, estilo="ribbat")
    D.pergaminho(s, w * 0.5 + 44, h - 70, 0.6, brilho=t * 1.2)
    _aguia(s, "alto", w * 0.2 + (t * 20) % (w * 0.6), 60, 1, 0.22, (math.sin(t * 5) + 1) / 2)
    if _fonte_fim is None:
        _fonte_fim = pygame.font.SysFont("segoeui,arial", 54, bold=True)
    for dx, dy, cor in ((3, 3, (90, 50, 30)), (0, 0, (255, 250, 236))):
        img = _fonte_fim.render("RIBBAT", True, cor)
        s.blit(img, img.get_rect(center=(w / 2 + dx, h * 0.3 + dy)))


def painel_vitoria_vovo(s, t):
    """Venceu o Vô: ele volta pro tamanho normal, rindo, e dá a bengala pro Ribbat segurar (orgulho de vô)."""
    w, h = s.get_size()
    gradiente(s, (18, 26, 64), (58, 68, 120))
    estrelas(s, t, 40, 9, h * 0.55)
    agua = (36, 72, 104)
    pygame.draw.rect(s, agua, R(0, h - 70, w, 70))
    vitoria_regia(s, w * 0.5, h - 52, w * 0.7, agua=agua)
    D.desenhar_sapo(s, w * 0.36, h - 56, 1, "parado", escala=2.0, estilo="vovo")
    D.desenhar_sapo(s, w * 0.64, h - 56, -1, "pulo" if int(t * 3) % 2 else "parado", escala=1.8, estilo="ribbat")
    pygame.draw.line(s, MADEIRA_ESC, (w * 0.64 - 24, h - 150), (w * 0.64 - 14, h - 62), 5)       # a bengala com o neto
    pygame.draw.arc(s, MADEIRA_ESC, R(w * 0.64 - 36, h - 162, 22, 22), 0, math.pi, 5)
    for i in range(3):                                                                       # risadas do vô (sem texto: notinhas)
        a = t * 2 + i
        x, y = w * 0.36 + 40 + i * 26, h - 190 - (t * 30 + i * 18) % 40
        pygame.draw.circle(s, (250, 240, 200), (int(x), int(y)), 5)
        pygame.draw.line(s, (250, 240, 200), (x + 4, y), (x + 4, y - 16), 2)
    for i in range(10):
        a = t * 0.7 + i
        pygame.draw.circle(s, (250, 240, 140), (int((i * 97 + math.sin(a) * 30) % w), int(40 + (i * 53) % 120)), 2)
    pygame.draw.circle(s, (230, 60, 80), (int(w * 0.5), int(h - 230)), 10)                  # coração no meio
    pygame.draw.circle(s, (230, 60, 80), (int(w * 0.5 + 14), int(h - 230)), 10)
    pygame.draw.polygon(s, (230, 60, 80), [(w * 0.5 - 10, h - 226), (w * 0.5 + 24, h - 226), (w * 0.5 + 7, h - 206)])


PAINEIS_FINAL = [painel_final_pergaminho, painel_final_carona, painel_final_casa, painel_final_titulo]
