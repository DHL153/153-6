# 17 네온 루시아 내려찍기 키 만들기 → attack/keys17.json (smash17.py · tools/keyfit17.py 가 읽음)   python3 -I tools/genkeys17.py
#   골반·숙임 트랙 = 22 스카이 smash22 트랙 × 몸 배율(루시아 네온 540 / 22 734 = .736, 숙임은 그대로) — 7 러스트(× .757)와 같은 모양
#   쥔 점·자루 각 = 7 러스트 키를 네온 어깨 기준으로 옮김(어깨 → 쥔 점 벡터 × 팔 길이 비 1.115) 뒤 keyfit17 로 고침:
#     휘두름 시작 .32 = 도끼 꼭대기 ×1.66 → (315,−228,−122°) ×1.61 · 타격·버팀 = 날 아래 +24~27 → (280,70,−24°) 날 앞 끝이 땅 +7~10, 펴짐 .79 · 손목 −22°
#     v1.2: 골반 내림 0(서 있는 원화 다리로 공격 끝까지) → 타격·버팀 (280,98,−24°) 펴짐 .87 · 손목 −12° · 날 아래 +6
import json, os, math
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIFT, WIND, SW1, SW2, HIT, HOLD, RET1, RET, END = .18, .27, .32, .36, .40, .58, .68, .82, 1.0
KB = 540 / 734
k = lambda *kv: [list(x) for x in kv]
HXK = .6   # v1.2: 서 있는 원화 다리로 공격 → 골반 앞으로 60%만(먼 다리가 원화처럼 펴진 채 — 100% 면 먼 무릎이 77° 접혀 정강이·부츠 사이가 벌어짐, 실수 68)
TR = {'hipX': k((0, 0, 'io'), (LIFT, -10 * KB * HXK, 'io'), (WIND, -12 * KB * HXK, 'i'), (SW2, 25 * KB * HXK, 'o'), (HIT, 56 * KB * HXK, 'o'), (HOLD, 60 * KB * HXK, 'io'), (RET + .08, 0)),
      'hipY': k((0, 0)),   # v1.2(DHL 10-21 15:40 '공격 중 다리를 틀지 말고 이전 다리 모양으로') 공격 내내 서 있는 원화 다리 → 골반을 내리지 않음(실수 66 ②) — 전엔 22 트랙 × KB(타격 29 · 버팀 32)
      'lean': k((0, 0, 'io'), (LIFT, -.12, 'io'), (WIND, -.13, 'i'), (SW1, -.02), (SW2, .14, 'o'), (HIT, .30, 'o'), (HOLD, .32, 'io'), (RET + .08, 0))}
for kk in TR.values():
    for r in kk: r[1] = round(r[1], 2)
E = {'io': lambda u: u * u * (3 - 2 * u), 'i': lambda u: u * u, 'o': lambda u: 1 - (1 - u) ** 2, 'lin': lambda u: u}
def tr(K, t):
    if t <= K[0][0]: return K[0][1]
    for a, b in zip(K, K[1:]):
        if t <= b[0]: return a[1] + (b[1] - a[1]) * E[a[2] if len(a) > 2 and a[2] else 'io']((t - a[0]) / max(1e-6, b[0] - a[0]))
    return K[-1][1]
# 쥔 점(골반 기준 리그 px)·자루 각(도)·쥔 손·이음 — 대기 = 원화 쥔 점·자루 각(build_lucia17 의 G·HU 와 같아야 함 — smash17 assert)
_src = open(os.path.join(HERE, 'build_lucia17.py')).read(); _j = _src[_src.index('# ---------------- 원화 관절'):_src.index('# ---------------- 칸 (seg17.py)')]
import numpy as np
B = {'np': np, 'math': math, 'unitv': lambda v: np.array(v, float) / np.linalg.norm(v), 'print': lambda *a, **k: None, 'MS': json.load(open(os.path.join(HERE, 'measure17.json')))}
exec(compile(_j, 'build_lucia17.py(관절)', 'exec'), B)
_g0 = (B['G'] - B['HIP']) * 2; G0 = (round(float(_g0[0]), 1), round(float(_g0[1]), 1), round(math.degrees(math.atan2(B['HU'][1], B['HU'][0])), 1))
GK = [(0, *G0, 'art', 'io'),
      (LIFT, 261, -303, -150, 'art', 'io'),
      (WIND, 257, -310, -153, 'art', 'i'),
      (SW1, 315, -220, -122, 'art', None),   # v1.2 골반 내림 0 → 꼭대기 ×1.63 이라 8 내림
      (SW2, 371, -136, -66, 'art', 'o'),
      (HIT, 280, 98, -24, 'art', 'o'),    # 골반을 안 내리는 만큼(29) 쥔 점을 내려 날 앞 끝 = 땅(날 아래 +6) · 펴짐 .87
      (HOLD, 280, 98, -24, 'art', 'io'),
      (RET1, 304, -13, -52, 'art', 'io'),
      (RET, 281, -91, -85, 'art', 'io'),
      (END - .03, *G0, 'art', None)]
rows = [[t, gx, gy, sa, tr(TR['lean'], t), round(tr(TR['hipX'], t), 2), round(tr(TR['hipY'], t), 2), f, e] for t, gx, gy, sa, f, e in GK]
for r in rows: r[4] = round(r[4], 4)
json.dump({'_note': '17 네온 루시아 한 손 도끼 내려찍기 키 — tools/genkeys17.py 가 만듦. keys = [t, gx, gy(리그 px, 골반 기준), 자루 각(도), 숙임(rad), 골반 x, 골반 y, 쥔 손, 이음] · tracks = 엔진 트랙 통째(골반·숙임)',
           'artBack': RET1, 'keys': rows, 'tracks': TR}, open(os.path.join(HERE, 'attack', 'keys17.json'), 'w'), ensure_ascii=False, indent=1)
print('keys17.json', len(rows), '키 · 대기', G0)
