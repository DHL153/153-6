"""17 네온 루시아 — 시트 요청 가이드 그림 3장(0번 합격 원화 ref512.png + measure17.json) — guides20(20 네온 브루노) 구조
  N17 = 프롬프트 2 첨부 2: 방패만 빨갛게(가까운 손은 방패 뒤라 원화에 안 보임 — 지운 뒤에도 팔은 그리지 않음)
  F17 = 프롬프트 3 첨부 2: 먼 팔 전체(큰 크림 어깨갑 · 회색 윗팔 판 · 짙은 소매 · 크림 팔뚝 갑 · 회색 손목 고리 · 쇠 장갑 주먹) + 도끼 전체 빨갛게
  L17 = 프롬프트 1 첨부 2: 조각 길이 선(빨강 = 먼 윗팔·팔뚝 · 보라 = 허벅지·정강이, 숫자 = 칸 번호)
  방패·먼 팔 = 격자 확대(grid17.py 3·4·6배)에서 읽은 바깥 외곽선 다각형 ∩ 불투명, 도끼 = 머리·모자 상자(x < 344 · y > 176, 챙 끝 x < 352 · y > 205) 밖 y < 262 + 주먹 밑 자루·마개 캡슐
실행: python3 -I guides17.py   (출력 = source/refs/)
"""
import json, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.abspath(os.path.join(HERE, '..')); OUT = os.path.join(SRC, 'refs')
M = json.load(open(os.path.join(SRC, 'measure17.json'))); RA = np.array(Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA'))
AL = RA[..., 3] > 20; YY, XX = np.mgrid[0:512, 0:512].astype(float)
def poly(pts):
    m = Image.new('L', (512, 512), 0); ImageDraw.Draw(m).polygon([tuple(map(float, p)) for p in pts], fill=255); return np.array(m) > 0
def cap(p, q, r):
    p, q = np.array(p, float), np.array(q, float); d = q - p; L2 = max(d @ d, 1e-9); t = np.clip(((XX - p[0]) * d[0] + (YY - p[1]) * d[1]) / L2, 0, 1)
    return (XX - (p[0] + t * d[0])) ** 2 + (YY - (p[1] + t * d[1])) ** 2 <= r * r
SHIELD = AL & poly([(120, 147), (152, 171), (190, 197), (224, 212), (230, 232), (238, 250), (234, 275), (229, 310), (220, 345), (209, 390), (196, 420),
                    (180, 440), (152, 462), (138, 455), (126, 434), (110, 405), (96, 396), (75, 386), (64, 372), (48, 330), (50, 290), (55, 240), (72, 203), (82, 178), (105, 160)])
FARARM = AL & poly([(343, 258), (352, 254), (368, 253), (385, 259), (396, 272), (402, 288), (406, 275), (414, 263), (430, 257), (450, 260), (462, 272), (465, 292),
                    (460, 308), (450, 318), (430, 322), (420, 320), (418, 330), (410, 342), (402, 360), (380, 361), (362, 360), (349, 345), (345, 330), (343, 300), (340, 275)])
AXE = AL & (((YY < 262) & (XX > 296) & ~(((XX < 344) & (YY > 176)) | ((XX < 352) & (YY > 205)))) | cap((440, 318), (453, 366), 21))
FN = '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'; f = ImageFont.truetype(FN, 30); BH = 112
def white(a):
    al = a[..., 3:4] / 255.0; return Image.fromarray((a[..., :3] * al + 255 * (1 - al)).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
def banded(img, l1, l2, c1):
    W = Image.new('RGB', (1024, 1024 + BH), (255, 255, 255)); W.paste(img, (0, BH)); d = ImageDraw.Draw(W)
    d.text((20, 14), l1, fill=c1, font=f); d.text((20, 56), l2, fill=(30, 30, 30), font=f); d.line([(0, BH - 2), (1024, BH - 2)], fill=(200, 200, 200), width=2); return W
def red_guide(mask, l1, l2, name):
    m = cv2.dilate(mask.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    m2 = np.array(Image.fromarray((m * 255).astype(np.uint8)).resize((1024, 1024), Image.BILINEAR)) > 127
    im = np.array(white(RA)).astype(float); im[m2] = im[m2] * .45 + np.array([235, 40, 40]) * .55
    edge = m2 & ~(cv2.erode(m2.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0); im[edge] = (200, 0, 0)
    banded(Image.fromarray(im.astype(np.uint8)), l1, l2, (200, 0, 0)).save(os.path.join(OUT, name)); print('저장', name, '빨간 px@512', int(m.sum()))
red_guide(SHIELD, '빨간 곳(방패 전체)만 지우고 그 뒤 몸을 그려 주세요',
          '가까운 팔은 그리지 않음 · 나머지는 첨부 1과 픽셀 그대로', 'ref_N17_shield_remove.png')
red_guide(FARARM | AXE, '빨간 곳(먼 팔 전체 + 도끼 전체)만 지우고 그 뒤를 그려 주세요',
          '먼 팔은 새로 그리지 않음 · 나머지는 첨부 1과 픽셀 그대로', 'ref_F17_far_arm_axe_remove.png')
# L17: 조각 길이 선(먼 윗팔 = 어깨 → 팔꿈치, 먼 팔뚝 = 팔꿈치 → 손목, 다리 = 엉덩이 → 무릎 → 발목)
img = white(RA); d = ImageDraw.Draw(img); P = lambda p: (2 * p[0], 2 * p[1]); fb = ImageFont.truetype(FN, 40)
fa = M['far']; lines = [('13', fa['SH'], fa['EL'], (230, 30, 30), (-62, -10)), ('14', fa['EL'], fa['WR'], (230, 30, 30), (6, 14))]
for n, a, b, c, off in lines:
    d.line([P(a), P(b)], fill=c, width=7)
    for p in (a, b): x, y = P(p); d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(0, 0, 0), width=3)
    x, y = P(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)); d.text((x + off[0], y + off[1]), n, fill=c, font=fb)
for n, sd, off in (('15·17', 'near', (-150, -30)), ('16·18', 'far', (24, -60))):
    g = M['legs'][sd]; d.line([P(g['hip']), P(g['knee'])], fill=(150, 60, 200), width=7); d.line([P(g['knee']), P(g['ankle'])], fill=(150, 60, 200), width=7)
    for p in (g['hip'], g['knee'], g['ankle']): x, y = P(p); d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(0, 0, 0), width=3)
    x, y = P(g['knee']); d.text((x + off[0], y + off[1]), n, fill=(150, 60, 200), font=fb)
banded(img, '빨강 = 먼 윗팔(13)·먼 팔뚝(14) · 보라 = 허벅지·정강이(15~18)', '조각 길이 = 선 길이 + 양 끝 둥근 마디, 굵기 = 그림 속 팔·다리 그대로', (30, 30, 30)).save(os.path.join(OUT, 'ref_L17_limb_guide.png'))
print('저장 ref_L17_limb_guide.png', {n: round(float(np.hypot(a[0] - b[0], a[1] - b[1])), 1) for n, a, b, c, o in lines})
