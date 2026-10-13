import hashlib
import io
import tarfile
import threading
import unittest
from pathlib import Path
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

from context import TempDirCase
from r36img import external as X
from r36img import features as F
from r36img.errors import R36Error
from test_features import STORAGE_BASE, desc, write_feature


def make_tar(path, members):
    """members: [(nome, dados | None p/ diretório | ('link', alvo) | ('dev',))]."""
    with tarfile.open(path, "w:gz") as t:
        for name, data in members:
            ti = tarfile.TarInfo(name)
            if data is None:
                ti.type = tarfile.DIRTYPE
                ti.mode = 0o755
                t.addfile(ti)
            elif isinstance(data, tuple) and data[0] == "link":
                ti.type = tarfile.SYMTYPE
                ti.linkname = data[1]
                t.addfile(ti)
            elif isinstance(data, tuple) and data[0] == "dev":
                ti.type = tarfile.CHRTYPE
                t.addfile(ti)
            else:
                ti.size = len(data)
                ti.mode = 0o644
                t.addfile(ti, io.BytesIO(data))
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ext_toml(url, sha, dest="themes/T", extra="", layer="storage"):
    return (f'[[external]]\nlayer = "{layer}"\ndest = "{dest}"\nurl = "{url}"\nsha256 = "{sha}"\n{extra}\n')


class DescriptorExternalTest(TempDirCase):
    SHA = "a" * 64

    n = 0

    def load(self, toml):
        self.n += 1
        return F.load_feature(write_feature(self.tmp, f"10-t{self.n}", desc(extra=toml)))

    def test_valid(self):
        f = self.load(ext_toml("https://x/y.tar.gz", self.SHA, extra='strip = 1\nexclude = ["*.md"]')
                      + "\n")
        x = f.externals[0]
        self.assertEqual((x.layer, x.dest, x.strip, x.exclude), ("storage", "themes/T", 1, ("*.md",)))

    def test_budget_needs_external(self):
        with self.assertRaises(R36Error):
            self.load("budget_mib = 10\n")

    def test_missing_field(self):
        with self.assertRaises(R36Error) as cm:
            self.load('[[external]]\nlayer = "storage"\ndest = "a"\nurl = "https://x/y"\n')
        self.assertIn("sha256", str(cm.exception))

    def test_bad_layer(self):
        with self.assertRaises(R36Error) as cm:
            self.load(ext_toml("https://x/y", self.SHA, layer="kernel"))
        self.assertIn("kernel", str(cm.exception))

    def test_bad_sha(self):
        for bad in ("abc", "A" * 64, "g" * 64):
            with self.assertRaises(R36Error, msg=bad):
                self.load(ext_toml("https://x/y", bad))

    def test_bad_url_and_unknown_key(self):
        with self.assertRaises(R36Error):
            self.load(ext_toml("ftp://x/y", self.SHA))
        with self.assertRaises(R36Error):
            self.load(ext_toml("https://x/y", self.SHA, extra="foo = 1\n"))


class ServerCase(TempDirCase):
    def setUp(self):
        super().setUp()
        self.srv_dir = self.tmp / "srv"
        self.srv_dir.mkdir()
        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self, *a, **k):
                pass

        handler = partial(Quiet, directory=str(self.srv_dir))
        self.httpd = HTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.cache = self.tmp / "cache"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        super().tearDown()

    def feature(self, members, extra="", name="t.tar.gz", sha=None, fid="50-t", top=""):
        self.nf = getattr(self, "nf", 0) + 1
        d0 = self.tmp / f"features{self.nf}"
        real = make_tar(self.srv_dir / name, members)
        toml = top + ext_toml(f"{self.base_url}/{name}", sha or real, extra=extra)
        d = write_feature(d0, fid, desc(order=50, extra=toml))
        return F.load_feature(d), real


class FetchTest(ServerCase):
    def test_download_and_cache_reuse(self):
        f, sha = self.feature([("a", b"1")])
        p = X.fetch(f, f.externals[0], self.cache)
        self.assertEqual(p, self.cache / f"{sha}.tar.gz")
        self.assertEqual(list(self.cache.glob(".*")), [])  # sem temporário
        self.httpd.shutdown()
        self.httpd.server_close()
        self.assertEqual(X.fetch(f, f.externals[0], self.cache), p)  # sem rede

    def test_sha_mismatch(self):
        f, real = self.feature([("a", b"1")], sha="0" * 64)
        with self.assertRaises(R36Error) as cm:
            X.fetch(f, f.externals[0], self.cache)
        msg = str(cm.exception)
        self.assertIn("50-t", msg)
        self.assertIn(f"{self.base_url}/t.tar.gz", msg)
        self.assertIn("0" * 64, msg)
        self.assertIn(real, msg)
        self.assertEqual(list(self.cache.iterdir()), [])

    def test_offline_without_cache(self):
        f, _ = self.feature([("a", b"1")])
        with self.assertRaises(R36Error) as cm:
            X.prepare([f], self.cache, self.tmp / "stage", offline=True)
        self.assertIn(f"{self.base_url}/t.tar.gz", str(cm.exception))

    def test_offline_with_cache(self):
        f, _ = self.feature([("top/", None), ("top/a", b"1")], extra="strip = 1\n")
        X.prepare([f], self.cache, self.tmp / "s1")
        self.httpd.shutdown()
        self.httpd.server_close()
        X.prepare([f], self.cache, self.tmp / "s2", offline=True)
        self.assertEqual((self.tmp / "s2" / "50-t" / "1" / "a").read_bytes(), b"1")


class ExtractTest(ServerCase):
    def prep(self, members, extra=""):
        f, _ = self.feature(members, extra=extra)
        X.prepare([f], self.cache, self.tmp / f"stage{self.nf}")
        return f

    def test_strip_and_exclude(self):
        f = self.prep([("T-abc", None), ("T-abc/theme.xml", b"<t/>"), ("T-abc/README.md", b"r"),
                       ("T-abc/art", None), ("T-abc/art/a.png", b"png"), ("T-abc/shots", None),
                       ("T-abc/shots/s.png", b"s")], extra='strip = 1\nexclude = ["*.md", "shots/*"]\n')
        tree = f.staged[0][1]
        self.assertTrue((tree / "theme.xml").is_file())
        self.assertTrue((tree / "art" / "a.png").is_file())
        self.assertFalse((tree / "README.md").exists())
        self.assertFalse((tree / "shots" / "s.png").exists())

    def test_refused_entries(self):
        for members in ([("../../etc/passwd", b"x")],
                        [("a/b", ("link", "/etc/passwd"))],
                        [("dev", ("dev",))]):
            with self.assertRaises(R36Error, msg=str(members)) as cm:
                self.prep(members)
            self.assertIn("50-t", str(cm.exception))
            self.assertIn("recusada", str(cm.exception))

    def test_plan_merges_under_dest(self):
        f = self.prep([("T", None), ("T/theme.xml", b"<t/>"), ("T/art", None), ("T/art/a.png", b"png")],
                      extra="strip = 1\n")
        base = dict(STORAGE_BASE)
        plan = F.plan_layer("storage", [f], base)
        self.assertEqual(plan.final["themes"].type, "d")
        self.assertEqual(plan.final["themes/T/art/a.png"].type, "-")
        self.assertEqual(plan.final["themes/T/theme.xml"].mode, 0o644)
        self.assertEqual(plan.final["themes/T/theme.xml"].uid, 0)
        c = next(c for c in plan.changes if c.path == "themes/T/theme.xml")
        self.assertEqual((c.op, c.feature), ("added", "50-t"))

    def test_conflict_with_other_feature(self):
        f = self.prep([("theme.xml", b"<t/>")])
        other = F.load_feature(write_feature(self.tmp / "features", "20-o", desc(order=20),
                                             {"storage/themes/T/theme.xml": "x"}))
        base = dict(STORAGE_BASE)
        with self.assertRaises(R36Error) as cm:
            F.plan_layer("storage", [other, f], base)
        self.assertIn("conflito", str(cm.exception))


class BudgetTest(ServerCase):
    def test_within_budget_and_report(self):
        f, _ = self.feature([("a", b"x" * 1000)], top="budget_mib = 1\n")
        X.prepare([f], self.cache, self.tmp / "stage")
        self.assertEqual(f.staged[0][2], 1000)
        plan = F.plan_layer("storage", [f], dict(STORAGE_BASE))
        text = F.report({"storage": plan}, [f])
        self.assertIn("total de 50-t (limite 1 MiB)", text)
        self.assertIn(f"{self.base_url}/t.tar.gz", text)

    def test_over_budget(self):
        f, _ = self.feature([("a", b"x" * (2 * X.MIB))], top="budget_mib = 1\n")
        with self.assertRaises(R36Error) as cm:
            X.prepare([f], self.cache, self.tmp / "stage")
        self.assertIn("passa do orçamento", str(cm.exception))
        self.assertIn("themes/T", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
