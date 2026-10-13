import struct
import unittest

from context import CFG, needs_base
from r36img import layout
from r36img.errors import R36Error


def entry(status, type_, start, sectors, chs_s=b"\x00\x01\x00", chs_e=b"\x10\x20\x30"):
    return bytes([status]) + chs_s + bytes([type_]) + chs_e + struct.pack("<II", start, sectors)


def synthetic_disk():
    """MBR + 2 EBRs: p1 primária no fim, p2 FAT16, p3 estendida com p5 e p6."""
    disk = bytearray(512 * 8)
    mbr = bytearray(512)
    mbr[0:4] = b"\xfa\x33\xc0\x8e"  # "código de boot"
    mbr[0x1B8:0x1BC] = b"\x77\x9b\x5d\x81"
    mbr[0x1BE:0x1CE] = entry(0, 0x0C, 1000, 500, b"\x81\x4e\x34", b"\x9a\x7a\x3f")
    mbr[0x1CE:0x1DE] = entry(0x80, 0x06, 100, 200)
    mbr[0x1DE:0x1EE] = entry(0, 0x85, 1, 999)
    mbr[510:512] = layout.SIG
    disk[0:512] = mbr
    # EBR @1: p5 em 300 (rel 299), próximo EBR em ext+1 = 2
    e1 = bytearray(512)
    e1[0x1BE:0x1CE] = entry(0, 0x83, 299, 50)
    e1[0x1CE:0x1DE] = entry(0, 0x85, 1, 900)
    e1[510:512] = layout.SIG
    disk[512:1024] = e1
    # EBR @2: p6 em 400 (rel 398), link para EBR @3 sem assinatura (quirk)
    e2 = bytearray(512)
    e2[0x1BE:0x1CE] = entry(0, 0x83, 398, 60)
    e2[0x1CE:0x1DE] = entry(0, 0x85, 2, 800)
    e2[510:512] = layout.SIG
    disk[1024:1536] = e2
    return bytes(disk)


class SyntheticMbrTest(unittest.TestCase):
    def setUp(self):
        self.disk = synthetic_disk()
        self.read = lambda off, n: self.disk[off:off + n]

    def test_parse_mbr_and_ebrs(self):
        s0, entries, logicals = layout.read_layout(self.read)
        self.assertEqual([(e.type, e.start, e.sectors) for e in entries[:3]],
                         [(0x0C, 1000, 500), (0x06, 100, 200), (0x85, 1, 999)])
        self.assertTrue(entries[3].empty)
        self.assertEqual([(lg.number, lg.start, lg.sectors) for lg in logicals],
                         [(5, 300, 50), (6, 400, 60)])

    def test_set_p1_changes_only_entry1(self):
        s0 = self.disk[:512]
        new = layout.set_p1(s0, 1000, 123456)
        changed = [i for i in range(512) if s0[i] != new[i]]
        self.assertTrue(all(0x1BE <= i < 0x1CE for i in changed), changed)
        e = layout.parse_mbr(new)[0]
        self.assertEqual((e.start, e.sectors, e.type, e.status), (1000, 123456, 0x0C, 0))
        self.assertEqual(e.chs_end, b"\xfe\xff\xff")
        self.assertEqual(e.chs_start, b"\x81\x4e\x34")
        self.assertEqual(layout.parse_mbr(new)[1:], layout.parse_mbr(s0)[1:])

    def test_replace_p1_entry_roundtrip(self):
        s0 = self.disk[:512]
        other = layout.set_p1(s0, 1000, 42)
        back = layout.replace_p1_entry(other, layout.p1_entry_bytes(s0))
        self.assertEqual(back, s0)

    def test_invalid_mbr(self):
        with self.assertRaises(R36Error):
            layout.parse_mbr(bytes(512))

    def test_softw411_synthetic(self):
        data = bytearray(layout.SOFTW411_SIZE)
        struct.pack_into("<I", data, 4, 0x200)
        data[8:16] = layout.SOFTW411_MAGIC
        struct.pack_into("<IIII", data, 16, 4, 0, 2, 0)
        for i, (name, addr, ln) in enumerate([("boot", 0x8000, 0x10000), ("UDISK", 0x20000, 0)]):
            o = 0x20 + i * 128
            struct.pack_into("<IIII", data, o, 0, addr, 0, ln)
            data[o + 16:o + 20] = b"DISK"
            data[o + 32:o + 32 + len(name)] = name.encode()
        import zlib
        struct.pack_into("<I", data, 0, zlib.crc32(bytes(data[4:])))
        sw = layout.parse_softw411(bytes(data))
        self.assertTrue(sw.crc_ok)
        self.assertEqual([(p.name, p.addr, p.length) for p in sw.parts],
                         [("boot", 0x8000, 0x10000), ("UDISK", 0x20000, 0)])


@needs_base
class BaseLayoutTest(unittest.TestCase):
    """Somente leitura na base real: reproduz a tabela do design."""

    def read(self, off, n):
        with open(CFG.base_path, "rb") as f:
            f.seek(off)
            return f.read(n)

    def test_design_table(self):
        s0, entries, logicals = layout.read_layout(self.read)
        self.assertEqual((entries[0].type, entries[0].start, entries[0].sectors), (0x0C, 4956160, 178335))
        self.assertEqual((entries[1].type, entries[1].start, entries[1].sectors, entries[1].status),
                         (0x06, 73728, 262144, 0x80))
        self.assertEqual((entries[2].type, entries[2].start, entries[2].sectors), (0x85, 1, 4956160))
        self.assertTrue(entries[3].empty)
        self.assertEqual([(lg.number, lg.start, lg.sectors, lg.ebr_sector) for lg in logicals], [
            (5, 139264, 32768, 1), (6, 172032, 65536, 2), (7, 237568, 1572864, 3), (8, 1810432, 3145728, 4),
        ])
        # cada partição do config bate com a base
        for key in ("boot", "env", "kernel", "system", "storage", "roms"):
            p = CFG.part(key)
            got = {e.index: e for e in entries} | {lg.number: lg for lg in logicals}
            self.assertEqual((got[p.number].start, got[p.number].sectors), (p.start, p.sectors), key)

    def test_ebr4_points_to_empty_sector5(self):
        self.assertNotEqual(self.read(5 * 512 + 510, 2), layout.SIG)

    def test_softw411(self):
        sw = layout.parse_softw411(self.read(CFG.softw411_sector * 512, layout.SOFTW411_SIZE))
        self.assertTrue(sw.crc_ok)
        got = [(p.name, p.absolute_start(CFG.softw411_sector), p.length) for p in sw.parts]
        self.assertEqual(got, [
            ("bootloader", 73728, 65536),
            ("env", 139264, 32768),
            ("boot", 172032, 65536),
            ("rootfs", 237568, 1572864),
            ("storage", 1810432, 3145728),
            ("UDISK", 4956160, 0),
        ])


if __name__ == "__main__":
    unittest.main()
