# 17 네온 루시아 내려찍기 키 미리 재기 — keyfit7(7 러스트) 구조, 엔진(rig.js _swordRigid wristArm)과 같은 팔: 주먹 = 쥔 점(G)에 붙음, 팔뚝 조각 = G → 팔꿈치(길이 |EL_F−G|), 윗팔 = 어깨 → 팔꿈치
#   손목 꺾임 = 팔뚝 방향(G→E) − 주먹 그림 foreDir(원화 G→팔꿈치 − 자루 각)  → 엔진 this.wrN 과 같음
#   python3 -I tools/keyfit17.py            → attack/keys17.json 의 키마다 표(펴짐·손목·도끼 꼭대기·날 아래·앞끝)
#   python3 -I tools/keyfit17.py sa gx gy lean hx hy [a0 a1 st] → 그 자세에서 자루 각별 표
#   python3 -I tools/keyfit17.py hit lean hx hy → 타격 자세 찾기(날 아래 끝 = 땅 −5~+15, 손목 ±30°, 펴짐 .7~.88)
#   기준: 펴짐 ≤ .90(DHL 팔 늘이지 않기) · 손목 ±40° · 도끼 꼭대기 ≤ 몸 키 ×1.62 · 날 아래 ≤ 땅 + 18
import json, math, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_src = open(os.path.join(HERE, 'build_lucia17.py')).read(); _j = _src[_src.index('# ---------------- 원화 관절'):_src.index('# ---------------- 칸 (seg17.py)')]
B = {'np': np, 'math': math, 'unitv': lambda v: np.array(v, float) / np.linalg.norm(v), 'print': lambda *a, **k: None, 'MS': json.load(open(os.path.join(HERE, 'measure17.json')))}
exec(compile(_j, 'build_lucia17.py(관절)', 'exec'), B)
O, HIP, SH_F, EL_F, G0, HU = (B[k] for k in ('O', 'HIP', 'SH_F', 'EL_F', 'G', 'HU'))
rig = lambda p: (np.asarray(p, float) - O) * 2
L1, L2 = 2 * float(np.linalg.norm(EL_F - SH_F)), 2 * float(np.linalg.norm(EL_F - G0))
SA0 = math.atan2(HU[1], HU[0]); FD = math.atan2(*(EL_F - G0)[::-1]) - SA0
BODY = 2 * (450 - 180)
A_ = np.array(Image.open(os.path.join(HERE, 'work', 'axeArt.png')))[..., 3] > 128; ys, xs = np.nonzero(A_)
o_ = np.array(json.load(open(os.path.join(HERE, 'work', 'offsets.json')))['axe'], float)
AX = (np.stack([xs, ys], 1) + o_ - G0) * 2; AX = AX[np.linspace(0, len(AX) - 1, 3000).astype(int)]
R = lambda a: np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
ang = lambda v: math.atan2(v[1], v[0]); wrap = lambda a: (a + math.pi) % (2 * math.pi) - math.pi
def pose(gx, gy, sad, lean, hx, hy, side=1):
    sa = math.radians(sad); th = lean; hipL = rig(HIP) + np.array([hx, hy]); S = hipL + R(th) @ (rig(SH_F) - rig(HIP)); G = hipL + np.array([gx, gy])
    d = float(np.linalg.norm(G - S)); base = ang(G - S)
    if d >= L1 + L2: E = S + (G - S) / d * L1
    else:
        al = math.acos(max(-1, min(1, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)))); E = S + L1 * np.array([math.cos(base + side * al), math.sin(base + side * al)])
    fd = sa + FD; wr = math.degrees(wrap(ang(E - G) - fd))
    P = AX @ R(sa - SA0).T + G
    return dict(reach=d / (L1 + L2), wr=wr, top=-P[:, 1].min() / BODY, low=P[:, 1].max(), front=(P[:, 0].max() - hipL[0]) / BODY, G=G, S=S, E=E, el=math.degrees(ang(E - S)))
def row(tag, gx, gy, sad, lean, hx, hy, *_):
    r = pose(gx, gy, sad, lean, hx, hy); bad = r['reach'] > .90 or abs(r['wr']) > 40 or r['top'] > 1.62 or r['low'] > 18
    print(f"  {tag}: gx {gx:+5.0f} gy {gy:+5.0f} sa {sad:+5.0f}° 펴짐 {r['reach']:.2f} 손목 {r['wr']:+4.0f}° 윗팔 {r['el']:+5.0f}° 꼭대기 ×{r['top']:.2f} 날아래 {r['low']:+5.0f} 앞끝 ×{r['front']:.2f} {'✗' if bad else ''}")
    return r
if __name__ == '__main__':
    print(f'  팔 L1 {L1:.1f} · 팔뚝(G→팔꿈치) {L2:.1f} · 대기 자루 {math.degrees(SA0):.1f}° · foreDir {math.degrees(FD):.1f}° · 몸 키 {BODY} · 대기 쥔 점 {((G0 - HIP) * 2).round(1).tolist()} · 어깨 {((SH_F - HIP) * 2).round(1).tolist()}')
    a = sys.argv[1:]
    if not a:
        K = json.load(open(os.path.join(HERE, 'attack', 'keys17.json')))
        for k in K['keys']: row(f"{k[0]:.2f}", *k[1:7])
    elif a[0] == 'sa':
        gx, gy, lean, hx, hy = map(float, a[1:6]); a0, a1, st = (map(int, a[6:9]) if len(a) > 8 else (-170, 30, 10))
        for sd in range(a0, a1 + 1, st): row(f'sa{sd:+d}', gx, gy, sd, lean, hx, hy)
    elif a[0] == 'hit':
        lean, hx, hy = map(float, a[1:4]); out = []
        for sd in range(-40, 21, 2):
            for gx in range(180, 461, 10):
                for gy in range(-200, 141, 10):
                    r = pose(gx, gy, sd, lean, hx, hy)
                    if -5 <= r['low'] <= 15 and abs(r['wr']) <= 30 and .70 <= r['reach'] <= .88:
                        out.append((abs(r['wr']) / 30 + r['front'] * 2 + abs(r['reach'] - .8) * 3, gx, gy, sd, r))
        out.sort(key=lambda o: o[0]); print(f'  타격 후보 {len(out)}')
        for o in out[:12]: row('hit', o[1], o[2], o[3], lean, hx, hy)
