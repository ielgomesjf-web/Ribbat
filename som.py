"""
Música do jogo, feita pelo próprio código (igual os desenhos: nenhum arquivo extra).

As músicas são compostas pelo Gomes no Strudel (strudel.cc) e o código original fica em musica/.
Aqui elas são escritas do mesmo jeitinho (as mesmas notas e batidas) e um sintetizador pequeno
transforma em som:
  - "square", "triangle", "sawtooth", "sine": as ondas do Strudel
  - "bd" bumbo, "sd" caixa, "hh" chimbal: imitando a bateria Roland TR-909
  - "~" é silêncio, "x*3" toca 3 vezes no espaço de um passo
  - .room(0.4) = eco de sala (reverb)

Se o computador não tiver som, o jogo continua funcionando (só fica mudo).
"""
import hashlib
import json
import math
import os
import random
import threading
from array import array

import pygame

TAXA = 44100

# ---------------------------------------------------------------- as músicas (do Strudel)
# Chefões (Gomes): setcps(0.55) / stack(
#   n("3 5 ~ 7 ~ 0 1 1 3 ~ 5 ~").scale("A3:minor").s("square").gain(0.5),
#   s("bd ~ ~ sd ~ ~ bd ~ bd sd ~ ~, hh*6").bank("RolandTR909").gain(0.7))
# Fases (Gomes): setcps(0.30) / stack(
#   n("~ 0 0 ~ 5 ~ ~ 1 1 ~ 7 ~").scale("C3:major").s("triangle").room(0.40))
MUSICAS = {
    "fase": {
        "cps": 0.30,
        "camadas": [
            {"n": "~ 0 0 ~ 5 ~ ~ 1 1 ~ 7 ~", "escala": ("C3", "major"), "s": "triangle", "room": 0.40},
        ],
    },
    "chefe": {
        "cps": 0.55,
        "camadas": [
            {"n": "3 5 ~ 7 ~ 0 1 1 3 ~ 5 ~", "escala": ("A3", "minor"), "s": "square", "gain": 0.5},
            {"s": "bd ~ ~ sd ~ ~ bd ~ bd sd ~ ~", "gain": 0.7},
            {"s": "hh*6", "gain": 0.7},
        ],
    },
}

ESCALAS = {"major": (0, 2, 4, 5, 7, 9, 11), "minor": (0, 2, 3, 5, 7, 8, 10)}
NOTAS = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}


def midi(nome):
    """'A3' -> 57"""
    return 12 * (int(nome[1:]) + 1) + NOTAS[nome[0].lower()]


def passos(padrao):
    """'3 5 ~ hh*2' -> [(inicio, duração, valor)] com tempo em voltas (0..1)."""
    toks = padrao.split()
    out = []
    for i, tok in enumerate(toks):
        rep = 1
        if "*" in tok:
            tok, rep = tok.split("*")
            rep = int(rep)
        for k in range(rep):
            ini = (i + k / rep) / len(toks)
            if tok != "~":
                out.append((ini, 1 / len(toks) / rep, tok))
    return out


# ---------------------------------------------------------------- instrumentos
def _onda(tipo, fase):
    f = fase % 1.0
    if tipo == "square":
        return 1.0 if f < 0.5 else -1.0
    if tipo == "sawtooth":
        return 2 * f - 1
    if tipo == "triangle":
        return 4 * abs(f - 0.5) - 1
    return math.sin(fase * math.tau)


def nota(tipo, freq, dur):
    """Uma nota com envelope (ataque rápido, cai um pouco, segura, solta)."""
    solta = 0.05
    n = int((dur + solta) * TAXA)
    out = [0.0] * n
    filtro = 0.0
    for i in range(n):
        t = i / TAXA
        if t < 0.004:
            env = t / 0.004
        elif t < dur:
            env = 0.65 + 0.35 * math.exp(-(t - 0.004) * 20)
        else:
            env = (0.65 + 0.35 * math.exp(-(dur - 0.004) * 20)) * max(0.0, 1 - (t - dur) / solta)
        v = _onda(tipo, freq * t) * env
        filtro += (v - filtro) * 0.35                   # tira um pouquinho do chiado da onda quadrada
        out[i] = filtro * 0.32
    return out


def bumbo():
    n = int(0.45 * TAXA)
    out, fase = [0.0] * n, 0.0
    for i in range(n):
        t = i / TAXA
        f = 48 + 170 * math.exp(-t * 32)                # o "tum" do 909: começa agudo e afunda
        fase += f / TAXA
        out[i] = math.sin(fase * math.tau) * math.exp(-t * 7) * 0.95
    return out


def caixa(rnd):
    n = int(0.25 * TAXA)
    out, ant = [0.0] * n, 0.0
    for i in range(n):
        t = i / TAXA
        r = rnd.uniform(-1, 1)
        chiado = r - ant * 0.6                          # ruído mais agudo
        ant = r
        tom = math.sin(t * 185 * math.tau) * math.exp(-t * 28)
        out[i] = (chiado * 0.55 * math.exp(-t * 16) + tom * 0.5) * 0.8
    return out


def chimbal(rnd):
    n = int(0.07 * TAXA)
    out, ant = [0.0] * n, 0.0
    for i in range(n):
        t = i / TAXA
        r = rnd.uniform(-1, 1)
        out[i] = (r - ant) * 0.5 * math.exp(-t * 70) * 0.5
        ant = r
    return out


def renderizar(musica):
    """Uma volta da música (que repete sem emenda: o rabinho do som passa pro começo)."""
    volta = 1 / musica["cps"]
    n = int(volta * TAXA)
    mix = [0.0] * n
    rnd = random.Random(7)
    bateria = {"bd": bumbo(), "sd": caixa(rnd), "hh": chimbal(rnd)}
    for c in musica["camadas"]:
        camada = [0.0] * n
        _camada(c, camada, n, volta, bateria)
        if c.get("room"):
            camada = eco(camada, c["room"])
        for i in range(n):
            mix[i] += camada[i]
    pico = max(1e-6, max(abs(x) for x in mix))
    k = 0.85 / pico * 32767                              # todas as músicas no mesmo volume
    return array("h", (int(x * k) for x in mix))


def _camada(c, mix, n, volta, bateria):
    """Uma camada do stack(): melodia (n + escala) ou bateria (s)."""
    if "n" in c:
        base, modo = c["escala"]
        esc = ESCALAS[modo]
        for ini, dur, v in passos(c["n"]):
            g = int(v)
            m = midi(base) + 12 * (g // len(esc)) + esc[g % len(esc)]
            som = nota(c.get("s", "triangle"), 440 * 2 ** ((m - 69) / 12), dur * volta)
            _somar(mix, som, int(ini * n), c.get("gain", 1.0))
    else:
        for ini, dur, v in passos(c["s"]):
            _somar(mix, bateria[v], int(ini * n), c.get("gain", 1.0))


def eco(sinal, quanto):
    """Reverb de sala (Schroeder: 4 ecos que vão sumindo + 2 que espalham). Roda a música 2 vezes
    e fica com a segunda, assim o eco do fim já está soando no começo e o loop não tem emenda."""
    n = len(sinal)
    x = sinal + sinal
    molhado = [0.0] * (2 * n)
    for atraso, fb in ((1116, 0.80), (1188, 0.79), (1277, 0.78), (1356, 0.77)):
        buf = [0.0] * atraso
        filtro, j = 0.0, 0
        for i in range(2 * n):
            saida = buf[j]
            filtro = saida * 0.6 + filtro * 0.4               # abafa os agudos do eco
            buf[j] = x[i] + filtro * fb
            molhado[i] += saida * 0.25
            j = (j + 1) % atraso
    for atraso in (556, 441):
        buf = [0.0] * atraso
        j = 0
        for i in range(2 * n):
            b = buf[j]
            buf[j] = molhado[i] + b * 0.5
            molhado[i] = b - molhado[i] * 0.5
            j = (j + 1) % atraso
    return [sinal[i] * (1 - quanto * 0.5) + molhado[n + i] * quanto for i in range(n)]


def _somar(mix, som, ini, ganho):
    n = len(mix)
    for i, v in enumerate(som):
        mix[(ini + i) % n] += v * ganho


# ---------------------------------------------------------------- efeitos de som (curtinhos)
def _env(t, dur, ataque=0.005):
    if t < ataque:
        return t / ataque
    return max(0.0, 1 - (t - ataque) / max(1e-6, dur - ataque)) ** 2


def _varre(tipo, f0, f1, dur, vol=0.5, curva=1.0):
    """Um som que escorrega de f0 até f1 (o "fiu" dos videogames)."""
    n, fase, out = int(dur * TAXA), 0.0, []
    for i in range(n):
        k = (i / n) ** curva
        fase += (f0 + (f1 - f0) * k) / TAXA
        out.append(_onda(tipo, fase) * _env(i / TAXA, dur) * vol)
    return out


def _ruido(dur, vol=0.5, agudo=0.5, semente=3, sobe=False):
    rnd = random.Random(semente)
    n, ant, filtro, out = int(dur * TAXA), 0.0, 0.0, []
    for i in range(n):
        r = rnd.uniform(-1, 1)
        v = r - ant * agudo
        ant = r
        corte = 0.05 + 0.6 * (i / n) if sobe else 0.5
        filtro += (v - filtro) * corte
        out.append(filtro * _env(i / TAXA, dur) * vol)
    return out


def _notas(tipo, midis, passo, vol=0.4, ultima=0.3):
    out = []
    for k, m in enumerate(midis):
        dur = ultima if k == len(midis) - 1 else passo
        f = 440 * 2 ** ((m - 69) / 12)
        out += [_onda(tipo, f * i / TAXA) * _env(i / TAXA, dur + 0.02) * vol for i in range(int(dur * TAXA))]
    return out


def _junta(*sons):
    n = max(len(x) for x in sons)
    return [sum(x[i] for x in sons if i < len(x)) for i in range(n)]


EFEITOS = {
    "pulo": lambda: _varre("square", 260, 620, 0.12, 0.22, 0.6),
    "lingua": lambda: _junta(_varre("sine", 900, 260, 0.16, 0.5), _ruido(0.08, 0.15, 0.8)),     # slurp!
    "investida": lambda: _ruido(0.22, 0.55, 0.3, sobe=True),                                    # fuuush
    "mosca": lambda: _notas("triangle", (88, 93), 0.05, 0.35, 0.08),                            # plim
    "pop": lambda: _varre("sine", 620, 160, 0.11, 0.6),                                         # derrotou um bicho
    "dor": lambda: _junta(_varre("square", 420, 110, 0.28, 0.25), _ruido(0.1, 0.25, 0.2)),
    "acerto": lambda: _junta(_varre("square", 240, 90, 0.12, 0.3), _ruido(0.09, 0.45, 0.4, 5)),
    "pedra": lambda: _junta(_varre("sine", 120, 40, 0.35, 0.7), _ruido(0.3, 0.5, 0.1, 9)),       # crack!
    "teia": lambda: [math.sin(math.tau * (150 + 40 * math.sin(i / TAXA * 40)) * i / TAXA) * _env(i / TAXA, 0.3) * 0.45
                     for i in range(int(0.3 * TAXA))],                                         # boing grudento
    "bandeira": lambda: _notas("triangle", (72, 76, 79, 84), 0.07, 0.35, 0.25),
    "cura": lambda: _notas("sine", (76, 79, 83, 88), 0.06, 0.4, 0.2),
    "vitoria": lambda: _notas("square", (72, 76, 79, 76, 79, 84), 0.1, 0.2, 0.45),
    "gameover": lambda: _notas("triangle", (67, 64, 60, 55), 0.18, 0.4, 0.5),
}
VOLUME_EFEITOS = 0.35
EFEITOS_VERSAO = 1          # mudou algum efeito? aumenta aqui (pra fabricar de novo em vez de usar o guardado)


def fabricar_efeito(nome):
    sinal = EFEITOS[nome]()
    pico = max(1e-6, max(abs(x) for x in sinal))
    k = 0.8 / pico * 32767
    return array("h", (int(x * k) for x in sinal))


# ---------------------------------------------------------------- tocar
_ligado = False
_dados = {}                 # as músicas já fabricadas (feitas por trás, sem travar o jogo)
_efeitos_dados = {}
_efeitos = {}
_ultimo_efeito = {}
_sons = {}
_tocando = None
_canal = None
VOLUME = 0.25                # bem de fundo (o Gomes pediu: "só de fundo")


def iniciar():
    """Liga o som (chamar ANTES de pygame.init). Sem placa de som, fica mudo e tudo bem."""
    global _ligado
    try:
        pygame.mixer.pre_init(TAXA, -16, 1, 1024)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(16)
        _ligado = pygame.mixer.get_init() is not None
    except pygame.error:
        _ligado = False
    if _ligado:                                          # fabrica as músicas enquanto o título aparece
        threading.Thread(target=_fabricar, daemon=True).start()


def _guardado(coisa):
    """Onde fica o som já fabricado (junto do save). O nome muda se a música/efeito mudar."""
    import progresso
    chave = hashlib.md5(json.dumps(coisa, sort_keys=True).encode()).hexdigest()[:12]
    return os.path.join(os.path.dirname(progresso.caminho()), "musica", f"{chave}.pcm")


def _pegar(coisa, fabricar):
    """Lê o som guardado; se não tiver (primeira vez), fabrica e guarda."""
    arq = _guardado(coisa)
    try:
        with open(arq, "rb") as f:
            dados = array("h")
            dados.frombytes(f.read())
        if dados:
            return dados
    except OSError:
        pass
    dados = fabricar()
    try:
        os.makedirs(os.path.dirname(arq), exist_ok=True)
        with open(arq + ".tmp", "wb") as f:
            f.write(dados.tobytes())
        os.replace(arq + ".tmp", arq)
    except OSError:
        pass
    return dados


def _fabricar():
    for nome in EFEITOS:                                 # os efeitos primeiro (são curtinhos)
        _efeitos_dados[nome] = _pegar(["efeito", nome, EFEITOS_VERSAO, TAXA], lambda: fabricar_efeito(nome))
    for nome, m in MUSICAS.items():
        _dados[nome] = _pegar(m, lambda: renderizar(m))


def tocar(nome):
    """Troca a música (None = silêncio). Chamar todo quadro: só faz algo quando muda."""
    global _tocando, _canal
    if not _ligado or nome == _tocando:
        return
    if nome is not None and nome not in _dados:
        return                                           # ainda fabricando: tenta de novo no próximo quadro
    if _canal:
        _canal.fadeout(300)
    _tocando = nome
    if nome is None:
        return
    if nome not in _sons:
        _sons[nome] = _som_de(_dados[nome])
    _canal = _sons[nome].play(loops=-1, fade_ms=200)
    if _canal:
        _canal.set_volume(VOLUME)


def _som_de(dados):
    if pygame.mixer.get_init()[2] == 2:                  # o Windows às vezes só abre em estéreo
        est = array("h", [0]) * (len(dados) * 2)
        est[0::2] = dados
        est[1::2] = dados
        dados = est
    return pygame.mixer.Sound(buffer=dados.tobytes())


def efeito(nome):
    """Toca um efeito curtinho (se o som estiver ligado e ele já estiver pronto)."""
    if not _ligado or nome not in _efeitos_dados:
        return
    agora = pygame.time.get_ticks()
    if agora - _ultimo_efeito.get(nome, -999) < 60:     # o mesmo som 2x no mesmo instante: só um
        return
    _ultimo_efeito[nome] = agora
    if nome not in _efeitos:
        _efeitos[nome] = _som_de(_efeitos_dados[nome])
        _efeitos[nome].set_volume(VOLUME_EFEITOS)
    _efeitos[nome].play()


def pausar(pausado):
    if _ligado and _canal:
        _canal.set_volume(VOLUME * (0.25 if pausado else 1.0))


def musica_do_jogo(jogo):
    """Qual música toca agora: a dos chefões (luta + corrida da Águia) ou a das fases."""
    e = jogo.estado
    if e == "pausa":
        e = getattr(jogo, "voltar_para", "jogando")
    if e == "chefe" or (e == "jogando" and getattr(jogo, "corrida", None) is not None):
        return "chefe"
    if e == "jogando":
        return "fase"
    return None


def atualizar(jogo):
    tocar(musica_do_jogo(jogo))
    pausar(jogo.estado == "pausa")
