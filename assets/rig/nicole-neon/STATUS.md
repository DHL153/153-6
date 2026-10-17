# 니콜 네온 (nicole-neon, 18번) — v1 완성 (2026-10-17), 게임 적용
기준: **8 러스트 니콜(rust-fork-girl v15) 구조 1:1** (DHL 결정). 원화도 러스트 니콜 자세로 새로 뽑아 마이룸 그림(char_0018) 교체.
검수(전부 통과): 관절 검사(tools/audit_joints.py, 10장면) 손목·팔꿈치·무릎·엉덩이 범위 안 · 무기 땅 아래 ≤12 · 동작 밖 튐 ≤14° · 발 미끄러짐 0 /
  추가 검사(tools/audit_extra.py) 허리 이음매 0 · 손-자루 접촉 · 팔꿈치 방향 유지 · 팔뚝 비틀림 0° · 코트 메시 접힘 0, 변 늘어남 ≤1.95(달리기)/1.5(찌르기) /
  마이룸 반응 6종(wave·hop·nod·surprise·cute·cute2) 중 손이 창에서 안 떨어짐 / 8 니콜·28 스카이 회귀 통과.
시트: sheets/sheet0.png(원화) · partsA.png(조각 25칸) · partsB.png(재요청 3칸: 먼 주먹·허벅지·정강이) · weaponW.png(창 단독, 원화 비율)
만들기: cd source && python3 -I split_parts.py && python3 -I make_ref.py && python3 -I hands.py && python3 -I faces.py && python3 -I joints.py && python3 -I build_neon.py
  (조각 배치: sift_result.json·fix_result.json — sift_match.py·fixmatch.py 결과. 손질값: tune.json) · 검사: bash tools/check.sh · 장면표: tools/sheet.py
8과 다른 점(전부 opt-in, 8·28 동작 그대로):
  칼라 앞/뒤(collar·collarBack: 목이 칼라 안으로) · 먼 어깨갑(pauldronF, 먼 팔 35% 따라 돎: def.follow) · 코트 꼬리(cape 자리, 허리 뼈) · 파우치 2개(코트 위)
  그린 깜빡임(blinkFaces) · 표정 8종 + 먼 눈까지 패치
  긴 기계 창: 찌르기 때 자루가 앞손 안에서 미끄러짐(actions.thrust.slide — 뒤끝이 땅에 안 박힘) · 달릴 때 창 팔 팔꿈치 더 굽힘(runForeBend)
  코트 밑으로 다리가 보임: 서 있을 때만 발 벌림(idleStance) · 발 닿기 전 골반 미리 내림(dropLift) · 코트 밀림은 서 있는 자세 기준(hemRest)
  도감·시작 선택 공격 = 전투와 같은 찌르기(ui.stillSame), 컷인만 찌른 자세 유지
남은 것: 없음(DHL 확인 대기). 원화 대비 서 있는 자세에서 골반이 약 7px(512 기준) 낮음 — 다리 길이·벌림 때문, 필요하면 다리 시트로 보정

## 연구 기록 (2026-10-17 오후) — 게임에는 아직 반영 안 함
- 동작 시트 motion1(달리기 8·찌르기 6) 받음 → tools/keys.py(프레임 분리·측정), tools/cmpkeys.py(시트 vs 리그 같은 시점 겹침), tools/fit.py·fitrun.py(겹침 최대화 맞춤) 작성.
- 찌르기: 시트는 창을 수평 그대로 허리로 당겼다 찌름(지금 리그는 위로 젖혔다 내림). 맞춤값은 tune.json thrustFull_wip — 겹침 0.53→0.68까지 올랐으나 엉덩이 각도 초과(−110°) + 코트가 안 벌어져 다리 모양이 시트와 다름 → 보류.
- 달리기: 실루엣 겹침만으로 맞추면 골반을 과하게 낮춤(hipBase 88) — 코트가 한 장이라 다리 대신 코트로 겹침을 채우는 '꼼수 해'. **실루엣 IoU만으로 동작을 맞추면 안 됨** → 발·무릎·손·머리 위치(관절점) 기준 맞춤으로 바꿀 것.
- 막힌 것: 코트 앞트임 조각(앞자락 / 뒤판+안감) — DHL에게 시트 요청함. 받으면 코트 2장 → 관절점 맞춤 → 찌르기·달리기 교체 → 검사 전부 통과 후 반영.
- 11:46 코트 트임 시트(sheets/coatSplit.png) 받음 → 코트 = 뒤판(skirt, 트임 뒤 안감 포함) + 앞자락(coatFlap). 두 장 겹침이 원래 코트와 IoU 0.997·색 차이 1.9. 엔진 opt-in def.flap: 앞자락은 뒤판 변형을 그대로 따르고 앞 무릎·런지만큼 트임 쪽이 벌어짐(안감 보임). 천 검사에 coatFlap 추가(접힘 0, 변 ≤1.59). 게임 반영.
- 찌르기 수평 당기기 시도(tune.json thrustOverride_wip): 창은 수평이 됐지만 시트보다 창이 높고(가슴), 발 벌림 좁음 → 관절점 맞춤 필요, 보류.
