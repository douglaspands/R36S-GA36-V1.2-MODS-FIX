# Proposal

## Why

O tema padrão atual do sistema, **Epic Cody** (versão 4:3 640x480 do CodyV59 adaptada para o RG351V), possui todos os textos de coleções, subtítulos de hardware e descrições históricas dos videogames fixos em inglês nos arquivos `theme.xml` de cada um dos mais de 60 consoles suportados.

Em um console configurado em português e voltado para a comunidade de língua portuguesa e hispânica, a presença constante de textos em inglês quebra a imersão. Além disso, temas do EmulationStation tipicamente não oferecem troca dinâmica de idioma. 

Por outro lado, termos técnicos como *16-bit*, *32-bit*, *Ports*, *Arcade*, *D-Pad* e gêneros como *RPGs* e *Shmups* são amplamente aceitos e preferidos em inglês, devendo ser mantidos nessa forma na versão em português do Brasil para máxima naturalidade.

Propomos a criação do **Epic Cody ML** (Multi-Language), uma versão refatorada que desacopla os textos do tema em catálogos de variáveis por idioma (`pt-br.xml`, `es-latam.xml` e `en.xml`), permitindo ao usuário alternar instantaneamente entre Português (Brasil), Espanhol (Latino) e Inglês através do menu de configuração do tema do EmulationStation (`<subset name="language">`), com textos rigorosamente calibrados para as dimensões da tela compacta de 3.5" (640x480) e com preservação das nomenclaturas técnicas clássicas.

## What Changes

- **Arquitetura de Subsets Multi-Idioma**: introdução do seletor `<subset name="language">` no `theme.xml` raiz com opções para `pt-br` (padrão ativo), `es-latam` e `en`.
- **Catálogos centralizados de idioma**:
  - `_languages/pt-br.xml`: textos traduzidos para português do Brasil, mantendo termos técnicos consagrados (*16-bit*, *Ports*, *Arcade*, *RPGs*, *Shmups*) e calibrados para não excederem as caixas de texto de 640x480.
  - `_languages/es-latam.xml`: textos em espanhol latino-americano (evitando regionalismos peninsulares).
  - `_languages/en.xml`: preservação integral dos textos originais em inglês do CodyV59.
- **Refatoração dos sistemas**: substituição dos textos estáticos em todos os `theme.xml` de sistemas, coleções automáticas (`auto-favorites`, `auto-allgames`, `auto-lastplayed`) e coleções customizadas por referências a variáveis (`${sistema.*}`).
- **Substituição na imagem e remoção do original**: o tema original `Epic Cody` é completamente removido da partição `storage`, sendo substituído pelo novo tema **Epic Cody ML** como padrão nativo do sistema em `es_settings.cfg` (`ThemeSet = "Epic Cody ML"`), evitando consumo duplo de espaço na partição de sistema.
- **Calibração de layout para tela pequena**: revisão dos comprimentos máximos de `shortdescription` (1 linha) e `longdescription` (máximo 4 linhas em 0.28x0.24) para evitar sobreposição ou corte com a barra inferior.

## Capabilities

### New Capabilities
Nenhuma.

### Modified Capabilities
- `es-themes`: atualiza o tema padrão para `Epic Cody ML`, adicionando o requisito de suporte a múltiplos idiomas selecionáveis via subset (PT-BR, ES-Latam, EN) e calibração visual dos textos em 640x480.

## Impact

- **Temas do EmulationStation**: o tema `Epic Cody` é substituído ou evoluído para `Epic Cody ML` em `.config/emulationstation/themes/Epic Cody ML`.
- **Configurações do EmulationStation (`es_settings.cfg`)**: atualizado para referenciar o tema `Epic Cody ML`.
- **Armazenamento e Build**: a estrutura de catálogos XML consome menos de 200 KB adicionais, mantendo-se perfeitamente dentro do orçamento da partição `storage` (p8).
