"""23 스카이아크 산초 — 새 원화가 오기 전 미리 검사: 러스트 자세(13 네온 산초 관절 = 러스트와 같은 자세)에 23 칼 비율을 얹어
러스트/13 올려베기 키를 1/60초로 촘촘히 돌려 '눈·입 가림 여유'와 '칼끝-땅'을 13 칼과 비교한다.
23 칼 비율(지금 char_0023, 몸 키 370 기준): 날밑 가운데→칼끝 264(0.71) · 날 폭 70(0.19) · 날밑 길이 116(0.31) · 두께 25(0.07)
  13 칼(몸 337): 날 278(0.82) · 폭 57(0.17) · 날밑 80(0.24) · 두께 28
실행: python3 -I presim_sword.py   (sancho-neon/source/tools/check_keys.py 를 불러 칼 그림만 바꿈)"""
import importlib.util, math, os, json, sys
import numpy as np, cv2
from PIL import Image, ImageDraw
NEON = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'sancho-neon', 'source')
spec = importlib.util.spec_from_file_location('ck', os.path.join(NEON, 'tools', 'check_keys.py')); ck = importlib.util.module_from_spec(spec); spec.loader.exec_module(ck)
BODY13 = 337.0
def sword_mask(blade_len, blade_w, guard_len, guard_th, tip_taper=0.22):
    """13 원화 좌표에 23 모양 칼(곧은 넓은 날 + 뾰족 끝 + 날밑 + 손잡이·폼멜은 13 그대로)"""
    m = Image.new('L', (512, 512), 0); d = ImageDraw.Draw(m)
    gc = np.array(ck.BL['guardC'], float); ax = np.array([math.cos(ck.SA0 + ck.BLADE_OFF), math.sin(ck.SA0 + ck.BLADE_OFF)])   # 날 방향(날밑 → 칼끝)
    ax = (np.array(ck.TIP, float) - gc); ax /= np.linalg.norm(ax); nx = np.array([-ax[1], ax[0]]); hw = blade_w / 2
    tip = gc + ax * blade_len; sh = gc + ax * blade_len * (1 - tip_taper)
    d.polygon([tuple(gc + nx * hw), tuple(sh + nx * hw), tuple(tip), tuple(sh - nx * hw), tuple(gc - nx * hw)], fill=255)
    d.polygon([tuple(gc + nx * guard_len / 2 + ax * guard_th / 2), tuple(gc + nx * guard_len / 2 - ax * guard_th / 2), tuple(gc - nx * guard_len / 2 - ax * guard_th / 2), tuple(gc - nx * guard_len / 2 + ax * guard_th / 2)], fill=255)
    pp = np.array([ck.HD[1], -ck.HD[0]]) * 9; P2 = ck.POM + ck.HD * 20
    d.polygon([tuple(ck.COL + pp), tuple(P2 + pp), tuple(P2 - pp), tuple(ck.COL - pp)], fill=255); d.ellipse([ck.POM[0] - 11, ck.POM[1] - 6, ck.POM[0] + 11, ck.POM[1] + 16], fill=255)
    return np.array(m) > 0, float(np.linalg.norm(tip - (ck.GU_art))) * 2, math.atan2(tip[1] - ck.GU_art[1], tip[0] - ck.GU_art[0]) - ck.SA0
def use(mask, tipd, off):
    ck.SWM = mask; ck.DT = cv2.distanceTransform((~mask).astype(np.uint8), cv2.DIST_L2, 5); ck.TIPd = tipd; ck.BLADE_OFF = off
EASE = {'io': lambda u: u * u * (3 - 2 * u), 'i': lambda u: u * u, 'o': lambda u: 1 - (1 - u) ** 2, 'lin': lambda u: u}
def keyv(K, t, i):
    if t <= K[0][0]: return K[0][i]
    for a, b in zip(K, K[1:]):
        if a[0] <= t <= b[0]:
            u = (t - a[0]) / (b[0] - a[0]) if b[0] > a[0] else 0; e = a[4] if len(a) > 4 else 'io'; u = EASE.get(e, EASE['io'])(u)
            return a[i] + (b[i] - a[i]) * u
    return K[-1][i]
def run(tag):
    K = json.load(open(os.path.join(NEON, 'attack_keys.json'), encoding='utf-8')); act = K['action']; side = act.get('ikSide', {'N': 1, 'F': -1}); sk = act.get('ikSideK', {})
    G = [[t, *(ck.GU0 if x == 'idle' else (x, y)), (ck.SA0 if x == 'idle' else a), *e] for t, x, y, a, *e in K['grip']]
    rows = []
    for f in range(0, 57):
        t = f / 60 / 0.94 * 1.0; t = f / 56 * 0.94 if False else f / 60 / 0.94
        if t > 1: break
        g = (keyv(G, t, 1), keyv(G, t, 2)); sa = keyv(G, t, 3); tr = lambda n: ck.track(act.get(n), t); stp = lambda KK, d: ([v for tt, v in KK if t >= tt] or [d])[-1]
        c = ck.check(g, sa, tr('head'), (tr('shFx'), tr('shFy')), (tr('shNx'), tr('shNy')), stp(sk.get('N', []), side['N']), stp(sk.get('F', []), side['F']), tr('hipY'))
        rows.append((round(t, 3), c['face'], c['tipGnd']))
    return rows
if __name__ == '__main__':
    k = BODY13 / 370
    cases = {'13 칼(지금 13 리그)': None,
             '23 칼 비율 그대로': (264 * k, 70 * k, 116 * k, 25 * k),
             '23 폭·날밑 + 13 길이': (278, 70 * k, 116 * k, 25 * k)}
    base = (ck.SWM.copy(), ck.TIPd, ck.BLADE_OFF); res = {}
    for name, p in cases.items():
        if p: use(*sword_mask(*p))
        else: use(*base)
        res[name] = run(name)
    # 정지·느린 구간(얼굴이 보여야 하는 곳) = 지나감(0.15~0.27·0.66~0.78) 밖
    for name, rows in res.items():
        hold = [r for r in rows if not (0.15 < r[0] < 0.27 or 0.66 < r[0] < 0.78)]
        mins = {kk: min(r[1][kk] for r in hold) for kk in rows[0][1]}
        worst = sorted(hold, key=lambda r: min(r[1].values()))[:4]
        print(f'[{name}] 얼굴 여유 최소(지나감 밖) {mins} · 칼끝-땅 최소 {min(r[2] for r in rows):.0f}')
        print('   가장 가까운 시각:', [(r[0], r[1]) for r in worst])
        bad = [(r[0], {kk: v for kk, v in r[1].items() if v < (0 if kk == 'mask' else 6)}) for r in hold if any(v < (0 if kk == 'mask' else 6) for kk, v in r[1].items())]
        print('   가림(눈 <6 · 입 <0):', bad[:12], '…' if len(bad) > 12 else '', len(bad), '장면')
