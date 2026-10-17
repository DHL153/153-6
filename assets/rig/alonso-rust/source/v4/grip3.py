"""쥔 팔 시트 3(sheetGRIP3_v4) → 머리 위·내려찍기 쥔 팔뚝 4조각.
축 = 회색 쇠마개 두 덩어리 중심을 잇는 선, 주먹 구간 = 축 밖으로 넓게 불투명한 구간, 그 밖의 손잡이 토막은 지움.
팔꿈치 = 피부색 둥근 끝 덩어리 중심. 크기 = 팔꿈치→손잡이 136 리그 단위(기존 쥔 손과 같은 팔뚝 길이).
실행: cd v4 && python3 -I grip3.py → work/<name>_s.png + work/grips3.json"""
import json, numpy as np
from PIL import Image
from scipy import ndimage as nd
# 이름: (조각 파일, 칼날 쪽 = 축의 어느 끝: 'left'/'right'/'down-right')
# 이름: (조각, 쇠마개 추정점 두 개(칼날 쪽 먼저), 팔꿈치 추정점) — 조각 안 px, 시트 그림을 보고 찍은 값(근처 회색 덩어리 중심으로 다듬음)
J = {'gNup': ('k01', (24, 55), (354, 55), (189, 480)), 'gFup': ('../grip3b/j01', (39, 126), (559, 126), (689, 701)),   # 13:17 재요청분(11시 방향) — 12:59 k02는 1시라 교체
     'gNdn': ('k03', (513, 408), (238, 323), (58, 58)), 'gFdn': ('k04', (448, 505), (178, 360), (68, 65))}
FIST = {'gNup': (79, 259), 'gFup': (115, 395), 'gNdn': (18, 235), 'gFdn': (42, 232)}
CLEAR = {'gNup': 'both', 'gFup': 'both', 'gNdn': 'blade', 'gFdn': 'blade'}   # 주먹 밖 띠를 통째로 지울 쪽(팔뚝과 겹치지 않는 쪽만)   # 주먹 구간(폼멜 쪽 쇠마개에서 축 따라 px) — 그림 보고 정함
FORE = 136.0
out = {}
for n, (f, cB, cP, eG) in J.items():
    a = np.asarray(Image.open(f'pieces/grip3/{f}.png').convert('RGBA')).copy(); H, W = a.shape[:2]
    rgb = a[..., :3].astype(float); mx = rgb.max(-1); mn = rgb.min(-1); al = a[..., 3] > 128
    grey = al & ((mx - mn) < 26) & (mx > 140)
    lab, k = nd.label(grey); sz = nd.sum(grey, lab, range(1, k + 1)); cs = nd.center_of_mass(grey, lab, range(1, k + 1))
    def near(q):
        c = min(((np.hypot(c_[1] - q[0], c_[0] - q[1]), c_) for c_, s_ in zip(cs, sz) if s_ > 40), key=lambda z: z[0])
        return np.array([c[1][1], c[1][0]]) if c[0] < 30 else np.array(q, float)
    C1, C0 = near(cB), near(cP)   # C1 = 칼날 쪽 끝, C0 = 폼멜 쪽 끝
    u = (C1 - C0) / np.linalg.norm(C1 - C0); L = float(np.linalg.norm(C1 - C0))
    yy, xx = np.mgrid[0:H, 0:W]; t = (xx - C0[0]) * u[0] + (yy - C0[1]) * u[1]; nv = (xx - C0[0]) * (-u[1]) + (yy - C0[1]) * u[0]
    # 토막 반 굵기: 쇠마개 바로 안쪽(축 위 8~20px)에서 축 수직 불투명 폭
    seg = al & (((t > L - 30) & (t < L - 12)) | ((t > 12) & (t < 30))); half = float(min(np.percentile(np.abs(nv[(al & (t > L - 30) & (t < L - 12))]), 95), np.percentile(np.abs(nv[(al & (t > 12) & (t < 30))]), 95)))
    # 주먹 구간: 축에서 half+6 ~ half+60 떨어진 곳에 불투명이 많은 t 구간
    ts = np.arange(0, int(L) + 1); occ = np.array([((al) & (np.abs(t - x) < 1.5) & (np.abs(nv) > half + 6) & (np.abs(nv) < half + 70)).sum() for x in ts])
    t0, t1 = FIST[n]
    h = half + 3
    k_ = np.where(np.abs(nv) < h, 1 - np.clip(np.maximum(t0 - t, t - t1) / 2.5, 0, 1), 1)
    a[..., 3] = (a[..., 3] * k_).astype(np.uint8)
    zone = (np.abs(nv) < h + 14) & ((t < t0 + 3) | (t > t1 - 3))
    op = nd.binary_opening(a[..., 3] > 60, structure=np.ones((7, 7)))
    a[..., 3] = np.where(zone & ~op, 0, a[..., 3])
    cz = (np.abs(nv) < h + 14) & ((t > t1 + 2) | ((t < t0 - 2) if CLEAR[n] == 'both' else False))
    a[..., 3] = np.where(cz, 0, a[..., 3])
    lab2, n2 = nd.label(a[..., 3] > 20); s2 = nd.sum(a[..., 3] > 20, lab2, range(1, n2 + 1)); big = np.argmax(s2) + 1
    a[..., 3] = np.where(nd.binary_dilation(lab2 == big, iterations=1), a[..., 3], 0)
    g = C0 + u * (t0 + t1) / 2
    # 팔꿈치: 피부색(밝은 살구) 덩어리 중 손잡이에서 가장 먼 것의 중심
    r, gg, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    skin = al & (r > 220) & (gg > 160) & (gg < 225) & (b > 100) & (b < 190)
    lab3, k3 = nd.label(skin); l3 = lab3[int(eG[1]), int(eG[0])]
    E = np.array(nd.center_of_mass(skin, lab3, l3))[::-1] if l3 else np.array(eG, float)
    Image.fromarray(a, 'RGBA').save(f'work/{n}_s.png')
    fl = float(np.linalg.norm(E - g))
    out[n] = {'grip': [round(float(g[0]), 1), round(float(g[1]), 1)], 'shaftDir': [round(float(u[0]), 4), round(float(u[1]), 4)], 'elbow': [round(float(E[0]), 1), round(float(E[1]), 1)],
              'forearm': round(fl, 1), 'scale': round(FORE / fl, 4), 'fist': [t0, t1], 'stubHalf': round(half, 1)}
    print(n, out[n])
json.dump(out, open('work/grips3.json', 'w'), indent=1)
