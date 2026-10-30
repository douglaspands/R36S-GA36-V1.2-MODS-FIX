from PIL import Image
import numpy as np

im = Image.open("var/exemplos-tv/shader-sonic1-f600.png").convert("RGB")
arr = np.asarray(im).astype(np.float32) / 255.0

# Calcule a luminosidade média de cada linha (y = 0 até 479)
row_luma = arr.mean(axis=(1, 2))

# Imprima as primeiras 60 linhas
print("Luminosidade média linha a linha (y=100 a y=160 no céu/fundo uniforme):")
for y in range(120, 170):
    val = row_luma[y]
    diff = val - row_luma[120:170].mean()
    bars = "#" * int(abs(diff) * 200)
    sign = "+" if diff >= 0 else "-"
    print(f"y={y:3d}: {val:.4f} | {sign} {bars}")
