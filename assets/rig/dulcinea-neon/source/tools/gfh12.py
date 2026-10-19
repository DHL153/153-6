# 12 네온 둘시네: 21번 쥔 손(자루 가로) 단독 그림 → attack/pieces/gFh.png + attack/pieces.json (10-20 08:58 기록, 다시 요청한 그림 오기 전 준비)
#   python3 -I tools/gfh12.py 받은그림.png  → 쥔 점·손목 점·자루 방향·배율을 재고 review/gfh_check.png(점·선 표시) 저장
#   자루 = 주먹 양옆으로 보이는 가로 띠(가운데 y) · 주먹 = 자루보다 높이가 1.6배 넘는 세로줄들 · 쥔 점 = 주먹 가로 가운데 × 자루 가운데
#   팔뚝 = 자루 위·쥔 점 왼쪽의 불투명 덩어리(주먹 빼고) → 주성분 축, 손목 = 그 축 위 주먹 쪽 끝 · 배율 = 원화 먼 주먹 손가락 줄(자루 따라 36px) ÷ 그림 손가락 줄
import os, sys, json, math
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fn = sys.argv[1]; ART_STACK = 36.0
a = np.array(Image.open(fn).convert('RGBA')).astype(np.int16)
if a[..., 3].min() == 255:   # 자홍 배경 → 알파
    m = (a[..., 0] > 180) & (a[..., 2] > 180) & (a[..., 1] < 90); a[..., 3] = np.where(m, 0, 255)
    soft = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None); a[..., 0] -= soft; a[..., 2] -= soft
a = np.clip(a, 0, 255).astype(np.uint8); A = a[..., 3] > 128
n_, lb, st, _ = cv2.connectedComponentsWithStats(A.astype(np.uint8), 8); big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])); A = lb == big; a[..., 3] = np.where(A, a[..., 3], 0)
ys, xs = np.nonzero(A); x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
colh = A.sum(0); cols = np.arange(A.shape[1])
# 자루: 왼쪽·오른쪽 끝 10% 세로줄의 불투명 가운데
edge = [c for c in range(x0, x0 + max(3, (x1 - x0) // 10))] + [c for c in range(x1 - max(3, (x1 - x0) // 10), x1 + 1)]
sh_c = [np.nonzero(A[:, c])[0].mean() for c in edge if A[:, c].any()]; sh_w = np.median([A[:, c].sum() for c in edge if A[:, c].any()])
SY = float(np.median(sh_c))
fist_cols = cols[colh > sh_w * 1.6]; fx0, fx1 = int(fist_cols.min()), int(fist_cols.max())
hsv = cv2.cvtColor(a[..., :3], cv2.COLOR_RGB2HSV); SK = A & (hsv[..., 0] >= 5) & (hsv[..., 0] <= 25) & (hsv[..., 1] > 80) & (hsv[..., 2] > 130)
# 손가락 줄 = 자루 둘레(±1.2 자루 굵기)의 살색 x 범위
_ry = np.arange(A.shape[0])[:, None]; band = SK & (_ry > SY - sh_w * .3) & (_ry < SY + sh_w * 1.2)   # 엄지(자루 위)는 빼고 손가락 줄만
bx = np.nonzero(band.any(0))[0]; stack = float(bx.max() - bx.min()) if len(bx) else float(fx1 - fx0)
G = np.array([(fx0 + fx1) / 2.0, SY])
# 팔뚝: 자루 위(y < SY − 굵기)·쥔 점 왼쪽·주먹 높이 위쪽 덩어리
top_f = np.nonzero(A[:, fx0:fx1 + 1].any(1))[0].min()
fm = A.copy(); fm[int(SY - sh_w * .6):, :] = False; fm[:, int(G[0]) + 1:] = False
pts = np.stack(np.nonzero(fm)[::-1], 1).astype(float)
if len(pts) > 50:
    c = pts.mean(0); w, v = np.linalg.eigh(np.cov((pts - c).T)); ax = v[:, 1]
    if ax @ (c - G) < 0: ax = -ax
    t = (pts - G) @ ax; WR = G + ax * np.percentile(t, 15)      # 손목 = 팔뚝 축 위, 주먹 쪽 15% 지점
    ang = math.degrees(math.atan2(-(ax[1]), -ax[0]))              # 자루 왼쪽(자루 끝 쪽)에서 위로 몇 도
else:
    WR = G + np.array([-20.0, -20.0]); ang = float('nan')
k = ART_STACK / stack
if os.environ.get('GRIP'): G = np.array([float(v) for v in os.environ['GRIP'].split(',')])     # 손으로 고칠 때: GRIP=x,y WRIST=x,y SCALE=원화배율
if os.environ.get('WRIST'): WR = np.array([float(v) for v in os.environ['WRIST'].split(',')]); ang = math.degrees(math.atan2(-(WR[1] - G[1]), -(WR[0] - G[0])))
if os.environ.get('SCALE'): k = float(os.environ['SCALE'])
print(f'size {A.shape[1]}x{A.shape[0]} · 자루 y {SY:.1f} 굵기 {sh_w:.0f} · 주먹 x {fx0}~{fx1} · 손가락 줄 {stack:.0f}px → 원화 배율 {k:.3f} (리그 {2 * k:.3f})')
print(f'쥔 점 {G.round(1).tolist()} · 손목 {WR.round(1).tolist()} · 팔뚝 각(자루 끝 쪽에서 위로) {ang:.1f}°  (러스트 33° · 받은 시트 21칸 65°)')
crop = a[max(0, y0 - 4):y1 + 5, max(0, x0 - 4):x1 + 5]; o = np.array([max(0, x0 - 4), max(0, y0 - 4)], float)
os.makedirs(os.path.join(HERE, 'attack', 'pieces'), exist_ok=True); Image.fromarray(crop).save(os.path.join(HERE, 'attack', 'pieces', 'gFh.png'))
J = {'gFh': {'size': [crop.shape[1], crop.shape[0]], 'grip': [round(float(G[0] - o[0]), 1), round(float(G[1] - o[1]), 1)], 'wrist': [round(float(WR[0] - o[0]), 1), round(float(WR[1] - o[1]), 1)],
             'shaftDir': [1, 0], 'scale': round(2 * k, 4), 'note': f'tools/gfh12.py {os.path.basename(fn)} — 손가락 줄 {stack:.0f}px → 원화 36px, 팔뚝 {ang:.1f}°'}}
json.dump(J, open(os.path.join(HERE, 'attack', 'pieces.json'), 'w'), ensure_ascii=False, indent=1)
v = Image.fromarray(crop).convert('RGBA'); bg = Image.new('RGBA', v.size, (210, 240, 210, 255)); bg.alpha_composite(v); d = ImageDraw.Draw(bg)
g, wr = G - o, WR - o; d.line([tuple(g - np.array([200, 0])), tuple(g + np.array([200, 0]))], fill=(0, 120, 255), width=2); d.line([tuple(g), tuple(g + (wr - g) * 3)], fill=(255, 0, 0), width=3)
d.ellipse([g[0] - 5, g[1] - 5, g[0] + 5, g[1] + 5], outline=(0, 0, 255), width=3); d.ellipse([wr[0] - 5, wr[1] - 5, wr[0] + 5, wr[1] + 5], outline=(255, 0, 0), width=3)
os.makedirs(os.path.join(HERE, 'review'), exist_ok=True); bg.convert('RGB').save(os.path.join(HERE, 'review', 'gfh_check.png')); print('→ attack/pieces/gFh.png · attack/pieces.json · review/gfh_check.png')
