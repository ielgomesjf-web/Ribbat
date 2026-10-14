"""
Testes do Ribbat (roda sem abrir janela):  python teste.py [pasta_pras_fotos]
1) Confere as mecânicas (torre de formiga, teia, pedra).
2) Um robô joga a Fase 1 sozinho e confere se dá pra chegar na toca do chefão.
"""
import math
import os
import random
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
SAVE_TESTE = os.environ.get("RIBBAT_SAVE_TESTE") or os.path.join(tempfile.gettempdir(), "ribbat_teste", "save_teste.json")
os.makedirs(os.path.dirname(SAVE_TESTE), exist_ok=True)
os.environ["RIBBAT_SAVE"] = SAVE_TESTE   # o teste nunca mexe no save de verdade
if os.path.exists(SAVE_TESTE):
    os.remove(SAVE_TESTE)
import pygame  # noqa: E402

import ribbat as rb  # noqa: E402
import chefe as CH  # noqa: E402
from config import GRAVIDADE, LARGURA, TILE, TOPO_VITORIA, VEL_MAX  # noqa: E402
from entidades import R, Aranha, BolaTeia, Entrada, Formiga  # noqa: E402

FOTOS = sys.argv[1] if len(sys.argv) > 1 else None
pygame.init()
tela = pygame.display.set_mode((rb.LARGURA, rb.ALTURA))
erros = []


def checa(cond, msg):
    print(("  ok  " if cond else "  ERRO ") + msg)
    if not cond:
        erros.append(msg)


def foto(jogo, nome):
    if FOTOS:
        jogo.desenhar(tela)
        pygame.image.save(tela, os.path.join(FOTOS, nome + ".png"))


def jogo_no(col, linha_pe=14):
    """Cria um jogo com o Ribbat parado na coluna `col`, em pé na linha `linha_pe`."""
    random.seed(1)
    j = rb.Jogo()
    j.estado = "jogando"
    j.tem_lingua = j.tem_investida = True
    j.ribbat.x = col * TILE
    j.ribbat.y = linha_pe * TILE - j.ribbat.H
    return j


def rodar(j, segundos, entrada=lambda j, i: Entrada()):
    for i in range(int(segundos * 60)):
        j.atualizar(1 / 60, entrada(j, i))


print("Mapa")
fase = rb.Fase(rb.fases.FASE_1)
checa(len(set(len(l) for l in fase.linhas)) == 1, "todas as linhas da fase têm a mesma largura")
checa(len(fase.checkpoints) == 3, "fase tem 3 bandeiras")
checa(fase.toca is not None, "fase tem a toca do chefão")
checa(len(fase.pedras) == 1 and len(fase.pedras[0].celulas) == 4, "os X viraram UMA pedra 2x2")

buracos_sem_querer = []
for nome_fase in ("FASE_1", "FASE_2", "FASE_3", "FASE_4"):
    for i, p in enumerate(getattr(rb.fases, nome_fase)["pedacos"]):
        larg = max(len(l) for l in p)
        if any(len(l) < larg for l in p[-3:]):
            buracos_sem_querer.append(f"{nome_fase} pedaço {i}")
checa(not buracos_sem_querer, "nenhum chão mais curto que o pedaço (buraco sem querer) " + ", ".join(buracos_sem_querer))

print("Pedra")
pedra = fase.pedras[0]
j = jogo_no(pedra.rect.left // TILE - 3)
j.fase.inimigos = []
rodar(j, 0.3)


def investe(j, i):
    e = Entrada()
    e.dir = 1
    e.investida = i == 5
    return e


rodar(j, 1.5, investe)
checa(not j.fase.pedras and all(c not in j.fase.solidos for c in pedra.celulas), "investida quebra a pedra inteira")
checa(j.ribbat.x > pedra.rect.right, "Ribbat passou pelo túnel")

print("Formigas")
# 3 formigas no chão, e o Ribbat em cima de uma plataforma
j = jogo_no(0)
j.fase.inimigos = []
j.fase.solidos.update({(c, 11): "=" for c in range(40, 45)})
j.ribbat.x, j.ribbat.y = 42 * TILE, 11 * TILE - j.ribbat.H
for i in range(3):
    j.fase.inimigos.append(Formiga((36 + i) * TILE, 14 * TILE - Formiga.H, 1))
viu_alerta = viu_torre = viu_salto = tirou_foto = False
for i in range(60 * 8):
    j.coracoes = 99
    j.atualizar(1 / 60, Entrada())
    fs = [e for e in j.fase.inimigos if isinstance(e, Formiga)]
    viu_alerta |= any(f.estado == "alerta" for f in fs)
    viu_torre |= any(f.nivel >= 2 for f in fs)
    viu_salto |= any(f.saltando and f.vy < 0 for f in fs)
    if viu_torre and not tirou_foto:
        tirou_foto = True
        rodar(j, 0.25)
        foto(j, "torre")
checa(viu_alerta, "formigas entram em alerta")
checa(viu_torre, "formigas montam torre (2+ andares)")
checa(viu_salto, "a formiga do topo pula no Ribbat")

print("Teia")
j = jogo_no(10)
j.fase.inimigos = []
a = Aranha(j.fase, 14 * TILE, 10 * TILE)
j.fase.inimigos.append(a)
j.bolas.append(BolaTeia(j.ribbat.cx, j.ribbat.y + 5, 0, 0, a))
rodar(j, 0.05)
checa(j.ribbat.preso is not None, "bola de teia prende o Ribbat")
rodar(j, 0.6)
foto(j, "casulo")


def debate(j, i):
    e = Entrada()
    e.mash = 1 if i % 4 == 0 else 0
    return e


rodar(j, 1.0, debate)
checa(j.ribbat.preso is None, "apertando rápido ele rasga a teia")
coracoes = j.coracoes
rodar(j, 1.0)
j.ribbat.invuln = 0
j.bolas.append(BolaTeia(j.ribbat.cx, j.ribbat.y + 5, 0, 0, a))
rodar(j, 6)
checa(j.coracoes < coracoes, "se não se debater, a aranha puxa e morde")


# --- robô que joga sozinho
ESTADO_ROBO = {}


def chao_em(f, cx, pe):
    """Altura do chão nessa coluna perto da altura do pé (terra, pedra ou vitória-régia)."""
    for cy in range(pe - 1, pe + 4):
        ch = f.solidos.get((cx, cy))
        if ch in ("#", "v", "X", "r"):
            return cy * TILE + (TOPO_VITORIA if ch == "v" else 0)
    return None


def escolher_pouso(f, r):
    """Depois do buraco à frente, onde dá pra cair? (esquerda, direita, altura)"""
    pe = int((r.y + r.H + 4) // TILE)
    c = int(r.cx // TILE)
    while chao_em(f, c, pe) is not None and c < f.larg - 1:
        c += 1
    vao = 0
    while chao_em(f, c, pe) is None and vao < 9 and c < f.larg - 1:
        c += 1
        vao += 1
    altura = chao_em(f, c, pe)
    if altura is None:
        return None
    fim = c
    while chao_em(f, fim + 1, pe) is not None and fim - c < 5:
        fim += 1
    return c * TILE + 2, (fim + 1) * TILE - r.W - 2, altura


def robo(jogo):
    r, f = jogo.ribbat, jogo.fase
    e = Entrada()
    e.dir = 1
    st = ESTADO_ROBO.setdefault(id(jogo), {"alvo": None})
    if r.preso:
        e.mash = 1 if int(jogo.tempo_total * 60) % 4 == 0 else 0
        return e
    if r.no_chao:
        st["alvo"] = None
    frente = int((r.x + r.W + 6) // TILE)
    linha = int((r.y + r.H / 2) // TILE)
    pe = int((r.y + r.H + 4) // TILE)
    parede = f.solido(frente, linha)
    pedra = any(f.pedra_em(frente + i, linha) for i in range(2))
    buraco = not any(f.solido(frente + i, pe) for i in range(2))
    perigo = any(abs(s.centerx - r.cx - 30) < 40 for s in f.espinhos)
    perto = any(0 < x.cx - r.cx < 70 for x in f.inimigos if isinstance(x, Formiga))
    if pedra and jogo.tem_investida:
        e.investida = True
    elif r.no_chao and (parede or buraco or perigo or perto):
        e.pulo_apertou = True
        st["alvo"] = escolher_pouso(f, r) if buraco else None
    e.pulo = e.pulo_apertou or r.vy < 0 or r.buffer > 0
    e.lingua = any(0 < x.cx - r.cx < 110 and abs(x.rect().centery - r.y) < 70 for x in f.inimigos)
    # no ar: freia ou acelera pra cair em cima do pouso escolhido
    if not r.no_chao and st["alvo"]:
        a0, a1, ys = st["alvo"]
        disc = r.vy * r.vy + 2 * GRAVIDADE * (ys - (r.y + r.H))
        if disc > 0:
            pouso = r.x + r.vx * (-r.vy + disc ** 0.5) / GRAVIDADE
            if pouso > a1 - 4:
                e.dir = -1
            elif pouso < a0 + 4:
                e.dir = 1
            else:
                e.dir = 0
    return e


def jogar(semente, segundos=360, dados=rb.fases.FASE_1):
    random.seed(semente)
    jogo = rb.Jogo(dados)
    jogo.estado = "jogando"
    jogo.mais_longe = 0
    for i in range(int(segundos * 60)):
        jogo.coracoes = 99  # o teste é do CAMINHO, não da habilidade do robô
        jogo.atualizar(1 / 60, robo(jogo))
        jogo.mais_longe = max(jogo.mais_longe, jogo.ribbat.x)
        if jogo.estado in ("fim", "final"):
            return jogo, i / 60
        if FOTOS and i % 300 == 0 and semente == 0:
            foto(jogo, f"robo_{i // 60:03d}s")
    return jogo, None


print("Robô jogando a fase 1")
for semente in range(3):
    jogo, t = jogar(semente)
    checa(t is not None, f"semente {semente}: robô chegou na toca"
          + (f" em {t:.0f}s, moscas {len(jogo.moscas_pegas)}/{jogo.fase.total_moscas}" if t else
             f" (o mais longe foi a coluna {jogo.mais_longe // TILE:.0f} de {jogo.fase.larg},"
             f" bandeiras: {jogo.salvo['bandeiras']})"))
    if t:
        checa(jogo.tem_lingua and jogo.tem_investida and jogo.coracoes_max == 4,
              "as 3 bandeiras deram linguada, investida e 4º coração")

print("Fase 2: Terreno de Lamaçal")
from entidades import PeixeLama  # noqa: E402
fase2 = rb.Fase(rb.fases.FASE_2)
checa(len(fase2.linhas[0]) == 360 and len(fase2.checkpoints) == 3 and fase2.toca, "lamaçal: 360 blocos, 3 bandeiras e toca")
checa(sum(isinstance(e, PeixeLama) for e in fase2.inimigos) >= 10, "lamaçal tem peixes-lama escondidos")


def jogo_com_peixe_lama():
    random.seed(3)
    j = rb.Jogo(rb.fases.FASE_2)
    j.estado = "jogando"
    j.fase.inimigos = [PeixeLama(20 * TILE + 16, 14 * TILE)]
    j.ribbat.y = 14 * TILE - j.ribbat.H
    return j, j.fase.inimigos[0]


j, pl = jogo_com_peixe_lama()
j.ribbat.x = pl.x - 12
c = j.coracoes
rodar(j, 1.0)
checa(j.coracoes < c, "parado em cima do peixe-lama: ele morde")
foto(j, "peixe_lama")
j, pl = jogo_com_peixe_lama()
j.ribbat.x = pl.x - 200
j.ribbat.vx = 260
c = j.coracoes


def corre(j, i):
    e = Entrada()
    e.dir = 1
    return e


rodar(j, 1.5, corre)
checa(j.coracoes == c and j.ribbat.x > pl.x + 100, "passando correndo por cima dá tempo de escapar")
j, pl = jogo_com_peixe_lama()
j.ribbat.x = pl.x - 12
j.tem_lingua = True
rodar(j, 0.8)
j.ribbat.x, j.ribbat.dir = pl.x - 90, 1
e = Entrada()
e.lingua = True
rodar(j, 0.4, lambda j, i: e if i == 0 else Entrada())
checa(pl.estado == "fora" or not pl.vivo, "depois de morder ele fica pra fora")
checa(not pl.vivo, "linguada mata o peixe-lama quando ele tá pra fora")

print("Robô jogando a fase 2")
for semente in range(2):
    jogo, tt = jogar(semente, dados=rb.fases.FASE_2)
    checa(tt is not None, f"semente {semente}: robô chegou na toca do besouro"
          + (f" em {tt:.0f}s, moscas {len(jogo.moscas_pegas)}/{jogo.fase.total_moscas}" if tt else
             f" (o mais longe foi a coluna {jogo.mais_longe // TILE:.0f} de {jogo.fase.larg},"
             f" bandeiras: {jogo.salvo['bandeiras']})"))
    if semente == 0 and FOTOS:
        for col in (60, 150, 230, 300):
            jj = rb.Jogo(rb.fases.FASE_2)
            jj.estado = "jogando"
            jj.ribbat.x, jj.ribbat.y = col * TILE, 14 * TILE - 24
            jj.ultimo_seguro = (jj.ribbat.x, jj.ribbat.y)
            jj.cam_x = jj.ribbat.cx - 384
            rodar(jj, 0.5)
            foto(jj, f"lamacal_{col}")

print("Fase 3: O Formigueiro")
from entidades import Buraco, FormigaGuerreira  # noqa: E402
fase3 = rb.Fase(rb.fases.FASE_3)
checa(len(fase3.checkpoints) == 3 and fase3.toca and all(set(fase3.linhas[i]) == {"#"} for i in range(3)),
      f"formigueiro: {fase3.larg} blocos, 3 bandeiras, toca e teto de terra")
checa(sum(isinstance(e, FormigaGuerreira) for e in fase3.inimigos) >= 8 and len(fase3.buracos) >= 5,
      "formigueiro tem formigas guerreiras e buracos")


def jogo_com_guerreira():
    random.seed(4)
    j = rb.Jogo(rb.fases.FASE_3)
    j.estado = "jogando"
    j.fase.inimigos, j.fase.buracos = [], []
    j.ribbat.x, j.ribbat.y = 40 * TILE, 14 * TILE - j.ribbat.H
    g = FormigaGuerreira(j.ribbat.cx + 150, 11 * TILE)
    g.cd = 0
    j.fase.inimigos.append(g)
    return j, g


j, g = jogo_com_guerreira()
rodar(j, 0.1)
checa(g.estado == "mirando", "guerreira vê o Ribbat e se prepara (aviso)")
rodar(j, FormigaGuerreira.AVISO - 0.15)
checa(g.estado == "mirando", f"o aviso dura {FormigaGuerreira.AVISO}s antes da investida")
foto(j, "guerreira_mirando")
c = j.coracoes
rodar(j, 1.0)
checa(j.coracoes < c, "parado no lugar: a investida da guerreira acerta")
j, g = jogo_com_guerreira()
c = j.coracoes


def foge(j, i):
    e = Entrada()
    e.dir = -1 if 6 < i < 40 else 0
    return e


rodar(j, 1.6, foge)
checa(j.coracoes == c, "saindo do lugar durante o aviso, a guerreira erra")
j, g = jogo_com_guerreira()
j.ribbat.dir = 1
rodar(j, 0.1)
j.tem_lingua = True
e = Entrada()
e.lingua = True
g.x, g.y = j.ribbat.cx + 90, j.ribbat.y + 10
rodar(j, 0.3, lambda j, i: e if i == 0 else Entrada())
checa(not g.vivo, "linguada derruba a guerreira")

random.seed(4)
j = rb.Jogo(rb.fases.FASE_3)
j.estado = "jogando"
j.tem_investida = True
j.fase.inimigos = []
h = Buraco(30 * TILE + 16, 14 * TILE)
j.fase.buracos = [h]
j.ribbat.x, j.ribbat.y = 22 * TILE, 14 * TILE - j.ribbat.H
rodar(j, 2.5)
checa(len(j.fase.inimigos) >= 1, "buraco de formigueiro solta formigas")
j.fase.inimigos = []
j.ribbat.x, j.ribbat.dir = h.x - 90, 1
j.ribbat.invuln = 9
e = Entrada()
e.investida = True
rodar(j, 0.5, lambda j, i: e if i == 0 else Entrada())
checa(not h.vivo, "investida em cima do buraco tampa ele")
foto(j, "buraco_tampado")

print("Robô jogando a fase 3")
for semente in range(2):
    jogo, tt = jogar(semente, dados=rb.fases.FASE_3)
    checa(tt is not None, f"semente {semente}: robô chegou na câmara real"
          + (f" em {tt:.0f}s, moscas {len(jogo.moscas_pegas)}/{jogo.fase.total_moscas}" if tt else
             f" (o mais longe foi a coluna {jogo.mais_longe // TILE:.0f} de {jogo.fase.larg},"
             f" bandeiras: {jogo.salvo['bandeiras']})"))
if FOTOS:
    for col in (20, 112, 150, 250, 300):
        jj = rb.Jogo(rb.fases.FASE_3)
        jj.estado = "jogando"
        jj.ribbat.x, jj.ribbat.y = col * TILE, 14 * TILE - 24
        jj.ultimo_seguro = (jj.ribbat.x, jj.ribbat.y)
        jj.cam_x = jj.ribbat.cx - 384
        rodar(jj, 0.6)
        foto(jj, f"formigueiro_{col}")

print("Orelhinhas de coelho")
if os.path.exists(SAVE_TESTE):
    os.remove(SAVE_TESTE)
j = rb.Jogo()
j.fase_atual = __import__("menu").FASES[0]
j.comecar_chefe()
checa(not j.orelhas_coelho, "primeira luta com a Viúva: sem orelhinhas")
j.venceu_chefe()
j.comecar_chefe()
checa(j.orelhas_coelho, "revanche com a Viúva: Ribbat de orelhinhas de coelho")
rodar(j, 2.6)
foto(j, "orelhinhas")
j.fase_atual = __import__("menu").FASES[1]
j.comecar_chefe()
checa(not j.orelhas_coelho, "besouro ainda não vencido: sem orelhinhas")
if os.path.exists(SAVE_TESTE):
    os.remove(SAVE_TESTE)

print("Chefão: Viúva Negra")


def pontos_cegos(graus):
    """Lugares (chão e raízes) onde o Ribbat fica a salvo de TODOS os fios de um padrão."""
    segs = []
    for g in graus:
        pts = CH.simular_ricochete(math.radians(g))
        segs += list(zip(pts, pts[1:]))
    cegos = []
    for y, x0, x1 in ((456, 0, LARGURA - 24), (360, 128, 264), (360, 704, 840)):
        livres = [x for x in range(x0, x1 + 1, 4)
                  if not any(R(x, y, 24, 24).inflate(CH.RICO_FOLGA, CH.RICO_FOLGA).clipline(a, b) for a, b in segs)]
        grupos = []
        for x in livres:
            if grupos and x - grupos[-1][1] <= 4:
                grupos[-1][1] = x
            else:
                grupos.append([x, x])
        cegos += [(a, b + 24, y) for a, b in grupos if b + 24 - a >= 36]
    return cegos


for nome, graus in zip("AB", CH.PADROES):
    cegos = pontos_cegos(graus)
    checa(2 <= len(cegos) <= 3, f"padrão {nome} da teia ricocheteando tem {len(cegos)} pontos cegos: "
          + ", ".join(f"x {a}-{b}" + (" (raiz)" if y < 400 else "") for a, b, y in cegos))


def luta():
    random.seed(5)
    j = rb.Jogo()
    j.tem_lingua = j.tem_investida = True
    j.coracoes_max = 4
    j.iniciar_chefe()
    return j


j = luta()
rodar(j, 2.6)
b = j.boss
checa(b.estado == "pendurada", "a Viúva desce e começa a luta")
foto(j, "chefe_estagio1")
vida = b.vida
b.levar(CH.DANO_LINGUA, j)
b.levar(CH.DANO_INVESTIDA, j)
checa(vida - b.vida == 5, "linguada tira 2 e investida tira 3")

# apertar E sem parar não vira metralhadora: a recarga segura
j = luta()
rodar(j, 2.6)
b = j.boss
b.estagio_1 = lambda *a: None             # congela a aranha pra medir
b.x, b.y = 784, CH.ALTURA_1
j.ribbat.x, j.ribbat.y = 784 - 130, 384 - 24
j.ribbat.dir = 1
vida = b.vida


def spam_e(j, i):
    e = Entrada()
    e.lingua = True
    e.pulo_apertou = i % 40 == 0
    e.pulo = True
    return e


rodar(j, 1.0, spam_e)
checa(0 < vida - b.vida <= 4, f"1 segundo apertando E sem parar tirou {vida - b.vida} (recarga funciona)")

# reclamações do Gomes que nunca mais podem voltar
j = luta()
rodar(j, 2.6)
b = j.boss
b.padrao = 0
b.cd_especial, b.cd_tiro, b.rajada = 0, 99, 0
rodar(j, CH.RICO_CARGA + 0.1)
ric = b.ricochetes[0]
rodar(j, 0.5)
pts = ric.pontos()
meio_fio = ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
bola = pts[-1]
alvo = R(meio_fio[0] - 12, meio_fio[1] - 12, 24, 24)
checa(math.dist(meio_fio, bola) > 60 and not ric.acerta(alvo), "andar em cima do fio NÃO machuca (só a bola)")
checa(ric.acerta(R(bola[0] - 12, bola[1] - 12, 24, 24)), "a bola de teia machuca")

for olha in (-1, 1):
    j = luta()
    rodar(j, 2.6)
    b = j.boss
    b.estagio, b.vida, b.y, b.x = 2, CH.VIDA[1], CH.CHAO_Y, 480
    b.estado = "andando"
    b.estagio_2 = lambda *a: None          # parada, só pra medir
    b.dir = -olha
    r = j.ribbat
    r.dir = olha
    r.y = CH.CHAO_Y - r.H
    tudo = b.partes()[0].unionall(b.partes()[1:])
    r.x = (tudo.left - 120 - r.W) if olha > 0 else (tudo.right + 120)
    vida = b.vida
    e = Entrada()
    e.lingua = True
    rodar(j, 0.4, lambda j, i: e if i == 0 else Entrada())
    checa(b.vida == vida - CH.DANO_LINGUA,
          f"estágio 2: linguada DO CHÃO acerta ela ({'da esquerda' if olha > 0 else 'da direita'})")

j = luta()
rodar(j, 2.6)
b = j.boss
b.estagio_1 = lambda *a: None
b.x, b.y = 480, CH.ALTURA_1
r = j.ribbat
r.x, r.y, r.dir = 480 - 150, CH.CHAO_Y - r.H, 1
vida = b.vida


def pula_e_lingua(j, i):
    e = Entrada()
    e.pulo_apertou = i == 0
    e.pulo = True
    e.lingua = i == 18
    return e


rodar(j, 1.0, pula_e_lingua)
checa(b.vida < vida, "estágio 1: pulando do chão + linguada acerta ela")

# troca de estágio
j = luta()
rodar(j, 2.6)
b = j.boss
b.vida = 1
b.levar(CH.DANO_LINGUA, j)
checa(b.estado == "caindo", "com 15 de dano o fio arrebenta e ela cai")
rodar(j, 2.6)
checa(b.estagio == 2 and b.vida == CH.VIDA[1], "estágio 2 começa com 20 de vida")
foto(j, "chefe_estagio2")

# teia do estágio 2: puxa devagar e precisa de 12 apertos
b.prender(j)
x0 = j.ribbat.x
rodar(j, 1.0)
puxou = abs(j.ribbat.x - x0)
checa(j.ribbat.preso is not None and 15 < puxou < 45, f"teia puxa devagarzinho ({puxou:.0f}px em 1s)")
foto(j, "chefe_puxando")


def aperta(j, i):
    e = Entrada()
    e.mash = 1 if i % 3 == 0 and i < 33 else 0
    return e


rodar(j, 0.34, aperta)
checa(j.ribbat.preso is not None, "11 apertos ainda não soltam")
rodar(j, 0.1, lambda j, i: type("E", (), {**Entrada().__dict__, "mash": 1})())
checa(j.ribbat.preso is None and b.estado == "tonta", "no 12º aperto ele escapa e ela fica tonta")
foto(j, "chefe_tonta")

b.vida = 1
b.levar(CH.DANO_INVESTIDA, j)
rodar(j, 3.5)
checa(j.estado == "vitoria", "com 20 de dano no estágio 2 ela perde e aparece a vitória")
foto(j, "chefe_vitoria")


# --- robô brigão (corações infinitos): prova que dá pra vencer
def robo_luta(j):
    r, b = j.ribbat, j.boss
    e = Entrada()
    if r.preso:
        e.mash = 1 if int(j.tempo_total * 60) % 3 == 0 else 0
        return e
    hb = b.hitbox()
    if b.estagio == 1:
        alvo = 208 if b.x < 480 else 784                       # raiz mais perto dela
        if abs(r.cx - alvo) > 10:
            e.dir = 1 if alvo > r.cx else -1
        elif (b.x > r.cx) != (r.dir > 0):
            e.dir = 1 if b.x > r.cx else -1                      # vira pra ela
        if r.no_chao and (r.y > 400 and abs(r.cx - alvo) < 50 or r.y < 400 and abs(b.x - r.cx) < 220):
            e.pulo_apertou = True
    else:
        lado = 1 if r.cx > b.x else -1
        alvo = max(40, min(LARGURA - 40, b.x + lado * 200))
        if abs(r.cx - alvo) > 12:
            e.dir = 1 if alvo > r.cx else -1
        elif (b.x > r.cx) != (r.dir > 0):
            e.dir = 1 if b.x > r.cx else -1
        if b.estado == "preparando" and r.no_chao:
            e.pulo_apertou = True
    e.pulo = e.pulo_apertou or r.vy < 0
    if hb:
        bx, by = r.boca()
        lingua = R(bx if r.dir > 0 else bx - 150, by - 7, 150, 14)
        e.lingua = lingua.collidelist(hb) >= 0
        dash = R(r.x if r.dir > 0 else r.x - 120, r.y, r.W + 120, r.H)
        e.investida = dash.collidelist(hb) >= 0 and not e.lingua
    return e


j = luta()
for i in range(60 * 240):
    j.coracoes = 99
    j.atualizar(1 / 60, robo_luta(j))
    if j.estado != "chefe":
        break
checa(j.estado == "vitoria", f"robô brigão venceu a Viúva em {i / 60:.0f}s" if j.estado == "vitoria" else
      f"robô brigão NÃO venceu (estágio {j.boss.estagio}, vida {j.boss.vida})")

print("Chefão: Besouro-rinoceronte")
import besouro as BS  # noqa: E402


def luta_besouro():
    random.seed(7)
    j = rb.Jogo()
    j.fase_atual = MENU_FASES[1]
    j.comecar_chefe()
    return j


MENU_FASES = __import__("menu").FASES
j = luta_besouro()
rodar(j, 2.2)
b = j.boss
checa(j.chefe_mod is BS and b.estado == "andando", "o besouro sai da terra e a luta começa")
for estagio, vida in ((1, 12), (2, 10), (3, 8)):
    checa(b.estagio == estagio and b.vida == vida, f"estágio {estagio} precisa de {vida} acertos")
    foto(j, f"besouro_estagio{estagio}")
    for _ in range(vida):
        b.levar(BS.DANO, j)
    rodar(j, 2.2 if estagio < 3 else 3.5)
checa(j.estado == "vitoria", "30 acertos: besouro vencido e aparece a vitória")
foto(j, "besouro_vitoria")

j = luta_besouro()
rodar(j, 2.2)
b = j.boss
b.estagio, b.vida = 3, 8
b.mudar("rolando")
b.vx, b.y = -650, BS.CHAO_Y
j.ribbat.x = b.x - 160
j.ribbat.invuln = 0
rodar(j, 0.5)
checa(j.estado == "gameover" and j.coracoes == 0, "a bola rolando prensa = morte na hora (mesmo com 4 corações)")


def robo_esperto(j):
    """Joga como gente: desvia dos ataques olhando os avisos e ataca nas brechas. SEM trapaça de vida."""
    r, b = j.ribbat, j.boss
    e = Entrada()
    est = b.estado
    no_chao = r.no_chao

    def ir(x, folga=10):
        if abs(r.cx - x) > folga:
            e.dir = 1 if x > r.cx else -1

    def pular():
        if no_chao:
            e.pulo_apertou = True

    if est in ("cavando", "correndo"):
        if est == "cavando":
            ir(min(max(b.x - b.dir * 260, 60), LARGURA - 60), 6)   # vai pra trás dele: ele sai correndo pro outro lado
        else:
            ir(480)
        if est == "correndo":
            x, y, ang = BS.pos_volta(b.s, b.sentido)
            vindo = (x - r.cx) * -b.sentido
            if ang == 0 and 0 < vindo < 250:
                pular()
    elif b.ondas:
        if any(0 < (r.cx - o.x) * o.d < 70 for o in b.ondas):
            pular()
    elif est in ("agachando", "quicando"):
        if b.alvo_x is not None and abs(r.cx - b.alvo_x) < 150:
            ir(b.alvo_x + (220 if r.cx > b.alvo_x else -220), 4)
        elif b.alvo_x is None:
            ir(480 if abs(r.cx - b.x) > 200 else (b.x + (260 if r.cx > b.x else -260)))
    elif est in ("enrolando", "rolando"):
        if b.alvo_x is not None and abs(r.cx - b.alvo_x) < 150:
            ir(b.alvo_x + (220 if r.cx > b.alvo_x else -220), 4)
        elif est == "rolando" and b.y >= BS.CHAO_Y - 1 and 0 < (r.cx - b.x) * (1 if b.vx > 0 else -1) < 170:
            pular()
        elif est == "enrolando":
            ir(480)
    elif est in ("mirando", "chifrando", "levantando", "batendo", "balancando", "rabada"):
        fuga = b.x + (300 if r.cx > b.x else -300)    # foge pra longe do ataque de perto...
        if not 40 < fuga < LARGURA - 40:
            fuga = b.x - (300 if r.cx > b.x else -300)  # ...e se tá encurralado, passa POR BAIXO dele
        ir(fuga, 4)
        if est == "rabada" and abs(r.cx - b.x) < 200:
            pular()
        if est == "levantando" and abs(r.cx - b.x) < 240 and b.tempo > 0.5:
            pular()                                    # pula na hora que ele bate a pata
    else:
        tudo = b.partes()[0].unionall(b.partes()[1:])
        lado = 1 if r.cx > b.x else -1
        alvo = (tudo.right + 110) if lado > 0 else (tudo.left - 110)
        ir(min(max(alvo, 30), LARGURA - 30), 8)
        if abs(r.cx - alvo) <= 30 and (b.x > r.cx) != (r.dir > 0):
            e.dir = 1 if b.x > r.cx else -1
        hb = b.hitbox()
        if hb:
            bx, by = r.boca()
            lingua = R(bx if r.dir > 0 else bx - 150, by - 7, 150, 14)
            e.lingua = lingua.collidelist(hb) >= 0
    e.pulo = e.pulo_apertou or r.vy < 0
    return e


vitorias, coracoes_sobrando = 0, []
import collections  # noqa: E402
perdas = collections.Counter()
for tentativa in range(3):
    j = luta_besouro()
    random.seed(100 + tentativa)
    c = j.coracoes
    for i in range(60 * 240):
        quem = (j.boss.estagio, j.boss.estado)
        j.atualizar(1 / 60, robo_esperto(j))
        if j.coracoes < c:
            perdas[quem] += c - j.coracoes
            c = j.coracoes
        if j.estado != "chefe":
            break
    if j.estado == "vitoria":
        vitorias += 1
        coracoes_sobrando.append(j.coracoes)
    print(f"      tentativa {tentativa + 1}: {j.estado}, estágio {j.boss.estagio}, vida dele {j.boss.vida}, "
          f"corações do Ribbat {j.coracoes}, {i / 60:.0f}s")
print("      corações perdidos por ataque:", ", ".join(f"estágio {e} {a}: {n}" for (e, a), n in perdas.most_common()))
checa(vitorias >= 1, f"robô esperto (4 corações, sem trapaça) venceu {vitorias} de 3 lutas")

print("Chefão: Formiga Rainha")
import rainha as RA  # noqa: E402


def luta_rainha(semente=9):
    random.seed(semente)
    j = rb.Jogo()
    j.fase_atual = MENU_FASES[2]
    j.comecar_chefe()
    rodar(j, 2.2)
    return j


j = luta_rainha()
b = j.boss
checa(j.chefe_mod is RA and b.estado == "voando", "a Rainha desce voando e a luta começa")
vida = b.vida
b.levar(RA.DANO_LINGUA, j)
b.levar(RA.DANO_INVESTIDA, j)
checa(vida - b.vida == 5 and b.vida == 9, "linguada tira 2, investida tira 3 (14 de vida no estágio 1)")
b.mudar("voando")
b.cd_especial = 0
rodar(j, 1.4)
checa(len(j.fase.inimigos) >= 2, f"ela chama formigas pelos buracos ({len(j.fase.inimigos)} apareceram)")
b.vida = 1
b.levar(2, j)
rodar(j, 2.2)
checa(b.estagio == 2 and b.vida == 14, "com 14 de dano vai pro estágio 2 (mais 14 de vida)")
b.vida = 1
b.levar(2, j)
rodar(j, 2.0)
checa(b.estagio == 3 and b.horda is not None and not j.fase.inimigos, "estágio 3: ela vai pro trono e a horda aparece")
foto(j, "rainha_estagio3")
b.levar(2, j)
rodar(j, 3.5)
checa(j.estado == "vitoria", "no estágio 3 UM acerto vence a Rainha")


def parar_ataques(b):
    b.cd_principal = b.cd_especial = 99


# ferroada (estágio 1): parado leva, se mexendo desvia
for mexe in (False, True):
    j = luta_rainha()
    b = j.boss
    j.fase.inimigos = []
    r = j.ribbat
    r.x = 300
    b.cd_principal, b.cd_especial = 0, 99
    c = j.coracoes

    def anda(j, i, mexe=mexe):
        e = Entrada()
        if mexe and i > 20:
            e.dir = 1 if (i // 50) % 2 else -1
        return e
    rodar(j, 1.4, anda)
    parar_ataques(b)
    rodar(j, 0.6)
    checa((j.coracoes < c) != mexe, "ferroada: " + ("parado, leva" if not mexe else "se mexendo depois do aviso, desvia"))

# rajada de ferroadas (estágio 2): correndo pra lá e pra cá quase não leva
j = luta_rainha()
b = j.boss
b.estagio, b.vida = 2, 14
j.fase.inimigos = []
b.cd_principal, b.cd_especial = 99, 0
c = j.coracoes


def corre_sem_parar(j, i):
    e = Entrada()
    r = j.ribbat
    if not hasattr(j, "_ida"):
        j._ida = 1
    if r.cx > LARGURA - 80:
        j._ida = -1
    elif r.cx < 80:
        j._ida = 1
    e.dir = j._ida
    return e


rodar(j, 3.0, corre_sem_parar)
checa(c - j.coracoes <= 1, f"gomu gomu no gatling: correndo sem parar perdeu {c - j.coracoes} coração(ões)")
foto(j, "rainha_gatling")

# rasante (estágio 2): perto da parede ou pulando na hora certa, escapa
for jeito in ("parede", "pulo"):
    j = luta_rainha()
    b = j.boss
    b.estagio, b.vida = 2, 14
    j.fase.inimigos = []
    r = j.ribbat
    r.x = 900 if jeito == "parede" else 500
    b.cd_principal, b.cd_especial = 0, 99
    c = j.coracoes

    def esquiva(j, i, jeito=jeito):
        e = Entrada()
        b, r = j.boss, j.ribbat
        if jeito == "pulo" and b.estado == "rasante" and abs(b.x - r.cx) < 160 and r.no_chao:
            e.pulo_apertou = True
        e.pulo = True
        return e
    rodar(j, 3.2, esquiva)
    checa(j.coracoes == c, f"rasante: {'perto da parede' if jeito == 'parede' else 'pulando na hora certa'} escapa")


# estágio 3: escalar antes da horda e acertar UMA vez
def escalador(j):
    """Sobe a escadinha: vai até a ponta do degrau, pula pro próximo; lá em cima, linguada na Rainha."""
    r, b = j.ribbat, j.boss
    e = Entrada()
    degraus = [(linha * TILE, c0 * TILE, (c1 + 1) * TILE) for linha, c0, c1 in RA.ESCADA]
    pe = r.y + r.H
    atual = next((d for d in degraus if abs(pe - d[0]) < 3 and d[1] - 4 <= r.cx <= d[2] + 4), (RA.CHAO_Y, 0, LARGURA))
    if r.no_chao:
        j._atual = atual                       # lembra de onde pulou (no ar ele não sabe)
    atual = getattr(j, "_atual", atual)
    acima = [d for d in degraus if d[0] < atual[0] - 4]
    if acima:
        prox = max(acima, key=lambda d: d[0])
        meio = (prox[1] + prox[2]) / 2
        if r.no_chao:
            borda = (atual[2] - 16) if meio > (atual[1] + atual[2]) / 2 else (atual[1] + 16)
            if atual[0] == RA.CHAO_Y:
                borda = prox[1] - 20 if meio > r.cx else prox[2] + 20
            if abs(r.cx - borda) > 8:
                e.dir = 1 if borda > r.cx else -1
            else:
                e.pulo_apertou = True
                e.dir = 1 if meio > r.cx else -1
        else:
            e.dir = 1 if meio > r.cx + 6 else -1 if meio < r.cx - 6 else 0
    else:
        alvo = atual[2] - 18
        if abs(r.cx - alvo) > 6:
            e.dir = 1 if alvo > r.cx else -1
        elif r.dir < 0:
            e.dir = 1
        e.lingua = r.dir > 0 and abs(r.cx - alvo) <= 6
    e.pulo = e.pulo_apertou or r.vy < 0
    return e


j = luta_rainha()
b = j.boss
b.vida = 1
b.levar(2, j)
rodar(j, 2.2)
b.vida = 1
b.levar(2, j)
rodar(j, 1.8)
c = j.coracoes
for i in range(60 * 30):
    j.atualizar(1 / 60, escalador(j))
    if j.estado != "chefe" or b.estado == "morrendo":
        break
checa(b.estado == "morrendo" or j.estado == "vitoria",
      f"estágio 3: escalando dá tempo de subir e acertar ({i / 60:.1f}s, horda em y={b.horda:.0f}, corações perdidos {c - j.coracoes})")
j = luta_rainha()
b = j.boss
b.vida = 1
b.levar(2, j)
rodar(j, 2.2)
b.vida = 1
b.levar(2, j)
rodar(j, 1.8)
c = j.coracoes
b.horda = j.ribbat.y + 10
rodar(j, 0.1)
checa(c - j.coracoes == 2, "encostar na horda tira 2 corações")

print("Fase 4: O Quintal")
from entidades import Abelha, Mao  # noqa: E402
fase4 = rb.Fase(rb.fases.FASE_4)
checa(len(fase4.checkpoints) == 3 and fase4.toca and len(fase4.flores) >= 8 and len(fase4.maos) == 1,
      f"quintal: {fase4.larg} blocos, 3 bandeiras, {len(fase4.flores)} canteiros com abelha e a mão do churrasco")


def quintal_limpo():
    random.seed(6)
    j = rb.Jogo(rb.fases.FASE_4)
    j.estado = "jogando"
    j.fase.inimigos, j.fase.maos = [], []
    return j


j = quintal_limpo()
fl = j.fase.flores[0]
ab = Abelha(fl)
j.fase.inimigos = [ab]
j.ribbat.x, j.ribbat.y = (fl.x0 + fl.x1) / 2 - 12, fl.chao - j.ribbat.H
rodar(j, 0.1)
checa(ab.estado == "alerta", "pisou nas flores: a abelha acorda (aviso)")
c = j.coracoes
rodar(j, 1.5)
checa(j.coracoes < c, "a abelha persegue e ferroa")
j = quintal_limpo()
fl = j.fase.flores[0]
ab = Abelha(fl)
j.fase.inimigos = [ab]
j.ribbat.x, j.ribbat.y = fl.x0 - 200, fl.chao - j.ribbat.H
rodar(j, 1.0)
checa(ab.estado == "pousada", "sem pisar nas flores, a abelha fica quietinha")

for foge in (False, True):
    j = quintal_limpo()
    mao = Mao(160 * TILE)
    mao.cd = 0.3
    j.fase.maos = [mao]
    j.ribbat.x, j.ribbat.y = 160 * TILE, 11 * TILE - j.ribbat.H
    c = j.coracoes

    def mexe(j, i, foge=foge):
        e = Entrada()
        if foge and j.fase.maos[0].estado == "mirando":
            e.dir = 1
        return e
    rodar(j, 2.2, mexe)
    if not foge:
        foto(j, "mao_churrasco")
    checa((j.coracoes < c) != foge, "mão do churrasco: " + ("parado debaixo da sombra, leva o tapão" if not foge
                                                           else "saindo da sombra durante o aviso, escapa"))

print("Robô jogando a fase 4")
for semente in range(2):
    jogo, tt = jogar(semente, dados=rb.fases.FASE_4)
    checa(tt is not None, f"semente {semente}: robô chegou na portinha do gato"
          + (f" em {tt:.0f}s" if tt else f" (o mais longe foi a coluna {jogo.mais_longe // TILE:.0f} de {jogo.fase.larg},"
                                          f" bandeiras: {jogo.salvo['bandeiras']})"))

print("Fase 5: A Montanha")
from entidades import Passaro  # noqa: E402
fase5 = rb.Fase(rb.fases.FASE_5)
inicio_y = fase5.inicio[1]
cume_y = fase5.toca.base
checa(len(fase5.checkpoints) == 3 and fase5.toca and inicio_y - cume_y > 30 * TILE,
      f"montanha: {fase5.larg} blocos de largura e sobe {(inicio_y - cume_y) // TILE} blocos até o topo")
checa(len(fase5.espinhos) >= 15 and sum(isinstance(e, Passaro) for e in fase5.inimigos) >= 6,
      f"montanha tem muitos espinhos ({len(fase5.espinhos)}) e gaviões")


def jogo_com_gaviao(foge):
    random.seed(4)
    j = rb.Jogo(rb.fases.FASE_5)
    j.estado = "jogando"
    j.fase.inimigos = []
    r = j.ribbat
    r.x, r.y = 6 * TILE, j.fase.inicio[1]
    gv = Passaro(r.cx + 120, r.y - 200)
    gv.cd = 0
    j.fase.inimigos.append(gv)
    c = j.coracoes

    def mexe(j, i):
        e = Entrada()
        if foge and j.fase.inimigos and j.fase.inimigos[0].estado == "mirando":
            e.dir = 1
        return e
    rodar(j, 2.0, mexe)
    return j, c


j, c = jogo_com_gaviao(False)
checa(j.coracoes < c, "gavião: parado no alvo, leva o mergulho")
foto(j, "gaviao")
j, c = jogo_com_gaviao(True)
checa(j.coracoes == c, "gavião: saindo do alvo durante o aviso, ele erra")

colados = []
for nome_fase in ("FASE_1", "FASE_2", "FASE_3", "FASE_4", "FASE_5"):
    L = rb.Fase(getattr(rb.fases, nome_fase)).linhas
    W, H = len(L[0]), len(L)

    def sol(c, r):
        return 0 <= c < W and 0 <= r < H and L[r][c] in "#=XvrK"
    for r in range(H):
        for c in range(W):
            if L[r][c] == "^":
                for d in range(1, 5):
                    if c + d >= W or sol(c + d, r):
                        break
                    if not sol(c + d, r + 1):
                        colados.append(f"{nome_fase} coluna {c}")
                        break
checa(not colados, "nenhum espinho colado na beirada de um buraco " + ", ".join(colados))

print("Robô escalando a fase 5")
for semente in range(2):
    jogo, tt = jogar(semente, dados=rb.fases.FASE_5)
    checa(tt is not None, f"semente {semente}: robô chegou no topo da montanha"
          + (f" em {tt:.0f}s" if tt else f" (o mais longe foi a coluna {jogo.mais_longe // TILE:.0f} de {jogo.fase.larg},"
                                          f" bandeiras: {jogo.salvo['bandeiras']})"))

print("Chefão: o Gato")
import gato as GT  # noqa: E402


def luta_gato(semente=3):
    random.seed(semente)
    j = rb.Jogo()
    j.fase_atual = MENU_FASES[3]
    j.comecar_chefe()
    rodar(j, 1.8)
    return j


j = luta_gato()
g = j.boss
r = j.ribbat
monte = g.baguncas[2]
r.x = monte.cx - r.W / 2
rodar(j, 0.1)
checa(g.escondido_em(r) is monte, "parado atrás da bagunça, o Ribbat fica escondido")
g.cd = 0
rodar(j, 0.1)
checa(g.estado == "mirando" and g.alvo is monte, "a patada mira a bagunça onde ele está escondido")
c = j.coracoes
rodar(j, 1.4)
checa(not monte.vivo and j.coracoes < c and g.patadas == 4, "a patada tira a bagunça e machuca quem ficou")

j = luta_gato()
g, r = j.boss, j.ribbat
r.x = g.baguncas[2].cx - r.W / 2
rodar(j, 0.1)
g.cd = 0
c = j.coracoes
outro = g.baguncas[3].cx - r.W / 2


def troca(j, i):
    e = Entrada()
    rr = j.ribbat
    if j.boss.estado == "mirando" and abs(rr.x - outro) > 4:
        e.dir = 1 if outro > rr.x else -1
    return e


rodar(j, 1.6, troca)
checa(j.coracoes == c and not g.baguncas[2].vivo, "trocando de bagunça durante o aviso, escapa (mas a bagunça some)")
foto(j, "gato_patada")

j = luta_gato()
g, r = j.boss, j.ribbat
g.patadas = 0
rodar(j, 0.2)
checa(g.estado == "agachando", "depois das 5 patadas ele se prepara pra investida")
rodar(j, 2.6)
checa(j.estado == "gameover" and j.coracoes == 0, "investida: ficou parado = X_X (morte na hora)")

j = luta_gato()
g, r = j.boss, j.ribbat
g.patadas = 0
r.x = 300


def foge_da_sombra(j, i):
    e = Entrada()
    g = j.boss
    if g.estado in ("agachando", "pulando") and g.trava:
        e.dir = 1 if j.ribbat.cx < 700 else 0
    return e


rodar(j, 1.5, foge_da_sombra)
foto(j, "gato_investida")
rodar(j, 2.5, foge_da_sombra)
checa(j.estado == "chefe" and g.modo == "sala", "investida: fugiu da sombra vermelha = o gato erra e cai NA SALA")
rodar(j, 0.5)
foto(j, "gato_sala")


def gato_na_sala(semente=3):
    j = luta_gato(semente)
    j.boss.ir_pra_sala(j)
    rodar(j, 2.2)                                      # ele chega tontinho
    return j, j.boss


j, g = gato_na_sala()
checa(g.estado == "andando" and g.vida == GT.VIDA_SALA, f"na sala ele luta de verdade ({GT.VIDA_SALA} de vida)")
vida = g.vida
g.levar(GT.DANO_LINGUA, j)
g.levar(GT.DANO_INVESTIDA, j)
checa(vida - g.vida == 5, "na sala: linguada tira 2, investida tira 3")

# linguada do chão acerta (as pernas contam)
j, g = gato_na_sala()
g.atualizar_sala = lambda *a: None
r = j.ribbat
r.dir = 1
r.x = g.partes()[0].left - 120 - r.W             # 120px antes do corpo dele
vida = g.vida
e = Entrada()
e.lingua = True
rodar(j, 0.4, lambda j, i: e if i == 0 else Entrada())
checa(g.vida < vida, "na sala, a linguada DO CHÃO acerta o gato")

# patada: dá pra fugir pra trás
for foge in (False, True):
    j, g = gato_na_sala()
    j.mosquitos = []
    r = j.ribbat
    g.x = 600
    r.x = g.x - 200
    g.dir = -1
    g.cd_patada = 0
    g.cd_laser = 99
    c = j.coracoes

    def recua(j, i, foge=foge):
        e = Entrada()
        if foge and j.boss.estado == "mirando":
            e.dir = -1
        return e
    rodar(j, 1.4, recua)
    checa((j.coracoes < c) != foge, "patada da sala: " + ("parado na frente, leva" if not foge else "recuando no aviso, escapa"))

# laser: correndo é alto demais; escorregando dá pra passar por cima
j, g = gato_na_sala()
g.estado = "correndo"
g.escorregando = False
alto = g.perigos()[0].unionall(g.perigos()[1:]).top
g.escorregando = True
baixo = g.perigos()[0].unionall(g.perigos()[1:]).top
checa(GT.CHAO_Y - alto > 125 and GT.CHAO_Y - baixo < 90,
      f"laser: correndo ele tem {GT.CHAO_Y - alto}px de altura (não dá pra pular), escorregando só {GT.CHAO_Y - baixo}px (dá!)")


def robo_gato(j):
    """Joga como gente nas duas partes: se esconde/troca de bagunça e foge da sombra (quarto);
    na sala foge da patada, fica atrás do gato no laser e PULA POR CIMA quando ele escorrega."""
    r, g = j.ribbat, j.boss
    e = Entrada()

    def ir(x, folga=6):
        x = min(max(x, 30), LARGURA - 30)
        if abs(r.cx - x) > folga:
            e.dir = 1 if x > r.cx else -1

    if g.modo == "quarto":
        vivos = [b for b in g.baguncas if b.vivo]
        if g.estado in ("agachando", "pulando"):
            if g.trava:
                ir(820 if g.alvo_x < 480 else 140)
            return e
        meu = g.escondido_em(r)
        if g.estado == "mirando" and (meu is g.alvo or abs(r.cx - g.alvo_x) < 90):
            outros = [b for b in vivos if b is not g.alvo]
            ir(min(outros, key=lambda b: abs(b.cx - r.cx)).cx if outros else (140 if r.cx > 480 else 820), 4)
        elif not meu and vivos:
            ir(min(vivos, key=lambda b: abs(b.cx - r.cx)).cx, 4)
        return e
    est = g.estado
    if not r.no_chao and getattr(j, "_salto", 0):          # no meio do pulo por cima: segue reto até cair
        e.dir = j._salto
        e.pulo = r.vy < 0
        return e
    j._salto = 0
    if est in ("laser_inicio", "correndo"):
        sentido = (1 if g.vx > 0 else -1) if abs(g.vx) > 1 else g.dir
        if g.escorregando and g.virando <= 0 and abs(g.vx) > 1:
            sentido = 1 if g.vx > 0 else -1               # escorregando: o "pra frente" é pra onde ele desliza
        atras = (r.cx - g.x) * sentido < 0                # o Ribbat está atrás do gato?
        costas = g.x - sentido * 60                       # onde fica o bumbum dele
        if g.escorregando and atras:
            ir(g.x + sentido * 200)                       # ele vai voltar: pula POR CIMA pro outro lado
            if 0 <= (costas - r.cx) * sentido < 70 and r.no_chao:
                e.pulo_apertou = True
                j._salto = sentido
        elif g.escorregando:                              # na frente do escorregão: pula por cima vindo de frente
            ir(g.x)
            if abs(r.cx - g.x) < 120 and r.no_chao:
                e.pulo_apertou = True
                j._salto = 1 if g.x > r.cx else -1
        elif atras:
            ir(g.x - sentido * 130)                       # vai atrás dele, de pertinho
        else:
            ir(LARGURA - 40 if sentido > 0 else 40)       # na frente dele: corre pra parede e espera ele escorregar
    elif est in ("mirando", "patada"):
        ir(r.cx + (-200 if g.x > r.cx else 200))
        if est == "patada" and abs(r.cx - g.x) < 230:
            e.pulo_apertou = True
    elif est in ("tonto", "recuperando", "andando", "chegando"):
        tudo = g.partes()[0].unionall(g.partes()[1:])
        alvo = (tudo.right + 110) if r.cx > g.x else (tudo.left - 110)
        ir(alvo)
        if abs(r.cx - alvo) <= 30 and (g.x > r.cx) != (r.dir > 0):
            e.dir = 1 if g.x > r.cx else -1
        hb = g.hitbox()
        if hb:
            bx, by = r.boca()
            lingua = R(bx if r.dir > 0 else bx - 150, by - 7, 150, 14)
            e.lingua = lingua.collidelist(hb) >= 0
    e.pulo = e.pulo_apertou or r.vy < 0
    return e


ganhou, perdas = 0, collections.Counter()
for tentativa in range(3):
    j = luta_gato(20 + tentativa)
    c = j.coracoes
    for i in range(60 * 150):
        quem = (j.boss.modo, j.boss.estado, j.boss.escorregando)
        j.atualizar(1 / 60, robo_gato(j))
        if j.coracoes < c:
            perdas[quem] += c - j.coracoes
        c = j.coracoes
        if j.estado != "chefe":
            break
    ganhou += j.estado == "vitoria"
    print(f"      tentativa {tentativa + 1}: {j.estado}, parte {j.boss.modo}, vida do gato {j.boss.vida}, "
          f"corações {j.coracoes}, {i / 60:.0f}s")
print("      corações perdidos por ataque:", dict(perdas))
checa(ganhou >= 2, f"robô esperto (4 corações) venceu o gato (quarto + sala) {ganhou} de 3 vezes")
foto(j, "gato_vitoria")

j, g = gato_na_sala()
j.coracoes = 1
j.ribbat.invuln = 0
j.ribbat.machucar(j, j.ribbat.cx + 10)
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "chefe" and j.boss.modo == "sala", "perdeu na sala: recomeça JÁ NA SALA (não volta pro quarto)")

import progresso as PR_  # noqa: E402
import medalhas as MD_VO  # noqa: E402
print("Chefão secreto: o Vô gigante")
import vovo as VV  # noqa: E402


def luta_vovo(semente=1):
    random.seed(semente)
    j = rb.Jogo()
    j.fase_atual = MENU_FASES[5]
    j.comecar_chefe()
    return j


j = luta_vovo()
checa(j.estado == "chefe" and j.chefe_mod is VV and j.boss.vida == 30, "o Vô: chefão secreto com 30 de vida")
v = j.boss
v.mudar("parado")
j.ribbat.x = v.x - 12
rodar(j, 0.05)
checa(VV.lingua_frente(j.ribbat) is None, "sem apertar E não tem língua")
e = Entrada()
e.lingua = True
j.atualizar(1 / 60, e)
v.tempo = 0
rodar(j, 0.3)
checa(v.vida == 30, "parado ele não leva dano (a língua bate e volta)")
v.mudar("tonto")
v.tempo = -9
rodar(j, 0.6)
e = Entrada()
e.lingua = True
j.atualizar(1 / 60, e)
rodar(j, 0.3)
checa(v.vida == 28, f"tonto: a linguada do Ribbat vai PRA FRENTE e acerta o Vô (vida {v.vida})")
x0 = j.ribbat.x
rodar(j, 0.7)
e = Entrada()
e.investida = True
j.atualizar(1 / 60, e)
rodar(j, 0.3)
checa(v.vida == 25 and abs(j.ribbat.x - x0) < 4, f"a investida é um pulão pra frente (não anda pro lado) e tira 3 (vida {v.vida})")
v.mudar("lingua")
v.alvo_x = 100
e = Entrada()
e.lingua = True
rodar(j, 0.6)
j.atualizar(1 / 60, e)
checa(v.vida == 23 or v.estado == "recolhendo", "com a língua dele pra fora, dá pra castigar")
# justiça: a faixa da linguada dele dá pra sair a tempo, e a área do pulo sempre deixa um lado livre
vel = VEL_MAX
checa(min(VV.MIRA) > (VV.FAIXA / 2 + rb.Ribbat.W) / vel + 0.2,
      f"aviso da linguada ({min(VV.MIRA)}s) dá tempo de sair da faixa andando")
pior = 0
for rx in range(0, LARGURA, 10):
    meio = min(max(rx, VV.ZONA / 2 + 110), LARGURA - VV.ZONA / 2 - 110)
    x0z, x1z = meio - VV.ZONA / 2, meio + VV.ZONA / 2
    checa_livre = max(x0z, LARGURA - x1z)
    pior = max(pior, min(abs(rx - x0z), abs(x1z - rx)) if x0z <= rx <= x1z else 0)
    if checa_livre < 280:
        checa(False, f"a área do pulo deixou pouco lugar livre ({checa_livre}px)")
        break
checa(min(VV.AGACHA) > (pior + rb.Ribbat.W) / vel + 0.2,
      f"aviso do pulo ({min(VV.AGACHA)}s) dá tempo de sair da área (pior caso {pior}px)")
for nome, pos in (("faixa", "lingua"), ("area", "pulo")):
    j = luta_vovo(5)
    v = j.boss
    v.mudar("parado")
    v.tempo = 99
    v.seguidas = 0 if pos == "lingua" else 9
    random.seed(0 if pos == "lingua" else 3)
    c = j.coracoes
    fugiu = False
    for i in range(60 * 4):
        e = Entrada()
        if v.estado == "mirando" and v.tempo > 0.25:
            e.dir = 1 if j.ribbat.cx < LARGURA / 2 else -1
        if v.estado == "agachando" and v.tempo > 0.25:
            x0z, x1z = v.zona
            e.dir = -1 if (j.ribbat.cx - x0z) < (x1z - j.ribbat.cx) else 1
        j.atualizar(1 / 60, e)
        if v.estado in ("tonto", "recolhendo"):
            fugiu = True
            break
    checa(fugiu and j.coracoes == c, f"reagindo 0.25s depois do aviso dá pra fugir da {nome} do Vô")


def robo_vovo(j):
    r, v = j.ribbat, j.boss
    e = Entrada()

    def ir(x, tol=8):
        e.dir = 0 if abs(x - r.cx) < tol else (1 if x > r.cx else -1)
    if v.estado in ("mirando", "lingua"):
        lado = 1 if v.alvo_x < LARGURA / 2 else -1
        ir(v.alvo_x + lado * 150)
    elif v.estado in ("agachando", "pulando", "caiu"):
        x0z, x1z = v.zona
        ir(x0z - 50 if (r.cx - x0z) < (x1z - r.cx) and x0z > 60 else x1z + 50)
    elif v.vulneravel or v.estado == "voltando":
        ir(v.x, 30)
        if abs(r.cx - v.x) < 80 and v.vulneravel:
            e.lingua = r.lingua_cd <= 0
            e.investida = not e.lingua and r.dash_cd <= 0
    e.pulo = e.pulo_apertou or r.vy < 0
    return e


ganhou, perdas, tempos = 0, collections.Counter(), []
for tentativa in range(3):
    j = luta_vovo(60 + tentativa)
    c = j.coracoes
    for i in range(60 * 150):
        quem = j.boss.estado
        j.atualizar(1 / 60, robo_vovo(j))
        if j.estado == "chefe" and j.coracoes < c:
            perdas[quem] += c - j.coracoes
        c = j.coracoes
        if j.estado != "chefe":
            break
    ganhou += j.estado == "vitoria"
    tempos.append(round(i / 60))
    print(f"      tentativa {tentativa + 1}: {j.estado}, vida do Vô {j.boss.vida}, corações {j.coracoes}, {i / 60:.0f}s")
print("      corações perdidos por ataque:", dict(perdas))
checa(ganhou >= 2, f"robô esperto (4 corações) venceu o Vô {ganhou} de 3 vezes")
checa(MD_VO.METAS["secreta"]["tempo_chefe"][0] >= max(tempos) * 1.4, f"ouro do Vô com folga (robô {max(tempos)}s)")
foto(j, "vovo_vitoria")

print("Chefão final: a Águia-careca")
import aguia as AG  # noqa: E402


def luta_aguia(semente=1):
    random.seed(semente)
    j = rb.Jogo()
    j.fase_atual = MENU_FASES[4]
    j.comecar_chefe()
    return j


j = luta_aguia()
checa(j.estado == "chefe" and j.chefe_mod is AG and j.boss.vida == 25, "fase 5 tem chefão: a Águia, com 25 de vida")
H = rb.Ribbat.H
chao = R(400, AG.CHAO_Y - H, rb.Ribbat.W, H)
na_pedra = R(14 * TILE, AG.PEDRA_Y - H, rb.Ribbat.W, H)
pulando = chao.move(0, -int(760 ** 2 / (2 * GRAVIDADE)))
alto = AG.caixas("alto", 420, AG.ALTO_Y, 1)
baixo = AG.caixas("baixo", 420, AG.BAIXO_Y, 1)
checa(chao.collidelist(alto) < 0 and na_pedra.collidelist(alto) >= 0 and pulando.collidelist(alto) >= 0,
      "rasante ALTO: pega quem está na pedra ou pulando, mas quem fica no chão escapa")
checa(chao.collidelist(baixo) >= 0 and na_pedra.collidelist(baixo) < 0,
      "rasante BAIXO: pega quem está no chão, mas quem sobe na pedra escapa")
folga = min(c.top for c in baixo) - na_pedra.bottom
checa(folga >= 12, f"rasante baixo passa {folga}px abaixo do pé de quem está na pedra")
by = AG.CHAO_Y - H + 8
alcanca = []
for d in (-1, 1):                                    # ela de costas e de frente pro Ribbat (que está à direita)
    pousada = AG.caixas("pousada", 480, AG.POUSO_Y, d)
    frente = max(c.right for c in pousada if c.bottom > by - 7)
    bx = frente + 120 - 18                           # o Ribbat a 120px, olhando pra ela
    alcanca.append(R(bx - 150, by - 7, 150, 14).collidelist(pousada) >= 0)
checa(all(alcanca), "a linguada do chão alcança ela pousada, de frente e de costas (sem precisar pular)")

# dá pra subir nas pedras pulando do chão
j = luta_aguia()
j.boss.mudar("pausa")
j.boss.tempo = -99
c0, c1 = AG.PEDRAS[1]
j.ribbat.x = (c0 + c1) / 2 * TILE - 12
rodar(j, 0.3)


def sobe(j, i):
    e = Entrada()
    e.pulo_apertou = i == 0
    e.pulo = i < 30
    return e


rodar(j, 1.2, sobe)
checa(j.ribbat.no_chao and abs(j.ribbat.y + H - AG.PEDRA_Y) < 2, "pulando do chão dá pra subir na pedra (passa por baixo)")


def ataque(altura, onde, semente=3):
    """Um ataque só, com o Ribbat parado num lugar. Devolve quantos corações perdeu."""
    j = luta_aguia(semente)
    a = j.boss
    if onde == "pedra":
        j.ribbat.x, j.ribbat.y = 14 * TILE, AG.PEDRA_Y - H - 2
    else:
        j.ribbat.x = onde
    rodar(j, 0.4)
    a.fila = [altura]
    a.mudar("pausa")
    a.tempo = 99
    c = j.coracoes
    for i in range(60 * 4):
        j.atualizar(1 / 60, Entrada())
        if a.estado in ("pausa", "subindo") and i > 30:
            break
    return c - j.coracoes, a


perdeu, _ = ataque("alto", 300)
checa(perdeu == 0, "rasante alto: parado no chão não perde coração")
perdeu, _ = ataque("alto", "pedra")
checa(perdeu == 1, "rasante alto: parado na pedra perde coração (o ataque é de verdade)")
perdeu, _ = ataque("baixo", "pedra")
checa(perdeu == 0, "rasante baixo: em cima da pedra não perde coração")
perdeu, _ = ataque("baixo", 300)
checa(perdeu == 1, "rasante baixo: parado no chão perde coração")
perdeu, a = ataque("mergulho", 300)
checa(perdeu == 1, "mergulho: ficar parado no alvo perde coração")

# mergulho: sair do alvo durante o aviso
j = luta_aguia()
a = j.boss
j.ribbat.x = 300
rodar(j, 0.4)
a.fila = ["mergulho"]
a.mudar("pausa")
a.tempo = 99
c = j.coracoes
for i in range(60 * 3):
    e = Entrada()
    if a.estado == "aviso_mergulho" and a.tempo > 0.3:
        e.dir = 1                                    # reage 0.3s depois que a mira aparece
    j.atualizar(1 / 60, e)
checa(j.coracoes == c, "mergulho: saindo do alvo durante o aviso, ela erra")
checa(a.estado in ("subindo", "pausa", "aviso_rasante", "aviso_mergulho", "pousando") , "depois de errar ela volta pro céu")

# pousa cansada longe do Ribbat (nunca em cima)
for x in (60, 300, 470, 500, 700, 900):
    j = luta_aguia()
    a = j.boss
    j.ribbat.x = x
    rodar(j, 0.3)
    a.fila = []
    a.mudar("pausa")
    a.tempo = 99
    rodar(j, 1.6)
    if a.estado != "cansada" or abs(a.x - j.ribbat.cx) < 150:
        checa(False, f"pousou longe do Ribbat (Ribbat em {x}, ela em {a.x:.0f}, {a.estado})")
        break
else:
    checa(True, "ela sempre pousa cansada longe do Ribbat")
dano_ok = a.vulneravel
a.levar(AG.DANO_LINGUA, j)
a.levar(AG.DANO_INVESTIDA, j)
checa(dano_ok and a.vida == 20, "cansada: linguada tira 2 e investida tira 3")
a.vida = 13
a.levar(2, j)
checa(a.furiosa, "com metade da vida ela fica furiosa")
a.nova_fila()
checa(len(a.fila) == 4 and set(a.fila) >= {"alto", "baixo", "mergulho"}, "furiosa: 4 rasantes por rodada (dos 3 jeitos)")
checa(AG.CANSADA[1] >= 3 and min(AG.AVISO) >= 0.8, "furiosa ainda dá aviso e tempo de bater")
foto(j, "aguia_cansada")


def robo_aguia(j):
    r, a = j.ribbat, j.boss
    e = Entrada()

    def ir(x, tol=8):
        e.dir = 0 if abs(x - r.cx) < tol else (1 if x > r.cx else -1)
    na_pedra = r.no_chao and abs(r.y + r.H - AG.PEDRA_Y) < 3
    est = a.estado
    if est in ("aviso_rasante", "rasante") and a.altura == "baixo":
        melhor = min(AG.PEDRAS, key=lambda p: abs((p[0] + p[1]) / 2 * TILE - r.cx))
        x0, x1 = melhor[0] * TILE + 20, melhor[1] * TILE - 20
        alvo = min(max(r.cx, x0), x1)
        ir(alvo)
        if not na_pedra and r.no_chao and x0 - 10 <= r.cx <= x1 + 10:
            e.pulo_apertou = True
    elif est in ("aviso_rasante", "rasante"):
        if na_pedra:                                  # desce da pedra pelo lado mais perto
            for c0, c1 in AG.PEDRAS:
                if c0 * TILE - 20 <= r.cx <= c1 * TILE + 20:
                    ir(c0 * TILE - 40 if r.cx - c0 * TILE < c1 * TILE - r.cx else c1 * TILE + 40)
    elif est in ("aviso_mergulho", "mergulho") and a.alvo:
        ax = a.alvo[0]
        ir(ax + 240 if ax < LARGURA / 2 else ax - 240)
    elif est in ("cansada", "presa"):
        hb = a.hitbox()
        by = r.boca()[1]
        baixas = [c for c in hb if c.bottom > by - 7 and c.top < by + 7]     # o que a língua do chão alcança
        tudo = baixas[0].unionall(baixas[1:])
        alvo = (tudo.right + 100) if r.cx > a.x else (tudo.left - 100)
        ir(alvo, 24)
        if abs(r.cx - alvo) <= 40 and (a.x > r.cx) != (r.dir > 0):
            e.dir = 1 if a.x > r.cx else -1
        bx, by = r.boca()
        lingua = R(bx if r.dir > 0 else bx - 150, by - 7, 150, 14)
        e.lingua = lingua.collidelist(hb) >= 0
        e.investida = not e.lingua and r.lingua_cd > 0.2 and abs(r.cx - a.x) < 200 and (a.x > r.cx) == (r.dir > 0)
    else:
        ir(LARGURA / 2 + (120 if r.cx > LARGURA / 2 else -120), 40)
    e.pulo = e.pulo_apertou or r.vy < 0
    return e


ganhou, perdas = 0, collections.Counter()
for tentativa in range(3):
    j = luta_aguia(40 + tentativa)
    c = j.coracoes
    for i in range(60 * 150):
        quem = (j.boss.estado, j.boss.altura if j.boss.estado in ("rasante", "aviso_rasante") else "")
        j.atualizar(1 / 60, robo_aguia(j))
        if j.estado == "chefe" and j.coracoes < c:
            perdas[quem] += c - j.coracoes
        c = j.coracoes
        if j.estado != "chefe":
            break
    ganhou += j.corrida is not None
    print(f"      tentativa {tentativa + 1}: {j.estado}, vida da águia {j.boss.vida}, corações {j.coracoes}, {i / 60:.0f}s")
print("      corações perdidos por ataque:", dict(perdas))
checa(ganhou >= 2, f"robô esperto (4 corações) venceu a Águia {ganhou} de 3 vezes")

print("A Corrida até o pergaminho")
j = luta_aguia()
a = j.boss
a.fila = []
a.mudar("pausa")
a.tempo = 99
rodar(j, 1.6)
a.vida = 2
a.levar(2, j)
checa(a.estado == "vencida", "25 de dano: a águia perde")
fotos_cena = {}
for i in range(60 * 8):
    j.atualizar(1 / 60, Entrada())
    if j.estado == "chefe" and j.boss.estado not in fotos_cena:
        fotos_cena[j.boss.estado] = True
        foto(j, f"aguia_{j.boss.estado}")
    if j.estado != "chefe":
        break
checa({"agarrando", "levando", "arremesso"} <= set(fotos_cena), "ela agarra o Ribbat no bico, leva pro alto e JOGA")
checa(j.estado == "jogando" and j.corrida is not None and j.fase.pergaminho and j.dados_fase is rb.fases.FASE_CORRIDA,
      "depois do arremesso começa a CORRIDA")
checa(j.tem_lingua and j.tem_investida and j.coracoes_max == 4, "na corrida já tem linguada, investida e 4 corações")
x0 = j.ribbat.x


def anda(j, i):
    e = Entrada()
    e.dir = 1
    return e


rodar(j, 1.0, anda)
checa(abs(j.ribbat.x - x0) < 2, "luzinhas vermelhas: ainda não dá pra correr")
foto(j, "corrida_largada")

tempos = []
for semente in range(3):
    jj, tt = jogar(semente, segundos=90, dados=rb.fases.FASE_CORRIDA)
    tempos.append(tt)
checa(all(tempos), f"o robô chega no pergaminho (tempos {tempos})")
if all(tempos):
    checa(max(tempos) < AG.TEMPO_AGUIA * 0.75,
          f"sobra folga pra gente: robô {max(tempos):.0f}s, águia {AG.TEMPO_AGUIA:.0f}s")


def corrida_de_verdade(semente):
    """A corrida inteira com 4 corações de verdade (perdeu = começa a corrida de novo, igual o jogo)."""
    random.seed(semente)
    j = rb.Jogo()
    j.fase_atual = MENU_FASES[4]
    j.comecar_corrida()
    ESTADO_ROBO.clear()
    for i in range(60 * 70):
        j.atualizar(1 / 60, robo(j))
        if j.estado != "jogando":
            return j, i / 60
    return j, None


venceu = 0
for semente in range(3):
    j, tt = corrida_de_verdade(semente)
    venceu += j.estado == "final"
    print(f"      corrida {semente + 1}: {j.estado} em {tt}s, corações {j.coracoes}")
checa(venceu >= 2, f"com corações de verdade o robô ganha a corrida {venceu} de 3 vezes")
if j.estado == "final":
    checa(PR_.carregar()["fases"]["fase5"]["chefe"], "ganhar a corrida salva: jogo zerado!")
    for k in range(8):
        j.tecla(pygame.K_RETURN, Entrada())
        if j.estado != "final":
            break
    checa(j.estado == "menu", "o quadrinho final tem 4 quadros e depois volta pro menu")

j = rb.Jogo()
j.fase_atual = MENU_FASES[4]
j.comecar_corrida()
j.corrida["t"] = AG.TEMPO_AGUIA
j.atualizar(1 / 60, Entrada())
checa(j.estado == "perdeu_corrida", "se a águia chegar primeiro, perdeu a corrida")
foto(j, "corrida_perdeu")
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "jogando" and j.corrida["t"] < 0 and not j.no_chefe, "Enter: corre de novo (sem lutar de novo)")
j.coracoes = 1
j.ribbat.invuln = 0
j.ribbat.machucar(j, j.ribbat.cx + 10)
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "jogando" and j.corrida is not None, "game over na corrida: recomeça a corrida")
j = rb.Jogo()
j.tecla(pygame.K_F6, Entrada())
checa(j.estado == "chefe" and j.chefe_mod is AG, "F6 no título: atalho pra Águia")

print("Mosquitos de cura (todas as lutas)")
from entidades import Mosquito  # noqa: E402
for indice, nome in ((0, "Viúva"), (1, "Besouro"), (2, "Rainha"), (4, "Águia")):
    random.seed(1)
    j = rb.Jogo()
    j.fase_atual = MENU_FASES[indice]
    j.comecar_chefe()
    apareceu = False
    for i in range(60 * 20):
        j.ribbat.invuln = 9
        j.coracoes = j.coracoes_max
        j.atualizar(1 / 60, Entrada())
        if j.mosquitos:
            apareceu = True
            break
    checa(apareceu, f"luta com a {nome}: aparece mosquito de cura ({i / 60:.0f}s)")
j.coracoes = 2
m = Mosquito(1, j.ribbat.y + 10)
m.x = j.ribbat.cx - 30
j.mosquitos = [m]
rodar(j, 0.5)
checa(j.coracoes == 3 and not j.mosquitos, "pegou o mosquito: +1 coração")
foto(j, "mosquito")
j.coracoes = j.coracoes_max
m = Mosquito(1, j.ribbat.y + 10)
m.x = j.ribbat.cx - 30
j.mosquitos = [m]
rodar(j, 0.5)
checa(j.coracoes == j.coracoes_max, "com a vida cheia, não passa do máximo")

j = luta_rainha()
b = j.boss
b.vida = 1
b.levar(2, j)
rodar(j, 2.2)
b.vida = 1
b.levar(2, j)
rodar(j, 2.0)
b.levar(2, j)
rodar(j, 1.5)
foto(j, "rainha_morrendo")
checa(b.estado == "morrendo" and b.y >= RA.CHAO_Y - 31, "a Rainha cai deitada no chão (sem virar de cabeça pra baixo)")

print("Menu e save")
import menu as MENU  # noqa: E402
import progresso as PR  # noqa: E402
if os.path.exists(SAVE_TESTE):
    os.remove(SAVE_TESTE)
j = rb.Jogo()
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "menu", "Enter no título abre o menu de fases")
foto(j, "menu_novo")
j.tecla(pygame.K_DOWN, Entrada())
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "menu" and j.menu_tremor > 0, "chefão trancado enquanto a fase não foi zerada")
j.tecla(pygame.K_RIGHT, Entrada())
j.tecla(pygame.K_UP, Entrada())
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "menu", "Lamaçal (fase 2) trancado até zerar o pântano")
j.tecla(pygame.K_LEFT, Entrada())
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "quadrinho", "primeira vez na fase mostra a história")
j.estado = "jogando"
j.ribbat.x = j.fase.toca.x
j.atualizar(1 / 60, Entrada())
checa(j.estado == "fim" and PR.carregar()["fases"]["fase1"]["zerada"], "chegar na toca salva a fase como zerada")
j = rb.Jogo()
checa(PR.fase(j.progresso, "fase1")["zerada"], "abrindo o jogo de novo, o save lembra")
j.estado = "menu"
j.tecla(pygame.K_DOWN, Entrada())
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "chefe" and j.tem_investida and j.coracoes_max == 4, "fase zerada: dá pra pular direto pro chefão")
j.boss.estagio, j.boss.vida = 2, 1
j.boss.estado = "andando"
j.boss.levar(3, j)
rodar(j, 3.5)
checa(j.estado == "vitoria" and PR.carregar()["fases"]["fase1"]["chefe"], "vencer a Viúva salva no save")
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "menu", "depois da vitória volta pro menu")
j.tecla(pygame.K_RIGHT, Entrada())
j.tecla(pygame.K_UP, Entrada())
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "jogando" and j.fase.tema == "lamacal", "pântano zerado: Lamaçal abre (sem história, direto)")
j.ribbat.x = j.fase.toca.x
j.atualizar(1 / 60, Entrada())
checa(j.estado == "fim", "chegar na toca do besouro termina a fase 2")
foto(j, "fim_lamacal")
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "chefe" and j.chefe_mod is BS and PR.carregar()["fases"]["fase2"]["zerada"],
      "Lamaçal salvo como zerado e Enter na toca leva pro Besouro")
j.tecla(pygame.K_ESCAPE, Entrada())
j.tecla(pygame.K_m, Entrada())
foto(j, "menu_3")
j.tempo_total = 1.0
foto(j, "menu_zerado")

print("Relógio e recordes de tempo")
if os.path.exists(SAVE_TESTE):
    os.remove(SAVE_TESTE)
j = rb.Jogo()
j.fase_atual = MENU.FASES[0]
j.comecar_fase()
j.estado = "jogando"
rodar(j, 2.0)
checa(abs(j.tempo_fase - 2.0) < 0.05, f"o relógio da fase conta o tempo jogando ({j.tempo_fase:.2f}s)")
j.estado = "pausa"
rodar(j, 1.0)
checa(abs(j.tempo_fase - 2.0) < 0.05, "na pausa o relógio para")
j.estado = "jogando"
j.coracoes = 1
j.ribbat.invuln = 0
j.ribbat.machucar(j, j.ribbat.cx + 10)
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "jogando" and j.tempo_fase > 1.9, "game over na fase NÃO zera o relógio (é o tempo do caminho todo)")
j.tempo_fase = 90.0
j.ribbat.x = j.fase.toca.x
j.atualizar(1 / 60, Entrada())
checa(PR.carregar()["fases"]["fase1"]["tempo"] == 90.02 and j.ultimo_tempo[1], "chegar na toca salva o recorde da fase")
j.comecar_fase()
j.estado = "jogando"
checa(j.tempo_fase == 0, "começar a fase de novo zera o relógio")
j.tempo_fase = 120.0
j.ribbat.x = j.fase.toca.x
j.atualizar(1 / 60, Entrada())
checa(PR.carregar()["fases"]["fase1"]["tempo"] == 90.02 and not j.ultimo_tempo[1], "tempo pior não apaga o recorde")
j.tecla(pygame.K_RETURN, Entrada())
rodar(j, 3.0)
checa(j.estado == "chefe" and abs(j.tempo_chefe - 3.0) < 0.05, "o chefão tem relógio próprio")
j.coracoes = 1
j.ribbat.invuln = 0
j.ribbat.machucar(j, j.ribbat.cx + 10)
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "chefe" and j.tempo_chefe == 0, "perdeu a luta e recomeçou: o relógio da luta zera")
rodar(j, 1.0)
j.boss.estagio, j.boss.vida = 2, 1
j.boss.estado = "andando"
j.boss.levar(3, j)
rodar(j, 3.5)
rec = PR.carregar()["fases"]["fase1"].get("tempo_chefe")
checa(j.estado == "vitoria" and rec and 4 < rec < 5, f"vencer o chefão salva o recorde da luta ({rec}s)")
checa(abs(PR.tempo_total(PR.carregar()) - (90.02 + rec)) < 0.01, "tempo total = soma de todos os recordes")
foto(j, "tempo_vitoria")
j = rb.Jogo()
j.fase_atual = MENU.FASES[4]
j.comecar_chefe()
rodar(j, 1.0)
j.comecar_corrida()
rodar(j, 1.0)
checa(abs(j.tempo_chefe - 2.0) < 0.05, "na Águia, a corrida continua o relógio da luta")
j.estado = "menu"
foto(j, "tempo_menu")

print("Música")
import som as SOM  # noqa: E402
strudel = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "musica", "chefe.strudel.js"), encoding="utf-8").read()
cam = SOM.MUSICAS["chefe"]["camadas"]
checa(f'n("{cam[0]["n"]}")' in strudel and f'"{cam[1]["s"]}, {cam[2]["s"]}"' in strudel and "setcps(0.55)" in strudel,
      "a música dos chefões é a mesma que o Gomes escreveu no Strudel")
notas = [v for _, _, v in SOM.passos(cam[0]["n"])]
checa(notas == ["3", "5", "7", "0", "1", "1", "3", "5"] and len(SOM.passos("hh*6")) == 6, "lê as notas, os silêncios (~) e o *6")
checa([SOM.midi("A3") + SOM.ESCALAS["minor"][g] for g in (0, 3, 5)] == [57, 62, 65], "escala A3:minor: lá, ré, fá")
dados = SOM.renderizar(SOM.MUSICAS["chefe"])
checa(abs(len(dados) / SOM.TAXA - 1 / 0.55) < 0.01 and max(dados) > 20000 and max(dados) <= 32767,
      f"uma volta da música dura {len(dados) / SOM.TAXA:.2f}s (setcps 0.55) e não estoura o volume")
j = luta_aguia()
checa(SOM.musica_do_jogo(j) == "chefe", "na luta toca a música dos chefões")
j.voltar_para, j.estado = "chefe", "pausa"
checa(SOM.musica_do_jogo(j) == "chefe", "na pausa da luta ela continua (mais baixinha)")
j = rb.Jogo()
j.fase_atual = MENU_FASES[4]
j.comecar_corrida()
checa(SOM.musica_do_jogo(j) == "chefe", "na corrida contra a Águia também")
j = rb.Jogo()
j.estado = "jogando"
checa(SOM.musica_do_jogo(j) == "fase" and SOM.musica_do_jogo(rb.Jogo()) is None, "nas fases toca a música das fases (no menu, silêncio)")
strudel = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "musica", "fase.strudel.js"), encoding="utf-8").read()
cf = SOM.MUSICAS["fase"]["camadas"][0]
checa(f'n("{cf["n"]}")' in strudel and "setcps(0.30)" in strudel and ".room(0.40)" in strudel and cf["room"] == 0.40,
      "a música das fases é a mesma do Strudel do Gomes (com o eco)")
dados = SOM.renderizar(SOM.MUSICAS["fase"])
checa(abs(len(dados) / SOM.TAXA - 1 / 0.30) < 0.01 and dados[0] != 0,
      f"uma volta dura {len(dados) / SOM.TAXA:.2f}s e o eco do fim já soa no começo (loop sem emenda)")

print("Efeitos, medalhas, fantasma, loja e maratona")
import json  # noqa: E402
import shutil  # noqa: E402
import medalhas as MD_  # noqa: E402
import chapeus as CP_  # noqa: E402
checa(len(SOM.EFEITOS) >= 12 and all(len(SOM.fabricar_efeito(n)) > 1000 for n in ("pulo", "lingua", "mosca")),
      "os efeitos de som são fabricados pelo código")
SOM.efeito("pulo")                                       # sem som ligado (teste): não pode quebrar
robo_fases = {"fase1": 68, "fase2": 50, "fase3": 50, "fase4": 46, "fase5": 45}
robo_chefes = {"fase1": 53, "fase2": 46, "fase3": 60, "fase4": 49, "fase5": 57 + 33}
checa(all(MD_.METAS[f]["tempo"][0] >= robo_fases[f] * 1.4 and MD_.METAS[f]["tempo_chefe"][0] >= robo_chefes[f] * 1.4
          for f in robo_fases), "ouro dá pra pegar com folga (pelo menos 1.4x o tempo do robô)")
checa(MD_.medalha("fase1", "tempo", 60) == "ouro" and MD_.medalha("fase1", "tempo", 130) == "prata"
      and MD_.medalha("fase1", "tempo", 999) == "bronze" and MD_.proxima("fase1", "tempo", 130) == ("ouro", 100),
      "medalhas: ouro, prata, bronze e a próxima meta")
if os.path.exists(SAVE_TESTE):
    os.remove(SAVE_TESTE)
shutil.rmtree(os.path.join(os.path.dirname(os.path.abspath(SAVE_TESTE)), "fantasmas"), ignore_errors=True)
random.seed(0)
j = rb.Jogo()
j.fase_atual = MENU.FASES[0]
j.comecar_fase()
j.estado = "jogando"
ESTADO_ROBO.clear()
for i in range(60 * 120):
    j.atualizar(1 / 60, robo(j))
    if j.estado != "jogando":
        break
if j.estado != "fim":                                    # o robô não é perfeito: termina com corações infinitos
    j.comecar_fase()
    j.estado = "jogando"
    ESTADO_ROBO.clear()
    for i in range(60 * 120):
        j.coracoes = 99
        j._coracoes_visto = 99
        j.atualizar(1 / 60, robo(j))
        if j.estado != "jogando":
            break
checa(j.estado == "fim", f"robô zerou a fase 1 ({j.tempo_fase:.0f}s, sem dano: {j.sem_dano})")
reg = PR.carregar()["fases"]["fase1"]
fant = PR.carregar_fantasma("fase1")
checa(fant and abs(len(fant) - j.tempo_fase * rb.FANTASMA_HZ) < 3, "bateu o recorde: o caminho virou o fantasma")
checa(reg.get("sem_dano") == j.sem_dano and j.ultimo_tempo[3] == j.sem_dano, "coração de sem dano salvo certo")
checa(PR.carregar()["carteira"] == len(j.moscas_pegas), f"as moscas da fase viram dinheiro ({len(j.moscas_pegas)})")
foto(j, "fim_medalha")
j.comecar_fase()
j.estado = "jogando"
checa(j.fantasma and j.mostrando_fantasma(), "na próxima vez o sapo fantasma aparece")
rodar(j, 2.0)
x, y = j.fantasma[int(j.tempo_fase * rb.FANTASMA_HZ)][:2]
checa(x > j.fase.inicio[0], "o fantasma anda pelo caminho do recorde")
foto(j, "fantasma")
j.tecla(pygame.K_g, Entrada())
checa(not j.mostrando_fantasma(), "a tecla G esconde o fantasma")
j.coracoes = 3
j.ribbat.invuln = 0
j.ribbat.machucar(j, j.ribbat.cx + 10)
rodar(j, 0.1)
checa(not j.sem_dano, "levou dano: perde o coração de sem dano")
# carteira de save antigo, loja
dados = {"fases": {"fase1": {"zerada": True, "chefe": True, "moscas": 20},
                   "fase2": {"zerada": True, "chefe": False, "moscas": 13}}}
with open(SAVE_TESTE, "w", encoding="utf-8") as fh:
    json.dump(dados, fh)
j = rb.Jogo()
checa(j.progresso["carteira"] == 33 and j.progresso["chapeu"] == "nenhum",
      "save antigo: as moscas que já tinha viram 33 de dinheiro")
j.estado = "menu"
j.menu_j = 1
j.tecla(pygame.K_DOWN, Entrada())
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "loja", "seta pra baixo no menu leva pra loja")
nomes = [n for n, _ in CP_.CHAPEUS]
j.loja_i = nomes.index("folha")
j.tecla(pygame.K_RETURN, Entrada())
checa(PR.carregar()["carteira"] == 18 and PR.carregar()["chapeu"] == "folha", "comprou a folha (15): sobram 18 e já veste")
j.loja_i = nomes.index("coroa")
j.tecla(pygame.K_RETURN, Entrada())
checa(PR.carregar()["carteira"] == 18 and "coroa" not in PR.carregar()["chapeus"] and j.loja_tremor > 0,
      "sem mosca suficiente não compra (a loja treme)")
j.loja_i = 0
j.tecla(pygame.K_RETURN, Entrada())
j.loja_i = nomes.index("folha")
j.tecla(pygame.K_RETURN, Entrada())
checa(PR.carregar()["carteira"] == 18 and PR.carregar()["chapeu"] == "folha", "o que já comprou veste de graça")
foto(j, "loja")
for nm in nomes:
    CP_.desenhar(tela, nm, 300, 300, -1, 0.85, pose="pulo")
checa(True, "todos os chapéus desenham")
j.tecla(pygame.K_ESCAPE, Entrada())
j.menu_j = 0
j.tecla(pygame.K_UP, Entrada())
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "menu" and j.menu_tremor > 0, "maratona trancada até vencer os 5 chefões")
p = PR.carregar()
for f in MENU.FASES:
    PR.fase(p, f["id"]).update(zerada=True, chefe=True)
PR.salvar(p)
j = rb.Jogo()
j.estado = "menu"
j.menu_j = -1
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "chefe" and j.chefe_mod is CH and j.maratona["i"] == 0, "seta pra cima no menu: a maratona começa pela Viúva")
j.coracoes = 2
j.boss.estagio, j.boss.vida = 2, 1
j.boss.estado = "andando"
j.boss.levar(3, j)
for i in range(60 * 4):
    j.ribbat.invuln = 9
    j.atualizar(1 / 60, Entrada())
checa(j.estado == "chefe" and j.chefe_mod is BS and j.coracoes == 2 and j.maratona["i"] == 1,
      "venceu a Viúva: vai direto pro Besouro, com os mesmos corações")
checa(j.maratona["t"] > 3.9, f"o relógio da maratona continua ({j.maratona['t']:.1f}s)")
foto(j, "maratona")
j.coracoes = 1
j.ribbat.invuln = 0
j.ribbat.machucar(j, j.ribbat.cx + 10)
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "chefe" and j.chefe_mod is CH and j.maratona["t"] == 0, "game over na maratona: começa tudo de novo")
j.maratona.update(i=4, t=500.0)
j.fase_atual = MENU.FASES[4]
j.iniciar_chefe()
j.coracoes = 3
j.comecar_corrida()
checa(j.coracoes == 3 and j.maratona, "na corrida da maratona os corações não enchem")
j.ribbat.x = j.fase.toca.x
j.corrida["t"] = 5
j.atualizar(1 / 60, Entrada())
checa(j.estado == "maratona_fim" and PR.carregar()["maratona"] > 500, "chegou no pergaminho: maratona completa e recorde salvo")
foto(j, "maratona_fim")
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "menu" and j.maratona is None, "depois volta pro menu")

print("Mapa do mundo e álbum de conquistas")
import conquistas as CQ  # noqa: E402
if os.path.exists(SAVE_TESTE):
    os.remove(SAVE_TESTE)
j = rb.Jogo()
j.estado = "menu"
checa(MENU.ordem_mapa(j) == [0, 1, 2, 3, 4] and MENU.alcance_mapa(j) == [0, 1],
      "mapa novo: a casa do Vô escondida, e só dá pra andar até o 1º lugar trancado")
j.tecla(pygame.K_RIGHT, Entrada())
j.tecla(pygame.K_RIGHT, Entrada())
checa(j.menu_i == 1, "andando pro lado o Ribbat vai pro próximo lugar (e para no trancado)")
rodar(j, 0.5)
foto(j, "mapa")
p = PR.carregar()
for f in MENU.FASES[:5]:
    PR.fase(p, f["id"]).update(zerada=True, chefe=True)
PR.salvar(p)
j = rb.Jogo()
j.estado = "menu"
checa(MENU.ordem_mapa(j)[0] == 5, "zerou o jogo: a casa do Vô aparece no começo do caminho")
j.menu_i = 0
j.tecla(pygame.K_LEFT, Entrada())
checa(j.menu_i == 5 and j.menu_j == 1, "na casa do Vô só tem o botão do chefão")
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "chefe" and j.chefe_mod is VV, "Enter na casa do Vô: luta com o Vô")
foto(j, "vovo_luta")

# álbum: cada figurinha dá pra conseguir
if os.path.exists(SAVE_TESTE):
    os.remove(SAVE_TESTE)
d = PR.carregar()
checa(CQ.conferir(d) == [], "save novo: nenhuma figurinha ainda")
for f in CQ.FASES_IDS:
    checa(CQ.total_moscas(f) > 0, f"{f}: tem {CQ.total_moscas(f)} moscas pra pegar")
PR.fase(d, "fase3")["moscas"] = CQ.total_moscas("fase3")
PR.fase(d, "fase2")["sem_dano"] = True
PR.fase(d, "fase4")["sem_dano_chefe"] = True
for f in CQ.FASES_IDS:
    r_ = PR.fase(d, f)
    r_.update(zerada=True, chefe=True, tempo=MD_.METAS[f]["tempo"][0] - 1, tempo_chefe=MD_.METAS[f]["tempo_chefe"][0] - 1)
d["maratona"] = 299.0
d["chapeus"] = [n for n, _ in CP_.CHAPEUS]
d["bateu_fantasma"] = True
d["venceu_de_coelho"] = True
PR.fase(d, "secreta")["chefe"] = True
for nome, n in (("inimigos", 100), ("teias", 15), ("mosquitos", 10), ("pedras", 10)):
    CQ.contar(d, nome, n)
novas = CQ.conferir(d)
checa(sorted(novas) == sorted(CQ.IDS), f"as {len(CQ.IDS)} figurinhas dá pra conseguir ({len(novas)} conseguidas)")
checa(sum(CP_.PRECO.values()) < 600, f"todos os chapéus custam {sum(CP_.PRECO.values())} moscas (dá pra juntar jogando)")
checa(min(MD_.METAS[f]["tempo_chefe"][0] for f in CQ.FASES_IDS) > 0, "ouro em todos os chefões tem meta de verdade")

# contadores de verdade, pelo jogo
if os.path.exists(SAVE_TESTE):
    os.remove(SAVE_TESTE)
j = rb.Jogo()
j.fase_atual = MENU.FASES[0]
j.comecar_fase()
j.estado = "jogando"
f0 = Formiga(j.ribbat.x + 60, j.ribbat.y)
j.fase.inimigos.append(f0)
j.derrotar(f0)
checa(CQ.contador(j.progresso, "inimigos") == 1, "derrotar um bicho conta pro álbum")
for k in range(99):
    j.contar("inimigos")
checa("inimigos" in j.progresso["conquistas"] and j.avisos_conquista, "100 bichos: figurinha nova (e o aviso aparece no canto)")
rodar(j, 0.5)
foto(j, "figurinha_nova")
checa(PR.carregar()["contadores"]["inimigos"] == 100, "a figurinha nova fica salva")
rodar(j, 3.5)
checa(not j.avisos_conquista, "o aviso some sozinho")
j.estado = "menu"
j.menu_j = 0
j.tecla(pygame.K_UP, Entrada())
j.tecla(pygame.K_RIGHT, Entrada())
j.tecla(pygame.K_RETURN, Entrada())
checa(j.estado == "album", "no mapa: seta pra cima, depois pro lado = o álbum")
foto(j, "album")
j.tecla(pygame.K_ESCAPE, Entrada())
checa(j.estado == "menu", "Esc volta pro mapa")

print("Telas")
for estado, paineis in (("titulo", 0), ("menu", 0), ("quadrinho", 4), ("pausa", 0), ("gameover", 0),
                        ("fim", 0), ("vitoria", 0), ("final", 4)):
    j = rb.Jogo()
    j.estado = estado
    j.voltar_para = "jogando"
    j.hq_paineis, j.hq_alfa = paineis, 1.0
    j.tempo_total = 0.2
    foto(j, f"tela_{estado}")
    j.desenhar(tela)
checa(True, "todas as telas desenham sem erro")

print("\nTUDO CERTO!" if not erros else f"\n{len(erros)} ERRO(S)")
sys.exit(1 if erros else 0)
