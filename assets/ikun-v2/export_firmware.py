"""Crop generated 2x2 atlases and encode board-sized transparent GIF resources."""
from pathlib import Path
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
BOARD = ROOT.parents[1] / 'xiaozhi-esp32/main/boards/waveshare/esp32-s3-touch-amoled-1.75/ikun'
NAMES = 'neutral happy laughing funny sad angry crying loving embarrassed surprised shocked thinking winking cool relaxed delicious kissy confident sleepy silly confused singing dancing rapper basketball'.split()
BOARD.mkdir(exist_ok=True)
(ROOT / 'preview').mkdir(exist_ok=True)
report = {}
contact = Image.new('RGB', (5 * 236, 5 * 270), '#f5f8f5')
draw = ImageDraw.Draw(contact)
for index, name in enumerate(NAMES):
    sheet = Image.open(ROOT / 'generated' / (name + '.png')).convert('RGBA')
    w, h = sheet.size
    cells = [sheet.crop((x*w//2, y*h//2, (x+1)*w//2, (y+1)*h//2)) for y in range(2) for x in range(2)]
    bounds = [cell.getchannel('A').point(lambda a: 255 if a >= 128 else 0).getbbox() for cell in cells]
    assert all(bounds), name
    union = (min(b[0] for b in bounds), min(b[1] for b in bounds), max(b[2] for b in bounds), max(b[3] for b in bounds))
    scale = min(200/(union[2]-union[0]), 202/(union[3]-union[1]))
    size = (round((union[2]-union[0])*scale), round((union[3]-union[1])*scale))
    frames = []
    for cell in cells:
        art = cell.crop(union).resize(size, Image.Resampling.LANCZOS)
        frame = Image.new('RGBA', (216, 234))
        frame.alpha_composite(art, ((216-size[0])//2, 212-size[1]))
        alpha = frame.getchannel('A')
        pal = frame.convert('RGB').quantize(colors=96, dither=Image.Dither.NONE)
        palette = pal.getpalette()
        pal.putpalette(palette[:765] + [0,0,0])
        pal.paste(255, mask=alpha.point(lambda a: 255 if a < 128 else 0))
        frames.append(pal)
    duration = [240, 160, 160, 240]
    if name in ['singing','dancing','rapper','basketball']: duration = [180]*4
    if name == 'sleepy': duration = [550]*4
    output = BOARD / ('ikun_' + name + '.gif')
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=duration, loop=0, transparency=255, disposal=2, optimize=False)
    with Image.open(output) as gif:
        assert gif.n_frames == 4, (name,gif.n_frames)
        first = gif.convert('RGBA')
        first.save(ROOT / 'preview' / (name + '.png'))
        contact.paste(first, ((index%5)*236+10,(index//5)*270+5), first)
    draw.text(((index%5)*236+10,(index//5)*270+243), name, fill='black')
    report[name] = {'frames':4,'duration_ms':duration,'bytes':output.stat().st_size,'source_size':[w,h]}
contact.save(ROOT / 'contact-sheet.png')
(ROOT / 'animations.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'{len(report)} unique states, {sum(r["bytes"] for r in report.values())} bytes')
