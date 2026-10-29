# Proposal

## Why

O R36S tem o botão FN, e de fábrica ele não faz nada: o driver `udt_joystick` o expõe em `/sys/devices/platform/micro_gamepad/fn_key` (código padrão 464, `KEY_FN`), mas nenhum script nem bind do RetroArch o usa. O usuário quer os atalhos do RetroArch (menu, estado, screenshot e os demais) no FN e o Select livre para o jogo. Um primeiro teste no aparelho, com o FN emitindo o código do Select, provou que o FN chega ao RetroArch; agora o Select deixa de ser hotkey e o FN passa a ser o único modificador dos atalhos. O mesmo teste deixou uma queixa: o boot parece um pouco mais lento.

## What Changes

- Um serviço de boot escreve `316` (`BTN_MODE`) em `fn_key`. Para o RetroArch o FN passa a ser um botão próprio do `micro_gamepad` (o botão 10 do autoconfig), diferente do Select (botão 8).
- O hotkey do RetroArch passa do Select para o FN: o `micro_gamepad.cfg` troca `input_enable_hotkey_btn` de `8` para `10`. Os atalhos de fábrica ficam nos mesmos botões (FN + X menu, FN + R salvar estado, FN + Start sair etc.), e o Select vira só o botão Select do jogo.
- O hotkey acompanha o resultado do remapeamento, para o aparelho não ficar sem menu: o serviço grava `input_enable_hotkey_btn` no `micro_gamepad.cfg` da p8 no boot, com `10` só se a escrita do 316 no `fn_key` teve sucesso (a leitura de volta do `fn_key` não é confiável: no aparelho devolve um valor sem relação com o código, mesmo com o 316 chegando como evento) e `8` (Select) em qualquer outro caso (chave `r36-fn-original`, `fn_key` ausente, escrita recusada). O fim da change é o FN funcionando como hotkey no aparelho. O arquivo da feature traz `8`, o valor seguro.
- O estado do serviço (`fn_key` antes e depois, uptime do início, da aparição do `fn_key` e do fim) fica em `/run/r36-fn.estado`. Um log de diagnóstico do FN na p1 existiu durante os testes no aparelho e foi removido ao fim da change.
- A chave `r36-fn-original` na raiz da p1 desliga o remapeamento: o FN volta ao código 464 e o hotkey volta ao Select (botão 8).
- **BREAKING** para quem usa Select + botão: Select + X deixa de abrir o menu e passa a ser só o Select do jogo; o atalho agora é FN + X.
- Testes no aparelho (instrução ao usuário): FN + X abre o menu, FN + R salva estado, Select + X não abre o menu, e o uptime do estado mostrou quanto o `fn_key` demora, para decidir o que fazer com o boot lento.

O FN como menu de um toque só (sem outro botão) fica de fora: disputaria o botão com o modificador dos atalhos.

## Capabilities

### New Capabilities
- `fn-button`: o FN do aparelho como botão próprio e hotkey do RetroArch (remapeamento do código no boot, hotkey do autoconfig acompanhando o resultado e chave para desfazer).

### Modified Capabilities
- `retroarch-controls`: o requisito "Hotkey no Select com atalhos de fábrica" passa a dizer que o hotkey é o FN, que o Select é só o botão Select do jogo e que o hotkey volta ao Select quando o FN não está remapeado.

## Impact

- `features/20-controle-posicional`: o script `fn-remapeia`, o unit com o link em `emuelec.target.wants`, o `micro_gamepad.cfg` (hotkey padrão `8`, gravado como `10` pelo serviço) e o `feature.toml`.
- Testes novos e atualizados em `tests/` (o do FN e o do autoconfig, que hoje exige o hotkey fixo em `8`).
- `README.md` e `CLAUDE.md` (fato do aparelho: `fn_key`, os códigos 464 e 316, o hotkey no cfg da p8 e as chaves).
- O `fn_key` só existe depois de o `udt_joystick` carregar; o `fn-remapeia` espera o driver aparecer.
- Depende de conferência no aparelho: se o driver não anuncia o `BTN_MODE` (316) ou o SDL não o numera como botão 10, o código ou o número do hotkey mudam antes de arquivar.
