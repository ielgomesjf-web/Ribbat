"""
Chefão FINAL (Fase 5, no topo da Montanha): a ÁGUIA-CARECA (design do Gomes).

O maior chefão do jogo. Ataque principal: RASANTE. Ataque especial: não tem.
Precisa de 25 de dano (linguada 2, investida 3).

A águia de verdade: cabeça e cauda BRANCAS, corpo e asas marrom-escuros, bico amarelo enorme com a
ponta em gancho, olho amarelo-claro debaixo de uma "sobrancelha" de osso (por isso a cara de brava),
pernas com "calça" de penas e pés amarelos com garras pretas, asas largas com as penas da ponta
abertas feito dedos.

Como ela é a maior, o rasante vem de 3 jeitos (sempre com aviso):
  - RASANTE ALTO: entra pela beirada na altura das pedras (faixa vermelha). Fica no CHÃO.
  - RASANTE BAIXO: entra raspando o chão. SOBE numa pedra (ou pula por cima, se for bom!).
  - MERGULHO: trava a mira em você e desce em diagonal. SAI DO ALVO. Ela crava as garras no chão
    e fica presa um tiquinho (dá pra bater).
Depois de 3 rasantes ela POUSA cansada, ofegando: é a hora de bater. Com metade da vida ela fica
FURIOSA: 4 rasantes por rodada e mais rápida.

Quando perde: agarra o Ribbat no bico e joga ele pro alto... e começa a CORRIDA até o pergaminho
(a corrida mesmo fica em ribbat.py + fases.FASE_CORRIDA; aqui ficam a águia voando e a barrinha).
"""
import math
import random

import pygame

import som as SOM

from chefe import ESC, RECARGA_INVESTIDA, RECARGA_LINGUA, _Pincel, _pts_elipse  # noqa: F401
from config import *  # noqa: F401,F403
from entidades import R

ARENA = {"nome": "O Cume", "tema": "montanha", "pedacos": [[
    "..............................",
    "...rrrr......rrrr......rrrr...",
    "..............................",
    "..S...........................",
    "##############################",
    "##############################",
]]}
CHAO_Y = 15 * TILE
PEDRA_Y = 12 * TILE                    # topo das 3 pedras (dá pra subir por baixo)
PEDRAS = ((3, 7), (13, 17), (23, 27))  # colunas de cada pedra
VIDA = 25
FURIA = 12                             # com essa vida (ou menos) ela fica furiosa
DANO_LINGUA, DANO_INVESTIDA = 2, 3
MOSQUITO_Y = (330, 440)

ALTO_Y = 330                           # centro dela no rasante alto
BAIXO_Y = CHAO_Y - 42                  # centro dela no rasante baixo
POUSO_Y = CHAO_Y - 72                  # centro dela em pé no chão
PAIRA_Y = 110                          # lá em cima, antes do mergulho
VEL_RASANTE = (820, 940)               # normal, furiosa
VEL_MERGULHO = (900, 1000)
AVISO = (1.0, 0.85)
CANSADA = (4.0, 3.4)
PAUSA = (0.55, 0.4)
PRESA = 0.9

# a corrida
LARGADA = 2.0                          # o Ribbat caindo do céu + as luzinhas
TEMPO_AGUIA = 46.0                     # quanto a águia leva da largada até o pergaminho

# cores
MARROM = (74, 50, 34)
MARROM_CLARO = (116, 84, 56)
MARROM_ESC = (40, 26, 18)
BRANCO_P = (248, 246, 240)
BRANCO_SOMBRA = (206, 202, 194)
AMARELO_B = (250, 196, 44)
AMARELO_ESC = (190, 130, 24)
GARRA = (28, 24, 24)

# ---------------------------------------------------------------- geometria (desenho E colisão usam a mesma)
# Coordenadas locais: (0, 0) = centro do corpo, olhando pra DIREITA. (x, y, largura, altura)
GEO = {
    "alto": {"corpo": (-62, -28, 124, 56), "cabeca": (40, -46, 96, 48), "garras": (12, 8, 52, 50)},
    "baixo": {"corpo": (-62, -28, 124, 56), "cabeca": (46, -34, 96, 44), "garras": (-40, 14, 44, 24)},
    "pousada": {"corpo": (-56, -44, 112, 98), "cabeca": (28, -76, 90, 52), "pernas": (-14, 28, 44, 46)},
}
CABECA = {"alto": (70, -20), "baixo": (76, -8), "pousada": (50, -50), "mergulho": (70, -8)}
BICO = (60, 4)                         # ponta do bico, a partir do centro da cabeça


def caixas(pose, x, y, d):
    out = []
    for gx, gy, gw, gh in GEO[pose].values():
        if d < 0:
            gx = -gx - gw
        out.append(R(x + gx, y + gy, gw, gh))
    return out


def ponta_bico(pose, x, y, d):
    hx, hy = CABECA[pose]
    return x + (hx + BICO[0]) * d, y + hy + BICO[1]


# =====================================================================
# A Águia
# =====================================================================
class Aguia:
    def __init__(self):
        self.x, self.y = LARGURA + 260, 150.0
        self.dir = -1
        self.vida = VIDA
        self.t = 0.0
        self.tempo = 0.0
        self.flash = 0.0
        self.estado = "entrando"
        self.fila = []
        self.altura = "alto"           # do rasante que vem aí
        self.vx = self.vy = 0.0
        self.alvo = None               # mira do mergulho (no chão)
        self.de = None                 # de onde ela sai (pouso, agarrar)
        self.pouso_x = LARGURA / 2
        self.branco = 0.0              # tela clareando no fim (o Ribbat sumindo lá pra cima)
        self.vivo = True

    @property
    def furiosa(self):
        return self.vida <= FURIA

    @property
    def nivel(self):
        return 1 if self.furiosa else 0

    def mudar(self, estado):
        self.estado, self.tempo = estado, 0.0

    @property
    def pose(self):
        e = self.estado
        if e in ("rasante", "aviso_rasante"):
            return self.altura
        if e == "mergulho":
            return "mergulho"
        if e == "agarrando":
            return "baixo"
        if e in ("cansada", "presa", "vencida", "furia_final", "decolando"):
            return "pousada"
        if e == "pousando" and self.tempo > 0.9:
            return "pousada"
        return "alto"

    @property
    def vulneravel(self):
        return self.estado in ("cansada", "presa")

    def hitbox(self):
        return caixas("pousada", self.x, self.y, self.dir) if self.vulneravel else []

    def perigos(self):
        if self.estado == "rasante":
            return caixas(self.altura, self.x, self.y, self.dir)
        if self.estado == "mergulho":
            ux, uy = self.vx / VEL_MERGULHO[self.nivel], self.vy / VEL_MERGULHO[self.nivel]
            return [R(self.x + ux * 24 - 55, self.y + uy * 24 - 50, 110, 100)]
        return []

    def levar(self, dano, jogo):
        if not self.vulneravel:
            return False
        estava = self.furiosa
        self.vida -= dano
        self.flash = 0.12
        hb = self.hitbox()[0]
        jogo.faiscas(hb.centerx, hb.centery, BRANCO_P, 10, 240)
        jogo.faiscas(hb.centerx, hb.centery, MARROM_CLARO, 6, 200)
        jogo.tremer(4)
        if self.vida <= 0:
            self.vida = 0
            self.y = POUSO_Y
            self.mudar("vencida")
            jogo.tremer(10)
        elif self.furiosa and not estava:
            jogo.tremer(8)                                # ficou furiosa!
        return True

    def nova_fila(self):
        f = ["alto", "baixo", "mergulho"]
        random.shuffle(f)
        if self.furiosa:
            extra = random.choice(("alto", "baixo"))
            f.insert(random.randint(1, 3), extra)
        self.fila = f

    # ---------- comportamento ----------
    def atualizar(self, dt, jogo):
        r = jogo.ribbat
        self.t += dt
        self.tempo += dt
        self.flash = max(0.0, self.flash - dt)
        n = self.nivel
        e = self.estado
        if e == "entrando":                                # passa lá no alto gritando e some
            self.x -= 640 * dt
            self.y = 150 + math.sin(self.tempo * 2) * 20
            if self.tempo < 0.1:
                jogo.tremer(6)
            if self.x < -300:
                self.nova_fila()
                self.mudar("pausa")
        elif e == "pausa":
            if self.tempo >= PAUSA[n]:
                self.escolher(jogo)
        elif e == "aviso_rasante":                         # aparece na beirada, na altura certa
            self.x = (-70 if self.dir > 0 else LARGURA + 70) + math.sin(self.tempo * 6) * 6
            if self.tempo >= AVISO[n]:
                self.x = -260 if self.dir > 0 else LARGURA + 260
                self.mudar("rasante")
                jogo.tremer(5)
        elif e == "rasante":
            self.x += self.dir * VEL_RASANTE[n] * dt
            if self.altura == "baixo" and int(self.t * 30) % 2 == 0 and 0 < self.x < LARGURA:
                jogo.poeira(self.x - self.dir * 40, CHAO_Y, 2)
            if (self.dir > 0 and self.x > LARGURA + 280) or (self.dir < 0 and self.x < -280):
                self.mudar("pausa")
        elif e == "aviso_mergulho":                        # chega lá no alto e TRAVA a mira
            hx = 150 if self.alvo[0] > LARGURA / 2 else LARGURA - 150
            k = min(1.0, self.tempo / 0.4)
            self.x = hx
            self.y = -140 + (PAIRA_Y + 140) * (1 - (1 - k) ** 2) + math.sin(self.t * 5) * 4
            self.dir = 1 if self.alvo[0] > self.x else -1
            if self.tempo >= AVISO[n]:
                ax, ay = self.alvo
                d = math.hypot(ax - self.x, ay - self.y) or 1
                self.vx = (ax - self.x) / d * VEL_MERGULHO[n]
                self.vy = (ay - self.y) / d * VEL_MERGULHO[n]
                self.mudar("mergulho")
        elif e == "mergulho":
            self.x += self.vx * dt
            self.y += self.vy * dt
            if self.y >= POUSO_Y:
                self.y = POUSO_Y
                self.x = min(max(self.x, 90), LARGURA - 90)
                self.mudar("presa")                        # cravou as garras no chão!
                jogo.tremer(10)
                jogo.poeira(self.x, CHAO_Y, 14)
        elif e == "presa":
            if self.tempo >= PRESA:
                self.de = (self.x, self.y)
                self.mudar("subindo")
        elif e == "subindo":
            self.y -= 520 * dt
            self.x += self.dir * 220 * dt
            if self.y < -200:
                self.mudar("pausa")
        elif e == "pousando":                              # desce planando e pousa (longe do Ribbat, nunca em cima)
            k = min(1.0, self.tempo / 1.1)
            x0, y0 = self.de
            self.x = x0 + (self.pouso_x - x0) * (1 - (1 - k) ** 2)
            self.y = y0 + (POUSO_Y - y0) * k * k
            if k >= 1:
                self.dir = 1 if r.cx > self.x else -1
                jogo.poeira(self.x, CHAO_Y, 12)
                jogo.tremer(6)
                self.mudar("cansada")
        elif e == "cansada":
            self.dir = 1 if r.cx > self.x else -1
            if self.tempo >= CANSADA[n]:
                self.mudar("decolando")
        elif e == "decolando":
            if self.tempo > 0.5:
                self.y -= 600 * dt
            if self.y < -200:
                self.nova_fila()
                self.mudar("pausa")
        elif e == "vencida":                               # tonta... mas não acabou!
            if self.tempo >= 1.6:
                self.mudar("furia_final")
                jogo.tremer(12)
        elif e == "furia_final":
            if self.tempo >= 0.8:
                self.de = (self.x, self.y)
                self.dir = 1 if r.cx > self.x else -1
                self.mudar("agarrando")
        elif e == "agarrando":                             # vai buscar o Ribbat com o bico
            k = min(1.0, self.tempo / 0.55)
            bx, by = ponta_bico("baixo", 0, 0, self.dir)
            alvo = (r.cx - bx, r.y + 4 - by)
            x0, y0 = self.de
            self.x = x0 + (alvo[0] - x0) * k
            self.y = y0 + (alvo[1] - y0) * k - math.sin(k * math.pi) * 60
            if k >= 1:
                self.de = (self.x, self.y)
                self.mudar("levando")
                jogo.tremer(6)
        elif e == "levando":                               # sobe com ele no bico
            k = min(1.0, self.tempo / 1.0)
            x0, y0 = self.de
            self.x = x0 + (LARGURA / 2 - x0) * k
            self.y = y0 + (190 - y0) * (1 - (1 - k) ** 2)
            bx, by = ponta_bico("alto", self.x, self.y, self.dir)
            r.x, r.y = bx - r.W / 2, by - 10
            if k >= 1:
                r.vx, r.vy = 0.0, -1150.0                  # e JOGA pro alto!
                self.mudar("arremesso")
        elif e == "arremesso":
            r.y += r.vy * dt
            if self.tempo > 0.3:
                self.y -= 700 * dt
            self.branco = min(1.0, max(0.0, (self.tempo - 0.5) / 0.9))
            if self.tempo >= 1.5:
                self.vivo = False
                jogo.comecar_corrida()

    def escolher(self, jogo):
        r = jogo.ribbat
        if not self.fila:
            lado = -1 if r.cx > LARGURA / 2 else 1
            self.pouso_x = LARGURA / 2 + lado * 200        # pousa do lado de LÁ (longe do Ribbat)
            self.de = (LARGURA / 2 + lado * 700, -160)
            self.dir = -lado
            self.mudar("pousando")
            return
        ataque = self.fila.pop(0)
        if ataque == "mergulho":
            self.alvo = (min(max(r.cx, 60), LARGURA - 60), POUSO_Y)
            self.mudar("aviso_mergulho")
        else:
            self.altura = ataque
            self.y = ALTO_Y if ataque == "alto" else BAIXO_Y
            self.dir = random.choice((-1, 1))
            self.mudar("aviso_rasante")
            jogo.tremer(3)


def criar():
    return Aguia()


CINEMA = ("agarrando", "levando", "arremesso")


def atualizar(jogo, dt, ent):
    r, a = jogo.ribbat, jogo.boss
    if a.estado not in CINEMA:
        r.atualizar(dt, ent, jogo)
    else:
        r.invuln = max(r.invuln, 0.2)
        r.lingua_t = r.dash_t = 0
        r.rastro = []
    a.atualizar(dt, jogo)
    if jogo.estado != "chefe":
        return
    pr, lingua = r.rect(), r.rect_lingua()
    hb = a.hitbox()
    if hb:
        if lingua and not r.lingua_acertou and lingua.collidelist(hb) >= 0:
            r.lingua_acertou = True
            if a.levar(DANO_LINGUA, jogo):
                SOM.efeito("acerto")
        if r.dash_t > 0 and not r.dash_acertou and pr.collidelist(hb) >= 0:
            r.dash_acertou = True
            if a.levar(DANO_INVESTIDA, jogo):
                SOM.efeito("acerto")
            r.dash_t = 0
            r.vx = -r.dir * 330
            r.vy = -380
            r.invuln = max(r.invuln, 0.5)
            r.atordoado = 0.2
    if r.dash_t <= 0 and any(pr.colliderect(p) for p in a.perigos()):
        r.machucar(jogo, a.x)
    jogo.efeitos(dt)


# =====================================================================
# Desenho da águia
# =====================================================================
_sprites = {}
SPR_W, SPR_H = 440, 320
SPR_O = (220, 170)                       # onde fica o centro do corpo dentro do sprite


def _asa(p, ombro, ang, comp, larg, cor, cor_clara, cor_esc):
    """Asa larga de águia: penas cobertas, penas de trás em 'escadinha' e as primárias abertas feito dedos.
    ang = pra onde a asa aponta (0 = frente, -pi/2 = pra cima, pi = pra trás)."""
    ux, uy = math.cos(ang), math.sin(ang)
    vx, vy = uy, -ux                                   # a borda de trás da asa fica pro lado da cauda
    if -vx + 0.3 * vy < 0:
        vx, vy = -vx, -vy
    bx, by = ombro

    def P(s, c):
        return bx + ux * s * comp + vx * c * larg, by + uy * s * comp + vy * c * larg
    for i in range(6):                                 # primárias (os "dedos")
        k = i / 5
        b = (0.66, 0.08 + k * 0.62)
        ponta = (1.0 - k * 0.2, -0.02 + k * 0.5)
        lado = 0.07
        p.pol([P(b[0], b[1] - lado), P(ponta[0] - 0.04, ponta[1] - lado * 0.5), P(*ponta),
               P(ponta[0] - 0.05, ponta[1] + lado * 0.6), P(b[0], b[1] + lado)], cor_esc if i % 2 else cor)
    corpo = [P(0, -0.05), P(0.3, -0.12), P(0.5, -0.1), P(0.7, 0.0), P(0.72, 0.7)]
    for i in range(7):                                 # secundárias: borda de trás em escadinha
        s = 0.68 - i * 0.1
        corpo += [P(s, 0.98 + (i % 2) * 0.04), P(s - 0.05, 0.9)]
    corpo += [P(-0.04, 0.8)]
    p.pol(corpo, cor)
    p.pol([P(0, -0.05), P(0.3, -0.12), P(0.5, -0.1), P(0.68, 0.0), P(0.6, 0.3), P(0.3, 0.38), P(0, 0.34)], cor_clara)
    for i in range(5):                                 # fileira de penas cobertas
        s = 0.08 + i * 0.12
        p.linha([P(s, 0.32), P(s + 0.06, 0.42), P(s + 0.12, 0.33)], cor_esc, 1.5)
    p.linha([P(0, -0.05), P(0.3, -0.12), P(0.5, -0.1), P(0.7, 0.0)], cor_esc, 1.5)


def _cauda(p, base, ang, comp=64, abre=0.5):
    """Cauda branca em leque."""
    bx, by = base
    pts = [(bx, by - 8)]
    n = 6
    for i in range(n + 1):
        a = ang + (i / n - 0.5) * abre
        pts.append((bx + math.cos(a) * comp, by + math.sin(a) * comp))
    pts.append((bx, by + 8))
    p.pol(pts, BRANCO_SOMBRA)
    pts2 = [(bx, by - 6)] + [(bx + math.cos(ang + (i / n - 0.5) * abre * 0.8) * (comp - 6),
                               by + math.sin(ang + (i / n - 0.5) * abre * 0.8) * (comp - 6)) for i in range(n + 1)] + [(bx, by + 6)]
    p.pol(pts2, BRANCO_P)
    for i in range(1, n):
        a = ang + (i / n - 0.5) * abre * 0.8
        p.linha([(bx + math.cos(a) * 18, by + math.sin(a) * 18), (bx + math.cos(a) * (comp - 8), by + math.sin(a) * (comp - 8))],
                BRANCO_SOMBRA, 1)


def _cabeca(p, hx, hy, bico_aberto=False, furia=False, olho_fechado=False):
    """Cabeça branca, 'sobrancelha' de osso por cima do olho e o bicão amarelo em gancho."""
    p.pol(_pts_elipse(hx - 2, hy + 3, 31, 25), BRANCO_SOMBRA)
    p.pol(_pts_elipse(hx, hy, 30, 24), BRANCO_P)
    for i in range(5):                                 # penugem da nuca
        p.pol([(hx - 26 + i * 4, hy + 12), (hx - 36 + i * 3, hy + 22), (hx - 20 + i * 4, hy + 18)], BRANCO_P)
    # bico de baixo (abre pra agarrar / ofegar)
    if bico_aberto:
        p.pol([(hx + 28, hy + 2), (hx + 50, hy + 4), (hx + 50, hy + 12), (hx + 28, hy + 8)], (120, 40, 40))
        p.pol([(hx + 28, hy + 6), (hx + 50, hy + 13), (hx + 50, hy + 19), (hx + 30, hy + 14)], AMARELO_ESC)
        p.pol([(hx + 28, hy + 5), (hx + 49, hy + 11), (hx + 48, hy + 15), (hx + 30, hy + 11)], AMARELO_B)
    else:
        p.pol([(hx + 28, hy + 2), (hx + 48, hy + 2), (hx + 52, hy + 7), (hx + 42, hy + 10), (hx + 28, hy + 8)], AMARELO_ESC)
        p.pol([(hx + 28, hy + 3), (hx + 47, hy + 3), (hx + 49, hy + 6), (hx + 28, hy + 6)], AMARELO_B)
    # bico de cima: grosso, curvo, com a ponta em gancho
    cima = [(hx + 24, hy - 14), (hx + 32, hy - 15), (hx + 44, hy - 13), (hx + 54, hy - 8), (hx + 61, hy + 1),
            (hx + 61, hy + 10), (hx + 57, hy + 5), (hx + 50, hy + 2), (hx + 28, hy + 3)]
    p.pol(cima, AMARELO_ESC)
    p.pol([(hx + 25, hy - 12), (hx + 33, hy - 13), (hx + 44, hy - 11), (hx + 53, hy - 6), (hx + 58, hy + 1),
           (hx + 50, hy - 1), (hx + 28, hy)], AMARELO_B)
    p.linha([(hx + 34, hy - 11), (hx + 46, hy - 9), (hx + 54, hy - 4)], (255, 232, 140), 1.5)      # brilho
    p.pol(_pts_elipse(hx + 32, hy - 7, 3, 2), (120, 80, 20))                                         # narina
    # olho amarelo-claro com a sobrancelha brava em cima
    if olho_fechado:
        p.linha([(hx + 10, hy - 6), (hx + 20, hy - 4)], PRETO, 2)
    else:
        p.pol(_pts_elipse(hx + 15, hy - 6, 6, 5), (255, 120, 50) if furia else (252, 230, 120))
        p.circ(hx + 17, hy - 6, 2.6, PRETO)
        p.circ(hx + 15.5, hy - 7.5, 1, BRANCO)
    p.pol([(hx + 2, hy - 16), (hx + 24, hy - 14), (hx + 27, hy - 8), (hx + 14, hy - 11), (hx + 4, hy - 11)], BRANCO_SOMBRA)
    p.linha([(hx + 6, hy - 13), (hx + 24, hy - 10)], (130, 124, 116), 2)


def _pe(p, tornozelo, pe, abre=1.0):
    """Pé amarelo: 3 dedos pra frente + 1 pra trás, garras pretas."""
    p.osso(tornozelo, pe, 5, 4, AMARELO_ESC)
    p.osso(tornozelo, pe, 4, 3, AMARELO_B)
    fx, fy = pe
    dedos = ((14, 2 - 6 * abre), (15, 4), (12, 8 + 4 * abre), (-10, 3))
    for dx, dy in dedos:
        ponta = (fx + dx, fy + dy)
        p.osso((fx, fy), ponta, 3, 2.4, AMARELO_B)
        s = 1 if dx > 0 else -1
        p.pol([(ponta[0], ponta[1] - 2.5), (ponta[0] + s * 6, ponta[1] + 1), (ponta[0] + s * 3, ponta[1] + 5),
               (ponta[0], ponta[1] + 2)], GARRA)


def _perna(p, quadril, joelho, tornozelo, pe, abre=1.0):
    p.osso(quadril, joelho, 13, 10, MARROM_ESC)        # "calça" de penas
    p.osso(quadril, joelho, 12, 9, MARROM)
    for i in range(3):
        x = joelho[0] - 6 + i * 6
        p.linha([(x, joelho[1] - 4), (x - 2, joelho[1] + 6)], MARROM_ESC, 1.5)
    _pe(p, tornozelo if tornozelo else joelho, pe, abre)


def _corpo_voo(p, ang=0.0):
    p.pol(_pts_elipse(0, 2, 68, 30, ang), MARROM_ESC)
    p.pol(_pts_elipse(0, 0, 66, 28, ang), MARROM)
    p.pol(_pts_elipse(6, -10, 50, 12, ang), MARROM_CLARO)
    for i in range(6):                                 # escamas de pena no peito
        x = -30 + i * 14
        p.linha([(x, 8), (x + 6, 14), (x + 12, 8)], MARROM_ESC, 1.5)


def _desenhar(p, pose, asa, bico, furia, tonta):
    if pose == "pousada":
        # em pé: corpo inclinado (cabeça pra cima), asas dobradas, cauda pra trás e pra baixo
        if asa > 0:                                    # asas abrindo (decolando / fúria)
            _asa(p, (-4, -30), -math.pi / 2 - 0.4 - (1 - asa) * 1.0, 150 * asa + 40, 64, MARROM_ESC, MARROM, MARROM_ESC)
        _cauda(p, (-40, 22), math.pi * 0.82, 66, 0.5)
        _perna(p, (-2, 24), (6, 50), None, (10, 70))
        p.pol(_pts_elipse(0, 2, 58, 44, -0.45), MARROM_ESC)
        p.pol(_pts_elipse(0, 0, 56, 42, -0.45), MARROM)
        p.pol(_pts_elipse(14, 4, 30, 30, -0.45), MARROM_CLARO)
        for i in range(5):
            y = -10 + i * 10
            p.linha([(10, y), (18, y + 6), (26, y)], MARROM_ESC, 1.5)
        # asa dobrada por cima do corpo, as pontas cruzando a cauda
        dobrada = [(30, -36), (6, -40), (-30, -24), (-74, 6), (-96, 26), (-80, 24), (-60, 22), (-30, 30), (0, 24), (26, 0)]
        p.pol(dobrada, MARROM_ESC)
        p.pol([(28, -34), (6, -36), (-28, -22), (-60, 0), (-30, 4), (0, -4), (24, -14)], MARROM_CLARO)
        for i in range(4):
            x = -10 - i * 16
            p.linha([(x, -16 + i * 6), (x - 18, 14 + i * 3)], (26, 16, 10), 1.5)
        _perna(p, (12, 26), (18, 52), None, (24, 72))
        p.pol([(24, -40), (50, -64), (68, -36), (40, -20)], BRANCO_P)                     # pescoço branco
        hx, hy = CABECA["pousada"]
        _cabeca(p, hx, hy, bico, furia, olho_fechado=tonta)
        return
    if pose == "mergulho":
        _cauda(p, (-56, 0), math.pi, 50, 0.25)
        for ombro, cor, clara in (((-6, -16), MARROM_ESC, MARROM), ((4, -12), MARROM, MARROM_CLARO)):
            _asa(p, ombro, math.pi - 0.12, 120, 36, cor, clara, MARROM_ESC)
        _corpo_voo(p)
        _pe(p, (40, 14), (62, 20), 1.0)                # garras na frente, prontas
        p.pol([(40, -24), (60, -30), (66, 4), (40, 16)], BRANCO_P)
        hx, hy = CABECA["mergulho"]
        _cabeca(p, hx, hy, False, furia)
        return
    baixo = pose == "baixo"
    if baixo:                                          # asas varridas pra trás, rentinho
        angs = (math.pi + 0.18, math.pi + 0.05)
        comp, larg = 150, 46
    else:                                              # batendo asa / planando
        a0 = -math.pi / 2 - 0.3 - asa * (math.pi - 0.6)   # de cima, passando por trás, até embaixo
        angs = (a0 - 0.15, a0 + 0.05)
        comp, larg = 160, 72
    _asa(p, (-6, -20), angs[0], comp, larg, MARROM_ESC, MARROM, (26, 16, 10))          # a de lá
    _cauda(p, (-58, 0), math.pi, 62, 0.5)
    if baixo:
        _perna(p, (-6, 18), (-26, 26), None, (-44, 30), 0.3)                         # pernas recolhidas
    else:
        _perna(p, (14, 16), (28, 34), None, (46, 50), 1.0)                           # garras pra frente
    _corpo_voo(p)
    p.pol([(36, -26), (58, -40), (70, 6), (40, 18)], BRANCO_P)
    hx, hy = CABECA[pose]
    _cabeca(p, hx, hy, bico, furia, olho_fechado=tonta)
    _asa(p, (4, -16), angs[1], comp, larg, MARROM, MARROM_CLARO, MARROM_ESC)          # a de cá


def sprite(pose="alto", asa=0.3, bico=False, furia=False, tonta=False):
    """Sprite dela olhando pra direita. O centro do corpo fica em SPR_O."""
    chave = (pose, round(asa, 1), bico, furia, tonta)
    if chave not in _sprites:
        sf = pygame.Surface((SPR_W * ESC, SPR_H * ESC), pygame.SRCALPHA)
        _desenhar(_Pincel(sf, *SPR_O), pose, round(asa, 1), bico, furia, tonta)
        _sprites[chave] = pygame.transform.smoothscale(sf, (SPR_W, SPR_H))
    return _sprites[chave]


def blit_aguia(tela, img, x, y, d, ang=0.0, k=1.0):
    if d < 0:
        img = pygame.transform.flip(img, True, False)
    if k != 1.0:
        img = pygame.transform.smoothscale(img, (int(SPR_W * k), int(SPR_H * k)))
    ox = (SPR_O[0] if d > 0 else SPR_W - SPR_O[0]) * k
    oy = SPR_O[1] * k
    if ang:
        img2 = pygame.transform.rotate(img, ang)
        cx, cy = img.get_width() / 2, img.get_height() / 2
        dx, dy = ox - cx, oy - cy                           # o centro do corpo, girado junto
        a = math.radians(-ang)
        rx, ry = dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
        tela.blit(img2, img2.get_rect(center=(x - rx, y - ry)))
    else:
        tela.blit(img, (x - ox, y - oy))


def desenhar_aguia(tela, a, t, ox=0, oy=0):
    e = a.estado
    pose = a.pose
    asa = (math.sin(t * 7) + 1) / 2
    if e in ("rasante", "aviso_rasante"):
        asa = 0.15 + 0.08 * math.sin(t * 5) if a.altura == "alto" else 0.0     # planando
    bico = e in ("cansada", "vencida", "furia_final", "agarrando", "aviso_rasante", "aviso_mergulho")
    if pose == "pousada":
        asa = {"decolando": min(1.0, a.tempo * 2), "furia_final": min(1.0, a.tempo * 3)}.get(e, 0.0)
        if e == "presa":
            asa = 0.6
    img = sprite(pose, asa, bico, a.furiosa and e not in ("vencida",), tonta=e == "vencida")
    ang = 0.0
    if e == "mergulho":
        ang = -math.degrees(math.atan2(a.vy, abs(a.vx) + 0.01)) * (1 if a.dir > 0 else -1)
    if a.flash > 0:
        img = img.copy()
        img.fill((90, 90, 90), special_flags=pygame.BLEND_RGB_ADD)
    sobe = math.sin(t * 3) * 3 if e == "cansada" else 0
    blit_aguia(tela, img, a.x - ox, a.y - oy + sobe, a.dir, ang)
    hx, hy = CABECA[pose if pose in CABECA else "alto"]
    cx, cy = a.x + hx * a.dir - ox, a.y + hy - oy
    if e == "cansada":                                  # ofegando: bafinho
        for i in range(2):
            k = (t * 1.5 + i * 0.5) % 1
            pygame.draw.circle(tela, (240, 244, 252), (int(cx + a.dir * (66 + k * 30)), int(cy + 8 - k * 20)),
                               int(4 + k * 6), 2)
        for i in range(2):                              # gotinhas de suor
            k = (t * 1.2 + i * 0.5) % 1
            pygame.draw.circle(tela, (150, 210, 255), (int(cx - a.dir * (24 + i * 10)), int(cy - 20 + k * 30)), 3)
    if e == "vencida":
        for i in range(3):
            ang2 = t * 4 + i * math.tau / 3
            pygame.draw.circle(tela, AMARELO, (int(cx + math.cos(ang2) * 40), int(cy - 34 + math.sin(ang2) * 10)), 6)


# =====================================================================
# Arena: lá no cume
# =====================================================================
_fundo = None


def criar_fundo():
    s = pygame.Surface((LARGURA, ALTURA))
    for y in range(ALTURA):
        k = y / ALTURA
        s.fill([int(a + (b - a) * k) for a, b in zip((70, 110, 190), (250, 210, 170))], R(0, y, LARGURA, 1))
    pygame.draw.circle(s, (255, 236, 180), (760, 150), 60)                      # o sol nascendo
    pygame.draw.circle(s, (255, 246, 214), (760, 150), 44)
    rnd = random.Random(8)
    for camada, (cor, base, amp) in enumerate((((150, 150, 186), 330, 90), ((120, 116, 150), 380, 60))):
        pts = [(0, ALTURA)]
        x = 0
        while x <= LARGURA + 60:
            pts.append((x, base - rnd.randint(0, amp)))
            x += rnd.randint(50, 110)
        pts.append((LARGURA, ALTURA))
        pygame.draw.polygon(s, cor, pts)
    for i in range(14):                                                         # mar de nuvens lá embaixo
        pygame.draw.circle(s, (250, 246, 244), (i * 76 + rnd.randint(-10, 10), 420 + rnd.randint(-8, 8)), rnd.randint(40, 64))
    for i in range(14):
        pygame.draw.circle(s, (236, 228, 230), (i * 76 + 30, 450), 46)
    # o chão do cume: rocha com neve
    pygame.draw.rect(s, (110, 100, 96), R(0, CHAO_Y, LARGURA, ALTURA - CHAO_Y))
    for _ in range(30):
        pygame.draw.circle(s, (92, 84, 82), (rnd.randint(0, LARGURA), rnd.randint(CHAO_Y + 14, ALTURA)), rnd.randint(3, 8))
    pts = [(0, CHAO_Y + 10)] + [(x, CHAO_Y + 10 + math.sin(x / 23) * 3) for x in range(0, LARGURA + 20, 20)] + [(LARGURA, CHAO_Y - 2)]
    pygame.draw.polygon(s, (244, 248, 252), [(0, CHAO_Y - 2)] + pts)
    pygame.draw.line(s, (200, 214, 232), (0, CHAO_Y + 12), (LARGURA, CHAO_Y + 12), 2)
    # o ninho dela, num canto (galhos)
    for i in range(14):
        a = i / 14 * math.pi
        pygame.draw.line(s, (96, 70, 46), (860 + math.cos(a) * 70, CHAO_Y - 4 - math.sin(a) * 10),
                         (860 - math.cos(a) * 60, CHAO_Y - 18 + math.sin(a * 2) * 6), 4)
    for c0, c1 in PEDRAS:                                                       # as 3 pedras
        x0, x1 = c0 * TILE, c1 * TILE
        pygame.draw.polygon(s, (96, 88, 86), [(x0 + 6, PEDRA_Y + 30), (x0 - 4, PEDRA_Y + 4), (x0 + 10, PEDRA_Y - 2),
                                              (x1 - 8, PEDRA_Y - 2), (x1 + 4, PEDRA_Y + 6), (x1 - 10, PEDRA_Y + 34),
                                              ((x0 + x1) / 2, PEDRA_Y + 44)])
        pygame.draw.polygon(s, (132, 122, 118), [(x0 + 2, PEDRA_Y + 4), (x0 + 12, PEDRA_Y), (x1 - 10, PEDRA_Y),
                                                 (x1 - 2, PEDRA_Y + 8), ((x0 + x1) / 2, PEDRA_Y + 16)])
        pygame.draw.rect(s, (244, 248, 252), R(x0 + 2, PEDRA_Y - 4, x1 - x0 - 4, 7), border_radius=4)
    return s


def _tracejado(tela, a, b, cor, larg=3, passo=16):
    n = max(1, int(math.dist(a, b) // passo))
    for k in range(0, n, 2):
        p0 = (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n)
        p1 = (a[0] + (b[0] - a[0]) * (k + 1) / n, a[1] + (b[1] - a[1]) * (k + 1) / n)
        pygame.draw.line(tela, cor, p0, p1, larg)


def desenhar_aviso(tela, a, t):
    k = 0.55 + 0.45 * abs(math.sin(t * 9))
    if a.estado == "aviso_rasante":
        cx = caixas(a.altura, 0, a.y, 1)
        topo, baixo = min(c.top for c in cx), max(c.bottom for c in cx)
        faixa = pygame.Surface((LARGURA, baixo - topo), pygame.SRCALPHA)
        faixa.fill((230, 50, 40, int(60 * k)))
        tela.blit(faixa, (0, topo))
        _tracejado(tela, (0, a.y), (LARGURA, a.y), (230, 50, 40), 3)
        for i in range(5):                                         # setinhas: pra onde ela vai
            x = (i * 200 + t * 300 * a.dir) % LARGURA
            pygame.draw.polygon(tela, (230, 50, 40), [(x, a.y - 12), (x + a.dir * 14, a.y), (x, a.y + 12)])
    elif a.estado == "aviso_mergulho" and a.alvo:
        ax, ay = a.alvo
        _tracejado(tela, (a.x, a.y), (ax, ay + 50), (230, 50, 40), 3)
        gy = CHAO_Y - 14
        pygame.draw.circle(tela, (230, 50, 40), (int(ax), int(gy)), int(30 * k), 4)
        pygame.draw.line(tela, (230, 50, 40), (ax - 40, gy), (ax + 40, gy), 3)
        pygame.draw.line(tela, (230, 50, 40), (ax, gy - 40), (ax, gy + 20), 3)


def desenhar(jogo, tela):
    global _fundo
    if _fundo is None:
        _fundo = criar_fundo()
    a, t = jogo.boss, jogo.tempo_total
    tx = random.uniform(-jogo.tremor, jogo.tremor) if jogo.tremor > 0 else 0
    ty = random.uniform(-jogo.tremor, jogo.tremor) if jogo.tremor > 0 else 0
    tela.blit(_fundo, (tx, ty))
    desenhar_aviso(tela, a, t)
    desenhar_aguia(tela, a, t, -tx, -ty)
    if a.estado == "levando":                                      # o Ribbat preso no bico (o gancho por cima dele)
        import desenho as D
        r = jogo.ribbat
        bx, by = ponta_bico("alto", a.x, a.y, a.dir)
        D.desenhar_sapo(tela, r.cx + tx, r.y + r.H + ty, -a.dir, "tonto", escala=0.85, orelhas=jogo.orelhas_coelho)
        pygame.draw.polygon(tela, AMARELO_ESC, [(bx - a.dir * 16 + tx, by - 8 + ty), (bx + a.dir * 2 + tx, by + ty),
                                                (bx - a.dir * 4 + tx, by + 10 + ty), (bx - a.dir * 12 + tx, by + 2 + ty)])
    else:
        jogo.desenhar_ribbat(tela, -tx, -ty)
    jogo.desenhar_efeitos(tela, -tx, -ty)
    if a.branco > 0:
        b = pygame.Surface((LARGURA, ALTURA))
        b.fill((255, 255, 255))
        b.set_alpha(int(255 * a.branco))
        tela.blit(b, (0, 0))
    desenhar_hud(jogo, tela)


def icone_cabeca(tela, x, y, k=1.0):
    """Cabecinha branca da águia (pra barra de vida e pra corrida)."""
    pygame.draw.circle(tela, PRETO, (int(x), int(y)), int(13 * k))
    pygame.draw.circle(tela, BRANCO_P, (int(x), int(y)), int(11 * k))
    pygame.draw.polygon(tela, AMARELO_B, [(x + 6 * k, y - 5 * k), (x + 18 * k, y - 2 * k), (x + 17 * k, y + 6 * k),
                                          (x + 12 * k, y + 2 * k), (x + 6 * k, y + 3 * k)])
    pygame.draw.circle(tela, (240, 200, 60), (int(x + 3 * k), int(y - 3 * k)), max(1, int(3 * k)))
    pygame.draw.line(tela, (120, 116, 110), (x - 3 * k, y - 8 * k), (x + 8 * k, y - 6 * k), max(1, int(2 * k)))


def desenhar_hud(jogo, tela):
    a = jogo.boss
    if a.estado in ("entrando", "agarrando", "levando", "arremesso"):
        return
    larg = 420
    x, y = LARGURA / 2 - larg / 2, 18
    frac = max(0.0, a.vida / VIDA)
    pygame.draw.rect(tela, PRETO, R(x - 3, y - 3, larg + 6, 18), border_radius=6)
    pygame.draw.rect(tela, (50, 34, 24), R(x, y, larg, 12), border_radius=4)
    cor = (230, 90, 50) if a.furiosa else (220, 170, 60)
    pygame.draw.rect(tela, cor, R(x, y, larg * frac, 12), border_radius=4)
    pygame.draw.rect(tela, (255, 230, 160), R(x + 2, y + 2, max(0, larg * frac - 4), 3), border_radius=2)
    mx = x + larg * FURIA / VIDA                                      # risquinho: daqui pra baixo ela fica furiosa
    pygame.draw.line(tela, PRETO, (mx, y - 4), (mx, y + 14), 2)
    icone_cabeca(tela, x - 26, y + 6)


# =====================================================================
# A corrida: a águia voando junto e a barrinha (sapo x águia x pergaminho)
# =====================================================================
def progresso_aguia(jogo):
    return max(0.0, min(1.0, jogo.corrida["t"] / TEMPO_AGUIA))


def progresso_sapo(jogo):
    x0, xf = jogo.fase.inicio[0], jogo.fase.toca.x
    return max(0.0, min(1.0, (jogo.ribbat.x - x0) / max(1, xf - x0)))


def pos_aguia_corrida(jogo):
    x0, xf = jogo.fase.inicio[0], jogo.fase.toca.x
    t = jogo.corrida["t"]
    return x0 + (xf - x0) * progresso_aguia(jogo), 96 + math.sin(t * 2) * 14 + min(0.0, t) * 90


def desenhar_corrida(jogo, tela):
    t = jogo.tempo_total
    ox, oy = jogo.cam_x, getattr(jogo, "cam_y", 0)
    ax, ay = pos_aguia_corrida(jogo)
    if -260 < ax - ox < LARGURA + 260:
        blit_aguia(tela, sprite("alto", round((math.sin(t * 7) + 1) / 2, 1)), ax - ox, ay - oy, 1, k=0.55)
    # a barrinha
    larg = 440
    x, y = LARGURA / 2 - larg / 2, 22
    pygame.draw.rect(tela, PRETO, R(x - 4, y - 4, larg + 8, 14), border_radius=7)
    pygame.draw.rect(tela, (230, 236, 246), R(x, y, larg, 6), border_radius=3)
    for i in range(1, 10):
        pygame.draw.line(tela, (170, 180, 200), (x + larg * i / 10, y), (x + larg * i / 10, y + 6), 1)
    import desenho as D
    D.pergaminho(tela, x + larg + 26, y + 3, 0.6, brilho=t * 1.5)
    pa, ps = progresso_aguia(jogo), progresso_sapo(jogo)
    icone_cabeca(tela, x + larg * pa, y + 3 - 16, 0.9)
    fx, fy = x + larg * ps, y + 3 + 18
    pygame.draw.circle(tela, PRETO, (int(fx), int(fy)), 13)
    pygame.draw.circle(tela, (112, 186, 80), (int(fx), int(fy)), 11)
    for ex in (-5, 5):
        pygame.draw.circle(tela, BRANCO, (int(fx + ex), int(fy - 7)), 4)
        pygame.draw.circle(tela, PRETO, (int(fx + ex + 1), int(fy - 7)), 2)
    if jogo.corrida["t"] < 0.6:                                        # luzinhas da largada
        acesas = 3 - max(0, math.ceil(-jogo.corrida["t"] / (LARGADA / 3)))
        for i in range(3):
            cx = LARGURA / 2 - 50 + i * 50
            pygame.draw.circle(tela, PRETO, (int(cx), 90), 20)
            if jogo.corrida["t"] >= 0:
                cor = (80, 220, 90)
            else:
                cor = (230, 60, 50) if i < acesas else (70, 40, 40)
            pygame.draw.circle(tela, cor, (int(cx), 90), 16)


def desenhar_chegada(tela, x, base, t):
    """No fim da corrida: uma pedra lá no alto com o PERGAMINHO brilhando em cima."""
    import desenho as D
    pygame.draw.polygon(tela, (96, 88, 86), [(x - 46, base), (x - 34, base - 46), (x + 30, base - 50), (x + 48, base)])
    pygame.draw.polygon(tela, (132, 122, 118), [(x - 34, base - 46), (x + 30, base - 50), (x + 20, base - 38), (x - 26, base - 36)])
    pygame.draw.rect(tela, (244, 248, 252), R(x - 34, base - 54, 64, 8), border_radius=4)
    luz = pygame.Surface((220, 220), pygame.SRCALPHA)
    for i in range(8):
        pygame.draw.circle(luz, (255, 230, 140, 16), (110, 110), 100 - i * 11)
    tela.blit(luz, (x - 110, base - 190))
    D.pergaminho(tela, x, base - 80 + math.sin(t * 2) * 5, 1.1, brilho=t * 1.2)


def desenhar_perdeu(jogo, tela):
    """A águia chegou primeiro: ela em pé em cima do pergaminho, o Ribbat tontinho. Enter = de novo."""
    import desenho as D
    t = jogo.tempo_total
    jogo.escurecer(tela)
    blit_aguia(tela, sprite("pousada", 0.0, int(t * 3) % 2 == 0, False), LARGURA / 2 + 60, ALTURA / 2 + 20, -1, k=0.9)
    D.pergaminho(tela, LARGURA / 2 + 40, ALTURA / 2 + 100, 1.0)
    D.desenhar_sapo(tela, LARGURA / 2 - 170, ALTURA / 2 + 110, 1, "tonto", escala=2.0, orelhas=jogo.orelhas_coelho)
    D.tecla(tela, jogo.fonte_tecla, LARGURA / 2 - 20, ALTURA - 60, "enter", 40)
