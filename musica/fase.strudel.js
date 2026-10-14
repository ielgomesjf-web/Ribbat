// Música das fases. Composta pelo Gomes no Strudel (strudel.cc).
// O jogo toca esta mesma música pelo som.py (MUSICAS["fase"]): se mudar aqui, mude lá também.
setcps(0.30)
stack(
  n("~ 0 0 ~ 5 ~ ~ 1 1 ~ 7 ~").scale("C3:major").s("triangle").room(0.40),
)
