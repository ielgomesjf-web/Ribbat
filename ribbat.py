"""
Ribbat e o Pergaminho Perdido
Jogo de plataforma em Python + Pygame.

Controles:
  A/D ou setas ............ andar
  Espaço, W ou seta cima .. pular (segura pra pular mais alto)
  E ....................... linguada  (depois da 1ª bandeira)
  Q ....................... investida (depois da 2ª bandeira)
  apertar rápido .......... rasgar a teia quando estiver preso
  Esc ..................... pausa
  F11 ..................... tela cheia
"""
import math
import os
import random
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402

import desenho as D  # noqa: E402
import fases  # noqa: E402
import pantano as P  # noqa: E402
import lamacal as L  # noqa: E402
import formigueiro as FM  # noqa: E402
import quintal as Q  # noqa: E402
import montanha as MT  # noqa: E402
import quadrinhos as HQ  # noqa: E402
import chefe as CH  # noqa: E402
import besouro as BS  # noqa: E402
import rainha as RA  # noqa: E402
import gato as GT  # noqa: E402
import aguia as AG  # noqa: E402
import vovo as VV  # noqa: E402
import menu as MENU  # noqa: E402
import progresso as PR  # noqa: E402
import som as SOM  # noqa: E402
import medalhas as MD  # noqa: E402
import chapeus as CP  # noqa: E402
import conquistas as CQ  # noqa: E402
from config import *  # noqa: E402,F401,F403
from entidades import (Abelha, Aranha, Entrada, Fase, Formiga, FormigaGuerreira, Mosquito, Passaro, Peixe,  # noqa: E402
                       PeixeLama, Ribbat, R)

FANTASMA_HZ = 30          # o sapo fantasma guarda 30 posições por segundo
CHEFES = {"viuva": CH, "besouro": BS, "rainha": RA, "gato": GT, "aguia": AG, "vovo": VV}
TECLAS_PULO = (pygame.K_SPACE, pygame.K_w, pygame.K_UP)
TECLAS_MASH = TECLAS_PULO + (pygame.K_e, pygame.K_q, pygame.K_a, pygame.K_d, pygame.K_LEFT, pygame.K_RIGHT)


class Jogo:
    def __init__(self, dados_fase=fases.FASE_1):
        self.dados_fase = dados_fase
        self.fonte_gigante = pygame.font.SysFont("segoeui,arial", 80, bold=True)
        self.fonte_grande = pygame.font.SysFont("segoeui,arial", 36, bold=True)
        self.fonte = pygame.font.SysFont("segoeui,arial", 22, bold=True)
        self.fonte_tecla = pygame.font.SysFont("segoeui,arial", 15, bold=True)
        self.tiles = D.criar_tiles()
        self.fundo = P.criar_fundo()
        self.fundo_lama = L.criar_fundo()
        self.tiles_lama = {**self.tiles, **L.criar_tiles()}
        self.fundo_form = FM.criar_fundo()
        self.tiles_form = {**self.tiles, **FM.criar_tiles()}
        self.fundo_quintal = Q.criar_fundo()
        self.tiles_quintal = {**self.tiles, **Q.criar_tiles()}
        self.fundo_montanha = MT.criar_fundo()
        self.tiles_montanha = {**self.tiles, **MT.criar_tiles()}
        self.estado = "titulo"
        self.tempo_total = 0.0
        self.hq_paineis = 0
        self.hq_alfa = 0.0
        self.progresso = PR.carregar()
        self.menu_i = 0
        self.menu_j = 0
        self.menu_tremor = 0.0
        self.fase_atual = MENU.FASES[0]
        self.tempo_fase = 0.0          # relógio da fase (não zera quando cai: é o tempo do caminho todo)
        self.tempo_chefe = 0.0         # relógio da luta (zera quando recomeça a luta)
        self.ultimo_tempo = None       # (tempo, foi recorde?, "tempo"/"tempo_chefe", sem dano?) pra tela do fim
        self.sem_dano = True           # essa tentativa (fase ou luta) ainda não perdeu coração?
        self._coracoes_visto = 0
        self.gravacao = []             # o caminho desta tentativa (vira o fantasma se for recorde)
        self.fantasma = None           # o caminho do recorde, que o sapo fantasma refaz
        self.ver_fantasma = True       # tecla G liga/desliga
        self.maratona = None           # maratona de chefões: {"i": qual chefe, "t": tempo, "c": corações}
        self.loja_i = 0
        self.loja_tremor = 0.0
        self.menu_k = 0                # na fileira de cima: 0 = maratona, 1 = álbum
        self.avisos_conquista = []     # figurinhas novas descendo no canto: [nome, tempo]
        CQ.conferir(self.progresso)    # o que já tinha conseguido antes do álbum existir (sem aviso)
        self._fantasma_img = {}
        self.novo_jogo()

    # ---------- ciclo de vida ----------
    def novo_jogo(self):
        self.tem_lingua = False
        self.tem_investida = False
        self.coracoes_max = CORACOES_INICIO
        self.salvo = {"bandeiras": 0, "moscas": set()}
        self.carregar()

    def carregar(self):
        """Monta a fase de novo a partir da última bandeira fincada."""
        self.fase = Fase(self.dados_fase)
        self.moscas_pegas = set(self.salvo["moscas"])
        self.fase.moscas = [m for m in self.fase.moscas if m.id not in self.moscas_pegas]
        for b in self.fase.checkpoints[:self.salvo["bandeiras"]]:
            b.ativa = True
            b.subida = 1.0
        self.ribbat = Ribbat(*self.ponto_renascer())
        self.coracoes = self.coracoes_max
        self.particulas = []
        self.bolas = []
        self.torres = []
        self.icones = []
        self.tremor = 0.0
        self.no_chefe = False
        # a corrida contra a Águia (depois de vencer ela): o Ribbat cai lá de cima e a águia larga junto
        self.corrida = {"t": -AG.LARGADA} if self.dados_fase is fases.FASE_CORRIDA else None
        self.orelhas_coelho = self.corrida is not None and PR.fase(self.progresso, self.fase_atual["id"])["chefe"]
        if self.corrida:
            self.ribbat.y = -80
            if self.maratona:
                self.coracoes = self.maratona["c"]
        self.recarga_lingua = 0.0
        self.recarga_investida = DASH_RECARGA
        self.cam_x = max(0, self.ribbat.cx - LARGURA * 0.4)
        self.cam_y = max(0, min(self.ribbat.y - ALTURA * 0.55, self.fase.alt * TILE - ALTURA))
        self.ultimo_seguro = (self.ribbat.x, self.ribbat.y)
        self.vagalumes = [[random.uniform(0, LARGURA), random.uniform(80, 420), random.uniform(0, 6)]
                          for _ in range(18)]

    def ponto_renascer(self):
        ativas = [b for b in self.fase.checkpoints if b.ativa]
        if ativas:
            return ativas[-1].x + 14, ativas[-1].base - Ribbat.H
        return self.fase.inicio

    def game_over(self):
        self.estado = "gameover"
        SOM.efeito("gameover")

    # ---------- efeitos ----------
    def tremer(self, forca):
        self.tremor = max(self.tremor, forca)

    def faiscas(self, x, y, cor, n, forca=180):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(forca * 0.3, forca)
            vida = random.uniform(0.3, 0.7)
            self.particulas.append([x, y, math.cos(a) * v, math.sin(a) * v - 80, vida, vida, cor,
                                    random.randint(2, 5)])

    def poeira(self, x, y, n):
        for _ in range(n):
            vida = random.uniform(0.2, 0.4)
            self.particulas.append([x + random.uniform(-10, 10), y - 2, random.uniform(-60, 60),
                                    random.uniform(-60, -10), vida, vida, (210, 200, 170), 3])

    def respingo(self, x, y, n=10, cor=None):
        if cor is None:
            cor = {"pantano": (170, 220, 220), "formigueiro": (170, 130, 90), "quintal": (200, 235, 255),
                   "montanha": (230, 236, 244)}.get(self.fase.tema, LAMA)
        for _ in range(n):
            vida = random.uniform(0.3, 0.6)
            self.particulas.append([x + random.uniform(-8, 8), y, random.uniform(-90, 90),
                                    random.uniform(-320, -120), vida, vida, cor, 3])

    def cair(self, na_agua):
        """Caiu no buraco ou na água: perde 1 coração e volta pro último chão firme."""
        r = self.ribbat
        if na_agua:
            self.respingo(r.cx, r.y + r.H, 16)
        self.soltar_teia(mordida=True)
        self.coracoes -= 1
        SOM.efeito("dor")
        if self.coracoes <= 0:
            self.game_over()
            return
        r.x, r.y = self.ultimo_seguro
        r.vx = r.vy = 0
        r.dash_t = 0
        r.invuln = 1.2
        self.tremer(6)

    def atualizar_vitorias(self, dt):
        r = self.ribbat
        pe = r.y + r.H
        for v in self.fase.vitorias:
            if v.afundada > 0:
                v.afundada -= dt
                if v.afundada <= 0 and not r.rect().colliderect(v.rect.inflate(0, 30)):
                    for c in v.celulas:
                        self.fase.solidos[c] = "v"
                    v.peso = 0
                    self.respingo(v.rect.centerx, v.rect.top, 6)
                elif v.afundada <= 0:
                    v.afundada = 0.1
                continue
            em_cima = r.no_chao and abs(pe - v.rect.top) < 2 and r.x + r.W > v.rect.left and r.x < v.rect.right
            v.peso = v.peso + dt if em_cima else max(0.0, v.peso - dt * 0.5)
            if v.peso >= v.AGUENTA:
                for c in v.celulas:
                    self.fase.solidos.pop(c, None)
                v.afundada = v.SUMIDA
                self.respingo(v.rect.centerx, v.rect.top, 8)

    def quebrar_pedra(self, cx, cy):
        SOM.efeito("pedra")
        self.contar("pedras")
        p = self.fase.pedra_em(cx, cy)
        if p is None:
            return False
        for c in p.celulas:
            self.fase.solidos.pop(c, None)
        self.fase.pedras.remove(p)
        for c in p.celulas:
            self.faiscas(c[0] * TILE + 16, c[1] * TILE + 16, ROCHA, 12, 300)
        self.tremer(10)
        return True

    def derrotar(self, e):
        SOM.efeito("pop")
        self.contar("inimigos")
        e.vivo = False
        self.faiscas(e.cx, e.rect().centery, (250, 240, 200), 10)

    # ---------- teia ----------
    def prender(self, aranha):
        SOM.efeito("teia")
        r = self.ribbat
        r.preso = {"aranha": aranha, "prog": 0.0, "t": 0.0}
        r.vx = 0
        r.lingua_t = 0
        aranha.puxando = True

    def soltar_teia(self, mordida=False):
        r = self.ribbat
        if not r.preso:
            return
        a = r.preso["aranha"]
        a.puxando = False
        a.recarga = 3.0
        r.preso = None
        self.faiscas(r.cx, r.y + 12, TEIA, 16, 220)
        if not mordida:
            r.invuln = max(r.invuln, 0.6)
            r.vy = -300
            self.contar("teias")                     # se soltou sozinho

    # ---------- formigas em grupo ----------
    def coordenar_formigas(self, dt):
        """Quando o Ribbat sobe num lugar alto, as formigas montam uma torre e a de cima pula nele."""
        r = self.ribbat
        pe = r.y + r.H
        for t in list(self.torres):
            t["t"] += dt
            t["espera"] += dt
            base = t["membros"][0]
            desfaz = (not all(m.vivo for m in t["membros"]) or abs(r.cx - base.cx) > 110
                      or pe > base.y - 10 or t["t"] > 8 or len(t["membros"]) < 2 and t["espera"] > 2)
            if desfaz:
                for m in t["membros"]:
                    m.torre = None
                    m.nivel = 0
                    m.vy = 0
                self.torres.remove(t)
                continue
            for n, m in enumerate(t["membros"][1:], start=1):
                alvo_y = base.y - n * Formiga.ALTURA_ANDAR
                m.x += (base.x - m.x) * min(1, dt * 10)
                m.y = max(alvo_y, m.y - 150 * dt) if m.y > alvo_y else alvo_y
                m.dir = base.dir
            topo = t["membros"][-1]
            n = len(t["membros"]) - 1
            no_lugar = n > 0 and abs(topo.y - (base.y - n * Formiga.ALTURA_ANDAR)) < 1
            alcanca = topo.y - Formiga.ALCANCE_SALTO <= pe
            if no_lugar and (alcanca or t["espera"] > 1.5):
                t["membros"].pop()
                topo.torre = None
                topo.nivel = 0
                topo.vy = -Formiga.SALTO
                topo.vx = math.copysign(150, r.cx - topo.cx)
                topo.saltando = True
                t["espera"] = 0
        if not r.no_chao or r.preso:
            return
        for f in self.fase.inimigos:
            if not isinstance(f, Formiga) or f.estado != "ataque" or f.torre is not None:
                continue
            if not f.no_chao or f.saltando or abs(r.cx - f.cx) > 40 or pe > f.y - 24:
                continue
            t = next((t for t in self.torres if abs(t["membros"][0].cx - f.cx) < 50), None)
            if t is None:
                self.torres.append({"membros": [f], "t": 0.0, "espera": 0.0})
                f.torre = self.torres[-1]
            elif len(t["membros"]) < 6:
                f.nivel = len(t["membros"])
                f.torre = t
                t["membros"].append(f)
                t["espera"] = 0.0

    # ---------- regras ----------
    def fincar_bandeira(self, b):
        SOM.efeito("bandeira")
        b.ativa = True
        if b.ordem == 0:
            self.tem_lingua = True
            self.icones = [["lingua", 2.5]]
        elif b.ordem == 1:
            self.tem_investida = True
            self.icones = [["investida", 2.5]]
        else:
            self.coracoes_max = CORACOES_MAX
            self.coracoes = CORACOES_MAX
            self.icones = [["coracao", 2.5]]
        self.salvo = {"bandeiras": b.ordem + 1, "moscas": set(self.moscas_pegas)}
        for _ in range(3):
            self.faiscas(b.x + 16, b.base - 90, random.choice([(96, 196, 84), AMARELO, BRANCO]), 10, 260)

    def conferir_dano(self):
        if self.coracoes < self._coracoes_visto:
            self.sem_dano = False
        self._coracoes_visto = self.coracoes

    def conferir_conquistas(self):
        """Figurinha nova? Aparece no canto, toca um somzinho e salva."""
        novas = CQ.conferir(self.progresso)
        for n in novas:
            self.avisos_conquista.append([n, 0.0])
            SOM.efeito("bandeira")
        if novas:
            PR.salvar(self.progresso)

    def contar(self, nome):
        CQ.contar(self.progresso, nome)
        self.conferir_conquistas()

    def gravar_fantasma(self):
        r = self.ribbat
        while len(self.gravacao) <= int(self.tempo_fase * FANTASMA_HZ):
            self.gravacao.append([int(r.x), int(r.y), r.pose(), r.dir])

    def atualizar(self, dt, ent):
        self.tempo_total += dt
        self.conferir_dano()
        self.loja_tremor = max(0.0, self.loja_tremor - dt * 2)
        if self.avisos_conquista:
            self.avisos_conquista[0][1] += dt
            if self.avisos_conquista[0][1] > 3.2:
                self.avisos_conquista.pop(0)
        if self.estado == "maratona_troca":
            self.proximo_da_maratona()
            return
        if self.maratona and (self.estado == "chefe" or (self.estado == "jogando" and self.corrida is not None)):
            self.maratona["t"] += dt
        if self.estado == "jogando" and self.corrida is None:
            self.tempo_fase += dt
            self.gravar_fantasma()
        elif self.estado == "chefe" or (self.estado == "jogando" and self.corrida is not None):
            self.tempo_chefe += dt                   # na Águia, a corrida conta junto com a luta
        if self.estado in ("quadrinho", "final"):
            self.hq_alfa = min(1.0, self.hq_alfa + dt * 2.5)
        self.menu_tremor = max(0.0, self.menu_tremor - dt * 2)
        self.menu_anda = min(1.0, getattr(self, "menu_anda", 1.0) + dt * 3.5)   # o Ribbat pulando no mapa
        if self.estado == "chefe":
            self.chefe_mod.atualizar(self, dt, ent)
            if self.estado == "chefe":
                self.atualizar_mosquitos(dt)
            return
        if self.estado != "jogando":
            return
        r, fase = self.ribbat, self.fase
        if self.corrida is not None:
            self.corrida["t"] += dt
            if self.corrida["t"] < 0:
                ent = Entrada()                       # luzinhas vermelhas: ainda não pode correr
            elif AG.progresso_aguia(self) >= 1:
                self.estado = "perdeu_corrida"        # a águia chegou primeiro...
                return
        pe_antes = r.y + r.H
        r.atualizar(dt, ent, self)

        self.atualizar_vitorias(dt)
        pr = r.rect()
        lingua = r.rect_lingua()

        # guarda o último chão firme (terra dos dois lados dos pés) pra voltar se cair
        if r.no_chao and not r.preso:
            pe = int((r.y + r.H + 2) // TILE)
            if all(fase.solidos.get((int(x // TILE), pe)) == "#" for x in (r.x - 24, r.x + r.W + 24)):
                self.ultimo_seguro = (r.x, r.y)

        for m in fase.moscas:
            m.t += dt
        pegas = [m for m in fase.moscas if pr.colliderect(m.rect()) or (lingua and lingua.colliderect(m.rect()))]
        for m in pegas:
            SOM.efeito("mosca")
            self.moscas_pegas.add(m.id)
            self.faiscas(m.x, m.y, AMARELO, 6, 120)
        if pegas:
            fase.moscas = [m for m in fase.moscas if m.id not in self.moscas_pegas]

        for mao in fase.maos:
            mao.atualizar(dt, self)
            if mao.batendo() and pr.colliderect(mao.rect()):
                r.machucar(self, mao.x)
                if self.estado != "jogando":
                    return
        for h in fase.buracos:
            if not h.vivo:
                continue
            h.atualizar(dt, self)
            if r.dash_t > 0 and pr.colliderect(h.rect()):
                h.vivo = False                       # tampou o buraco!
                self.faiscas(h.x, h.chao - 6, (150, 110, 76), 20, 260)
                self.tremer(6)
        self.coordenar_formigas(dt)
        for e in list(fase.inimigos):
            e.atualizar(dt, fase, self)
            if not e.vivo:
                continue
            if isinstance(e, Aranha) and e.puxando:
                continue  # essa aí tá puxando o fio, a mordida é tratada abaixo
            er = e.rect()
            if lingua and lingua.colliderect(er):
                self.derrotar(e)
            elif pr.colliderect(er):
                if r.dash_t > 0:
                    self.derrotar(e)
                elif r.vy > 0 and pe_antes <= er.top + 10 and not r.preso:
                    self.derrotar(e)  # pisou em cima!
                    r.vy = -QUIQUE * (1.4 if ent.pulo else 1.0)
                    r.pulando = ent.pulo
                    r.dash_pronto = True
                else:
                    r.machucar(self, e.cx)
            if self.estado != "jogando":
                return
        fase.inimigos = [e for e in fase.inimigos if e.vivo]

        for b in self.bolas:
            b.atualizar(dt, fase)
            if not b.viva:
                continue
            br = b.rect()
            if lingua and lingua.colliderect(br):
                b.viva = False
                self.faiscas(b.x, b.y, TEIA, 8)
            elif pr.colliderect(br):
                b.viva = False
                if r.dash_t > 0 or r.invuln > 0 or r.preso:
                    self.faiscas(b.x, b.y, TEIA, 8)
                else:
                    self.prender(b.dona)
        self.bolas = [b for b in self.bolas if b.viva]

        if r.preso:
            a = r.preso["aranha"]
            if math.hypot(a.x - r.cx, a.y - (r.y + 12)) < 26:
                self.soltar_teia(mordida=True)
                r.machucar(self, a.x)
                if self.estado != "jogando":
                    return

        for s in fase.espinhos:
            if pr.colliderect(s):
                r.machucar(self, r.cx + r.dir)
                if self.estado != "jogando":
                    return

        afogou = any(pr.colliderect(a.move(0, AFOGA)) for a in fase.agua)
        if afogou or r.y > fase.alt * TILE + 60:
            self.cair(afogou)
            if self.estado != "jogando":
                return

        for b in fase.checkpoints:
            if b.ativa:
                b.subida = min(1.0, b.subida + dt * 1.5)
            elif r.cx >= b.x:
                self.fincar_bandeira(b)
                self.ultimo_seguro = (r.x, r.y)

        if fase.toca and r.cx >= fase.toca.x - 10 and self.corrida is not None and self.maratona:
            self.estado = "maratona_fim"             # os 5 chefões seguidos!
            SOM.efeito("vitoria")
            t = self.maratona["t"]
            novo = self.progresso.get("maratona") is None or t < self.progresso["maratona"]
            if novo:
                self.progresso["maratona"] = round(t, 2)
                PR.salvar(self.progresso)
            self.ultimo_tempo = (t, novo, None, False)
            self.conferir_conquistas()
            return
        if fase.toca and r.cx >= fase.toca.x - 10 and self.corrida is not None:
            self.estado = "final"                    # CHEGOU NO PERGAMINHO PRIMEIRO! fim do jogo
            SOM.efeito("vitoria")
            self.hq_paineis, self.hq_alfa = 1, 0.0
            reg = PR.fase(self.progresso, self.fase_atual["id"])
            reg["zerada"] = reg["chefe"] = True
            self.conferir_dano()
            reg["sem_dano_chefe"] = reg.get("sem_dano_chefe") or self.sem_dano
            if self.orelhas_coelho:
                self.progresso["venceu_de_coelho"] = True
            self.ultimo_tempo = (self.tempo_chefe, PR.recorde(self.progresso, self.fase_atual["id"], "tempo_chefe",
                                                              self.tempo_chefe), "tempo_chefe", self.sem_dano)
            PR.salvar(self.progresso)
            self.conferir_conquistas()
            return
        if fase.toca and r.cx >= fase.toca.x - 10:
            self.estado = "fim"
            SOM.efeito("vitoria")
            reg = PR.fase(self.progresso, self.fase_atual["id"])
            reg["zerada"] = True
            reg["moscas"] = max(reg["moscas"], len(self.moscas_pegas))
            self.progresso["carteira"] = self.progresso.get("carteira", 0) + len(self.moscas_pegas)
            self.conferir_dano()
            reg["sem_dano"] = reg.get("sem_dano") or self.sem_dano
            novo = PR.recorde(self.progresso, self.fase_atual["id"], "tempo", self.tempo_fase)
            self.ultimo_tempo = (self.tempo_fase, novo, "tempo", self.sem_dano)
            if novo:                                 # bateu o recorde: esse caminho vira o novo fantasma
                if self.fantasma:
                    self.progresso["bateu_fantasma"] = True
                self.gravar_fantasma()
                PR.salvar_fantasma(self.fase_atual["id"], self.gravacao)
            PR.salvar(self.progresso)
            self.conferir_conquistas()

        self.efeitos(dt)
        alvo = r.cx - LARGURA * 0.4 + r.dir * 40
        self.cam_x += (alvo - self.cam_x) * min(1, dt * 6)
        self.cam_x = max(0, min(self.cam_x, fase.larg * TILE - LARGURA))
        alvo_y = r.y - ALTURA * 0.55                    # a câmera também sobe (Montanha)
        self.cam_y += (alvo_y - self.cam_y) * min(1, dt * 5)
        self.cam_y = max(0, min(self.cam_y, fase.alt * TILE - ALTURA))

    def efeitos(self, dt):
        for p in self.particulas:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 600 * dt
            p[4] -= dt
        self.particulas = [p for p in self.particulas if p[4] > 0]
        for i in self.icones:
            i[1] -= dt
        self.icones = [i for i in self.icones if i[1] > 0]
        self.tremor = max(0, self.tremor - dt * 30)

    def atualizar_mosquitos(self, dt):
        """Mosquito de cura: aparece de vez em quando (mais vezes se tiver pouca vida)."""
        r = self.ribbat
        self.cd_mosquito -= dt * (1.6 if self.coracoes <= 2 else 1.0)
        if self.cd_mosquito <= 0 and not self.mosquitos:
            self.cd_mosquito = random.uniform(11, 16)
            faixa = getattr(self.boss, "mosquito_y", getattr(self.chefe_mod, "MOSQUITO_Y", (250, 380)))
            self.mosquitos.append(Mosquito(random.choice((-1, 1)), random.uniform(*faixa)))
        pr, lingua = r.rect(), r.rect_lingua()
        for m in self.mosquitos:
            m.atualizar(dt)
            if m.vivo and (pr.colliderect(m.rect()) or (lingua and lingua.colliderect(m.rect()))):
                m.vivo = False
                self.contar("mosquitos")
                if self.coracoes < self.coracoes_max:
                    self.coracoes += 1
                    SOM.efeito("cura")
                    self.icones = [["coracao", 1.6]]
                self.faiscas(m.x, m.y, (255, 120, 150), 14, 180)
        self.mosquitos = [m for m in self.mosquitos if m.vivo]

    # ---------- chefão ----------
    def iniciar_chefe(self):
        self.no_chefe = True
        self.tempo_chefe = 0.0
        self.sem_dano = True
        # revanche: se já venceu esse chefe antes, o Ribbat entra de orelhinhas de coelho
        self.orelhas_coelho = PR.fase(self.progresso, self.fase_atual["id"])["chefe"]
        self.chefe_mod = CHEFES[self.fase_atual["chefe"]]
        self.fase = Fase(self.chefe_mod.ARENA)
        self.ribbat = Ribbat(*self.fase.inicio)
        self.coracoes = self.coracoes_max
        self.boss = self.chefe_mod.criar()
        if getattr(self, "chefe_meio", None) == self.fase_atual["id"] and hasattr(self.boss, "ir_pra_sala"):
            self.boss.ir_pra_sala(self)                # já tinha chegado na sala: recomeça de lá
        self.particulas, self.bolas, self.torres, self.icones = [], [], [], []
        self.cam_x = 0
        self.tremor = 0.0
        self.recarga_lingua = self.chefe_mod.RECARGA_LINGUA
        self.recarga_investida = self.chefe_mod.RECARGA_INVESTIDA
        self.estado = "chefe"
        self._coracoes_visto = self.coracoes
        self.mosquitos = []
        self.cd_mosquito = 8.0

    # ---------- menu ----------
    def comecar_fase(self):
        self.dados_fase = self.fase_atual["dados"]
        self.novo_jogo()
        self.tempo_fase = 0.0
        self.sem_dano = True
        self._coracoes_visto = self.coracoes
        self.gravacao = []
        self.fantasma = PR.carregar_fantasma(self.fase_atual["id"])
        if PR.fase(self.progresso, self.fase_atual["id"])["zerada"] or not self.fase_atual["historia"]:
            self.estado = "jogando"          # já viu a história (ou a fase não tem): vai direto
        else:
            self.estado = "quadrinho"
            self.hq_paineis = 1
            self.hq_alfa = 0.0

    def comecar_chefe(self):
        """Pular direto pro chefão: chega com tudo que as 3 bandeiras dão."""
        self.chefe_meio = None
        self.dados_fase = self.fase_atual["dados"]
        self.novo_jogo()
        self.tem_lingua = self.tem_investida = True
        self.coracoes_max = CORACOES_MAX
        self.iniciar_chefe()

    def comecar_corrida(self):
        """A Águia jogou o Ribbat pro alto: agora é corrida até o pergaminho (com tudo liberado)."""
        self.dados_fase = fases.FASE_CORRIDA
        self.tem_lingua = self.tem_investida = True
        self.coracoes_max = CORACOES_MAX
        self.salvo = {"bandeiras": 0, "moscas": set()}
        if self.maratona:
            self.maratona["c"] = self.coracoes       # na maratona os corações não enchem
        self.carregar()
        self.estado = "jogando"

    def comecar_maratona(self):
        """Os 5 chefões seguidos, um relógio só. Os corações passam de uma luta pra outra."""
        self.maratona = {"i": 0, "t": 0.0, "c": CORACOES_MAX}
        self.fase_atual = MENU.FASES[0]
        self.comecar_chefe()

    def proximo_da_maratona(self):
        c = self.coracoes
        self.maratona["i"] += 1
        self.fase_atual = MENU.FASES[self.maratona["i"]]
        self.chefe_meio = None
        self.iniciar_chefe()
        self.coracoes = self._coracoes_visto = c

    def venceu_chefe(self):
        SOM.efeito("vitoria")
        if self.maratona:                            # maratona: vai direto pro próximo chefão (no próximo quadro)
            self.estado = "maratona_troca"
            return
        reg = PR.fase(self.progresso, self.fase_atual["id"])
        reg["chefe"] = True
        self.conferir_dano()
        reg["sem_dano_chefe"] = reg.get("sem_dano_chefe") or self.sem_dano
        if self.orelhas_coelho:
            self.progresso["venceu_de_coelho"] = True
        self.ultimo_tempo = (self.tempo_chefe, PR.recorde(self.progresso, self.fase_atual["id"], "tempo_chefe",
                                                          self.tempo_chefe), "tempo_chefe", self.sem_dano)
        self.conferir_conquistas()
        PR.salvar(self.progresso)
        self.estado = "vitoria"

    def ir_pro_menu(self):
        self.maratona = None
        PR.salvar(self.progresso)                    # os contadores do álbum também
        self.dados_fase = self.fase_atual["dados"]
        self.novo_jogo()
        self.estado = "menu"

    def comprar_ou_vestir(self):
        nome, preco = CP.CHAPEUS[self.loja_i]
        p = self.progresso
        if nome in p["chapeus"]:
            p["chapeu"] = nome                       # já tem: veste
        elif p["carteira"] >= preco:
            p["carteira"] -= preco                   # compra e já veste
            p["chapeus"].append(nome)
            p["chapeu"] = nome
            SOM.efeito("cura")
            self.conferir_conquistas()
        else:
            self.loja_tremor = 0.4                   # não tem mosca suficiente
            return
        PR.salvar(p)

    def tecla(self, k, ent):
        """Trata um aperto de tecla. Devolve 'sair' pra fechar o jogo."""
        confirma = k in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)
        if self.estado == "titulo":
            if confirma:
                self.estado = "menu"
            elif k == pygame.K_ESCAPE:
                return "sair"
            elif k in (pygame.K_F2, pygame.K_F3, pygame.K_F4, pygame.K_F5, pygame.K_F6, pygame.K_F7):   # atalhos
                self.fase_atual = MENU.FASES[{pygame.K_F2: 0, pygame.K_F3: 1, pygame.K_F4: 2, pygame.K_F5: 3,
                                              pygame.K_F6: 4, pygame.K_F7: 5}[k]]       # F2 Viúva ... F6 Águia, F7 o Vô
                self.comecar_chefe()
        elif self.estado == "menu":
            if self.menu_j == -1 and k in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                self.menu_k = 1 if k in (pygame.K_RIGHT, pygame.K_d) else 0     # lá em cima: maratona ou álbum
            elif k in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):    # anda pelo caminho do mapa
                caminho = MENU.alcance_mapa(self)
                pos = caminho.index(self.menu_i) if self.menu_i in caminho else 0
                pos = max(0, min(len(caminho) - 1, pos + (1 if k in (pygame.K_RIGHT, pygame.K_d) else -1)))
                if caminho[pos] != self.menu_i:
                    self.menu_de, self.menu_i, self.menu_anda = self.menu_i, caminho[pos], 0.0
            elif k in (pygame.K_UP, pygame.K_w):
                self.menu_j = max(-1, self.menu_j - 1)          # lá em cima: a maratona
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.menu_j = min(2, self.menu_j + 1)           # lá embaixo: a loja
            if MENU.FASES[self.menu_i].get("so_chefe") and self.menu_j == 0:
                self.menu_j = -1 if k in (pygame.K_UP, pygame.K_w) else 1    # a casa do Vô só tem o chefão
            elif k == pygame.K_ESCAPE:
                self.estado = "titulo"
            elif confirma and self.menu_j == -1 and self.menu_k == 1:
                self.estado = "album"
            elif confirma and self.menu_j == -1:
                if MENU.maratona_liberada(self):
                    self.comecar_maratona()
                else:
                    self.menu_tremor = 0.4
            elif confirma and self.menu_j == 2:
                self.estado = "loja"
                nomes = [n for n, _ in CP.CHAPEUS]
                self.loja_i = nomes.index(self.progresso.get("chapeu", "nenhum"))
            elif confirma:
                if not MENU.liberado(self, self.menu_i, self.menu_j):
                    self.menu_tremor = 0.4           # trancado: a carta treme
                else:
                    self.fase_atual = MENU.FASES[self.menu_i]
                    if self.menu_j == 0:
                        self.comecar_fase()
                    else:
                        self.comecar_chefe()
        elif self.estado == "quadrinho":
            if k == pygame.K_ESCAPE:
                self.estado = "jogando"
            elif confirma:
                if self.hq_alfa < 1:
                    self.hq_alfa = 1.0
                elif self.hq_paineis < len(HQ.PAINEIS_INTRO):
                    self.hq_paineis += 1
                    self.hq_alfa = 0.0
                else:
                    self.estado = "jogando"
        elif self.estado in ("jogando", "chefe"):
            if k in TECLAS_MASH:
                ent.mash += 1
            if k in TECLAS_PULO:
                ent.pulo_apertou = True
            elif k == pygame.K_e:
                ent.lingua = True
            elif k == pygame.K_q:
                ent.investida = True
            elif k == pygame.K_g:
                self.ver_fantasma = not self.ver_fantasma
            elif k in (pygame.K_ESCAPE, pygame.K_p):
                self.voltar_para = self.estado
                self.estado = "pausa"
        elif self.estado == "pausa":
            if k in (pygame.K_ESCAPE, pygame.K_p, pygame.K_RETURN):
                self.estado = self.voltar_para
            elif k == pygame.K_m:
                self.ir_pro_menu()
        elif self.estado == "gameover":
            if confirma:
                if self.maratona:
                    self.comecar_maratona()      # maratona: perdeu, começa tudo de novo
                elif self.no_chefe:
                    self.iniciar_chefe()   # igual Cuphead: perdeu, recomeça a luta
                else:
                    self.carregar()
                    self.estado = "jogando"
            elif k == pygame.K_ESCAPE:
                self.ir_pro_menu()
        elif self.estado == "fim":
            if confirma and self.fase_atual["chefe"]:
                self.iniciar_chefe()
            elif confirma:
                self.ir_pro_menu()       # chefão dessa fase ainda vai ser feito
            elif k == pygame.K_ESCAPE:
                self.ir_pro_menu()
        elif self.estado == "vitoria":
            if confirma or k == pygame.K_ESCAPE:
                self.ir_pro_menu()
        elif self.estado == "loja":
            if k in (pygame.K_LEFT, pygame.K_a):
                self.loja_i = max(0, self.loja_i - 1)
            elif k in (pygame.K_RIGHT, pygame.K_d):
                self.loja_i = min(len(CP.CHAPEUS) - 1, self.loja_i + 1)
            elif confirma:
                self.comprar_ou_vestir()
            elif k == pygame.K_ESCAPE:
                self.estado = "menu"
        elif self.estado == "maratona_fim":
            if confirma or k == pygame.K_ESCAPE:
                self.ir_pro_menu()
        elif self.estado == "album":
            if confirma or k == pygame.K_ESCAPE:
                self.estado = "menu"
        elif self.estado == "perdeu_corrida":
            if confirma:
                self.carregar()                      # corrida de novo (a luta já foi vencida)
                self.estado = "jogando"
            elif k == pygame.K_ESCAPE:
                self.ir_pro_menu()
        elif self.estado == "final":
            if confirma:
                if self.hq_alfa < 1:
                    self.hq_alfa = 1.0
                elif self.hq_paineis < len(HQ.PAINEIS_FINAL):
                    self.hq_paineis += 1
                    self.hq_alfa = 0.0
                else:
                    self.ir_pro_menu()
            elif k == pygame.K_ESCAPE:
                self.ir_pro_menu()
        return None

    # ---------- desenho ----------
    def desenhar(self, tela):
        t = self.tempo_total
        if self.estado == "titulo":
            self.desenhar_titulo(tela)
        elif self.estado == "menu":
            MENU.desenhar(self, tela)
        elif self.estado == "loja":
            MENU.desenhar_loja(self, tela)
        elif self.estado == "maratona_fim":
            MENU.desenhar_maratona_fim(self, tela)
        elif self.estado == "album":
            CQ.desenhar_album(self, tela)
        elif self.estado == "quadrinho":
            HQ.desenhar_pagina(tela, HQ.PAINEIS_INTRO, self.hq_paineis, self.hq_alfa, t, self.fonte_tecla)
        elif self.estado == "final":
            HQ.desenhar_pagina(tela, HQ.PAINEIS_FINAL, self.hq_paineis, self.hq_alfa, t, self.fonte_tecla)
            x = self.desenhar_tempo_fim(tela, ALTURA - 30)
            D.icone_trofeu(tela, x + 30, ALTURA - 30)
            D.texto(tela, self.fonte, D.fmt_tempo(PR.tempo_total(self.progresso)), x + 48, ALTURA - 44)
        elif self.estado == "fim":
            painel = {"fase1": HQ.painel_toca, "fase2": HQ.painel_toca_besouro, "fase3": HQ.painel_camara_real,
                      "fase4": HQ.painel_portinha, "fase5": HQ.painel_cume}[self.fase_atual["id"]]
            HQ.desenhar_painel_unico(tela, painel, t, self.fonte_tecla)
            self.desenhar_tempo_fim(tela, ALTURA - 26)
        elif self.estado == "vitoria":
            painel = {"viuva": HQ.painel_vitoria, "besouro": HQ.painel_vitoria_besouro,
                      "rainha": HQ.painel_vitoria_rainha, "gato": HQ.painel_vitoria_gato,
                      "vovo": HQ.painel_vitoria_vovo}[self.fase_atual["chefe"]]
            HQ.desenhar_painel_unico(tela, painel, t, self.fonte_tecla)
            self.desenhar_tempo_fim(tela, ALTURA - 26)
        else:
            if self.no_chefe:
                self.chefe_mod.desenhar(self, tela)
            else:
                self.desenhar_mundo(tela)
                if self.corrida is not None:
                    AG.desenhar_corrida(self, tela)
            self.desenhar_hud(tela)
            if self.estado == "perdeu_corrida":
                AG.desenhar_perdeu(self, tela)
            if self.estado == "pausa":
                self.escurecer(tela)
                for dx in (-22, 10):
                    pygame.draw.rect(tela, BRANCO, R(LARGURA / 2 + dx, ALTURA / 2 - 50, 14, 70), border_radius=4)
                D.tecla(tela, self.fonte_tecla, LARGURA / 2 - 60, ALTURA / 2 + 50, "Esc", 44)
                pygame.draw.polygon(tela, BRANCO, [(LARGURA / 2 - 6, ALTURA / 2 + 52), (LARGURA / 2 - 6, ALTURA / 2 + 72),
                                                   (LARGURA / 2 + 10, ALTURA / 2 + 62)])          # continuar
                D.tecla(tela, self.fonte_tecla, LARGURA / 2 + 30, ALTURA / 2 + 50, "M")
                for i in range(2):                                                                # menu (cartinhas)
                    pygame.draw.rect(tela, BRANCO, R(LARGURA / 2 + 64 + i * 14, ALTURA / 2 + 52, 11, 18), 2,
                                     border_radius=2)
            elif self.estado == "gameover":
                self.escurecer(tela)
                prensado = getattr(self.ribbat, "prensado", False)      # o tatu-bola passou por cima...
                D.desenhar_sapo(tela, LARGURA / 2, ALTURA / 2 + 30, 1, "tonto", 0.45 if prensado else 1.0, escala=2.4)
                for i in range(3):
                    a = t * 3 + i * math.tau / 3
                    x, y = LARGURA / 2 + 20 + math.cos(a) * 46, ALTURA / 2 - 70 + math.sin(a) * 12
                    pygame.draw.polygon(tela, AMARELO, estrela(x, y, 9))
                D.tecla(tela, self.fonte_tecla, LARGURA / 2 - 20, ALTURA / 2 + 70, "enter", 40)
        CQ.desenhar_aviso(self, tela)                        # figurinha nova, por cima de tudo

    def desenhar_tempo_fim(self, tela, y):
        """Embaixo do quadrinho: relógio + o tempo que fez (estrela piscando se foi recorde). Devolve onde parou."""
        if not self.ultimo_tempo:
            return 20
        tempo, novo, chave, sem_dano = self.ultimo_tempo
        D.icone_relogio(tela, 40, y, 11)
        D.texto(tela, self.fonte, D.fmt_tempo(tempo), 58, y - 14)
        x = 58 + self.fonte.size(D.fmt_tempo(tempo))[0] + 18
        if novo:
            D.estrelinha(tela, x, y, 11 + 2 * abs(math.sin(self.tempo_total * 5)))
            x += 22
        ident = self.fase_atual["id"]
        x += 10
        MD.desenhar(tela, x, y + 3, MD.medalha(ident, chave, tempo), 11)
        x += 28
        if sem_dano:
            MD.desenhar_coracao(tela, x, y - 2, 10)
            x += 28
        prox = MD.proxima(ident, chave, tempo)
        if prox:                                     # a próxima medalha (apagada) e o tempo que precisa
            x += 14
            MD.desenhar(tela, x, y + 3, prox[0], 9, apagada=True)
            D.texto(tela, self.fonte_tecla, D.fmt_tempo(prox[1]), x + 16, y - 7)
            x += 20 + self.fonte_tecla.size(D.fmt_tempo(prox[1]))[0]
        return x

    def escurecer(self, tela):
        escuro = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        escuro.fill((0, 0, 0, 150))
        tela.blit(escuro, (0, 0))

    def desenhar_mundo(self, tela):
        fase, r, t = self.fase, self.ribbat, self.tempo_total
        tx = random.uniform(-self.tremor, self.tremor) if self.tremor > 0 else 0
        ty = random.uniform(-self.tremor, self.tremor) if self.tremor > 0 else 0
        ox = int(self.cam_x - tx)
        oy = int(getattr(self, "cam_y", 0) - ty)
        lama = fase.tema == "lamacal"
        form = fase.tema == "formigueiro"
        quintal = fase.tema == "quintal"
        mont = fase.tema == "montanha"
        if mont:
            MT.desenhar_fundo(tela, self.fundo_montanha, self.cam_x, self.cam_y, fase.alt, t)
        elif quintal:
            Q.desenhar_fundo(tela, self.fundo_quintal, self.cam_x, t)
            for mao in fase.maos:
                if -500 < mao.x0 - ox < LARGURA + 500:
                    Q.desenhar_moco(tela, mao, ox, oy)
        elif lama:
            L.desenhar_fundo(tela, self.fundo_lama, self.cam_x, t)
        elif form:
            FM.desenhar_fundo(tela, self.fundo_form, self.cam_x, t)
        else:
            P.desenhar_fundo(tela, self.fundo, self.cam_x, t)

        if fase.toca:
            if fase.pergaminho:
                AG.desenhar_chegada(tela, fase.toca.x - ox, fase.toca.base - oy, t)
            elif mont:
                MT.desenhar_cume(tela, fase.toca.x - ox, fase.toca.base - oy, t)
            elif quintal:
                Q.desenhar_porta(tela, fase.toca.x - ox, fase.toca.base - oy, t)
            elif lama:
                L.desenhar_toca_besouro(tela, fase.toca.x - ox, fase.toca.base - oy, t)
            elif form:
                FM.desenhar_camara_real(tela, fase.toca.x - ox, fase.toca.base - oy, t)
            else:
                D.desenhar_toca(tela, fase.toca.x - ox, fase.toca.base - oy, t)
        tiles = self.tiles_lama if lama else self.tiles_form if form else self.tiles_quintal if quintal else \
            self.tiles_montanha if mont else self.tiles

        for cav in fase.cavernas if not (form or quintal or mont) else []:
            D.desenhar_caverna(tela, cav, ox, oy)
        c0 = max(0, ox // TILE - 1)
        c1 = min(fase.larg, (ox + LARGURA) // TILE + 2)
        for cx in range(c0, c1) if not (form or quintal or mont) else []:   # taboas nascendo do chão
            for cy in range(fase.alt):
                if fase.solidos.get((cx, cy)) == "#" and (cx, cy - 1) not in fase.solidos:
                    if (cx * 37 + cy * 11) % 5 == 0:
                        P.desenhar_taboas(tela, cx * TILE + 16 - ox, cy * TILE + 6 - oy, t, cx)
                    break
        linha_neve = fase.alt if fase.neve else fase.alt * 0.55   # na montanha, daqui pra cima o chão tem neve
        for cy in range(max(0, oy // TILE - 1), min(fase.alt, (oy + ALTURA) // TILE + 2)):
            for cx in range(c0, c1):
                ch = fase.solidos.get((cx, cy))
                if ch == "#":
                    if fase.solidos.get((cx, cy - 1), "X") == "X":
                        img = tiles["neve"] if mont and cy < linha_neve else tiles["grama"]
                    else:
                        img = tiles["terra"][(cx * 7 + cy * 13) % 3]
                elif ch == "K":
                    img = tiles.get("caixa", tiles["terra"][0])
                elif ch == "r" and quintal:
                    img = tiles["boia"]
                elif ch in ("=", "r"):
                    img = tiles["madeira"]
                else:
                    continue
                tela.blit(img, (cx * TILE - ox, cy * TILE - oy))
        for p in fase.pedras:
            (FM.desenhar_torrao if form else Q.desenhar_vaso if quintal else D.desenhar_pedra)(tela, p.rect.move(-ox, -oy), p.semente)
            if self.tem_investida and abs(p.rect.centerx - r.cx) < 180 and int(t * 3) % 2 == 0:
                D.tecla(tela, self.fonte_tecla, p.rect.centerx - 13 - ox, p.rect.top - 40 - oy, "Q")
        for w in fase.teias_chao:
            tela.blit(self.tiles["teia"], (w.x - ox, w.y - oy))
        for u in fase.lama_chao:
            if -TILE < u.x - ox < LARGURA:
                (FM.desenhar_melado if form else L.desenhar_lama_grudenta)(tela, u.move(-ox, -oy), t, u.x // TILE)
        for fl in fase.flores:
            if -200 < fl.x0 - ox < LARGURA + 60:
                Q.desenhar_flores(tela, fl, ox, oy, t)
        for h in fase.buracos:
            if -60 < h.x - ox < LARGURA + 60:
                if h.vivo:
                    FM.desenhar_buraco(tela, h.x - ox, h.chao - oy, t)
                else:
                    FM.desenhar_tampado(tela, h.x - ox, h.chao - oy)
        for s in fase.espinhos:
            if mont:
                MT.desenhar_espinho(tela, s.x - ox - 4, s.bottom - oy, s.y < linha_neve * TILE)
            else:
                D.desenhar_espinhos(tela, s.x - ox - 4, s.bottom - oy)
        for b in fase.checkpoints:
            D.desenhar_bandeira(tela, b.x - ox, b.base - oy, b, t)

        for m in fase.moscas:
            mr = m.rect()
            D.desenhar_mosca(tela, mr.centerx - ox, mr.centery - oy, m.t)
        for e in fase.inimigos:
            if isinstance(e, Passaro):
                if -80 < e.x - ox < LARGURA + 80:
                    MT.desenhar_gaviao(tela, e, ox, oy, t)
            elif isinstance(e, Abelha):
                if -60 < e.x - ox < LARGURA + 60:
                    Q.desenhar_abelha(tela, e, ox, oy, t)
            elif isinstance(e, FormigaGuerreira):
                if -60 < e.x - ox < LARGURA + 60:
                    FM.desenhar_guerreira(tela, e, ox, oy, t)
            elif isinstance(e, PeixeLama):
                if -60 < e.x - ox < LARGURA + 60:
                    L.desenhar_peixe_lama(tela, e, ox, oy, t)
            elif isinstance(e, Peixe):
                if e.aviso:
                    P.desenhar_aviso_peixe(tela, e.x0 - ox, e.agua - oy, t)
                if e.pulando:
                    P.desenhar_peixe(tela, e.x - ox, e.y - oy, e.vx, e.vy)
            elif isinstance(e, Formiga):
                D.desenhar_formiga(tela, e.x - ox, e.y - oy, e.W, e.H, e.dir, e.anim, parada=e.nivel > 0)
                if e.estado == "alerta":
                    D.desenhar_alerta(tela, e.cx - ox, e.y - 16 - oy)
            else:
                D.desenhar_aranha(tela, e.x - ox, e.y - oy, e.topo - oy, e.t, e.mira)
        for b in self.bolas:
            D.desenhar_bola_teia(tela, b.x - ox, b.y - oy, b.t)
        for a in fase.agua:
            ar = a.move(-ox, -oy).clip(R(0, 0, LARGURA, ALTURA))
            if ar.width > 0:
                (L.desenhar_poca if lama else Q.desenhar_piscina if quintal else P.desenhar_agua)(tela, ar, t)
        for v in fase.vitorias:
            P.desenhar_vitoria(tela, v.rect.move(-ox, -oy), v.peso, v.afundada, v.AGUENTA, t)

        self.desenhar_fantasma(tela, ox, oy)
        self.desenhar_ribbat(tela, ox, oy)
        for mao in fase.maos:
            Q.desenhar_mao(tela, mao, ox, oy, t, mao.superficie(fase, mao.x))
        for i, (vx, vy, fase_v) in enumerate(self.vagalumes if not (lama or quintal or mont) else []):
            x = (vx - self.cam_x * 0.3 + math.sin(t * 0.5 + fase_v) * 30) % LARGURA
            P.desenhar_vagalume(tela, x, vy + math.sin(t * 0.8 + fase_v * 2) * 14, t + fase_v)
        self.desenhar_efeitos(tela, ox, oy)

    def mostrando_fantasma(self):
        return bool(self.fantasma) and self.ver_fantasma and not self.no_chefe and self.corrida is None

    def desenhar_fantasma(self, tela, ox, oy):
        """O sapo fantasma: refaz o caminho do teu recorde, transparente e azulado."""
        if not self.mostrando_fantasma():
            return
        i = int(self.tempo_fase * FANTASMA_HZ)
        if i >= len(self.fantasma):
            return
        x, y, pose, d = self.fantasma[i]
        chave = (pose, d)
        if chave not in self._fantasma_img:
            img = D.sprite_sapo(pose, d, 0.85).copy()
            img.fill((60, 70, 120), special_flags=pygame.BLEND_RGB_ADD)
            img.set_alpha(110)
            self._fantasma_img[chave] = img
        img = self._fantasma_img[chave]
        w, h = img.get_size()
        fx = (46 / 80 if d > 0 else 34 / 80) * w
        tela.blit(img, (x + Ribbat.W / 2 - fx - ox, y + Ribbat.H - 50 / 52 * h - oy))

    def desenhar_ribbat(self, tela, ox, oy):
        r, t = self.ribbat, self.tempo_total
        for x, y, v in r.rastro:
            fantasma = D.sprite_sapo("investida", r.dir, 0.85).copy()
            fantasma.set_alpha(int(255 * v / 0.18 * 0.45))
            w, h = fantasma.get_size()
            fx = (46 / 80 if r.dir > 0 else 34 / 80) * w
            tela.blit(fantasma, (x + r.W / 2 - fx - ox, y + r.H - 50 / 52 * h - oy))
        ext = r.lingua_ext()
        if ext > 2:
            bx, by = r.boca()
            pts = (bx - ox, by - oy), (bx + r.dir * ext - ox, by - oy)
            pygame.draw.line(tela, (190, 60, 90), *pts, 7)
            pygame.draw.line(tela, (240, 110, 140), *pts, 4)
            pygame.draw.circle(tela, (240, 110, 140), (int(pts[1][0]), int(pts[1][1])), 6)
        if r.preso:
            a = r.preso["aranha"]
            fx, fy = r.preso.get("fio", (a.x, a.y + 10))
            pygame.draw.line(tela, TEIA, (fx - ox, fy - oy), (r.cx - ox, r.y + 8 - oy), 2)
        piscando = r.invuln > 0 and int(r.invuln * 14) % 2 == 0
        if not piscando:
            onda = int(t * 8) % 4
            D.desenhar_sapo(tela, r.cx - ox, r.y + r.H - oy, r.dir, r.pose(), r.squash, onda, 0.85,
                            orelhas=self.orelhas_coelho, chapeu=self.progresso.get("chapeu"))
        if r.preso:
            p = r.preso
            D.desenhar_casulo(tela, r.rect().move(-ox, -oy), p["prog"] * TEIA_ESCAPE / p.get("precisa", TEIA_ESCAPE), t)

    def desenhar_efeitos(self, tela, ox, oy):
        r = self.ribbat
        for m in getattr(self, "mosquitos", []) if self.no_chefe else []:
            D.desenhar_mosquito(tela, m.x - ox, m.y - oy, m.t)
        for p in self.particulas:
            tam = max(1, int(p[7] * p[4] / p[5]))
            pygame.draw.circle(tela, p[6], (int(p[0] - ox), int(p[1] - oy)), tam)

        # ícone da habilidade nova subindo em cima do Ribbat
        for tipo, tempo in self.icones:
            sobe = (2.5 - tempo) * 14
            x, y = r.cx - ox, r.y - 40 - sobe - oy
            pygame.draw.circle(tela, PRETO, (int(x), int(y)), 25)
            pygame.draw.circle(tela, (40, 80, 50), (int(x), int(y)), 23)
            if tipo == "lingua":
                D.icone_lingua(tela, x - 12, y + 2, 1.0)
                D.tecla(tela, self.fonte_tecla, x + 26, y - 12, "E")
            elif tipo == "investida":
                D.icone_investida(tela, x - 2, y, 1.0)
                D.tecla(tela, self.fonte_tecla, x + 26, y - 12, "Q")
            else:
                D.desenhar_coracao(tela, int(x - 12), int(y - 11), 24, True)

    def desenhar_hud(self, tela):
        for i in range(self.coracoes_max):
            D.desenhar_coracao(tela, 16 + i * 34, 14, 28, i < self.coracoes)
        rel = self.tempo_chefe if (self.no_chefe or self.corrida is not None) else self.tempo_fase
        if self.maratona:
            D.icone_trofeu(tela, 28, 64, 0.9)
            D.texto(tela, self.fonte, D.fmt_tempo(self.maratona["t"]), 44, 49)
            for i in range(5):                       # quais chefões já foram
                feito = i < self.maratona["i"]
                pygame.draw.circle(tela, PRETO, (24 + i * 18, 92), 7)
                pygame.draw.circle(tela, AMARELO if feito else (90, 90, 96) if i > self.maratona["i"] else BRANCO,
                                   (24 + i * 18, 92), 5)
        else:
            D.icone_relogio(tela, 28, 62, 9)
            D.texto(tela, self.fonte, D.fmt_tempo(rel), 44, 49)
        if not self.no_chefe:
            D.desenhar_mosca(tela, LARGURA - 96, 30, self.tempo_total)
            D.texto(tela, self.fonte, str(len(self.moscas_pegas)), LARGURA - 78, 15)
        # teclinhas no canto
        x, y = 14, ALTURA - 36
        f = self.fonte_tecla
        x += D.tecla(tela, f, x, y, "<") + 4
        x += D.tecla(tela, f, x, y, ">") + 14
        x += D.tecla(tela, f, x, y, "espaco", 52) + 6
        D.icone_pulo(tela, x + 6, y + 12, 0.9)
        x += 26
        r = self.ribbat
        if self.tem_lingua:
            x += D.tecla(tela, f, x, y, "E", recarga=r.lingua_cd / (LINGUA_DUR + self.recarga_lingua)) + 6
            D.icone_lingua(tela, x, y + 13, 0.7)
            x += 30
        if self.tem_investida:
            x += D.tecla(tela, f, x, y, "Q", recarga=r.dash_cd / max(0.01, self.recarga_investida)) + 18
            D.icone_investida(tela, x, y + 12, 0.7)
            x += 30
        if self.fantasma and not self.no_chefe and self.corrida is None:
            x += D.tecla(tela, f, x, y, "G") + 4
            img = D.sprite_sapo("parado", 1, 0.4).copy()
            img.fill((60, 70, 120), special_flags=pygame.BLEND_RGB_ADD)
            img.set_alpha(150 if self.ver_fantasma else 50)
            tela.blit(img, (x, y - 4))

    def desenhar_titulo(self, tela):
        t = self.tempo_total
        P.desenhar_fundo(tela, self.fundo, t * 30, t)
        pygame.draw.rect(tela, GRAMA, (0, 448, LARGURA, 8))
        pygame.draw.rect(tela, TERRA, (0, 456, LARGURA, ALTURA))
        ciclo = (t * 0.9) % 1
        pulo = math.sin(ciclo * math.pi) * 60 if ciclo < 0.6 else 0
        x = 120 + (t * 90) % (LARGURA - 200)
        pose = "parado" if pulo == 0 else ("pulo" if ciclo < 0.3 else "queda")
        D.desenhar_sapo(tela, x, 450 - pulo, 1, pose, 1.0, int(t * 8) % 4, 1.4)
        D.texto(tela, self.fonte_gigante, "RIBBAT", LARGURA / 2, 70, centro=True, cor=(112, 196, 84),
                borda=(30, 70, 34))
        D.texto(tela, self.fonte_grande, "e o Pergaminho Perdido", LARGURA / 2, 170, centro=True, cor=AMARELO)
        D.pergaminho(tela, LARGURA / 2, 270, 1.6, brilho=t)
        if int(t * 2) % 2 == 0:
            D.tecla(tela, self.fonte_tecla, LARGURA / 2 - 20, 480, "enter", 40)


def estrela(x, y, r):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        k = r if i % 2 == 0 else r * 0.45
        pts.append((x + math.cos(a) * k, y + math.sin(a) * k))
    return pts


def criar_icone():
    s = pygame.Surface((40, 40), pygame.SRCALPHA)
    D.desenhar_sapo(s, 22, 36, 1, "parado", escala=0.55)
    return s


# =====================================================================
# Loop principal
# =====================================================================
def main():
    SOM.iniciar()
    pygame.init()
    pygame.display.set_caption("Ribbat e o Pergaminho Perdido")
    try:
        tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.SCALED)
    except pygame.error:
        tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_icon(criar_icone())
    relogio = pygame.time.Clock()
    jogo = Jogo()
    while True:
        dt = min(relogio.tick(FPS) / 1000, 1 / 30)
        ent = Entrada()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif jogo.tecla(ev.key, ent) == "sair":
                    return
        k = pygame.key.get_pressed()
        ent.dir = int(k[pygame.K_RIGHT] or k[pygame.K_d]) - int(k[pygame.K_LEFT] or k[pygame.K_a])
        ent.pulo = bool(k[pygame.K_SPACE] or k[pygame.K_w] or k[pygame.K_UP])
        jogo.atualizar(dt, ent)
        SOM.atualizar(jogo)
        jogo.desenhar(tela)
        pygame.display.flip()


if __name__ == "__main__":
    main()
    pygame.quit()
