import hashlib
import re
import struct
import unittest
import xml.etree.ElementTree as ET
import zlib

from context import CFG, ROOT, TempDirCase, needs_base, slow
from r36img import build, mtools, squash
from r36img.util import run

F30 = ROOT / "features" / "30-telas-icone-controle"
LEIA_ME = F30 / "LEIA-ME.txt"
CAMADAS = ("system/usr/config", "storage/.config")
TELAS = ("splash/splash-std.png", "splash/splash-1080.png", "splash/retroarch.png",
         "splash/splash-1080.raw", "splash/loading-game-std.png", "splash/loading-game.png",
         "emulationstation/resources/logo.png", "emulationstation/resources/splash.xml")
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registrados():
    """Linhas '<sha256>  <caminho>' do LEIA-ME e o sha256 da arte de fábrica."""
    txt = LEIA_ME.read_text(encoding="utf-8")
    pares = dict((p, h) for h, p in re.findall(r"^([0-9a-f]{64})  (\S+)$", txt, re.M))
    arte = re.search(r"Arte de fábrica.*\n([0-9a-f]{64})$", txt, re.M).group(1)
    return pares, arte


def chunks(data):
    assert data[:8] == PNG_SIG, "assinatura PNG inválida"
    pos = 8
    while pos < len(data):
        (n,) = struct.unpack(">I", data[pos:pos + 4])
        tipo = data[pos + 4:pos + 8]
        yield tipo, data[pos + 8:pos + 8 + n]
        pos += 12 + n


def ihdr(path):
    tipo, corpo = next(chunks(path.read_bytes()))
    assert tipo == b"IHDR"
    w, h, prof, cor, _, _, entrel = struct.unpack(">IIBBBBB", corpo)
    return w, h, prof, cor, entrel


def pixels_rgb8(path):
    """Decodifica um PNG RGB de 8 bits sem entrelaçamento em bytes RGB24."""
    data = path.read_bytes()
    w, h, prof, cor, entrel = ihdr(path)
    assert (prof, cor, entrel) == (8, 2, 0)
    bruto = zlib.decompress(b"".join(c for t, c in chunks(data) if t == b"IDAT"))
    bpp, passo = 3, w * 3
    out, ant = bytearray(), bytearray(passo)
    for y in range(h):
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
        out += lin
        ant = lin
    return bytes(out)


class TelasIconeControle(unittest.TestCase):
    def test_sha256_contra_leia_me(self):
        pares, _ = registrados()
        esperados = {f"{c}/{n}" for c in CAMADAS for n in TELAS} | {"fonte-gamepad-2.svg", "boot/bootlogo.bmp"}
        self.assertEqual(set(pares), esperados)
        for caminho, h in pares.items():
            self.assertEqual(sha256(F30 / caminho), h, caminho)

    def test_bootlogo_bmp_valido(self):
        logo = F30 / "boot" / "bootlogo.bmp"
        self.assertTrue(logo.is_file(), "bootlogo.bmp ausente")
        self.assertEqual(logo.stat().st_size, 921654, "tamanho de bootlogo.bmp deve ser 921654")
        data = logo.read_bytes()
        self.assertEqual(data[:2], b"BM", "assinatura BMP inválida")
        magic, size, _, _, offset = struct.unpack("<2sIHHI", data[:14])
        bi_size, w, h, planes, bpp, comp, img_size = struct.unpack("<IIIHHII", data[14:38])
        self.assertEqual((size, offset, bi_size, w, h, planes, bpp, comp, img_size),
                         (921654, 54, 40, 640, 480, 1, 24, 0, 921600))

    def test_camadas_so_com_as_telas(self):
        for c in CAMADAS:
            raiz = c.split("/")[0]
            achados = {p.relative_to(F30 / c).as_posix()
                       for p in (F30 / raiz).rglob("*") if p.is_file()}
            self.assertEqual(achados, set(TELAS), raiz)

    def test_ihdr_640x480_rgb8(self):
        for c in CAMADAS:
            for n in TELAS:
                if n.endswith(".png"):
                    self.assertEqual(ihdr(F30 / c / n), (640, 480, 8, 2, 0), f"{c}/{n}")

    def test_todas_as_telas_iguais_ao_icone(self):
        icone = (F30 / CAMADAS[0] / "splash/loading-game.png").read_bytes()
        for c in CAMADAS:
            for n in TELAS:
                if n.endswith(".png"):
                    self.assertEqual((F30 / c / n).read_bytes(), icone, f"{c}/{n}")

    def test_raw_igual_ao_png(self):
        for c in CAMADAS:
            raw = (F30 / c / "splash/splash-1080.raw").read_bytes()
            self.assertEqual(len(raw), 921600, c)
            self.assertEqual(raw, pixels_rgb8(F30 / c / "splash/loading-game.png"), c)

    def test_logo_nas_duas_camadas(self):
        for c in CAMADAS:
            self.assertTrue((F30 / c / "emulationstation/resources/logo.png").is_file(), c)

    def test_splash_xml_valido_e_sem_texto(self):
        for c in CAMADAS:
            raiz = ET.parse(F30 / c / "emulationstation/resources/splash.xml").getroot()
            self.assertEqual(raiz.tag, "theme", c)
            texto = raiz.find("./view[@name='splash']/text[@name='label']/color")
            self.assertEqual(texto.text, "00000000", c)

    def test_sem_arte_de_fabrica(self):
        _, arte = registrados()
        for p in F30.rglob("*"):
            if p.is_file():
                self.assertNotEqual(sha256(p), arte, p.relative_to(F30))

    def test_emuelec_run_emu_splash_path(self):
        runemu = ROOT / "features" / "10-ptbr-sao-paulo" / "system" / "usr" / "bin" / "emuelecRunEmu.sh"
        self.assertTrue(runemu.is_file(), "emuelecRunEmu.sh ausente")
        txt = runemu.read_text(encoding="utf-8")
        self.assertIn('SPLASH_IMG="/usr/config/splash/loading-game.png"', txt)
        self.assertIn('mpv "$SPLASH_IMG"', txt)
        self.assertNotIn('mpv /storage/.config/splash/loading-game.png', txt)




FORA_DO_ESCOPO = ("blank.png", "emuelec_intro_1080p.mp4", "twitch-1080.png", "youtube-1080.png")


def hashes_system(parts_dir, tmp):
    """sha256 de todos os arquivos do SYSTEM (squashfs) de um build."""
    sq = tmp / "SYSTEM"
    run(["mcopy", "-n", "-i", parts_dir / "system.img", "::/SYSTEM", sq], env=mtools.ENV)
    tree = tmp / "system-tree"
    squash.extract(sq, tree)
    try:
        return squash.tree_hashes(tree)
    finally:
        run(["chmod", "-R", "u+rwX", tree])
        run(["rm", "-rf", tree, sq])


def hashes_boot(parts_dir, tmp):
    """sha256 dos arquivos do BOOT (FAT): o .img em si muda a cada build (datas)."""
    tree = tmp / "boot-tree"
    tree.mkdir()
    mtools.copy_tree_out(parts_dir / "boot.img", tree)
    try:
        return squash.tree_hashes(tree)
    finally:
        run(["rm", "-rf", tree])


def hashes_storage(parts_dir, tmp):
    """sha256 de todos os arquivos do STORAGE (ext4) de um build."""
    tree = tmp / "storage-tree"
    tree.mkdir()
    run(["debugfs", "-R", f"rdump / {tree}", parts_dir / "storage.img"])
    try:
        return squash.tree_hashes(tree)
    finally:
        run(["chmod", "-R", "u+rwX", tree])
        run(["rm", "-rf", tree])


@needs_base
@slow
class SemArteDeFabricaNaImagem(TempDirCase):
    """1.6: varre o SYSTEM e o STORAGE de imagens reais atrás da arte de fábrica."""

    def build(self, nome, **kw):
        return build.build(CFG, size_mib=7000, timestamp="20261013-153045", compress=False,
                           out_root=self.tmp / nome, work_root=self.tmp / f"work-{nome}", **kw) / "parts"

    def test_arte_de_fabrica(self):
        _, arte = registrados()
        base = self.build("base", none=True)
        feitas = self.build("feitas", names=["30-telas-icone-controle"])

        # a base tem o God of War, senão o teste não provaria nada
        base_sys, base_sto = hashes_system(base, self.tmp), hashes_storage(base, self.tmp)
        achados = [p for p, h in {**base_sys, **{"storage/" + k: v for k, v in base_sto.items()}}.items()
                   if h == arte]
        self.assertTrue(achados, "a arte de fábrica sumiu da imagem sem features")

        sys_, sto = hashes_system(feitas, self.tmp), hashes_storage(feitas, self.tmp)
        self.assertEqual([p for p, h in sys_.items() if h == arte], [])
        self.assertEqual([p for p, h in sto.items() if h == arte], [])

        # fora do escopo: vídeo de introdução e tela de bateria
        for nome in FORA_DO_ESCOPO:
            caminho = f"usr/config/splash/{nome}"
            self.assertEqual(sys_[caminho], base_sys[caminho], caminho)
        for parte in ("bootarea", "env", "kernel"):
            self.assertEqual(sha256(feitas / f"{parte}.img"), sha256(base / f"{parte}.img"), parte)

        # O boot.img tem bootlogo.bmp substituído pela feature 30:
        base_boot = hashes_boot(base, self.tmp)
        feitas_boot = hashes_boot(feitas, self.tmp)
        self.assertEqual(feitas_boot["bootlogo.bmp"], sha256(F30 / "boot" / "bootlogo.bmp"))
        self.assertNotEqual(feitas_boot["bootlogo.bmp"], base_boot["bootlogo.bmp"])
        self.assertEqual({k: v for k, v in feitas_boot.items() if k != "bootlogo.bmp"},
                         {k: v for k, v in base_boot.items() if k != "bootlogo.bmp"})


if __name__ == "__main__":
    unittest.main()
