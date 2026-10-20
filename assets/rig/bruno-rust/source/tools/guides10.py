"""10 러스트 브루노 — 시트 요청 가이드 그림 3장(0번 합격 원화로) — 2026-10-20 22:05
  W10 = 프롬프트 2 첨부 2: 가까운 팔(소매·붕대 팔뚝·주먹) + 가까운 도끼만 빨갛게 — '그 부품만 지운 원화'(19 에서 가려진 곳 메움에 가장 좋았음)
  X10 = 프롬프트 3 첨부 2: 먼 팔(소매·붕대 팔뚝·주먹) + 먼 도끼만 빨갛게
  B10 = 프롬프트 1 첨부 2: 팔·다리 조각 길이 선(빨강 = 윗팔 · 초록 = 팔뚝 · 보라 = 다리, 숫자 = 칸 번호) — 받은 시트 팔이 짧게 오는 것(19: 0.7배) 미리 막음
  부품 칸은 seg 없이 measure10.json 관절 + 도끼 축으로(캡슐·띠) — 재킷(올리브)·칼라(크림) 픽셀은 팔에서 뺌
실행: python3 -I guides10.py   (출력 = source/refs/)
"""
import json, math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.abspath(os.path.join(HERE, '..')); OUT = os.path.join(SRC, 'refs')
M = json.load(open(os.path.join(SRC, 'measure10.json'))); RA = np.array(Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA'))
AL = RA[..., 3] > 20; YY, XX = np.mgrid[0:512, 0:512].astype(float)
hsv = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV); Hh, S, Vv = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
JACKET = (Hh >= 18) & (Hh <= 40) & (S > 70) & (Vv > 60) & (Vv < 200)          # 올리브 재킷
V = lambda p: np.array(p, float)
def cap(p, q, r):
    p, q = V(p), V(q); d = q - p; L2 = max(d @ d, 1e-9); t = np.clip(((XX - p[0]) * d[0] + (YY - p[1]) * d[1]) / L2, 0, 1)
    return (XX - (p[0] + t * d[0])) ** 2 + (YY - (p[1] + t * d[1])) ** 2 <= r * r
def axe(sd):
    s = M[sd]; Fi, Hd = V(s['fist']), V(s['head']); ax = (Hd - Fi) / np.linalg.norm(Hd - Fi); nv = np.array([-ax[1], ax[0]]); hu = np.linalg.norm(Hd - Fi)
    u = (XX - Fi[0]) * ax[0] + (YY - Fi[1]) * ax[1]; v = (XX - Fi[0]) * nv[0] + (YY - Fi[1]) * nv[1]
    return AL & (((u > -34) & (u < hu) & (np.abs(v) < 12)) | ((u > hu - 62) & (u < hu + 84) & (v > -74) & (v < 106)))
def arm(sd, rU, rF):
    s = M[sd]; m = cap(s['SH'], s['EL'], rU) | cap(s['EL'], s['fist'], rF) | cap(s['fist'], s['fist'], 19)
    return AL & m & ~JACKET
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
red_guide(arm('near', 15, 15) | axe('near'), '빨간 곳(가까운 팔·주먹 + 가까운 도끼 전체)만 지우고 그 뒤를 그려 주세요',
          '나머지(머리카락·얼굴·재킷·먼 팔·먼 도끼·다리)는 첨부 1과 픽셀 그대로', 'ref_W10_near_arm_axe_remove.png')
red_guide(arm('far', 13, 14) | axe('far'), '빨간 곳(먼 팔·주먹 + 먼 도끼 전체)만 지우고 그 뒤를 그려 주세요',
          '나머지는 첨부 1과 픽셀 그대로 · 도끼가 있던 몸 밖은 투명', 'ref_X10_far_arm_axe_remove.png')
# B10: 조각 길이 선
img = white(RA); d = ImageDraw.Draw(img); P = lambda p: (2 * p[0], 2 * p[1]); fb = ImageFont.truetype(FN, 40)
lines = [('13', M['near']['SH'], M['near']['EL'], (230, 30, 30), (-80, -10)), ('14', M['far']['SH'], M['far']['EL'], (230, 30, 30), (-10, 30)),
         ('15', M['near']['EL'], M['near']['WR'], (20, 160, 40), (-80, -20)), ('16', M['far']['EL'], M['far']['WR'], (20, 160, 40), (20, 10))]
for n, a, b, c, off in lines:
    d.line([P(a), P(b)], fill=c, width=7)
    for p in (a, b): x, y = P(p); d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(0, 0, 0), width=3)
    x, y = P(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)); d.text((x + off[0], y + off[1]), n, fill=c, font=fb)
for n, sd, off in (('22·23', 'near', (-150, -10)), ('24·25', 'far', (30, -10))):
    g = M['legs'][sd]; d.line([P(g['hip']), P(g['knee'])], fill=(150, 60, 200), width=7); d.line([P(g['knee']), P(g['ankle'])], fill=(150, 60, 200), width=7)
    x, y = P(g['knee']); d.text((x + off[0], y + off[1]), n, fill=(150, 60, 200), font=fb)
banded(img, '빨강 = 윗팔(어깨→팔꿈치) · 초록 = 팔뚝(팔꿈치→손목) · 보라 = 허벅지·정강이', '조각 길이 = 선 길이 + 양 끝 둥근 마디, 굵기 = 그림 속 팔·다리 그대로', (30, 30, 30)).save(os.path.join(OUT, 'ref_B10_limb_guide.png'))
print('저장 ref_B10_limb_guide.png', {n: round(float(np.hypot(a[0] - b[0], a[1] - b[1])), 1) for n, a, b, c, o in lines})
