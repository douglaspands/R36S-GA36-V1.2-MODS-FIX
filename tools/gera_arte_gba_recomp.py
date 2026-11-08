#!/usr/bin/env python3
"""Deriva a arte do sistema gba-recomp (tema Epic Cody ML) da arte do GBA, com o selo RECOMP.

A arte do GBA vem do tarball do tema upstream já em work/cache/external (o repositório só
guarda o que o build acrescenta). Gera, na pasta do tema da feature 50-temas-extras:
  gba-recomp/logo.png, gba-recomp/system.png   500x161, texto "GBA RECOMP"
  gba-recomp/selo.png                           selo amarelo "RECOMP" (ao lado da 1ª linha do título)
  gba-recomp/poster.png                         640x480, pôster do GBA
  _art/posters/gba-recomp.png                   o mesmo pôster (o tema acha por ${system.theme})
  _art/controllers/gba-recomp.png               530x400, controle do GBA

Uso: uv run --with pillow python -I tools/gera_arte_gba_recomp.py [tarball]
"""

import io
import sys
import tarfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
TEMA = ROOT / "features/50-temas-extras/storage/.config/emulationstation/themes/Epic Cody ML"
TARBALL = ROOT / "work/cache/external/4a0d1e11850e0a1f0ae54ba3f4c067aefa44751e6fa7996a799493308dbe5d55.tar.gz"
FONTES = (
    "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf",
    "/usr/share/fonts/open-sans/OpenSans-Bold.ttf",
)
ROXO = (92, 70, 168)       # roxo do GBA
SELO = (255, 196, 0)       # amarelo do selo
SELO_TEXTO = (40, 24, 80)


def fonte(tam):
    for caminho in FONTES:
        if Path(caminho).is_file():
            return ImageFont.truetype(caminho, tam)
    return ImageFont.load_default(tam)


def le_do_tarball(tarball, sufixo):
    with tarfile.open(tarball) as t:
        for m in t.getmembers():
            if m.name.endswith(sufixo):
                return Image.open(io.BytesIO(t.extractfile(m).read()))
    raise SystemExit(f"{sufixo} não está em {tarball}")


def selo(img, canto, altura):
    """Cola o selo RECOMP (retângulo arredondado amarelo) com o canto superior esquerdo em `canto`."""
    img = img.convert("RGBA")
    f = fonte(int(altura * 0.62))
    tmp = ImageDraw.Draw(img)
    largura_texto = tmp.textlength("RECOMP", font=f)
    larg = int(largura_texto + altura * 0.8)
    camada = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    x, y = canto
    if x is None:  # centraliza na largura da imagem
        x = (img.size[0] - larg) // 2
    d.rounded_rectangle((x, y, x + larg, y + altura), radius=altura // 4, fill=SELO + (255,),
                        outline=SELO_TEXTO + (255,), width=max(2, altura // 14))
    d.text((x + larg / 2, y + altura / 2), "RECOMP", font=f, fill=SELO_TEXTO + (255,), anchor="mm")
    return Image.alpha_composite(img, camada)


def logo():
    img = Image.new("RGBA", (500, 161), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = fonte(92)
    d.text((250, 62), "GBA", font=f, fill=ROXO + (255,), anchor="mm")
    return selo(img, (None, 112), 44)


def selo_pequeno():
    """Selo RECOMP sozinho (fundo transparente), colocado ao lado da primeira linha do título."""
    altura = 44
    f = fonte(int(altura * 0.62))
    largura = int(ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength("RECOMP", font=f) + altura * 0.8)
    return selo(Image.new("RGBA", (largura + 2, altura + 2), (0, 0, 0, 0)), (1, 1), altura)


def main():
    tarball = Path(sys.argv[1]) if len(sys.argv) > 1 else TARBALL
    # Pôster e controle idênticos aos do GBA, sem selo: o selo fica ao lado do título (selo.png)
    poster = le_do_tarball(tarball, "_art/posters/gba.jpg")
    controle = le_do_tarball(tarball, "_art/controllers/gba.png")
    saidas = {
        TEMA / "gba-recomp/selo.png": selo_pequeno(),
        TEMA / "gba-recomp/logo.png": logo(),
        TEMA / "gba-recomp/system.png": logo(),
        TEMA / "gba-recomp/poster.png": poster.convert("RGB"),
        TEMA / "_art/posters/gba-recomp.png": poster.convert("RGB"),
        TEMA / "_art/controllers/gba-recomp.png": controle.convert("RGBA"),
    }
    for caminho, img in saidas.items():
        caminho.parent.mkdir(parents=True, exist_ok=True)
        img.save(caminho, optimize=True)
        print(f"{caminho.relative_to(ROOT)}  {img.size[0]}x{img.size[1]}  {caminho.stat().st_size} bytes")


if __name__ == "__main__":
    main()
