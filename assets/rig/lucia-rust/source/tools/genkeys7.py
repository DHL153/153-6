# 7 루시아 내려찍기 키 만들기 → attack/keys7.json (smash7.py · tools/keyfit7.py 가 읽음)   python3 -I tools/genkeys7.py
#   골반·숙임 트랙 = 22 스카이 smash22 트랙 × 몸 배율(루시아 556 / 22 734 = .757, 숙임은 그대로)
#   쥔 점·자루 각 = 루시아 키(keyfit7.py 로 잼 — 펴짐 ≤ .92 · 손목 ±40° · 도끼 꼭대기 ≤ ×1.62 · 타격 날 앞 끝 = 땅)
import json, os, math
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIFT, WIND, SW1, SW2, HIT, HOLD, RET1, RET, END = .18, .27, .32, .36, .40, .58, .68, .82, 1.0
KB = 556 / 734
k = lambda *kv: [list(x) for x in kv]
TR = {'hipX': k((0, 0, 'io'), (LIFT, -10 * KB, 'io'), (WIND, -12 * KB, 'i'), (SW2, 25 * KB, 'o'), (HIT, 56 * KB, 'o'), (HOLD, 60 * KB, 'io'), (RET + .08, 0)),
      'hipY': k((0, 0, 'io'), (LIFT, 10 * KB, 'io'), (WIND, 14 * KB, 'i'), (SW2, 24 * KB, 'o'), (HIT, 40 * KB, 'o'), (HIT + .05, 46 * KB, 'io'), (HOLD, 44 * KB, 'io'), (RET + .08, 0)),
      'lean': k((0, 0, 'io'), (LIFT, -.12, 'io'), (WIND, -.13, 'i'), (SW1, -.02), (SW2, .14, 'o'), (HIT, .30, 'o'), (HOLD, .32, 'io'), (RET + .08, 0))}
for kk in TR.values():
    for r in kk: r[1] = round(r[1], 2)
E = {'io': lambda u: u * u * (3 - 2 * u), 'i': lambda u: u * u, 'o': lambda u: 1 - (1 - u) ** 2, 'lin': lambda u: u}
def tr(K, t):
    if t <= K[0][0]: return K[0][1]
    for a, b in zip(K, K[1:]):
        if t <= b[0]: return a[1] + (b[1] - a[1]) * E[a[2] if len(a) > 2 and a[2] else 'io']((t - a[0]) / max(1e-6, b[0] - a[0]))
    return K[-1][1]
# 쥔 점(골반 기준 리그 px)·자루 각(도)·쥔 손·이음 — 대기 = (308.8, −114, −105.8°)
G0 = (308.8, -114.0, -105.8)
GK = [(0, *G0, 'art', 'io'),
      (LIFT, 282, -270, -150, 'art', 'io'),
      (WIND, 278, -276, -153, 'art', 'i'),
      (SW1, 336, -214, -110, 'art', None),
      (SW2, 380, -120, -66, 'art', 'o'),    # v1.3(DHL 23:29 '손이 이상하게 들어갔어요') — 휘두름~버팀도 원화 주먹(시트 19 gFh 안 씀), 자루 −55→−66°(원화 주먹 손목 −38→−27°, 1/60 표 가장 큰 꺾임 −36°)
      (HIT, 300, 80, -24, 'art', 'o'),
      (HOLD, 300, 80, -24, 'art', 'io'),
      (RET1, 320, -10, -52, 'art', 'io'),   # −45→−52°(손목 −37→−30°)
      (RET, 300, -80, -85, 'art', 'io'),
      (END - .03, *G0, 'art', None)]
rows = [[t, gx, gy, sa, tr(TR['lean'], t), round(tr(TR['hipX'], t), 2), round(tr(TR['hipY'], t), 2), f, e] for t, gx, gy, sa, f, e in GK]
for r in rows: r[4] = round(r[4], 4)
json.dump({'_note': '7 루시아 한 손 도끼 내려찍기 키 — tools/genkeys7.py 가 만듦. keys = [t, gx, gy(리그 px, 골반 기준), 자루 각(도), 숙임(rad), 골반 x, 골반 y, 쥔 손, 이음] · tracks = 엔진 트랙 통째(골반·숙임)',
           'artBack': RET1, 'keys': rows, 'tracks': TR}, open(os.path.join(HERE, 'attack', 'keys7.json'), 'w'), ensure_ascii=False, indent=1)
print('keys7.json', len(rows), '키')
