"""Menu de fases: o MAPA DO MUNDO (sem texto). O Ribbat anda pelo caminho de um lugar pro outro;
embaixo, o painel do lugar: bandeira = jogar a fase, cara do chefão = ir pro chefão."""
import math

import pygame

import desenho as D
import fases
import pantano as P
import progresso as PR
import medalhas as MD
from config import *  # noqa: F401,F403
from entidades import R

FASES = [
    {"id": "fase1", "dados": fases.FASE_1, "pronta": True, "chefe": "viuva", "historia": True},
    {"id": "fase2", "dados": fases.FASE_2, "pronta": True, "chefe": "besouro", "historia": False},
    {"id": "fase3", "dados": fases.FASE_3, "pronta": True, "chefe": "rainha", "historia": False},
    {"id": "fase4", "dados": fases.FASE_4, "pronta": True, "chefe": "gato", "historia": False},
    {"id": "fase5", "dados": fases.FASE_5, "pronta": True, "chefe": "aguia", "historia": False},
    # a casa do Vô: SÓ o chefão secreto (aparece depois de zerar o jogo). "dados" é só pra montar o jogo.
    {"id": "secreta", "dados": fases.FASE_1, "pronta": True, "chefe": "vovo", "historia": False, "so_chefe": True},
]


def liberado(jogo, i, j):
    """j = 0 é a fase (abre quando a anterior foi zerada), j = 1 é o chefão (abre quando zera a fase)."""
    f = FASES[i]
    if not f["pronta"]:
        return False
    if f.get("so_chefe"):                       # a casa do Vô: só o chefão, depois de zerar o jogo
        return j == 1 and zerou_o_jogo(jogo)
    if i > 0 and not PR.fase(jogo.progresso, FASES[i - 1]["id"])["zerada"]:
        return False
    if j == 0:
        return True
    return f["chefe"] is not None and PR.fase(jogo.progresso, f["id"])["zerada"]


def zerou_o_jogo(jogo):
    return PR.fase(jogo.progresso, "fase5")["chefe"]


def ordem_mapa(jogo):
    """Os lugares na ordem do caminho (a casa do Vô aparece no começo depois de zerar)."""
    return ([5] if zerou_o_jogo(jogo) else []) + [0, 1, 2, 3, 4]


def alcance_mapa(jogo):
    """Até onde o Ribbat pode andar no mapa: até o primeiro lugar trancado (pra ver o que vem)."""
    ordem = ordem_mapa(jogo)
    for k, i in enumerate(ordem):
        if not liberado(jogo, i, 0) and not liberado(jogo, i, 1):
            return ordem[:k + 1]
    return ordem


def cadeado(tela, cx, cy, k=1.0):
    pygame.draw.arc(tela, (200, 200, 210), R(cx - 9 * k, cy - 20 * k, 18 * k, 22 * k), 0, math.pi, max(2, int(4 * k)))
    pygame.draw.rect(tela, (230, 190, 60), R(cx - 13 * k, cy - 9 * k, 26 * k, 20 * k), border_radius=int(4 * k))
    pygame.draw.rect(tela, (140, 100, 30), R(cx - 13 * k, cy - 9 * k, 26 * k, 20 * k), 2, border_radius=int(4 * k))
    pygame.draw.circle(tela, (90, 60, 20), (int(cx), int(cy)), int(3 * k))


def icone_viuva(tela, cx, cy, k=1.0):
    for s in (-1, 1):
        for i in range(4):
            jx, jy = cx + s * 8 * k, cy - 3 * k + i * 3 * k
            kx, ky = cx + s * 20 * k, cy - 14 * k + i * 6 * k
            px, py = cx + s * 26 * k, cy + 2 * k + i * 6 * k
            pygame.draw.lines(tela, (16, 14, 22), False, [(jx, jy), (kx, ky), (px, py)], max(2, int(3 * k)))
    pygame.draw.circle(tela, (16, 14, 22), (int(cx), int(cy - 6 * k)), int(14 * k))
    pygame.draw.circle(tela, (16, 14, 22), (int(cx), int(cy + 8 * k)), int(9 * k))
    pygame.draw.circle(tela, (70, 60, 90), (int(cx - 5 * k), int(cy - 11 * k)), int(4 * k))
    pygame.draw.polygon(tela, (220, 28, 44), [(cx - 5 * k, cy - 12 * k), (cx + 5 * k, cy - 12 * k), (cx, cy - 6 * k)])
    pygame.draw.polygon(tela, (220, 28, 44), [(cx - 5 * k, cy), (cx + 5 * k, cy), (cx, cy - 6 * k)])
    for ox in (-3, 3):
        pygame.draw.circle(tela, (230, 40, 50), (int(cx + ox * k), int(cy + 9 * k)), max(1, int(2 * k)))


def _miniatura_fase1(s, t):
    w, h = s.get_size()
    for y in range(h):
        k = y / h
        s.fill([int(a + (b - a) * k) for a, b in zip((120, 168, 160), (214, 226, 186))], R(0, y, w, 1))
    folha = P._folha_gigante(90, (70, 132, 74), 0.3)
    s.blit(folha, (w - 130, h - folha.get_height() + 10))
    s.blit(pygame.transform.flip(folha, True, False), (-40, h - folha.get_height() + 30))
    P.desenhar_agua(s, R(0, h - 46, w, 46), t)
    for x in (60, 150, 220):
        P.desenhar_vitoria(s, R(x, h - 48, 40, 6), 0, 0, 1, t)
    pulo = abs(math.sin(t * 2.5)) * 22
    D.desenhar_sapo(s, 168, h - 48 - pulo, 1, "pulo" if pulo > 4 else "parado", escala=1.0)
    if int(t * 0.8) % 2:
        P.desenhar_peixe(s, 105, h - 60 - abs(math.sin(t * 1.6)) * 30, 10, -math.cos(t * 1.6) * 300)


def _miniatura_colonia(s, t):
    import formigueiro as FM
    w, h = s.get_size()
    for y in range(h):
        k = y / h
        s.fill([int(a + (b - a) * k) for a, b in zip((36, 24, 18), (70, 48, 34))], R(0, y, w, 1))
    pygame.draw.rect(s, (92, 64, 44), R(0, 0, w, 22))
    pygame.draw.rect(s, (92, 64, 44), R(0, h - 34, w, 34))
    pygame.draw.line(s, (140, 104, 72), (0, h - 34), (w, h - 34), 3)
    for i in range(5):
        pygame.draw.ellipse(s, (214, 206, 186), R(20 + i * 12, h - 50, 10, 14))
    FM.desenhar_buraco(s, w - 50, h - 34, t)
    for i in range(3):
        x = (i * 80 + t * 40) % (w + 40) - 20
        D.desenhar_formiga(s, x, h - 50, 26, 16, 1, t * 10 + i)

    class _G:
        estado, vx, vy = "voando", 0, 0
    _G.x, _G.y, _G.dir = w * 0.62 + math.sin(t) * 30, 60 + math.sin(t * 2) * 6, 1 if math.cos(t) > 0 else -1
    FM.desenhar_guerreira(s, _G, 0, 0, t)
    pulo = abs(math.sin(t * 2.5)) * 26
    D.desenhar_sapo(s, 110, h - 34 - pulo, 1, "pulo" if pulo > 4 else "parado", escala=1.0)


def _miniatura_lamacal(s, t):
    import lamacal as L
    w, h = s.get_size()
    for y in range(h):
        k = y / h
        s.fill([int(a + (b - a) * k) for a, b in zip((214, 150, 110), (240, 214, 160))], R(0, y, w, 1))
    pygame.draw.circle(s, (255, 230, 170), (w - 50, 40), 22)
    L._arvore_seca(s, 40, h - 30, 110, 3)
    L.desenhar_poca(s, R(100, h - 40, 90, 40), t)
    pygame.draw.rect(s, (86, 60, 40), R(0, h - 40, 100, 40))
    pygame.draw.rect(s, (86, 60, 40), R(190, h - 40, w - 190, 40))
    pygame.draw.line(s, (150, 118, 86), (0, h - 39), (100, h - 39), 2)
    pygame.draw.line(s, (150, 118, 86), (190, h - 39), (w, h - 39), 2)

    mordida = 0.08 + (t * 0.6) % 0.2

    class _P:
        x, chao, dir = 215, h - 40, -1
        estado = "mordendo"
        espia = 1
    _P.t = mordida
    if int(t * 0.7) % 2:
        L.desenhar_peixe_lama(s, _P, 0, 0, t)
    pulo = abs(math.sin(t * 2.5)) * 30
    D.desenhar_sapo(s, 145, h - 46 - pulo, -1 if int(t * 0.7) % 2 else 1, "pulo" if pulo > 4 else "parado", escala=1.0)


def icone_besouro(tela, cx, cy, k=1.0):
    """Silhueta do besouro-rinoceronte com '?' de mistério desenhado (é surpresa!)."""
    pygame.draw.ellipse(tela, (40, 30, 26), R(cx - 20 * k, cy - 10 * k, 40 * k, 24 * k))
    pygame.draw.polygon(tela, (40, 30, 26), [(cx + 14 * k, cy - 4 * k), (cx + 30 * k, cy - 22 * k), (cx + 22 * k, cy + 2 * k)])
    for i in range(3):
        pygame.draw.line(tela, (40, 30, 26), (cx - 10 * k + i * 10 * k, cy + 10 * k), (cx - 14 * k + i * 10 * k, cy + 18 * k), 2)


def _miniatura_quintal(s, t):
    import quintal as Q
    w, h = s.get_size()
    for y in range(h):
        k = y / h
        s.fill([int(a + (b - a) * k) for a, b in zip((120, 190, 245), (214, 238, 250))], R(0, y, w, 1))
    pygame.draw.rect(s, (238, 220, 190), R(20, 30, 150, 110))
    pygame.draw.polygon(s, (176, 80, 60), [(10, 34), (95, -10), (180, 34)])
    pygame.draw.rect(s, (130, 170, 210), R(40, 60, 40, 34))
    for x in range(0, w, 14):
        pygame.draw.rect(s, (246, 246, 240), R(x, 96, 9, 44))
    pygame.draw.rect(s, (104, 190, 76), R(0, h - 30, w, 30))

    class _F:
        ini, fim, linha = 4, 5, 0
        chao = h - 30
    _F.x0, _F.x1 = 120, 170
    Q.desenhar_flores(s, _F, 0, 0, t)

    class _A:
        estado, dir = "atacando", -1
    _A.x, _A.y = 130 + math.sin(t * 3) * 20, h - 70 + math.sin(t * 7) * 6
    Q.desenhar_abelha(s, _A, 0, 0, t)
    pulo = abs(math.sin(t * 2.5)) * 26
    D.desenhar_sapo(s, 60, h - 30 - pulo, 1, "pulo" if pulo > 4 else "parado", escala=1.0)


def icone_gato(tela, cx, cy, k=1.0):
    pygame.draw.circle(tela, (26, 24, 30), (int(cx), int(cy)), int(16 * k))
    for s in (-1, 1):
        pygame.draw.polygon(tela, (26, 24, 30), [(cx + s * 6 * k, cy - 12 * k), (cx + s * 16 * k, cy - 26 * k), (cx + s * 16 * k, cy - 6 * k)])
        pygame.draw.ellipse(tela, (250, 208, 60), R(cx + s * 7 * k - 5 * k, cy - 6 * k, 10 * k, 8 * k))
        pygame.draw.ellipse(tela, PRETO, R(cx + s * 7 * k - 1 * k, cy - 6 * k, 2 * k, 8 * k))


def _miniatura_montanha(s, t):
    w, h = s.get_size()
    for y in range(h):
        k = y / h
        s.fill([int(a + (b - a) * k) for a, b in zip((60, 80, 150), (190, 220, 244))], R(0, y, w, 1))
    pygame.draw.polygon(s, (124, 112, 104), [(-10, h), (w * 0.5, 16), (w + 10, h)])
    pygame.draw.polygon(s, (240, 246, 252), [(w * 0.5, 16), (w * 0.36, 60), (w * 0.46, 52), (w * 0.52, 64), (w * 0.64, 56)])
    for i in range(3):
        pygame.draw.circle(s, (250, 252, 255), (int((i * 70 + t * 12) % (w + 60) - 30), 90 + i * 8), 18)
    pulo = abs(math.sin(t * 2.5)) * 22
    D.desenhar_sapo(s, w * 0.36, h - 52 - pulo, 1, "pulo" if pulo > 4 else "parado", escala=0.9)
    import montanha as MT

    class _G:
        estado, vx, vy, alvo = "voando", 0, 0, None
    _G.x, _G.y, _G.dir = w * 0.7 + math.sin(t) * 20, 40, -1
    MT.desenhar_gaviao(s, _G, 0, 0, t)


def _miniatura_vovo(s, t):
    w, h = s.get_size()
    for y in range(h):
        k = y / h
        s.fill([int(a + (b - a) * k) for a, b in zip((16, 22, 58), (60, 70, 120))], R(0, y, w, 1))
    pygame.draw.circle(s, (244, 242, 214), (w - 30, 24), 14)
    pygame.draw.rect(s, (30, 60, 90), R(0, h * 0.62, w, h))
    import vovo as VV
    img = VV.sprite("parado", math.sin(t) * 0.5, 0.0, False)
    img = pygame.transform.smoothscale(img, (int(VV.SPR_W * 0.36), int(VV.SPR_H * 0.36)))
    s.blit(img, img.get_rect(midbottom=(w / 2, h - 4)))


MINIATURAS = {"fase1": _miniatura_fase1, "fase2": _miniatura_lamacal, "fase3": _miniatura_colonia,
              "fase4": _miniatura_quintal, "fase5": _miniatura_montanha,
              "secreta": _miniatura_vovo}


NOS = {5: (74, 316), 0: (196, 300), 1: (334, 246), 2: (468, 302), 3: (608, 240), 4: (748, 214)}
PERGAMINHO = (872, 104)
_fundo_mapa = None


def criar_fundo_mapa():
    """O mundo do Ribbat visto de cima: lagoa de casa, pântano, lamaçal, formigueiro, quintal e a montanha."""
    import random
    s = pygame.Surface((LARGURA, ALTURA))
    for y in range(ALTURA):
        k = y / ALTURA
        s.fill([int(a + (b - a) * k) for a, b in zip((120, 176, 230), (214, 232, 200))], R(0, y, LARGURA, 1))
    rnd = random.Random(12)
    pygame.draw.polygon(s, (150, 186, 150), [(0, 230)] + [(x, 200 - math.sin(x / 90) * 26) for x in range(0, 700, 20)] +
                        [(700, 260), (0, 260)])
    # a montanha (com neve e nuvens) e o lugar do pergaminho lá em cima
    pygame.draw.polygon(s, (124, 112, 104), [(620, 372), (872, 80), (1000, 372)])
    pygame.draw.polygon(s, (98, 88, 82), [(872, 80), (940, 372), (1000, 372)])
    pygame.draw.polygon(s, (244, 248, 252), [(872, 80), (822, 140), (850, 132), (872, 150), (896, 130), (918, 140)])
    for x, y, r in ((780, 150, 24), (812, 160, 30), (940, 170, 26), (968, 150, 20)):
        pygame.draw.circle(s, (250, 252, 255), (x, y), r)
    # o chão: cada região de um jeito
    pygame.draw.rect(s, (96, 150, 80), R(0, 270, 268, 110))                         # pântano
    for x, y, w in ((20, 290, 70), (120, 330, 90), (210, 286, 50)):
        pygame.draw.ellipse(s, (60, 110, 140), R(x, y, w, 26))
        pygame.draw.ellipse(s, (80, 150, 80), R(x + w * 0.3, y + 6, 16, 9))
    pygame.draw.rect(s, (120, 92, 64), R(268, 236, 138, 144))                       # lamaçal
    for _ in range(12):
        pygame.draw.circle(s, (96, 72, 50), (rnd.randint(272, 400), rnd.randint(250, 370)), rnd.randint(4, 10))
    pygame.draw.rect(s, (186, 150, 100), R(406, 260, 136, 120))                     # formigueiro
    for x in (420, 500, 524):
        pygame.draw.polygon(s, (150, 112, 70), [(x - 14, 300 + (x % 7) * 6), (x, 278 + (x % 7) * 6), (x + 14, 300 + (x % 7) * 6)])
    pygame.draw.rect(s, (110, 180, 90), R(542, 226, 140, 154))                      # quintal
    for x in range(546, 682, 12):
        pygame.draw.rect(s, (246, 246, 240), R(x, 212, 6, 18))
    pygame.draw.line(s, (246, 246, 240), (542, 218), (682, 218), 3)
    pygame.draw.rect(s, (238, 220, 190), R(640, 180, 34, 28))
    pygame.draw.polygon(s, (176, 80, 60), [(636, 182), (657, 164), (678, 182)])
    # a casa do Vô: lagoinha com uma casinha de madeira
    pygame.draw.ellipse(s, (60, 110, 150), R(20, 320, 110, 44))
    pygame.draw.rect(s, (150, 104, 60), R(56, 272, 34, 26))
    pygame.draw.polygon(s, (110, 70, 40), [(50, 274), (73, 254), (96, 274)])
    pygame.draw.rect(s, (90, 60, 34), R(68, 284, 9, 14))
    # o caminho pontilhado entre os lugares
    pts = [NOS[i] for i in (5, 0, 1, 2, 3, 4)] + [PERGAMINHO]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.dist(a, b) // 12))
        for k in range(0, n, 2):
            pygame.draw.line(s, (250, 240, 210), (a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n),
                             (a[0] + (b[0] - a[0]) * (k + 1) / n, a[1] + (b[1] - a[1]) * (k + 1) / n), 5)
    pygame.draw.rect(s, (60, 90, 66), R(0, 380, LARGURA, ALTURA - 380))             # o chão do painel
    return s


def _icone_lugar(tela, i, x, y):
    """O desenho de cada lugar no mapa (dentro da bolinha)."""
    if i == 0:                                                     # vitória-régia com florzinha
        pygame.draw.ellipse(tela, (70, 150, 76), R(x - 18, y - 6, 36, 16))
        pygame.draw.circle(tela, (240, 150, 190), (x + 6, y - 4), 5)
    elif i == 1:                                                   # árvore seca
        pygame.draw.line(tela, (110, 80, 56), (x, y + 12), (x, y - 14), 4)
        pygame.draw.line(tela, (110, 80, 56), (x, y - 4), (x - 10, y - 14), 3)
        pygame.draw.line(tela, (110, 80, 56), (x, y), (x + 10, y - 10), 3)
    elif i == 2:                                                   # formigueiro
        pygame.draw.polygon(tela, (150, 110, 70), [(x - 18, y + 10), (x, y - 14), (x + 18, y + 10)])
        pygame.draw.ellipse(tela, (40, 26, 16), R(x - 4, y - 14, 8, 5))
    elif i == 3:                                                   # casinha
        pygame.draw.rect(tela, (238, 220, 190), R(x - 12, y - 6, 24, 18))
        pygame.draw.polygon(tela, (176, 80, 60), [(x - 16, y - 5), (x, y - 18), (x + 16, y - 5)])
    elif i == 4:                                                   # montanha com neve
        pygame.draw.polygon(tela, (124, 112, 104), [(x - 18, y + 10), (x, y - 16), (x + 18, y + 10)])
        pygame.draw.polygon(tela, (244, 248, 252), [(x, y - 16), (x - 7, y - 6), (x + 7, y - 6)])
    elif i == 5:                                                   # o Vô
        import vovo as VV
        VV.icone(tela, x, y + 2, 1.0)


def _posicao_ribbat(jogo):
    a = NOS[getattr(jogo, "menu_de", jogo.menu_i)]
    b = NOS[jogo.menu_i]
    u = getattr(jogo, "menu_anda", 1.0)
    pulo = math.sin(u * math.pi) * 30 if a != b else 0
    return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u - pulo, u < 1


def desenhar(jogo, tela):
    global _fundo_mapa
    t = jogo.tempo_total
    if _fundo_mapa is None:
        _fundo_mapa = criar_fundo_mapa()
    tela.blit(_fundo_mapa, (0, 0))
    D.texto(tela, jogo.fonte_grande, "RIBBAT", LARGURA / 2, 14, centro=True, cor=(112, 196, 84), borda=(30, 70, 34))
    zerou = zerou_o_jogo(jogo)
    D.pergaminho(tela, *PERGAMINHO, 0.8 if zerou else 0.6, brilho=t * 1.5)
    alcance = alcance_mapa(jogo)
    for i in ordem_mapa(jogo):
        x, y = NOS[i]
        aberto = liberado(jogo, i, 0) or liberado(jogo, i, 1)
        sel = i == jogo.menu_i
        if sel:
            r = 34 + 3 * math.sin(t * 5)
            pygame.draw.circle(tela, AMARELO, (x, y), int(r), 4)
        pygame.draw.circle(tela, PRETO, (x, y), 28)
        pygame.draw.circle(tela, (240, 232, 200) if aberto else (130, 130, 136), (x, y), 25)
        _icone_lugar(tela, i, x, y)
        if not aberto:
            cadeado(tela, x + 18, y + 18, 0.6)
        reg = PR.fase(jogo.progresso, FASES[i]["id"])
        if reg["zerada"] and not FASES[i].get("so_chefe"):
            pygame.draw.line(tela, (230, 220, 190), (x - 22, y - 18), (x - 22, y - 44), 2)
            D.bandeirinha(tela, x - 21, y - 44, 0.5, t)
        if reg["chefe"]:                                       # a medalha do teu tempo no chefão
            MD.desenhar(tela, x + 22, y - 24, MD.medalha(FASES[i]["id"], "tempo_chefe", reg.get("tempo_chefe")) or "bronze", 7)
        if i not in alcance:
            veu = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(veu, (40, 40, 50, 140), (30, 30), 28)
            tela.blit(veu, (x - 30, y - 30))
    rx, ry, andando = _posicao_ribbat(jogo)                          # o Ribbat no lugar escolhido
    D.desenhar_sapo(tela, rx, ry - 20, 1, "pulo" if andando else "parado", escala=0.9,
                    chapeu=jogo.progresso.get("chapeu"))
    _painel(tela, jogo, t)
    # teclinhas no canto
    fn = jogo.fonte_tecla
    x, y = 14, ALTURA - 36
    x += D.tecla(tela, fn, x, y, "<") + 4
    x += D.tecla(tela, fn, x, y, ">") + 16
    x += D.tecla(tela, fn, x, y, "enter", 40) + 16
    D.tecla(tela, fn, x, y, "Esc", 44)
    x += 60
    x += D.tecla(tela, fn, x, y, "^") + 2                       # setinhas: ↑ maratona, ↓ loja
    D.tecla(tela, fn, x, y, "v")
    _plaquinha_maratona(tela, jogo, t)
    _plaquinha_album(tela, jogo, t)
    _plaquinha_loja(tela, jogo, t)
    total = PR.tempo_total(jogo.progresso)
    if total:                                                  # tempo total: a soma de todos os recordes
        s = D.fmt_tempo(total)
        tx = LARGURA - 24 - jogo.fonte.size(s)[0]
        D.icone_trofeu(tela, tx - 22, 34)
        D.texto(tela, jogo.fonte, s, tx, 22)


def _painel(tela, jogo, t):
    """O painel do lugar escolhido: miniatura + botão da fase + botão do chefão (com recorde e medalha)."""
    i = jogo.menu_i
    f = FASES[i]
    reg = PR.fase(jogo.progresso, f["id"])
    treme = math.sin(t * 60) * 6 * jogo.menu_tremor if jogo.menu_j in (0, 1) else 0
    caixa = R(222 + treme, 386, 516, 104)
    pygame.draw.rect(tela, (20, 30, 24), caixa.move(0, 5), border_radius=14)
    pygame.draw.rect(tela, (54, 84, 60), caixa, border_radius=14)
    pygame.draw.rect(tela, AMARELO if jogo.menu_j in (0, 1) else (30, 50, 36), caixa, 4, border_radius=14)
    mini = pygame.Surface((140, 88))
    MINIATURAS[f["id"]](mini, t)
    tela.blit(mini, (caixa.x + 8, caixa.y + 8))
    pygame.draw.rect(tela, PRETO, R(caixa.x + 8, caixa.y + 8, 140, 88), 3)
    if reg["moscas"]:
        D.desenhar_mosca(tela, caixa.x + 22, caixa.y + 84, t)
        D.texto(tela, jogo.fonte_tecla, str(reg["moscas"]), caixa.x + 36, caixa.y + 74)
    botoes = [1] if f.get("so_chefe") else [0, 1]
    for k, j in enumerate(botoes):
        h = 88 if len(botoes) == 1 else 42
        botao = R(caixa.x + 158, caixa.y + 8 + k * 46, caixa.width - 166, h)
        aberto = liberado(jogo, i, j)
        marcado = jogo.menu_j == j or (len(botoes) == 1 and jogo.menu_j == 0)
        pygame.draw.rect(tela, (34, 50, 38) if aberto else (44, 44, 48), botao, border_radius=10)
        if marcado:
            brilho = 160 + int(95 * abs(math.sin(t * 4)))
            pygame.draw.rect(tela, (brilho, brilho, 90), botao, 4, border_radius=10)
            seta_x = botao.x - 2 + math.sin(t * 8) * 3
            pygame.draw.polygon(tela, AMARELO, [(seta_x, botao.centery), (seta_x - 10, botao.centery - 8),
                                                (seta_x - 10, botao.centery + 8)])
        else:
            pygame.draw.rect(tela, (24, 36, 28), botao, 2, border_radius=10)
        ic = R(botao.x, botao.y, 90, botao.height)
        if j == 0:
            pygame.draw.line(tela, (230, 220, 190), (ic.centerx - 8, ic.y + 6), (ic.centerx - 8, ic.bottom - 6), 3)
            D.bandeirinha(tela, ic.centerx - 7, ic.y + 6, 0.7, t)
        else:
            _icone_chefe(tela, f, ic.centerx, ic.centery, 0.8)
        chave = "tempo" if j == 0 else "tempo_chefe"
        recorde = reg.get(chave) if aberto else None
        if recorde:
            s = D.fmt_tempo(recorde)
            D.texto(tela, jogo.fonte, s, botao.x + 110, botao.centery - 13)
            MD.desenhar(tela, botao.right - 24, botao.centery + 4, MD.medalha(f["id"], chave, recorde), 9)
            if reg.get("sem_dano" if j == 0 else "sem_dano_chefe"):
                MD.desenhar_coracao(tela, botao.right - 52, botao.centery, 8)
        if not aberto:
            veu = pygame.Surface(botao.size, pygame.SRCALPHA)
            veu.fill((20, 20, 24, 150))
            tela.blit(veu, botao.topleft)
            cadeado(tela, botao.right - 30, botao.centery + 4, 0.9)


def _icone_chefe(tela, f, cx, cy, k=1.0):
    c = f["chefe"]
    if c == "viuva":
        icone_viuva(tela, cx, cy + 2, k)
    elif c == "besouro":
        icone_besouro(tela, cx - 6, cy, k * 1.1)
    elif c == "gato":
        icone_gato(tela, cx, cy + 4, k)
    elif c == "aguia":
        import aguia as AG
        AG.icone_cabeca(tela, cx - 8, cy, k * 1.5)
    elif c == "vovo":
        import vovo as VV
        VV.icone(tela, cx, cy + 4, k * 2.2)
    elif c == "rainha":                                        # formigona com coroa
        s = k
        pygame.draw.ellipse(tela, (124, 36, 22), R(cx - 30 * s, cy - 4 * s, 30 * s, 20 * s))
        pygame.draw.ellipse(tela, (124, 36, 22), R(cx - 4 * s, cy - 2 * s, 16 * s, 12 * s))
        pygame.draw.circle(tela, (124, 36, 22), (int(cx + 18 * s), int(cy)), int(8 * s))
        pygame.draw.polygon(tela, (246, 200, 70), [(cx + 11 * s, cy - 6 * s), (cx + 11 * s, cy - 16 * s), (cx + 15 * s, cy - 10 * s),
                                                   (cx + 18 * s, cy - 18 * s), (cx + 21 * s, cy - 10 * s), (cx + 25 * s, cy - 16 * s),
                                                   (cx + 25 * s, cy - 6 * s)])
        pygame.draw.ellipse(tela, (220, 236, 246), R(cx - 20 * s, cy - 18 * s, 26 * s, 12 * s))


def maratona_liberada(jogo):
    return all(PR.fase(jogo.progresso, f["id"])["chefe"] for f in FASES[:5])


def _plaquinha(tela, caixa, marcada, aberta, t):
    pygame.draw.rect(tela, (20, 30, 24), caixa.move(0, 4), border_radius=12)
    pygame.draw.rect(tela, (54, 84, 60) if aberta else (50, 50, 54), caixa, border_radius=12)
    if marcada:
        brilho = 160 + int(95 * abs(math.sin(t * 4)))
        pygame.draw.rect(tela, (brilho, brilho, 90), caixa, 4, border_radius=12)
    else:
        pygame.draw.rect(tela, (30, 50, 36), caixa, 3, border_radius=12)


def _icones_chefes(tela, x, y, k=0.55):
    """As 5 caras dos chefões em fila (a maratona)."""
    e = 34 * k / 0.55                                          # espaço entre um e outro
    icone_viuva(tela, x, y + 2, k)
    icone_besouro(tela, x + e, y, k * 1.1)
    rx, s = x + 2 * e, k / 0.55
    pygame.draw.ellipse(tela, (124, 36, 22), R(rx - 9 * s, y - 6 * s, 18 * s, 12 * s))
    pygame.draw.polygon(tela, (246, 200, 70), [(rx - 6 * s, y - 6 * s), (rx - 6 * s, y - 13 * s), (rx - 2 * s, y - 9 * s),
                                               (rx + 1 * s, y - 14 * s), (rx + 4 * s, y - 9 * s), (rx + 7 * s, y - 13 * s),
                                               (rx + 7 * s, y - 6 * s)])
    icone_gato(tela, x + 3 * e, y + 2, k)
    import aguia as AG
    AG.icone_cabeca(tela, x + 4 * e - 4 * s, y, k * 1.4)


def _plaquinha_maratona(tela, jogo, t):
    aberta = maratona_liberada(jogo)
    treme = math.sin(t * 60) * 6 * jogo.menu_tremor if jogo.menu_j == -1 else 0
    caixa = R(14 + treme, 12, 250, 52)
    _plaquinha(tela, caixa, jogo.menu_j == -1 and jogo.menu_k == 0, aberta, t)
    D.icone_trofeu(tela, caixa.x + 22, caixa.centery + 2)
    _icones_chefes(tela, caixa.x + 66, caixa.centery - (6 if jogo.progresso.get("maratona") else 0))
    if jogo.progresso.get("maratona"):
        D.texto(tela, jogo.fonte_tecla, D.fmt_tempo(jogo.progresso["maratona"]), caixa.x + 112, caixa.y + 31)
    if not aberta:
        veu = pygame.Surface(caixa.size, pygame.SRCALPHA)
        veu.fill((20, 20, 24, 150))
        tela.blit(veu, caixa.topleft)
        cadeado(tela, caixa.right - 22, caixa.centery + 4, 0.9)


def _plaquinha_album(tela, jogo, t):
    import conquistas as CQ
    caixa = R(276, 12, 112, 52)
    _plaquinha(tela, caixa, jogo.menu_j == -1 and jogo.menu_k == 1, True, t)
    CQ.icone_album(tela, caixa.x + 28, caixa.centery, 1.1)
    D.texto(tela, jogo.fonte_tecla, f"{len(jogo.progresso.get('conquistas', []))}/{len(CQ.IDS)}", caixa.x + 52, caixa.centery - 10)


def _plaquinha_loja(tela, jogo, t):
    caixa = R(LARGURA - 214, ALTURA - 60, 200, 48)
    _plaquinha(tela, caixa, jogo.menu_j == 2, True, t)
    import chapeus as CP
    CP.icone(tela, "cartola", caixa.x + 30, caixa.centery + 12, 1.2)
    D.desenhar_mosca(tela, caixa.x + 92, caixa.centery, t)
    D.texto(tela, jogo.fonte, str(jogo.progresso.get("carteira", 0)), caixa.x + 108, caixa.centery - 14)


def desenhar_loja(jogo, tela):
    """A loja: o Ribbat grandão no meio provando o chapéu, e os chapéus em fila embaixo."""
    import chapeus as CP
    t = jogo.tempo_total
    P.desenhar_fundo(tela, jogo.fundo, t * 20, t)
    veu = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    veu.fill((10, 20, 16, 130))
    tela.blit(veu, (0, 0))
    p = jogo.progresso
    nome, preco = CP.CHAPEUS[jogo.loja_i]
    treme = math.sin(t * 60) * 8 * jogo.loja_tremor
    # o Ribbat provando
    pygame.draw.ellipse(tela, (60, 130, 70), R(LARGURA / 2 - 130, 300, 260, 50))
    D.desenhar_sapo(tela, LARGURA / 2 + treme, 322, 1, "parado", escala=3.0, chapeu=nome)
    # a carteira
    D.desenhar_mosca(tela, LARGURA - 110, 34, t)
    D.texto(tela, jogo.fonte_grande, str(p.get("carteira", 0)), LARGURA - 92, 12)
    # os chapéus
    n = len(CP.CHAPEUS)
    w, vao = 100, 10
    x0 = LARGURA / 2 - (n * w + (n - 1) * vao) / 2
    for i, (nm, pr) in enumerate(CP.CHAPEUS):
        caixa = R(x0 + i * (w + vao), 372 - (6 if i == jogo.loja_i else 0), w, 110)
        tem = nm in p["chapeus"]
        pygame.draw.rect(tela, (20, 30, 24), caixa.move(0, 4), border_radius=12)
        pygame.draw.rect(tela, (54, 84, 60) if tem else (44, 60, 50), caixa, border_radius=12)
        pygame.draw.rect(tela, AMARELO if i == jogo.loja_i else (30, 50, 36), caixa, 4, border_radius=12)
        CP.icone(tela, nm, caixa.centerx, caixa.y + 52, 1.5)
        if p.get("chapeu") == nm:                                   # vestindo: certinho verde
            pygame.draw.circle(tela, PRETO, (caixa.right - 16, caixa.y + 16), 11)
            pygame.draw.circle(tela, (90, 200, 90), (caixa.right - 16, caixa.y + 16), 9)
            pygame.draw.lines(tela, BRANCO, False, [(caixa.right - 21, caixa.y + 16), (caixa.right - 17, caixa.y + 20),
                                                    (caixa.right - 10, caixa.y + 11)], 3)
        if not tem:                                                 # preço
            pode = p.get("carteira", 0) >= pr
            D.desenhar_mosca(tela, caixa.x + 30, caixa.bottom - 22, t)
            D.texto(tela, jogo.fonte, str(pr), caixa.x + 46, caixa.bottom - 36, cor=BRANCO if pode else (230, 110, 100))
    fn = jogo.fonte_tecla
    x, y = 14, ALTURA - 36
    x += D.tecla(tela, fn, x, y, "<") + 4
    x += D.tecla(tela, fn, x, y, ">") + 16
    x += D.tecla(tela, fn, x, y, "enter", 40) + 16
    D.tecla(tela, fn, x, y, "Esc", 44)


def desenhar_maratona_fim(jogo, tela):
    """Venceu os 5 chefões seguidos: troféu gigante, o tempo e o Ribbat pulando de alegria."""
    t = jogo.tempo_total
    tela.fill((40, 60, 46))
    for i in range(16):                                             # raios dourados
        a = i / 16 * math.tau + t * 0.2
        pygame.draw.line(tela, (70, 96, 66), (LARGURA / 2, 210), (LARGURA / 2 + math.cos(a) * 700, 210 + math.sin(a) * 700), 18)
    D.icone_trofeu(tela, LARGURA / 2, 190, 6.0)
    _icones_chefes(tela, LARGURA / 2 - 120, 330, 1.0)
    pulo = abs(math.sin(t * 4)) * 30
    D.desenhar_sapo(tela, LARGURA / 2 - 300, 470 - pulo, 1, "pulo" if pulo > 6 else "parado", escala=2.4,
                    chapeu=jogo.progresso.get("chapeu"))
    tempo, novo, _, _ = jogo.ultimo_tempo
    D.icone_relogio(tela, LARGURA / 2 - 70, 420, 16)
    D.texto(tela, jogo.fonte_grande, D.fmt_tempo(tempo), LARGURA / 2 - 44, 398)
    if novo:
        D.estrelinha(tela, LARGURA / 2 + 150, 420, 16 + 3 * abs(math.sin(t * 5)))
    if int(t * 2) % 2 == 0:
        D.tecla(tela, jogo.fonte_tecla, LARGURA - 60, ALTURA - 34, "enter", 40)
