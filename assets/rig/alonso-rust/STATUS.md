# 알론소 (alonso-rust, 1번) — 지금: v4 게임 적용 (2026-10-17)
기준: 오른쪽 3/4 새 시트 (source/v4/sheets). 빌드: `cd source/v4 && python3 -I build_v4.py` (출력 = 이 폴더 rig.json·rig.def.js·parts/)
게임: 전투·마이룸·친구 방문 = 리그 / 도감·시작 선택 = 대기 → 클릭 → 전투와 같은 내려찍기 → 대기 / 스킬 컷인 = 내려찍은 자세 유지(cutHold .58)
캐시: rig.json version = 그림 해시 → 게임이 조각 그림에 ?v= 를 붙임. index.html 스크립트 태그 ?v= 도 같은 값으로 바꿀 것
게임 그림 자리: gameRef (characters/char_0001.png 512px 기준 발 자리·배율). refOrigin·refScale은 시트 기준(편집기용)
엔진 opt-in: swordGrip + rigid 내려찍기, hitStop, streamers(목도리 꼬리), overlays, headFront, legs.hipX/runX
남은 것: 전투 타격 시점(게임 타격 100ms vs 칼이 땅에 닿는 308ms) 맞출지 결정 · 다리 길이/자세 시트 2 조각으로 다시 · 손 흔들기 인사(시트 W) · 정적 그림(char_0001·battle_char_0001)은 아직 v3 그림
