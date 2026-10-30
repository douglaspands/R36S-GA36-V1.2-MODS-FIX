import numpy as np

OH = 480
h = 224
ys = np.arange(OH, dtype=np.float32)
v = (ys + 0.5) / OH
py = h / OH

# 1. Point-sampled sine
y_pos = (v * h) - np.floor(v * h) - 0.5
s = np.sin(np.pi * y_pos)
beam_point = 1.0 - 0.15 * (s * s)

# 2. Box-filtered gap
pos = (v * h) - np.floor(v * h)
gap = min(py, 0.45)
lo = pos - 0.5 * py
hi = pos + 0.5 * py
cover = (np.clip(np.minimum(hi, 1.0) - np.maximum(lo, 1.0 - gap), 0.0, gap) +
         np.clip(np.minimum(hi, 0.0) - np.maximum(lo, -gap), 0.0, gap))
cover = np.minimum(cover / py, 1.0)
beam_box = 1.0 - 0.15 * cover

print("Point-sampled (first 30 pixels):")
for i in range(30):
    val = beam_point[i]
    bars = '#' * int(round((1.0 - val) * 100))
    print(f"pix {i:2d} (line {v[i]*h:.2f}): {val:.3f} | {bars}")

print("\nBox-filtered (first 30 pixels):")
for i in range(30):
    val = beam_box[i]
    bars = '#' * int(round((1.0 - val) * 100))
    print(f"pix {i:2d} (line {v[i]*h:.2f}): {val:.3f} | {bars}")
