import hashlib
import io
import json
import shutil
import subprocess
import threading
import unittest
import zipfile
import zlib
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

from context import CFG, ROOT, TempDirCase, needs_base
from r36img import cores as C
from r36img import external as X
from r36img import mtools
from r36img.errors import R36Error

RECEITA = ROOT / "cores" / "snes9x2005_plus" / "receita.toml"

# Saída de `LC_ALL=C readelf -h -A -d -V -S --dyn-syms -W` de um core compatível (resumida).
READELF_OK = """\
ELF Header:
  Class:                             ELF32
  Machine:                           ARM
Section Headers:
  [Nr] Name              Type            Addr     Off    Size   ES Flg Lk Inf Al
  [ 1] .dynsym           DYNSYM          00000114 000114 000330 10   A  2   1  4
  [11] .text             PROGBITS        00008968 008968 06d640 00  AX  0   0  8
Dynamic section at offset 0x78f08 contains 26 entries:
 0x00000001 (NEEDED)                     Shared library: [libc.so.6]
Symbol table '.dynsym' contains 51 entries:
   Num:    Value  Size Type    Bind   Vis      Ndx Name
     1: 00000000     0 FUNC    GLOBAL DEFAULT  UND __isoc99_sscanf@GLIBC_2.7 (2)
     2: 00000000     0 FUNC    GLOBAL DEFAULT  UND memcpy@GLIBC_2.4 (3)
    24: 0006ee9c     8 FUNC    GLOBAL DEFAULT   11 retro_api_version
    49: 0006f2a4   636 FUNC    GLOBAL DEFAULT   11 retro_run
Version needs section '.gnu.version_r' contains 1 entry:
  000000: Version: 1  File: libc.so.6  Cnt: 2
  0x0010:   Name: GLIBC_2.7  Flags: none  Version: 2
  0x0020:   Name: GLIBC_2.4  Flags: none  Version: 3
Attribute Section: aeabi
File Attributes
  Tag_CPU_name: "7-A"
  Tag_CPU_arch: v7
  Tag_FP_arch: VFPv4
  Tag_Advanced_SIMD_arch: NEONv1 with Fused-MAC
  Tag_ABI_VFP_args: VFP registers
"""
LIBS = C.LIBS_BASE_PADRAO


def extrai_da_base(dest, caminho):
    sq = dest.parent / "SYSTEM"
    if not sq.exists():
        subprocess.run(
            ["mcopy", "-n", "-i", mtools.spec(CFG.base_path, CFG.part("system").offset), "::/SYSTEM", str(sq)],
            check=True, env=mtools.ENV, capture_output=True)
    dest.write_bytes(subprocess.run(["unsquashfs", "-cat", str(sq), caminho], check=True, capture_output=True).stdout)
    return dest


def raiz_com_receita(tmp, url=None, sha=None):
    """Uma raiz de repositório mínima em tmp com a receita do snes9x2005_plus."""
    d = tmp / "repo" / "cores" / "snes9x2005_plus"
    d.mkdir(parents=True)
    txt = RECEITA.read_text(encoding="utf-8")
    if url:
        rec = C.carregar("snes9x2005_plus", ROOT / "cores")
        txt = txt.replace(f'url = "{rec.url}"', f'url = "{url}"').replace(rec.sha256, sha)
    (d / "receita.toml").write_text(txt, encoding="utf-8")
    return tmp / "repo"


class Receita(TempDirCase):
    def setUp(self):
        super().setUp()
        self.rec = C.carregar("snes9x2005_plus")

    def escreve(self, troca):
        d = self.tmp / "cores" / "snes9x2005_plus"
        d.mkdir(parents=True, exist_ok=True)
        txt = RECEITA.read_text(encoding="utf-8")
        for a, b in troca:
            self.assertIn(a, txt)
            txt = txt.replace(a, b)
        (d / "receita.toml").write_text(txt, encoding="utf-8")
        return C.carregar("snes9x2005_plus", self.tmp / "cores")

    def test_receita_do_repositorio(self):
        r = self.rec
        self.assertEqual(r.commit, "fd45b0e055bce6cff3acde77414558784e93e7d0")
        self.assertEqual(r.sha256, "a400aa12955b8aa6f877d2d0fb852d17b76121a4730858e349ed434ea56e8f05")
        self.assertIn(r.commit, r.url)
        self.assertEqual(r.make, ("USE_BLARGG_APU=1", "platform=armv8-hardfloat-neon"))
        self.assertEqual(list(r.variantes), ["o2", "o3", "pgo_treino", "pgo"])
        self.assertEqual({v.nome for v in r.variantes.values()},
                         {"snes9x2005_plus_a33"} | {f"snes9x2005_plus_a33_{x}" for x in ("o3", "pgo_treino", "pgo")})
        self.assertEqual(r.pgo_dir, "/storage/roms/pgo/snes9x2005_plus")
        for f in ("-marm", "-mcpu=cortex-a7", "-mfpu=neon-vfpv4", "-mfloat-abi=hard", "-DNDEBUG",
                  "-ffunction-sections", "-fdata-sections"):
            self.assertIn(f, r.comuns)
        self.assertTrue(any(f.startswith("-flto") for f in r.comuns))
        self.assertEqual(r.ligacao, ("-Wl,--gc-sections", "-Wl,-O1", "-s"))

    def test_flags_por_variante(self):
        r = self.rec
        for vid, nivel in (("o2", "-O2"), ("o3", "-O3")):
            todas, lig = C.flags(r, C.variante(r, vid))
            self.assertEqual(todas[:len(r.comuns)], list(r.comuns))
            self.assertEqual(C.nivel_o(todas), nivel)
            self.assertEqual(lig, list(r.ligacao))

    def test_variante_desconhecida_lista_as_validas(self):
        with self.assertRaises(R36Error) as cm:
            C.variante(self.rec, "o4")
        msg = str(cm.exception)
        self.assertIn("o4", msg)
        self.assertIn("o2, o3, pgo_treino, pgo", msg)

    def test_pgo_sem_base_da_erro_claro(self):
        r = self.escreve([('base = "o2"', 'base = ""')])
        for vid in ("pgo_treino", "pgo"):
            with self.assertRaises(R36Error) as cm:
                C.variante(r, vid)
            self.assertIn("base", str(cm.exception))
            self.assertIn("o2, o3", str(cm.exception))

    def test_pgo_da_receita_usa_o2(self):
        for vid in ("pgo_treino", "pgo"):
            todas, _ = C.flags(self.rec, C.variante(self.rec, vid))
            self.assertEqual(C.nivel_o(todas), "-O2", vid)

    def test_pgo_com_base(self):
        r = self.escreve([('base = "o2"', 'base = "o3"')])
        todas, _ = C.flags(r, C.variante(r, "pgo"))
        self.assertEqual(C.nivel_o(todas), "-O3")
        self.assertLess(todas.index("-O3"), todas.index("-fprofile-use=/storage/roms/pgo/snes9x2005_plus"))
        for f in ("-fprofile-partial-training", "-Werror=missing-profile", "-Werror=coverage-mismatch"):
            self.assertIn(f, todas)
        treino, _ = C.flags(r, C.variante(r, "pgo_treino"))
        self.assertIn("-fprofile-generate=/storage/roms/pgo/snes9x2005_plus", treino)

    def test_base_precisa_ser_variante_sem_pgo(self):
        with self.assertRaises(R36Error) as cm:
            self.escreve([('base = "o2"', 'base = "pgo"')])
        self.assertIn("base", str(cm.exception))

    def test_commit_curto_recusado(self):
        with self.assertRaises(R36Error) as cm:
            self.escreve([('commit = "fd45b0e055bce6cff3acde77414558784e93e7d0"', 'commit = "fd45b0e"')])
        self.assertIn("40 hexadecimais", str(cm.exception))

    def test_receita_ausente(self):
        with self.assertRaises(R36Error) as cm:
            C.carregar("nao_existe")
        self.assertIn("receita não encontrada", str(cm.exception))

    def test_versao(self):
        r = self.rec
        self.assertEqual(C.git_version(r, r.variantes["o3"]), '" fd45b0e a33-o3"')
        self.assertEqual(C.git_version(r, r.variantes["pgo_treino"]), '" fd45b0e a33-pgo-treino"')


class Fonte(TempDirCase):
    def setUp(self):
        super().setUp()
        self.srv = self.tmp / "srv"
        self.srv.mkdir()

        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self, *a, **k):
                pass

        self.httpd = HTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(self.srv)))
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        commit = "fd45b0e055bce6cff3acde77414558784e93e7d0"  # a receita exige o commit na URL
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/{commit}.tar.gz"
        (self.srv / f"{commit}.tar.gz").write_bytes(b"conteudo do fonte")
        self.sha = hashlib.sha256(b"conteudo do fonte").hexdigest()

    def tearDown(self):
        self.para_servidor()
        super().tearDown()

    def para_servidor(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None

    def test_sha256_divergente_falha_sem_gerar_binario(self):
        root = raiz_com_receita(self.tmp, self.url, "0" * 64)
        with self.assertRaises(R36Error) as cm:
            C.compilar("snes9x2005_plus", "o2", root=root)
        self.assertIn("sha256 divergente", str(cm.exception))
        self.assertFalse((root / "features").exists())
        self.assertFalse((root / "cores" / "snes9x2005_plus" / "builds.jsonl").exists())
        self.assertEqual(list((root / "work" / "cache" / "cores").iterdir()), [])

    def test_cache_reaproveitado_sem_rede(self):
        cache = self.tmp / "cache"
        p = X.download("core 'x'", self.url, self.sha, cache)
        self.assertEqual(p, cache / f"{self.sha}.tar.gz")
        self.para_servidor()
        self.assertEqual(X.download("core 'x'", "http://127.0.0.1:9/inexistente.tar.gz", self.sha, cache), p)

    def test_cache_corrompido(self):
        cache = self.tmp / "cache"
        cache.mkdir()
        (cache / f"{self.sha}.tar.gz").write_bytes(b"outra coisa")
        with self.assertRaises(R36Error) as cm:
            X.download("core 'x'", self.url, self.sha, cache)
        self.assertIn("corrompido", str(cm.exception))


class Abi(unittest.TestCase):
    def problemas(self, *troca):
        txt = READELF_OK
        for a, b in troca:
            self.assertIn(a, txt)
            txt = txt.replace(a, b)
        return C.problemas_abi(txt, LIBS)

    def test_compativel(self):
        self.assertEqual(self.problemas(), [])

    def test_glibc_nova(self):
        p = self.problemas(("Name: GLIBC_2.7", "Name: GLIBC_2.38"))
        self.assertEqual(len(p), 1)
        self.assertIn("GLIBC_2.38", p[0])

    def test_glibc_no_limite(self):
        self.assertEqual(self.problemas(("Name: GLIBC_2.7", "Name: GLIBC_2.36")), [])

    def test_glibcxx_nova(self):
        p = self.problemas(("Name: GLIBC_2.4", "Name: GLIBCXX_3.4.30"))
        self.assertTrue(any("GLIBCXX_3.4.30" in x for x in p))
        self.assertEqual(self.problemas(("Name: GLIBC_2.4", "Name: GLIBCXX_3.4.29")), [])

    def test_biblioteca_ausente_na_base(self):
        p = self.problemas(("Shared library: [libc.so.6]", "Shared library: [libfoo.so.1]"))
        self.assertTrue(any("libfoo.so.1" in x for x in p))

    def test_sem_hard_float(self):
        p = self.problemas(("  Tag_ABI_VFP_args: VFP registers\n", ""))
        self.assertTrue(any("hard-float" in x for x in p))

    def test_isa_errada(self):
        self.assertTrue(self.problemas(("Tag_CPU_arch: v7", "Tag_CPU_arch: v6")))
        self.assertTrue(self.problemas(("Tag_FP_arch: VFPv4", "Tag_FP_arch: VFPv3")))
        self.assertTrue(self.problemas(("Machine:                           ARM", "Machine: AArch64")))

    def test_retro_em_thumb(self):
        p = self.problemas(("0006f2a4   636 FUNC", "0006f2a5   636 FUNC"))
        self.assertTrue(any("Thumb" in x and "retro_run" in x for x in p))

    def test_secao_de_depuracao(self):
        p = self.problemas(("  [11] .text", "  [12] .debug_info        PROGBITS        00000000 000000 000010 00      0   0  1\n  [11] .text"))
        self.assertTrue(any(".debug_info" in x for x in p))

    @needs_base
    def test_core_da_base_passa(self):
        tmp = ROOT / "work" / "tests" / "abi-base"
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        try:
            so = extrai_da_base(tmp / "base.so", "usr/lib/libretro/snes9x2005_plus_libretro.so")
            libs = C.libs_base(work=tmp)
            self.assertLessEqual(LIBS, libs)
            self.assertEqual(C.problemas_abi(C.readelf(so), libs), [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class Log(unittest.TestCase):
    def test_resumo_do_log(self):
        texto = (
            "arm-linux-gnueabihf-gcc -fPIC -O2 -c -osource/c4.o source/c4.c -marm -O3\n"
            "arm-linux-gnueabihf-gcc -fPIC -O2 -c -o libretro.o libretro.c -marm -O3\n"
            "arm-linux-gnueabihf-gcc -fPIC -shared -o x.so source/c4.o libretro.o -marm -O3 -s\n"
        )
        niveis, objetos, ligacao = C.resumo_log(texto)
        self.assertEqual(niveis, ["-O3"])
        self.assertEqual(objetos, ["libretro.o", "source/c4.o"])
        self.assertTrue(ligacao.endswith("-O3 -s"))
        niveis, _, _ = C.resumo_log(texto.replace("-marm -O3\n", "-marm -O3 -O2\n", 1))
        self.assertEqual(niveis, ["-O2", "-O3"])

    def test_gcda_do_binario(self):
        so = ROOT / "work" / "tests" / "gcda.so"
        so.parent.mkdir(parents=True, exist_ok=True)
        try:
            so.write_bytes(b"\x00\x7fELF\x00/storage/roms/pgo/x/#build#src#source#cpu.gcda\x00lixo\x00"
                           b"/storage/roms/pgo/x/#build#src#libretro.gcda\x00")
            self.assertEqual(C.gcda_do_binario(so), ["/storage/roms/pgo/x/#build#src#libretro.gcda",
                                                     "/storage/roms/pgo/x/#build#src#source#cpu.gcda"])
        finally:
            so.unlink(missing_ok=True)


class Verificar(TempDirCase):
    @needs_base
    def test_binario_com_registro(self):
        root = raiz_com_receita(self.tmp)
        rec = C.carregar("snes9x2005_plus", root / "cores")
        dst = C.feature_dir(root) / C.LIBRETRO / C.nome_so(rec.variantes["o2"])
        dst.parent.mkdir(parents=True)
        extrai_da_base(dst, "usr/lib/libretro/snes9x2005_plus_libretro.so")
        sha = hashlib.sha256(dst.read_bytes()).hexdigest()
        reg = root / "cores" / "snes9x2005_plus" / "builds.jsonl"
        reg.write_text(json.dumps({"variante": "o2", "sha256": "1" * 64}) + "\n"
                       + json.dumps({"variante": "o2", "sha256": sha}) + "\n")
        C.verificar("snes9x2005_plus", root=root, libs=LIBS)
        reg.write_text(json.dumps({"variante": "o2", "sha256": sha}) + "\n"
                       + json.dumps({"variante": "o2", "sha256": "1" * 64}) + "\n")
        with self.assertRaises(R36Error) as cm:
            C.verificar("snes9x2005_plus", root=root, libs=LIBS)
        self.assertIn("último registro", str(cm.exception))
        reg.unlink()
        with self.assertRaises(R36Error) as cm:
            C.verificar(root=root, libs=LIBS)
        self.assertIn("sem registro", str(cm.exception))

    def test_sem_binarios(self):
        root = raiz_com_receita(self.tmp)
        C.verificar(root=root, libs=LIBS)


class Perfil(TempDirCase):
    GCDA = ["/storage/roms/pgo/snes9x2005_plus/#build#src#libretro.gcda",
            "/storage/roms/pgo/snes9x2005_plus/#build#src#source#cpu.gcda"]

    def setUp(self):
        super().setUp()
        self.root = raiz_com_receita(self.tmp)
        self.cdir = self.root / "cores" / "snes9x2005_plus"
        (self.cdir / "builds.jsonl").write_text(
            json.dumps({"variante": "o3", "sha256": "3" * 64}) + "\n"
            + json.dumps({"variante": "pgo_treino", "sha256": "7" * 64, "gcda": self.GCDA}) + "\n")
        self.origem = self.tmp / "cartao" / "pgo" / "snes9x2005_plus"
        self.origem.mkdir(parents=True)

    def grava(self, *nomes):
        for n in nomes:
            (self.origem / n).write_bytes(n.encode())

    def test_importa_um_por_objeto(self):
        self.grava("#build#src#libretro.gcda", "#build#src#source#cpu.gcda", "#outro.gcda")
        (self.cdir / "pgo").mkdir()
        (self.cdir / "pgo" / "#velho.gcda").write_bytes(b"x")
        arquivos = C.perfil("snes9x2005_plus", self.origem, root=self.root)
        self.assertEqual(sorted(arquivos), ["#build#src#libretro.gcda", "#build#src#source#cpu.gcda"])
        self.assertEqual(sorted(p.name for p in (self.cdir / "pgo").glob("*.gcda")), sorted(arquivos))
        info = json.loads((self.cdir / "pgo" / "perfil.json").read_text())
        self.assertEqual(info["treino"], {"variante": "pgo_treino", "sha256": "7" * 64})
        self.assertEqual(info["arquivos"]["#build#src#libretro.gcda"],
                         hashlib.sha256(b"#build#src#libretro.gcda").hexdigest())

    def test_falta_gcda(self):
        self.grava("#build#src#libretro.gcda")
        with self.assertRaises(R36Error) as cm:
            C.perfil("snes9x2005_plus", self.origem, root=self.root)
        self.assertIn("#build#src#source#cpu.gcda", str(cm.exception))
        self.assertFalse((self.cdir / "pgo").exists())

    def test_sem_build_de_treino(self):
        (self.cdir / "builds.jsonl").write_text(json.dumps({"variante": "o3", "sha256": "3" * 64}) + "\n")
        with self.assertRaises(R36Error) as cm:
            C.perfil("snes9x2005_plus", self.origem, root=self.root)
        self.assertIn("instrumentado", str(cm.exception))


CSV = """\
date,uptime_s,boot,temp_cpu,temp_gpu,cpu_mhz,cpu_max_mhz,governor,cpus_online,cpu0,cpu1,cpu2,cpu3,dram_scene,dram_mhz,bat_status,bat_pct,bat_voltage,system,emulator,core,rom
2026-10-18 10:00:00,100,aaaa1111,40,38,600,1200,ondemand,0-3,5,5,5,5,1,,Discharging,90,4000,,,,
2026-10-18 10:00:05,105,aaaa1111,45,44,1200,1200,performance,0-3,60,40,20,,0,,Discharging,90,4000,snes,libretro,snes9x2005_plus,Yoshi's Island (USA).zip
2026-10-18 10:00:10,110,aaaa1111,47,46,1200,1200,performance,0-3,80,60,40,,0,,Discharging,90,4000,snes,libretro,snes9x2005_plus,Yoshi's Island (USA).zip
2026-10-18 10:00:15,115,aaaa1111,48,49,1200,1200,performance,0-3,70,50,30,,0,,Discharging,89,4000,snes,libretro,snes9x2005_plus,Yoshi's Island (USA).zip
2026-10-18 10:00:20,120,aaaa1111,44,40,600,1200,ondemand,0-3,5,5,5,5,1,,Discharging,89,4000,,,,
2026-10-18 10:05:00,400,aaaa1111,41,40,1200,1200,performance,0-3,30,30,30,30,0,,Discharging,88,4000,snes,libretro,snes9x2005_plus_a33_o3,Yoshi's Island (USA).zip
2026-10-18 10:05:05,405,aaaa1111,43,42,1200,1200,performance,0-3,50,50,50,50,0,,Discharging,88,4000,snes,libretro,snes9x2005_plus_a33_o3,Yoshi's Island (USA).zip
"""


class Resumo(TempDirCase):
    def setUp(self):
        super().setUp()
        self.csv = self.tmp / "r36-thermal.csv"
        self.csv.write_text(CSV, encoding="utf-8")

    def linhas(self, texto):
        return [[c.strip() for c in l.strip("|").split("|")] for l in texto.splitlines()]

    def test_duas_sessoes_em_cores_diferentes(self):
        t = self.linhas(C.resumo(self.csv))
        self.assertEqual(len(t), 4)  # cabeçalho, separador e duas sessões
        cab, a, b = t[0], t[2], t[3]
        col = {n: i for i, n in enumerate(cab)}
        self.assertEqual(a[col["core"]], "snes9x2005_plus")
        self.assertEqual(b[col["core"]], "snes9x2005_plus_a33_o3")
        self.assertEqual(a[col["duração (s)"]], "10")
        self.assertEqual(a[col["amostras"]], "3")
        # ocupação por linha = média dos núcleos com valor: 40, 60, 50
        self.assertEqual(a[col["ocupação média (%)"]], "50,0")
        self.assertEqual(a[col["ocupação máx. (%)"]], "60,0")
        self.assertEqual(a[col["MHz médio"]], "1200")
        self.assertEqual(a[col["teto MHz"]], "1200")
        # temperatura = maior zona da linha
        self.assertEqual((a[col["temp. início (°C)"]], a[col["temp. fim (°C)"]]), ("45", "49"))
        self.assertEqual(b[col["ocupação média (%)"]], "40,0")
        self.assertNotIn("CRC32", cab)

    def test_hashes_das_roms(self):
        roms = self.tmp / "R36-ROMS"
        (roms / "snes").mkdir(parents=True)
        rom = b"\x00rom do yoshi" * 100
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("Yoshi's Island (USA).sfc", rom)
        (roms / "snes" / "Yoshi's Island (USA).zip").write_bytes(buf.getvalue())
        t = self.linhas(C.resumo(self.csv, roms))
        col = {n: i for i, n in enumerate(t[0])}
        for linha in t[2:]:
            self.assertEqual(linha[col["CRC32"]], f"{zlib.crc32(rom):08x}")
            self.assertEqual(linha[col["SHA1"]], hashlib.sha1(rom).hexdigest())

    def test_rom_nao_achada(self):
        t = self.linhas(C.resumo(self.csv, self.tmp / "vazio"))
        self.assertEqual(t[2][-2], "não achada")

    def test_sem_sessoes(self):
        self.csv.write_text(CSV.splitlines()[0] + "\n" + CSV.splitlines()[1] + "\n", encoding="utf-8")
        self.assertIn("Nenhuma sessão", C.resumo(self.csv))


class Cli(unittest.TestCase):
    def test_help_lista_os_subcomandos(self):
        out = subprocess.run([str(ROOT / "cores.sh"), "--help"], check=True, capture_output=True, text=True).stdout
        for s in ("compilar", "verificar", "perfil", "resumo"):
            self.assertIn(s, out)


if __name__ == "__main__":
    unittest.main()
