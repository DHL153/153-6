# 12 네온 둘시네: 21번 쥔 손(자루 가로) 단독 그림 → attack/pieces/gFh.png + attack/pieces.json   (10-20 09:12 DHL 그림 받음 → 방법 고침)
#   python3 -I tools/gfh12.py sheets/gFh_v2.png
#   ①자홍 배경 → 알파 ②팔뚝 축 = 살색·흰 손목 보호대(쥔 점 위·왼쪽) 주성분 ③손목 = 흰 보호대 가장 큰 덩어리의 주먹 쪽 끝(축 위 97%)
#   ④쥔 점 = 손가락(자루 아래 살색) x 가운데 × 자루 가운데 y ⑤그림에서 팔뚝·보호대는 손목 선(축에 수직)에서 잘라 냄 — 팔뚝은 원화 팔뚝 조각(afFart2)이 IK 로 그림
#   ⑥자루 토막(주먹 밖)은 지움 — 실제 망치 자루가 그 자리에 그려짐 ⑦배율 = 원화 먼 주먹(손가락 줄 36 × 높이 43.6)과 넓이가 같게 → 리그 px 로 줄여 저장(scale 1)
#   엔진 규칙(러스트 gFh 와 같음): grip = wrist = elbow = 쥔 점(공 손목), foreDir = 쥔 점 → 손목 방향(팔뚝이 장갑 끝으로 들어오는 방향)
import os, sys, json, math
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fn = sys.argv[1]
a = np.array(Image.open(fn).convert('RGB')).astype(np.int16); H_, W_ = a.shape[:2]
mag = (a[..., 0] > 180) & (a[..., 2] > 180) & (a[..., 1] < 90); A = ~mag
soft = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None) * (a[..., 0] > 120) * (a[..., 2] > 120); a[..., 0] -= soft; a[..., 2] -= soft
a = np.clip(a, 0, 255).astype(np.uint8)
n_, lb, st, _ = cv2.connectedComponentsWithStats(A.astype(np.uint8), 8); A = lb == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
yy, xx = np.mgrid[0:H_, 0:W_]
hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV); SK = A & (hsv[..., 0] >= 5) & (hsv[..., 0] <= 25) & (hsv[..., 1] > 80) & (hsv[..., 2] > 130)
WH = A & (a.min(-1) > 165) & (np.abs(a[..., 0].astype(int) - a[..., 2]) < 45)
# 자루: 그림 양 끝 세로줄 불투명 가운데 · 굵기
xs = np.nonzero(A.any(0))[0]; x0, x1 = xs.min(), xs.max()
edge = list(range(x1 - 19, x1 + 1))   # 오른쪽 끝(쇠 머리 쪽 자루 토막)만 — 왼쪽 끝은 팔뚝이 먼저 나올 수 있음
SY = float(np.median([np.nonzero(A[:, c])[0].mean() for c in edge])); SW = float(np.median([A[:, c].sum() for c in edge]))
# 손가락 = 자루 가운데 아래 살색
FG = SK & (yy > SY + SW * .15); fx = np.nonzero(FG.any(0))[0]; FX0, FX1 = int(fx.min()), int(fx.max()); FYB = int(np.nonzero(FG.any(1))[0].max())
G = np.array([(FX0 + FX1) / 2.0, SY])
# 흰 보호대(가장 큰 덩어리) · 팔뚝 축
nw, lw, sw, _ = cv2.connectedComponentsWithStats(WH.astype(np.uint8), 8); GUARD = lw == 1 + int(np.argmax(sw[1:, cv2.CC_STAT_AREA]))
FA = (SK | GUARD) & (yy < SY - SW * .2) & (xx < G[0] - 40)
pts = np.stack(np.nonzero(FA)[::-1], 1).astype(float); c = pts.mean(0); w, v = np.linalg.eigh(np.cov((pts - c).T)); ax = v[:, 1]
if ax[0] < 0: ax = -ax                      # ax: 팔뚝 → 주먹 쪽
gp = np.stack(np.nonzero(GUARD)[::-1], 1).astype(float); tg = (gp - c) @ ax; tc = float(np.percentile(tg, 97))
WR = c + ax * tc                             # 손목(보호대 → 장갑) 축 위 점
fore_ang = math.degrees(math.atan2(ax[1], ax[0]))
wr_ang = math.degrees(math.atan2(-(WR[1] - G[1]), -(WR[0] - G[0])))
# 자르기: 손목 선(축에 수직)보다 팔뚝 쪽 + 남은 흰 보호대 조각 + 주먹 밖 자루 토막
T = (xx - c[0]) * ax[0] + (yy - c[1]) * ax[1]
cut = A & (T < tc + 14)   # 손목 선에서 장갑 쪽으로 조금 더(보호대 아래 검은 띠 끝이 뾰족하게 남았음)
cut |= GUARD & (T < tc + 25)
stub = A & ((xx < FX0 - 6) | (xx > FX1 + 14)) & (np.abs(yy - SY) <= SW * .62)
keep = A & ~cut & ~stub
keep = cv2.morphologyEx(keep.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0   # 잘린 보호대 외곽선 실 같은 찌꺼기 지움
_op = cv2.morphologyEx(keep.astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31))) > 0; keep = np.where(T < tc + 70, _op, keep)   # 손목 선 근처 뾰족한 장갑 띠 끝 지움(큰 원으로 열기)
nk, lk, sk_, _ = cv2.connectedComponentsWithStats(keep.astype(np.uint8), 8); keep = lk == 1 + int(np.argmax(sk_[1:, cv2.CC_STAT_AREA]))
# 잘린 장갑 끝(손목 선) = 장갑 입구 외곽선: 손목 선 근처 가장자리를 원화 선 색으로(굵기 = 원화 2.4px ÷ 배율)
_d = cv2.distanceTransform(keep.astype(np.uint8), cv2.DIST_L2, 3); _lw = 2.4 / math.sqrt(36.0 * 43.6 / (float(FX1 - FX0) * 470.0))
_rim = keep & (_d <= _lw) & (T < tc + 60) & (T > tc - 5)
a[_rim] = (22, 20, 24)
# 배율: 원화 먼 주먹 손가락 줄 36 × 높이 43.6(외곽선 포함) 과 넓이 같게
FH = float(FYB - np.nonzero(keep[:, FX0:FX1 + 1].any(1))[0].min()); stack = float(FX1 - FX0)
k = math.sqrt(36.0 * 43.6 / (stack * FH)); R = 2 * k   # 리그 px
out = np.dstack([a, (keep * 255).astype(np.uint8)])
ys_, xs_ = np.nonzero(keep); bx0, by0, bx1, by1 = xs_.min() - 3, ys_.min() - 3, xs_.max() + 4, ys_.max() + 4
crop = Image.fromarray(out[by0:by1, bx0:bx1]); crop = crop.resize((max(1, round(crop.width * R)), max(1, round(crop.height * R))), Image.LANCZOS)
o = np.array([bx0, by0], float); g = (G - o) * R; wr = (WR - o) * R
os.makedirs(os.path.join(HERE, 'attack', 'pieces'), exist_ok=True); crop.save(os.path.join(HERE, 'attack', 'pieces', 'gFh.png'))
J = {'gFh': {'size': [crop.width, crop.height], 'grip': [round(float(g[0]), 1), round(float(g[1]), 1)], 'wrist': [round(float(wr[0]), 1), round(float(wr[1]), 1)], 'shaftDir': [1, 0], 'scale': 1.0,
             'note': f'tools/gfh12.py {os.path.basename(fn)} (DHL 09:12 다시 받은 21 쥔 손) — 원화 배율 {k:.4f}(손가락 줄 {stack:.0f}px·높이 {FH:.0f}px), 리그 px 로 줄여 저장. 팔뚝 축 {-fore_ang:.1f}° · 쥔 점→손목 {wr_ang:.1f}°(러스트 33°, 시트 1장 65°)'}}
json.dump(J, open(os.path.join(HERE, 'attack', 'pieces.json'), 'w'), ensure_ascii=False, indent=1)
print(f'자루 y {SY:.1f} 굵기 {SW:.0f} · 손가락 x {FX0}~{FX1} · 주먹 높이 {FH:.0f} → 원화 배율 {k:.4f} (리그 {R:.4f}) · 저장 {crop.width}x{crop.height}')
print(f'쥔 점 {G.round(1).tolist()} · 손목 {WR.round(1).tolist()} · 팔뚝 축 {-fore_ang:.1f}° · 쥔 점→손목 {wr_ang:.1f}°  (러스트 33° · 시트 1장 21칸 65°)')
v = Image.fromarray(np.dstack([a, (A * 255).astype(np.uint8)])).convert('RGBA'); bg = Image.new('RGBA', v.size, (210, 240, 210, 255)); bg.alpha_composite(v)
ov = Image.new('RGBA', v.size, (0, 0, 0, 0)); ovd = np.array(ov); ovd[cut | stub] = (255, 0, 0, 110); bg.alpha_composite(Image.fromarray(ovd)); d = ImageDraw.Draw(bg)
d.line([tuple(c - ax * 400), tuple(c + ax * 500)], fill=(0, 160, 0), width=4); d.line([tuple(G), tuple(WR)], fill=(0, 0, 255), width=4)
for p, col in [(G, (0, 0, 255)), (WR, (255, 0, 0))]: d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], outline=col, width=5)
os.makedirs(os.path.join(HERE, 'review'), exist_ok=True); bg.convert('RGB').resize((512, 512)).save(os.path.join(HERE, 'review', 'gfh_check.png')); print('→ attack/pieces/gFh.png · attack/pieces.json · review/gfh_check.png')
