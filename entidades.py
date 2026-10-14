"""Tudo que existe dentro da fase: o mapa, o Ribbat, os bichos e as coisas."""
import math
import random

import pygame

import som as SOM

import fases
from config import *  # noqa: F401,F403


UMA_MAO = ("v", "r")   # plataformas que dá pra atravessar pulando por baixo


def R(x, y, w, h):
    return pygame.Rect(int(x), int(y), int(w), int(h))


# =====================================================================
# Fase (o mapa)
# =====================================================================
class Fase:
    def __init__(self, dados):
        self.nome = dados["nome"]
        self.tema = dados.get("tema", "pantano")
        self.neve = dados.get("neve", False)              # chão todo de neve (lá no alto)
        self.pergaminho = dados.get("pergaminho", False)  # o fim é o PERGAMINHO (a corrida)
        if dados.get("montanha"):
            self.linhas = fases.montar_montanha(dados["pedacos"], dados["altura"])
        else:
            self.linhas = fases.montar(dados["pedacos"], dados.get("teto", 0))
        self.alt = len(self.linhas)
        self.larg = len(self.linhas[0])
        self.solidos = {}
        self.espinhos = []
        self.teias_chao = []
        self.lama_chao = []     # lama grudenta (deixa lento, igual teia)
        self.buracos = []       # buracos de formigueiro (soltam formigas)
        self.flores = []        # canteiros de flores (cada um com uma abelha)
        self.maos = []          # mãos do churrasqueiro (não morrem)
        self.pedras = []
        self.inicio = (64, 0)
        self.checkpoints = []
        self.inimigos = []
        self.moscas = []
        self.toca = None
        self.vitorias = []
        self.agua = []          # retângulos de água (cair = perde coração)
        aranhas = []
        peixes = []
        celulas_flor = []
        maos = []
        celulas_pedra = set()
        celulas_agua = set()
        for cy, linha in enumerate(self.linhas):
            for cx, ch in enumerate(linha):
                x, y = cx * TILE, cy * TILE
                if ch in "#=K":
                    self.solidos[(cx, cy)] = "#" if ch == "#" else ch
                elif ch in "vr":
                    self.solidos[(cx, cy)] = ch
                elif ch == "~":
                    celulas_agua.add((cx, cy))
                elif ch == "p":
                    peixes.append(cx)
                elif ch == "X":
                    self.solidos[(cx, cy)] = "X"
                    celulas_pedra.add((cx, cy))
                elif ch == "^":
                    self.espinhos.append(R(x + 4, y + 16, TILE - 8, 16))
                elif ch == "w":
                    self.teias_chao.append(R(x, y + 10, TILE, TILE - 10))
                elif ch == "u":
                    self.lama_chao.append(R(x, y + 18, TILE, TILE - 18))
                elif ch == "m":
                    self.inimigos.append(PeixeLama(x + TILE / 2, y + TILE))
                elif ch == "g":
                    self.inimigos.append(FormigaGuerreira(x + TILE / 2, y + TILE / 2))
                elif ch == "H":
                    self.buracos.append(Buraco(x + TILE / 2, y + TILE))
                elif ch == "F":
                    celulas_flor.append((cx, cy))
                elif ch == "M":
                    maos.append(x + TILE / 2)
                elif ch == "P":
                    self.inimigos.append(Passaro(x + TILE / 2, y + TILE / 2))
                elif ch == "S":
                    self.inicio = (x + 4, y + TILE - Ribbat.H)
                elif ch == "C":
                    self.checkpoints.append(Bandeira(x, y + TILE))
                elif ch == "o":
                    self.moscas.append(Mosca(len(self.moscas), x + TILE / 2, y + TILE / 2))
                elif ch == "f":
                    self.inimigos.append(Formiga(x + 3, y + TILE - Formiga.H))
                elif ch == "a":
                    aranhas.append((x + TILE / 2, y + TILE / 2))
                elif ch == "B":
                    self.toca = Toca(x, y + TILE)
        # vários X encostados viram UMA pedra só
        while celulas_pedra:
            pilha = [celulas_pedra.pop()]
            grupo = set(pilha)
            while pilha:
                cx, cy = pilha.pop()
                for viz in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if viz in celulas_pedra:
                        celulas_pedra.remove(viz)
                        grupo.add(viz)
                        pilha.append(viz)
            self.pedras.append(Pedra(grupo))
        # vitórias-régias: "v" encostados viram uma folha só
        for (cx, cy) in sorted(c for c, ch in self.solidos.items() if ch == "v"):
            if self.vitorias and (cx - 1, cy) in self.vitorias[-1].celulas:
                self.vitorias[-1].celulas.append((cx, cy))
            else:
                self.vitorias.append(Vitoria([(cx, cy)]))
        # lagos: junta a água em retângulos (um por trecho de colunas seguidas)
        topo_agua = {}
        for cx, cy in celulas_agua:
            topo_agua[cx] = min(cy, topo_agua.get(cx, 99))
        for cx in sorted(topo_agua):
            y = topo_agua[cx] * TILE + SUPERFICIE
            if self.agua and self.agua[-1].right == cx * TILE and self.agua[-1].top == y:
                self.agua[-1].width += TILE
            else:
                self.agua.append(R(cx * TILE, y, TILE, self.alt * TILE - y + 200))
        for cx in peixes:
            if cx in topo_agua:
                self.inimigos.append(Peixe(cx * TILE + TILE / 2, topo_agua[cx] * TILE + SUPERFICIE))
        # canteiros de flores: "F" encostados viram um canteiro, cada um com sua abelha
        for cx, cy in sorted(celulas_flor):
            if self.flores and self.flores[-1].fim == cx - 1 and self.flores[-1].linha == cy:
                self.flores[-1].fim = cx
            else:
                self.flores.append(Flor(cx, cx, cy))
        for f in self.flores:
            self.inimigos.append(Abelha(f))
        for x in maos:
            self.maos.append(Mao(x))
        # aranhas por último: precisam saber onde tem teto pra pendurar o fio
        for x, y in aranhas:
            self.inimigos.append(Aranha(self, x, y))
        self.cavernas = self.achar_cavernas()
        self.checkpoints.sort(key=lambda b: b.x)
        for i, b in enumerate(self.checkpoints):
            b.ordem = i
        self.total_moscas = len(self.moscas)

    def achar_cavernas(self):
        """Acha os túneis (terra em cima, vão embaixo, chão logo abaixo) pra desenhar como caverna num morro."""
        colunas = {}
        for (cx, cy), ch in self.solidos.items():
            if ch != "#" or self.solidos.get((cx, cy + 1), "X") != "X":
                continue
            for fundo in range(cy + 2, cy + 6):
                if self.solidos.get((cx, fundo)) == "#":
                    topo = cy
                    while self.solidos.get((cx, topo - 1)) == "#":
                        topo -= 1
                    colunas[cx] = (topo, cy + 1, fundo)
                    break
        cavernas = []
        for cx in sorted(colunas):
            topo, teto, chao = colunas[cx]
            if cavernas and cavernas[-1]["fim"] == cx - 1:
                cavernas[-1]["fim"] = cx
            else:
                cavernas.append({"ini": cx, "fim": cx, "topo": topo, "teto": teto, "chao": chao})
        return cavernas

    def solido(self, cx, cy):
        if cx < 0 or cx >= self.larg:
            return True  # paredes invisíveis nas pontas da fase
        return (cx, cy) in self.solidos

    def tiles_em(self, r):
        """Todos os blocos sólidos que encostam no retângulo r: (cx, cy, tipo, retângulo)."""
        for cy in range(r.top // TILE, (r.bottom - 1) // TILE + 1):
            for cx in range(r.left // TILE, (r.right - 1) // TILE + 1):
                if cx < 0 or cx >= self.larg:
                    yield cx, cy, "#", R(cx * TILE, cy * TILE, TILE, TILE)
                    continue
                ch = self.solidos.get((cx, cy))
                if ch in UMA_MAO:
                    # vitória-régia boia mais embaixo; raiz é o topo do bloco. As duas são fininhas.
                    t = R(cx * TILE, cy * TILE + (TOPO_VITORIA if ch == "v" else 0), TILE, 6)
                    if t.colliderect(r):
                        yield cx, cy, ch, t
                elif ch:
                    yield cx, cy, ch, R(cx * TILE, cy * TILE, TILE, TILE)

    def pedra_em(self, cx, cy):
        for p in self.pedras:
            if (cx, cy) in p.celulas:
                return p
        return None


class Vitoria:
    """Vitória-régia boiando. Se ficar parado em cima, ela afunda e volta depois."""
    AGUENTA = 0.9     # segundos em cima antes de afundar
    SUMIDA = 2.5      # segundos debaixo d'água

    def __init__(self, celulas):
        self.celulas = celulas
        self.peso = 0.0
        self.afundada = 0.0

    @property
    def rect(self):
        (x0, y0), (x1, _) = self.celulas[0], self.celulas[-1]
        return R(x0 * TILE, y0 * TILE + TOPO_VITORIA, (x1 - x0 + 1) * TILE, 6)


class Pedra:
    """Pedrona que só quebra com a investida."""

    def __init__(self, celulas):
        self.celulas = celulas
        xs = [c[0] for c in celulas]
        ys = [c[1] for c in celulas]
        self.rect = R(min(xs) * TILE, min(ys) * TILE,
                      (max(xs) - min(xs) + 1) * TILE, (max(ys) - min(ys) + 1) * TILE)
        self.semente = len(celulas) * 31 + min(xs)


# =====================================================================
# Corpo: qualquer coisa que anda e bate nos blocos
# =====================================================================
class Corpo:
    W = H = TILE

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.no_chao = False
        self.bateu_x = False
        self.vivo = True

    def rect(self):
        return R(self.x, self.y, self.W, self.H)

    @property
    def cx(self):
        return self.x + self.W / 2

    def mover(self, fase, dt, atravessa=None):
        # 1) anda na horizontal e resolve batida em parede
        self.bateu_x = False
        if self.vx:
            indo_dir = self.vx > 0
            self.x += self.vx * dt
            for cx, cy, ch, t in list(fase.tiles_em(self.rect())):
                if ch in UMA_MAO or (atravessa and atravessa(cx, cy)):
                    continue
                if indo_dir:
                    self.x = min(self.x, t.left - self.W)
                else:
                    self.x = max(self.x, t.right)
                self.bateu_x = True
            if self.bateu_x:
                self.vx = 0
        # 2) anda na vertical e resolve chão/teto
        descendo = self.vy >= 0
        pe_antes = self.y + self.H
        self.y += self.vy * dt
        self.no_chao = False
        bateu_y = False
        for cx, cy, ch, t in list(fase.tiles_em(self.rect())):
            if ch in UMA_MAO and not (descendo and pe_antes <= t.top + 1):
                continue  # plataforma de mão única: só segura quem cai por cima
            bateu_y = True
            if descendo:
                self.y = min(self.y, t.top - self.H)
                self.no_chao = True
            else:
                self.y = max(self.y, t.bottom)
        if bateu_y:
            self.vy = 0
        # sonda 1 pixel abaixo dos pés: evita "piscar" entre chão e ar
        if not self.no_chao and self.vy >= 0:
            sonda = self.rect()
            sonda.y += 1
            pe = self.y + self.H
            if any(ch not in UMA_MAO or abs(pe - t.top) <= 1.5 for _, _, ch, t in fase.tiles_em(sonda)):
                self.no_chao = True


# =====================================================================
# Ribbat
# =====================================================================
class Ribbat(Corpo):
    W, H = 24, 24

    def __init__(self, x, y):
        super().__init__(x, y)
        self.dir = 1
        self.coyote = 0.0
        self.buffer = 0.0
        self.pulando = False
        self.invuln = 0.0
        self.atordoado = 0.0
        self.lingua_t = 0.0
        self.lingua_cd = 0.0
        self.lingua_acertou = False
        self.dash_acertou = False
        self.dash_t = 0.0
        self.dash_cd = 0.0
        self.dash_pronto = True
        self.rastro = []
        self.squash = 1.0
        self.passo = 0.0
        self.preso = None     # {"aranha", "prog", "t"} quando tá no casulo de teia
        self.lento = False    # pisando na teia grudenta

    def lingua_ext(self):
        if self.lingua_t <= 0:
            return 0
        p = 1 - self.lingua_t / LINGUA_DUR
        return math.sin(p * math.pi) * LINGUA_ALCANCE

    def boca(self):
        return self.cx + self.dir * 18, self.y + self.H - 16

    def rect_lingua(self):
        ext = self.lingua_ext()
        if ext < 4:
            return None
        bx, by = self.boca()
        if self.dir > 0:
            return R(bx, by - 7, ext, 14)
        return R(bx - ext, by - 7, ext, 14)

    def pose(self):
        if self.preso:
            return "parado"
        if self.dash_t > 0:
            return "investida"
        if not self.no_chao:
            return "pulo" if self.vy < 0 else "queda"
        if abs(self.vx) > 30 and int(self.passo) % 2:
            return "anda"
        return "parado"

    def atualizar(self, dt, ent, jogo):
        self.invuln = max(0, self.invuln - dt)
        self.atordoado = max(0, self.atordoado - dt)
        self.lingua_t = max(0, self.lingua_t - dt)
        self.lingua_cd = max(0, self.lingua_cd - dt)
        self.dash_cd = max(0, self.dash_cd - dt)
        self.coyote = max(0, self.coyote - dt)
        self.buffer = max(0, self.buffer - dt)
        self.rastro = [(x, y, v - dt) for x, y, v in self.rastro if v - dt > 0]
        pr = self.rect()
        self.lento = any(pr.colliderect(t) for t in jogo.fase.teias_chao + jogo.fase.lama_chao)

        if self.preso:
            self.atualizar_preso(dt, ent, jogo)
            return

        vel_max = LENTO_VEL if self.lento else VEL_MAX
        if self.dash_t > 0:
            # investida: reto pra frente, sem gravidade
            self.dash_t -= dt
            self.vx = self.dir * DASH_VEL
            self.vy = 0
            self.rastro.append((self.x, self.y, 0.18))
            if self.dash_t <= 0:
                self.vx = self.dir * vel_max
        else:
            mx = 0 if self.atordoado > 0 else ent.dir
            if mx:
                self.dir = mx
                acel = ACEL if mx * self.vx >= 0 else ACEL + ATRITO
                self.vx = max(-vel_max, min(vel_max, self.vx + mx * acel * dt))
            elif self.atordoado <= 0:
                if self.vx > 0:
                    self.vx = max(0, self.vx - ATRITO * dt)
                else:
                    self.vx = min(0, self.vx + ATRITO * dt)
            if self.lento:
                self.vx = max(-vel_max, min(vel_max, self.vx))
            self.vy = min(self.vy + GRAVIDADE * dt, QUEDA_MAX)

            if self.no_chao:
                self.coyote = COYOTE
            if ent.pulo_apertou:
                self.buffer = BUFFER_PULO
            if self.buffer > 0 and self.coyote > 0 and self.atordoado <= 0:
                self.vy = -PULO * (0.7 if self.lento else 1.0)
                SOM.efeito("pulo")
                self.buffer = self.coyote = 0
                self.pulando = True
                self.squash = 1.25
                jogo.poeira(self.cx, self.y + self.H, 6)
            if self.pulando and not ent.pulo and self.vy < 0:
                self.vy *= PULO_CORTE
                self.pulando = False
            if self.vy >= 0:
                self.pulando = False

            if ent.lingua and jogo.tem_lingua and self.lingua_t <= 0 and self.lingua_cd <= 0:
                self.lingua_t = LINGUA_DUR
                SOM.efeito("lingua")
                self.lingua_cd = LINGUA_DUR + jogo.recarga_lingua
                self.lingua_acertou = False
            if ent.investida and jogo.tem_investida and self.dash_pronto and self.dash_cd <= 0:
                self.dash_t = DASH_DUR
                SOM.efeito("investida")
                self.dash_cd = jogo.recarga_investida
                self.dash_pronto = False
                self.dash_acertou = False
                self.lingua_t = 0
                self.vy = 0
                jogo.tremer(3)

        estava_no_chao = self.no_chao
        atravessa = None
        if self.dash_t > 0:
            def atravessa(cx, cy):
                return jogo.quebrar_pedra(cx, cy)
        self.mover(jogo.fase, dt, atravessa)

        if self.no_chao:
            self.dash_pronto = True
            if not estava_no_chao:
                self.squash = 0.8
                jogo.poeira(self.cx, self.y + self.H, 4)
        self.squash += (1 - self.squash) * min(1, dt * 12)
        self.passo += dt * abs(self.vx) / 45

    def atualizar_preso(self, dt, ent, jogo):
        """Dentro do casulo: não anda, não pula. A aranha vai puxando o fio."""
        p = self.preso
        p["t"] += dt
        p["prog"] = max(0.0, p["prog"] - 0.6 * dt) + ent.mash
        self.lingua_t = 0
        self.dash_t = 0
        a = p["aranha"]
        if not a.vivo or p["prog"] >= p.get("precisa", TEIA_ESCAPE):
            jogo.soltar_teia()
            return
        dx = p.get("puxa_x", a.x) - self.cx
        self.vx = 0 if abs(dx) < 4 else math.copysign(p.get("vel", 70), dx)
        self.vy = min(self.vy + GRAVIDADE * dt, QUEDA_MAX)
        self.mover(jogo.fase, dt)

    def machucar(self, jogo, origem_x):
        if self.invuln > 0 or self.dash_t > 0:
            return
        jogo.coracoes -= 1
        SOM.efeito("dor")
        self.invuln = 1.3
        self.atordoado = 0.25
        self.vy = -420
        self.vx = -260 if origem_x > self.cx else 260
        self.lingua_t = 0
        jogo.tremer(8)
        jogo.faiscas(self.cx, self.y + 12, (230, 60, 70), 12)
        if jogo.coracoes <= 0:
            jogo.game_over()


# =====================================================================
# Formigas: patrulham, se avisam e trabalham em grupo
# =====================================================================
class Formiga(Corpo):
    W, H = 26, 16
    VEL_PATRULHA = 60
    VEL_ATAQUE = 125
    ALTURA_ANDAR = 14     # quanto cada formiga sobe na torre
    SALTO = 480           # pulo da formiga do topo da torre
    ALCANCE_SALTO = 57    # quanto esse pulo sobe (SALTO² / 2·GRAVIDADE)

    def __init__(self, x, y, d=-1):
        super().__init__(x, y)
        self.dir = d
        self.anim = random.random() * 10
        self.estado = "patrulha"   # patrulha -> alerta -> ataque
        self.alerta_t = 0.0
        self.longe_t = 0.0
        self.torre = None
        self.nivel = 0             # 0 = no chão; 1, 2, 3... = andar da torre
        self.saltando = False

    def ve(self, r):
        dx = r.cx - self.cx
        dy = (r.y + r.H) - (self.y + self.H)
        return abs(dx) < 230 and abs(dy) < 110 and (dx * self.dir > 0 or abs(dx) < 70)

    def alertar(self, jogo, atraso=0.0):
        """Viu o sapo! Avisa as amigas por perto, que avisam as delas (onda de alerta)."""
        if self.estado != "patrulha":
            return
        self.estado = "alerta"
        self.alerta_t = 0.45 + atraso
        for o in jogo.fase.inimigos:
            if isinstance(o, Formiga) and o is not self and o.estado == "patrulha":
                d = abs(o.cx - self.cx)
                if d < 320:
                    o.alertar(jogo, atraso + d / 500)

    def atualizar(self, dt, fase, jogo):
        self.anim += dt * 12
        if self.nivel > 0:
            return  # tá na torre: quem posiciona é o jogo
        r = jogo.ribbat
        alvo_vx = 0
        if self.estado == "patrulha":
            alvo_vx = self.dir * self.VEL_PATRULHA
            if self.ve(r):
                self.alertar(jogo)
        elif self.estado == "alerta":
            self.alerta_t -= dt
            self.dir = 1 if r.cx > self.cx else -1
            if self.alerta_t <= 0:
                self.estado = "ataque"
        else:
            dx = r.cx - self.cx
            if abs(dx) > 8:
                self.dir = 1 if dx > 0 else -1
                if self.torre is None:
                    alvo_vx = self.dir * self.VEL_ATAQUE
            self.longe_t = self.longe_t + dt if abs(dx) > 450 else 0
            if self.longe_t > 3:
                self.estado = "patrulha"
        if not self.saltando:
            self.vx = alvo_vx
        self.vy = min(self.vy + GRAVIDADE * dt, QUEDA_MAX)
        self.mover(fase, dt)
        if self.no_chao:
            self.saltando = False
        if self.bateu_x and self.estado == "patrulha":
            self.dir *= -1
        elif self.no_chao and self.vx:
            frente = self.x + (self.W + 2 if self.vx > 0 else -2)
            if not fase.solido(int(frente // TILE), int((self.y + self.H + 2) // TILE)):
                if self.estado == "patrulha":
                    self.dir *= -1       # vira na beirada
                else:
                    self.x -= self.vx * dt  # caçando: para na beirada e espera
        if self.y > fase.alt * TILE + 100:
            self.vivo = False


# =====================================================================
# Aranha: fica pendurada e atira teia
# =====================================================================
class Aranha:
    RAIO = 13

    def __init__(self, fase, x, y):
        self.x, self.base = x, y
        cx, cy = int(x // TILE), int(y // TILE) - 1
        self.topo = 0
        while cy >= 0:
            if (cx, cy) in fase.solidos:
                self.topo = (cy + 1) * TILE
                break
            cy -= 1
        self.amp = max(10, min(90, y - self.topo - 30))
        self.t = random.uniform(0, math.tau)
        self.y = y
        self.vivo = True
        self.recarga = random.uniform(1.5, 3.0)
        self.mira = 0.0           # >0 = se preparando pra atirar
        self.puxando = False      # o Ribbat tá preso na teia dela

    @property
    def cx(self):
        return self.x

    def rect(self):
        return R(self.x - self.RAIO, self.y - self.RAIO, self.RAIO * 2, self.RAIO * 2)

    def atualizar(self, dt, fase, jogo):
        r = jogo.ribbat
        if self.puxando:
            alvo = min(r.y + 6, self.base + self.amp + 120)
            self.y += (alvo - self.y) * min(1, dt * 2.5)
            return
        self.t += dt * 1.8
        normal = self.base + math.sin(self.t) * self.amp
        self.y += (normal - self.y) * min(1, dt * 6)
        if self.mira > 0:
            self.mira -= dt
            if self.mira <= 0:
                self.atirar(jogo)
            return
        self.recarga -= dt
        dx = r.cx - self.x
        dy = r.y + r.H / 2 - self.y
        if self.recarga <= 0 and abs(dx) < 260 and -40 < dy < 260 and not r.preso and r.invuln <= 0:
            self.mira = 0.5

    def atirar(self, jogo):
        r = jogo.ribbat
        dx = r.cx - self.x
        dy = (r.y + r.H / 2) - (self.y + 10)
        d = math.hypot(dx, dy) or 1
        jogo.bolas.append(BolaTeia(self.x, self.y + 10, dx / d * TEIA_VEL, dy / d * TEIA_VEL - 60, self))
        self.recarga = 3.6


class Peixe:
    """Mora no lago e pula SEMPRE no mesmo lugar e no mesmo ritmo. Antes de pular, a água borbulha."""
    CICLO = 3.4     # segundos entre um pulo e outro
    AVISO = 1.0     # borbulha esse tempo antes de pular
    SALTO = 560     # força do pulo (sobe uns 100px)

    def __init__(self, x, agua_y):
        self.x0 = self.x = x
        self.agua = agua_y
        self.y = agua_y + 30
        self.vx = self.vy = 0.0
        self.t = (x / TILE * 0.9) % self.CICLO   # cada peixe num tempo diferente, mas sempre igual
        self.pulando = False
        self.vivo = True
        self.lado = 1

    @property
    def cx(self):
        return self.x

    @property
    def aviso(self):
        return not self.pulando and self.t >= self.CICLO - self.AVISO

    def rect(self):
        if not self.pulando:
            return R(self.x, self.y, 0, 0)
        return R(self.x - 13, self.y - 8, 26, 16)

    def atualizar(self, dt, fase, jogo):
        if not self.pulando:
            self.t += dt
            if self.t >= self.CICLO:
                self.pulando = True
                self.lado *= -1
                self.x, self.y = self.x0, self.agua
                self.vx, self.vy = 25 * self.lado, -self.SALTO
                jogo.respingo(self.x, self.agua)
            return
        self.vy += GRAVIDADE * 0.8 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.vy > 0 and self.y > self.agua + 6:
            self.pulando = False
            self.y = self.agua + 30
            self.t = 0.0
            jogo.respingo(self.x, self.agua)


class PeixeLama:
    """Fica escondido na lama. Se o Ribbat parar (ou cair) em cima, a lama treme e ele morde.
    Passando correndo dá tempo de escapar. Depois de morder fica um pouco pra fora (dá pra matar)."""
    AVISO = 0.25      # lama tremendo antes da mordida
    MORDE = 0.35
    FORA = 1.3

    def __init__(self, x, chao_y):
        self.x, self.chao = x, chao_y
        self.estado = "escondido"
        self.t = 0.0
        self.espia = random.uniform(1.0, 4.0)   # de vez em quando aparecem os olhinhos
        self.vivo = True
        self.dir = 1

    @property
    def cx(self):
        return self.x

    def rect(self):
        if self.estado == "mordendo":
            return R(self.x - 20, self.chao - 46, 40, 46)
        if self.estado == "fora":
            return R(self.x - 22, self.chao - 18, 44, 18)
        return R(self.x, self.chao, 0, 0)

    def atualizar(self, dt, fase, jogo):
        r = jogo.ribbat
        self.t += dt
        if self.estado == "escondido":
            self.espia -= dt
            if self.espia < -0.8:
                self.espia = random.uniform(2.5, 4.5)
            em_cima = r.no_chao and abs(r.cx - self.x) < 22 and abs((r.y + r.H) - self.chao) < 4
            if em_cima:
                self.estado, self.t = "tremendo", 0.0
        elif self.estado == "tremendo":
            if self.t >= self.AVISO:
                self.estado, self.t = "mordendo", 0.0
                self.dir = 1 if r.cx >= self.x else -1
                jogo.respingo(self.x, self.chao, 12, LAMA)
        elif self.estado == "mordendo":
            if self.t >= self.MORDE:
                self.estado, self.t = "fora", 0.0
        elif self.estado == "fora":
            if self.t >= self.FORA:
                self.estado, self.t = "escondido", 0.0
                jogo.respingo(self.x, self.chao, 6, LAMA)


class FormigaGuerreira:
    """Formiga guerreira: voa patrulhando. Quando vê o Ribbat, recua com os olhos acesos (aviso)
    e dá uma INVESTIDA reta pro lugar onde ele estava. Se ele sair de lá durante o aviso, ela erra."""
    W, H = 34, 22
    AVISO = 0.6
    VEL = 520
    ALCANCE = 280

    def __init__(self, x, y):
        self.x0, self.y0 = x, y
        self.x, self.y = x, y
        self.t = random.uniform(0, 6)
        self.estado = "voando"
        self.tempo = 0.0
        self.cd = random.uniform(1.0, 2.0)
        self.dir = 1
        self.vx = self.vy = 0.0
        self.alvo = None
        self.vivo = True

    @property
    def cx(self):
        return self.x

    def rect(self):
        return R(self.x - 22, self.y - 10, 44, 22)     # do tamanho do desenho novo (cabeça ao gáster)

    def mudar(self, estado):
        self.estado, self.tempo = estado, 0.0

    def atualizar(self, dt, fase, jogo):
        r = jogo.ribbat
        self.t += dt
        self.tempo += dt
        alvo_x, alvo_y = r.cx, r.y + r.H / 2
        if self.estado == "voando":
            nx = self.x0 + math.sin(self.t * 0.8) * 60
            self.dir = 1 if nx > self.x else -1
            self.x, self.y = nx, self.y0 + math.sin(self.t * 2.2) * 10
            self.cd -= dt
            if self.cd <= 0 and math.hypot(alvo_x - self.x, alvo_y - self.y) < self.ALCANCE and not r.preso:
                self.alvo = (alvo_x, alvo_y)          # trava a mira no lugar onde ele ESTÁ agora
                self.dir = 1 if alvo_x > self.x else -1
                self.mudar("mirando")
        elif self.estado == "mirando":
            ax, ay = self.alvo
            d = math.hypot(ax - self.x, ay - self.y) or 1
            self.x -= (ax - self.x) / d * 40 * dt      # recua um tiquinho
            self.y -= (ay - self.y) / d * 40 * dt
            if self.tempo >= self.AVISO:
                d = math.hypot(ax - self.x, ay - self.y) or 1
                self.vx, self.vy = (ax - self.x) / d * self.VEL, (ay - self.y) / d * self.VEL
                self.mudar("investindo")
        elif self.estado == "investindo":
            self.x += self.vx * dt
            self.y += self.vy * dt
            if self.tempo > 0.75 or fase.solido(int(self.x // TILE), int(self.y // TILE)):
                self.x -= self.vx * dt
                self.y -= self.vy * dt
                self.mudar("voltando")
        elif self.estado == "voltando":
            casa_x = self.x0 + math.sin(self.t * 0.8) * 60
            dx, dy = casa_x - self.x, self.y0 - self.y
            d = math.hypot(dx, dy)
            if d < 6:
                self.cd = 2.5
                self.mudar("voando")
            else:
                self.dir = 1 if dx > 0 else -1
                self.x += dx / d * min(d, 160 * dt)
                self.y += dy / d * min(d, 160 * dt)


class Buraco:
    """Buraco de formigueiro: solta formigas. Uma investida em cima TAMPA o buraco."""

    def __init__(self, x, chao_y):
        self.x, self.chao = x, chao_y
        self.vivo = True
        self.timer = random.uniform(0.8, 2.0)
        self.filhas = []

    def rect(self):
        return R(self.x - 26, self.chao - 16, 52, 16)

    def atualizar(self, dt, jogo):
        self.filhas = [f for f in self.filhas if f.vivo]
        if abs(jogo.ribbat.cx - self.x) > 520:
            return
        self.timer -= dt
        if self.timer <= 0 and len(self.filhas) < 2:
            self.timer = 4.0
            d = -1 if jogo.ribbat.cx < self.x else 1
            f = Formiga(self.x - Formiga.W / 2, self.chao - Formiga.H, d)
            f.estado = "ataque"           # sai do buraco já sabendo onde você tá
            self.filhas.append(f)
            jogo.fase.inimigos.append(f)
            jogo.poeira(self.x, self.chao, 5)


class Mosquito:
    """Mosquito das lutas de chefe: atravessa a arena voando. Pegou (linguada ou encostando) = +1 coração."""

    def __init__(self, lado, y):
        self.lado = lado                      # 1 = vem da esquerda, -1 = vem da direita
        self.x = -20 if lado > 0 else LARGURA + 20
        self.y0 = y
        self.y = y
        self.t = random.uniform(0, 6)
        self.vivo = True

    @property
    def cx(self):
        return self.x

    def rect(self):
        return R(self.x - 12, self.y - 10, 24, 20)

    def atualizar(self, dt):
        self.t += dt
        self.x += self.lado * 105 * dt
        self.y = self.y0 + math.sin(self.t * 2.4) * 30
        if not -40 < self.x < LARGURA + 40:
            self.vivo = False


class Passaro:
    """Gavião: plana patrulhando. Quando vê o Ribbat lá embaixo, guincha, TRAVA a mira (alvo no chão)
    e mergulha reto. Se o Ribbat sair do alvo durante o aviso, ele erra."""
    AVISO = 0.7
    VEL = 470

    def __init__(self, x, y):
        self.x0, self.y0 = x, y
        self.x, self.y = x, y
        self.t = random.uniform(0, 6)
        self.estado = "voando"
        self.tempo = 0.0
        self.cd = random.uniform(1.0, 2.0)
        self.dir = 1
        self.vx = self.vy = 0.0
        self.alvo = None
        self.percorrido = 0.0
        self.vivo = True

    @property
    def cx(self):
        return self.x

    def rect(self):
        return R(self.x - 20, self.y - 10, 40, 22)

    def mudar(self, estado):
        self.estado, self.tempo = estado, 0.0

    def atualizar(self, dt, fase, jogo):
        r = jogo.ribbat
        self.t += dt
        self.tempo += dt
        if self.estado == "voando":
            nx = self.x0 + math.sin(self.t * 0.6) * 110
            self.dir = 1 if nx >= self.x else -1
            self.x, self.y = nx, self.y0 + math.sin(self.t * 1.4) * 8
            self.cd -= dt
            dx, dy = r.cx - self.x, (r.y + r.H / 2) - self.y
            if self.cd <= 0 and abs(dx) < 240 and 40 < dy < 360 and not r.preso:
                self.alvo = (r.cx, r.y + r.H / 2)             # trava a mira AQUI
                self.dir = 1 if dx > 0 else -1
                self.mudar("mirando")
        elif self.estado == "mirando":
            self.y -= 30 * dt                                 # sobe um tiquinho pra pegar impulso
            if self.tempo >= self.AVISO:
                ax, ay = self.alvo
                d = math.hypot(ax - self.x, ay - self.y) or 1
                self.vx, self.vy = (ax - self.x) / d * self.VEL, (ay - self.y) / d * self.VEL
                self.distancia = d
                self.percorrido = 0.0
                self.mudar("mergulhando")
        elif self.estado == "mergulhando":
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.percorrido += self.VEL * dt
            bateu = fase.solido(int(self.x // TILE), int((self.y + 8) // TILE))
            if bateu or self.percorrido > self.distancia + 50 or self.tempo > 1.4:
                if bateu:
                    self.x -= self.vx * dt
                    self.y -= self.vy * dt
                self.mudar("voltando")
        elif self.estado == "voltando":
            casa_x = self.x0 + math.sin(self.t * 0.6) * 110
            dx, dy = casa_x - self.x, self.y0 - self.y
            d = math.hypot(dx, dy)
            if d < 6:
                self.cd = 2.5
                self.mudar("voando")
            else:
                self.dir = 1 if dx > 0 else -1
                self.x += dx / d * min(d, 190 * dt)
                self.y += dy / d * min(d, 190 * dt)


class Flor:
    """Canteiro de flores no chão (não é sólido). Pisar em cima acorda a abelha."""

    def __init__(self, ini, fim, linha):
        self.ini, self.fim, self.linha = ini, fim, linha

    @property
    def x0(self):
        return self.ini * TILE

    @property
    def x1(self):
        return (self.fim + 1) * TILE

    @property
    def chao(self):
        return (self.linha + 1) * TILE

    def pisando(self, r):
        return r.no_chao and self.x0 - 2 <= r.cx <= self.x1 + 2 and abs(r.y + r.H - self.chao) < 4


class Abelha:
    """Fica pousada no canteiro. Se o Ribbat pisar nas flores, ela levanta (aviso) e PERSEGUE ele um tempinho."""
    AVISO = 0.45
    PERSEGUE = 3.2
    VEL = 175

    def __init__(self, flor):
        self.flor = flor
        self.casa = ((flor.x0 + flor.x1) / 2, flor.chao - 34)
        self.x, self.y = self.casa
        self.estado = "pousada"
        self.tempo = 0.0
        self.t = random.uniform(0, 6)
        self.dir = 1
        self.cd = 0.0
        self.vivo = True

    @property
    def cx(self):
        return self.x

    def rect(self):
        return R(self.x - 12, self.y - 9, 24, 18)

    def mudar(self, estado):
        self.estado, self.tempo = estado, 0.0

    def atualizar(self, dt, fase, jogo):
        r = jogo.ribbat
        self.t += dt
        self.tempo += dt
        self.cd = max(0.0, self.cd - dt)
        if self.estado == "pousada":
            self.x = self.casa[0] + math.sin(self.t * 0.7) * 14
            self.y = self.casa[1] + math.sin(self.t * 3) * 2
            if self.cd <= 0 and self.flor.pisando(r):
                self.mudar("alerta")
        elif self.estado == "alerta":
            self.y -= 50 * dt
            self.dir = 1 if r.cx > self.x else -1
            if self.tempo > self.AVISO:
                self.mudar("atacando")
        elif self.estado == "atacando":
            dx, dy = r.cx - self.x, (r.y + 8) - self.y
            d = math.hypot(dx, dy) or 1
            self.dir = 1 if dx > 0 else -1
            self.x += dx / d * self.VEL * dt
            self.y += dy / d * self.VEL * dt + math.sin(self.t * 14) * 60 * dt
            if self.tempo > self.PERSEGUE:
                self.mudar("voltando")
        elif self.estado == "voltando":
            dx, dy = self.casa[0] - self.x, self.casa[1] - self.y
            d = math.hypot(dx, dy)
            if d < 6:
                self.cd = 1.5
                self.mudar("pousada")
            else:
                self.dir = 1 if dx > 0 else -1
                self.x += dx / d * min(d, 140 * dt)
                self.y += dy / d * min(d, 140 * dt)


class Mao:
    """A mão do moço do churrasco: segue o Ribbat lá de cima (a sombra aparece embaixo), para e TREME (aviso)
    e dá um tapão. Não dá pra matar (é gente!). Só ataca quando o Ribbat está perto da mesa."""
    AREA = 260          # até onde ela alcança (pra cada lado do moço)
    AVISO = 0.7

    def __init__(self, x):
        self.x0 = x
        self.x = x
        self.y = -160.0     # y = onde fica a PALMA da mão (embaixo dela)
        self.estado = "longe"
        self.tempo = 0.0
        self.cd = 1.0
        self.alvo_y = 0.0

    def mudar(self, estado):
        self.estado, self.tempo = estado, 0.0

    def superficie(self, fase, x):
        cx = int(x // TILE)
        for cy in range(fase.alt):
            ch = fase.solidos.get((cx, cy))
            if ch and ch not in "vr":
                return cy * TILE
        return fase.alt * TILE

    def batendo(self):
        return self.estado in ("batendo", "no_chao")

    def rect(self):
        return R(self.x - 44, self.y - 64, 88, 64)

    def atualizar(self, dt, jogo):
        r, fase = jogo.ribbat, jogo.fase
        self.tempo += dt
        perto = abs(r.cx - self.x0) < self.AREA
        alto = 130
        if self.estado == "longe":
            self.y += (-160 - self.y) * min(1, dt * 3)
            if perto:
                self.mudar("seguindo")
        elif self.estado == "seguindo":
            alvo = min(max(r.cx, self.x0 - self.AREA + 40), self.x0 + self.AREA - 40)
            self.x += (alvo - self.x) * min(1, dt * 2.5)
            self.y += (alto - self.y) * min(1, dt * 4)
            self.cd -= dt
            if not perto:
                self.mudar("longe")
            elif self.cd <= 0:
                self.alvo_y = self.superficie(fase, self.x)
                self.mudar("mirando")
        elif self.estado == "mirando":                      # parou e tremeu: vai bater AQUI
            if self.tempo > self.AVISO:
                self.mudar("batendo")
        elif self.estado == "batendo":
            self.y = min(self.alvo_y, self.y + 1500 * dt)
            if self.y >= self.alvo_y:
                jogo.tremer(9)
                jogo.poeira(self.x, self.alvo_y, 10)
                self.mudar("no_chao")
        elif self.estado == "no_chao":
            if self.tempo > 0.4:
                self.mudar("subindo")
        elif self.estado == "subindo":
            self.y += (alto - self.y) * min(1, dt * 4)
            if self.tempo > 0.5:
                self.cd = random.uniform(1.0, 1.6)
                self.mudar("seguindo")


class BolaTeia:
    def __init__(self, x, y, vx, vy, dona):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.dona = dona
        self.vida = 2.0
        self.viva = True
        self.t = 0.0

    def rect(self):
        return R(self.x - 7, self.y - 7, 14, 14)

    def atualizar(self, dt, fase):
        self.t += dt
        self.vy += 250 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vida -= dt
        if self.vida <= 0 or fase.solido(int(self.x // TILE), int(self.y // TILE)):
            self.viva = False


# =====================================================================
# Coisas da fase
# =====================================================================
class Mosca:
    def __init__(self, ident, x, y):
        self.id = ident
        self.x, self.y = x, y
        self.t = random.random() * 6

    def rect(self):
        return R(self.x - 10, self.y - 10 + math.sin(self.t * 3) * 4, 20, 20)


class Bandeira:
    ALT = 3 * TILE

    def __init__(self, x, base):
        self.x = x + TILE / 2
        self.base = base
        self.ativa = False
        self.subida = 0.0
        self.ordem = 0


class Toca:
    def __init__(self, x, base):
        self.x = x + TILE / 2
        self.base = base


class Entrada:
    """O que o jogador apertou neste quadro."""

    def __init__(self):
        self.dir = 0
        self.pulo = False
        self.pulo_apertou = False
        self.lingua = False
        self.investida = False
        self.mash = 0     # quantas teclas de ação foram apertadas (pra rasgar a teia)
