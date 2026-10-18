# core-builds Specification

## Purpose
Definir como um core libretro é compilado para o A33 a partir de uma receita versionada, verificado contra a ABI da imagem base e registrado com os resultados de avaliação, para servir de molde aos próximos cores.

## Requirements

### Requirement: Receita versionada por core
Cada core compilado SHALL ter no repositório uma receita com o repositório do fonte, o commit completo, o sha256 do arquivo do fonte, as variáveis do `make` e, para cada variante, o nome do core e as flags. A compilação SHALL usar só o que a receita declara. Uma receita ausente ou inválida, ou uma variante desconhecida, SHALL fazer a compilação falhar.

#### Scenario: Compilar uma variante declarada
- **WHEN** o usuário compila a variante `o3` do `snes9x2005_plus`
- **THEN** o binário sai do commit e das flags declarados na receita para `o3`, sem flag vinda do ambiente

#### Scenario: Variante inexistente
- **WHEN** o usuário pede uma variante que a receita não declara
- **THEN** a compilação falha com uma mensagem que lista as variantes válidas

### Requirement: Fonte fixado e conferido
O fonte SHALL ser obtido como arquivo do commit declarado, conferido pelo sha256 da receita e guardado num cache local fora do git, que SHALL ser reaproveitado sem acessar a rede. Um sha256 divergente SHALL fazer a compilação falhar.

#### Scenario: Fonte já no cache
- **WHEN** o arquivo do fonte já está no cache com o sha256 da receita
- **THEN** a compilação o usa sem acessar a rede

#### Scenario: Fonte adulterado
- **WHEN** o arquivo baixado não tem o sha256 da receita
- **THEN** a compilação falha e não gera binário

### Requirement: Toolchain fixada e sem root
A compilação SHALL rodar como usuário comum, sem sudo, num container cuja imagem de origem é fixada por digest e cujo userland tem glibc igual ou anterior à da base (2.36). O caminho do fonte dentro do container SHALL ser fixo, para que o perfil do PGO seja aplicável entre compilações.

#### Scenario: Compilação sem privilégios
- **WHEN** o usuário compila qualquer variante
- **THEN** nenhum passo pede sudo, e o container roda sem root no host

### Requirement: Alvo e flags comuns do A33
Toda variante SHALL compilar para armhf com `-marm -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard`, `-DNDEBUG`, LTO, seções por função e dados com `--gc-sections`, e binário sem símbolos de depuração. A versão informada pelo core SHALL incluir o commit curto e o nome da variante.

#### Scenario: Atributos do binário
- **WHEN** um binário compilado é inspecionado no PC
- **THEN** ele é ELF 32-bit ARM hard-float, ARMv7-A com VFPv4 e NEON, em modo ARM e sem símbolos de depuração

#### Scenario: Versão identifica a variante
- **WHEN** o usuário abre as informações do core no RetroArch
- **THEN** a versão mostra o commit curto e a variante, por exemplo `v1.36 fd45b0e a33-o3`

### Requirement: Checagem de ABI contra a base
Cada binário SHALL ser recusado se depender de biblioteca que a base não tem, de símbolo `GLIBC_` acima de 2.36 ou de símbolo `GLIBCXX_` acima do que a libstdc++ da base (6.0.29) oferece, ou se não for ARM hard-float. A checagem SHALL rodar ao fim de toda compilação e também sobre os binários já commitados.

#### Scenario: Símbolo de glibc nova
- **WHEN** um binário exige `GLIBC_2.38`
- **THEN** a compilação falha, aponta o símbolo e não copia o binário para a feature

#### Scenario: Binário compatível
- **WHEN** um binário depende só de `libc.so.6` com símbolos até `GLIBC_2.36`
- **THEN** a checagem passa e o binário é copiado para a feature

### Requirement: Registro de cada compilação
Cada compilação aceita SHALL acrescentar ao registro do core a data, a variante, o nome do core, o commit, as flags efetivas, a versão do compilador, o digest da imagem do container, o tamanho e o sha256 do binário. O sha256 registrado SHALL ser igual ao do binário na feature.

#### Scenario: Binário commitado confere com o registro
- **WHEN** os testes comparam os binários da feature com o registro
- **THEN** cada binário tem uma entrada com o mesmo sha256

### Requirement: PGO com perfil coletado no aparelho
Uma variante SHALL poder ser instrumentada, gravando o perfil num diretório da p1 que o PC lê sem root, ou compilada com um perfil guardado no repositório. O perfil SHALL ser usado com treino parcial, para que código não exercitado não seja otimizado só para tamanho. A variante com perfil SHALL falhar se o perfil faltar ou não corresponder ao fonte e às flags.

#### Scenario: Perfil gravado no cartão
- **WHEN** o usuário joga com a variante instrumentada e sai pelo menu do RetroArch
- **THEN** os arquivos de perfil aparecem na p1, no diretório declarado na receita

#### Scenario: Perfil incompatível
- **WHEN** a variante com perfil é compilada com um perfil de outro commit ou de outras flags
- **THEN** a compilação falha, em vez de gerar um binário com o perfil ignorado

### Requirement: Resumo das sessões pelo registro térmico
O repositório SHALL oferecer um resumo de `r36-thermal.csv` lido do cartão no PC. O resumo traz, por sessão contínua de um mesmo `core` e `rom`, a duração, a ocupação média e máxima da CPU, o clock médio, o teto de clock e a temperatura no início e no fim, e calcula o CRC32 e o SHA1 de cada ROM quando a p1 é informada.

#### Scenario: Duas sessões do Yoshi em cores diferentes
- **WHEN** o CSV tem uma sessão do Yoshi no `snes9x2005_plus` e outra no `snes9x2005_plus_a33_o3`
- **THEN** o resumo mostra uma linha para cada uma, com os campos separados por core

### Requirement: Resultado da avaliação registrado
O resultado de cada sessão de avaliação SHALL ficar registrado junto da receita, com o core, as ROMs e seus hashes, as condições (clock fixo, temperatura inicial), a percepção do usuário, o FPS observado nos trechos pesados e o resumo térmico. O registro SHALL incluir a decisão tomada, inclusive quando a variante não melhorou.

#### Scenario: PGO sem ganho
- **WHEN** o `_pgo` fica igual ao vencedor sem perfil
- **THEN** o registro diz isso e indica que o vencedor sem perfil é o candidato
