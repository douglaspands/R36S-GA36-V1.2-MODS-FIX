import shutil
from pathlib import Path
from PIL import Image

src = Path("var/r36s.jpg")
dst = Path("docs/img/r36s.jpg")
shutil.copyfile(src, dst)
im = Image.open(dst).convert("RGB")
print("original", im.size, dst.stat().st_size // 1024, "KB")
LIMITE = 500 * 1024
while dst.stat().st_size > LIMITE:
    w, h = im.size
    im = im.resize((int(w * 0.85), int(h * 0.85)), Image.LANCZOS)
    im.save(dst, quality=85, optimize=True)
print("final", Image.open(dst).size, dst.stat().st_size // 1024, "KB")
