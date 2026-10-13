import os
import unittest
from pathlib import Path

from context import ROOT, TempDirCase
from r36img import features as F
from r36img.errors import R36Error
from r36img.squash import Entry


def write_feature(root, fid, toml, files=None):
    d = Path(root) / fid
    d.mkdir(parents=True)
    if toml is not None:
        (d / "feature.toml").write_text(toml)
    for rel, content in (files or {}).items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if content is None:
            p.mkdir(exist_ok=True)
            continue
        p.write_text(content)
        if rel.endswith(".sh"):
            p.chmod(0o755)
    return d


def desc(name="X", order=10, extra=""):
    return f'schema = 1\nname = "{name}"\ndescription = "teste"\norder = {order}\n{extra}'


SYSTEM_BASE = {
    "": Entry("d", 0o755, 0, 0, "", "2025-08-22 09:45"),
    "usr": Entry("d", 0o755, 0, 0, "", "t"),
    "usr/bin": Entry("d", 0o755, 0, 0, "", "t"),
    "usr/bin/busybox": Entry("-", 0o4755, 0, 0, "510988", "t"),
    "usr/config": Entry("d", 0o755, 0, 0, "", "t"),
    "usr/config/emuelec": Entry("d", 0o755, 0, 0, "", "t"),
    "usr/config/emuelec/bin": Entry("d", 0o755, 0, 0, "", "t"),
    "usr/config/emuelec/bin/put_user_bins_here": Entry("-", 0o644, 0, 0, "0", "t"),
}
STORAGE_BASE = {"": Entry("d", 0o755, 0, 0, ""), ".config": Entry("d", 0o755, 0, 0, "")}
BOOT_BASE = {"bootlogo.bmp": Entry("-", 0, 0, 0, "921654"), "bat": Entry("d", 0, 0, 0, "")}


class DescriptorTest(TempDirCase):
    def test_valid(self):
        d = write_feature(self.tmp, "10-a", desc(extra='enabled = false\n[[remove]]\nlayer = "system"\npath = "/usr/x"\n'
                                                 '[[meta]]\nlayer = "system"\npath = "usr/x"\nmode = "4755"\n'
                                                 '[[override]]\nlayer = "storage"\npath = "a"\nfeature = "05-b"\n'),
                          {"system/usr/x": "x"})
        f = F.load_feature(d)
        self.assertEqual((f.id, f.name, f.order, f.enabled), ("10-a", "X", 10, False))
        self.assertEqual(f.removes, [("system", "usr/x")])
        self.assertEqual(f.metas[0].mode, 0o4755)
        self.assertIn(("storage", "a", "05-b"), f.overrides)

    def test_missing_descriptor(self):
        d = write_feature(self.tmp, "10-a", None, {"system/x": "1"})
        with self.assertRaises(R36Error) as cm:
            F.load_feature(d)
        self.assertIn("10-a", str(cm.exception))
        self.assertIn("feature.toml ausente", str(cm.exception))

    def test_missing_fields(self):
        for field, toml in (("name", 'schema = 1\ndescription = ""\norder = 1\n'),
                            ("order", 'schema = 1\nname = "a"\ndescription = ""\n'),
                            ("description", 'schema = 1\nname = "a"\norder = 1\n'),
                            ("schema", 'name = "a"\ndescription = ""\norder = 1\n')):
            with self.subTest(field=field):
                d = write_feature(self.tmp / field, "10-a", toml)
                with self.assertRaises(R36Error) as cm:
                    F.load_feature(d)
                self.assertIn(f"campo '{field}' faltando", str(cm.exception))
                self.assertIn(str(d), str(cm.exception))

    def test_unknown_schema(self):
        d = write_feature(self.tmp, "10-a", desc().replace("schema = 1", "schema = 2"))
        with self.assertRaises(R36Error) as cm:
            F.load_feature(d)
        self.assertIn("schema 2 desconhecido", str(cm.exception))

    def test_unknown_layer_dir(self):
        d = write_feature(self.tmp, "10-a", desc(), {"kernel/zImage": "k"})
        with self.assertRaises(R36Error) as cm:
            F.load_feature(d)
        msg = str(cm.exception)
        self.assertIn("camada desconhecida 'kernel/'", msg)
        self.assertIn("system, storage, roms, boot", msg)

    def test_meta_on_fat_layer_rejected(self):
        d = write_feature(self.tmp, "10-a", desc(extra='[[meta]]\nlayer = "boot"\npath = "a"\nmode = "0644"\n'))
        with self.assertRaises(R36Error):
            F.load_feature(d)


class SelectionAndConflictTest(TempDirCase):
    def setUp(self):
        super().setUp()
        write_feature(self.tmp, "10-a", desc("A", 10), {"storage/.config/x.conf": "de A"})
        write_feature(self.tmp, "20-b", desc("B", 20), {"storage/.config/x.conf": "de B"})
        write_feature(self.tmp, "05-off", desc("Off", 5, "enabled = false\n"), {"system/usr/bin/off": "o"})

    def test_order_and_disabled(self):
        all_f = F.discover(self.tmp)
        self.assertEqual([f.id for f in all_f], ["05-off", "10-a", "20-b"])
        self.assertEqual([f.id for f in F.select(all_f)], ["10-a", "20-b"])
        self.assertEqual(F.select(all_f, none=True), [])
        self.assertEqual([f.id for f in F.select(all_f, ["05-off"])], ["05-off"])
        with self.assertRaises(R36Error) as cm:
            F.select(all_f, ["99-nao"])
        self.assertIn("Disponíveis: 05-off, 10-a, 20-b", str(cm.exception))

    def test_undeclared_conflict(self):
        feats = F.select(F.discover(self.tmp))
        with self.assertRaises(R36Error) as cm:
            F.plan_layer("storage", feats, STORAGE_BASE)
        msg = str(cm.exception)
        self.assertIn("'10-a'", msg)
        self.assertIn("'20-b'", msg)
        self.assertIn("storage:/.config/x.conf", msg)

    def test_declared_override(self):
        (self.tmp / "20-b" / "feature.toml").write_text(
            desc("B", 20, '[[override]]\nlayer = "storage"\npath = ".config/x.conf"\nfeature = "10-a"\n'))
        feats = F.select(F.discover(self.tmp))
        plan = F.plan_layer("storage", feats, STORAGE_BASE)
        last = plan.changes[-1]
        self.assertEqual((last.feature, last.op, last.overrode), ("20-b", "replaced", "10-a"))
        self.assertEqual(last.src.read_text(), "de B")
        self.assertIn("substitui '10-a'", F.report({"storage": plan}, feats))

    def test_disabled_not_in_plan(self):
        feats = F.select(F.discover(self.tmp))
        plan = F.plan_layer("system", feats, SYSTEM_BASE)
        self.assertEqual(plan.changes, [])


class MetadataRulesTest(TempDirCase):
    def plan(self, files, extra=""):
        write_feature(self.tmp / "feats", "10-a", desc(extra=extra), files)
        return F.plan_layer("system", F.discover(self.tmp / "feats"), SYSTEM_BASE)

    def test_new_script_is_0755_root(self):
        p = self.plan({"system/usr/bin/meu-script.sh": "#!/bin/sh\n"})
        self.assertEqual(p.final["usr/bin/meu-script.sh"].describe()[:14], "-rwxr-xr-x 0/0")

    def test_new_plain_file_and_dir(self):
        p = self.plan({"system/usr/share/novo/dados.txt": "x"})
        self.assertEqual(p.final["usr/share"].lsmode(), "drwxr-xr-x")
        self.assertEqual(p.final["usr/share/novo/dados.txt"].describe()[:14], "-rw-r--r-- 0/0")
        self.assertEqual([c.op for c in p.changes], ["added", "added", "added"])

    def test_replace_inherits(self):
        p = self.plan({"system/usr/bin/busybox": "novo"})
        e = p.final["usr/bin/busybox"]
        self.assertEqual(e.describe()[:14], "-rwsr-xr-x 0/0")
        self.assertEqual(e.size, "4")
        self.assertEqual(p.changes[0].op, "replaced")

    def test_meta_overrides(self):
        p = self.plan({"system/usr/bin/privado": "x"},
                      '[[meta]]\nlayer = "system"\npath = "usr/bin/privado"\nmode = "0700"\nuid = 0\ngid = 0\n')
        self.assertEqual(p.final["usr/bin/privado"].describe()[:14], "-rwx------ 0/0")

    def test_meta_on_base_path(self):
        p = self.plan({}, '[[meta]]\nlayer = "system"\npath = "usr/bin/busybox"\nmode = "0755"\n')
        self.assertEqual(p.final["usr/bin/busybox"].lsmode(), "-rwxr-xr-x")
        self.assertIn("usr/bin/busybox", p.touched)
        self.assertEqual(p.changes[0].op, "meta")

    def test_declared_removal(self):
        p = self.plan({}, '[[remove]]\nlayer = "system"\npath = "usr/config/emuelec/bin/put_user_bins_here"\n')
        self.assertNotIn("usr/config/emuelec/bin/put_user_bins_here", p.final)
        self.assertIn("removido", F.report({"system": p}, F.discover(self.tmp / "feats")))

    def test_remove_dir_recursive(self):
        p = self.plan({}, '[[remove]]\nlayer = "system"\npath = "usr/config"\n')
        self.assertFalse(any(k.startswith("usr/config") for k in p.final))

    def test_remove_nonexistent_fails(self):
        with self.assertRaises(R36Error) as cm:
            self.plan({}, '[[remove]]\nlayer = "system"\npath = "usr/nao/existe"\n')
        self.assertIn("10-a", str(cm.exception))
        self.assertIn("usr/nao/existe", str(cm.exception))

    def test_fat_case_insensitive_replace(self):
        write_feature(self.tmp, "10-a", desc(), {"boot/BOOTLOGO.BMP": "logo"})
        p = F.plan_layer("boot", F.discover(self.tmp), BOOT_BASE)
        self.assertEqual((p.changes[0].op, p.changes[0].path), ("replaced", "bootlogo.bmp"))

    def test_apply_to_tree(self):
        tree = self.tmp / "tree"
        (tree / "usr/bin").mkdir(parents=True)
        (tree / "usr/bin/busybox").write_text("velho")
        (tree / "usr/config/emuelec/bin").mkdir(parents=True)
        (tree / "usr/config/emuelec/bin/put_user_bins_here").write_text("")
        p = self.plan({"system/usr/bin/busybox": "novo", "system/etc/novo.conf": "c"},
                      '[[remove]]\nlayer = "system"\npath = "usr/config/emuelec/bin/put_user_bins_here"\n')
        F.apply_to_tree(p, tree)
        self.assertEqual((tree / "usr/bin/busybox").read_text(), "novo")
        self.assertEqual((tree / "etc/novo.conf").read_text(), "c")
        self.assertFalse((tree / "usr/config/emuelec/bin/put_user_bins_here").exists())


class ResizeMarkerTest(TempDirCase):
    def test_feature_brings_marker(self):
        write_feature(self.tmp, "30-ruim", desc(), {"boot/.please_resize_me": ""})
        with self.assertRaises(R36Error) as cm:
            F.plan_layer("boot", F.discover(self.tmp), BOOT_BASE)
        msg = str(cm.exception)
        self.assertIn("'30-ruim'", msg)
        self.assertIn("boot:/.please_resize_me", msg)

    def test_marker_in_base(self):
        with self.assertRaises(R36Error) as cm:
            F.check_resize_marker("p7", {"pasta/.please_resize_me": None}, "a imagem base")
        self.assertIn("a imagem base", str(cm.exception))
        self.assertIn("p7:/pasta/.please_resize_me", str(cm.exception))


class ExampleFeatureTest(unittest.TestCase):
    def test_example_disabled_and_valid(self):
        all_f = F.discover(ROOT / "features")
        ex = next(f for f in all_f if f.id == "00-exemplo")
        self.assertFalse(ex.enabled)
        self.assertNotIn(ex, F.select(all_f))
        for layer in F.LAYERS:
            self.assertTrue(any(ex.layer_dir(layer).rglob("*")), layer)


if __name__ == "__main__":
    unittest.main()
