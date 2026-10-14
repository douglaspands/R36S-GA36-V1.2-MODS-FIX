# Design

## Context

O build parte sempre da imagem base e aplica as features habilitadas. Para tirar algo da imagem, basta tirar a feature ou a entrada do `feature.toml`, sem precisar de `[[remove]]`. No relatório do último build (`out/20261013-194239/changes.txt`), todos os arquivos da `51-gameboy-fiel` aparecem como `adicionado`, sem nenhum substituído. Por isso, apagar a feature deixa o GB e o GBC iguais aos da base.

Há uma complicação: a maior parte do que sai está na p8 (storage), e o `./flash.sh --keep-storage` não regrava a p8.

```
o que sai                                      camada   com --keep-storage
---------------------------------------------  -------  ------------------
retroarch-overlays/r36-gameboy/*.png|cfg       system   some (p7 regravada)
.config/retroarch/config/Gambatte/gb*.cfg|opt  storage  FICA no cartao
shaders/presets/Gambatte/gb*.glslp             storage  FICA no cartao
.config/emulationstation/themes/* (GPi)        storage  FICA no cartao
```

## Goals / Non-Goals

**Goals:**
- Com `--wipe-storage`, o cartão sai sem nenhum vestígio da moldura do GB nem dos temas GPi.
- Com `--keep-storage`, o README diz exatamente o que apagar pelo PC.

**Non-Goals:**
- Fazer o build ou o flash apagarem os arquivos antigos de uma p8 preservada. O `--keep-storage` existe justamente para não mexer nela.
- Mexer no código de conteúdo externo (`external.py`) ou no orçamento de 400 MiB.

## Decisions

1. **Apagar a feature 51 em vez de usar `enabled = false`.** O usuário não quer mais a feature, e uma feature desligada continuaria sendo testada (`tests/test_gameboy.py`) e documentada. O histórico do git guarda tudo, caso ela volte.
2. **Tirar as três entradas `[[external]]` da feature 50, sem criar uma feature nova.** A feature continua com os quatro temas gerais. Também sai do comentário do topo a nota sobre PokemonUno, KirbyUno e YoshiUno, porque eles só faziam sentido com a meta de temas infantis, que deixa de existir.
3. **No `R36-BUILD.txt`, só sai a linha `timestamp:`.** O nome da imagem já termina no timestamp e é a versão que o usuário usa. O cabeçalho, o tamanho do cartão e a lista de features continuam. O `manifest.json` mantém a chave `timestamp`, que é lida por máquina, e o `build_info.text` acompanha o arquivo.
4. **Limpeza manual com `--keep-storage`, documentada no README.** A outra opção seria um `[[remove]]` numa feature ativa. Ela não resolve o problema, porque com `--keep-storage` a p8 nem é regravada. Com `--wipe-storage`, um `[[remove]]` também não é necessário, porque os arquivos não existem na base.

## Risks / Trade-offs

- [Cartão gravado com `--keep-storage` continua lento no GB] → No README, listar os quatro arquivos `Gambatte/*` e os dois presets `shaders/presets/Gambatte/*` para apagar. Com a p7 nova, o overlay apontado não existe mais, mas o shader de 5 passadas continua ativo, porque os shaders são da base.
- [O tema ativo é um GPi e o usuário apaga o diretório] → No README, pedir para trocar de tema antes de apagar.
- [Tarballs GPi esquecidos em `work/cache/external/`] → Não atrapalham o build, porque o cache é indexado pelo sha256 das entradas declaradas. Podem ser apagados à mão.

## Migration Plan

1. Gerar o build e gravar com `./flash.sh ... --wipe-storage`. É o caminho recomendado.
2. Se for preciso preservar saves e configurações (`--keep-storage`), montar a `R36-STORAGE` no PC e apagar os caminhos da tabela acima.
3. Rollback: gravar um build anterior com `--build <timestamp>`, como já descrito no README.
