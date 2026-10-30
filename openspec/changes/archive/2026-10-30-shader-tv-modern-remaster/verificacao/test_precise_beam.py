import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

W709 = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
OW, OH = 640, 480


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def bilinear_sample(tex, u, v):
    h, w, _ = tex.shape
    x = u * w - 0.5
    y = v * h - 0.5
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx = (x - x0)[..., None]
    fy = (y - y0)[..., None]

    def g(yy, xx):
        return tex[np.clip(yy, 0, h - 1), np.clip(xx, 0, w - 1)]

    c00 = g(y0, x0)
    c10 = g(y0, x0 + 1)
    c01 = g(y0 + 1, x0)
    c11 = g(y0 + 1, x0 + 1)
    return (c00 * (1.0 - fx) + c10 * fx) * (1.0 - fy) + (c01 * (1.0 - fx) + c11 * fx) * fy


def shader_tv_preciso(tex, OW=OW, OH=OH, dither_blend=1.0, tv_scanlines=0.14):
    """
    Shader com modulação milimetricamente calibrada em cada uma das scanlines originais
    e fusão seletiva completa de dithering para transparência analógica perfeita.
    """
    h, w, _ = tex.shape
    ys, xs = np.mgrid[0:OH, 0:OW].astype(np.float32)
    u = (xs + 0.5) / OW
    v = (ys + 0.5) / OH

    # 1. Sharp-bilinear
    px = w / OW
    py = h / OH
    width = max(px * 0.90 + 0.10, 1e-4)
    pxx = u * w - 0.5
    pyy = v * h - 0.5
    ix = np.floor(pxx)
    iy = np.floor(pyy)
    fx = np.clip((pxx - ix - 0.5) / width + 0.5, 0.0, 1.0)
    fy = np.clip((pyy - iy - 0.5) / width + 0.5, 0.0, 1.0)

    uv_x = (ix + 0.5 + fx) / w
    uv_y = (iy + 0.5 + fy) / h

    # 2. Dither blend seletivo horizontal (3 taps)
    dx = 1.0 / w
    C = bilinear_sample(tex, uv_x, uv_y)
    L = bilinear_sample(tex, uv_x - dx, uv_y)
    R = bilinear_sample(tex, uv_x + dx, uv_y)

    diff_LR = np.abs(L - R).mean(axis=-1)
    diff_C = np.abs(C - 0.5 * (L + R)).mean(axis=-1)

    # Permite transições graduais com 0.6 * diff_LR garantindo que bordas sólidas zerem (diff_C <= 0.5*diff_LR)
    w_dither = np.clip((diff_C - 0.5 * diff_LR) / (diff_C + 0.001), 0.0, 1.0) * dither_blend
    c = C * (1.0 - w_dither[..., None]) + (0.5 * C + 0.25 * (L + R)) * w_dither[..., None]

    # 3. Pipeline de cor viva remaster
    luma = c @ W709
    mx = c.max(axis=-1)
    mn = c.min(axis=-1)
    sat = (mx - mn) / np.maximum(mx, 0.001)
    hs = smooth(0.5, 1.0, luma)
    gain = (1.0 + 0.40 * np.minimum(1.0 - sat, 4.0 * sat * (1.0 - sat))) * 1.08
    anchor = (luma + (mx - luma) * hs)[..., None]
    c = np.maximum(anchor + (c - anchor) * (1.0 + (gain - 1.0) * (1.0 - 0.35 * hs))[..., None], 0.0)

    L2 = luma + 0.25 * 2.0 * luma * (1.0 - luma) * (luma - 0.35)
    k = L2 / np.maximum(luma, 0.001)
    k = np.maximum(k, k + (1.0 - k) * sat * sat)
    ceiling = np.minimum(1.0, mx + 0.035)
    k = np.minimum(k, np.maximum(ceiling / np.maximum(c.max(axis=-1), 0.001), 1.0))
    c = c * k[..., None]
    L2 = c @ W709

    top = c.max(axis=-1)
    t = np.where(top > ceiling, np.clip((ceiling - L2) / np.maximum(top - L2, 1e-4), 0.0, 1.0), 1.0)
    c = L2[..., None] + (c - L2[..., None]) * t[..., None]

    # 4. Modulação de feixe CRT milimetricamente calibrada em cada linha
    # y_game é a coordenada exata dentro da linha (0.0 no topo, 0.5 no centro, 1.0 no fim)
    pos_y = (v * h) - np.floor(v * h)
    dist_fronteira = np.minimum(pos_y, 1.0 - pos_y)  # 0.0 na fronteira entre linhas, 0.5 no centro
    # Largura adaptativa proporcional ao tamanho do pixel de tela em texels do jogo
    sigma = py * 1.15
    fator_notch = np.exp(- (dist_fronteira * dist_fronteira) / (2.0 * sigma * sigma))
    beam = 1.0 - tv_scanlines * fator_notch

    c = c * beam[..., None]
    return np.clip(c, 0.0, 1.0)


def main():
    saida = Path("var/exemplos-tv")
    saida.mkdir(parents=True, exist_ok=True)

    shots = [
        ("sonic1-f600", Path(os.path.expanduser("~/.cache/shader-tv-test/sonic1/sonic1-f600.png"))),
        ("sonic1-f900", Path(os.path.expanduser("~/.cache/shader-tv-test/sonic1/sonic1-f900.png"))),
        ("sor2-f600", Path(os.path.expanduser("~/.cache/shader-tv-test/sor2/sor2-f600.png"))),
        ("smw-f600", Path(os.path.expanduser("~/.cache/shader-tv-test/smw/smw-f600.png"))),
    ]

    for nome, caminho in shots:
        if not caminho.exists():
            continue
        im = Image.open(caminho).convert("RGB")
        im_np = np.asarray(im).astype(np.float32) / 255.0

        out_preciso = shader_tv_preciso(im_np, dither_blend=1.0, tv_scanlines=0.14)

        # Salvar o frame milimetricamente calibrado
        Image.fromarray((out_preciso * 255).astype(np.uint8)).save(saida / f"{nome}-calibrado.png")

        # Gerar comparativo direto: Original Pixel Duro vs Shader Calibrado
        nn_img = im.resize((OW, OH), Image.NEAREST)
        comp = Image.new("RGB", (OW * 2 + 30, OH + 60), (20, 20, 24))
        draw = ImageDraw.Draw(comp)
        comp.paste(nn_img, (10, 45))
        comp.paste(Image.fromarray((out_preciso * 255).astype(np.uint8)), (OW + 20, 45))

        draw.text((15, 15), f"ORIGINAL (Sem Shader / Pixel Duro) - {nome}", fill=(200, 200, 200))
        draw.text((OW + 25, 15), f"TV MODERN REMASTER (Scanlines Precisas + Transparência) - {nome}", fill=(100, 240, 160))

        comp.save(saida / f"comparativo-calibrado-{nome}.png")
        print(f"Salvo: var/exemplos-tv/comparativo-calibrado-{nome}.png")


if __name__ == "__main__":
    main()
