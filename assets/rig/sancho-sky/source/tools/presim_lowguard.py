"""23 칼(넓은 날·큰 날밑)로 낮은 겨눔(0.255~0.36) 손 자리를 얼마나 옮겨야 입이 보이나 — 조립 전 미리 찾기
python3 -I presim_lowguard.py"""
import os, sys, math, json
sys.argv = [sys.argv[0]]; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'presim_sword.py')).read().split("if __name__ == '__main__':")[0])
k = BODY13 / 370; use(*sword_mask(264 * k, 70 * k, 116 * k, 25 * k))
K = json.load(open(os.path.join(NEON, 'attack_keys.json'), encoding='utf-8')); act = K['action']; sk = act.get('ikSideK', {})
low = [g for g in K['grip'] if 0.25 <= g[0] <= 0.37]; print('지금 낮은 겨눔 키:', low)
best = []
for dx in range(-10, 41, 5):
    for dy in range(0, 41, 5):
        worst = 99; reach = 0; gnd = 999
        for t, x, y, a, *e in low:
            c = ck.check((x + dx, y + dy), a, ck.track(act.get('head'), t), (ck.track(act.get('shFx'), t), 0), (ck.track(act.get('shNx'), t), 0), 1, -1, ck.track(act.get('hipY'), t))
            worst = min(worst, c['face']['mask'], c['face']['nEye'] - 6, c['face']['fEye'] - 6); reach = max(reach, c['rN'], c['rF']); gnd = min(gnd, c['tipGnd'])
        if worst >= 0 and reach <= 1.0 and gnd >= 20: best.append((dx * dx + dy * dy, dx, dy, round(worst, 1), round(reach, 3), round(gnd)))
best.sort(); print('입·눈 보이고(여유 ≥0) 팔 닿고(≤1.00) 칼끝 땅 위(≥20)인 옮김 — 작은 순:', best[:6])
