import subprocess
import unittest

from context import CFG, ROOT, TempDirCase, needs_base
from r36img import mtools

F52 = ROOT / "features" / "52-psp-desempenho"
INI_SYSTEM = F52 / "system" / "usr" / "config" / "ppsspp" / "PSP" / "SYSTEM" / "ppsspp.ini"
INI_STORAGE = F52 / "storage" / ".config" / "ppsspp" / "PSP" / "SYSTEM" / "ppsspp.ini"

NOVOS = {
    "InternalResolution": ("2", "1"),
    "CPUSpeed": ("666", "0"),
    "NumWorkerThreads": ("8", "4"),
    "SkipGPUReadbackMode": ("0", "1"),
    "SplineBezierQuality": ("1", "0"),
    "ShowFPSCounter": ("2", "0"),
}


def linhas(data):
    return data.decode("utf-8").split("\n")


def diferencas(base, novo):
    """[(chave, valor_base, valor_novo)] das linhas que mudaram; exige mesma contagem de linhas."""
    a, b = linhas(base), linhas(novo)
    assert len(a) == len(b), (len(a), len(b))
    out = []
    for x, y in zip(a, b):
        if x != y:
            ck, _, vx = x.partition(" = ")
            cy, _, vy = y.partition(" = ")
            assert ck == cy, (x, y)
            out.append((ck, vx, vy))
    return out


class PspFeature(unittest.TestCase):
    def test_descritor(self):
        txt = (F52 / "feature.toml").read_text()
        self.assertIn("order = 52", txt)
        self.assertIn("enabled = true", txt)

    def test_camadas_iguais(self):
        self.assertEqual(INI_SYSTEM.read_bytes(), INI_STORAGE.read_bytes())

    def test_valores_novos(self):
        d = {}
        for line in linhas(INI_STORAGE.read_bytes()):
            k, sep, v = line.partition(" = ")
            if sep:
                d.setdefault(k, []).append(v)
        for chave, (_, novo) in NOVOS.items():
            self.assertEqual(d[chave], [novo], chave)


@needs_base
class PspContraBase(TempDirCase):
    def extrai_base(self):
        sq = self.tmp / "SYSTEM"
        subprocess.run(
            ["mcopy", "-n", "-i", mtools.spec(CFG.base_path, CFG.part("system").offset), "::/SYSTEM", str(sq)],
            check=True, env=mtools.ENV, capture_output=True)
        return subprocess.run(
            ["unsquashfs", "-cat", str(sq), "usr/config/ppsspp/PSP/SYSTEM/ppsspp.ini"],
            check=True, capture_output=True).stdout

    def test_so_as_seis_chaves_mudam(self):
        base = self.extrai_base()
        esperado = sorted((k, a, b) for k, (a, b) in NOVOS.items())
        self.assertEqual(sorted(diferencas(base, INI_SYSTEM.read_bytes())), esperado)
        self.assertEqual(sorted(diferencas(base, INI_STORAGE.read_bytes())), esperado)


if __name__ == "__main__":
    unittest.main()
