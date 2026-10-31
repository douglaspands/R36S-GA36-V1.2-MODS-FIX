#!/usr/bin/env python3
"""Gera capturas de tela e mockups da interface em alta fidelidade para avaliação."""

import tarfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(".")
VAR = ROOT / "var"
OUTPUT_DIR = VAR / "prints-calibracao-cody"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. Carrega fontes do tarball upstream
tar_path = ROOT / "work" / "cache" / "external" / "4a0d1e11850e0a1f0ae54ba3f4c067aefa44751e6fa7996a799493308dbe5d55.tar.gz"
font_dir = ROOT / "scratch" / "fonts"
font_dir.mkdir(parents=True, exist_ok=True)

with tarfile.open(tar_path, "r:gz") as tar:
    for m in tar.getmembers():
        if m.name.endswith("Acre.otf") or m.name.endswith("BebasNeue.otf"):
            tar.extract(m, font_dir)

bebas_p = list(font_dir.rglob("BebasNeue.otf"))[0]
acre_p = list(font_dir.rglob("Acre.otf"))[0]

# Instâncias de fontes em escalas normalizadas (640x480)
font_bebas_header = ImageFont.truetype(str(bebas_p), 24)       # fontSize 0.050 (~24px)
font_bebas_title = ImageFont.truetype(str(bebas_p), 22)        # fontSize 0.045 (~22px)
font_bebas_card = ImageFont.truetype(str(bebas_p), 18)         # card header
font_bebas_hero = ImageFont.truetype(str(bebas_p), 60)         # sys_line2 (~60px)
font_acre_list = ImageFont.truetype(str(acre_p), 14)           # fontSize 0.030 (~14px)
font_acre_help = ImageFont.truetype(str(acre_p), 11)           # fontSize 0.022 (~11px)
font_acre_card = ImageFont.truetype(str(acre_p), 10)           # fontSize 0.028 (~10px compact)
font_acre_desc = ImageFont.truetype(str(acre_p), 12)           # descrições

# Paleta oficial do Design System
C_BG = (0, 0, 0, 255)
C_SURFACE = (28, 28, 28, 255)       # #1C1C1C
C_BORDER = (51, 51, 51, 255)        # #333333
C_INACTIVE = (88, 88, 88, 255)      # #585858
C_MUTED = (136, 136, 136, 255)      # #888888
C_LEGEND = (160, 160, 160, 255)     # #A0A0A0
C_WHITE = (255, 255, 255, 255)      # #FFFFFF
C_HEADER = (248, 248, 248, 255)     # #F8F8F8
C_AMBER = (255, 174, 0, 255)        # #FFAE00

# Base canvas
bg_path = ROOT / "features" / "50-temas-extras" / "storage" / ".config" / "emulationstation" / "themes" / "Epic Cody ML" / "_art" / "ingame-global-bg.png"
base_bg = Image.open(bg_path).convert("RGBA")

def desenha_helpsystem(draw, x_start=16, y=462, prompts=None):
    if prompts is None:
        prompts = [
            ("A", "ENTRAR"),
            ("B", "VOLTAR"),
            ("X", "FAVORITO"),
            ("SELECT", "OPÇÕES"),
        ]
    x = x_start
    for btn, label in prompts:
        btn_txt = f"({btn})"
        draw.text((x, y), btn_txt, font=font_acre_help, fill=C_AMBER)
        bbox = draw.textbbox((x, y), btn_txt, font=font_acre_help)
        x = bbox[2] + 4
        draw.text((x, y), label, font=font_acre_help, fill=C_LEGEND)
        bbox2 = draw.textbbox((x, y), label, font=font_acre_help)
        x = bbox2[2] + 14

def desenha_bateria_relogio(draw):
    # Relógio 09:45
    draw.text((586, 16), "09:45", font=font_acre_help, fill=C_WHITE)
    # Bateria em 550, 18
    draw.rectangle([556, 18, 574, 28], outline=(255, 255, 255, 160), width=1)
    draw.rectangle([574, 20, 576, 26], fill=(255, 255, 255, 160))
    draw.rectangle([558, 20, 570, 26], fill=C_AMBER)  # 75%

def renderiza_gamelist(system_name, display_title, jogos, jogo_selecionado_idx, preview_img, game_title):
    im = base_bg.copy()
    draw = ImageDraw.Draw(im)

    # 1. Cabeçalho
    draw.text((16, 14), "JOGOS", font=font_bebas_header, fill=C_HEADER)
    draw.text((217, 14), display_title.upper(), font=font_bebas_header, fill=C_AMBER)
    desenha_bateria_relogio(draw)

    # 2. Lista de Jogos (textlist gamelist: pos 0 0.12, size 0.319 0.805 -> y=58..444)
    # horizontalMargin = 0.025 (x = 16.0px) alinhado perfeitamente com GAMES na régua
    y_start = 58
    row_height = 29.69
    for i, nome in enumerate(jogos[:13]):
        y_row = int(y_start + i * row_height)
        if i == jogo_selecionado_idx:
            # Selector bar
            draw.rectangle([0, y_row, 206, y_row + 28], fill=C_SURFACE)
            draw.text((16, y_row + 6), nome, font=font_acre_list, fill=C_AMBER)
        else:
            draw.text((16, y_row + 6), nome, font=font_acre_list, fill=C_INACTIVE)

    # 3. Preview de Mídia na Coluna Direita (pos 0.66 0.485, maxSize 0.62 0.70)
    # Caixa útil: centro (422, 233), max 396 x 336
    if preview_img:
        pw, ph = preview_img.size
        scale = min(396 / pw, 336 / ph)
        new_w, new_h = int(pw * scale), int(ph * scale)
        p_resized = preview_img.resize((new_w, new_h), Image.LANCZOS)
        px = 422 - new_w // 2
        py = 233 - new_h // 2
        # Sombra sutil
        im.paste((10, 10, 10, 200), [px - 2, py - 2, px + new_w + 2, py + new_h + 2])
        im.paste(p_resized, (px, py))

    # 4. Título do Jogo (md_name: pos 0.339 0.865 -> x=217, y=415, cor branca #FFFFFF)
    draw.text((217, 415), game_title.upper(), font=font_bebas_title, fill=C_WHITE)

    # 5. Helpsystem alinhado à esquerda em x=16px na altura exata do menu de jogos (y=450)
    desenha_helpsystem(draw, x_start=16, y=450)

    return im

def renderiza_modal_savestate(bg_base_img, slot_thumbnails):
    # Base escurecida com overlay modal
    im = bg_base_img.copy()
    overlay = Image.new("RGBA", (640, 480), (0, 0, 0, 175))
    im = Image.alpha_composite(im, overlay)
    draw = ImageDraw.Draw(im)

    # Janela Modal: 608px largura (x=16..624, 95%), 432px altura (y=24..456)
    modal_box = [16, 24, 624, 456]
    draw.rectangle(modal_box, fill=(24, 24, 24, 255), outline=C_BORDER, width=2)

    # Linha amarela no topo do modal
    draw.line([16, 24, 624, 24], fill=C_AMBER, width=2)

    # Cabeçalho do Modal: x=32px, y=36 (título do jogo com fonte calibrada e subtítulo)
    draw.text((32, 32), "SUPER MARIO WORLD", font=font_bebas_title, fill=C_AMBER)
    draw.text((32, 52), "GERENCIADOR DE SAVE STATES (SLOTS)", font=font_acre_help, fill=C_MUTED)
    draw.line([32, 68, 608, 68], fill=(45, 45, 45, 255), width=1)

    # Grid de 3 cards: x=32..608 (576px úteis / 3 = 192px cada, cards de 180px com 18px de espaçamento)
    card_w = 178
    card_h = 330
    card_y = 76

    slots_info = [
        ("SLOT 1", "2026-10-31 02:45", slot_thumbnails[0] if len(slot_thumbnails) > 0 else None, True),
        ("SLOT 2", "2026-10-31 01:12", slot_thumbnails[1] if len(slot_thumbnails) > 1 else None, False),
        ("SLOT 3", "[ VAZIO ]", None, False),
    ]

    for idx, (slot_name, timestamp, thumb, selected) in enumerate(slots_info):
        cx = 32 + idx * (card_w + 17)
        c_box = [cx, card_y, cx + card_w, card_y + card_h]

        if selected:
            draw.rectangle(c_box, fill=(34, 34, 34, 255), outline=C_AMBER, width=2)
            title_color = C_AMBER
        else:
            draw.rectangle(c_box, fill=(28, 28, 28, 255), outline=C_BORDER, width=1)
            title_color = C_WHITE if thumb else C_INACTIVE

        # Título do Card
        draw.text((cx + 16, card_y + 12), slot_name, font=font_bebas_card, fill=title_color)

        # Thumbnail (152x114, 4:3)
        tx = cx + (card_w - 152) // 2
        ty = card_y + 40
        t_box = [tx, ty, tx + 152, ty + 114]

        if thumb:
            th_resized = thumb.resize((152, 114), Image.LANCZOS)
            im.paste(th_resized, (tx, ty))
            draw.rectangle(t_box, outline=(60, 60, 60, 255), width=1)
        else:
            draw.rectangle(t_box, fill=(18, 18, 18, 255), outline=(45, 45, 45, 255), width=1)
            draw.text((tx + 46, ty + 50), "[ VAZIO ]", font=font_acre_card, fill=C_INACTIVE)

        # Rótulo de Data e Hora compacto (fontSize 0.028)
        time_color = C_MUTED if thumb else C_INACTIVE
        draw.text((cx + 20, ty + 124), "DATA / HORA:", font=font_acre_card, fill=C_INACTIVE)
        draw.text((cx + 20, ty + 140), timestamp, font=font_acre_card, fill=time_color)

    # Linha divisória antes do rodapé
    draw.line([32, 420, 608, 420], fill=(45, 45, 45, 255), width=1)

    # Barra de atalhos alinhada à esquerda em x=32px
    modal_prompts = [
        ("A", "CARREGAR"),
        ("X", "NOVO SAVE"),
        ("Y", "APAGAR"),
        ("B", "CANCELAR"),
    ]
    desenha_helpsystem(draw, x_start=32, y=430, prompts=modal_prompts)

    return im

def renderiza_system_view(sys_name, line1, line2, shortdesc, longdesc, controller_img, poster_img):
    im = Image.new("RGBA", (640, 480), (10, 10, 10, 255))

    # Poster à direita (y=0..480, x=320..640) com fade gradiente para a esquerda
    if poster_img:
        pw, ph = poster_img.size
        poster_scaled = poster_img.resize((320, 480), Image.LANCZOS)
        im.paste(poster_scaled, (320, 0))
        # Gradiente suave
        grad = Image.new("L", (180, 480))
        for gx in range(180):
            alpha = int(255 * (1.0 - (gx / 180)))
            for gy in range(480):
                grad.putpixel((gx, gy), alpha)
        fade_layer = Image.new("RGBA", (180, 480), (10, 10, 10, 255))
        fade_layer.putalpha(grad)
        im.paste(fade_layer, (320, 0), fade_layer)

    draw = ImageDraw.Draw(im)

    # 1. shortdescription (pos 0.025 0.080 -> x=16, y=38)
    draw.text((16, 38), shortdesc, font=font_acre_help, fill=C_WHITE)

    # 2. sys_line1 (pos 0.025 0.115 -> x=16, y=55)
    draw.text((16, 55), line1.upper(), font=font_bebas_title, fill=C_WHITE)

    # 3. sys_line2 (pos 0.025 0.160 -> x=16, y=77)
    draw.text((16, 77), line2.upper(), font=font_bebas_hero, fill=C_WHITE)

    # 4. Botão (A) ENTRAR (pos 0.025 0.460 -> x=16, y=221)
    btn_box = [16, 221, 140, 256]
    draw.rounded_rectangle(btn_box, radius=17, fill=C_AMBER)
    draw.text((32, 228), "(A) ENTRAR", font=font_acre_list, fill=C_BG)

    # 5. systemInfo (pos 0.025 0.570 -> x=16, y=274)
    draw.text((16, 274), "788 JOGOS DISPONÍVEIS", font=font_bebas_title, fill=C_AMBER)

    # 6. longdescription (pos 0.025 0.660 -> x=16, y=317, width ~192px)
    import textwrap
    linhas = textwrap.wrap(longdesc, width=32)
    for idx, l in enumerate(linhas[:5]):
        draw.text((16, 317 + idx * 16), l, font=font_acre_help, fill=(220, 220, 220, 255))

    # 7. Controle do Console (pos 0.35 0.62 -> x=224, y=298)
    if controller_img:
        cw, ch = controller_img.size
        c_scale = min(179 / cw, 134 / ch)
        c_resized = controller_img.resize((int(cw * c_scale), int(ch * c_scale)), Image.LANCZOS)
        im.paste(c_resized, (224, 298), c_resized if c_resized.mode == "RGBA" else None)

    # 8. Helpsystem (pos 0.025 0.965 -> x=16, y=463)
    sys_prompts = [
        ("A", "ENTRAR"),
        ("B", "VOLTAR"),
        ("START", "MENU"),
    ]
    desenha_helpsystem(draw, x_start=16, y=463, prompts=sys_prompts)

    return im

def main():
    print("Gerando prints das interfaces calibradas...")

    # Imagens de jogos reais de exemplo
    shot_mario = Image.open("var/exemplos-cor/mario-kart_3-novo.png").convert("RGBA")
    shot_sonic = Image.open("var/exemplos-tv/sonic1-f600-calibrado.png").convert("RGBA")
    shot_zelda = Image.open("var/exemplos-gb-gbc/gbc_zelda-dx-f1500_comparacao.png").convert("RGBA")

    # Extrai poster e controller do SNES do tarball
    snes_poster = None
    snes_controller = None
    with tarfile.open(tar_path, "r:gz") as tar:
        for m in tar.getmembers():
            if m.name.endswith("posters/snes.jpg"):
                snes_poster = Image.open(tar.extractfile(m)).convert("RGBA")
            elif m.name.endswith("controllers/snes.png"):
                snes_controller = Image.open(tar.extractfile(m)).convert("RGBA")

    # 1. Gamelist SNES
    jogos_snes = [
        "Super Mario World",
        "Super Mario Kart",
        "The Legend of Zelda: A Link to the Past",
        "Super Metroid",
        "Chrono Trigger",
        "Donkey Kong Country",
        "Street Fighter II Turbo",
        "Mega Man X",
        "Super Castlevania IV",
        "F-Zero",
        "Star Fox",
        "Final Fantasy VI",
        "Super Mario RPG",
    ]
    im_snes = renderiza_gamelist(
        "snes", "Super Nintendo", jogos_snes, 0, shot_mario, "SUPER MARIO WORLD"
    )
    im_snes.save(OUTPUT_DIR / "01_gamelist_snes.png")
    im_snes.save(VAR / "preview_snes_gamelist_pt.png")

    # 2. Gamelist Mega Drive
    jogos_md = [
        "Sonic the Hedgehog",
        "Sonic the Hedgehog 2",
        "Streets of Rage 2",
        "Golden Axe",
        "Shinobi III",
        "Castle of Illusion",
        "Aladdin",
        "Comix Zone",
        "Gunstar Heroes",
        "Ristar",
        "Phantasy Star IV",
        "OutRun",
        "Earthworm Jim",
    ]
    im_md = renderiza_gamelist(
        "megadrive", "Sega Mega Drive", jogos_md, 0, shot_sonic, "SONIC THE HEDGEHOG"
    )
    im_md.save(OUTPUT_DIR / "02_gamelist_megadrive.png")
    im_md.save(VAR / "preview_megadrive_gamelist_pt.png")

    # 3. Gamelist GBA
    jogos_gba = [
        "Mario Kart: Super Circuit",
        "The Legend of Zelda: Minish Cap",
        "Metroid Fusion",
        "Pokemon Emerald",
        "Castlevania: Aria of Sorrow",
        "Advance Wars",
        "Golden Sun",
        "Fire Emblem",
        "Super Mario Advance 4",
        "Mega Man Zero",
        "WarioWare, Inc.",
        "Final Fantasy Tactics",
        "Mother 3",
    ]
    im_gba = renderiza_gamelist(
        "gba", "Game Boy Advance", jogos_gba, 0, shot_mario, "MARIO KART: SUPER CIRCUIT"
    )
    im_gba.save(OUTPUT_DIR / "03_gamelist_gba.png")
    im_gba.save(VAR / "preview_gba_gamelist_pt.png")

    # 4. Gamelist PlayStation (PSX)
    jogos_psx = [
        "Castlevania: Symphony of the Night",
        "Metal Gear Solid",
        "Final Fantasy VII",
        "Resident Evil 2",
        "Crash Bandicoot 3: Warped",
        "Silent Hill",
        "Tekken 3",
        "Gran Turismo 2",
        "Tony Hawk's Pro Skater 2",
        "Spyro the Dragon",
        "Tomb Raider II",
        "Legacy of Kain: Soul Reaver",
        "Chrono Cross",
    ]
    im_psx = renderiza_gamelist(
        "psx", "PlayStation", jogos_psx, 0, shot_zelda, "CASTLEVANIA: SYMPHONY OF THE NIGHT"
    )
    im_psx.save(OUTPUT_DIR / "04_gamelist_psx.png")

    # 5. Diálogo de Save State (GuiSaveState)
    im_modal = renderiza_modal_savestate(im_snes, [shot_mario, shot_sonic])
    im_modal.save(OUTPUT_DIR / "05_modal_savestate.png")

    # 6. Carrossel de Videogames (System View - SNES)
    longdesc_snes = (
        "O lendário console de 16-bit da Nintendo com chip de som SPC700 e "
        "acervo inesquecível de clássicos que definiram a história dos videogames."
    )
    im_sys = renderiza_system_view(
        "snes", "Nintendo", "Super Nintendo",
        "1990  ·  Console 16-bit",
        longdesc_snes,
        snes_controller,
        snes_poster
    )
    im_sys.save(OUTPUT_DIR / "06_system_snes.png")

    # 7. Detalhe e Régua de Alinhamento (Zoom da Gamelist)
    regua = im_snes.copy()
    draw_r = ImageDraw.Draw(regua)
    # Linhas de guia em ciano para auditoria
    draw_r.line([16, 0, 16, 480], fill=(0, 255, 255, 220), width=1)   # margem esquerda 16px (GAMES e lista perfeitamente alinhados)
    draw_r.line([206, 0, 206, 480], fill=(0, 255, 255, 180), width=1) # limite da coluna gamelist (32%)
    draw_r.line([217, 0, 217, 480], fill=(0, 255, 255, 180), width=1) # margem da coluna direita (título do console e md_name)
    draw_r.line([0, 53, 640, 53], fill=(0, 255, 255, 180), width=1)   # linha de cabeçalho y=53
    draw_r.line([0, 444, 206, 444], fill=(0, 255, 255, 220), width=1) # final da gamelist y=444 (término da divisória)
    draw_r.line([0, 448, 640, 448], fill=(0, 255, 255, 220), width=1) # início da barra de atalhos y=448 (4px de respiro)
    draw_r.line([217, 415, 630, 415], fill=(0, 255, 255, 180), width=1) # início do nome do jogo branco y=415
    regua.save(OUTPUT_DIR / "07_detalhe_regua_gamelist.png")

    print(f"7 prints gerados com sucesso em {OUTPUT_DIR}")
    for p in sorted(OUTPUT_DIR.glob("*.png")):
        print(f"  - {p.name}: {p.stat().st_size // 1024} KB")

if __name__ == "__main__":
    main()
