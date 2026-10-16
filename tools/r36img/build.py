"""./build.sh — gera a imagem do cartão a partir da base e das features."""

import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from . import base as basemod
from . import config, deps, ext4, external, features, image, layout, mtools, parts, squash
from .cli import PtParser, positive_int
from .errors import R36Error
from .util import extract_region, fmt_mib, log, run, sha256_file

HELP = """\
Gera uma imagem nova do cartão SD do R36S (GA36-MB V1.2) a partir da imagem
base de fábrica (base/) e das features do diretório features/.

Roda como usuário comum (sem sudo). A saída fica em out/<AAAAMMDD-HHMMSS>/:
  <prefixo>_build_<timestamp>.img.xz   imagem completa (Etcher/dd)
Com --test, o diretório e a imagem ganham o sufixo -test (<timestamp>-test).
  parts/*.img                          imagens por partição (usadas pelo ./flash.sh)
  manifest.json, changes.txt           registro do build e relatório de mudanças
"""

EPILOG = """\
exemplos:
  ./build.sh                          cartão de 16 GB (15000 MiB), features habilitadas
  ./build.sh --no-features            build igual à base (teste de referência)
  ./build.sh --size-mib 7400          cartão de "8 GB" (meça com: lsblk -b)
  ./build.sh --features 00-exemplo    só a feature 00-exemplo (mesmo desabilitada)
  ./build.sh --offline                usa só o cache de downloads das features
  ./build.sh --test                   marca o build como imagem de teste (sufixo -test)
"""


def parse_args(argv):
    p = PtParser(prog="./build.sh", description=HELP, epilog=EPILOG)
    p.add_argument("--size-mib", type=positive_int("--size-mib"), metavar="MIB",
                   help="tamanho do cartão em MiB (padrão 15000, mínimo 7000; "
                        "alinhado para baixo a múltiplo de 4)")
    p.add_argument("--features", metavar="LISTA",
                   help="aplica só estas features (nomes de diretório separados por vírgula), "
                        "inclusive as desabilitadas")
    p.add_argument("--no-features", action="store_true",
                   help="não aplica nenhuma feature (imagem equivalente à base)")
    p.add_argument("--offline", action="store_true",
                   help="não acessa a rede: usa só o cache de conteúdo externo (work/cache/external) "
                        "e falha se faltar algum arquivo")
    p.add_argument("--fast", action="store_true",
                   help="pula a verificação de conteúdo (sha256) do SYSTEM; "
                        "a verificação de metadados continua")
    p.add_argument("--test", action="store_true",
                   help="marca o build como imagem de teste (intermediária): diretório e imagem "
                        "ganham o sufixo -test; o conteúdo não muda")
    args = p.parse_args(argv)
    if args.features is not None and args.no_features:
        p.error("as opções --features e --no-features não podem ser usadas juntas")
    if args.features is not None:
        names = [n.strip() for n in args.features.split(",") if n.strip()]
        if not names:
            p.error("--features exige ao menos um nome de feature")
        args.features = names
    return args


def build_info_text(ts, image_name, size_mib, feats, test=False):
    lines = [
        "R36S GA36-MB V1.2 - registro do build",
        f"imagem: {image_name}",
        f"tamanho_cartao_mib: {size_mib}",
    ]
    if test:
        lines.append("teste: sim")
    lines.append("features:")
    if feats:
        lines += [f"  {i}. {f.id} - {f.name}" for i, f in enumerate(feats, 1)]
    else:
        lines.append("  (nenhuma)")
    return "\n".join(lines) + "\n"


def _feature_manifest(f):
    d = {"id": f.id, "name": f.name, "order": f.order}
    if f.staged:
        d["external"] = [{"layer": x.layer, "dest": x.dest, "url": x.url, "sha256": x.sha256, "bytes": size}
                         for x, _tree, size in f.staged]
    return d


def _step(msg):
    log(f"==> {msg}")


def build(cfg, *, size_mib=None, names=None, none=False, fast=False, offline=False, timestamp=None, test=False,
          features_dir=None, out_root=None, work_root=None, compress=True):
    """Executa o build completo. Devolve o diretório de saída.
    `compress=False` (só para testes) pula o .img.xz; parts/ e manifest são gerados igual."""
    t0 = time.monotonic()
    deps.check_build()
    size = basemod.card_size_mib(cfg, size_mib)
    _step("Conferindo a imagem base (sha256)")
    basemod.verify_base(cfg)
    feats = features.select(features.discover(features_dir or cfg.root / "features"), names, none)

    ts = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    dirname = ts + "-test" if test else ts
    image_name = f"{cfg.image_prefix}_build_{dirname}.img.xz"
    out_root = Path(out_root or cfg.root / "out")
    work_root = Path(work_root or cfg.root / "work")
    out_root.mkdir(parents=True, exist_ok=True)
    out_dir = out_root / dirname
    try:
        out_dir.mkdir()
    except FileExistsError:
        raise R36Error(f"o diretório de saída {out_dir} já existe; nada foi alterado. Rode o build de novo.")
    work = work_root / dirname
    if work.exists():
        _rmtree(work)
    work.mkdir(parents=True)
    ok = False
    try:
        _build_into(cfg, out_dir, work, ts, image_name, size, feats, fast, compress, offline,
                    external.cache_dir(work_root), test)
        ok = True
    finally:
        if ok:
            _rmtree(work)
        else:
            _rmtree(out_dir)
            print(f"(arquivos temporários mantidos em {work} para diagnóstico)", file=sys.stderr)
    log(f"\nBuild {dirname} concluído em {time.monotonic() - t0:.0f}s: {out_dir}")
    return out_dir


def _rmtree(path):
    if os.path.exists(path):
        run(["chmod", "-R", "u+rwX", str(path)], check=False)
        shutil.rmtree(path)


def _build_into(cfg, out_dir, work, ts, image_name, size_mib, feats, fast, compress=True, offline=False,
                cache=None, test=False):
    base = cfg.base_path
    card_sectors = size_mib * 2048
    card_bytes = card_sectors * 512
    log(f"    build {ts}, cartão {size_mib} MiB, features: "
        + (", ".join(f.id for f in feats) if feats else "(nenhuma)"))

    _step("Lendo as partições da base")
    p_boot, p_sys, p_sto, p_roms = (cfg.part(k) for k in ("boot", "system", "storage", "roms"))
    p7_list = mtools.listing(base, p_sys.offset)
    features.check_resize_marker("p7", p7_list, "a imagem base")
    sq_base = work / "SYSTEM.base"
    run(["mcopy", "-n", "-i", mtools.spec(base, p_sys.offset), "::/SYSTEM", str(sq_base)], env=mtools.ENV)
    storage_img = work / "storage.img"
    extract_region(base, storage_img, p_sto.offset, p_sto.size)
    base_lists = {
        "system": squash.listing(sq_base),
        "storage": ext4.listing(storage_img),
        "boot": mtools.listing(base, p_boot.offset),
        "roms": mtools.listing(base, p_roms.offset),
    }
    for layer, entries in base_lists.items():
        features.check_resize_marker(layer, entries, "a imagem base")

    if any(f.externals for f in feats):
        _step("Conteúdo externo das features (download, sha256, extração)")
        external.prepare(feats, cache, work / "external", offline=offline)

    _step("Planejando as features")
    plans = {layer: features.plan_layer(layer, feats, base_lists[layer]) for layer in features.LAYERS}

    _step("SYSTEM: extraindo, aplicando features e reempacotando (lzo1x_999, pode demorar)")
    sp = plans["system"]
    tree = work / "system"
    dir_times = squash.extract(sq_base, tree)
    features.apply_to_tree(sp, tree)
    squash.restore_dir_times(tree, dir_times)
    pf = work / "system.pf"
    squash.write_pseudo_file(sp.final, pf)
    sq_new = work / "SYSTEM"
    squash.mksquashfs(tree, sq_new, pf, sp.final[""], squash.mkfs_time(sq_base))
    _step("SYSTEM: verificando metadados" + ("" if fast else " e conteúdo"))
    squash.verify(sq_new, sp.final, untouched=sp.untouched,
                  content_tree=None if fast else tree, work_dir=work)
    _rmtree(tree)

    info_text = build_info_text(ts, image_name, size_mib, feats, test)
    _step("Partições: BOOT (p2), SYSTEM (p7), STORAGE (p8), ROMS (p1)")
    boot_img = parts.build_boot(cfg, base, work, plans["boot"])
    system_img = parts.build_system_part(cfg, base, work, sq_new, info_text)
    features.check_resize_marker("p7", mtools.listing(system_img), "o build")
    parts.finish_storage(storage_img, plans["storage"], p_sto.label)
    volume_id = int(ts.replace("-", "")) & 0xFFFFFFFF
    roms_img, roms_wl, roms_ext = parts.build_roms(cfg, base, work, plans["roms"], card_sectors, volume_id)
    roms_list = mtools.listing(roms_img)
    features.check_resize_marker("roms", roms_list, "o build")

    bootarea_img = work / "bootarea.img"
    bootarea_img.write_bytes(image.make_bootarea(cfg, base, card_sectors))
    env_img, kernel_img = work / "env.img", work / "kernel.img"
    extract_region(base, env_img, cfg.part("env").offset, cfg.part("env").size)
    extract_region(base, kernel_img, cfg.part("kernel").offset, cfg.part("kernel").size)

    regions = {
        "bootarea": (bootarea_img, 0, cfg.bootarea_size, cfg.bootarea_size, None),
        "boot": (boot_img, p_boot.offset, p_boot.write_size, p_boot.write_size, p_boot.number),
        "env": (env_img, cfg.part("env").offset, cfg.part("env").size, cfg.part("env").size, 5),
        "kernel": (kernel_img, cfg.part("kernel").offset, cfg.part("kernel").size, cfg.part("kernel").size, 6),
        "system": (system_img, p_sys.offset, p_sys.size, p_sys.size, p_sys.number),
        "storage": (storage_img, p_sto.offset, p_sto.size, p_sto.size, p_sto.number),
        "roms": (roms_img, p_roms.offset, card_bytes - p_roms.offset, roms_wl, p_roms.number),
    }

    _step("Montando a imagem completa e verificando a estrutura contra a base")
    full = work / "full.img"
    image.assemble(full, card_bytes, [(f, off, wl) for f, off, _sz, wl, _n in regions.values()])
    image.verify_structure(cfg, full, base, card_sectors)

    if compress:
        _step(f"Comprimindo {image_name} (xz -T0)")
        raw_sha, xz_sha = image.compress(full, out_dir / image_name)
    else:
        raw_sha = xz_sha = None
    full.unlink()

    _step("Gravando parts/, manifest.json e changes.txt")
    parts_dir = out_dir / "parts"
    parts_dir.mkdir()
    manifest_regions = {}
    for name, (src, off, size, wl, num) in regions.items():
        dst = parts_dir / f"{name}.img"
        os.replace(src, dst)
        manifest_regions[name] = {
            "file": f"parts/{name}.img",
            "partition": num,
            "offset": off,
            "size": size,
            "write_length": wl,
            "sha256": sha256_file(dst, wl),
        }
    sector0 = (parts_dir / "bootarea.img").read_bytes()[:512]
    mbr = [e.__dict__ | {"chs_start": e.chs_start.hex(), "chs_end": e.chs_end.hex()}
           for e in layout.parse_mbr(sector0)]
    manifest = {
        "schema": 1,
        "timestamp": ts,
        "image": {
            "file": image_name,
            "size_bytes": card_bytes,
            "sha256": xz_sha,
            "sha256_uncompressed": raw_sha,
        },
        "card_size_mib": size_mib,
        "base": {"file": cfg.base_path.name, "sha256": cfg.base_sha256},
        "features": [_feature_manifest(f) for f in feats],
        "overrides": [
            {"layer": c.layer, "path": c.path, "feature": c.feature, "replaces": c.overrode}
            for plan in plans.values() for c in plan.changes if c.overrode
        ],
        "build_info": {"file": f"p7:/{parts.BUILD_INFO_NAME}", "text": info_text},
        "regions": manifest_regions,
        "layout": {
            "softw411_sector": cfg.softw411_sector,
            "softw411_sha256": sha256_file(parts_dir / "bootarea.img", 16384, cfg.softw411_sector * 512),
            "mbr": mbr,
        },
        "roms": {
            "cluster_bytes": roms_ext.info.cluster_bytes,
            "known_paths": sorted(p.casefold() for p in roms_list),
            "known_bytes": sum(int(e.size) for e in roms_list.values() if e.type == "-"),
        },
        "labels": {k: cfg.part(k).label for k in ("boot", "system", "storage", "roms")},
    }
    if test:
        manifest["test"] = True
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "changes.txt").write_text(features.report(plans, feats), encoding="utf-8")

    _step("Conferindo que a base continua intacta")
    if sha256_file(base) != cfg.base_sha256:
        raise R36Error("a imagem base mudou durante o build!")
    log(f"    imagem: {image_name} ({fmt_mib(card_bytes)}), ROMs gravam {fmt_mib(roms_wl)}")


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        cfg = config.load()
        build(cfg, size_mib=args.size_mib, names=args.features, none=args.no_features, fast=args.fast,
              offline=args.offline, test=args.test)
        return 0
    except R36Error as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ninterrompido", file=sys.stderr)
        return 130
