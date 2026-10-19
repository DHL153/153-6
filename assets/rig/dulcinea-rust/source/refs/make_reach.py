# 키트 시트(5번) 첨부용: 원화(2배) 위에 두 팔이 닿는 범위 원(외곽선만 — 채운 도형 금지, 실수 28)
#   팔 길이 = 원화 관절점(build_dulcinea.py SH·EL·WR·G)에서 잰 어깨→팔꿈치→주먹 가운데. ref_G_arm_len.png(14:20)는 팔을 길게 잡은 틀린 그림 — 쓰지 않음
from PIL import Image, ImageDraw, ImageFont
import numpy as np, glob
RA = Image.open('../ref512.png').convert('RGBA'); k = 2
SH_N, EL_N, WR_N, GN = map(np.array, ([170, 248], [146, 280], [133, 299], [130, 332]))
SH_F, EL_F, WR_F = map(np.array, ([270, 262], [255, 300], [288, 304])); GF = np.array([357 - 0.70 * (311 - 250), 311.0])
LN = np.linalg.norm(EL_N - SH_N) + np.linalg.norm(GN - EL_N); LF = np.linalg.norm(EL_F - SH_F) + np.linalg.norm(GF - EL_F)
print('arm near', round(LN, 1), 'far', round(LF, 1), 'height 448 ->', round(LN / 448, 3), round(LF / 448, 3))
W = 1024 + 560; bg = Image.new('RGBA', (W, 1024), (255, 255, 255, 255)); bg.alpha_composite(RA.resize((1024, 1024), Image.LANCZOS), (0, 0))
d = ImageDraw.Draw(bg)
fs = glob.glob('/usr/share/fonts/**/*CJK*Bold*', recursive=True); f = ImageFont.truetype(fs[0], 28); f2 = ImageFont.truetype(fs[0], 22)
for S, L, col in ((SH_N, LN, (30, 90, 230)), (SH_F, LF, (230, 40, 40))):
    c = S * k; r = L * k
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], outline=col + (255,), width=6)
    d.ellipse([c[0] - 10, c[1] - 10, c[0] + 10, c[1] + 10], fill=col + (255,))
# 곧게 위로 뻗은 팔 끝 높이
for S, L, col in ((SH_N, LN, (30, 90, 230)), (SH_F, LF, (230, 40, 40))):
    top = (S[1] - L) * k; d.line([(S[0] * k - 70, top), (S[0] * k + 70, top)], fill=col + (255,), width=9)
x0 = 1045
lines = [('두 손이 닿는 곳 (팔 길이 = 원화 그대로)', (20, 20, 20), f),
         ('파랑 원 = 가까운 손(화면 왼쪽, 쇠판 장갑)', (30, 90, 230), f2), ('   어깨 → 주먹 가운데 ' + f'{LN / 448:.2f} × 키', (30, 90, 230), f2),
         ('빨강 원 = 먼 손(화면 오른쪽, 붕대 손)', (230, 40, 40), f2), ('   어깨 → 주먹 가운데 ' + f'{LF / 448:.2f} × 키', (230, 40, 40), f2),
         ('', (0, 0, 0), f2),
         ('두 손이 같이 자루를 쥘 수 있는 곳', (20, 20, 20), f2), ('= 두 원이 겹치는 곳', (20, 20, 20), f2),
         ('', (0, 0, 0), f2),
         ('짧은 가로선 = 팔을 위로 곧게', (20, 20, 20), f2), ('뻗었을 때 주먹 높이(이마 근처)', (20, 20, 20), f2),
         ('→ 두 손은 머리 꼭대기 위로', (20, 20, 20), f2), ('   올라갈 수 없음', (20, 20, 20), f2)]
y = 60
for t, col, ff in lines: d.text((x0, y), t, fill=col, font=ff); y += 40
bg.convert('RGB').save('ref_H_reach.png'); print('ok', bg.size)
