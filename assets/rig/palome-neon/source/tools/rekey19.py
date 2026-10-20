# 19 공격 키 맞추기 (9 v1.1 키에서 시작 — 29 rekey29 복사) — 규칙 33: 펴짐(reach) ≤ 0.85 · 손목 ≤ 35° · 칼끝 땅 위 · 칼끝이 지금보다 높지 않게(전투 칸)
#   키마다 칼 각·몸 기울기·골반 내림은 그대로, 쥔 점만 지금 자리에서 가장 가까운 '조건 맞는 자리'로 옮김 → attack_keys.json(keys_prev 에 이전 키)
import json, math, os, sys
import numpy as np
S_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.argv = ['presim19.py']; __file__ = os.path.join(S_, 'tools', 'presim19.py')
exec(open(__file__).read().split("if __name__ == '__main__':")[0])
AK = json.load(open(os.path.join(S_, 'attack_keys.json'))); K0 = AK['keys']
RMAX, WMAX, TIPTOP = float(os.environ.get('RMAX', .85)), 35, -88
def ok_at(gx, gy, sa, lean, hd):
    globals()['KEYS'] = [[0, gx, gy, sa, lean, hd], [1, gx, gy, sa, lean, hd]]; p = pose(.5, SIDE)
    ty = p['tip'][1] + HIP[1]; py = p['pom'][1] + HIP[1]
    good = p['ok'] and p['reach'] <= RMAX and abs(p['bend']) <= WMAX and ty >= TIPTOP and max(ty, py) <= J['GROUND'] - 2
    return good, p
out = []
for k in K0:
    t, gx, gy, sa, lean, hd = k[:6]; e = k[6] if len(k) > 6 else 'io'
    g, p = ok_at(gx, gy, sa, lean, hd)
    if g: out.append(k); print(t, 'keep', round(p['reach'], 2), round(p['bend'])); continue
    best = None
    for dx in range(-90, 61, 2):
        for dy in range(-90, 61, 2):
            g, p = ok_at(gx + dx, gy + dy, sa, lean, hd)
            if g:
                d = math.hypot(dx, dy)
                if best is None or d < best[0]: best = (d, gx + dx, gy + dy, p)
    if best is None: print(t, 'NO SOLUTION'); out.append(k); continue
    d, nx, ny, p = best; out.append([t, round(nx, 1), round(ny, 1), sa, lean, hd, e]); print(t, 'move', round(d, 1), 'reach', round(p['reach'], 2), 'wrist', round(p['bend']))
AK['keys_prev'] = K0; AK['keys'] = out
AK['note'] = AK['note'] + ' · 10-20 07:40 rekey19.py: 펴짐 ≤ %.2f(규칙 33) — 쥔 점만 가장 가까운 조건 맞는 자리로' % RMAX
json.dump(AK, open(os.path.join(S_, 'attack_keys.json'), 'w'), ensure_ascii=False, indent=1)
