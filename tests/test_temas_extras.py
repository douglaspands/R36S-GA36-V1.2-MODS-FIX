import tarfile
import unittest
from pathlib import Path

from context import ROOT, TempDirCase
from r36img import features as F
from r36img.errors import R36Error


class TemasExtrasTest(unittest.TestCase):
    def setUp(self):
        self.feat_dir = ROOT / "features" / "50-temas-extras"
        self.assertTrue(self.feat_dir.is_dir(), "features/50-temas-extras não encontrada")
        self.feat = F.load_feature(self.feat_dir)

    def test_descriptor_layers_and_paths(self):
        self.assertEqual(self.feat.id, "50-temas-extras")
        self.assertEqual(self.feat.budget_mib, 700)
        self.assertTrue(self.feat.enabled)

        roms_themes = {}
        storage_themes = {}

        for ext in self.feat.externals:
            if ext.layer == "roms":
                self.assertTrue(
                    ext.dest.startswith("themes/"),
                    f"Tema na camada 'roms' deve iniciar com 'themes/': {ext.dest}",
                )
                theme_name = ext.dest.split("/", 1)[1]
                roms_themes[theme_name] = ext
            elif ext.layer == "storage":
                self.assertTrue(
                    ext.dest.startswith(".config/emulationstation/themes/"),
                    f"Tema na camada 'storage' deve iniciar com '.config/emulationstation/themes/': {ext.dest}",
                )
                theme_name = ext.dest.split("themes/", 1)[1]
                storage_themes[theme_name] = ext
            else:
                self.fail(f"Camada inesperada para tema: {ext.layer}")

        self.assertEqual(set(storage_themes.keys()), {"Minimal EmuELEC", "Graphite OGA", "Epic Cody"})
        self.assertEqual(set(roms_themes.keys()), {"Switch", "Crystal"})
        self.assertIn(("storage", ".config/emulationstation/themes/NES-BOX"), self.feat.removes)

        nesbox = self.feat_dir / "roms" / "themes" / "NES-BOX"
        self.assertTrue(nesbox.is_dir(), "NES-BOX ausente em roms/themes/")
        self.assertTrue((nesbox / "theme.xml").is_file(), "theme.xml do NES-BOX ausente")

    def test_roms_themes_cache_have_no_symlinks(self):
        cache = ROOT / "work" / "cache" / "external"
        for ext in self.feat.externals:
            if ext.layer == "roms":
                archive = cache / f"{ext.sha256}.tar.gz"
                if not archive.is_file():
                    continue
                with tarfile.open(archive, "r:gz") as tar:
                    for m in tar:
                        self.assertFalse(
                            m.issym(),
                            f"Tarball {archive.name} ({ext.dest}) contém link simbólico: {m.name} -> {m.linkname}",
                        )
                        self.assertFalse(
                            m.islnk(),
                            f"Tarball {archive.name} ({ext.dest}) contém hard link: {m.name} -> {m.linkname}",
                        )


class FatSymlinkRejectionTest(TempDirCase):
    def test_symlink_rejected_in_roms_layer(self):
        roms_dir = self.tmp / "roms"
        roms_dir.mkdir()
        target = roms_dir / "target.txt"
        target.write_text("ok")
        link = roms_dir / "link.txt"
        link.symlink_to(target)

        feat_mock = type("MockFeature", (), {"id": "test-feat"})()
        with self.assertRaises(R36Error) as cm:
            F._walk_tree(feat_mock, "roms", roms_dir, "")
        self.assertIn("FAT não suporta links simbólicos", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
