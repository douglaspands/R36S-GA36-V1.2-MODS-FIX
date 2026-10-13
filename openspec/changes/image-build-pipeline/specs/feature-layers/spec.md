# Spec Delta

## Purpose

Definir como uma feature é declarada no repositório, em quais partes da imagem ela pode atuar e como é aplicada e registrada, para que cada feature pedida vire uma mudança reproduzível na próxima imagem.

## ADDED Requirements

### Requirement: Declaração de feature
Cada feature SHALL ser um diretório próprio no diretório de features do repositório. Ele SHALL conter um descritor com nome, descrição e ordem de aplicação, e SHALL conter subdiretórios opcionais por camada: `system`, `storage`, `roms` e `boot`. Um descritor ausente ou inválido SHALL fazer o build falhar.

#### Scenario: Feature válida
- **WHEN** existe um diretório de feature com descritor válido e um subdiretório `system/` com arquivos
- **THEN** o build reconhece a feature e aplica os arquivos de `system/` no SYSTEM

#### Scenario: Descritor inválido
- **WHEN** um diretório de feature não tem descritor, ou o descritor não tem nome ou ordem
- **THEN** o build falha, indicando o diretório e o campo faltante

### Requirement: Camadas e destino
Cada subdiretório de camada SHALL ser aplicado na raiz do filesystem correspondente: `system` no squashfs SYSTEM (raiz `/` do sistema), `storage` na p8 (`/storage`), `roms` na p1 (`/storage/roms`) e `boot` na p2. Subdiretórios com outros nomes SHALL fazer o build falhar.

#### Scenario: Arquivo na camada storage
- **WHEN** uma feature contém `storage/.config/emuelec/configs/emuelec.conf`
- **THEN** a p8 da imagem gerada contém `/.config/emuelec/configs/emuelec.conf` com o conteúdo da feature

#### Scenario: Camada desconhecida
- **WHEN** uma feature contém um subdiretório `kernel/`
- **THEN** o build falha, informando as camadas válidas

### Requirement: Adição, substituição e remoção de arquivos
Arquivos de uma camada SHALL ser adicionados ao destino, ou SHALL substituir um arquivo existente no mesmo caminho. A remoção de um caminho da base SHALL ser declarada explicitamente no descritor da feature. Remover um caminho que não existe SHALL fazer o build falhar.

#### Scenario: Substituição
- **WHEN** uma feature traz `boot/bootlogo.bmp`
- **THEN** a p2 da imagem gerada contém o `bootlogo.bmp` da feature no lugar do original

#### Scenario: Remoção declarada
- **WHEN** o descritor de uma feature declara a remoção de `usr/config/emuelec/bin/put_user_bins_here` na camada `system`
- **THEN** esse caminho não existe no SYSTEM gerado, e a remoção aparece no relatório de diferenças

#### Scenario: Remoção de caminho inexistente
- **WHEN** o descritor declara a remoção de um caminho que não existe na base nem em features anteriores
- **THEN** o build falha, informando a feature e o caminho

### Requirement: Metadados de arquivos de features
Nas camadas `system` e `storage`, arquivos e diretórios novos SHALL receber dono `0:0` por padrão. Executáveis e diretórios SHALL receber modo `0755`, e os demais arquivos `0644`. Um arquivo que substitui outro da base SHALL herdar dono e modo do original. O descritor SHALL poder sobrescrever dono, grupo e modo de caminhos específicos, inclusive setuid.

#### Scenario: Script novo
- **WHEN** uma feature adiciona `system/usr/bin/meu-script.sh` com bit de execução no repositório
- **THEN** o SYSTEM gerado lista o arquivo como `-rwxr-xr-x 0/0`

#### Scenario: Substituição herda metadados
- **WHEN** uma feature substitui `system/usr/bin/busybox`
- **THEN** o arquivo novo é listado como `-rwsr-xr-x 0/0`, igual ao original

#### Scenario: Metadados declarados
- **WHEN** o descritor declara modo `0700` e dono `0:0` para `usr/bin/privado`
- **THEN** o SYSTEM gerado lista `usr/bin/privado` como `-rwx------ 0/0`

### Requirement: Ordem e conflitos entre features
As features ativas SHALL ser aplicadas na ordem declarada nos descritores. Se duas features escreverem ou removerem o mesmo caminho na mesma camada, o build SHALL falhar, a menos que a feature posterior declare explicitamente que substitui a anterior naquele caminho.

#### Scenario: Conflito não declarado
- **WHEN** as features A (ordem 10) e B (ordem 20) trazem `storage/.config/x.conf`, e B não declara substituir A
- **THEN** o build falha, listando as duas features e o caminho

#### Scenario: Substituição declarada
- **WHEN** a feature B declara que substitui A em `storage/.config/x.conf`
- **THEN** o `x.conf` da imagem tem o conteúdo trazido pela feature B, e o manifest registra a substituição

### Requirement: Seleção de features no build
Por padrão, o build SHALL aplicar todas as features habilitadas. O build SHALL aceitar uma opção para aplicar só uma lista de features, ou nenhuma (a "feature vazia"). Uma feature desabilitada no descritor SHALL ser ignorada.

#### Scenario: Build sem features
- **WHEN** o build é executado com a opção de nenhuma feature
- **THEN** a imagem é gerada só a partir da base, e o manifest registra a lista de features vazia

#### Scenario: Feature desabilitada
- **WHEN** um descritor marca a feature como desabilitada
- **THEN** o build padrão não a aplica, e ela não aparece no manifest

### Requirement: Registro do build na imagem
A imagem SHALL conter um arquivo de informação do build, legível no aparelho e no PC, com o timestamp do build, o nome da imagem completa, o tamanho do cartão e a lista ordenada de features aplicadas. O conteúdo SHALL ser igual ao registrado no manifest.

#### Scenario: Consulta no PC
- **WHEN** o cartão gravado é conectado ao PC
- **THEN** o arquivo de informação do build está visível numa partição FAT e mostra o mesmo timestamp de build e as mesmas features do manifest

#### Scenario: Consulta no aparelho
- **WHEN** o usuário lê o arquivo de informação do build por um terminal no aparelho
- **THEN** o conteúdo é o mesmo visto no PC

### Requirement: Relatório de diferenças por feature
Cada build SHALL gerar um relatório legível com cada caminho adicionado, substituído ou removido por camada, com a feature responsável e os metadados finais.

#### Scenario: Relatório gerado
- **WHEN** um build aplica uma feature que adiciona um arquivo em `system` e substitui outro em `boot`
- **THEN** o relatório lista os dois caminhos, a operação (adicionado/substituído), a camada, a feature e, para `system`, o dono e o modo finais
