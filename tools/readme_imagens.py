import shutil
from pathlib import Path

dst = Path("docs/img")
dst.mkdir(parents=True, exist_ok=True)
mapa = {
    "var/prints-tema-epic-cody/auto-allgames.png": "tema-todos-os-jogos.png",
    "var/prints-tema-epic-cody/gba.png": "tema-gba.png",
    "var/prints-tema-epic-cody/snes.png": "tema-snes.png",
    "var/prints-tema-epic-cody/megadrive.png": "tema-megadrive.png",
    "var/prints-tema-epic-cody/psx.png": "tema-psx.png",
    "var/prints-tema-epic-cody/love.png": "tema-love.png",
    "var/prints-tema-epic-cody/retroarch.png": "tema-retroarch.png",
    "var/exemplos-cor/mario-kart_comparacao-1-2-3-4.png": "shader-gba-comparativo.png",
    "var/exemplos-gb-gbc/gbc_smb-deluxe-f500_comparacao.png": "shader-gbc-comparativo.png",
    "var/exemplos-tv/comparativo-sonic1-f600.png": "shader-tv-comparativo.png",
}
LIMITE = 500 * 1024
for o, d in mapa.items():
    shutil.copyfile(o, dst / d)

try:
    from PIL import Image
except ImportError:
    Image = None
    print("sem PIL")

for d in mapa.values():
    p = dst / d
    if p.stat().st_size > LIMITE and Image:
        im = Image.open(p).convert("RGB")
        w, h = im.size
        while True:
            w, h = int(w * 0.8), int(h * 0.8)
            im2 = im.resize((w, h), Image.LANCZOS)
            im2.save(p, optimize=True)
            if p.stat().st_size <= LIMITE:
                break
    im_ok = Image.open(p).size if Image else "?"
    print(d, p.stat().st_size // 1024, "KB", im_ok)
