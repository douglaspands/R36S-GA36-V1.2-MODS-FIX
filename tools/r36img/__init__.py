"""Fábrica de imagens para o R36S clone (GA36-MB V1.2, Allwinner A33).

Só biblioteca padrão. As ferramentas externas (mksquashfs, mtools, debugfs,
mkfs.fat...) são chamadas via subprocess com argumentos em lista.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
