# Proposal

## Why

O R36S esquenta demais durante o jogo. A opção "Enable max performance" do EmuELEC vem ligada (`global.maxperf=1`) para todos os sistemas, e desligá-la reduziu muito o calor do aparelho (validado no aparelho). A imagem deve sair com a opção desligada e ligar o `maxperf` só onde for preciso, por sistema ou por jogo, pelo menu do EmulationStation.

## What Changes

- A `emuelec.conf` da feature `10-ptbr-sao-paulo` passa a trazer `global.maxperf=0` (hoje `1`), com o comentário da chave ajustado.
- Nenhuma chave por sistema ou por jogo vai para a imagem. Os ajustes de N64 e Super Mario World 2 vistos no cartão do autor eram testes e ficam de fora.
- O teste da feature 10 passa a verificar `global.maxperf == 0`.
- O README e a spec `thermal-control` deixam de dizer que o `maxperf` "age como sempre" e passam a descrever o padrão desligado.
- Não há mudança no `emuelecRunEmu.sh`, em `profile.d` nem em qualquer arquivo de `system/`.

## Capabilities

### New Capabilities

Nenhuma.

### Modified Capabilities

- `thermal-control`: ganha o requisito de que a imagem sai com o `maxperf` desligado por padrão, ligável por sistema ou por jogo; o requisito "Medição sem efeito no desempenho" continua valendo, agora em relação à imagem com esse padrão.

## Impact

- `features/10-ptbr-sao-paulo/storage/.config/emuelec/configs/emuelec.conf` (linha 9).
- `tests/test_ptbr_controle.py` (nova asserção).
- `README.md` (trecho da feature `43-registro-termico` e, se couber, o da feature 10).
- Efeito no aparelho: menos calor e menos desempenho nos sistemas pesados (GBA, PSP, N64) até que o usuário ligue o `maxperf` neles. Cartões já em uso mantêm a `emuelec.conf` que têm na p8; só imagens novas ou regravadas recebem o novo padrão.
- Risco conhecido: o `emuelecRunEmu.sh` da imagem base chama `maxperf` na linha 8 sem consultar a chave, e o bloco que a lê está comentado. O efeito foi validado no aparelho, então a mudança de configuração basta, mas a causa não foi confirmada pelo código; o `design.md` trata da verificação pelo log da feature 43.
