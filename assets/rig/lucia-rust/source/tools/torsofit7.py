# 7 루시아: 시트 13칸 상체를 원화 상체(보이는 곳, 목도리 포함)에 맞춤 — 배율·회전·이동 격자 탐색(색 차이 + 안 덮인 비율) → torso_fit7.json
import numpy as np, cv2, json, math, os, sys
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RA = np.array(Image.open(os.path.join(HERE, 'ref512.png')).convert('RGBA')).astype(np.float32)
lab = np.load(os.path.join(HERE, 'work', 'labels.npy')); NM = json.load(open(os.path.join(HERE, 'work', 'label_names.json')))
tor = (lab == NM.index('body') + 1) & (RA[..., 3] > 200); tor = cv2.erode(tor.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
a = np.array(Image.open(os.path.join(HERE, 'pieces', 'torso.png')).convert('RGBA')).astype(np.int16); m = np.clip(np.minimum(a[..., 0], a[..., 2]) - a[..., 1], 0, None); a[..., 0] -= m; a[..., 2] -= m; a = np.clip(a, 0, 255).astype(np.float32)
h, w = a.shape[:2]
def score(s, r, tx, ty):
    M = cv2.getRotationMatrix2D((w / 2, h / 2), r, s); M[0, 2] += tx; M[1, 2] += ty
    wp = cv2.warpAffine(a, M, (512, 512)); ov = tor & (wp[..., 3] > 200)
    if ov.sum() < 1500: return 1e9, M
    return float(np.abs(wp[..., :3][ov] - RA[..., :3][ov]).mean() + (tor.sum() - ov.sum()) / tor.sum() * 60), M
best = None
for s in np.arange(1.0, 1.45, .05):
    for r in np.arange(-16, 6.1, 2):
        for tx in range(190, 260, 4):
            for ty in range(230, 300, 4):
                d, M = score(s, r, tx, ty)
                if best is None or d < best[0]: best = (d, s, r, tx, ty)
d, s, r, tx, ty = best
for s2 in np.arange(s - .04, s + .041, .01):   # 다듬기
    for r2 in np.arange(r - 2, r + 2.1, .5):
        for tx2 in range(tx - 4, tx + 5):
            for ty2 in range(ty - 4, ty + 5):
                d2, M = score(s2, r2, tx2, ty2)
                if d2 < best[0]: best = (d2, s2, r2, tx2, ty2)
d, s, r, tx, ty = best; _, M = score(s, r, tx, ty)
print(f'torso fit: 차이 {d:.1f} · 배율 {s:.3f} · 회전 {r:.1f}° · 이동 {tx},{ty}')
json.dump({'M': M.tolist(), 'scale': s, 'rot': r, 'err': d}, open(os.path.join(HERE, 'torso_fit7.json'), 'w'))
wp = cv2.warpAffine(a, M, (512, 512)); out = Image.new('RGBA', (512, 512), (255, 255, 255, 255)); out.alpha_composite(Image.fromarray(RA.astype(np.uint8)))
ov = wp.copy(); ov[..., 3] *= .6; out.alpha_composite(Image.fromarray(ov.astype(np.uint8))); out.crop((180, 220, 400, 380)).resize((660, 480)).save(os.path.join(HERE, 'review', 'torso_fit.png'))
