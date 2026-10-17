# 21 스카이아크 알론소 (alonso-sky) — 지금: 내려찍기 v2 확인 대기 (2026-10-18 01:40)
기준: 1 러스트 알론소 v4 (대검). 대검 위치 = 원화 그대로(칼날 머리 뒤, 손잡이 얼굴 앞). 원화 손 4손가락 수정본 대기.
받은 것: 조각 시트 A·B (source/sheets/sheet1_A.png·sheet1_B.png, 각 36조각) → **A 사용**
- 표정: A(작은 얼굴 패치)가 머리에 1.1배로 잘 맞음. B는 귀까지 그려져 귀가 두 겹. 둘 다 앞머리가 없는 얼굴이라 → 머리 그림의 앞머리(머리카락 색)를 얼굴 위에 다시 그림(클립)
- 몸통: A(벨트까지) + 앞·뒤 자락 따로가 깔끔. B 몸통은 자락이 한 번 더 그려짐
- 쥔 손 4종·메는 손·먼 주먹: 엄지 빼고 4손가락 보임 — 합격
- 팔뚝: 쥔 손에 팔뚝이 없음 → 메는 손·먼 주먹 조각의 팔뚝(토시)을 잘라 씀
남은 것: 고친 원화(4손가락), 동작 시트(달리기 8·내려찍기 6)

## 22:24~22:26 받음
- 원화 4손가락 수정본: 손 부분만 바뀜(666px, 다른 곳 0) → 합격. source/ref512.png, 게임 마이룸 그림 char_0021.png도 교체
- 동작 시트 v1 (source/sheets/motion_v1.png): 달리기 8 — 칼이 원화 자리(머리 뒤 칼날·얼굴 앞 손잡이) 그대로 ✓ / 내려찍기 6 — 잡기·들기·머리 위·수평 휘두름·런지 타격·복귀
  - 2번: 두 팔뚝이 얼굴 아래쪽 앞을 지나지만 두 눈은 보임
  - 3번: 머리 위에서 얼굴이 정면으로 돎 — 조각은 3/4 얼굴뿐 → 리그는 3/4 얼굴 유지(목표 자세로는 팔·칼 자리만)
- 조각 이름 붙이기·자홍 번짐 제거: source/pieces/*.png (36장, names.json). 맞춤 도구 source/fit.py
- 머리 조각 → 원화 맞춤 1차: 0.76배·−6° (오차 53 — 원화와 시트 머리 그림이 조금 달라 관절점 기준으로 다시 맞출 것)

## 00:30 내려찍기 v1 (편집 툴 v54)
- 빌드: `cd source && python3 -I build_sky.py` (attack_sky.py + attack_keys.json 포함). 보기: `tools/shota.py 'ts=0,0.3,0.43,0.52&k=0.5&cols=4&fw=1400&ox=600' out.png`
- 긴 손잡이: 칼 = 칼날(weapon) + 감은 부분(hiltW) 두 장. 공격 때 엔진 hiltSlide로 칼날이 손 쪽으로 미끄러져 손잡이가 짧아짐(시트처럼). 서 있을 땐 원래 그림 그대로
- 시작·끝(0~0.12, 0.80~)은 원화 메는 손(cArt) — 서 있는 그림과 튐 없이 이어짐. orderAlways(opt-in)
- 쥔 팔 조각 6장(cUp·fUp·cSw·fSw·cIm·fIm), 타격 때 가까운 손은 좌우 뒤집은 주먹(손목이 어깨 쪽)
- 남은 것: 앞자락 길이, 정강이 굵기, 게임 연결(REGISTRY 21·gameRef·cutHold·컷인 가운데)

## 01:40 내려찍기 v2 (DHL 00:39 표시 6곳)
- 손: 메는 손=왼손(cArt·gF45), 자유 손=오른손(gNv·gNh), 좌우 뒤집기 없음. 손목 꺾임 ±40° 안에서 `tools/solve2.py`·`tools/opt.py`로 풂
- 머리 위 칼은 머리 앞(drawOver), 휘두름·타격은 drawStrike(먼 주먹이 가까운 팔 위)
- 엔진 opt-in: reachIK(손 잡기·놓기 IK)·reachUp(계단 키)·reachBulge(곡선 경로)·shoulderN/F(+shN/shF 키)
- 키 보정: `tools/calib.py` (빌드 + 프로브 + gripFix 3회)

## 01:50 내려찍기 v3 (DHL 01:26 표시 3곳)
- 머리 위: 먼 팔 = cN(cFist+토시 팔뚝 한 장) + armFup, 가까운 윗팔 armNup, 어깨갑 fade(엔진 opt-in `fade`)
- 들어 올리기 0~0.20 · 돌아옴 0.72~ = 원화 메는 손 cArt + drawA (cU 삭제)
- 타격: 뒷손을 가까운 팔 뒤로, hilt 235(날밑이 앞주먹 앞)
- 보기 도구: `tools/atkview.html?...&hide=pauldron,armF` (조각 숨겨 보기)
- 남은 것: 타격 손 그림(칼끝 오른쪽·손목 왼쪽으로 쥔 양손) 요청 여부, 앞자락·정강이, 게임 연결

## 02:15 내려찍기 v4 (DHL 01:54)
- 칼 메는 손: 공격 내내 원화 손 cArt + 늘인 소매 armFw (cN·armFup·armNup 삭제)
- 가까운 팔: armUs(소매 밑단에서 자름, source/sleeve_crop.py) + 쥔 팔뚝, 소매가 팔뚝 위
- 휘두름·타격 0.40~0.62: 먼 팔 fade 0, 그리는 순서 drawSwing·drawStrike2 추가

## 02:30 게임 반영 (DHL 02:20 "기존 것 참고해서 · 컷인 안 잘리게 · 도감 가운데")
- index.html: REGISTRY 21:'alonso-sky', rig.def 스크립트(?v=버전 해시)
- 도감: gameRef.refOrigin x 273.7 (fitArt 중심 275.7 − hip x 4/2) → 마이룸·전투 두 장 모두 골반 = 칸 가운데
- 컷인: cutHold .55 (내려찍은 런지 자세, 칼까지 칸 가운데 · 발은 칸 안 — 6 카르덴 발 보정과 같이 동작)
- 확인 스크립트: source/tools/game_check.py [가로 세로 이름]
