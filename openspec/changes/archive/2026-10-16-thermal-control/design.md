# Design

## Context

- **Clock nos jogos:** `emuelecRunEmu.sh` chama `maxperf` na linha 8, para qualquer jogo, e `normperf` ao sair. No A33, `maxperf` põe `performance` em `cpu0/cpufreq/scaling_governor` e `0` em `sunxi-ddrfreq/dsm/scene` (DRAM a 552 MHz). `normperf` volta para `ondemand` e cena `1` (360 MHz). O ajuste por jogo do EmuELEC (`get_ee_setting maxperf`) veio comentado.
- **Limites do `script.bin` (bootarea):** `max_freq` 1200 MHz a 1,32 V. O kernel só reduz o clock a partir de 75 °C (`ths_trip1_0`) e corta para 648 MHz aos 90 °C (`ths_trip1_1`). Não há controle de temperatura da bateria (`pmu_temp_enable = 0`).
- **Ferramentas na imagem:** o shell e as ferramentas são do busybox (`awk`, `df`, `stat`, `date`, `logger`, `mountpoint`, `cut`, `tr`, `sleep`). Não há Python no aparelho para isso.
- **Partição de ROMs:** a p1 (FAT32) é montada em `/storage/roms` pelo initramfs, e a feature 42 a remonta com `noatime` depois do `emuelec-autostart.service`.
- **Padrão de serviço:** as features 40 e 42 usam uma unit em `system/usr/lib/systemd/system/`, um script em `system/usr/lib/r36/` e um symlink de ativação no diretório `*.wants/`.
- **Relógio:** o aparelho não tem rede no uso normal e pode ligar sem hora certa.

## Goals / Non-Goals

**Goals:**
- Medir com o mínimo de interferência: sem mudar clock nem governor, sem custo de CPU perceptível e sem desgaste relevante do cartão.
- Gerar dados que respondam às duas perguntas da spec futura: quanto cada `sistema:core` esquenta e quanto clock ele usa de fato.
- Script testável no PC, sem o aparelho.

**Non-Goals:**
- Analisar o log no aparelho ou mostrar a temperatura no EmulationStation.
- Medir fps ou quedas de quadro. A folga de clock vem da ocupação da CPU.
- Mudar o `emuelecRunEmu.sh` para avisar quando um jogo começa ou termina.

## Decisions

1. **Serviço com laço próprio, não timer nem cron.** A unit `r36-thermal-log.service` é `Type=simple`, com `Restart=always`, `RestartSec=30` e `Nice=19`, `After=emuelec-autostart.service`, ativada em `emuelec.target.wants`, como a feature 42. Ela roda `/usr/lib/r36/thermal-log`, que fica num laço de `sleep 5`.
   - Por quê: a ocupação da CPU é a diferença entre duas leituras de `/proc/stat`. Um processo contínuo guarda a leitura anterior em memória. Com um timer, cada execução teria de salvar esse estado em arquivo.
   - Alternativa descartada: religar o cron. Ele foi desligado pela feature 41, e a resolução de 1 minuto é grossa demais.

2. **Ocupação por núcleo, não a média.** A cada ciclo, o script lê as linhas `cpuN` de `/proc/stat` e grava, por núcleo, `100 x (delta total - delta idle - delta iowait) / delta total`. Os emuladores rodam o trabalho principal numa thread. Com a média dos 4 núcleos, um NES a 30% num núcleo apareceria como 8%. A análise futura usa o núcleo mais ocupado: `teto ≈ clock x ocupação / 0,8`.
   - Um núcleo ausente de `/proc/stat` (desligado por hotplug do kernel sunxi) fica com o campo vazio. A coluna `cpus_online` grava `/sys/devices/system/cpu/online`, porque núcleos desligados também afetam o calor.

3. **Colunas do CSV.** Na ordem:
   `date,uptime_s,boot,temp_<zona>...,cpu_mhz,governor,cpus_online,cpu0,cpu1,cpu2,cpu3,dram_scene,bat_status,bat_pct,system,emulator,core,rom`
   - `date` vem de `date '+%F %T'`. `uptime_s` é a parte inteira de `/proc/uptime`. `boot` são os 8 primeiros caracteres de `/proc/sys/kernel/random/boot_id`. Os dois últimos garantem a ordem e a separação das sessões mesmo com o relógio errado.
   - As zonas térmicas são descobertas no início: uma coluna `temp_<type>` por `/sys/class/thermal/thermal_zone*`. O valor é gravado em °C inteiro: uma leitura acima de 1000 é tratada como milésimos e dividida por 1000.
   - `cpu_mhz` vem de `cpu0/cpufreq/scaling_cur_freq` / 1000. `dram_scene` vem de `sunxi-ddrfreq/dsm/scene`. A bateria é a primeira `/sys/class/power_supply/*` com `type` = `Battery` (`status` e `capacity`).
   - Uma linha tem cerca de 100 bytes. Uma leitura que falha deixa o campo vazio, sem quebrar a linha.

4. **Jogo em execução pela linha de comando do `emuelecRunEmu.sh`.** O ES inicia todo jogo por `emuelecRunEmu.sh %ROM% -P%SYSTEM% --core=%CORE% --emulator=%EMULATOR%`, e o script fica vivo até o emulador sair. O registrador procura em `/proc/[0-9]*/cmdline` o processo desse script e extrai `-P`, `--core=`, `--emulator=` e o nome base da ROM. Vírgulas e aspas no nome da ROM viram `;`. Sem esse processo, os quatro campos ficam vazios.
   - Alternativa descartada: procurar `retroarch`, `PPSSPPSDL`, `FbneoSA` etc. pelo nome. Seria preciso manter uma lista de emuladores, e o sistema não apareceria.

5. **Limite de espaço, verificado antes de cada linha.**
   - Rotação: se `stat -c %s r36-thermal.csv` for maior que 1048576, faz `mv -f r36-thermal.csv r36-thermal.1.csv` e grava o cabeçalho num arquivo novo. Com isso, o total fica em no máximo 2 MB mais uma linha.
   - Piso: se o espaço livre de `df -k /storage/roms` for menor que 65536 KB, pula a gravação do ciclo. A leitura de `/proc/stat` continua, para a ocupação do próximo ciclo ficar correta.
   - Se `/storage/roms` não for ponto de montagem (`mountpoint -q`), também pula o ciclo.
   - Cabeçalho: ao iniciar, se o arquivo existir e a primeira linha for diferente do cabeçalho atual (por exemplo, outra lista de zonas), o script força uma rotação, para nunca misturar formatos num arquivo.

6. **Gravação por `>>`, sem `sync`.** Cada linha é anexada com um `printf ... >>`. O writeback do kernel junta as escritas. Numa queda de energia, perde-se no máximo cerca de 30 s de log. Forçar `sync` a cada 5 s gastaria o cartão por dados que não são críticos.

7. **Caminhos configuráveis para teste.** O script lê os caminhos de `/proc`, `/sys` e do log por variáveis de ambiente, com os valores reais como padrão. Ele também aceita `--once`, que faz duas leituras seguidas, grava uma linha e sai. O teste em `tests/` roda o script no PC com `sh`, sobre uma árvore falsa de `/proc` e `/sys`, e confere o cabeçalho, a linha, a rotação e o piso de espaço livre. O `df` é substituído por um stub no `PATH` do teste.

## Risks / Trade-offs

- [O caminho ou a unidade da temperatura no kernel sunxi 3.4 são diferentes do esperado] → O script grava todas as `thermal_zone*` que existirem, com o tipo no nome da coluna. Se não houver nenhuma, as colunas de temperatura não existem e o resto do log continua útil. Isso é conferido na primeira sessão no aparelho.
- [Varrer `/proc/*/cmdline` a cada 5 s custa CPU] → São algumas dezenas de processos lidos por um `awk` com `Nice=19` a cada 5 s, o que é desprezível perto de um emulador. Se aparecer no log como ocupação, o intervalo da busca pode subir sem mudar a spec.
- [Queda de energia deixa a FAT32 marcada como suja] → É o mesmo risco que os saves gravados na p1 já correm. O log não aumenta esse risco de forma relevante.
- [O relógio sem hora certa deixa `date` sem sentido] → `uptime_s` e `boot` bastam para ordenar e separar as sessões.
- [Medir também aquece] → Um processo acordando a cada 5 s não muda a temperatura de forma mensurável perto dos 4 núcleos a 1,2 GHz de um jogo.

## Migration Plan

1. Build com todas as features e conferência do `changes.txt`: script, unit e link de ativação adicionados, nada removido.
2. Gravação num arquivo de teste com `./flash.sh --target-file` (sem `sudo`) e verificação.
3. O usuário grava o cartão. Não é preciso `--wipe-storage`, porque tudo está no SYSTEM.
4. Sessão de medição: 5 min no menu e 10 min em cada um de NES, Mega Drive, SNES, GBA (Mario Kart), PSX, N64, PSP e CPS2. Depois, ler o CSV no PC.
5. Rollback: `enabled = false` na feature 43 e gerar de novo. Os CSVs que já estão no cartão podem ser apagados à mão.

## Open Questions

- Qual é a zona térmica do SoC e em que unidade ela lê? Isso só muda a análise, não o registrador.
- O kernel desliga núcleos (hotplug) no menu com `ondemand`? A coluna `cpus_online` responde isso.
