import os
from pathlib import Path
import numpy as np
from PIL import Image

W709 = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
OW, OH = 640, 480


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


def shader_fast(tex, dither_blend=1.0, scanline_strength=0.10, scanline_mode="grid_tela"):
    h, w, _ = tex.shape
    ys, xs = np.mgrid[0:OH, 0:OW].astype(np.float32)
    u = (xs + 0.5) / OW
    v = (ys + 0.5) / OH

    # 1. Sharp-bilinear ultra-rápido
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

    # 2. Dither blend seletivo horizontal (3 taps) sem divisão
    dx = 1.0 / w
    C = bilinear_sample(tex, uv_x, uv_y)
    L = bilinear_sample(tex, uv_x - dx, uv_y)
    R = bilinear_sample(tex, uv_x + dx, uv_y)

    diff_LR = np.abs(L - R).mean(axis=-1)
    diff_C = np.abs(C - 0.5 * (L + R)).mean(axis=-1)

    # Rampa linear rápida sem divisão: quando diff_C > 0.5 * diff_LR, funde
    w_dither = np.clip((diff_C - 0.5 * diff_LR) * 10.0, 0.0, 1.0) * dither_blend
    c = C * (1.0 - w_dither[..., None]) + (0.5 * C + 0.25 * (L + R)) * w_dither[..., None]

    # 3. Cor viva remaster ultra-otimizada (sem divisões nem smoothstep)
    luma = c @ W709
    # Vibrance seletiva simples: mais ganho em cores de saturação média
    mx = c.max(axis=-1)
    mn = c.min(axis=-1)
    sat = mx - mn
    c = c + (c - luma[..., None]) * (0.25 + 0.35 * (1.0 - sat))[..., None]

    # Contraste suave na luma sem divisão
    c = c + c * (1.0 - c) * (c - 0.35) * 0.40

    # 4. Scanline ultra-leve
    if scanline_mode == "grid_tela":
        # 1 a cada 2 linhas de tela (perfeitamente uniforme, zero instrução pesada)
        beam = 1.0 - scanline_strength * (ys % 2)
    elif scanline_mode == "parabolico":
        # Parábola por linha do jogo sem exp/trig
        pos_y = (v * h) - np.floor(v * h) - 0.5
        beam = 1.0 - scanline_strength * (pos_y * pos_y * 4.0)
    else:
        beam = np.ones_like(ys)

    c = c * beam[..., None]
    return np.clip(c, 0.0, 1.0)


def main():
    saida = Path("var/exemplos-tv")
    saida.mkdir(parents=True, exist_ok=True)

    shots = [
        ("sonic1-f600", Path(os.path.expanduser("~/.cache/shader-tv-test/sonic1/sonic1-f600.png"))),
        ("sor2-f600", Path(os.path.expanduser("~/.cache/shader-tv-test/sor2/sor2-f600.png"))),
    ]

    for nome, caminho in shots:
        if not caminho.exists():
            continue
        im = Image.open(caminho).convert("RGB")
        im_np = np.asarray(im).astype(np.float32) / 255.0

        out_grid = shader_fast(im_np, dither_blend=1.0, scanline_strength=0.10, scanline_mode="grid_tela")
        out_none = shader_fast(im_np, dither_blend=1.0, scanline_strength=0.00, scanline_mode="sem_scanline")

        Image.fromarray((out_grid * 255).astype(np.uint8)).save(saida / f"{nome}-otimizado-grid.png")
        Image.fromarray((out_none * 255).astype(np.uint8)).save(saida / f"{nome}-otimizado-sem-scanline.png")
        print(f"Salvo: {saida / f'{nome}-otimizado-grid.png'}")


if __name__ == "__main__":
    main()
