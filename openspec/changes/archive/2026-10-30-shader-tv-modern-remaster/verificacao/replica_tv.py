"""Réplica numérica do tv-modern-remaster.glsl e medição dos cenários da spec.

Uso:
    uv run --with pillow --with numpy python -I openspec/changes/shader-tv-modern-remaster/verificacao/replica_tv.py [CAPTURAS_DIR [SAIDA_DIR]]
"""

import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W709 = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

DEF_TV = {
    "DITHER_BLEND": 1.00,
    "TV_SCANLINES": 0.10,
    "PIXEL_SOFTNESS": 0.10,
    "VIBRANCE": 0.40,
    "SATURATION": 1.08,
    "CONTRAST": 0.25,
    "ROLLOFF": 0.35,
    "BRIGHTNESS": 0.00,
    "CEIL": 0.035,
}

OW, OH = 640, 480  # Resolução nativa da tela do R36S


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def bilinear_sample(tex, u, v):
    """Amostragem bilinear com coordenadas normalizadas u, v (H, W, 3)."""
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


def shader_tv(tex, OW=OW, OH=OH, fp16=False, **kw):
    """Execução numérica do tv-modern-remaster espelhando o GLSL."""
    P = dict(DEF_TV)
    P.update(kw)

    q = (lambda x: x.astype(np.float16).astype(np.float32)) if fp16 else (lambda x: x)

    h, w, _ = tex.shape
    ys, xs = np.mgrid[0:OH, 0:OW].astype(np.float32)

    # Varying TEX0 (mediump)
    u = q((xs + 0.5) / OW)
    v = q((ys + 0.5) / OH)

    # 1. Sharp-bilinear: cálculo das coordenadas de interpolação
    px = w / OW  # tamanho de 1 pixel de saída em texels do jogo
    width = max(px * (1.0 - P["PIXEL_SOFTNESS"]) + P["PIXEL_SOFTNESS"], 1e-4)

    pxx = q(u * w - 0.5)
    pyy = q(v * h - 0.5)
    ix = np.floor(pxx)
    iy = np.floor(pyy)
    fx = np.clip((q(pxx - ix) - 0.5) / width + 0.5, 0.0, 1.0)
    fy = np.clip((q(pyy - iy) - 0.5) / width + 0.5, 0.0, 1.0)

    uv_x = (ix + 0.5 + fx) / w
    uv_y = (iy + 0.5 + fy) / h

    # 2. Dither blend seletivo horizontal: 3 amostras na mesma scanline
    dx = 1.0 / w
    C = bilinear_sample(tex, uv_x, uv_y)
    L = bilinear_sample(tex, uv_x - dx, uv_y)
    R = bilinear_sample(tex, uv_x + dx, uv_y)

    # Métrica de dither: diferença entre extremos e alternância do centro
    diff_LR = np.abs(L - R).mean(axis=-1)
    diff_C = np.abs(C - 0.5 * (L + R)).mean(axis=-1)

    w_dither = np.clip((diff_C - 0.5 * diff_LR) * 10.0, 0.0, 1.0) * P["DITHER_BLEND"]
    c = C * (1.0 - w_dither[..., None]) + (0.5 * C + 0.25 * (L + R)) * w_dither[..., None]

    # 3. Pipeline de cor viva remaster ultra-otimizado (zero divisões, zero estouro)
    luma = c @ W709
    sat = c.max(axis=-1) - c.min(axis=-1)
    sat_boost = P["VIBRANCE"] * (1.0 - sat) + (P["SATURATION"] - 1.0)
    c = c + (c - luma[..., None]) * (c * (1.0 - c) * 4.0) * sat_boost[..., None]
    c = c + c * (1.0 - c) * ((c - 0.35) * P["CONTRAST"] + P["BRIGHTNESS"])

    # 4. Scanline leve na grade da tela (1 mod, uniforme, sem moire)
    scan = (ys % 2).astype(np.float32)
    beam = 1.0 - P["TV_SCANLINES"] * scan

    c = c * beam[..., None]
    return np.clip(c, 0.0, 1.0)


def cor_pura(c_in, P=DEF_TV):
    """Aplica o pipeline de cor pura (sem escala nem scanline) para medição de nitidez."""
    c = np.array(c_in, copy=True)
    luma = c @ W709
    sat = c.max(axis=-1) - c.min(axis=-1)
    sat_boost = P["VIBRANCE"] * (1.0 - sat) + (P["SATURATION"] - 1.0)
    c = c + (c - luma[..., None]) * (c * (1.0 - c) * 4.0) * sat_boost[..., None]
    c = c + c * (1.0 - c) * ((c - 0.35) * P["CONTRAST"] + P["BRIGHTNESS"])
    return np.clip(c, 0.0, 1.0)


def calcula_metricas(img_np):
    """Mede nitidez contra vizinho mais próximo, dither e estabilidade."""
    h, w, _ = img_np.shape
    # 1. Medição de nitidez do filtro sharp-bilinear nos contornos (DITHER_BLEND=0.0)
    out_2x_clean = shader_tv(img_np, OW=w * 2, OH=h * 2, DITHER_BLEND=0.0, TV_SCANLINES=0.0)
    nn_2x = np.repeat(np.repeat(img_np, 2, axis=0), 2, axis=1)
    nn_color = cor_pura(nn_2x)

    # Gradiente em verde (G)
    grad_clean = (np.abs(np.diff(out_2x_clean[..., 1], axis=0)).mean() +
                  np.abs(np.diff(out_2x_clean[..., 1], axis=1)).mean())
    grad_nn = (np.abs(np.diff(nn_color[..., 1], axis=0)).mean() +
               np.abs(np.diff(nn_color[..., 1], axis=1)).mean())

    nitidez_filtro = (grad_clean / grad_nn) * 100.0 if grad_nn > 0 else 100.0

    # 2. Avaliação de fusão de dither num padrão xadrez puro (checkerboard)
    chk_native = np.zeros((32, 32, 3), dtype=np.float32)
    chk_native[::2, 1::2, :] = 1.0
    chk_native[1::2, ::2, :] = 1.0
    chk_blend = shader_tv(chk_native, OW=64, OH=64, TV_SCANLINES=0.0, DITHER_BLEND=1.0)
    # No centro da área xadrez, a variação entre vizinhos horizontais deve tender a zero
    var_dither_orig = np.abs(np.diff(chk_native[..., 0], axis=1)).mean()
    var_dither_fused = np.abs(np.diff(chk_blend[16:48, 16:48, 0], axis=1)).mean()
    fusao_dither = (1.0 - (var_dither_fused / var_dither_orig)) * 100.0

    # Saída completa em 640x480
    out_full_f32 = shader_tv(img_np, OW=OW, OH=OH, fp16=False)
    out_full_fp16 = shader_tv(img_np, OW=OW, OH=OH, fp16=True)

    # Estouro de brancos (canal máximo original < 245 que chega a 255)
    p_orig = (img_np * 255.0).max(axis=-1)
    p_out = (out_full_f32 * 255.0).max(axis=-1)
    # Reamostrado para resolução de saída (OW, OH)
    nn_pil = Image.fromarray((img_np * 255).astype(np.uint8)).resize((OW, OH), Image.NEAREST)
    nn_full = np.asarray(nn_pil).astype(np.float32) / 255.0
    orig_sub245 = (nn_full * 255.0).max(axis=-1) < 245.0
    estouros = int(np.sum(orig_sub245 & (p_out >= 254.5)))

    # PSNR fp16
    mse = np.mean((out_full_f32 - out_full_fp16) ** 2)
    psnr = 10.0 * np.log10(1.0 / max(mse, 1e-10))

    return nitidez_filtro, fusao_dither, estouros, psnr, out_full_f32


def monta_prancha(img_np, out_full, titulo):
    """Monta imagem comparativa (original vizinho mais próximo vs shader)."""
    h, w, _ = img_np.shape
    # Original ampliado para 640x480 via vizinho mais próximo
    nn_img = Image.fromarray((img_np * 255).astype(np.uint8)).resize((OW, OH), Image.NEAREST)
    shader_img = Image.fromarray((out_full * 255).astype(np.uint8))

    # Prancha lado a lado: 1280 x 520 (com cabeçalho)
    canvas = Image.new("RGB", (OW * 2 + 30, OH + 60), (24, 24, 28))
    draw = ImageDraw.Draw(canvas)

    canvas.paste(nn_img, (10, 45))
    canvas.paste(shader_img, (OW + 20, 45))

    draw.text((15, 15), f"ORIGINAL (Sem Shader / Pixel Duro) - {titulo}", fill=(200, 200, 200))
    draw.text((OW + 25, 15), f"TV MODERN REMASTER (640x480) - {titulo}", fill=(100, 230, 160))
    return canvas


def main():
    capturas_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.path.expanduser("~/.cache/shader-tv-test"))
    saida_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("var/exemplos-tv")
    saida_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("VERIFICAÇÃO DO SHADER TV MODERN REMASTER (R36S 640x480)")
    print(f"Diretório de capturas: {capturas_dir}")
    print(f"Diretório de saída:    {saida_dir}")
    print("=" * 70)

    # Coletar arquivos de teste
    test_files = list(capturas_dir.glob("*/*.png"))
    if not test_files:
        print(f"Nenhuma captura encontrada em {capturas_dir}!")
        return 1

    sucesso_total = True

    for f in sorted(test_files):
        nome = f.stem
        img = Image.open(f).convert("RGB")
        img_np = np.asarray(img).astype(np.float32) / 255.0

        nitidez, fusao, estouros, psnr, out_full = calcula_metricas(img_np)

        status_nitidez = "PASS" if nitidez >= 95.0 else "FAIL"
        status_fusao = "PASS" if fusao >= 95.0 else "FAIL"
        status_estouro = "PASS" if estouros == 0 else "FAIL"
        status_psnr = "PASS" if psnr >= 35.0 else "FAIL"

        if not (nitidez >= 95.0 and fusao >= 95.0 and estouros == 0 and psnr >= 35.0):
            sucesso_total = False

        print(f"\n[{nome}] ({img_np.shape[1]}x{img_np.shape[0]}) -> 640x480:")
        print(f"  Nitidez de Borda:       {nitidez:.2f}% (>= 95.0%) -> {status_nitidez}")
        print(f"  Fusão de Dither Xadrez: {fusao:.2f}% (>= 95.0%) -> {status_fusao}")
        print(f"  Estouro de Brancos:     {estouros} pixels (esperado 0) -> {status_estouro}")
        print(f"  Estabilidade fp16 PSNR: {psnr:.2f} dB (>= 35.0 dB) -> {status_psnr}")

        # Salvar prancha comparativa
        prancha = monta_prancha(img_np, out_full, nome)
        saida_png = saida_dir / f"comparativo-{nome}.png"
        prancha.save(saida_png)

        # Salvar também o frame do shader isolado
        shader_png = saida_dir / f"shader-{nome}.png"
        Image.fromarray((out_full * 255).astype(np.uint8)).save(shader_png)

    print("\n" + "=" * 70)
    if sucesso_total:
        print("TODOS OS CENÁRIOS NUMÉRICOS CUMPRIRAM A SPEC COM SUCESSO!")
    else:
        print("AVISO: Alguns critérios não atingiram os limites estritos.")
    print(f"Imagens salvas em: {saida_dir}")
    print("=" * 70)
    return 0 if sucesso_total else 1


if __name__ == "__main__":
    sys.exit(main())
