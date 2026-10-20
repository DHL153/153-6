# 7 루시아 타격(.40)·버팀(.58) 자세 찾기 — 날 아래 끝이 땅(-5~+15), gFh 손목 2 러스트 버팀 ±20°, 팔 펴짐 .72~.88, 도끼 앞끝 짧게
#   python3 -I tools/fit_hit7.py [lean°] [hipX] [hipY] → 좋은 후보 10개 (gx gy sa)
import json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE)
J = json.load(open(os.path.join(SRC, 'joints7.json'))); O = np.array(J['O'], float); rig = lambda a: (np.array(a, float) - O) * 2
HIP, S0, E0, W0, G0 = (rig(J[k]) for k in ('HIP', 'SH_F', 'EL_F', 'WR_F', 'G'))
L1, L2 = float(np.linalg.norm(E0 - S0)), float(np.linalg.norm(W0 - E0)); WG = float(np.linalg.norm(W0 - G0))
SA0 = math.radians(J['AXE']['shaft_deg']); BODY = (J['feet'] - J['helmet_top']) * 2
FDH = math.radians(-146.6); BENDH0 = -32.0
lab = np.load(os.path.join(SRC, 'work', 'labels.npy')); NM = json.load(open(os.path.join(SRC, 'work', 'label_names.json')))
ys, xs = np.nonzero(lab == NM.index('axe') + 1); AX = (np.stack([xs, ys], 1).astype(float) - O) * 2
AX = AX[np.linspace(0, len(AX) - 1, 3000).astype(int)]
R = lambda a: np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
ang = lambda v: math.atan2(v[1], v[0]); cr = lambda a, b: float(a[0] * b[1] - a[1] * b[0])
adiff = lambda a, b: (a - b + math.pi) % (2 * math.pi) - math.pi
side0 = np.sign(cr(W0 - S0, E0 - S0))
lean = math.radians(float(sys.argv[1]) if len(sys.argv) > 1 else 17.2)
hx = float(sys.argv[2]) if len(sys.argv) > 2 else 42; hy = float(sys.argv[3]) if len(sys.argv) > 3 else 50
hipL = HIP + np.array([hx, hy]); S = hipL + R(lean) @ (S0 - HIP)
out = []
for sad in range(-20, 41, 2):
    sa = math.radians(sad); AXt0 = (AX - G0) @ R(sa - SA0).T
    for gx in range(200, 461, 10):
        for gy in range(-200, 101, 10):
            G = hipL + np.array([gx, gy]); AXt = AXt0 + G; low = AXt[:, 1].max(); front = AXt[:, 0].max()
            if not (-5 <= low <= 15): continue
            fd = sa + FDH; Wp = G + np.array([math.cos(fd), math.sin(fd)]) * WG; d = float(np.linalg.norm(Wp - S)); reach = d / (L1 + L2)
            if d >= L1 + L2 or not (.72 <= reach <= .88): continue
            a = (L1 * L1 - L2 * L2 + d * d) / (2 * d); h = math.sqrt(max(0, L1 * L1 - a * a)); m = S + (Wp - S) * a / d; n = np.array([-(Wp - S)[1], (Wp - S)[0]]) / d
            E1, E2 = m + n * h, m - n * h; E = E1 if np.sign(cr(Wp - S, E1 - S)) == side0 else E2
            bend = math.degrees(adiff(ang(E - Wp), fd)) - BENDH0
            if abs(bend) > 20: continue
            out.append((abs(bend) / 20 + (front / BODY) * 2 + abs(reach - .8) * 3, gx, gy, sad, reach, bend, low, front / BODY, (G[1]) / -BODY * -1))
out.sort()
print(f'lean {math.degrees(lean):+.1f}° hip +{hx:.0f},+{hy:.0f} · 후보 {len(out)}개 (점수 낮을수록 좋음: 손목·도끼 앞끝·펴짐 .8)')
for o in out[:12]:
    print(f'  gx {o[1]:+4d} gy {o[2]:+4d} sa {o[3]:+3d}° · 펴짐 {o[4]:.2f} 손목 {o[5]:+4.0f}° 날아래 {o[6]:+4.0f} 앞끝 ×{o[7]:.2f} · 쥔 점 땅 위 ×{-o[8]:.2f}')
