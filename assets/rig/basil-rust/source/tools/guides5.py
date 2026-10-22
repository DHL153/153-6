"""5 러스트 바실 — 시트 요청 가이드 3장(ref512.png + measure5.json) — guides30 구조
  W5 = 프롬프트 2 첨부 2: 가까운 팔(어깨 살) + 가까운 건틀릿 전체만 빨갛게 / X5 = 프롬프트 3 첨부 2: 먼 윗팔 살 + 먼 건틀릿 전체만
  B5 = 프롬프트 1 첨부 2: 다리 조각 길이 선(보라) · 윗팔(빨강)
실행: python3 -I guides5.py   (출력 = source/refs/)
"""
import json, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.abspath(os.path.join(HERE, '..')); OUT = os.path.join(SRC, 'refs')
M = json.load(open(os.path.join(SRC, 'measure5.json'))); RA = np.array(Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA'))
AL = RA[..., 3] > 20; YY, XX = np.mgrid[0:512, 0:512].astype(float)
V = lambda p: np.array(p, float)
def cap(p, q, r):
    p, q = V(p), V(q); d = q - p; L2 = max(d @ d, 1e-9); t = np.clip(((XX - p[0]) * d[0] + (YY - p[1]) * d[1]) / L2, 0, 1)
    return (XX - (p[0] + t * d[0])) ** 2 + (YY - (p[1] + t * d[1])) ** 2 <= r * r
def poly(pts):
    m = np.zeros((512, 512), np.uint8); cv2.fillPoly(m, [np.array(pts, np.int32)], 1); return m > 0
def side(sd):
    s = M[sd]; return AL & (poly(s['gaunt']) | cap(s['SH'], s['EL'], 14))
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
red_guide(side('near'), '빨간 곳(가까운 어깨·팔 + 가까운 건틀릿 전체)만 지우고 그 뒤를 그려 주세요', '나머지(머리·조끼·몸·먼 팔·먼 건틀릿·다리)는 첨부 1과 픽셀 그대로', 'ref_W5_near_arm_gauntlet_remove.png')
red_guide(side('far'), '빨간 곳(먼 윗팔 + 먼 건틀릿 전체)만 지우고 그 뒤를 그려 주세요', '나머지는 첨부 1과 픽셀 그대로 · 건틀릿이 있던 몸 밖은 투명', 'ref_X5_far_arm_gauntlet_remove.png')
img = white(RA); d = ImageDraw.Draw(img); P = lambda p: (2 * p[0], 2 * p[1]); fb = ImageFont.truetype(FN, 40)
for n, sd, off in (('16·17', 'near', (-150, -10)), ('18·19', 'far', (30, -10))):
    g = M['legs'][sd]; d.line([P(g['hip']), P(g['knee'])], fill=(150, 60, 200), width=7); d.line([P(g['knee']), P(g['ankle'])], fill=(150, 60, 200), width=7)
    for p in (g['hip'], g['knee'], g['ankle']): x, y = P(p); d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(0, 0, 0), width=3)
    x, y = P(g['knee']); d.text((x + off[0], y + off[1]), n, fill=(150, 60, 200), font=fb)
for n, sd, off in (('13', 'near', (-60, -20)), ('14', 'far', (10, -50))):
    s = M[sd]; d.line([P(s['SH']), P(s['EL'])], fill=(230, 30, 30), width=7); x, y = P(s['SH']); d.text((x + off[0], y + off[1]), n, fill=(230, 30, 30), font=fb)
banded(img, '빨강 = 윗팔(어깨→팔꿈치) · 보라 = 허벅지·정강이(엉덩이→무릎→발목)', '숫자 = 칸 번호 · 조각 길이 = 선 길이 + 둥근 끝, 굵기 = 그림 속 그대로', (30, 30, 30)).save(os.path.join(OUT, 'ref_B5_limb_guide.png'))
print('저장 ref_B5_limb_guide.png')
