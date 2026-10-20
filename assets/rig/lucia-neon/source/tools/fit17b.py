"""17 네온 루시아 — 방패 자리 다시(10-21 08:13 DHL '방패든 것이 이상한데요' — 새 원화 0번 첫 그림)
  원인: fit17 이 네온 방패(폭 144, 러스트 231 보다 좁음)를 러스트 방패 '가로 가운데'에 놓아 방패 오른쪽 끝이 x 208 —
        몸(x 210~)과 겹치지 않고 옆에 선 벽처럼, 가까운 팔·주먹·다리가 다 보이며 방패 모서리를 옆에서 잡은 꼴.
        러스트는 방패가 몸 왼쪽 절반을 가리고(오른쪽 끝 y 220 → 245 · y 300 → 226 · y 440 → 168, 위 끝이 몸 쪽으로 기욺) 주먹은 그 아래쪽 가장자리에서 감아 쥠
  고침: 네온 방패 ×1.046 을 시계 방향 TILT° 기울이고, 오른쪽 끝(가운데 높이) = 러스트 방패 오른쪽 끝(y 300 → x 226), 아래 끝 = 러스트 459
  출력: ../refs/ref_weapon_fit17b.png(러스트 자세 위) · ../refs/ref_shield_move17.png(첨부 2 — 08:13 그림에서 방패만 옮긴 가이드) · 숫자
실행: python3 -I fit17b.py [TILT]
"""
import json, math, os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); REPO = os.path.abspath(os.path.join(SRC, '..', '..', '..', '..'))
TILT = float(sys.argv[1]) if len(sys.argv) > 1 else 12.0
NEON = np.array(Image.open(os.path.join(SRC, 'refs', 'ref_design_char0017.png')).convert('RGBA')).astype(np.float32)
NEW0 = np.array(Image.open(os.path.join(SRC, 'refs', 'ref_dhl_0813_new0.png')).convert('RGBA')).astype(np.float32)
RUST = np.array(Image.open(os.path.join(SRC, 'refs', 'ref_pose_char0007.png')).convert('RGBA')).astype(np.float32)
RS = os.path.join(REPO, 'assets', 'rig', 'lucia-rust', 'source')
LAB = np.load(os.path.join(RS, 'work', 'labels.npy')); NAMES = json.load(open(os.path.join(RS, 'work', 'label_names.json')))
lab = lambda *ns: np.logical_or.reduce([LAB == NAMES.index(n) + 1 for n in ns])
YY, XX = np.mgrid[0:512, 0:512]
shield = (NEON[..., 3] > 60) & (XX >= 352) & (YY >= 195) & ~((XX < 365) & (YY > 430))
SH = NEON.copy(); SH[~shield] = 0; SH[shield & (XX <= 354)] = [18, 18, 20, 255]
K = 1.046; c = (424.0, 352.0)                                  # 네온 방패 가운데쯤
M = cv2.getRotationMatrix2D(c, -TILT, K)                       # cv2: + = 반시계 → −TILT = 시계(위 끝이 오른쪽)
def warp(M): return cv2.warpAffine(SH, M, (512, 512), flags=cv2.INTER_AREA, borderValue=(0, 0, 0, 0))
for it in range(4):   # 아래 끝 = 459 · y 300 의 오른쪽 끝 = 226 (러스트 방패 오른쪽 끝) — 몇 번 되풀이해 맞춤
    w = warp(M); a = w[..., 3] > 60; ys, xs = np.nonzero(a)
    dy = 459 - ys.max(); dx = 226 - np.nonzero(a[300 - int(round(dy))])[0].max() if a[300 - int(round(dy))].any() else 0
    M[:, 2] += [dx, dy]
w = warp(M); a = w[..., 3] > 60; ys, xs = np.nonzero(a)
print(f'기울기 {TILT}° · 방패 상자 x {xs.min()}–{xs.max()} · y {ys.min()}–{ys.max()}')
for y in (220, 300, 340, 400, 440):
    r = np.nonzero(a[y])[0]; rr = np.nonzero(lab('shield')[y])[0]
    print(f'  y {y}: 네온 방패 x {r.min()}–{r.max()}  · 러스트 방패 x {rr.min()}–{rr.max()}')
def over(dst, src):
    al = src[..., 3:4] / 255.0; o = dst.copy(); o[..., :3] = src[..., :3] * al + dst[..., :3] * (1 - al); o[..., 3:4] = np.maximum(dst[..., 3:4], src[..., 3:4]); return o
f = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc', 30)
def save(img, name, l1, l2, mark=None):
    W = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); W.alpha_composite(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)))
    W = W.convert('RGB').resize((1024, 1024), Image.LANCZOS); d0 = ImageDraw.Draw(W)
    if mark: d0.ellipse([mark[0] * 2 - mark[2] * 2, mark[1] * 2 - mark[2] * 2, mark[0] * 2 + mark[2] * 2, mark[1] * 2 + mark[2] * 2], outline=(230, 0, 0), width=5)
    BH = 112; out = Image.new('RGB', (1024, 1024 + BH), (255, 255, 255)); out.paste(W, (0, BH)); d = ImageDraw.Draw(out)
    d.text((20, 14), l1, fill=(170, 0, 0), font=f); d.text((20, 56), l2, fill=(30, 30, 30), font=f)
    d.line([(0, BH - 2), (1024, BH - 2)], fill=(200, 200, 200), width=2); out.save(os.path.join(SRC, 'refs', name)); print('저장', name)
# 1) 러스트 자세 위
ghost = RUST.copy(); ghost[lab('axe', 'shield', 'handN')] = 0; ghost[..., 3] *= .30
save(over(ghost, w), 'ref_weapon_fit17b.png', '방패 = 몸 왼쪽 절반을 가림 (위 끝이 몸 쪽으로 기욺)', '흐린 그림 = 러스트 자세 참고')
# 2) 08:13 그림에서 방패만 옮긴 가이드: 옛 방패(x < 206) 지우고 새 자리 방패
g = NEW0.copy(); old = (g[..., 3] > 0) & (XX < 206) & (YY >= 125) & (YY <= 458); g[old] = 0
hand = (int(round(np.nonzero(a[338])[0].max())) + 6, 338, 17)
save(over(g, w), 'ref_shield_move17.png', '방패만 이 자리·기울기로 (나머지는 첨부 1 그대로)', '빨간 원 = 가까운 주먹이 방패 오른쪽 가장자리를 감아 쥐는 곳', mark=hand)
print('주먹 표시', hand)
