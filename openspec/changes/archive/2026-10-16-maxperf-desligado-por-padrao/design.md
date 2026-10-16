# Design

## Context

- **Onde a chave vive:** `global.maxperf` está na linha 9 de `features/10-ptbr-sao-paulo/storage/.config/emuelec/configs/emuelec.conf`, que a camada `storage/` copia para a p8 (`/storage/.config/emuelec/configs/emuelec.conf`). Cartões já gravados mantêm a conf da p8; só imagem nova ou regravada recebe o valor novo.
- **Estado validado pelo autor:** no cartão do autor, `global.maxperf=0` e o aparelho esquenta muito menos. O mesmo arquivo trazia `n64.maxperf=1` e uma linha por jogo do Super Mario World 2, ambas só testes.
- **O que o código da imagem base mostra:** `emuelecRunEmu.sh` chama `maxperf` na linha 8, antes de qualquer leitura de configuração, e o bloco que consultaria `get_ee_setting "maxperf"` (linhas 475 a 484) está comentado. `maxperf` (em `/etc/profile.d/99-emuelec.conf`) põe `performance` em `cpu0/cpufreq/scaling_governor` e `0` na cena da DRAM. `emuelec_autostart.sh` também chama `maxperf` (linha 80) e `normperf` (linha 247). Pela leitura, a chave não deveria ter efeito, mas o autor validou o efeito no aparelho. A causa não foi confirmada.
- **Log da feature 43:** o `r36-thermal.csv` do cartão não tem sessão posterior à mudança, então ainda não prova nada. As colunas `governor` e `dram_scene` mostram o efeito real.
- **Testes:** `tests/test_ptbr_controle.py` já lê a `emuelec.conf` da feature 10 (`test_emuelec_conf`).

## Goals / Non-Goals

**Goals:**
- A imagem gerada sai com `global.maxperf=0` e sem outras chaves `*.maxperf`.
- O ajuste é testado e documentado.

**Non-Goals:**
- Alterar `emuelecRunEmu.sh`, `profile.d` ou qualquer arquivo de `system/` (nenhum feature mexe neles hoje).
- Definir tetos de clock por sistema (ficam para uma spec futura baseada no log da feature 43).
- Levar para a imagem os ajustes de N64 e Super Mario World 2, nem os demais ajustes do cartão do autor (volume, `psp.*`, `cps2.*`, proporção).

## Decisions

- **Só configuração, na feature 10.** Trocar `1` por `0` na linha 9 e ajustar o comentário. Alternativa descartada: patch no `emuelecRunEmu.sh` para ler a chave. Seria a primeira feature a sobrescrever um script do sistema, e o autor já obteve o resultado só com a configuração. Se o teste de verificação mostrar que a chave não tem efeito, esse patch vira uma change própria.
- **Na feature 10, e não numa nova.** A conf inteira do EmuELEC já vem dessa feature, e duas features trazendo o mesmo arquivo disputariam a camada. Alternativa descartada: feature nova só para o `maxperf`.
- **Spec em `thermal-control`.** O objetivo é reduzir calor, que é o escopo declarado dessa capability. O requisito existente "Medição sem efeito no desempenho" continua valendo sem alteração: ele compara com a imagem sem a feature 43, e isso segue verdadeiro.
- **Sem linhas por sistema ou por jogo.** O padrão é desligado e o usuário liga pelo menu onde precisar.

## Risks / Trade-offs

- [Menos desempenho em GBA, PSP e N64, onde o `ondemand` já oscilou no Mario Kart do GBA] → o usuário liga o `maxperf` nesses sistemas pelo menu; a spec garante que isso é possível.
- [A chave pode não ter efeito pelo código lido] → a tarefa de verificação confere `governor` e `dram_scene` no CSV depois de jogar; se continuar `performance`, abrir uma change para o `emuelecRunEmu.sh`.
- [Cartões existentes não mudam] → documentar no README que só imagem nova ou regravada recebe o padrão, e que no aparelho basta desligar a opção no menu.
