"""Rebuild the original hero loop: pip install pillow imageio-ffmpeg; python infra/media/render-fruit-loop.py."""
from math import cos, sin, pi
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFilter
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'mobile/assets/hero'
sheet = Image.open(ASSETS / 'fruit-cutouts.png').convert('RGBA')
sprites = [sheet.crop((x * 512, y * 512, (x + 1) * 512, (y + 1) * 512)) for y in range(2) for x in range(3)]
W, H, FPS, SECONDS = 1280, 720, 24, 10
background = Image.new('RGB', (W, H))
draw = ImageDraw.Draw(background)
for y in range(H):
    f = y / H
    draw.line((0, y, W, y), fill=(255, int(211 - 36 * f), int(91 - 49 * f)))
# Subject, centre, size, phase. Every trajectory returns to its start after ten seconds.
pieces = [(3, 1120, 70, 300, .2), (1, 740, 95, 210, 1.4), (2, 1070, 380, 330, 2.8),
          (0, 730, 415, 350, .5), (4, 925, 620, 190, 3.8), (5, 1245, 675, 290, 4.7),
          (1, 470, 680, 185, 2.2), (4, 440, 70, 125, 5.1), (3, 160, 750, 260, 1.7)]
pipe = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'error', '-f', 'rawvideo',
    '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-an', '-c:v', 'libx264',
    '-preset', 'slow', '-crf', '24', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
    str(ASSETS / 'grove-and-stone-fruit-loop.mp4')], stdin=subprocess.PIPE)
for frame in range(FPS * SECONDS):
    t = frame / (FPS * SECONDS) * 2 * pi
    canvas = background.copy().convert('RGBA')
    for fruit, x, y, size, phase in pieces:
        scale = int(size * (1 + .045 * sin(t + phase)))
        sprite = sprites[fruit].resize((scale, scale), Image.Resampling.LANCZOS).rotate(
            24 * sin(t + phase) + phase * 35, Image.Resampling.BICUBIC, expand=True)
        px, py = int(x + 32 * cos(t + phase) - sprite.width / 2), int(y + 48 * sin(t + phase) - sprite.height / 2)
        shadow = Image.new('RGBA', sprite.size, (133, 65, 0, 0))
        shadow.putalpha(sprite.getchannel('A').point(lambda a: int(a * .13)))
        canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(12)), (px + 10, py + 18))
        canvas.alpha_composite(sprite, (px, py))
    if frame == 0:
        canvas.convert('RGB').save(ASSETS / 'fruit-loop-poster.jpg', quality=88)
    pipe.stdin.write(canvas.convert('RGB').tobytes())
pipe.stdin.close()
if pipe.wait():
    raise SystemExit('Video encoding failed')
print('Created 10-second, 1280x720, silent H.264 loop:', ASSETS / 'grove-and-stone-fruit-loop.mp4')
