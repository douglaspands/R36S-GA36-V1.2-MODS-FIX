#!/usr/bin/env python3
"""Gera a arte do poster 640x480 do console LÖVE para o tema Epic Cody ML."""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
POSTER_PATH = (
    ROOT
    / "features"
    / "50-temas-extras"
    / "storage"
    / ".config"
    / "emulationstation"
    / "themes"
    / "Epic Cody ML"
    / "_art"
    / "posters"
    / "love2d.png"
)
POSTER_LOVE2D_DIR = (
    ROOT
    / "features"
    / "50-temas-extras"
    / "storage"
    / ".config"
    / "emulationstation"
    / "themes"
    / "Epic Cody ML"
    / "love2d"
    / "poster.png"
)
LOGO_PATH = (
    ROOT
    / "features"
    / "50-temas-extras"
    / "storage"
    / ".config"
    / "emulationstation"
    / "themes"
    / "Epic Cody ML"
    / "love2d"
    / "logo.png"
)

WIDTH, HEIGHT = 640, 480

def create_poster():
    # Cria tela base
    img = Image.new("RGBA", (WIDTH, HEIGHT), (18, 20, 32, 255))
    draw = ImageDraw.Draw(img)

    # 1. Gradiente de fundo: Escuro à esquerda (#121420), suavemente azul-índigo à direita (#1c2136)
    for x in range(WIDTH):
        factor = x / WIDTH
        r = int(16 + factor * 14)
        g = int(18 + factor * 16)
        b = int(28 + factor * 32)
        draw.line([(x, 0), (x, HEIGHT)], fill=(r, g, b, 255))

    # 2. Glows de iluminação suave no quadrante direito (estética love2d.org)
    glow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    # Glow magenta/rosa (#d6336c / #e64980) atrás dos balões principais
    glow_draw.ellipse([340, 60, 620, 340], fill=(214, 51, 108, 45))
    # Glow ciano suave (#15aabf) na parte inferior direita
    glow_draw.ellipse([400, 220, 640, 460], fill=(21, 170, 191, 35))
    # Glow violeta central
    glow_draw.ellipse([440, 120, 600, 280], fill=(132, 94, 247, 40))

    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(40))
    img = Image.alpha_composite(img, glow_layer)

    # 3. Desenho de balões estilizados e corações com sombreado 3D suave (vetorial em alta resolução)
    balloon_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(balloon_layer)

    def draw_heart(cx, cy, size, color, highlight=True):
        """Desenha coração paramétrico suave."""
        points = []
        for deg in range(0, 360, 4):
            t = math.radians(deg)
            # Curva clássica do coração
            x = 16 * (math.sin(t) ** 3)
            y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            points.append((cx + x * (size / 16.0), cy + y * (size / 16.0)))
        bdraw.polygon(points, fill=color)
        if highlight:
            # Brilho especular no lobo superior esquerdo
            bdraw.ellipse(
                [cx - size * 0.55, cy - size * 0.55, cx - size * 0.2, cy - size * 0.2],
                fill=(255, 255, 255, 120)
            )

    def draw_round_balloon(cx, cy, rx, ry, color):
        """Desenha balão oval com brilho e nó."""
        bdraw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=color)
        # Brilho
        bdraw.ellipse(
            [cx - rx * 0.65, cy - ry * 0.65, cx - rx * 0.15, cy - ry * 0.15],
            fill=(255, 255, 255, 100)
        )
        # Nó do balão
        bdraw.polygon([
            (cx - 4, cy + ry), (cx + 4, cy + ry), (cx, cy + ry + 6)
        ], fill=color)

    def draw_string(start_x, start_y, end_x, end_y, ctrl_dx):
        """Desenha cordão sinuoso do balão."""
        pts = []
        steps = 25
        for i in range(steps + 1):
            t = i / steps
            # Bezier quadrática com controle
            cx = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * (start_x + ctrl_dx) + t ** 2 * end_x
            cy = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * (start_y + (end_y - start_y) * 0.5) + t ** 2 * end_y
            pts.append((cx, cy))
        for j in range(len(pts) - 1):
            bdraw.line([pts[j], pts[j+1]], fill=(220, 225, 240, 80), width=1)

    # Cordões convergindo para a parte inferior direita
    draw_string(440, 200, 520, 420, -15)
    draw_string(530, 160, 520, 420, 20)
    draw_string(480, 270, 520, 420, -10)
    draw_string(570, 240, 520, 420, 15)

    # Balão Ciano (fundo)
    draw_round_balloon(570, 220, 32, 40, (34, 184, 207, 230))

    # Balão Violeta (médio)
    draw_round_balloon(480, 250, 36, 44, (132, 94, 247, 235))

    # Coração LÖVE Rosa Choque (ícone principal love2d.org)
    draw_heart(440, 150, 58, (230, 73, 128, 250))

    # Coração Ciano Claro flutuando ao lado
    draw_heart(530, 120, 42, (77, 171, 247, 240))

    # Pequenos corações e partículas de confete flutuando
    draw_heart(380, 220, 14, (247, 131, 172, 190), highlight=False)
    draw_heart(590, 140, 16, (255, 212, 59, 210), highlight=False)
    draw_heart(490, 80, 12, (255, 135, 135, 180), highlight=False)
    draw_heart(550, 310, 18, (34, 184, 207, 190), highlight=False)
    draw_heart(420, 290, 15, (177, 151, 252, 180), highlight=False)

    # Partículas circulares de confete colorido
    confetti = [
        (410, 110, 3, (255, 212, 59, 200)),
        (460, 95, 4, (34, 184, 207, 180)),
        (560, 85, 3, (247, 131, 172, 190)),
        (610, 210, 4, (132, 94, 247, 180)),
        (450, 330, 3, (77, 171, 247, 170)),
        (370, 170, 2, (255, 255, 255, 160)),
        (510, 200, 3, (255, 212, 59, 180)),
    ]
    for px, py, pr, pc in confetti:
        bdraw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=pc)

    img = Image.alpha_composite(img, balloon_layer)

    # 4. Inserção do logotipo oficial estilizado do LÖVE na composição à direita
    if LOGO_PATH.is_file():
        logo = Image.open(LOGO_PATH).convert("RGBA")
        # Redimensiona mantendo proporção (ex: largura ~210px)
        lw, lh = logo.size
        target_w = 210
        target_h = int(lh * (target_w / lw))
        logo_resized = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # Posiciona na área inferior direita (x ~410, y ~350)
        pos_x = 405
        pos_y = 350

        # Adiciona sombra suave sob o logotipo
        shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        shadow.paste(logo_resized, (pos_x + 2, pos_y + 3))
        # Escurece a sombra
        s_data = []
        for item in shadow.getdata():
            if item[3] > 0:
                s_data.append((0, 0, 0, int(item[3] * 0.45)))
            else:
                s_data.append((0, 0, 0, 0))
        shadow.putdata(s_data)
        shadow = shadow.filter(ImageFilter.GaussianBlur(4))
        img = Image.alpha_composite(img, shadow)

        # Cola o logotipo
        img.paste(logo_resized, (pos_x, pos_y), logo_resized)

    # 5. Salva na resolução oficial 640x480 em RGB
    final_poster = img.convert("RGB")
    POSTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    final_poster.save(POSTER_PATH, format="PNG", optimize=True)
    print(f"Salvo: {POSTER_PATH} ({final_poster.size[0]}x{final_poster.size[1]})")

    POSTER_LOVE2D_DIR.parent.mkdir(parents=True, exist_ok=True)
    final_poster.save(POSTER_LOVE2D_DIR, format="PNG", optimize=True)
    print(f"Salvo: {POSTER_LOVE2D_DIR} ({final_poster.size[0]}x{final_poster.size[1]})")

if __name__ == "__main__":
    create_poster()
