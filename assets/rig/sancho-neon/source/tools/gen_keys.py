"""13 네온 산초 올려베기 키 = 3 러스트 산초 v3.1 키(sancho-rust/source/attack_keys.json) + 네온 몸에 맞춘 곳만 바꿈 → ../attack_keys.json
실행: cd source && python3 -I tools/gen_keys.py && python3 -I tools/check_keys.py
바꾼 곳(이유):
 1) 칼 각도 sa = 러스트 각도 + (네온 대기 손잡이 축 − 러스트 대기) — 같은 시계 방향
 2) 가까운 팔 접힘(0.16~0.18, 0.75~0.77 — 프레임이 하나는 꼭 들어가게 0.02): 네온 가까운 어깨는 아래 주먹 뒤(러스트는 위 주먹 왼쪽 아래)라 대기 팔꿈치 쪽(ikSide −1)과 내려친 뒤 쪽(+1)이 반대
    → 두 손이 어깨 앞을 지나며 팔이 완전히 접히는 자리(쥔 점 = 어깨에서 팔뚝−윗팔 만큼, 팔꿈치 왼쪽 아래)를 잠깐 지나게 하고 그 순간에 ikSideK 를 바꿈 — 접힌 자리에선 두 쪽 팔꿈치가 같은 점이라 튐 없음
 3) 낮은 겨눔(0.255~0.36) 손 13~17 아래: 네온 마스크(입 자리)가 러스트 입보다 낮아 날밑 끝이 마스크를 덮었음
 4) 올려베기·끝 런지 손 오른쪽으로 4~12(끝 −38°, 러스트 −40°) + 가까운 어깨 앞으로 80~85: 주먹이 마스크 아래를, 날밑이 먼 눈을 덜 가림(렌더 10-19 0.53)
 5) 끝 런지 먼 어깨 뒤로 20 (먼 주먹이 먼 어깨 바로 앞 — 먼 팔이 다 접혀도 닿음이 모자랐음)
 6) 돌아옴 0.72 손 (−80,−120)·접힘 팔꿈치 140°(시작 110°와 따로) — 팔꿈치가 한 프레임에 크게 안 튐(elbow_sim)
"""
import json, math, os, sys, copy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(HERE, 'tools'))
import check_keys as C
R = json.load(open(os.path.join(HERE, '..', '..', 'sancho-rust', 'source', 'attack_keys.json'), encoding='utf-8'))
K = copy.deepcopy(R); D = C.SA0 - (-1.944)
L1, L2 = C.L1N, C.L2N; U_EL = (-0.342, 0.940)                               # 접힌 자리 팔꿈치 방향(어깨에서 아래로 110°) — 대기(178°, 왼쪽)와 내려친 뒤(+1 쪽 86~100°) 사이: 접힘을 지나며 팔꿈치가 크게 안 튐(0.8,0.6 일 때 한 프레임 47px)
FOLD = (round(C.SN[0] - (L2 - L1) * U_EL[0], 1), round(C.SN[1] - (L2 - L1) * U_EL[1], 1))
U_ELR = (math.cos(math.radians(140)), math.sin(math.radians(140)))   # 돌아올 때 접힘 팔꿈치 140° + 0.72 손 (−80,−120) — tools/elbow_sim.py 로 고른 값(한 프레임 팔꿈치 이동 최대 39px, 러스트 돌아옴 42px)
FOLDR = (round(C.SN[0] - (L2 - L1) * U_ELR[0], 1), round(C.SN[1] - (L2 - L1) * U_ELR[1], 1))
R_ = {round(t, 3): (gx, gy, sa, e) for t, gx, gy, sa, *e in R['grip']}
deg = lambda d: round(math.radians(d), 4)
G = [[0, 'idle', 'idle', 'idle', 'io'], [0.1, 'idle', 'idle', 'idle', 'io'],
     [0.16, FOLD[0], FOLD[1], deg(-95), 'io'], [0.18, FOLD[0], FOLD[1], deg(-91), 'io'],
     [0.2, -55, -120, round(R_[0.2][2] + D, 4)], [0.225, -40, -88, round(R_[0.225][2] + D, 4)],
     [0.255, -34, -52, round(R_[0.255][2] + D, 4), 'io'], [0.3, -32, -40, round(R_[0.3][2] + D, 4), 'io'], [0.36, -32, -38, round(R_[0.36][2] + D, 4), 'i'],
     [0.4, 126, -106, round(R_[0.4][2] + D, 4), 'o'], [0.44, 134, -100, deg(-38), 'o'], [0.62, 134, -100, deg(-38), 'io'],
     [0.72, -80, -120, round(R_[0.72][2] + D, 4), 'io'], [0.75, FOLDR[0], FOLDR[1], deg(-99), 'io'], [0.77, FOLDR[0], FOLDR[1], deg(-104), 'io'],
     [0.8, 'idle', 'idle', 'idle', 'io'], [0.94, 'idle', 'idle', 'idle']]
K['grip'] = G
a = K['action']; a['sF'] = [[0, round(-C.SFL, 1)]]
a['ikSide'] = {'N': 1, 'F': -1}; a['ikSideK'] = {'N': [[0, -1], [0.17, 1], [0.76, -1]], 'F': [[0, -1]]}
a['shFx'] = [[0, 0, 'io'], [0.36, 0, 'i'], [0.4, 80, 'o'], [0.44, 85, 'o'], [0.62, 85, 'io'], [0.72, 0, 'io'], [0.94, 0]]
a['shNx'] = [[0, 0, 'io'], [0.1, 0, 'io'], [0.165, -20, 'io'], [0.2, -30], [0.225, -50], [0.255, -40, 'io'], [0.3, -45, 'io'], [0.36, -45, 'i'], [0.4, 10, 'o'], [0.44, 20, 'o'], [0.62, 20, 'io'], [0.72, 0, 'io'], [0.94, 0]]   # 5) 끝 런지 먼 어깨 뒤로 20(몸 튼 쪽) — 먼 주먹이 먼 어깨에 너무 가까워 팔이 다 접혀도 모자랐음
K['torsoTwist'] = {'ax': 110, 'by': -16, 'p': 1}
K['cutHold'] = 0.42   # 스킬 컷인 멈춤 = 올려 베는 순간(칼 2시로 올라가는 중·런지 들어가기 전, 골반 높음) — 0.36~0.62 후보 8장 중(버팀·끝 런지 .44~ 는 낮게 깔림), 2026-10-19 게임 연결
K['note'] = ('13 네온 산초 올려베기 키 v1 (2026-10-19, DHL 13:39 "러스트 산초와 똑같은 모션") — 3 러스트 산초 v3.1 키를 그대로 옮기고 네온 몸에 맞춘 곳만 바꿈(tools/gen_keys.py 머리말). '
             f'접힌 자리 FOLD {FOLD}·돌아옴 {FOLDR} (가까운 어깨 {C.SN} 에서 팔뚝−윗팔 {L2 - L1}). grip = [t, gx, gy, sa, ease] (상체 기준, 골반 원점, 리그 단위), idle = 원화 쥔 점·각도')
json.dump(K, open(os.path.join(HERE, 'attack_keys.json'), 'w'), ensure_ascii=False, indent=0)
print('FOLD', FOLD, 'D', round(D, 4), 'sF', a['sF'])
