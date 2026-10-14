"""
Chefão SECRETO: o VÔ do Ribbat, gigante (design do Gomes).

Aparece no mapa depois de zerar o jogo (a casa do Vô, lá no começo do caminho). É "tipo o gato":
o Ribbat fica DE COSTAS pra câmera e o Vô gigante lá no fundo, de frente. Mas aqui dá pra bater nele
com linguada (a língua vai pra frente, pra dentro da tela) e investida (um pulão pra frente).

Ele tem as MESMAS habilidades do Ribbat:
  - LINGUADA: mira (o papo enche e aparece uma faixa vermelha no chão) e a língua gigante bate ali.
    Sai da faixa (ou pula).
  - INVESTIDA: agacha (a área onde ele vai cair aparece no chão) e pula pra cima da câmera.
    Sai da área: sempre sobra um lado livre. Depois ele fica tonto, pertinho: hora de bater!
30 de vida (linguada 2, investida 3). Com metade da vida ele fica mais rápido.
"""
import math
import random

import pygame

import som as SOM
from chefe import ESC, RECARGA_INVESTIDA, RECARGA_LINGUA, _Pincel, _pts_elipse  # noqa: F401
from config import *  # noqa: F401,F403
from entidades import R

ARENA = {"nome": "A Casa do Vô", "tema": "lagoa", "pedacos": [[
    "..............................",
    "..S...........................",
    "##############################",
    "##############################",
]]}
CHAO_Y = 15 * TILE
VIDA = 30
FURIA = 15
DANO_LINGUA, DANO_INVESTIDA = 2, 3
MOSQUITO_Y = (400, 440)            # voam baixinho (de costas, o Ribbat pega com o corpo)

LONGE_Y = 330                      # onde ficam os pés do Vô lá no fundo
PERTO_Y = CHAO_Y - 6               # e quando ele pula pra perto (logo atrás do Ribbat)
PERTO_K = 0.7                      # pertinho ele fica 1.7x maior
LARG = 230                         # largura do corpo dele (lá no fundo; perto dobra)
FAIXA = 110                        # largura da faixa da linguada dele
ZONA = 380                         # largura da área onde ele cai na investida
ALCANCE_FRENTE = 1.5               # a língua do Ribbat "pra frente" vai 1.5x mais longe (perspectiva)
MIRA = (0.95, 0.75)                # aviso da linguada (normal, bravo)
AGACHA = (1.3, 1.1)                # aviso da investida
PARADO = (1.0, 0.65)
TONTO = 2.6

PELE, ESCURA, CONTORNO = (132, 160, 104), (84, 108, 66), (44, 58, 38)
BARRIGA, MANCHA, IRIS = (228, 222, 192), (100, 124, 80), (206, 174, 96)
BRANCO_P = (246, 244, 238)


class Vovo:
    def __init__(self):
        self.x = LARGURA / 2
        self.z = 0.0                    # 0 = lá no fundo, 1 = pertinho da câmera
        self.vida = VIDA
        self.t = 0.0
        self.tempo = 0.0
        self.flash = 0.0
        self.estado = "acordando"
        self.alvo_x = None              # onde a língua dele vai bater
        self.zona = None                # (x0, x1) onde ele vai cair
        self.pulo_de = None
        self.seguidas = 0               # linguadas seguidas (no máximo 2)
        self.olhar = 0.0
        self.vivo = True
        self.bateu = False              # a língua/o pulo já machucou nessa vez?

    @property
    def bravo(self):
        return self.vida <= FURIA

    @property
    def n(self):
        return 1 if self.bravo else 0

    @property
    def k(self):
        return 1.0 + PERTO_K * self.z

    @property
    def base(self):
        return LONGE_Y + (PERTO_Y - LONGE_Y) * self.z

    def mudar(self, estado):
        self.estado, self.tempo = estado, 0.0
        self.bateu = False

    def corpo(self):
        k = self.k
        return R(self.x - LARG / 2 * k, self.base - 215 * k, LARG * k, 200 * k)

    @property
    def vulneravel(self):
        return self.estado in ("lingua", "recolhendo", "tonto")     # só com a língua pra fora ou tonto

    def boca(self):
        return self.x, self.base - 150 * self.k

    def levar(self, dano, jogo):
        if not self.vulneravel:
            return False
        self.vida -= dano
        self.flash = 0.12
        c = self.corpo()
        jogo.faiscas(c.centerx, c.centery, PELE, 12, 240)
        jogo.tremer(4)
        if self.vida <= 0:
            self.vida = 0
            self.mudar("vencido")
            jogo.tremer(10)
        return True

    def atualizar(self, dt, jogo):
        r = jogo.ribbat
        self.t += dt
        self.tempo += dt
        self.flash = max(0.0, self.flash - dt)
        self.olhar += ((max(-1, min(1, (r.cx - self.x) / 300))) - self.olhar) * min(1, dt * 4)
        e, n = self.estado, self.n
        if e == "acordando":                               # espreguiça e encara o neto
            if self.tempo > 1.8:
                self.mudar("parado")
        elif e == "parado":
            alvo = min(max(r.cx, 260), LARGURA - 260)      # vai devagarinho pro lado do Ribbat
            self.x += max(-60 * dt, min(60 * dt, alvo - self.x))
            if self.tempo >= PARADO[n]:
                if self.seguidas < (2 if self.bravo else 1) and random.random() < 0.55:
                    self.seguidas += 1
                    self.alvo_x = min(max(r.cx, 40), LARGURA - 40)
                    self.mudar("mirando")
                else:
                    self.seguidas = 0
                    meio = min(max(r.cx, ZONA / 2 + 110), LARGURA - ZONA / 2 - 110)
                    self.zona = (meio - ZONA / 2, meio + ZONA / 2)
                    self.mudar("agachando")
        elif e == "mirando":                               # o papo enche... e a faixa vermelha no chão
            if self.tempo >= MIRA[n]:
                self.mudar("lingua")
                SOM.efeito("lingua")
        elif e == "lingua":
            if self.tempo >= 0.5:
                self.mudar("recolhendo")
        elif e == "recolhendo":
            if self.tempo >= 0.35:
                self.mudar("parado")
        elif e == "agachando":
            if self.tempo >= AGACHA[n]:
                self.pulo_de = self.x
                self.mudar("pulando")
                SOM.efeito("investida")
        elif e == "pulando":                               # pulão pra cima da câmera
            u = min(1.0, self.tempo / 0.5)
            self.z = u
            self.x = self.pulo_de + ((self.zona[0] + self.zona[1]) / 2 - self.pulo_de) * u
            if u >= 1:
                self.mudar("caiu")
                jogo.tremer(14)
                jogo.poeira(self.x, CHAO_Y, 20)
        elif e == "caiu":
            if self.tempo >= 0.25:
                self.mudar("tonto")
        elif e == "tonto":
            if self.tempo >= TONTO:
                self.mudar("voltando")
        elif e == "voltando":
            u = min(1.0, self.tempo / 0.6)
            self.z = 1 - u
            if u >= 1:
                self.mudar("parado")
        elif e == "vencido":                               # senta, tontinho... e ri
            self.z = max(0.0, self.z - dt * 1.5)
            if self.tempo >= 3.0:
                self.vivo = False
                jogo.venceu_chefe()

    def perigos(self, r):
        """O que machuca o Ribbat agora."""
        pe = r.y + r.H
        if self.estado == "lingua" and 0.08 < self.tempo < 0.5 and pe > CHAO_Y - 46:
            if abs(r.cx - self.alvo_x) < FAIXA / 2 + r.W / 2:
                return True
        if self.estado == "caiu" and pe > CHAO_Y - 40:
            if self.zona[0] - r.W / 2 < r.cx < self.zona[1] + r.W / 2:
                return True
        return False


def criar():
    return Vovo()


def lingua_frente(r):
    """A língua do Ribbat de costas vai PRA FRENTE (pra cima na tela)."""
    ext = r.lingua_ext()
    if ext < 4:
        return None
    alto = ext * ALCANCE_FRENTE
    return R(r.cx - 8, r.y + r.H - 22 - alto, 16, alto)


def atualizar(jogo, dt, ent):
    r, v = jogo.ribbat, jogo.boss
    x_antes = r.x
    r.atualizar(dt, ent, jogo)
    if r.dash_t > 0:
        r.x = x_antes                                      # de costas, a investida é pra FRENTE (não pro lado)
        r.vx = 0
    v.atualizar(dt, jogo)
    if jogo.estado != "chefe":
        return
    corpo = v.corpo()
    lingua = lingua_frente(r)
    if lingua and not r.lingua_acertou and lingua.colliderect(corpo):
        r.lingua_acertou = True
        if v.levar(DANO_LINGUA, jogo):
            SOM.efeito("acerto")
        elif v.estado != "vencido":                        # fora da hora: bate e volta (faisquinha cinza)
            jogo.faiscas(r.cx, max(lingua.top, corpo.top + 20), (200, 200, 200), 6, 140)
    if r.dash_t > 0 and not r.dash_acertou and corpo.left < r.cx < corpo.right:
        r.dash_acertou = True
        acertou = v.levar(DANO_INVESTIDA, jogo)
        if acertou:
            SOM.efeito("acerto")
        else:
            jogo.faiscas(r.cx, r.y - 40, (200, 200, 200), 6, 140)
        r.dash_t = 0
        r.vx = 0
        r.vy = -380
        r.invuln = max(r.invuln, 0.5 if acertou else 0.0)
    if not v.bateu and v.perigos(r):
        v.bateu = True
        r.machucar(jogo, v.x if v.estado == "caiu" else v.alvo_x)
    jogo.efeitos(dt)


# =====================================================================
# Desenho
# =====================================================================
_fundo = None
_sprites = {}
SPR_W, SPR_H = 340, 300
SPR_O = (170, 290)                                     # os pés dele (meio) dentro do sprite


def criar_fundo():
    """De noite, na lagoa de casa: lua, estrelas, vagalumes, a água e a vitória-régia grandona do Vô."""
    s = pygame.Surface((LARGURA, ALTURA))
    for y in range(ALTURA):
        k = y / ALTURA
        s.fill([int(a + (b - a) * k) for a, b in zip((16, 22, 58), (60, 70, 120))], R(0, y, LARGURA, 1))
    rnd = random.Random(4)
    for _ in range(60):
        pygame.draw.circle(s, (240, 240, 210), (rnd.randint(0, LARGURA), rnd.randint(0, 260)), rnd.choice((1, 1, 2)))
    pygame.draw.circle(s, (244, 242, 214), (820, 80), 40)
    pygame.draw.circle(s, (220, 216, 186), (808, 70), 8)
    for i in range(14):                                                    # taboas lá atrás
        x = 20 + i * 70 + rnd.randint(-10, 10)
        pygame.draw.line(s, (30, 50, 40), (x, 300), (x + rnd.randint(-8, 8), 300 - rnd.randint(60, 120)), 3)
        pygame.draw.ellipse(s, (60, 44, 30), R(x - 4, 300 - rnd.randint(70, 110), 8, 22))
    pygame.draw.rect(s, (30, 60, 90), R(0, 290, LARGURA, ALTURA - 290))    # a água
    for i in range(10):
        y = 300 + i * 18
        pygame.draw.line(s, (50, 90, 130), (rnd.randint(0, 300), y), (rnd.randint(500, LARGURA), y), 1)
    pygame.draw.ellipse(s, (54, 110, 64), R(160, 290, 640, 90))            # a vitória-régia do Vô
    pygame.draw.ellipse(s, (74, 140, 80), R(170, 292, 620, 80))
    pygame.draw.polygon(s, (30, 60, 90), [(480, 336), (430, 372), (530, 372)])
    pygame.draw.rect(s, (60, 120, 60), R(0, CHAO_Y, LARGURA, ALTURA - CHAO_Y))  # a folha onde o Ribbat está
    pygame.draw.rect(s, (90, 160, 80), R(0, CHAO_Y, LARGURA, 6))
    for x in range(0, LARGURA, 60):
        pygame.draw.line(s, (50, 104, 52), (x + 30, CHAO_Y + 10), (x + 10, ALTURA), 2)
    return s


def _vovo(p, pose, olhar, papo, tonto):
    """O Vô de FRENTE: olhões dourados lá em cima, sobrancelhas brancas cheias, bigode branco, papo,
    a boca larga, os braços com as mãozonas no chão e a bengala."""
    agacha = pose == "agachado"
    sy = 0.86 if agacha else 1.0

    def Y(y):
        return y * sy
    # coxas (as pernas de trás dobradas dos lados)
    for s in (-1, 1):
        p.pol(_pts_elipse(s * 112, Y(-46), 58, 44), CONTORNO)
        p.pol(_pts_elipse(s * 112, Y(-48), 54, 40), ESCURA)
        p.pol(_pts_elipse(s * 150, -6, 34, 12), CONTORNO)                  # pés de trás
        p.pol(_pts_elipse(s * 150, -8, 31, 10), ESCURA)
    # corpo
    p.pol(_pts_elipse(0, Y(-104), 134, 108), CONTORNO)
    p.pol(_pts_elipse(0, Y(-104), 130, 104), PELE)
    for x, y, r in ((-90, -150, 10), (84, -140, 8), (-70, -60, 7), (96, -70, 9), (-40, -186, 6), (50, -192, 7)):
        p.pol(_pts_elipse(x, Y(y), r, r * 0.8), MANCHA)
    p.pol(_pts_elipse(0, Y(-62), 86, 62), BARRIGA)                          # barriga
    for i in range(4):
        p.linha([(-60 + i * 40, Y(-30)), (-50 + i * 40, Y(-90))], (210, 202, 170), 1.5)
    # papo (enche antes da linguada)
    if papo > 0.02:
        p.pol(_pts_elipse(0, Y(-124 + papo * 8), 40 + 36 * papo, 16 + 26 * papo), (196, 186, 150))
        p.pol(_pts_elipse(0, Y(-126 + papo * 8), 36 + 34 * papo, 13 + 24 * papo), (244, 230, 200))
    # boca larga (aberta na linguada)
    if pose == "lingua":
        p.pol(_pts_elipse(0, Y(-150), 70, 22), (80, 30, 40))
        p.pol(_pts_elipse(0, Y(-144), 40, 10), (220, 100, 130))
    else:
        p.linha([(-100, Y(-160)), (-50, Y(-150)), (0, Y(-148)), (50, Y(-150)), (100, Y(-160))], CONTORNO, 3)
    # narinas + bigode branco
    for s in (-1, 1):
        p.circ(s * 14, Y(-176), 3, CONTORNO)
        for i in range(4):
            p.pol([(s * (8 + i * 9), Y(-170)), (s * (22 + i * 12), Y(-154 + i * 2)), (s * (14 + i * 9), Y(-166))], BRANCO_P)
    # olhos lá em cima (com pálpebra de vô)
    for s in (-1, 1):
        ex, ey = s * 70, Y(-206)
        p.pol(_pts_elipse(ex, ey, 40, 36), CONTORNO)
        p.pol(_pts_elipse(ex, ey, 37, 33), PELE)
        if tonto:
            p.pol(_pts_elipse(ex, ey + 4, 25, 23), BRANCO_P)
            p.linha([(ex + math.cos(i * 0.35) * i * 0.75, ey + 4 + math.sin(i * 0.35) * i * 0.75)
                     for i in range(1, 30)], CONTORNO, 2.5)                       # olho rodando (espiral)
        else:
            p.pol(_pts_elipse(ex, ey + 4, 27, 25), IRIS)
            ox = olhar * 8
            p.pol(_pts_elipse(ex + ox, ey + 5, 15 if pose != "mirando" else 17, 7 if pose != "mirando" else 4), PRETO)
            p.circ(ex + ox - 6, ey - 2, 4, BRANCO)
        p.pol([(ex - 30, ey - 12), (ex + 30, ey - 12), (ex + 26, ey - 22), (ex - 26, ey - 22)], PELE)   # pálpebra
        p.linha([(ex - 30, ey - 12), (ex + 30, ey - 12)], CONTORNO, 2)
        # sobrancelhas brancas e cheias (bravas quando mira)
        bravo = 10 if pose in ("mirando", "agachado") else 0
        for i in range(6):
            bx = ex - 34 + i * 13
            dentro = ((bx - ex) * -s + 34) / 68              # 1 = pontinha do lado do nariz, 0 = do lado de fora
            y0 = ey - 30 + bravo * dentro                    # bravo: a sobrancelha desce no meio
            p.pol([(bx - 8, y0), (bx + 2 + s * 4, ey - 52 + bravo * dentro), (bx + 10, y0)], BRANCO_P)
    # bochechas
    for s in (-1, 1):
        p.pol(_pts_elipse(s * 104, Y(-140), 13, 8), (232, 150, 140))
    # braços e mãozonas no chão
    for s in (-1, 1):
        ombro, mao = (s * 92, Y(-96)), (s * 86, -14)
        p.osso(ombro, mao, 20, 16, CONTORNO)
        p.osso(ombro, mao, 17, 13, PELE)
        for i in range(4):
            dx = s * (-18 + i * 13)
            p.osso((mao[0], mao[1]), (mao[0] + dx, -2), 5, 4, PELE)
            p.circ(mao[0] + dx, -2, 6, ESCURA)
    # a bengala na mão direita dele
    p.linha([(118, -2), (130, -150)], (120, 84, 52), 7)
    p.linha([(130, -150), (138, -170), (156, -172), (162, -158)], (120, 84, 52), 7)


def sprite(pose="parado", olhar=0.0, papo=0.0, tonto=False):
    chave = (pose, round(olhar, 1), round(papo, 1), tonto)
    if chave not in _sprites:
        sf = pygame.Surface((SPR_W * ESC, SPR_H * ESC), pygame.SRCALPHA)
        _vovo(_Pincel(sf, *SPR_O), pose, round(olhar, 1), round(papo, 1), tonto)
        _sprites[chave] = pygame.transform.smoothscale(sf, (SPR_W, SPR_H))
    return _sprites[chave]


def desenhar_vovo(tela, v, t, ox=0):
    e = v.estado
    pose = {"agachando": "agachado", "lingua": "lingua", "mirando": "mirando"}.get(e, "parado")
    papo = min(1.0, v.tempo / MIRA[v.n]) if e == "mirando" else 0.0
    tonto = e in ("tonto", "vencido")
    img = sprite(pose, v.olhar, papo, tonto)
    k = v.k * (1.06 if e == "pulando" else 1.0)
    if k != 1.0:
        img = pygame.transform.smoothscale(img, (int(SPR_W * k), int(SPR_H * k)))
    if v.flash > 0:
        img = img.copy()
        img.fill((80, 80, 80), special_flags=pygame.BLEND_RGB_ADD)
    sobe = math.sin(v.tempo / 0.5 * math.pi) * 120 if e == "pulando" else 0
    tela.blit(img, (v.x - SPR_O[0] * k + ox, v.base - SPR_O[1] * k - sobe))
    if tonto:
        for i in range(3):
            a = t * 4 + i * math.tau / 3
            pygame.draw.circle(tela, AMARELO, (int(v.x + ox + math.cos(a) * 60 * v.k), int(v.base - 270 * v.k + math.sin(a) * 12)), 7)


def desenhar_lingua_vovo(tela, v, ox=0):
    """A língua gigante dele saindo da boca e batendo no chão (na faixa vermelha)."""
    if v.estado not in ("lingua", "recolhendo"):
        return
    bx, by = v.boca()
    u = min(1.0, v.tempo / 0.08) if v.estado == "lingua" else 1 - min(1.0, v.tempo / 0.35)
    tx, ty = bx + (v.alvo_x - bx) * u, by + (CHAO_Y - 14 - by) * u
    for larg, cor in ((30, (150, 50, 80)), (24, (230, 110, 140))):
        pygame.draw.line(tela, cor, (bx + ox, by), (tx + ox, ty), larg)
    pygame.draw.ellipse(tela, (150, 50, 80), R(tx - 30 + ox, ty - 16, 60, 30))
    pygame.draw.ellipse(tela, (240, 130, 160), R(tx - 26 + ox, ty - 13, 52, 24))


def desenhar_avisos(tela, v, t):
    k = 0.55 + 0.45 * abs(math.sin(t * 9))
    if v.estado == "mirando":
        faixa = pygame.Surface((FAIXA, ALTURA - CHAO_Y + 30), pygame.SRCALPHA)
        faixa.fill((230, 50, 40, int(90 * k)))
        tela.blit(faixa, (v.alvo_x - FAIXA / 2, CHAO_Y - 30))
        pygame.draw.rect(tela, (230, 50, 40), R(v.alvo_x - FAIXA / 2, CHAO_Y - 30, FAIXA, ALTURA - CHAO_Y + 30), 3)
    if v.estado == "agachando":
        x0, x1 = v.zona
        area = pygame.Surface((x1 - x0, 80), pygame.SRCALPHA)
        pygame.draw.ellipse(area, (230, 50, 40, int(110 * k)), area.get_rect())
        pygame.draw.ellipse(area, (230, 50, 40, 255), area.get_rect(), 4)
        tela.blit(area, (x0, CHAO_Y - 40))


def desenhar_sapo_frente(tela, r, t, orelhas):
    """O Ribbat de costas (o mesmo do quarto do Gato), com a língua e a investida indo PRA FRENTE."""
    import gato as GT
    sobe = 0
    if r.dash_t > 0:                                       # o pulão pra frente: sobe na tela e encolhe um pouco
        sobe = math.sin((1 - r.dash_t / DASH_DUR) * math.pi) * 70
    r.y -= sobe
    ext = r.lingua_ext()
    lingua = lingua_frente(r)
    if lingua:                                             # a língua vai pra dentro da tela (fica mais fina lá longe)
        cx, y0 = r.cx, r.y + r.H - 22
        topo = lingua.top
        pygame.draw.polygon(tela, (190, 60, 90), [(cx - 7, y0), (cx - 3, topo), (cx + 3, topo), (cx + 7, y0)])
        pygame.draw.polygon(tela, (240, 110, 140), [(cx - 4, y0), (cx - 2, topo), (cx + 2, topo), (cx + 4, y0)])
        pygame.draw.circle(tela, (240, 110, 140), (int(cx), int(topo)), 6)
    lt = r.lingua_t
    r.lingua_t = 0                                         # (pra não desenhar a língua pro lado)
    GT.desenhar_sapo_costas(tela, r, t, orelhas)
    r.lingua_t = lt
    r.y += sobe
    return ext


def desenhar(jogo, tela):
    global _fundo
    if _fundo is None:
        _fundo = criar_fundo()
    v, r, t = jogo.boss, jogo.ribbat, jogo.tempo_total
    tx = random.uniform(-jogo.tremor, jogo.tremor) if jogo.tremor > 0 else 0
    tela.blit(_fundo, (tx, 0))
    for i in range(10):                                    # vagalumes
        a = t * 0.7 + i * 1.7
        pygame.draw.circle(tela, (250, 240, 140), (int((i * 97 + math.sin(a) * 30) % LARGURA), int(60 + (i * 53) % 200 + math.cos(a) * 12)), 2)
    desenhar_avisos(tela, v, t)
    desenhar_vovo(tela, v, t, tx)
    desenhar_lingua_vovo(tela, v, tx)
    piscando = r.invuln > 0 and int(r.invuln * 14) % 2 == 0
    if not piscando:                                       # o Ribbat é quem está mais perto da câmera: sempre na frente
        desenhar_sapo_frente(tela, r, t, jogo.orelhas_coelho)
    jogo.desenhar_efeitos(tela, -tx, 0)
    desenhar_hud(jogo, tela)


def icone(tela, x, y, k=1.0):
    """Carinha do Vô (barra de vida, menu, mapa)."""
    pygame.draw.ellipse(tela, CONTORNO, R(x - 14 * k, y - 8 * k, 28 * k, 20 * k))
    pygame.draw.ellipse(tela, PELE, R(x - 12 * k, y - 6 * k, 24 * k, 16 * k))
    for s in (-1, 1):
        pygame.draw.circle(tela, CONTORNO, (int(x + s * 7 * k), int(y - 8 * k)), int(6 * k))
        pygame.draw.circle(tela, IRIS, (int(x + s * 7 * k), int(y - 8 * k)), int(4.5 * k))
        pygame.draw.circle(tela, PRETO, (int(x + s * 7 * k), int(y - 7 * k)), max(1, int(2 * k)))
        pygame.draw.line(tela, BRANCO_P, (x + s * 3 * k, y - 15 * k), (x + s * 12 * k, y - 14 * k), max(1, int(3 * k)))
        pygame.draw.line(tela, BRANCO_P, (x + s * 2 * k, y + 1 * k), (x + s * 9 * k, y + 4 * k), max(1, int(2 * k)))


def desenhar_hud(jogo, tela):
    v = jogo.boss
    if v.estado == "acordando":
        return
    larg = 420
    x, y = LARGURA / 2 - larg / 2, 18
    frac = max(0.0, v.vida / VIDA)
    pygame.draw.rect(tela, PRETO, R(x - 3, y - 3, larg + 6, 18), border_radius=6)
    pygame.draw.rect(tela, (30, 40, 30), R(x, y, larg, 12), border_radius=4)
    pygame.draw.rect(tela, (230, 110, 60) if v.bravo else (150, 190, 110), R(x, y, larg * frac, 12), border_radius=4)
    pygame.draw.rect(tela, (230, 240, 200), R(x + 2, y + 2, max(0, larg * frac - 4), 3), border_radius=2)
    pygame.draw.line(tela, PRETO, (x + larg * FURIA / VIDA, y - 4), (x + larg * FURIA / VIDA, y + 14), 2)
    icone(tela, x - 26, y + 8)
