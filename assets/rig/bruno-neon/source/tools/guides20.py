"""20 네온 브루노 — 시트 요청 가이드 그림 3장(0번 합격 원화 ref512.png + measure20.json) — 2026-10-21 01:10 (guides10 구조)
  W20 = 프롬프트 2 첨부 2: 가까운 팔(맨살 윗팔·자줏빛 띠·크림 토시 팔뚝·주먹) + 가까운 철퇴(자루·공)만 빨갛게 — 어깨갑·검은 소매는 몸
  X20 = 프롬프트 3 첨부 2: 먼 팔 + 먼 철퇴만 빨갛게
  B20 = 프롬프트 1 첨부 2: 윗팔·다리 조각 길이 선(빨강 = 윗팔 · 보라 = 허벅지·정강이, 숫자 = 칸 번호)
  부품 칸은 seg 없이 관절 캡슐 + 철퇴 띠·공 원으로 — 윗팔 캡슐은 어깨갑(크림) 앞에서 끊음
실행: python3 -I guides20.py   (출력 = source/refs/)
"""
import json, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.abspath(os.path.join(HERE, '..')); OUT = os.path.join(SRC, 'refs')
M = json.load(open(os.path.join(SRC, 'measure20.json'))); RA = np.array(Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA'))
AL = RA[..., 3] > 20; YY, XX = np.mgrid[0:512, 0:512].astype(float)
hsv = cv2.cvtColor(RA[..., :3], cv2.COLOR_RGB2HSV); S, Vv = hsv[..., 1].astype(int), hsv[..., 2].astype(int)
CREAM = (S < 70) & (Vv > 165)                                                    # 어깨갑·토시 크림(어깨 쪽에서만 뺌)
V = lambda p: np.array(p, float)
def cap(p, q, r):
    p, q = V(p), V(q); d = q - p; L2 = max(d @ d, 1e-9); t = np.clip(((XX - p[0]) * d[0] + (YY - p[1]) * d[1]) / L2, 0, 1)
    return (XX - (p[0] + t * d[0])) ** 2 + (YY - (p[1] + t * d[1])) ** 2 <= r * r
UP_END = {'near': ((196, 321), XX > 178), 'far': ((297, 340), XX < 300)}         # 윗팔 = 팔꿈치 → 자줏빛 띠 끝(어깨갑 앞), 그 쪽 크림 = 어깨갑
def arm(sd):
    s = M[sd]; end, shoulder_side = UP_END[sd]
    up = cap(s['EL'], end, 14) & ~(CREAM & shoulder_side)
    return AL & (up | cap(s['EL'], s['WR'], 16) | cap(s['WR'], s['fist'], 17) | cap(s['fist'], s['fist'], 21))
def mace(sd):
    s = M[sd]; return AL & (cap(s['fist'], s['ball'], 13) | cap(s['ball'], s['ball'], s['ballR'] + 5))
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
red_guide(arm('near') | mace('near'), '빨간 곳(가까운 팔·주먹 + 가까운 철퇴 전체)만 지우고 그 뒤를 그려 주세요',
          '나머지(머리카락·얼굴·어깨갑·몸·먼 팔·먼 철퇴·다리)는 첨부 1과 픽셀 그대로', 'ref_W20_near_arm_mace_remove.png')
red_guide(arm('far') | mace('far'), '빨간 곳(먼 팔·주먹 + 먼 철퇴 전체)만 지우고 그 뒤를 그려 주세요',
          '나머지는 첨부 1과 픽셀 그대로 · 철퇴가 있던 몸 밖은 투명', 'ref_X20_far_arm_mace_remove.png')
# B20: 조각 길이 선(윗팔 = 어깨 → 팔꿈치, 다리 = 엉덩이 → 무릎 → 발목)
img = white(RA); d = ImageDraw.Draw(img); P = lambda p: (2 * p[0], 2 * p[1]); fb = ImageFont.truetype(FN, 40)
lines = [('11', M['near']['SH'], M['near']['EL'], (230, 30, 30), (-30, 20)), ('12', M['far']['SH'], M['far']['EL'], (230, 30, 30), (-10, 24))]
for n, a, b, c, off in lines:
    d.line([P(a), P(b)], fill=c, width=7)
    for p in (a, b): x, y = P(p); d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(0, 0, 0), width=3)
    x, y = P(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)); d.text((x + off[0], y + off[1]), n, fill=c, font=fb)
for n, sd, off in (('14·15', 'near', (-150, -10)), ('16·17', 'far', (30, -10))):
    g = M['legs'][sd]; d.line([P(g['hip']), P(g['knee'])], fill=(150, 60, 200), width=7); d.line([P(g['knee']), P(g['ankle'])], fill=(150, 60, 200), width=7)
    for p in (g['hip'], g['knee'], g['ankle']): x, y = P(p); d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(0, 0, 0), width=3)
    x, y = P(g['knee']); d.text((x + off[0], y + off[1]), n, fill=(150, 60, 200), font=fb)
banded(img, '빨강 = 윗팔(어깨→팔꿈치) · 보라 = 허벅지·정강이(엉덩이→무릎→발목)', '조각 길이 = 선 길이 + 양 끝 둥근 마디, 굵기 = 그림 속 팔·다리 그대로', (30, 30, 30)).save(os.path.join(OUT, 'ref_B20_limb_guide.png'))
print('저장 ref_B20_limb_guide.png', {n: round(float(np.hypot(a[0] - b[0], a[1] - b[1])), 1) for n, a, b, c, o in lines})
