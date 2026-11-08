import sys
import tempfile
import unittest
from pathlib import Path

from context import ROOT  # noqa: F401  (ajusta sys.path para tools/)

import auditar_roms as au


class TituloNormal(unittest.TestCase):
    def test_artigo_no_sufixo_casa_com_artigo_no_prefixo(self):
        self.assertEqual(
            au.titulo_normal("Legend of Zelda, The - A Link to the Past (USA).zip"),
            au.titulo_normal("The Legend of Zelda - A Link to the Past (Europe).zip"),
        )

    def test_tags_e_espacos_nao_mudam_o_titulo(self):
        self.assertEqual(
            au.titulo_normal("Donkey Kong Country 2  [E].zip"),
            au.titulo_normal("Donkey Kong Country 2 (USA).zip"),
        )

    def test_titulos_diferentes_continuam_diferentes(self):
        self.assertNotEqual(au.titulo_normal("Casper (USA).zip"), au.titulo_normal("Casper 2 (USA).zip"))


class Classificacao(unittest.TestCase):
    def test_hack_com_marcacao_forte(self):
        self.assertEqual(au.classificar("Battle Mania (U) [h1].zip")[0], "hack_provavel")
        self.assertEqual(au.classificar("Wonder Momo Sprite Hack 1 v1.1(Japan).zip")[0], "hack_provavel")

    def test_traducao_tem_prioridade_sobre_hack(self):
        self.assertEqual(au.classificar("Lady Sword (J) (Alt) [T_Eng] [h1].zip")[0], "traducao")
        self.assertEqual(au.classificar("Out Live (Japan) T+Eng v1.0.zip")[0], "traducao")
        self.assertEqual(au.classificar("Ambition of Caesar (J) [T+Chi].zip")[0], "traducao")
        self.assertEqual(au.classificar("Legend of Zelda, The - A Link to the Past (pt_BR).zip")[0], "traducao")

    def test_kaizou_nao_e_kaizo(self):
        self.assertNotEqual(au.classificar("Kaizou Choujin Shubibinman (J) [p1].zip")[0], "hack_provavel")

    def test_regiao_entre_colchetes_conta_como_original(self):
        self.assertEqual(au.classificar("Advance Wars 2 [E].zip")[0], "original")

    def test_sem_marcacao_nao_e_suspeito(self):
        self.assertEqual(au.classificar("Adventures of Lolo.zip")[0], "sem_marcacao")

    def test_marcacoes_goodtools_nao_sao_hack(self):
        for nome in (
            "Card Sharks (USA) (Proto).zip",
            "Dinosaur (USA) (Beta).zip",
            "Pocket Smash Out (Europe) (Unl).zip",
            "Super Mario Bros. Deluxe (USA, Europe).zip",
            "Mega SWIV (E) [f1].zip",
            "Runark (JUE) [p1][!].zip",
            "Jurassic Boy 2 (World) (Unl) [b].zip",
            "Idol Hanafuda Fan Club (J).zip",
            "Killing Game Show - 1993 Remix (JUE).zip",
        ):
            with self.subTest(nome=nome):
                self.assertEqual(au.classificar(nome)[0], "original")


class Revisao(unittest.TestCase):
    def test_rev_e_versao(self):
        self.assertEqual(au.rev_de("Game (Rev 2).zip"), 2.0)
        self.assertEqual(au.rev_de("Game (V1.2).zip"), 1.2)
        self.assertEqual(au.rev_de("Game (U).zip"), 0.0)


class ChecagemDeCapa(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def arquivo(self, nome, conteudo):
        p = self.dir / nome
        p.write_bytes(conteudo)
        return p

    def test_png_valido_passa(self):
        p = self.arquivo("a.png", au.PNG_ASSINATURA + b"\x00" * 600)
        self.assertIsNone(au.classificar_capa(p))

    def test_ponteiro_de_texto_com_alvo_ausente(self):
        p = self.arquivo("b.png", b"Dr. Mario (USA) (Beta).png")
        self.assertIn("alvo ausente", au.classificar_capa(p))

    def test_ponteiro_de_texto_com_alvo_existente(self):
        self.arquivo("alvo.png", au.PNG_ASSINATURA + b"\x00" * 600)
        p = self.arquivo("c.png", b"alvo.png")
        self.assertIn("alvo existe", au.classificar_capa(p))

    def test_jpeg_com_extensao_png(self):
        p = self.arquivo("d.png", b"\xff\xd8\xff\xe0" + b"\x00" * 600)
        self.assertIn("JPEG", au.classificar_capa(p))

    def test_mpeg_com_extensao_png(self):
        p = self.arquivo("e.png", b"\x00\x00\x01\xba" + b"\x00" * 600)
        self.assertIn("MPEG", au.classificar_capa(p))

    def test_binario_sem_cabecalho(self):
        p = self.arquivo("f.png", bytes(range(256)) * 3)
        self.assertIn("binário", au.classificar_capa(p))

    def test_arquivo_vazio(self):
        p = self.arquivo("g.png", b"")
        self.assertEqual(au.classificar_capa(p), "arquivo vazio")

    def test_capa_invalida_nao_conta_como_capa(self):
        img = self.dir / "img"
        img.mkdir()
        (img / "Jogo (U).png").write_bytes(b"Outro Jogo (U).png")
        (img / "Bom (U).png").write_bytes(au.PNG_ASSINATURA + b"\x00" * 600)
        roms = [self.dir / "Jogo (U).zip", self.dir / "Bom (U).zip"]
        for r in roms:
            r.write_bytes(b"x")
        mapa = {"Jogo (U).zip": "Jogo (U).png", "Bom (U).zip": "Bom (U).png"}
        problemas, com_capa = au.analisar_capas("teste", self.dir, roms, mapa)
        self.assertEqual(com_capa, {"Bom (U).zip"})
        capas = [p for p in problemas if p["problema"] == "capa_invalida"]
        self.assertEqual([p["rom"] for p in capas], ["Jogo (U).zip"])
        self.assertIn("ponteiro", capas[0]["detalhe"])


class Execucao(unittest.TestCase):
    def test_cartao_falso_gera_relatorio_sem_alterar_a_raiz(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cartao = base / "cartao"
            gba = cartao / "gba"
            (gba / "img").mkdir(parents=True)
            (gba / "Casper (USA).zip").write_bytes(b"nao-e-zip")
            (gba / "Casper (Europe).zip").write_bytes(b"outro")
            (gba / "Battle Mania (U) [h1].zip").write_bytes(b"hack")
            (gba / "img" / "Casper (USA).png").write_bytes(b"png")
            (gba / "gamelist.xml").write_text(
                "<gameList><game><path>./Casper (USA).zip</path>"
                "<image>./img/Casper (USA).png</image></game></gameList>",
                encoding="utf-8",
            )
            antes = sorted(str(p.relative_to(cartao)) for p in cartao.rglob("*"))
            saida = base / "saida"

            argv = sys.argv
            try:
                sys.argv = ["auditar_roms.py", str(cartao), "--saida", str(saida)]
                self.assertEqual(au.main(), 0)
            finally:
                sys.argv = argv

            depois = sorted(str(p.relative_to(cartao)) for p in cartao.rglob("*"))
            self.assertEqual(antes, depois, "a raiz do cartão não pode ser alterada")
            relatorio = (saida / "relatorio.md").read_text(encoding="utf-8")
            self.assertIn("| gba |", relatorio)
            self.assertIn("Battle Mania (U) [h1].zip", (saida / "classificacao.csv").read_text(encoding="utf-8"))
            self.assertIn("zip_invalido", (saida / "outras.csv").read_text(encoding="utf-8"))

    def test_saida_dentro_do_cartao_e_recusada(self):
        with tempfile.TemporaryDirectory() as tmp:
            cartao = Path(tmp)
            argv = sys.argv
            try:
                sys.argv = ["auditar_roms.py", str(cartao), "--saida", str(cartao / "x")]
                with self.assertRaises(SystemExit):
                    au.main()
            finally:
                sys.argv = argv


if __name__ == "__main__":
    unittest.main()
