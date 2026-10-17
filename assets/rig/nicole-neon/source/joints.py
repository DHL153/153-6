"""기준 그림(ref1024 = 리그 단위) 위의 관절 좌표를 조각 배치에서 계산하고 표시 그림을 만든다."""
import json, numpy as np, cv2
from PIL import Image, ImageDraw
import sys; sys.path.insert(0, '.')
from limbs import ends
S = json.load(open('sift_result.json')); F = json.load(open('fix_result.json')); HJ = json.load(open('hands.json'))
M = lambda r: np.array(r['M'])
ap = lambda m, p: m[:, :2] @ np.array(p, float) + m[:, 2]
def alpha(fn): return np.asarray(Image.open(fn))[..., 3] > 128
J = {}
# 머리: 목 = 피부(목 토막)의 가장 아래 줄 가운데
h = np.asarray(Image.open('cut/head.png').convert('RGBA')).astype(int); al = h[..., 3] > 128
sk = al & (h[..., 0] > 200) & (h[..., 1] > 140) & (h[..., 2] < 170) & (h[..., 0] - h[..., 2] > 50)
ys, xs = np.nonzero(sk); yb = ys.max(); nx = xs[ys > yb - 12].mean(); J['neckImg'] = [float(nx), float(yb - 10)]
J['NECK'] = ap(M(S['head']), J['neckImg']).tolist()
# 코트 허리띠 버클 중심 = 엉덩이 뼈(H)
c = np.asarray(Image.open('cut/coat.png').convert('RGBA')).astype(int); al = c[..., 3] > 128
gold = al & (c[..., 0] > 170) & (c[..., 1] > 120) & (c[..., 2] < 90) & (c[..., 0] - c[..., 2] > 90)
ys, xs = np.nonzero(gold & (np.arange(c.shape[0])[:, None] < 60)); J['buckleImg'] = [float(xs.mean()), float(ys.mean())]
J['H'] = ap(M(S['coat']), J['buckleImg']).tolist()
# 앞팔(가까운 팔) 팔꿈치 = armL 조각 위쪽 끝
(e1, w1), (e2, w2) = ends('cut/armL.png')[0]; top = e1 if e1[1] < e2[1] else e2; J['armLElbowImg'] = top.tolist(); J['EN'] = ap(M(S['armL']), top).tolist()
# 어깨: 어깨갑 그림의 아래쪽 1/3 가운데
def bbox_ref(r):
    a = np.asarray(Image.open(r['file']))[..., 3]; w = cv2.warpAffine(a, M(r), (1024, 1024)); ys, xs = np.nonzero(w > 128); return xs.min(), xs.max(), ys.min(), ys.max()
x0, x1, y0, y1 = bbox_ref(S['pauldron']); J['SN'] = [(x0 + x1) / 2 + 4, y0 + (y1 - y0) * .62]
x0, x1, y0, y1 = bbox_ref(F['pauldronF']); J['SF'] = [(x0 + x1) / 2 + 2, y0 + (y1 - y0) * .6]
# 먼 주먹: hands.json 의 쥔 점(자르기 전 cut 좌표) → 기준
g = np.array(HJ['fistF']['grip']) + HJ['fistF']['off']; J['G'] = ap(M(S['fistF']), g).tolist()
json.dump(J, open('joints.json', 'w'), indent=1); print(json.dumps(J))
ref = Image.open('ref1024.png'); b = Image.new('RGBA', ref.size, (255, 255, 255, 255)); b.alpha_composite(ref); d = ImageDraw.Draw(b)
for k in ['NECK', 'H', 'EN', 'SN', 'SF', 'G']:
    x, y = J[k]; d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 0, 80)); d.text((x + 7, y - 6), k, fill=(255, 0, 80))
b.crop((250, 350, 850, 800)).convert('RGB').save(sys.argv[1] if len(sys.argv) > 1 else 'joints.png')
