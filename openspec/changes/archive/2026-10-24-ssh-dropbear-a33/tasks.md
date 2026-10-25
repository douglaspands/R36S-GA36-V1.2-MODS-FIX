# Tasks

## 1. Preparação dos binários do Dropbear para ARMv7-A

- [x] 1.1 Obter ou compilar os binários `dropbear` e `dropbearkey` compatíveis com a ABI do Allwinner A33 (armhf, ARMv7-A, glibc <= 2.36) e verificar a arquitetura com comando de inspeção ELF.
- [x] 1.2 Registrar os binários e seus hashes sha256 em conformidade com o padrão de arquivos externos ou embutidos do repositório.

## 2. Estrutura da feature e configuração do systemd

- [x] 2.1 Criar a feature `features/45-ssh-dropbear` com descritor `feature.toml` apontando para a camada `system`.
- [x] 2.2 Criar script de suporte para inicialização e geração automática de chaves de host em `/storage/.cache/ssh/` caso não existam.
- [x] 2.3 Criar a unit do systemd `dropbear.service` e habilitá-la no target `multi-user.target.wants` da camada `system`.

## 3. Testes automatizados e integração

- [x] 3.1 Criar teste unitário em `tests/test_ssh_dropbear.py` verificando a integridade da feature, permissões de execução dos binários e declarações do `feature.toml`.
- [x] 3.2 Executar toda a suíte de testes do projeto via `uv run python -I -m unittest discover -s tests` e verificar 100% de aprovação.
- [x] 3.3 Testar a geração da imagem com `./build.sh --features 45-ssh-dropbear --test` e verificar que o squashfs do `SYSTEM` contém o serviço e os binários esperados.
