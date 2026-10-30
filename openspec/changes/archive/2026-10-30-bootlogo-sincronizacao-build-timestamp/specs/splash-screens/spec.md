# Spec Delta

## MODIFIED Requirements

### Requirement: Nenhuma cópia da arte de terceiros
Nenhum arquivo do SYSTEM nem do STORAGE da imagem gerada SHALL conter a arte do God of War, incluindo as imagens de recursos do EmulationStation. As telas de bateria e vídeo de introdução SHALL permanecer como na base, enquanto o logo do U-Boot SHALL conter a identificação da placa.

#### Scenario: Inspeção pelo PC
- **WHEN** todos os arquivos do SYSTEM e do STORAGE gerados são verificados
- **THEN** nenhum arquivo tem o sha256 da arte de fábrica, e os arquivos fora do escopo são idênticos aos da base

## ADDED Requirements

### Requirement: Tela de abertura do U-Boot com identificação da placa
O arquivo `bootlogo.bmp` fornecido na partição BOOT (p2) SHALL ser uma imagem BMP pura de 640x480 pixels em 24 bpp (exatamente 921654 bytes), mantendo a arte central do console R36S sobre fundo branco e exibindo a identificação da placa-mãe `GA36-MB V1.2-20260416` na parte inferior no lugar do texto original `OPEN SOURCE`.

#### Scenario: Boot inicial no hardware
- **WHEN** o console liga e o U-Boot inicializa a tela
- **THEN** a tela exibe o papel de parede branco com o logo R36S e o texto "GA36-MB V1.2-20260416" na base, sem exibir o texto "OPEN SOURCE"

#### Scenario: Formato e tamanho do arquivo
- **WHEN** o arquivo `bootlogo.bmp` gerado na camada `boot/` é inspecionado
- **THEN** o arquivo é um BMP 24-bit de 640x480 com exatamente 921654 bytes e sha256 registrado no LEIA-ME da feature
