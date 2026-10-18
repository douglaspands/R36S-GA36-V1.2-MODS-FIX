"""./cores.sh — compila cores libretro para o A33 a partir de uma receita versionada
(cores/<core>/receita.toml), confere a ABI contra a imagem base, importa o perfil do PGO
e resume o registro térmico das sessões de avaliação."""

import csv
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tomllib
import zipfile
import zlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import REPO_ROOT, config, external, mtools, squash
from .cli import PtParser, positive_int
from .errors import R36Error
from .util import log, run, sha256_file, warn

HELP = """\
Compila cores libretro para o A33 (Cortex-A7) a partir de cores/<core>/receita.toml,
num container podman rootless (cores/toolchain/Containerfile), sem sudo.

Os binários aceitos vão para a feature features/53-cores-a33 e cada compilação
fica registrada em cores/<core>/builds.jsonl.
"""

EPILOG = """\
exemplos:
  ./cores.sh compilar snes9x2005_plus o3
  ./cores.sh verificar
  ./cores.sh perfil snes9x2005_plus /run/media/$USER/R36-ROMS/pgo/snes9x2005_plus
  ./cores.sh resumo /run/media/$USER/R36-ROMS/r36-thermal.csv --roms /run/media/$USER/R36-ROMS
"""

FEATURE = "53-cores-a33"
LIBRETRO = Path("system/usr/lib/libretro")
IMAGEM = "localhost/r36-cores-a33"
SRC = "/build/src"
LOGDIR = "/build/log"
GLIBC_MAX = (2, 36)
GLIBCXX_MAX = (3, 4, 29)
# /usr/lib da base, para quando a imagem base não está em base/ (conferido na base).
LIBS_BASE_PADRAO = frozenset({
    "libc.so.6", "libm.so.6", "libpthread.so.0", "libdl.so.2", "librt.so.1",
    "libgcc_s.so.1", "libstdc++.so.6", "libz.so.1",
})
PGO_MODOS = ("", "gerar", "usar")
_HEX40 = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_NIVEL = re.compile(r"-O(\d|s|z|g|fast)?")


@dataclass(frozen=True)
class Variante:
    id: str
    nome: str
    flags: tuple
    pgo: str = ""  # "" (sem PGO), "gerar" (instrumentado) ou "usar" (com o perfil guardado)
    base: str = ""  # variante sem PGO cujas flags vêm antes das próprias


@dataclass(frozen=True)
class Receita:
    dir: Path
    core: str
    saida: str
    info: str
    repo: str
    commit: str
    url: str
    sha256: str
    make: tuple
    versao: str
    comuns: tuple
    ligacao: tuple
    pgo_dir: str
    variantes: dict


def _strs(valor, campo):
    if not isinstance(valor, list) or not all(isinstance(x, str) for x in valor):
        raise R36Error(f"{campo} deve ser uma lista de textos")
    return tuple(valor)


def carregar(core, cores_dir=None) -> Receita:
    """Lê e valida cores/<core>/receita.toml."""
    d = Path(cores_dir or REPO_ROOT / "cores") / core
    path = d / "receita.toml"
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise R36Error(f"core '{core}': receita não encontrada em {path}")
    except tomllib.TOMLDecodeError as e:
        raise R36Error(f"{path}: TOML inválido: {e}")
    try:
        c, f, m, fl = data["core"], data["fonte"], data["make"], data["flags"]
        variantes = {}
        for vid, v in data["variantes"].items():
            variantes[vid] = Variante(
                id=vid, nome=v["nome"], flags=_strs(v["flags"], f"variantes.{vid}.flags"),
                pgo=v.get("pgo", ""), base=v.get("base", ""))
        rec = Receita(
            dir=d, core=c["nome"], saida=c["saida"], info=c["info"],
            repo=f["repo"], commit=f["commit"], url=f["url"], sha256=f["sha256"].lower(),
            make=_strs(m["args"], "make.args"), versao=m["versao"],
            comuns=_strs(fl["comuns"], "flags.comuns"), ligacao=_strs(fl.get("ligacao", []), "flags.ligacao"),
            pgo_dir=data.get("pgo", {}).get("dir", ""), variantes=variantes)
    except (KeyError, TypeError, AttributeError) as e:
        raise R36Error(f"{path}: campo ausente ou inválido: {e}")
    except R36Error as e:
        raise R36Error(f"{path}: {e}")

    erros = []
    if rec.core != core:
        erros.append(f"core.nome é '{rec.core}', mas o diretório é '{core}'")
    if not _HEX40.fullmatch(rec.commit):
        erros.append("fonte.commit deve ser o hash completo (40 hexadecimais)")
    if not _HEX64.fullmatch(rec.sha256):
        erros.append("fonte.sha256 deve ter 64 hexadecimais")
    if rec.commit not in rec.url:
        erros.append("fonte.url deve apontar para o commit de fonte.commit")
    if not rec.variantes:
        erros.append("nenhuma variante declarada")
    nomes = [v.nome for v in rec.variantes.values()]
    if len(set(nomes)) != len(nomes):
        erros.append("dois cores com o mesmo nome em variantes")
    for v in rec.variantes.values():
        if not re.fullmatch(r"[a-z0-9_]+", v.id) or not re.fullmatch(r"[a-z0-9_]+", v.nome):
            erros.append(f"variantes.{v.id}: id e nome só com letras minúsculas, dígitos e _")
        if v.pgo not in PGO_MODOS:
            erros.append(f"variantes.{v.id}.pgo deve ser \"gerar\" ou \"usar\"")
        if v.pgo and not rec.pgo_dir:
            erros.append(f"variantes.{v.id} usa PGO, mas falta pgo.dir")
        if v.base and (v.base not in rec.variantes or rec.variantes[v.base].pgo):
            erros.append(f"variantes.{v.id}.base deve ser uma variante sem PGO "
                         f"({', '.join(sem_pgo(rec))})")
    if erros:
        raise R36Error(f"{path}:\n" + "\n".join(f"  {e}" for e in erros))
    return rec


def sem_pgo(rec):
    return [vid for vid, v in rec.variantes.items() if not v.pgo]


def variante(rec, vid) -> Variante:
    """A variante `vid` pronta para compilar; erro claro se não existe ou se falta a base do PGO."""
    if vid not in rec.variantes:
        raise R36Error(f"core '{rec.core}': variante '{vid}' não existe na receita; "
                       f"válidas: {', '.join(rec.variantes)}")
    v = rec.variantes[vid]
    if v.pgo and not v.base:
        raise R36Error(f"core '{rec.core}': a variante '{vid}' usa PGO e o campo base dela está vazio "
                       f"na receita; preencha com a variante vencedora sem PGO ({', '.join(sem_pgo(rec))})")
    return v


def flags(rec, v):
    """(flags de toda chamada do compilador, flags só da ligação), na ordem em que o a33-cc
    as acrescenta depois das do Makefile: comuns, nível da base (PGO) e as da variante."""
    nivel = list(rec.variantes[v.base].flags) if v.base else []
    proprias = [x.replace("{pgo_dir}", rec.pgo_dir) for x in v.flags]
    return [*rec.comuns, *nivel, *proprias], list(rec.ligacao)


def nivel_o(args):
    """O último -O de uma linha de comando (o que vale no GCC), ou None."""
    niveis = [a for a in args if _NIVEL.fullmatch(a)]
    return niveis[-1] if niveis else None


def git_version(rec, v):
    """Valor de GIT_VERSION para o make, com as aspas (o Makefile faz -DGIT_VERSION=\\"$(GIT_VERSION)\\")."""
    return '"' + rec.versao.replace("{variante}", v.id.replace("_", "-")) + '"'


def nome_so(v):
    return f"{v.nome}_libretro.so"


def feature_dir(root=None):
    return Path(root or REPO_ROOT) / "features" / FEATURE


# --- ABI -------------------------------------------------------------------------------

def readelf(so) -> str:
    return run(["readelf", "-h", "-A", "-d", "-V", "-S", "--dyn-syms", "-W", so], env={"LC_ALL": "C"}).stdout


def _versao(s):
    return tuple(int(x) for x in s.split("."))


def problemas_abi(texto, libs) -> list:
    """Problemas de ABI na saída de readelf (-h -A -d -V -S --dyn-syms -W, LC_ALL=C) contra a
    base: bibliotecas, versões de glibc/libstdc++, ISA e ABI de ponto flutuante, retro_* em
    modo ARM e seções de depuração. Lista vazia = compatível."""
    p = []
    if not re.search(r"Class:\s+ELF32\b", texto) or not re.search(r"Machine:\s+ARM\b", texto):
        p.append("não é ELF 32-bit ARM")
    for lib in re.findall(r"\(NEEDED\)\s+Shared library: \[([^\]]+)\]", texto):
        if lib not in libs:
            p.append(f"depende de {lib}, que não existe no /usr/lib da base")
    for nome, ver in sorted(set(re.findall(r"\b(GLIBC|GLIBCXX)_(\d+(?:\.\d+)+)\b", texto))):
        limite = GLIBC_MAX if nome == "GLIBC" else GLIBCXX_MAX
        if _versao(ver) > limite:
            p.append(f"exige {nome}_{ver}; a base vai até {nome}_{'.'.join(map(str, limite))}")
    if not re.search(r"Tag_CPU_arch: v7\b", texto):
        p.append("não é ARMv7 (Tag_CPU_arch)")
    if not re.search(r"Tag_FP_arch: VFPv4\b", texto):
        p.append("não usa VFPv4 (Tag_FP_arch)")
    if not re.search(r"Tag_ABI_VFP_args: VFP registers\b", texto):
        p.append("não é hard-float (falta Tag_ABI_VFP_args: VFP registers)")
    retro = re.findall(r"^\s*\d+:\s+([0-9a-f]+)\s+\d+\s+FUNC\s+\w+\s+\w+\s+\d+\s+(retro_\w+)\s*$", texto, re.M)
    if not retro:
        p.append("não exporta funções retro_*")
    impares = sorted(nome for end, nome in retro if int(end, 16) & 1)
    if impares:
        p.append(f"retro_* em modo Thumb (endereço ímpar): {', '.join(impares)}")
    debug = sorted(set(re.findall(r"\[\s*\d+\]\s+(\.debug_\S+)", texto)))
    if debug:
        p.append(f"tem seções de depuração: {', '.join(debug)}")
    return p


def libs_base(cfg=None, work=None) -> frozenset:
    """Nomes em /usr/lib do SYSTEM da base; sem a base em base/, a lista fixa LIBS_BASE_PADRAO."""
    cfg = cfg or config.load()
    if not cfg.base_path.is_file():
        warn(f"imagem base ausente ({cfg.base_path}); usando a lista fixa de bibliotecas da base")
        return LIBS_BASE_PADRAO
    work = Path(work or cfg.root / "work" / "cores")
    work.mkdir(parents=True, exist_ok=True)
    sq = work / f".SYSTEM.{os.getpid()}"
    try:
        run(["mcopy", "-n", "-i", mtools.spec(cfg.base_path, cfg.part("system").offset), "::/SYSTEM", sq],
            env=mtools.ENV)
        entradas = squash.listing(sq)
    finally:
        sq.unlink(missing_ok=True)
    return frozenset(p.split("/")[-1] for p, e in entradas.items()
                     if p.startswith("usr/lib/") and p.count("/") == 2 and e.type in "-l")


def checar_abi(so, libs):
    probs = problemas_abi(readelf(so), libs)
    if probs:
        raise R36Error(f"{so}: binário recusado pela checagem de ABI:\n" + "\n".join(f"  {x}" for x in probs))


# --- registro --------------------------------------------------------------------------

def registros(rec) -> list:
    path = rec.dir / "builds.jsonl"
    if not path.is_file():
        return []
    out = []
    for n, linha in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if linha.strip():
            try:
                out.append(json.loads(linha))
            except json.JSONDecodeError as e:
                raise R36Error(f"{path}:{n}: JSON inválido: {e}")
    return out


def ultimos(rec) -> dict:
    """{variante: último registro dela}."""
    return {r["variante"]: r for r in registros(rec)}


def resumo_log(texto):
    """Linhas do log do a33-cc -> (níveis -O efetivos, objetos compilados, linha da ligação)."""
    niveis, objetos, ligacao = set(), [], None
    for linha in texto.splitlines():
        args = linha.split()
        niveis.add(nivel_o(args))
        if "-c" in args:
            for i, a in enumerate(args):  # "-o x.o" ou "-ox.o" (o OBJOUT do Makefile)
                if a == "-o" and i + 1 < len(args):
                    objetos.append(args[i + 1])
                elif a.startswith("-o") and a.endswith(".o"):
                    objetos.append(a[2:])
        else:
            ligacao = linha
    return sorted(niveis, key=str), sorted(objetos), ligacao


def gcda_do_binario(so) -> list:
    """Caminhos .gcda gravados no binário instrumentado (um por objeto)."""
    dados = Path(so).read_bytes()
    return sorted({m.decode() for m in re.findall(rb"[\x21-\x7e]+\.gcda(?=\x00)", dados)})


def origem_da_imagem(containerfile) -> str:
    m = re.search(r"^FROM\s+(\S+)", Path(containerfile).read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else ""


# --- compilar --------------------------------------------------------------------------

def _rmtree(path):
    if os.path.exists(path):
        run(["chmod", "-R", "u+rwX", str(path)], check=False)
        shutil.rmtree(path)


def _step(msg):
    log(f"==> {msg}")


def compilar(core, vid, *, root=None, jobs=None):
    """Compila uma variante, confere a ABI, copia o .so para a feature e registra o build."""
    root = Path(root or REPO_ROOT)
    rec = carregar(core, root / "cores")
    v = variante(rec, vid)
    todas, lig = flags(rec, v)
    nivel = nivel_o(todas)
    pgo_local = rec.dir / "pgo"
    if v.pgo == "usar" and not any(pgo_local.glob("*.gcda")):
        raise R36Error(f"core '{core}': a variante '{vid}' usa o perfil, mas {pgo_local} não tem .gcda; "
                       f"importe-o com ./cores.sh perfil {core} <diretório no cartão>")

    work = root / "work" / "cores" / core / vid
    _rmtree(work)
    (work / "log").mkdir(parents=True)
    _step(f"Fonte {rec.commit[:7]} (sha256 conferido, cache em work/cache/cores)")
    arquivo = external.download(f"core '{core}'", rec.url, rec.sha256, root / "work" / "cache" / "cores")
    src = external.extract_tar(f"core '{core}': {rec.url}", arquivo, work / "src", strip=1)

    _step("Toolchain (podman build, rootless)")
    toolchain = root / "cores" / "toolchain"
    run(["podman", "build", "-q", "-t", IMAGEM, toolchain])
    imagem_id = run(["podman", "image", "inspect", IMAGEM, "--format", "{{.Id}}"]).stdout.strip()
    gcc = run(["podman", "run", "--rm", "--network=none", IMAGEM,
               "arm-linux-gnueabihf-gcc", "--version"]).stdout.splitlines()[0]

    _step(f"Compilando {v.nome} ({' '.join(todas)})")
    montagens = ["-v", f"{src}:{SRC}:Z", "-v", f"{work / 'log'}:{LOGDIR}:Z"]
    if v.pgo == "usar":
        montagens += ["-v", f"{pgo_local}:{rec.pgo_dir}:ro,Z"]
    cmd = ["podman", "run", "--rm", "--userns=keep-id", "--network=none", *montagens,
           "-e", f"A33_FLAGS={' '.join(todas)}", "-e", f"A33_LDFLAGS={' '.join(lig)}",
           "-e", f"A33_LOG={LOGDIR}/a33-cc.log",
           IMAGEM, "make", f"-j{jobs or os.cpu_count() or 1}", "CC=a33-cc", *rec.make,
           f"GIT_VERSION={git_version(rec, v)}"]
    proc = run(cmd, check=False, capture=True)
    saida_make = (proc.stdout or "") + (proc.stderr or "")
    (work / "make.log").write_text(saida_make, encoding="utf-8")
    if proc.returncode != 0:
        fim = "\n".join(saida_make.strip().splitlines()[-30:])
        raise R36Error(f"o make falhou (código {proc.returncode}); saída completa em {work / 'make.log'}\n{fim}")
    avisos_pgo = [x for x in saida_make.splitlines() if "warning" in x and re.search(r"profile|coverage|gcda", x)]
    for x in avisos_pgo:
        warn(x)

    _step("Conferindo as flags efetivas e a ABI")
    niveis, objetos, ligacao = resumo_log((work / "log" / "a33-cc.log").read_text(encoding="utf-8"))
    if niveis != [nivel]:
        raise R36Error(f"o último -O das linhas do compilador foi {niveis}, esperado [{nivel!r}]; "
                       f"veja {work / 'log' / 'a33-cc.log'}")
    if ligacao is None:
        raise R36Error(f"nenhuma linha de ligação no log {work / 'log' / 'a33-cc.log'}")
    so = src / rec.saida
    checar_abi(so, libs_base(work=root / "work" / "cores"))

    dst = feature_dir(root) / LIBRETRO / nome_so(v)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(so, dst)
    os.chmod(dst, 0o755)  # como os .so da base
    entrada = {
        "data": datetime.now().isoformat(timespec="seconds"),
        "core": core,
        "variante": vid,
        "nome": v.nome,
        "commit": rec.commit,
        "flags": todas,
        "flags_ligacao": lig,
        "log": {"nivel": nivel, "compilacoes": len(objetos), "ligacao": ligacao},
        "objetos": objetos,
        "gcc": gcc,
        "imagem": {"origem": origem_da_imagem(toolchain / "Containerfile"), "id": imagem_id},
        "tamanho": dst.stat().st_size,
        "sha256": sha256_file(dst),
    }
    if v.pgo == "gerar":
        entrada["gcda"] = gcda_do_binario(dst)
    if v.pgo == "usar":
        entrada["perfil"] = {p.name: sha256_file(p) for p in sorted(pgo_local.glob("*.gcda"))}
    with open(rec.dir / "builds.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    log(f"    {dst.relative_to(root)}: {entrada['tamanho']} bytes, sha256 {entrada['sha256']}")
    if avisos_pgo:
        log(f"    {len(avisos_pgo)} aviso(s) do compilador sobre o perfil (acima)")
    return dst


# --- verificar -------------------------------------------------------------------------

def verificar(core=None, *, root=None, libs=None):
    """ABI dos binários da feature e sha256 igual ao último registro de cada variante."""
    root = Path(root or REPO_ROOT)
    cores_dir = root / "cores"
    if core:
        nomes = [core]
    else:
        nomes = sorted(d.name for d in cores_dir.iterdir() if (d / "receita.toml").is_file())
    if libs is None:
        libs = libs_base(work=root / "work" / "cores")
    problemas = []
    for nome in nomes:
        rec = carregar(nome, cores_dir)
        ult = ultimos(rec)
        for v in rec.variantes.values():
            so = feature_dir(root) / LIBRETRO / nome_so(v)
            if not so.is_file():
                log(f"  {v.nome}: fora da feature (sem binário)")
                continue
            probs = problemas_abi(readelf(so), libs)
            sha = sha256_file(so)
            reg = ult.get(v.id)
            if reg is None:
                probs.append("sem registro no builds.jsonl")
            elif reg["sha256"] != sha:
                probs.append(f"sha256 {sha} diferente do último registro ({reg['sha256']})")
            if probs:
                problemas += [f"{v.nome}: {x}" for x in probs]
            else:
                log(f"  {v.nome}: ok ({sha[:12]}…)")
    if problemas:
        raise R36Error("verificação falhou:\n" + "\n".join(f"  {x}" for x in problemas))


# --- perfil ----------------------------------------------------------------------------

def perfil(core, origem, *, root=None):
    """Importa os .gcda do treino (lidos do cartão) para cores/<core>/pgo/, conferindo que há
    exatamente os que o binário instrumentado grava, e registra os hashes em perfil.json."""
    root = Path(root or REPO_ROOT)
    rec = carregar(core, root / "cores")
    origem = Path(origem)
    if not origem.is_dir():
        raise R36Error(f"{origem}: diretório não encontrado (monte a R36-ROMS do cartão)")
    treino = [r for r in registros(rec) if rec.variantes.get(r["variante"], Variante("", "", ())).pgo == "gerar"]
    if not treino or not treino[-1].get("gcda"):
        raise R36Error(f"core '{core}': nenhum build instrumentado registrado; "
                       f"compile a variante de treino antes")
    reg = treino[-1]
    esperados = {Path(g).name for g in reg["gcda"]}
    achados = {p.name for p in origem.glob("*.gcda")}
    faltam = sorted(esperados - achados)
    if faltam:
        raise R36Error(f"{origem}: faltam {len(faltam)} de {len(esperados)} .gcda do treino "
                       f"(o RetroArch saiu pelo menu?):\n" + "\n".join(f"  {x}" for x in faltam))
    for x in sorted(achados - esperados):
        warn(f"{origem / x}: não é do build instrumentado registrado; ignorado")
    dst = rec.dir / "pgo"
    dst.mkdir(exist_ok=True)
    for p in dst.glob("*.gcda"):
        p.unlink()
    arquivos = {}
    for nome in sorted(esperados):
        shutil.copyfile(origem / nome, dst / nome)
        arquivos[nome] = sha256_file(dst / nome)
    info = {
        "data": datetime.now().isoformat(timespec="seconds"),
        "origem": str(origem),
        "treino": {"variante": reg["variante"], "sha256": reg["sha256"]},
        "arquivos": arquivos,
    }
    (dst / "perfil.json").write_text(json.dumps(info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log(f"    {len(arquivos)} .gcda importados para {dst}")
    return arquivos


# --- resumo ----------------------------------------------------------------------------

@dataclass
class Sessao:
    boot: str
    core: str
    rom: str
    system: str
    linhas: list


def sessoes(linhas) -> list:
    """Agrupa as linhas do r36-thermal.csv em sessões de (boot, core, rom) contíguos;
    linhas sem core (menu) separam sessões e ficam de fora."""
    out, atual = [], None
    for r in linhas:
        chave = (r.get("boot", ""), r.get("core", ""), r.get("rom", ""))
        if not chave[1]:
            atual = None
            continue
        if atual is None or (atual.boot, atual.core, atual.rom) != chave:
            atual = Sessao(*chave, r.get("system", ""), [])
            out.append(atual)
        atual.linhas.append(r)
    return out


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _media(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _ocupacao(r):
    return _media([_num(r.get(f"cpu{i}")) for i in range(4)])


def _temperatura(r):
    ts = [_num(v) for k, v in r.items() if k and k.startswith("temp_")]
    ts = [t for t in ts if t is not None]
    return max(ts) if ts else None


def _fmt(x, casas=1):
    return "—" if x is None else f"{x:.{casas}f}".replace(".", ",")


def _faixa(xs):
    xs = sorted({int(x) for x in xs if x is not None})
    if not xs:
        return "—"
    return str(xs[0]) if len(xs) == 1 else f"{xs[0]}–{xs[-1]}"


def hashes_rom(path):
    """(crc32, sha1) do conteúdo da ROM; num .zip de um só arquivo, do arquivo de dentro."""
    dados = Path(path).read_bytes()
    if zipfile.is_zipfile(io.BytesIO(dados)):
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            membros = [i for i in z.infolist() if not i.is_dir()]
            if len(membros) == 1:
                dados = z.read(membros[0])
    return f"{zlib.crc32(dados):08x}", hashlib.sha1(dados).hexdigest()


def achar_rom(roms, system, rom):
    roms = Path(roms)
    direto = roms / system / rom
    if system and direto.is_file():
        return direto
    return next((p for p in sorted(roms.rglob(rom)) if p.is_file()), None)


def resumo(csv_path, roms=None) -> str:
    """Tabela Markdown das sessões do r36-thermal.csv."""
    try:
        with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
            linhas = list(csv.DictReader(f))
    except FileNotFoundError:
        raise R36Error(f"{csv_path}: arquivo não encontrado")
    ss = sessoes(linhas)
    if not ss:
        return "Nenhuma sessão de jogo no registro.\n"
    cab = ["início", "core", "rom", "duração (s)", "amostras", "ocupação média (%)", "ocupação máx. (%)",
           "MHz médio", "teto MHz", "temp. início (°C)", "temp. fim (°C)"]
    if roms:
        cab += ["CRC32", "SHA1"]
    out = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    cache = {}
    for s in ss:
        ups = [_num(r.get("uptime_s")) for r in s.linhas]
        ups = [u for u in ups if u is not None]
        ocup = [_ocupacao(r) for r in s.linhas]
        temps = [_temperatura(r) for r in s.linhas]
        temps = [t for t in temps if t is not None]
        cel = [
            s.linhas[0].get("date", ""), s.core, s.rom,
            str(int(ups[-1] - ups[0])) if len(ups) > 1 else "0",
            str(len(s.linhas)),
            _fmt(_media(ocup)),
            _fmt(max([o for o in ocup if o is not None], default=None)),
            _fmt(_media([_num(r.get("cpu_mhz")) for r in s.linhas]), 0),
            _faixa([_num(r.get("cpu_max_mhz")) for r in s.linhas]),
            _fmt(temps[0] if temps else None, 0),
            _fmt(temps[-1] if temps else None, 0),
        ]
        if roms:
            chave = (s.system, s.rom)
            if chave not in cache:
                p = achar_rom(roms, s.system, s.rom)
                cache[chave] = hashes_rom(p) if p else ("não achada", "—")
            cel += list(cache[chave])
        out.append("| " + " | ".join(c.replace("|", "\\|") for c in cel) + " |")
    return "\n".join(out) + "\n"


# --- linha de comando ------------------------------------------------------------------

def parse_args(argv):
    p = PtParser(prog="./cores.sh", description=HELP, epilog=EPILOG)
    sub = p.add_subparsers(dest="cmd", metavar="SUBCOMANDO", title="subcomandos", parser_class=PtParser)
    sub.required = True
    c = sub.add_parser("compilar", help="compila uma variante, confere a ABI e copia para a feature",
                       description="Compila <core> <variante> da receita, confere a ABI contra a base, copia o "
                                   ".so para features/53-cores-a33 e registra em cores/<core>/builds.jsonl.")
    c.add_argument("core")
    c.add_argument("variante")
    c.add_argument("-j", "--jobs", type=positive_int("--jobs"), metavar="N",
                   help="processos do make (padrão: um por CPU)")
    v = sub.add_parser("verificar", help="confere a ABI e o sha256 dos binários commitados",
                       description="Confere a ABI dos binários da feature e o sha256 contra o último registro "
                                   "de cada variante (todos os cores, ou só <core>).")
    v.add_argument("core", nargs="?")
    pf = sub.add_parser("perfil", help="importa os .gcda do treino do PGO lidos do cartão",
                        description="Copia os .gcda de <dir> (no cartão: R36-ROMS/pgo/<core>) para "
                                    "cores/<core>/pgo/, conferindo um por objeto do build instrumentado.")
    pf.add_argument("core")
    pf.add_argument("dir")
    r = sub.add_parser("resumo", help="tabela Markdown das sessões do r36-thermal.csv",
                       description="Resume o r36-thermal.csv por sessão (boot, core, rom) numa tabela Markdown.")
    r.add_argument("csv")
    r.add_argument("--roms", metavar="PONTO", help="ponto de montagem da R36-ROMS, para CRC32 e SHA1 das ROMs")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.cmd == "compilar":
            compilar(args.core, args.variante, jobs=args.jobs)
        elif args.cmd == "verificar":
            verificar(args.core)
        elif args.cmd == "perfil":
            perfil(args.core, args.dir)
        elif args.cmd == "resumo":
            sys.stdout.write(resumo(args.csv, args.roms))
        return 0
    except R36Error as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ninterrompido", file=sys.stderr)
        return 130
