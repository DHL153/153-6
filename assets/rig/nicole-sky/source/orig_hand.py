"""앞손(먼 팔) = 원본 그림(char_0028)의 손 그대로 (2026-10-18, DHL "이 손을 그대로 적용")
원본에서 팔뚝(은색 팔 보호대)·손목·손을 오려 한 장으로 쓴다.
 - 원본은 자루가 팔뚝 앞을 지나고, 손가락만 자루 앞에서 감싼다 → 두 장으로 나눔
   origHandF.png  : 팔뚝+손 (자루에 가려졌던 팔뚝은 둘레 색으로 메움) → 창 뒤에 그림
   origFingersF.png: 손가락(피부+테두리)만 → 창 앞에 그림 (같은 캔버스·같은 기준점이라 정확히 겹침)
 - 원본 1px = 리그 2단위(refScale 2). 4배로 키워 배율 .5 (보간만, 새 디테일 없음)
 - 자루 축: 손 양옆 나무 심 가운데를 이은 선 -33.4°. 가릴 곳은 일정한 띠가 아니라 실제 나무색(+테두리)으로 찾음 (원본 자루는 원근으로 왼쪽 아래가 굵음)
출력: ../parts/origHandF.png, ../parts/origFingersF.png, orig_hand.json (pivot=팔꿈치, grip, shaftDir, scale)
실행: cd source && python3 -I orig_hand.py
"""
import os, json, math, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..', 'parts')
SRC = os.path.join(HERE, '..', '..', '..', 'art', 'characters', 'char_0028.png')
a = np.asarray(Image.open(SRC).convert('RGBA')).astype(np.float32)
X0, Y0, X1, Y1 = 292, 238, 372, 324                       # 오릴 범위 (원본 px)
A = a[Y0:Y1, X0:X1].copy(); H, W = A.shape[:2]
ANG = math.atan(-0.66); U = np.array([math.cos(ANG), math.sin(ANG)]); N_ = np.array([-U[1], U[0]])   # 손 양옆(x 320~334, 360~370) 나무 심 가운데를 이은 선 (-33.4°). 원본 자루는 왼쪽 아래로 갈수록 굵어짐(원근)
P0 = np.array([366., 249.5])                               # 자루 축 위의 한 점 (원본 px)
HALF = float(os.environ.get('SKY_OH_HALF', '7.5'))         # 자루 반폭(테두리 포함, 원본 px): 심 9.4 + 테두리
yy, xx = np.mgrid[0:H, 0:W] + np.array([Y0, X0])[:, None, None]
sgn = (xx - P0[0]) * N_[0] + (yy - P0[1]) * N_[1]
band = np.abs(sgn) <= HALF
# 팔뚝+손 윤곽 (원본 px, 눈금 확대로 읽음): 왼쪽 가까운 팔 소매·위 머리카락·아래 치마 제외. 위쪽은 보호대 윗단(금·은 띠)까지만 — 그 위 자루 테두리는 넣지 않음
poly = [(303.5, 271), (310, 268), (318, 267.5), (324, 269.5), (330, 266), (334, 261), (338, 249), (350, 247), (358, 250), (362, 258), (360, 270), (352, 281),
        (347, 291), (341, 300), (330, 309), (320, 316), (312, 314), (305.5, 306), (301, 298), (300.5, 283)]
pm = Image.new('L', (W, H), 0); ImageDraw.Draw(pm).polygon([(x - X0, y - Y0) for x, y in poly], fill=255); inside = np.asarray(pm) > 0
r, g, b, al = A[..., 0], A[..., 1], A[..., 2], A[..., 3]
rgb = A[..., :3] / 255; mx = rgb.max(-1); mn = rgb.min(-1); dd = np.maximum(mx - mn, 1e-6); sat = (mx - mn) / np.maximum(mx, 1e-6)
hue = np.where(mx == rgb[..., 0], ((rgb[..., 1] - rgb[..., 2]) / dd) % 6, np.where(mx == rgb[..., 1], (rgb[..., 2] - rgb[..., 0]) / dd + 2, (rgb[..., 0] - rgb[..., 1]) / dd + 4)) * 60
skin = (al > 150) & (hue > 14) & (hue < 40) & (sat > .3) & (mx > .7) & inside
lb, n = nd.label(skin); sz = nd.sum(skin, lb, range(1, n + 1)); skin = lb == 1 + int(np.argmax(sz))
skin = nd.binary_fill_holes(nd.binary_closing(skin, iterations=2))
lum = A[..., :3].mean(-1); ink = (lum < 70) & (al > 150)
fingers = skin | (nd.binary_dilation(skin, iterations=2) & ink)          # 손가락 + 손가락 테두리
fingers &= inside
_hull = np.zeros(skin.shape, np.uint8); cv2.fillPoly(_hull, [cv2.convexHull(np.argwhere(skin)[:, ::-1].astype(np.int32))], 1)
fingers &= nd.binary_dilation(_hull.astype(bool), iterations=2)          # 손가락 테두리만 (손 밖으로 이어지는 자루 테두리 가시는 뺌)
# 팔뚝: 윤곽 안, 자루 띠(+테두리 2px) 밖의 원본 픽셀. 띠 안(자루에 가려졌던 팔뚝)은 띠 위·아래 팔뚝 색을 가로질러 이어 메움
along = (xx - P0[0]) * U[0] + (yy - P0[1]) * U[1]
tF = along[fingers & band].min()                           # 손가락이 자루에 닿기 시작하는 자리 (여기부터 오른쪽은 팔뚝 없음)
wood = (al > 150) & (r > 60) & (r < 175) & (g > 35) & (g < 115) & (b > 15) & (b < 85) & (r - b > 30) & (r > g)   # 자루 나무색
bandW = nd.binary_dilation(nd.binary_opening(wood, iterations=1) & (np.abs(sgn) <= 13), iterations=3) & (np.abs(sgn) <= 16)   # 자루 = 실제 나무색 + 테두리 3px
known = inside & ~bandW & (al > 10)
rowk = np.round(sgn * 2).astype(int); right = np.zeros_like(fingers)        # 손가락 오른쪽(자루가 손 밖으로 나가는 쪽)은 팔뚝 없음
for k in np.unique(rowk[fingers & bandW]):
    sel = rowk == k; right |= sel & (along > along[sel & fingers].max())
hidden = inside & bandW & ~fingers & ~right & (along < tF + 12)
col = A[..., :3].copy()
def side(y, x, dirn):
    for k in range(1, 9):
        q = np.array([x, y]) + dirn * N_ * k
        xi, yi = int(round(q[0])), int(round(q[1]))
        if 0 <= xi < W and 0 <= yi < H and known[yi, xi] and lum[yi, xi] > 80: return A[yi, xi, :3], k
    return None, None
for y, x in zip(*np.nonzero(hidden)):
    cu, ku = side(y, x, -1); cd, kd = side(y, x, 1)
    if cu is None and cd is None: continue
    if cu is None: col[y, x] = cd
    elif cd is None: col[y, x] = cu
    else: col[y, x] = (cu * kd + cd * ku) / (ku + kd)
col = np.where(hidden[..., None], cv2.GaussianBlur(col, (0, 0), 1.0), col)   # 메운 곳만 살짝 부드럽게
base = np.zeros((H, W, 4), np.float32)
base[..., :3] = np.where(fingers[..., None], A[..., :3], col)
base[..., 3] = np.where(known | fingers, al, np.where(hidden, 255, 0))
# 메운 곳의 바깥 윤곽(팔꿈치 쪽 끝)에 원본 같은 잉크 테두리
edge = hidden & ~nd.binary_erosion(inside, iterations=2)
base[edge, :3] = [26, 20, 24]
# 윤곽으로 잘린 자리(바깥에도 원본 그림이 이어지던 곳)에 잉크 테두리 — 잘린 면이 거칠게 보이지 않게
cut = inside & ~nd.binary_erosion(inside, iterations=1) & nd.binary_dilation((al > 150) & ~inside, iterations=1) & ~fingers & (base[..., 3] > 0)
base[cut, :3] = [26, 20, 24]; base[cut, 3] = 255
fing = np.zeros_like(base); fing[fingers] = A[fingers]
K = 4
def up(img):
    pmul = img.copy(); pmul[..., :3] *= pmul[..., 3:4] / 255
    big = cv2.resize(pmul, (W * K, H * K), interpolation=cv2.INTER_LANCZOS4)
    big[..., 3] = np.clip(big[..., 3], 0, 255); aa = big[..., 3:4]
    big[..., :3] = np.where(aa > 0, big[..., :3] * 255 / np.maximum(aa, 1e-3), 0)
    return Image.fromarray(np.clip(big, 0, 255).astype(np.uint8), 'RGBA')
up(base).save(os.path.join(OUT, 'origHandF.png')); up(fing).save(os.path.join(OUT, 'origFingersF.png'))
# 기준점 (조각 px = (원본 px - 오린 시작) × K)
ELB = np.array([float(os.environ.get('SKY_OH_EX', '305')), float(os.environ.get('SKY_OH_EY', '293'))])   # 팔꿈치: 보호대 넓은 끝(금테) 가운데 바로 바깥
cy, cx = np.argwhere(skin).mean(0) + [Y0, X0]
G = P0 + U * ((cx - P0[0]) * U[0] + (cy - P0[1]) * U[1])               # 쥔 점 = 손 가운데를 자루 축에 내린 점
tp = lambda p: [round(float((p[0] - X0) * K), 1), round(float((p[1] - Y0) * K), 1)]
geo = dict(src='parts/origHandF.png', fingers='parts/origFingersF.png', scale=round(2 / K, 4), pivot=tp(ELB), elbow=tp(ELB), grip=tp(G), wrist=tp(G),
           shaftDir=[round(float(U[0]), 4), round(float(U[1]), 4)], origGrip=[round(float(G[0]), 1), round(float(G[1]), 1)])
json.dump(geo, open(os.path.join(HERE, 'orig_hand.json'), 'w'), indent=1); print(geo)
# 확인용: 노란 바탕 3배 + 자루 축
chk = Image.new('RGBA', (W * K, H * K), (250, 235, 150, 255)); chk.alpha_composite(up(base)); chk.alpha_composite(up(fing))
d = ImageDraw.Draw(chk); g = tp(G); e = tp(ELB)
d.line([(g[0] - U[0] * 300, g[1] - U[1] * 300), (g[0] + U[0] * 300, g[1] + U[1] * 300)], fill=(255, 0, 0, 255), width=1)
d.ellipse([g[0] - 5, g[1] - 5, g[0] + 5, g[1] + 5], outline=(255, 0, 0, 255)); d.ellipse([e[0] - 5, e[1] - 5, e[0] + 5, e[1] + 5], outline=(0, 0, 255, 255))
chk.convert('RGB').save(os.path.join(HERE, '_orighand_check.png'))
