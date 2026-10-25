# Spec Delta

## Purpose

Prover serviço de acesso remoto via SSH (Dropbear) no R36S clone para depuração, cópia de arquivos e gerenciamento do sistema operacional quando uma interface de rede estiver conectada.

## ADDED Requirements

### Requirement: Execução do daemon Dropbear
A imagem gerada SHALL iniciar o daemon Dropbear escutando conexões SSH na porta TCP 22 durante o boot.

#### Scenario: Conexão SSH remota
- **WHEN** uma interface de rede obtém endereço IP e um cliente conecta na porta 22
- **THEN** o daemon Dropbear aceita a conexão e apresenta o banner de autenticação

### Requirement: Geração automática de chaves de host
O sistema SHALL verificar a existência das chaves de host do Dropbear e gerá-las automaticamente em `/storage/.cache/ssh/` caso não existam antes do início do daemon.

#### Scenario: Chaves geradas no primeiro boot
- **WHEN** o sistema inicializa e não encontra chaves de host em `/storage/.cache/ssh/`
- **THEN** chaves Ed25519 e RSA válidas são criadas com permissões restritas antes do daemon subir

### Requirement: Autenticação e diretório padrão
O servidor Dropbear SHALL permitir autenticação do usuário root com a senha padrão do sistema e chaves públicas autorizadas, iniciando a sessão no diretório `/storage`.

#### Scenario: Login via SSH
- **WHEN** o usuário autentica com credenciais válidas do usuário root
- **THEN** uma sessão interativa de shell é aberta no diretório `/storage`
