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


def render_mode(tex, mode="sem_scanline", scanline_strength=0.10):
    """
    mode:
      - 'sem_scanline': Scanline desligada (imagem limpa, 100% uniforme, sem moire)
      - 'grid_tela': Scanlines alinhadas a tela de 480p (240 linhas de feixe perfeitas, sem batimento)
      - 'box_filter': Scanlines de 224 linhas integradas por pixel (sem corte abrupto)
    """
    h, w, _ = tex.shape
    ys, xs = np.mgrid[0:OH, 0:OW].astype(np.float32)
    u = (xs + 0.5) / OW
    v = (ys + 0.5) / OH

    # Sharp-bilinear
    px = w / OW
    width = max(px * 0.90 + 0.10, 1e-4)
    pxx = u * w - 0.5
    pyy = v * h - 0.5
    ix = np.floor(pxx)
    iy = np.floor(pyy)
    fx = np.clip((pxx - ix - 0.5) / width + 0.5, 0.0, 1.0)
    fy = np.clip((pyy - iy - 0.5) / width + 0.5, 0.0, 1.0)

    uv_x = (ix + 0.5 + fx) / w
    uv_y = (iy + 0.5 + fy) / h

    # Dither blend seletivo
    dx = 1.0 / w
    C = bilinear_sample(tex, uv_x, uv_y)
    L = bilinear_sample(tex, uv_x - dx, uv_y)
    R = bilinear_sample(tex, uv_x + dx, uv_y)

    diff_LR = np.abs(L - R).mean(axis=-1)
    diff_C = np.abs(C - 0.5 * (L + R)).mean(axis=-1)
    w_dither = np.clip((diff_C - diff_LR) / (diff_C + 0.001), 0.0, 1.0) * 0.85
    c = C * (1.0 - w_dither[..., None]) + (0.5 * C + 0.25 * (L + R)) * w_dither[..., None]

    # Cor viva remaster
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

    # Beam / Scanline
    if mode == "sem_scanline":
        beam = np.ones((OH, OW), dtype=np.float32)
    elif mode == "grid_tela":
        # Scanlines alinhadas aos 480 pixels da tela: linhas alternadas perfeitas
        beam = 1.0 - scanline_strength * (ys % 2)
    elif mode == "box_filter":
        py = h / OH
        pos = (v * h) - np.floor(v * h)
        gap = min(py, 0.35)
        lo = pos - 0.5 * py
        hi = pos + 0.5 * py
        cover = (np.clip(np.minimum(hi, 1.0) - np.maximum(lo, 1.0 - gap), 0.0, gap) +
                 np.clip(np.minimum(hi, 0.0) - np.maximum(lo, -gap), 0.0, gap))
        cover = np.minimum(cover / py, 1.0)
        beam = 1.0 - scanline_strength * cover
    else:
        beam = np.ones((OH, OW), dtype=np.float32)

    c = c * beam[..., None]
    return np.clip(c, 0.0, 1.0)


def main():
    saida = Path("var/exemplos-tv")
    saida.mkdir(parents=True, exist_ok=True)

    # Vamos gerar comparativos do Sonic 1 (f600) e Streets of Rage 2 (f600) nos 3 modos
    shots = [
        ("sonic1-f600", Path(os.path.expanduser("~/.cache/shader-tv-test/sonic1/sonic1-f600.png"))),
        ("sor2-f600", Path(os.path.expanduser("~/.cache/shader-tv-test/sor2/sor2-f600.png"))),
    ]

    for nome, caminho in shots:
        if not caminho.exists():
            continue
        im = Image.open(caminho).convert("RGB")
        im_np = np.asarray(im).astype(np.float32) / 255.0

        out_sem = render_mode(im_np, "sem_scanline")
        out_grid = render_mode(im_np, "grid_tela", scanline_strength=0.10)
        out_box = render_mode(im_np, "box_filter", scanline_strength=0.12)

        # Salvar as 3 opções isoladas
        Image.fromarray((out_sem * 255).astype(np.uint8)).save(saida / f"{nome}-modo1-sem-scanline.png")
        Image.fromarray((out_grid * 255).astype(np.uint8)).save(saida / f"{nome}-modo2-grid-tela.png")
        Image.fromarray((out_box * 255).astype(np.uint8)).save(saida / f"{nome}-modo3-box-filter.png")

        # Montar prancha comparativa das 3 opções
        # Largura: 3 x 640 + margens = 1960
        comp = Image.new("RGB", (OW * 3 + 40, OH + 60), (20, 20, 24))
        draw = ImageDraw.Draw(comp)
        comp.paste(Image.fromarray((out_sem * 255).astype(np.uint8)), (10, 45))
        comp.paste(Image.fromarray((out_grid * 255).astype(np.uint8)), (OW + 20, 45))
        comp.paste(Image.fromarray((out_box * 255).astype(np.uint8)), (OW * 2 + 30, 45))

        draw.text((15, 15), "1. PURO REMASTER (Sem Scanline / Nitidez Maxima)", fill=(100, 240, 160))
        draw.text((OW + 25, 15), "2. SCANLINES NA TELA 480p (Sem Batimento)", fill=(120, 200, 255))
        draw.text((OW * 2 + 35, 15), "3. BOX-FILTER CRT (Integracao Suave)", fill=(255, 200, 100))

        comp.save(saida / f"comparativo-scanlines-{nome}.png")
        print(f"Gerado: var/exemplos-tv/comparativo-scanlines-{nome}.png")


if __name__ == "__main__":
    main()
