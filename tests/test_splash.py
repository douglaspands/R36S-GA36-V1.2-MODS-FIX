import hashlib
import re
import struct
import unittest
import zlib

from context import ROOT

F30 = ROOT / "features" / "30-splash-padrao-emuelec"
LEIA_ME = F30 / "LEIA-ME.txt"
CAMADAS = ("system/usr/config/splash", "storage/.config/splash")
TELAS = ("splash-std.png", "splash-1080.png", "retroarch.png", "splash-1080.raw",
         "loading-game-std.png", "loading-game.png")
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


class SplashPadraoEmuelec(unittest.TestCase):
    def test_sha256_contra_leia_me(self):
        pares, _ = registrados()
        esperados = {f"{c}/{n}" for c in CAMADAS for n in TELAS}
        esperados |= {"fonte-splash-distribuicao-1080.png", "fonte-gamepad-2.svg"}
        self.assertEqual(set(pares), esperados)
        for caminho, h in pares.items():
            self.assertEqual(sha256(F30 / caminho), h, caminho)

    def test_camadas_so_com_as_telas(self):
        for c in CAMADAS:
            raiz = c.split("/")[0]
            achados = {p.relative_to(F30 / raiz).as_posix()
                       for p in (F30 / raiz).rglob("*") if p.is_file()}
            prefixo = c.split("/", 1)[1]
            self.assertEqual(achados, {f"{prefixo}/{n}" for n in TELAS}, raiz)

    def test_ihdr_640x480_rgb8(self):
        for c in CAMADAS:
            for n in TELAS:
                if n.endswith(".png"):
                    self.assertEqual(ihdr(F30 / c / n), (640, 480, 8, 2, 0), f"{c}/{n}")

    def test_raw_igual_ao_png_de_boot(self):
        for c in CAMADAS:
            raw = (F30 / c / "splash-1080.raw").read_bytes()
            self.assertEqual(len(raw), 921600, c)
            self.assertEqual(raw, pixels_rgb8(F30 / c / "splash-std.png"), c)

    def test_sem_arte_de_fabrica(self):
        _, arte = registrados()
        for p in F30.rglob("*"):
            if p.is_file():
                self.assertNotEqual(sha256(p), arte, p.relative_to(F30))


if __name__ == "__main__":
    unittest.main()
