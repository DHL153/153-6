# 자세 하나: 가까운 손(어깨 SF 고정)이 손목 꺾임 작게 닿는 G 들 → 먼 어깨를 어디로 옮겨야 먼 손목 꺾임 0 인지
from arm import *
import sys
def far_need(G, a, SN):
    c = far; U = np.array([math.cos(a), math.sin(a)]); rho = a - ang(c['sd']); W = np.array(G, float) + R(rho) @ c['w']
    E0 = W + R(rho) @ c['fd'] * c['L2']; v = np.array(SN, float) - E0; S = E0 + v / np.linalg.norm(v) * c['L1']   # 먼 어깨: 원(반지름 L1) 위 SN 에 가장 가까운 점
    up, fo = E0 - S, W - E0; cr = (up[0] * fo[1] - up[1] * fo[0]) / (np.linalg.norm(up) * np.linalg.norm(fo))
    return S, np.linalg.norm(S - np.array(SN)), cr, W, E0
def run(a, SN, SF, pref, lim=25, top=8, wS=1.0, wP=.3):
    out = []
    for x in range(-260, 260, 4):
        for y in range(-420, 160, 4):
            n = chain(near, np.array([x, y], float), a, np.array(SF, float))
            if not n['ok'] or abs(n['bend']) > lim: continue
            S, dS, cr, W, E0 = far_need((x, y), a, SN)
            c = abs(n['bend']) * .5 + wS * dS + wP * math.hypot(x - pref[0], y - pref[1])
            out.append((round(c), (x, y), 'nb', round(n['bend']), 'ncr', round(n['cross'], 2), 'farS', S.round(0).tolist(), 'shift', (S - np.array(SN)).round(0).tolist(), 'fcr', round(cr, 2), 'fE', E0.round(0).tolist(), 'nE', n['E'].round(0).tolist()))
    out.sort(key=lambda r: r[0]); return out[:top]
if __name__ == '__main__':
    a = float(sys.argv[1]); SN, SF, pref = eval(sys.argv[2]), eval(sys.argv[3]), eval(sys.argv[4])
    for r in run(a, SN, SF, pref, wS=float(sys.argv[5]) if len(sys.argv) > 5 else 1): print(r)
