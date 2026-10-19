# 둘시네 원화 팔 2관절 + 손목 꺾임 계산(엔진 wristArm 과 같은 식) — 골반 기준 리그 px
import numpy as np, math
HU = np.array([0.574, -0.819]); HU /= np.linalg.norm(HU)
G0 = np.array([357.0 - 0.70 * (311 - 250), 311.0])
SH_N, EL_N = np.array([170.0, 248.0]), np.array([146.0, 280.0]); WR2 = np.array([133.0, 309.0]); GRIP_N = np.array([130.0, 332.0])
SH_F, EL_F, WR_F = np.array([270.0, 262.0]), np.array([255.0, 300.0]), np.array([288.0, 304.0])
un = lambda v: v / np.linalg.norm(v)
fdN = un(EL_N - WR2); sdN = np.array([-fdN[1], fdN[0]])
far = dict(w=np.zeros(2), fd=un(EL_F - G0), L1=np.linalg.norm(EL_F - SH_F) * 2, L2=np.linalg.norm(EL_F - G0) * 2, sd=HU, s=0)   # 공 손목: 손목 = 쥔 점
near = dict(w=np.zeros(2), fd=un(EL_N - GRIP_N), L1=np.linalg.norm(EL_N - SH_N) * 2, L2=np.linalg.norm(EL_N - GRIP_N) * 2, sd=sdN, s=82)
ang = lambda v: math.atan2(v[1], v[0])
R = lambda t: np.array([[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]])
wrap = lambda a: (a + math.pi) % (2 * math.pi) - math.pi
def chain(c, G, a, S):
    U = np.array([math.cos(a), math.sin(a)]); rho = a - ang(c['sd']); Gp = G + U * c['s']; W = Gp + R(rho) @ c['w']
    E0 = W + R(rho) @ c['fd'] * c['L2']; d = np.linalg.norm(W - S)
    if d > c['L1'] + c['L2']: return dict(ok=False, gap=d - c['L1'] - c['L2'], W=W, E=None, bend=None, cross=None)
    dd = max(d, abs(c['L1'] - c['L2']) + 1e-3); al = math.acos(np.clip((c['L1'] ** 2 + dd ** 2 - c['L2'] ** 2) / (2 * c['L1'] * dd), -1, 1)); base = ang(W - S)
    best = None
    for sg in (-1, 1):
        E = S + np.array([math.cos(base + sg * al), math.sin(base + sg * al)]) * c['L1']; bend = wrap(ang(E - W) - ang(E0 - W))
        up, fo = E - S, W - E; cr = up[0] * fo[1] - up[1] * fo[0]
        o = dict(ok=True, gap=0, W=W, E=E, bend=math.degrees(bend), cross=cr / (np.linalg.norm(up) * np.linalg.norm(fo)), side=sg)
        if best is None or abs(o['bend']) < abs(best['bend']): best = o
    return best
def both(G, a, SN, SF): return chain(far, np.array(G, float), a, np.array(SN, float)), chain(near, np.array(G, float), a, np.array(SF, float))
if __name__ == '__main__':
    print('far L', far['L1'], far['L2'], 'near L', near['L1'], near['L2'])
