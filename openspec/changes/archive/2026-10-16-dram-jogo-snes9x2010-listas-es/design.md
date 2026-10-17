# Design

## Context

Veja `proposal.md` para a motivação. Estado atual, conferido na `main` e no SYSTEM do build `20261016-172250-test`:

- `normperf()` e `maxperf()` ficam em `/etc/profile.d/99-emuelec.conf` (base). No A33, `normperf` grava `ondemand` no governor e `1` em `/sys/devices/platform/sunxi-ddrfreq/devfreq/sunxi-ddrfreq/dsm/scene`; `maxperf` grava `performance` e `0`. O comentário da base diz "1--360M 2-224M"; o significado da cena `0` não está documentado.
- O `emuelecRunEmu.sh` (feature `10-ptbr-sao-paulo`) chama `normperf` ou `maxperf` na abertura do jogo (por volta da linha 145) e `normperf` de novo na saída (por volta da linha 567). Depois de cada `normperf` chama `/usr/lib/r36/cpu-ondemand-tune`, protegido por `[ -x ]`.
- O `cpu-ondemand-tune` (feature `44-cpu-ondemand`) também é chamado pelo `/usr/bin/cpufreq` no boot, pelo `cpufreq.service` (`WantedBy=basic.target`). Só age com o governor `ondemand`.
- O `thermal-log` (feature `43-registro-termico`) roda como serviço depois do `emuelec-autostart.service`, portanto depois do `cpufreq.service`. Grava só quando `/storage/roms` é ponto de montagem e tem 64 MB livres. Troca o arquivo quando o cabeçalho muda.
- O teste `test_so_difere_da_base_nos_pontos_esperados` aceita no `emuelecRunEmu.sh` exatamente uma linha removida (`maxperf`) e 12 adicionadas em relação à base.
- O aparelho não tem Wi-Fi nem SSH: a única forma de ler o estado dele é por arquivos na `R36-ROMS`.

## Goals / Non-Goals

**Goals:**
- DRAM na cena `0` só durante o jogo em modo normal, sem tocar no menu nem no boot.
- Responder, com dados do próprio aparelho, de onde vem o teto de 1104 MHz e o que a cena `0` significa em MHz.

**Non-Goals:**
- Não mudar o governor, os valores do afinamento (30 / 10 / 600 MHz) nem o modo de máximo desempenho.
- Não criar chave por sistema ou por jogo para a DRAM. Se a bateria incomodar, isso vira change própria.
- Não mexer no `profile.d/99-emuelec.conf` da base.

## Decisions

**1. A cena da DRAM é gravada pelo `cpu-ondemand-tune`, só quando ele recebe o argumento `jogo`.**
O `emuelecRunEmu.sh` passa `jogo` na chamada após o `normperf` da abertura. A chamada da saída e a do boot (`/usr/bin/cpufreq`) não passam argumento, então não tocam na DRAM: na saída o `normperf` já gravou `1`, e no boot a cena fica a da base. O script só grava a cena se o governor for `ondemand`, então com o máximo desempenho ligado nada muda (o `maxperf` já gravou `0`).
Ficar na feature 44 atende ao requisito de desligar: sem ela, o `[ -x ]` falha e a DRAM fica na cena `1`. A linha do `emuelecRunEmu.sh` muda de conteúdo, mas a contagem de 12 linhas adicionadas em relação à base continua a mesma.
O caminho da cena é o mesmo que o `maxperf` usa, configurável por `R36_DRAM_SCENE` nos testes, como já é feito com `R36_CPU_SYS`.
Alternativas descartadas: um script separado, que exigiria outra linha no `emuelecRunEmu.sh` e outra proteção `[ -x ]` para o mesmo ponto; gravar a cena no próprio `emuelecRunEmu.sh`, que deixaria o comportamento na feature 10 e impediria desligá-lo com a 44; mudar o `normperf` na base, o que obriga a substituir o `profile.d` inteiro.

**2. SNES e listas do ES nos arquivos da feature 10.**
`snes.emulator=libretro` e `snes.core=snes9x2005_plus` entram no `emuelec.conf` junto de `gba.*` e `cps2.*`. No `es_settings.cfg`, `FolderViewMode` passa de `always` para `never` e entra `<bool name="FavoritesFirst" value="true" />` na ordem alfabética dos `bool`. São os mesmos arquivos e o mesmo padrão já usados. O `LastSystem` do cartão do usuário é estado de uso e não entra.

**2b. RetroArch em inglês devolvendo o `user_language` ao valor da base.**
O `retroarch.cfg` da feature 10 passa a ter `user_language = "0"`, o valor de fábrica, que no RetroArch é o inglês. O arquivo continua na feature por causa do `menu_driver` e do OK/Cancel. O `setsettings.sh` da base não mexe em `user_language` (conferido no SYSTEM do build `20261016-172250-test`), então o valor gravado na imagem é o que vale. O `system.language` e o `Language` do ES continuam `pt_BR`.
Alternativa descartada: apagar a linha do arquivo. O RetroArch também usaria o inglês, mas deixar a chave explícita facilita o teste e a volta ao português.

**3. Retrato do sistema gravado pelo `thermal-log`, uma vez por boot, no primeiro ciclo em que ele pode gravar.**
O serviço já espera a montagem das ROMs e confere o espaço livre, e roda depois do `cpufreq.service`, então o retrato pega os tunables afinados. Ele é gravado num arquivo temporário na própria `R36-ROMS` e renomeado para `r36-sysinfo.txt`, para não deixar um retrato pela metade. O formato é uma linha `caminho: valor` por arquivo lido, agrupada por seções (CPU, ondemand, DRAM, térmico, bateria). Um caminho ausente vira `caminho: (ausente)`. Os itens lidos são os do `proposal.md`: em `cpu0/cpufreq` e `cpufreq/ondemand` (ou `policy*`), o diretório de devfreq do `sunxi-ddrfreq` e o `dsm`, `thermal_zone*/trip_point_*` e `cooling_device*/{type,cur_state,max_state}`.
Alternativas descartadas: um serviço oneshot próprio, que duplicaria a espera pela montagem e a checagem de espaço; gravar no `/storage`, que o usuário não lê no PC sem montar a ext4.

**4. Colunas novas ao lado das que elas complementam.**
`cpu_max_mhz` (de `cpu0/cpufreq/scaling_max_freq`) vem depois de `cpu_mhz`, `dram_mhz` depois de `dram_scene` e `bat_voltage` depois de `bat_pct`. A troca de cabeçalho já faz o log antigo virar `r36-thermal.1.csv`. A tensão vem de `voltage_now` da bateria, em µV, convertida para mV. A frequência da DRAM vem do `cur_freq` do devfreq do `sunxi-ddrfreq`. Como a unidade não está confirmada, o script converte pela ordem de grandeza: valores acima de 10.000.000 são tratados como Hz e os demais como kHz. O retrato grava o valor bruto, para conferir a conversão.

**5. Imagem de teste, gravada com `--wipe-storage`.**
`./build.sh --test`. O `es_settings.cfg` e o `emuelec.conf` estão no `/storage`. Com `--keep-storage`, só a DRAM e o diagnóstico chegariam, porque ficam no SYSTEM.

## Risks / Trade-offs

- [A cena `0` pode não ser a frequência máxima da DRAM, e sim um modo dinâmico] → O retrato e a coluna `dram_mhz` mostram a frequência real em jogo. Se a cena `0` não mudar nada em relação à `1`, a hipótese da DRAM cai, e o próximo passo é o clock da CPU.
- [Mais calor e consumo em todo jogo, inclusive nos leves (NES, GB)] → O log mede a temperatura com a mudança. A DRAM consome bem menos que a CPU em `performance`. Uma chave por sistema fica para outra change, se for preciso.
- [A unidade de `cur_freq` da DRAM pode ser outra] → A conversão pela ordem de grandeza cobre Hz e kHz, e o valor bruto no retrato permite conferir.
- [O teto de 1104 MHz pode vir da bateria a 5%, e não do calor] → A validação é feita com a bateria carregada. `cpu_max_mhz`, `bat_voltage` e o estado dos dispositivos de resfriamento no retrato separam as duas causas.
- [O RGUI com `rgui_extended_ascii` pode ter sido ligado no cartão do usuário por causa dos acentos] → Com o inglês, a opção deixa de importar. A imagem não muda essa chave.
- [O snes9x2005_plus é menos preciso que o snes9x] → Os outros cores continuam selecionáveis por jogo.
- [O retrato no boot pode atrasar o primeiro ciclo do log] → São leituras de sysfs uma vez por boot. O serviço já roda com `Nice=19`.

## Migration Plan

Só imagem nova. Gravar com `./flash.sh ... --all --keep-roms --wipe-storage`. Reverter: desligar a 44, o que também tira a DRAM em jogo; tirar as linhas do SNES e as duas do ES; voltar o `user_language` a `7` para o português. O retrato e as colunas novas não alteram o desempenho.

## Open Questions

- O significado da cena `2` e de outras cenas além de `0` e `1`: o retrato lista as disponíveis, o que basta para uma change futura.
