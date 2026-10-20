# 7 루시아: 시트 19칸 '자루 따라 쥔 손'(gFh, 86×51 작은 조각) → attack/pieces/gFh.png + attack/pieces.json   (10-20 21:3x, 22 gfh22.py 를 루시아 손으로 고침)
#   python3 -I tools/gfh7.py [pieces/gFh.png] [배율 K]
#   22 와 다른 점: 루시아 팔뚝 = 살 + 갈색 손목 띠(원화 팔뚝 조각 afFart 에 띠가 있음) → 시트 19 는 띠·살을 손 경계에서 잘라 손만 씀
#   ①자홍 테두리 빼기 ②자루 = 오른쪽 끝 세로줄 가운데·굵기 ③쥔 점 = 손가락(자루 아래 살색) x 가운데 × 자루 가운데 y
#   ④팔뚝 축 = 쥔 점 왼쪽 위 팔뚝(살 + 갈색 띠) 주성분 → 손목 = 띠가 손으로 바뀌는 곳(띠 갈색의 축 위 97%) ⑤띠·살은 그 선(축에 수직)에서 잘라 냄
#   ⑥자루 토막(주먹 밖)은 지움 — 실제 도끼 자루가 뒤에 그려짐 ⑦배율 K(시트 → 원화, 22 는 1.38) → 리그 px(×2)로 늘려 저장(scale 1)
#   엔진 규칙(러스트·12·22 gFh 와 같음): grip = wrist = elbow = 쥔 점(공 손목), foreDir = 쥔 점 → 손목 방향
import os, sys, json, math
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fn = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'pieces', 'gFh.png')
k = float(sys.argv[2]) if len(sys.argv) > 2 else float(os.environ.get('GFH_K', 1.3))
src = np.array(Image.open(fn).convert('RGBA')).astype(np.int16)
m_ = np.clip(np.minimum(src[..., 0], src[..., 2]) - src[..., 1], 0, None); src[..., 0] -= m_; src[..., 2] -= m_
a = np.clip(src[..., :3], 0, 255).astype(np.uint8); A0 = src[..., 3] > 128; H_, W_ = A0.shape
n_, lb, st, _ = cv2.connectedComponentsWithStats(A0.astype(np.uint8), 8); A = lb == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
yy, xx = np.mgrid[0:H_, 0:W_]
hsv = cv2.cvtColor(a, cv2.COLOR_RGB2HSV); SK = A & (hsv[..., 0] >= 5) & (hsv[..., 0] <= 25) & (hsv[..., 1] > 70) & (hsv[..., 2] > 170)
BR = A & (hsv[..., 0] >= 3) & (hsv[..., 0] <= 22) & (hsv[..., 1] > 90) & (hsv[..., 2] > 50) & (hsv[..., 2] <= 170)   # 갈색(띠·자루)
xs = np.nonzero(A.any(0))[0]; x0, x1 = xs.min(), xs.max()
edge = list(range(x1 - 9, x1 + 1))
SY = float(np.median([np.nonzero(A[:, c])[0].mean() for c in edge])); SW = float(np.median([A[:, c].sum() for c in edge]))
FG = SK & (yy > SY + SW * .15); fx = np.nonzero(FG.any(0))[0]; FX0, FX1 = int(fx.min()), int(fx.max())
G = np.array([(FX0 + FX1) / 2.0, SY])
FA = (SK | BR) & (yy < SY - SW * .45) & (xx < FX0 + 4)          # 팔뚝(살 + 띠) — 자루 위, 손가락 왼쪽
pts = np.stack(np.nonzero(FA)[::-1], 1).astype(float); c = pts.mean(0); w, v = np.linalg.eigh(np.cov((pts - c).T)); ax = v[:, 1]
if ax[0] < 0: ax = -ax                                          # 손 쪽(오른쪽 아래)
T = (xx - c[0]) * ax[0] + (yy - c[1]) * ax[1]
band = BR & FA; tc = float(np.percentile(T[band], 97))
WR = c + ax * tc
fore_ang = math.degrees(math.atan2(-ax[1], ax[0]))
cut = A & (T < tc + .5) & (yy < SY - SW * .45 + 2)                 # 띠·살(손목 선 위쪽)
stub = A & ((xx < FX0 - 3) | (xx > FX1 + 3)) & (yy >= SY - SW / 2 - .5) & (yy <= SY + SW / 2 + 1.5)
keep = A & ~cut & ~stub
nk, lk, sk_, _ = cv2.connectedComponentsWithStats(keep.astype(np.uint8), 8); keep = lk == 1 + int(np.argmax(sk_[1:, cv2.CC_STAT_AREA]))
R = 2 * k
_d = cv2.distanceTransform(keep.astype(np.uint8), cv2.DIST_L2, 3); _lw = max(1.0, 2.4 / k)
_cutz = cv2.dilate((cut | stub).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
a = a.copy(); a[keep & (_d <= _lw) & _cutz] = (22, 20, 24)      # 잘린 면 = 외곽선
out = np.dstack([a, (keep * 255).astype(np.uint8)])
ys_, xs_ = np.nonzero(keep); bx0, by0, bx1, by1 = xs_.min() - 2, ys_.min() - 2, xs_.max() + 3, ys_.max() + 3
bx0, by0 = max(0, bx0), max(0, by0)
crop = Image.fromarray(out[by0:by1, bx0:bx1])
crop = crop.resize((max(1, round(crop.width * R)), max(1, round(crop.height * R))), Image.LANCZOS)
o = np.array([bx0, by0], float); g = (G - o) * R; wr = (WR - o) * R
os.makedirs(os.path.join(HERE, 'attack', 'pieces'), exist_ok=True); crop.save(os.path.join(HERE, 'attack', 'pieces', 'gFh.png'))
wr_ang = math.degrees(math.atan2(-(WR[1] - G[1]), -(WR[0] - G[0])))
J = {'gFh': {'size': [crop.width, crop.height], 'grip': [round(float(g[0]), 1), round(float(g[1]), 1)], 'wrist': [round(float(wr[0]), 1), round(float(wr[1]), 1)], 'shaftDir': [1, 0], 'scale': 1.0,
             'note': f'tools/gfh7.py {os.path.basename(fn)} (시트 19칸) — 원화 배율 {k:.3f}(손가락 줄 {FX1 - FX0 + 1}px), 리그 px 로 늘려 저장. 팔뚝 축 {fore_ang:.1f}° · 쥔 점→손목 {wr_ang:.1f}°'}}
json.dump(J, open(os.path.join(HERE, 'attack', 'pieces.json'), 'w'), ensure_ascii=False, indent=1)
print(f'자루 y {SY:.1f} 굵기 {SW:.0f}(원화 배율이면 {SW * k:.1f}, 원화 자루 약 24) · 손가락 x {FX0}~{FX1} · 배율 {k:.3f} → 저장 {crop.width}x{crop.height}')
print(f'쥔 점 {G.round(1).tolist()} · 손목 {WR.round(1).tolist()} · 팔뚝 축 {fore_ang:.1f}° · 쥔 점→손목 {wr_ang:.1f}° (foreDir−sa = {-(180 - wr_ang):.1f}°)')
S = 8; vv = Image.fromarray(np.dstack([a, (A * 255).astype(np.uint8)])).convert('RGBA'); bg = Image.new('RGBA', vv.size, (210, 240, 210, 255)); bg.alpha_composite(vv)
ovd = np.zeros((H_, W_, 4), np.uint8); ovd[(cut | stub) & A] = (255, 0, 0, 120); bg.alpha_composite(Image.fromarray(ovd)); bg = bg.resize((W_ * S, H_ * S), Image.NEAREST); d = ImageDraw.Draw(bg)
d.line([tuple((c - ax * 30) * S), tuple((c + ax * 40) * S)], fill=(0, 160, 0), width=2); d.line([tuple(G * S), tuple(WR * S)], fill=(0, 0, 255), width=2)
for p, col in [(G, (0, 0, 255)), (WR, (255, 0, 0))]: d.ellipse([p[0] * S - 6, p[1] * S - 6, p[0] * S + 6, p[1] * S + 6], outline=col, width=3)
can = Image.new('RGBA', (bg.width + crop.width + 30, max(bg.height, crop.height) + 10), (210, 240, 210, 255)); can.alpha_composite(bg, (0, 0)); can.alpha_composite(crop, (bg.width + 20, 0))
os.makedirs(os.path.join(HERE, 'review'), exist_ok=True); can.convert('RGB').save(os.path.join(HERE, 'review', 'gfh_check.png')); print('→ attack/pieces/gFh.png · attack/pieces.json · review/gfh_check.png')
