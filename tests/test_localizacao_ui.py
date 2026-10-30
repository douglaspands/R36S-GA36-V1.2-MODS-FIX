import ast
import struct
import subprocess
import unittest
from pathlib import Path

from context import ROOT

LOCALE_BASE = ROOT / "features" / "10-ptbr-sao-paulo" / "system" / "usr" / "config" / "emuelec" / "configs" / "locale"
PT_DIR = LOCALE_BASE / "pt_BR" / "LC_MESSAGES"
ES_DIR = LOCALE_BASE / "es_MX" / "LC_MESSAGES"


def parse_po(file_path: Path):
    """Parses a PO file into a list of dicts with header and entries."""
    lines = file_path.read_text(encoding="utf-8").splitlines()
    entries = []

    msgid_parts = []
    msgid_plural_parts = []
    msgstr_parts = []
    msgstr_n = {}
    current_n = None
    state = None
    has_plural = False

    def unescape(parts):
        res = ""
        for p in parts:
            p = p.strip()
            if p.startswith('"') and p.endswith('"'):
                try:
                    res += ast.literal_eval(p)
                except Exception:
                    res += p[1:-1]
            else:
                res += p
        return res

    def flush():
        nonlocal msgid_parts, msgid_plural_parts, msgstr_lines, msgstr_n, current_n, state, has_plural
        if msgid_parts:
            msgid = unescape(msgid_parts)
            msgid_plural = unescape(msgid_plural_parts) if has_plural else None
            if has_plural:
                msgstr = {k: unescape(v) for k, v in msgstr_n.items()}
            else:
                msgstr = unescape(msgstr_lines)
            entries.append({
                "msgid": msgid,
                "msgid_plural": msgid_plural,
                "msgstr": msgstr,
            })
        msgid_parts = []
        msgid_plural_parts = []
        msgstr_lines = []
        msgstr_n = {}
        current_n = None
        state = None
        has_plural = False

    msgstr_lines = []
    for line in lines:
        sline = line.strip()
        if not sline:
            flush()
            continue
        if sline.startswith("#"):
            continue
        elif sline.startswith("msgid "):
            state = "msgid"
            msgid_parts.append(sline[6:].strip())
        elif sline.startswith("msgid_plural "):
            state = "msgid_plural"
            has_plural = True
            msgid_plural_parts.append(sline[13:].strip())
        elif sline.startswith("msgstr "):
            state = "msgstr"
            msgstr_lines.append(sline[7:].strip())
        elif sline.startswith("msgstr["):
            state = "msgstr_n"
            current_n = int(sline[7:sline.find("]")])
            if current_n not in msgstr_n:
                msgstr_n[current_n] = []
            msgstr_n[current_n].append(sline[sline.find("]") + 1:].strip())
        elif sline.startswith('"'):
            if state == "msgid":
                msgid_parts.append(sline)
            elif state == "msgid_plural":
                msgid_plural_parts.append(sline)
            elif state == "msgstr":
                msgstr_lines.append(sline)
            elif state == "msgstr_n":
                msgstr_n[current_n].append(sline)
    flush()
    return entries


class TestLocalizacaoUI(unittest.TestCase):
    def test_arquivos_existem(self):
        """Verifica se arquivos .po e .mo estão presentes nas pastas esperadas."""
        for lang_dir in (PT_DIR, ES_DIR):
            po_file = lang_dir / "emulationstation2.po"
            mo_file = lang_dir / "emulationstation2.mo"
            self.assertTrue(po_file.is_file(), f"Arquivo {po_file} ausente")
            self.assertTrue(mo_file.is_file(), f"Arquivo {mo_file} ausente")
            self.assertGreater(po_file.stat().st_size, 10000, f"{po_file} vazio ou muito pequeno")
            self.assertGreater(mo_file.stat().st_size, 10000, f"{mo_file} vazio ou muito pequeno")

    def test_mo_magic_number(self):
        """Verifica se os arquivos .mo são binários gettext válidos."""
        for lang_dir in (PT_DIR, ES_DIR):
            mo_file = lang_dir / "emulationstation2.mo"
            if not mo_file.is_file():
                self.skipTest(f"{mo_file} não existe")
            with open(mo_file, "rb") as f:
                magic = f.read(4)
            self.assertIn(
                magic,
                (b"\xde\x12\x04\x95", b"\x95\x04\x12\xde"),
                f"{mo_file} não possui o número mágico válido do gettext MO"
            )

    def test_cabecalho_utf8(self):
        """Verifica se os cabeçalhos gettext declaram UTF-8."""
        for lang_dir in (PT_DIR, ES_DIR):
            po_file = lang_dir / "emulationstation2.po"
            if not po_file.is_file():
                self.skipTest(f"{po_file} não existe")
            entries = parse_po(po_file)
            header = next((e for e in entries if e["msgid"] == ""), None)
            self.assertIsNotNone(header, f"Cabeçalho ausente em {po_file}")
            self.assertIn("charset=UTF-8", header["msgstr"], f"Charset UTF-8 não encontrado em {po_file}")

    def test_zero_mensagens_vazias_pt_br(self):
        """Valida que todas as mensagens em pt_BR possuem tradução preenchida."""
        po_file = PT_DIR / "emulationstation2.po"
        if not po_file.is_file():
            self.skipTest(f"{po_file} não existe")
        entries = parse_po(po_file)
        empty = []
        for e in entries:
            if e["msgid"] == "":
                continue
            if e["msgid_plural"]:
                if any(v == "" for v in e["msgstr"].values()) or not e["msgstr"]:
                    empty.append(e["msgid"])
            else:
                if e["msgstr"] == "":
                    empty.append(e["msgid"])
        self.assertEqual(empty, [], f"Existem mensagens vazias em pt_BR: {empty[:10]}")

    def test_zero_mensagens_vazias_es_mx(self):
        """Valida que todas as mensagens em es_MX possuem tradução preenchida."""
        po_file = ES_DIR / "emulationstation2.po"
        if not po_file.is_file():
            self.skipTest(f"{po_file} não existe")
        entries = parse_po(po_file)
        empty = []
        for e in entries:
            if e["msgid"] == "":
                continue
            if e["msgid_plural"]:
                if any(v == "" for v in e["msgstr"].values()) or not e["msgstr"]:
                    empty.append(e["msgid"])
            else:
                if e["msgstr"] == "":
                    empty.append(e["msgid"])
        self.assertEqual(empty, [], f"Existem mensagens vazias em es_MX: {empty[:10]}")

    def test_preservacao_termos_tecnicos_pt_br(self):
        """Verifica se termos técnicos consagrados são mantidos em inglês no pt_BR."""
        po_file = PT_DIR / "emulationstation2.po"
        if not po_file.is_file():
            self.skipTest(f"{po_file} não existe")
        entries = parse_po(po_file)
        msg_dict = {e["msgid"]: e["msgstr"] for e in entries if isinstance(e["msgstr"], str)}

        # 1. Core
        key_core = "WARNING: RETROARCH CONFIG WILL RESET TO DEFAULT\n\nPER-CORE CONFIGURATIONS WILL NOT BE AFFECTED BUT NO BACKUP WILL BE CREATED!\n\nRESET RETROARCH CONFIG TO DEFAULT?"
        if key_core in msg_dict:
            self.assertIn("Core", msg_dict[key_core])

        # 2. Save State
        key_backup = "WARNING THIS WILL RESTART EMULATIONSTATION!\n\nThis will backup your game saves, savestates and emuelec configs to the cloud service configured on rclone.conf\n\nBACKUP TO CLOUD AND RESTART?"
        if key_backup in msg_dict:
            self.assertIn("Save State", msg_dict[key_backup])

        # 3. Shader
        if "SHADERS SET" in msg_dict:
            self.assertIn("SHADER", msg_dict["SHADERS SET"].upper())

        # 4. Bezel
        if "ENABLE RA BEZELS" in msg_dict:
            self.assertIn("BEZEL", msg_dict["ENABLE RA BEZELS"].upper())

        # 5. BIOS
        if "Use HLE BIOS" in msg_dict:
            self.assertIn("BIOS", msg_dict["Use HLE BIOS"])

        # 6. ROMs
        key_roms = "Select the mounted drive to be used for ROMS."
        if key_roms in msg_dict:
            self.assertIn("ROMs", msg_dict[key_roms])

    def test_calibracao_tela_compacta(self):
        """Verifica se opções de ordenação e diálogos rápidos são concisos para tela de 3.5 polegadas."""
        for lang_dir in (PT_DIR, ES_DIR):
            po_file = lang_dir / "emulationstation2.po"
            entries = parse_po(po_file)
            msg_dict = {e["msgid"]: e["msgstr"] for e in entries if isinstance(e["msgstr"], str)}
            # Ordenação de nomes concisa
            self.assertIn("SORTNAME, ASCENDING", msg_dict)
            self.assertLessEqual(len(msg_dict["SORTNAME, ASCENDING"]), 20)
            self.assertIn("SORTNAME, DESCENDING", msg_dict)
            self.assertLessEqual(len(msg_dict["SORTNAME, DESCENDING"]), 20)
            # Diálogo de multidisco conciso por linha
            multidisc = msg_dict.get("THIS WILL CREATE A MULTI-DISC FILE(S)!\nARE YOU SURE?", "")
            for line in multidisc.splitlines():
                self.assertLessEqual(len(line), 40, f"Linha muito longa em {po_file.name}: {line}")

            # SAVESTATE MANAGER abreviado para caber na barra de botões sem truncamento
            self.assertIn("SAVESTATE MANAGER", msg_dict)
            self.assertLessEqual(len(msg_dict["SAVESTATE MANAGER"]), 15, "SAVESTATE MANAGER deve ser conciso")
            self.assertIn("Hide Game", msg_dict)
            self.assertTrue(bool(msg_dict["Hide Game"]), "Hide Game deve estar traduzido")
            self.assertIn("HIDE GAME", msg_dict)
            self.assertTrue(bool(msg_dict["HIDE GAME"]), "HIDE GAME deve estar traduzido")
            self.assertIn("UNHIDE GAME", msg_dict)
            self.assertTrue(bool(msg_dict["UNHIDE GAME"]), "UNHIDE GAME deve estar traduzido")
            self.assertIn("RESTART EMULATIONSTATION", msg_dict)
            expected_restart = "REINICIAR INTERFACE" if "pt_BR" in str(po_file) else "REINICIAR INTERFAZ"
            self.assertEqual(msg_dict["RESTART EMULATIONSTATION"], expected_restart)
            self.assertIn("ENTER", msg_dict)
            self.assertEqual(msg_dict["ENTER"], "ENTRAR")
            self.assertIn("(A) ENTER", msg_dict)
            self.assertEqual(msg_dict["(A) ENTER"], "(A) ENTRAR")

    def test_storage_locale_present(self):
        """Verifica se a cópia para a p8 (storage) existe e contém .po e .mo compilados."""
        storage_locale = ROOT / "features" / "10-ptbr-sao-paulo" / "storage" / ".config" / "emuelec" / "configs" / "locale"
        for lang in ("pt_BR", "es_MX"):
            po_file = storage_locale / lang / "LC_MESSAGES" / "emulationstation2.po"
            mo_file = storage_locale / lang / "LC_MESSAGES" / "emulationstation2.mo"
            self.assertTrue(po_file.is_file(), f"{po_file} ausente na storage da feature 10")
            self.assertTrue(mo_file.is_file(), f"{mo_file} ausente na storage da feature 10")
            self.assertGreater(mo_file.stat().st_size, 10000, f"{mo_file} vazio ou muito pequeno")

    def test_usr_share_locale_symlink(self):
        """Verifica se o symlink system/usr/share/locale aponta para /usr/config/emuelec/configs/locale."""
        link_path = ROOT / "features" / "10-ptbr-sao-paulo" / "system" / "usr" / "share" / "locale"
        self.assertTrue(link_path.is_symlink(), f"{link_path} deve ser um link simbólico")
        import os
        target = os.readlink(link_path)
        self.assertEqual(target, "/usr/config/emuelec/configs/locale")


if __name__ == "__main__":
    unittest.main()
