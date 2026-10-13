import os
import unittest

from context import TempDirCase, mcopy, mkfat
from r36img import fat


class FatTest(TempDirCase):
    def _file(self, name, size):
        p = self.tmp / name
        p.write_bytes(os.urandom(size))
        return p

    def test_fat16_empty(self):
        img = self.tmp / "f16.img"
        mkfat(img, 32, fat=16, extra=["-s", "4"])
        ext = fat.extent(img)
        self.assertEqual(ext.info.fat_type, 16)
        self.assertEqual(ext.info.cluster_bytes, 2048)
        self.assertEqual(ext.last_cluster, 0)
        self.assertEqual(ext.used_end, ext.info.data_start)
        self.assertEqual(ext.root_dir_end, ext.info.fats_end + ext.info.root_entries * 32)
        self.assertGreater(ext.free_clusters, 0)

    def test_fat16_last_cluster(self):
        img = self.tmp / "f16.img"
        mkfat(img, 32, fat=16, extra=["-s", "4"])
        mcopy(img, self._file("a.bin", 100_000))
        ext = fat.extent(img)
        # 100000 bytes = 49 clusters de 2 KiB, a partir do cluster 2
        self.assertEqual(ext.last_cluster, 2 + 49 - 1)
        self.assertEqual(ext.last_cluster_end, ext.info.data_start + 49 * 2048)
        self.assertEqual(ext.used_end, ext.last_cluster_end)

    def test_fat32_extent_and_free(self):
        img = self.tmp / "f32.img"
        mkfat(img, 300, fat=32, extra=["-S", "512"])
        info = fat.read_info(img)
        self.assertEqual(info.fat_type, 32)
        self.assertEqual(info.root_dir_bytes, 0)
        before = fat.extent(img)
        self.assertEqual(before.last_cluster, info.root_cluster)  # só o diretório raiz
        d = self.tmp / "dir"
        d.mkdir()
        (d / "x.bin").write_bytes(os.urandom(3 * 1024 * 1024))
        mcopy(img, d)
        after = fat.extent(img)
        cb = info.cluster_bytes
        self.assertGreaterEqual(after.last_cluster_end - info.data_start, 3 * 1024 * 1024)
        self.assertLess(after.free_clusters, before.free_clusters - (3 * 1024 * 1024) // cb + 1)
        self.assertEqual(fat.align_up(after.used_end, 4 << 20) % (4 << 20), 0)

    def test_hidden_sectors(self):
        img = self.tmp / "h.img"
        mkfat(img, 300, fat=32, extra=["-S", "512", "-h", "4956160"])
        self.assertEqual(fat.read_info(img).hidden_sectors, 4956160)


if __name__ == "__main__":
    unittest.main()
