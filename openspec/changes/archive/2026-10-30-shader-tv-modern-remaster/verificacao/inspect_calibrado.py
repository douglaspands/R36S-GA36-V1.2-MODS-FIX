from PIL import Image
import numpy as np

im = Image.open("var/exemplos-tv/sonic1-f600-calibrado.png").convert("RGB")
arr = np.asarray(im).astype(np.float32) / 255.0
row_luma = arr.mean(axis=(1, 2))

print("Luminosidade média linha a linha no calibrado (y=120 a y=160):")
media = row_luma[120:160].mean()
for y in range(120, 160):
    val = row_luma[y]
    diff = val - media
    bars = "#" * int(abs(diff) * 200)
    sign = "+" if diff >= 0 else "-"
    print(f"y={y:3d}: {val:.4f} | {sign} {bars}")
