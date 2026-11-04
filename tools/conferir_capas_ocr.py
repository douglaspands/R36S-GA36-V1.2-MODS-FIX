#!/usr/bin/env python3
"""Conferência de capas por OCR local (RapidOCR), numa amostra sorteada.

Uso (a partir da raiz do projeto):
    uv run --with rapidocr-onnxruntime python -I tools/conferir_capas_ocr.py \
        /run/media/douglas/R36-ROMS --amostra 400

Só lê o cartão. Grava o CSV e o resumo em --saida (padrão:
var/auditoria-roms/conferencia-capas/). O OCR roda na máquina, sem enviar nada
para fora.

Pontuação: fração das palavras do nome do jogo que aparecem no texto lido na
capa (com tolerância a erro de OCR). Abaixo de LIMITE, a capa vai para
"suspeita" e precisa de olho humano. "sem_texto" = o OCR não leu nada útil
(não é erro comprovado).
"""

from __future__ import annotations

import argparse
import csv
import difflib
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import auditar_roms as au  # noqa: E402

LIMITE = 0.5
STOP = {
    "the", "and", "for", "les", "des", "der", "die", "das", "del", "the", "with",
    "pt", "br", "en", "fr", "de", "es", "it", "nl", "sv", "dk", "fi", "jp", "usa",
}


def palavras_nome(nome_rom: str) -> list[str]:
    s = au.RE_TAG.sub(" ", Path(nome_rom).stem)
    s = re.sub(r"[^A-Za-z0-9]+", " ", s).lower()
    return [w for w in s.split() if len(w) >= 3 and w not in STOP]


def palavras_ocr(texto: str) -> list[str]:
    return [w for w in re.split(r"[^A-Za-z0-9]+", texto.lower()) if w]


def fracao_latina(texto: str) -> float:
    """Parte dos caracteres não-espaço que são letras ASCII."""
    nao_espaco = [c for c in texto if not c.isspace()]
    if not nao_espaco:
        return 0.0
    return sum(c.isascii() and c.isalpha() for c in nao_espaco) / len(nao_espaco)


def palavras_latinas_longas(texto: str) -> int:
    """Quantas palavras latinas de 4+ letras o OCR leu (base mínima para julgar)."""
    return sum(1 for w in palavras_ocr(texto) if len(w) >= 4 and w.isascii())


def pontuar(nome_rom: str, texto: str) -> float | None:
    pal = palavras_nome(nome_rom)
    if not pal:
        return None
    ocr = palavras_ocr(texto)
    junto = "".join(ocr)
    acertos = 0
    for w in pal:
        if w in junto or difflib.get_close_matches(w, ocr, n=1, cutoff=0.7):
            acertos += 1
    return acertos / len(pal)


def coletar(raiz: Path) -> list[tuple[str, str, Path]]:
    """Pares (sistema, ROM, capa) em que a capa é um PNG válido e está no gamelist."""
    pares = []
    for pasta in au.pasta_de_sistemas(raiz):
        mapa, _erro = au.ler_gamelist(pasta)
        if not mapa:
            continue
        for rom in au.listar_roms(pasta):
            img = mapa.get(rom.name)
            if not img:
                continue
            caminho = pasta / "img" / img
            if not caminho.is_file():
                continue
            if au.classificar_capa(caminho) is not None:
                continue
            pares.append((pasta.name, rom.name, caminho))
    return pares


def main() -> int:
    ap = argparse.ArgumentParser(description="Conferência de capas por OCR local.")
    ap.add_argument("raiz")
    ap.add_argument("--amostra", type=int, default=400)
    ap.add_argument("--semente", type=int, default=20260416)
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

    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        sys.exit("Falta o RapidOCR. Rode com: uv run --with rapidocr-onnxruntime python -I tools/conferir_capas_ocr.py ...")

    pool = coletar(raiz)
    rng = random.Random(args.semente)
    escolhidos = rng.sample(pool, min(args.amostra, len(pool)))
    motor = RapidOCR()

    linhas = []
    for sistema, rom, caminho in escolhidos:
        resultado, _ = motor(str(caminho))
        texto = " ".join(t for _, t, _ in (resultado or []))
        score = pontuar(rom, texto)
        if score is None:
            status = "sem_nome_util"
        elif len(texto.strip()) < 3:
            status = "sem_texto"
        elif fracao_latina(texto) < 0.5:
            status = "texto_nao_latino"
        elif palavras_latinas_longas(texto) < 2:
            status = "sem_base_para_julgar"
        elif score < LIMITE:
            status = "suspeita"
        else:
            status = "ok"
        linhas.append({
            "sistema": sistema,
            "rom": rom,
            "capa": caminho.name,
            "pontuacao": "" if score is None else f"{score:.2f}",
            "status": status,
            "texto_lido": texto[:160],
        })

    saida.mkdir(parents=True, exist_ok=True)
    with (saida / "amostra_ocr.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()) if linhas else ["sistema"])
        w.writeheader()
        w.writerows(linhas)

    contagem = {}
    for l in linhas:
        contagem[l["status"]] = contagem.get(l["status"], 0) + 1
    suspeitas = [l for l in linhas if l["status"] == "suspeita"]
    md = [
        "# Conferência de capas por OCR",
        "",
        f"Universo (capas PNG válidas no gamelist): {len(pool)}",
        f"Amostra sorteada: {len(escolhidos)} (semente {args.semente})",
        f"Limite de suspeita: pontuação < {LIMITE}",
        "",
        "## Resultado",
        "",
    ]
    md += [f"- `{k}`: {v}" for k, v in sorted(contagem.items())]
    md += ["", "## Suspeitas (conferir visualmente)", ""]
    md += [f"- {l['sistema']}: {l['rom']} (pontuação {l['pontuacao']}) — leu: {l['texto_lido'][:90]!r}"
           for l in suspeitas]
    (saida / "conferencia.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Universo: {len(pool)} | amostra: {len(escolhidos)}")
    print(contagem)
    print(f"Resumo: {saida / 'conferencia.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
