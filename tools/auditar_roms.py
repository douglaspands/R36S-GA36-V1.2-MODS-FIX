#!/usr/bin/env python3
"""Auditoria somente leitura das ROMs de um cartão R36S.

Uso (a partir da raiz do projeto):
    uv run python -I tools/auditar_roms.py /run/media/douglas/R36-ROMS
    uv run python -I tools/auditar_roms.py <raiz> --saida var/auditoria-roms

Não grava, move nem apaga nada dentro da raiz informada. Só escreve na pasta de
saída (padrão: var/auditoria-roms/ do projeto): relatorio.md e quatro CSVs.

Classificação de hacks é heurística. Traduções têm prioridade: um arquivo com
marcação de tradução nunca é sugerido para remoção.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

PASTAS_IGNORADAS = {
    "bios", "bezels", "themes", "downloads", "screenshots", "savestates",
    "splash", "BGM", "ports", "ports_scripts", "pgo", "img",
    "System Volume Information",
}

EXT_ROM = {
    ".zip", ".7z", ".nes", ".fds", ".unf", ".sfc", ".smc", ".swc", ".gb", ".gbc",
    ".gba", ".md", ".gen", ".smd", ".bin", ".32x", ".pce", ".sgx", ".cue", ".chd",
    ".iso", ".sms", ".gg", ".sg", ".col", ".n64", ".z64", ".v64", ".a26", ".a78",
    ".lnx", ".ws", ".wsc", ".ngp", ".ngc", ".ngpc", ".m3u", ".pbp", ".cdi", ".love",
    ".dsk", ".rom", ".jag", ".vb", ".vec", ".min", ".mx1", ".mx2", ".zx", ".tzx", ".tap",
    ".nds", ".fs",
}

RE_ACESSORIO = re.compile(
    r"\.(srm|sav|rtc|state\d*|state\.auto|auto|nv|eep|fla|mcr|bak|xml|png|jpg|jpeg|"
    r"bmp|gif|txt|cfg|opt|ini|log|json|csv|rtf|pdf|mp4|mp3|ogg|wav|lnk|sha1|crc)$",
    re.IGNORECASE,
)
RE_SAVE = re.compile(r"^(.*?)\.(srm|sav|state\d*|state\.auto|auto)(\.png)?$", re.IGNORECASE)

RE_TAG = re.compile(r"\s*[\(\[][^\)\]]*[\)\]]")
RE_ARTIGO = re.compile(r"^(the|a|an|o|os|as|el|la|les|der|die|das)\s+")
RE_ARTIGO_SUFIXO = re.compile(r"^(.*?),\s*(the|a|an)\b", re.IGNORECASE)
RE_REGIAO = re.compile(
    r"[\(\[](?:[UEJW]{1,3}|BR|USA|Europe|Japan|World|Brazil|Asia|Korea|Australia|"
    r"Germany|France|Spain|Italy|Sweden|Netherlands|Canada|China|Taiwan|Hong Kong|JP)\b",
    re.IGNORECASE,
)
RE_REV = re.compile(r"\((?:Rev|REV)\s*(\d+)\)|\(V(\d+(?:\.\d+)*)\)", re.IGNORECASE)
RE_TRAD = re.compile(
    r"tradu|translat|pt[-_ ]?br|portugu|[\[\(]T[+_\-][A-Za-z]+|\bT[+_\-][A-Za-z]{2,}\b|\bENG\b|\(Por\)",
    re.IGNORECASE,
)
RE_HACK_FORTE = re.compile(
    r"\(hack|\[h\d*[a-z]*\]|\bhack\b|\bkaizo\b|rom ?hack", re.IGNORECASE
)
CAMPOS_CLASSE = ("original", "traducao", "hack_provavel", "sem_marcacao")


def titulo_normal(nome: str) -> str:
    """Título sem tags, em minúsculas e só com letras e números."""
    s = Path(nome).stem
    s = RE_TAG.sub("", s).strip()
    # "Legend of Zelda, The - ..." vira "The Legend of Zelda - ..." antes de tirar o artigo.
    s = RE_ARTIGO_SUFIXO.sub(r"\2 \1", s)
    s = s.lower().replace("&", " and ")
    s = RE_ARTIGO.sub("", s)
    return re.sub(r"[^a-z0-9]", "", s)


def rev_de(nome: str) -> float:
    m = RE_REV.search(nome)
    if not m:
        return 0.0
    try:
        return float(m.group(1) or m.group(2))
    except ValueError:
        return 0.0


def classificar(nome: str) -> tuple[str, str]:
    m = RE_TRAD.search(nome)
    if m:
        return "traducao", f"marcação de tradução ({m.group(0).strip()})"
    m = RE_HACK_FORTE.search(nome)
    if m:
        return "hack_provavel", f"marcação de hack ({m.group(0).strip()})"
    # Unl, Beta, Proto, Deluxe, [f], [p], [c], [b] e nomes como "Fan Club" ou "Remix"
    # são jogos reais (ou cópias deles), não hacks: ficam como original.
    if not (RE_REGIAO.search(nome) or "[!]" in nome or RE_REV.search(nome)):
        return "sem_marcacao", "sem região, sem [!] e sem revisão (nome sem padrão)"
    return "original", ""


def pontuar(m: dict) -> float:
    """Pontuação para escolher a versão a manter num grupo de duplicados."""
    base = {"original": 5, "traducao": 5, "sem_marcacao": 1, "hack_provavel": -10}[m["classe"]]
    nome = m["arquivo"]
    if "[!]" in nome:
        base += 3
    if re.search(r"\((U|USA|W|World|UE|EU)\b", nome, re.IGNORECASE):
        base += 2
    elif re.search(r"\(E\b|Europe", nome, re.IGNORECASE):
        base += 1
    if m["tem_capa"]:
        base += 2
    base += min(m["rev"], 5)
    return base


def ler_gamelist(pasta: Path) -> tuple[dict | None, str | None]:
    """Devolve (mapa nome_da_rom -> nome_da_imagem_ou_None, erro)."""
    arq = pasta / "gamelist.xml"
    if not arq.is_file():
        return None, "gamelist_ausente"
    try:
        raiz = ET.parse(arq).getroot()
    except ET.ParseError as exc:
        return None, f"gamelist_invalido ({exc})"
    mapa: dict[str, str | None] = {}
    for jogo in raiz.iter("game"):
        caminho = (jogo.findtext("path") or "").strip()
        imagem = (jogo.findtext("image") or "").strip()
        if caminho:
            mapa[Path(caminho).name] = Path(imagem).name if imagem else None
    return mapa, None


def listar_roms(pasta: Path) -> list[Path]:
    arquivos = sorted(p for p in pasta.iterdir() if p.is_file() and not p.name.startswith("."))
    nomes = {p.name for p in arquivos}
    roms = []
    for p in arquivos:
        ext = p.suffix.lower()
        if ext not in EXT_ROM:
            continue
        # PSX: o .bin do par .cue/.bin é a mesma jogo; conta só o .cue.
        if ext == ".bin" and f"{p.stem}.cue" in nomes:
            continue
        roms.append(p)
    return roms


def sha1(p: Path) -> str:
    h = hashlib.sha1()
    with p.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


PNG_ASSINATURA = b"\x89PNG\r\n\x1a\n"


def classificar_capa(caminho: Path) -> str | None:
    """None se a capa tem cabeçalho PNG; senão, o motivo de não ser imagem.

    Checagem local: lê só o começo do arquivo (e o arquivo inteiro quando
    ele é pequeno, para achar ponteiros de texto). Não abre a imagem.
    """
    with caminho.open("rb") as f:
        inicio = f.read(512)
    if inicio.startswith(PNG_ASSINATURA):
        return None
    if not inicio:
        return "arquivo vazio"
    if len(inicio) < 512:  # arquivo inteiro coube na leitura
        try:
            alvo = inicio.decode("utf-8").strip()
        except UnicodeDecodeError:
            alvo = ""
        if alvo and "\n" not in alvo:
            existe = (caminho.parent / alvo).is_file()
            estado = "alvo existe" if existe else "alvo ausente"
            return f"ponteiro de texto para '{alvo}' ({estado})"
    for assinatura, tipo in (
        (b"\xff\xd8\xff", "JPEG"),
        (b"GIF8", "GIF"),
        (b"RIFF", "WEBP"),
        (b"\x00\x00\x01\xba", "MPEG-PS"),
    ):
        if inicio.startswith(assinatura):
            return f"{tipo} com extensão .png"
    return "binário sem cabeçalho PNG (corrompido ou outro formato)"


def analisar_capas(sistema: str, pasta: Path, roms: list[Path], mapa: dict | None):
    """Devolve (linhas de problema, nomes de ROM com capa válida)."""
    imgdir = pasta / "img"
    pngs = {p.name: p.stat().st_size for p in imgdir.iterdir() if p.is_file()} if imgdir.is_dir() else {}
    invalidas: dict[str, str] = {}
    if imgdir.is_dir():
        for nome in pngs:
            motivo = classificar_capa(imgdir / nome)
            if motivo:
                invalidas[nome] = motivo
    # Capa inválida não conta como capa existente.
    stems_png = {Path(n).stem: n for n in pngs if n not in invalidas}
    problemas: list[dict] = []
    com_capa: set[str] = set()
    referenciadas: set[str] = set()
    nomes_roms = {r.name for r in roms}
    stems_roms = {r.stem for r in roms}

    def add(rom: str, problema: str, detalhe: str = ""):
        problemas.append({"sistema": sistema, "rom": rom, "problema": problema, "detalhe": detalhe})

    for r in roms:
        existe_png_mesmo_nome = r.stem in stems_png
        if mapa is None or r.name not in mapa:
            if existe_png_mesmo_nome:
                add(r.name, "capa_existe_sem_entrada_no_gamelist", stems_png[r.stem])
            else:
                add(r.name, "sem_capa", "sem entrada no gamelist e sem imagem")
            continue
        img = mapa[r.name]
        if img is None:
            if existe_png_mesmo_nome:
                add(r.name, "capa_existe_sem_referencia_no_gamelist", stems_png[r.stem])
            else:
                add(r.name, "sem_capa", "entrada sem <image>")
            continue
        referenciadas.add(img)
        if img not in pngs:
            add(r.name, "imagem_referenciada_ausente", img)
        elif pngs[img] == 0:
            add(r.name, "imagem_vazia", img)
        elif img in invalidas:
            add(r.name, "capa_invalida", invalidas[img])
        else:
            com_capa.add(r.name)

    for nome in sorted(mapa or {}):
        if nome not in nomes_roms:
            add(nome, "entrada_gamelist_sem_rom", "ROM citada no gamelist não está no cartão")

    for png, tamanho in sorted(pngs.items()):
        if png in invalidas:
            # Capa referenciada já saiu como capa_invalida na linha da ROM.
            if png not in referenciadas:
                add(png, "capa_invalida", invalidas[png])
        elif tamanho == 0:
            add(png, "png_vazio", "arquivo de imagem com 0 bytes")
        elif png not in referenciadas and Path(png).stem not in stems_roms:
            add(png, "png_orfao", "imagem sem ROM correspondente")

    return problemas, com_capa


def pasta_de_sistemas(raiz: Path) -> list[Path]:
    return sorted(
        p for p in raiz.iterdir()
        if p.is_dir() and p.name not in PASTAS_IGNORADAS and not p.name.startswith(".")
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Auditoria somente leitura das ROMs do R36S.")
    ap.add_argument("raiz", help="Ponto de montagem da partição R36-ROMS")
    ap.add_argument(
        "--saida",
        default=str(Path(__file__).resolve().parent.parent / "var" / "auditoria-roms"),
        help="Pasta de saída (fora do cartão)",
    )
    args = ap.parse_args()

    raiz = Path(args.raiz).resolve()
    saida = Path(args.saida).resolve()
    if not raiz.is_dir():
        sys.exit(f"Raiz não encontrada: {raiz}")
    if saida == raiz or raiz in saida.parents:
        sys.exit("A pasta de saída não pode ficar dentro do cartão.")
    saida.mkdir(parents=True, exist_ok=True)

    capas_linhas: list[dict] = []
    outras: list[dict] = []
    registros: list[dict] = []
    resumo: dict[str, dict] = {}

    def outra(sistema: str, categoria: str, arquivo: str, detalhe: str = ""):
        outras.append({"sistema": sistema, "categoria": categoria, "arquivo": arquivo, "detalhe": detalhe})

    for rom_raiz in sorted(p for p in raiz.iterdir() if p.is_file() and p.suffix.lower() in EXT_ROM):
        outra("(raiz)", "rom_na_raiz_do_cartao", rom_raiz.name)

    for pasta in pasta_de_sistemas(raiz):
        sistema = pasta.name
        roms = listar_roms(pasta)
        mapa, erro = ler_gamelist(pasta)
        if erro:
            outra(sistema, erro.split(" ")[0], "gamelist.xml", erro)
        if (pasta / "gamelist.xml.bak").exists():
            outra(sistema, "gamelist_bak_existe", "gamelist.xml.bak")

        nomes_roms = {r.name for r in roms}
        stems_roms = {r.stem for r in roms}

        for p in sorted(pasta.iterdir()):
            if not p.is_file() or p.name.startswith("."):
                continue
            ext = p.suffix.lower()
            if p.name in ("gamelist.xml", "gamelist.xml.bak") or RE_ACESSORIO.search(p.name):
                m = RE_SAVE.match(p.name)
                if m and not (m.group(1) in nomes_roms or m.group(1) in stems_roms):
                    outra(sistema, "save_orfao", p.name, "save sem ROM correspondente")
                continue
            if ext not in EXT_ROM:
                outra(sistema, "extensao_desconhecida", p.name, ext or "(sem extensão)")

        if not roms:
            outra(sistema, "pasta_sem_roms", sistema)
            resumo[sistema] = {"roms": 0, "com_capa": 0}
            continue

        problemas, com_capa = analisar_capas(sistema, pasta, roms, mapa)
        capas_linhas.extend(problemas)

        contagem = Counter()
        for r in roms:
            if r.name not in nomes_roms:
                continue
            if r.suffix.lower() == ".zip":
                try:
                    with zipfile.ZipFile(r) as z:
                        z.namelist()
                except (zipfile.BadZipFile, OSError) as exc:
                    outra(sistema, "zip_invalido", r.name, str(exc))
            tamanho = r.stat().st_size
            if tamanho == 0:
                outra(sistema, "arquivo_vazio", r.name)
            if "  " in r.name or r.name != r.name.strip() or re.search(r"\s\.\w+$", r.name):
                outra(sistema, "nome_com_espaco", r.name)

            classe, motivo = classificar(r.name)
            contagem[classe] += 1
            registros.append({
                "sistema": sistema,
                "arquivo": r.name,
                "path": r,
                "tamanho": tamanho,
                "classe": classe,
                "motivo": motivo,
                "titulo": titulo_normal(r.name),
                "tem_capa": r.name in com_capa,
                "rev": rev_de(r.name),
            })

        resumo[sistema] = {
            "roms": len(roms),
            "com_capa": len(com_capa),
            "original": contagem["original"],
            "traducao": contagem["traducao"],
            "hack_provavel": contagem["hack_provavel"],
            "sem_marcacao": contagem["sem_marcacao"],
        }

    # Hash só onde há indício de cópia: mesmo tamanho no cartão ou mesmo título no sistema.
    tamanhos = Counter(r["tamanho"] for r in registros)
    titulos_sistema = Counter((r["sistema"], r["titulo"]) for r in registros)
    precisa_hash = {
        r["path"] for r in registros
        if tamanhos[r["tamanho"]] > 1 or (titulos_sistema[(r["sistema"], r["titulo"])] > 1 and r["titulo"])
    }
    hashes = {p: sha1(p) for p in precisa_hash}
    for r in registros:
        r["sha1"] = hashes.get(r["path"], "")

    # Duplicados dentro do mesmo sistema (mesmo título normalizado).
    grupos: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in registros:
        if r["titulo"]:
            grupos[(r["sistema"], r["titulo"])].append(r)

    duplicados: list[dict] = []
    grupo_id = 0
    for (sistema, titulo), membros in sorted(grupos.items()):
        if len(membros) < 2:
            continue
        grupo_id += 1
        for m in membros:
            m["score"] = pontuar(m)
        candidatos = [m for m in membros if m["classe"] in ("original", "sem_marcacao")]
        melhor = max(candidatos, key=lambda m: m["score"]) if candidatos else None
        for m in membros:
            if m["classe"] == "traducao":
                decisao = "manter (tradução)"
            elif m is melhor:
                decisao = "manter"
            elif m["classe"] == "hack_provavel":
                decisao = "remover (hack)"
            elif melhor and m["sha1"] and m["sha1"] == melhor["sha1"]:
                decisao = "remover (cópia idêntica)"
            else:
                decisao = "revisar (versão diferente)"
            duplicados.append({
                "tipo": "mesmo_sistema",
                "grupo": grupo_id,
                "sistema": sistema,
                "arquivo": m["arquivo"],
                "classe": m["classe"],
                "pontuacao": f"{m['score']:.1f}",
                "tem_capa": "sim" if m["tem_capa"] else "não",
                "sha1": m["sha1"],
                "decisao": decisao,
            })

    # Cópias idênticas em sistemas diferentes (informativo).
    por_sha: dict[str, list[dict]] = defaultdict(list)
    for r in registros:
        if r["sha1"]:
            por_sha[r["sha1"]].append(r)
    for sha, membros in sorted(por_sha.items()):
        if len({m["sistema"] for m in membros}) > 1:
            grupo_id += 1
            for m in membros:
                duplicados.append({
                    "tipo": "copia_identica_outro_sistema",
                    "grupo": grupo_id,
                    "sistema": m["sistema"],
                    "arquivo": m["arquivo"],
                    "classe": m["classe"],
                    "pontuacao": "",
                    "tem_capa": "sim" if m["tem_capa"] else "não",
                    "sha1": sha,
                    "decisao": "informativo",
                })

    # Mesmo jogo em sistemas diferentes (informativo; gb/gbc é esperado em alguns casos).
    por_titulo: dict[str, list[dict]] = defaultdict(list)
    for r in registros:
        if r["titulo"]:
            por_titulo[r["titulo"]].append(r)
    for titulo, membros in sorted(por_titulo.items()):
        if len({m["sistema"] for m in membros}) > 1:
            grupo_id += 1
            for m in membros:
                duplicados.append({
                    "tipo": "mesmo_jogo_outro_sistema",
                    "grupo": grupo_id,
                    "sistema": m["sistema"],
                    "arquivo": m["arquivo"],
                    "classe": m["classe"],
                    "pontuacao": "",
                    "tem_capa": "sim" if m["tem_capa"] else "não",
                    "sha1": m["sha1"],
                    "decisao": "informativo",
                })

    # Gravação dos CSVs.
    def escrever_csv(nome: str, linhas: list[dict], colunas: list[str]):
        with (saida / nome).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=colunas, extrasaction="ignore")
            w.writeheader()
            w.writerows(linhas)

    escrever_csv("capas.csv", capas_linhas, ["sistema", "rom", "problema", "detalhe"])
    escrever_csv(
        "duplicados.csv", duplicados,
        ["tipo", "grupo", "sistema", "arquivo", "classe", "pontuacao", "tem_capa", "sha1", "decisao"],
    )
    escrever_csv(
        "classificacao.csv",
        [{"sistema": r["sistema"], "arquivo": r["arquivo"], "classe": r["classe"], "motivo": r["motivo"]}
         for r in registros],
        ["sistema", "arquivo", "classe", "motivo"],
    )
    escrever_csv("outras.csv", outras, ["sistema", "categoria", "arquivo", "detalhe"])

    gerar_relatorio(saida, raiz, resumo, capas_linhas, duplicados, registros, outras)
    gerar_pacote_de_acoes(saida, raiz, resumo, capas_linhas, duplicados, registros, outras)

    total = sum(v["roms"] for v in resumo.values())
    print(f"ROMs analisadas: {total}")
    print(f"Relatório: {saida / 'relatorio.md'}")
    return 0


def gerar_relatorio(saida, raiz, resumo, capas_linhas, duplicados, registros, outras):
    hoje = datetime.date.today().isoformat()
    L: list[str] = []
    L.append(f"# Auditoria das ROMs — {raiz}")
    L.append("")
    L.append(f"Gerado em {hoje}. Somente leitura: nada foi alterado no cartão.")
    L.append("")
    L.append("## Resumo por sistema")
    L.append("")
    L.append("| Sistema | ROMs | Com capa | Sem capa | Originais | Traduções | Hack provável | Sem marcação |")
    L.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for sistema, v in sorted(resumo.items(), key=lambda kv: -kv[1]["roms"]):
        if v["roms"] == 0:
            L.append(f"| {sistema} | 0 | - | - | - | - | - | - |")
            continue
        L.append(
            f"| {sistema} | {v['roms']} | {v['com_capa']} | {v['roms'] - v['com_capa']} | "
            f"{v.get('original', 0)} | {v.get('traducao', 0)} | {v.get('hack_provavel', 0)} | "
            f"{v.get('sem_marcacao', 0)} |"
        )
    L.append("")

    L.append("## Capas")
    L.append("")
    cont = Counter(l["problema"] for l in capas_linhas)
    for problema, n in cont.most_common():
        L.append(f"- `{problema}`: {n}")
    L.append("")
    for problema in ("sem_capa", "imagem_referenciada_ausente", "capa_invalida", "png_orfao", "entrada_gamelist_sem_rom"):
        exemplos = [l for l in capas_linhas if l["problema"] == problema][:15]
        if exemplos:
            L.append(f"Exemplos de `{problema}`:")
            for e in exemplos:
                L.append(f"- {e['sistema']}: {e['rom']} ({e['detalhe']})")
            L.append("")

    L.append("## Duplicados")
    L.append("")
    mesmo = [d for d in duplicados if d["tipo"] == "mesmo_sistema"]
    grupos_mesmo = {d["grupo"] for d in mesmo}
    decisoes = Counter(d["decisao"] for d in mesmo)
    L.append(f"- Grupos de mesmo título no mesmo sistema: {len(grupos_mesmo)}")
    for dec, n in decisoes.most_common():
        L.append(f"  - {dec}: {n}")
    L.append(
        f"- Cópias idênticas (sha1) em sistemas diferentes: "
        f"{len({d['grupo'] for d in duplicados if d['tipo'] == 'copia_identica_outro_sistema'})} grupos"
    )
    L.append(
        f"- Mesmo jogo em sistemas diferentes (informativo): "
        f"{len({d['grupo'] for d in duplicados if d['tipo'] == 'mesmo_jogo_outro_sistema'})} grupos"
    )
    L.append("")
    L.append("Primeiros grupos do mesmo sistema:")
    for g in sorted(grupos_mesmo)[:20]:
        membros = [d for d in mesmo if d["grupo"] == g]
        L.append(f"- Grupo {g} ({membros[0]['sistema']}):")
        for d in membros:
            L.append(f"  - {d['arquivo']} [{d['classe']}, capa: {d['tem_capa']}] → {d['decisao']}")
    L.append("")

    L.append("## Hacks e classificação")
    L.append("")
    cont_cls = Counter(r["classe"] for r in registros)
    for classe in CAMPOS_CLASSE:
        L.append(f"- `{classe}`: {cont_cls.get(classe, 0)}")
    L.append("")
    for classe in ("hack_provavel", "sem_marcacao"):
        exemplos = [r for r in registros if r["classe"] == classe][:40]
        if exemplos:
            L.append(f"Exemplos de `{classe}` (lista completa em `classificacao.csv`):")
            for r in exemplos:
                L.append(f"- {r['sistema']}: {r['arquivo']} — {r['motivo']}")
            L.append("")

    L.append("## Outras inconsistências")
    L.append("")
    cont_out = Counter(o["categoria"] for o in outras)
    for cat, n in cont_out.most_common():
        L.append(f"- `{cat}`: {n}")
    L.append("")
    for cat in cont_out:
        exemplos = [o for o in outras if o["categoria"] == cat][:10]
        L.append(f"Exemplos de `{cat}`:")
        for o in exemplos:
            L.append(f"- {o['sistema']}: {o['arquivo']} {o['detalhe']}".rstrip())
        L.append("")

    L.append("## Limitações")
    L.append("")
    L.append("- Sem DAT do No-Intro: 'verificado' é só a marcação `[!]` do nome, não o hash.")
    L.append("- Títulos com numeral romano e arábico (II e 2) não são agrupados.")
    L.append("- A classificação de hack é por nome. Títulos sem nenhuma marcação ficam em `sem_marcacao`, não são suspeitos.")
    L.append("- Traduções nunca são sugeridas para remoção, mesmo que também sejam hacks.")
    L.append("")
    L.append("## Arquivos")
    L.append("")
    for nome in ("capas.csv", "duplicados.csv", "classificacao.csv", "outras.csv"):
        L.append(f"- `{saida / nome}`")
    L.append("")

    (saida / "relatorio.md").write_text("\n".join(L), encoding="utf-8")


SUGESTOES_MD = """# Sugestões de correção do cartão R36-ROMS

Cada item abaixo tem uma lista pronta em `acoes/`. Nada disto foi aplicado.
Para pedir a aplicação, diga o item pelo número (por exemplo, "aplicar 3").

1. **Regenerar gamelists** (`acoes/gamelists_regenerar.txt`). Sistemas com
   capas que existem em `img/` mas não estão no gamelist, ou entradas sem `<image>`.
   Ação: refazer o gamelist só com as capas existentes e manter as entradas válidas.
2. **Capas faltando ou inválidas** (`acoes/capas_faltando.csv`). Inclui capas que
   não são imagem (ponteiros de texto, binários corrompidos). Ação: baixar com o
   scraper do EmulationStation, ou remover a entrada de imagem que não existe.
3. **Hacks prováveis, quarentena** (`acoes/hacks_quarentena.csv`). Marcação forte
   de hack (`[h1]`, `(Hack)`, `Kaizo`). Ação: mover para fora do cartão, com backup
   prévio da p1 e aprovação de cada item.
4. **Duplicados** (`acoes/duplicados_remover_ou_revisar.csv`). Ação: manter a
   versão indicada como "manter", remover ou revisar os demais. Traduções
   ficam sempre.
5. **Outras inconsistências** (`acoes/outras_inconsistencias.csv`). Pastas vazias,
   nomes com espaço, `gamelist.xml.bak`. Ação: limpar só depois de conferir
   o `es_systems.cfg`.

6. **Capas trocadas** (`tools/conferir_capas_iguais.py` → `var/auditoria-roms/conferencia-capas/capas_compartilhadas.md`).
   Capa idêntica (mesmo sha1) usada por títulos diferentes: pelo menos um está
   errado. Ação: refazer a capa dos títulos do grupo com o scraper. Compilações
   (ex.: MegaGames 3in1) e o mesmo jogo em outra região não contam.
   Limite: só pega capa repetida. Capa trocada que aparece uma vez só precisa de
   conferência visual.
   O OCR (`tools/conferir_capas_ocr.py`) não serve para decidir: na amostra de 8
   suspeitas, todas as 8 estavam corretas (logo estilizado e título em japonês).

Traduções (`[T+...]`, `(pt_BR)`, `ENG`) nunca entram em remoção.
Unl, Beta, Proto, Deluxe, `[f]`, `[p]`, `[c]` e `[b]` são jogos reais (ou cópias
deles), não hacks: ficam como original. Já removidos do cartão: GameShark Online
(Unl) e os bad dumps `[b]` do GBC (cópia em `var/auditoria-roms/quarentena/`).
Mantido: `pcengine/Vigilante (U) [T+Por100] [b1]`, que é tradução.
Sem marcação (`classificacao.csv`, classe `sem_marcacao`) não é suspeito.
Hack sem marcação não é detectável pelo nome: precisaria de um DAT do No-Intro.
"""


def gerar_pacote_de_acoes(saida, raiz, resumo, capas_linhas, duplicados, registros, outras):
    """Listas de ação e índice para pedir a aplicação das sugestões depois."""
    acoes = saida / "acoes"
    acoes.mkdir(parents=True, exist_ok=True)

    def escrever(nome: str, linhas: list[dict], colunas: list[str]):
        with (acoes / nome).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=colunas, extrasaction="ignore")
            w.writeheader()
            w.writerows(linhas)

    escrever(
        "hacks_quarentena.csv",
        [{"sistema": r["sistema"], "arquivo": r["arquivo"], "motivo": r["motivo"],
          "acao": "mover para quarentena após confirmação"}
         for r in registros if r["classe"] == "hack_provavel"],
        ["sistema", "arquivo", "motivo", "acao"],
    )
    escrever(
        "duplicados_remover_ou_revisar.csv",
        [d for d in duplicados if d["tipo"] == "mesmo_sistema"
         and d["decisao"] not in ("manter", "manter (tradução)")],
        ["grupo", "sistema", "arquivo", "classe", "pontuacao", "tem_capa", "sha1", "decisao"],
    )
    escrever(
        "capas_faltando.csv",
        [{**l, "acao": {
            "sem_capa": "baixar capa ou remover entrada",
            "imagem_referenciada_ausente": "baixar capa ou remover <image>",
            "capa_existe_sem_entrada_no_gamelist": "regenerar gamelist",
            "capa_existe_sem_referencia_no_gamelist": "regenerar gamelist",
            "png_orfao": "remover PNG órfão ou ligar à ROM",
            "png_vazio": "baixar de novo",
            "capa_invalida": "refazer capa (o arquivo não é imagem)",
            "entrada_gamelist_sem_rom": "remover entrada do gamelist",
        }.get(l["problema"], "revisar")} for l in capas_linhas],
        ["sistema", "rom", "problema", "detalhe", "acao"],
    )
    sistemas_gamelist = sorted({
        l["sistema"] for l in capas_linhas
        if l["problema"] in ("capa_existe_sem_entrada_no_gamelist",
                             "capa_existe_sem_referencia_no_gamelist",
                             "sem_capa", "imagem_referenciada_ausente", "entrada_gamelist_sem_rom")
    })
    (acoes / "gamelists_regenerar.txt").write_text(
        "# Sistemas cujo gamelist.xml precisa ser refeito\n" + "\n".join(sistemas_gamelist) + "\n",
        encoding="utf-8",
    )
    escrever(
        "outras_inconsistencias.csv",
        [{**o, "acao": {
            "pasta_sem_roms": "conferir es_systems.cfg antes de remover",
            "nome_com_espaco": "renomear",
            "gamelist_bak_existe": "remover .bak após conferir",
            "gamelist_ausente": "criar gamelist se a pasta tiver ROMs",
            "zip_invalido": "substituir arquivo",
            "rom_na_raiz_do_cartao": "mover para a pasta do sistema",
        }.get(o["categoria"], "revisar")} for o in outras],
        ["sistema", "categoria", "arquivo", "detalhe", "acao"],
    )

    (saida / "SUGESTOES.md").write_text(SUGESTOES_MD, encoding="utf-8")

    indice = f"""# Auditoria das ROMs — índice

Gerado a partir de `{raiz}` pelo `tools/auditar_roms.py`.
Para regerar: `uv run python -I tools/auditar_roms.py <raiz do cartão>`.

- `relatorio.md`: resumo completo com números e exemplos.
- `SUGESTOES.md`: as sugestões numeradas, para pedir a aplicação de cada uma.
- `acoes/`: listas prontas por tipo de ação (ver `SUGESTOES.md`).
- `classificacao.csv`: classe (original, traducao, hack_provavel, incerto, sem_marcacao) de cada ROM.
- `capas.csv`: problemas de capa e gamelist.
- `duplicados.csv`: grupos de duplicados com decisão sugerida.
- `outras.csv`: pastas vazias, nomes, saves, zips inválidos.
"""
    (saida / "LEIAME.md").write_text(indice, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
