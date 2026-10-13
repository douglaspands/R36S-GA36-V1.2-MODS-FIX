"""Features: descritor feature.toml, seleção, ordem, conflitos e plano de mudanças por camada."""

import os
import posixpath
import stat
import tomllib
from dataclasses import dataclass, field, replace
from pathlib import Path

from .errors import R36Error
from .squash import Entry

LAYERS = ("system", "storage", "roms", "boot")
META_LAYERS = ("system", "storage")  # FAT não tem dono/modo
FAT_LAYERS = ("roms", "boot")
SCHEMA = 1
DESCRIPTOR = "feature.toml"
RESIZE_MARKER = ".please_resize_me"

_TOP_KEYS = {"schema", "name", "description", "order", "enabled", "remove", "meta", "override"}


@dataclass(frozen=True)
class Meta:
    layer: str
    path: str
    mode: int | None
    uid: int | None
    gid: int | None


@dataclass
class Feature:
    id: str  # nome do diretório (usado em --features e em [[override]])
    dir: Path
    name: str
    description: str
    order: int
    enabled: bool = True
    removes: list = field(default_factory=list)  # [(layer, path)]
    metas: list = field(default_factory=list)  # [Meta]
    overrides: set = field(default_factory=set)  # {(layer, path_key, feature_id)}

    def layer_dir(self, layer):
        return self.dir / layer


def norm_path(p, where):
    if not isinstance(p, str) or not p.strip():
        raise R36Error(f"{where}: 'path' ausente ou vazio")
    p = posixpath.normpath("/" + p.strip()).lstrip("/")
    if not p or p == "." or ".." in p.split("/"):
        raise R36Error(f"{where}: caminho inválido: {p!r}")
    return p


def key_for(layer, path):
    """FAT ignora maiúsculas/minúsculas."""
    return path.casefold() if layer in FAT_LAYERS else path


def _parse_mode(v, where):
    if v is None:
        return None
    if isinstance(v, bool):
        raise R36Error(f"{where}: 'mode' inválido")
    if isinstance(v, str):
        try:
            v = int(v, 8)
        except ValueError:
            raise R36Error(f"{where}: 'mode' deve ser octal, ex.: \"0755\"")
    if not isinstance(v, int) or not 0 <= v <= 0o7777:
        raise R36Error(f"{where}: 'mode' fora do intervalo 0000..7777")
    return v


def _parse_id(v, name, where):
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise R36Error(f"{where}: '{name}' deve ser inteiro ≥ 0")
    return v


def _layer(v, where, allowed=LAYERS):
    if v not in allowed:
        raise R36Error(f"{where}: camada {v!r} inválida; válidas: {', '.join(allowed)}")
    return v


def load_feature(fdir: Path) -> Feature:
    fdir = Path(fdir)
    fid = fdir.name
    desc = fdir / DESCRIPTOR
    if not desc.is_file():
        raise R36Error(f"feature '{fid}' ({fdir}): descritor {DESCRIPTOR} ausente")
    try:
        data = tomllib.loads(desc.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise R36Error(f"feature '{fid}': {DESCRIPTOR} com TOML inválido: {e}")
    where = f"feature '{fid}' ({desc})"
    unknown = set(data) - _TOP_KEYS
    if unknown:
        raise R36Error(f"{where}: campo(s) desconhecido(s): {', '.join(sorted(unknown))}")
    if "schema" not in data:
        raise R36Error(f"{where}: campo 'schema' faltando")
    if data["schema"] != SCHEMA:
        raise R36Error(f"{where}: schema {data['schema']!r} desconhecido (suportado: {SCHEMA})")
    for k in ("name", "description"):
        if k not in data:
            raise R36Error(f"{where}: campo '{k}' faltando")
        if not isinstance(data[k], str) or (k == "name" and not data[k].strip()):
            raise R36Error(f"{where}: campo '{k}' deve ser texto")
    if "order" not in data:
        raise R36Error(f"{where}: campo 'order' faltando")
    if isinstance(data["order"], bool) or not isinstance(data["order"], int):
        raise R36Error(f"{where}: campo 'order' deve ser inteiro")
    enabled = data.get("enabled", True)
    if not isinstance(enabled, bool):
        raise R36Error(f"{where}: campo 'enabled' deve ser true ou false")

    f = Feature(id=fid, dir=fdir, name=data["name"].strip(), description=data["description"],
                order=data["order"], enabled=enabled)

    for i, r in enumerate(data.get("remove", [])):
        w = f"{where} [[remove]] #{i + 1}"
        if not isinstance(r, dict) or set(r) - {"layer", "path"}:
            raise R36Error(f"{w}: use apenas 'layer' e 'path'")
        layer = _layer(r.get("layer"), w)
        f.removes.append((layer, norm_path(r.get("path"), w)))
    for i, m in enumerate(data.get("meta", [])):
        w = f"{where} [[meta]] #{i + 1}"
        if not isinstance(m, dict) or set(m) - {"layer", "path", "mode", "uid", "gid"}:
            raise R36Error(f"{w}: use apenas 'layer', 'path', 'mode', 'uid' e 'gid'")
        layer = _layer(m.get("layer"), w, META_LAYERS)
        meta = Meta(layer, norm_path(m.get("path"), w), _parse_mode(m.get("mode"), w),
                    _parse_id(m.get("uid"), "uid", w), _parse_id(m.get("gid"), "gid", w))
        if meta.mode is None and meta.uid is None and meta.gid is None:
            raise R36Error(f"{w}: informe ao menos 'mode', 'uid' ou 'gid'")
        f.metas.append(meta)
    for i, o in enumerate(data.get("override", [])):
        w = f"{where} [[override]] #{i + 1}"
        if not isinstance(o, dict) or set(o) - {"layer", "path", "feature"}:
            raise R36Error(f"{w}: use apenas 'layer', 'path' e 'feature'")
        layer = _layer(o.get("layer"), w)
        other = o.get("feature")
        if not isinstance(other, str) or not other:
            raise R36Error(f"{w}: campo 'feature' faltando (diretório da feature substituída)")
        f.overrides.add((layer, key_for(layer, norm_path(o.get("path"), w)), other))

    for child in sorted(fdir.iterdir()):
        if child.name == DESCRIPTOR:
            continue
        if child.is_dir() and not child.is_symlink():
            if child.name not in LAYERS:
                raise R36Error(
                    f"feature '{fid}': camada desconhecida '{child.name}/'; "
                    f"camadas válidas: {', '.join(LAYERS)}"
                )
        elif child.name in LAYERS:
            raise R36Error(f"feature '{fid}': '{child.name}' deve ser um diretório")
    return f


def discover(features_dir: Path) -> list:
    features_dir = Path(features_dir)
    if not features_dir.is_dir():
        return []
    feats = [load_feature(d) for d in sorted(features_dir.iterdir())
             if d.is_dir() and not d.name.startswith(".")]
    return sorted(feats, key=lambda f: (f.order, f.id))


def select(all_features: list, names=None, none=False) -> list:
    """Padrão: todas as habilitadas. `names`: só essas (mesmo desabilitadas). `none`: nenhuma."""
    if none:
        return []
    if names is None:
        return [f for f in all_features if f.enabled]
    by_id = {f.id: f for f in all_features}
    missing = [n for n in names if n not in by_id]
    if missing:
        avail = ", ".join(sorted(by_id)) or "(nenhuma)"
        raise R36Error(f"feature(s) inexistente(s): {', '.join(missing)}. Disponíveis: {avail}")
    chosen = {n for n in names}
    return [f for f in all_features if f.id in chosen]


# ---------------------------------------------------------------- plano

@dataclass
class Change:
    layer: str
    path: str
    op: str  # added | replaced | removed | meta
    feature: str
    kind: str  # file | dir | symlink
    src: Path | None = None
    entry: Entry | None = None  # metadados finais (system/storage)
    overrode: str | None = None  # feature substituída (override declarado)


@dataclass
class LayerPlan:
    layer: str
    base: dict  # {path: Entry} da base
    final: dict  # {path: Entry} esperado após as features
    changes: list  # [Change], na ordem de aplicação
    touched: set  # caminhos (como na listagem final) que não devem ser comparados à base

    @property
    def untouched(self):
        return [p for p in self.final if p not in self.touched and p in self.base]


def _new_entry(kind, src: Path):
    if kind == "dir":
        return Entry("d", 0o755, 0, 0, "", None)
    if kind == "symlink":
        target = os.readlink(src)
        return Entry("l", 0o777, 0, 0, str(len(os.fsencode(target))), None, target)
    st = os.stat(src)
    mode = 0o755 if st.st_mode & 0o111 else 0o644
    return Entry("-", mode, 0, 0, str(st.st_size), None)


def _walk_layer(feature: Feature, layer: str):
    """(caminho relativo, tipo, origem) da árvore da camada, pais antes dos filhos."""
    root = feature.layer_dir(layer)
    if not root.is_dir():
        return []
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        rel_dir = os.path.relpath(dirpath, root)
        for name in sorted(dirnames + filenames):
            src = Path(dirpath) / name
            rel = name if rel_dir == "." else f"{rel_dir}/{name}"
            st = os.lstat(src)
            if stat.S_ISLNK(st.st_mode):
                kind = "symlink"
            elif stat.S_ISDIR(st.st_mode):
                kind = "dir"
            elif stat.S_ISREG(st.st_mode):
                kind = "file"
            else:
                raise R36Error(f"feature '{feature.id}': {layer}/{rel}: tipo de arquivo não suportado")
            if kind == "symlink" and layer in FAT_LAYERS:
                raise R36Error(f"feature '{feature.id}': {layer}/{rel}: FAT não suporta links simbólicos")
            if "\n" in rel or '"' in rel:
                raise R36Error(f"feature '{feature.id}': {layer}/{rel}: nome com aspas ou quebra de linha")
            out.append((rel, kind, src))
        # os.walk não desce em symlinks de diretório; tratados como symlink acima
        dirnames[:] = [d for d in dirnames if not (Path(dirpath) / d).is_symlink()]
    return out


def check_resize_marker(layer, entries, who):
    for p in entries:
        if p.rsplit("/", 1)[-1].casefold() == RESIZE_MARKER:
            raise R36Error(
                f"{who} faria existir '{RESIZE_MARKER}' em {layer}:/{p}. "
                "Esse arquivo faz o aparelho formatar a p1 e a p8 no boot; build abortado."
            )


def plan_layer(layer: str, features: list, base: dict) -> LayerPlan:
    """Aplica as features (em ordem) sobre a listagem da camada e devolve o plano."""
    k = (lambda p: key_for(layer, p))
    state = {k(p): (p, e) for p, e in base.items()}  # chave -> (caminho exibido, Entry)
    owner = {}  # chave -> feature id que escreveu/removeu por último
    changes = []
    touched_keys = set()

    def conflict_check(f: Feature, key, shown):
        prev = owner.get(key)
        if prev is not None and prev != f.id and (layer, key, prev) not in f.overrides:
            raise R36Error(
                f"conflito entre as features '{prev}' e '{f.id}' em {layer}:/{shown}. "
                f"Se '{f.id}' deve substituir '{prev}', declare em {f.id}/{DESCRIPTOR}:\n"
                f'  [[override]]\n  layer = "{layer}"\n  path = "{shown}"\n  feature = "{prev}"'
            )
        return prev if prev is not None and prev != f.id else None

    def parent_ok(f, key, shown):
        parent = key.rsplit("/", 1)[0] if "/" in key else ""
        if parent and (parent not in state or state[parent][1].type != "d"):
            raise R36Error(f"feature '{f.id}': {layer}:/{shown}: diretório pai inexistente")

    for f in features:
        # 1) remoções declaradas
        for rlayer, path in f.removes:
            if rlayer != layer:
                continue
            key = k(path)
            if key not in state:
                raise R36Error(
                    f"feature '{f.id}': remoção de caminho inexistente em {layer}:/{path} "
                    "(não existe na base nem em features anteriores)"
                )
            shown, entry = state[key]
            overrode = conflict_check(f, key, shown)
            doomed = [c for c in state if c == key or c.startswith(key + "/")]
            for c in doomed:
                del state[c]
                owner[c] = f.id
            touched_keys.update(doomed)
            changes.append(Change(layer, shown, "removed", f.id,
                                  "dir" if entry.type == "d" else "symlink" if entry.type == "l" else "file",
                                  entry=entry, overrode=overrode))
        # 2) árvore da camada
        for rel, kind, src in _walk_layer(f, layer):
            key = k(rel)
            check_resize_marker(layer, [rel], f"a feature '{f.id}'")
            existing = state.get(key)
            if kind == "dir":
                if existing is not None:
                    if existing[1].type != "d":
                        raise R36Error(f"feature '{f.id}': {layer}:/{rel} é diretório na feature mas não na imagem")
                    continue
                parent_ok(f, key, rel)
                entry = _new_entry("dir", src)
                state[key] = (rel, entry)
                touched_keys.add(key)
                changes.append(Change(layer, rel, "added", f.id, "dir", src, entry))
                continue
            overrode = conflict_check(f, key, existing[0] if existing else rel)
            new = _new_entry(kind, src)
            if existing is not None:
                shown, old = existing
                if old.type == "d":
                    raise R36Error(f"feature '{f.id}': {layer}:/{shown} é diretório na imagem; não pode virar arquivo")
                entry = replace(new, mode=old.mode if old.type == new.type else new.mode, uid=old.uid, gid=old.gid)
                op = "replaced"
            else:
                parent_ok(f, key, rel)
                shown, entry, op = rel, new, "added"
            state[key] = (shown, entry)
            owner[key] = f.id
            touched_keys.add(key)
            changes.append(Change(layer, shown, op, f.id, kind, src, entry, overrode))
        # 3) metadados declarados
        for m in f.metas:
            if m.layer != layer:
                continue
            key = k(m.path)
            if key not in state:
                raise R36Error(f"feature '{f.id}': [[meta]] para caminho inexistente {layer}:/{m.path}")
            shown, entry = state[key]
            new = replace(
                entry,
                mode=entry.mode if m.mode is None else m.mode,
                uid=entry.uid if m.uid is None else m.uid,
                gid=entry.gid if m.gid is None else m.gid,
            )
            state[key] = (shown, new)
            touched_keys.add(key)
            mine = next((c for c in reversed(changes)
                         if c.feature == f.id and k(c.path) == key and c.op in ("added", "replaced")), None)
            if mine:
                mine.entry = new
            else:
                overrode = conflict_check(f, key, shown)
                owner[key] = f.id
                changes.append(Change(layer, shown, "meta", f.id,
                                      "dir" if new.type == "d" else "symlink" if new.type == "l" else "file",
                                      entry=new, overrode=overrode))
    final = {shown: e for shown, e in state.values()}
    touched = {state[key][0] for key in touched_keys if key in state}
    return LayerPlan(layer, base, final, changes, touched)


def apply_to_tree(plan: LayerPlan, tree) -> None:
    """Aplica as mudanças numa árvore extraída (SYSTEM). Metadados vão no pseudo-file."""
    import shutil

    for c in plan.changes:
        dst = os.path.join(tree, c.path)
        if c.op == "removed":
            if os.path.isdir(dst) and not os.path.islink(dst):
                shutil.rmtree(dst)
            else:
                os.unlink(dst)
        elif c.op in ("added", "replaced"):
            if c.kind == "dir":
                os.mkdir(dst)
                continue
            if os.path.lexists(dst):
                os.unlink(dst)
            if c.kind == "symlink":
                os.symlink(os.readlink(c.src), dst)
            else:
                shutil.copy2(c.src, dst)


def report(plans: dict, features: list) -> str:
    """Relatório de diferenças (changes.txt)."""
    lines = []
    if not features:
        lines.append("Nenhuma feature aplicada (build sem features).")
    else:
        lines.append("Features aplicadas (em ordem):")
        for f in features:
            lines.append(f"  {f.order:>4}  {f.id}  —  {f.name}")
    op_pt = {"added": "adicionado", "replaced": "substituído", "removed": "removido", "meta": "metadados"}
    for layer in LAYERS:
        plan = plans.get(layer)
        if not plan or not plan.changes:
            continue
        lines.append("")
        lines.append(f"[{layer}]")
        for c in plan.changes:
            extra = ""
            if layer in META_LAYERS and c.entry is not None and c.op != "removed":
                extra = f"  {c.entry.lsmode()} {c.entry.uid}/{c.entry.gid}"
            ov = f"  (substitui '{c.overrode}')" if c.overrode else ""
            lines.append(f"  {op_pt[c.op]:<12} /{c.path}{'/' if c.kind == 'dir' else ''}  feature={c.feature}{extra}{ov}")
    return "\n".join(lines) + "\n"
