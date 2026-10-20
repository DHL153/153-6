# 29 타격 손 자리 찾기 (10-20 10:41 DHL '어깨 위치를 무시하고 팔이 너무 아래로'): 팔꿈치 아래 쪽(SIDE 1)에서 칼 각·쥔 점 격자 → 펴짐 ≤ .9 · 손목 ≤ 40 · 칼끝 땅 위 중 어깨 기준 손이 가장 높고 앞인 곳
#   python3 strike_grid29.py → 몸 기울기 14·20·26 × 칼 각 구간별 상위 2개 (dy, dx = 어깨→손목 ÷ 팔 길이)
import json, math, os, sys
import numpy as np
S_ = '/home/claude/153-6/assets/rig/palome-sky/source'
sys.argv = ['presim29.py']; __file__ = os.path.join(S_, 'tools', 'presim29.py')
exec(open(__file__).read().split("if __name__ == '__main__':")[0])
L = L1 + L2
def one(gx, gy, sa, lean, hd, side=1):
    globals()['KEYS'] = [[0, gx, gy, sa, lean, hd, 'io'], [1, gx, gy, sa, lean, hd, 'io']]; return pose(.5, side)
for lean, hd in [(14, 12), (20, 14), (26, 16)]:
    for samin in (-12, -4, 4):
        best = []
        for sa in range(samin, samin + 8, 2):
            for gx in range(150, 270, 3):
                for gy in range(-40, 50, 3):
                    p = one(gx, gy, sa, lean, hd)
                    if not p['ok'] or p['reach'] > .9 or abs(p['bend']) > 40: continue
                    ty = p['tip'][1] + HIP[1]
                    if ty > 474: continue
                    S = p['S'] + HIP; W = p['W'] + HIP; E = p['E'] + HIP
                    dx, dy = (W - S) / L
                    if dx < .45: continue
                    best.append((round(dy, 2), round(dx, 2), sa, gx, gy, round(p['reach'], 2), round(p['bend']), E.round().tolist(), W.round().tolist(), S.round().tolist(), round(ty)))
        best.sort(); print('lean', lean, 'sa', samin, '..', samin + 6, best[:2])
