"""Réplica numérica do gb-modern-dmg.glsl e do gbc-modern-remaster.glsl e medição dos cenários da spec.

Uso (da raiz do projeto; RetroArch não é necessário, veja LEIA-ME.md para obter as capturas):

    uv run --with pillow --with numpy python -I openspec/changes/shaders-gb-gbc-r36s/verificacao/replica.py [CAPTURAS_DIR [SAIDA_DIR]]

CAPTURAS_DIR (padrão ~/.cache/shader-gb-gbc-test) traz as capturas SEM shader, em 160x144, feitas
por capturar-sem-shader.sh. O script aplica os shaders (float32), imprime as medidas dos cenários de
specs/gb-gbc-emulation/spec.md e grava as pranchas comparativas em SAIDA_DIR (padrão
var/exemplos-gb-gbc), em 533x480, a área do GB/GBC na tela de 640x480 do R36S (escala 3,33x).
Qualquer mudança num .glsl precisa ser espelhada aqui (cor_gb/cor_gbc, grade e os dicionários de
padrões); tests/test_shaders_gb_gbc.py confere que os padrões do .glsl são os de DEF_GB e DEF_GBC.
fp16=True arredonda os pontos críticos para meia precisão (estimativa do mediump do Mali-400).
Sai com código 1 se alguma medida não cumpre a spec.
"""
import colorsys
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

W709 = np.array([0.2126, 0.7152, 0.0722], np.float32)
# Padrões dos .glsl (TONE_SEP, WARMTH... = identificadores do código; o resto são constantes do shader)
# SOFTNESS 0.05 (e não 0.15 do GBA): os jogos de GB/GBC usam muito pontilhado de 1 pixel, e com
# 0.10 ou mais a nitidez em 2x cai abaixo de 97% (Pokemon, Zelda DX, DKC). Em 3,33x a transição
# continua com ~1 pixel de saída (width = 0.3 + 0.7 * SOFTNESS).
DEF_GB = dict(TONE_SEP=0.50, CONTRAST=0.20, WARMTH=0.50, SOFTNESS=0.05, LCD_GRID=0.22, BRIGHTNESS=0.0, GAPMAX=0.3)
DEF_GBC = dict(VIBRANCE=0.45, SATURATION=1.10, ROLLOFF=0.35, CONTRAST=0.28, HIGHLIGHT=0.05,
               SOFTNESS=0.05, LCD_GRID=0.10, BRIGHTNESS=0.0, CEIL=0.035, GAPMAX=0.3)
# Paleta High-Clarity DMG-01 (T0 tinta acesa ... T3 fundo desligado) e o tom do substrato na lacuna
T = np.array([(20, 36, 12), (56, 104, 44), (136, 176, 68), (216, 234, 148)], np.float32) / 255
SUBSTRATO = 0.55  # a lacuna da grade puxa para T3 * SUBSTRATO (sombra do relevo do substrato verde-oliva)
# Paleta DMG clássica (#0f380f, #306230, #8bac0f, #9bbc0f), só para a prancha de comparação
DMG_ANTIGA = np.array([(15, 56, 15), (48, 98, 48), (139, 172, 15), (155, 188, 15)], np.float32) / 255

OW, OH = 533, 480          # GB/GBC na tela do R36S
GB = ("sml2-f600", "zelda-la-f1500", "pokemon-red-f700")
GBC = ("smb-deluxe-f500", "zelda-dx-f1500", "dkc-f700")


def carrega(caminho):
    a = np.asarray(Image.open(caminho).convert("RGB")).astype(np.float32) / 255
    return a[::2, ::2] if a.shape[1] == 320 else a  # 320x288 (2x) ou 160x144 (nativo)


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


def amostra(tex, ow, oh, P, q):
    """Etapa 1 dos dois shaders: sharp-bilinear com uma leitura de textura."""
    h, w, _ = tex.shape
    ys, xs = np.mgrid[0:oh, 0:ow].astype(np.float32)
    u, v = q((xs + 0.5) / ow), q((ys + 0.5) / oh)                     # varying TEX0 (mediump)
    px = w / ow                                                       # pixel de saída, em pixels do jogo
    width = max(px * (1 - P["SOFTNESS"]) + P["SOFTNESS"], 1e-4)
    pxx, pyy = q(u * w - 0.5), q(v * h - 0.5)
    ix, iy = np.floor(pxx), np.floor(pyy)
    fx = np.clip((q(pxx - ix) - 0.5) / width + 0.5, 0, 1)
    fy = np.clip((q(pyy - iy) - 0.5) / width + 0.5, 0, 1)
    c = bilinear(tex, (ix + 0.5 + fx) / w, (iy + 0.5 + fy) / h)
    return c, u, v, px


def cobertura_grade(tex, u, v, px, P, q):
    """Fração (x, y) do pixel de saída que cai na lacuna de 1 pixel de saída na borda de trás."""
    h, w, _ = tex.shape
    gap = min(px, P["GAPMAX"])
    pos_x, pos_y = q(u * w), q(v * h)
    pos_x, pos_y = pos_x - np.floor(pos_x), pos_y - np.floor(pos_y)

    def cobertura(pos):
        lo, hi = pos - 0.5 * px, pos + 0.5 * px
        cv = (np.clip(np.minimum(hi, 1) - np.maximum(lo, 1 - gap), 0, gap)
              + np.clip(np.minimum(hi, 0) - np.maximum(lo, -gap), 0, gap))
        return np.minimum(cv / px, 1)

    return cobertura(pos_x), cobertura(pos_y)


def cor_gb(c, P):
    """Etapas 2 e 3 do gb-modern-dmg: luma, curva em S e os 4 tons High-Clarity DMG-01."""
    L = c @ W709
    L = np.clip(L + P["CONTRAST"] * 2 * L * (1 - L) * (L - 0.35), 0, 1)
    w = np.clip(L[..., None] * 3 - np.array([0, 1, 2], np.float32), 0, 1)
    w = w + (w * w * (3 - 2 * w) - w) * P["TONE_SEP"]                # mix(w, smoothstep, TONE_SEP)
    o = T[0] + (T[1] - T[0]) * w[..., 0:1] + (T[2] - T[1]) * w[..., 1:2] + (T[3] - T[2]) * w[..., 2:3]
    return o + (P["WARMTH"] - 0.5) * np.array([0.10, 0, -0.10], np.float32) * o[..., 1:2]


def shader_gb(tex, ow=OW, oh=OH, fp16=False, **kw):
    P = dict(DEF_GB)
    P.update(kw)
    q = (lambda x: x.astype(np.float16).astype(np.float32)) if fp16 else (lambda x: x)
    c, u, v, px = amostra(tex, ow, oh, P, q)
    c = cor_gb(c, P)
    cx, cy = cobertura_grade(tex, u, v, px, P, q)
    g = (1 - (1 - cx) * (1 - cy))[..., None]                          # lacuna em x ou em y
    c = c + (T[3] * SUBSTRATO - c) * (P["LCD_GRID"] * g)              # mix(c, substrato, LCD_GRID * g)
    return np.clip(c * (1 + P["BRIGHTNESS"]), 0, 1)


def cor_gbc(c, P):
    """Etapas 2 a 5 do gbc-modern-remaster (o pipeline do gba-modern-remaster)."""
    L = c @ W709
    mx, mn = c.max(-1), c.min(-1)
    sat = (mx - mn) / np.maximum(mx, 0.001)
    hs = smooth(0.5, 1.0, L)
    gain = (1 + P["VIBRANCE"] * np.minimum(1 - sat, 4 * sat * (1 - sat))) * P["SATURATION"]
    ceil = np.minimum(1, mx + P["CEIL"])
    L2 = L + P["CONTRAST"] * 2 * L * (1 - L) * (L - 0.35) + P["HIGHLIGHT"] * hs * (1 - L) * 0.5
    A = (L + (mx - L) * hs)[..., None]
    c = np.maximum(A + (c - A) * (1 + (gain - 1) * (1 - P["ROLLOFF"] * hs))[..., None], 0)
    k = L2 / np.maximum(L, 0.001)
    k = np.maximum(k, k + (1 - k) * sat * sat)
    k = np.minimum(k, np.maximum(ceil / np.maximum(c.max(-1), 0.001), 1))
    c = c * k[..., None]
    L2 = c @ W709
    top = c.max(-1)
    t = np.where(top > ceil, np.clip((ceil - L2) / np.maximum(top - L2, 1e-4), 0, 1), 1)
    return L2[..., None] + (c - L2[..., None]) * t[..., None]


def shader_gbc(tex, ow=OW, oh=OH, fp16=False, entrada=False, **kw):
    P = dict(DEF_GBC)
    P.update(kw)
    q = (lambda x: x.astype(np.float16).astype(np.float32)) if fp16 else (lambda x: x)
    c0, u, v, px = amostra(tex, ow, oh, P, q)
    c = cor_gbc(c0, P)
    cx, cy = cobertura_grade(tex, u, v, px, P, q)
    lit = (1 - P["LCD_GRID"] * cx) * (1 - P["LCD_GRID"] * cy)
    out = np.clip(c * (lit * (1 + P["BRIGHTNESS"]))[..., None], 0, 1)
    return (out, c0) if entrada else out


def vizinho(tex, ow, oh):
    h, w, _ = tex.shape
    return tex[(np.arange(oh) * h // oh)][:, (np.arange(ow) * w // ow)]


def sat(a):
    mx = a.max(-1)
    return np.where(mx > 0, (mx - a.min(-1)) / np.maximum(mx, 1e-6), 0)


def luma(a):
    return a @ W709


def matiz(c):
    return colorsys.rgb_to_hsv(*c)[0] * 360


def psnr(x, y):
    return 10 * np.log10(1 / max(((x - y) ** 2).mean(), 1e-12))


def nitidez(b, ref):
    # gradiente médio do verde, com shader, contra o do vizinho mais próximo com a mesma cor
    grad = lambda x: np.abs(np.diff(x[..., 1], axis=1)).mean() + np.abs(np.diff(x[..., 1], axis=0)).mean()
    return grad(b) / grad(ref) * 100


FALHAS = []


def confere(ok, texto):
    print(("  ok    " if ok else "  FALHA ") + texto)
    if not ok:
        FALHAS.append(texto)


def medidas_gb(caps):
    print("=== gb-modern-dmg")
    # 4 níveis do Game Boy em faixas verticais (0, 85, 170, 255), LCD_GRID 0
    tons = np.zeros((144, 160, 3), np.float32)
    for n, nivel in enumerate((0, 85, 170, 255)):
        tons[:, n * 40:(n + 1) * 40] = nivel / 255
    out = shader_gb(tons, LCD_GRID=0.0)
    cent = [out[240, int((n * 40 + 20) * OW / 160)] for n in range(4)]
    Ls = [float(luma(c)) for c in cent]
    print("  tons " + " | ".join(f"T{n} {tuple(int(v * 255 + .5) for v in c)} L={L:.3f}" for n, (c, L) in enumerate(zip(cent, Ls))))
    difs = [Ls[n + 1] - Ls[n] for n in range(3)]
    confere(min(difs) >= 0.20, f"Delta Luma entre tons vizinhos {', '.join(f'{d:.3f}' for d in difs)} (>= 0.20)")
    confere(Ls[3] > 0.82 and Ls[0] < 0.14, f"fundo L3 {Ls[3]:.3f} (> 0.82) e tinta L0 {Ls[0]:.3f} (< 0.14)")
    confere(all(c[1] > c[0] > c[2] for c in cent), "matiz verde-oliva (G > R > B) nos 4 tons")
    # mesmo teste com os cinzas do mGBA (0, 82, 173, 255) e de outros cores
    tons2 = tons.copy()
    for n, nivel in enumerate((0, 82, 173, 255)):
        tons2[:, n * 40:(n + 1) * 40] = nivel / 255
    out2 = shader_gb(tons2, LCD_GRID=0.0)
    L2 = [float(luma(out2[240, int((n * 40 + 20) * OW / 160)])) for n in range(4)]
    confere(min(L2[n + 1] - L2[n] for n in range(3)) >= 0.20, f"cinzas do mGBA (0/82/173/255): L {', '.join(f'{v:.3f}' for v in L2)}")
    # grade dot-matrix: blocos de T0 (tinta) e de T3 (fundo), padrões, 533x480
    bloco = np.zeros((144, 160, 3), np.float32)
    bloco[:, 80:] = 1.0
    g = luma(shader_gb(bloco))[60:-60]
    esc, cla = g[:, 30:230], g[:, 300:500]
    print(f"  grade T0: centro {esc.min():.3f}, lacuna {esc.max():.3f} | grade T3: menor/maior {cla.min() / cla.max():.3f}")
    confere(esc.max() > esc.min() + 0.03, "lacuna entre pixels T0 mais clara que o centro (substrato verde-oliva)")
    confere(0.82 <= cla.min() / cla.max() <= 0.96, f"fundo T3: menor valor {cla.min() / cla.max() * 100:.1f}% do pico (82% a 96%)")
    for nome, a in caps:
        n2 = nitidez(shader_gb(a, 320, 288, LCD_GRID=0.0), cor_gb(vizinho(a, 320, 288), DEF_GB))
        n3 = nitidez(shader_gb(a, OW, OH, LCD_GRID=0.0), cor_gb(vizinho(a, OW, OH), DEF_GB))
        p = psnr(shader_gb(a), shader_gb(a, fp16=True))
        # 3,33x só é impresso: a spec mede 2x. Em 3,33x o vizinho mais próximo tem bordas duras de
        # larguras desiguais (3 e 4 pixels de saída) e o sharp-bilinear tem transição de ~1 pixel, então
        # o Pokémon Red fica em 94,6% (95,2% mesmo com SOFTNESS 0): não dá para afirmar 97% ali.
        print(f"  {nome}: nitidez 2x {n2:.1f}% | nitidez 3,33x {n3:.1f}% (informativa) | PSNR fp16 533x480 {p:.1f} dB")
        confere(n2 >= 97, f"{nome}: nitidez em 320x288 (LCD 0) >= 97%")
        confere(p > 30, f"{nome}: PSNR fp16 > 30 dB")


def medidas_gbc(caps):
    print("=== gbc-modern-remaster")
    out = shader_gbc(cartela(), LCD_GRID=0.0)
    pior_sat, pior_matiz = 1.0, 0.0
    for n, (nome, rgb) in enumerate(CARTELA):
        y, x = divmod(n, 6)
        o = np.array(rgb, np.float32) / 255
        b = out[int((y * 36 + 18) * OH / 144), int((x * 26 + 13) * OW / 160)]
        so, sb = sat(o[None])[0], sat(b[None])[0]
        dh = abs((matiz(b) - matiz(o) + 180) % 360 - 180) if so > 0.05 else 0.0
        pior_sat, pior_matiz = min(pior_sat, sb - so), max(pior_matiz, dh)
        print(f"    {nome:14} sat {so:.2f}->{sb:.2f} | matiz {dh:4.1f} graus | canal máximo {o.max() * 255:3.0f}->{b.max() * 255:3.0f}")
    confere(pior_matiz <= 2.0, f"cartela: maior desvio de matiz {pior_matiz:.2f} graus (<= 2)")
    confere(pior_sat >= -0.05, f"cartela: menor ganho de saturação {pior_sat:+.3f} (>= -0.05)")
    for nome, a in caps + [("cartela", cartela())]:
        ref = vizinho(a, OW, OH)
        b, ent = shader_gbc(a, entrada=True)
        n2 = nitidez(shader_gbc(a, 320, 288, LCD_GRID=0.0), cor_gbc(vizinho(a, 320, 288), DEF_GBC))
        # estouro: o canal máximo da cor que o shader leu (já amostrada) estava abaixo de 245 e
        # saiu em 255; comparar com o vizinho mais próximo contaria a borda de um branco
        estouro = int(((b.max(-1) >= 254.5 / 255) & (ent.max(-1) < 245 / 255)).sum())
        p = psnr(b, shader_gbc(a, fp16=True))
        Lr, sr = luma(ref), sat(ref)
        print(f"  {nome}: luma {(luma(b).mean() / max(Lr.mean(), 1e-6) - 1) * 100:+.1f}% | sat média {sr.mean():.3f}->{sat(b).mean():.3f}"
              f" | nitidez 2x {n2:.1f}% | estouro {estouro} px | PSNR fp16 {p:.1f} dB")
        confere(n2 >= 97, f"{nome}: nitidez em 320x288 (LCD 0) >= 97%")
        confere(estouro == 0, f"{nome}: nenhum pixel abaixo de 245 chega a 255")
        confere(p > 30, f"{nome}: PSNR fp16 533x480 > 30 dB")


# Cartela de cores de referência (nome, RGB 0-255), 6 colunas x 4 linhas de 26x36 pixels do GBC
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
    tex = np.zeros((144, 160, 3), np.float32)
    for n, (_, rgb) in enumerate(CARTELA):
        y, x = divmod(n, 6)
        tex[y * 36:(y + 1) * 36, x * 26:(x + 1) * 26] = np.array(rgb, np.float32) / 255
    return tex


def quadro(a, titulo):
    img = Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8))
    tela = Image.new("RGB", (img.width, img.height + 22), (24, 24, 24))
    tela.paste(img, (0, 22))
    ImageDraw.Draw(tela).text((6, 5), titulo, fill=(240, 240, 240))
    return tela


def prancha(quadros, caminho):
    w, h = quadros[0].size
    lado = Image.new("RGB", (w * 2 + 4, h * 2 + 4), (24, 24, 24))
    for n, q in enumerate(quadros):
        lado.paste(q, ((n % 2) * (w + 4), (n // 2) * (h + 4)))
    lado.save(caminho)
    # recorte do centro ampliado 2x (vizinho), para ver a grade e as bordas
    rec = Image.new("RGB", (w * 2 + 4, h * 2 + 4), (24, 24, 24))
    for n, q in enumerate(quadros):
        parte = q.crop((w // 4, 22 + (h - 22) // 4, w // 4 + w // 2, 22 + (h - 22) // 4 + (h - 22) // 2))
        parte = parte.resize((parte.width * 2, parte.height * 2), Image.NEAREST)
        caixa = Image.new("RGB", (w, h), (24, 24, 24))
        caixa.paste(q.crop((0, 0, w, 22)), (0, 0))
        caixa.paste(parte.crop((0, 0, w, h - 22)), (0, 22))
        rec.paste(caixa, ((n % 2) * (w + 4), (n // 2) * (h + 4)))
    rec.save(caminho.replace("_comparacao", "_recorte-2x"))


def exemplos(caps_gb, caps_gbc, saida):
    os.makedirs(saida, exist_ok=True)
    bil = dict(SOFTNESS=1.0, LCD_GRID=0.0)
    for nome, a in caps_gb:
        antiga = DMG_ANTIGA[np.clip(np.round(luma(a) * 3), 0, 3).astype(int)]
        quadros = [quadro(shader_gbc(a, SOFTNESS=1.0, LCD_GRID=0.0, VIBRANCE=0, SATURATION=1, ROLLOFF=0, CONTRAST=0, HIGHLIGHT=0),
                          "1. sem shader (bilinear, 4 cinzas do core)"),
                   quadro(vizinho(antiga, OW, OH), "2. paleta DMG classica (Tom 2 some no fundo)"),
                   quadro(shader_gb(a), "3. NOVO gb-modern-dmg (padrao)"),
                   quadro(shader_gb(a, LCD_GRID=0.0), "4. gb-modern-dmg sem grade (DOT MATRIX GRID 0)")]
        prancha(quadros, f"{saida}/gb_{nome}_comparacao.png")
    for nome, a in caps_gbc + [("cartela-de-cores", cartela())]:
        quadros = [quadro(shader_gbc(a, VIBRANCE=0, SATURATION=1, ROLLOFF=0, CONTRAST=0, HIGHLIGHT=0, **bil),
                          "1. sem shader (bilinear, RGB555 cru)"),
                   quadro(shader_gbc(a), "2. NOVO gbc-modern-remaster (padrao)"),
                   quadro(shader_gbc(a, LCD_GRID=0.0), "3. gbc-modern-remaster sem grade (LCD GRID 0)"),
                   quadro(shader_gbc(a, ROLLOFF=0.65), "4. variante contida (HIGHLIGHT ROLLOFF 0.65)")]
        prancha(quadros, f"{saida}/gbc_{nome}_comparacao.png")
    print(f"pranchas em {saida}")


def main():
    caps_dir = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/.cache/shader-gb-gbc-test")
    saida = sys.argv[2] if len(sys.argv) > 2 else "var/exemplos-gb-gbc"
    caps = {}
    for nome in GB + GBC:
        arq = os.path.join(caps_dir, nome.rsplit("-f", 1)[0], nome + ".png")
        if os.path.isfile(arq):
            caps[nome] = carrega(arq)
        else:
            print(f"AVISO: captura ausente: {arq}")
    caps_gb = [(n, caps[n]) for n in GB if n in caps]
    caps_gbc = [(n, caps[n]) for n in GBC if n in caps]
    medidas_gb(caps_gb)
    medidas_gbc(caps_gbc)
    exemplos(caps_gb, caps_gbc, saida)
    if not caps_gb or not caps_gbc:
        FALHAS.append("capturas ausentes")
    print(f"=== {len(FALHAS)} falha(s)" if FALHAS else "=== todas as medidas cumprem a spec")
    sys.exit(1 if FALHAS else 0)


if __name__ == "__main__":
    main()
