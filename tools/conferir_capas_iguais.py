#!/usr/bin/env python3
"""Acha capas com bytes idênticos usadas por títulos diferentes (sem OCR).

Uso (a partir da raiz do projeto):
    uv run python -I tools/conferir_capas_iguais.py /run/media/douglas/R36-ROMS

Uma capa só pode ser de um jogo. Se o mesmo arquivo (mesmo sha1) aparece em
ROMs de títulos diferentes, pelo menos uma está com capa trocada. Mesmo título
em regiões ou revisões diferentes não conta (é o mesmo jogo). Compilações
(ex.: "MegaGames 3in1") aparecem como título diferente, então são revisadas à parte.

Só lê o cartão. Grava em --saida (padrão: var/auditoria-roms/conferencia-capas/).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import auditar_roms as au  # noqa: E402


def sha1(p: Path) -> str:
    h = hashlib.sha1()
    with p.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Capas idênticas usadas por títulos diferentes.")
    ap.add_argument("raiz")
    ap.add_argument(
        "--saida",
        default=str(Path(__file__).resolve().parent.parent / "var" / "auditoria-roms" / "conferencia-capas"),
    )
    args = ap.parse_args()

    raiz = Path(args.raiz).resolve()
    saida = Path(args.saida).resolve()
    if not raiz.is_dir():
        sys.exit(f"Raiz não encontrada: {raiz}")
    if saida == raiz or raiz in saida.parents:
        sys.exit("A pasta de saída não pode ficar dentro do cartão.")

    # (sha1 -> lista de (sistema, rom, capa))
    por_hash: dict[str, list[tuple[str, str, Path]]] = defaultdict(list)
    for pasta in au.pasta_de_sistemas(raiz):
        mapa, _erro = au.ler_gamelist(pasta)
        if not mapa:
            continue
        for rom in au.listar_roms(pasta):
            img = mapa.get(rom.name)
            if not img:
                continue
            caminho = pasta / "img" / img
            if not caminho.is_file() or au.classificar_capa(caminho) is not None:
                continue
            por_hash[sha1(caminho)].append((pasta.name, rom.name, caminho))

    linhas = []
    grupos = 0
    for h, membros in por_hash.items():
        if len(membros) < 2:
            continue
        titulos = {au.titulo_normal(rom) for _, rom, _ in membros}
        if len(titulos) < 2:
            continue  # mesmo jogo em outra região/revisão
        grupos += 1
        for sistema, rom, caminho in membros:
            outros = sorted({r for _, r, _ in membros if au.titulo_normal(r) != au.titulo_normal(rom)})
            linhas.append({
                "grupo": grupos,
                "sistema": sistema,
                "rom": rom,
                "capa": caminho.name,
                "titulo": au.titulo_normal(rom),
                "sha1": h,
                "dividida_com": " | ".join(outros[:5]),
            })

    saida.mkdir(parents=True, exist_ok=True)
    colunas = ["grupo", "sistema", "rom", "capa", "titulo", "sha1", "dividida_com"]
    with (saida / "capas_compartilhadas.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colunas)
        w.writeheader()
        w.writerows(linhas)

    md = [
        "# Capas idênticas usadas por títulos diferentes",
        "",
        f"Grupos: {grupos} | ROMs envolvidas: {len(linhas)}",
        "",
        "Cada grupo é uma capa usada por jogos com títulos diferentes. Pelo menos um",
        "dos títulos do grupo está com capa trocada (exceto compilações).",
        "",
    ]
    atual = None
    for l in linhas:
        if l["grupo"] != atual:
            atual = l["grupo"]
            md.append(f"- Grupo {atual} (capa `{l['capa']}`):")
        md.append(f"  - {l['sistema']}: {l['rom']}")
    (saida / "capas_compartilhadas.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Grupos de capa compartilhada por títulos diferentes: {grupos} ({len(linhas)} ROMs)")
    print(f"Detalhe: {saida / 'capas_compartilhadas.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
