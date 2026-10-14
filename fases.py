"""
Fases do Ribbat, desenhadas com letras.

Cada fase é uma lista de PEDAÇOS colados um do lado do outro.
Cada pedaço é desenhado de cima pra baixo. Não precisa escrever as linhas
vazias do topo: o jogo completa sozinho até ter 17 linhas.
As 3 últimas linhas de cada pedaço são o chão.

Legenda:
  .  vazio
  #  terra (chão)
  =  plataforma de madeira
  X  pedra (vários X juntos viram UMA pedrona; só quebra com a INVESTIDA)
  ^  espinhos
  w  teia grudenta no chão (deixa o Ribbat lento)
  ~  água do lago (cair = perde 1 coração e volta pro último chão firme)
  v  vitória-régia (boia na água; afunda se ficar parado em cima)
  r  raiz (plataforma que dá pra atravessar pulando por baixo)
  K  caixa (sólida: caixa térmica embaixo da mesa do churrasco)
  F  canteiro de flores (com abelha: pisou, ela te persegue)
  M  o moço do churrasco (a mão dele bate de cima)
  P  pássaro (gavião: trava a mira e mergulha)
  p  peixe (mora na água embaixo dessa coluna e pula pra fora)
  S  onde o Ribbat começa
  C  bandeira (checkpoint) - a 1ª dá linguada, a 2ª investida, a 3ª +1 coração
  o  mosca (coletável)
  f  formiga (formigas perto umas das outras se avisam e atacam juntas)
  a  aranha (pendurada no fio, atira teia)
  B  toca do chefão (fim da fase)

Os formigueiros vão ganhar uma fase só deles (a Colônia).
"""

ALTURA = 17


def montar(pedacos, teto=0):
    """Cola os pedaços lado a lado e devolve as 17 linhas da fase.
    teto = quantas linhas de terra em cima (fase subterrânea)."""
    linhas = [""] * ALTURA
    for p in pedacos:
        assert len(p) <= ALTURA, "pedaço com mais de 17 linhas"
        largura = max(len(l) for l in p)
        completo = ["." * largura] * (ALTURA - len(p)) + [l.ljust(largura, ".") for l in p]
        for i in range(ALTURA):
            linhas[i] += completo[i]
    for i in range(teto):
        linhas[i] = "#" * len(linhas[i])
    return linhas


CHAO = "#" * 80   # chão pronto pra cortar ([:largura]). Tem que ser maior que o maior pedaço!

# ---------------------------------------------------------------- FASE 1
COMECO = [
    "..................o.o.o.........",
    ".................=====..........",
    "................................",
    "..........o.o.o.................",
    ".........=====..................",
    "..S.....................f.......",
    CHAO[:32],
    CHAO[:32],
    CHAO[:32],
]

BURACOS = [
    "...............o.o.o............",
    "..............=====.............",
    "..........o.o...................",
    ".....f......f..f..^^........f...",
    "##########....##########...#####",
    "##########....##########...#####",
    "##########....##########...#####",
]

BANDEIRA_1 = [
    "......................o.o.o.......",
    ".....................=======......",
    "..................................",
    "..........a....................a..",
    "...............====...............",
    "..................................",
    "..C...................ww....f.....",
    CHAO[:34],
    CHAO[:34],
    CHAO[:34],
]

PONTE = [
    "......................o.o...........",
    "......a....................a........",
    "...........o.o......................",
    "..........====..........o.o.o.......",
    "...f.............................f..",
    "########.........#####....##########",
    "########.........#####....##########",
    "########.........#####....##########",
]

LAMACAL = [
    ".....................o.o.o..........",
    "....................=====...........",
    "....................................",
    "..............p.....................",
    "......f.f...vv.vv..........f........",
    "##########" + "~" * 8 + "#" * 18,
    "##########" + "~" * 8 + "#" * 18,
    "##########" + "~" * 8 + "#" * 18,
]

# o lago grande: vitórias-régias, peixes e uma ilhota no meio
LAGO = [
    "..........o....o....o....o............o....o....o....o......",
    "..........p.........p.....p......p.........p....p...........",
    "..f....vv...vv...vv...vv......f....vv...vv...vv...vv........",
    "######" + "~" * 22 + "####" + "~" * 24 + "####",
    "######" + "~" * 22 + "####" + "~" * 24 + "####",
    "######" + "~" * 22 + "####" + "~" * 24 + "####",
]

# campo das formigas: dois grupos, e plataformas onde elas montam torre
CAMPO_FORMIGAS = [
    "......................o.o.o.............",
    ".....................=======............",
    "..........====..........................",
    "........................................",
    "....f.f.f..............f.f.f............",
    CHAO[:40],
    CHAO[:40],
    CHAO[:40],
]

BREJO = [
    "........a...............a..............a...",
    "...................====.....................",
    "............o.o.o...........................",
    "....ww..............f.f...ww.......^^.......",
    "##############....##########################",
    "##############....##########################",
    "##############....##########################",
]

# segundo lago: um tronco boiando no meio do vão grande
LAGO_2 = [
    "..........................o.o...................",
    "..........................====..................",
    "............p.....p.....p......p.....p..........",
    ".......vvv....vv....vv...........vv....vv.......",
    "####" + "~" * 40 + "####",
    "####" + "~" * 40 + "####",
    "####" + "~" * 40 + "####",
]

# barranco com um túnel embaixo, tampado por uma pedrona
PEDRA = [
    "..................##############....",
    "..................##############....",
    "..................##############....",
    "..................##############....",
    "......====........XX....o.o.o.......",
    "..C.......f.f.f...XX..........f.....",
    CHAO[:36],
    CHAO[:36],
    CHAO[:36],
]

RETA_FINAL = [
    ".........................o.o.o..........",
    ".........a..............=======.........",
    ".....====...............................",
    "........................................",
    "..C.........^^.....f.....ww.f.f.....f...",
    "#####################....###############",
    "#####################....###############",
    "#####################....###############",
]

TOCA = [
    "..............B.........",
    CHAO[:24],
    CHAO[:24],
    CHAO[:24],
]

FASE_1 = {
    "nome": "Fase 1 - Bosque do Brejo",
    "tema": "pantano",
    "pedacos": [COMECO, BURACOS, LAMACAL, BANDEIRA_1, PONTE, LAGO, CAMPO_FORMIGAS, PEDRA, BREJO, LAGO_2,
                RETA_FINAL, TOCA],
}

# ---------------------------------------------------------------- FASE 2: TERRENO DE LAMAÇAL
# Aqui "~" é lama movediça, "r" é tronco boiando, "u" é lama grudenta e "m" é peixe-lama escondido.
L_INICIO = [
    "..................o.o.o...........",
    ".................=====............",
    "..................................",
    "..........o.o.o...................",
    "..S..................m.......f....",
    CHAO[:34],
    CHAO[:34],
    CHAO[:34],
]

L_POCAS = [
    "..........o.o..........o.o..........",
    "....................................",
    ".....f.....rrr..........rrr....m....",
    "########" + "~" * 10 + "###" + "~" * 10 + "#####",
    "########" + "~" * 10 + "###" + "~" * 10 + "#####",
    "########" + "~" * 10 + "###" + "~" * 10 + "#####",
]

L_BANDEIRA_1 = [
    ".....................o.o.o........",
    "....................=====.........",
    "..................................",
    "..C.......m.....m.....f.f.f.......",
    CHAO[:34],
    CHAO[:34],
    CHAO[:34],
]

L_GRUDE = [
    "..............o.o.o.....................",
    ".............=====......................",
    "....uuuuuu.........muuuum.......f.f.....",
    CHAO[:40],
    CHAO[:40],
    CHAO[:40],
]

L_LAGO_LAMA = [
    "...........o.....o.....o.....o.....o........",
    "............................................",
    ".......rr....rr....rr....rr....rr...rr......",
    "####" + "~" * 36 + "####",
    "####" + "~" * 36 + "####",
    "####" + "~" * 36 + "####",
]

L_RIACHO = [
    "........o.o.o...................",
    "...m....rrr.......f......rr.....",
    "######" + "~" * 7 + "#" * 10 + "~" * 6 + "###",
    "######" + "~" * 7 + "#" * 10 + "~" * 6 + "###",
    "######" + "~" * 7 + "#" * 10 + "~" * 6 + "###",
]

# paredão de barro com túnel (e um peixe-lama escondido lá dentro!)
L_PAREDAO = [
    "..................##############....",
    "..................##############....",
    "..................##############....",
    "..................##############....",
    "......====........XX....o.o.o.......",
    "..C.......f.f.....XX.....m.....f....",
    CHAO[:36],
    CHAO[:36],
    CHAO[:36],
]

L_FORMIGAS = [
    "........o.o.o...........................",
    ".......=====.............====...........",
    "........................................",
    "...f.f.f.....m.....uuuu....f.f.f....m...",
    CHAO[:40],
    CHAO[:40],
    CHAO[:40],
]

L_FINAL = [
    "................o.o.o...................",
    "...............=====....................",
    "..C.....m.....^^.......f.f.....m....m...",
    "#" * 27 + "..." + "#" * 10,
    "#" * 27 + "..." + "#" * 10,
    "#" * 27 + "..." + "#" * 10,
]

FASE_2 = {
    "nome": "Fase 2 - Terreno de Lamaçal",
    "tema": "lamacal",
    "pedacos": [L_INICIO, L_POCAS, L_BANDEIRA_1, L_GRUDE, L_LAGO_LAMA, L_RIACHO, L_PAREDAO, L_FORMIGAS,
                L_FINAL, TOCA],
}

# ---------------------------------------------------------------- FASE 3: O FORMIGUEIRO (a Colônia)
# Fase subterrânea: as 3 primeiras linhas viram teto de terra ("teto": 3).
# "r" é raiz (plataforma que dá pra atravessar por baixo), "u" aqui é MELADO, "H" é buraco de formigueiro
# (tampa com a investida) e "g" é formiga guerreira (voa e dá investida).
F_ENTRADA = [
    "..................o.o.o...........",
    ".................rrrrr............",
    "..................................",
    "..........o.o.o...................",
    "..S..........f.f.........H......f.",
    CHAO[:34],
    CHAO[:34],
    CHAO[:34],
]

F_POCOS = [
    "..............g.....................",
    "....................................",
    "..........o.o.o.....................",
    "...........rrr.........rrr..........",
    "....................................",
    "....f...............................",
    "########......#######......#########",
    "########......#######......#########",
    "########......#######......#########",
]

F_BANDEIRA_1 = [
    "........................g.........",
    "..................................",
    "..................................",
    "................rrrr..............",
    "..................................",
    "..C.......H..........f.f.f........",
    CHAO[:34],
    CHAO[:34],
    CHAO[:34],
]

F_MEL = [
    "....................################....",
    "....................################....",
    "....................################....",
    "........................................",
    "........................................",
    "........................................",
    ".............................g..........",
    "......o.o.o.............................",
    ".....rrrrr..............................",
    "........................................",
    "...uuuu.......f.f...uuuuuu..........f...",
    CHAO[:40],
    CHAO[:40],
    CHAO[:40],
]

F_CAMARA = [
    "......g...............g.....................",
    "............................................",
    "............................................",
    "...........o.o.o...........o.o.o............",
    "..........rrrrr...........rrrrr.............",
    "............................................",
    "...f.f.f.....H.......f.f.........H....f.....",
    CHAO[:44],
    CHAO[:44],
    CHAO[:44],
]

F_PAREDAO = [
    "..................##############....",
    "..................##############....",
    "..................##############....",
    "..................##############....",
    "......rrrr........XX....o.o.o.......",
    "..C.......f.f.....XX....g......f....",
    CHAO[:36],
    CHAO[:36],
    CHAO[:36],
]

F_TUNEL = [
    "#" * 40,
    "#" * 40,
    "#" * 40,
    "#" * 40,
    "#" * 40,
    "........................................",
    "........................................",
    ".......o.o.o.................o.o.o......",
    "........................................",
    "......................g.................",
    "....f.f.f.......H..........f.f.f........",
    CHAO[:40],
    CHAO[:40],
    CHAO[:40],
]

F_GALERIAS = [
    "...........g..............g.............",
    "........................................",
    "........................................",
    ".......rrr......rrr.........rrr.........",
    "........................................",
    "..f.....................................",
    "#####......####.....####......##########",
    "#####......####.....####......##########",
    "#####......####.....####......##########",
]

F_FINAL = [
    "....................g...................",
    "........................................",
    "...............o.o.o....................",
    "..............rrrrr.....................",
    "........................................",
    "..C.....H.......f.f.f.....uuuu.....f....",
    CHAO[:40],
    CHAO[:40],
    CHAO[:40],
]

FASE_3 = {
    "nome": "Fase 3 - O Formigueiro",
    "tema": "formigueiro",
    "teto": 3,
    "pedacos": [F_ENTRADA, F_POCOS, F_BANDEIRA_1, F_MEL, F_CAMARA, F_PAREDAO, F_TUNEL, F_GALERIAS, F_FINAL, TOCA],
}

# ---------------------------------------------------------------- FASE 4: O QUINTAL
# "F" canteiro de flores (abelha!), "K" caixa térmica, "M" o moço do churrasco (a mão bate de cima),
# "=" aqui é a mesa com toalha xadrez, "~" a piscininha e "r" as boias.
Q_INICIO = [
    "..................o.o.o...........",
    ".................=====............",
    "..................................",
    "..........o.o.o...................",
    "..S.............FFF.......f.f.....",
    CHAO[:34],
    CHAO[:34],
    CHAO[:34],
]

Q_FLORES = [
    "...........o.o.o..............o.o.......",
    "..........=====..............=====......",
    "........................................",
    "........................................",
    "....FFFFF.......FFFF.........FFFFF......",
    CHAO[:40],
    CHAO[:40],
    CHAO[:40],
]

Q_BANDEIRA_1 = [
    "....................o.o.o.........",
    "...................=====..........",
    "..................................",
    "..................................",
    "..C.......f.f.f.......FFF.........",
    CHAO[:34],
    CHAO[:34],
    CHAO[:34],
]

Q_PISCINA = [
    "..........o.....o.....o.....o...........",
    "........................................",
    ".......rr....rr....rr....rr....rr.......",
    "#####" + "~" * 30 + "#####",
    "#####" + "~" * 30 + "#####",
    "#####" + "~" * 30 + "#####",
]

Q_CHURRASCO = [
    "........................M.......................",
    "................................................",
    "................................................",
    "................................................",
    "................................................",
    "...........o.o.o..........o.o.o.......o.o.......",
    "........================================........",
    "....===.KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK........",
    "........KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK..f.....",
    CHAO[:48],
    CHAO[:48],
    CHAO[:48],
]

Q_PAREDAO = [
    "..................##############....",
    "..................##############....",
    "..................##############....",
    "..................##############....",
    "......====........XX....o.o.o.......",
    "..C.......f.f.....XX.........FF.....",
    CHAO[:36],
    CHAO[:36],
    CHAO[:36],
]

Q_JARDIM = [
    "..............o.o.o.....................",
    ".............=====......................",
    "........................................",
    "........................................",
    "...FFFF.....f.f......FFFFFF......f......",
    "#####################....###############",
    "#####################....###############",
    "#####################....###############",
]

Q_GRAMA = [
    ".........o.o.o..............",
    "........=====...............",
    "............................",
    "............................",
    "...f.f.........FFF......f...",
    CHAO[:28],
    CHAO[:28],
    CHAO[:28],
]

Q_FINAL = [
    "................o.o.o...................",
    "...............=====....................",
    "........................................",
    "........................................",
    "..C.....FFFF.......f.f.f.....FFF....f...",
    CHAO[:40],
    CHAO[:40],
    CHAO[:40],
]

FASE_4 = {
    "nome": "Fase 4 - O Quintal",
    "tema": "quintal",
    "pedacos": [Q_INICIO, Q_FLORES, Q_BANDEIRA_1, Q_PISCINA, Q_CHURRASCO, Q_PAREDAO, Q_JARDIM, Q_GRAMA, Q_FINAL, TOCA],
}


# ---------------------------------------------------------------- FASE 5: A MONTANHA (a última!)
# A montanha é desenhada diferente: cada pedaço diz a ALTURA do chão em cada coluna (em blocos)
# e onde ficam as coisas. O próximo pedaço começa na altura onde o anterior terminou, então a
# fase vai SUBINDO sozinha. A câmera sobe junto com o Ribbat.
#   degraus((largura, altura), ...)   -> alturas do chão (altura -1 = fenda funda: cair = perde coração)
#   coisas: {(coluna, linha): letra}  -> linha conta a partir do chão do começo do pedaço (0 = o chão)
#   Pra pôr algo EM CIMA de um degrau de altura h, use linha h + 1.


def degraus(*partes):
    alturas = []
    for largura, altura in partes:
        alturas += [altura] * largura
    return alturas


def encosta(alturas, coisas=None):
    """Monta as linhas de um pedaço da montanha a partir das alturas do chão de cada coluna."""
    coisas = coisas or {}
    topo = max(max(alturas), max((l for _, l in coisas), default=0)) + 1
    linhas = []
    for linha in range(topo - 1, -1, -1):
        s = ""
        for c, h in enumerate(alturas):
            ch = coisas.get((c, linha))
            if ch is None:
                ch = "#" if h >= 0 and linha <= h else "."
            s += ch
        linhas.append(s)
    return linhas


def montar_montanha(pedacos, altura):
    """Cola os pedaços subindo: o chão de cada um começa onde o anterior terminou.
    Embaixo do chão é tudo rocha, menos nas fendas (lá é buraco até lá embaixo)."""
    largura = sum(max(len(l) for l in p) for p in pedacos)
    grade = [["."] * largura for _ in range(altura)]
    base, x0 = altura - 1, 0
    for p in pedacos:
        w = max(len(l) for l in p)
        p = [l.ljust(w, ".") for l in p]
        h = len(p)
        for i, linha in enumerate(p):
            y = base - (h - 1 - i)
            if 0 <= y < altura:
                for c, ch in enumerate(linha):
                    grade[y][x0 + c] = ch
        for c in range(w):
            if p[-1][c] == "#":
                for y in range(base + 1, altura):
                    grade[y][x0 + c] = "#"
        topo_ultima = next(i for i in range(h) if p[i][w - 1] == "#")
        base -= (h - 1 - topo_ultima)
        x0 += w
    return ["".join(linha) for linha in grade]


M_BASE = encosta(degraus((30, 0)), {
    (2, 1): "S", (12, 1): "f", (14, 1): "f", (24, 1): "f",
    (12, 4): "o", (14, 4): "o", (16, 4): "o"})
M_DEGRAUS = encosta(degraus((8, 0), (8, 2), (6, 4), (6, 6)), {
    (8, 3): "^", (16, 5): "^", (17, 5): "^",
    (23, 8): "o", (25, 8): "o", (27, 8): "o", (24, 11): "P"})
M_FENDA = encosta(degraus((8, 0), (4, -1), (15, 0), (5, 3)), {
    (1, 1): "^", (2, 1): "^", (18, 1): "f", (20, 1): "f",
    (9, 4): "o", (11, 4): "o", (16, 8): "P"})
M_BANDEIRA_1 = encosta(degraus((26, 0), (4, 2)), {
    (2, 1): "C", (10, 1): "f", (12, 1): "f", (14, 1): "f",
    **{(c, 4): "r" for c in range(17, 22)}, (18, 6): "o", (20, 6): "o"})
M_PAREDAO = encosta(degraus((18, 0), (12, 6)), {
    (3, 1): "^", (4, 1): "^",
    **{(c, 2): "r" for c in range(12, 16)}, **{(c, 4): "r" for c in range(15, 18)},
    (6, 9): "P", (22, 8): "o", (24, 8): "o"})
M_ESPINHOS = encosta(degraus((4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (14, 5)), {
    (6, 2): "^", (13, 4): "^", (21, 6): "^", (27, 6): "^", (28, 6): "^",
    (25, 10): "P", (31, 6): "f", (17, 8): "o", (19, 8): "o"})
M_PEDRA = encosta(degraus((31, 0), (3, 3)), {
    (2, 1): "C", (10, 1): "f", (12, 1): "f",
    **{(c, l): "#" for c in range(18, 28) for l in range(3, 8)},
    (18, 1): "X", (19, 1): "X", (18, 2): "X", (19, 2): "X",
    (22, 1): "o", (24, 1): "o", (29, 1): "f"})
M_GAVIOES = encosta(degraus((6, 0), (3, -1), (5, 1), (3, -1), (5, 2), (3, -1), (9, 4)), {
    (27, 5): "^", (10, 4): "P", (19, 6): "P", (28, 9): "P",
    (7, 3): "o", (15, 4): "o", (23, 6): "o", (30, 5): "f"})
M_GELO = encosta(degraus((10, 0), (6, 2), (6, 4), (8, 4)), {
    (12, 3): "^", (13, 3): "^", (20, 5): "^", (26, 5): "^", (27, 5): "^",
    (5, 1): "f", (7, 1): "f", (29, 5): "f", (16, 8): "o", (18, 8): "o"})
M_BANDEIRA_3 = encosta(degraus((20, 0), (5, 2), (5, 4)), {
    (2, 1): "C", (10, 1): "f", (12, 1): "f", (16, 1): "^", (17, 1): "^", (14, 7): "P",
    (23, 4): "o", (27, 6): "o"})
M_CUME = encosta(degraus((6, 0), (6, 2), (6, 4), (16, 6)), {
    (8, 3): "^", (14, 5): "^", (24, 7): "B", (19, 9): "o", (21, 9): "o"})

FASE_5 = {
    "nome": "Fase 5 - A Montanha",
    "tema": "montanha",
    "montanha": True,
    "altura": 64,
    "pedacos": [M_BASE, M_DEGRAUS, M_FENDA, M_BANDEIRA_1, M_PAREDAO, M_ESPINHOS, M_PEDRA, M_GAVIOES, M_GELO,
                M_BANDEIRA_3, M_CUME],
}

# ---------------------------------------------------------------- A CORRIDA (depois de vencer a Águia)
# Lá no alto, acima das nuvens. A Águia joga o Ribbat pra cima e os dois apostam corrida até o
# PERGAMINHO (o "B" no fim). Feita com encosta() igual a Montanha, mas reta (cabe numa tela de altura).
# Aqui "r" é nuvem firme (atravessa por baixo): atalho com moscas, nunca obrigatória.


def pista(alturas, coisas=None):
    """Encosta com chão grossinho (3 blocos), pra corrida."""
    linhas = encosta(alturas, coisas)
    return linhas + [linhas[-1]] * 2


def _nuvem(c0, c1, linha):
    return {(c, linha): "r" for c in range(c0, c1)}


K_LARGADA = pista(degraus((14, 0), (3, -1), (9, 0), (4, 1), (4, 2), (6, 2)), {
    (2, 1): "S", (8, 3): "o", (10, 3): "o", (12, 3): "o", (21, 1): "^",
    **_nuvem(26, 32, 6), (27, 7): "o", (29, 7): "o", (31, 7): "o"})
K_CEU = pista(degraus((6, 2), (4, -1), (6, 2), (4, -1), (8, 1), (12, 1)), {
    **_nuvem(8, 16, 6), (9, 7): "o", (11, 7): "o", (13, 7): "o",
    (31, 2): "^", (30, 9): "P", (36, 2): "f"})
K_MORRO = pista(degraus((5, 1), (4, 2), (4, 3), (4, 4), (8, 4), (3, -1), (5, 3), (4, 2), (5, 1)), {
    (19, 5): "^", (17, 8): "o", (19, 8): "o", (21, 8): "o", (33, 3): "f"})
K_FENDAS = pista(degraus((8, 1), (3, -1), (7, 1), (4, -1), (7, 1), (3, -1), (8, 0)), {
    (14, 4): "o", (24, 4): "o", (32, 9): "P", (36, 1): "f"})
K_GELO = pista(degraus((10, 0), (3, -1), (10, 0), (3, -1), (14, 0)), {
    (5, 1): "^", (18, 1): "^", **_nuvem(26, 34, 5), (27, 6): "o", (29, 6): "o", (31, 6): "o",
    (34, 1): "f"})
K_CHEGADA = pista(degraus((6, 0), (4, 1), (4, 2), (4, 3), (22, 3)), {
    (24, 4): "^", (20, 9): "P", (33, 4): "B"})

FASE_CORRIDA = {
    "nome": "A Corrida",
    "tema": "montanha",
    "neve": True,
    "pergaminho": True,
    "pedacos": [K_LARGADA, K_CEU, K_MORRO, K_FENDAS, K_GELO, K_CHEGADA],
}
