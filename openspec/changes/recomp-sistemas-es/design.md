# Design

## Context

Ver `proposal.md` (Why). Estado atual relevante, lido no repositório:

- O console `love` (feature `64-love2d`) é o molde: sistema próprio no `es_systems.cfg`, lançador `/usr/bin/love.sh`, perfil `love.gptk` com `hotkey = guide`, `start = enter` e `gptokeyb ... -killsignal 15`, e FN como `guide:b10` no `SDL_GAMECONTROLLERCONFIG`.
- O `es_systems.cfg` existe em duas cópias completas (`system/usr/config/emulationstation/` e `storage/.config/emulationstation/`), e cada feature que acrescenta um sistema traz a cópia inteira e declara `[[override]]` da feature anterior. A `64-love2d` já sobrepõe a `53-cores-a33`.
- O `58-ports-exec` varre só `/storage/roms/ports` (`find -maxdepth 4`), reconhece ELF pela assinatura e monta cópia `0755` da p8 por cima (`mount --bind`). Não pode ter `After=emuelec-autostart.service` (trava o boot).
- Sem core, o hotkey do RetroArch (`input_enable_hotkey_btn`) não vale: a saída do jogo é por `gptokeyb`, como no LÖVE.
- No ES, o FN não tem bind (spec `fn-button`) e não pode ganhar nenhum.
- O tema Epic Cody ML tem uma pasta por sistema com `theme.xml` que só consome variáveis `${sistema.*}` dos três `_languages`. A pasta `gba/` tem só o `theme.xml`; a do `love2d/` traz também `logo.png`, `poster.png` e `system.png`.

## Goals / Non-Goals

**Goals:**
- Console novo `*-recomp` entra por declaração (sistema, pasta, tema), sem lançador nem serviço novos.
- Sair do jogo com FN + Start sem depender do RetroArch.
- Validar tudo com um ELF de teste, antes de o recompilador existir.

**Non-Goals:**
- Recompilador, runtime do GBA, save states, shaders, bezels e `emuelecRunEmu.sh` para recomps.
- Declarar sistemas vazios de outros consoles.
- Qualquer mudança em `es_input.cfg` ou no hotkey do RetroArch.

## Decisions

**D1. Feature nova `66-recomp`, sobrepondo o `es_systems.cfg` da `64-love2d`.** Segue o padrão do repositório (cópia completa nas duas camadas, `[[override]]` encadeado) e deixa a mudança numa feature que se liga e desliga sozinha. Alternativa: pôr o sistema dentro da `64-love2d` — mistura LÖVE com recomp e quebra o "uma feature, um assunto". Custo aceito: uma terceira cópia de ~2300 linhas do `es_systems.cfg`; o `test_es_systems.py` já compara as cópias.

**D2. Lançador `recomp.sh` por derivação do `love.sh`, sem copiá-lo inteiro.** Reaproveita o que é igual (splash, rota e ganho de áudio, idioma, rotação de log, `SDL_GAMECONTROLLERCONFIG` com `guide:b10`) e troca o que é do LÖVE: executa o ELF em vez de `love "$ROM"`, e não exporta variáveis de `LD_LIBRARY_PATH` do LÖVE. Alternativa: extrair um trecho comum para um arquivo `source`d pelos dois — melhor a longo prazo, mas toca o `love.sh` já validado no aparelho; fica como melhoria futura. O primeiro argumento é o jogo e o segundo o sistema; sem o segundo, o lançador deduz o sistema pelo nome da pasta.

**D3. Alvo do `gptokeyb` com nome fixo, via symlink.** O `gptokeyb` mata um processo pelo nome (`comm`, no máximo 15 caracteres), e os ELFs recompilados terão nomes arbitrários e longos. O lançador cria `/tmp/r36-recomp-game` apontando para o ELF, executa por esse caminho (o kernel usa o basename do caminho como `comm`) e inicia `gptokeyb 1 r36-recomp-game -c recomp.gptk -killsignal 15`. O nome tem exatamente 15 caracteres. Alternativa: `basename` do ELF — quebra com nomes longos ou repetidos. Que o `comm` sai do nome do symlink é regra do kernel mas só se confirma no aparelho (tarefa de validação).

**D4. Perfil `recomp.gptk` igual ao do `love.gptk`.** `hotkey = guide`, `start = enter`, `back = esc`, `guide = esc`, sem teclas de ação. Alternativa: FN sozinho encerra. Descartada: um toque acidental em criança de 6 anos perderia o progresso; o FN+Start já é o padrão do LÖVE.

**D5. `ports-exec` varre `roms/ports` e `roms/*-recomp` por padrão de nome.** A lista de diretórios é montada no início (`ports` e cada `/storage/roms/*-recomp` de primeiro nível), e o laço de cópia/montagem existente roda sobre a união. O cache, o `sha256`, a limpeza e o log são os mesmos, para manter um só lugar que decide o que é executável. O padrão `*-recomp` evita lista fixa de consoles. `recomp.log` não é ELF e já cai fora pela assinatura. Alternativa: segundo serviço `r36-recomp-exec` — duplica o cache e a limpeza, e as duas limpezas apagariam as cópias uma da outra.

**D6. O log do serviço continua em `roms/ports/r36-ports-exec.log`.** A pasta `ports/` existe na base (o sistema `ports` do ES a usa), então o log segue num lugar conhecido. Alternativa: um log por pasta — mais arquivos na p1 para o PC.

**D7. (revisada) Extensão `.sh`: o jogo é o script da raiz da pasta.** A primeira versão listava `.recomp` (um ELF solto). Os pacotes recompilados que o usuário já tem no cartão têm outro formato: `Jogo.sh` na raiz de `gba-recomp/` chama `Jogo/launch.sh`, que roda `Jogo/Jogo.elf` (e cria `Jogo/saves/`). O ES passa a listar só `.sh` (`.sh .SH`); `.recomp` e `.elf` não são listados. **O recompilador pode gerar o binário com qualquer extensão e quem coordena como dispará-lo é o `.sh`**: nada no lançador nem no `ports-exec` depende da extensão do binário, só da assinatura ELF. Consequências:
- `recomp.sh` roda o `.sh` com `bash` explícito e, para o `gptokeyb`, procura o primeiro arquivo com assinatura ELF (que não seja `.so`) na pasta com o nome do `.sh` (e, se não houver, ao lado dele); o `comm` é o nome do arquivo cortado em 15 caracteres (`Donkey Kong Country.elf` vira `Donkey Kong Cou`). O symlink de nome fixo (D3) fica só para um ELF passado direto. Vários binários na pasta: vale o primeiro, e se o `.sh` disparar outro o FN + Start não o encerra (plano B: monitorar os filhos do script).
- `ports-exec` passa a montar `0755` também os scripts com `#!` dentro das pastas `*-recomp` (só lá; em `ports/` continua só ELF), porque o `.sh` da raiz faz `exec` do `launch.sh` e a p1 não tem bit de execução.
- O `launch.sh` do pacote define o próprio `SDL_GAMECONTROLLERCONFIG` (layout Nintendo) e sobrescreve o do lançador; a saída por FN + Start não depende disso.
- Risco: o ES pode listar também o `launch.sh` de dentro de cada pasta de jogo. Só se vê no aparelho; se acontecer, esconder no `gamelist.xml`.
- A ordem de teste muda: o ELF de teste vai num pacote (`Teste.sh` + `Teste/Teste.elf`).

**D8. Arte do tema derivada da do GBA por script, com selo RECOMP.** Um script em `tools/` (Python via `uv`, regra do projeto) gera `logo.png`, `poster.png` e `system.png` a partir da arte já presente no tema, sem baixar nada. Quando o tema não traz arte do GBA para derivar (a pasta `gba/` só tem `theme.xml`), o script usa a arte genérica do tema e compõe o selo; isso é conferido na primeira tarefa do tema.

*Origem da arte (conferida na tarefa 4.1):* a pasta `gba/` só tem `theme.xml`; a arte do GBA vem do tarball do tema upstream (`work/cache/external/4a0d1e11…tar.gz`): pôster em `_art/posters/gba.jpg` (640x480) e controle em `_art/controllers/gba.png` (530x400), achados pelo tema por `${system.theme}`. O tema upstream não traz `logo.png` nem `system.png` do GBA. O script `tools/gera_arte_gba_recomp.py` gera `_art/posters/gba-recomp.png` e `_art/controllers/gba-recomp.png` (o que o ES realmente lê, pois `<theme>` é `gba-recomp`), e os três arquivos `logo.png`, `poster.png`, `system.png` em `gba-recomp/` (o `logo` e o `system` são o texto "GBA" com o selo RECOMP). Sem trilha sonora própria: o `bgsound` do tema fica mudo para `gba-recomp`.

**D9. Sem sistema vazio e sem rede.** Um único `gba-recomp` agora; o ES esconde sistema sem jogos, como já acontece com o `love` sem jogos. Esse comportamento é uma suposição a conferir no aparelho (tarefa de validação).

## Risks / Trade-offs

- [O `comm` não vira o nome do symlink, e FN+Start não encerra] → ELF de teste que espera sinal valida no aparelho; plano B: lançador grava o PID e o `gptokeyb` é substituído por um `kill` do PID por um monitor de botões simples.
- [Binário recompilado precisa de bibliotecas que a imagem não tem] → `ldd` no log do lançador; o contrato de ABI fica na spec e no `CLAUDE.md`.
- [`mount --bind` cobre os arquivos da p1, e o ES lista o arquivo da p1] → comportamento já validado pelos ports; recomp usa o mesmo caminho.
- [Cópia `0755` de ELFs grandes enche a p8] → a limpeza apaga cópias sem uso a cada boot; ELFs de GBA recompilado ficam de poucos MiB a dezenas de MiB. Conferir o espaço livre da p8 com 20 jogos de teste.
- [Terceira cópia do `es_systems.cfg` aumenta a chance de divergência] → `test_es_systems.py` compara as duas camadas e confere a presença só do `gba-recomp` como `*-recomp`.
- [Quem copiar um jogo no cartão com a p1 já montada não vê o jogo até religar] → o ES só relê as pastas no boot; o aparelho não tem rede e o fluxo normal é copiar pelo PC com o aparelho desligado.
