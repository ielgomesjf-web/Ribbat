// Música dos chefões. Composta pelo Gomes no Strudel (strudel.cc).
// O jogo toca esta mesma música pelo som.py (MUSICAS["chefe"]): se mudar aqui, mude lá também.
setcps(0.55)
stack(
  n("3 5 ~ 7 ~ 0 1 1 3 ~ 5 ~").scale("A3:minor").s("square").gain(0.5),
  s("bd ~ ~ sd ~ ~ bd ~ bd sd ~ ~, hh*6").bank("RolandTR909").gain(0.7),
)
