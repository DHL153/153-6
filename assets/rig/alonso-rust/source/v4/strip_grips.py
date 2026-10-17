"""쥔 손 조각에서 주먹 밖으로 나온 손잡이 토막(잘린 끝 쇠마개·폼멜)을 지움.
축 = 회색 쇠마개 두 덩어리의 중심을 잇는 선(폼멜이 안 보이면 주어진 방향). 토막 반 굵기는 주먹 밖 구간에서 실측.
지우는 곳 = 축에서 반 굵기+잉크 안쪽 띠 중, 주먹 바깥 끝(t0 이전 / t1 이후). 띠 안에 남는 토막은 게임 칼 손잡이(더 굵음) 위에 겹쳐 안 보임.
실행: cd v4 && python3 -I strip_grips.py → work/<name>_s.png + work/grips.json"""
import json, numpy as np
from PIL import Image
from scipy import ndimage as nd
G = {  # name: 쇠마개 추정점 C, 폼멜 추정점 P(None=방향 dir), 주먹 구간 [t0,t1](C에서), 팔꿈치
 'gN49': ((36, 15), (145, 140), None, (42, 140), (95, 300), 17),
 'gF34': ((22, 25), (178, 138), None, (52, 168), (95, 300), 18),
 'gF46': ((25, 22), (135, 148), None, (50, 142), (65, 305), 17),
 'gN90': ((170, 20), None, (0, 1), (168, 9999), (190, 930), 58),
}
out = {}
for n, (Cg, Pg, dirg, (t0, t1), E, hfix) in G.items():
    a = np.asarray(Image.open(f'work/{n}.png').convert('RGBA')).copy(); H, W = a.shape[:2]
    rgb = a[..., :3].astype(float); mx = rgb.max(-1); mn = rgb.min(-1); al = a[..., 3] > 128
    grey = al & ((mx - mn) < 28) & (mx > 120)
    lab, k = nd.label(grey); cs = nd.center_of_mass(grey, lab, range(1, k + 1)); sz = nd.sum(grey, lab, range(1, k + 1))
    def near(p):
        best = min((np.hypot(c[1] - p[0], c[0] - p[1]), i) for i, c in enumerate(cs) if sz[i] > 30); c = cs[best[1]]; return np.array([c[1], c[0]])
    C = near(Cg); u = (near(Pg) - C) if Pg else np.array(dirg, float); u /= np.linalg.norm(u)
    yy, xx = np.mgrid[0:H, 0:W]; t = (xx - C[0]) * u[0] + (yy - C[1]) * u[1]; nv = (xx - C[0]) * (-u[1]) + (yy - C[1]) * u[0]
    # 토막 반 굵기: 주먹 앞(t < t0-6) 구간에서 축 수직 방향 불투명 폭
    sel = al & (t > 6) & (t < t0 - 24); half = float(np.percentile(np.abs(nv[sel]), 97)) if sel.sum() > 20 else 16
    h = hfix
    k_ = np.where(np.abs(nv) < h, 1 - np.clip(np.maximum(t0 - t, t - t1) / 2.5, 0, 1), 1)
    a[..., 3] = (a[..., 3] * k_).astype(np.uint8)
    # 띠 바깥에 남은 토막 테두리 선(얇은 선)은 띠를 넓힌 구역 안에서만 열기(opening)로 지움
    zone = (np.abs(nv) < h + 16) & ((t < t0 + 4) | (t > t1 - 4))
    op = nd.binary_opening(a[..., 3] > 60, structure=np.ones((7, 7)))
    a[..., 3] = np.where(zone & ~op, 0, a[..., 3])
    lab2, n2 = nd.label(a[..., 3] > 20); s2 = nd.sum(a[..., 3] > 20, lab2, range(1, n2 + 1)); big = np.argmax(s2) + 1
    a[..., 3] = np.where(nd.binary_dilation(lab2 == big, iterations=1), a[..., 3], 0)
    Image.fromarray(a, 'RGBA').save(f'work/{n}_s.png')
    tm = (t0 + t1) / 2 if t1 < 5000 else t0 + 138
    g = C + u * tm
    out[n] = {'grip': [round(float(g[0]), 1), round(float(g[1]), 1)], 'shaftDir': [round(float(-u[0]), 4), round(float(-u[1]), 4)], 'elbow': list(E),
              'forearm': round(float(np.hypot(*(np.array(E) - g))), 1), 'stubHalf': round(half, 1), 'axisDeg': round(float(np.degrees(np.arctan2(-u[1], -u[0]))), 1)}
json.dump(out, open('work/grips.json', 'w'), indent=1)
for n, o in out.items(): print(n, o)
