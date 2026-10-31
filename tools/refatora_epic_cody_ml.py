#!/usr/bin/env python3
"""Utilitário de extração e refatoração do tema Epic Cody para Epic Cody ML (Multi-Language).

Desacopla os textos estáticos dos nós <text> dos arquivos theme.xml de cada console/coleção
em variáveis centralizadas por idioma (_languages/en.xml, pt-br.xml, es-latam.xml), insere
o seletor <subset name="language"> no theme.xml raiz, aplica margem segura (x=0.025),
calibra a hierarquia tipográfica e o rodapé helpsystem, elimina truncamentos por reticências
e gera os SVGs de botões localizados.
"""

import argparse
import re
import sys
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

# Tabela completa de descrições históricas calibradas para 640x480 em pt-BR (<= 190 chars)
DESCRICOES_PT = {
    "action": "Jogos de ação focados em reflexos rápidos, coordenação motora e desafios em tempo real.",
    "adventure": "Jogos de aventura com histórias interativas focadas em exploração e resolução de enigmas.",
    "amiga": "Computador de 16/32-bit famoso por sua interface gráfica avançada, som estéreo e multitarefa.",
    "amigacd32": "Primeiro console doméstico de 32-bit baseado em CD-ROM lançado no Ocidente pela Commodore.",
    "amstradcpc": "Série popular de computadores domésticos de 8-bit com grande acervo de jogos na Europa.",
    "apple2": "Um dos primeiros microcomputadores de sucesso massivo, projetado por Steve Wozniak.",
    "arcade": "Máquinas clássicas operadas por moedas da era de ouro do Arcade nos anos 70 e 80.",
    "atari2600": "Console pioneiro que popularizou o uso de cartuchos com jogos e videogames domésticos.",
    "atari5200": "Console doméstico avançado da Atari baseado na arquitetura de seus computadores 8-bit.",
    "atari7800": "Console de 8-bit com gráficos aprimorados e compatibilidade total com o Atari 2600.",
    "atari800": "Família de computadores domésticos da Atari com chips dedicados de som e vídeo.",
    "atarijaguar": "Console comercializado como 64-bit com arquitetura multiprocessada da Atari.",
    "atarilynx": "Primeiro portátil com tela colorida retroiluminada e aceleração gráfica com zoom.",
    "atarist": "Computador de 16-bit com portas MIDI nativas e grande biblioteca de jogos.",
    "atomiswave": "Sistema arcade da Sammy baseado na tecnologia Dreamcast com cartuchos intercambiáveis.",
    "auto-allgames": "Lista completa com todos os jogos disponíveis instalados no seu cartão de memória.",
    "auto-favorites": "Acesso rápido a todos os títulos marcados como favoritos no sistema.",
    "auto-lastplayed": "Histórico dos títulos jogados recentemente no aparelho organizados por data.",
    "btmups": "Jogos clássicos de combate corpo a corpo contra hordas de inimigos em rolagem lateral.",
    "c128": "Sucessor do Commodore 64 com modo de 80 colunas e compatibilidade com o C64.",
    "c16": "Computador doméstico de entrada da Commodore com rica paleta de 121 cores.",
    "c64": "O modelo de computador mais vendido da história com o lendário chip de som SID.",
    "coco": "Computador Color Computer da Tandy RadioShack baseado no processador Motorola 6809E.",
    "coleco": "Console da Coleco conhecido por conversões caseiras fiéis de sucessos do Arcade.",
    "colecovision": "Console doméstico famoso por conversões quase perfeitas de clássicos do Arcade.",
    "cps1": "Placa arcade lendária da Capcom berço de clássicos como Street Fighter II e Final Fight.",
    "cps2": "Segunda geração da placa arcade da Capcom com som Q-Sound estéreo e clássicos de luta 2D.",
    "cps3": "Placa arcade avançada da Capcom com animações 2D ultra detalhadas em Street Fighter III.",
    "custom-collections": "Listas e coleções temáticas personalizadas criadas para organizar seus títulos.",
    "daphne": "Emulador de jogos clássicos de fliperama em Laserdisc como Dragon's Lair e Space Ace.",
    "doom": "Engine do clássico jogo de tiro em primeira pessoa da id Software que marcou época.",
    "dos": "Sistema operacional em disco dominante em computadores compatíveis com IBM PC.",
    "dreamcast": "Último console da Sega com jogos arcade incríveis, gráficos 3D e modem integrado.",
    "easyrpg": "Interpretador de código aberto para jogos criados com RPG Maker 2000 e 2003.",
    "famicom": "Versão japonesa original do Family Computer que iniciou a era de ouro da Nintendo.",
    "fba": "Emulador arcade multi-sistema versátil compatível com Neo-Geo, CPS e clássicos.",
    "fbn": "Emulador arcade moderno para placas clássicas, Neo-Geo, Capcom CPS e fliperamas.",
    "fbneo": "Emulador arcade multi-sistema versátil compatível com Neo-Geo, CPS e clássicos.",
    "fbneo_fbneo": "Emulador arcade multi-sistema versátil compatível com Neo-Geo, CPS e clássicos.",
    "fds": "Periférico de disquetes para Famicom que introduziu clássicos como Zelda e Metroid.",
    "fighting": "Jogos competitivos de combate mano a mano entre lutadores com golpes especiais.",
    "fixedscreen": "Clássicos do arcade onde toda a ação ocorre em uma única tela fixa sem rolagem.",
    "gameandwatch": "Série pioneira de portáteis LCD criada por Gunpei Yokoi para a Nintendo em 1980.",
    "gamegear": "Console portátil colorido da Sega com hardware poderoso baseado no Master System.",
    "gb": "O lendário portátil monocromático da Nintendo que marcou gerações com Tetris e Pokémon.",
    "gba": "Poderoso portátil de 32-bit da Nintendo com acervo excepcional de clássicos 2D e RPGs.",
    "gbc": "Evolução do Game Boy com tela colorida reflexiva e processador com o dobro de velocidade.",
    "gc": "Console cúbico da Nintendo com discos ópticos compactos e gráficos 3D marcantes.",
    "genesis": "O clássico console de 16-bit da Sega com jogabilidade veloz e biblioteca marcante.",
    "imageviewer": "Galeria multimídia para visualizar todas as capturas de tela e fotos salvas durante suas partidas.",
    "intellivision": "Console pioneiro da Mattel com processador de 16-bit e controle numérico inovador.",
    "kids": "Jogos com temática acessível e divertida para todas as idades e crianças.",
    "kodi": "Central de entretenimento e mídia para reprodução de vídeos, músicas e fotos.",
    "mame": "Emulador dedicado à preservação histórica do hardware de fliperamas e jogos arcade.",
    "mame2003": "Versão clássica do emulador MAME otimizada para placas arcade das eras de ouro.",
    "mame2010": "Versão atualizada do MAME com compatibilidade expandida para jogos arcade.",
    "mastersystem": "Console de 8-bit da Sega com gráficos vibrantes e enorme sucesso histórico no Brasil.",
    "mega32x": "Acessório de 32-bit da Sega para Mega Drive com dois processadores RISC SH-2.",
    "megacd": "Expansão de CD-ROM para Mega Drive com áudio estéreo de alta qualidade e vídeos FMV.",
    "megadrive": "O clássico console de 16-bit da Sega com jogabilidade veloz, Sonic e som marcante.",
    "msx": "Padrão de microcomputador liderado por Microsoft e ASCII com grandes jogos da Konami.",
    "msx2": "Segunda geração do MSX com paleta de 256 cores e clássicos inesquecíveis como Metal Gear.",
    "n64": "Console pioneiro em mundos 3D autênticos com alavanca analógica e jogos marcantes.",
    "n64dd": "Unidade de disco magnético reescrevível de 64MB lançada no Japão para o Nintendo 64.",
    "naomi": "Poderosa placa arcade da Sega sucessora da Model 3 com tecnologia similar ao Dreamcast.",
    "nds": "Portátil inovador da Nintendo com duas telas, entrada tátil e microfone integrado.",
    "neogeo": "O lendário sistema da SNK que levou a experiência autêntica do Arcade para casa.",
    "neogeocd": "Versão em CD do Neo Geo com trilhas sonoras orquestradas em alta fidelidade.",
    "nes": "O Nintendo Entertainment System que revitalizou a indústria mundial de videogames.",
    "ngp": "Portátil monocromático da SNK com controle em microswitch de alta precisão.",
    "ngpc": "Portátil colorido de 16-bit da SNK aclamado pelo excelente controle e jogos de luta.",
    "odyssey2": "Console pioneiro da Magnavox com teclado alfanumérico de membrana integrado.",
    "openbor": "Engine de código aberto para criação de jogos estilo Beat 'em Up em rolagem lateral.",
    "pc": "Plataforma de computadores pessoais com vasta biblioteca histórica de clássicos.",
    "pc98": "Computador da NEC que dominou o mercado de jogos japonês nos anos 80 e 90.",
    "pce-cd": "Expansão de CD-ROM pioneira para o PC Engine com trilha sonora de qualidade CD.",
    "pcengine": "Console compacto de 16-bit da NEC e Hudson Soft com excelentes conversões arcade.",
    "pcenginecd": "Primeiro console de videogame doméstico a utilizar CD-ROM com áudio de alta fidelidade.",
    "pcfx": "Console de 32-bit da NEC sucessor do PC Engine com foco em animações e vídeos FMV.",
    "pico-8": "Console virtual com limitações retrô deliberadas para desenvolvimento e jogos criativos.",
    "platformers": "Jogos clássicos focados em pulos, precisão de navegação e superação de obstáculos.",
    "ports": "Adaptações nativas de jogos clássicos de PC e engines portadas para o aparelho.",
    "power": "Opções de gerenciamento de energia para reiniciar ou desligar o aparelho com segurança.",
    "ps2": "O console doméstico mais vendido da história com Emotion Engine e leitor de DVD.",
    "psp": "Primeiro portátil da Sony com tela widescreen de alta resolução e gráficos de console.",
    "pspminis": "Linha de jogos compactos e criativos lançados digitalmente para PSP e PS3.",
    "psx": "Console de 32-bit da Sony que revolucionou a indústria com CDs e gráficos 3D marcantes.",
    "puzzle": "Jogos de raciocínio, lógica, quebra-cabeças e encaixe estratégico de peças.",
    "racing": "Competições em alta velocidade sobre pistas com veículos e desafios contra o relógio.",
    "residualvm": "Interpretador 3D de código aberto para clássicos como Grim Fandango e Myst III.",
    "retroarch": "Frontend modular para emuladores com suporte a shaders, conquistas e filtros.",
    "retropie": "Painel de ajustes do sistema, temas visuais, conexões e configurações de hardware.",
    "rpgs": "Role-playing games com histórias profundas, exploração e evolução de personagens.",
    "satellaview": "Periférico por satélite para Super Famicom com transmissões e jogos exclusivos.",
    "saturn": "Console de 32-bit da Sega com dois processadores, líder em jogos de luta 2D e arcades.",
    "scummvm": "Interpretador de clássicos de aventura gráfica da LucasArts, Sierra e outras.",
    "sega32x": "Expansão de 32-bit para o Mega Drive equipada com dois processadores RISC SH-2.",
    "segacd": "Expansão de CD-ROM para Mega Drive com áudio de CD e sequências de vídeo animadas.",
    "sfc": "Versão japonesa original do Super Famicom de 16-bit com gráficos e som lendários.",
    "sg-1000": "Primeiro console doméstico da Sega lançado no Japão no mesmo dia do Famicom em 1983.",
    "sgb": "Adaptador de Super Nintendo que permitia jogar cartuchos de Game Boy na TV a cores.",
    "shmups": "Jogos clássicos de tiro espacial em rolagem vertical ou horizontal intensa.",
    "snes": "O lendário console de 16-bit da Nintendo com chip de som SPC700 e acervo inesquecível.",
    "snes-hacks": "Modificações e melhorias criadas pela comunidade para clássicos do Super Nintendo.",
    "snesmsu1": "Jogos aprimorados de Super Nintendo com áudio com qualidade de CD via chip MSU-1.",
    "solarus": "Engine de código aberto para execução e criação de RPGs de ação no estilo 16-bit.",
    "sports": "Simulações esportivas incluindo futebol, basquete, beisebol, tênis e automobilismo.",
    "steam": "Plataforma de distribuição digital de jogos para computador da Valve Corporation.",
    "strategy": "Jogos de planejamento estratégico e tático disputados em turnos ou em tempo real.",
    "sufami": "Adaptador da Bandai para Super Famicom com minicartuchos de séries e animes.",
    "supergrafx": "Evolução do PC Engine com dois processadores de vídeo e quatro vezes mais memória RAM.",
    "sys_3do": "Plataforma multimídia de 32-bit da The 3DO Company com jogos em formato CD-ROM.",
    "tg-cd": "Versão norte-americana do CD-ROM do TurboGrafx-16 com áudio estéreo em CD.",
    "tg16": "Versão norte-americana do PC Engine de 16-bit lançada pela NEC na América do Norte.",
    "ti99": "Computador doméstico pioneiro da Texas Instruments com processador de 16-bit.",
    "tic80": "Computador virtual de fantasia para criação e execução de pequenos jogos retrô.",
    "turbografxcd": "Expansão de CD-ROM para TurboGrafx-16 com trilhas sonoras orquestradas em CD.",
    "turbographx": "Versão ocidental do PC Engine com cartuchos finos HuCard e grandes jogos de ação.",
    "uzebox": "Console retrô minimalista de código aberto baseado no microcontrolador AVR.",
    "vectrex": "Console único com monitor vetorial monocromático embutido e lâminas coloridas.",
    "vic20": "Primeiro computador a vender mais de um milhão de unidades, fabricado pela Commodore.",
    "virtualboy": "Console estereoscópico de mesa da Nintendo com gráficos em 3D em tons de vermelho.",
    "vmu": "Cartão de memória inteligente do Dreamcast com tela LCD, controles e minijogos.",
    "wii": "Console revolucionário da Nintendo com controles sensíveis a movimento Wii Remote.",
    "wiiu": "Primeiro console em alta definição da Nintendo com controle GamePad de tela tátil.",
    "wonderswan": "Portátil de 16-bit da Bandai projetado por Gunpei Yokoi jogável na vertical e horizontal.",
    "wonderswancolor": "Versão com tela colorida do portátil WonderSwan da Bandai com ótimos RPGs.",
    "x68000": "Potente computador de 16/32-bit da Sharp com conversões fiéis de sucessos do Arcade.",
    "zx81": "Computador britânico pioneiro da Sinclair de baixo custo com 1KB de memória RAM.",
    "zxspectrum": "Lendário microcomputador da Sinclair que marcou a indústria de jogos britânica.",
}

# Tabela completa de descrições históricas em es-latam (<= 190 chars)
DESCRICOES_ES = {
    "action": "Juegos de acción enfocados en reflejos rápidos, coordinación y desafíos en tiempo real.",
    "adventure": "Juegos de aventura con historias interactivas enfocadas en exploración y acertijos.",
    "amiga": "Computadora de 16/32-bit famosa por su interfaz gráfica avanzada, sonido estéreo y multitarea.",
    "amigacd32": "Primera consola doméstica de 32 bits basada en CD lanzada en Occidente por Commodore.",
    "amstradcpc": "Popular serie de computadoras de 8-bit con una gran biblioteca de juegos en Europa.",
    "apple2": "Uno de los primeros microcomputadores de gran éxito masivo, creado por Steve Wozniak.",
    "arcade": "Máquinas clásicas operadas por monedas de la era dorada del Arcade en los 70 y 80.",
    "atari2600": "Consola pionera que popularizó los cartuchos intercambiables y los videojuegos domésticos.",
    "atari5200": "Consola doméstica avanzada de Atari con hardware basado en sus computadoras de 8-bit.",
    "atari7800": "Consola de 8-bit con gráficos mejorados y retrocompatibilidad total con Atari 2600.",
    "atari800": "Familia de computadoras de Atari conocidas por sus chips dedicados de gráficos y sonido.",
    "atarijaguar": "Consola promocionada como de 64 bits con arquitectura multiprocesador de Atari.",
    "atarilynx": "Primer portátil con pantalla a color retroiluminada y zoom gráfico por hardware.",
    "atarist": "Computadora de 16-bit con puertos MIDI integrados y gran catálogo de videojuegos.",
    "atomiswave": "Sistema arcade de Sammy basado en la tecnología Dreamcast con cartuchos intercambiables.",
    "auto-allgames": "Lista completa con todos los juegos disponibles instalados en su tarjeta de memoria.",
    "auto-favorites": "Acceso rápido a todos los títulos marcados como favoritos en el sistema.",
    "auto-lastplayed": "Historial de los últimos juegos ejecutados en la consola ordenados por fecha de uso.",
    "btmups": "Juegos clásicos de combate cuerpo a cuerpo contra hordas de enemigos en avance lateral.",
    "c128": "Sucesor del Commodore 64 con modo de 80 columnas y compatibilidad casi total con el C64.",
    "c16": "Computadora doméstica de entrada de Commodore con una paleta de 121 colores.",
    "c64": "El modelo de computadora más vendido de la historia con el legendario chip de sonido SID.",
    "coco": "Computadora Color Computer de Tandy RadioShack basada en el microprocesador Motorola 6809E.",
    "coleco": "Consola famosa por traer conversiones casi perfectas de éxitos de arcade al hogar.",
    "colecovision": "Consola doméstica célebre por sus conversiones fieles de clásicos de recreativas.",
    "cps1": "Mítica placa arcade de Capcom que estableció clásicos como Street Fighter II y Final Fight.",
    "cps2": "Segunda generación de la placa de Capcom con sonido Q-Sound y clásicos de lucha 2D.",
    "cps3": "Avanzada placa arcade con animaciones 2D ultra fluidas y detalladas en Street Fighter III.",
    "custom-collections": "Listas y colecciones temáticas personalizadas creadas para organizar sus títulos.",
    "daphne": "Emulador de juegos clásicos de arcade en Laserdisc como Dragon's Lair y Space Ace.",
    "doom": "Motor del clásico juego de disparos en primera persona de id Software que marcó época.",
    "dos": "Sistema operativo de disco dominante en computadoras IBM PC compatibles en los 80 y 90.",
    "dreamcast": "Última consola de Sega con increíbles juegos arcade, gráficos avanzados y módem.",
    "easyrpg": "Intérprete de código abierto para juegos creados con RPG Maker 2000 y 2003.",
    "famicom": "Versión japonesa original del Family Computer que inició la era dorada de Nintendo.",
    "fba": "Emulador arcade versátil compatible con Neo-Geo, CPS1, CPS2, CPS3 y clásicos.",
    "fbn": "Emulador arcade moderno para placas clásicas, Neo-Geo, Capcom CPS y recreativas.",
    "fbneo": "Emulador arcade versátil compatible con Neo-Geo, CPS1, CPS2, CPS3 y clásicos.",
    "fbneo_fbneo": "Emulador arcade versátil compatible con Neo-Geo, CPS1, CPS2, CPS3 y clásicos.",
    "fds": "Periférico de disquetes para Famicom que introdujo juegos legendarios como Zelda y Metroid.",
    "fighting": "Juegos competitivos de combate mano a mano entre luchadores con movimientos especiales.",
    "fixedscreen": "Clásicos de arcade donde toda la acción ocurre en una única pantalla fija sin scroll.",
    "gameandwatch": "Serie pionera de portátiles con pantalla LCD creada por Gunpei Yokoi para Nintendo.",
    "gamegear": "Consola portátil a color de Sega basada en la arquitectura técnica de Master System.",
    "gb": "La mítica portátil monocromática de Nintendo que conquistó el mundo con Tetris y Pokémon.",
    "gba": "Potente portátil de 32-bit de Nintendo con una gran biblioteca de clásicos 2D y RPGs.",
    "gbc": "Evolución de Game Boy con pantalla a color y un procesador con el doble de velocidad.",
    "gc": "Consola cúbica de Nintendo con discos ópticos compactos y destacados gráficos en 3D.",
    "genesis": "La clásica consola de 16-bit de Sega conocida por Sonic, su velocidad y sonido.",
    "imageviewer": "Galería multimedia para ver todas las capturas de pantalla e imágenes guardadas durante tus partidas.",
    "intellivision": "Consola pionera de Mattel con procesador de 16-bit y control numérico innovador.",
    "kids": "Juegos con temática accesible y divertida para todas las edades y niños.",
    "kodi": "Centro de entretenimiento multimedia para reproducir videos, música y fotos.",
    "mame": "Emulador dedicado a la preservación histórica del hardware de recreativas y arcade.",
    "mame2003": "Versión clásica del emulador MAME optimizada para placas arcade de la era dorada.",
    "mame2010": "Versión actualizada de MAME con compatibilidad extendida para juegos arcade clásicos.",
    "mastersystem": "Consola de 8-bit de Sega con gráficos vibrantes y un enorme éxito en Europa y Brasil.",
    "mega32x": "Accesorio de 32 bits para Mega Drive con dos potentes procesadores RISC SH-2.",
    "megacd": "Expansión de CD-ROM para Mega Drive con audio en calidad de CD y secuencias de video.",
    "megadrive": "La clásica consola de 16-bit de Sega conocida por Sonic, su velocidad y sonido.",
    "msx": "Estándar de microcomputadora con una destacada biblioteca de juegos clásicos de Konami.",
    "msx2": "Segunda generación de MSX con paleta de 256 colores y títulos míticos como Metal Gear.",
    "n64": "Consola pionera en mundos 3D auténticos con palanca analógica y grandes clásicos.",
    "n64dd": "Unidad de disco magnético regrabable de 64MB lanzada en Japón para Nintendo 64.",
    "naomi": "Potente placa arcade de Sega sucesora de Model 3 con arquitectura similar a Dreamcast.",
    "nds": "Innovadora portátil de Nintendo con dos pantallas, panel táctil y micrófono integrado.",
    "neogeo": "El mítico sistema de SNK que llevó la auténtica experiencia recreativa al salón de casa.",
    "neogeocd": "Versión en CD de Neo Geo con bandas sonoras orquestadas en alta fidelidad de audio.",
    "nes": "El Nintendo Entertainment System que revitalizó la industria mundial de los videojuegos.",
    "ngp": "Portátil monocromático de SNK famoso por su microswitch de control de alta precisión.",
    "ngpc": "Portátil a color de 16-bit de SNK elogiado por su gran control y juegos de lucha.",
    "odyssey2": "Consola de Magnavox/Philips con teclado alfanumérico de membrana integrado en el chasis.",
    "openbor": "Motor de código abierto para creación de juegos Beat 'em Up con múltiples personajes.",
    "pc": "Plataforma de computadoras personales con una inmensa biblioteca histórica de clásicos.",
    "pc98": "Computadora de NEC que dominó el mercado japonés de videojuegos durante más de una década.",
    "pce-cd": "Expansión pionera de CD-ROM para PC Engine con bandas sonoras en calidad de CD.",
    "pcengine": "Consola compacta de 16-bit de NEC y Hudson Soft con grandes conversiones arcade.",
    "pcenginecd": "Primer sistema doméstico en utilizar CD-ROM con audio de alta fidelidad acústica.",
    "pcfx": "Consola de 32 bits de NEC sucesora de PC Engine con diseño en torre y video JPEG FMV.",
    "pico-8": "Consola virtual con limitaciones retro intencionales para desarrollo creativo de juegos.",
    "platformers": "Juegos clásicos enfocados en saltos, precisión de movimiento y esquivar obstáculos.",
    "ports": "Adaptaciones nativas de juegos clásicos de PC y motores portados a consolas portátiles.",
    "power": "Opciones de gestión de energía para reiniciar o apagar el sistema con total seguridad.",
    "ps2": "La consola doméstica más vendida de la historia con chip Emotion Engine y lector DVD.",
    "psp": "Primer portátil de Sony con pantalla panorámica de alta definición y gráficos de consola.",
    "pspminis": "Gama de videojuegos descargables compactos e innovadores para PSP y PlayStation 3.",
    "psx": "La revolucionaria consola de 32 bits de Sony que transformó la industria con juegos en CD.",
    "puzzle": "Juegos de ingenio, lógica, acertijos y resolución estratégica de paneles.",
    "racing": "Competencias de alta velocidad en circuitos con vehículos y desafíos contrarreloj.",
    "residualvm": "Intérprete 3D de código abierto para aventuras como Grim Fandango y Myst III.",
    "retroarch": "Frontend modular para emuladores con soporte para shaders, logros y filtros visuales.",
    "retropie": "Ajustes del sistema, redes inalámbricas, temas visuales y configuración de hardware.",
    "rpgs": "Juegos de rol con historias profundas, exploración de mundos y progresión de personajes.",
    "satellaview": "Periférico satelital de Nintendo para Super Famicom con emisiones y juegos exclusivos.",
    "saturn": "Consola de 32 bits de Sega con dos procesadores, reina de los juegos de lucha 2D y arcades.",
    "scummvm": "Intérprete para aventuras gráficas clásicas de LucasArts, Sierra y otras compañías.",
    "sega32x": "Accesorio de 32 bits para Mega Drive equipado con dos procesadores RISC SH-2.",
    "segacd": "Expansión de CD-ROM para Mega Drive con audio en calidad de CD y secuencias de video.",
    "sfc": "Versión japonesa original de Super Famicom de 16-bit con gráficos y sonido legendarios.",
    "sg-1000": "Primera consola de videojuegos lanzada por Sega en Japón el mismo día que Famicom en 1983.",
    "sgb": "Adaptador para Super Nintendo que permitía jugar cartuchos de Game Boy en el televisor.",
    "shmups": "Clásicos juegos de disparos con naves espaciales en intenso avance vertical u horizontal.",
    "snes": "La legendaria consola de 16-bit de Nintendo con chip de sonido SPC700 y catálogo histórico.",
    "snes-hacks": "Modificaciones y mejoras creadas por la comunidad para clásicos de Super Nintendo.",
    "snesmsu1": "Juegos mejorados de Super Nintendo con audio en calidad de CD mediante chip MSU-1.",
    "solarus": "Motor de código abierto enfocado en crear y ejecutar juegos de acción RPG estilo 16-bit.",
    "sports": "Simuladores deportivos que incluyen fútbol, baloncesto, béisbol, tenis y carreras.",
    "steam": "Plataforma de distribución digital de videojuegos para PC de Valve Corporation.",
    "strategy": "Juegos de pensamiento táctico y planificación estratégica por turnos o en tiempo real.",
    "sufami": "Adaptador de Bandai para Super Famicom con minicartuchos de juegos de anime.",
    "supergrafx": "Evolución de PC Engine con dos procesadores de video y cuatro veces más memoria RAM.",
    "sys_3do": "Plataforma multimedia de 32-bit creada por The 3DO Company con tecnología CD-ROM.",
    "tg-cd": "Versión norteamericana del CD-ROM de TurboGrafx-16 con audio estéreo en CD.",
    "tg16": "Versión norteamericana de PC Engine de 16-bit lanzada por NEC en América del Norte.",
    "ti99": "Computadora doméstica pionera de Texas Instruments equipada con procesador de 16 bits.",
    "tic80": "Computadora virtual de fantasía para crear y ejecutar minijuegos retro.",
    "turbografxcd": "Expansión de CD-ROM para TurboGrafx-16 con bandas sonoras orquestadas en CD.",
    "turbographx": "Versión occidental de PC Engine con tarjetas finas HuCard y grandes juegos de acción.",
    "uzebox": "Consola retro minimalista de código abierto basada en microcontrolador AVR.",
    "vectrex": "Consola única con monitor vectorial integrado en blanco y negro y láminas de color.",
    "vic20": "Primer computador de la historia en vender más de un millón de unidades, de Commodore.",
    "virtualboy": "Consola estereoscópica de Nintendo diseñada para ilusión de profundidad en rojo.",
    "vmu": "Tarjeta de memoria inteligente de Dreamcast con pantalla monocromática y minijuegos.",
    "wii": "Revolucionaria consola de Nintendo con mandos por movimiento Wii Remote de gran éxito.",
    "wiiu": "Primera consola en alta definición de Nintendo con mando GamePad con pantalla táctil.",
    "wonderswan": "Portátil de 16-bit de Bandai diseñado por Gunpei Yokoi jugable en vertical y horizontal.",
    "wonderswancolor": "Versión con pantalla a color de la portátil WonderSwan de Bandai con grandes RPGs.",
    "x68000": "Potente computadora de 16/32-bit de Sharp con adaptaciones idénticas a los arcades.",
    "zx81": "Computadora británica pionera de Sinclair de bajo coste con 1KB de memoria RAM.",
    "zxspectrum": "Mítica microcomputadora británica de Sinclair que definió los videojuegos en Europa.",
}

def sanitiza_xml(texto: str) -> str:
    """Escapa entidades XML básicas e & soltos mantendo entidades já existentes."""
    return re.sub(r'&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)', '&amp;', texto)

def normaliza_var_prefix(sys_name: str) -> str:
    """Gera o identificador de variável XML válido para o sistema/coleção."""
    prefix = sys_name.replace("/", "_")
    if prefix and prefix[0].isdigit():
        prefix = f"sys_{prefix}"
    return prefix

def gera_svg_botao_entrar() -> str:
    """Gera o SVG estilizado do botão de ação com o texto (A) ENTRAR."""
    outer_pill = (
        "M125,0H25C11.2,0,0,11.2,0,25s11.2,25,25,25h100c13.8,0,25-11.2,25-25S138.8,0,125,0z "
        "M25.9,46.8C13.8,46.8,4.1,37,4.1,25S13.8,3.2,25.9,3.2c12,0,21.8,9.8,21.8,21.8S37.9,46.8,25.9,46.8z"
    )
    a_circle_path = "M22.8,13.1l-3.7,23.1h3.3L23,32h4.5l0.6,4.2h3.7l-3.7-23.1H22.8z M23.5,28.9l1.7-11.7L27,28.9H23.5z"

    def letter_E(x):
        return f"M{x+9.9:.1f},16.4h-6.3v6.4h5v3.3h-5v6.8h6.3v3.3h-9.9V13.1h9.9V16.4z"

    def letter_N(x):
        return (
            f"M{x+11.5:.1f},36.2h-3.7l-4.5-16.7v16.7h-3.3V13.1h4.6l3.7,13.8V13.1h3.2"
            f"C{x+11.5:.1f},13.1,{x+11.5:.1f},36.2,{x+11.5:.1f},36.2z"
        )

    def letter_T(x):
        return (
            f"M{x+11.2:.1f},16.4h-3.8v19.8h-3.6V16.4h-3.8v-3.3h11.2"
            f"L{x+11.2:.1f},16.4L{x+11.2:.1f},16.4z"
        )

    def letter_R(x):
        body = (
            f"M{x+7.6:.1f},36.2c-0.2-0.6-0.3-1-0.3-2.8v-3.6c0-2.1-0.7-2.9-2.4-2.9h-1.3v9.4h-3.6V13.1h5.5"
            f"c3.8,0,5.4,1.7,5.4,5.3v1.8c0,2.4-0.8,3.9-2.4,4.7c1.8,0.8,2.4,2.5,2.4,4.9v3.6c0,1.1,0,1.9,0.4,2.8H{x+7.6:.1f}z"
        )
        hole = (
            f"M{x+5.4:.1f},16.4h-1.7v7.1h1.4c1.4,0,2.2-0.6,2.2-2.4v-2.3C{x+7.3:.1f},17.1,{x+6.7:.1f},16.4,{x+5.4:.1f},16.4z"
        )
        return body, hole

    def letter_A(x):
        return (
            f"M{x+3.7:.1f},13.1h5.3l3.7,23.1h-3.7l-0.6-4.2h-4.5l-0.6,4.2h-3.3l3.7-23.1z "
            f"M{x+4.4:.1f},28.9h3.5l-1.8-11.7L{x+4.4:.1f},28.9z"
        )

    xE = 56.5
    xN = 68.4
    xT = 81.7
    xR1 = 94.7
    xA = 107.4
    xR2 = 121.9

    path_E = letter_E(xE)
    path_N = letter_N(xN)
    path_T = letter_T(xT)
    body_R1, hole_R1 = letter_R(xR1)
    path_A = letter_A(xA)
    body_R2, hole_R2 = letter_R(xR2)

    combined_main_path = f"{outer_pill} {path_E} {path_N} {path_T} {body_R1} {path_A} {body_R2}"

    return f"""<?xml version="1.0" encoding="utf-8"?>
<!-- Generator: Adobe Illustrator 24.0.3, SVG Export Plug-In . SVG Version: 6.00 Build 0)  -->
<svg version="1.0" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
\t width="150px" height="50px" viewBox="0 0 150 50" enable-background="new 0 0 150 50" xml:space="preserve">
<g>
\t<path fill="#FFFFFF" d="{a_circle_path}"/>
\t<path fill="#FFFFFF" d="{combined_main_path}"/>
\t<path fill="#FFFFFF" d="{hole_R1}"/>
\t<path fill="#FFFFFF" d="{hole_R2}"/>
</g>
</svg>
"""

def gera_svg_botao_enter() -> str:
    """Gera o SVG upstream original com o texto (A) ENTER."""
    return """<?xml version="1.0" encoding="utf-8"?>
<!-- Generator: Adobe Illustrator 24.0.3, SVG Export Plug-In . SVG Version: 6.00 Build 0)  -->
<svg version="1.0" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px"
\t width="150px" height="50px" viewBox="0 0 150 50" enable-background="new 0 0 150 50" xml:space="preserve">
<g>
\t<path fill="#FFFFFF" d="M22.8,13.1l-3.7,23.1h3.3L23,32h4.5l0.6,4.2h3.7l-3.7-23.1H22.8z M23.5,28.9l1.7-11.7L27,28.9H23.5z"/>
\t<path fill="#FFFFFF" d="M125,0H25C11.2,0,0,11.2,0,25s11.2,25,25,25h100c13.8,0,25-11.2,25-25S138.8,0,125,0z M25.9,46.8
\t\tC13.8,46.8,4.1,37,4.1,25S13.8,3.2,25.9,3.2c12,0,21.8,9.8,21.8,21.8S37.9,46.8,25.9,46.8z M75.1,16.4h-6.3v6.4h5v3.3h-5v6.8h6.3
\t\tv3.3h-9.9V13.1h9.9V16.4z M88.8,36.2h-3.7l-4.5-16.7v16.7h-3.3V13.1h4.6l3.7,13.8V13.1h3.2C88.8,13.1,88.8,36.2,88.8,36.2z
\t\t M101.6,16.4h-3.8v19.8h-3.6V16.4h-3.8v-3.3h11.2L101.6,16.4L101.6,16.4z M113.1,16.4h-6.3v6.4h5v3.3h-5v6.8h6.3v3.3h-9.9V13.1h9.9
\t\tV16.4z M122.9,36.2c-0.2-0.6-0.3-1-0.3-2.8v-3.6c0-2.1-0.7-2.9-2.4-2.9h-1.3v9.4h-3.6V13.1h5.5c3.8,0,5.4,1.7,5.4,5.3v1.8
\t\tc0,2.4-0.8,3.9-2.4,4.7c1.8,0.8,2.4,2.5,2.4,4.9v3.6c0,1.1,0,1.9,0.4,2.8H122.9z"/>
\t<path fill="#FFFFFF" d="M120.7,16.4H119v7.1h1.4c1.4,0,2.2-0.6,2.2-2.4v-2.3C122.6,17.1,122,16.4,120.7,16.4z"/>
</g>
</svg>
"""

def extrai_textos_do_tarball(tar_path: Path):
    """Lê o tarball do tema upstream e extrai os pares (sistema, campo, texto)."""
    systems_data = {}
    root_theme_content = None

    with tarfile.open(tar_path, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.isreg():
                continue
            name = member.name
            parts = name.split("/", 1)
            if len(parts) < 2:
                continue
            rel = parts[1]

            if rel == "theme.xml":
                root_theme_content = tar.extractfile(member).read().decode("utf-8", errors="replace")
            elif rel.endswith("/theme.xml"):
                sys_name = rel.rsplit("/theme.xml", 1)[0]
                raw_content = tar.extractfile(member).read().decode("utf-8", errors="replace")
                clean_content = sanitiza_xml(raw_content)
                root = ET.fromstring(clean_content)
                
                fields = []
                for text_node in root.findall(".//text[@name]"):
                    name_attr = text_node.get("name")
                    inner = text_node.find("text")
                    if inner is not None and inner.text and inner.text.strip():
                        fields.append((name_attr, inner.text.strip()))
                
                systems_data[sys_name] = (root, fields)

    return root_theme_content, systems_data

def refatora_console_tree(root: ET.Element, sys_name: str) -> str:
    """Substitui o conteúdo de cada nó <text> pelo placeholder ${sistema.campo} e garante sys_line1."""
    prefix = normaliza_var_prefix(sys_name)

    # Injeta <text name="sys_line1" extra="true"> se ausente na view system
    sys_view = None
    for view in root.findall(".//view"):
        names = [n.strip() for n in (view.get("name") or "").split(",")]
        if "system" in names:
            sys_view = view
            break

    if sys_view is not None and sys_view.find(".//text[@name='sys_line1']") is None:
        line1_elem = ET.Element("text", {"name": "sys_line1", "extra": "true"})
        inner = ET.SubElement(line1_elem, "text")
        inner.text = f"${{{prefix}.sys_line1}}"

        line2_node = sys_view.find(".//text[@name='sys_line2']")
        if line2_node is not None:
            idx = list(sys_view).index(line2_node)
            sys_view.insert(idx, line1_elem)
        else:
            sys_view.append(line1_elem)

    for text_node in root.findall(".//text[@name]"):
        name_attr = text_node.get("name")
        inner = text_node.find("text")
        if inner is not None and inner.text and inner.text.strip():
            inner.text = f"${{{prefix}.{name_attr}}}"

    ET.indent(root, space="  ")
    xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
    return xml_str + "\n"

def gera_catalogo_xml(variaveis: dict) -> str:
    """Gera o arquivo XML de catálogo de idioma para o subset."""
    lines = [
        "<theme>",
        "  <formatVersion>7</formatVersion>",
        "  <variables>",
    ]
    for key in sorted(variaveis.keys()):
        val = sanitiza_xml(variaveis[key])
        lines.append(f"    <{key}>{val}</{key}>")
    lines.append("  </variables>")
    lines.append("</theme>")
    lines.append("")
    return "\n".join(lines)

def refatora_raiz_theme_xml(content: str) -> str:
    """Atualiza o theme.xml raiz com seletor de idiomas, margens seguras (x=0.025) e hierarquia calibrada."""
    # Subset de idiomas
    if '<subset name="language"' not in content:
        subset_xml = """\t<subset name="language" displayName="${languageSubsetName}">
        <include name="pt-br" displayName="Português (Brasil)">./_languages/pt-br.xml</include>
        <include name="es-latam" displayName="Español (Latino)">./_languages/es-latam.xml</include>
        <include name="en" displayName="English">./_languages/en.xml</include>
    </subset>\n\n"""

        pattern = r'(\s*<subset name="controller")'
        match = re.search(pattern, content)
        if match:
            idx = match.start(1)
            content = content[:idx] + "\n" + subset_xml + content[idx:]
        else:
            idx = content.find('<view name="system">')
            if idx != -1:
                content = content[:idx] + subset_xml + content[idx:]
            else:
                content = content + "\n" + subset_xml

    # Calibra elementos da visualização system
    calibrated_system_block = """    <text name="shortdescription" extra="true">
        <fontPath>./_art/Acre.otf</fontPath>
        <alignment>left</alignment>
        <forceUppercase>0</forceUppercase>
        <fontSize>0.022</fontSize>
        <color>ffffff</color>
        <origin>0 0</origin>
        <pos>0.025 0.080</pos>
        <size>0.320 0.025</size>
    </text>

    <text name="sys_line1" extra="true">
        <fontPath>./_art/BebasNeue.otf</fontPath>
        <alignment>left</alignment>
        <forceUppercase>1</forceUppercase>
        <color>FFFFFF</color>
        <fontSize>0.045</fontSize>
        <origin>0 0</origin>
        <pos>0.025 0.115</pos>
        <size>0.975 0.045</size>
    </text>
    
    <text name="sys_line2" extra="true">
        <fontPath>./_art/BebasNeue.otf</fontPath>
        <alignment>left</alignment>
        <forceUppercase>1</forceUppercase>
        <fontSize>0.130</fontSize>
        <origin>0 0</origin>
        <pos>0.025 0.160</pos>
        <size>0.975 0.200</size>
        <color>FFFFFF</color>
    </text>

    <image name="buttonA" extra="true">
        <path>${buttonImage}</path>
        <path>./_art/var/button.svg</path>
        <tile>false</tile>
        <origin>0 0</origin>
        <pos>0.025 0.460</pos>
        <size>0 0.085</size>
        <color>585858</color>
    </image>

    <text name="systemInfo">
        <fontPath>./_art/BebasNeue.otf</fontPath>
        <alignment>left</alignment>
        <backgroundColor>00000000</backgroundColor>
        <forceUppercase>1</forceUppercase>
        <color>FFAE00</color>
        <origin>0 0</origin>
        <pos>0.025 0.570</pos>
        <size>0.400 0.042</size>
        <fontSize>0.050</fontSize>
    </text>
    
    <text name="longdescription" extra="true">
        <fontPath>./_art/Acre.otf</fontPath>
        <alignment>left</alignment>
        <forceUppercase>0</forceUppercase>
        <fontSize>0.022</fontSize>
        <color>ffffff</color>
        <lineSpacing>1.18</lineSpacing>
        <origin>0 0</origin>
        <pos>0.025 0.660</pos>
        <size>0.30 0.26</size>
    </text>

    <image name="controller" extra="true">
        <path>./_art/controllers/${system.theme}.png</path>
        <tile>false</tile>
        <origin>0 0</origin>
        <pos>0.35 0.62</pos>
        <maxSize>0.28 0.28</maxSize>
    </image>

    <helpsystem name="help">
        <fontPath>./_art/Acre.otf</fontPath>
        <fontSize>0.022</fontSize>
        <textColor>A0A0A0</textColor>
        <iconColor>FFAE00</iconColor>
        <pos>0.025 0.965</pos>
        <origin>0 1</origin>
    </helpsystem>
</view>"""

    # Substitui bloco antigo de views do system
    old_system_pattern = re.compile(
        r'<text name="sys_line1".*?</view>',
        re.DOTALL
    )
    if old_system_pattern.search(content):
        content = old_system_pattern.sub(calibrated_system_block, content, count=1)
    else:
        # Tenta casar shortdescription se ela já veio primeiro
        alt_pattern = re.compile(
            r'<text name="shortdescription".*?</view>',
            re.DOTALL
        )
        if alt_pattern.search(content):
            content = alt_pattern.sub(calibrated_system_block, content, count=1)

    # Helpsystem na view basic, detailed, video, grid e unificação de views
    calibrated_gamelist_block = """<view name="basic, detailed, video, grid">

    <image name="background" extra="true">
        <tile>false</tile>
        <path>./_art/ingame-global-bg.png</path>
        <size>1 1</size>
        <pos>0 0</pos>
    </image>

    <textlist name="gamelist">
        <selectorColor>1c1c1c</selectorColor>
        <selectedColor>FFAE00</selectedColor>
        <selectorHeight>0.06</selectorHeight>
        <primaryColor>585858</primaryColor>
        <secondaryColor>888888</secondaryColor>
        <fontPath>./_art/Acre.otf</fontPath>
        <alignment>left</alignment>
        <pos>0 0.12</pos>
	    <size>0.319 0.805</size>
        <fontSize>0.03</fontSize>
        <lineSpacing>1.683</lineSpacing>
        <horizontalMargin>0.025</horizontalMargin>
    </textlist>
	
	<helpsystem name="help">
        <fontPath>./_art/Acre.otf</fontPath>
        <fontSize>0.022</fontSize>
        <textColor>A0A0A0</textColor>
        <iconColor>FFAE00</iconColor>
        <pos>0.025 0.965</pos>
	    <origin>0 1</origin>
    </helpsystem>
    
    <text name="top_label" extra="true">
        <fontPath>./_art/BebasNeue.otf</fontPath>
        <text>${top_label}</text>
        <alignment>left</alignment>
        <color>F8F8F8</color>
        <fontSize>0.050</fontSize>
        <origin>0 0</origin>
        <pos>0.025 0.025</pos>
        <size>0.28 0.08</size>
    </text>
    
    <text name="nameLabel" extra="true">
        <fontPath>./_art/BebasNeue.otf</fontPath>
        <alignment>left</alignment>
        <forceUppercase>1</forceUppercase>
        <color>FFAE00</color>
        <fontSize>0.050</fontSize>
        <origin>0 0</origin>
        <pos>0.339 0.025</pos>
        <size>0.64 0.08</size>
        <zIndex>50</zIndex>
    </text>

    <image name="md_image">
        <tile>false</tile>
        <origin>0.5 0.5</origin>
        <pos>0.66 0.485</pos>
        <maxSize>0.62 0.70</maxSize>
    </image>

    <video name="md_video">
        <origin>0.5 0.5</origin>
        <pos>0.66 0.485</pos>
        <maxSize>0.62 0.70</maxSize>
        <delay>1.4</delay>
        <showSnapshotNoVideo>true</showSnapshotNoVideo>
        <showSnapshotDelay>true</showSnapshotDelay>
    </video>
    
    <text name="md_name">
        <fontPath>./_art/BebasNeue.otf</fontPath>
        <alignment>left</alignment>
        <color>FFFFFF</color>
        <fontSize>0.045</fontSize>
        <origin>0 0</origin>
        <pos>0.339 0.865</pos>
        <size>0.64 0.06</size>
        <zIndex>50</zIndex>
        <singleLineScroll>true</singleLineScroll>
    </text>

    <image name="md_marquee">
        <pos>0.6598958333333333 0.220</pos>
        <origin>0.5 0.5</origin>
        <maxSize>0.300 0.180</maxSize>
    </image>

    <text name="txt_descript" extra="true">
        <text></text>
        <fontPath>./_art/Acre.otf</fontPath>
        <alignment>left</alignment>
        <fontSize>0.02</fontSize>
        <color>FFAE00</color>
        <origin>0 0</origin>
        <pos>0.339 0.630</pos>
        <size>0.06 0.2</size>
    </text> 
        
    <!-- Hidden Elements -->
    <text name="shortdescription, longdescription" extra="true">
        <origin>1 1</origin>
        <pos>0 0</pos>
        <color>00000000</color>
    </text>
        
    <text name="md_lbl_releasedate, md_lbl_developer, md_developer, md_lbl_playcount, md_playcount, md_lbl_lastplayed, md_lbl_publisher, md_publsher">
        <origin>1 1</origin>
        <color>00000000</color>
        <pos>0 0</pos>
    </text>

    <datetime name="md_releasedate, md_lastplayed">
        <origin>1 1</origin>
        <color>00000000</color>
        <pos>0 0</pos>
    </datetime>
        
</view>"""

    # Substitui todo o bloco de gamelist antigo (basic, detailed, video e features)
    old_gamelist_pattern = re.compile(
        r'<view name="basic,\s*detailed,\s*video">.*?(?=\s*<view name="screen">)',
        re.DOTALL
    )
    if old_gamelist_pattern.search(content):
        content = old_gamelist_pattern.sub(calibrated_gamelist_block + "\n\n", content, count=1)
    else:
        alt_gamelist_pattern = re.compile(
            r'<view name="basic,\s*detailed,\s*video,\s*grid">.*?(?=\s*<view name="screen">)',
            re.DOTALL
        )
        if alt_gamelist_pattern.search(content):
            content = alt_gamelist_pattern.sub(calibrated_gamelist_block + "\n\n", content, count=1)

    # Menu calibrado
    calibrated_menu_block = """  <view name="menu">
    <menuBackground name="menubg">
      <color>202020</color>
    </menuBackground>
    <menuText name="menutitle">
      <fontPath>./_art/BebasNeue.otf</fontPath>
      <fontSize>0.038</fontSize>
      <color>FFAE00</color>
      <alignment>left</alignment>
    </menuText>
    <menuText name="menutext">
      <fontPath>./_art/Acre.otf</fontPath>
      <fontSize>0.030</fontSize>
      <color>FFAE00</color>
    </menuText>
    <menuText name="menufooter">
      <fontPath>./_art/Acre.otf</fontPath>
      <fontSize>0.022</fontSize>
      <color>A0A0A0</color>
    </menuText>
    <menuText name="menutextsmall">
      <fontPath>./_art/Acre.otf</fontPath>
      <fontSize>0.028</fontSize>
      <color>888888</color>
    </menuText>
    <menuTextEdit name="menutextedit">
      <inactive>./_art/assets/textinput_inactive.png</inactive>
      <active>./_art/assets/textinput_active.png</active>
    </menuTextEdit>
  </view>"""

    old_menu_pattern = re.compile(r'<view name="menu">.*?</view>', re.DOTALL)
    if old_menu_pattern.search(content):
        content = old_menu_pattern.sub(calibrated_menu_block, content, count=1)

    return content

def traduz_shortdescription(s: str, lang: str) -> str:
    """Traduz subtítulos técnicos mantendo limites de caracteres (<= 35)."""
    if lang == "pt-br":
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*(\d+-bit|\d+/\d+-bit)\s+Handheld Console', r'\1  ·  Portátil \2', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*(\d+-bit|\d+/\d+-bit)\s+Console', r'\1  ·  Console \2', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*(\d+-bit|\d+/\d+-bit)\s+Computer', r'\1  ·  Computador \2', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*Arcade Machines', r'\1  ·  Máquinas Arcade', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*Handheld Console', r'\1  ·  Console Portátil', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*Home Computer', r'\1  ·  Computador Doméstico', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*Desktop Computers', r'\1  ·  Computador PC', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*Arcade Board', r'\1  ·  Placa Arcade', s)
        
        direta = {
            "Game Genre": "Gênero de Jogo",
            "All Consoles / Handhelds": "Todos os Sistemas",
            "Coin Operated Cabinet": "Máquinas Arcade",
            "Laserdisc Console": "Jogos em Laserdisc",
            "LZdoom · Doom Engine": "Engine de Jogo Doom",
            "2019  ·  CUSTOM RPG Engine": "Engine de Jogos RPG",
            "Handheld Electronic Games": "Jogos Eletrônicos Portáteis",
            "Streaming Video Service": "Central de Mídia",
            "2003  ·  Pixel Engine": "Console Virtual Fantasia",
            "Software": "Ports de Jogos",
            "Shut Down Menu": "Menu de Energia",
            "CROSS PLATFORM COMPUTER": "Engine de Jogos de PC",
            "Cross Platform Computer": "Engine de Jogos de PC",
            "Front-End": "Interface de Emulação",
            "System Configuration": "Configuração do Sistema",
            "1995  ·  16-bit Accessory": "1995  ·  Módem Satelital 16-bit",
            "2006 · Open Source Engine": "2006  ·  Engine de RPG 2D",
            "Digital Platform": "Plataforma Digital",
            "1996  ·  16-bit accessory": "1996  ·  Adaptador 16-bit",
            "1981  ·  16 Bit Computer": "1981  ·  Computador 16-bit",
            "2017  ·  16-bit Fantasy Computer": "2017  ·  Computador Fantasia",
            "1995  ·  32-bit Table-top Console": "1995  ·  Console 32-bit 3D",
            "1998  ·  8-bit Sanyo LC8670": "1998  ·  Cartão Memória LCD",
            "2003  ·  32-bit Board": "2003  ·  Placa Arcade 32-bit",
            "1980  ·  Game & Watch": "1980  ·  Portátil LCD",
            "1994  ·  Capcom Arcade": "1994  ·  Arcade Capcom",
            "1989  ·  Capcom Arcade": "1989  ·  Arcade Capcom",
            "1996  ·  Capcom Arcade": "1996  ·  Arcade Capcom",
            "1990's  ·  Arcade Machines": "Anos 90  ·  Máquinas Arcade",
            "1970's  ·  Arcade Machines": "Anos 70  ·  Máquinas Arcade",
            "1980's  ·  Arcade Machines": "Anos 80  ·  Máquinas Arcade",
            "Ports": "Ports de Jogos",
            "1982  ·  8-bit Console": "1982  ·  Console 8-bit",
        }
        return direta.get(s, s)
    elif lang == "es-latam":
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*(\d+-bit|\d+/\d+-bit)\s+Handheld Console', r'\1  ·  Portátil \2', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*(\d+-bit|\d+/\d+-bit)\s+Console', r'\1  ·  Consola \2', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*(\d+-bit|\d+/\d+-bit)\s+Computer', r'\1  ·  Computadora \2', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*Arcade Machines', r'\1  ·  Máquinas Arcade', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*Handheld Console', r'\1  ·  Consola Portátil', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*Home Computer', r'\1  ·  Computadora Doméstica', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*Desktop Computers', r'\1  ·  Computadora PC', s)
        s = re.sub(r'(\d{4}(?:\'s)?)\s*·\s*Arcade Board', r'\1  ·  Placa Arcade', s)
        
        direta = {
            "Game Genre": "Género de juego",
            "All Consoles / Handhelds": "Todos los sistemas",
            "Coin Operated Cabinet": "Máquinas Arcade",
            "Laserdisc Console": "Juegos en Laserdisc",
            "LZdoom · Doom Engine": "Motor de juego Doom",
            "2019  ·  CUSTOM RPG Engine": "Motor de juegos RPG",
            "Handheld Electronic Games": "Juegos Portátiles LCD",
            "Streaming Video Service": "Centro multimedia",
            "2003  ·  Pixel Engine": "Consola Virtual Fantasía",
            "Software": "Ports de juegos",
            "Shut Down Menu": "Menú de apagado",
            "CROSS PLATFORM COMPUTER": "Motor de juegos de PC",
            "Cross Platform Computer": "Motor de juegos de PC",
            "Front-End": "Interfaz de emulación",
            "System Configuration": "Configuración del sistema",
            "1995  ·  16-bit Accessory": "1995  ·  Módem Satelital 16-bit",
            "2006 · Open Source Engine": "2006  ·  Motor de RPG 2D",
            "Digital Platform": "Plataforma digital",
            "1996  ·  16-bit accessory": "1996  ·  Adaptador 16-bit",
            "1981  ·  16 Bit Computer": "1981  ·  Computadora 16-bit",
            "2017  ·  16-bit Fantasy Computer": "2017  ·  Computadora Fantasía",
            "1995  ·  32-bit Table-top Console": "1995  ·  Consola 32-bit 3D",
            "1998  ·  8-bit Sanyo LC8670": "1998  ·  Tarjeta Memoria LCD",
            "2003  ·  32-bit Board": "2003  ·  Placa Arcade 32-bit",
            "1980  ·  Game & Watch": "1980  ·  Portátil LCD",
            "1994  ·  Capcom Arcade": "1994  ·  Arcade Capcom",
            "1989  ·  Capcom Arcade": "1989  ·  Arcade Capcom",
            "1996  ·  Capcom Arcade": "1996  ·  Arcade Capcom",
            "1990's  ·  Arcade Machines": "Años 90  ·  Máquinas Arcade",
            "1970's  ·  Arcade Machines": "Años 70  ·  Máquinas Arcade",
            "1980's  ·  Arcade Machines": "Años 80  ·  Máquinas Arcade",
            "Ports": "Ports de juegos",
            "1982  ·  8-bit Console": "1982  ·  Consola 8-bit",
        }
        return direta.get(s, s)
    return s

def monta_catalogos(en_vars: dict):
    """Gera os dicionários completos de variáveis para en, pt-br e es-latam."""
    en_vars["buttonImage"] = "./_art/var/button.svg"
    pt_vars = dict(en_vars)
    es_vars = dict(en_vars)

    pt_vars["buttonImage"] = "./_art/var/button-pt.svg"
    es_vars["buttonImage"] = "./_art/var/button-es.svg"

    en_vars["top_label"] = "GAMES"
    pt_vars["top_label"] = "GAMES"
    es_vars["top_label"] = "JUEGOS"

    # Metadados de controle e menu
    pt_vars["languageSubsetName"] = "Idioma do Tema"
    pt_vars["controllerSubsetName"] = "Mostrar controles no sistema"
    pt_vars["on"] = "Ligado"
    pt_vars["off"] = "Desligado"

    es_vars["languageSubsetName"] = "Idioma del tema"
    es_vars["controllerSubsetName"] = "Mostrar mandos en sistema"
    es_vars["on"] = "Activado"
    es_vars["off"] = "Desactivado"

    # Curadorias de títulos e divisão semântica (Linha 1 Marca/Família, Linha 2 Modelo/Identificador)
    curations = [
        # ImageViewer (galeria de capturas)
        ("imageviewer", "sys_line1", "Media", "Galeria", "Galería"),
        ("imageviewer", "sys_line2", "Images", "Imagens", "Imágenes"),
        ("imageviewer", "nameLabel", "Image Viewer", "Visualizador de Imagens", "Visor de Imágenes"),
        ("imageviewer", "shortdescription", "Screenshots and photos", "Capturas de tela e fotos", "Capturas de pantalla y fotos"),
        ("imageviewer", "longdescription", "Multimedia gallery to view all screenshots and photos saved during gameplay.", DESCRICOES_PT["imageviewer"], DESCRICOES_ES["imageviewer"]),

        # Nintendo
        ("snes", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("snes", "sys_line2", "Super Nintendo", "Super Nintendo", "Super Nintendo"),
        ("sfc", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("sfc", "sys_line2", "Super Famicom", "Super Famicom", "Super Famicom"),
        ("snes-hacks", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("snes-hacks", "sys_line2", "SNES Hacks", "SNES Hacks", "SNES Hacks"),
        ("snesmsu1", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("snesmsu1", "sys_line2", "Super Nintendo CD", "Super Nintendo CD", "Super Nintendo CD"),
        ("nes", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("nes", "sys_line2", "NES", "Nintendo", "NES"),
        ("famicom", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("famicom", "sys_line2", "Famicom", "Famicom", "Famicom"),
        ("fds", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("fds", "sys_line2", "Disk System", "Disk System", "Disk System"),
        ("n64", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("n64", "sys_line2", "Nintendo 64", "Nintendo 64", "Nintendo 64"),
        ("n64dd", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("n64dd", "sys_line2", "Nintendo 64DD", "Nintendo 64DD", "Nintendo 64DD"),
        ("nds", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("nds", "sys_line2", "Nintendo DS", "Nintendo DS", "Nintendo DS"),
        ("gb", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("gb", "sys_line2", "Game Boy", "Game Boy", "Game Boy"),
        ("gbc", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("gbc", "sys_line2", "Game Boy Color", "Game Boy Color", "Game Boy Color"),
        ("gba", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("gba", "sys_line2", "Game Boy Advance", "Game Boy Advance", "Game Boy Advance"),
        ("sgb", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("sgb", "sys_line2", "Super Game Boy", "Super Game Boy", "Super Game Boy"),
        ("virtualboy", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("virtualboy", "sys_line2", "Virtual Boy", "Virtual Boy", "Virtual Boy"),
        ("gc", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("gc", "sys_line2", "GameCube", "GameCube", "GameCube"),
        ("wii", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("wii", "sys_line2", "Wii", "Wii", "Wii"),
        ("wiiu", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("wiiu", "sys_line2", "Wii U", "Wii U", "Wii U"),
        ("gameandwatch", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("gameandwatch", "sys_line2", "Game & Watch", "Game & Watch", "Game & Watch"),

        # Sony
        ("psx", "sys_line1", "Sony", "Sony", "Sony"),
        ("psx", "sys_line2", "PlayStation", "PlayStation", "PlayStation"),
        ("ps2", "sys_line1", "Sony", "Sony", "Sony"),
        ("ps2", "sys_line2", "PlayStation 2", "PlayStation 2", "PlayStation 2"),
        ("psp", "sys_line1", "Sony", "Sony", "Sony"),
        ("psp", "sys_line2", "PSP", "PSP", "PSP"),
        ("pspminis", "sys_line1", "Sony", "Sony", "Sony"),
        ("pspminis", "sys_line2", "PSP Minis", "PSP Minis", "PSP Minis"),

        # Sega
        ("megadrive", "sys_line1", "Sega", "Sega", "Sega"),
        ("megadrive", "sys_line2", "Mega Drive", "Mega Drive", "Mega Drive"),
        ("genesis", "sys_line1", "Sega", "Sega", "Sega"),
        ("genesis", "sys_line2", "Sega Genesis", "Sega Genesis", "Sega Genesis"),
        ("mastersystem", "sys_line1", "Sega", "Sega", "Sega"),
        ("mastersystem", "sys_line2", "Master System", "Master System", "Master System"),
        ("gamegear", "sys_line1", "Sega", "Sega", "Sega"),
        ("gamegear", "sys_line2", "Game Gear", "Game Gear", "Game Gear"),
        ("dreamcast", "sys_line1", "Sega", "Sega", "Sega"),
        ("dreamcast", "sys_line2", "Dreamcast", "Dreamcast", "Dreamcast"),
        ("saturn", "sys_line1", "Sega", "Sega", "Sega"),
        ("saturn", "sys_line2", "Sega Saturn", "Sega Saturn", "Sega Saturn"),
        ("segacd", "sys_line1", "Sega", "Sega", "Sega"),
        ("segacd", "sys_line2", "Sega CD", "Sega CD", "Sega CD"),
        ("megacd", "sys_line1", "Sega", "Sega", "Sega"),
        ("megacd", "sys_line2", "Mega-CD", "Mega-CD", "Mega-CD"),
        ("sega32x", "sys_line1", "Sega", "Sega", "Sega"),
        ("sega32x", "sys_line2", "Sega 32X", "Sega 32X", "Sega 32X"),
        ("mega32x", "sys_line1", "Sega", "Sega", "Sega"),
        ("mega32x", "sys_line2", "Mega 32X", "Mega 32X", "Mega 32X"),
        ("sg-1000", "sys_line1", "Sega", "Sega", "Sega"),
        ("sg-1000", "sys_line2", "SG-1000", "SG-1000", "SG-1000"),
        ("naomi", "sys_line1", "Sega", "Sega", "Sega"),
        ("naomi", "sys_line2", "NAOMI", "NAOMI", "NAOMI"),

        # Atari
        ("atari2600", "sys_line1", "Atari", "Atari", "Atari"),
        ("atari2600", "sys_line2", "Atari 2600", "Atari 2600", "Atari 2600"),
        ("atari5200", "sys_line1", "Atari", "Atari", "Atari"),
        ("atari5200", "sys_line2", "Atari 5200", "Atari 5200", "Atari 5200"),
        ("atari7800", "sys_line1", "Atari", "Atari", "Atari"),
        ("atari7800", "sys_line2", "Atari 7800", "Atari 7800", "Atari 7800"),
        ("atari800", "sys_line1", "Atari", "Atari", "Atari"),
        ("atari800", "sys_line2", "Atari 800", "Atari 800", "Atari 800"),
        ("atarijaguar", "sys_line1", "Atari", "Atari", "Atari"),
        ("atarijaguar", "sys_line2", "Atari Jaguar", "Atari Jaguar", "Atari Jaguar"),
        ("atarilynx", "sys_line1", "Atari", "Atari", "Atari"),
        ("atarilynx", "sys_line2", "Atari Lynx", "Atari Lynx", "Atari Lynx"),
        ("atarist", "sys_line1", "Atari", "Atari", "Atari"),
        ("atarist", "sys_line2", "Atari ST", "Atari ST", "Atari ST"),

        # Commodore
        ("c64", "sys_line1", "Commodore", "Commodore", "Commodore"),
        ("c64", "sys_line2", "Commodore 64", "Commodore 64", "Commodore 64"),
        ("c128", "sys_line1", "Commodore", "Commodore", "Commodore"),
        ("c128", "sys_line2", "Commodore 128", "Commodore 128", "Commodore 128"),
        ("c16", "sys_line1", "Commodore", "Commodore", "Commodore"),
        ("c16", "sys_line2", "Commodore 16", "Commodore 16", "Commodore 16"),
        ("vic20", "sys_line1", "Commodore", "Commodore", "Commodore"),
        ("vic20", "sys_line2", "VIC-20", "VIC-20", "VIC-20"),
        ("amiga", "sys_line1", "Commodore", "Commodore", "Commodore"),
        ("amiga", "sys_line2", "Amiga", "Amiga", "Amiga"),
        ("amigacd32", "sys_line1", "Commodore", "Commodore", "Commodore"),
        ("amigacd32", "sys_line2", "Amiga CD32", "Amiga CD32", "Amiga CD32"),

        # NEC
        ("tg16", "sys_line1", "NEC", "NEC", "NEC"),
        ("tg16", "sys_line2", "TurboGrafx-16", "TurboGrafx-16", "TurboGrafx-16"),
        ("turbographx", "sys_line1", "NEC", "NEC", "NEC"),
        ("turbographx", "sys_line2", "TurboGrafx-16", "TurboGrafx-16", "TurboGrafx-16"),
        ("tg-cd", "sys_line1", "NEC", "NEC", "NEC"),
        ("tg-cd", "sys_line2", "TurboGrafx-CD", "TurboGrafx-CD", "TurboGrafx-CD"),
        ("turbografxcd", "sys_line1", "NEC", "NEC", "NEC"),
        ("turbografxcd", "sys_line2", "TurboGrafx-CD", "TurboGrafx-CD", "TurboGrafx-CD"),
        ("pcengine", "sys_line1", "NEC", "NEC", "NEC"),
        ("pcengine", "sys_line2", "PC Engine", "PC Engine", "PC Engine"),
        ("pce-cd", "sys_line1", "NEC", "NEC", "NEC"),
        ("pce-cd", "sys_line2", "PC Engine CD", "PC Engine CD", "PC Engine CD"),
        ("pcenginecd", "sys_line1", "NEC", "NEC", "NEC"),
        ("pcenginecd", "sys_line2", "PC Engine CD", "PC Engine CD", "PC Engine CD"),
        ("supergrafx", "sys_line1", "NEC", "NEC", "NEC"),
        ("supergrafx", "sys_line2", "SuperGrafx", "SuperGrafx", "SuperGrafx"),
        ("pc98", "sys_line1", "NEC", "NEC", "NEC"),
        ("pc98", "sys_line2", "PC-98", "PC-98", "PC-98"),
        ("pcfx", "sys_line1", "NEC", "NEC", "NEC"),
        ("pcfx", "sys_line2", "PC-FX", "PC-FX", "PC-FX"),

        # SNK
        ("neogeo", "sys_line1", "SNK", "SNK", "SNK"),
        ("neogeo", "sys_line2", "Neo Geo", "Neo Geo", "Neo Geo"),
        ("neogeocd", "sys_line1", "SNK", "SNK", "SNK"),
        ("neogeocd", "sys_line2", "Neo Geo CD", "Neo Geo CD", "Neo Geo CD"),
        ("ngp", "sys_line1", "SNK", "SNK", "SNK"),
        ("ngp", "sys_line2", "Neo Geo Pocket", "Neo Geo Pocket", "Neo Geo Pocket"),
        ("ngpc", "sys_line1", "SNK", "SNK", "SNK"),
        ("ngpc", "sys_line2", "Neo Geo Pocket Color", "Neo Geo Pocket Color", "Neo Geo Pocket Color"),

        # Bandai
        ("wonderswan", "sys_line1", "Bandai", "Bandai", "Bandai"),
        ("wonderswan", "sys_line2", "WonderSwan", "WonderSwan", "WonderSwan"),
        ("wonderswancolor", "sys_line1", "Bandai", "Bandai", "Bandai"),
        ("wonderswancolor", "sys_line2", "WonderSwan Color", "WonderSwan Color", "WonderSwan Color"),

        # Coleco, Mattel, GCE, Panasonic
        ("colecovision", "sys_line1", "Coleco", "Coleco", "Coleco"),
        ("colecovision", "sys_line2", "ColecoVision", "ColecoVision", "ColecoVision"),
        ("coleco", "sys_line1", "Coleco", "Coleco", "Coleco"),
        ("coleco", "sys_line2", "ColecoVision", "ColecoVision", "ColecoVision"),
        ("intellivision", "sys_line1", "Mattel", "Mattel", "Mattel"),
        ("intellivision", "sys_line2", "Intellivision", "Intellivision", "Intellivision"),
        ("vectrex", "sys_line1", "GCE", "GCE", "GCE"),
        ("vectrex", "sys_line2", "Vectrex", "Vectrex", "Vectrex"),
        ("sys_3do", "sys_line1", "Panasonic", "Panasonic", "Panasonic"),
        ("sys_3do", "sys_line2", "3DO", "3DO", "3DO"),

        # Computers
        ("msx", "sys_line1", "Microsoft & ASCII", "Microsoft & ASCII", "Microsoft & ASCII"),
        ("msx", "sys_line2", "MSX", "MSX", "MSX"),
        ("msx2", "sys_line1", "Microsoft & ASCII", "Microsoft & ASCII", "Microsoft & ASCII"),
        ("msx2", "sys_line2", "MSX2", "MSX2", "MSX2"),
        ("amstradcpc", "sys_line1", "Amstrad", "Amstrad", "Amstrad"),
        ("amstradcpc", "sys_line2", "Amstrad CPC", "Amstrad CPC", "Amstrad CPC"),
        ("apple2", "sys_line1", "Apple", "Apple", "Apple"),
        ("apple2", "sys_line2", "Apple II", "Apple II", "Apple II"),
        ("x68000", "sys_line1", "Sharp", "Sharp", "Sharp"),
        ("x68000", "sys_line2", "X68000", "X68000", "X68000"),
        ("zxspectrum", "sys_line1", "Sinclair", "Sinclair", "Sinclair"),
        ("zxspectrum", "sys_line2", "ZX Spectrum", "ZX Spectrum", "ZX Spectrum"),
        ("zx81", "sys_line1", "Sinclair", "Sinclair", "Sinclair"),
        ("zx81", "sys_line2", "ZX81", "ZX81", "ZX81"),

        # Collections
        ("auto-allgames", "sys_line1", "Collection", "Coleção", "Colección"),
        ("auto-allgames", "sys_line2", "All Games", "Todos os Jogos", "Todos los Juegos"),
        ("auto-allgames", "nameLabel", "All Games", "Todos os Jogos", "Todos los Juegos"),

        ("auto-favorites", "sys_line1", "Collection", "Coleção", "Colección"),
        ("auto-favorites", "sys_line2", "Favorites", "Favoritos", "Favoritos"),
        ("auto-favorites", "nameLabel", "Favorites", "Favoritos", "Favoritos"),

        ("auto-lastplayed", "sys_line1", "Collection", "Coleção", "Colección"),
        ("auto-lastplayed", "sys_line2", "Recent Games", "Jogados Recentemente", "Jugados Recientemente"),
        ("auto-lastplayed", "nameLabel", "Last Played", "Jogados Recentemente", "Jugados Recientemente"),

        ("custom-collections", "sys_line1", "Collection", "Coleção", "Colección"),
        ("custom-collections", "sys_line2", "Custom Collections", "Coleções Personalizadas", "Colecciones Personalizadas"),
        ("custom-collections", "nameLabel", "Custom Collections", "Coleções Personalizadas", "Colecciones Personalizadas"),

        # Systems & Utilities
        ("power", "sys_line1", "System", "Sistema", "Sistema"),
        ("power", "sys_line2", "Power Options", "Opções de Energia", "Opciones de Energía"),
        ("power", "nameLabel", "Power", "Energia", "Energía"),

        ("retropie", "sys_line1", "System", "Sistema", "Sistema"),
        ("retropie", "sys_line2", "System Settings", "Ajustes do Sistema", "Ajustes del Sistema"),
        ("retropie", "nameLabel", "Settings", "Ajustes do Sistema", "Ajustes del Sistema"),

        ("retroarch", "sys_line1", "System", "Sistema", "Sistema"),
        ("retroarch", "sys_line2", "RetroArch", "RetroArch", "RetroArch"),
        ("retroarch", "nameLabel", "RetroArch", "RetroArch", "RetroArch"),

        ("ports", "sys_line1", "Ports", "Ports", "Ports"),
        ("ports", "sys_line2", "Native Games", "Jogos Nativos", "Juegos Nativos"),
        ("ports", "nameLabel", "Ports", "Ports", "Ports"),

        ("kodi", "sys_line1", "Media Center", "Central de Mídia", "Centro Multimedia"),
        ("kodi", "sys_line2", "Kodi", "Kodi", "Kodi"),
        ("kodi", "nameLabel", "Kodi", "Kodi", "Kodi"),

        ("pico-8", "sys_line1", "Fantasy Console", "Console Fantasia", "Consola Fantasía"),
        ("pico-8", "sys_line2", "PICO-8", "PICO-8", "PICO-8"),
        ("pico-8", "nameLabel", "PICO-8", "PICO-8", "PICO-8"),

        ("daphne", "sys_line1", "Laserdisc", "Laserdisc", "Laserdisc"),
        ("daphne", "sys_line2", "Daphne", "Daphne", "Daphne"),
        ("doom", "sys_line1", "id Software", "id Software", "id Software"),
        ("doom", "sys_line2", "Doom", "Doom", "Doom"),
        ("easyrpg", "sys_line1", "Engine", "Engine", "Motor"),
        ("easyrpg", "sys_line2", "EasyRPG", "EasyRPG", "EasyRPG"),
        ("coco", "sys_line1", "Tandy", "Tandy", "Tandy"),
        ("coco", "sys_line2", "TRS-80 CoCo", "TRS-80 CoCo", "TRS-80 CoCo"),

        # Arcade
        ("arcade", "sys_line1", "Arcade", "Arcade", "Arcade"),
        ("arcade", "sys_line2", "Arcade Classics", "Fliperama", "Recreativas"),
        ("mame", "sys_line1", "Arcade", "Arcade", "Arcade"),
        ("mame", "sys_line2", "MAME", "MAME", "MAME"),
        ("fba", "sys_line1", "Arcade", "Arcade", "Arcade"),
        ("fba", "sys_line2", "FinalBurn Alpha", "FinalBurn Alpha", "FinalBurn Alpha"),
        ("fbn", "sys_line1", "Arcade", "Arcade", "Arcade"),
        ("fbn", "sys_line2", "FinalBurn Neo", "FinalBurn Neo", "FinalBurn Neo"),
        ("fbneo", "sys_line1", "Arcade", "Arcade", "Arcade"),
        ("fbneo", "sys_line2", "FinalBurn Neo", "FinalBurn Neo", "FinalBurn Neo"),
        ("fbneo_fbneo", "sys_line1", "Arcade", "Arcade", "Arcade"),
        ("fbneo_fbneo", "sys_line2", "FinalBurn Neo", "FinalBurn Neo", "FinalBurn Neo"),
        ("cps1", "sys_line1", "Capcom", "Capcom", "Capcom"),
        ("cps1", "sys_line2", "CPS-1", "CPS-1", "CPS-1"),
        ("cps2", "sys_line1", "Capcom", "Capcom", "Capcom"),
        ("cps2", "sys_line2", "CPS-2", "CPS-2", "CPS-2"),
        ("cps3", "sys_line1", "Capcom", "Capcom", "Capcom"),
        ("cps3", "sys_line2", "CPS-3", "CPS-3", "CPS-3"),
        ("atomiswave", "sys_line1", "Sammy", "Sammy", "Sammy"),
        ("atomiswave", "sys_line2", "Atomiswave", "Atomiswave", "Atomiswave"),
        ("pc98", "sys_line2", "PC-98", "PC-98", "PC-98"),
        ("residualvm", "sys_line1", "3D Adventure", "Engine 3D", "Motor 3D"),
        ("residualvm", "sys_line2", "ResidualVM", "ResidualVM", "ResidualVM"),
        ("scummvm", "sys_line1", "Adventure Engine", "Engine de Aventura", "Motor de Aventura"),
        ("scummvm", "sys_line2", "ScummVM", "ScummVM", "ScummVM"),
        ("solarus", "sys_line1", "Engine", "Engine", "Motor"),
        ("solarus", "sys_line2", "Solarus", "Solarus", "Solarus"),
        ("tic80", "sys_line1", "Fantasy Computer", "Computador Fantasia", "Computadora Fantasía"),
        ("tic80", "sys_line2", "TIC-80", "TIC-80", "TIC-80"),
        ("vectrex", "sys_line1", "GCE", "GCE", "GCE"),
        ("vectrex", "sys_line2", "Vectrex", "Vectrex", "Vectrex"),
        ("virtualboy", "sys_line1", "Nintendo", "Nintendo", "Nintendo"),
        ("virtualboy", "sys_line2", "Virtual Boy", "Virtual Boy", "Virtual Boy"),
        ("wonderswan", "sys_line1", "Bandai", "Bandai", "Bandai"),
        ("wonderswan", "sys_line2", "WonderSwan", "WonderSwan", "WonderSwan"),
        ("x68000", "sys_line1", "Sharp", "Sharp", "Sharp"),
        ("x68000", "sys_line2", "X68000", "X68000", "X68000"),
        ("zx81", "sys_line1", "Sinclair", "Sinclair", "Sinclair"),
        ("zx81", "sys_line2", "ZX81", "ZX81", "ZX81"),

        # Collections
        ("auto-allgames", "sys_line1", "Collection", "Coleção", "Colección"),
        ("auto-allgames", "sys_line2", "All Games", "Todos os Jogos", "Todos los Juegos"),
        ("auto-allgames", "nameLabel", "All Games", "Todos os Jogos", "Todos los Juegos"),

        ("auto-favorites", "sys_line1", "Collection", "Coleção", "Colección"),
        ("auto-favorites", "sys_line2", "Favorites", "Favoritos", "Favoritos"),
        ("auto-favorites", "nameLabel", "Favorites", "Favoritos", "Favoritos"),

        ("auto-lastplayed", "sys_line1", "Collection", "Coleção", "Colección"),
        ("auto-lastplayed", "sys_line2", "Recent Games", "Jogados Recentemente", "Jugados Recientemente"),
        ("auto-lastplayed", "nameLabel", "Last Played", "Jogados Recentemente", "Jugados Recientemente"),

        ("custom-collections", "sys_line1", "Collection", "Coleção", "Colección"),
        ("custom-collections", "sys_line2", "Custom Collections", "Coleções Personalizadas", "Colecciones Personalizadas"),
        ("custom-collections", "nameLabel", "Custom Collections", "Coleções Personalizadas", "Colecciones Personalizadas"),

        # Systems & Utilities
        ("power", "sys_line1", "System", "Sistema", "Sistema"),
        ("power", "sys_line2", "Power Options", "Opções de Energia", "Opciones de Energía"),
        ("power", "nameLabel", "Power", "Energia", "Energía"),

        ("retropie", "sys_line1", "System", "Sistema", "Sistema"),
        ("retropie", "sys_line2", "System Settings", "Ajustes do Sistema", "Ajustes del Sistema"),
        ("retropie", "nameLabel", "Settings", "Ajustes do Sistema", "Ajustes del Sistema"),

        ("retroarch", "sys_line1", "System", "Sistema", "Sistema"),
        ("retroarch", "sys_line2", "RetroArch", "RetroArch", "RetroArch"),
        ("retroarch", "nameLabel", "RetroArch", "RetroArch", "RetroArch"),

        ("ports", "sys_line1", "Ports", "Ports", "Ports"),
        ("ports", "sys_line2", "Native Games", "Jogos Nativos", "Juegos Nativos"),
        ("ports", "nameLabel", "Ports", "Ports", "Ports"),

        ("kodi", "sys_line1", "Media Center", "Central de Mídia", "Centro Multimedia"),
        ("kodi", "sys_line2", "Kodi", "Kodi", "Kodi"),
        ("kodi", "nameLabel", "Kodi", "Kodi", "Kodi"),

        ("pico-8", "sys_line1", "Fantasy Console", "Console Fantasia", "Consola Fantasía"),
        ("pico-8", "sys_line2", "PICO-8", "PICO-8", "PICO-8"),
        ("pico-8", "nameLabel", "PICO-8", "PICO-8", "PICO-8"),

        ("daphne", "sys_line1", "Laserdisc", "Laserdisc", "Laserdisc"),
        ("daphne", "sys_line2", "Daphne", "Daphne", "Daphne"),
        ("doom", "sys_line1", "id Software", "id Software", "id Software"),
        ("doom", "sys_line2", "Doom", "Doom", "Doom"),
        ("easyrpg", "sys_line1", "Engine", "Engine", "Motor"),
        ("easyrpg", "sys_line2", "EasyRPG", "EasyRPG", "EasyRPG"),
    ]

    # Gêneros
    genres = [
        ("action", "Action", "Ação", "Acción"),
        ("adventure", "Adventure", "Aventura", "Aventura"),
        ("btmups", "Beat 'em Up", "Beat 'em Up", "Beat 'em Up"),
        ("fighting", "Fighting", "Luta", "Lucha"),
        ("fixedscreen", "Fixed Screen", "Tela Fixa", "Pantalla Fija"),
        ("kids", "Kids", "Infantil", "Infantil"),
        ("platformers", "Platform", "Plataforma", "Plataformas"),
        ("puzzle", "Puzzle", "Puzzle", "Puzzle"),
        ("racing", "Racing", "Corrida", "Carreras"),
        ("rpgs", "RPGs", "RPGs", "RPGs"),
        ("shmups", "Shmups", "Shmups", "Shmups"),
        ("sports", "Sports", "Esportes", "Deportes"),
        ("strategy", "Strategy", "Estratégia", "Estrategia"),
    ]

    for g, g_en, g_pt, g_es in genres:
        curations.append((g, "sys_line1", "Genre", "Gênero", "Género"))
        curations.append((g, "sys_line2", g_en, g_pt, g_es))
        curations.append((g, "nameLabel", f"Genre {g_en}", f"Gênero {g_pt}", f"Género {g_es}"))

    # Traduz shortdescription e longdescription
    for k, val in en_vars.items():
        if k.endswith(".shortdescription"):
            pt_vars[k] = traduz_shortdescription(val, "pt-br")
            es_vars[k] = traduz_shortdescription(val, "es-latam")
        elif k.endswith(".longdescription"):
            sys_key = k.rsplit(".longdescription", 1)[0]
            if sys_key in DESCRICOES_PT:
                pt_vars[k] = DESCRICOES_PT[sys_key]
            if sys_key in DESCRICOES_ES:
                es_vars[k] = DESCRICOES_ES[sys_key]

    # Aplica curadorias explícitas por cima
    for s, field, v_en, v_pt, v_es in curations:
        prefix = normaliza_var_prefix(s)
        k = f"{prefix}.{field}"
        en_vars[k] = v_en
        pt_vars[k] = v_pt
        es_vars[k] = v_es

    return pt_vars, es_vars

def executa_refatoracao(tar_path: Path, dest_dir: Path):
    """Executa o processo de extração e desacoplamento do tema upstream."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    lang_dir = dest_dir / "_languages"
    lang_dir.mkdir(parents=True, exist_ok=True)
    var_art_dir = dest_dir / "_art" / "var"
    var_art_dir.mkdir(parents=True, exist_ok=True)

    # Gera botões de ação SVG localizados
    svg_btn = gera_svg_botao_entrar()
    (var_art_dir / "button.svg").write_text(svg_btn, encoding="utf-8")
    (var_art_dir / "button-pt.svg").write_text(svg_btn, encoding="utf-8")
    (var_art_dir / "button-es.svg").write_text(svg_btn, encoding="utf-8")

    root_theme, systems_data = extrai_textos_do_tarball(tar_path)

    en_vars = {
        "languageSubsetName": "Theme Language",
        "controllerSubsetName": "Show controllers in system view",
        "on": "On",
        "off": "Off",
    }

    for sys_name, (root_elem, fields) in systems_data.items():
        prefix = normaliza_var_prefix(sys_name)
        for field_name, field_val in fields:
            var_name = f"{prefix}.{field_name}"
            en_vars[var_name] = field_val

        refat_xml = refatora_console_tree(root_elem, sys_name)
        sys_dir = dest_dir / sys_name
        sys_dir.mkdir(parents=True, exist_ok=True)
        (sys_dir / "theme.xml").write_text(refat_xml, encoding="utf-8")

    # Gera os 3 catálogos
    pt_vars, es_vars = monta_catalogos(en_vars)

    en_xml_content = gera_catalogo_xml(en_vars)
    (lang_dir / "en.xml").write_text(en_xml_content, encoding="utf-8")

    pt_xml_content = gera_catalogo_xml(pt_vars)
    (lang_dir / "pt-br.xml").write_text(pt_xml_content, encoding="utf-8")

    es_xml_content = gera_catalogo_xml(es_vars)
    (lang_dir / "es-latam.xml").write_text(es_xml_content, encoding="utf-8")

    if root_theme:
        refat_root = refatora_raiz_theme_xml(root_theme)
        (dest_dir / "theme.xml").write_text(refat_root, encoding="utf-8")

    return en_vars, pt_vars, es_vars

def main():
    parser = argparse.ArgumentParser(description="Refatora tema Epic Cody para Multi-Language")
    parser.add_argument(
        "--tarball",
        type=Path,
        default=Path("work/cache/external/4a0d1e11850e0a1f0ae54ba3f4c067aefa44751e6fa7996a799493308dbe5d55.tar.gz"),
        help="Caminho do tarball upstream do Epic Cody"
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path("features/50-temas-extras/storage/.config/emulationstation/themes/Epic Cody ML"),
        help="Diretório de destino da árvore refatorada do tema"
    )
    args = parser.parse_args()

    if not args.tarball.is_file():
        print(f"Erro: Tarball {args.tarball} não encontrado.", file=sys.stderr)
        sys.exit(1)

    print(f"Lendo tarball upstream: {args.tarball}")
    en_vars, pt_vars, es_vars = executa_refatoracao(args.tarball, args.dest)
    print(f"Catálogos gerados com sucesso:")
    print(f"  en.xml: {len(en_vars)} variáveis")
    print(f"  pt-br.xml: {len(pt_vars)} variáveis")
    print(f"  es-latam.xml: {len(es_vars)} variáveis")
    print(f"Refatoração concluída com sucesso em: {args.dest}")

if __name__ == "__main__":
    main()
