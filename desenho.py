"""Tudo que é desenhado. Sem imagens: tudo feito com formas."""
import math
import random

import pygame

from config import *  # noqa: F401,F403
from entidades import R

# =====================================================================
# Sapos (Ribbat e o vô) - de perfil, estilo sapo de verdade fofinho
# =====================================================================
ESTILOS = {
    "ribbat": dict(pele=(112, 186, 80), escura=(62, 124, 54), contorno=(30, 70, 34), barriga=(240, 232, 178),
                   manchas=(78, 146, 60), listra=(176, 218, 116), iris=(236, 184, 52), lenco=True),
    "filhote": dict(pele=(112, 186, 80), escura=(62, 124, 54), contorno=(30, 70, 34), barriga=(240, 232, 178),
                    manchas=(78, 146, 60), listra=(176, 218, 116), iris=(236, 184, 52), lenco=False),
    "vovo": dict(pele=(132, 160, 104), escura=(84, 108, 66), contorno=(44, 58, 38), barriga=(228, 222, 192),
                 manchas=(100, 124, 80), listra=(184, 198, 152), iris=(206, 174, 96), lenco=False, vovo=True),
}
_cache = {}
ONDAS = (0.0, 1.6, 0.0, -1.6)


def _sapo_bruto(pose, e, estilo, onda):
    """Desenha o sapo virado pra DIREITA. Caixa de 80x52 unidades, chão em y=46."""
    c = ESTILOS[estilo]
    s = pygame.Surface((int(80 * e), int(52 * e)), pygame.SRCALPHA)
    oy = -2 if pose == "anda" else 0

    def P(x, y):
        return ((x + 16) * e, (y + 4 + oy) * e)

    def circ(x, y, r, cor):
        pygame.draw.circle(s, cor, P(x, y), max(1, r * e))

    def eli(x, y, w, h, cor):
        px, py = P(x, y)
        pygame.draw.ellipse(s, cor, R(px, py, w * e, h * e))

    def pol(pts, cor):
        pygame.draw.polygon(s, cor, [P(*p) for p in pts])

    def linha(pts, cor, larg):
        pygame.draw.lines(s, cor, False, [P(*p) for p in pts], max(1, int(larg * e)))

    def osso(a, b, r1, r2, cor):
        (x1, y1), (x2, y2) = a, b
        ang = math.atan2(y2 - y1, x2 - x1)
        nx, ny = -math.sin(ang), math.cos(ang)
        pol([(x1 + nx * r1, y1 + ny * r1), (x2 + nx * r2, y2 + ny * r2),
             (x2 - nx * r2, y2 - ny * r2), (x1 - nx * r1, y1 - ny * r1)], cor)
        circ(x1, y1, r1, cor)
        circ(x2, y2, r2, cor)

    pele, esc = c["pele"], c["escura"]

    # ---- perna de trás (atrás do corpo quando esticada) ----
    def perna_de_tras():
        if pose == "parado":
            osso((10, 40), (24, 43.5), 3.6, 3.0, esc)
            osso((22, 44), (36, 45), 2.6, 2.0, esc)
            circ(37, 45, 2.0, esc)
            circ(34.5, 46.2, 1.7, esc)
        elif pose == "anda":
            osso((8, 37), (22, 40.5), 3.6, 3.0, esc)
            osso((20, 41), (33, 42.5), 2.6, 2.0, esc)
            circ(34, 42.5, 2.0, esc)
        elif pose == "pulo":
            osso((14, 34), (2, 39), 6.5, 4.0, pele)
            osso((2, 39), (-8, 43), 3.4, 2.6, esc)
            osso((-8, 43), (-18, 45), 2.4, 1.8, esc)
            circ(-19, 45, 1.9, esc)
        elif pose == "queda":
            osso((16, 36), (12, 43), 6.5, 4.0, pele)
            osso((12, 43), (20, 46.5), 3.2, 2.6, esc)
            osso((20, 46.5), (30, 47), 2.4, 1.8, esc)
        elif pose == "investida":
            osso((12, 32), (-2, 33), 6.0, 4.0, pele)
            osso((-2, 33), (-14, 34), 3.2, 2.6, esc)
            osso((-14, 34), (-24, 34), 2.4, 1.8, esc)

    perna_de_tras()

    # ---- corpo ----
    eli(6, 20, 32, 24, pele)                # traseiro
    eli(26, 12, 30, 23, pele)               # cabeça
    pol([(16, 20), (34, 12), (46, 15), (42, 36), (16, 43)], pele)
    circ(42, 14, 8.5, pele)                 # calombo do olho
    eli(21, 30, 27, 13.5, c["barriga"])     # barriga clarinha
    linha([(9, 25), (19, 18.5), (31, 13.5), (37, 10.5)], c["listra"], 1.7)  # dobra das costas
    for mx, my, mr in ((16, 27, 2.6), (24, 22, 2.0), (11, 33, 2.0), (30, 18.5, 1.5), (20, 33, 1.7)):
        circ(mx, my, mr, c["manchas"])

    # ---- coxa (por cima do corpo quando sentado) ----
    if pose in ("parado", "anda"):
        dy = -3 if pose == "anda" else 0
        eli(3, 27 + dy, 25, 15, pele)
        linha([(9, 30 + dy), (12, 40 + dy)], esc, 1.6)
        linha([(16, 29 + dy), (19, 40 + dy)], esc, 1.6)

    # ---- braço da frente ----
    if pose == "parado":
        osso((42, 32), (44, 43), 3.0, 2.4, pele)
        circ(46.5, 44.6, 1.9, esc)
        circ(43.5, 45.2, 1.9, esc)
    elif pose == "anda":
        osso((42, 31), (48, 40), 3.0, 2.4, pele)
        circ(50, 41, 1.9, esc)
    elif pose == "pulo":
        osso((41, 32), (35, 39), 2.8, 2.2, pele)
    elif pose == "queda":
        osso((43, 32), (50, 41), 3.0, 2.4, pele)
        circ(51.5, 42.5, 2.0, esc)
    elif pose == "investida":
        osso((40, 33), (30, 38), 2.6, 2.1, pele)

    # ---- lenço da Vila dos Sapos ----
    if c["lenco"]:
        pol([(31, 19), (22, 15.5 + onda), (21.5, 20 + onda), (30, 22)], LENCO)
        pol([(31, 21), (24, 24 + onda * 0.6), (25, 27.5 + onda * 0.6), (32, 23.5)], LENCO)
        osso((31.5, 19), (36, 32), 2.2, 2.2, LENCO)
        pol([(35, 27), (44, 33), (37, 37)], LENCO)                       # pontinha no peito
        linha([(35, 27.5), (43, 32.8)], (170, 36, 40), 0.9)
        circ(31, 20.5, 2.6, (190, 44, 46))

    # ---- rosto ----
    circ(52.5, 18.5, 0.9, c["contorno"])                                      # narina
    linha([(55.5, 24), (51, 26.4), (44, 27.2), (38.5, 25.6)], c["contorno"], 1.3)  # boca
    circ(48, 27.8, 2.4, (238, 156, 136))                                     # bochecha
    if pose == "tonto":
        linha([(39, 10), (47, 18)], c["contorno"], 1.6)
        linha([(47, 10), (39, 18)], c["contorno"], 1.6)
    else:
        circ(43, 13.5, 6.2, c["iris"])
        circ(44, 13.6, 4.3, PRETO)
        circ(45.6, 11.6, 1.6, BRANCO)
        circ(42.3, 15.6, 0.8, BRANCO)
        linha([(35.5, 10), (39, 6.6), (45, 6), (50, 9)], c["escura"], 1.3)  # pálpebra
    if c.get("vovo"):
        pygame.draw.circle(s, (70, 56, 40), P(43, 13.5), 7.6 * e, max(1, int(1.2 * e)))  # óculos
        linha([(35.6, 13), (30, 14)], (70, 56, 40), 1.1)
        pol([(37, 6.5), (44, 3), (51, 5), (49, 7.5), (42, 6.4), (38, 8)], BRANCO)       # sobrancelha
        circ(51, 28, 2.4, BRANCO)                                                        # bigode
        circ(47.5, 29, 2.0, BRANCO)
    return s


def sprite_sapo(pose="parado", d=1, escala=0.75, estilo="ribbat", onda=0):
    chave = (pose, d, escala, estilo, onda)
    img = _cache.get(chave)
    if img is None:
        ss = 3
        bruto = _sapo_bruto(pose, escala * ss, estilo, ONDAS[onda % 4])
        cont = pygame.mask.from_surface(bruto).to_surface(
            setcolor=ESTILOS[estilo]["contorno"], unsetcolor=(0, 0, 0, 0))
        final = pygame.Surface(bruto.get_size(), pygame.SRCALPHA)
        k = max(1, int(1.3 * escala * ss))
        for dx, dy in ((-k, 0), (k, 0), (0, -k), (0, k), (-k, -k), (k, k), (-k, k), (k, -k)):
            final.blit(cont, (dx, dy))
        final.blit(bruto, (0, 0))
        w, h = bruto.get_size()
        img = pygame.transform.smoothscale(final, (w // ss, h // ss))
        if d < 0:
            img = pygame.transform.flip(img, True, False)
        _cache[chave] = img
    return img


def orelhas_coelho(tela, cx, base, d, pose, escala, sq=1.0):
    """Orelhinhas de coelho (Ribbat = Ribbit + Rabbit). Ficam atrás da cabeça."""
    def P(x, y):
        return cx + d * (x - 30) * escala, base - (46 - y) * escala * sq
    para_tras = {"pulo": 10, "investida": 16, "queda": -4}.get(pose, 0)
    for bx, by, tx, ty in ((32, 12, 20 - para_tras, -24), (38, 10, 36 - para_tras, -30)):
        b, p = P(bx, by), P(tx, ty)
        ang = math.atan2(p[1] - b[1], p[0] - b[0])
        nx, ny = -math.sin(ang), math.cos(ang)
        for larg, cor in ((8.0, (60, 50, 50)), (6.6, (240, 236, 232)), (3.2, (246, 170, 186))):
            w = larg * escala
            m = ((b[0] + p[0]) / 2, (b[1] + p[1]) / 2)
            pts = [b, (m[0] + nx * w, m[1] + ny * w), p, (m[0] - nx * w, m[1] - ny * w)]
            pygame.draw.polygon(tela, cor, pts)


def desenhar_sapo(tela, cx, base, d=1, pose="parado", sq=1.0, onda=0, escala=0.75, estilo="ribbat", orelhas=False,
                  chapeu=None):
    """Desenha com os pés em `base` e o meio do corpo em `cx`. (orelhinhas de coelho ganham do chapéu)"""
    if orelhas:
        orelhas_coelho(tela, cx, base, d, pose, escala, sq)
    img = sprite_sapo(pose, d, escala, estilo, onda)
    if abs(sq - 1) > 0.03:
        w, h = img.get_size()
        img = pygame.transform.smoothscale(img, (int(w / math.sqrt(sq)), int(h * sq)))
    w, h = img.get_size()
    fx = (46 / 80 if d > 0 else 34 / 80) * w
    tela.blit(img, (cx - fx, base - 50 / 52 * h))
    if chapeu and not orelhas:
        import chapeus
        chapeus.desenhar(tela, chapeu, cx, base, d, escala, sq, pose)


# =====================================================================
# Cenário
# =====================================================================
def criar_ceu():
    ceu = pygame.Surface((LARGURA, ALTURA))
    for y in range(ALTURA):
        k = y / ALTURA
        cor = [int(CEU_TOPO[i] + (CEU_BAIXO[i] - CEU_TOPO[i]) * k) for i in range(3)]
        pygame.draw.line(ceu, cor, (0, y), (LARGURA, y))
    return ceu


def criar_tiles():
    rnd = random.Random(7)

    def terra():
        s = pygame.Surface((TILE, TILE))
        s.fill(TERRA)
        for _ in range(6):
            pygame.draw.circle(s, TERRA_ESC, (rnd.randint(3, 28), rnd.randint(3, 28)), rnd.randint(1, 3))
        return s

    grama = terra()
    pygame.draw.rect(grama, GRAMA, (0, 0, TILE, 10))
    for i in range(0, TILE, 4):
        pygame.draw.line(grama, GRAMA_ESC, (i, 9), (i + 2, 13), 2)
    pygame.draw.line(grama, GRAMA_CLARA, (0, 1), (TILE, 1), 2)

    madeira = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    pygame.draw.rect(madeira, MADEIRA, (0, 2, TILE, 14), border_radius=3)
    pygame.draw.rect(madeira, MADEIRA_ESC, (0, 2, TILE, 14), 2, border_radius=3)
    pygame.draw.line(madeira, MADEIRA_ESC, (4, 9), (20, 9), 1)
    pygame.draw.circle(madeira, MADEIRA_ESC, (26, 9), 2)

    teia = pygame.Surface((TILE, TILE - 10), pygame.SRCALPHA)
    cor = (*TEIA, 200)
    base = TILE - 10
    for x in (0, 8, 16, 24, 32):
        pygame.draw.line(teia, cor, (16, base), (x, 0), 1)
    for k in (6, 12, 18):
        pygame.draw.arc(teia, cor, R(16 - k * 1.3, base - k, k * 2.6, k * 2), 0, math.pi, 1)

    return {"grama": grama, "terra": [terra() for _ in range(3)], "madeira": madeira, "teia": teia}


def desenhar_fundo(tela, ceu, nuvens, cam):
    tela.blit(ceu, (0, 0))
    larg_nuvem = LARGURA + 400
    for nx, ny, ns in nuvens:
        x = (nx - cam * 0.1) % larg_nuvem - 200
        for dx, dy, k in ((0, 0, 1.0), (ns * 0.8, 6, 0.8), (-ns * 0.8, 8, 0.7)):
            pygame.draw.circle(tela, (245, 250, 255), (int(x + dx), int(ny + dy)), int(ns * 0.6 * k))
    for cor, fator, base, amp, onda in ((MORRO_LONGE, 0.2, 300, 40, 170), (MORRO_PERTO, 0.45, 370, 28, 95)):
        pts = [(0, ALTURA)]
        for x in range(0, LARGURA + 17, 16):
            w = x + cam * fator
            pts.append((x, base + math.sin(w / onda) * amp + math.sin(w / (onda * 0.37)) * amp * 0.3))
        pts.append((LARGURA, ALTURA))
        pygame.draw.polygon(tela, cor, pts)


def desenhar_caverna(tela, cav, ox, oy):
    """Fundo escuro do túnel + as encostas do morro dos dois lados."""
    x0, x1 = cav["ini"] * TILE - ox, (cav["fim"] + 1) * TILE - ox
    topo, teto, chao = cav["topo"] * TILE - oy, cav["teto"] * TILE - oy, cav["chao"] * TILE - oy
    larg = (chao - topo) * 0.7
    for lado, x in ((-1, x0), (1, x1)):
        encosta = [(x, topo + 6), (x + lado * larg, chao), (x, chao)]
        pygame.draw.polygon(tela, TERRA_ESC, encosta)
        pygame.draw.line(tela, GRAMA, (x, topo + 4), (x + lado * larg, chao - 2), 8)
    pygame.draw.rect(tela, (58, 38, 26), R(x0, teto, x1 - x0, chao - teto))
    for i in range(int((x1 - x0) / 40)):
        rx = x0 + 20 + i * 40
        pygame.draw.lines(tela, (92, 62, 36), False, [(rx, teto), (rx + 4, teto + 10), (rx - 2, teto + 18)], 2)


def desenhar_pedra(tela, r, semente):
    """Pedrona redonda e rachada, com musgo em cima."""
    rnd = random.Random(semente)
    cx, cy = r.centerx, r.centery + 2
    rx, ry = r.width / 2 + 3, r.height / 2 + 2
    pts = []
    for i in range(18):
        a = i / 18 * math.tau
        k = rnd.uniform(0.9, 1.04)
        pts.append((cx + math.cos(a) * rx * k, min(r.bottom, cy + math.sin(a) * ry * k)))
    pygame.draw.polygon(tela, ROCHA_ESC, [(x, y + 3) for x, y in pts])
    pygame.draw.polygon(tela, ROCHA, pts)
    pygame.draw.ellipse(tela, (166, 164, 172), R(cx - rx * 0.7, cy - ry * 0.85, rx * 0.9, ry * 0.6))
    pygame.draw.ellipse(tela, (114, 112, 122), R(cx - rx * 0.2, cy + ry * 0.2, rx * 1.0, ry * 0.65))
    pygame.draw.polygon(tela, PRETO, pts, 2)
    pygame.draw.lines(tela, ROCHA_ESC, False, [(cx - 6, cy - ry + 6), (cx + 2, cy - 6), (cx - 4, cy + 4),
                                               (cx + 6, cy + ry - 8)], 2)
    pygame.draw.lines(tela, ROCHA_ESC, False, [(cx + 2, cy - 6), (cx + 14, cy - 2)], 2)
    for i in range(5):
        mx = cx - rx * 0.6 + i * rx * 0.3
        pygame.draw.circle(tela, (96, 150, 70), (int(mx), int(cy - ry * 0.88 + abs(i - 2) * 3)), 5)


def desenhar_toca(tela, x, base, t, k=1.0):
    """Toca do chefão: buraco escuro num morro de terra, com raízes e olhos brilhando."""
    w, h = 300 * k, 170 * k
    pts = [(x - w / 2, base)]
    for i in range(1, 24):
        a = math.pi - i / 24 * math.pi
        pts.append((x + math.cos(a) * w / 2, base - math.sin(a) * h * (0.92 + 0.08 * math.sin(i * 1.7))))
    pts.append((x + w / 2, base))
    pygame.draw.polygon(tela, TERRA, pts)
    pygame.draw.lines(tela, GRAMA, False, pts[1:-1], int(12 * k))
    pygame.draw.lines(tela, GRAMA_CLARA, False, [(px, py - 4 * k) for px, py in pts[3:-3]], max(1, int(3 * k)))
    rnd = random.Random(5)
    for _ in range(14):
        pygame.draw.circle(tela, TERRA_ESC, (int(x + rnd.uniform(-0.4, 0.4) * w),
                                             int(base - rnd.uniform(0.1, 0.6) * h)), int(rnd.randint(2, 5) * k))
    # boca da toca (arco achatado no chão)
    bw, bh = 110 * k, 92 * k
    arco = [(x - bw / 2, base)]
    for i in range(1, 16):
        a = math.pi - i / 16 * math.pi
        arco.append((x + math.cos(a) * bw / 2, base - math.sin(a) * bh))
    arco.append((x + bw / 2, base))
    pygame.draw.polygon(tela, (14, 10, 16), arco)
    for i, (px, py) in enumerate(arco[1:-1]):
        if i % 2 == 0:
            pygame.draw.circle(tela, ROCHA_ESC, (int(px), int(py)), int(9 * k))
            pygame.draw.circle(tela, ROCHA, (int(px - 1), int(py - 2)), int(7 * k))
    for i, rx in enumerate((-30, -8, 18, 34)):
        balanco = math.sin(t * 1.5 + i) * 2 * k
        comp = (22 + i * 7 % 14) * k
        topo = base - bh * 0.88 * math.sqrt(max(0, 1 - (rx * k / (bw / 2)) ** 2))
        pygame.draw.lines(tela, MADEIRA_ESC, False, [(x + rx * k, topo), (x + rx * k + balanco, topo + comp / 2),
                                                     (x + rx * k - balanco, topo + comp)], max(1, int(3 * k)))
    if int(t * 10) % 37 != 0:  # pisca de vez em quando
        for ox in (-16, 16):
            ex, ey = x + ox * k, base - 40 * k
            pygame.draw.ellipse(tela, (250, 210, 60), R(ex - 7 * k, ey - 5 * k, 14 * k, 10 * k))
            pygame.draw.ellipse(tela, PRETO, R(ex - 1.5 * k, ey - 4 * k, 3 * k, 8 * k))


def desenhar_espinhos(tela, x, base):
    for i in range(3):
        px = x + 4 + i * 10
        pygame.draw.polygon(tela, (110, 90, 70), [(px, base), (px + 5, base - 16), (px + 10, base)])
        pygame.draw.line(tela, (220, 210, 190), (px + 5, base - 16), (px + 5, base - 10), 1)


def desenhar_bandeira(tela, x, base, b, t):
    pygame.draw.rect(tela, ROCHA_ESC, R(x - 9, base - 8, 18, 8), border_radius=3)
    pygame.draw.rect(tela, (230, 220, 190), R(x - 2, base - b.ALT, 4, b.ALT))
    pygame.draw.circle(tela, AMARELO, (int(x), int(base - b.ALT)), 4)
    if not b.ativa:
        return
    fy = base - 22 - b.subida * (b.ALT - 34)
    bandeirinha(tela, x + 2, fy, 1.0, t)


def bandeirinha(tela, x, y, k, t):
    """A bandeira verde da Vila dos Sapos, com a vitória-régia."""
    onda = math.sin(t * 6) * 3 * k
    pts = [(x, y), (x + 34 * k, y + 2 * k + onda), (x + 32 * k, y + 22 * k + onda), (x, y + 20 * k)]
    pygame.draw.polygon(tela, (96, 196, 84), pts)
    pygame.draw.polygon(tela, (40, 112, 50), pts, max(1, int(2 * k)))
    cx, cy = x + 16 * k, y + 11 * k + onda / 2
    pygame.draw.circle(tela, (230, 245, 160), (int(cx), int(cy)), int(6 * k))
    pygame.draw.line(tela, (96, 196, 84), (cx, cy), (cx + 6 * k, cy - 4 * k), max(1, int(2 * k)))


# =====================================================================
# Bichos
# =====================================================================
def desenhar_formiga(tela, x, y, w, h, d, anim, parada=False):
    cor, escura = (128, 48, 32), (70, 24, 14)
    meio = x + w / 2
    by = y + h - 8
    for i, px in enumerate((-6, 0, 6)):
        o = 0 if parada else math.sin(anim + i * 2) * 3
        pygame.draw.line(tela, escura, (meio + px, by), (meio + px - 4 + o, y + h), 2)
        pygame.draw.line(tela, escura, (meio + px, by), (meio + px + 4 - o, y + h), 2)
    pygame.draw.ellipse(tela, cor, R(meio - d * 9 - 8, by - 7, 16, 12))
    pygame.draw.circle(tela, cor, (int(meio), int(by - 1)), 4)
    hx, hy = meio + d * 9, by - 3
    pygame.draw.circle(tela, cor, (int(hx), int(hy)), 6)
    pygame.draw.circle(tela, BRANCO, (int(hx + d * 2), int(hy - 1)), 2)
    mexe = math.sin(anim * 0.7) * 2
    pygame.draw.line(tela, escura, (hx, hy - 4), (hx + d * 7, hy - 11 + mexe), 2)
    pygame.draw.line(tela, escura, (hx - d * 2, hy - 5), (hx + d * 2, hy - 13 - mexe), 2)


def desenhar_alerta(tela, x, y):
    """Balãozinho com '!' (desenhado, não é texto)."""
    pygame.draw.circle(tela, PRETO, (int(x), int(y)), 10)
    pygame.draw.circle(tela, AMARELO, (int(x), int(y)), 8)
    pygame.draw.rect(tela, PRETO, R(x - 1.5, y - 6, 3, 8))
    pygame.draw.circle(tela, PRETO, (int(x), int(y + 5)), 2)


def desenhar_aranha(tela, x, y, topo, t, mira=0.0):
    pygame.draw.line(tela, (230, 230, 240), (x, topo), (x, y), 1)
    if mira > 0:
        x += math.sin(t * 60) * 2  # tremendo antes de atirar
    mexe = math.sin(t * 4) * 2
    for s in (-1, 1):
        for i in range(4):
            jx, jy = x + s * 6, y - 4 + i * 3
            kx, ky = x + s * 18, y - 12 + i * 6 + mexe * s
            px, py = x + s * 24, y + 2 + i * 6
            pygame.draw.lines(tela, (40, 30, 50), False, [(jx, jy), (kx, ky), (px, py)], 2)
    pygame.draw.circle(tela, (60, 40, 76), (int(x), int(y)), 13)
    pygame.draw.circle(tela, (90, 64, 110), (int(x - 4), int(y - 5)), 4)
    olho = (255, 120, 60) if mira > 0 else (240, 60, 60)
    for ex in (-4, 4):
        pygame.draw.circle(tela, olho, (int(x + ex), int(y + 2)), 3)
    pygame.draw.line(tela, BRANCO, (x - 3, y + 9), (x - 2, y + 13), 2)
    pygame.draw.line(tela, BRANCO, (x + 3, y + 9), (x + 2, y + 13), 2)
    if mira > 0:
        pygame.draw.circle(tela, TEIA, (int(x), int(y + 15)), int(3 + (0.5 - mira) * 8))


def desenhar_bola_teia(tela, x, y, t):
    pygame.draw.circle(tela, TEIA, (int(x), int(y)), 7)
    for i in range(4):
        a = t * 8 + i * math.pi / 2
        pygame.draw.line(tela, (200, 204, 220), (x, y), (x + math.cos(a) * 10, y + math.sin(a) * 10), 1)
    pygame.draw.circle(tela, (200, 204, 220), (int(x), int(y)), 7, 1)


def desenhar_casulo(tela, rect, prog, t):
    """Casulo de teia em volta do Ribbat. Quanto mais ele se debate, mais fios somem."""
    fios = max(2, 7 - int(prog))
    camada = pygame.Surface((56, 48), pygame.SRCALPHA)
    tremor = math.sin(t * 40) * 1.5 if prog > 0.5 else 0
    for i in range(fios):
        y0 = 8 + i * 6
        pts = [(4 + j * 6 + tremor, y0 + math.sin(j * 1.3 + i * 2) * 3 + j * (1 if i % 2 else -1))
               for j in range(9)]
        pygame.draw.lines(camada, (*TEIA, 210), False, pts, 2)
    pygame.draw.line(camada, (*TEIA, 170), (8, 6), (48, 42), 1)
    pygame.draw.line(camada, (*TEIA, 170), (48, 6), (8, 42), 1)
    tela.blit(camada, (rect.centerx - 28, rect.bottom - 46))


def desenhar_mosquito(tela, x, y, t):
    """Mosquito de cura: corpinho fino, perninhas compridas, ferrãozinho e um coração em cima."""
    asa = 4 + abs(math.sin(t * 40)) * 6
    pygame.draw.ellipse(tela, (220, 236, 250), R(x - 12, y - 6 - asa, 12, asa + 2))
    pygame.draw.ellipse(tela, (220, 236, 250), R(x - 2, y - 7 - asa, 12, asa + 2))
    for i in range(3):
        pygame.draw.lines(tela, (60, 50, 50), False, [(x - 4 + i * 4, y + 2), (x - 9 + i * 5, y + 12), (x - 12 + i * 6, y + 18)], 1)
    pygame.draw.ellipse(tela, (80, 66, 60), R(x - 14, y - 3, 16, 6))       # abdômen fininho
    pygame.draw.circle(tela, (70, 58, 52), (int(x + 4), int(y - 1)), 4)     # tórax
    pygame.draw.circle(tela, (60, 50, 46), (int(x + 9), int(y - 1)), 3)     # cabeça
    pygame.draw.line(tela, (60, 50, 46), (x + 11, y), (x + 19, y + 3), 1)   # ferrãozinho
    pygame.draw.circle(tela, (220, 40, 40), (int(x + 10), int(y - 2)), 1)
    pulsa = 1.0 + 0.15 * math.sin(t * 8)
    desenhar_coracao(tela, int(x - 7 * pulsa), int(y - 30), int(14 * pulsa), True)


def desenhar_mosca(tela, x, y, t):
    asa = 3 + abs(math.sin(t * 25)) * 5
    pygame.draw.ellipse(tela, (215, 235, 250), R(x - 9, y - 4 - asa, 9, asa + 2))
    pygame.draw.ellipse(tela, (215, 235, 250), R(x, y - 4 - asa, 9, asa + 2))
    pygame.draw.ellipse(tela, (50, 50, 60), R(x - 6, y - 4, 12, 8))
    pygame.draw.circle(tela, (210, 40, 40), (int(x + 5), int(y - 1)), 2)


# =====================================================================
# Ícones e teclas (a única "escrita" do jogo são as letrinhas das teclas)
# =====================================================================
def desenhar_coracao(tela, x, y, s, cheio):
    r = s // 4

    def forma(cor, d):
        pygame.draw.circle(tela, cor, (x + r, y + r), r + d)
        pygame.draw.circle(tela, cor, (x + 3 * r, y + r), r + d)
        pygame.draw.polygon(tela, cor, [(x - d, y + r + 1), (x + 4 * r + d, y + r + 1), (x + 2 * r, y + 4 * r + d)])

    forma(PRETO, 2)
    forma((232, 52, 72) if cheio else (80, 60, 70), 0)
    if cheio:
        pygame.draw.circle(tela, (255, 160, 170), (x + r - 1, y + r - 2), 2)


def icone_lingua(tela, x, y, k=1.0):
    pts = [(x, y), (x + 8 * k, y - 3 * k), (x + 16 * k, y + 1 * k), (x + 22 * k, y - 2 * k)]
    pygame.draw.lines(tela, (190, 60, 90), False, pts, max(2, int(6 * k)))
    pygame.draw.lines(tela, (240, 110, 140), False, pts, max(1, int(3 * k)))
    pygame.draw.circle(tela, (240, 110, 140), (int(x + 23 * k), int(y - 2 * k)), int(4 * k))


def icone_investida(tela, x, y, k=1.0):
    for i in range(2):
        ox = x + i * 9 * k
        pygame.draw.lines(tela, (96, 196, 84), False, [(ox, y - 7 * k), (ox + 7 * k, y), (ox, y + 7 * k)],
                          max(2, int(4 * k)))
    for i, dy in enumerate((-5, 0, 5)):
        pygame.draw.line(tela, BRANCO, (x - (12 + i * 3) * k, y + dy * k), (x - 4 * k, y + dy * k), 2)


def icone_pulo(tela, x, y, k=1.0):
    pygame.draw.polygon(tela, BRANCO, [(x, y - 8 * k), (x + 7 * k, y), (x - 7 * k, y)])
    pygame.draw.rect(tela, BRANCO, R(x - 2.5 * k, y, 5 * k, 7 * k))


def tecla(tela, fonte, x, y, rot, w=26, h=24, recarga=0.0):
    """Uma teclinha de teclado. rot pode ser letra, '<', '>', 'enter', 'espaco'.
    recarga (0 a 1) escurece a tecla enquanto a habilidade recarrega."""
    caixa = R(x, y, w, h)
    pygame.draw.rect(tela, (70, 70, 84), caixa.move(0, 3), border_radius=5)
    pygame.draw.rect(tela, (238, 238, 244) if recarga <= 0 else (150, 150, 160), caixa, border_radius=5)
    if recarga > 0:
        pygame.draw.rect(tela, (238, 238, 244), R(x, y + h * min(1, recarga), w, h * (1 - min(1, recarga))),
                         border_radius=5)
    pygame.draw.rect(tela, (70, 70, 84), caixa, 2, border_radius=5)
    cx, cy = caixa.centerx, caixa.centery
    cor = (50, 50, 60)
    if rot == "<":
        pygame.draw.polygon(tela, cor, [(cx - 5, cy), (cx + 4, cy - 6), (cx + 4, cy + 6)])
    elif rot == ">":
        pygame.draw.polygon(tela, cor, [(cx + 5, cy), (cx - 4, cy - 6), (cx - 4, cy + 6)])
    elif rot == "enter":
        pygame.draw.lines(tela, cor, False, [(cx + 7, cy - 6), (cx + 7, cy + 2), (cx - 6, cy + 2)], 2)
        pygame.draw.polygon(tela, cor, [(cx - 9, cy + 2), (cx - 4, cy - 2), (cx - 4, cy + 6)])
    elif rot == "espaco":
        pygame.draw.line(tela, cor, (cx - w / 2 + 8, cy + 3), (cx + w / 2 - 8, cy + 3), 2)
    elif rot:
        img = fonte.render(rot, True, cor)
        tela.blit(img, (cx - img.get_width() / 2, cy - img.get_height() / 2))
    return w


def fmt_tempo(seg):
    """1:23.4 (ou 1:02:03 se passar de uma hora)."""
    seg = max(0.0, seg)
    if seg >= 3600:
        return f"{int(seg // 3600)}:{int(seg % 3600 // 60):02d}:{int(seg % 60):02d}"
    return f"{int(seg // 60)}:{int(seg % 60):02d}.{int(seg * 10) % 10}"


def icone_relogio(tela, x, y, r=10):
    """Cronômetro: botãozinho em cima, mostrador branco e ponteiros."""
    pygame.draw.rect(tela, PRETO, R(x - 3, y - r - 6, 6, 5))
    pygame.draw.circle(tela, PRETO, (int(x), int(y)), r + 2)
    pygame.draw.circle(tela, (250, 248, 236), (int(x), int(y)), r)
    pygame.draw.line(tela, PRETO, (x, y), (x, y - r * 0.7), 2)
    pygame.draw.line(tela, (210, 50, 50), (x, y), (x + r * 0.55, y + r * 0.2), 2)
    pygame.draw.circle(tela, PRETO, (int(x), int(y)), 2)


def icone_trofeu(tela, x, y, k=1.0):
    """Taça dourada (o tempo total do jogo)."""
    ouro, esc = (246, 200, 70), (170, 120, 30)
    for cor, a in ((esc, 2), (ouro, 0)):
        pygame.draw.polygon(tela, cor, [(x - 10 * k - a, y - 12 * k - a), (x + 10 * k + a, y - 12 * k - a),
                                        (x + 6 * k + a, y + 2 * k + a), (x - 6 * k - a, y + 2 * k + a)])
    for lado in (-1, 1):
        pygame.draw.arc(tela, esc, R(x + lado * 11 * k - 5 * k, y - 11 * k, 10 * k, 10 * k), 0, math.tau, 2)
    pygame.draw.rect(tela, esc, R(x - 2 * k, y + 2 * k, 4 * k, 6 * k))
    pygame.draw.rect(tela, esc, R(x - 8 * k, y + 8 * k, 16 * k, 4 * k))
    pygame.draw.line(tela, (255, 240, 170), (x - 5 * k, y - 9 * k), (x - 3 * k, y - 2 * k), 2)


def estrelinha(tela, x, y, r=9, cor=(255, 214, 60)):
    pts = [(x + math.cos(-math.pi / 2 + i * math.pi / 5) * (r if i % 2 == 0 else r * 0.45),
            y + math.sin(-math.pi / 2 + i * math.pi / 5) * (r if i % 2 == 0 else r * 0.45)) for i in range(10)]
    pygame.draw.polygon(tela, PRETO, pts, 0)
    pygame.draw.polygon(tela, cor, [(x + (px - x) * 0.8, y + (py - y) * 0.8) for px, py in pts])


def texto(tela, fonte, s, x, y, centro=False, cor=BRANCO, borda=PRETO):
    img = fonte.render(s, True, cor)
    sombra = fonte.render(s, True, borda)
    if centro:
        x -= img.get_width() / 2
    b = 2 if fonte.get_height() > 30 else 1
    for dx, dy in ((-b, 0), (b, 0), (0, -b), (0, b), (b, b)):
        tela.blit(sombra, (x + dx, y + dy))
    tela.blit(img, (x, y))


def pergaminho(tela, cx, cy, k=1.0, brilho=0.0):
    """O Pergaminho Perdido."""
    if brilho:
        for i in range(8):
            a = brilho + i * math.pi / 4
            pygame.draw.line(tela, (255, 236, 150), (cx + math.cos(a) * 26 * k, cy + math.sin(a) * 20 * k),
                             (cx + math.cos(a) * 44 * k, cy + math.sin(a) * 34 * k), max(1, int(3 * k)))
    w, h = 44 * k, 28 * k
    pygame.draw.rect(tela, (242, 224, 172), R(cx - w / 2, cy - h / 2, w, h))
    pygame.draw.rect(tela, (150, 110, 60), R(cx - w / 2, cy - h / 2, w, h), max(1, int(2 * k)))
    for i in range(3):
        yy = cy - h / 4 + i * h / 4
        pts = [(cx - w / 2 + 8 * k + j * 4 * k, yy + math.sin(j * 1.3 + i) * 1.5 * k) for j in range(8)]
        pygame.draw.lines(tela, (150, 110, 60), False, pts, 1)
    for ex in (cx - w / 2, cx + w / 2):
        pygame.draw.ellipse(tela, (214, 190, 130), R(ex - 5 * k, cy - h / 2 - 3 * k, 10 * k, h + 6 * k))
        pygame.draw.ellipse(tela, (150, 110, 60), R(ex - 5 * k, cy - h / 2 - 3 * k, 10 * k, h + 6 * k),
                            max(1, int(2 * k)))
    pygame.draw.circle(tela, (200, 40, 40), (int(cx + 10 * k), int(cy + h / 2)), int(5 * k))
