# Design

## Context

O padrão de core de cada sistema vem de `<sistema>.emulator` e `<sistema>.core` em `features/10-ptbr-sao-paulo/storage/.config/emuelec/configs/emuelec.conf`, que só chega à imagem pela p8 (`/storage`). O SNES (`snes.core=snes9x2005_plus`, linha 195), o GBA e o CPS2 já usam esse molde, e `tests/test_ptbr_controle.py` confere cada um. Hoje o arquivo não declara nenhuma chave `nes.*`; o padrão é o da base, onde a lista de cores do RetroArch associa o NES ao `nestopia`. O repositório não tem o SYSTEM da base descompactado, então a presença do `fceumm_libretro.so` não é verificável por leitura.

## Goals / Non-Goals

**Goals:**
- NES abre no `fceumm` sem escolha do usuário, pelo mesmo mecanismo do SNES.

**Non-Goals:**
- Mexer em `fds` ou em outros sistemas, ou afinar opções do core (shaders, overclock, paleta).
- Criar feature nova ou mexer no tema do NES (outra change).

## Decisions

- **Duas linhas em `emuelec.conf`, na feature `10-ptbr-sao-paulo`**, ao lado das do SNES. Alternativa: feature própria; descartada porque os demais padrões de core já moram ali e uma feature nova só para duas linhas fragmentaria a configuração.
- **Só `nes.*`, sem `fds.*`.** O `fceumm` também roda FDS, mas o pedido é o NES; mudar o FDS ampliaria o escopo e o teste garante que ele fica intacto.
- **Teste no `test_ptbr_controle.py`**, junto das asserções de `snes.core`, com `assertNotIn("fds.core", c)`.
- **Conferir o core antes de editar** montando a imagem base sem sudo (ferramentas `mtools`/`r36img` do projeto, ou `unsquashfs` sobre o SYSTEM extraído) e buscando `fceumm_libretro.so` e a entrada `nes` do `es_systems.cfg`, para confirmar o nome exato do core que o EmuELEC aceita em `nes.core`.

## Risks / Trade-offs

- [`fceumm` ausente ou com outro nome na base] → a tarefa 1.2 confirma antes; se faltar, parar e pedir decisão ao usuário (instalar o core está fora do escopo).
- [Cartão já gravado não recebe o padrão, pois o `emuelec.conf` vive no `/storage`] → igual às changes anteriores; documentar no README que vale com `--wipe-storage` ou imagem nova, e que no cartão antigo se troca pelo menu.
- [Jogos de NES com save state do `nestopia` não carregam no `fceumm`] → avisar no README; saves de bateria (.srm) são compatíveis na maioria dos casos.
- [Branch atual `tema-nes-box-completo` tem alterações não commitadas de outra change] → criar a branch desta change a partir da `main` só depois de o usuário resolver essas alterações (commit, stash ou descarte), sem mexer nelas.
