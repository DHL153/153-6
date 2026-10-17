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
