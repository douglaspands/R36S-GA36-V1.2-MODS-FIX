# Spec Delta

## ADDED Requirements

### Requirement: Conteúdo externo fixado
O descritor de uma feature SHALL poder declarar conteúdo externo: um arquivo `.tar.gz` com URL, sha256 esperado e destino numa camada. O build SHALL baixar o arquivo, conferir o sha256 e aplicar o conteúdo na camada, sob o destino declarado, como se estivesse no diretório da feature. Um sha256 divergente SHALL fazer o build falhar.

#### Scenario: Conteúdo aplicado
- **WHEN** uma feature declara um `.tar.gz` com destino `.config/emulationstation/themes/Crystal` na camada `storage`, e o sha256 confere
- **THEN** a p8 gerada contém os arquivos do arquivo sob `/.config/emulationstation/themes/Crystal`, e o relatório de diferenças os atribui à feature

#### Scenario: sha256 divergente
- **WHEN** o arquivo baixado tem sha256 diferente do declarado
- **THEN** o build falha, informando a feature, a URL e os dois sha256, e não gera imagem

### Requirement: Cache do conteúdo externo
O build SHALL guardar cada arquivo externo num cache local fora do git, identificado pelo sha256, e SHALL reutilizá-lo sem acessar a rede. O build SHALL oferecer uma opção que usa só o cache e falha se faltar algum arquivo.

#### Scenario: Segundo build
- **WHEN** um build já baixou o arquivo e um novo build é executado
- **THEN** o novo build usa o arquivo do cache sem acessar a rede

#### Scenario: Offline sem cache
- **WHEN** o build roda na opção offline e um arquivo declarado não está no cache
- **THEN** o build falha, listando as URLs que faltam

### Requirement: Extração segura do conteúdo externo
A extração SHALL recusar entradas com caminho absoluto, com `..`, nós de dispositivo e symlinks que apontem para fora do destino. O descritor SHALL poder indicar quantos níveis de diretório remover do início dos caminhos e quais caminhos excluir.

#### Scenario: Caminho malicioso
- **WHEN** o arquivo contém uma entrada `../../etc/passwd`
- **THEN** o build falha, informando a feature e a entrada recusada

#### Scenario: Diretório raiz do tarball removido
- **WHEN** o descritor indica remover um nível e o tarball tem tudo sob `Crystal-<commit>/`
- **THEN** os arquivos ficam diretamente sob o destino declarado
