# 7 루시아 진행 그림(편집 툴·DHL 보고용): 원화 · 리그 서 있기 · 표정 / 내려찍기 8장면(4×2) / 달리기 8장면 → review/<이름>.jpg
#   먼저: tools/idle_check7.py · tools/rig_shots.py review/v1/s "0.18,0.27,0.32,0.36,0.4,0.58,0.68,0.82" 0.5 · tools/run_shots.py review/v1/run_raw.png 8 .5
#   python3 -I tools/progress7.py 이름 "제목"
import glob, sys, os, json
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(HERE)
name = sys.argv[1] if len(sys.argv) > 1 else 'lucia7_v1'; title = sys.argv[2] if len(sys.argv) > 2 else ''
FT = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 24); FS = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 18)
BG = (232, 236, 242); NAVY = (40, 56, 96); W = 2000; rows = []
art = Image.open('ref512.png').convert('RGBA'); idle = Image.open('review/idle_check.png').crop((512, 0, 1024, 512)).convert('RGBA')
r1 = Image.new('RGB', (W, 440), BG); d = ImageDraw.Draw(r1)
if title: d.text((10, 2), title, fill=(30, 40, 60), font=FT)
for i, (im, lab) in enumerate(((art, '원화'), (idle, '리그 서 있기'))):
    a = im.resize((390, 390), Image.LANCZOS); bg = Image.new('RGBA', a.size, BG + (255,)); bg.alpha_composite(a); r1.paste(bg.convert('RGB'), (10 + i * 400, 44)); d.text((14 + i * 400, 44), lab, fill=(30, 40, 60), font=FS)
head = Image.open('../parts/head.png').convert('RGBA'); fx = 830
NM = [('face_neutral', '기본'), ('face_happy', '웃음'), ('face_angry', '화남'), ('face_focus', '집중'), ('face_shout', '외침'), ('face_effort', '힘줌'), ('blink_half', '깜빡 반'), ('blink_closed', '깜빡 다')]
for j, (n, lab) in enumerate(NM):
    h = head.copy(); h.alpha_composite(Image.open(f'../parts/{n}.png').convert('RGBA'))
    c = h.crop((58, 100, 178, 215)).resize((270, 259), Image.LANCZOS); c = c.crop((0, 40, 270, 230)); bg = Image.new('RGBA', c.size, BG + (255,)); bg.alpha_composite(c)
    x = fx + (j % 4) * 290; y = 44 + (j // 4) * 198; r1.paste(bg.convert('RGB'), (x, y)); d.text((x + 4, y + 2), lab, fill=(255, 255, 255), font=FS, stroke_width=2, stroke_fill=(30, 40, 60))
rows.append(r1)
fs = sorted(glob.glob('review/v1/s_*.png'), key=lambda f: float(f.split('_')[-1][:-4]))
LAB = {'0.180': '들어 올림', '0.270': '예비', '0.320': '휘두름', '0.360': '휘두름', '0.400': '타격', '0.580': '버팀', '0.680': '들어 돌림', '0.820': '돌아옴'}
tw, th = W // 4, 330; r2 = Image.new('RGB', (W, th * 2), NAVY); d = ImageDraw.Draw(r2)
for i, f in enumerate(fs[:8]):
    x0, y0, x1, y1 = 360, 900, 1110, 1310; im = Image.open(f).crop((x0, y0, x1, y1)); bg = Image.new('RGBA', im.size, NAVY + (255,)); dd = ImageDraw.Draw(bg); gy = 1300 - y0
    for kk, col in ((1.817, (255, 200, 0)), (1.75, (255, 90, 60))): y = gy - kk * 556 * .5; dd.line([(0, y), (x1 - x0, y)], fill=col, width=2)
    dd.line([(0, gy), (x1 - x0, gy)], fill=(160, 140, 100), width=3); bg.alpha_composite(im)
    s = min(tw / (x1 - x0), th / (y1 - y0)); bg = bg.resize((int((x1 - x0) * s), int((y1 - y0) * s)), Image.LANCZOS)
    t = f.split('_')[-1][:-4]; X, Y = (i % 4) * tw, (i // 4) * th; r2.paste(bg.convert('RGB'), (X, Y)); d.text((X + 8, Y + 6), f'{t}초 {LAB.get(t, "")}', fill=(255, 255, 255), font=FS)
rows.append(r2)
rr = Image.open('review/v1/run_raw.png').convert('RGB'); rr = rr.crop((0, 60, rr.width, rr.height)); rr = rr.resize((W, int(rr.height * W / rr.width)), Image.LANCZOS)
r3 = Image.new('RGB', (W, rr.height + 34), (255, 255, 255)); ImageDraw.Draw(r3).text((10, 4), '달리기 (1/60초씩 8장면)', fill=(30, 40, 60), font=FS); r3.paste(rr, (0, 34)); rows.append(r3)
H = sum(r.height for r in rows) + 8 * len(rows); B = Image.new('RGB', (W, H), BG); y = 0
for r in rows: B.paste(r, (0, y)); y += r.height + 8
B.save(f'review/{name}.jpg', quality=86); print(f'review/{name}.jpg', B.size)
