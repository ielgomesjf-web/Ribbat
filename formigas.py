"""
Desenhista das formigas aladas (guerreira e rainha), com a anatomia de verdade:
cabeça (olho composto, mandíbulas com dentes, antena dobrada em "cotovelo"), tórax, cinturinha de
dois carocinhos (pecíolo), gáster com os segmentos, 6 pernas presas no tórax e 2 pares de asas com nervuras.
A geometria (centro x, centro y, raio x, raio y) vem pronta em pixels, virada pra direita, origem no tórax.
"""
import math

import pygame

from besouro import _brilhante
from chefe import ESC, _Pincel, _pts_elipse

# --- guerreira: cabeção e mandíbulas grandes (é soldado), corpo vermelho-escuro
GUERREIRA = {
    "geo": {"cabeca": (24, -2, 13, 11), "torax": (3, -3, 13, 8), "gaster": (-31, 3, 15, 11)},
    "nos": ((-11, 0, 3.5), (-17, 1, 3.5)),
    "asa": ((2, -9), 56, 15),
    "k": 1.0,
    "cores": {"cabeca": (150, 34, 24), "torax": (118, 28, 20), "gaster": (52, 18, 12),
              "claro": (220, 110, 80), "esc": (30, 8, 6)},
    "mandibula": 1.4,
}
# --- rainha: gáster enorme e tórax grande (músculos de voar). Mesma geometria que a hitbox do rainha.py
RAINHA = {
    "geo": {"cabeca": (60, -10, 25, 21), "torax": (14, -4, 32, 20), "gaster": (-72, 8, 44, 33)},
    "nos": ((-22, 2, 9), (-34, 4, 9)),
    "asa": ((10, -20), 150, 38),
    "k": 1.9,
    "cores": {"cabeca": (132, 40, 24), "torax": (124, 36, 22), "gaster": (112, 32, 20),
              "claro": (214, 104, 70), "esc": (46, 12, 8)},
    "mandibula": 1.0,
}
OURO = (246, 200, 70)


def _asa(p, base, comp, larg, ang, cor, nervura):
    """Asa transparente: gota comprida com nervuras e a manchinha (pterostigma)."""
    ca, sa = math.cos(ang), math.sin(ang)
    centro = (base[0] + ca * comp / 2, base[1] + sa * comp / 2)
    pts = _pts_elipse(centro[0], centro[1], comp / 2, larg / 2, ang)
    p.pol(pts, cor)
    p.pol(pts, nervura, 1)
    ponta = (base[0] + ca * comp * 0.95, base[1] + sa * comp * 0.95)
    p.linha([base, ponta], nervura, 1)                                     # nervura principal
    for f in (0.35, 0.6):                                                  # nervuras cruzadas
        m = (base[0] + ca * comp * f, base[1] + sa * comp * f)
        p.linha([(m[0] - sa * larg * 0.4, m[1] + ca * larg * 0.4), (m[0] + sa * larg * 0.35, m[1] - ca * larg * 0.35)],
                nervura, 1)
    mx, my = base[0] + ca * comp * 0.55 - sa * larg * 0.3, base[1] + sa * comp * 0.55 + ca * larg * 0.3
    p.pol(_pts_elipse(mx, my, larg * 0.22, larg * 0.1, ang), (nervura[0], nervura[1], nervura[2], 200))


def desenhar(p, cfg, t, *, bate=0.0, abre=0.3, gaster=None, olho=None, coroa=False, ferrao=None,
             voando=True, pernas_y=None, morta=False):
    """Desenha a formiga alada no pincel p (origem = tórax).
    gaster = (x, y, rx, ry, ang) pra quando a rainha curva o abdômen; ferrao = cor da ponta (ou None)."""
    geo, k, c = cfg["geo"], cfg["k"], cfg["cores"]
    gx, gy, grx, gry = geo["gaster"]
    gang = 0.2
    if gaster:
        gx, gy, grx, gry, gang = gaster
    (bx, by), comp, larg = cfg["asa"]
    # 1) asas (atrás), batendo
    for i, (dc, dl, alfa) in enumerate(((1.0, 1.0, 110), (0.72, 0.8, 140))):
        a = math.pi + 0.35 - bate * 0.55 + i * 0.18
        _asa(p, (bx + i * 3 * k, by + i * 2 * k), comp * dc, larg * dl, a, (220, 236, 248, alfa), (120, 140, 160, 190))
    # 2) pernas do lado de lá
    _pernas(p, cfg, t, lado=1, voando=voando, pernas_y=pernas_y, morta=morta)
    # 3) gáster com segmentos
    _brilhante(p, gx, gy, grx, gry, gang, c["gaster"], c["claro"], c["esc"])
    ca, sa = math.cos(gang), math.sin(gang)
    for f in (-0.4, 0.0, 0.38):                                            # bordas dos segmentos
        x0, y0 = gx + f * grx * ca, gy + f * grx * sa
        meia = gry * math.sqrt(max(0.0, 1 - f * f)) * 0.95
        p.linha([(x0 - sa * meia, y0 + ca * meia), (x0 + sa * meia * 0.3 - ca * 2, y0), (x0 + sa * meia, y0 - ca * meia)],
                c["esc"], 1.6 * k)
    if ferrao:
        tx, ty = gx - ca * grx, gy - sa * grx
        p.pol([(tx + sa * 3 * k, ty - ca * 3 * k), (tx - ca * 12 * k, ty - sa * 12 * k), (tx - sa * 3 * k, ty + ca * 3 * k)], ferrao)
    # 4) cinturinha: dois carocinhos
    for nx, ny, nr in cfg["nos"]:
        _brilhante(p, nx, ny, nr, nr * 1.1, 0.0, c["torax"], c["claro"], c["esc"])
    # 5) tórax em partes
    tx_, ty_, trx, try_ = geo["torax"]
    _brilhante(p, tx_ - trx * 0.55, ty_ + try_ * 0.15, trx * 0.5, try_ * 0.75, 0.1, c["torax"], c["claro"], c["esc"])
    _brilhante(p, tx_ + trx * 0.15, ty_ - try_ * 0.1, trx * 0.62, try_ * 0.95, -0.1, c["torax"], c["claro"], c["esc"])
    _brilhante(p, tx_ + trx * 0.75, ty_ + try_ * 0.1, trx * 0.38, try_ * 0.7, 0.2, c["torax"], c["claro"], c["esc"])
    # 6) cabeça: antenas dobradas, olho composto, mandíbulas com dentes
    hx, hy, hrx, hry = geo["cabeca"]
    mexe = math.sin(t * 3) * 2 * k
    for i in (0, 1):
        base_a = (hx + hrx * (0.2 + i * 0.25), hy - hry * 0.75)
        cotovelo = (hx - hrx * (0.25 - i * 0.15), hy - hry * 2.4 + mexe)
        ponta = (hx + hrx * (1.6 + i * 0.2), hy - hry * 2.7 + mexe * 1.5)
        cor = c["esc"] if i == 0 else tuple(min(255, v + 20) for v in c["esc"])
        p.linha([base_a, cotovelo], cor, 2.2 * k)                          # escapo (o "braço" da antena)
        for s in range(6):                                                 # funículo em continhas
            f = (s + 1) / 6
            p.circ(cotovelo[0] + (ponta[0] - cotovelo[0]) * f, cotovelo[1] + (ponta[1] - cotovelo[1]) * f,
                   (1.1 + (0.9 if s == 5 else 0)) * k, cor)
    _brilhante(p, hx, hy, hrx, hry, 0.15, c["cabeca"], c["claro"], c["esc"])
    p.pol(_pts_elipse(hx + hrx * 0.25, hy - hry * 0.2, hrx * 0.32, hry * 0.42, 0.3), olho or (16, 8, 6))
    p.circ(hx + hrx * 0.15, hy - hry * 0.38, max(1.0, hrx * 0.1), (240, 220, 210))
    if cfg is RAINHA:                                                      # ocelos: 3 olhinhos no alto
        for i in range(3):
            p.circ(hx - hrx * 0.3 + i * hrx * 0.18, hy - hry * 0.85 + (i % 2) * 2, 1.4 * k, (240, 200, 120))
    tam = hrx * 0.95 * cfg["mandibula"]
    for s in (-1, 1):
        a = s * (0.35 + abre * 0.6)
        mx, my = hx + hrx * 0.85, hy + hry * 0.35
        ex, ey = mx + math.cos(a) * tam, my + math.sin(a) * tam
        lado = (-math.sin(a) * s, math.cos(a) * s)
        p.pol([(mx, my - 2.2 * k * s), (ex, ey), (mx + math.cos(a) * tam * 0.4 + lado[0] * 3 * k,
                                                 my + math.sin(a) * tam * 0.4 + lado[1] * 3 * k)], c["esc"])
        for d in (0.45, 0.7):                                              # dentinhos
            dx_, dy_ = mx + math.cos(a) * tam * d, my + math.sin(a) * tam * d
            p.pol([(dx_, dy_), (dx_ - lado[0] * 2.5 * k, dy_ - lado[1] * 2.5 * k), (dx_ + math.cos(a) * 2 * k, dy_ + math.sin(a) * 2 * k)],
                  c["esc"])
    if coroa:
        cr = [(hx - hrx * 0.55, hy - hry * 0.85), (hx - hrx * 0.55, hy - hry * 1.55), (hx - hrx * 0.27, hy - hry * 1.15),
              (hx, hy - hry * 1.7), (hx + hrx * 0.27, hy - hry * 1.15), (hx + hrx * 0.55, hy - hry * 1.55),
              (hx + hrx * 0.55, hy - hry * 0.85)]
        p.pol(cr, OURO)
        p.pol(cr, (170, 120, 30), 1)
        p.circ(hx, hy - hry * 1.12, 2.8 * k / 1.9 * 1.9, (220, 40, 60))
    if morta:                                                              # olhinho de X
        ex, ey, er = hx + hrx * 0.25, hy - hry * 0.2, hry * 0.42
        p.pol(_pts_elipse(ex, ey, er * 1.1, er * 1.1), c["cabeca"])
        p.linha([(ex - er, ey - er), (ex + er, ey + er)], (20, 8, 6), 2.2 * k)
        p.linha([(ex + er, ey - er), (ex - er, ey + er)], (20, 8, 6), 2.2 * k)
    # 7) pernas do lado de cá
    _pernas(p, cfg, t, lado=0, voando=voando, pernas_y=pernas_y, morta=morta)


def _pernas(p, cfg, t, lado, voando, pernas_y, morta=False):
    """6 pernas finas presas no tórax: coxa, fêmur, tíbia e tarso."""
    geo, k, c = cfg["geo"], cfg["k"], cfg["cores"]
    tx_, ty_, trx, try_ = geo["torax"]
    cor = c["esc"] if lado else tuple(min(255, v + 25) for v in c["torax"])
    for i in range(3):
        raiz = (tx_ + trx * (0.55 - i * 0.55) - lado * 2 * k, ty_ + try_ * 0.75)
        balanco = math.sin(t * 5 + i + lado) * 2 * k
        if morta:                                  # encolhidinhas, tremendo
            treme = math.sin(t * 30 + i * 2 + lado) * 1.5 * k
            joelho = (raiz[0] + (5 - i * 5) * k, raiz[1] + 7 * k)
            tornozelo = (raiz[0] + (9 - i * 6) * k + treme, raiz[1] + 2 * k)
            pe = (tornozelo[0] + 3 * k, tornozelo[1] - 4 * k + treme)
        elif voando:
            joelho = (raiz[0] + (6 - i * 6) * k, raiz[1] + 9 * k + balanco)
            tornozelo = (raiz[0] + (2 - i * 9) * k, raiz[1] + 19 * k + balanco)
            pe = (tornozelo[0] - 5 * k, tornozelo[1] + 5 * k)
        else:
            chao = pernas_y
            pe = (raiz[0] + (16 - i * 16) * k, chao)
            joelho = (raiz[0] + (10 - i * 12) * k, raiz[1] - 6 * k)
            tornozelo = (pe[0] - (2 - i * 2) * k, chao - 6 * k)
        p.osso(raiz, joelho, 2.2 * k, 1.7 * k, cor)
        p.osso(joelho, tornozelo, 1.7 * k, 1.1 * k, cor)
        p.linha([tornozelo, pe], cor, 1.3 * k)


def sprite_guerreira(t, *, bate, abre, olho=None):
    """Guerreira renderizada 2x e reduzida (lisinha). Devolve a superfície virada pra direita."""
    w, h = 110, 90
    s = pygame.Surface((w * ESC, h * ESC), pygame.SRCALPHA)
    desenhar(_Pincel(s, 56, 48), GUERREIRA, t, bate=bate, abre=abre, olho=olho)
    return pygame.transform.smoothscale(s, (w, h))
