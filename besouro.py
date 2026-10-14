"""
Chefão da Fase 2: o BESOURO-RINOCERONTE (design do Gomes). Cada acerto (linguada OU investida) conta 1.

Estágio 1 (12 acertos) - armadura de placas marrom
  - principal: chifrada de perto (abaixa a cabeça = aviso, depois mete o chifre)
  - especial: cava o chão (aviso) e dá 3 VOLTAS na toca: chão, parede, teto, parede.
    Fica no meio e pula quando ele passar pelo chão.
Estágio 2 (10 acertos) - a armadura racha
  - principal: patada de mamute (empina, bate a pata) -> onda de terra pros dois lados: pula!
  - especial: sai quicando pela toca (5 pulos); a sombra mostra onde ele vai cair
Estágio 3 (8 acertos) - a armadura quebrou: virou um tatu
  - principal: rabada (rabo balança = aviso, depois gira o rabo baixinho)
  - especial: enrola igual o Sonic e sai rolando e quicando. Se pegar, PRENSA (morte na hora),
    mas a bola é baixa e dá pra pular.
"""
import math
import random

import pygame

import som as SOM

from chefe import ESC, RECARGA_INVESTIDA, RECARGA_LINGUA, _Pincel, _pts_elipse  # noqa: F401
from config import *  # noqa: F401,F403
from entidades import R

ARENA = {"nome": "Toca do Besouro", "tema": "lamacal", "pedacos": [[
    "..S...........................",
    "##############################",
    "##############################",
]]}
CHAO_Y = 15 * TILE
VIDA = (12, 10, 8)
DANO = 1

# volta na toca (posição dos PÉS dele em cada lado da toca)
VOLTA_VEL = 1000
VOLTA_LADOS = ((840, "chao"), (360, "parede_d"), (840, "teto"), (360, "parede_e"))
VOLTA_TOTAL = sum(c for c, _ in VOLTA_LADOS)

SOBE = (0, 0, 0)       # besouro de verdade é baixo e parrudo (pernas curtas)

# Geometria (desenho virado pra direita, origem no chão embaixo dele): centro x, centro y, raio x, raio y.
# O DESENHO e a HITBOX usam essas mesmas medidas.
GEO_BESOURO = {"elitro": (-30, -54, 88, 48), "pronoto": (44, -56, 38, 33), "cabeca": (90, -28, 22, 17)}
GEO_TATU = {"casco": (-14, -46, 92, 42), "cabeca": (100, -26, 30, 18)}

# besouro-rinoceronte: mogno escuro e brilhante
CASCA = (92, 44, 22)
CASCA_CLARA = (196, 116, 66)
CASCA_ESC = (34, 15, 7)
PATA = (40, 20, 10)
CHIFRE = (58, 26, 12)
PELO = (196, 150, 80)          # pelinhos dourados das pernas
# tatu-rinoceronte
TATU = (176, 150, 124)         # carapaça
TATU_CLARO = (222, 202, 174)
TATU_ESC = (104, 84, 66)
PELE = (214, 168, 156)         # barriga e cabeça (sem armadura)


def pos_volta(s, sentido):
    """Onde estão os pés dele na volta (s = distância andada) e pra que lado ele tá virado (graus)."""
    s %= VOLTA_TOTAL
    for comp, lado in VOLTA_LADOS:
        if s < comp:
            break
        s -= comp
    if lado == "chao":
        x, y, ang = 60 + s, CHAO_Y, 0
    elif lado == "parede_d":
        x, y, ang = LARGURA, CHAO_Y - 60 - s, 90
    elif lado == "teto":
        x, y, ang = LARGURA - 60 - s, 0, 180
    else:
        x, y, ang = 0, 60 + s, 270
    if sentido < 0:                       # anti-horário = espelho
        x, ang = LARGURA - x, -ang
    return x, y, ang


class Onda:
    """Onda de terra da patada: corre pelo chão. Pula!"""

    def __init__(self, x, d):
        self.x, self.d = x, d
        self.vivo = True
        self.t = 0.0

    def rect(self):
        return R(self.x - 14, CHAO_Y - 30, 28, 30)

    def atualizar(self, dt):
        self.t += dt
        self.x += self.d * 380 * dt
        if not -40 < self.x < LARGURA + 40:
            self.vivo = False


class Besouro:
    def __init__(self):
        self.estagio = 1
        self.vida = VIDA[0]
        self.x, self.y = 740.0, CHAO_Y + 130
        self.dir = -1
        self.estado = "entrando"
        self.tempo = 0.0
        self.t = 0.0
        self.flash = 0.0
        self.andar = 0.0
        self.vivo = True
        self.puxando = False
        self.recarga = 0.0
        self.cd_principal = 2.0
        self.cd_especial = 7.0
        self.ondas = []
        self.s = 0.0                 # volta na toca
        self.s_fim = 0.0
        self.sentido = 1
        self.ang = 0.0               # rotação do desenho (volta na parede/teto)
        self.vx = self.vy = 0.0
        self.pulos = 0
        self.alvo_x = None           # onde vai cair (sombra)
        self.rot = 0.0               # giro da bola
        self.quiques = 0

    def mudar(self, estado):
        self.estado = estado
        self.tempo = 0.0

    # ---------- geometria ----------
    @property
    def vulneravel(self):
        return self.estado not in ("entrando", "rachando", "morrendo")

    @property
    def bola(self):
        return self.estado in ("enrolando", "rolando")

    def mundo(self, dx, dy):
        return self.x + self.dir * dx, self.y + dy

    @property
    def sobe(self):
        return SOBE[self.estagio - 1]

    def caixa(self, centro, w, h):
        cx, cy = self.mundo(*centro)
        return R(cx - w / 2, cy - h / 2, w, h)

    def partes(self):
        if self.estado == "correndo":
            x, y, ang = pos_volta(self.s, self.sentido)
            nx, ny = {0: (0, -1), 90: (-1, 0), -90: (1, 0), 180: (0, 1), -180: (0, 1), 270: (1, 0), -270: (-1, 0)}[ang]
            cx, cy = x + nx * 50, y + ny * 50
            w, h = (170, 100) if ang in (0, 180, -180) else (100, 170)
            return [R(cx - w / 2, cy - h / 2, w, h)]
        if self.bola:
            return [R(self.x - 46, self.y - 96, 92, 92)]
        geo = GEO_TATU if self.estagio == 3 else GEO_BESOURO
        return [self.caixa((cx, cy), rx * 2, ry * 2) for cx, cy, rx, ry in geo.values()]

    def hitbox(self):
        return self.partes() if self.vulneravel else None

    def perigos(self):
        """(retângulo, letal?) de tudo nele que machuca agora."""
        if not self.vulneravel:
            return []
        e = self.estado
        if e == "correndo" and self.tempo < 0.2:
            return []                            # arrancada: quem tava colado nele não leva nada
        if e == "rolando" or e == "enrolando":
            return [(r, e == "rolando") for r in self.partes()]
        lista = [(r.inflate(-18, -18), False) for r in self.partes()]
        if e == "chifrando":
            a, b = self.mundo(96, -150), self.mundo(196, 0)
            lista.append((R(min(a[0], b[0]), a[1], abs(b[0] - a[0]), b[1] - a[1]), False))
        elif e == "batendo" and self.tempo < 0.12:
            lista.append((R(self.x - 130, CHAO_Y - 50, 260, 50), False))
        elif e == "rabada":
            lista.append((R(self.x - 175, CHAO_Y - 54, 350, 54), False))
        return lista

    # ---------- dano ----------
    def levar(self, dano, jogo):
        if not self.vulneravel:
            return False
        self.vida -= dano
        self.flash = 0.12
        hb = self.partes()[-1]
        cor = TATU_CLARO if self.estagio == 3 else CASCA_CLARA
        jogo.faiscas(hb.centerx, hb.centery, cor, 12, 240)
        jogo.tremer(4)
        if self.vida <= 0:
            self.ondas.clear()
            self.alvo_x = None
            if not self.bola and self.estado != "correndo":
                self.y = CHAO_Y
            self.y, self.vx, self.vy = CHAO_Y, 0.0, 0.0
            if self.estado == "correndo":
                self.x = min(max(pos_volta(self.s, self.sentido)[0], 110), LARGURA - 110)
            self.ang = 0.0
            self.mudar("morrendo" if self.estagio == 3 else "rachando")
            for _ in range(4):
                jogo.faiscas(self.x, CHAO_Y - 70, CASCA if self.estagio < 3 else TATU, 10, 320)
        return True

    # ---------- comportamento ----------
    def atualizar(self, dt, jogo):
        r = jogo.ribbat
        self.t += dt
        self.tempo += dt
        self.flash = max(0.0, self.flash - dt)
        for o in self.ondas:
            o.atualizar(dt)
        self.ondas = [o for o in self.ondas if o.vivo]
        e = self.estado
        if e == "entrando":                      # sai de dentro da terra
            self.y += (CHAO_Y - self.y) * min(1, dt * 3)
            if int(self.tempo * 10) % 2 == 0:
                jogo.poeira(self.x + random.uniform(-80, 80), CHAO_Y, 2)
            if self.tempo > 2.0:
                self.y = CHAO_Y
                self.mudar("andando")
            return
        if e == "rachando":
            if self.tempo > 2.0:
                self.estagio += 1
                self.vida = VIDA[self.estagio - 1]
                self.cd_principal, self.cd_especial = 1.5, 7.0
                self.mudar("andando")
            return
        if e == "morrendo":
            if self.tempo > 3.0:
                self.vivo = False
                jogo.venceu_chefe()
            return
        dx = r.cx - self.x
        if e == "andando":
            self.dir = 1 if dx > 0 else -1
            vel = (70, 85, 100)[self.estagio - 1]
            if abs(dx) > 200:                     # para antes da cabeça encostar em você
                self.x = max(110, min(LARGURA - 110, self.x + self.dir * vel * dt))
                self.andar += dt
            self.cd_principal -= dt
            self.cd_especial -= dt
            alcance = (200, 320, 210)[self.estagio - 1]
            encurralado = (r.cx < 170 and self.x > r.cx) or (r.cx > LARGURA - 170 and self.x < r.cx)
            if encurralado:
                # não prende ninguém na parede: dá espaço e volta pro meio
                self.x = max(110, min(LARGURA - 110, self.x - self.dir * vel * 1.3 * dt))
                self.andar += dt
                self.cd_principal = max(self.cd_principal, 0.6)
            if self.cd_especial <= 0:
                self.mudar(("cavando", "agachando", "enrolando")[self.estagio - 1])
            elif self.cd_principal <= 0 and abs(dx) < alcance:
                self.mudar(("mirando", "levantando", "balancando")[self.estagio - 1])
        # ----- estágio 1 -----
        elif e == "mirando":
            if self.tempo > 0.5:
                self.mudar("chifrando")
        elif e == "chifrando":
            self.x = max(110, min(LARGURA - 110, self.x + self.dir * 220 * dt))
            if self.tempo > 0.3:
                self.mudar("recuperando")
        elif e == "cavando":
            self.andar += dt * 3
            if int(self.tempo * 10) != int((self.tempo - dt) * 10):
                jogo.poeira(self.x - self.dir * 90, CHAO_Y, 4)
                jogo.tremer(2)
            if self.tempo > 1.0:
                self.sentido = self.dir
                xm = self.x if self.sentido > 0 else LARGURA - self.x
                self.s = min(max(xm - 60, 0), 840)
                self.s_fim = self.s + 3 * VOLTA_TOTAL
                self.mudar("correndo")
        elif e == "correndo":
            self.s += VOLTA_VEL * dt
            self.andar += dt * 4
            x, y, self.ang = pos_volta(self.s, self.sentido)
            self.dir = self.sentido
            if self.s >= self.s_fim:
                self.x, self.y, self.ang = x, CHAO_Y, 0.0
                self.cd_especial = 9.0
                self.mudar("recuperando")
            else:
                self.x, self.y = x, y
        # ----- estágio 2 -----
        elif e == "levantando":
            if self.tempo > 0.7:
                self.mudar("batendo")
                jogo.tremer(10)
                jogo.poeira(self.x + self.dir * 60, CHAO_Y, 12)
                self.ondas += [Onda(self.x - 110, -1), Onda(self.x + 110, 1)]
        elif e == "batendo":
            if self.tempo > 0.25:
                self.cd_principal = 2.2
                self.mudar("recuperando")
        elif e == "agachando":
            if self.tempo > 0.6:
                self.pulos = 0
                self.pular(r)
                self.mudar("quicando")
        elif e == "quicando":
            if self.alvo_x is None:                       # pausinha entre um pulo e outro
                if self.tempo > 0.3:
                    if self.pulos >= 5:
                        self.cd_especial = 10.0
                        self.mudar("recuperando")
                    else:
                        self.pular(r)
                        self.tempo = 0.0
            else:
                self.vy += 1800 * dt
                self.x += self.vx * dt
                self.y += self.vy * dt
                if self.y >= CHAO_Y and self.vy > 0:
                    self.y = CHAO_Y
                    self.alvo_x = None
                    self.tempo = 0.0
                    jogo.tremer(6)
                    jogo.poeira(self.x, CHAO_Y, 10)
        # ----- estágio 3 -----
        elif e == "balancando":
            if self.tempo > 0.6:
                self.mudar("rabada")
        elif e == "rabada":
            if self.tempo > 0.4:
                self.cd_principal = 2.0
                self.mudar("recuperando")
        elif e == "enrolando":
            self.rot += dt * 900 * min(1.0, self.tempo)
            if int(self.tempo * 12) != int((self.tempo - dt) * 12):
                jogo.poeira(self.x - self.dir * 40, CHAO_Y, 3)
            if self.tempo > 1.2:
                self.vx = self.dir * 650
                self.vy = 0.0
                self.quiques = 0
                self.mudar("rolando")
        elif e == "rolando":
            self.rot += self.vx * dt * 1.3
            self.x += self.vx * dt
            if self.y < CHAO_Y or self.vy < 0:
                self.vy += 2000 * dt
                self.y += self.vy * dt
                if self.y >= CHAO_Y:
                    self.y, self.vy = CHAO_Y, 0.0
                    self.alvo_x = None
                    jogo.tremer(5)
            if (self.x < 70 and self.vx < 0) or (self.x > LARGURA - 70 and self.vx > 0):
                self.x = min(max(self.x, 70), LARGURA - 70)
                self.quiques += 1
                jogo.tremer(8)
                if self.quiques >= 4:
                    self.vx = 0.0
                    self.cd_especial = 11.0
                    self.y, self.vy = CHAO_Y, 0.0
                    self.alvo_x = None
                    self.mudar("recuperando")
                else:
                    self.vx = -self.vx
                    self.vy = -850
                    self.alvo_x = self.x + self.vx * (2 * 850 / 2000)
        elif e == "recuperando":
            if self.tempo > 0.6:
                if self.estagio == 1 and self.cd_principal <= 0:
                    self.cd_principal = 1.6
                self.mudar("andando")

    def pular(self, r):
        self.alvo_x = min(max(r.cx, 200), LARGURA - 200)   # nunca cai colado na parede: lá é lugar seguro
        tempo = 0.9
        self.vx = (self.alvo_x - self.x) / tempo
        self.vy = -1800 * tempo / 2
        self.dir = 1 if self.vx >= 0 else -1
        self.pulos += 1


# =====================================================================
# Luta (chamado pelo Jogo enquanto estado == "chefe")
# =====================================================================
def criar():
    return Besouro()


def prensar(jogo):
    """A bola pegou: prensa = morte na hora."""
    r = jogo.ribbat
    if r.invuln > 0 or r.dash_t > 0:
        return
    r.prensado = True
    jogo.coracoes = 0
    jogo.tremer(16)
    jogo.faiscas(r.cx, r.y + 12, (230, 60, 70), 20)
    jogo.game_over()


def atualizar(jogo, dt, ent):
    r, b = jogo.ribbat, jogo.boss
    r.atualizar(dt, ent, jogo)
    b.atualizar(dt, jogo)
    if jogo.estado != "chefe":
        return
    pr = r.rect()
    lingua = r.rect_lingua()
    hb = b.hitbox()
    if hb:
        if lingua and not r.lingua_acertou and lingua.collidelist(hb) >= 0:
            r.lingua_acertou = True
            if b.levar(DANO, jogo):
                SOM.efeito("acerto")
        if r.dash_t > 0 and not r.dash_acertou and pr.collidelist(hb) >= 0:
            r.dash_acertou = True
            if b.levar(DANO, jogo):
                SOM.efeito("acerto")
            r.dash_t = 0
            r.vx = -r.dir * 330
            r.vy = -380
            r.invuln = max(r.invuln, 0.5)
            r.atordoado = 0.2
    if r.dash_t <= 0:
        for rect, letal in b.perigos():
            if pr.colliderect(rect):
                if letal:
                    prensar(jogo)
                else:
                    r.machucar(jogo, b.x)
                break
    for o in b.ondas:
        if pr.colliderect(o.rect()):
            r.machucar(jogo, o.x)
    jogo.efeitos(dt)


# =====================================================================
# Desenho
# =====================================================================
_fundo = None
CAIXA = (440, 320)
ORIGEM = (220, 300)          # onde ficam os pés dele dentro da caixa


def criar_fundo():
    """Dentro da toca do besouro: barro em camadas, raízes, luz entrando por um buraco, bolinhas de esterco."""
    s = pygame.Surface((LARGURA, ALTURA))
    for y in range(ALTURA):
        k = y / ALTURA
        s.fill([int(a + (b - a) * k) for a, b in zip((44, 30, 22), (96, 66, 44))], R(0, y, LARGURA, 1))
    rnd = random.Random(21)
    for i in range(9):                       # camadas de barro
        y = 40 + i * 50 + rnd.randint(-10, 10)
        pts = [(x, y + math.sin(x / 70 + i) * 8) for x in range(0, LARGURA + 20, 20)]
        pygame.draw.lines(s, (70 + i * 3, 48 + i * 2, 32), False, pts, 3)
    luz = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    pygame.draw.polygon(luz, (255, 210, 140, 34), [(150, 0), (260, 0), (520, CHAO_Y), (300, CHAO_Y)])
    s.blit(luz, (0, 0))
    for _ in range(16):                      # raízes
        x = rnd.randint(0, LARGURA)
        comp = rnd.randint(40, 150)
        pts = [(x + math.sin(i * 0.8 + x) * 7, i * comp / 6) for i in range(7)]
        pygame.draw.lines(s, (92, 64, 40), False, pts, rnd.randint(2, 5))
    for x, r in ((60, 22), (100, 16), (900, 26), (860, 15), (930, 12)):   # bolinhas de esterco (eca!)
        pygame.draw.circle(s, (78, 52, 30), (x, CHAO_Y - r), r)
        pygame.draw.circle(s, (110, 76, 46), (x - r // 3, CHAO_Y - r - r // 3), r // 3)
    pygame.draw.rect(s, (86, 60, 40), R(0, CHAO_Y, LARGURA, ALTURA - CHAO_Y))
    pygame.draw.line(s, (150, 118, 86), (0, CHAO_Y + 1), (LARGURA, CHAO_Y + 1), 3)
    for _ in range(40):
        pygame.draw.circle(s, (66, 46, 30), (rnd.randint(0, LARGURA), rnd.randint(CHAO_Y + 8, ALTURA)), rnd.randint(2, 5))
    return s


def _brilhante(p, cx, cy, rx, ry, ang, base, claro, escuro):
    p.pol(_pts_elipse(cx, cy, rx + 2, ry + 2, ang), escuro)
    p.pol(_pts_elipse(cx, cy, rx, ry, ang), base)
    p.pol(_pts_elipse(cx - rx * 0.3, cy - ry * 0.4, rx * 0.45, ry * 0.22, ang - 0.25), claro)
    p.pol(_pts_elipse(cx - rx * 0.38, cy - ry * 0.48, rx * 0.14, ry * 0.07, ang - 0.25), (240, 220, 200))


def _chifre(p, base, meio, ponta, larg, cor):
    pts_e, pts_d = [], []
    for i in range(13):
        k = i / 12
        x = (1 - k) ** 2 * base[0] + 2 * (1 - k) * k * meio[0] + k * k * ponta[0]
        y = (1 - k) ** 2 * base[1] + 2 * (1 - k) * k * meio[1] + k * k * ponta[1]
        dx = 2 * (1 - k) * (meio[0] - base[0]) + 2 * k * (ponta[0] - meio[0])
        dy = 2 * (1 - k) * (meio[1] - base[1]) + 2 * k * (ponta[1] - meio[1])
        n = math.hypot(dx, dy) or 1
        w = larg * (1 - k * 0.85)
        pts_e.append((x - dy / n * w, y + dx / n * w))
        pts_d.append((x + dy / n * w, y - dx / n * w))
    p.pol(pts_e + pts_d[::-1], cor)
    p.linha(pts_e[2:10], (min(255, cor[0] + 60), min(255, cor[1] + 50), min(255, cor[2] + 40)), 1.5)


def _faixa(p, cx, cy, rx, ry, a0, a1, esp, cor, ang=0.0):
    """Faixa grudada na borda de uma elipse (sombra embaixo, borda de luz...)."""
    fora = [p_ for p_ in _arco(cx, cy, rx, ry, a0, a1, ang)]
    dentro = [p_ for p_ in _arco(cx, cy - esp * 0.3, rx - esp, ry - esp, a0, a1, ang)]
    p.pol(fora + dentro[::-1], cor)


def _arco(cx, cy, rx, ry, a0, a1, ang=0.0, n=16):
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        x, y = math.cos(a) * rx, math.sin(a) * ry
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return pts


def _pernas(p, b, lado, tatu=False):
    """Pernas curtas e fortes: coxa, canela com dentinhos e pé com garra em gancho."""
    if tatu:
        cor, claro = ((150, 112, 100), PELE) if not lado else ((120, 90, 80), (170, 130, 120))
        pernas = (((70, -16), (82, -10), (96, 0)), ((-60, -14), (-70, -8), (-82, 0)))
    else:
        cor, claro = (PATA, (90, 50, 26)) if not lado else ((22, 10, 4), (54, 30, 16))
        pernas = (((64, -26), (90, -20), (114, 0)), ((14, -20), (32, -14), (42, 0)), ((-40, -20), (-66, -16), (-100, 0)))
    for i, (raiz, joelho, pe) in enumerate(pernas):
        fase = b.andar * 9 + i * 2.1 + (math.pi if lado else 0)
        dx = math.sin(fase) * 8
        sobe = max(0.0, math.cos(fase)) * 6
        joelho = (joelho[0] + dx * 0.5 - lado * 6, joelho[1] - sobe * 0.5)
        pe = (pe[0] + dx - lado * 6, pe[1] - sobe)
        tornozelo = (pe[0] - (6 if pe[0] > raiz[0] else -6), pe[1] - 5)
        p.osso(raiz, joelho, 7 if not tatu else 8, 6, cor)
        p.osso(joelho, tornozelo, 6, 4, cor)
        lado_fora = 1 if pe[0] > raiz[0] else -1
        if tatu:                                   # garras grandes de cavar
            for k in range(3):
                p.linha([tornozelo, (pe[0] + lado_fora * (6 + k * 3), pe[1] - k), (pe[0] + lado_fora * (11 + k * 3), pe[1] + 1)],
                        (60, 46, 36), 2)
        else:
            for k in (0.3, 0.55, 0.8):             # dentinhos da canela
                sx = joelho[0] + (tornozelo[0] - joelho[0]) * k
                sy = joelho[1] + (tornozelo[1] - joelho[1]) * k
                p.pol([(sx, sy - 3), (sx + lado_fora * 6, sy - 6), (sx + lado_fora * 1, sy + 1)], cor)
            p.linha([tornozelo, pe, (pe[0] + lado_fora * 5, pe[1] - 5)], cor, 2.5)     # pé com gancho
            for k in (0.3, 0.6):                   # pelinhos dourados
                hx = raiz[0] + (joelho[0] - raiz[0]) * k
                hy = raiz[1] + (joelho[1] - raiz[1]) * k
                p.linha([(hx, hy + 4), (hx - 2, hy + 9)], PELO, 1)
        p.circ(joelho[0], joelho[1], 3, claro)


def _desenhar_besouro(p, b, t):
    e = b.estado
    baixa = min(1.0, b.tempo / 0.5) if e == "mirando" else (1.0 if e == "chifrando" else 0.0)
    cima = 1.0 if e == "chifrando" else 0.0
    rachado = b.estagio == 2 or e == "rachando"
    _pernas(p, b, 1)
    # élitros: o domo brilhante (a "armadura de placas")
    ex, ey, rx, ry = GEO_BESOURO["elitro"]
    _brilhante(p, ex, ey, rx, ry, 0.06, CASCA, CASCA_CLARA, CASCA_ESC)
    _faixa(p, ex, ey, rx, ry, 15, 165, 12, (60, 28, 14), 0.06)                   # sombra embaixo
    for k in (1, 2, 3):                                                           # ranhuras de comprido
        p.linha(_arco(ex, ey, rx * (1 - 0.13 * k), ry * (1 - 0.2 * k), 200, 340, 0.06), (70, 32, 16), 1.5)
    for x in (ex - 52, ex - 16, ex + 22):                                         # bordas das placas
        meia = ry * math.sqrt(max(0.0, 1 - ((x - ex) / rx) ** 2))
        p.linha([(x, ey - meia + 3), (x + 6, ey), (x + 3, ey + meia - 6)], CASCA_ESC, 2.5)
        p.linha([(x - 3, ey - meia + 6), (x + 3, ey), (x, ey + meia - 10)], CASCA_CLARA, 1)
    p.pol(_pts_elipse(ex - 6, ey - ry * 0.62, rx * 0.66, ry * 0.11, 0.04), (226, 160, 112))   # reflexo
    # pronoto (escudo do peito) com o chifre que aponta pra frente
    px, py, prx, pry = GEO_BESOURO["pronoto"]
    _chifre(p, (px + 10, py - pry + 8), (px + 58, py - pry - 12),
            (px + 92 + baixa * 6, py - pry + 6 + baixa * 16), 9, CHIFRE)
    _brilhante(p, px, py, prx, pry, 0.15, CASCA, CASCA_CLARA, CASCA_ESC)
    _faixa(p, px, py, prx, pry, 20, 160, 8, (60, 28, 14), 0.15)
    # cabeça pequena e baixa com o CHIFRÃO curvando pra cima (ponta em forquilha)
    hx, hy, hrx, hry = GEO_BESOURO["cabeca"]
    hy += baixa * 8
    _brilhante(p, hx, hy, hrx, hry, 0.4, CASCA, CASCA_CLARA, CASCA_ESC)
    ponta = (hx + 36 + baixa * 44 + cima * 10, hy - 92 + baixa * 66 - cima * 18)
    _chifre(p, (hx + 6, hy - 8), (hx + 46, hy - 30 + baixa * 26 - cima * 10), ponta, 12, CHIFRE)
    p.osso(ponta, (ponta[0] - 10, ponta[1] - 12), 3, 1.5, CHIFRE)                 # forquilha
    p.osso(ponta, (ponta[0] + 10, ponta[1] - 10), 3, 1.5, CHIFRE)
    p.circ(hx + 8, hy - 3, 3.5, PRETO)
    p.circ(hx + 9, hy - 4, 1.2, BRANCO)
    p.linha([(hx + 16, hy + 8), (hx + 24, hy + 13)], PATA, 2)                    # anteninha com clava
    p.circ(hx + 26, hy + 14, 3, PELO)
    if rachado:                                                                   # rachaduras na armadura
        for pts in (((-96, -84), (-82, -70), (-90, -56), (-76, -40)), ((-34, -100), (-28, -82), (-40, -70), (-30, -50)),
                    ((10, -92), (2, -76), (14, -64)), ((40, -82), (48, -66), (40, -52)), ((-64, -30), (-52, -44), (-44, -34))):
            p.linha(list(pts), (236, 210, 180), 2.2)
        p.pol([(-44, -100), (-28, -104), (-36, -90)], CASCA_ESC)
        p.pol([(30, -84), (44, -88), (38, -76)], CASCA_ESC)
    _pernas(p, b, 0)


def _escamas(p, x0, x1, cx, cy, rx, ry, cor, claro):
    """Bolinhas de escama (os escudos do ombro e do quadril do tatu)."""
    for fila in range(4):
        y = cy - ry * (0.78 - fila * 0.22)
        for i in range(12):
            x = x0 + (i + (fila % 2) * 0.5) * (x1 - x0) / 11
            dentro = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 0.82
            if x0 <= x <= x1 and dentro:
                p.pol(_pts_elipse(x, y, 4.2, 3.4), cor)
                p.circ(x - 1, y - 1, 1.2, claro)


def _desenhar_tatu(p, b, t):
    e = b.estado
    cx, cy, rx, ry = GEO_TATU["casco"]
    hx, hy, hrx, hry = GEO_TATU["cabeca"]
    _pernas(p, b, 1, tatu=True)
    # rabo com aneizinhos (levanta e balança na rabada)
    base = (cx - rx + 10, cy + 18)
    if e == "balancando":
        ponta = (cx - rx - 72, -14 + math.sin(t * 22) * 22)
    elif e == "rabada":
        ponta = (cx - rx - 86, cy - 6)
    else:
        ponta = (cx - rx - 70, -6 + math.sin(t * 2) * 3)
    for i in range(7):
        k0, k1 = i / 7, (i + 1) / 7
        a = (base[0] + (ponta[0] - base[0]) * k0, base[1] + (ponta[1] - base[1]) * k0)
        c = (base[0] + (ponta[0] - base[0]) * k1, base[1] + (ponta[1] - base[1]) * k1)
        p.osso(a, c, 11 - i * 1.4, 10 - i * 1.4, TATU_ESC if i % 2 else TATU)
    # barriguinha de pele (sem armadura)
    p.pol(_pts_elipse(cx + 4, cy + ry * 0.62, rx * 0.86, ry * 0.36), PELE)
    # carapaça: escudo do quadril + faixas que dobram + escudo do ombro
    _brilhante(p, cx, cy, rx, ry, 0.0, TATU, TATU_CLARO, TATU_ESC)
    _escamas(p, cx - rx + 6, cx - 34, cx, cy, rx, ry, (150, 124, 100), TATU_CLARO)        # quadril
    _escamas(p, cx + 30, cx + rx - 6, cx, cy, rx, ry, (150, 124, 100), TATU_CLARO)        # ombro
    for k in range(7):                                                                     # 7 faixas
        x = cx - 30 + k * 9
        meia = ry * math.sqrt(max(0.0, 1 - ((x - cx) / rx) ** 2))
        p.linha([(x, cy - meia + 2), (x + 2, cy + meia * 0.7)], TATU_ESC, 3)
        p.linha([(x + 3, cy - meia + 4), (x + 5, cy + meia * 0.66)], TATU_CLARO, 1.2)
    for i in range(14):                                                                    # barrinha de escamas
        x = cx - rx + 10 + i * (2 * rx - 20) / 13
        y = cy + ry * math.sqrt(max(0.0, 1 - ((x - cx) / rx) ** 2)) * 0.82
        p.pol(_pts_elipse(x, y, 6, 4), TATU_ESC)
    p.pol(_pts_elipse(cx - 20, cy - ry * 0.7, rx * 0.5, ry * 0.12, 0.05), (240, 224, 200))   # reflexo
    # cabeça: focinho comprido, escudo da cabeça, orelhona e o CHIFRE de rinoceronte
    p.osso((cx + rx - 24, cy + 4), (hx - 14, hy + 2), 20, 16, PELE)                       # pescoço
    p.pol(_pts_elipse(hx - 22, hy - 26, 7, 15, -0.35), (180, 130, 120))                   # orelha
    p.pol(_pts_elipse(hx - 21, hy - 25, 3.5, 10, -0.35), (236, 180, 170))
    p.pol([(hx - 26, hy - 6), (hx + 6, hy - 18), (hx + 40, hy + 2), (hx + 40, hy + 10), (hx + 2, hy + 14), (hx - 24, hy + 10)],
          PELE)                                                                              # focinho cônico
    p.pol([(hx - 24, hy - 8), (hx + 4, hy - 20), (hx + 26, hy - 8), (hx + 2, hy - 2)], TATU)  # escudo da cabeça
    p.linha([(hx - 18, hy - 9), (hx + 4, hy - 17), (hx + 22, hy - 8)], TATU_CLARO, 1.2)
    _chifre(p, (hx + 10, hy - 14), (hx + 30, hy - 40), (hx + 26 + (8 if e == "rabada" else 0), hy - 78), 11, CHIFRE)
    p.circ(hx + 40, hy + 6, 2.5, (110, 70, 66))                                          # nariz
    p.circ(hx + 2, hy - 6, 3.5, PRETO)
    p.circ(hx + 3, hy - 7, 1.2, BRANCO)
    _pernas(p, b, 0, tatu=True)


def _desenhar_bola(p, b, t):
    """Tatu enrolado igual o Sonic: bola de carapaça com o chifre pra fora, girando."""
    a = math.radians(b.rot)
    pc = (math.cos(a) * 46, -50 + math.sin(a) * 46)                       # base do chifre na borda
    pt = (math.cos(a) * 84, -50 + math.sin(a) * 84)
    meio = (math.cos(a + 0.25) * 66, -50 + math.sin(a + 0.25) * 66)
    _chifre(p, pc, meio, pt, 10, CHIFRE)
    p.pol(_pts_elipse(0, -50, 50, 50), TATU_ESC)
    p.pol(_pts_elipse(0, -50, 47, 47), TATU)
    for k in range(-4, 5):                                                # faixas girando
        ang = a + math.pi / 2 + k * 0.3
        x1, y1 = math.cos(ang) * 46, math.sin(ang) * 46
        p.linha([(x1, -50 + y1), (-x1, -50 - y1)], TATU_ESC, 2.5)
    p.pol(_pts_elipse(math.cos(a + math.pi) * 30, -50 + math.sin(a + math.pi) * 30, 13, 13), (150, 124, 100))  # rabo enrolado
    p.pol(_pts_elipse(-14, -66, 16, 8, -0.5), TATU_CLARO)                 # brilho (não gira)


def desenhar_besouro(tela, b, t):
    w, h = CAIXA
    s = pygame.Surface((w * ESC, h * ESC), pygame.SRCALPHA)
    p = _Pincel(s, ORIGEM[0], ORIGEM[1] - (0 if b.bola else b.sobe))   # corpo lá em cima das patas
    if b.bola:
        _desenhar_bola(p, b, t)
    elif b.estagio == 3:
        _desenhar_tatu(p, b, t)
    else:
        _desenhar_besouro(p, b, t)
    img = pygame.transform.smoothscale(s, CAIXA)
    if b.dir < 0 and not b.bola:
        img = pygame.transform.flip(img, True, False)
    ang = b.ang
    if b.estado == "levantando":
        ang += b.dir * 28 * min(1.0, b.tempo / 0.5)         # empina (patada de mamute)
    elif b.estado == "quicando" and b.alvo_x is not None:
        ang += -b.vy / 60 * (1 if b.vx >= 0 else -1)
    elif b.estado == "morrendo":
        ang = 180 * min(1.0, b.tempo / 0.6)                 # de barriga pra cima
    if b.estado in ("cavando", "enrolando"):
        tremor = math.sin(t * 60) * 3
    else:
        tremor = 0
    if b.flash > 0:
        img = img.copy()
        img.fill((140, 140, 140), special_flags=pygame.BLEND_RGB_ADD)
    gira = pygame.transform.rotate(img, ang) if ang else img
    centro = pygame.math.Vector2(w / 2 - ORIGEM[0], h / 2 - ORIGEM[1]).rotate(-ang)
    pe_y = b.y if b.estado != "morrendo" else b.y - 90 * min(1.0, b.tempo / 0.6)
    tela.blit(gira, gira.get_rect(center=(b.x + centro.x + tremor, pe_y + centro.y)))


def desenhar(jogo, tela):
    global _fundo
    if _fundo is None:
        _fundo = criar_fundo()
    b, t = jogo.boss, jogo.tempo_total
    tx = random.uniform(-jogo.tremor, jogo.tremor) if jogo.tremor > 0 else 0
    ty = random.uniform(-jogo.tremor, jogo.tremor) if jogo.tremor > 0 else 0
    tela.blit(_fundo, (tx, ty))
    if b.alvo_x is not None:                     # sombra: onde ele vai cair
        k = 0.6 + 0.4 * abs(math.sin(t * 10))
        sombra = pygame.Surface((180, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (20, 10, 6, int(150 * k)), sombra.get_rect())
        tela.blit(sombra, (b.alvo_x - 90, CHAO_Y - 14))
    if b.estado == "morrendo":
        for i in range(3):
            a = t * 4 + i * math.tau / 3
            x, y = b.x + math.cos(a) * 50, b.y - 150 + math.sin(a) * 10
            pygame.draw.circle(tela, AMARELO, (int(x), int(y)), 6)
    desenhar_besouro(tela, b, t)
    for o in b.ondas:                            # onda de terra
        for i in range(4):
            x = o.x - o.d * i * 13
            hh = 34 - i * 8 + math.sin(o.t * 30 + i) * 3
            pygame.draw.polygon(tela, (70, 48, 30), [(x - 18, CHAO_Y + 2), (x - 2, CHAO_Y - hh - 2), (x + 18, CHAO_Y + 2)])
            pygame.draw.polygon(tela, (150, 108, 70), [(x - 15, CHAO_Y), (x - 2, CHAO_Y - hh), (x + 15, CHAO_Y)])
        for k in range(3):
            pygame.draw.circle(tela, (180, 140, 100), (int(o.x + k * 7 - 7), int(CHAO_Y - 36 - (o.t * 40 + k * 5) % 14)), 3)
    jogo.desenhar_ribbat(tela, -tx, -ty)
    jogo.desenhar_efeitos(tela, -tx, -ty)
    desenhar_hud(jogo, tela)


def desenhar_hud(jogo, tela):
    """Barra de vida e 3 plaquinhas de armadura = 3 estágios."""
    b = jogo.boss
    if b.estado in ("entrando", "morrendo"):
        return
    larg = 360
    x, y = LARGURA / 2 - larg / 2, 18
    frac = max(0.0, b.vida / VIDA[b.estagio - 1]) if b.estado != "rachando" else min(1.0, b.tempo / 2.0)
    pygame.draw.rect(tela, PRETO, R(x - 3, y - 3, larg + 6, 18), border_radius=6)
    pygame.draw.rect(tela, (50, 30, 20), R(x, y, larg, 12), border_radius=4)
    pygame.draw.rect(tela, (200, 120, 50), R(x, y, larg * frac, 12), border_radius=4)
    pygame.draw.rect(tela, (250, 190, 120), R(x + 2, y + 2, max(0, larg * frac - 4), 3), border_radius=2)
    for i in range(3):                           # plaquinhas: as cheias são os estágios que faltam
        cx = x - 24 - i * 24
        falta = i < 4 - b.estagio - (1 if b.estado == "rachando" else 0)
        cor = CASCA_CLARA if falta else (70, 50, 40)
        pygame.draw.ellipse(tela, cor, R(cx - 9, y - 4, 18, 20))
        pygame.draw.line(tela, CASCA_ESC, (cx, y - 3), (cx, y + 15), 2)
