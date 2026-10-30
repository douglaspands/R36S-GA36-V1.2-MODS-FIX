#!/usr/bin/env python3
"""Gera as artes temáticas para o imageviewer no tema Epic Cody ML.
Cria:
  - _art/posters/imageviewer.png e imageviewer.jpg (640x480)
  - _art/controllers/imageviewer.png (530x400 RGBA)
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
THEME_DIR = ROOT / "features" / "50-temas-extras" / "storage" / ".config" / "emulationstation" / "themes" / "Epic Cody ML"
POSTERS_DIR = THEME_DIR / "_art" / "posters"
CONTROLLERS_DIR = THEME_DIR / "_art" / "controllers"

def cria_cena_pixel_1(w, h):
    """Cena 1: Pôr do sol pixel art com montanhas e gradiente retro."""
    im = Image.new("RGB", (w, h), (20, 24, 40))
    d = ImageDraw.Draw(im)
    # Céu degradê entardecer
    for y in range(h):
        t = y / h
        r = int(35 * (1 - t) + 240 * t * 0.9)
        g = int(30 * (1 - t) + 110 * t * 0.9)
        b = int(60 * (1 - t) + 80 * (1 - t * 0.5))
        d.line([(0, y), (w, y)], fill=(r, g, b))
    # Sol retro com listras
    cx, cy, r_sol = int(w * 0.5), int(h * 0.52), int(h * 0.32)
    for y in range(cy - r_sol, cy + r_sol):
        dy = y - cy
        if -r_sol <= dy <= r_sol:
            dx = int(math.sqrt(max(0, r_sol * r_sol - dy * dy)))
            # Listras horizontais do sol de synthwave
            if (y > cy and (y % 6) in (0, 1)):
                continue
            d.line([(cx - dx, y), (cx + dx, y)], fill=(255, 190, 40))
    # Montanhas em silhueta
    pontos1 = [(0, h), (0, int(h * 0.72)), (int(w * 0.3), int(h * 0.55)), (int(w * 0.55), int(h * 0.7)), (int(w * 0.8), int(h * 0.52)), (w, int(h * 0.68)), (w, h)]
    d.polygon(pontos1, fill=(45, 20, 55))
    pontos2 = [(0, h), (0, int(h * 0.82)), (int(w * 0.2), int(h * 0.7)), (int(w * 0.45), int(h * 0.8)), (int(w * 0.75), int(h * 0.65)), (w, int(h * 0.78)), (w, h)]
    d.polygon(pontos2, fill=(18, 12, 28))
    return im

def cria_cena_pixel_2(w, h):
    """Cena 2: Plataforma retro clássica (céu azul, nuvem, blocos e moedas)."""
    im = Image.new("RGB", (w, h), (92, 148, 252))
    d = ImageDraw.Draw(im)
    # Nuvens fofas
    for cx, cy, sz in [(int(w*0.25), int(h*0.22), 16), (int(w*0.75), int(h*0.3), 20)]:
        d.ellipse([cx - sz*1.5, cy - sz*0.7, cx + sz*1.5, cy + sz*0.7], fill=(255, 255, 255))
        d.ellipse([cx - sz*0.8, cy - sz*1.2, cx + sz*0.8, cy + sz*0.8], fill=(255, 255, 255))
    # Colina verde redonda
    d.ellipse([-20, int(h*0.55), int(w*0.55), int(h*1.2)], fill=(0, 168, 0))
    # Chão de tijolos
    chao_y = int(h * 0.75)
    d.rectangle([0, chao_y, w, h], fill=(200, 76, 12))
    # Linhas de tijolo do chão
    for x in range(0, w, 16):
        d.line([(x, chao_y), (x, h)], fill=(120, 40, 5), width=2)
    d.line([(0, chao_y), (w, chao_y)], fill=(0, 168, 0), width=4)
    # Bloco ? e tijolos suspensos
    bx, by, bsz = int(w*0.52), int(h*0.42), 22
    for offset in [-bsz*1.2, 0, bsz*1.2]:
        x0 = int(bx + offset)
        if offset == 0:
            d.rectangle([x0, by, x0 + bsz, by + bsz], fill=(252, 152, 56), outline=(0, 0, 0), width=2)
            d.text((x0 + 6, by + 2), "?", fill=(255, 255, 255))
        else:
            d.rectangle([x0, by, x0 + bsz, by + bsz], fill=(180, 70, 20), outline=(0, 0, 0), width=2)
    return im

def cria_cena_pixel_3(w, h):
    """Cena 3: Espaço sideral retro com nave pixel art e estrelas."""
    im = Image.new("RGB", (w, h), (10, 12, 22))
    d = ImageDraw.Draw(im)
    # Nebulosa
    for x in range(w):
        for y in range(h):
            dist = math.hypot(x - w*0.7, y - h*0.4)
            if dist < 60:
                glow = int((1 - dist / 60) * 80)
                im.putpixel((x, y), (10 + glow, 12 + int(glow * 0.4), 22 + glow * 2))
    d = ImageDraw.Draw(im)
    # Estrelas cintilantes
    estrelas = [(15, 20), (45, 12), (90, 35), (130, 15), (30, 80), (110, 95), (150, 70), (70, 110), (140, 120), (20, 140)]
    for sx, sy in estrelas:
        if sx < w and sy < h:
            d.point((sx, sy), fill=(255, 255, 255))
            if (sx + sy) % 3 == 0:
                d.point((sx+1, sy), fill=(200, 220, 255))
                d.point((sx, sy+1), fill=(200, 220, 255))
    # Nave espacial clássica
    nx, ny = int(w * 0.4), int(h * 0.5)
    pontos_nave = [(nx + 28, ny), (nx - 14, ny - 14), (nx - 6, ny - 4), (nx - 18, ny), (nx - 6, ny + 4), (nx - 14, ny + 14)]
    d.polygon(pontos_nave, fill=(240, 240, 250), outline=(255, 60, 40))
    # Propulsor azul
    d.polygon([(nx - 18, ny - 4), (nx - 28, ny), (nx - 18, ny + 4)], fill=(80, 180, 255))
    return im

def cria_polaroid(imagem_cena, rot_deg, border_w=12, bottom_h=34):
    """Empacota a cena dentro de uma moldura Polaroid clássica inclinada com sombra."""
    cw, ch = imagem_cena.size
    pw = cw + border_w * 2
    ph = ch + border_w + bottom_h
    # Imagem polaroid plana
    polaroid = Image.new("RGBA", (pw, ph), (250, 250, 252, 255))
    polaroid.paste(imagem_cena, (border_w, border_w))
    pd = ImageDraw.Draw(polaroid)
    # Borda sutil na foto interna
    pd.rectangle([border_w - 1, border_w - 1, border_w + cw, border_w + ch], outline=(210, 210, 215))
    # Linha decorativa ou logo sutil na base
    pd.rectangle([border_w, ph - 16, border_w + 32, ph - 12], fill=(255, 174, 0, 220)) # Accent Epic Cody
    pd.rectangle([border_w + 36, ph - 16, border_w + 70, ph - 14], fill=(200, 200, 205, 180))

    # Criação de sombra suave
    padding = 40
    canvas_w = pw + padding * 2
    canvas_h = ph + padding * 2
    shadow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle([padding + 6, padding + 10, padding + pw + 6, padding + ph + 10], fill=(0, 0, 0, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))

    # Junta foto sobre sombra
    shadow.paste(polaroid, (padding, padding), polaroid)

    # Rotaciona
    rotated = shadow.rotate(rot_deg, resample=Image.BICUBIC, expand=True)
    return rotated

def gera_poster():
    W, H = 640, 480
    bg = Image.new("RGB", (W, H), (16, 18, 22))
    d = ImageDraw.Draw(bg)

    # Gradiente de fundo suave da esquerda escura para direita grafite
    for x in range(W):
        t = x / W
        r = int(14 * (1 - t) + 28 * t)
        g = int(16 * (1 - t) + 32 * t)
        b = int(20 * (1 - t) + 38 * t)
        d.line([(x, 0), (x, H)], fill=(r, g, b))

    # Padrão sutil de pontos na área direita
    for x in range(240, W, 20):
        for y in range(0, H, 20):
            d.point((x, y), fill=(35, 42, 50))

    # Elemento geométrico temático de câmera / galeria em aramado âmbar ao fundo
    cx, cy = int(W * 0.72), int(H * 0.48)
    for rad in [140, 148, 170]:
        d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=(255, 174, 0, 30 if rad == 170 else 20), width=1)
    # Linhas de diafragma / foco
    for a in range(0, 360, 45):
        rad_a = math.radians(a)
        x1 = cx + int(130 * math.cos(rad_a))
        y1 = cy + int(130 * math.sin(rad_a))
        x2 = cx + int(155 * math.cos(rad_a))
        y2 = cy + int(155 * math.sin(rad_a))
        d.line([(x1, y1), (x2, y2)], fill=(255, 174, 0, 40), width=2)

    # 3 Cenas retro
    cena1 = cria_cena_pixel_1(170, 130)
    cena2 = cria_cena_pixel_2(170, 130)
    cena3 = cria_cena_pixel_3(160, 120)

    pol1 = cria_polaroid(cena1, -10)
    pol2 = cria_polaroid(cena2, 7)
    pol3 = cria_polaroid(cena3, -3)

    # Conversão do bg para RGBA para compor as polaroids
    bg_rgba = bg.convert("RGBA")

    # Posiciona as fotos em camadas
    # Foto 1 (fundo superior)
    bg_rgba.paste(pol1, (int(W * 0.42), int(H * 0.04)), pol1)
    # Foto 3 (fundo inferior)
    bg_rgba.paste(pol3, (int(W * 0.58), int(H * 0.46)), pol3)
    # Foto 2 (destaque central frente)
    bg_rgba.paste(pol2, (int(W * 0.46), int(H * 0.32)), pol2)

    # Fita adesiva semi-transparente sobre a foto principal
    tape = Image.new("RGBA", (50, 20), (255, 255, 255, 120))
    tape = tape.rotate(25, resample=Image.BICUBIC, expand=True)
    bg_rgba.paste(tape, (int(W * 0.48), int(H * 0.28)), tape)

    # Gradiente preto na esquerda (0 a 240) para contraste absoluto dos textos da UI
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    for x in range(250):
        alpha = int(255 * (1.0 - (x / 250.0) ** 1.3))
        vd.line([(x, 0), (x, H)], fill=(12, 14, 18, alpha))
    bg_rgba = Image.alpha_composite(bg_rgba, vignette)

    final_rgb = bg_rgba.convert("RGB")
    final_rgb.save(POSTERS_DIR / "imageviewer.jpg", quality=95)
    final_rgb.save(POSTERS_DIR / "imageviewer.png")
    print(f"Salvo pôster: {POSTERS_DIR / 'imageviewer.jpg'} ({W}x{H})")

def gera_controller_icon():
    W, H = 530, 400
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    # Centro do ícone de câmera instantânea elegante
    cx, cy = int(W * 0.52), int(H * 0.52)

    # Sombra geral sob a câmera
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([cx - 150, cy - 80, cx + 150, cy + 130], radius=32, fill=(0, 0, 0, 160))
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    im = Image.alpha_composite(im, sh)
    d = ImageDraw.Draw(im)

    # Foto saindo do topo da câmera (polaroid miniatura)
    px1, py1, px2, py2 = cx - 85, cy - 155, cx + 85, cy - 50
    d.rounded_rectangle([px1, py1, px2, py2], radius=6, fill=(245, 245, 248, 255), outline=(210, 210, 215, 255), width=2)
    # Cena da fotinho
    d.rectangle([px1 + 10, py1 + 10, px2 - 10, py2 - 25], fill=(70, 130, 220, 255))
    # Mini sol e montanhas na fotinho
    d.ellipse([cx + 15, py1 + 16, cx + 45, py1 + 46], fill=(255, 200, 40, 255))
    d.polygon([(px1 + 10, py2 - 25), (cx - 20, py1 + 35), (cx + 30, py2 - 25)], fill=(30, 90, 40, 255))
    d.polygon([(cx - 10, py2 - 25), (cx + 45, py1 + 45), (px2 - 10, py2 - 25)], fill=(20, 60, 30, 255))
    # Accent âmbar na base da foto
    d.rectangle([px1 + 10, py2 - 18, px1 + 40, py2 - 14], fill=(255, 174, 0, 255))

    # Corpo da câmera (Retângulo arredondado com visual premium cinza escuro/grafite)
    cam_x1, cam_y1, cam_x2, cam_y2 = cx - 145, cy - 75, cx + 145, cy + 120
    d.rounded_rectangle([cam_x1, cam_y1, cam_x2, cam_y2], radius=28, fill=(38, 42, 48, 255), outline=(55, 60, 68, 255), width=3)

    # Faixa decorativa superior com textura
    d.rectangle([cam_x1 + 4, cam_y1 + 4, cam_x2 - 4, cam_y1 + 44], fill=(28, 30, 35, 255))

    # Linha de acento âmbar (assinatura Epic Cody #FFAE00) atravessando a câmera
    d.rectangle([cam_x1 + 4, cam_y1 + 44, cam_x2 - 4, cam_y1 + 50], fill=(255, 174, 0, 255))

    # Slot de ejeção de filme no topo
    d.rounded_rectangle([cx - 95, cam_y1 + 6, cx + 95, cam_y1 + 14], radius=4, fill=(12, 12, 14, 255))

    # Flash à direita
    fx1, fy1, fx2, fy2 = cam_x2 - 60, cam_y1 + 16, cam_x2 - 20, cam_y1 + 38
    d.rounded_rectangle([fx1, fy1, fx2, fy2], radius=6, fill=(220, 225, 230, 255), outline=(120, 125, 135, 255), width=2)
    d.rectangle([fx1 + 6, fy1 + 6, fx2 - 6, fy2 - 6], fill=(255, 240, 180, 255))

    # Visor óptico à esquerda
    vx1, vy1, vx2, vy2 = cam_x1 + 22, cam_y1 + 16, cam_x1 + 52, cam_y1 + 38
    d.rounded_rectangle([vx1, vy1, vx2, vy2], radius=4, fill=(20, 22, 26, 255), outline=(80, 85, 95, 255), width=2)
    d.rounded_rectangle([vx1 + 5, vy1 + 5, vx2 - 5, vy2 - 5], radius=2, fill=(40, 120, 200, 220))

    # Lente circular centralizada
    lx, ly = cx, cy + 28
    # Anel externo da lente
    d.ellipse([lx - 68, ly - 68, lx + 68, ly + 68], fill=(24, 26, 30, 255), outline=(70, 75, 85, 255), width=4)
    # Anel metálico intermediário
    d.ellipse([lx - 55, ly - 55, lx + 55, ly + 55], fill=(48, 52, 60, 255), outline=(255, 174, 0, 255), width=2)
    # Vidro da lente
    d.ellipse([lx - 44, ly - 44, lx + 44, ly + 44], fill=(16, 22, 32, 255))
    # Reflexos de luz azul/turquesa e branco na lente esférica
    d.ellipse([lx - 34, ly - 34, lx - 8, ly - 8], fill=(50, 160, 220, 160))
    d.ellipse([lx - 28, ly - 28, lx - 18, ly - 18], fill=(255, 255, 255, 220))
    d.ellipse([lx + 10, ly + 10, lx + 26, ly + 26], fill=(40, 120, 180, 100))

    # Botão de disparo no topo esquerdo
    d.rounded_rectangle([cam_x1 + 26, cam_y1 - 10, cam_x1 + 56, cam_y1], radius=4, fill=(200, 50, 40, 255), outline=(150, 30, 25, 255), width=1)

    # LED indicador âmbar
    d.ellipse([cam_x2 - 80, cam_y1 + 24, cam_x2 - 72, cam_y1 + 32], fill=(255, 174, 0, 255))

    im.save(CONTROLLERS_DIR / "imageviewer.png")
    print(f"Salvo controller: {CONTROLLERS_DIR / 'imageviewer.png'} ({W}x{H})")

if __name__ == "__main__":
    gera_poster()
    gera_controller_icon()
