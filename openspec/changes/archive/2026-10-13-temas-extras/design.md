# Design

## Context

- O EmulationStation desta imagem (fork do Batocera) procura temas em `/storage/.config/emulationstation/themes` (= `/storage/.emulationstation/themes`), `/usr/config/emulationstation/themes`, `/etc/emulationstation/themes` e `/storage/roms/themes`. O `ThemeSet` de fábrica é `NES-BOX`.
- O downloader embutido usa a lista `EmuELEC/emuelec.github.io/settings/EE_themes` (20 temas) e exige rede. O Wi-Fi está desligado.
- A p8 tem 1,5 GiB, com cerca de 660 MiB livres. O change `otimizacoes-sistema` libera mais 300 MB.
- O build aplica camadas a partir de arquivos dentro de `features/<id>/<camada>/` e não tem hoje nenhum mecanismo para conteúdo externo. Temas têm de 5 a 200 MB e muitos arquivos de imagem, e não devem entrar no git.
- Python 3.14 (`requires-python >= 3.11`), só biblioteca padrão. `tarfile` com `filter="data"` recusa caminhos absolutos, `..`, dispositivos e links para fora do destino.
- A tela é 640x480 (4:3). Os temas da série `GPi_` do RetroHursty69 foram feitos para 4:3 (GPi Case). Os `*Uno` são 16:9 e podem ficar apertados.

## Goals / Non-Goals

**Goals:**
- Builds reproduzíveis: o mesmo `feature.toml` sempre gera os mesmos arquivos (URL de commit fixo e sha256).
- Funcionar offline depois do primeiro download.
- Mecanismo genérico (conteúdo externo), reaproveitável por outras features.

**Non-Goals:**
- Colocar os temas na p1 (`/storage/roms/themes`). Decisão do usuário: p8, por sobreviver a `--keep-roms` e ser ext4.
- Mudar o tema padrão.
- Traduzir ou ajustar os temas. Se um tema não funcionar em 640x480, ele sai da lista.

## Decisions

1. **Formato no descritor: `[[external]]`.**

   ```toml
   [[external]]
   layer = "storage"
   dest = ".config/emulationstation/themes/Crystal"
   url = "https://codeload.github.com/dm2912/Crystal/tar.gz/<commit>"
   sha256 = "<sha256 do tar.gz>"
   strip = 1                         # remove "Crystal-<commit>/"
   exclude = ["*.md", "screenshots/*"]   # opcional
   ```

   As URLs apontam para um commit, não para um branch, então o conteúdo não muda. O `sha256` é o do `.tar.gz` baixado. O codeload do GitHub gera tarballs estáveis para o mesmo commit, e se isso mudar o build falha (sha divergente) em vez de gerar algo diferente.
   - Alternativa descartada: um script separado que baixa os temas para `features/50-temas-extras/storage/` (ignorado no git). Isso deixaria o build dependente de um passo manual e o `changes.txt` sem a origem.

2. **Cache em `work/cache/external/<sha256>.tar.gz`.** O download vai para um arquivo temporário no mesmo diretório e só é renomeado depois de conferir o sha256. `./build.sh --offline` não acessa a rede. O `work/` já está no `.gitignore`.

3. **A extração vira uma árvore temporária que entra no plano da camada.** Cada `[[external]]` é extraído para `work/tmp/<build>/external/<feature>/<n>/` com `tarfile.extractall(filter="data")`, depois de aplicar `strip` e `exclude`. Essa árvore é mesclada à camada da feature sob `dest`. A partir daí, o resto do pipeline (conflitos, metadados `0:0` e `0644`/`0755`, `changes.txt`) é o mesmo dos arquivos locais. O manifest registra URL e sha256 de cada externo.

4. **Orçamento de 400 MiB declarado no descritor (`budget_mib = 400`), não fixo no código.** A soma dos arquivos extraídos é medida antes de aplicar a camada. Se passar do limite, o build falha mostrando o tamanho de cada `[[external]]`. O `changes.txt` mostra o total por feature.
   - Alternativa descartada: só confiar na falha do `debugfs` quando a p8 encher. A mensagem seria confusa e chegaria tarde.

5. **Seleção de temas em duas etapas.** Primeiro, medir no PC o tamanho extraído de cada candidato, fixar os commits e calcular o total. Depois, validar no aparelho: os que não cabem ou não funcionam saem. Ordem de prioridade se faltar espaço:
   1. infantis 4:3 (GPi_Mario, GPi_Sonic, GPi_Crash);
   2. gerais pequenos (minimal-EmuELEC, Graphite-OGA, es-theme-switch);
   3. Crystal;
   4. infantis 16:9 (PokemonUno, KirbyUno, YoshiUno).

   O requisito de pelo menos 3 temas infantis é atendido já pelo primeiro grupo.

6. **Nomes dos diretórios de destino legíveis** (ex.: `Mario (GPi)`, `Sonic (GPi)`, `Pokemon`), porque o ES mostra o nome do diretório na lista. Sem `/` e sem caracteres que o `debugfs` recuse. O carregador já valida nomes.

## Risks / Trade-offs

- [Tema 16:9 fica ruim em 4:3] → Validação no aparelho. Se falhar, sai da lista (decisão 5).
- [Tema usa recursos do ES que este fork não suporta] → O ES ignora elementos desconhecidos ou recusa o tema com aviso. Validação no aparelho.
- [O GitHub muda o tarball gerado e o sha256 deixa de conferir] → O build falha com mensagem clara. Basta atualizar o sha256 depois de conferir o conteúdo. O cache local continua servindo.
- [O build fica mais lento por gravar milhares de arquivos na p8 via `debugfs`] → Medir. Se passar de alguns minutos, agrupar os comandos num script `debugfs` só (o `apply_plan` já faz isso).
- [Licenças dos temas] → Os temas são distribuídos pelos autores para uso em EmulationStation. O build mantém os arquivos de licença e o README de cada um, e o manifest registra a origem. Uso pessoal, sem redistribuição das imagens.
- [`--keep-storage` não leva os temas] → Documentado no README, com a cópia manual pelo PC como alternativa.

## Open Questions

- Commits e sha256 exatos de cada tema: definidos na primeira tarefa, ao medir os tamanhos. Não mudam a abordagem.
