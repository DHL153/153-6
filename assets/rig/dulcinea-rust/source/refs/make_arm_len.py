# 팔 조각 다시 요청용 기준 그림: 원화(2배) 위에 팔 길이만 색 선으로 (채운 도형 없음 — 실수 28)
from PIL import Image, ImageDraw, ImageFont
import glob
RA = Image.open('../ref512.png').convert('RGBA'); k = 2
bg = Image.new('RGBA', (1024 + 360, 1024), (255, 255, 255, 255)); bg.alpha_composite(RA.resize((1024, 1024), Image.LANCZOS), (0, 0))
d = ImageDraw.Draw(bg)
fs = glob.glob('/usr/share/fonts/**/*CJK*Bold*', recursive=True) + glob.glob('/usr/share/fonts/**/*CJK*', recursive=True)
f = ImageFont.truetype(fs[0], 26) if fs else ImageFont.load_default(); f2 = ImageFont.truetype(fs[0], 22) if fs else f
UP, FO = 70, 65   # 원화 px: 어깨~팔꿈치, 팔꿈치~손목
for sx, sy in ((150, 236), (290, 250)):   # 가까운 어깨(화면 왼쪽)·먼 어깨(오른쪽) — 곧게 위로 뻗은 팔
    S = (sx * k, sy * k); E = (sx * k, (sy - UP) * k); Wr = (sx * k, (sy - UP - FO) * k)
    d.line([S, E], fill=(230, 30, 30), width=9); d.line([E, Wr], fill=(30, 90, 230), width=9)
    for p in (S, E, Wr): d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], outline=(20, 20, 20), width=4)
d.text((1040, 60), '팔 길이 기준', fill=(20, 20, 20), font=f)
d.text((1040, 110), '빨강 = 어깨~팔꿈치', fill=(230, 30, 30), font=f2)
d.text((1040, 145), '      (키의 0.16)', fill=(230, 30, 30), font=f2)
d.text((1040, 190), '파랑 = 팔꿈치~손목', fill=(30, 90, 230), font=f2)
d.text((1040, 225), '      (키의 0.15)', fill=(30, 90, 230), font=f2)
d.text((1040, 290), '팔을 위로 곧게 뻗으면', fill=(20, 20, 20), font=f2)
d.text((1040, 322), '주먹이 머리 꼭대기 높이', fill=(20, 20, 20), font=f2)
d.text((1040, 380), '왼쪽 선 = 가까운 팔', fill=(20, 20, 20), font=f2)
d.text((1040, 412), '오른쪽 선 = 먼 팔', fill=(20, 20, 20), font=f2)
bg.convert('RGB').save('ref_G_arm_len.png'); print(bg.size)
