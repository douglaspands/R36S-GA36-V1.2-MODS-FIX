#!/usr/bin/env python3
"""Utilitário de extração e refatoração do tema Epic Cody para Epic Cody ML (Multi-Language).

Desacopla os textos estáticos dos nós <text> dos arquivos theme.xml de cada console/coleção
em variáveis centralizadas por idioma (_languages/en.xml, pt-br.xml, es-latam.xml) e insere
o seletor <subset name="language"> no theme.xml raiz.
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
    """Substitui o conteúdo de cada nó <text> pelo placeholder ${sistema.campo}."""
    prefix = normaliza_var_prefix(sys_name)
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
    """Atualiza o theme.xml raiz adicionando o subset de idiomas se ainda não existir."""
    if '<subset name="language"' in content:
        return content

    subset_xml = """\t<subset name="language" displayName="${languageSubsetName}">
        <include name="pt-br" displayName="Português (Brasil)">./_languages/pt-br.xml</include>
        <include name="es-latam" displayName="Español (Latino)">./_languages/es-latam.xml</include>
        <include name="en" displayName="English">./_languages/en.xml</include>
    </subset>\n\n"""

    pattern = r'(\s*<subset name="controller")'
    match = re.search(pattern, content)
    if match:
        idx = match.start(1)
        return content[:idx] + "\n" + subset_xml + content[idx:]
    else:
        idx = content.find('<view name="system">')
        if idx != -1:
            return content[:idx] + subset_xml + content[idx:]
        return content + "\n" + subset_xml

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
    """Gera os dicionários completos de variáveis para pt-br e es-latam."""
    pt_vars = dict(en_vars)
    es_vars = dict(en_vars)

    # Metadados de controle e menu
    pt_vars["languageSubsetName"] = "Idioma do Tema"
    pt_vars["controllerSubsetName"] = "Mostrar controles no sistema"
    pt_vars["on"] = "Ligado"
    pt_vars["off"] = "Desligado"

    es_vars["languageSubsetName"] = "Idioma del tema"
    es_vars["controllerSubsetName"] = "Mostrar mandos en sistema"
    es_vars["on"] = "Activado"
    es_vars["off"] = "Desactivado"

    # Gêneros
    genres_pt = {
        "action": ("Ação", "Ação"),
        "adventure": ("Aventura", "Aventura"),
        "btmups": ("Beat 'em Ups", "Beat 'em Ups"),
        "fighting": ("Luta", "Luta"),
        "fixedscreen": ("Tela Fixa", "Tela Fixa"),
        "kids": ("Infantil", "Infantil"),
        "platformers": ("Plataforma", "Plataforma"),
        "puzzle": ("Puzzle", "Puzzle"),
        "racing": ("Corrida", "Corrida"),
        "rpgs": ("RPGs", "RPGs"),
        "shmups": ("Shmups", "Shmups"),
        "sports": ("Esportes", "Esportes"),
        "strategy": ("Estratégia", "Estratégia"),
    }

    genres_es = {
        "action": ("Acción", "Acción"),
        "adventure": ("Aventura", "Aventura"),
        "btmups": ("Beat 'em Ups", "Beat 'em Ups"),
        "fighting": ("Lucha", "Lucha"),
        "fixedscreen": ("Pantalla fija", "Pantalla fija"),
        "kids": ("Infantil", "Infantil"),
        "platformers": ("Plataformas", "Plataformas"),
        "puzzle": ("Puzzle", "Puzzle"),
        "racing": ("Carreras", "Carreras"),
        "rpgs": ("RPGs", "RPGs"),
        "shmups": ("Shmups", "Shmups"),
        "sports": ("Deportes", "Deportes"),
        "strategy": ("Estrategia", "Estrategia"),
    }

    for g, (nl, s2) in genres_pt.items():
        pt_vars[f"{g}.nameLabel"] = f"Gênero {nl}" if g not in ("rpgs", "shmups", "btmups", "puzzle") else nl
        pt_vars[f"{g}.sys_line2"] = s2

    for g, (nl, s2) in genres_es.items():
        es_vars[f"{g}.nameLabel"] = f"Género {nl}" if g not in ("rpgs", "shmups", "btmups", "puzzle") else nl
        es_vars[f"{g}.sys_line2"] = s2

    # Coleções e utilitários
    def set_if_exists(dict_vars, key, val):
        if key in en_vars:
            dict_vars[key] = val

    set_if_exists(pt_vars, "auto-allgames.nameLabel", "Todos os Jogos")
    set_if_exists(pt_vars, "auto-allgames.sys_line1", "COLEÇÃO")
    set_if_exists(pt_vars, "auto-allgames.sys_line2", "Todos os Jogos")
    set_if_exists(es_vars, "auto-allgames.nameLabel", "Todos los juegos")
    set_if_exists(es_vars, "auto-allgames.sys_line1", "COLECCIÓN")
    set_if_exists(es_vars, "auto-allgames.sys_line2", "Todos los juegos")

    set_if_exists(pt_vars, "auto-favorites.nameLabel", "Favoritos")
    set_if_exists(pt_vars, "auto-favorites.sys_line1", "COLEÇÃO")
    set_if_exists(pt_vars, "auto-favorites.sys_line2", "Favoritos")
    set_if_exists(es_vars, "auto-favorites.nameLabel", "Favoritos")
    set_if_exists(es_vars, "auto-favorites.sys_line1", "COLECCIÓN")
    set_if_exists(es_vars, "auto-favorites.sys_line2", "Favoritos")

    set_if_exists(pt_vars, "auto-lastplayed.nameLabel", "Jogados Recentemente")
    set_if_exists(pt_vars, "auto-lastplayed.sys_line1", "COLEÇÃO")
    set_if_exists(pt_vars, "auto-lastplayed.sys_line2", "Recentes")
    set_if_exists(es_vars, "auto-lastplayed.nameLabel", "Jugados recientemente")
    set_if_exists(es_vars, "auto-lastplayed.sys_line1", "COLECCIÓN")
    set_if_exists(es_vars, "auto-lastplayed.sys_line2", "Recientes")

    set_if_exists(pt_vars, "custom-collections.nameLabel", "Coleções Personalizadas")
    set_if_exists(pt_vars, "custom-collections.sys_line1", "COLEÇÃO")
    set_if_exists(pt_vars, "custom-collections.sys_line2", "Coleções")
    set_if_exists(es_vars, "custom-collections.nameLabel", "Colecciones personalizadas")
    set_if_exists(es_vars, "custom-collections.sys_line1", "COLECCIÓN")
    set_if_exists(es_vars, "custom-collections.sys_line2", "Colecciones")

    set_if_exists(pt_vars, "power.nameLabel", "Energia")
    set_if_exists(pt_vars, "power.sys_line2", "Energia")
    set_if_exists(es_vars, "power.nameLabel", "Energía")
    set_if_exists(es_vars, "power.sys_line2", "Energía")

    set_if_exists(pt_vars, "retropie.nameLabel", "Opções")
    set_if_exists(pt_vars, "retropie.sys_line2", "Opções")
    set_if_exists(es_vars, "retropie.nameLabel", "Opciones")
    set_if_exists(es_vars, "retropie.sys_line2", "Opciones")

    set_if_exists(pt_vars, "ports.nameLabel", "Ports")
    set_if_exists(pt_vars, "ports.sys_line2", "Ports")
    set_if_exists(es_vars, "ports.nameLabel", "Ports")
    set_if_exists(es_vars, "ports.sys_line2", "Ports")

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

    return pt_vars, es_vars

def executa_refatoracao(tar_path: Path, dest_dir: Path):
    """Executa o processo de extração e desacoplamento do tema upstream."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    lang_dir = dest_dir / "_languages"
    lang_dir.mkdir(parents=True, exist_ok=True)

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
