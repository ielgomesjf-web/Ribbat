"""
Chefão da Fase 4: o GATO PRETO de olhos amarelos (design do Gomes). Duas partes:

PARTE 1 - no QUARTO. A câmera fica atrás do Ribbat (ele aparece DE COSTAS) e o gato fica no fundo.

- Esconda-se na bagunça do quarto (roupas, caixa, travesseiro, brinquedos...).
- Patada (principal): ele levanta a pata (aviso), a sombra aparece no lugar e ele dá um tapa,
  TIRANDO a bagunça dali. Se você estiver ali, leva 1 coração. Só ataca 5 vezes por luta.
  (Se você estiver à vista, ele ataca mais rápido; escondido, ele demora.)
- Investida (especial): quando não dá mais pra se esconder (acabaram as patadas ou a bagunça),
  ele se agacha mexendo o bumbum, mira (a sombra segue e depois TRAVA) e pula.
  Se errar, ele cai NA SALA (e começa a luta de verdade). Se acertar: X_X.

PARTE 2 - na SALA, de lado, igual os outros chefes. Estágio único, 18 de dano (linguada 2, investida 3).
- Patada (principal): levanta a pata (aviso) e dá o tapa na frente.
- Laserzinho (especial): um humano brinca com o laser e o gato sai correndo atrás da bolinha.
  Correndo ele é alto demais pra pular. Mas na hora de virar ele ESCORREGA (fica baixinho):
  é aí que você passa por cima dele! No fim do laser ele fica tonto (hora de bater).
- Se perder na sala, recomeça já na sala.
"""
import math
import random

import pygame

import som as SOM

from chefe import ESC, RECARGA_INVESTIDA, RECARGA_LINGUA, _Pincel, _pts_elipse  # noqa: F401
from config import *  # noqa: F401,F403
from entidades import R

ARENA = {"nome": "O Quarto", "tema": "quarto", "pedacos": [[
    "..S...........................",
    "##############################",
    "##############################",
]]}
CHAO_Y = 15 * TILE
PATADAS = 5
MOSQUITO_Y = (400, 440)        # no quarto os mosquitos voam baixinho (dá pra pegar)
VIDA_SALA = 18
DANO_LINGUA, DANO_INVESTIDA = 2, 3
ARENA_SALA = {"nome": "A Sala", "tema": "quarto", "pedacos": [[
    "..S...........................",
    "##############################",
    "##############################",
]]}
LASER_VEL = 560                # velocidade da bolinha vermelha
GATO_CORRE = 300               # velocidade máxima do gato atrás do laser
GATO_FREIA = 520               # quanto ele consegue frear (baixo = escorrega muito)
LASER_VOLTAS = 4
VIRADA = 0.8                   # tempo patinando no lugar pra virar (a melhor hora de pular por cima!)
ARRANCADA = 150                # até essa velocidade ele ainda corre baixinho (pegando impulso)
GATO_X, GATO_Y = 480, 326      # onde ele fica sentado (base) lá no fundo
TAM = 0.88                     # tamanho dele lá no fundo
JANELA = R(800, 120, 140, 150)

PELO = (26, 24, 30)
PELO_LUZ = (70, 66, 92)
OLHO = (250, 208, 60)
BAGUNCA = (("roupas", 110), ("caixa", 230), ("travesseiro", 370), ("blocos", 560), ("cesto", 710), ("tenis", 850))


class Bagunca:
    def __init__(self, tipo, cx):
        self.tipo, self.cx = tipo, cx
        self.x0, self.x1 = cx - 58, cx + 58
        self.vivo = True

    def esconde(self, r):
        return self.vivo and r.no_chao and self.x0 + 6 <= r.x and r.x + r.W <= self.x1 - 6


class Gato:
    def __init__(self):
        self.estado = "entrando"
        self.tempo = 0.0
        self.t = 0.0
        self.patadas = PATADAS
        self.cd = 2.5
        self.alvo_x = GATO_X
        self.alvo = None             # monte de bagunça que ele mirou
        self.trava = False
        self.olhar = 0.0             # -1..1 pra onde as pupilas olham
        self.pulo = None             # (x inicial, y inicial)
        self.vivo = True
        self.puxando = False
        self.recarga = 0.0
        self.baguncas = [Bagunca(tipo, cx) for tipo, cx in BAGUNCA]
        # parte 2 (sala)
        self.modo = "quarto"
        self.mosquito_y = MOSQUITO_Y
        self.x, self.dir = 700.0, -1
        self.vida = VIDA_SALA
        self.vx = 0.0
        self.flash = 0.0
        self.andar = 0.0
        self.cd_patada = 1.5
        self.cd_laser = 6.0
        self.laser = None            # [x, direção]
        self.viradas = 0
        self.escorregando = False
        self.virando = 0.0
        self.fade = 0.0

    def mudar(self, estado):
        self.estado, self.tempo = estado, 0.0

    def escondido_em(self, r):
        return next((b for b in self.baguncas if b.esconde(r)), None)

    def rect_patada(self):
        if self.estado == "batendo" and self.tempo < 0.15:
            return R(self.alvo_x - 62, CHAO_Y - 90, 124, 90)
        return None

    def atualizar(self, dt, jogo):
        r = jogo.ribbat
        self.t += dt
        self.tempo += dt
        esconderijo = self.escondido_em(r)
        alvo_olhar = 0.0 if esconderijo else max(-1.0, min(1.0, (r.cx - GATO_X) / 420))
        if self.estado in ("mirando", "batendo"):
            alvo_olhar = max(-1.0, min(1.0, (self.alvo_x - GATO_X) / 420))
        self.olhar += (alvo_olhar - self.olhar) * min(1, dt * 6)
        e = self.estado
        if e == "entrando":
            if self.tempo > 1.6:
                self.mudar("olhando")
        elif e == "olhando":
            self.cd -= dt * (1.0 if esconderijo else 2.2)     # à vista = ataca mais rápido
            restam = [b for b in self.baguncas if b.vivo]
            if self.patadas <= 0 or not restam:
                self.mudar("agachando")
            elif self.cd <= 0:
                self.alvo = esconderijo
                self.alvo_x = esconderijo.cx if esconderijo else r.cx
                self.mudar("mirando")
        elif e == "mirando":                                   # pata levantada (aviso)
            if self.tempo > 1.0:
                self.mudar("batendo")
                jogo.tremer(8)
        elif e == "batendo":
            if self.tempo < dt * 1.5:
                self.patadas -= 1
                for b in self.baguncas:                         # tira a bagunça dali
                    if b.vivo and b.x0 - 10 < self.alvo_x < b.x1 + 10:
                        b.vivo = False
                        for _ in range(3):
                            jogo.faiscas(b.cx, CHAO_Y - 30, (200, 180, 150), 10, 280)
            if self.tempo > 0.3:
                self.mudar("recolhendo")
        elif e == "recolhendo":
            if self.tempo > 0.7:
                self.cd = 2.4
                self.mudar("olhando")
        elif e == "agachando":                                 # mexe o bumbum, a sombra segue e depois TRAVA
            if self.tempo < 1.2:
                self.alvo_x = r.cx
                self.trava = False
            else:
                self.trava = True
            if self.tempo > 1.8:
                self.pulo = (GATO_X, GATO_Y)
                self.mudar("pulando")
        elif e == "pulando":
            if self.tempo > 0.5:
                pegou = abs(r.cx - self.alvo_x) < 64 and r.dash_t <= 0 and r.y + r.H > CHAO_Y - 60
                if pegou:
                    jogo.coracoes = 0
                    r.prensado = True
                    jogo.tremer(16)
                    jogo.game_over()
                    self.mudar("pegou")
                else:
                    jogo.tremer(10)
                    self.mudar("errou")
        elif e == "errou":                                     # erra o bote e despenca... lá pra SALA!
            self.fade = max(0.0, (self.tempo - 1.0) / 0.6)
            if self.tempo > 1.6:
                self.ir_pra_sala(jogo)

    # posição do gato pra desenhar (base dos pés e escala)
    def pose(self):
        if self.estado == "pulando":
            u = min(1.0, self.tempo / 0.5)
            x = GATO_X + (self.alvo_x - GATO_X) * u
            y = GATO_Y + (CHAO_Y + 20 - GATO_Y) * u - math.sin(u * math.pi) * 120
            return x, y, TAM + 0.9 * u
        if self.estado == "errou":                             # passa direto e despenca pra baixo da tela
            u = min(1.0, self.tempo / 1.2)
            x = self.alvo_x + (GATO_X - self.alvo_x) * u * 0.3
            y = CHAO_Y + 20 + u * u * 500
            return x, y, 1.9
        return GATO_X, GATO_Y + (14 if self.estado == "agachando" else 0), TAM


    # =================== PARTE 2: A SALA ===================
    def ir_pra_sala(self, jogo):
        from entidades import Fase, Ribbat
        jogo.fase = Fase(ARENA_SALA)
        jogo.ribbat = Ribbat(120, CHAO_Y - Ribbat.H)
        jogo.particulas, jogo.icones = [], []
        jogo.chefe_meio = jogo.fase_atual["id"]          # se perder, recomeça já na sala
        self.modo = "sala"
        self.mosquito_y = (330, 420)
        self.x, self.dir, self.vx = 700.0, -1, 0.0
        self.vida = VIDA_SALA
        self.laser = None
        self.fade = 1.0
        self.mudar("chegando")

    def mundo(self, dx, dy):
        return self.x + self.dir * dx, CHAO_Y + dy

    def caixa(self, centro, w, h):
        cx, cy = self.mundo(*centro)
        return R(cx - w / 2, cy - h / 2, w, h)

    @property
    def vulneravel(self):
        return self.modo == "sala" and self.estado not in ("chegando", "morrendo")

    def partes(self):
        """Corpo, cabeça e pernas (do jeito que estão desenhados)."""
        if self.escorregando or self.estado in ("chegando", "tonto"):
            return [self.caixa((0, -34), 170, 50), self.caixa((88, -54), 60, 48)]
        if self.estado == "correndo":
            return [self.caixa((0, -74), 176, 62), self.caixa((96, -104), 62, 56), self.caixa((0, -20), 190, 40)]
        return [self.caixa((0, -62), 150, 70), self.caixa((88, -100), 66, 60), self.caixa((0, -14), 132, 28)]

    def hitbox(self):
        return self.partes() if self.vulneravel else None

    def perigos(self):
        if not self.vulneravel or self.estado in ("tonto", "chegando"):
            return []
        if self.escorregando:                                 # escorregando: só o corpo baixinho machuca
            return [self.caixa((0, -22), 118, 40)]
        lista = [r.inflate(-14, -10) for r in self.partes()]
        if self.estado == "patada" and self.tempo < 0.2:
            a, b = self.mundo(96, -84), self.mundo(214, 0)
            lista.append(R(min(a[0], b[0]), a[1], abs(b[0] - a[0]), 84))
        return lista

    def levar(self, dano, jogo):
        if not self.vulneravel:
            return False
        self.vida -= dano
        self.flash = 0.12
        hb = self.partes()[1]
        jogo.faiscas(hb.centerx, hb.centery, (200, 196, 210), 12, 240)
        jogo.tremer(4)
        if self.vida <= 0:
            self.laser = None
            self.escorregando = False
            self.mudar("morrendo")
        return True

    def atualizar_sala(self, dt, jogo):
        r = jogo.ribbat
        self.flash = max(0.0, self.flash - dt)
        self.fade = max(0.0, self.fade - dt * 2)
        e = self.estado
        dx = r.cx - self.x
        if e == "chegando":                                  # caiu de mau jeito: tontinho
            if self.tempo > 1.8:
                self.mudar("andando")
        elif e == "andando":
            self.dir = 1 if dx > 0 else -1
            encurralado = (r.cx < 200 and self.x > r.cx) or (r.cx > LARGURA - 200 and self.x < r.cx)
            if encurralado:                                  # nunca te prende na parede: dá espaço
                self.x = max(110, min(LARGURA - 110, self.x - self.dir * 150 * dt))
                self.andar += dt
                self.cd_patada = max(self.cd_patada, 0.6)
            elif abs(dx) > 190:
                self.x = max(110, min(LARGURA - 110, self.x + self.dir * 120 * dt))
                self.andar += dt
            self.cd_patada -= dt
            self.cd_laser -= dt
            if self.cd_laser <= 0:
                self.mudar("laser_inicio")
                ida = 1 if self.x < LARGURA / 2 else -1        # a bolinha aparece e sai pro lado mais longe
                self.laser = [self.x + ida * 60, ida]
            elif self.cd_patada <= 0 and abs(dx) < 240:
                self.mudar("mirando")
        elif e == "mirando":                                 # pata levantada, bumbum mexendo (aviso)
            if self.tempo > 0.6:
                self.mudar("patada")
        elif e == "patada":
            self.x = max(110, min(LARGURA - 110, self.x + self.dir * 200 * dt))
            if self.tempo > 0.25:
                self.mudar("recuperando")
        elif e == "recuperando":
            if self.tempo > 0.7:
                self.cd_patada = 1.6
                self.mudar("andando")
        elif e == "laser_inicio":                            # o humano aponta o laser; o gato arregala os olhos
            self.dir = self.laser[1]
            if self.tempo > 1.0:
                self.viradas = 0
                self.vx = 0.0
                self.mudar("correndo")
        elif e == "correndo":
            lx, ld = self.laser
            lx += ld * LASER_VEL * dt
            if (lx > LARGURA - 60 and ld > 0) or (lx < 60 and ld < 0):
                ld = -ld                                       # a bolinha vira na parede
                self.viradas += 1
            self.laser = [lx, ld] if self.viradas < LASER_VOLTAS else self.laser
            quer = 1 if lx > self.x else -1
            if self.virando > 0:                              # patinando no lugar pra virar (baixinho!)
                self.virando -= dt
                self.escorregando = True
                self.vx = 0.0
            elif self.vx * quer < 0:                          # vai pro lado errado: ESCORREGA freando
                self.escorregando = True
                novo = self.vx + quer * GATO_FREIA * dt
                if novo * self.vx <= 0:
                    novo = 0.0
                    self.virando = VIRADA
                self.vx = novo
                if int(self.tempo * 20) % 2 == 0:
                    jogo.poeira(self.x - self.dir * 70, CHAO_Y, 2)
            else:
                self.dir = quer
                self.vx = max(-GATO_CORRE, min(GATO_CORRE, self.vx + quer * 1400 * dt))
                self.escorregando = abs(self.vx) < ARRANCADA     # ainda pegando impulso: baixinho
            self.x += self.vx * dt
            if self.x < 100 or self.x > LARGURA - 100:
                self.x = min(max(self.x, 100), LARGURA - 100)
                self.vx = 0.0
            self.andar += dt * 3
            if self.viradas >= LASER_VOLTAS and not self.escorregando and abs(self.x - lx) < 140:
                self.laser = None
                self.escorregando = False
                self.mudar("tonto")
        elif e == "tonto":                                   # cansou de correr: hora de bater!
            self.vx = 0.0
            if self.tempo > 2.0:
                self.cd_laser = 10.0
                self.cd_patada = 1.2
                self.mudar("andando")
        elif e == "morrendo":
            if self.tempo > 3.0:
                self.vivo = False
                jogo.chefe_meio = None
                jogo.venceu_chefe()


# =====================================================================
# Luta
# =====================================================================
def criar():
    return Gato()


def atualizar(jogo, dt, ent):
    r, g = jogo.ribbat, jogo.boss
    r.atualizar(dt, ent, jogo)
    if g.modo == "quarto":
        g.atualizar(dt, jogo)
        if jogo.estado != "chefe":
            return
        pata = g.rect_patada()
        if pata and jogo.ribbat.rect().colliderect(pata):
            jogo.ribbat.machucar(jogo, g.alvo_x)
        jogo.efeitos(dt)
        return
    g.t += dt
    g.tempo += dt
    g.atualizar_sala(dt, jogo)
    if jogo.estado != "chefe":
        return
    pr, lingua = r.rect(), r.rect_lingua()
    hb = g.hitbox()
    if hb:
        if lingua and not r.lingua_acertou and lingua.collidelist(hb) >= 0:
            r.lingua_acertou = True
            if g.levar(DANO_LINGUA, jogo):
                SOM.efeito("acerto")
        if r.dash_t > 0 and not r.dash_acertou and pr.collidelist(hb) >= 0:
            r.dash_acertou = True
            if g.levar(DANO_INVESTIDA, jogo):
                SOM.efeito("acerto")
            r.dash_t = 0
            r.vx = -r.dir * 330
            r.vy = -380
            r.invuln = max(r.invuln, 0.5)
            r.atordoado = 0.2
    if r.dash_t <= 0 and any(pr.colliderect(p) for p in g.perigos()):
        r.machucar(jogo, g.x)
    jogo.efeitos(dt)


# =====================================================================
# Desenho
# =====================================================================
_fundo = None


def criar_fundo():
    """O quarto: parede listrada, janela, cama, estante com brinquedos, chão de tábua em perspectiva."""
    s = pygame.Surface((LARGURA, ALTURA))
    s.fill((214, 196, 226))
    for x in range(0, LARGURA, 40):                              # papel de parede listrado
        pygame.draw.rect(s, (204, 184, 218), R(x, 0, 20, 330))
    pygame.draw.rect(s, (170, 140, 110), R(0, 318, LARGURA, 14))  # rodapé
    for i in range(14):                                          # chão de tábua em perspectiva
        x_fundo = i * LARGURA / 13
        x_frente = LARGURA / 2 + (x_fundo - LARGURA / 2) * 2.2
        pygame.draw.line(s, (150, 104, 66), (x_fundo, 332), (x_frente, ALTURA), 2)
    chao = pygame.Surface((LARGURA, ALTURA - 332), pygame.SRCALPHA)
    for y in range(ALTURA - 332):
        k = y / (ALTURA - 332)
        pygame.draw.line(chao, (176 - int(30 * k), 124 - int(20 * k), 80 - int(14 * k), 120), (0, y), (LARGURA, y))
    s.blit(chao, (0, 332))
    for y in (360, 400, 450, 510):
        pygame.draw.line(s, (140, 96, 60), (0, y), (LARGURA, y), 1)
    # tapete redondo, pôster e abajurzinho: quarto de criança
    pygame.draw.ellipse(s, (120, 170, 220), R(300, 360, 360, 70))
    pygame.draw.ellipse(s, (160, 200, 240), R(330, 370, 300, 50))
    pygame.draw.rect(s, (250, 240, 200), R(300, 60, 90, 120))
    pygame.draw.rect(s, (200, 160, 110), R(300, 60, 90, 120), 4)
    pygame.draw.circle(s, (250, 200, 60), (345, 100), 22)                            # pôster de sol
    pygame.draw.polygon(s, (110, 180, 90), [(310, 170), (345, 125), (380, 170)])
    # janela
    pygame.draw.rect(s, (150, 210, 240), JANELA)
    pygame.draw.rect(s, (110, 200, 110), R(JANELA.x, JANELA.bottom - 40, JANELA.width, 40))
    pygame.draw.rect(s, BRANCO, JANELA, 10)
    pygame.draw.line(s, BRANCO, (JANELA.centerx, JANELA.top), (JANELA.centerx, JANELA.bottom), 6)
    pygame.draw.rect(s, (240, 120, 120), R(JANELA.x - 26, JANELA.y - 16, 30, JANELA.height + 30))   # cortina
    # cama
    pygame.draw.rect(s, (120, 80, 50), R(20, 220, 240, 110), border_radius=10)
    pygame.draw.rect(s, (90, 140, 210), R(30, 200, 230, 60), border_radius=14)
    pygame.draw.ellipse(s, BRANCO, R(40, 190, 80, 36))
    # estante com brinquedos
    pygame.draw.rect(s, (140, 96, 60), R(600, 120, 150, 200))
    for y in (170, 230, 290):
        pygame.draw.line(s, (100, 66, 40), (600, y), (750, y), 5)
    for i, cor in enumerate(((230, 80, 70), (80, 170, 230), (250, 210, 70), (120, 200, 110))):
        pygame.draw.rect(s, cor, R(612 + i * 34, 140, 26, 30), border_radius=4)
    pygame.draw.circle(s, (230, 120, 60), (640, 210), 16)
    pygame.draw.rect(s, (60, 60, 70), R(690, 250, 46, 40), border_radius=6)
    return s


def desenhar_bagunca(tela, b, t):
    x, base = b.cx, CHAO_Y + 4
    if b.tipo == "roupas":
        for i, cor in enumerate(((90, 140, 210), (230, 90, 90), (250, 220, 120), (120, 190, 120))):
            pygame.draw.ellipse(tela, cor, R(x - 58 + i * 8, base - 70 + i * 12, 116 - i * 16, 70 - i * 10))
        pygame.draw.polygon(tela, (60, 60, 160), [(x + 20, base - 70), (x + 54, base - 90), (x + 50, base - 60)])  # manga
    elif b.tipo == "caixa":
        pygame.draw.rect(tela, (200, 150, 90), R(x - 56, base - 86, 112, 86))
        pygame.draw.polygon(tela, (220, 170, 110), [(x - 56, base - 86), (x - 40, base - 104), (x + 2, base - 96), (x - 10, base - 86)])
        pygame.draw.polygon(tela, (180, 130, 76), [(x + 56, base - 86), (x + 40, base - 106), (x - 2, base - 96), (x + 10, base - 86)])
        pygame.draw.rect(tela, (150, 106, 60), R(x - 56, base - 86, 112, 86), 3)
        pygame.draw.line(tela, (230, 210, 170), (x - 56, base - 50), (x + 56, base - 50), 6)
    elif b.tipo == "travesseiro":
        pygame.draw.rect(tela, (250, 250, 246), R(x - 60, base - 70, 120, 70), border_radius=26)
        pygame.draw.rect(tela, (210, 210, 220), R(x - 60, base - 70, 120, 70), 3, border_radius=26)
        for i in range(4):
            pygame.draw.circle(tela, (180, 200, 240), (int(x - 36 + i * 24), base - 36), 6)
    elif b.tipo == "blocos":
        for i, (dx, dy, cor) in enumerate(((-50, 0, (230, 80, 70)), (-6, 0, (80, 170, 230)), (38, 0, (250, 210, 70)),
                                           (-28, -40, (120, 200, 110)), (16, -40, (200, 120, 220)), (-6, -80, (250, 150, 60)))):
            pygame.draw.rect(tela, cor, R(x + dx - 6, base - 40 + dy, 40, 40), border_radius=4)
            pygame.draw.rect(tela, PRETO, R(x + dx - 6, base - 40 + dy, 40, 40), 2, border_radius=4)
            pygame.draw.circle(tela, BRANCO, (int(x + dx + 14), int(base - 20 + dy)), 6, 2)
    elif b.tipo == "cesto":
        pygame.draw.polygon(tela, (190, 150, 90), [(x - 58, base - 90), (x + 58, base - 90), (x + 48, base), (x - 48, base)])
        for i in range(6):
            pygame.draw.line(tela, (150, 110, 60), (x - 54 + i * 4, base - 84 + i * 15), (x + 54 - i * 4, base - 84 + i * 15), 3)
        pygame.draw.ellipse(tela, (240, 120, 160), R(x - 40, base - 104, 60, 26))                 # meia saindo
    else:                                                                                           # tênis
        pygame.draw.polygon(tela, (240, 240, 244), [(x - 60, base), (x - 60, base - 46), (x - 10, base - 66), (x + 30, base - 40),
                                                    (x + 60, base - 30), (x + 60, base)])
        pygame.draw.polygon(tela, (230, 70, 60), [(x - 60, base - 12), (x + 60, base - 12), (x + 60, base), (x - 60, base)])
        for i in range(4):
            pygame.draw.line(tela, (60, 60, 80), (x - 30 + i * 9, base - 56 + i * 4), (x - 18 + i * 9, base - 50 + i * 4), 3)


def _gato(p, g, t):
    """Gato preto SENTADO de frente: bochechas fofas, orelhas peludas, peito, patinhas retas e o rabo enrolado."""
    e = g.estado
    agachado = e in ("agachando", "pulando")
    bumbum = math.sin(t * 18) * 6 if e == "agachando" else 0
    baixa = 50 if agachado else 0
    mexe = math.sin(t * (6 if agachado else 1.8)) * 12
    # rabo enrolando do lado
    rabo = [(60, -24), (104, -30), (122, -70 - mexe), (110, -120 - mexe * 0.5)] if not agachado else \
        [(50, -40), (90, -90), (100 + mexe, -150), (90 + mexe, -190)]
    for a, b in zip(rabo, rabo[1:]):
        p.osso(a, b, 11, 10, PELO)
    # quadris (as coxas de trás aparecem dos lados) e corpo
    for s in (-1, 1):
        p.pol(_pts_elipse(s * 56 + bumbum * 0.3, -46 + baixa * 0.3, 40, 46 - baixa * 0.3), PELO)
    p.pol(_pts_elipse(bumbum * 0.2, -104 + baixa, 66, 82 - baixa * 0.4), PELO)
    p.pol(_pts_elipse(-26, -124 + baixa, 20, 46 - baixa * 0.3, -0.2), PELO_LUZ)        # brilho do pelo
    p.pol(_pts_elipse(0, -120 + baixa, 30, 50 - baixa * 0.3), (40, 38, 48))             # peito
    # patas da frente retinhas (a direita sai quando ele vai bater)
    for s in (-1, 1):
        if s == 1 and e in ("mirando", "batendo"):
            continue
        p.osso((s * 22, -120 + baixa), (s * 24, -16), 14, 13, PELO)
        p.pol(_pts_elipse(s * 25, -12, 18, 12), PELO)
        for k in (-1, 0, 1):
            p.linha([(s * 25 + k * 7, -4), (s * 25 + k * 7, -14)], PELO_LUZ, 1.5)
    # cabeça larga com bochechas fofas
    hy = -214 + baixa
    p.pol(_pts_elipse(0, hy, 72, 58), PELO)
    for s in (-1, 1):
        p.pol([(s * 58, hy + 6), (s * 84, hy + 22), (s * 62, hy + 30), (s * 76, hy + 40), (s * 46, hy + 44)], PELO)   # bochecha
        p.pol([(s * 22, hy - 44), (s * 50, hy - 112), (s * 72, hy - 30)], PELO)                                    # orelha
        p.pol([(s * 32, hy - 48), (s * 50, hy - 94), (s * 62, hy - 40)], (196, 116, 146))
        for k in range(3):                                                                                       # pelinhos
            p.linha([(s * (40 + k * 6), hy - 46), (s * (46 + k * 4), hy - 66 - k * 6)], (220, 220, 230), 1)
    p.pol(_pts_elipse(-30, hy - 34, 24, 9, -0.3), PELO_LUZ)
    # olhos amendoados amarelos (pupila de risquinho; redondona quando vai pular)
    for s in (-1, 1):
        ox, oy = s * 30, hy - 2
        p.pol(_pts_elipse(ox, oy, 21, 15, s * 0.18), (60, 50, 20))
        p.pol(_pts_elipse(ox, oy, 19, 13, s * 0.18), OLHO)
        px = ox + g.olhar * 8
        p.pol(_pts_elipse(px, oy, 11 if agachado else 3.2, 12 if agachado else 12.5), PRETO)
        p.circ(px - 5, oy - 5, 3, BRANCO)
    p.pol([(-8, hy + 20), (8, hy + 20), (0, hy + 29)], (226, 136, 166))                 # nariz
    p.linha([(0, hy + 29), (0, hy + 34)], PELO_LUZ, 2)
    p.linha([(0, hy + 34), (-10, hy + 40), (-18, hy + 36)], PELO_LUZ, 2)
    p.linha([(0, hy + 34), (10, hy + 40), (18, hy + 36)], PELO_LUZ, 2)
    for s in (-1, 1):                                                                       # bigodes
        for k in (-1, 0, 1):
            p.linha([(s * 24, hy + 26 + k * 6), (s * 100, hy + 16 + k * 16)], (226, 226, 236), 1.4)


def _pata_grande(tela, x, y, k, t):
    """A patona vindo pra frente (com as almofadinhas cor-de-rosa)."""
    pygame.draw.ellipse(tela, PELO, R(x - 56 * k, y - 40 * k, 112 * k, 80 * k))
    pygame.draw.ellipse(tela, (230, 140, 170), R(x - 22 * k, y - 4 * k, 44 * k, 30 * k))
    for i, dx in enumerate((-36, -12, 12, 36)):
        pygame.draw.ellipse(tela, (230, 140, 170), R(x + dx * k - 10 * k, y - 32 * k + abs(dx) * 0.3 * k, 20 * k, 18 * k))


def desenhar_gato(tela, g, t):
    x, y, k = g.pose()
    w, h = 360, 380
    s = pygame.Surface((w * ESC, h * ESC), pygame.SRCALPHA)
    _gato(_Pincel(s, w / 2, h - 10), g, t)
    img = pygame.transform.smoothscale(s, (int(w * k), int(h * k)))
    if g.estado == "errou":
        img = pygame.transform.rotate(img, -g.tempo * 400)
    tela.blit(img, img.get_rect(midbottom=(x, y + 10 * k)) if g.estado != "errou" else img.get_rect(center=(x, y - 100)))


def desenhar_sapo_costas(tela, r, t, orelhas):
    """O Ribbat visto DE COSTAS: as bolinhas dos olhos em cima, o nó do lenço na nuca e as coxas dos lados."""
    import desenho as D
    cx, base = r.cx, r.y + r.H
    no_ar = not r.no_chao
    verde, esc, claro = (112, 186, 80), (40, 112, 50), (176, 218, 116)
    if orelhas:
        for s in (-1, 1):
            pygame.draw.ellipse(tela, (60, 50, 50), R(cx + s * 9 - 6, base - 66, 13, 34))
            pygame.draw.ellipse(tela, (240, 236, 232), R(cx + s * 9 - 5, base - 65, 11, 32))
            pygame.draw.ellipse(tela, (246, 170, 186), R(cx + s * 9 - 2, base - 60, 5, 22))
    for s in (-1, 1):                                                      # coxas e pés
        if no_ar:
            pygame.draw.ellipse(tela, esc, R(cx + s * 14 - 7, base - 10, 14, 22))
        else:
            pygame.draw.ellipse(tela, esc, R(cx + s * 16 - 10, base - 18, 20, 18))
            pygame.draw.ellipse(tela, esc, R(cx + s * 24 - 8, base - 6, 18, 7))
    pygame.draw.ellipse(tela, esc, R(cx - 20, base - 34, 40, 34))
    pygame.draw.ellipse(tela, verde, R(cx - 18, base - 33, 36, 31))
    for dx, dy in ((-8, -22), (6, -16), (-2, -10)):                         # manchinhas
        pygame.draw.circle(tela, (78, 146, 60), (int(cx + dx), int(base + dy)), 3)
    for s in (-1, 1):                                                      # dobras das costas
        pygame.draw.line(tela, claro, (cx + s * 7, base - 30), (cx + s * 9, base - 8), 2)
    for s in (-1, 1):                                                      # bolinhas dos olhos
        pygame.draw.circle(tela, esc, (int(cx + s * 9), int(base - 34)), 8)
        pygame.draw.circle(tela, verde, (int(cx + s * 9), int(base - 34)), 7)
        pygame.draw.circle(tela, BRANCO, (int(cx + s * 14), int(base - 35)), 2)
    pygame.draw.line(tela, LENCO, (cx - 15, base - 26), (cx + 15, base - 26), 4)       # lenço com o nó na nuca
    onda = math.sin(t * 8) * 3
    pygame.draw.polygon(tela, LENCO, [(cx, base - 26), (cx - 7 + onda, base - 14), (cx - 1, base - 16)])
    pygame.draw.polygon(tela, LENCO, [(cx, base - 26), (cx + 7 + onda, base - 13), (cx + 1, base - 16)])
    pygame.draw.circle(tela, (190, 44, 46), (int(cx), int(base - 26)), 4)
    ext = r.lingua_ext()
    if ext > 2:                                                            # língua (pra pegar mosquito)
        by = base - 22
        pygame.draw.line(tela, (190, 60, 90), (cx + r.dir * 16, by), (cx + r.dir * (16 + ext), by), 7)
        pygame.draw.line(tela, (240, 110, 140), (cx + r.dir * 16, by), (cx + r.dir * (16 + ext), by), 4)
        pygame.draw.circle(tela, (240, 110, 140), (int(cx + r.dir * (16 + ext)), int(by)), 6)


# =================== desenho da SALA ===================
_fundo_sala = None


def criar_fundo_sala():
    """A sala: sofá, TV, abajur, quadro, planta, tapete e chão de madeira."""
    s = pygame.Surface((LARGURA, ALTURA))
    s.fill((236, 226, 200))
    for x in range(0, LARGURA, 60):
        pygame.draw.line(s, (226, 214, 186), (x, 0), (x, CHAO_Y), 2)
    pygame.draw.rect(s, (160, 120, 80), R(0, CHAO_Y - 14, LARGURA, 14))                 # rodapé
    pygame.draw.rect(s, (176, 124, 78), R(0, CHAO_Y, LARGURA, ALTURA - CHAO_Y))           # chão de madeira
    for x in range(0, LARGURA, 90):
        pygame.draw.line(s, (150, 104, 64), (x, CHAO_Y), (x, ALTURA), 2)
    pygame.draw.rect(s, (130, 160, 210), R(380, 70, 200, 150))                           # janela
    pygame.draw.rect(s, BRANCO, R(380, 70, 200, 150), 8)
    pygame.draw.line(s, BRANCO, (480, 70), (480, 220), 5)
    pygame.draw.rect(s, (110, 190, 90), R(388, 180, 184, 32))
    pygame.draw.rect(s, (90, 140, 200), R(120, 270, 260, 120), border_radius=24)          # sofá
    pygame.draw.rect(s, (70, 120, 180), R(100, 300, 50, 100), border_radius=18)
    pygame.draw.rect(s, (70, 120, 180), R(350, 300, 50, 100), border_radius=18)
    pygame.draw.rect(s, (110, 170, 220), R(150, 330, 200, 50), border_radius=14)
    for x in (190, 290):
        pygame.draw.rect(s, (240, 200, 90), R(x - 26, 290, 52, 44), border_radius=10)   # almofadas
    pygame.draw.rect(s, (70, 50, 36), R(640, 330, 230, 80))                              # rack + TV
    pygame.draw.rect(s, (30, 30, 36), R(660, 200, 190, 120), border_radius=6)
    pygame.draw.rect(s, (70, 90, 120), R(670, 210, 170, 100))
    pygame.draw.line(s, (130, 160, 200), (690, 220), (740, 290), 3)
    pygame.draw.rect(s, (220, 200, 160), R(40, 120, 70, 90))                              # quadro
    pygame.draw.rect(s, (120, 80, 50), R(40, 120, 70, 90), 5)
    pygame.draw.circle(s, (110, 180, 90), (75, 170), 18)
    pygame.draw.line(s, (90, 70, 50), (910, CHAO_Y), (910, 200), 4)                       # abajur
    pygame.draw.polygon(s, (250, 220, 150), [(880, 200), (940, 200), (925, 160), (895, 160)])
    pygame.draw.rect(s, (180, 90, 60), R(20, 380, 50, 60), border_radius=6)              # planta no vaso
    for i in range(5):
        a = -math.pi / 2 + (i - 2) * 0.4
        pygame.draw.ellipse(s, (70, 160, 70), R(45 + math.cos(a) * 30 - 12, 380 + math.sin(a) * 40 - 8, 24, 16))
    pygame.draw.ellipse(s, (200, 90, 80), R(220, CHAO_Y - 8, 520, 30))                    # tapete
    pygame.draw.ellipse(s, (230, 140, 110), R(250, CHAO_Y - 4, 460, 20))
    return s


def _gato_lado(p, g, t):
    """Gato preto DE LADO (virado pra direita): anda, galopa, escorrega, dá patada, fica tonto."""
    e = g.estado
    correndo = e == "correndo" and not g.escorregando
    deitado = e in ("chegando", "morrendo")
    baixo = g.escorregando or e == "tonto"
    fase = g.andar * (14 if correndo else 7)
    corpo_y = -36 if baixo else -40 if deitado else (-74 if correndo else -62)
    if correndo:
        corpo_y += math.sin(fase * 2) * 6
    # rabo
    if correndo:
        rabo = [(-70, corpo_y - 6), (-120, corpo_y - 14), (-160, corpo_y - 10)]
    elif g.escorregando:
        rabo = [(-70, corpo_y - 10), (-96, corpo_y - 50), (-90, corpo_y - 90)]
    else:
        m = math.sin(t * 2) * 10
        rabo = [(-70, corpo_y - 6), (-104, corpo_y - 30), (-112 + m, corpo_y - 80)]
    for a, b in zip(rabo, rabo[1:]):
        p.osso(a, b, 10, 8, PELO)

    def perna(raiz, joelho, pe, cor):
        p.osso(raiz, joelho, 12, 9, cor)
        p.osso(joelho, pe, 9, 7, cor)
        p.pol(_pts_elipse(pe[0] + 4, pe[1] - 4, 11, 7), cor)

    longe, perto = (16, 14, 20), PELO
    for lado, cor in ((1, longe), (0, perto)):                          # 4 pernas (as de lá mais escuras)
        d = 1 if lado else -1
        for i, rx in enumerate((48, -48)):
            raiz = (rx - lado * 8, corpo_y + 18)
            if deitado:
                joelho, pe = (rx + 20, -24), (rx + 44, -10)
            elif g.escorregando:                                          # escorregando: pernas abertas!
                pe = (rx + (70 if i == 0 else -70) - lado * 10, -4)
                joelho = ((raiz[0] + pe[0]) / 2, -22)
            elif correndo:
                ang = math.sin(fase + i * math.pi + lado * 0.6)
                pe = (rx + ang * 46, -4 - max(0.0, ang) * 20)
                joelho = ((raiz[0] + pe[0]) / 2 + 8, corpo_y + 46)
            elif e in ("mirando", "patada") and i == 0 and lado == 0:      # a pata da patada
                cima = e == "mirando"
                pe = (rx + (40 if cima else 110), -96 if cima else -10)
                joelho = (rx + (30 if cima else 70), -70 if cima else -30)
            else:
                ang = math.sin(fase + i * math.pi + lado * math.pi) * (1 if e == "andando" else 0)
                pe = (rx + ang * 18, -2 - max(0.0, ang) * 8)
                joelho = (rx + ang * 6 + 4, -34)
            perna(raiz, joelho, pe, cor)
    # corpo, peito e brilho do pelo
    p.pol(_pts_elipse(0, corpo_y, 80 if correndo else 74, 30 if correndo else 34, 0.04), PELO)
    p.pol(_pts_elipse(-6, corpo_y - 20, 56, 9, 0.04), PELO_LUZ)
    p.pol(_pts_elipse(50, corpo_y - 8, 30, 30), PELO)
    # cabeça
    hx, hy = 92, corpo_y - (30 if not baixo else 18)
    if e == "mirando":
        hy -= 6
    p.pol(_pts_elipse(hx, hy, 32, 28), PELO)
    p.pol(_pts_elipse(hx + 26, hy + 8, 14, 11), PELO)                    # focinho
    for k, (ex, cor) in enumerate(((0, (16, 14, 20)), (14, PELO))):     # orelhas
        p.pol([(hx - 16 + ex, hy - 18), (hx - 10 + ex, hy - 52), (hx + 6 + ex, hy - 22)], cor)
    p.pol([(hx - 1, hy - 20), (hx + 3, hy - 42), (hx + 13, hy - 22)], (196, 116, 146))
    if e in ("tonto", "chegando", "morrendo"):                           # olho de X / espiral
        p.linha([(hx + 8, hy - 10), (hx + 22, hy + 2)], OLHO, 3)
        p.linha([(hx + 22, hy - 10), (hx + 8, hy + 2)], OLHO, 3)
    else:
        p.pol(_pts_elipse(hx + 14, hy - 4, 10, 8, 0.2), OLHO)
        largo = e in ("laser_inicio", "correndo")
        p.pol(_pts_elipse(hx + 17, hy - 4, 6 if largo else 2.2, 7), PRETO)
        p.circ(hx + 13, hy - 7, 2, BRANCO)
    p.pol(_pts_elipse(hx + 38, hy + 6, 4, 3), (226, 136, 166))           # nariz
    for k in (-1, 0, 1):                                                 # bigodes
        p.linha([(hx + 30, hy + 10 + k * 3), (hx + 70, hy + 4 + k * 9)], (226, 226, 236), 1.2)
    if e in ("tonto", "chegando"):
        for i in range(3):
            a = t * 4 + i * math.tau / 3
            x, y = hx + math.cos(a) * 30, hy - 50 + math.sin(a) * 8
            p.pol([(x + math.cos(k * math.pi / 5 - math.pi / 2) * (8 if k % 2 == 0 else 3.5),
                    y + math.sin(k * math.pi / 5 - math.pi / 2) * (8 if k % 2 == 0 else 3.5)) for k in range(10)], AMARELO)


def desenhar_sala(jogo, tela):
    global _fundo_sala
    if _fundo_sala is None:
        _fundo_sala = criar_fundo_sala()
    g, t = jogo.boss, jogo.tempo_total
    tx = random.uniform(-jogo.tremor, jogo.tremor) if jogo.tremor > 0 else 0
    tela.blit(_fundo_sala, (tx, 0))
    if g.laser:                                                         # o humano com o laserzinho
        lx = g.laser[0] + tx
        mao = (60, 40)
        pygame.draw.line(tela, (255, 60, 60), mao, (lx, CHAO_Y - 2), 1)
        pygame.draw.polygon(tela, (220, 80, 70), [(-10, 0), (40, 0), (70, 34), (30, 60)])          # manga
        pygame.draw.ellipse(tela, (232, 182, 146), R(36, 20, 50, 40))                               # mão
        pygame.draw.rect(tela, (60, 60, 70), R(54, 30, 34, 10), border_radius=4)                    # caneta laser
        brilho = pygame.Surface((40, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(brilho, (255, 40, 40, 90), brilho.get_rect())
        tela.blit(brilho, (lx - 20, CHAO_Y - 12))
        pygame.draw.circle(tela, (255, 40, 40), (int(lx), int(CHAO_Y - 2)), 5)
        pygame.draw.circle(tela, (255, 200, 200), (int(lx - 1), int(CHAO_Y - 3)), 2)
    w, h = 380, 260
    sf = pygame.Surface((w * ESC, h * ESC), pygame.SRCALPHA)
    _gato_lado(_Pincel(sf, w / 2, h - 10), g, t)
    img = pygame.transform.smoothscale(sf, (w, h))
    if g.dir < 0:
        img = pygame.transform.flip(img, True, False)
    if g.estado == "morrendo":
        img = pygame.transform.rotate(img, -g.dir * 10)
    if g.flash > 0:
        img = img.copy()
        img.fill((140, 140, 140), special_flags=pygame.BLEND_RGB_ADD)
    treme = math.sin(t * 40) * 3 if g.estado in ("mirando", "laser_inicio") else 0
    tela.blit(img, img.get_rect(midbottom=(g.x + tx + treme, CHAO_Y + 10)))
    if g.escorregando:                                                  # risquinhos da derrapada
        for i in range(3):
            pygame.draw.line(tela, (230, 220, 200), (g.x - g.dir * (60 + i * 18), CHAO_Y - 4 - i * 3),
                             (g.x - g.dir * (90 + i * 18), CHAO_Y - 4 - i * 3), 3)
    jogo.desenhar_ribbat(tela, -tx, 0)
    jogo.desenhar_efeitos(tela, -tx, 0)
    if g.estado != "morrendo":                                          # barra de vida (sem texto)
        larg = 360
        x, y = LARGURA / 2 - larg / 2, 18
        frac = max(0.0, g.vida / VIDA_SALA)
        pygame.draw.rect(tela, PRETO, R(x - 3, y - 3, larg + 6, 18), border_radius=6)
        pygame.draw.rect(tela, (50, 40, 60), R(x, y, larg, 12), border_radius=4)
        pygame.draw.rect(tela, (250, 208, 60), R(x, y, larg * frac, 12), border_radius=4)
        pygame.draw.rect(tela, (255, 240, 170), R(x + 2, y + 2, max(0, larg * frac - 4), 3), border_radius=2)
        cx = x - 26                                                     # carinha de gato do lado da barra
        pygame.draw.circle(tela, PELO, (int(cx), int(y + 6)), 11)
        for sx in (-1, 1):
            pygame.draw.polygon(tela, PELO, [(cx + sx * 4, y - 2), (cx + sx * 11, y - 12), (cx + sx * 11, y + 2)])
            pygame.draw.circle(tela, OLHO, (int(cx + sx * 5), int(y + 5)), 3)
    if g.fade > 0:
        escuro = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        escuro.fill((0, 0, 0, int(255 * min(1.0, g.fade))))
        tela.blit(escuro, (0, 0))


def desenhar(jogo, tela):
    global _fundo
    if jogo.boss.modo == "sala":
        desenhar_sala(jogo, tela)
        return
    if _fundo is None:
        _fundo = criar_fundo()
    g, r, t = jogo.boss, jogo.ribbat, jogo.tempo_total
    tx = random.uniform(-jogo.tremor, jogo.tremor) if jogo.tremor > 0 else 0
    tela.blit(_fundo, (tx, 0))
    if g.estado not in ("pulando", "errou"):
        desenhar_gato(tela, g, t)
    if g.estado == "mirando":                                # aviso da patada: sombra no lugar
        k = min(1.0, g.tempo / 1.0)
        sombra = pygame.Surface((150, 34), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (20, 10, 30, int(60 + 140 * k)), sombra.get_rect())
        tela.blit(sombra, (g.alvo_x - 75, CHAO_Y - 14))
    if g.estado == "agachando":                              # aviso da investida: sombra segue e TRAVA (vermelha)
        cor = (220, 40, 40, 180) if g.trava else (20, 10, 30, 140)
        sombra = pygame.Surface((150, 34), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, cor, sombra.get_rect())
        tela.blit(sombra, (g.alvo_x - 75, CHAO_Y - 14))
    escondido = g.escondido_em(r)
    piscando = r.invuln > 0 and int(r.invuln * 14) % 2 == 0
    if not piscando:
        desenhar_sapo_costas(tela, r, t, jogo.orelhas_coelho)
    for b in g.baguncas:
        if b.vivo:
            desenhar_bagunca(tela, b, t)
    if escondido and not piscando:                           # só as bolinhas dos olhos por cima da bagunça
        for s in (-1, 1):
            pygame.draw.circle(tela, (112, 186, 80), (int(r.cx + s * 9), int(escondido_topo(escondido))), 6)
    if g.estado in ("mirando", "batendo", "recolhendo"):     # a patona vindo pra frente
        if g.estado == "mirando":
            px, py, k = GATO_X + 60 + (g.alvo_x - GATO_X - 60) * 0.4, 230, 0.8 + 0.2 * min(1, g.tempo)
        elif g.estado == "batendo":
            px, py, k = g.alvo_x, CHAO_Y - 30, 1.3
        else:
            u = min(1.0, g.tempo / 0.7)
            px, py, k = g.alvo_x + (GATO_X + 60 - g.alvo_x) * u, CHAO_Y - 30 - 200 * u, 1.3 - 0.5 * u
        pygame.draw.line(tela, PELO, (GATO_X + 50, 200), (px, py), int(50 * k))
        _pata_grande(tela, px, py, k, t)
    if g.estado in ("pulando", "errou"):
        desenhar_gato(tela, g, t)
    jogo.desenhar_efeitos(tela, -tx, 0)
    desenhar_hud(jogo, tela)
    if g.fade > 0:
        escuro = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        escuro.fill((0, 0, 0, int(255 * min(1.0, g.fade))))
        tela.blit(escuro, (0, 0))


def escondido_topo(b):
    return CHAO_Y - {"roupas": 74, "caixa": 104, "travesseiro": 74, "blocos": 124, "cesto": 96, "tenis": 70}[b.tipo]


def desenhar_hud(jogo, tela):
    """5 patinhas lá em cima: quantas patadas ele ainda tem."""
    g = jogo.boss
    for i in range(PATADAS):
        x, y = LARGURA / 2 - 2 * 44 + i * 44, 26
        cheia = i < g.patadas
        cor = PELO if cheia else (150, 140, 160)
        rosa = (230, 140, 170) if cheia else (190, 180, 196)
        pygame.draw.circle(tela, cor, (int(x), int(y + 4)), 13)
        pygame.draw.circle(tela, rosa, (int(x), int(y + 6)), 6)
        for dx in (-9, -3, 3, 9):
            pygame.draw.circle(tela, cor, (int(x + dx), int(y - 9 + abs(dx) * 0.3)), 5)
