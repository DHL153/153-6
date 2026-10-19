# 2 러스트 둘시네 — 팔·허벅지 위치 그림(첨부 E): python3 -I make_limbs_ref.py
# 원화(손 고친 그림)를 2배로, 팔·허벅지 축을 색 선 + 번호로 (모양 도형은 그리지 않음 — 1번 시트에서 회색 알약 모양을 그대로 칠해 온 것 방지)
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
F = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'; FR = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
f_n = ImageFont.truetype(F, 30); f_t = ImageFont.truetype(F, 30); f_s = ImageFont.truetype(FR, 25)
S = 2; W, H = 1024 + 760, 1024
img = Image.new('RGB', (W, H), 'white')
art = Image.open(os.path.join(HERE, '..', 'ref512.png')).convert('RGBA').resize((1024, 1024), Image.LANCZOS)
bg = Image.new('RGBA', art.size, (255, 255, 255, 255)); bg.alpha_composite(art); img.paste(bg.convert('RGB'), (0, 0))
d = ImageDraw.Draw(img)
LIMBS = [  # 번호, 이름, 시작(어깨/엉덩이), 끝(팔꿈치/무릎/손목), 색, 숨음
    (1, '가까운 윗팔', (168, 258), (143, 291), (230, 40, 40), False),
    (2, '가까운 팔뚝', (143, 291), (133, 306), (240, 140, 0), False),
    (3, '먼 윗팔(몸 뒤에 숨음)', (276, 254), (246, 298), (40, 90, 230), True),
    (4, '먼 팔뚝', (246, 298), (290, 306), (0, 160, 200), False),
    (5, '가까운 허벅지', (190, 334), (178, 384), (150, 40, 200), False),
    (6, '먼 허벅지', (248, 338), (263, 389), (40, 160, 60), False)]
def dash(p, q, col):
    n = 10
    for i in range(n):
        if i % 2: continue
        a = (p[0] + (q[0] - p[0]) * i / n, p[1] + (q[1] - p[1]) * i / n); b = (p[0] + (q[0] - p[0]) * (i + 1) / n, p[1] + (q[1] - p[1]) * (i + 1) / n)
        d.line((a[0] * S, a[1] * S, b[0] * S, b[1] * S), fill=col, width=7)
for n, nm, p, q, col, hid in LIMBS:
    if hid: dash(p, q, col)
    else: d.line((p[0] * S, p[1] * S, q[0] * S, q[1] * S), fill=col, width=7)
    for r in (p, q): d.ellipse((r[0] * S - 8, r[1] * S - 8, r[0] * S + 8, r[1] * S + 8), outline=col, width=4)
    mx, my = (p[0] + q[0]) / 2 * S, (p[1] + q[1]) / 2 * S
    ox = -46 if n in (1, 2, 5) else 18
    d.ellipse((mx + ox - 4, my - 22, mx + ox + 40, my + 22), fill=col)
    d.text((mx + ox + 18, my), str(n), font=f_n, fill='white', anchor='mm')
x0 = 1060
d.text((x0, 30), '팔·허벅지 조각 — 위치 그림', font=f_t, fill='black')
for i, (n, nm, p, q, col, hid) in enumerate(LIMBS):
    y = 90 + i * 46; d.ellipse((x0, y, x0 + 34, y + 34), fill=col); d.text((x0 + 17, y + 17), str(n), font=f_n, fill='white', anchor='mm')
    d.text((x0 + 48, y + 2), nm, font=f_s, fill=(30, 30, 30))
notes = ['색 선 = 팔·다리 뼈의 방향(원 = 관절)', '점선 = 원화에서 몸에 가려 안 보이는 팔',
         '', '조각은 이 팔·다리를 곧게 편 모양으로:', '· 원화와 같은 굵기·외곽선·피부 음영', '· 근육 굴곡·관절 모양이 있는 그린 팔다리',
         '  (단순 알약·타원 도형 X)', '· 윗팔: 위 둥근 어깨, 아래 둥근 팔꿈치', '· 팔뚝: 위 둥근 팔꿈치, 아래 손목 붕대에서', '  곧게 잘림(주먹이 붙는 자리)',
         '· 허벅지: 위는 반바지 밑단 속으로 곧게,', '  아래 둥근 무릎(부츠 속으로)']
for i, t in enumerate(notes): d.text((x0, 400 + i * 40), t, font=f_s, fill=(60, 60, 60))
out = os.path.join(HERE, 'ref_E_limbs.png'); img.save(out); print(out)
