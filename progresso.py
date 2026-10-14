"""Save do jogo: quais fases foram zeradas, quais chefes vencidos, o recorde de moscas
e os recordes de TEMPO ("tempo" = a fase, "tempo_chefe" = a luta com o chefão).

Fica em %APPDATA%/Ribbat/progresso.json (pra não sumir quando o .exe é trocado).
Os testes usam outro arquivo, apontado pela variável RIBBAT_SAVE.
"""
import json
import os


def caminho():
    if os.environ.get("RIBBAT_SAVE"):
        return os.environ["RIBBAT_SAVE"]
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "Ribbat", "progresso.json")


def carregar():
    try:
        with open(caminho(), encoding="utf-8") as f:
            dados = json.load(f)
    except (OSError, ValueError):
        dados = {}
    dados.setdefault("fases", {})
    if "carteira" not in dados:          # save antigo: as moscas que ele já tinha juntado viram dinheiro
        dados["carteira"] = sum(r.get("moscas", 0) for r in dados["fases"].values())
    dados.setdefault("chapeus", ["nenhum"])
    dados.setdefault("chapeu", "nenhum")
    return dados


def salvar(dados):
    arq = caminho()
    try:
        os.makedirs(os.path.dirname(arq), exist_ok=True)
        tmp = arq + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        os.replace(tmp, arq)   # troca de uma vez: nunca fica um save pela metade
    except OSError:
        pass                   # sem save não trava o jogo


def fase(dados, ident):
    return dados["fases"].setdefault(ident, {"zerada": False, "chefe": False, "moscas": 0})


def recorde(dados, ident, chave, tempo):
    """Guarda o tempo se for o melhor. Devolve True se foi recorde."""
    reg = fase(dados, ident)
    if reg.get(chave) is None or tempo < reg[chave]:
        reg[chave] = round(tempo, 2)
        return True
    return False


def tempo_total(dados):
    """Soma de todos os recordes (fases + chefões): o tempo de zerar o jogo."""
    return sum(r.get("tempo", 0) + r.get("tempo_chefe", 0) for r in dados["fases"].values())


def _arq_fantasma(ident):
    return os.path.join(os.path.dirname(caminho()), "fantasmas", f"{ident}.json")


def carregar_fantasma(ident):
    """O caminho do recorde: [[x, y, pose, dir], ...] (30 por segundo), ou None."""
    try:
        with open(_arq_fantasma(ident), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def salvar_fantasma(ident, quadros):
    arq = _arq_fantasma(ident)
    try:
        os.makedirs(os.path.dirname(arq), exist_ok=True)
        with open(arq + ".tmp", "w", encoding="utf-8") as f:
            json.dump(quadros, f, separators=(",", ":"))
        os.replace(arq + ".tmp", arq)
    except OSError:
        pass
