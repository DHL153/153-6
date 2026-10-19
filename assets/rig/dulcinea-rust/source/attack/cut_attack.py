"""내려찍기 조각 자르기 (2026-10-19 13:40~): 흰 배경 시트에서 팔·쥔 손을 오려 attack/pieces/*.png + pieces.json(관절 점, 오린 그림 px)
- 팔 4(시트 4번 3줄): auN 가까운 윗팔 · afN 가까운 팔뚝 · auF 먼 윗팔 · afF 먼 팔뚝 — 시트 px × 0.8 = 리그(1·2줄 캐릭터의 2배로 그린 것, 칸 그림 1.6배)
- 쥔 손 4(시트 3번 2줄): gNv 가까운 손·자루 세로 · gNh 가까운 손·자루 가로 · gFv 먼 손·세로 · gFh 먼 손·가로 — 자루 굵기 65px = 원화 자루 22px → 리그 0.68
  자루는 주먹 밖으로 나온 부분을 지움(진짜 망치 자루가 뒤에 그려짐)"""
import json, os, numpy as np, cv2
from PIL import Image
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, '..'); OUTD = os.path.join(HERE, 'pieces'); os.makedirs(OUTD, exist_ok=True)
def unwhite(rgb, keep=None):
    """흰 배경 → 투명: 테두리와 이어진 밝은 곳 = 배경, 그 둘레 2px 은 밝기로 반투명(검은 외곽선)"""
    a = rgb.astype(np.int16); light = a.min(2) > 222
    lb, n = ndimage.label(light); border = set(np.unique(np.concatenate([lb[0], lb[-1], lb[:, 0], lb[:, -1]]))) - {0}
    bg = np.isin(lb, list(border))
    ring = cv2.dilate(bg.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool) & ~bg
    L = a.mean(2); al = np.where(bg, 0, 255).astype(np.float32)
    al[ring] = np.clip((255 - L[ring]) / (255 - 40) * 255, 0, 255)
    out = np.dstack([rgb, al.astype(np.uint8)]).astype(np.uint8)
    out[..., :3][ring] = np.clip((rgb[ring].astype(np.float32) - (1 - al[ring, None] / 255) * 255) / np.maximum(al[ring, None] / 255, .05), 0, 255).astype(np.uint8)
    return out
def crop_alpha(a, pad=3):
    ys, xs = np.nonzero(a[..., 3] > 0); y0, x0 = max(ys.min() - pad, 0), max(xs.min() - pad, 0); return a[y0:ys.max() + pad + 1, x0:xs.max() + pad + 1], np.array([x0, y0], float)
def cap_centers(m):
    """곧게 세운 팔다리: 위 둥근 끝 원 가운데 · 아래 둥근 끝 원 가운데 (가로 폭의 절반만큼 안쪽)"""
    ys = np.nonzero(m.any(1))[0]; y0, y1 = ys.min(), ys.max(); H = y1 - y0
    def row(y): xs = np.nonzero(m[int(y)])[0]; return xs.min(), xs.max()
    a0, b0 = row(y0 + H * .22); a1, b1 = row(y1 - H * .22)
    r0, r1 = (b0 - a0) / 2, (b1 - a1) / 2
    return [float((a0 + b0) / 2), float(y0 + r0)], [float((a1 + b1) / 2), float(y1 - r1)], r0, r1
J = {}
# ---- 팔 (시트 4번 3줄) ----
S4 = np.array(Image.open(os.path.join(SRC, 'sheets', 'attack_v2.png')).convert('RGB'))
LIMB = {'auN': (206, 2467, 306, 2633), 'afN': (732, 2466, 805, 2633), 'auF': (1227, 2466, 1333, 2633), 'afF': (1757, 2467, 1825, 2633)}
for n, (x0, y0, x1, y1) in LIMB.items():
    c = unwhite(S4[y0 - 12:y1 + 12, x0 - 12:x1 + 12]); c, o = crop_alpha(c); m = c[..., 3] > 128
    top, bot, r0, r1 = cap_centers(m)
    if n.startswith('af'):   # 팔뚝: 위 = 팔꿈치 둥근 끝, 아래 = 손목 붕대(붕대 띠 가운데 — 크림색 줄의 가운데)
        hsv = cv2.cvtColor(c[..., :3], cv2.COLOR_RGB2HSV); band = m & (hsv[..., 1] < 70) & (hsv[..., 2] > 150); bys = np.nonzero(band.any(1))[0]
        bot = [float(np.nonzero(m[int(np.median(bys))])[0].mean()), float(np.median(bys))]
    # (임시, 10-19 13:55) 받은 팔 조각은 동작 8장면 속 팔보다 짧음 → 새 팔 시트(ref_G, 윗팔 키의 0.16·팔뚝 0.15) 오기 전까지 길이만 늘인 자리표시 — 새 조각 오면 TEMP 지움
    TEMP = {'auN': 140, 'auF': 140, 'afN': 130, 'afF': 130}   # 원하는 관절 길이(리그)
    if n in TEMP:
        sy = TEMP[n] / (np.hypot(bot[0] - top[0], bot[1] - top[1]) * .8); c = np.array(Image.fromarray(c).resize((c.shape[1], int(round(c.shape[0] * sy))), Image.LANCZOS))
        top = [top[0], top[1] * sy]; bot = [bot[0], bot[1] * sy]
    Image.fromarray(c).save(os.path.join(OUTD, n + '.png'))
    J[n] = dict(size=[c.shape[1], c.shape[0]], top=top, bot=bot, r=[r0, r1], scale=0.8, temp=n in TEMP)
    print(n, c.shape[1], c.shape[0], 'top', np.round(top, 1), 'bot', np.round(bot, 1), 'len rig', round(float(np.hypot(bot[0] - top[0], bot[1] - top[1])) * .8, 1))
# ---- 쥔 손 (시트 3번 2줄) ----
S3 = np.array(Image.open(os.path.join(SRC, 'sheets', 'attack_v1.png')).convert('RGB'))
K = 44.0 / 65.5   # 리그 px / 칸 px (자루 굵기)
GRIP = {   # 칸 상자, 자루 축(가로/세로) 가운데, 주먹이 자루를 덮는 범위(축 방향), 손목 점(붕대 가운데), 머리 쪽(자루 방향)
    'gNv': dict(box=(10, 555, 250, 830), ax='v', c=169.5, keep=(604, 760), wrist=(62, 690), head=(0, -1)),
    'gNh': dict(box=(290, 600, 620, 780), ax='h', c=670.0, keep=(0, 497), wrist=(345, 678), head=(1, 0), gpos=448),
    'gFv': dict(box=(660, 555, 862, 830), ax='v', c=734.5, keep=(622, 768), wrist=(812, 712), head=(0, -1)),
    'gFh': dict(box=(876, 625, 1145, 772), ax='h', c=695.0, keep=(938, 1082), wrist=(960, 662), head=(1, 0)),
}
for n, g in GRIP.items():
    x0, y0, x1, y1 = g['box']; c = unwhite(S3[y0:y1, x0:x1]); yy, xx = np.mgrid[y0:y1, x0:x1]
    if g['ax'] == 'v': band = (np.abs(xx - g['c']) <= 36) & ((yy < g['keep'][0]) | (yy > g['keep'][1]))
    else: band = (np.abs(yy - g['c']) <= 36) & ((xx < g['keep'][0]) | (xx > g['keep'][1]))
    c[..., 3][band] = 0
    lb, k = ndimage.label(c[..., 3] > 0); sz = ndimage.sum(c[..., 3] > 0, lb, range(1, k + 1)); c[..., 3][~np.isin(lb, 1 + np.nonzero(sz >= sz.max() * .2)[0])] = 0   # 떨어진 자루 조각 지움
    c, o = crop_alpha(c); o = o + np.array([x0, y0])
    gp = g.get('gpos', (g['keep'][0] + g['keep'][1]) / 2)   # 주먹 가운데(자루 축 위)
    grip = [g['c'], gp] if g['ax'] == 'v' else [gp, g['c']]
    J[n] = dict(size=[c.shape[1], c.shape[0]], grip=[float(grip[0] - o[0]), float(grip[1] - o[1])], wrist=[float(g['wrist'][0] - o[0]), float(g['wrist'][1] - o[1])], shaftDir=list(g['head']), scale=round(K, 4))
    Image.fromarray(c).save(os.path.join(OUTD, n + '.png'))
    print(n, c.shape[1], c.shape[0], 'grip', np.round(J[n]['grip'], 1), 'wrist', np.round(J[n]['wrist'], 1), 'grip→wrist rig', round(float(np.hypot(*(np.array(J[n]['wrist']) - J[n]['grip']))) * K, 1))
json.dump(J, open(os.path.join(HERE, 'pieces.json'), 'w'), indent=1)
