"""30 스카이 브루노 — 시트 요청 가이드 그림 3장(0번 합격 원화 ref512.png + measure30.json) — guides20 구조
  W30 = 프롬프트 2 첨부 2: 가까운 팔(팔꿈치 맨살·토시·크림 감기·주먹) + 가까운 도끼(자루·머리)만 빨갛게 — 은색 어깨갑·남색 소매는 몸
  X30 = 프롬프트 3 첨부 2: 먼 팔 + 먼 도끼만 빨갛게
  B30 = 프롬프트 1 첨부 2: 다리 조각 길이 선(보라 = 허벅지·정강이, 숫자 = 칸 번호)
  도끼 머리 = 옛 30 원화 먼 도끼 머리를 SIFT 로 새 원화에 옮긴 모양(check_art30 와 같음) + 4px, 자루 = 소켓 → 주먹 → 마개 캡슐
실행: python3 -I guides30.py   (출력 = source/refs/)
"""
import json, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.abspath(os.path.join(HERE, '..')); OUT = os.path.join(SRC, 'refs')
M = json.load(open(os.path.join(SRC, 'measure30.json'))); RA = np.array(Image.open(os.path.join(SRC, 'ref512.png')).convert('RGBA'))
OLD = np.array(Image.open(os.path.join(SRC, 'refs', 'ref_design_char0030.png')).convert('RGBA'))
AL = RA[..., 3] > 20; YY, XX = np.mgrid[0:512, 0:512].astype(float)
V = lambda p: np.array(p, float)
def cap(p, q, r):
    p, q = V(p), V(q); d = q - p; L2 = max(d @ d, 1e-9); t = np.clip(((XX - p[0]) * d[0] + (YY - p[1]) * d[1]) / L2, 0, 1)
    return (XX - (p[0] + t * d[0])) ** 2 + (YY - (p[1] + t * d[1])) ** 2 <= r * r
# 도끼 머리 모양: 옛 원화 먼 도끼 머리 → 새 원화(SIFT)
_g = lambda a: cv2.cvtColor(np.ascontiguousarray(a[..., :3]), cv2.COLOR_RGB2GRAY); sf = cv2.SIFT_create(4000)
HM = (OLD[..., 3] > 0) & (((YY <= 146) & (XX >= 352)) | ((YY > 146) & (YY <= 184) & (XX >= 466)))
_n, _cc, _st, _ = cv2.connectedComponentsWithStats(HM.astype(np.uint8), connectivity=8); HM = _cc == 1 + int(np.argmax(_st[1:, cv2.CC_STAT_AREA]))
def head_mask(reg):
    k1, d1 = sf.detectAndCompute(_g(OLD), (HM * 255).astype(np.uint8)); k2, d2 = sf.detectAndCompute(_g(RA), ((AL & reg) * 255).astype(np.uint8))
    mm = [a for a, b in cv2.BFMatcher().knnMatch(d1, d2, k=2) if a.distance < 0.75 * b.distance]
    T, _ = cv2.estimateAffinePartial2D(np.float32([k1[a.queryIdx].pt for a in mm]), np.float32([k2[a.trainIdx].pt for a in mm]), ransacReprojThreshold=4.0)
    w = cv2.warpAffine(HM.astype(np.uint8) * 255, T, (512, 512)) > 60
    return cv2.dilate(w.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
HEADM = {'near': head_mask((XX < 230) & (YY < 220)), 'far': head_mask((XX > 330) & (YY < 280))}
UP_END = {'near': (182, 322), 'far': (308, 338)}                                   # 윗팔 = 팔꿈치 → 어깨갑·소매 앞 가장자리까지(그 안은 몸)
def arm(sd):
    s = M[sd]
    return AL & (cap(s['EL'], UP_END[sd], 13) | cap(s['EL'], s['WR'], 16) | cap(s['WR'], s['fist'], 17) | cap(s['fist'], s['fist'], 21))
def axe(sd):
    s = M[sd]; return AL & (cap(s['head'], s['fist'], 13) | cap(s['fist'], s['pommel'], 14) | HEADM[sd])
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
red_guide(arm('near') | axe('near'), '빨간 곳(가까운 팔·주먹 + 가까운 도끼 전체)만 지우고 그 뒤를 그려 주세요',
          '나머지(머리카락·얼굴·어깨갑·몸·먼 팔·먼 도끼)는 첨부 1과 픽셀 그대로', 'ref_W30_near_arm_axe_remove.png')
red_guide(arm('far') | axe('far'), '빨간 곳(먼 팔·주먹 + 먼 도끼 전체)만 지우고 그 뒤를 그려 주세요',
          '나머지는 첨부 1과 픽셀 그대로 · 도끼가 있던 몸 밖은 투명', 'ref_X30_far_arm_axe_remove.png')
img = white(RA); d = ImageDraw.Draw(img); P = lambda p: (2 * p[0], 2 * p[1]); fb = ImageFont.truetype(FN, 40)
for n, sd, off in (('14·15', 'near', (-150, -10)), ('16·17', 'far', (30, -10))):
    g = M['legs'][sd]; d.line([P(g['hip']), P(g['knee'])], fill=(150, 60, 200), width=7); d.line([P(g['knee']), P(g['ankle'])], fill=(150, 60, 200), width=7)
    for p in (g['hip'], g['knee'], g['ankle']): x, y = P(p); d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=(0, 0, 0), width=3)
    x, y = P(g['knee']); d.text((x + off[0], y + off[1]), n, fill=(150, 60, 200), font=fb)
banded(img, '보라 = 허벅지·정강이(엉덩이→무릎→발목) — 숫자 = 칸 번호', '조각 길이 = 선 길이 + 양 끝 둥근 마디, 굵기 = 그림 속 다리 그대로', (30, 30, 30)).save(os.path.join(OUT, 'ref_B30_limb_guide.png'))
print('저장 ref_B30_limb_guide.png')
