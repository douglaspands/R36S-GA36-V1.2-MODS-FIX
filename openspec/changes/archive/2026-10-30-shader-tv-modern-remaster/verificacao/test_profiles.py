import math

OH = 480
H_game = 224
py = H_game / OH  # ~0.4666667

def test_profile(name, func):
    # Para cada uma das 224 linhas do jogo, encontre os pixels de tela que cobrem a fronteira da linha
    # e meça a profundidade máxima do scanline observada naquela linha.
    depths_per_game_line = []
    screen_values = []
    
    for y_screen in range(OH):
        v = (y_screen + 0.5) / OH
        y_game = v * H_game
        val = func(y_game, py)
        screen_values.append(val)
        
    for k in range(H_game):
        # A fronteira entre a linha k e k+1 está em y_game = k + 1.0
        # Encontre os pixels de tela mais próximos dessa fronteira
        y_target = k + 1.0
        # Pixels na vizinhança da fronteira
        nearby = [screen_values[ys] for ys in range(OH) if abs((ys + 0.5)*py - y_target) < 1.2 * py]
        if nearby:
            max_darkness = 1.0 - min(nearby)  # quanto mais escuro, maior o valor
            depths_per_game_line.append(max_darkness)
            
    min_d = min(depths_per_game_line)
    max_d = max(depths_per_game_line)
    ratio = min_d / max_d if max_d > 0 else 1.0
    print(f"[{name}]")
    print(f"  Profundidade mínima nas 224 linhas: {min_d:.4f}")
    print(f"  Profundidade máxima nas 224 linhas: {max_d:.4f}")
    print(f"  Uniformidade (min/max):             {ratio * 100.0:.2f}% (100% = perfeitamente uniforme)")
    print()

# 1. Perfil antigo (seno pontual)
def f_antigo(y_game, py):
    y_pos = y_game - math.floor(y_game) - 0.5
    s = math.sin(math.pi * y_pos)
    return 1.0 - 0.15 * (s * s)

# 2. Perfil Gaussiano com largura adaptativa ao tamanho do pixel de tela
def f_gauss_adaptativo(y_game, py):
    # Distância até a fronteira de linha mais próxima
    pos = y_game - math.floor(y_game)
    dist = min(pos, 1.0 - pos)  # 0.0 na fronteira, 0.5 no centro
    # Largura da scanline proporcional a py para cobrir o pixel de tela
    sigma = max(py * 0.70, 0.25)
    # Gaussiana invertida na fronteira: 0 na fronteira (escuro), 1 no centro (claro)
    # dist vai de 0 (fronteira) a 0.5 (centro)
    # Queremos que na fronteira atenue por 0.15, e no centro atenue 0
    t = math.exp(- (dist * dist) / (2.0 * sigma * sigma))
    return 1.0 - 0.15 * t

# 3. Box filter analítico na fronteira
def f_box_analitico(y_game, py):
    pos = y_game - math.floor(y_game)
    gap = min(py * 0.85, 0.40)
    lo = pos - 0.5 * py
    hi = pos + 0.5 * py
    # cobertura da faixa [1-gap, 1] ou [0, gap]
    cov1 = max(0.0, min(hi, 1.0) - max(lo, 1.0 - gap))
    cov2 = max(0.0, min(hi, gap) - max(lo, 0.0))
    cov3 = max(0.0, min(hi, 0.0) - max(lo, -gap))
    cover = min((cov1 + cov2 + cov3) / py, 1.0)
    return 1.0 - 0.15 * cover

# 4. Modulação Cosseno Suavizada com Anti-Aliasing (sinc(py))
def f_cosseno_aa(y_game, py):
    # y vai de 0 a H_game
    # Frequência fundamental é 2*pi*y_game (1 ciclo por linha de jogo)
    # sinc(py) = sin(pi * py) / (pi * py)
    sinc = math.sin(math.pi * py) / (math.pi * py)
    # Na fronteira (y inteiro), cos(2*pi*y) = 1 (máxima atenuação)
    # No centro (y + 0.5), cos(2*pi*y) = -1 (máximo brilho)
    # Atenuação: 0 no centro, TV_SCANLINES na fronteira
    # (1 - cos(2*pi*y)) / 2 dá 0 na fronteira e 1 no centro? Não:
    # y=0 (fronteira) -> cos(0) = 1. Queremos escuro na fronteira!
    # Então (1 + cos(2*pi*y)) / 2 dá 1 na fronteira e 0 no centro!
    mod = 0.5 * (1.0 + math.cos(2.0 * math.pi * y_game) * sinc)
    return 1.0 - 0.15 * mod

for s_mult in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]:
    def make_gauss(mult):
        def f(y_game, py):
            pos = y_game - math.floor(y_game)
            dist = min(pos, 1.0 - pos)
            sigma = py * mult
            t = math.exp(- (dist * dist) / (2.0 * sigma * sigma))
            return 1.0 - 0.15 * t
        return f
    test_profile(f"Gauss mult={s_mult:.1f}", make_gauss(s_mult))
