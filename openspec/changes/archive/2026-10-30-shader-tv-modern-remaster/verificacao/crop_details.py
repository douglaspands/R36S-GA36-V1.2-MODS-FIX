from PIL import Image
from pathlib import Path

saida = Path("var/exemplos-tv")

# Carrega original e calibrado do SOR2
im_orig_sor2 = Image.open("~/.cache/shader-tv-test/sor2/sor2-f600.png".replace("~", str(Path.home()))).convert("RGB")
im_calib_sor2 = Image.open(saida / "sor2-f600-calibrado.png").convert("RGB")

# No SOR2 f600, o chão/sombra e a placa neon do bar
# Em 320x224 nativo, área [100, 100, 220, 180] -> em 640x480 é [200, 214, 440, 385]
crop_orig_sor2 = im_orig_sor2.crop((80, 80, 240, 180)).resize((480, 300), Image.NEAREST)
crop_calib_sor2 = im_calib_sor2.crop((160, 171, 480, 385))

comp_sor2 = Image.new("RGB", (980, 330), (20, 20, 24))
comp_sor2.paste(crop_orig_sor2, (10, 20))
comp_sor2.paste(crop_calib_sor2, (500, 20))
comp_sor2.save(saida / "zoom-sor2-luzes-e-transparencia.png")

# Carrega original e calibrado do Sonic
im_orig_sonic = Image.open("~/.cache/shader-tv-test/sonic1/sonic1-f600.png".replace("~", str(Path.home()))).convert("RGB")
im_calib_sonic = Image.open(saida / "sonic1-f600-calibrado.png").convert("RGB")

crop_orig_sonic = im_orig_sonic.crop((100, 60, 220, 160)).resize((480, 400), Image.NEAREST)
crop_calib_sonic = im_calib_sonic.crop((200, 128, 440, 342)).resize((480, 400), Image.NEAREST)

comp_sonic = Image.new("RGB", (980, 430), (20, 20, 24))
comp_sonic.paste(crop_orig_sonic, (10, 20))
comp_sonic.paste(crop_calib_sonic, (500, 20))
comp_sonic.save(saida / "zoom-sonic-detalhes.png")

print("Zoons de detalhes salvos em:")
print(f"  {saida / 'zoom-sor2-luzes-e-transparencia.png'}")
print(f"  {saida / 'zoom-sonic-detalhes.png'}")
