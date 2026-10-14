"""
Álbum de conquistas: 16 figurinhas (sem texto: desenho + "quanto falta", tipo 37/100).

Todas dá pra conseguir de verdade (o Gomes pediu: nada impossível, tipo "vencer a Viúva sem pular",
que não dá porque ela fica lá no alto). Cada uma diz o progresso (atual, meta) a partir do save.
Os contadores (inimigos, teias, mosquitos, pedras) ficam em progresso["contadores"].
"""
import math

import pygame

import desenho as D
import medalhas as MD
import progresso as PR
from config import *  # noqa: F401,F403
from entidades import R

FASES_IDS = ("fase1", "fase2", "fase3", "fase4", "fase5")
CHEFES_IDS = FASES_IDS
_total_moscas = {}


def total_moscas(ident):
    """Quantas moscas a fase tem (monta a fase uma vez só pra contar)."""
    if ident not in _total_moscas:
        import menu
        from entidades import Fase
        f = next(x for x in menu.FASES if x["id"] == ident)
        _total_moscas[ident] = Fase(f["dados"]).total_moscas
    return _total_moscas[ident]


def contador(dados, nome):
    return dados.setdefault("contadores", {}).get(nome, 0)


def contar(dados, nome, n=1):
    c = dados.setdefault("contadores", {})
    c[nome] = c.get(nome, 0) + n


def _reg(dados, ident):
    return PR.fase(dados, ident)


def _moscas(dados):
    melhor = (0, 1)
    for f in FASES_IDS:
        tot = total_moscas(f)
        tem = _reg(dados, f).get("moscas", 0)
        if tem / tot > melhor[0] / melhor[1]:
            melhor = (tem, tot)
    return melhor


def _ouro(dados, chave):
    return sum(MD.medalha(f, chave, _reg(dados, f).get(chave)) == "ouro" for f in FASES_IDS), 5


# (id, progresso(dados) -> (atual, meta))
CONQUISTAS = (
    ("moscas", _moscas),                                                                   # todas as moscas de uma fase
    ("fase_sem_dano", lambda d: (min(1, sum(bool(_reg(d, f).get("sem_dano")) for f in FASES_IDS)), 1)),
    ("chefe_sem_dano", lambda d: (min(1, sum(bool(_reg(d, f).get("sem_dano_chefe")) for f in CHEFES_IDS)), 1)),
    ("ouro_fases", lambda d: _ouro(d, "tempo")),
    ("ouro_chefes", lambda d: _ouro(d, "tempo_chefe")),
    ("zerou", lambda d: (int(bool(_reg(d, "fase5")["chefe"])), 1)),                       # chegou no pergaminho
    ("maratona", lambda d: (int(d.get("maratona") is not None), 1)),
    ("maratona_5min", lambda d: (int(d.get("maratona") is not None and d["maratona"] < 300), 1)),
    ("chapeus", lambda d: (len(d.get("chapeus", ["nenhum"])) - 1, 7)),
    ("fantasma", lambda d: (int(bool(d.get("bateu_fantasma"))), 1)),                      # bateu o próprio fantasma
    ("inimigos", lambda d: (min(100, contador(d, "inimigos")), 100)),
    ("teias", lambda d: (min(15, contador(d, "teias")), 15)),                              # se soltou da teia
    ("mosquitos", lambda d: (min(10, contador(d, "mosquitos")), 10)),                      # mosquitos de cura
    ("pedras", lambda d: (min(10, contador(d, "pedras")), 10)),                            # pedras quebradas
    ("coelho", lambda d: (int(bool(d.get("venceu_de_coelho"))), 1)),                      # revanche de orelhinhas
    ("vovo", lambda d: (int(bool(_reg(d, "secreta")["chefe"])), 1)),                       # o segredo
)
IDS = [c for c, _ in CONQUISTAS]


def progresso(dados, ident):
    return dict(CONQUISTAS)[ident](dados)


def conferir(dados):
    """Marca as que acabaram de ser conseguidas. Devolve a lista das NOVAS."""
    feitas = dados.setdefault("conquistas", [])
    novas = []
    for ident, fn in CONQUISTAS:
        if ident not in feitas:
            atual, meta = fn(dados)
            if atual >= meta:
                feitas.append(ident)
                novas.append(ident)
    return novas


# =====================================================================
# Desenho das figurinhas
# =====================================================================
def _coracao(tela, x, y, r=10):
    MD.desenhar_coracao(tela, x, y, r)


def figura(tela, ident, cx, cy, t, k=1.0):
    """O desenho de cada figurinha, no meio (cx, cy)."""
    import menu
    if ident == "moscas":
        for i, dx in enumerate((-22, 0, 22)):
            D.desenhar_mosca(tela, cx + dx, cy - 6 + (i % 2) * 8, t + i)
        pygame.draw.line(tela, (230, 220, 190), (cx + 30, cy + 22), (cx + 30, cy - 2), 2)
        D.bandeirinha(tela, cx + 31, cy - 2, 0.5, t)
    elif ident == "fase_sem_dano":
        _coracao(tela, cx - 12, cy, 14)
        pygame.draw.line(tela, (230, 220, 190), (cx + 22, cy + 18), (cx + 22, cy - 14), 2)
        D.bandeirinha(tela, cx + 23, cy - 14, 0.6, t)
    elif ident == "chefe_sem_dano":
        _coracao(tela, cx - 18, cy, 14)
        menu.icone_viuva(tela, cx + 22, cy, 0.7)
    elif ident == "ouro_fases":
        MD.desenhar(tela, cx - 14, cy + 6, "ouro", 14)
        pygame.draw.line(tela, (230, 220, 190), (cx + 22, cy + 18), (cx + 22, cy - 14), 2)
        D.bandeirinha(tela, cx + 23, cy - 14, 0.6, t)
    elif ident == "ouro_chefes":
        MD.desenhar(tela, cx - 18, cy + 6, "ouro", 14)
        menu.icone_viuva(tela, cx + 22, cy, 0.7)
    elif ident == "zerou":
        D.pergaminho(tela, cx, cy, 1.0, brilho=t * 1.5)
    elif ident == "maratona":
        D.icone_trofeu(tela, cx, cy + 4, 1.8)
    elif ident == "maratona_5min":
        D.icone_trofeu(tela, cx - 16, cy + 4, 1.5)
        D.icone_relogio(tela, cx + 22, cy + 2, 13)
    elif ident == "chapeus":
        import chapeus as CP
        CP.icone(tela, "cartola", cx - 18, cy + 4, 1.4)
        CP.icone(tela, "coroa", cx + 20, cy + 4, 1.4)
    elif ident == "fantasma":
        img = D.sprite_sapo("pulo", 1, 0.9).copy()
        img.fill((60, 70, 120), special_flags=pygame.BLEND_RGB_ADD)
        img.set_alpha(150)
        tela.blit(img, img.get_rect(center=(cx, cy)))
    elif ident == "inimigos":
        for i in range(3):
            D.desenhar_formiga(tela, cx - 30 + i * 22, cy + 10 - i * 4, 22, 13, 1, t * 8 + i)
    elif ident == "teias":
        for a in range(8):
            ang = a * math.pi / 4
            pygame.draw.line(tela, TEIA, (cx, cy), (cx + math.cos(ang) * 28, cy + math.sin(ang) * 24), 1)
        for rr in (8, 16, 24):
            pygame.draw.circle(tela, TEIA, (cx, cy), rr, 1)
        D.desenhar_sapo(tela, cx, cy + 22, 1, "pulo", escala=0.55)
    elif ident == "mosquitos":
        D.desenhar_mosquito(tela, cx, cy, t)
        _coracao(tela, cx + 22, cy - 14, 7)
    elif ident == "pedras":
        D.desenhar_pedra(tela, R(cx - 26, cy - 22, 52, 44), 3)
        for i in range(4):
            a = i * 1.6
            pygame.draw.line(tela, (60, 54, 50), (cx, cy), (cx + math.cos(a) * 20, cy + math.sin(a) * 16), 2)
    elif ident == "coelho":
        D.desenhar_sapo(tela, cx, cy + 22, 1, "parado", escala=0.9, orelhas=True)
    elif ident == "vovo":
        import vovo as VV
        VV.icone(tela, cx, cy + 4, 2.0)


def desenhar_album(jogo, tela):
    """O álbum: 4x4 figurinhas. As que faltam ficam cinza com o progresso embaixo (ex.: 37/100)."""
    import pantano as P
    t = jogo.tempo_total
    P.desenhar_fundo(tela, jogo.fundo, t * 20, t)
    veu = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    veu.fill((10, 20, 16, 150))
    tela.blit(veu, (0, 0))
    dados = jogo.progresso
    feitas = dados.get("conquistas", [])
    import menu
    w, h, vx, vy = 200, 104, 16, 12
    x0 = LARGURA / 2 - (4 * w + 3 * vx) / 2
    y0 = 24
    for n, ident in enumerate(IDS):
        caixa = R(x0 + (n % 4) * (w + vx), y0 + (n // 4) * (h + vy), w, h)
        tem = ident in feitas
        segredo = ident == "vovo" and not menu.zerou_o_jogo(jogo) and not tem
        pygame.draw.rect(tela, (20, 30, 24), caixa.move(0, 4), border_radius=12)
        pygame.draw.rect(tela, (250, 240, 210) if tem else (70, 80, 74), caixa, border_radius=12)
        pygame.draw.rect(tela, (230, 190, 60) if tem else (40, 50, 44), caixa, 4, border_radius=12)
        if segredo:                                                     # ainda é segredo: só um "?" de sombra
            pygame.draw.circle(tela, (50, 58, 52), caixa.center, 26)
            pygame.draw.arc(tela, (120, 130, 124), R(caixa.centerx - 10, caixa.centery - 18, 20, 20), -0.3, math.pi, 4)
            pygame.draw.line(tela, (120, 130, 124), (caixa.centerx + 9, caixa.centery - 6), (caixa.centerx, caixa.centery + 4), 4)
            pygame.draw.circle(tela, (120, 130, 124), (caixa.centerx, caixa.centery + 13), 3)
            continue
        fig = pygame.Surface(caixa.size, pygame.SRCALPHA)
        figura(fig, ident, w / 2, h / 2 - (6 if not tem else 0), t)
        if not tem:                                                     # figurinha que falta: cinza e apagada
            fig.fill((60, 60, 60), special_flags=pygame.BLEND_RGB_MULT)
            fig.set_alpha(150)
        tela.blit(fig, caixa.topleft)
        if tem:                                                         # brilhinho de figurinha nova
            a = (t * 0.8 + n * 0.37) % 3
            if a < 1:
                x = caixa.x + a * caixa.width
                pygame.draw.line(tela, (255, 255, 255), (x, caixa.y + 6), (x - 20, caixa.bottom - 6), 3)
        else:
            atual, meta = progresso(dados, ident)
            s = f"{atual}/{meta}"
            D.texto(tela, jogo.fonte_tecla, s, caixa.centerx - jogo.fonte_tecla.size(s)[0] / 2, caixa.bottom - 24)
    fn = jogo.fonte_tecla
    D.tecla(tela, fn, 14, ALTURA - 36, "Esc", 44)
    s = f"{len(feitas)}/{len(IDS)}"
    D.texto(tela, jogo.fonte, s, LARGURA - 24 - jogo.fonte.size(s)[0], ALTURA - 40)


def desenhar_aviso(jogo, tela):
    """Figurinha nova! Ela desce no canto da tela por uns segundos."""
    if not getattr(jogo, "avisos_conquista", None):
        return
    ident, tempo = jogo.avisos_conquista[0]
    t = jogo.tempo_total
    entra = min(1.0, tempo * 4, (3.2 - tempo) * 4)
    caixa = R(LARGURA - 200, -110 + 130 * max(0.0, entra), 180, 96)
    pygame.draw.rect(tela, (20, 30, 24), caixa.move(0, 4), border_radius=12)
    pygame.draw.rect(tela, (250, 240, 210), caixa, border_radius=12)
    pygame.draw.rect(tela, (230, 190, 60), caixa, 4, border_radius=12)
    fig = pygame.Surface(caixa.size, pygame.SRCALPHA)
    figura(fig, ident, caixa.width / 2, caixa.height / 2, t)
    tela.blit(fig, caixa.topleft)
    for i in range(6):
        a = t * 3 + i
        pygame.draw.circle(tela, (255, 230, 120), (int(caixa.centerx + math.cos(a) * 100), int(caixa.centery + math.sin(a) * 56)), 2)


def icone_album(tela, x, y, k=1.0):
    """Livrinho de figurinhas."""
    pygame.draw.rect(tela, PRETO, R(x - 16 * k, y - 12 * k, 32 * k, 24 * k), border_radius=int(3 * k))
    pygame.draw.rect(tela, (200, 70, 60), R(x - 14 * k, y - 10 * k, 28 * k, 20 * k), border_radius=int(3 * k))
    pygame.draw.line(tela, PRETO, (x, y - 10 * k), (x, y + 10 * k), max(1, int(2 * k)))
    pygame.draw.rect(tela, (250, 240, 210), R(x - 11 * k, y - 7 * k, 8 * k, 10 * k))
    pygame.draw.rect(tela, (250, 240, 210), R(x + 3 * k, y - 7 * k, 8 * k, 10 * k))
    MD.desenhar(tela, x + 7 * k, y - 1 * k, "ouro", max(2, int(3 * k)))
