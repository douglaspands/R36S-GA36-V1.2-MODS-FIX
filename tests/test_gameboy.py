import hashlib
import re
import unittest
import zlib

from context import CFG, ROOT, TempDirCase, needs_base
from r36img import mtools, squash
from r36img.util import run
from test_splash import chunks, ihdr

F51 = ROOT / "features" / "51-gameboy-fiel"
LEIA_ME = F51 / "LEIA-ME.txt"
OVERLAYS = F51 / "system/usr/share/retroarch-overlays/r36-gameboy"
OVERRIDES = F51 / "storage/.config/retroarch/config/Gambatte"
PRESETS = F51 / "storage/shaders/presets/Gambatte"
MOLDURAS = {"gb": "gb-dmg", "gbc": "gbc-atomic-purple"}
W, H = 640, 480
JOGO_X0, JOGO_X1 = 53, 586
DIR_X0 = 587


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgba(path):
    """Linhas de bytes RGBA de um PNG RGBA de 8 bits sem entrelaçamento."""
    assert ihdr(path) == (W, H, 8, 6, 0), path
    bruto = zlib.decompress(b"".join(c for t, c in chunks(path.read_bytes()) if t == b"IDAT"))
    passo, bpp = W * 4, 4
    linhas, ant = [], bytearray(passo)
    for y in range(H):
        filtro = bruto[y * (passo + 1)]
        lin = bytearray(bruto[y * (passo + 1) + 1:(y + 1) * (passo + 1)])
        for i in range(passo):
            a = lin[i - bpp] if i >= bpp else 0
            b = ant[i]
            c = ant[i - bpp] if i >= bpp else 0
            if filtro == 1:
                lin[i] = (lin[i] + a) & 0xFF
            elif filtro == 2:
                lin[i] = (lin[i] + b) & 0xFF
            elif filtro == 3:
                lin[i] = (lin[i] + (a + b) // 2) & 0xFF
            elif filtro == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                lin[i] = (lin[i] + pred) & 0xFF
        linhas.append(lin)
        ant = lin
    return linhas


def pixel(linhas, x, y):
    return tuple(linhas[y][x * 4:x * 4 + 4])


def chaves(path):
    """{chave: valor} de um .cfg/.opt do RetroArch (valores sem aspas)."""
    return dict(re.findall(r'^(\w+) = "?([^"\n]*)"?$', path.read_text(), re.M))


class Molduras(unittest.TestCase):
    def test_sha256_contra_leia_me(self):
        txt = LEIA_ME.read_text(encoding="utf-8")
        pares = dict((p, h) for h, p in re.findall(r"^([0-9a-f]{64})  (\S+)$", txt, re.M))
        base = "system/usr/share/retroarch-overlays/r36-gameboy"
        esperados = {"fonte-barlow-semibold.ttf", "fonte-barlow-OFL.txt"}
        for m in MOLDURAS.values():
            esperados |= {f"{base}/{m}.png", f"{base}/{m}.cfg"}
        self.assertEqual(set(pares), esperados)
        for caminho, h in pares.items():
            self.assertEqual(sha256(F51 / caminho), h, caminho)

    def test_640x480_rgba(self):
        for m in MOLDURAS.values():
            self.assertEqual(ihdr(OVERLAYS / f"{m}.png"), (W, H, 8, 6, 0), m)

    def test_recorte_do_jogo_transparente_e_faixas_opacas(self):
        for m in MOLDURAS.values():
            linhas = rgba(OVERLAYS / f"{m}.png")
            for y in range(H):
                lin = linhas[y]
                for x in range(JOGO_X0, JOGO_X1 + 1):
                    self.assertEqual(lin[x * 4 + 3], 0, (m, x, y))
                for x in (*range(0, JOGO_X0), *range(DIR_X0, W)):
                    self.assertEqual(lin[x * 4 + 3], 255, (m, x, y))

    def test_faixa_direita_lisa(self):
        for m in MOLDURAS.values():
            linhas = rgba(OVERLAYS / f"{m}.png")
            ref = bytes(linhas[0][DIR_X0 * 4:])
            for y in range(1, H):
                self.assertEqual(bytes(linhas[y][DIR_X0 * 4:]), ref, (m, y))

    def test_faixa_esquerda_tem_o_led(self):
        for m in MOLDURAS.values():
            linhas = rgba(OVERLAYS / f"{m}.png")
            r, g, b, _ = pixel(linhas, 26, 172)
            self.assertTrue(r > 180 and g < 90 and b < 90, (m, (r, g, b)))

    def test_cfg_de_overlay(self):
        for m in MOLDURAS.values():
            c = chaves(OVERLAYS / f"{m}.cfg")
            self.assertEqual(c["overlays"], "1")
            self.assertEqual(c["overlay0_overlay"], f"{m}.png")
            self.assertEqual(c["overlay0_full_screen"], "true")
            self.assertEqual(c["overlay0_descs"], "0")


class Overrides(unittest.TestCase):
    def test_viewport_bate_com_o_recorte(self):
        for sistema, m in MOLDURAS.items():
            c = chaves(OVERRIDES / f"{sistema}.cfg")
            self.assertEqual(c["aspect_ratio_index"], "23")
            self.assertEqual(int(c["custom_viewport_x"]), JOGO_X0)
            self.assertEqual(int(c["custom_viewport_y"]), 0)
            self.assertEqual(int(c["custom_viewport_width"]), JOGO_X1 - JOGO_X0 + 1)
            self.assertEqual(int(c["custom_viewport_height"]), H)
            self.assertEqual(c["video_scale_integer"], "false")
            self.assertEqual(c["video_smooth"], "false")
            self.assertEqual(c["input_overlay_enable"], "true")
            self.assertEqual(float(c["input_overlay_opacity"]), 1.0)
            self.assertEqual(c["input_overlay"], f"/tmp/overlays/r36-gameboy/{m}.cfg")

    def test_opcoes_do_core(self):
        self.assertEqual(chaves(OVERRIDES / "gb.opt"), {"gambatte_gb_colorization": "disabled"})
        self.assertEqual(chaves(OVERRIDES / "gbc.opt"), {"gambatte_gbc_color_correction": "GBC only"})

    def test_so_gb_e_gbc(self):
        achados = {p.name for p in OVERRIDES.iterdir()}
        self.assertEqual(achados, {"gb.cfg", "gbc.cfg", "gb.opt", "gbc.opt"})

    def test_caminhos_dos_presets_absolutos(self):
        for sistema in MOLDURAS:
            for caminho in caminhos_do_preset(PRESETS / f"{sistema}.glslp"):
                self.assertTrue(caminho.startswith("/usr/share/common-shaders/"), caminho)


def caminhos_do_preset(path):
    """Valores de shaderN e das texturas citadas no preset."""
    c = chaves(path)
    texturas = c.get("textures", "").split(";") if c.get("textures") else []
    return [v for k, v in c.items() if re.fullmatch(r"shader\d+", k)] + [c[t] for t in texturas]


@needs_base
class PresetsNaBase(TempDirCase):
    def test_shaders_e_texturas_existem_no_squashfs(self):
        sq = self.tmp / "SYSTEM"
        run(["mcopy", "-n", "-i", mtools.spec(CFG.base_path, CFG.part("system").offset), "::/SYSTEM", sq],
            env=mtools.ENV)
        existentes = set(squash.listing(sq))
        for sistema in MOLDURAS:
            for caminho in caminhos_do_preset(PRESETS / f"{sistema}.glslp"):
                self.assertIn(caminho.lstrip("/"), existentes, f"{sistema}: {caminho}")


if __name__ == "__main__":
    unittest.main()
