import json
import lzma
import os
import re
import subprocess
import unittest

from context import CFG, TempDirCase, needs_base, slow
from r36img import build, image, mtools
from r36img.errors import R36Error

NAME_RE = re.compile(r"^r36s_ga36-mb_v1\.2-20260416_build_\d{8}-\d{6}\.img\.xz$")


def skeleton_image(tmp, card_sectors):
    """Imagem esparsa só com bootarea, p5 e p6 (suficiente para a verificação estrutural)."""
    ba = tmp / "bootarea.img"
    ba.write_bytes(image.make_bootarea(CFG, CFG.base_path, card_sectors))
    regions = [(ba, 0, CFG.bootarea_size)]
    for key in ("env", "kernel"):
        p = CFG.part(key)
        regions.append((CFG.base_path, p.offset, p.size))
    img = tmp / "full.img"
    with open(img, "wb") as f:
        f.truncate(card_sectors * 512)
    from r36img.util import copy_region
    for src, off, n in regions:
        copy_region(src, img, src_offset=off if src == CFG.base_path else 0, dst_offset=off, length=n)
    return img


@needs_base
class AssembleTest(TempDirCase):
    card_sectors = 15000 * 2048

    def test_sfdisk_shows_p1_to_last_sector(self):
        img = skeleton_image(self.tmp, self.card_sectors)
        out = subprocess.run(["sfdisk", "-d", str(img)], capture_output=True, text=True, check=True).stdout
        m = re.search(r"img1 : start=\s*(\d+), size=\s*(\d+), type=c", out)
        self.assertIsNotNone(m, out)
        start, size = int(m.group(1)), int(m.group(2))
        self.assertEqual(start, 4956160)
        self.assertEqual(start + size - 1, self.card_sectors - 1)  # 30719999
        self.assertEqual(start + size - 1, 30719999)
        self.assertIn("start=       73728, size=      262144, type=6, bootable", out)
        image.verify_structure(CFG, img, CFG.base_path, self.card_sectors)

    def test_assemble_is_sparse(self):
        img = skeleton_image(self.tmp, self.card_sectors)
        self.assertLess(os.stat(img).st_blocks * 512, 200 * 1024 * 1024)

    def test_uboot_byte_change_fails(self):
        img = skeleton_image(self.tmp, self.card_sectors)
        with open(img, "r+b") as f:
            f.seek(38192 * 512 + 100)
            b = f.read(1)
            f.seek(-1, 1)
            f.write(bytes([b[0] ^ 0xFF]))
        with self.assertRaises(R36Error) as cm:
            image.verify_structure(CFG, img, CFG.base_path, self.card_sectors)
        self.assertIn("38192", str(cm.exception))

    def test_other_mbr_entry_change_fails(self):
        img = skeleton_image(self.tmp, self.card_sectors)
        with open(img, "r+b") as f:
            f.seek(0x1CE + 12)  # tamanho da p2
            f.write((131072).to_bytes(4, "little"))
        with self.assertRaises(R36Error) as cm:
            image.verify_structure(CFG, img, CFG.base_path, self.card_sectors)
        self.assertIn("entrada 2 do MBR", str(cm.exception))

    def test_p5_change_fails(self):
        img = skeleton_image(self.tmp, self.card_sectors)
        with open(img, "r+b") as f:
            f.seek(CFG.part("env").offset + 10)
            f.write(b"X")
        with self.assertRaises(R36Error) as cm:
            image.verify_structure(CFG, img, CFG.base_path, self.card_sectors)
        self.assertIn("p5 (env) difere", str(cm.exception))


@needs_base
class OutputDirTest(TempDirCase):
    def test_existing_dir_untouched(self):
        out = self.tmp / "out"
        (out / "20261013-153045").mkdir(parents=True)
        marker = out / "20261013-153045" / "manifest.json"
        marker.write_text("original")
        before = os.stat(marker).st_mtime_ns
        with self.assertRaises(R36Error) as cm:
            build.build(CFG, none=True, timestamp="20261013-153045", out_root=out, work_root=self.tmp / "work")
        self.assertIn("já existe", str(cm.exception))
        self.assertEqual(marker.read_text(), "original")
        self.assertEqual(os.stat(marker).st_mtime_ns, before)
        self.assertEqual(os.listdir(out / "20261013-153045"), ["manifest.json"])


@needs_base
@slow
class FullBuildTest(TempDirCase):
    """6.3: build completo com tamanho mínimo e a feature de exemplo."""

    def test_outputs(self):
        ts = "20261013-153045"
        out_dir = build.build(CFG, size_mib=7000, names=["00-exemplo"], timestamp=ts,
                              out_root=self.tmp / "out", work_root=self.tmp / "work")
        self.assertEqual(out_dir.name, ts)
        manifest = json.loads((out_dir / "manifest.json").read_text())
        name = manifest["image"]["file"]
        self.assertRegex(name, NAME_RE)
        self.assertEqual(name, f"r36s_ga36-mb_v1.2-20260416_build_{ts}.img.xz")
        self.assertEqual(manifest["timestamp"], ts)
        self.assertTrue((out_dir / name).is_file())
        for part in ("bootarea", "boot", "env", "kernel", "system", "storage", "roms"):
            self.assertTrue((out_dir / "parts" / f"{part}.img").is_file(), part)
        self.assertEqual(os.path.getsize(out_dir / "parts/boot.img"), 16 * 1024 * 1024)
        # R36-BUILD.txt na p7 igual ao manifest
        txt = subprocess.run(["mtype", "-i", str(out_dir / "parts/system.img"), "::/R36-BUILD.txt"],
                             capture_output=True, text=True, check=True, env=dict(os.environ, **mtools.ENV)).stdout
        self.assertEqual(txt, manifest["build_info"]["text"])
        self.assertIn(f"imagem: r36s_ga36-mb_v1.2-20260416_build_{ts}.img.xz", txt)
        self.assertNotIn("timestamp:", txt)
        self.assertIn("00-exemplo", txt)
        self.assertEqual([f["id"] for f in manifest["features"]], ["00-exemplo"])
        changes = (out_dir / "changes.txt").read_text()
        for layer in ("[system]", "[storage]", "[roms]", "[boot]"):
            self.assertIn(layer, changes)
        self.assertIn("/usr/share/r36-exemplo/LEIA-ME.txt  feature=00-exemplo  -rw-r--r-- 0/0", changes)
        # a imagem comprimida descomprime para o tamanho do cartão com o sha256 do manifest
        import hashlib
        h, n = hashlib.sha256(), 0
        with lzma.open(out_dir / name) as f:
            for buf in iter(lambda: f.read(1 << 22), b""):
                h.update(buf)
                n += len(buf)
        self.assertEqual(n, 7000 * 1024 * 1024)
        self.assertEqual(h.hexdigest(), manifest["image"]["sha256_uncompressed"])


if __name__ == "__main__":
    unittest.main()
