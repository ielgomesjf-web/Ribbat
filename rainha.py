"""
Chefão da Fase 3: a FORMIGA RAINHA (design do Gomes). Dano igual a Viúva: linguada 2, investida 3.

Estágio 1 (14 de dano) - voando
  - principal: ferroada (curva o abdômen, o ferrão brilha = aviso, atira 1 ferrão onde você tá)
  - especial (usa bastante): chama formigas pelos buracos do chão (às vezes uma guerreira)
Estágio 2 (14 de dano)
  - principal: rasante (sobe pro canto, mostra o caminho pontilhado e mergulha raspando o chão)
  - especial: rajada de ferroadas ("gomu gomu no gatling"): um monte de ferrões mirando em você.
    Fica correndo! Depois ela fica cansada no chão (hora de bater).
Estágio 3 - não ataca
  - foge pro trono lá em cima, aparecem raízes em escadinha e a HORDA DE FORMIGAS sobe.
    Escala sem encostar na horda e acerta UM ataque nela.
"""
import math
import random

import pygame

import som as SOM

from chefe import ESC, RECARGA_INVESTIDA, RECARGA_LINGUA, _Pincel, _pts_elipse, desenhar_raiz_plataforma  # noqa: F401
from besouro import _brilhante
from config import *  # noqa: F401,F403
from entidades import Formiga, FormigaGuerreira, R

ARENA = {"nome": "Câmara Real", "tema": "formigueiro", "pedacos": [[
    "....rrrrr............rrrrr....",
    "..............................",
    "..............................",
    "..S...........................",
    "##############################",
    "##############################",
]]}
CHAO_Y = 15 * TILE
VIDA = (14, 14)
DANO_LINGUA = 2
DANO_INVESTIDA = 3
BURACOS_X = (60, LARGURA - 60)

# estágio 3: escadinha de raízes (linha, coluna inicial, coluna final) e o trono
ESCADA = ((12, 2, 7), (10, 10, 15), (8, 3, 8), (6, 10, 15), (4, 17, 21))
TRONO = (840, 104)
HORDA_VEL = 26          # pixels por segundo que a horda de formigas sobe
HORDA_ESPERA = 3.0      # tempo antes da horda começar a subir
HORDA_DANO = 2         # encostar na horda tira 2 corações (pedido do Gomes)

import formigas as FA  # noqa: E402
GEO = FA.RAINHA["geo"]      # mesma geometria do desenho (formigas.py) = hitbox certinha
CORPO = (124, 36, 22)
CORPO_CLARO = (206, 96, 64)
CORPO_ESC = (46, 12, 8)
OURO = (246, 200, 70)


class Ferrao:
    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.vivo = True

    def rect(self):
        return R(self.x - 6, self.y - 6, 12, 12)

    def atualizar(self, dt):
        self.x += self.vx * dt                   # ferrão voa reto (sem cair)
        self.y += self.vy * dt
        if self.y > CHAO_Y or not -20 < self.x < LARGURA + 20 or self.y < -40:
            self.vivo = False


class Rainha:
    def __init__(self):
        self.estagio = 1
        self.vida = VIDA[0]
        self.x, self.y = 480.0, -120.0
        self.dir = -1
        self.estado = "entrando"
        self.tempo = 0.0
        self.t = 0.0
        self.flash = 0.0
        self.vivo = True
        self.puxando = False
        self.recarga = 0.0
        self.cd_principal = 2.0
        self.cd_especial = 3.0
        self.ferroes = []
        self.caminho = None          # rasante: (x0, x1)
        self.horda = None             # estágio 3: altura da horda
        self.acertou_3 = False

    def mudar(self, estado):
        self.estado, self.tempo = estado, 0.0

    # ---------- geometria ----------
    def curvatura(self):
        if self.estado == "mirando":
            return min(1.0, self.tempo / 0.5)
        if self.estado in ("metralhando", "ferroando"):
            return 1.0
        return 0.0

    def geo_gaster(self):
        c = self.curvatura()
        gx, gy, rx, ry = GEO["gaster"]
        return gx + 40 * c, gy + 34 * c, rx, ry, 0.25 + 1.3 * c

    def ponta_ferrao(self):
        gx, gy, rx, ry, ang = self.geo_gaster()
        tx, ty = gx - math.cos(ang) * rx, gy - math.sin(ang) * rx
        return self.x + self.dir * tx, self.y + ty

    @property
    def vulneravel(self):
        return self.estado not in ("entrando", "irritada", "fugindo", "morrendo")

    def partes(self):
        d = self.dir
        cx, cy, rx, ry = GEO["cabeca"]
        tx, ty, trx, try_ = GEO["torax"]
        gx, gy, grx, gry, _ = self.geo_gaster()

        def caixa(x, y, w, h):
            return R(self.x + d * x - w, self.y + y - h, w * 2, h * 2)
        return [caixa(gx, gy, grx * 0.9, gry * 0.9), caixa(tx, ty, trx, try_), caixa(cx, cy, rx, ry)]

    def hitbox(self):
        return self.partes() if self.vulneravel else None

    def perigos(self):
        if not self.vulneravel or self.estagio == 3:
            return []
        lista = [r.inflate(-16, -16) for r in self.partes()]
        if self.estado == "rasante":
            lista = [r.inflate(-6, -6) for r in self.partes()]
        return lista

    # ---------- dano ----------
    def levar(self, dano, jogo):
        if not self.vulneravel:
            return False
        hb = self.partes()[-1]
        jogo.faiscas(hb.centerx, hb.centery, OURO, 12, 240)
        jogo.tremer(4)
        self.flash = 0.12
        if self.estagio == 3:
            self.mudar("morrendo")
            jogo.fase.inimigos = []
            return True
        self.vida -= dano
        if self.vida <= 0:
            self.ferroes.clear()
            self.caminho = None
            if self.estagio == 1:
                self.mudar("irritada")
            else:
                self.mudar("fugindo")
                jogo.fase.inimigos = []      # as formigas viram a horda
                jogo.torres = []
        return True

    # ---------- comportamento ----------
    def atualizar(self, dt, jogo):
        r = jogo.ribbat
        self.t += dt
        self.tempo += dt
        self.flash = max(0.0, self.flash - dt)
        for f in self.ferroes:
            f.atualizar(dt)
        self.ferroes = [f for f in self.ferroes if f.vivo]
        e = self.estado
        if e == "entrando":
            self.y += (200 - self.y) * min(1, dt * 2)
            if self.tempo > 2.0:
                self.mudar("voando")
            return
        if e == "irritada":                      # troca pro estágio 2: treme e grita
            if self.tempo > 2.0:
                self.estagio, self.vida = 2, VIDA[1]
                self.cd_principal, self.cd_especial = 1.5, 6.0
                self.mudar("voando")
            return
        if e == "fugindo":                       # estágio 3: voa pro trono, aparece a escada
            tx, ty = TRONO
            self.x += (tx - self.x) * min(1, dt * 2.5)
            self.y += (ty - self.y) * min(1, dt * 2.5)
            self.dir = -1
            if self.tempo > 1.6:
                self.estagio = 3
                for c in [c for c, ch in jogo.fase.solidos.items() if ch == "r"]:
                    del jogo.fase.solidos[c]
                for linha, c0, c1 in ESCADA:
                    for c in range(c0, c1 + 1):
                        jogo.fase.solidos[(c, linha)] = "r"
                self.horda = CHAO_Y + 20
                self.mudar("no_trono")
            return
        if e == "no_trono":
            if self.tempo > HORDA_ESPERA:
                self.horda -= HORDA_VEL * dt
            return
        if e == "morrendo":
            if self.tempo < dt * 1.5:                       # a coroa sai voando
                self.coroa = [self.x + self.dir * GEO["cabeca"][0], self.y - 40, self.dir * 120, -380]
                self.vy = 0.0
            chao = CHAO_Y - 30
            if self.y < chao:
                self.vy = getattr(self, "vy", 0.0) + GRAVIDADE * 0.8 * dt
                self.y = min(chao, self.y + self.vy * dt)
                if self.y >= chao:
                    jogo.tremer(8)
                    jogo.poeira(self.x, CHAO_Y, 14)
            c = self.coroa
            c[3] += GRAVIDADE * dt
            c[0] += c[2] * dt
            c[1] += c[3] * dt
            if c[1] > CHAO_Y - 8:
                c[1], c[3], c[2] = CHAO_Y - 8, -c[3] * 0.45, c[2] * 0.6
            if self.tempo > 3.0:
                self.vivo = False
                jogo.venceu_chefe()
            return
        dx = r.cx - self.x
        if e == "voando":
            vel = 1.0 if self.estagio == 1 else 1.4
            alvo_x = 480 + math.sin(self.t * 0.5 * vel) * 230
            self.x += (alvo_x - self.x) * min(1, dt * 1.5)
            self.y = 200 + math.sin(self.t * 1.6) * 40
            self.dir = 1 if dx > 0 else -1
            self.cd_principal -= dt
            self.cd_especial -= dt
            if self.cd_especial <= 0:
                self.mudar("chamando" if self.estagio == 1 else "posicionando")
            elif self.cd_principal <= 0:
                self.mudar("mirando" if self.estagio == 1 else "subindo")
        # ----- estágio 1 -----
        elif e == "mirando":
            self.dir = 1 if dx > 0 else -1
            if self.tempo > 0.6:
                fx, fy = self.ponta_ferrao()
                ang = math.atan2((r.y + r.H / 2) - fy, r.cx - fx)
                self.ferroes.append(Ferrao(fx, fy, math.cos(ang) * 470, math.sin(ang) * 470))
                self.mudar("ferroando")
        elif e == "ferroando":
            if self.tempo > 0.3:
                self.cd_principal = 2.6
                self.mudar("voando")
        elif e == "chamando":
            if self.tempo > 1.2:
                self.chamar(jogo)
                self.cd_especial = 8.0
                self.mudar("voando")
        # ----- estágio 2 -----
        elif e == "subindo":
            canto = 80 if r.cx > 480 else LARGURA - 80        # vai pro canto do outro lado
            self.x += (canto - self.x) * min(1, dt * 4)
            self.y += (70 - self.y) * min(1, dt * 4)
            self.dir = 1 if canto < 480 else -1
            if self.tempo > 0.9:
                self.caminho = (canto, LARGURA - canto)
                self.mudar("preparando")
        elif e == "preparando":                  # caminho pontilhado aparece (aviso)
            if self.tempo > 0.7:
                self.mudar("rasante")
        elif e == "rasante":
            u = min(1.0, self.tempo / 1.3)
            x0, x1 = self.caminho
            self.x = x0 + (x1 - x0) * u
            self.y = 70 + (CHAO_Y - 34 - 70) * (1 - (2 * u - 1) ** 2)
            if u >= 1:
                self.caminho = None
                self.cd_principal = 4.0
                self.mudar("voando")
        elif e == "posicionando":
            self.x += (480 - self.x) * min(1, dt * 4)
            self.y += (110 - self.y) * min(1, dt * 4)
            if self.tempo > 0.6:
                self.cd_tiro = 0.0
                self.mudar("metralhando")
        elif e == "metralhando":                 # gomu gomu no gatling!
            self.dir = 1 if dx > 0 else -1
            self.cd_tiro -= dt
            if self.cd_tiro <= 0:
                self.cd_tiro = 0.12
                fx, fy = self.ponta_ferrao()
                ang = math.atan2((r.y + r.H / 2) - fy, r.cx - fx) + random.uniform(-0.06, 0.06)
                self.ferroes.append(Ferrao(fx, fy, math.cos(ang) * 520, math.sin(ang) * 520))
            if self.tempo > 1.6:
                self.mudar("cansada")
        elif e == "cansada":                     # desce bufando: hora de bater!
            self.y += (CHAO_Y - 60 - self.y) * min(1, dt * 3)
            if self.tempo > 2.6:
                self.cd_especial = 10.0
                self.mudar("voando")

    def chamar(self, jogo):
        vivas = [e for e in jogo.fase.inimigos if e.vivo]
        if len(vivas) >= 4:
            return
        for i, x in enumerate(BURACOS_X):                 # 1 formiga por buraco
            f = Formiga(x - Formiga.W / 2, CHAO_Y - Formiga.H, 1 if i == 0 else -1)
            f.estado = "ataque"
            jogo.fase.inimigos.append(f)
            jogo.poeira(x, CHAO_Y, 8)
        self.chamados = getattr(self, "chamados", 0) + 1
        guerreiras = sum(isinstance(e, FormigaGuerreira) for e in vivas)
        if guerreiras < 1 and self.chamados % 2 == 0:     # guerreira só de vez em quando
            g = FormigaGuerreira(random.choice((200, 760)), 150)
            g.cd = 1.5
            jogo.fase.inimigos.append(g)


# =====================================================================
# Luta
# =====================================================================
def criar():
    return Rainha()


def _formigas(jogo, dt, ent, pr, lingua, pe_antes):
    """As formigas chamadas pela rainha: mesmas regras da fase (pisão, linguada, investida)."""
    r = jogo.ribbat
    jogo.coordenar_formigas(dt)
    for e in list(jogo.fase.inimigos):
        e.atualizar(dt, jogo.fase, jogo)
        if not e.vivo:
            continue
        er = e.rect()
        if lingua and lingua.colliderect(er):
            jogo.derrotar(e)
        elif pr.colliderect(er):
            if r.dash_t > 0:
                jogo.derrotar(e)
            elif r.vy > 0 and pe_antes <= er.top + 10:
                jogo.derrotar(e)
                r.vy = -QUIQUE * (1.4 if ent.pulo else 1.0)
                r.pulando = ent.pulo
                r.dash_pronto = True
            else:
                r.machucar(jogo, e.cx)
        if jogo.estado != "chefe":
            return
    jogo.fase.inimigos = [e for e in jogo.fase.inimigos if e.vivo]


def atualizar(jogo, dt, ent):
    r, b = jogo.ribbat, jogo.boss
    pe_antes = r.y + r.H
    r.atualizar(dt, ent, jogo)
    b.atualizar(dt, jogo)
    if jogo.estado != "chefe":
        return
    pr = r.rect()
    lingua = r.rect_lingua()
    _formigas(jogo, dt, ent, pr, lingua, pe_antes)
    if jogo.estado != "chefe":
        return
    hb = b.hitbox()
    if hb:
        if lingua and not r.lingua_acertou and lingua.collidelist(hb) >= 0:
            r.lingua_acertou = True
            if b.levar(DANO_LINGUA, jogo):
                SOM.efeito("acerto")
        if r.dash_t > 0 and not r.dash_acertou and pr.collidelist(hb) >= 0:
            r.dash_acertou = True
            if b.levar(DANO_INVESTIDA, jogo):
                SOM.efeito("acerto")
            r.dash_t = 0
            r.vx = -r.dir * 330
            r.vy = -380
            r.invuln = max(r.invuln, 0.5)
            r.atordoado = 0.2
    if r.dash_t <= 0 and any(pr.colliderect(p) for p in b.perigos()):
        r.machucar(jogo, b.x)
    for f in b.ferroes:
        if lingua and lingua.colliderect(f.rect()):
            f.vivo = False
            jogo.faiscas(f.x, f.y, OURO, 5)
        elif pr.colliderect(f.rect()):
            f.vivo = False
            r.machucar(jogo, f.x)
    if b.horda is not None and r.y + r.H > b.horda + 8 and r.invuln <= 0:
        # a horda de formigas te pegou: perde 2 CORAÇÕES e é jogado pra cima
        jogo.coracoes -= HORDA_DANO - 1
        r.machucar(jogo, r.cx)
        jogo.coracoes = max(0, jogo.coracoes)
        if jogo.coracoes <= 0 and jogo.estado == "chefe":
            jogo.game_over()
        r.vy = -820
        r.vx = 0
        r.invuln = 1.6
        jogo.poeira(r.cx, b.horda, 10)
    jogo.efeitos(dt)


# =====================================================================
# Desenho
# =====================================================================
_fundo = None
CAIXA = (380, 280)
ORIGEM = (200, 150)


def criar_fundo():
    """A câmara real: cúpula de terra enfeitada, ovos, jardim de fungo e o trono lá no alto."""
    s = pygame.Surface((LARGURA, ALTURA))
    for y in range(ALTURA):
        k = y / ALTURA
        s.fill([int(a + (b - a) * k) for a, b in zip((40, 26, 18), (84, 58, 40))], R(0, y, LARGURA, 1))
    rnd = random.Random(41)
    cupula = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    pygame.draw.ellipse(cupula, (110, 78, 52, 70), R(-60, -200, LARGURA + 120, CHAO_Y + 240), 30)
    s.blit(cupula, (0, 0))
    for i in range(26):                         # enfeite de folhinhas e sementes na cúpula
        a = math.pi * (0.06 + i / 26 * 0.88)
        x, y = LARGURA / 2 - math.cos(a) * (LARGURA / 2 + 30), CHAO_Y + 20 - math.sin(a) * (CHAO_Y + 100)
        if 0 < y < CHAO_Y:
            cor = (96, 146, 66) if i % 2 else (226, 196, 128)
            pygame.draw.ellipse(s, cor, R(x - 9, y - 5, 18, 10))
    for x in (260, 700):                         # montes de ovos
        for k, (ex, ey) in enumerate(((-16, 0), (0, 0), (16, 0), (-8, -12), (8, -12), (0, -24))):
            pygame.draw.ellipse(s, (226, 218, 196), R(x + ex - 7, CHAO_Y - 20 + ey, 14, 18))
    for _ in range(5):                           # tufinhos de fungo
        x = rnd.randint(120, LARGURA - 120)
        for k in range(14):
            pygame.draw.circle(s, (204, 198, 170), (x + rnd.randint(-20, 20), CHAO_Y - 10 + rnd.randint(-10, 4)), rnd.randint(2, 4))
    tx, ty = TRONO                               # trono: torrão com folha de encosto
    pygame.draw.ellipse(s, (96, 140, 64), R(tx - 34, ty - 70, 70, 80))
    pygame.draw.rect(s, (120, 86, 58), R(tx - 70, ty + 26, 140, 24), border_radius=10)
    pygame.draw.rect(s, (150, 112, 76), R(tx - 70, ty + 26, 140, 8), border_radius=6)
    pygame.draw.rect(s, (54, 38, 26), R(0, CHAO_Y, LARGURA, ALTURA - CHAO_Y))
    pygame.draw.line(s, (140, 104, 72), (0, CHAO_Y + 1), (LARGURA, CHAO_Y + 1), 3)
    for x in BURACOS_X:
        pygame.draw.ellipse(s, (140, 104, 72), R(x - 30, CHAO_Y - 12, 60, 18))
        pygame.draw.ellipse(s, (14, 8, 4), R(x - 20, CHAO_Y - 8, 40, 12))
    return s


def _desenhar_rainha(p, b, t):
    e = b.estado
    if e == "morrendo":                          # caída de lado: asas murchas, perninhas encolhidas tremendo
        FA.desenhar(p, FA.RAINHA, t, bate=0.8, abre=0.1, olho=None, coroa=False, ferrao=(30, 10, 6),
                    voando=False, pernas_y=46, morta=True)
        return
    voando = e not in ("no_trono", "morrendo", "cansada")
    bate = abs(math.sin(t * 36)) if voando else 0.1
    abre = 0.85 if e in ("chamando", "irritada", "rasante") else 0.25
    olho = (255, 80, 40) if e in ("irritada", "chamando") and int(t * 12) % 2 else None
    brilho = e in ("mirando", "metralhando")
    ferrao = (230, 240, 120) if brilho and int(t * 14) % 2 else (30, 10, 6)
    FA.desenhar(p, FA.RAINHA, t, bate=bate, abre=abre, gaster=b.geo_gaster(), olho=olho, coroa=True,
                ferrao=ferrao, voando=voando, pernas_y=46)


def desenhar_rainha(tela, b, t):
    w, h = CAIXA
    s = pygame.Surface((w * ESC, h * ESC), pygame.SRCALPHA)
    _desenhar_rainha(_Pincel(s, *ORIGEM), b, t)
    img = pygame.transform.smoothscale(s, CAIXA)
    if b.dir < 0:
        img = pygame.transform.flip(img, True, False)
    ang = 0
    if b.estado == "rasante":
        u = min(1.0, b.tempo / 1.3)
        ang = -b.dir * (1 - 2 * u) * 35 * -1
    elif b.estado == "morrendo":
        ang = -b.dir * 14 * min(1.0, b.tempo / 0.5)        # deitadinha de lado
    if b.flash > 0:
        img = img.copy()
        img.fill((140, 140, 140), special_flags=pygame.BLEND_RGB_ADD)
    if ang:
        img = pygame.transform.rotate(img, ang)
    tremor = math.sin(t * 50) * 3 if b.estado in ("irritada", "chamando") else 0
    tela.blit(img, img.get_rect(center=(b.x + (w / 2 - ORIGEM[0]) * b.dir + tremor, b.y + h / 2 - ORIGEM[1])))


def desenhar_horda(tela, y, t):
    """A horda de formigas subindo: um mar de formiguinhas se mexendo."""
    camada = pygame.Surface((LARGURA, ALTURA - int(y) + 20), pygame.SRCALPHA)
    camada.fill((42, 14, 8, 245))
    rnd = random.Random(7)
    for i in range(140):
        x = (rnd.uniform(0, LARGURA) + t * rnd.uniform(-60, 60)) % LARGURA
        yy = rnd.uniform(0, ALTURA - y)
        pygame.draw.ellipse(camada, (110, 34, 22), R(x - 5, yy, 10, 6))
        pygame.draw.circle(camada, (130, 40, 26), (int(x + 6), int(yy + 3)), 3)
    tela.blit(camada, (0, y))
    for i in range(48):                          # formiguinhas na superfície, com antena pra cima
        x = (i * 21 + t * (40 if i % 2 else -40)) % LARGURA
        yy = y + math.sin(t * 6 + i) * 4
        pygame.draw.ellipse(tela, (140, 44, 28), R(x - 7, yy - 6, 14, 9))
        pygame.draw.circle(tela, (150, 50, 30), (int(x + 7), int(yy - 4)), 4)
        pygame.draw.line(tela, (60, 20, 12), (x + 8, yy - 7), (x + 12 + math.sin(t * 9 + i) * 2, yy - 14), 1)
        for k in (-1, 1):
            pygame.draw.line(tela, (60, 20, 12), (x + k * 3, yy), (x + k * 7, yy + 5), 1)


def desenhar(jogo, tela):
    global _fundo
    if _fundo is None:
        _fundo = criar_fundo()
    import formigueiro as FM
    b, t = jogo.boss, jogo.tempo_total
    tx = random.uniform(-jogo.tremor, jogo.tremor) if jogo.tremor > 0 else 0
    ty = random.uniform(-jogo.tremor, jogo.tremor) if jogo.tremor > 0 else 0
    tela.blit(_fundo, (tx, ty))
    for (cx, cy), ch in jogo.fase.solidos.items():
        if ch == "r" and (cx - 1, cy) not in jogo.fase.solidos:
            fim = cx
            while (fim + 1, cy) in jogo.fase.solidos:
                fim += 1
            desenhar_raiz_plataforma(tela, R(cx * TILE + tx, cy * TILE + ty, (fim - cx + 1) * TILE, 18))
    if b.estado == "preparando" and b.caminho:   # caminho pontilhado do rasante (aviso)
        x0, x1 = b.caminho
        for i in range(0, 41):
            if i % 2 == 0 and int(t * 10) % 2 == 0:
                u = i / 40
                x = x0 + (x1 - x0) * u
                y = 70 + (CHAO_Y - 34 - 70) * (1 - (2 * u - 1) ** 2)
                pygame.draw.circle(tela, (255, 220, 120), (int(x + tx), int(y + ty)), 4)
    for e in jogo.fase.inimigos:
        if isinstance(e, FormigaGuerreira):
            FM.desenhar_guerreira(tela, e, -tx, -ty, t)
        else:
            import desenho as D
            D.desenhar_formiga(tela, e.x + tx, e.y + ty, e.W, e.H, e.dir, e.anim, parada=e.nivel > 0)
            if e.estado == "alerta":
                D.desenhar_alerta(tela, e.cx + tx, e.y - 16 + ty)
    desenhar_rainha(tela, b, t)
    if b.estado == "morrendo" and getattr(b, "coroa", None):     # a coroa caída, quicando
        cx, cy = b.coroa[0] + tx, b.coroa[1] + ty
        pygame.draw.polygon(tela, OURO, [(cx - 14, cy + 8), (cx - 14, cy - 8), (cx - 7, cy), (cx, cy - 12), (cx + 7, cy),
                                         (cx + 14, cy - 8), (cx + 14, cy + 8)])
        pygame.draw.circle(tela, (220, 40, 60), (int(cx), int(cy + 1)), 3)
        for i in range(3):
            a = t * 4 + i * math.tau / 3
            pygame.draw.circle(tela, AMARELO, (int(b.x + math.cos(a) * 40), int(b.y - 70 + math.sin(a) * 8)), 5)
    for f in b.ferroes:                          # ferrões
        ang = math.atan2(f.vy, f.vx)
        a = (f.x - math.cos(ang) * 10, f.y - math.sin(ang) * 10)
        pygame.draw.line(tela, (30, 10, 6), a, (f.x + math.cos(ang) * 6, f.y + math.sin(ang) * 6), 4)
        pygame.draw.circle(tela, (220, 240, 120), (int(f.x + math.cos(ang) * 7), int(f.y + math.sin(ang) * 7)), 3)
    jogo.desenhar_ribbat(tela, -tx, -ty)
    if b.horda is not None:
        desenhar_horda(tela, b.horda + ty, t)
    jogo.desenhar_efeitos(tela, -tx, -ty)
    desenhar_hud(jogo, tela)


def desenhar_hud(jogo, tela):
    """Barra de vida + 3 coroinhas = 3 estágios. No estágio 3 a barra é só 1 coroa piscando."""
    b = jogo.boss
    if b.estado in ("entrando", "morrendo"):
        return
    larg = 360
    x, y = LARGURA / 2 - larg / 2, 18
    if b.estagio < 3 and b.estado not in ("fugindo",):
        frac = max(0.0, b.vida / VIDA[b.estagio - 1]) if b.estado != "irritada" else min(1.0, b.tempo / 2.0)
    else:
        frac = 1.0 if int(jogo.tempo_total * 4) % 2 else 0.85
    pygame.draw.rect(tela, PRETO, R(x - 3, y - 3, larg + 6, 18), border_radius=6)
    pygame.draw.rect(tela, (60, 20, 14), R(x, y, larg, 12), border_radius=4)
    pygame.draw.rect(tela, (230, 170, 50), R(x, y, larg * frac, 12), border_radius=4)
    pygame.draw.rect(tela, (255, 230, 150), R(x + 2, y + 2, max(0, larg * frac - 4), 3), border_radius=2)
    for i in range(3):
        cx = x - 26 - i * 26
        falta = i < 4 - b.estagio - (1 if b.estado in ("irritada", "fugindo") else 0)
        cor = OURO if falta else (80, 60, 40)
        pygame.draw.polygon(tela, cor, [(cx - 9, y + 12), (cx - 9, y - 2), (cx - 4, y + 4), (cx, y - 5), (cx + 4, y + 4),
                                        (cx + 9, y - 2), (cx + 9, y + 12)])
