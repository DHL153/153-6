"""두 점 짝(조각 px → 원화 512 px)으로 닮음변환 → fix_result.json (자동 맞춤이 틀린 작은 조각: 옆머리 등)
python3 -I place_manual.py name file ax ay AX AY bx by BX BY   (a·b = 조각 점, A·B = 원화 512 점)"""
import json, sys, math, os
import numpy as np
n, f = sys.argv[1], sys.argv[2]; ax, ay, AX, AY, bx, by, BX, BY = map(float, sys.argv[3:11])
a, b = np.array([ax, ay]), np.array([bx, by]); A, B = np.array([AX, AY]) * 2, np.array([BX, BY]) * 2
s = np.linalg.norm(B - A) / np.linalg.norm(b - a); phi = math.atan2(*(B - A)[::-1]) - math.atan2(*(b - a)[::-1])
c, sn = math.cos(phi) * s, math.sin(phi) * s; M = np.array([[c, -sn, 0], [sn, c, 0]]); M[:, 2] = A - M[:, :2] @ a
F = json.load(open('fix_result.json')) if os.path.exists('fix_result.json') else {}
F[n] = dict(file=f, s=round(s, 4), deg=round(math.degrees(phi), 2), M=M.tolist(), manual=[[ax, ay, AX, AY], [bx, by, BX, BY]])
json.dump(F, open('fix_result.json', 'w'), indent=1); print(n, 's', round(s, 3), 'deg', round(math.degrees(phi), 1))
