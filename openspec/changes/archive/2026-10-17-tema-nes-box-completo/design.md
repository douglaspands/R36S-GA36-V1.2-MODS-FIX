# Design

## Context

Ver proposal.md - Why. Fatos do repositório e da base que moldam a abordagem:

- O ES lê temas do `/storage/.config/emulationstation/themes/` antes de `/usr/config/`, e a p8 da base já traz uma cópia completa do NES-BOX (cerca de 21 MiB), com as mesmas lacunas da cópia do SYSTEM. Por isso a feature atua na camada `storage` (só chega com `--wipe-storage`, como `50-temas-extras`).
- O NES-BOX continua sendo o tema padrão e não é tocado. O tema novo é uma pasta irmã, `NES-BOX-V2`.
- Cada pasta de sistema do NES-BOX tem `theme.xml`, `system.png` (logo, cerca de 500x133 a 500x222, transparente) e `background_icon.png` (960x540, arte de personagem recortada, na metade direita). O `theme.xml` é idêntico entre as pastas (`<include>./../theme.xml</include>` e `<path>./system.png</path>`).
- Os caminhos do `theme.xml` são relativos, então uma pasta pode apontar para a arte de outra (`./../pcenginecd/system.png`).
- O mecanismo `[[external]]` do build só aceita `.tar.gz`. O padrão já usado para arte pequena e gerada (`30-telas-icone-controle`) é um `gerar.sh` que o autor roda, com o resultado versionado no git e as origens no `LEIA-ME.txt`.
- O Readme do NES-BOX proíbe reusar os gráficos do tema em outros projetos e compartilhar versões modificadas.

Pastas que faltam, pelo cruzamento do `es_systems.cfg` com o tema: 7 equivalentes por nome (`pce-cd`, `tic-80`, `sharpx1`, `prboom`, `ecwolf`, `megadrivemsu`, `ggh`) e 8 sem equivalente (`wii`, `pgm2`, `fmtmarty`, `mplayer`, `freej2me`, `gmloader`, `karaoke`, `imageviewer`).

## Goals / Non-Goals

**Goals:**
- Todo sistema do `es_systems.cfg` da imagem ter logo e arte de personagem no NES-BOX-V2.
- Arte oficial sempre que existir, e origem verificável de cada arquivo.
- Nenhuma arte do NES-BOX versionada no git.

**Non-Goals:**
- Mudar o NES-BOX, o tema padrão, ou os temas de `50-temas-extras`.
- Alterar a arte, o layout ou o `theme.xml` raiz dentro do V2: ele é cópia fiel, só com adições.
- Cobrir os sistemas que o NES-BOX lista mas a imagem não usa (`advision`, `arduboy` etc.).
- Mudar o código do build, o tema padrão ou o `es_systems.cfg`.

## Decisions

**1. Feature `51-tema-nes-box-v2`, camada `storage`, tema novo `NES-BOX-V2`.**
O V2 é uma cópia do NES-BOX da base mais as 15 pastas novas, em `.config/emulationstation/themes/NES-BOX-V2/`. É um caminho que nenhuma outra feature nem a base declaram, então não há conflito. Ordem 51, entre `50-temas-extras` e `52-psp-desempenho`. A camada `system` não é usada, porque o ES lê o `/storage` primeiro.
*Alternativas:* (a) acrescentar as pastas dentro do NES-BOX, rejeitada porque você quer o NES-BOX intacto e o V2 como escolha; (b) um V2 que só inclui o NES-BOX por referência, rejeitada porque exigiria um `theme.xml` de referência para cada uma das cerca de 190 pastas e dependeria de o ES resolver caminhos entre temas.

**2. A cópia sai da base e não vai para o git.**
O `gerar.sh` extrai o NES-BOX da p8 da base (`debugfs rdump`, só leitura, sem root) para `storage/.config/emulationstation/themes/NES-BOX-V2/` e escreve um `.gitignore` com os caminhos copiados. Só os arquivos novos (as 15 pastas, `fontes.toml`, `LEIA-ME.txt`, o próprio `gerar.sh`) são versionados. Quem clona o repositório roda o `gerar.sh` uma vez (a base já é pré-requisito do build) antes de gerar a imagem. O build falha com mensagem clara se a cópia não existir.
*Por quê:* o Readme do NES-BOX proíbe compartilhar versões modificadas e reusar os gráficos, e assim a arte dele nunca entra no repositório.
*Alternativa:* versionar a cópia (21 MiB). Rejeitada pelo mesmo motivo.

**3. Sistemas equivalentes por referência, dentro do V2.**
A pasta nova tem só um `theme.xml`, igual ao existente, com `./system.png` e `./background_icon.png` trocados por `./../<existente>/system.png` e `./../<existente>/background_icon.png`. Mapa: `pce-cd`→`pcenginecd`, `tic-80`→`tic80`, `sharpx1`→`x1`, `prboom`→`doom`, `ecwolf`→`wolf`, `megadrivemsu`→`megadrive`, `ggh`→`gamegear`.
*Por quê:* não duplica arte e o próprio `theme.xml` já usa `./../theme.xml` no `<include>`, e o ES resolve `./../` dentro do tema.
*Alternativa:* copiar os PNGs, rejeitada por duplicar cerca de 1 MiB.
*Validado no código do ES do EmuELEC* (`FileSystemUtil::resolveRelativePath`, usado por `ThemeData` em `<path>` e `<include>`): só caminhos que começam com `./` são resolvidos em relação ao tema. `../x` não é resolvido, mas `./../x` é. Por isso o `theme.xml` novo usa `./../<existente>/system.png`, e o fallback de copiar os PNGs não é necessário. O teste exige o prefixo `./`.

**4. Arte oficial baixada uma vez, pelo autor, e versionada.**
Um `gerar.sh` da feature (ImageMagick 7, como o de `30-telas-icone-controle`) lê um `fontes.toml` com, por sistema e por arquivo, a URL de origem e o sha256 do arquivo baixado. Ele baixa para `work/cache/`, confere o sha256, converte para PNG transparente no tamanho do tema e grava em `storage/`. O PNG pronto fica no git, e o build não baixa nada (funciona em `--offline`).
*Ordem de busca por sistema:* material do projeto ou do fabricante, Wikimedia Commons, Logopedia e wikis do sistema, arte promocional publicada. Arquivo escolhido só se a licença ou a origem estiver registrada e o fundo for transparente ou removível sem borda ruim.
*Alternativa:* `[[external]]` no build. Rejeitada: só aceita `.tar.gz`, exigiria mudar o build e quebraria o build offline.

**5. Logo e arte de personagem são decididos por arquivo.**
Cada sistema novo pode ter logo oficial e arte criada, ou o inverso. O `fontes.toml` marca cada um dos dois como `oficial` (URL e sha256) ou `criado`.
*Esperado pela pesquisa:* `wii`, `fmtmarty` e `pgm2` têm logo oficial ou de fabricante; `wii` também tem personagem (Mii, por exemplo) e `pgm2` tem personagens de jogos da plataforma, mas essa arte de personagem está sujeita a licença e qualidade, então pode cair em `criado`. `freej2me`, `gmloader` e `mplayer` são projetos de software, onde só `mplayer` tem logo com origem conhecida; `karaoke` e `imageviewer` não são produtos com logo.

**6. Arte criada com ImageMagick e ícones Lucide.**
Para o que não existir, o `gerar.sh` cria: logo como ícone temático mais o nome do sistema em texto, e arte de personagem como uma ilustração do assunto (microfone, moldura de imagem, tela de celular, filme) no tamanho e na posição (metade direita, 960x540) das artes do tema. Os SVGs do Lucide ficam na pasta da feature (licença ISC), como o `gamepad-2` de `30-telas-icone-controle`.
*Alternativa:* deixar esses sistemas sem pasta. Rejeitada: era o pedido de completar o tema.

**7. Verificação por teste, não por mudança no build.**
Um teste novo cruza os `<theme>` do `es_systems.cfg` com as pastas do NES-BOX-V2 (cópia da base mais as da feature), confere que todo caminho de imagem do `theme.xml` resolve, que os PNGs acrescentados são transparentes e têm as dimensões da spec, e que cada arquivo tem origem no registro. Roda no conjunto rápido quando a base está presente, como os testes de outras features.

**8. Registro de origem no `LEIA-ME.txt` da feature.**
Uma tabela por sistema: tipo (oficial, referência, criado), URL e sha256 de cada arquivo oficial, ou a pasta apontada. É a mesma informação do `fontes.toml`, gerada por ele para os dois não divergirem.

## Risks / Trade-offs

- [Pouca arte oficial encontrável, principalmente de personagem] → Fallback criado por arquivo, registrado como `criado`. O resultado ficará visualmente diferente das artes de fábrica nesses sistemas.
- [Direitos de marcas e personagens] → Uso pessoal, nenhuma arte do NES-BOX no git, origem registrada de tudo que for externo. Não é uma licença: se o repositório virar público, rever o que está versionado.
- [Fundo não transparente na arte baixada] → Remoção de fundo só quando sair limpa. Senão, fica `criado`. A conferência é visual, na pré-visualização gerada pelo `gerar.sh`.
- [Download parar de funcionar (URL some)] → O PNG já está no git e o sha256 identifica o original. O `gerar.sh` só precisa de rede para regenerar.
- [O ES não resolver `../` nos caminhos] → Resolvido: usa-se `./../`, que o ES resolve (Decisão 3). Conferir no aparelho na tarefa 5.3.
- [Só chega com `--wipe-storage`] → Igual às outras features de tema. Documentar no `LEIA-ME.txt` e no README, com a cópia pelo PC para `--keep-storage`.
