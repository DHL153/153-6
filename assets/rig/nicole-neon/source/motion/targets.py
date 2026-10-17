"""동작 시트 찌르기 프레임(8~13) → 관절점 목표 (리그 단위, 땅 y=0, 위가 −, x는 두 발 가운데 기준)
발(뒤·앞), 머리 위·머리 가운데 x, 손(뒤·앞: 자루 근처 피부 덩어리), 창 각도·앞손 x에서의 창 높이"""
import json, os, numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = os.path.dirname(os.path.abspath(__file__))
K = json.load(open(os.path.join(HERE, 'keys_m1.json')))
def hsv(a):
    rgb = a[..., :3] / 255; mx = rgb.max(-1); mn = rgb.min(-1); d = np.maximum(mx - mn, 1e-6); s = (mx - mn) / np.maximum(mx, 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, s, mx
out = {}
for i in range(8, 14):
    k = K[i]; a = np.asarray(Image.open(os.path.join(HERE, 'frames', f'{i:02d}.png')).convert('RGBA')).astype(float)
    h, s, v = hsv(a); al = a[..., 3] > 128
    skin = al & (h > 12) & (h < 40) & (s > .22) & (s < .75) & (v > .6)
    lb, n = nd.label(nd.binary_opening(skin, iterations=1)); sz = nd.sum(skin, lb, range(1, n + 1)); cm = nd.center_of_mass(skin, lb, range(1, n + 1))
    p1, p2 = np.array(k['spear']['p1']), np.array(k['spear']['p2']); u = (p2 - p1) / np.linalg.norm(p2 - p1); nrm = np.array([-u[1], u[0]])
    hands = []
    for j in range(n):
        if sz[j] < 150: continue
        c = np.array([cm[j][1], cm[j][0]]); dd = abs((c - p1) @ nrm)
        if dd < 45 and c[1] > k['head']['top'] + 60: hands.append((c, sz[j]))
    hands = sorted(hands, key=lambda t: t[0][0])
    G = k['ground']; feet = sorted(k['feet']); mid = (feet[0] + feet[-1]) / 2 if len(feet) > 1 else feet[0]; R = k['toRig']
    P = lambda x, y: [round((x - mid) * R, 1), round((y - G) * R, 1)]
    ang = float(np.degrees(np.arctan2(-(p2[1] - p1[1]), p2[0] - p1[0])))
    lead = hands[-1][0] if hands else None
    sy = (p1[1] + (lead[0] - p1[0]) / u[0] * u[1]) if lead is not None and abs(u[0]) > .3 else None
    out[i] = {'feet': [P(f, G)[0] for f in feet], 'headTop': P(k['head']['cx'], k['head']['top']), 'hands': [P(*c) for c, _ in hands],
              'spearAngDeg': round(ang, 1), 'spearYatLead': P(lead[0], sy)[1] if sy is not None else None, 'n_hands': len(hands)}
json.dump(out, open(os.path.join(HERE, 'targets_thrust.json'), 'w'), indent=1); print(json.dumps(out, indent=0))
