import os
from PIL import Image

cache_dir = os.path.expanduser("~/.cache/shader-tv-test")
for root, dirs, files in os.walk(cache_dir):
    for f in sorted(files):
        if f.endswith(".png"):
            p = os.path.join(root, f)
            im = Image.open(p)
            print(f"{f}: {im.size}, mode={im.mode}")
