#!/usr/bin/env python3
"""Gera features/30-telas-icone-controle/boot/bootlogo.bmp a partir do original da base.

Substitui a inscrição "OPEN SOURCE" por "GA36-MB V1.2-20260416" mantendo formato BMP
24bpp de 640x480 e tamanho exato de 921.654 bytes.
"""

import hashlib
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from r36img import config, mtools

DEST = Path(__file__).resolve().parent / "boot" / "bootlogo.bmp"
FONT_PATH = Path("/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf")


def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    cfg = config.load(ROOT)
    p_boot = cfg.part("boot")
    base = cfg.base_path

    tmp_orig = ROOT / "work" / "bootlogo_base.bmp"
    tmp_orig.parent.mkdir(parents=True, exist_ok=True)

    spec = mtools.spec(base, p_boot.offset)
    mtools._m(["mcopy", "-n", "-o", "-i", spec, "::/bootlogo.bmp", str(tmp_orig)])

    im = Image.open(tmp_orig)
    if im.size != (640, 480) or im.mode != "RGB":
        raise ValueError(f"Dimensões ou modo inesperado: {im.size}, {im.mode}")

    draw = ImageDraw.Draw(im)
    # Limpa a caixa contendo 'OPEN SOURCE' e suas sombras/reflexos
    draw.rectangle([180, 418, 460, 448], fill=(255, 255, 255))

    font = ImageFont.truetype(str(FONT_PATH), 21)
    text = "GA36-MB V1.2-20260416"
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (640 - tw) // 2 - bbox[0]
    ty = 432 - th // 2 - bbox[1]

    draw.text((tx, ty), text, font=font, fill=(0, 0, 0))

    im.save(DEST, format="BMP")

    size = DEST.stat().st_size
    if size != 921654:
        raise ValueError(f"Tamanho gerado inválido: {size} bytes (esperado 921654)")

    h = hashlib.sha256(DEST.read_bytes()).hexdigest()
    print(f"bootlogo.bmp gerado com sucesso em {DEST}")
    print(f"tamanho: {size} bytes")
    print(f"sha256:  {h}")


if __name__ == "__main__":
    main()
