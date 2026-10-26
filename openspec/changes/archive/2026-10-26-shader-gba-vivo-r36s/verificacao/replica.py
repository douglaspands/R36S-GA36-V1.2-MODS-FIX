"""Réplica numérica do gba-modern-remaster.glsl e medição dos cenários da spec.

Uso (RetroArch não é necessário; veja LEIA-ME.md para obter as capturas):

    uv run --with pillow --with numpy python -I replica.py CAPTURA_MARIO_KART.png CAPTURA_SMA3.png [SAIDA_DIR [EXTRA.png...]]

As capturas são do mGBA SEM shader, em 480x320 (2x de 240x160, vizinho mais próximo). O script
reduz para 240x160, aplica o shader (float32) e imprime as medidas dos cenários de
specs/gba-emulation/spec.md. Com SAIDA_DIR, grava PNGs de comparação (640x427, a tela do R36S).
Qualquer mudança no .glsl precisa ser espelhada em shader() abaixo (e DEF, que repete os padrões);
confira com `uv run python -I -m unittest tests.test_shaders_gba` que os padrões do .glsl não mudaram.
fp16=True arredonda os pontos críticos para meia precisão (estimativa do mediump do Mali-400).
"""
import os
import sys

import numpy as np
from PIL import Image

W709 = np.array([0.2126, 0.7152, 0.0722], np.float32)
# Padrões do .glsl (SATURATION, ROLLOFF... = identificadores do código; CEIL e GAPMAX são constantes do shader)
DEF = dict(VIBRANCE=0.45, SATURATION=1.10, ROLLOFF=0.35, CONTRAST=0.28, HIGHLIGHT=0.05,
           SOFTNESS=0.15, LCD_GRID=0.10, BRIGHTNESS=0.0, CEIL=0.05, GAPMAX=0.3)
NEUTRO = dict(VIBRANCE=0, SATURATION=1, ROLLOFF=0, CONTRAST=0, HIGHLIGHT=0)


def carrega(caminho):
    a = np.asarray(Image.open(caminho).convert("RGB")).astype(np.float32) / 255
    return a[::2, ::2] if a.shape[1] == 480 else a  # 480x320 (2x) ou 240x160 (nativo)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def bilinear(tex, u, v):
    h, w, _ = tex.shape
    x, y = u * w - 0.5, v * h - 0.5
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    g = lambda yy, xx: tex[np.clip(yy, 0, h - 1), np.clip(xx, 0, w - 1)]
    return ((g(y0, x0) * (1 - fx) + g(y0, x0 + 1) * fx) * (1 - fy)
            + (g(y0 + 1, x0) * (1 - fx) + g(y0 + 1, x0 + 1) * fx) * fy)


def shader(tex, OW, OH, fp16=False, **kw):
    P = dict(DEF)
    P.update(kw)
    q = (lambda x: x.astype(np.float16).astype(np.float32)) if fp16 else (lambda x: x)
    h, w, _ = tex.shape
    ys, xs = np.mgrid[0:OH, 0:OW].astype(np.float32)
    u, v = q((xs + 0.5) / OW), q((ys + 0.5) / OH)                     # varying TEX0 (mediump)
    px = w / OW                                                       # pixel de saída, em pixels do jogo
    width = max(px * (1 - P["SOFTNESS"]) + P["SOFTNESS"], 1e-4)
    pxx, pyy = q(u * w - 0.5), q(v * h - 0.5)
    ix, iy = np.floor(pxx), np.floor(pyy)
    fx = np.clip((q(pxx - ix) - 0.5) / width + 0.5, 0, 1)
    fy = np.clip((q(pyy - iy) - 0.5) / width + 0.5, 0, 1)
    c = bilinear(tex, (ix + 0.5 + fx) / w, (iy + 0.5 + fy) / h)       # sharp-bilinear
    L = c @ W709
    mx, mn = c.max(-1), c.min(-1)
    sat = (mx - mn) / np.maximum(mx, 0.001)
    hs = smooth(0.5, 1.0, L)
    if P.get("ANTIGO"):
        gain = (1 + P["VIBRANCE"] * (1 - sat)) * P["SATURATION"]
    else:  # o vibrance some perto do cinza (brancos e fundos bege não ganham tom)
        gain = (1 + P["VIBRANCE"] * np.minimum(1 - sat, 4 * sat * (1 - sat))) * P["SATURATION"]
    ceil = np.minimum(1, mx + P["CEIL"])
    L2 = L + P["CONTRAST"] * 2 * L * (1 - L) * (L - 0.35) + P["HIGHLIGHT"] * hs * (1 - L) * 0.5
    if P.get("ANTIGO"):  # build 20261026-103244: o roll-off e a curva desbotavam amarelos
        c = np.maximum(L[..., None] + (c - L[..., None]) * (gain * (1 - P["ROLLOFF"] * hs))[..., None], 0)
        c = c * (L2 / np.maximum(L, 0.001))[..., None]
    else:
        A = (L + (mx - L) * hs)[..., None]                            # âncora: luma -> canal máximo nos claros
        c = np.maximum(A + (c - A) * (1 + (gain - 1) * (1 - P["ROLLOFF"] * hs))[..., None], 0)
        k = L2 / np.maximum(L, 0.001)
        k = np.maximum(k, k + (1 - k) * sat * sat)                    # a curva não apaga cores saturadas
        k = np.minimum(k, np.maximum(ceil / np.maximum(c.max(-1), 0.001), 1))  # nem clareia o que está no teto
        c = c * k[..., None]
        L2 = c @ W709
    top = c.max(-1)
    t = np.where(top > ceil, np.clip((ceil - L2) / np.maximum(top - L2, 1e-4), 0, 1), 1)
    c = L2[..., None] + (c - L2[..., None]) * t[..., None]            # proteção de clip
    gap = min(px, P["GAPMAX"])
    pos_x, pos_y = q(u * w), q(v * h)
    pos_x, pos_y = pos_x - np.floor(pos_x), pos_y - np.floor(pos_y)

    def cobertura(pos):
        lo, hi = pos - 0.5 * px, pos + 0.5 * px
        cv = (np.clip(np.minimum(hi, 1) - np.maximum(lo, 1 - gap), 0, gap)
              + np.clip(np.minimum(hi, 0) - np.maximum(lo, -gap), 0, gap))
        return np.minimum(cv / px, 1)

    lit = (1 - P["LCD_GRID"] * cobertura(pos_x)) * (1 - P["LCD_GRID"] * cobertura(pos_y))
    return np.clip(c * (lit * (1 + P["BRIGHTNESS"]))[..., None], 0, 1)


def vizinho(tex, OW, OH):
    h, w, _ = tex.shape
    return tex[(np.arange(OH) * h // OH)][:, (np.arange(OW) * w // OW)]


def sat(a):
    mx = a.max(-1)
    return np.where(mx > 0, (mx - a.min(-1)) / np.maximum(mx, 1e-6), 0)


def luma(a):
    return a @ W709


def grava(a, caminho):
    Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8)).save(caminho)


def medidas(mk, sma):
    plano = np.full((160, 240, 3), 0.6, np.float32)
    grad = lambda x: np.abs(np.diff(x[..., 1], axis=1)).mean()
    for OW, OH in ((480, 320), (640, 427)):
        print(f"=== saída {OW}x{OH} (px={240 / OW:.3f})")
        for nome, a in (("Mario Kart", mk), ("Super Mario Advance 3", sma)):
            ref, b = vizinho(a, OW, OH), shader(a, OW, OH)
            sem_lcd = shader(a, OW, OH, LCD_GRID=0.0)
            Lr, sr, sb = luma(ref), sat(ref), sat(b)
            verm = (ref[..., 0] > 150 / 255) & (ref[..., 1] < 110 / 255) & (ref[..., 2] < 110 / 255)
            puro = (abs(ref[..., 0] - 1) < .012) & (abs(ref[..., 1] - 40 / 255) < .03) & (ref[..., 2] < .03)
            claros = (Lr > 0.6) & (sr > 0.25)
            medios = (Lr > 0.2) & (Lr < 0.5) & (sr > 0.3)
            estouro = ((b.max(-1) >= 254.5 / 255) & (ref.max(-1) < 245 / 255)).mean() * 100
            g = lambda m: (sr[m].mean(), sb[m].mean()) if m.any() else (0.0, 0.0)
            print(f" {nome}: luma {(luma(b).mean() / Lr.mean() - 1) * 100:+.1f}% | sat média {sr.mean():.3f}->{sb.mean():.3f}"
                  f" | vermelhos(n={verm.sum()}) {g(verm)[0]:.3f}->{g(verm)[1]:.3f} | puro(n={puro.sum()}) {g(puro)[0]:.3f}->{g(puro)[1]:.3f}"
                  f" | claros {g(claros)[0]:.3f}->{g(claros)[1]:.3f} ({(g(claros)[1] / max(g(claros)[0], 1e-6) - 1) * 100:+.0f}%)"
                  f" | médios {g(medios)[0]:.3f}->{g(medios)[1]:.3f} | estouro {estouro:.2f}% | nitidez (LCD 0) {grad(sem_lcd) / grad(ref) * 100:.0f}%")
        m = luma(shader(plano, OW, OH, **NEUTRO))[40:-40, 40:-40]
        col, lin = m.mean(0), m.mean(1)
        print(f" cena plana 0.6: menor/maior {m.min() / m.max():.2f}; colunas < 98% do pico {(col < .98 * col.max()).mean() * 100:.0f}%, linhas {(lin < .98 * lin.max()).mean() * 100:.0f}%")
        z = luma(shader(plano, OW, OH, LCD_GRID=0.0, **NEUTRO))[40:-40, 40:-40]
        print(f" LCD GRID 0: menor/maior {z.min() / z.max():.3f}")
        for nome, a in (("Mario Kart", mk), ("Super Mario Advance 3", sma)):
            x, y = shader(a, OW, OH), shader(a, OW, OH, fp16=True)
            print(f" fp16 {nome}: PSNR {10 * np.log10(1 / max(((x - y) ** 2).mean(), 1e-12)):.1f} dB")
    medidas_cartela()


def matiz(c):
    import colorsys
    return colorsys.rgb_to_hsv(*c)[0] * 360


def medidas_cartela():
    # Centro de cada célula da cartela, sem a grade LCD, em 640x427
    out = shader(cartela(), 640, 427, LCD_GRID=0.0)
    print("=== cartela de cores (640x427, LCD 0): cor | sat original->shader | matiz (graus) | canal máximo (255)")
    pior_sat, pior_matiz, sobe = 1.0, 0.0, 0.0
    for n, (nome, rgb) in enumerate(CARTELA):
        y, x = divmod(n, 6)
        o = np.array(rgb, np.float32) / 255
        b = out[int((y * 40 + 20) * 427 / 160), int((x * 40 + 20) * 640 / 240)]
        so, sb = sat(o[None])[0], sat(b[None])[0]
        dh = abs((matiz(b) - matiz(o) + 180) % 360 - 180) if so > 0.05 else 0.0
        pior_sat, pior_matiz = min(pior_sat, sb - so), max(pior_matiz, dh)
        if o.max() >= 245 / 255:
            sobe = max(sobe, luma(b) - luma(o))
        print(f"  {nome:14} {so:.2f}->{sb:.2f} | {dh:4.1f} | {o.max() * 255:3.0f}->{b.max() * 255:3.0f}")
    print(f"  menor ganho de saturação {pior_sat:+.3f} | maior desvio de matiz {pior_matiz:.1f} graus"
          f" | maior subida de luma das cores no teto {sobe:+.3f}")


# Cartela de cores de referência (nome, RGB 0-255), 6 colunas x 4 linhas de 40x40 pixels do GBA
CARTELA = [
    ("amarelo", (255, 255, 0)), ("ouro", (247, 209, 64)), ("amarelo claro", (255, 255, 128)),
    ("laranja", (255, 153, 0)), ("vermelho", (230, 25, 25)), ("magenta", (255, 51, 204)),
    ("verde", (77, 230, 51)), ("ciano", (0, 204, 255)), ("ceu", (128, 179, 255)),
    ("azul puro", (0, 0, 255)), ("azul medio", (51, 102, 230)), ("azul escuro", (25, 38, 140)),
    ("roxo", (128, 51, 204)), ("azul cinza", (89, 115, 153)), ("pele", (255, 204, 166)),
    ("marrom", (140, 80, 40)), ("cinza", (128, 128, 128)), ("branco", (255, 255, 255)),
    ("pele Mario", (248, 184, 136)), ("pele clara", (255, 206, 156)), ("rosa claro", (255, 180, 200)),
    ("lilas", (200, 170, 240)), ("verde claro", (160, 240, 140)), ("ceu claro", (180, 210, 255)),
]


def cartela():
    tex = np.zeros((160, 240, 3), np.float32)
    for n, (_, rgb) in enumerate(CARTELA):
        y, x = divmod(n, 6)
        tex[y * 40:(y + 1) * 40, x * 40:(x + 1) * 40] = np.array(rgb, np.float32) / 255
    return tex


def rotula(a, titulo, nomes=False):
    from PIL import ImageDraw
    img = Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8))
    tela = Image.new("RGB", (img.width, img.height + 22), (24, 24, 24))
    tela.paste(img, (0, 22))
    d = ImageDraw.Draw(tela)
    d.text((6, 5), titulo, fill=(240, 240, 240))
    if nomes:
        sx, sy = img.width / 240, img.height / 160
        for n, (nome, _) in enumerate(CARTELA):
            y, x = divmod(n, 6)
            d.text((x * 40 * sx + 4, 22 + y * 40 * sy + 4), nome, fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    return tela


# Recortes ampliados (x0, y0, x1, y1 em pixels do GBA), por nome de exemplo
RECORTES = {"smw-logo": (10, 40, 230, 140), "smw-escolha": (130, 0, 230, 90)}


def exemplos(mk, sma, saida, extras=()):
    os.makedirs(saida, exist_ok=True)
    bil = dict(VIBRANCE=0, SATURATION=1, ROLLOFF=0, CONTRAST=0, HIGHLIGHT=0, SOFTNESS=1.0, LCD_GRID=0.0)
    versoes = (("1-sem-shader", "1. RetroArch sem shader (bilinear, cor crua)", bil),
               ("2-build-103244", "2. build 20261026-103244 (amarelo e pele desbotados)", dict(ANTIGO=1, ROLLOFF=0.65)),
               ("3-novo", "3. NOVO PADRAO: cor viva sem clarear, matiz mantido", {}),
               ("4-novo-contido", "4. variante mais contida (HIGHLIGHT ROLLOFF 0.65)", dict(ROLLOFF=0.65)))
    jogos = [("mario-kart", mk), ("super-mario-advance-3", sma), ("cartela-de-cores", cartela())]
    for nome, a in jogos + list(extras):
        quadros = []
        for sufixo, titulo, kw in versoes:
            q = shader(a, 640, 427, **kw)
            grava(q, f"{saida}/{nome}_{sufixo}.png")
            quadros.append(rotula(q, titulo, nomes=nome == "cartela-de-cores"))
        lado = Image.new("RGB", (640 * 2 + 4, quadros[0].height * 2 + 4), (24, 24, 24))
        for n, q in enumerate(quadros):
            lado.paste(q, ((n % 2) * 644, (n // 2) * (q.height + 4)))
        lado.save(f"{saida}/{nome}_comparacao-1-2-3-4.png")
        if nome in RECORTES:
            x0, y0, x1, y1 = (int(v * 640 / 240) for v in RECORTES[nome])
            partes = [q.crop((x0, y0 + 22, x1, y1 + 22)).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.NEAREST) for q in quadros]
            w, h = partes[0].size
            rec = Image.new("RGB", (w * 2 + 4, (h + 22) * 2 + 4), (24, 24, 24))
            from PIL import ImageDraw
            d = ImageDraw.Draw(rec)
            for n, (q, (_, titulo, _)) in enumerate(zip(partes, versoes)):
                x, y = (n % 2) * (w + 4), (n // 2) * (h + 26)
                d.text((x + 6, y + 5), titulo, fill=(240, 240, 240))
                rec.paste(q, (x, y + 22))
            rec.save(f"{saida}/{nome}_recorte-2x_1-2-3-4.png")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    mk, sma = carrega(sys.argv[1]), carrega(sys.argv[2])
    medidas(mk, sma)
    if len(sys.argv) > 3:
        # capturas extras (opcionais): o nome do exemplo é o do arquivo até o primeiro "-f"
        extras = [(os.path.basename(c).split("-f")[0], carrega(c)) for c in sys.argv[4:]]
        exemplos(mk, sma, sys.argv[3], extras)
