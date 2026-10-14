"""Números e cores do jogo. Mexer aqui muda o jogo inteiro."""

LARGURA, ALTURA = 960, 544
TILE = 32
FPS = 60

# ---- física (pixels por segundo) ----
GRAVIDADE = 2000
VEL_MAX = 260
ACEL = 2000
ATRITO = 2600
PULO = 760            # força do pulo
PULO_CORTE = 0.45     # soltar o botão no meio do pulo corta a subida
QUEDA_MAX = 900
COYOTE = 0.10         # dá pra pular um tiquinho depois de sair da beirada
BUFFER_PULO = 0.12    # apertar pulo um tiquinho antes de cair no chão também vale
QUIQUE = 520          # pulinho ao pisar num inimigo

# ---- habilidades ----
LINGUA_DUR = 0.30
LINGUA_ALCANCE = 150
DASH_VEL = 640
DASH_DUR = 0.20
DASH_RECARGA = 0.45

CORACOES_INICIO = 3
CORACOES_MAX = 4

# ---- teia ----
TEIA_VEL = 330        # velocidade da bola de teia
TEIA_ESCAPE = 3       # quantos apertos pra rasgar o casulo
LENTO_VEL = 100       # velocidade andando na teia grudenta do chão

# ---- pântano ----
SUPERFICIE = -2       # a água fica 2px acima do topo do bloco de água
TOPO_VITORIA = 26     # a vitória-régia boia 26px abaixo do topo do bloco dela
AFOGA = 10            # quanto o Ribbat precisa afundar na água pra contar como "caiu"

# ---- cores ----
CEU_TOPO = (118, 186, 232)
CEU_BAIXO = (206, 236, 214)
MORRO_LONGE = (128, 182, 150)
MORRO_PERTO = (84, 150, 96)
TERRA = (96, 70, 48)
TERRA_ESC = (70, 50, 34)
GRAMA = (78, 150, 72)
GRAMA_CLARA = (130, 190, 96)
GRAMA_ESC = (48, 108, 52)
MADEIRA = (176, 120, 64)
MADEIRA_ESC = (120, 78, 40)
ROCHA = (140, 138, 146)
ROCHA_ESC = (86, 84, 94)
LENCO = (214, 56, 56)
BRANCO = (255, 255, 255)
PRETO = (20, 20, 24)
AMARELO = (250, 214, 70)
TEIA = (236, 238, 246)
LAMA = (110, 80, 52)
