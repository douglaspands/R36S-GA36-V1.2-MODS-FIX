"""Verificação da imagem base e do tamanho do cartão."""

import os

from .errors import R36Error
from .util import sha256_file

# Post do r/R36S onde a imagem de fábrica foi publicada.
BASE_SOURCE_URL = "https://www.reddit.com/r/R36S/comments/1w2i8em/r36s_ga36mb_v1220260416_emuelec_no_roms/"


def verify_base(cfg) -> None:
    """Confere existência, tamanho e sha256 da base. Só abre para leitura."""
    path = cfg.base_path
    if not path.is_file():
        raise R36Error(
            f"imagem base não encontrada.\n  caminho esperado: {path}\n"
            f"  sha256 esperado:  {cfg.base_sha256}\n  sha256 obtido:    (arquivo ausente)\n"
            f"  baixe em: {BASE_SOURCE_URL}"
        )
    got = sha256_file(path)
    if got != cfg.base_sha256:
        raise R36Error(
            f"imagem base divergente (sha256 não confere).\n  caminho: {path}\n"
            f"  sha256 esperado: {cfg.base_sha256}\n  sha256 obtido:   {got}"
        )
    size = os.path.getsize(path)
    if size != cfg.base_size:
        raise R36Error(f"imagem base com tamanho inesperado: {size} (esperado {cfg.base_size})")


def card_size_mib(cfg, requested=None) -> int:
    """Tamanho do cartão em MiB: padrão, mínimo e alinhamento para baixo."""
    mib = cfg.default_size_mib if requested is None else requested
    if isinstance(mib, bool) or not isinstance(mib, int):
        raise R36Error(f"tamanho do cartão inválido: {mib!r} (use um inteiro em MiB)")
    if mib < cfg.min_size_mib:
        raise R36Error(
            f"tamanho do cartão {mib} MiB abaixo do mínimo de {cfg.min_size_mib} MiB"
        )
    aligned = mib // cfg.align_mib * cfg.align_mib
    roms = cfg.part("roms")
    if aligned * 1024 * 1024 // 512 <= roms.start:
        raise R36Error(f"tamanho do cartão {aligned} MiB não comporta a partição de ROMs")
    return aligned
