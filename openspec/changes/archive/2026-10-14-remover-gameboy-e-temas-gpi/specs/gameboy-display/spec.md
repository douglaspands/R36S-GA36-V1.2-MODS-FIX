## REMOVED Requirements

### Requirement: Tela do jogo na altura total
**Reason**: A feature `51-gameboy-fiel` foi removida porque a moldura e o shader deixaram GB e GBC lentos no aparelho.
**Migration**: Nenhuma. GB e GBC voltam à apresentação de fábrica. Em cartões gravados com `--keep-storage`, apague pelo PC os overrides listados no README.

### Requirement: Laterais do Game Boy original
**Reason**: A moldura do DMG saiu junto com a feature `51-gameboy-fiel`.
**Migration**: Nenhuma. As laterais voltam a ser as de fábrica.

### Requirement: Laterais do Game Boy Color Atomic Purple
**Reason**: A moldura do GBC saiu junto com a feature `51-gameboy-fiel`.
**Migration**: Nenhuma. As laterais voltam a ser as de fábrica.

### Requirement: Paleta verde do DMG nos jogos de GB
**Reason**: A paleta vinha do shader de 5 passadas da feature `51-gameboy-fiel`, que foi removida.
**Migration**: Nenhuma. Se quiser, escolha uma paleta nas opções do core Gambatte, no menu do RetroArch.

### Requirement: Textura de LCD visível
**Reason**: A grade de LCD vinha dos presets de shader da feature `51-gameboy-fiel`, que foi removida.
**Migration**: Nenhuma. Se quiser, carregue um shader no menu do RetroArch.

### Requirement: Cor do GBC corrigida para o LCD
**Reason**: A correção de cor vinha das opções do core instaladas pela feature `51-gameboy-fiel`, que foi removida.
**Migration**: Nenhuma. A opção de fábrica do core Gambatte volta a valer.

### Requirement: Velocidade cheia com moldura e shader
**Reason**: A moldura e o shader saíram. Sem eles, GB e GBC rodam com a configuração de fábrica.
**Migration**: Nenhuma.

### Requirement: Outros sistemas inalterados
**Reason**: Sem a feature `51-gameboy-fiel`, não há configuração de GB e GBC que precise ficar isolada dos outros sistemas.
**Migration**: Nenhuma.

### Requirement: Artes geradas de forma reproduzível
**Reason**: As molduras e o script que as gerava saíram junto com a feature `51-gameboy-fiel`.
**Migration**: Nenhuma. O histórico do git guarda o script e as artes, caso sejam necessários depois.
