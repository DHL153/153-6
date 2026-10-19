"""가까운 팔꿈치 프레임마다 움직임 모의(엔진 track·EASE·ikSideK·armIK 와 같은 셈, 상체 기준) — 접힘에서 팔꿈치 쪽 바꿀 때 튐 찾기
실행: cd source && python3 -I tools/elbow_sim.py [attack_keys.json]  → 위상 4개(프레임 시작 0~0.75)에서 가장 큰 한 프레임 이동"""
import json, math, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(HERE, 'tools'))
import check_keys as C
EASE = {'lin': lambda t: t, 'io': lambda t: t * t * (3 - 2 * t), 'o': lambda t: 1 - (1 - t) ** 2, 'i': lambda t: t * t}
def track(K, t):
    if t <= K[0][0]: return K[0][1]
    for a, b in zip(K, K[1:]):
        if t <= b[0]: e = a[2] if len(a) > 2 else 'io'; return a[1] + (b[1] - a[1]) * EASE.get(e, EASE['io'])((t - a[0]) / max(1e-6, b[0] - a[0]))
    return K[-1][1]
def tracks(K):
    gi = [(t, C.GU0[0] if x == 'idle' else x, C.GU0[1] if y == 'idle' else y, C.SA0 if a == 'idle' else a, (e[0] if e else 'io')) for t, x, y, a, *e in K['grip']]
    return [[g[0], g[1], g[4]] for g in gi], [[g[0], g[2], g[4]] for g in gi], [[g[0], g[3], g[4]] for g in gi]
def elbow(K, t):
    gx, gy, sa = tracks(K); act = K['action']; G = (track(gx, t), track(gy, t))
    sk = act.get('ikSideK', {}).get('N', [[0, act.get('ikSide', {}).get('N', 1)]]); side = [v for tt, v in sk if t >= tt][-1]
    fx = track(act['shFx'], t) if act.get('shFx') else 0; S = (C.SN[0] + fx, C.SN[1])
    dd = max(math.dist(S, G), abs(C.L1N - C.L2N) + 1e-3); E, _ = C.ik(S, G if math.dist(S, G) > 1e-6 else (G[0] + 1e-3, G[1]), C.L1N, C.L2N, side)
    if E is None:   # 엔진: 최소 닿음 밑이면 dd 로 눌러 계산
        base = math.atan2(G[1] - S[1], G[0] - S[0]); al = math.pi; E = (S[0] + math.cos(base + al * side) * C.L1N, S[1] + math.sin(base + al * side) * C.L1N)
    return E, G
def worst(K, t0=0.0, t1=0.94):
    out = []
    for ph in (0, .25, .5, .75):
        prev = None; t = t0 + ph / 60
        while t < t1:
            E, G = elbow(K, t)
            if prev: out.append((math.dist(E, prev[0]), round(t, 3), [round(v) for v in E]))
            prev = (E, G); t += 1 / 60
    out.sort(reverse=True); return out
if __name__ == '__main__':
    K = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'attack_keys.json'), encoding='utf-8'))
    for d, t, E in worst(K)[:8]: print(f'  t{t:.3f} 팔꿈치 한 프레임 {d:5.1f}px → {E}')
