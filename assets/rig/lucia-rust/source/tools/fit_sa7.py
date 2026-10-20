# 자세(gx gy lean hipX hipY)·쥔 손(art|gFh)이 정해졌을 때 자루 각별 손목 꺾임·날 아래·꼭대기 — 돌아옴 키 자루 각 고르기
#   python3 -I tools/fit_sa7.py gx gy lean hx hy fist [sa_from sa_to step]
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
J = json.load(open(os.path.join(SRC, 'joints7.json'))); O = np.array(J['O'], float); rig = lambda a: (np.array(a, float) - O) * 2
HIP, S0, E0, W0, G0 = (rig(J[k]) for k in ('HIP', 'SH_F', 'EL_F', 'WR_F', 'G'))
L1, L2 = float(np.linalg.norm(E0 - S0)), float(np.linalg.norm(W0 - E0)); WG = float(np.linalg.norm(W0 - G0))
SA0 = math.radians(J['AXE']['shaft_deg']); BODY = (J['feet'] - J['helmet_top']) * 2
FD = {'art': math.radians(-100.3), 'gFh': math.radians(-146.6)}
R = lambda a: np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
ang = lambda v: math.atan2(v[1], v[0]); cr = lambda a, b: float(a[0] * b[1] - a[1] * b[0])
adiff = lambda a, b: (a - b + math.pi) % (2 * math.pi) - math.pi
side0 = np.sign(cr(W0 - S0, E0 - S0)); BEND0 = math.degrees(adiff(ang(E0 - W0), ang(W0 - G0))); BH = {'art': BEND0, 'gFh': -32.0}
lab = np.load(os.path.join(SRC, 'work', 'labels.npy')); NM = json.load(open(os.path.join(SRC, 'work', 'label_names.json')))
ys, xs = np.nonzero(lab == NM.index('axe') + 1); AX = (np.stack([xs, ys], 1).astype(float) - O) * 2; AX = AX[np.linspace(0, len(AX) - 1, 3000).astype(int)]
gx, gy, lean, hx, hy = map(float, sys.argv[1:6]); fist = sys.argv[6]
a0, a1, st = (map(int, sys.argv[7:10]) if len(sys.argv) > 9 else (-160, 30, 5))
hipL = HIP + np.array([hx, hy]); S = hipL + R(math.radians(lean)) @ (S0 - HIP); G = hipL + np.array([gx, gy])
for sad in range(a0, a1 + 1, st):
    sa = math.radians(sad); fd = sa + FD[fist]; Wp = G + np.array([math.cos(fd), math.sin(fd)]) * WG; d = float(np.linalg.norm(Wp - S))
    if d >= L1 + L2: print(f'  sa {sad:+4d}° 팔 늘어남 {d / (L1 + L2):.2f}'); continue
    a = (L1 * L1 - L2 * L2 + d * d) / (2 * d); h = math.sqrt(max(0, L1 * L1 - a * a)); m = S + (Wp - S) * a / d; n = np.array([-(Wp - S)[1], (Wp - S)[0]]) / d
    E1, E2 = m + n * h, m - n * h; E = E1 if np.sign(cr(Wp - S, E1 - S)) == side0 else E2
    bend = math.degrees(adiff(ang(E - Wp), fd)) - BH[fist]
    AXt = (AX - G0) @ R(sa - SA0).T + G
    ok = abs(bend) <= (35 if fist == 'art' else 25) and AXt[:, 1].max() <= 0
    print(f"  sa {sad:+4d}° 펴짐 {d / (L1 + L2):.2f} 손목 {bend:+5.0f}° 날아래 {AXt[:, 1].max():+5.0f} 꼭대기 ×{-AXt[:, 1].min() / BODY:.2f} {'○' if ok else ''}")
