# 7 루시아 v1.1 진행 그림(편집 툴·DHL 보고용): 달리기 다리 전(v1)/후(v1.1) 같은 장면 번호 + 내려찍기 8장면 → review/lucia7_v11.jpg
#   먼저: tools/run_shots.py (TW=578 TH=622, 18장면 .5) 로 전·후 달리기 줄 2개 · tools/rig_shots.py review/v11/s "0.18,…" 0.5
#   python3 -I tools/progress7_v11.py 전.png 후.png [제목]
import glob, sys, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); before, after = sys.argv[1], sys.argv[2]; title = sys.argv[3] if len(sys.argv) > 3 else ''
FT = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 26); FS = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 19)
BG = (232, 236, 242); NAVY = (40, 56, 96); W = 2000; rows = []
r0 = Image.new('RGB', (W, 48), BG); ImageDraw.Draw(r0).text((10, 6), title, fill=(30, 40, 60), font=FT); rows.append(r0)
TW, TH = 578, 622; FR = [0, 3, 6, 9, 12, 15]; cx0, cy0, cx1, cy1 = 120, 250, 460, 622
for fn, lab in ((before, 'v1 (전) — 다리가 튜닉 위로 · 무릎 크게 접힘'), (after, 'v1.1 (후) — 다리 = 튜닉·허리띠 뒤 · 작은 보폭 · 곧은 다리')):
    im = Image.open(fn).convert('RGB'); tw = W // len(FR); s = tw / (cx1 - cx0); th = int((cy1 - cy0) * s)
    r = Image.new('RGB', (W, th + 34), (255, 255, 255)); d = ImageDraw.Draw(r); d.text((10, 4), lab, fill=(30, 40, 60), font=FS)
    for i, f in enumerate(FR):
        x, y = (f % 9) * TW, (f // 9) * TH; t = im.crop((x + cx0, y + cy0, x + cx1, y + cy1)).resize((tw, th), Image.LANCZOS); r.paste(t, (i * tw, 34)); d.text((i * tw + 6, 38), f'{f}/60', fill=(200, 30, 30), font=FS)
    rows.append(r)
fs = sorted(glob.glob(os.path.join(HERE, 'review', 'v11', 's_*.png')), key=lambda f: float(f.split('_')[-1][:-4]))
LAB = {'0.180': '들어 올림', '0.270': '예비', '0.320': '휘두름', '0.360': '휘두름', '0.400': '타격', '0.580': '버팀', '0.680': '들어 돌림', '0.820': '돌아옴'}
fs = [f for f in fs if f.split('_')[-1][:-4] in LAB]
tw, th = W // 4, 330; r2 = Image.new('RGB', (W, th * 2 + 34), NAVY); d = ImageDraw.Draw(r2); d.text((10, 4), '내려찍기 (그리는 순서 v1.1: 다리 = 상체·골반 뒤, 도끼·팔뚝 = 다리 뒤)', fill=(255, 255, 255), font=FS)
for i, f in enumerate(fs[:8]):
    x0, y0, x1, y1 = 360, 900, 1110, 1310; im = Image.open(f).crop((x0, y0, x1, y1)); bg = Image.new('RGBA', im.size, NAVY + (255,)); ImageDraw.Draw(bg).line([(0, 1300 - y0), (x1 - x0, 1300 - y0)], fill=(160, 140, 100), width=3); bg.alpha_composite(im)
    s = min(tw / (x1 - x0), th / (y1 - y0)); bg = bg.resize((int((x1 - x0) * s), int((y1 - y0) * s)), Image.LANCZOS)
    t = f.split('_')[-1][:-4]; X, Y = (i % 4) * tw, 34 + (i // 4) * th; r2.paste(bg.convert('RGB'), (X, Y)); d.text((X + 8, Y + 6), f'{t}초 {LAB.get(t, "")}', fill=(255, 255, 255), font=FS)
rows.append(r2)
H = sum(r.height for r in rows) + 8 * len(rows); B = Image.new('RGB', (W, H), BG); y = 0
for r in rows: B.paste(r, (0, y)); y += r.height + 8
out = os.path.join(HERE, 'review', 'lucia7_v11.jpg'); B.save(out, quality=86); print(out, B.size)
