"""Testes da feature de shaders do Game Boy e do Game Boy Color (55-shaders-gb-gbc)."""

import ast
import os
import re
import stat
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

from context import ROOT

FEATURE_DIR = ROOT / "features" / "55-shaders-gb-gbc"
SHADERS_DIR = FEATURE_DIR / "system" / "usr" / "share" / "common-shaders"
GB_GLSL = SHADERS_DIR / "gb" / "gb-modern-dmg.glsl"
GB_GLSLP = SHADERS_DIR / "gb" / "gb-modern-dmg.glslp"
GBC_GLSL = SHADERS_DIR / "gbc" / "gbc-modern-remaster.glsl"
GBC_GLSLP = SHADERS_DIR / "gbc" / "gbc-modern-remaster.glslp"
GBA_GLSL = ROOT / "features" / "54-shaders-gba" / "system" / "usr" / "share" / "common-shaders" / "gba" / "gba-modern-remaster.glsl"
REPLICA_ACTIVE = ROOT / "openspec" / "changes" / "shaders-gb-gbc-r36s" / "verificacao" / "replica.py"
REPLICA_ARCHIVE = ROOT / "openspec" / "changes" / "archive" / "2026-10-29-shaders-gb-gbc-r36s" / "verificacao" / "replica.py"
REPLICA = REPLICA_ACTIVE if REPLICA_ACTIVE.exists() else REPLICA_ARCHIVE
PREPARA = FEATURE_DIR / "system" / "usr" / "lib" / "r36" / "shader-gb-gbc-prepara"
SERVICE_DIR = FEATURE_DIR / "system" / "usr" / "lib" / "systemd" / "system"
PREPARA_GBA = ROOT / "features" / "54-shaders-gba" / "system" / "usr" / "lib" / "r36" / "shader-gba-prepara"
REF = {
    "gb": '#reference "/usr/share/common-shaders/gb/gb-modern-dmg.glslp"\n',
    "gbc": '#reference "/usr/share/common-shaders/gbc/gbc-modern-remaster.glslp"\n',
}
REF_GBA = '#reference "/usr/share/common-shaders/gba/gba-modern-remaster.glslp"\n'
SETLINE = {"gb": "gb.shaderset=gb/gb-modern-dmg.glslp\n", "gbc": "gbc.shaderset=gbc/gbc-modern-remaster.glslp\n"}
SETLINE_GBA = "gba.shaderset=gba/gba-modern-remaster.glslp\n"
CORES = ("Gambatte", "Gearboy", "SameBoy", "TGB Dual", "mGBA", "VBA-M", "VBA Next")
NOMES = {"gb": "gb-modern-dmg", "gbc": "gbc-modern-remaster"}

GB_PARAMS = {  # identificador: (nome no menu, padrão, mínimo, máximo, passo)
    "TONE_SEP": ("TONE SEPARATION", 0.50, 0.0, 1.0, 0.05),
    "CONTRAST": ("S-CURVE Contrast", 0.20, 0.0, 1.0, 0.05),
    "WARMTH": ("OLIVE WARMTH", 0.50, 0.0, 1.0, 0.05),
    "SOFTNESS": ("PIXEL SOFTNESS", 0.05, 0.0, 1.0, 0.05),
    "LCD_GRID": ("DOT MATRIX GRID (0=Off)", 0.22, 0.0, 1.0, 0.05),
    "BRIGHTNESS": ("BRIGHTNESS", 0.0, -0.30, 0.30, 0.01),
}
GBC_PARAMS = {
    "VIBRANCE": ("VIBRANCE", 0.45, 0.0, 1.0, 0.05),
    "SATURATION": ("SATURATION", 1.10, 0.5, 1.3, 0.01),
    "ROLLOFF": ("HIGHLIGHT ROLLOFF", 0.35, 0.0, 1.0, 0.05),
    "CONTRAST": ("S-CURVE Contrast", 0.28, 0.0, 1.0, 0.05),
    "HIGHLIGHT": ("HIGHLIGHT SHOULDER", 0.05, 0.0, 1.0, 0.05),
    "SOFTNESS": ("PIXEL SOFTNESS", 0.05, 0.0, 1.0, 0.05),
    "LCD_GRID": ("LCD GRID (0=Off)", 0.10, 0.0, 1.0, 0.05),
    "BRIGHTNESS": ("BRIGHTNESS", 0.0, -0.30, 0.30, 0.01),
}


def pragmas(texto):
    return {
        m[0]: (m[1], float(m[2]), float(m[3]), float(m[4]), float(m[5]))
        for m in re.findall(r'^#pragma parameter (\w+) "([^"]*)" ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)\s*$', texto, re.MULTILINE)
    }


def preset(arq):
    d = {}
    for linha in arq.read_text(encoding="utf-8").splitlines():
        if "=" in linha:
            k, v = linha.split("=", 1)
            d[k.strip()] = v.strip().strip('"')
    return d


def padroes_da_replica(nome):
    """Lê o dict(...) de padrões da replica.py sem importá-la (precisa de numpy e pillow)."""
    arvore = ast.parse(REPLICA.read_text(encoding="utf-8"))
    for no in arvore.body:
        if isinstance(no, ast.Assign) and any(getattr(t, "id", None) == nome for t in no.targets):
            return {kw.arg: ast.literal_eval(kw.value) for kw in no.value.keywords}
    raise AssertionError(f"{nome} ausente em replica.py")


def constante_da_replica(nome):
    arvore = ast.parse(REPLICA.read_text(encoding="utf-8"))
    for no in arvore.body:
        if isinstance(no, ast.Assign) and any(getattr(t, "id", None) == nome for t in no.targets):
            return no.value
    raise AssertionError(f"{nome} ausente em replica.py")


class TestShadersGbGbc(unittest.TestCase):
    def test_feature_descriptor(self):
        dados = tomllib.loads((FEATURE_DIR / "feature.toml").read_text(encoding="utf-8"))
        self.assertEqual(dados["schema"], 1)
        self.assertEqual(dados["order"], 55)
        self.assertTrue(dados["enabled"])
        self.assertIn("GB", dados["name"])

    def test_arquivos_e_permissoes(self):
        for arq in (GB_GLSL, GB_GLSLP, GBC_GLSL, GBC_GLSLP):
            self.assertTrue(arq.is_file(), f"{arq.name} ausente")
            self.assertEqual(oct(stat.S_IMODE(arq.stat().st_mode)), oct(0o644), arq.name)

    def test_presets_de_passe_unico(self):
        for glslp, glsl in ((GB_GLSLP, GB_GLSL), (GBC_GLSLP, GBC_GLSL)):
            d = preset(glslp)
            self.assertEqual(d, {"shaders": "1", "shader0": glsl.name, "filter_linear0": "true",
                                 "scale_type0": "viewport", "scale0": "1.0"}, glslp.name)

    def confere_parametros(self, glsl, esperado, titulo):
        texto = glsl.read_text(encoding="utf-8")
        self.assertIn(titulo, texto)
        self.assertEqual(pragmas(texto), esperado)
        self.assertEqual(re.findall(r'^#pragma parameter (\w+)', texto, re.MULTILINE), list(esperado))
        # cada parâmetro tem uniform (PARAMETER_UNIFORM) e #define de reserva com o mesmo padrão
        for nome in esperado:
            self.assertRegex(texto, rf"uniform COMPAT_PRECISION float {nome};")
        reserva = {m[0]: float(m[1]) for m in re.findall(r"^#define (\w+) ([-\d.]+)\s*$", texto, re.MULTILINE) if m[0] in esperado}
        self.assertEqual(reserva, {k: v[1] for k, v in esperado.items()})

    def test_parametros_do_gb(self):
        self.confere_parametros(GB_GLSL, GB_PARAMS, "GB Modern DMG Shader")

    def test_parametros_do_gbc(self):
        self.confere_parametros(GBC_GLSL, GBC_PARAMS, "GBC Modern Remaster Shader")

    def test_leves_para_mali400(self):
        # Passe único (no .glslp), uma leitura de textura, mediump, sem pow() e sem laços
        for glsl in (GB_GLSL, GBC_GLSL):
            texto = glsl.read_text(encoding="utf-8")
            codigo = re.sub(r"/\*.*?\*/|//[^\n]*", "", texto, flags=re.DOTALL)
            self.assertNotIn("pow(", codigo, glsl.name)
            self.assertNotRegex(codigo, r"\b(for|while|do)\b\s*[({]", glsl.name)
            self.assertEqual(len(re.findall(r"COMPAT_TEXTURE\s*\(", codigo)), 1, glsl.name)
            self.assertEqual(len(re.findall(r"\btexture2D\s*\(|\btexture\s*\(", codigo)), 0, glsl.name)
            bloco = re.sub(r"#ifdef GL_FRAGMENT_PRECISION_HIGH.*?#else", "", codigo, flags=re.DOTALL)
            self.assertNotIn("highp", bloco, glsl.name)
            self.assertIn("#define COMPAT_PRECISION mediump", codigo, glsl.name)
            self.assertNotIn("FrameCount %", codigo, glsl.name)
            self.assertNotIn("PassPrev", codigo, glsl.name)

    def test_padroes_iguais_aos_da_replica(self):
        for glsl, nome in ((GB_GLSL, "DEF_GB"), (GBC_GLSL, "DEF_GBC")):
            texto = glsl.read_text(encoding="utf-8")
            replica = padroes_da_replica(nome)
            for param, valores in pragmas(texto).items():
                self.assertAlmostEqual(replica[param], valores[1], msg=f"{glsl.name} {param}")
        # constantes de cada shader espelhadas na réplica
        gbc = GBC_GLSL.read_text(encoding="utf-8")
        self.assertIn(f"mx + {padroes_da_replica('DEF_GBC')['CEIL']}", gbc)
        gb = GB_GLSL.read_text(encoding="utf-8")
        self.assertIn(f"T3 * {ast.literal_eval(constante_da_replica('SUBSTRATO'))}", gb)

    def test_paleta_do_gb_igual_a_da_replica(self):
        # T0..T3 do .glsl (vec3 em 0-1) são os RGB 0-255 de T na réplica
        texto = GB_GLSL.read_text(encoding="utf-8")
        glsl = [tuple(float(x) for x in m) for m in re.findall(
            r"const vec3 T\d = vec3\(([\d.]+), ([\d.]+), ([\d.]+)\);", texto)]
        no = constante_da_replica("T")
        rgb = ast.literal_eval(no.left.args[0])  # np.array([...], np.float32) / 255
        self.assertEqual(len(glsl), 4)
        for a, b in zip(glsl, rgb):
            for x, y in zip(a, b):
                self.assertAlmostEqual(x, y / 255, places=5)
            # verde-oliva: G > R > B nos quatro tons
            self.assertTrue(b[1] > b[0] > b[2], b)

    def test_gbc_segue_o_pipeline_do_gba(self):
        # O gbc-modern-remaster é o pipeline do gba-modern-remaster com os padrões remedidos
        # em 533x480 (SOFTNESS) e o teto mais baixo (sem estourar abaixo de 245): o corpo do
        # main() só difere nessas constantes.
        def corpo(arq):
            t = arq.read_text(encoding="utf-8")
            t = t[t.index("void main()", t.index("#elif defined(FRAGMENT)")):]
            return re.sub(r"\s+", " ", re.sub(r"//[^\n]*", "", t))
        self.assertEqual(corpo(GBC_GLSL).replace("mx + 0.035", "mx + 0.05"), corpo(GBA_GLSL))

    def test_preset_padrao_nasce_no_boot_nao_na_imagem(self):
        # Os presets automáticos (<Core>/gb.glslp, <Core>/gbc.glslp) e os .opt do Gambatte são
        # criados no boot pelo r36-shader-gb-gbc-prepara, para valer com --keep-storage.
        presets = sorted(p.name for p in FEATURE_DIR.rglob("*.glslp") if p not in (GB_GLSLP, GBC_GLSLP))
        self.assertEqual(presets, [])
        self.assertEqual(list(FEATURE_DIR.rglob("*.opt")), [])
        self.assertFalse((FEATURE_DIR / "storage").exists(), "Feature não deve mexer na p8 pela imagem")


class TestPreparoGbGbc(unittest.TestCase):
    """r36-shader-gb-gbc-prepara sobre um R36_ROOT temporário."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.radir = self.root / "storage" / ".config" / "retroarch"
        self.config = self.radir / "config"
        self.roms = self.root / "storage" / "roms"

    def roda(self, script=PREPARA):
        proc = subprocess.run(
            ["sh", str(script)], capture_output=True, text=True,
            env={"PATH": os.environ["PATH"], "R36_ROOT": str(self.root)},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def system(self, sis, glsl="#pragma parameter LCD_GRID novo\n"):
        destino = self.root / "usr" / "share" / "common-shaders" / sis
        destino.mkdir(parents=True, exist_ok=True)
        (destino / f"{NOMES.get(sis, 'gba-modern-remaster')}.glsl").write_text(glsl)
        (destino / f"{NOMES.get(sis, 'gba-modern-remaster')}.glslp").write_text(f'shader0 = "{NOMES.get(sis, "gba-modern-remaster")}.glsl"\n')

    def system_com_shaders(self):
        self.system("gb")
        self.system("gbc")

    def p8(self, sis, glsl, glslp="antigo\n"):
        destino = self.root / "storage" / "shaders" / sis
        destino.mkdir(parents=True, exist_ok=True)
        (destino / f"{NOMES[sis]}.glsl").write_text(glsl)
        (destino / f"{NOMES[sis]}.glslp").write_text(glslp)
        return destino

    def emuconf(self, texto):
        arq = self.root / "storage" / ".config" / "emuelec" / "configs" / "emuelec.conf"
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(texto)
        return arq

    def chave(self, nome):
        self.roms.mkdir(parents=True, exist_ok=True)
        (self.roms / nome).write_text("")

    def arquivo(self, rel, texto):
        arq = self.root / rel
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(texto)
        return arq

    def test_service_e_script(self):
        self.assertTrue(os.access(PREPARA, os.X_OK), "shader-gb-gbc-prepara sem permissão de execução")
        proc = subprocess.run(["sh", "-n", str(PREPARA)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        servico = (SERVICE_DIR / "r36-shader-gb-gbc-prepara.service").read_text(encoding="utf-8")
        self.assertEqual(oct(stat.S_IMODE((SERVICE_DIR / "r36-shader-gb-gbc-prepara.service").stat().st_mode)), oct(0o644))
        diretivas = [l for l in servico.splitlines() if l.strip() and not l.lstrip().startswith("#")]
        self.assertIn("Before=emustation.service", diretivas)
        self.assertIn("ExecStart=/usr/lib/r36/shader-gb-gbc-prepara", diretivas)
        # depois do autostart trava o boot no splash (CLAUDE.md, "Boot e ES")
        self.assertFalse([l for l in diretivas if l.startswith("After=") and "emuelec-autostart" in l])
        depois = " ".join(l[len("After="):] for l in diretivas if l.startswith("After="))
        self.assertIn("tmp-shaders.mount", depois)
        # em série com o serviço do GBA: os dois escrevem no emuelec.conf e montam /tmp/shaders
        self.assertIn("r36-shader-gba-prepara.service", depois)
        link = SERVICE_DIR / "emuelec.target.wants" / "r36-shader-gb-gbc-prepara.service"
        self.assertTrue(link.is_symlink())
        self.assertEqual(os.readlink(link), "../r36-shader-gb-gbc-prepara.service")

    def test_tmp_shaders_por_bind_sem_overlayfs(self):
        texto = PREPARA.read_text(encoding="utf-8")
        self.assertIn("mount -o bind /storage/shaders /tmp/shaders", texto)
        self.assertRegex(texto, r'\[ -z "\$ROOT" \] && ! grep -q \' /tmp/shaders \' /proc/mounts')

    def test_sem_shader_no_system_nada_e_criado(self):
        self.roda()
        self.assertFalse(self.config.exists())
        self.assertFalse(self.radir.exists())

    def test_atualiza_copia_antiga_no_mesmo_inode(self):
        # O rsync --ignore-existing do emuelec_autostart.sh nunca atualiza a cópia da p8
        self.system_com_shaders()
        for sis in ("gb", "gbc"):
            destino = self.p8(sis, "#pragma parameter LCD_GRID antigo\n")
            glsl = destino / f"{NOMES[sis]}.glsl"
            inode = glsl.stat().st_ino
            self.roda()
            self.assertEqual(glsl.read_text(), "#pragma parameter LCD_GRID novo\n", sis)
            self.assertEqual(glsl.stat().st_ino, inode, "a cópia deve ser regravada no lugar, não recriada")
            self.assertEqual((destino / f"{NOMES[sis]}.glslp").read_text(), f'shader0 = "{NOMES[sis]}.glsl"\n')

    def test_nao_cria_copia_que_nao_existe(self):
        self.system_com_shaders()
        self.roda()
        self.assertFalse((self.root / "storage" / "shaders").exists())

    def test_cria_presets_por_pasta_de_conteudo(self):
        self.system_com_shaders()
        self.roda()
        for core in CORES:
            for base in (self.config, self.radir):
                for sis in ("gb", "gbc"):
                    self.assertEqual((base / core / f"{sis}.glslp").read_text(), REF[sis], f"{base} {core} {sis}")
                # nunca o preset de core: ele valeria também para o GBA no mGBA/VBA
                self.assertFalse((base / core / f"{core}.glslp").exists(), core)

    def test_nao_sobrescreve_preset_do_usuario(self):
        self.system_com_shaders()
        salvo = self.arquivo("storage/.config/retroarch/config/Gambatte/gb.glslp", REF["gb"] + 'LCD_GRID = "0.0"\n')
        outro = self.arquivo("storage/.config/retroarch/Gambatte/gbc.glslp", '#reference "/tmp/shaders/crt/crt-pi.glslp"\n')
        self.roda()
        self.assertIn("LCD_GRID", salvo.read_text())
        self.assertIn("crt-pi", outro.read_text())

    def test_nao_toca_no_preset_de_core_do_gba(self):
        self.system_com_shaders()
        mgba = self.arquivo("storage/.config/retroarch/config/mGBA/mGBA.glslp", REF_GBA)
        self.roda()
        self.assertEqual(mgba.read_text(), REF_GBA)
        self.chave("r36-gb-sem-shader")
        self.chave("r36-gbc-sem-shader")
        self.roda()
        self.assertEqual(mgba.read_text(), REF_GBA)

    def test_idempotente(self):
        self.system_com_shaders()
        conf = self.emuconf("gb.core=gambatte\n")
        self.p8("gb", "#pragma parameter LCD_GRID antigo\n")
        self.arquivo("storage/.config/retroarch/config/Gambatte/Gambatte.opt", 'gambatte_mix_frames = "mix"\n')
        self.roda()
        pastas = (self.config, self.radir, self.root / "storage" / "shaders")

        def mtimes():  # config/ fica dentro de radir/; o dicionário junta tudo sem repetir
            return {p: p.stat().st_mtime_ns for pasta in pastas for p in pasta.rglob("*") if p.is_file()}

        antes = mtimes()
        self.assertTrue([p for p in antes if p.suffix == ".opt"], "o teste precisa cobrir os .opt")
        self.assertTrue([p for p in antes if p.parent.parent == self.root / "storage" / "shaders"], "e a p8")
        texto = conf.read_text()
        self.roda()
        self.assertEqual(antes, mtimes())
        self.assertEqual(conf.read_text(), texto)

    def test_liga_shaderset_no_emuelec_conf(self):
        self.system_com_shaders()
        for fim in ("\n", ""):  # com e sem quebra de linha no fim do arquivo
            conf = self.emuconf("gb.core=gambatte" + fim)
            self.roda()
            self.assertEqual(conf.read_text(), "gb.core=gambatte\n" + SETLINE["gb"] + SETLINE["gbc"])
            self.roda()
            self.assertEqual(conf.read_text().count("shaderset="), 2)

    def test_respeita_shaderset_do_usuario(self):
        self.system_com_shaders()
        for escolha in ("gb.shaderset=none\n", "gb.shaderset=crt/crt-pi.glslp\n"):
            conf = self.emuconf(escolha + "gbc.shaderset=none\n")
            self.roda()
            self.assertEqual(conf.read_text(), escolha + "gbc.shaderset=none\n")
        # gbc.shaderset do usuário não conta como gb.shaderset
        conf = self.emuconf("gbc.shaderset=none\n")
        self.roda()
        self.assertEqual(conf.read_text(), "gbc.shaderset=none\n" + SETLINE["gb"])

    def test_chave_desliga_so_o_gb(self):
        self.system_com_shaders()
        conf = self.emuconf("gb.core=gambatte\n")
        self.roda()
        salvo = self.arquivo("storage/.config/retroarch/config/SameBoy/gb.glslp", REF["gb"] + 'LCD_GRID = "0.0"\n')
        self.chave("r36-gb-sem-shader")
        self.roda()
        self.assertEqual(conf.read_text(), "gb.core=gambatte\n" + SETLINE["gbc"])
        for core in CORES:
            for base in (self.config, self.radir):
                if core != "SameBoy" or base != self.config:
                    self.assertFalse((base / core / "gb.glslp").exists(), f"{base} {core}")
                self.assertEqual((base / core / "gbc.glslp").read_text(), REF["gbc"], f"{base} {core}")
        self.assertTrue(salvo.exists(), "preset editado pelo usuário não pode ser apagado")
        self.roda()  # com a chave, nada volta
        self.assertFalse((self.config / "Gambatte" / "gb.glslp").exists())
        self.assertNotIn("gb.shaderset", conf.read_text())

    def test_chave_desliga_so_o_gbc(self):
        self.system_com_shaders()
        conf = self.emuconf("gbc.shaderset=gbc/gbc-modern-remaster.glslp\nsnes.shaderset=x\n")
        self.roda()
        self.chave("r36-gbc-sem-shader")
        self.roda()
        self.assertEqual(conf.read_text(), "snes.shaderset=x\n" + SETLINE["gb"])
        for core in CORES:
            self.assertFalse((self.config / core / "gbc.glslp").exists(), core)
            self.assertEqual((self.config / core / "gb.glslp").read_text(), REF["gb"], core)
        # escolha do usuário fica mesmo com a chave
        escolha = self.emuconf("gbc.shaderset=crt/crt-pi.glslp\n")
        self.roda()
        self.assertEqual(escolha.read_text(), "gbc.shaderset=crt/crt-pi.glslp\n" + SETLINE["gb"])

    def test_cria_opcoes_do_gambatte_por_pasta(self):
        self.system_com_shaders()
        self.roda()
        gambatte = self.config / "Gambatte"
        gb_opt = (gambatte / "gb.opt").read_text()
        gbc_opt = (gambatte / "gbc.opt").read_text()
        self.assertIn('gambatte_gb_colorization = "disabled"\n', gb_opt)
        self.assertIn('gambatte_mix_frames = "mix"\n', gb_opt)
        self.assertIn('gambatte_gbc_color_correction = "disabled"\n', gbc_opt)
        self.assertIn('gambatte_mix_frames = "mix"\n', gbc_opt)

    def test_preserva_opcoes_do_gambatte_existentes(self):
        self.system_com_shaders()
        gb = self.arquivo("storage/.config/retroarch/config/Gambatte/gb.opt",
                          'gambatte_gb_colorization = "auto"\ngambatte_gb_internal_palette = "GB - DMG"\n')
        gbc = self.arquivo("storage/.config/retroarch/config/Gambatte/gbc.opt",
                           'gambatte_gbc_color_correction = "GBC only"\n')
        antes = (gb.read_text(), gbc.read_text())
        self.roda()
        self.assertIn('gambatte_gb_colorization = "auto"\n', gb.read_text())
        self.assertIn('gambatte_gbc_color_correction = "GBC only"\n', gbc.read_text())

    def test_acrescenta_opcao_que_falta_sem_apagar_as_outras(self):
        self.system_com_shaders()
        gbc = self.arquivo("storage/.config/retroarch/config/Gambatte/gbc.opt", 'gambatte_audio_resampler = "cc"\n')
        self.roda()
        self.assertIn('gambatte_audio_resampler = "cc"\n', gbc.read_text())
        self.assertIn('gambatte_gbc_color_correction = "disabled"\n', gbc.read_text())
        self.assertIn('gambatte_mix_frames = "mix"\n', gbc.read_text())
        self.roda()
        self.assertEqual(gbc.read_text().count("gambatte_gbc_color_correction"), 1)
        self.assertEqual(gbc.read_text().count("gambatte_mix_frames"), 1)

    def test_opt_novo_parte_do_gambatte_opt_global(self):
        # global_core_options = "false" e game_specific_options = "true": um gb.opt/gbc.opt por
        # pasta vale no lugar do Gambatte.opt, então o arquivo novo herda as escolhas globais
        self.system_com_shaders()
        glob = self.arquivo("storage/.config/retroarch/config/Gambatte/Gambatte.opt",
                            'gambatte_mix_frames = "mix"\ngambatte_gb_colorization = "auto"\n'
                            'gambatte_gbc_color_correction = "GBC only"\ngambatte_audio_resampler = "cc"')
        antes = glob.read_text()
        self.roda()
        gambatte = self.config / "Gambatte"
        gb = (gambatte / "gb.opt").read_text()
        gbc = (gambatte / "gbc.opt").read_text()
        for texto in (gb, gbc):
            self.assertIn('gambatte_mix_frames = "mix"\n', texto)
            self.assertIn('gambatte_audio_resampler = "cc"\n', texto)
        # a chave do shader vale a do serviço, não a do arquivo global (o .opt é novo)
        self.assertEqual(gb.count("gambatte_gb_colorization"), 1)
        self.assertIn('gambatte_gb_colorization = "disabled"\n', gb)
        self.assertEqual(gbc.count("gambatte_gbc_color_correction"), 1)
        self.assertIn('gambatte_gbc_color_correction = "disabled"\n', gbc)
        self.assertEqual(glob.read_text(), antes, "o Gambatte.opt global não pode mudar")
        # segundo boot: nada muda
        self.roda()
        self.assertEqual(((gambatte / "gb.opt").read_text(), (gambatte / "gbc.opt").read_text()), (gb, gbc))

    def test_opt_existente_nao_e_tocado_mesmo_com_gambatte_opt(self):
        self.system_com_shaders()
        self.arquivo("storage/.config/retroarch/config/Gambatte/Gambatte.opt", 'gambatte_mix_frames = "mix"\n')
        gb = self.arquivo("storage/.config/retroarch/config/Gambatte/gb.opt", 'gambatte_gb_colorization = "auto"\n')
        self.roda()
        self.assertEqual(gb.read_text(), 'gambatte_gb_colorization = "auto"\ngambatte_mix_frames = "mix"\n')
        # o gbc.opt, que faltava, nasce com a cópia
        self.assertIn("gambatte_mix_frames", (self.config / "Gambatte" / "gbc.opt").read_text())

    def test_opcoes_ficam_com_as_chaves_de_desligar(self):
        # As chaves desligam o shader; a cor crua do Gambatte não depende dele
        self.system_com_shaders()
        self.chave("r36-gb-sem-shader")
        self.chave("r36-gbc-sem-shader")
        self.roda()
        self.assertTrue((self.config / "Gambatte" / "gb.opt").exists())
        self.assertTrue((self.config / "Gambatte" / "gbc.opt").exists())

    def test_log_sob_a_chave_de_diagnostico(self):
        self.system_com_shaders()
        self.emuconf("gb.core=gambatte\n")
        self.chave("r36-diagnostico")
        self.roda()
        log = (self.roms / "r36-shader-gb-gbc.log").read_text()
        self.assertIn("r36-shader-gb-gbc-prepara", log)
        self.assertIn("gb.shaderset=gb/gb-modern-dmg.glslp criada", log)
        self.assertIn("preset Gambatte/gbc.glslp criado", log)
        self.assertIn("gb.opt", log)
        self.roda()  # o log é refeito a cada boot
        self.assertEqual((self.roms / "r36-shader-gb-gbc.log").read_text().count("r36-shader-gb-gbc-prepara"), 1)

    def test_sem_a_chave_de_diagnostico_nao_ha_log_e_o_resto_vale(self):
        self.system_com_shaders()
        self.roms.mkdir(parents=True)
        (self.roms / "r36-shader-gb-gbc.log").write_text("boot antigo\n")
        conf = self.emuconf("gb.core=gambatte\n")
        self.roda()
        self.assertEqual((self.roms / "r36-shader-gb-gbc.log").read_text(), "boot antigo\n")
        self.assertIn("gb.shaderset=", conf.read_text())
        self.assertTrue((self.config / "Gambatte" / "gb.glslp").exists())

    def test_convive_com_o_servico_do_gba(self):
        # Os dois serviços no mesmo R36_ROOT, na ordem do boot (GBA antes), sem apagar o
        # trabalho um do outro, inclusive com as chaves de desligar e a limpeza do GBA
        self.system_com_shaders()
        self.system("gba", "#pragma parameter VIBRANCE novo\n")
        conf = self.emuconf("gba.core=gpsp\n")
        self.roda(PREPARA_GBA)
        self.roda()
        self.assertEqual(conf.read_text(), "gba.core=gpsp\n" + SETLINE_GBA + SETLINE["gb"] + SETLINE["gbc"])
        for core in ("mGBA", "VBA-M", "VBA Next"):
            self.assertEqual((self.config / core / f"{core}.glslp").read_text(), REF_GBA, core)
            self.assertEqual((self.config / core / "gb.glslp").read_text(), REF["gb"], core)
            self.assertEqual((self.config / core / "gbc.glslp").read_text(), REF["gbc"], core)
        # cópia velha do shader do GBA na p8: o serviço do GBA apaga os presets que só a
        # referenciam, e só esses
        gba_p8 = self.root / "storage" / "shaders" / "gba"
        gba_p8.mkdir(parents=True)
        (gba_p8 / "gba-modern-remaster.glsl").write_text("antigo\n")
        self.roda(PREPARA_GBA)
        self.roda()
        for core in CORES:
            self.assertTrue((self.config / core / "gb.glslp").exists(), core)
            self.assertTrue((self.config / core / "gbc.glslp").exists(), core)
        # chave do GBA: some o do GBA, ficam GB e GBC
        self.chave("r36-gba-sem-shader")
        self.roda(PREPARA_GBA)
        self.roda()
        self.assertEqual(conf.read_text(), "gba.core=gpsp\n" + SETLINE["gb"] + SETLINE["gbc"])
        self.assertFalse((self.config / "mGBA" / "mGBA.glslp").exists())
        self.assertTrue((self.config / "mGBA" / "gb.glslp").exists())
        # chaves do GB e do GBC: some o deles, o GBA (religado) fica
        (self.roms / "r36-gba-sem-shader").unlink()
        self.chave("r36-gb-sem-shader")
        self.chave("r36-gbc-sem-shader")
        self.roda(PREPARA_GBA)
        self.roda()
        self.assertEqual(conf.read_text(), "gba.core=gpsp\n" + SETLINE_GBA)
        self.assertEqual((self.config / "mGBA" / "mGBA.glslp").read_text(), REF_GBA)
        self.assertFalse((self.config / "mGBA" / "gb.glslp").exists())
        self.assertFalse((self.config / "mGBA" / "gbc.glslp").exists())


if __name__ == "__main__":
    unittest.main()
