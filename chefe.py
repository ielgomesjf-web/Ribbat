"""
Chefão da Fase 1: a VIÚVA NEGRA (estilo Cuphead: estágios com padrões que dá pra aprender).

Estágio 1 (15 de vida) - pendurada no teto
  - tiro de veneno: 3 gotinhas verdes mirando no Ribbat
  - especial: ela brilha, vai pro meio e atira uma teia que ricocheteia nas paredes deixando
    um fio. O caminho é SEMPRE o mesmo (2 padrões que se alternam): tem pontos cegos pra decorar.
Estágio 2 (20 de vida) - no chão
  - mordida: recua abrindo as presas (aviso) e dá um bote
  - especial: vira o abdômen e metralha teia. Se pegar, puxa devagarzinho com as patas;
    12 apertos pra escapar. Se escapar, ela fica tonta (hora de bater!)
Dano no chefão: linguada 2, investida 3. As duas têm recarga maior aqui.
"""
import math
import random

import pygame

import som as SOM

from config import *  # noqa: F401,F403
from entidades import R

ARENA = {"nome": "Toca da Viúva Negra", "pedacos": [[
    "....rrrrr............rrrrr....",
    "..............................",
    "..S...........................",
    "##############################",
    "##############################",
]]}
CHAO_Y = 15 * TILE
VIDA = (15, 20)
DANO_LINGUA = 2
DANO_INVESTIDA = 3
RECARGA_LINGUA = 0.55      # além do tempo da própria linguada
RECARGA_INVESTIDA = 1.1

# limites onde a teia ricocheteia
PAREDE_E, PAREDE_D, TETO, PISO = 6, LARGURA - 6, 6, CHAO_Y - 4
RICO_VEL = 750
RICO_CARGA = 1.6       # tempo brilhando (com as linhas de mira piscando) antes de atirar
RICO_QUIQUES = 10
RICO_FOLGA = 8          # o fio pega quem passa a 4px dele
RICO_ORIGEM = (480, 190)
# 3 bolas por especial. Calculei os pontos cegos de cada padrão (teste.py confere):
#   padrão A: chão 252-340, chão 632-724 e raiz da esquerda 176-232
#   padrão B: chão 392-580 e chão 728-828
PADROES = ((16, 24, 152), (144, 152, 160))

PRETO_VIUVA = (16, 14, 22)
BRILHO_VIUVA = (52, 46, 70)
VERMELHO_VIUVA = (220, 28, 44)
VENENO = (120, 230, 60)


# =====================================================================
# Projéteis
# =====================================================================
class Veneno:
    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.vivo = True
        self.rastro = []

    def rect(self):
        return R(self.x - 7, self.y - 7, 14, 14)

    def atualizar(self, dt, jogo):
        self.rastro = (self.rastro + [(self.x, self.y)])[-6:]
        self.vy += 250 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y > CHAO_Y - 4 or not (0 < self.x < LARGURA):
            self.vivo = False
            jogo.faiscas(self.x, min(self.y, CHAO_Y - 4), VENENO, 8, 140)


def simular_ricochete(ang, origem=RICO_ORIGEM):
    """Devolve os pontos onde a teia quica (usado pelo jogo e pelo teste dos pontos cegos)."""
    x, y = origem
    vx, vy = math.cos(ang), math.sin(ang)
    pts = [(x, y)]
    for _ in range(RICO_QUIQUES):
        tempos = []
        if vx > 0:
            tempos.append(((PAREDE_D - x) / vx, "x"))
        if vx < 0:
            tempos.append(((PAREDE_E - x) / vx, "x"))
        if vy > 0:
            tempos.append(((PISO - y) / vy, "y"))
        if vy < 0:
            tempos.append(((TETO - y) / vy, "y"))
        dist, eixo = min(tempos)
        x, y = x + vx * dist, y + vy * dist
        pts.append((x, y))
        if eixo == "x":
            vx = -vx
        else:
            vy = -vy
    return pts


class Ricochete:
    """Bola de teia que segue um caminho fixo e deixa o fio pra trás."""
    FIO_DURA = 0.4

    def __init__(self, ang):
        self.caminho = simular_ricochete(ang)
        self.dist = 0.0
        self.total = sum(math.dist(a, b) for a, b in zip(self.caminho, self.caminho[1:]))
        self.fio = self.FIO_DURA
        self.vivo = True

    def pontos(self):
        """Pedaço do caminho já percorrido (o fio) + onde a bola está."""
        pts, falta = [self.caminho[0]], self.dist
        for a, b in zip(self.caminho, self.caminho[1:]):
            seg = math.dist(a, b)
            if falta >= seg:
                pts.append(b)
                falta -= seg
            else:
                k = falta / seg
                pts.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k))
                break
        return pts

    @property
    def acabou(self):
        return self.dist >= self.total and self.fio <= 0

    def atualizar(self, dt):
        if self.dist < self.total:
            self.dist = min(self.total, self.dist + RICO_VEL * dt)
        else:
            self.fio -= dt

    def acerta(self, rect):
        """Só a BOLA machuca. O fio é só o rastro mostrando o caminho."""
        if self.dist >= self.total:
            return False
        x, y = self.pontos()[-1]
        return R(x - 10, y - 10, 20, 20).colliderect(rect)


class BolaTeiaChefe:
    def __init__(self, x, y, vx, vy):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.viva = True
        self.t = 0.0

    def rect(self):
        return R(self.x - 8, self.y - 8, 16, 16)

    def atualizar(self, dt):
        self.t += dt
        self.vy += 300 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y > CHAO_Y or not (-20 < self.x < LARGURA + 20):
            self.viva = False


# =====================================================================
# A Viúva Negra
# =====================================================================
BAIXA = 32          # estágio 2: quanto ela fica agachada (dá pra acertar do chão)
ALTURA_1 = 300      # estágio 1: altura do corpo pendurado


def pose_chao(b):
    """Onde ficam as partes dela no estágio 2 (desenho virado pra direita, origem no chão).
    O desenho E a hitbox usam isso, então o que você vê é o que conta."""
    e = b.estado
    corpo_x = {"preparando": -16, "mordendo": 22}.get(e, 0)
    corpo_y = (-10 if e == "preparando" else 0) + BAIXA
    inclina = 0.45 if b.costas else 0.0
    abd = (-62 + corpo_x * 0.5, -112 + corpo_y - 16 * inclina)
    return {"corpo_x": corpo_x, "corpo_y": corpo_y, "inclina": inclina, "abd": abd,
            "cefalo": (corpo_x + 34, -90 + corpo_y), "cabeca": (corpo_x + 70, -94 + corpo_y),
            "fiandeira": (abd[0] - 72, abd[1] - 22)}
class ViuvaNegra:
    def __init__(self):
        self.estagio = 1
        self.vida = VIDA[0]
        self.x, self.y = 480.0, -170.0
        self.dir = -1
        self.estado = "entrando"
        self.tempo = 0.0
        self.t = 0.0
        self.flash = 0.0
        self.vivo = True
        self.puxando = False
        self.recarga = 0.0
        self.costas = False      # estágio 2: virada de costas (abdômen pro Ribbat)
        self.giro = 0.0          # 0..1 animação de virar
        self.vy = 0.0
        self.cd_tiro = 1.8
        self.rajada = 0
        self.cd_rajada = 0.0
        self.cd_especial = 6.0
        self.cd_mordida = 2.0
        self.cd_metralha = 0.0
        self.padrao = 0
        self.rico_acertou = False
        self.andar = 0.0
        self.tiros = []
        self.ricochetes = []
        self.teias = []

    def mudar(self, estado):
        self.estado = estado
        self.tempo = 0.0

    # ---------- onde estão as partes ----------
    @property
    def vulneravel(self):
        return self.estado not in ("entrando", "caindo", "morrendo")

    def mundo(self, dx, dy):
        """Ponto do desenho do estágio 2 -> ponto na tela (o desenho é espelhado quando ela olha pra esquerda)."""
        olhando = -self.dir if self.costas else self.dir
        return self.x + olhando * dx, self.y + dy

    def partes(self):
        """Abdômen, corpo e cabeça (com as presas), do jeito que estão desenhados."""
        x, y = self.x, self.y
        if self.estagio == 1:
            return [R(x - 58, y - 146, 116, 136), R(x - 40, y - 30, 80, 84)]
        p = pose_chao(self)

        def caixa(centro, w, h):
            cx, cy = self.mundo(*centro)
            return R(cx - w / 2, cy - h / 2, w, h)
        cab = p["cabeca"]
        return [caixa(p["abd"], 140, 112), caixa(p["cefalo"], 88, 64), caixa((cab[0] + 12, cab[1] + 20), 60, 76)]

    def hitbox(self):
        return self.partes() if self.vulneravel else None

    def corpo(self):
        """Encostar aqui machuca (um pouco menor que a hitbox, pra ser justo)."""
        return [r.inflate(-16, -16) for r in self.partes()]

    def boca(self):
        if self.estagio == 1:
            return self.x, self.y + 36
        cab = pose_chao(self)["cabeca"]
        return self.mundo(cab[0] + 24, cab[1] + 44)

    def fiandeira(self):
        """Pontinha do abdômen, de onde sai a teia (estágio 2, de costas)."""
        return self.mundo(*pose_chao(self)["fiandeira"])

    def rect_mordida(self):
        if self.estagio == 2 and self.estado == "mordendo":
            bx, by = self.boca()
            return R(bx - 34, by - 30, 68, 64)
        return None

    # ---------- dano ----------
    def levar(self, dano, jogo):
        if not self.vulneravel:
            return False
        self.vida -= dano
        self.flash = 0.12
        hb = self.hitbox()[-1]          # faísca sai da cabeça
        jogo.faiscas(hb.centerx, hb.centery, (250, 240, 220), 14, 260)
        jogo.faiscas(hb.centerx, hb.centery, VERMELHO_VIUVA, 6, 200)
        jogo.tremer(4)
        if self.vida <= 0:
            self.tiros.clear()
            self.ricochetes.clear()
            self.teias.clear()
            if jogo.ribbat.preso:
                jogo.soltar_teia()
            if self.estagio == 1:
                self.vy = 0.0
                self.mudar("caindo")
            else:
                self.mudar("morrendo")
        return True

    def prender(self, jogo):
        r = jogo.ribbat
        fx, fy = self.fiandeira()
        r.preso = {"aranha": self, "prog": 0.0, "t": 0.0, "precisa": 12, "vel": 30, "puxa_x": fx, "fio": (fx, fy)}
        r.vx = 0
        r.lingua_t = 0
        self.puxando = True
        self.teias.clear()
        self.mudar("puxando")

    # ---------- comportamento ----------
    def atualizar(self, dt, jogo):
        r = jogo.ribbat
        self.t += dt
        self.tempo += dt
        self.flash = max(0.0, self.flash - dt)
        for tiro in self.tiros:
            tiro.atualizar(dt, jogo)
        self.tiros = [tr for tr in self.tiros if tr.vivo]
        for ric in self.ricochetes:
            ric.atualizar(dt)
        self.ricochetes = [ric for ric in self.ricochetes if not ric.acabou]
        for b in self.teias:
            b.atualizar(dt)
        self.teias = [b for b in self.teias if b.viva]
        if self.estagio == 1:
            self.estagio_1(dt, jogo, r)
        else:
            self.estagio_2(dt, jogo, r)

    def estagio_1(self, dt, jogo, r):
        e = self.estado
        if e == "entrando":
            self.y += (ALTURA_1 - self.y) * min(1, dt * 2.2)
            if self.tempo > 2.0:
                self.mudar("pendurada")
        elif e == "pendurada":
            alvo_x = 480 + math.sin(self.t * 0.45) * 300
            self.x += (alvo_x - self.x) * min(1, dt * 2)
            self.y = ALTURA_1 + math.sin(self.t * 1.3) * 40
            self.dir = -1 if r.cx < self.x else 1
            self.cd_tiro -= dt
            self.cd_especial -= dt
            if self.rajada > 0:
                self.cd_rajada -= dt
                if self.cd_rajada <= 0:
                    self.cuspir(jogo, r, (1 - self.rajada) * 0.14)
                    self.rajada -= 1
                    self.cd_rajada = 0.16
            elif self.cd_tiro <= 0:
                self.rajada = 3
                self.cd_rajada = 0.0
                self.cd_tiro = 3.0
            elif self.cd_especial <= 0:
                self.mudar("carregando")
        elif e == "carregando":
            self.x += (RICO_ORIGEM[0] - self.x) * min(1, dt * 4)
            self.y += (RICO_ORIGEM[1] - 40 - self.y) * min(1, dt * 4)
            if self.tempo >= RICO_CARGA:
                self.rico_acertou = False        # cada especial só pode acertar 1 vez
                for graus in PADROES[self.padrao]:
                    self.ricochetes.append(Ricochete(math.radians(graus)))
                self.padrao = 1 - self.padrao
                jogo.tremer(5)
                self.mudar("ricocheteando")
        elif e == "ricocheteando":
            if not self.ricochetes:
                self.cd_especial = 7.5
                self.cd_tiro = 1.0
                self.mudar("pendurada")
        elif e == "caindo":
            # o fio arrebentou!
            self.vy += GRAVIDADE * dt
            self.y += self.vy * dt
            if self.y >= CHAO_Y - 30:
                if self.vy > 0:
                    jogo.tremer(14)
                    for _ in range(3):
                        jogo.poeira(self.x, CHAO_Y, 10)
                self.y = CHAO_Y - 30
                self.vy = 0
            if self.tempo > 2.4:
                self.estagio = 2
                self.vida = VIDA[1]
                self.y = CHAO_Y
                self.cd_mordida = 1.5
                self.cd_especial = 5.0
                self.mudar("andando")

    def cuspir(self, jogo, r, desvio):
        bx, by = self.boca()
        ang = math.atan2((r.y + r.H / 2) - by, r.cx - bx) + desvio
        self.tiros.append(Veneno(bx, by, math.cos(ang) * 300, math.sin(ang) * 300))

    def estagio_2(self, dt, jogo, r):
        e = self.estado
        dx = r.cx - self.x
        if e == "andando":
            self.dir = 1 if dx > 0 else -1
            passo = 0.0
            if abs(dx) > 240:
                passo = self.dir * 80
            elif abs(dx) < 150:
                passo = -self.dir * 60
            self.x = max(150, min(LARGURA - 150, self.x + passo * dt))
            self.andar += dt * (1 if passo else 0.2)
            self.cd_mordida -= dt
            self.cd_especial -= dt
            if self.cd_especial <= 0:
                self.mudar("virando")
            elif self.cd_mordida <= 0 and abs(dx) < 330:
                self.mudar("preparando")
        elif e == "preparando":           # recua com as presas abertas (aviso!)
            self.x = max(150, min(LARGURA - 150, self.x - self.dir * 50 * dt))
            if self.tempo > 0.55:
                self.mudar("mordendo")
        elif e == "mordendo":
            self.x = max(130, min(LARGURA - 130, self.x + self.dir * 650 * dt))
            self.andar += dt * 3
            if self.tempo > 0.32:
                jogo.tremer(3)
                self.mudar("recuando")
        elif e == "recuando":
            self.x = max(150, min(LARGURA - 150, self.x - self.dir * 120 * dt))
            if self.tempo > 0.6:
                self.cd_mordida = 2.0
                self.mudar("andando")
        elif e == "virando":
            self.giro = min(1.0, self.tempo / 0.5)
            self.costas = self.giro > 0.5
            if self.tempo > 0.5:
                self.cd_metralha = 0.0
                self.mudar("metralhando")
        elif e == "metralhando":
            self.cd_metralha -= dt
            if self.cd_metralha <= 0:
                self.cd_metralha = 0.11
                fx, fy = self.fiandeira()
                ang = math.atan2((r.y + r.H / 2) - fy, r.cx - fx) + random.uniform(-0.35, 0.35)
                v = random.uniform(380, 460)
                self.teias.append(BolaTeiaChefe(fx, fy, math.cos(ang) * v, math.sin(ang) * v - 120))
            if self.tempo > 2.2:
                self.mudar("desvirando")
        elif e == "puxando":
            fx, fy = self.fiandeira()
            if not r.preso:
                self.puxando = False
                self.mudar("tonta")       # escapou! ela fica tonta
            else:
                r.preso["puxa_x"] = fx
                r.preso["fio"] = (fx, fy)
                self.andar += dt * 2
                if abs(r.cx - fx) < 60:
                    jogo.soltar_teia(mordida=True)
                    r.machucar(jogo, self.x)
                    self.mudar("desvirando")
        elif e == "tonta":
            if self.tempo > 1.8:
                self.mudar("desvirando")
        elif e == "desvirando":
            self.giro = max(0.0, 1 - self.tempo / 0.5)
            self.costas = self.giro > 0.5
            if self.tempo > 0.5:
                self.cd_especial = 9.0
                self.cd_mordida = 1.2
                self.mudar("andando")
        elif e == "morrendo":
            if self.tempo > 3.0:
                self.vivo = False
                jogo.venceu_chefe()


criar = ViuvaNegra


# =====================================================================
# Luta (chamado pelo Jogo enquanto estado == "chefe")
# =====================================================================
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
            if b.levar(DANO_LINGUA, jogo):
                SOM.efeito("acerto")
        if r.dash_t > 0 and not r.dash_acertou and pr.collidelist(hb) >= 0:
            r.dash_acertou = True
            if b.levar(DANO_INVESTIDA, jogo):
                SOM.efeito("acerto")
            r.dash_t = 0
            r.vx = -r.dir * 330          # quica pra trás depois da investida
            r.vy = -380
            r.invuln = max(r.invuln, 0.5)
            r.atordoado = 0.2
        elif r.dash_t <= 0 and not r.preso and b.estado != "tonta" and pr.collidelist(b.corpo()) >= 0:
            r.machucar(jogo, b.x)
    mordida = b.rect_mordida()
    if mordida and pr.colliderect(mordida):
        r.machucar(jogo, b.x)
    for tiro in b.tiros:
        if lingua and lingua.colliderect(tiro.rect()):
            tiro.vivo = False
            jogo.faiscas(tiro.x, tiro.y, VENENO, 6)
        elif pr.colliderect(tiro.rect()):
            tiro.vivo = False
            r.machucar(jogo, tiro.x)
    if not b.rico_acertou and any(ric.acerta(pr) for ric in b.ricochetes):
        if r.invuln <= 0 and r.dash_t <= 0:
            b.rico_acertou = True
        r.machucar(jogo, r.cx - r.dir)
    for bola in b.teias:
        if pr.colliderect(bola.rect()):
            bola.viva = False
            if r.dash_t > 0 or r.invuln > 0 or r.preso:
                jogo.faiscas(bola.x, bola.y, TEIA, 6)
            else:
                b.prender(jogo)
                break
    jogo.efeitos(dt)


# =====================================================================
# Desenho
# =====================================================================
_fundo = None


def criar_fundo():
    """Dentro da toca: terra escura, raízes, teias nos cantos, cogumelos que brilham, presas embrulhadas."""
    s = pygame.Surface((LARGURA, ALTURA))
    for y in range(ALTURA):
        k = y / ALTURA
        s.fill([int(a + (b - a) * k) for a, b in zip((22, 16, 20), (64, 44, 34))], R(0, y, LARGURA, 1))
    rnd = random.Random(4)
    manchas = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    for _ in range(70):
        x, y, rr = rnd.randint(0, LARGURA), rnd.randint(0, CHAO_Y), rnd.randint(10, 46)
        pygame.draw.circle(manchas, (90, 66, 50, 22), (x, y), rr)
    s.blit(manchas, (0, 0))
    for _ in range(18):  # raízes
        x = rnd.randint(0, LARGURA)
        comp = rnd.randint(40, 170)
        pts = [(x + math.sin(i * 0.7 + x) * 6, i * comp / 6) for i in range(7)]
        pygame.draw.lines(s, (80, 56, 36), False, pts, rnd.randint(2, 5))
    for canto, sx in ((0, 1), (LARGURA, -1)):  # teias enormes nos cantos
        for i in range(7):
            a = i / 6 * math.pi / 2
            pygame.draw.line(s, (120, 116, 130), (canto, 0), (canto + sx * math.sin(a) * 260, math.cos(a) * 260), 1)
        for k in range(1, 7):
            pts = [(canto + sx * math.sin(i / 6 * math.pi / 2) * k * 40, math.cos(i / 6 * math.pi / 2) * k * 40)
                   for i in range(7)]
            pygame.draw.lines(s, (110, 106, 120), False, pts, 1)
    for x, comp in ((300, 120), (650, 90), (820, 150)):  # presas embrulhadas penduradas
        pygame.draw.line(s, (150, 146, 160), (x, 0), (x, comp), 1)
        pygame.draw.ellipse(s, (180, 176, 186), R(x - 12, comp, 24, 40))
        for j in range(5):
            pygame.draw.line(s, (130, 126, 140), (x - 11, comp + 6 + j * 7), (x + 11, comp + 10 + j * 7), 1)
    pygame.draw.rect(s, (54, 38, 28), R(0, CHAO_Y, LARGURA, ALTURA - CHAO_Y))
    pygame.draw.rect(s, (84, 62, 44), R(0, CHAO_Y, LARGURA, 6))
    for i in range(30):
        pygame.draw.circle(s, (40, 28, 20), (rnd.randint(0, LARGURA), rnd.randint(CHAO_Y + 10, ALTURA)), rnd.randint(2, 5))
    for x in (40, 110, 890, 930, 470):  # cogumelos que brilham
        luz = pygame.Surface((90, 90), pygame.SRCALPHA)
        for k in range(6):
            pygame.draw.circle(luz, (90, 230, 200, 10), (45, 45), 44 - k * 7)
        s.blit(luz, (x - 45, CHAO_Y - 66))
        pygame.draw.rect(s, (200, 220, 210), R(x - 3, CHAO_Y - 16, 6, 16))
        pygame.draw.ellipse(s, (90, 230, 200), R(x - 13, CHAO_Y - 26, 26, 14))
        pygame.draw.circle(s, (220, 255, 245), (x - 4, CHAO_Y - 21), 2)
    return s


def desenhar_raiz_plataforma(tela, r):
    """Plataforma de raiz grossa, com teia por baixo."""
    pygame.draw.rect(tela, (60, 40, 26), r.move(0, 4), border_radius=10)
    pygame.draw.rect(tela, (112, 78, 48), r.inflate(0, -2), border_radius=10)
    for i in range(r.width // 26):
        x = r.left + 12 + i * 26
        pygame.draw.line(tela, (84, 58, 36), (x, r.top + 4), (x + 8, r.top + 10), 2)
    for i in range(3):
        x = r.left + 20 + i * (r.width - 40) / 2
        pygame.draw.line(tela, (150, 146, 160), (x, r.bottom), (x + 10, r.bottom + 22), 1)
        pygame.draw.line(tela, (150, 146, 160), (x + 20, r.bottom), (x + 10, r.bottom + 22), 1)


def desenhar_veneno(tela, v):
    for i, (x, y) in enumerate(v.rastro):
        pygame.draw.circle(tela, (90, 190, 50), (int(x), int(y)), 1 + i // 2)
    halo = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(halo, (*VENENO, 70), (16, 16), 15)
    tela.blit(halo, (v.x - 16, v.y - 16))
    ang = math.atan2(v.vy, v.vx)
    cauda = (v.x - math.cos(ang) * 11, v.y - math.sin(ang) * 11)
    lado = (math.cos(ang + math.pi / 2) * 5, math.sin(ang + math.pi / 2) * 5)
    pygame.draw.polygon(tela, (40, 110, 30), [cauda, (v.x + lado[0], v.y + lado[1]), (v.x - lado[0], v.y - lado[1])])
    pygame.draw.circle(tela, (40, 110, 30), (int(v.x), int(v.y)), 7)
    pygame.draw.circle(tela, VENENO, (int(v.x), int(v.y)), 6)
    pygame.draw.circle(tela, (210, 255, 170), (int(v.x - 2), int(v.y - 2)), 2)


def desenhar_ricochete(tela, ric, t):
    pts = ric.pontos()
    alfa = 1.0 if ric.dist < ric.total else max(0.0, ric.fio / ric.FIO_DURA)
    camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    if len(pts) > 1:
        pygame.draw.lines(camada, (220, 220, 240, int(90 * alfa)), False, pts, 7)
        pygame.draw.lines(camada, (250, 250, 255, int(255 * alfa)), False, pts, 2)
        for a, b in zip(pts, pts[1:]):
            n = int(math.dist(a, b) // 22)
            for i in range(1, n):
                k = i / n
                pygame.draw.circle(camada, (255, 255, 255, int(220 * alfa)),
                                   (int(a[0] + (b[0] - a[0]) * k), int(a[1] + (b[1] - a[1]) * k)), 2)
    tela.blit(camada, (0, 0))
    if ric.dist < ric.total:
        x, y = pts[-1]
        halo = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.circle(halo, (255, 255, 255, 80), (25, 25), 24)
        tela.blit(halo, (x - 25, y - 25))
        pygame.draw.circle(tela, (250, 250, 255), (int(x), int(y)), 10)
        for i in range(3):
            a = t * 12 + i * math.tau / 3
            pygame.draw.arc(tela, (170, 170, 200), R(x - 8, y - 8, 16, 16), a, a + 1.4, 2)


# ---------- a aranha em si ----------
ESC = 2      # desenha 2x maior e diminui (fica lisinho)
CAIXA = (480, 380)


def _pts_elipse(cx, cy, rx, ry, ang=0.0, n=36):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + math.cos(i / n * math.tau) * rx * ca - math.sin(i / n * math.tau) * ry * sa,
             cy + math.cos(i / n * math.tau) * rx * sa + math.sin(i / n * math.tau) * ry * ca) for i in range(n)]


class _Pincel:
    """Desenha numa superfície 2x com a origem onde a gente quiser."""

    def __init__(self, s, ox, oy):
        self.s, self.ox, self.oy = s, ox, oy

    def P(self, x, y):
        return ((self.ox + x) * ESC, (self.oy + y) * ESC)

    def pol(self, pts, cor, larg=0):
        pygame.draw.polygon(self.s, cor, [self.P(*p) for p in pts], larg * ESC)

    def circ(self, x, y, r, cor, larg=0):
        pygame.draw.circle(self.s, cor, self.P(x, y), r * ESC, larg * ESC)

    def linha(self, pts, cor, larg):
        pygame.draw.lines(self.s, cor, False, [self.P(*p) for p in pts], max(1, int(larg * ESC)))

    def osso(self, a, b, r1, r2, cor):
        (x1, y1), (x2, y2) = a, b
        ang = math.atan2(y2 - y1, x2 - x1)
        nx, ny = -math.sin(ang), math.cos(ang)
        self.pol([(x1 + nx * r1, y1 + ny * r1), (x2 + nx * r2, y2 + ny * r2),
                  (x2 - nx * r2, y2 - ny * r2), (x1 - nx * r1, y1 - ny * r1)], cor)
        self.circ(x1, y1, r1, cor)
        self.circ(x2, y2, r2, cor)

    def esfera(self, cx, cy, rx, ry, ang=0.0, base=PRETO_VIUVA, brilho=BRILHO_VIUVA):
        """Bolota preta brilhante: base, reflexo e brilho de luz."""
        self.pol(_pts_elipse(cx, cy, rx, ry, ang), base)
        self.pol(_pts_elipse(cx - rx * 0.18, cy - ry * 0.22, rx * 0.7, ry * 0.6, ang), (28, 24, 38))
        self.pol(_pts_elipse(cx - rx * 0.35, cy - ry * 0.45, rx * 0.32, ry * 0.18, ang - 0.4), brilho)
        self.pol(_pts_elipse(cx - rx * 0.42, cy - ry * 0.52, rx * 0.12, ry * 0.07, ang - 0.4), (170, 160, 200))
        borda = _pts_elipse(cx, cy, rx, ry, ang, 36)[3:13]
        self.linha(borda, (90, 64, 120), 2)

    def perna(self, juntas, grossura, cor=PRETO_VIUVA, junta_cor=(70, 50, 86)):
        n = len(juntas) - 1
        for i, (a, b) in enumerate(zip(juntas, juntas[1:])):
            r1 = grossura * (1 - i / (n + 1))
            r2 = grossura * (1 - (i + 1) / (n + 1)) * 0.9
            self.osso(a, b, r1, max(1.2, r2), cor)
            # pelinhos
            for k in (0.3, 0.6):
                px, py = a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
                self.linha([(px, py), (px + (b[1] - a[1]) * 0.06, py - (b[0] - a[0]) * 0.06)], cor, 1)
        for j in juntas[1:-1]:
            self.circ(j[0], j[1], grossura * 0.45, junta_cor)
        # pontinha afiada
        a, b = juntas[-2], juntas[-1]
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        self.pol([(b[0] + math.cos(ang) * 7, b[1] + math.sin(ang) * 7),
                  (b[0] + math.cos(ang + 1.6) * 2, b[1] + math.sin(ang + 1.6) * 2),
                  (b[0] + math.cos(ang - 1.6) * 2, b[1] + math.sin(ang - 1.6) * 2)], cor)

    def ampulheta(self, cx, cy, k, ang=0.0, brilho=0.0):
        ca, sa = math.cos(ang), math.sin(ang)

        def g(x, y):
            return cx + (x * ca - y * sa) * k, cy + (x * sa + y * ca) * k
        cor = (min(255, VERMELHO_VIUVA[0] + int(35 * brilho)), VERMELHO_VIUVA[1] + int(40 * brilho), 44)
        self.pol([g(-12, -18), g(12, -18), g(0, 0)], cor)
        self.pol([g(-12, 18), g(12, 18), g(0, 0)], cor)
        self.linha([g(-8, -15), g(0, -3)], (255, 120, 120), 1.5)


def _olhos(p, cx, cy, brilho):
    olho = (210 + int(45 * brilho), 30, 40)
    for ox, oy, r in ((-11, 0, 7), (11, 0, 7), (-21, -6, 3.5), (21, -6, 3.5), (-6, -10, 3), (6, -10, 3),
                      (-15, 9, 2.5), (15, 9, 2.5)):
        p.circ(cx + ox, cy + oy, r + 1, (40, 6, 10))
        p.circ(cx + ox, cy + oy, r, olho)
        p.circ(cx + ox - r * 0.35, cy + oy - r * 0.35, max(1, r * 0.35), (255, 220, 220))


def _desenhar_pendurada(p, b, t):
    """Estágio 1: pendurada de cabeça pra baixo, de frente, abdômen pra cima."""
    carregando = b.estado == "carregando"
    mexe = math.sin(t * 3)
    for s in (-1, 1):
        for i in range(4):
            raiz = (s * (14 + i * 4), -10 + i * 8)
            joelho = (s * (62 + i * 12), -100 + i * 40 + mexe * 4 * s)
            tornozelo = (s * (92 + i * 16), -58 + i * 50 + mexe * 3)
            ponta = (s * (104 + i * 20), -20 + i * 58 + mexe * 5 * s)
            p.perna([raiz, joelho, tornozelo, ponta], 8.5 - i * 0.6)
    p.esfera(0, -76, 62, 70)
    p.ampulheta(0, -64, 1.25, brilho=(math.sin(t * 8) + 1) / 2 if carregando else 0.0)
    p.esfera(0, -14, 14, 10)
    p.esfera(0, 2, 38, 31)
    for s in (-1, 1):  # pedipalpos e quelíceras com presas
        p.perna([(s * 16, 16), (s * 28, 34), (s * 22, 50)], 4.5)
        p.esfera(s * 10, 26, 10, 11)
        p.pol([(s * 13, 30), (s * 9, 50), (s * 3, 44)], (225, 214, 196))
    _olhos(p, 0, 10, 1.0 if carregando else 0.0)
    if b.estado == "pendurada" and b.rajada > 0:
        p.circ(0, 46, 5, VENENO)


def _desenhar_no_chao(p, b, t):
    """Estágio 2: de lado (virada pra direita; o jogo espelha quando precisa)."""
    e = b.estado
    morrendo = e == "morrendo"
    enrola = min(1.0, b.tempo / 0.8) if morrendo else 0.0
    pose = pose_chao(b)
    corpo_x, corpo_y, costas_inclina = pose["corpo_x"], pose["corpo_y"], pose["inclina"]
    presas_abertas = e in ("preparando", "mordendo")

    def perna(i, lado):
        raiz = (corpo_x + 46 - i * 12, -84 + corpo_y)
        fase = b.andar * 7 + i * math.pi / 2 + (math.pi if lado else 0)
        if e == "puxando" and i == 3:      # patas de trás puxando o fio, uma depois da outra
            fase = b.andar * 9 + (math.pi if lado else 0)
        pe_x = (150, 72, -34, -150)[i] + math.sin(fase) * 16
        pe_y = -max(0.0, math.cos(fase)) * 12
        joelho = ((raiz[0] + pe_x) / 2 + (26, 12, -12, -26)[i], -172 + i * 6 + corpo_y)
        tornozelo = (pe_x * 0.92 + (8, 4, -4, -8)[i], -70 + BAIXA * 0.6 + pe_y * 0.5)
        if enrola:
            joelho = (joelho[0] + (raiz[0] - joelho[0]) * enrola * 0.5, joelho[1] + 60 * enrola)
            tornozelo = (raiz[0] + (tornozelo[0] - raiz[0]) * (1 - enrola * 0.7), -110 + 40 * (1 - enrola))
            pe_x, pe_y = raiz[0] + (pe_x - raiz[0]) * (1 - enrola * 0.8), -120 * enrola
        return [raiz, joelho, tornozelo, (pe_x, pe_y)]

    for i in range(4):          # patas do lado de lá (mais escuras)
        p.perna(perna(i, 1), 8 - i * 0.5, (10, 8, 14), (40, 30, 50))
    abd_x, abd_y = pose["abd"]
    p.esfera(abd_x, abd_y, 74, 58, -0.35 - costas_inclina)
    p.ampulheta(abd_x + 6, abd_y + 50, 0.9, -0.35 - costas_inclina,
                brilho=(math.sin(t * 6) + 1) / 2 if e == "metralhando" else 0.0)
    if b.costas:                 # fiandeiras na ponta do abdômen
        p.circ(*pose["fiandeira"], 6, (60, 50, 70))
        if e == "metralhando":
            p.circ(abd_x - 78, abd_y - 24, 4 + math.sin(t * 30) * 2, TEIA)
    p.esfera(*pose["cefalo"], 44, 32, 0.08)
    cabeca_x, cabeca_y = pose["cabeca"]
    _olhos(p, cabeca_x, cabeca_y, 1.0 if presas_abertas else 0.3)
    abre = 0.7 if presas_abertas else 0.15
    for s, escura in ((1, (10, 8, 14)), (0, PRETO_VIUVA)):
        qx = cabeca_x + 6 - s * 8
        p.perna([(qx - 6, cabeca_y + 14), (qx + 16, cabeca_y + 20), (qx + 26, cabeca_y + 38)], 4.5, escura)
        p.esfera(qx + 6, cabeca_y + 24, 10, 12)
        ang = 1.2 - abre * (1 if s else -1) * 0.6
        p.pol([(qx + 8, cabeca_y + 30), (qx + 8 + math.cos(ang) * 22, cabeca_y + 30 + math.sin(ang) * 22),
               (qx + 2, cabeca_y + 34)], (225, 214, 196))
    for i in range(4):          # patas do lado de cá
        p.perna(perna(i, 0), 9 - i * 0.5)
    if e == "tonta" or morrendo:
        for i in range(3):
            a = t * 4 + i * math.tau / 3
            x, y = cabeca_x + math.cos(a) * 30, cabeca_y - 50 + math.sin(a) * 8
            p.pol([(x + math.cos(k * math.pi / 5 - math.pi / 2) * (8 if k % 2 == 0 else 3.5),
                    y + math.sin(k * math.pi / 5 - math.pi / 2) * (8 if k % 2 == 0 else 3.5)) for k in range(10)],
                  AMARELO)


def desenhar_viuva(tela, b, t):
    w, h = CAIXA
    s = pygame.Surface((w * ESC, h * ESC), pygame.SRCALPHA)
    if b.estagio == 1:
        _desenhar_pendurada(_Pincel(s, w / 2, 200), b, t)
        img = pygame.transform.smoothscale(s, CAIXA)
        pos = (b.x - w / 2, b.y - 200)
    else:
        _desenhar_no_chao(_Pincel(s, w / 2, h - 10), b, t)
        img = pygame.transform.smoothscale(s, CAIXA)
        olhando = -b.dir if b.costas else b.dir
        if olhando < 0:
            img = pygame.transform.flip(img, True, False)
        if b.estado == "morrendo":
            img = pygame.transform.rotate(img, -180 * min(1.0, b.tempo / 0.8))
        pos = (b.x - img.get_width() / 2, b.y - img.get_height() + 10) if b.estado != "morrendo" else \
            (b.x - img.get_width() / 2, b.y - img.get_height() * 0.6)
    if b.flash > 0:
        img = img.copy()
        img.fill((140, 140, 140), special_flags=pygame.BLEND_RGB_ADD)
    if b.estado == "carregando" and b.tempo > 0.3 and int(b.tempo * 8) % 2 == 0:
        ox, oy = RICO_ORIGEM
        for graus in PADROES[b.padrao]:      # mira: pra onde cada bola vai sair
            a = math.radians(graus)
            for k in range(4):
                d0, d1 = 40 + k * 34, 60 + k * 34
                pygame.draw.line(tela, (255, 240, 200), (ox + math.cos(a) * d0, oy + math.sin(a) * d0),
                                 (ox + math.cos(a) * d1, oy + math.sin(a) * d1), 4)
    if b.estado == "carregando":   # aura de energia antes do especial
        aura = pygame.Surface((300, 300), pygame.SRCALPHA)
        pygame.draw.circle(aura, (255, 255, 255, int(40 + 40 * math.sin(t * 20))), (150, 150), 140)
        tela.blit(aura, (b.x - 150, b.y - 190))
    tela.blit(img, pos)


def desenhar(jogo, tela):
    global _fundo
    if _fundo is None:
        _fundo = criar_fundo()
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
    if b.estagio == 1 and b.estado != "caindo":       # fio até o teto
        pygame.draw.line(tela, (220, 220, 235), (b.x + tx, 0), (b.x + tx, b.y - 138 + ty), 2)
    elif b.estagio == 1:                                 # fio arrebentado balançando
        balanco = math.sin(t * 6) * 10 * max(0.0, 1 - b.tempo / 2)
        pygame.draw.lines(tela, (220, 220, 235), False, [(b.x, 0), (b.x + balanco, 50), (b.x - balanco, 90)], 2)
    desenhar_viuva(tela, b, t)
    for ric in b.ricochetes:
        desenhar_ricochete(tela, ric, t)
    for v in b.tiros:
        desenhar_veneno(tela, v)
    for bola in b.teias:
        pygame.draw.circle(tela, TEIA, (int(bola.x), int(bola.y)), 8)
        for i in range(4):
            a = bola.t * 10 + i * math.pi / 2
            pygame.draw.line(tela, (190, 190, 210), (bola.x, bola.y),
                             (bola.x + math.cos(a) * 12, bola.y + math.sin(a) * 12), 1)
    jogo.desenhar_ribbat(tela, -tx, -ty)
    jogo.desenhar_efeitos(tela, -tx, -ty)
    desenhar_hud(jogo, tela)


def desenhar_hud(jogo, tela):
    """Barra de vida da Viúva (sem texto) e as duas ampulhetas = dois estágios."""
    b = jogo.boss
    if b.estado in ("entrando", "morrendo"):
        return
    larg = 360
    x, y = LARGURA / 2 - larg / 2, 18
    frac = max(0.0, b.vida / VIDA[b.estagio - 1]) if b.estado != "caindo" else min(1.0, b.tempo / 2.0)
    pygame.draw.rect(tela, PRETO, R(x - 3, y - 3, larg + 6, 18), border_radius=6)
    pygame.draw.rect(tela, (60, 20, 30), R(x, y, larg, 12), border_radius=4)
    pygame.draw.rect(tela, VERMELHO_VIUVA, R(x, y, larg * frac, 12), border_radius=4)
    pygame.draw.rect(tela, (255, 120, 130), R(x + 2, y + 2, max(0, larg * frac - 4), 3), border_radius=2)
    for i in range(2):
        cx = x - 26 - i * 22
        cheia = (2 - i) > (b.estagio - 1) if b.estado != "caindo" else i == 0
        cor = VERMELHO_VIUVA if cheia else (70, 40, 50)
        pygame.draw.polygon(tela, cor, [(cx - 7, y - 3), (cx + 7, y - 3), (cx, y + 6)])
        pygame.draw.polygon(tela, cor, [(cx - 7, y + 15), (cx + 7, y + 15), (cx, y + 6)])
