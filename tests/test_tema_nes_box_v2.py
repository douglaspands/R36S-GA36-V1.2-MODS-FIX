import re
import subprocess
import tomllib
import unittest
import xml.etree.ElementTree as ET

from context import CFG, ROOT, have, needs_base

F51 = ROOT / "features" / "51-tema-nes-box-v2"
V2 = F51 / "storage" / ".config" / "emulationstation" / "themes" / "NES-BOX-V2"
ARQUIVOS = ("system.png", "background_icon.png")


def temas_do_es_systems():
    """Nomes de <theme> do es_systems.cfg da p8 da base (debugfs, só leitura)."""
    p8 = CFG.part("storage")
    r = subprocess.run(
        ["debugfs", "-R", "cat /.config/emulationstation/es_systems.cfg",
         f"{CFG.base_path}?offset={p8.offset}"],
        capture_output=True, check=True)
    return sorted(set(re.findall(r"<theme>([^<]+)</theme>", r.stdout.decode())))


def pastas_copiadas():
    """Entradas da raiz do V2 que vêm do NES-BOX da base (listadas no .gitignore)."""
    gi = F51 / ".gitignore"
    if not gi.is_file():
        return set()
    prefixo = "/" + V2.relative_to(F51).as_posix() + "/"
    return {l[len(prefixo):] for l in gi.read_text().splitlines() if l.startswith(prefixo)}


def caminhos_do_theme_xml(theme_xml):
    """<include> e <path> do theme.xml, resolvidos a partir da pasta dele."""
    raiz = ET.parse(theme_xml).getroot()
    refs = [e.text.strip() for e in raiz.iter() if e.tag in ("include", "path") and e.text]
    return [(r, (theme_xml.parent / r).resolve()) for r in refs]


@needs_base
@unittest.skipUnless(have("debugfs", "magick"), "debugfs ou ImageMagick ausente")
class TemaNesBoxV2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fontes = tomllib.loads((F51 / "fontes.toml").read_text())
        cls.temas = temas_do_es_systems()
        cls.copiadas = pastas_copiadas()

    def test_fontes_cobrem_os_16_arquivos(self):
        novos = ["wii", "pgm2", "fmtmarty", "mplayer", "freej2me", "gmloader", "karaoke", "imageviewer"]
        esperado = {(s, a) for s in novos for a in ARQUIVOS}
        arte = self.fontes.get("arte", [])
        got = [(a["sistema"], a["arquivo"]) for a in arte]
        self.assertEqual(sorted(esperado - set(got)), [], "entrada(s) faltando em fontes.toml")
        self.assertEqual(sorted(set(got) - esperado), [], "entrada(s) inesperadas em fontes.toml")
        self.assertEqual(len(got), len(set(got)), "entrada duplicada em fontes.toml")

    def test_fontes_campos_por_tipo(self):
        erros = []
        for a in self.fontes.get("arte", []):
            nome = f"{a['sistema']}/{a['arquivo']}"
            if a.get("tipo") == "oficial":
                for campo in ("url", "sha256", "cache", "fonte"):
                    if not a.get(campo):
                        erros.append(f"{nome}: oficial sem {campo}")
                if not re.fullmatch(r"[0-9a-f]{64}", a.get("sha256", "")):
                    erros.append(f"{nome}: sha256 inválido")
            elif a.get("tipo") == "criado":
                if not a.get("motivo"):
                    erros.append(f"{nome}: criado sem motivo")
            else:
                erros.append(f"{nome}: tipo inválido {a.get('tipo')!r}")
        self.assertEqual(erros, [])

    def test_copia_do_nes_box_presente(self):
        self.assertTrue((V2 / "theme.xml").is_file(),
                        "cópia do NES-BOX ausente: rode features/51-tema-nes-box-v2/gerar.sh")

    def test_todo_sistema_tem_pasta_com_tema(self):
        faltam = [t for t in self.temas if not (V2 / t / "theme.xml").is_file()]
        self.assertEqual(faltam, [], f"{len(faltam)} sistema(s) sem pasta com theme.xml no NES-BOX-V2")

    def test_caminhos_dos_temas_novos_resolvem(self):
        quebrados = []
        for pasta in sorted(p for p in V2.iterdir() if p.is_dir() and p.name not in self.copiadas):
            theme_xml = pasta / "theme.xml"
            if not theme_xml.is_file():
                continue
            for ref, destino in caminhos_do_theme_xml(theme_xml):
                # O ES (resolveRelativePath) só resolve caminho que começa com "./".
                if not ref.startswith("./") or not destino.is_file():
                    quebrados.append(f"{pasta.name}: {ref}")
        self.assertEqual(quebrados, [])

    def test_png_acrescentados_tem_formato_da_spec(self):
        erros = []
        for a in self.fontes.get("arte", []):
            png = V2 / a["sistema"] / a["arquivo"]
            if not png.is_file():
                erros.append(f"{a['sistema']}/{a['arquivo']}: ausente")
                continue
            r = subprocess.run(["magick", "identify", "-format", "%w %h %A %[fx:minima.a]", str(png)],
                               capture_output=True, text=True, check=True)
            w, h, alpha, amin = r.stdout.split()
            nome = f"{a['sistema']}/{a['arquivo']}"
            if alpha == "Undefined" or float(amin) >= 1:
                erros.append(f"{nome}: sem transparência")
            if a["arquivo"] == "system.png" and not 400 <= int(w) <= 600:
                erros.append(f"{nome}: largura {w} fora de 400-600")
            if a["arquivo"] == "background_icon.png" and (int(w), int(h)) != (960, 540):
                erros.append(f"{nome}: {w}x{h}, esperado 960x540")
        self.assertEqual(erros, [])

    def test_leia_me_registra_os_15_sistemas(self):
        texto = (F51 / "LEIA-ME.txt").read_text()
        novos = set(self.fontes["referencias"]) | {a["sistema"] for a in self.fontes["arte"]}
        self.assertEqual(len(novos), 15)
        sem = [n for n in sorted(novos) if not re.search(rf"^\s+{re.escape(n)}\b", texto, re.M)]
        self.assertEqual(sem, [], "sistema(s) ausentes do LEIA-ME.txt")
        for a in self.fontes["arte"]:
            if a["tipo"] == "oficial":
                self.assertIn(a["sha256"], texto)
                self.assertIn(a["url"], texto)

    def test_pasta_nova_tem_origem_registrada(self):
        refs = self.fontes.get("referencias", {})
        arte = {(a["sistema"], a["arquivo"]) for a in self.fontes.get("arte", [])}
        sem_origem = []
        for pasta in sorted(p.name for p in V2.iterdir() if p.is_dir() and p.name not in self.copiadas):
            if pasta in refs:
                continue
            sem_origem += [f"{pasta}/{a}" for a in ARQUIVOS if (pasta, a) not in arte]
        self.assertEqual(sem_origem, [], "arquivo(s) de arte sem origem em fontes.toml")

    def test_sistemas_faltantes_tem_origem(self):
        """Todo sistema que o NES-BOX da base não cobre precisa de origem registrada."""
        refs = self.fontes.get("referencias", {})
        arte = {a["sistema"] for a in self.fontes.get("arte", [])}
        sem = [t for t in self.temas if t not in self.copiadas and t not in refs and t not in arte]
        self.assertEqual(sem, [], "sistema(s) sem pasta nem origem registrada")


if __name__ == "__main__":
    unittest.main()
