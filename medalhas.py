"""
Medalhas (pelo tempo) e o coração (zerou sem levar dano).

As metas vêm do tempo dos robôs nos testes, com bastante folga pra gente de verdade:
ouro ~ 1.5x o tempo do robô, prata ~ 2.5x. Bronze = só terminar.
"""
import math

import pygame

from config import *  # noqa: F401,F403

# (ouro, prata) em segundos. "tempo" = a fase, "tempo_chefe" = a luta (na Águia, luta + corrida)
METAS = {
    "fase1": {"tempo": (100, 165), "tempo_chefe": (80, 135)},     # robô: fase 65s, Viúva 53s
    "fase2": {"tempo": (75, 125), "tempo_chefe": (70, 115)},      # robô: 50s, Besouro 46s
    "fase3": {"tempo": (75, 125), "tempo_chefe": (90, 150)},      # robô: 50s, Rainha ~60s
    "fase4": {"tempo": (70, 115), "tempo_chefe": (75, 125)},      # robô: 46s, Gato 49s
    "fase5": {"tempo": (70, 110), "tempo_chefe": (140, 220)},     # robô: 44s, Águia 57s + corrida 33s
    "secreta": {"tempo": (1, 1), "tempo_chefe": (60, 100)},       # só chefão (o Vô); robô: ~32s
}
CORES = {"ouro": ((246, 200, 70), (170, 120, 30)), "prata": ((214, 220, 230), (120, 128, 140)),
         "bronze": ((214, 140, 80), (130, 74, 36))}
ORDEM = ("bronze", "prata", "ouro")


def medalha(ident, chave, tempo):
    """Qual medalha esse tempo dá (None se ainda não terminou)."""
    if tempo is None:
        return None
    ouro, prata = METAS[ident][chave]
    return "ouro" if tempo <= ouro else "prata" if tempo <= prata else "bronze"


def proxima(ident, chave, tempo):
    """A próxima medalha que dá pra pegar e o tempo que precisa (None se já é ouro)."""
    m = medalha(ident, chave, tempo)
    ouro, prata = METAS[ident][chave]
    if m == "bronze":
        return "prata", prata
    if m == "prata":
        return "ouro", ouro
    return None


def desenhar(tela, x, y, tipo, r=9, apagada=False):
    """Medalha redonda com fitinha. apagada = a que ainda falta pegar."""
    claro, escuro = CORES[tipo]
    if apagada:
        claro, escuro = (90, 90, 96), (50, 50, 56)
    pygame.draw.polygon(tela, (200, 40, 50) if not apagada else (70, 60, 60),
                        [(x - r * 0.7, y - r * 1.9), (x - r * 0.1, y - r * 0.6), (x - r * 0.9, y - r * 0.6)])
    pygame.draw.polygon(tela, (40, 90, 200) if not apagada else (60, 60, 70),
                        [(x + r * 0.7, y - r * 1.9), (x + r * 0.9, y - r * 0.6), (x + r * 0.1, y - r * 0.6)])
    pygame.draw.circle(tela, PRETO, (int(x), int(y)), int(r + 2))
    pygame.draw.circle(tela, escuro, (int(x), int(y)), int(r))
    pygame.draw.circle(tela, claro, (int(x), int(y)), int(r * 0.8))
    pygame.draw.arc(tela, (255, 255, 255), pygame.Rect(x - r * 0.55, y - r * 0.55, r * 1.1, r * 1.1),
                    math.pi * 0.55, math.pi * 1.05, max(1, int(r / 5)))


def desenhar_coracao(tela, x, y, r=8, apagado=False):
    """Coraçãozinho = zerou sem levar dano."""
    cor = (230, 60, 80) if not apagado else (80, 70, 74)
    for dx in (-r * 0.45, r * 0.45):
        pygame.draw.circle(tela, PRETO, (int(x + dx), int(y - r * 0.2)), int(r * 0.6) + 2)
    pygame.draw.polygon(tela, PRETO, [(x - r * 1.05, y), (x + r * 1.05, y), (x, y + r + 2)])
    for dx in (-r * 0.45, r * 0.45):
        pygame.draw.circle(tela, cor, (int(x + dx), int(y - r * 0.2)), int(r * 0.6))
    pygame.draw.polygon(tela, cor, [(x - r * 0.95, y), (x + r * 0.95, y), (x, y + r)])
