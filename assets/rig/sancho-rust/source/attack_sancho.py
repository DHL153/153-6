# 3 러스트 산초 올려베기 (2026-10-19) — build_sancho.py 끝에서 exec (rig, def_parts, bones, np, math, json, os, HERE, PC, OUT, img 사용)
#  rigid 칼(칼 먼저, 쥔 팔 조각이 칼에 붙음) + armIK(윗팔·팔뚝 길이 고정 두 관절) — 11 네온 알론소 v5.4 방식, 키는 attack_keys.json
#  · 엔진 이름: near(armF→foreF) = 위 주먹·가까운 팔 · far(armU→armL) = 아래 주먹·먼 팔 + 어깨갑
#  · 엔진 트랙 shNx·shNy 는 armU(= 산초 먼 어깨 + 어깨갑)를, shFx·shFy 는 armF(= 산초 가까운 어깨)를 옮김 (이름이 21 기준이라 반대)
ATK = json.load(open(os.path.join(HERE, 'attack_keys.json'), encoding='utf-8'))
#  · 먼 팔은 손목 마디(armL 주먹 + armLf 팔뚝, 엔진 wristArm) — 칼이 한 바퀴 돌아도 조각 바꾸기 없음
act = dict(ATK['action']); act.update({'kind': 'sword', 'rigid': True, 'frame': 'torso', 'orderAlways': True})
gx, gy, sa = [], [], []
for t, X, Y, A, *e in ATK['grip']:
    ee = e[0] if e else 'io'; gx.append([t, X, ee]); gy.append([t, Y, ee]); sa.append([t, A, ee])
act.update({'gx': gx, 'gy': gy, 'sa': sa})
for k, L in ATK.get('orders', {}).items(): rig[k] = L
if ATK.get('weaponFront'):   # 칼 앞 사본(weaponF·weaponHF): 올려베기·끝·돌아옴 동안 칼은 머리 뒤(얼굴을 안 가림) → 대기 순서(칼이 머리카락 앞)로 돌아가기 전 앞 사본이 서서히 나타남(순서 바뀜 튐 없음)
    bones.append(dict(name='weaponF', parent='weapon', pos=[0, 0], part='weapon')); bones.append(dict(name='weaponHF', parent='weaponH', pos=[0, 0], part='weaponH'))
    rig['hidden'] = rig.get('hidden', []) + ['weaponF', 'weaponHF']
rig['actions'] = {'upslash': act}
rig['ui']['attack'] = 'upslash'
rig['cutHold'] = ATK.get('cutHold', .5)
